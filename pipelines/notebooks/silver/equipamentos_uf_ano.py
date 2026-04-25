# Databricks notebook source
# MAGIC %md
# MAGIC # silver · equipamentos_uf_ano
# MAGIC
# MAGIC Lê `<catalog>.bronze.cnes_equipamentos`, agrega TODOS os equipamentos por
# MAGIC `(estado, ano, codequip)` com split de setor (SUS / Privado / Total).
# MAGIC Junta com `silver.populacao_uf_ano` (dim compartilhada) pra completar grid.
# MAGIC
# MAGIC Em vez de filtrar `CODEQUIP=42` (só RM), guarda TUDO. O front deixa o usuário
# MAGIC selecionar 1+ equipamentos e re-agregar client-side.
# MAGIC
# MAGIC ## Schema
# MAGIC ```
# MAGIC estado, ano, codequip, equipment_name, populacao,
# MAGIC cnes_count, total_avg, per_capita_scaled,
# MAGIC sus_cnes_count, sus_total_avg, sus_per_capita_scaled,
# MAGIC priv_cnes_count, priv_total_avg, priv_per_capita_scaled,
# MAGIC per_capita_scale_pow10
# MAGIC ```

# COMMAND ----------

dbutils.widgets.text("catalog", "mirante_prd")
CATALOG = dbutils.widgets.get("catalog")

BRONZE_TABLE     = f"{CATALOG}.bronze.cnes_equipamentos"
SILVER_POPULACAO = f"{CATALOG}.silver.populacao_uf_ano"
SILVER_TABLE     = f"{CATALOG}.silver.equipamentos_uf_ano"

PER_CAPITA_SCALE_POW10 = 6   # = "equipamentos por milhão de hab."

print(f"bronze={BRONZE_TABLE}  silver={SILVER_TABLE}")

# COMMAND ----------

# DATASUS CNES — código → descrição. Lista cobre os equipamentos de diagnóstico,
# terapia e infraestrutura mais relevantes. CODEQUIPs não mapeados aparecem como
# "Cód. NN" via fallback no front.
EQUIPMENT_NAMES = {
    "1":  "Aparelho de Raio-X",
    "2":  "Mamógrafo",
    "3":  "Ultrassom Geral",
    "4":  "Ultrassom Doppler",
    "5":  "Equipamento de Hemodiálise",
    "6":  "Eletrocardiógrafo (ECG)",
    "7":  "Equipamento de Endoscopia",
    "8":  "Eletroencefalógrafo (EEG)",
    "9":  "Equipamento de Hemodinâmica",
    "10": "Densitômetro Ósseo",
    "11": "Câmara Hiperbárica",
    "12": "Equipamento de Ondas de Choque",
    "13": "Equipamento de Cobaltoterapia",
    "14": "Acelerador Linear (Radioterapia)",
    "15": "Equipamento de Braquiterapia",
    "16": "Equipamento de Diagnóstico Cardiológico",
    "17": "Equipamento de Litotripsia",
    "18": "Bomba de Infusão",
    "19": "Eletrocardiógrafo Computadorizado",
    "20": "Equipamento de Ultrassonografia",
    "21": "Equipamento de Polissonografia",
    "22": "Equipamento de Audiometria",
    "23": "Equipamento de Anestesia",
    "24": "Aparelho de Eletrocardiografia",
    "25": "Equipamento de Esterilização",
    "26": "Aparelho de Tomografia Computadorizada",
    "27": "Equipamento de Mamografia",
    "28": "Equipamento de Mamografia Digital",
    "29": "Tomógrafo Computadorizado",
    "30": "Aparelho de Diatermia",
    "31": "Equipamento de Eletrocirurgia",
    "32": "Equipamento de Fototerapia",
    "33": "Equipamento de Ortopedia",
    "34": "Equipamento de Ergometria",
    "35": "Equipamento de Holter",
    "36": "Equipamento de MAPA",
    "37": "Aparelho de Ultrassom 3D/4D",
    "38": "Equipamento de Espirometria",
    "39": "Litotriptor",
    "40": "Equipamento de Cobaltoterapia",
    "41": "Acelerador Linear de Partículas",
    "42": "Ressonância Magnética",
    "43": "Equipamento de Medicina Nuclear",
    "44": "Tomografia por Emissão de Pósitrons (PET)",
    "45": "Tomografia (SPECT)",
    "46": "Equipamento de Radioterapia",
    "47": "Tomografia Híbrida (PET-CT)",
    "48": "Aparelho de Hemodiálise",
    "49": "Equipamento de Quimioterapia",
    "50": "Equipamento de Diálise Peritoneal",
}

# COMMAND ----------

from pyspark.sql import functions as F

# Read latest snapshot
bronze = spark.read.table(BRONZE_TABLE)
if bronze.head(1) == []:
    raise ValueError(f"{BRONZE_TABLE} is empty.")

latest_ts = bronze.agg(F.max("_ingest_ts")).first()[0]
src = bronze.where(F.col("_ingest_ts") == latest_ts)
print(f"bronze rows in latest snapshot: {src.count():,}")

# Normalize types — KEEP all CODEQUIPs (no MRI filter)
df = (
    src.select(
        F.col("estado").cast("string"),
        F.col("ano").cast("int"),
        F.col("mes").cast("string"),
        F.col("CNES").cast("string").alias("cnes"),
        F.col("CODEQUIP").cast("string").alias("codequip"),
        F.col("QT_EXIST").cast("double").alias("qt_exist"),
        F.col("IND_SUS").cast("string").alias("ind_sus"),
    )
    .where(F.col("qt_exist").isNotNull())
    .where(F.col("codequip").isNotNull())
)

# ─── Drop partial years (must have all 12 monthly DBC files ingested) ──────
# DATASUS publica EQ<UF><YY><MM>.dbc um por mês. Se o ano em curso só tem 8 meses,
# ele entra como stub. Mantemos só Anos com 12 meses distintos no bronze.
months_per_year = df.groupBy("ano").agg(F.countDistinct("mes").alias("n_months"))
month_counts = sorted([(r["ano"], r["n_months"]) for r in months_per_year.collect()])
print(f"meses por Ano: {month_counts}")
full_years = [a for a, n in month_counts if n == 12]
dropped    = [a for a, n in month_counts if n != 12]
print(f"anos completos: {full_years}")
if dropped:
    print(f"⚠ anos parciais descartados: {dropped}")
df = df.where(F.col("ano").isin(full_years))

print("Top 10 codequips by row count:")
df.groupBy("codequip").count().orderBy(F.desc("count")).show(10)

# COMMAND ----------

# MAGIC %md
# MAGIC ## Compute monthly + sector annual averages PER CODEQUIP

# COMMAND ----------

# Monthly totals per (CNES, codequip, mes) — sum across sectors for monthly_total
monthly_all = (
    df.groupBy("estado", "ano", "cnes", "codequip", "mes")
      .agg(F.sum("qt_exist").alias("monthly_total"))
)

# Active months per (CNES, codequip, year) — shared denominator
cnes_month_count = (
    monthly_all.groupBy("estado", "ano", "cnes", "codequip")
               .agg(F.count("mes").alias("n_months"))
)

# All-sector annual average per CNES per codequip
cnes_all = (
    monthly_all.groupBy("estado", "ano", "cnes", "codequip")
               .agg(F.avg("monthly_total").alias("avg_year"))
               .where(F.col("avg_year").isNotNull())
)


def sector_year_avg(df_sector):
    sector_sum = (
        df_sector.groupBy("estado", "ano", "cnes", "codequip")
                 .agg(F.sum("qt_exist").alias("sector_sum"))
    )
    return (
        sector_sum
        .join(cnes_month_count, on=["estado", "ano", "cnes", "codequip"], how="left")
        .withColumn("avg_year", F.col("sector_sum") / F.col("n_months"))
        .where(F.col("avg_year").isNotNull())
        .select("estado", "ano", "cnes", "codequip", "avg_year")
    )


cnes_sus  = sector_year_avg(df.where(F.col("ind_sus") == F.lit("1")))
cnes_priv = sector_year_avg(df.where(F.col("ind_sus") == F.lit("0")))

# COMMAND ----------

# State-year-codequip aggregates per sector
agg_cnes_count = (
    cnes_all.groupBy("estado", "ano", "codequip")
            .agg(F.countDistinct("cnes").cast("long").alias("cnes_count"))
)

def agg_sector(df_cnes_sector, prefix: str):
    return df_cnes_sector.groupBy("estado", "ano", "codequip").agg(
        F.countDistinct("cnes").cast("long").alias(f"{prefix}cnes_count"),
        F.sum("avg_year").alias(f"{prefix}total_avg"),
    )

agg_sus  = agg_sector(cnes_sus,  prefix="sus_")
agg_priv = agg_sector(cnes_priv, prefix="priv_")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Cartesian (estado × ano × codequip) ⨯ populacao

# COMMAND ----------

df_pop = (
    spark.read.table(SILVER_POPULACAO)
         .select(
             F.col("uf").cast("string").alias("estado"),
             F.col("Ano").cast("int").alias("ano"),
             F.col("populacao").cast("long").alias("populacao"),
         )
)

codequips = cnes_all.select("codequip").distinct()
print(f"Distinct codequips in bronze: {codequips.count()}")

grid = df_pop.crossJoin(codequips)

fill_zeros = {
    "cnes_count": 0,
    "sus_cnes_count": 0,  "sus_total_avg":  0.0,
    "priv_cnes_count": 0, "priv_total_avg": 0.0,
}
df_out = (
    grid
    .join(agg_cnes_count, on=["estado", "ano", "codequip"], how="left")
    .join(agg_sus,        on=["estado", "ano", "codequip"], how="left")
    .join(agg_priv,       on=["estado", "ano", "codequip"], how="left")
    .fillna(fill_zeros)
)

df_out = df_out.withColumn("total_avg", F.col("sus_total_avg") + F.col("priv_total_avg"))

scale = F.pow(F.lit(10.0), F.lit(PER_CAPITA_SCALE_POW10).cast("double"))
pop = F.col("populacao")
def per_capita_scaled(c):
    return F.when(pop.isNull() | (pop == 0), F.lit(0.0)).otherwise(F.col(c) / pop * scale)

df_out = (
    df_out
    .withColumn("per_capita_scaled",      per_capita_scaled("total_avg"))
    .withColumn("sus_per_capita_scaled",  per_capita_scaled("sus_total_avg"))
    .withColumn("priv_per_capita_scaled", per_capita_scaled("priv_total_avg"))
    .withColumn("per_capita_scale_pow10", F.lit(PER_CAPITA_SCALE_POW10).cast("int"))
)

# Add equipment_name
name_map = F.create_map(*[v for kv in EQUIPMENT_NAMES.items()
                          for v in (F.lit(kv[0]), F.lit(kv[1]))])
df_out = df_out.withColumn(
    "equipment_name",
    F.coalesce(name_map.getItem(F.col("codequip")),
               F.concat(F.lit("Cód. "), F.col("codequip"))),
)

# Drop rows with no equipment data at all (avoids cartesian bloat)
df_out = df_out.where((F.col("cnes_count") > 0) | (F.col("sus_cnes_count") > 0) | (F.col("priv_cnes_count") > 0))

silver_df = df_out.select(
    "estado", "ano", "codequip", "equipment_name",
    "cnes_count",     "total_avg",     "per_capita_scaled",
    "sus_cnes_count", "sus_total_avg", "sus_per_capita_scaled",
    "priv_cnes_count","priv_total_avg","priv_per_capita_scaled",
    "populacao", "per_capita_scale_pow10",
).withColumn("_silver_built_ts", F.current_timestamp()).orderBy("estado", "ano", "codequip")

# COMMAND ----------

n = silver_df.count()
ufs = silver_df.select("estado").distinct().count()
years = silver_df.select("ano").distinct().count()
codequips_kept = silver_df.select("codequip").distinct().count()
print(f"rows={n}  ufs={ufs}  years={years}  codequips={codequips_kept}")
assert ufs == 27, f"Expected 27 UFs, got {ufs}"
print("✔ DQ passed")

(
    silver_df.write.format("delta")
        .mode("overwrite")
        .option("overwriteSchema", "true")
        .partitionBy("ano")
        .saveAsTable(SILVER_TABLE)
)
spark.sql(f"COMMENT ON TABLE {SILVER_TABLE} IS "
          f"'Mirante · Equipamentos CNES por UF × Ano × CODEQUIP, com split SUS/Privado.'")
print(f"✔ {SILVER_TABLE} written ({n} rows)")

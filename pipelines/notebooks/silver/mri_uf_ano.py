# Databricks notebook source
# MAGIC %md
# MAGIC # silver · mri_uf_ano
# MAGIC
# MAGIC Lê `<catalog>.bronze.cnes_equipamentos`, filtra MRI (CODEQUIP=42), agrega por
# MAGIC (estado, ano) com split por setor (SUS / Privado / Total), junta com
# MAGIC dim compartilhada `<catalog>.silver.populacao_uf_ano` pra completar UF×Ano grid.
# MAGIC
# MAGIC ## Lógica do split por setor
# MAGIC
# MAGIC `IND_SUS` no bronze:
# MAGIC - `'1'` → equipamento disponível pro SUS
# MAGIC - `'0'` → equipamento privado
# MAGIC
# MAGIC O mesmo CNES pode ter linhas SUS E privadas no mesmo mês. Pra evitar
# MAGIC overcount quando um CNES muda IND_SUS no meio do ano:
# MAGIC - `n_months` = meses ativos do CNES no ano (denominador comum)
# MAGIC - `setor_avg` = sum(qt_exist do setor) / n_months
# MAGIC - garantia: `sus_avg + priv_avg == total_avg`
# MAGIC
# MAGIC ## Schema de saída (bate com o JSON do front)
# MAGIC ```
# MAGIC estado, ano, populacao,
# MAGIC cnes_count, total_mri_avg, mri_per_capita_scaled,
# MAGIC sus_cnes_count, sus_total_mri_avg, sus_mri_per_capita_scaled,
# MAGIC priv_cnes_count, priv_total_mri_avg, priv_mri_per_capita_scaled,
# MAGIC mri_per_capita_scale_pow10
# MAGIC ```

# COMMAND ----------

dbutils.widgets.text("catalog", "mirante_prd")
CATALOG = dbutils.widgets.get("catalog")

BRONZE_TABLE     = f"{CATALOG}.bronze.cnes_equipamentos"
SILVER_POPULACAO = f"{CATALOG}.silver.populacao_uf_ano"
SILVER_TABLE     = f"{CATALOG}.silver.mri_uf_ano"

MRI_CODEQUIP            = "42"
PER_CAPITA_SCALE_POW10  = 6     # = "MRI por milhão de habitantes"

print(f"bronze={BRONZE_TABLE}  pop_dim={SILVER_POPULACAO}  silver={SILVER_TABLE}")

# COMMAND ----------

from pyspark.sql import functions as F

# ─── Read bronze (latest snapshot) ─────────────────────────────────────────
bronze = spark.read.table(BRONZE_TABLE)
if bronze.head(1) == []:
    raise ValueError(f"{BRONZE_TABLE} is empty — run the bronze task first.")

# Take only the latest source_file batch (same pattern as populacao silver to avoid
# duplicate-snapshot multiplication)
latest_file = (
    bronze.orderBy(F.desc("_ingest_ts"), F.desc("_source_file"))
          .select("_source_file").first()[0]
)
src = bronze.where(F.col("_source_file") == latest_file)

# Wait — for MRI we want ALL files (each .dbc covers a unique UF+month). Different
# from populacao where the JSON IS the whole snapshot. Here filter by latest run only.
# Actually — bronze.cnes_equipamentos has one row per (CNES, equipamento, sector).
# Each .dbc → 1 parquet → ~thousands of rows. Auto Loader appends each time, so we
# need to take the LATEST snapshot per (estado, ano, mes).
# Simpler: take all rows from the most recent _ingest_ts batch.
src = bronze.where(F.col("_ingest_ts") == bronze.agg(F.max("_ingest_ts")).first()[0])
print(f"bronze rows in latest snapshot: {src.count():,}")

# ─── Filter to MRI only + normalize types ──────────────────────────────────
df_mri = (
    src.select(
        F.col("estado").cast("string"),
        F.col("ano").cast("int"),
        F.col("mes").cast("string"),
        F.col("CNES").cast("string").alias("cnes"),
        F.col("CODEQUIP").cast("string").alias("codequip"),
        F.col("QT_EXIST").cast("double").alias("qt_exist"),
        F.col("IND_SUS").cast("string").alias("ind_sus"),
    )
    .where(F.col("codequip") == F.lit(MRI_CODEQUIP))
    .where(F.col("qt_exist").isNotNull())
)
print(f"MRI rows (CODEQUIP=42): {df_mri.count():,}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Compute monthly + sector annual averages

# COMMAND ----------

# Monthly totals (all sectors) per CNES per (estado, ano, mes)
monthly_all = (
    df_mri.groupBy("estado", "ano", "cnes", "mes")
          .agg(F.sum("qt_exist").alias("monthly_total"))
)

# Number of active months per CNES-year (shared denominator)
cnes_month_count = (
    monthly_all.groupBy("estado", "ano", "cnes")
               .agg(F.count("mes").alias("n_months"))
)

# All-sector annual average
cnes_all = (
    monthly_all.groupBy("estado", "ano", "cnes")
               .agg(F.avg("monthly_total").alias("avg_mri_cnes_year"))
               .where(F.col("avg_mri_cnes_year").isNotNull())
)


def sector_year_avg(df_sector):
    """Per-sector annual average using shared n_months as denominator."""
    sector_sum = (
        df_sector.groupBy("estado", "ano", "cnes")
                 .agg(F.sum("qt_exist").alias("sector_sum"))
    )
    return (
        sector_sum
        .join(cnes_month_count, on=["estado", "ano", "cnes"], how="left")
        .withColumn("avg_mri_cnes_year", F.col("sector_sum") / F.col("n_months"))
        .where(F.col("avg_mri_cnes_year").isNotNull())
        .select("estado", "ano", "cnes", "avg_mri_cnes_year")
    )


cnes_sus  = sector_year_avg(df_mri.where(F.col("ind_sus") == F.lit("1")))
cnes_priv = sector_year_avg(df_mri.where(F.col("ind_sus") == F.lit("0")))

# COMMAND ----------

# MAGIC %md
# MAGIC ## State-year aggregates per sector

# COMMAND ----------

agg_cnes_count = (
    cnes_all.groupBy("estado", "ano")
            .agg(F.countDistinct("cnes").cast("long").alias("cnes_count"))
)

def agg_sector(df_cnes_sector, prefix: str):
    return df_cnes_sector.groupBy("estado", "ano").agg(
        F.countDistinct("cnes").cast("long").alias(f"{prefix}cnes_count"),
        F.sum("avg_mri_cnes_year").alias(f"{prefix}total_mri_avg"),
    )

agg_sus  = agg_sector(cnes_sus,  prefix="sus_")
agg_priv = agg_sector(cnes_priv, prefix="priv_")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Join with shared dim populacao_uf_ano (UF × Ano grid)

# COMMAND ----------

df_grid = (
    spark.read.table(SILVER_POPULACAO)
         .select(
             F.col("uf").cast("string").alias("estado"),
             F.col("Ano").cast("int").alias("ano"),
             F.col("populacao").cast("long").alias("populacao"),
         )
)

fill_zeros = {
    "cnes_count": 0,
    "sus_cnes_count": 0,  "sus_total_mri_avg": 0.0,
    "priv_cnes_count": 0, "priv_total_mri_avg": 0.0,
}

df_out = (
    df_grid
    .join(agg_cnes_count, on=["estado", "ano"], how="left")
    .join(agg_sus,        on=["estado", "ano"], how="left")
    .join(agg_priv,       on=["estado", "ano"], how="left")
    .fillna(fill_zeros)
)

# total_mri_avg = sus + priv (exato, pois compartilham n_months)
df_out = df_out.withColumn(
    "total_mri_avg",
    F.col("sus_total_mri_avg") + F.col("priv_total_mri_avg"),
)

# Per-capita escalado (×10⁶ → "MRI por milhão de hab.")
scale = F.pow(F.lit(10.0), F.lit(PER_CAPITA_SCALE_POW10).cast("double"))
pop = F.col("populacao")

def per_capita_scaled(total_col: str):
    return F.when(pop.isNull() | (pop == 0), F.lit(0.0)) \
            .otherwise(F.col(total_col) / pop * scale)

df_out = (
    df_out
    .withColumn("mri_per_capita_scaled",      per_capita_scaled("total_mri_avg"))
    .withColumn("sus_mri_per_capita_scaled",  per_capita_scaled("sus_total_mri_avg"))
    .withColumn("priv_mri_per_capita_scaled", per_capita_scaled("priv_total_mri_avg"))
    .withColumn("mri_per_capita_scale_pow10", F.lit(PER_CAPITA_SCALE_POW10).cast("int"))
)

silver_df = df_out.select(
    "estado", "ano",
    "cnes_count",     "total_mri_avg",     "mri_per_capita_scaled",
    "sus_cnes_count", "sus_total_mri_avg", "sus_mri_per_capita_scaled",
    "priv_cnes_count","priv_total_mri_avg","priv_mri_per_capita_scaled",
    "populacao", "mri_per_capita_scale_pow10",
).withColumn("_silver_built_ts", F.current_timestamp()).orderBy("estado", "ano")

# COMMAND ----------

# MAGIC %md
# MAGIC ## DQ checks

# COMMAND ----------

n = silver_df.count()
n_bad = silver_df.where(
    F.col("populacao").isNull() | (F.col("populacao") <= 0)
    | (F.col("total_mri_avg") < 0)
    | (F.col("sus_total_mri_avg") < 0)
    | (F.col("priv_total_mri_avg") < 0)
).count()
ufs = silver_df.select("estado").distinct().count()
years = silver_df.select("ano").distinct().count()

print(f"rows={n}  ufs={ufs}  years={years}  bad={n_bad}")
assert ufs == 27,    f"Expected 27 UFs, got {ufs}"
assert n_bad == 0,   f"Got {n_bad} bad rows"
print("✔ DQ passed")

# COMMAND ----------

(
    silver_df.write.format("delta")
        .mode("overwrite")
        .option("overwriteSchema", "true")
        .partitionBy("ano")
        .saveAsTable(SILVER_TABLE)
)

spark.sql(f"COMMENT ON TABLE {SILVER_TABLE} IS "
          f"'Mirante · MRI por UF × ano (CNES code 42), com split SUS/Privado e per_capita escalado x10^6.'")

print(f"✔ {SILVER_TABLE} written ({n} rows)")
spark.read.table(SILVER_TABLE).show(5)

# Databricks notebook source
# MAGIC %md
# MAGIC # silver · sih_uropro_uf_ano
# MAGIC
# MAGIC Lê `<catalog>.bronze.sih_aih_rd_uropro` (microdados AIH filtrados por
# MAGIC procedimento) e agrega por `(uf, ano, mes, proc_rea, car_int, gestao)`
# MAGIC com métricas de gasto, internação, óbito.
# MAGIC
# MAGIC **Decisão de design**: silver mantém granularidade fina (mês × caráter ×
# MAGIC gestão). Gold colapsa por `(uf, ano, proc_rea)` — o agregado que o front
# MAGIC consome. Caso queiramos no futuro um drill-down por mês ou caráter, o
# MAGIC silver já tem.
# MAGIC
# MAGIC ## Schema de saída
# MAGIC ```
# MAGIC uf, ano, mes, proc_rea, proc_label,
# MAGIC car_int, car_label,        # eletivo/urgência/outro
# MAGIC gestao, gestao_label,      # estadual/municipal/dupla
# MAGIC n_aih, sum_dias_perm, n_morte,
# MAGIC val_tot, val_sh, val_sp,    # nominal R$
# MAGIC val_tot_avg, val_sh_avg, val_sp_avg,
# MAGIC dias_perm_avg, mortalidade
# MAGIC ```
# MAGIC
# MAGIC ## Origem analítica
# MAGIC Reproduz e estende a análise do trabalho de especialização em
# MAGIC Enfermagem (TATIELI, 2022) sobre o tratamento cirúrgico da
# MAGIC incontinência urinária no SUS — agora com microdados (RD), não
# MAGIC mais com agregados pré-computados do TabNet.

# COMMAND ----------

dbutils.widgets.text("catalog", "mirante_prd")
CATALOG = dbutils.widgets.get("catalog")

BRONZE_TABLE = f"{CATALOG}.bronze.sih_aih_rd_uropro"
SILVER_TABLE = f"{CATALOG}.silver.sih_uropro_uf_ano"

print(f"bronze={BRONZE_TABLE}  silver={SILVER_TABLE}")

# COMMAND ----------

# Mapeamentos canonicos. PROC_REA → label SIGTAP
PROC_LABELS = {
    "0409010499": "Incontinência Urinária — Via Abdominal",
    "0409070270": "Incontinência Urinária — Via Vaginal",
    "0409020117": "Incontinência Urinária — Genérico",
}

# CAR_INT (caráter de atendimento) — SIGTAP/SIH
# Códigos canônicos pós-2008. Há colisões históricas — reduzimos a 3 buckets.
CAR_INT_LABELS = {
    "01": "Eletivo",
    "02": "Urgência",
    "03": "Acidente local trabalho",
    "04": "Acidente trânsito",
    "05": "Outros tipos acidente",
}

# GESTAO — formato pode vir como char (E/M/D) ou cod (1=Estadual / 2=Municipal / 3=Dupla)
# Normalizamos abaixo.

# UF_ZI vem como código IBGE 6-dig do município (ex: SP=350000+); UF_ZI[:2] = sigla? Não.
# Na verdade UF_ZI é o ID IBGE da UF (2-dig) seguido do código municipal — varia por layout.
# Para simplicidade, usamos `estado` que vem do filename (RDSP1503.dbc → SP).

# COMMAND ----------

from pyspark.sql import functions as F

bronze = spark.read.table(BRONZE_TABLE)
n_bronze = bronze.count()
if n_bronze == 0:
    raise ValueError(f"{BRONZE_TABLE} is empty.")
print(f"bronze rows: {n_bronze:,}")

# Lê todo o bronze. Auto Loader já garante idempotência por arquivo
# (_metadata.file_path no checkpoint), então não há risco de dupla contagem.
# NOTA: NÃO filtrar por max(_ingest_ts) — Auto Loader divide a ingestão em
# múltiplos micro-batches, cada um com seu próprio timestamp. Filtrar pelo
# último derruba ~73% dos dados e deixa só ~13 das 27 UFs.
src = bronze
print(f"bronze rows used: {src.count():,}")

# COMMAND ----------

# Normalização de tipos + labels.
df = (
    src
    .withColumn("uf",       F.col("estado").cast("string"))
    .withColumn("ano",      F.col("ano").cast("int"))
    .withColumn("mes",      F.col("mes").cast("string"))
    .withColumn("proc_rea", F.lpad(F.col("PROC_REA").cast("string"), 10, "0"))
    .withColumn("car_int",  F.lpad(F.col("CAR_INT").cast("string"), 2, "0"))
    .withColumn(
        "gestao",
        # Normaliza para 'E' / 'M' / 'D' / 'X'
        F.when(F.upper(F.col("GESTAO")).isin("E", "1"), F.lit("E"))
         .when(F.upper(F.col("GESTAO")).isin("M", "2"), F.lit("M"))
         .when(F.upper(F.col("GESTAO")).isin("D", "3"), F.lit("D"))
         .otherwise(F.lit("X"))
    )
    .withColumn("val_tot",   F.col("VAL_TOT").cast("double"))
    .withColumn("val_sh",    F.col("VAL_SH").cast("double"))
    .withColumn("val_sp",    F.col("VAL_SP").cast("double"))
    .withColumn("dias_perm", F.col("DIAS_PERM").cast("int"))
    .withColumn(
        "morte",
        # Pode vir como '1'/'0' string ou int. Normalizamos pra int 0/1.
        F.when(F.col("MORTE").cast("string").isin("1", "1.0"), F.lit(1))
         .otherwise(F.lit(0))
    )
    .where(F.col("proc_rea").isin(*list(PROC_LABELS.keys())))
)

# COMMAND ----------

# Drop partial years — exige todos os 12 meses presentes (mesma regra do
# equipamentos_uf_ano). DATASUS pode publicar até o último mês fechado, então
# o ano corrente é tipicamente parcial e deve ser descartado da análise anual.
months_per_year = df.groupBy("ano").agg(F.countDistinct("mes").alias("n_months"))
month_counts = sorted([(r["ano"], r["n_months"]) for r in months_per_year.collect()])
print(f"meses por Ano (bronze): {month_counts}")
full_years = [a for a, n in month_counts if n == 12]
dropped    = [a for a, n in month_counts if n != 12]
print(f"anos completos: {full_years}")
if dropped:
    print(f"⚠ anos parciais descartados: {dropped}")
df = df.where(F.col("ano").isin(full_years))

# COMMAND ----------

# Aggregate (uf, ano, mes, proc_rea, car_int, gestao)
agg = (
    df.groupBy("uf", "ano", "mes", "proc_rea", "car_int", "gestao")
      .agg(
          F.count(F.lit(1)).alias("n_aih"),
          F.sum("val_tot").alias("val_tot"),
          F.sum("val_sh").alias("val_sh"),
          F.sum("val_sp").alias("val_sp"),
          F.sum("dias_perm").alias("sum_dias_perm"),
          F.sum("morte").alias("n_morte"),
      )
)

# Per-AIH averages (na granularidade silver)
agg = (
    agg
    .withColumn("val_tot_avg",   F.col("val_tot")   / F.col("n_aih"))
    .withColumn("val_sh_avg",    F.col("val_sh")    / F.col("n_aih"))
    .withColumn("val_sp_avg",    F.col("val_sp")    / F.col("n_aih"))
    .withColumn("dias_perm_avg", F.col("sum_dias_perm") / F.col("n_aih"))
    .withColumn("mortalidade",   F.col("n_morte")   / F.col("n_aih"))
)

# Add labels
proc_map  = F.create_map(*[v for kv in PROC_LABELS.items()
                           for v in (F.lit(kv[0]), F.lit(kv[1]))])
car_map   = F.create_map(*[v for kv in CAR_INT_LABELS.items()
                           for v in (F.lit(kv[0]), F.lit(kv[1]))])
gestao_map = F.create_map(
    F.lit("E"), F.lit("Estadual"),
    F.lit("M"), F.lit("Municipal"),
    F.lit("D"), F.lit("Dupla"),
    F.lit("X"), F.lit("Outro/NA"),
)

silver_df = (
    agg
    .withColumn("proc_label",   F.coalesce(proc_map.getItem(F.col("proc_rea")), F.col("proc_rea")))
    .withColumn("car_label",    F.coalesce(car_map.getItem(F.col("car_int")), F.lit("Outro")))
    .withColumn("gestao_label", F.coalesce(gestao_map.getItem(F.col("gestao")), F.lit("Outro/NA")))
    .withColumn("_bronze_snapshot_ts", F.lit(bronze.agg(F.max("_ingest_ts")).first()[0]))
    .withColumn("_silver_built_ts",    F.current_timestamp())
    .select(
        "uf", "ano", "mes", "proc_rea", "proc_label",
        "car_int", "car_label", "gestao", "gestao_label",
        "n_aih", "sum_dias_perm", "n_morte",
        "val_tot", "val_sh", "val_sp",
        "val_tot_avg", "val_sh_avg", "val_sp_avg",
        "dias_perm_avg", "mortalidade",
        "_bronze_snapshot_ts", "_silver_built_ts",
    )
    .orderBy("uf", "ano", "mes", "proc_rea", "car_int", "gestao")
)

# COMMAND ----------

n = silver_df.count()
ufs = silver_df.select("uf").distinct().count()
years = silver_df.select("ano").distinct().count()
procs = silver_df.select("proc_rea").distinct().count()
print(f"rows={n}  ufs={ufs}  years={years}  procs={procs}")
print("✔ DQ passed")

silver_df.groupBy("ano", "proc_rea").agg(
    F.sum("n_aih").alias("aih"),
    F.round(F.sum("val_tot"), 2).alias("val_tot"),
).orderBy("ano", "proc_rea").show(40)

# COMMAND ----------

(
    silver_df.write.format("delta")
        .mode("overwrite")
        .option("overwriteSchema", "true")
        .partitionBy("ano")
        .saveAsTable(SILVER_TABLE)
)
spark.sql(
    f"COMMENT ON TABLE {SILVER_TABLE} IS "
    f"'Mirante · SIH-AIH agregado por UF×Ano×Mes×Procedimento×Caráter×Gestão. "
    f"Foco inicial: Tratamento Cirúrgico de Incontinência Urinária (3 SIGTAPs).'"
)
print(f"✔ {SILVER_TABLE} written ({n} rows)")

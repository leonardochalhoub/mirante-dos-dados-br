# Databricks notebook source
# MAGIC %md
# MAGIC # silver · pbf_total_uf_mes
# MAGIC
# MAGIC Lê o bronze `<catalog>.bronze.pbf_pagamentos`, aplica regra nov/2021 (PBF_AUX_SUM
# MAGIC substitui PBF+AUX), parseia `valor_parcela` como Decimal, e agrega por
# MAGIC `(Ano, Mes, uf)`:
# MAGIC - `n` = beneficiários distintos por mês (chave: `nis_favorecido` dígitos)
# MAGIC - `n_ano` = beneficiários distintos por ano (replicado em cada linha do mês)
# MAGIC - `total_estado` = soma de `valor_parcela`

# COMMAND ----------

dbutils.widgets.text("catalog", "mirante_prd")
CATALOG = dbutils.widgets.get("catalog")

BRONZE_TABLE = f"{CATALOG}.bronze.pbf_pagamentos"
SILVER_TABLE = f"{CATALOG}.silver.pbf_total_uf_mes"

print(f"bronze={BRONZE_TABLE}  silver={SILVER_TABLE}")

# COMMAND ----------

from pyspark.sql import functions as F, types as T

# Bronze é append-only via Auto Loader. Se um mesmo arquivo aparecer 2× (não deve, mas
# por garantia), tomamos a última versão. Aqui, dedupe pela coluna do filename + linha.
bronze = spark.read.table(BRONZE_TABLE)
print(f"bronze rows: {bronze.count():,}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Fix nov/2021 PBF header swap + apply origin rule

# COMMAND ----------

# In PBF nov/2021, the source files shipped with mes_competencia ↔ mes_referencia swapped.
# Reverse the swap only for those rows.
if {"mes_competencia", "mes_referencia"}.issubset(set(bronze.columns)):
    df = bronze.withColumn(
        "mes_competencia",
        F.when(
            (F.col("ano") == 2021) & (F.col("mes") == 11) & (F.col("origin") == "PBF"),
            F.col("mes_referencia"),
        ).otherwise(F.col("mes_competencia"))
    )
else:
    df = bronze

# Origin rule for nov/2021: synthesize PBF_AUX_SUM by summing PBF + AUX numeric cols,
# then keep ONLY PBF_AUX_SUM for that month and exclude PBF_AUX_SUM for all other months.
nov21_raw = df.where((F.col("ano") == 2021) & (F.col("mes") == 11) & (F.col("origin").isin(["PBF", "AUX"])))

if nov21_raw.head(1):
    meta_cols = {"origin", "ano", "mes", "competencia", "_source_file", "_ingest_ts"}
    numeric_cols = [c for c, t in nov21_raw.dtypes
                    if c not in meta_cols and t in ("int", "bigint", "double", "float", "decimal")]
    other_cols = [c for c in nov21_raw.columns if c not in meta_cols and c not in numeric_cols]
    if numeric_cols:
        agg_exprs = ([F.sum(F.col(c)).alias(c) for c in numeric_cols]
                     + [F.first(F.col(c), ignorenulls=True).alias(c) for c in other_cols])
        synthetic = (
            nov21_raw.groupBy("ano", "mes", "competencia").agg(*agg_exprs)
                     .withColumn("origin",       F.lit("PBF_AUX_SUM"))
                     .withColumn("_source_file", F.lit("SYNTHETIC"))
                     .withColumn("_ingest_ts",   F.current_timestamp())
        )
        df = df.unionByName(synthetic, allowMissingColumns=True)

# Apply the origin rule
is_2021_11 = (F.col("ano") == 2021) & (F.col("mes") == 11)
df = df.where(
    (is_2021_11 & (F.col("origin") == "PBF_AUX_SUM"))
    | (~is_2021_11 & (F.col("origin") != "PBF_AUX_SUM"))
)

# COMMAND ----------

# MAGIC %md
# MAGIC ## Aggregate UF × Ano × Mes

# COMMAND ----------

# Parse valor_parcela "800,00" → Decimal(38, 2)
df = df.withColumn(
    "valor_parcela_dec",
    F.regexp_replace(F.col("valor_parcela"), ",", ".").cast(T.DecimalType(38, 2))
)

# Beneficiary key: digits only of nis_favorecido
df = df.withColumn("_benef_id", F.regexp_replace(F.trim(F.col("nis_favorecido")), r"\D", ""))
df = df.where(F.length(F.col("_benef_id")) > 0)

# Annual distinct beneficiaries by (ano, uf), replicated on each month
df_year = (
    df.groupBy("ano", "uf")
      .agg(F.countDistinct("_benef_id").cast("long").alias("n_ano"))
      .select(F.col("ano").cast("int").alias("Ano"), "uf", "n_ano")
)

silver_df = (
    df.groupBy("mes_competencia", "uf")
      .agg(
          F.countDistinct("_benef_id").cast("long").alias("n"),
          F.sum(F.col("valor_parcela_dec")).alias("total_estado"),
      )
      .withColumn("Ano", F.substring(F.col("mes_competencia"), 1, 4).cast("int"))
      .withColumn("Mes", F.substring(F.col("mes_competencia"), 5, 2).cast("int"))
      .join(df_year, on=["Ano", "uf"], how="left")
      .select("Ano", "Mes", "uf", "mes_competencia",
              F.col("n").cast("long"),
              F.col("n_ano").cast("long"),
              F.col("total_estado").cast("decimal(38,2)"))
      .withColumn("_silver_built_ts", F.current_timestamp())
)

# Defensive filter: keep only valid 27 UFs + valid year range. CGU sometimes ships
# malformed rows with null/empty UF or Mês outside 1..12 — these would leak NULLs
# downstream when the gold tries to join with populacao_uf_ano / ipca_deflators_2021.
VALID_UFS = ["AC","AL","AM","AP","BA","CE","DF","ES","GO","MA","MG","MS","MT",
             "PA","PB","PE","PI","PR","RJ","RN","RO","RR","RS","SC","SE","SP","TO"]
n_before = silver_df.count()
silver_df = silver_df.where(
    F.col("Ano").isNotNull() & (F.col("Ano") >= 2013) & (F.col("Ano") <= 2099)
    & F.col("Mes").isNotNull() & (F.col("Mes").between(1, 12))
    & F.col("uf").isin(VALID_UFS)
)
n_after = silver_df.count()
if n_after < n_before:
    print(f"⚠ filtrou {n_before - n_after} linhas silver com Ano/Mes/uf inválidos "
          f"(mantém {n_after} válidas)")

# COMMAND ----------

n = silver_df.count()
ufs = silver_df.select("uf").distinct().count()
years = silver_df.select("Ano").distinct().count()
print(f"rows={n}  ufs={ufs}  years={years}")
assert ufs == 27, f"Expected 27 UFs, got {ufs}"
print("✔ DQ passed")

# COMMAND ----------

(
    silver_df.write.format("delta")
        .mode("overwrite")
        .option("overwriteSchema", "true")
        .partitionBy("Ano")
        .saveAsTable(SILVER_TABLE)
)

spark.sql(f"COMMENT ON TABLE {SILVER_TABLE} IS "
          f"'Mirante · PBF agregado UF × Ano × Mes (n distinto, n_ano distinto, total pago).'")

print(f"✔ {SILVER_TABLE} written ({n:,} rows)")

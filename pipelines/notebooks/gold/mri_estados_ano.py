# Databricks notebook source
# MAGIC %md
# MAGIC # gold · mri_estados_ano
# MAGIC
# MAGIC Pra MRI o silver `mri_uf_ano` já está no nível UF×Ano e tem TODAS as
# MAGIC métricas que o front precisa (split SUS/Privado, per_capita scaled).
# MAGIC O gold é só uma cópia do silver com as mesmas colunas + metadado de build.
# MAGIC
# MAGIC Schema (bate com `data/gold/gold_mri_estados_ano.json`):
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

SILVER_TABLE = f"{CATALOG}.silver.mri_uf_ano"
GOLD_TABLE   = f"{CATALOG}.gold.mri_estados_ano"

print(f"silver={SILVER_TABLE}  gold={GOLD_TABLE}")

# COMMAND ----------

from pyspark.sql import functions as F

silver = spark.read.table(SILVER_TABLE)
n_silver = silver.count()
print(f"silver rows: {n_silver}")

gold_df = silver.select(
    "estado", "ano",
    "cnes_count",     "total_mri_avg",     "mri_per_capita_scaled",
    "sus_cnes_count", "sus_total_mri_avg", "sus_mri_per_capita_scaled",
    "priv_cnes_count","priv_total_mri_avg","priv_mri_per_capita_scaled",
    "populacao", "mri_per_capita_scale_pow10",
).withColumn("_gold_built_ts", F.current_timestamp()).orderBy("estado", "ano")

# DQ checks
n = gold_df.count()
ufs = gold_df.select("estado").distinct().count()
years = gold_df.select("ano").distinct().count()
print(f"gold rows={n}  ufs={ufs}  years={years}")
assert ufs == 27, f"Expected 27 UFs, got {ufs}"

# Spot-check 2025
y2025 = gold_df.where(F.col("ano") == 2025)
if y2025.head(1):
    sums = y2025.agg(
        F.sum("total_mri_avg").alias("total"),
        F.sum("sus_total_mri_avg").alias("sus"),
        F.sum("priv_total_mri_avg").alias("priv"),
        F.sum("cnes_count").alias("cnes"),
    ).first()
    print(f"2025 Brasil: total={sums['total']:.0f}  sus={sums['sus']:.0f}  "
          f"priv={sums['priv']:.0f}  cnes={sums['cnes']}")
    print("(esperado para 2025: total≈10080, sus≈4318, priv≈5762, cnes≈6744)")

# COMMAND ----------

(
    gold_df.write.format("delta")
        .mode("overwrite")
        .option("overwriteSchema", "true")
        .partitionBy("ano")
        .saveAsTable(GOLD_TABLE)
)

spark.sql(f"COMMENT ON TABLE {GOLD_TABLE} IS "
          f"'Mirante · MRI por UF × ano (gold). Schema do JSON consumido pelo front.'")

print(f"✔ {GOLD_TABLE} written ({n} rows)")

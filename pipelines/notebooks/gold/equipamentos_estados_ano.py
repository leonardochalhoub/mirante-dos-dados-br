# Databricks notebook source
# MAGIC %md
# MAGIC # gold · equipamentos_estados_ano
# MAGIC
# MAGIC Pass-through do silver `equipamentos_uf_ano` (já está na granularidade
# MAGIC UF×Ano×codequip). Front re-agrega client-side quando o usuário seleciona
# MAGIC múltiplos equipamentos.

# COMMAND ----------

dbutils.widgets.text("catalog", "mirante_prd")
CATALOG = dbutils.widgets.get("catalog")

SILVER_TABLE = f"{CATALOG}.silver.equipamentos_uf_ano"
GOLD_TABLE   = f"{CATALOG}.gold.equipamentos_estados_ano"

print(f"silver={SILVER_TABLE}  gold={GOLD_TABLE}")

# COMMAND ----------

from pyspark.sql import functions as F

silver = spark.read.table(SILVER_TABLE)
print(f"silver rows: {silver.count():,}")

gold_df = silver.select(
    "estado", "ano", "codequip", "equipment_name",
    "cnes_count",     "total_avg",     "per_capita_scaled",
    "sus_cnes_count", "sus_total_avg", "sus_per_capita_scaled",
    "priv_cnes_count","priv_total_avg","priv_per_capita_scaled",
    "populacao", "per_capita_scale_pow10",
).withColumn("_gold_built_ts", F.current_timestamp()).orderBy("estado", "ano", "codequip")

n = gold_df.count()
ufs = gold_df.select("estado").distinct().count()
years = gold_df.select("ano").distinct().count()
codequips = gold_df.select("codequip").distinct().count()
print(f"gold rows={n}  ufs={ufs}  years={years}  codequips={codequips}")

# Spot-check
print("\n2025 SP top 10 equipamentos:")
gold_df.where((F.col("ano") == 2025) & (F.col("estado") == "SP")) \
       .select("codequip", "equipment_name", "total_avg", "cnes_count") \
       .orderBy(F.desc("total_avg")).show(10, truncate=False)

mri = gold_df.where((F.col("ano") == 2025) & (F.col("codequip") == "42"))
if mri.head(1):
    sums = mri.agg(
        F.sum("total_avg").alias("total"),
        F.sum("sus_total_avg").alias("sus"),
        F.sum("priv_total_avg").alias("priv"),
        F.sum("cnes_count").alias("cnes"),
    ).first()
    print(f"\n2025 Brasil RM (codequip=42): total={sums['total']:.0f}  "
          f"sus={sums['sus']:.0f}  priv={sums['priv']:.0f}  cnes={sums['cnes']}")

(
    gold_df.write.format("delta")
        .mode("overwrite")
        .option("overwriteSchema", "true")
        .partitionBy("ano")
        .saveAsTable(GOLD_TABLE)
)
spark.sql(f"COMMENT ON TABLE {GOLD_TABLE} IS "
          f"'Mirante · CNES Equipamentos por UF × Ano × CODEQUIP (gold). "
          f"Front escolhe um ou mais equipamentos e re-agrega.'")
print(f"\n✔ {GOLD_TABLE} written ({n} rows)")

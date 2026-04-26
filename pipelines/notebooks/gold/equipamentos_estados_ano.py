# Databricks notebook source
# MAGIC %md
# MAGIC # gold · equipamentos_estados_ano
# MAGIC
# MAGIC Pass-through do silver `equipamentos_uf_ano`. Granularidade:
# MAGIC `(estado, ano, tipequip, codequip)` com `equipment_key = "tipequip:codequip"`
# MAGIC já materializado.
# MAGIC
# MAGIC O front filtra por `equipment_key` (não mais por `codequip` sozinho — esse era
# MAGIC o bug do WP #4 v1, em que `codequip=42` capturava Eletroencefalógrafo achando
# MAGIC que era Ressonância Magnética).

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
    "estado", "ano", "tipequip", "codequip",
    "equipment_key", "equipment_name", "equipment_category",
    "cnes_count",     "total_avg",     "per_capita_scaled",
    "sus_cnes_count", "sus_total_avg", "sus_per_capita_scaled",
    "priv_cnes_count","priv_total_avg","priv_per_capita_scaled",
    "populacao", "per_capita_scale_pow10",
).withColumn("_gold_built_ts", F.current_timestamp()).orderBy(
    "estado", "ano", "tipequip", "codequip",
)

n = gold_df.count()
ufs = gold_df.select("estado").distinct().count()
years = gold_df.select("ano").distinct().count()
combos = gold_df.select("equipment_key").distinct().count()
print(f"gold rows={n}  ufs={ufs}  years={years}  combos={combos}")

# Spot-check 2025 SP top 10
last_year = gold_df.agg(F.max("ano")).first()[0]
print(f"\n{last_year} SP top 10 equipamentos:")
gold_df.where((F.col("ano") == last_year) & (F.col("estado") == "SP")) \
       .select("equipment_key", "equipment_name", "total_avg", "cnes_count") \
       .orderBy(F.desc("total_avg")).show(10, truncate=False)

# Spot-check RM nacional (deve bater com OECD ~17/Mhab × 215M ≈ 3,500–4,000)
rm = gold_df.where((F.col("ano") == last_year) & (F.col("equipment_key") == "1:12"))
if rm.head(1):
    sums = rm.agg(
        F.sum("total_avg").alias("total"),
        F.sum("sus_total_avg").alias("sus"),
        F.sum("priv_total_avg").alias("priv"),
        F.sum("cnes_count").alias("cnes"),
        F.sum("populacao").alias("pop"),
    ).first()
    per_M = sums['total'] / sums['pop'] * 1_000_000 if sums['pop'] else 0
    print(f"\n{last_year} Brasil RM REAL (equipment_key=1:12 = TIPEQUIP=1, CODEQUIP=12):")
    print(f"  total={sums['total']:.0f} unidades  per_M_hab={per_M:.1f}")
    print(f"  SUS={sums['sus']:.0f}  Privado={sums['priv']:.0f}  estabs={sums['cnes']}")
    print(f"  → Esperado pela mediana OCDE (~17/Mhab): {sums['pop']/1_000_000*17:.0f} unidades")

(
    gold_df.write.format("delta")
        .mode("overwrite")
        .option("overwriteSchema", "true")
        .partitionBy("ano")
        .saveAsTable(GOLD_TABLE)
)
# Inline minimal COMMENT — full enrichment via _meta/apply_catalog_metadata.py.
spark.sql(f"COMMENT ON TABLE {GOLD_TABLE} IS "
          f"'Mirante · CNES Equipamentos UF × Ano × (TIPEQUIP, CODEQUIP) — gold "
          f"pass-through do silver com composite key (`equipment_key`) e nomes "
          f"canônicos do catálogo oficial DATASUS "
          f"(cnes2.datasus.gov.br/Mod_Ind_Equipamento.asp). Spot-check: RM (1:12) "
          f"bate ~17/Mhab (mediana OCDE). Cobre WPs #4 e #6. "
          f"Reaplicar metadata rico via job_apply_catalog_metadata.'")
print(f"\n✔ {GOLD_TABLE} written ({n} rows)")

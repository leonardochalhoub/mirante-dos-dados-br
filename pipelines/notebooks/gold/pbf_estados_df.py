# Databricks notebook source
# MAGIC %md
# MAGIC # gold · pbf_estados_df
# MAGIC
# MAGIC Junta `silver.pbf_total_uf_mes` (PBF) com as dimensões compartilhadas
# MAGIC `silver.populacao_uf_ano` e `silver.ipca_deflators_2021` pra produzir o panel
# MAGIC final UF × Ano que o front consome.
# MAGIC
# MAGIC Schema (bate com `data/gold/gold_pbf_estados_df.json`):
# MAGIC ```
# MAGIC Ano int  uf string  n_benef long  valor_nominal double  valor_2021 double
# MAGIC populacao long  pbfPerBenef double  pbfPerCapita double
# MAGIC ```

# COMMAND ----------

dbutils.widgets.text("catalog", "mirante_prd")
CATALOG = dbutils.widgets.get("catalog")

SILVER_PBF       = f"{CATALOG}.silver.pbf_total_uf_mes"
SILVER_POPULACAO = f"{CATALOG}.silver.populacao_uf_ano"
SILVER_DEFLATORS = f"{CATALOG}.silver.ipca_deflators_2021"
GOLD_TABLE       = f"{CATALOG}.gold.pbf_estados_df"

print(f"silver_pbf={SILVER_PBF}")
print(f"silver_populacao={SILVER_POPULACAO}")
print(f"silver_deflators={SILVER_DEFLATORS}")
print(f"gold={GOLD_TABLE}")

# COMMAND ----------

from pyspark.sql import functions as F

silver = spark.read.table(SILVER_PBF)
pop    = spark.read.table(SILVER_POPULACAO).select("Ano", "uf", "populacao")
defl   = spark.read.table(SILVER_DEFLATORS).select("Ano", "deflator_to_2021")

print(f"silver_pbf rows={silver.count():,}  populacao rows={pop.count()}  deflators rows={defl.count()}")

# ─── Drop partial years (must have all 12 competency months) ────────────────
# CGU publica mensalmente acumulando, então o ano corrente sempre aparece com 1-N
# meses até dezembro. Mantemos somente Anos com 12 meses distintos em silver.
months_per_year = (
    silver.groupBy("Ano").agg(F.countDistinct("Mes").alias("n_months"))
)
full_years = [r["Ano"] for r in months_per_year.where(F.col("n_months") == 12).collect()]
all_years  = sorted([r["Ano"] for r in months_per_year.collect()])
dropped    = sorted(set(all_years) - set(full_years))
print(f"meses por Ano: {sorted([(r['Ano'], r['n_months']) for r in months_per_year.collect()])}")
print(f"anos completos (12 meses): {sorted(full_years)}")
if dropped:
    print(f"⚠ anos parciais descartados do gold: {dropped}")
silver = silver.where(F.col("Ano").isin(full_years))

# ─── Diagnostics: detect duplicates in dim tables (would multiply gold rows) ──
print("\n--- DUPLICATE DETECTION ---")

dup_pop = pop.groupBy("Ano", "uf").count().where(F.col("count") > 1)
n_dup_pop = dup_pop.count()
print(f"populacao_uf_ano: rows duplicated by (Ano, uf): {n_dup_pop}")
if n_dup_pop > 0:
    dup_pop.orderBy("Ano", "uf").show(20, truncate=False)

dup_defl = defl.groupBy("Ano").count().where(F.col("count") > 1)
n_dup_defl = dup_defl.count()
print(f"ipca_deflators_2021: rows duplicated by Ano: {n_dup_defl}")
if n_dup_defl > 0:
    dup_defl.orderBy("Ano").show(20, truncate=False)

dup_silver_naano = silver.groupBy("Ano", "uf").agg(F.countDistinct("n_ano").alias("distinct_n_ano")).where(F.col("distinct_n_ano") > 1)
n_dup_naano = dup_silver_naano.count()
print(f"silver pbf_total_uf_mes: (Ano, uf) groups with multiple distinct n_ano: {n_dup_naano}")
if n_dup_naano > 0:
    dup_silver_naano.orderBy("Ano", "uf").show(20, truncate=False)

# Defensive deduplication if any dim was bloated (silver populacao should be unique
# by construction; if not, take any one row per (Ano, uf))
if n_dup_pop > 0:
    print(f"⚠ collapsing pop to 1 row per (Ano, uf) via min")
    pop = pop.groupBy("Ano", "uf").agg(F.min("populacao").alias("populacao"))
if n_dup_defl > 0:
    print(f"⚠ collapsing defl to 1 row per Ano via min")
    defl = defl.groupBy("Ano").agg(F.min("deflator_to_2021").alias("deflator_to_2021"))

# COMMAND ----------

# Aggregate UF×Ano values from silver (which is UF×Ano×Mes)
valores = (
    silver.groupBy("Ano", "uf")
          .agg((F.sum("total_estado") / F.lit(1e9)).cast("double").alias("valor_nominal"))
)
# silver.n_ano is now guaranteed unique per (Ano, uf) since silver computes it on
# competency year. distinct gives 1 row per (Ano, uf).
benef = (
    silver.select("Ano", "uf", "n_ano").distinct()
          .withColumnRenamed("n_ano", "n_benef")
          .withColumn("n_benef", F.col("n_benef").cast("long"))
)

df = (
    valores.join(benef, on=["Ano", "uf"], how="left")
           .join(pop,   on=["Ano", "uf"], how="left")
           .join(defl,  on=["Ano"],       how="left")
)

df = df.withColumn("valor_2021",   F.col("valor_nominal") * F.col("deflator_to_2021"))
df = df.withColumn("pbfPerBenef",  (F.col("valor_2021") * F.lit(1e9)) / F.col("n_benef"))
df = df.withColumn("pbfPerCapita", (F.col("valor_2021") * F.lit(1e9)) / F.col("populacao"))

gold_df = df.select(
    "Ano", "uf",
    F.col("n_benef").cast("long").alias("n_benef"),
    F.col("valor_nominal").cast("double").alias("valor_nominal"),
    F.col("valor_2021").cast("double").alias("valor_2021"),
    F.col("populacao").cast("long").alias("populacao"),
    F.col("pbfPerBenef").cast("double").alias("pbfPerBenef"),
    F.col("pbfPerCapita").cast("double").alias("pbfPerCapita"),
).withColumn("_gold_built_ts", F.current_timestamp()).orderBy("Ano", "uf")

# COMMAND ----------

n = gold_df.count()
bad_filter = (
    F.col("valor_nominal").isNull() | F.col("valor_2021").isNull()
    | F.col("populacao").isNull() | F.col("n_benef").isNull()
)
n_bad = gold_df.where(bad_filter).count()
print(f"gold rows={n}  rows with NULL values={n_bad}")

if n_bad > 0:
    print(f"⚠ Diagnostic — first {min(n_bad, 20)} rows with NULL:")
    gold_df.where(bad_filter).select(
        "Ano", "uf", "n_benef", "valor_nominal", "valor_2021", "populacao"
    ).show(20, truncate=False)

    # Drop bad rows (typically 1 edge-case row from PBF having data outside dim coverage).
    # Pipeline continues with the clean subset.
    gold_df = gold_df.where(~bad_filter)
    n_after = gold_df.count()
    print(f"After dropping NULL rows: {n_after} clean rows (was {n})")
else:
    print("✔ DQ passed")

# Spot-check 2025 if present
y2025 = gold_df.where(F.col("Ano") == 2025)
if y2025.head(1):
    sums = y2025.agg(
        F.sum("n_benef").alias("benef"),
        F.sum("valor_2021").alias("v2021"),
        F.sum("populacao").alias("pop"),
    ).first()
    if sums and sums["benef"] and sums["pop"]:
        per_benef  = (sums["v2021"] * 1e9) / sums["benef"]
        per_capita = (sums["v2021"] * 1e9) / sums["pop"]
        print(f"2025 Brasil: per_benef=R${per_benef:.2f}  per_capita=R${per_capita:.2f}")
        print("(esperado: per_benef≈5825.32  per_capita≈608.33)")

# COMMAND ----------

(
    gold_df.write.format("delta")
        .mode("overwrite")
        .option("overwriteSchema", "true")
        .partitionBy("Ano")
        .saveAsTable(GOLD_TABLE)
)

spark.sql(f"COMMENT ON TABLE {GOLD_TABLE} IS "
          f"'Mirante · PBF UF × Ano (gold). Schema do JSON consumido pelo front.'")

print(f"✔ {GOLD_TABLE} written ({n} rows)")

# Databricks notebook source
# MAGIC %md
# MAGIC # silver · finops_daily_spend
# MAGIC
# MAGIC FinOps vertical — ledger diário por (data × produto × workload-class).
# MAGIC Diferente de `finops_run_costs`, esse silver inclui **todos os custos**
# MAGIC (não só os tagueados a job runs): SQL warehouses, NETWORKING (compute serverless
# MAGIC overhead), DEFAULT_STORAGE, INTERACTIVE clusters, DLT, etc.
# MAGIC
# MAGIC Workload-class (atribuição de custo):
# MAGIC - **chargeable**: workloads que rodam código do usuário (JOBS, SQL, INTERACTIVE, DLT)
# MAGIC - **overhead**:   custos de plataforma sem run_id (NETWORKING, DEFAULT_STORAGE, PREDICTIVE_OPTIMIZATION)
# MAGIC
# MAGIC Grão: 1 linha por `(usage_date, product, workload_class, is_serverless)`.

# COMMAND ----------

dbutils.widgets.text("catalog", "mirante_prd")
CATALOG = dbutils.widgets.get("catalog")

SILVER_TABLE = f"{CATALOG}.silver.finops_daily_spend"
print(f"silver={SILVER_TABLE}")

# COMMAND ----------

from pyspark.sql import functions as F

priced = spark.sql("""
  SELECT
    u.usage_date,
    u.billing_origin_product                    AS product,
    u.product_features.is_serverless            AS is_serverless,
    u.product_features.is_photon                AS is_photon,
    u.usage_metadata.job_run_id                 AS run_id,
    u.usage_quantity                            AS dbus,
    u.usage_quantity * lp.pricing.default       AS cost_usd
  FROM system.billing.usage u
  LEFT JOIN system.billing.list_prices lp
    ON  u.sku_name        = lp.sku_name
    AND u.cloud           = lp.cloud
    AND u.usage_unit      = lp.usage_unit
    AND u.usage_start_time >= lp.price_start_time
    AND (lp.price_end_time IS NULL OR u.usage_start_time < lp.price_end_time)
""")

# workload_class:
#   - "chargeable" se rodando código do usuário (JOBS / SQL / INTERACTIVE / DLT)
#   - "overhead" caso contrário (NETWORKING / DEFAULT_STORAGE / PREDICTIVE_OPTIMIZATION)
df = priced.withColumn(
    "workload_class",
    F.when(F.col("product").isin("JOBS", "SQL", "INTERACTIVE", "DLT"), F.lit("chargeable"))
     .otherwise(F.lit("overhead")),
)

silver_df = (
    df.groupBy("usage_date", "product", "workload_class", "is_serverless")
      .agg(
          F.bool_or("is_photon").alias("is_photon_any"),
          F.count("*").cast("long").alias("n_records"),
          F.countDistinct("run_id").cast("long").alias("n_runs"),
          F.round(F.sum("dbus"), 6).alias("dbus"),
          F.round(F.sum("cost_usd"), 6).alias("cost_usd"),
      )
      .withColumn("_silver_built_ts", F.current_timestamp())
      .orderBy("usage_date", "product", "workload_class")
)

n = silver_df.count()
days = silver_df.select("usage_date").distinct().count()
total = silver_df.agg(F.sum("cost_usd")).first()[0] or 0.0
print(f"rows={n}  days={days}  total_cost_usd={total:.4f}")
assert n > 0, "system.billing.usage parece vazio"

# COMMAND ----------

(
    silver_df.write.format("delta")
        .mode("overwrite")
        .option("overwriteSchema", "true")
        .saveAsTable(SILVER_TABLE)
)

spark.sql(f"COMMENT ON TABLE {SILVER_TABLE} IS "
          f"'Mirante FinOps · spend diário por produto × workload-class. "
          f"workload_class ∈ {{chargeable, overhead}} divide custo de execução de "
          f"código (JOBS/SQL/INTERACTIVE/DLT) vs custo de plataforma "
          f"(NETWORKING/DEFAULT_STORAGE/PREDICTIVE_OPTIMIZATION). "
          f"Grão: (usage_date, product, workload_class, is_serverless). "
          f"Bronze: system.billing.usage + system.billing.list_prices.'")

for col, desc in [
    ("usage_date",     "Data do uso (UTC, partição natural de system.billing.usage)"),
    ("product",        "billing_origin_product: JOBS, SQL, INTERACTIVE, DLT, NETWORKING, DEFAULT_STORAGE, PREDICTIVE_OPTIMIZATION, ..."),
    ("workload_class", "chargeable (JOBS/SQL/INTERACTIVE/DLT) vs overhead (NETWORKING/STORAGE/PRED_OPT)"),
    ("is_serverless",  "TRUE se compute serverless"),
    ("is_photon_any",  "TRUE se ao menos um record do bucket usou Photon"),
    ("n_records",      "Contagem de billing records no bucket"),
    ("n_runs",         "Contagem distinta de job_run_id (NULL inclusive) — cardinalidade de runs neste bucket"),
    ("dbus",           "DBUs consumidas no bucket"),
    ("cost_usd",       "Custo USD = Σ DBU × list_price"),
]:
    spark.sql(f"ALTER TABLE {SILVER_TABLE} ALTER COLUMN {col} COMMENT '{desc}'")

for k, v in [
    ("layer",  "silver"),
    ("domain", "finops"),
    ("source", "system.billing"),
    ("grain",  "day_product_class"),
    ("pii",    "false"),
]:
    spark.sql(f"ALTER TABLE {SILVER_TABLE} SET TAGS ('{k}'='{v}')")

print(f"✔ {SILVER_TABLE} written ({n} rows)")

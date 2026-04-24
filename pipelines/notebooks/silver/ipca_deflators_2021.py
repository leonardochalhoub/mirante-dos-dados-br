# Databricks notebook source
# MAGIC %md
# MAGIC # silver · ipca_deflators_2021
# MAGIC
# MAGIC Lê snapshot mais recente de `<catalog>.bronze.bcb_ipca_raw`, calcula índice
# MAGIC cumulativo via cumprod (log-sum-exp pra estabilidade numérica), normaliza pra
# MAGIC Dez/2021 = 1.0, e produz panel `Ano × deflator_to_2021`.

# COMMAND ----------

dbutils.widgets.text("catalog",  "mirante_prd")
dbutils.widgets.text("year_min", "2013")
dbutils.widgets.text("year_max", "2026")

CATALOG  = dbutils.widgets.get("catalog")
YEAR_MIN = int(dbutils.widgets.get("year_min"))
YEAR_MAX = int(dbutils.widgets.get("year_max"))

BRONZE_TABLE = f"{CATALOG}.bronze.bcb_ipca_raw"
SILVER_TABLE = f"{CATALOG}.silver.ipca_deflators_2021"

print(f"bronze={BRONZE_TABLE}  silver={SILVER_TABLE}  range=[{YEAR_MIN}..{YEAR_MAX}]")

# COMMAND ----------

from pyspark.sql import functions as F, Window

# Read latest bronze snapshot (one BCB refresh = many IPCA-month rows; we want only the latest set)
bronze = spark.read.table(BRONZE_TABLE)
latest_ts = bronze.agg(F.max("_ingest_ts")).first()[0]
if latest_ts is None:
    raise ValueError(f"{BRONZE_TABLE} is empty — run the bronze task first.")

src = bronze.where(F.col("_ingest_ts") == latest_ts)
print(f"Reading bronze snapshot from _ingest_ts={latest_ts} ({src.count()} rows)")

# COMMAND ----------

df = (
    src.withColumn("dt",       F.to_date("data", "dd/MM/yyyy"))
       .withColumn("ipca_pct", F.regexp_replace(F.col("valor"), ",", ".").cast("double"))
       .where(F.col("dt").isNotNull())
       .withColumn("year",     F.year("dt").cast("int"))
       .withColumn("month",    F.month("dt").cast("int"))
       .withColumn("factor",   F.lit(1.0) + F.col("ipca_pct") / F.lit(100.0))
)

# Cumulative product via log-sum-exp (numerically stable)
w = (Window.partitionBy(F.lit(1)).orderBy(F.col("dt").asc())
            .rowsBetween(Window.unboundedPreceding, Window.currentRow))
df = (
    df.withColumn("log_factor", F.log("factor"))
      .withColumn("cum_index",  F.exp(F.sum("log_factor").over(w)))
)

df_dec = df.where(F.col("month") == F.lit(12)).select(
    F.col("year").alias("Ano"),
    F.col("cum_index").alias("index_dec"),
)

idx_2021_row = df_dec.where(F.col("Ano") == F.lit(2021)).select("index_dec").first()
if not idx_2021_row:
    raise ValueError("BCB IPCA series doesn't contain December 2021 yet.")
idx_2021 = float(idx_2021_row[0])

df_dec = df_dec.withColumn("deflator_to_2021", F.lit(idx_2021) / F.col("index_dec"))

# Build complete year grid + forward-fill missing years
years_grid = spark.createDataFrame([(y,) for y in range(YEAR_MIN, YEAR_MAX + 1)], schema="Ano int")
panel = years_grid.join(df_dec.select("Ano", "deflator_to_2021"), on="Ano", how="left")
w_ff = (Window.partitionBy(F.lit(1)).orderBy(F.col("Ano").asc())
              .rowsBetween(Window.unboundedPreceding, Window.currentRow))
panel = panel.withColumn("deflator_to_2021",
                         F.last("deflator_to_2021", ignorenulls=True).over(w_ff))

silver_df = (
    panel
    .withColumn("_bronze_snapshot_ts", F.lit(latest_ts))
    .withColumn("_silver_built_ts",    F.current_timestamp())
    .orderBy("Ano")
)

# COMMAND ----------

n = silver_df.count()
n_bad = silver_df.where(F.col("deflator_to_2021").isNull() | (F.col("deflator_to_2021") <= 0)).count()
print(f"rows={n}  bad_deflator={n_bad}")
assert n_bad == 0, f"Got {n_bad} rows with bad deflator"
print("✔ DQ passed")

# COMMAND ----------

(
    silver_df.write.format("delta")
        .mode("overwrite")
        .option("overwriteSchema", "true")
        .saveAsTable(SILVER_TABLE)
)

spark.sql(f"COMMENT ON TABLE {SILVER_TABLE} IS "
          f"'Mirante · IPCA deflators (Dez/2021 = 1.0). Source: BCB SGS 433.'")

print(f"✔ {SILVER_TABLE} written ({n} rows)")
spark.read.table(SILVER_TABLE).show()

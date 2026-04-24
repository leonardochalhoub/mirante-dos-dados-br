# Databricks notebook source
# MAGIC %md
# MAGIC # ipca_deflators_2021 · 02 · DLT
# MAGIC
# MAGIC ```
# MAGIC mirante.bronze.bcb_ipca_raw         ← raw BCB SGS 433 JSON
# MAGIC mirante.silver.ipca_deflators_2021  ← Ano × deflator (Dez/2021 = 1.0)
# MAGIC ```
# MAGIC
# MAGIC ## Lógica
# MAGIC ```
# MAGIC factor[m]      = 1 + ipca_pct[m]/100
# MAGIC cum_index[m]   = ∏ factor[1..m]               (cumulative product, log-sum-exp)
# MAGIC index_dec[y]   = cum_index do dezembro de y
# MAGIC deflator[y]    = index_dec[2021] / index_dec[y]
# MAGIC ```
# MAGIC
# MAGIC Para anos sem dezembro publicado (corrente / futuro): forward-fill do último deflator conhecido.
# MAGIC
# MAGIC ## Parâmetros
# MAGIC
# MAGIC | chave | default | descrição |
# MAGIC | --- | --- | --- |
# MAGIC | `mirante.ipca.raw_path`  | `/Volumes/mirante/bronze/raw/bcb/ipca_mensal.json` | onde o JSON foi gravado |
# MAGIC | `mirante.ipca.year_min`  | `2013` | primeiro ano do panel |
# MAGIC | `mirante.ipca.year_max`  | `2026` | último ano (forward-fill se IPCA-dez não publicado) |

# COMMAND ----------

import dlt
from pyspark.sql import functions as F, Window

RAW_PATH = spark.conf.get("mirante.ipca.raw_path", "/Volumes/mirante/bronze/raw/bcb/ipca_mensal.json")
YEAR_MIN = int(spark.conf.get("mirante.ipca.year_min", "2013"))
YEAR_MAX = int(spark.conf.get("mirante.ipca.year_max", "2026"))

print(f"raw={RAW_PATH}  year_min={YEAR_MIN}  year_max={YEAR_MAX}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Bronze · `mirante.bronze.bcb_ipca_raw`

# COMMAND ----------

@dlt.table(
    name="mirante.bronze.bcb_ipca_raw",
    comment="Raw payload from BCB SGS série 433 (IPCA variação mensal %).",
    table_properties={"quality": "bronze"},
)
def bcb_ipca_raw():
    # JSON file is a top-level array: spark.read.json reads each row of the array as a record
    return spark.read.option("multiline", "true").json(RAW_PATH)

# COMMAND ----------

# MAGIC %md
# MAGIC ## Silver · `mirante.silver.ipca_deflators_2021`

# COMMAND ----------

@dlt.table(
    name="mirante.silver.ipca_deflators_2021",
    comment="Deflatores anuais de IPCA para Dez/2021 = 1.0. Construído via cumprod do "
            "índice mensal (BCB série 433); forward-fill quando dezembro do ano não publicado.",
    table_properties={"quality": "silver"},
)
@dlt.expect_or_drop("ano_no_intervalo",  "Ano BETWEEN 2000 AND 2100")
@dlt.expect_or_drop("deflator_positivo", "deflator_to_2021 > 0")
def ipca_deflators_2021():
    src = dlt.read("mirante.bronze.bcb_ipca_raw")

    df = (
        src.withColumn("dt",       F.to_date("data", "dd/MM/yyyy"))
           .withColumn("ipca_pct", F.regexp_replace(F.col("valor"), ",", ".").cast("double"))
           .where(F.col("dt").isNotNull())
           .withColumn("year",     F.year("dt").cast("int"))
           .withColumn("month",    F.month("dt").cast("int"))
           .withColumn("factor",   F.lit(1.0) + F.col("ipca_pct") / F.lit(100.0))
    )

    # Cumulative log-sum then exp = numerically stable cumulative product
    w = (Window.partitionBy(F.lit(1)).orderBy(F.col("dt").asc())
                .rowsBetween(Window.unboundedPreceding, Window.currentRow))
    df = df.withColumn("log_factor", F.log("factor"))\
           .withColumn("cum_index",  F.exp(F.sum("log_factor").over(w)))

    df_dec = df.where(F.col("month") == F.lit(12)).select(
        F.col("year").alias("Ano"),
        F.col("cum_index").alias("index_dec"),
    )

    # Normalize so Dec/2021 = 1.0 → deflator_to_2021 = index_dec_2021 / index_dec_year
    idx_2021_row = df_dec.where(F.col("Ano") == F.lit(2021)).select("index_dec").first()
    if not idx_2021_row:
        raise ValueError("BCB IPCA series doesn't contain December 2021 yet. Cannot build base.")
    idx_2021 = float(idx_2021_row[0])

    df_dec = df_dec.withColumn("deflator_to_2021", F.lit(idx_2021) / F.col("index_dec"))

    # Build complete year grid [YEAR_MIN..YEAR_MAX] and forward-fill
    years_grid = spark.createDataFrame([(y,) for y in range(YEAR_MIN, YEAR_MAX + 1)], schema="Ano int")
    panel = years_grid.join(df_dec.select("Ano", "deflator_to_2021"), on="Ano", how="left")

    w_ff = (Window.partitionBy(F.lit(1)).orderBy(F.col("Ano").asc())
                  .rowsBetween(Window.unboundedPreceding, Window.currentRow))
    panel = panel.withColumn("deflator_to_2021",
                             F.last("deflator_to_2021", ignorenulls=True).over(w_ff))

    return panel.orderBy("Ano")

# Databricks notebook source
# MAGIC %md
# MAGIC # bronze · bcb_ipca_raw
# MAGIC
# MAGIC Auto Loader → Delta append. Cada arquivo BCB IPCA novo (1× por mês) vira N linhas
# MAGIC novas — uma por ponto mensal da série 433. `_ingest_ts` permite recuperar snapshot.

# COMMAND ----------

dbutils.widgets.text("catalog", "mirante_prd")
CATALOG = dbutils.widgets.get("catalog")

SOURCE_DIR     = f"/Volumes/{CATALOG}/bronze/raw/bcb"
BRONZE_TABLE   = f"{CATALOG}.bronze.bcb_ipca_raw"
CHECKPOINT_LOC = f"/Volumes/{CATALOG}/bronze/_autoloader/bcb_ipca_raw/_checkpoint"
SCHEMA_LOC     = f"/Volumes/{CATALOG}/bronze/_autoloader/bcb_ipca_raw/_schema"

print(f"source={SOURCE_DIR}  target={BRONZE_TABLE}")

# COMMAND ----------

from pyspark.sql import functions as F

stream = (
    spark.readStream
        .format("cloudFiles")
        .option("cloudFiles.format", "json")
        .option("cloudFiles.inferColumnTypes", "true")
        .option("cloudFiles.schemaLocation", SCHEMA_LOC)
        .option("multiLine", "true")
        .load(SOURCE_DIR)
        .withColumn("_ingest_ts",   F.current_timestamp())
        .withColumn("_source_file", F.col("_metadata.file_path"))
)

query = (
    stream.writeStream
        .format("delta")
        .option("checkpointLocation", CHECKPOINT_LOC)
        .option("mergeSchema", "true")
        .trigger(availableNow=True)
        .toTable(BRONZE_TABLE)
)
query.awaitTermination()

# COMMAND ----------

n = spark.read.table(BRONZE_TABLE).count()
print(f"✔ {BRONZE_TABLE}: {n} rows total")

# Databricks notebook source
# MAGIC %md
# MAGIC # bronze · ibge_populacao_raw
# MAGIC
# MAGIC Auto Loader: monitora o Volume `/Volumes/<catalog>/bronze/raw/ibge/` e faz
# MAGIC append no Delta `<catalog>.bronze.ibge_populacao_raw` para cada novo arquivo.
# MAGIC Preserva o payload IBGE completo (id, variável, unidade, resultados[]...).
# MAGIC
# MAGIC - Modo: structured streaming, `trigger(availableNow=True)` (processa o que tem e para)
# MAGIC - Idempotência: checkpoint do Auto Loader marca arquivos já processados
# MAGIC - History: cada refresh = N novas linhas (`_ingest_ts` permite recuperar snapshot por data)

# COMMAND ----------

dbutils.widgets.text("catalog", "mirante_prd")
CATALOG = dbutils.widgets.get("catalog")

SOURCE_DIR     = f"/Volumes/{CATALOG}/bronze/raw/ibge"
BRONZE_TABLE   = f"{CATALOG}.bronze.ibge_populacao_raw"
CHECKPOINT_LOC = f"/Volumes/{CATALOG}/bronze/_autoloader/ibge_populacao_raw/_checkpoint"
SCHEMA_LOC     = f"/Volumes/{CATALOG}/bronze/_autoloader/ibge_populacao_raw/_schema"

print(f"source     = {SOURCE_DIR}")
print(f"target     = {BRONZE_TABLE}")
print(f"checkpoint = {CHECKPOINT_LOC}")

# COMMAND ----------

from pyspark.sql import functions as F

stream = (
    spark.readStream
        .format("cloudFiles")
        .option("cloudFiles.format", "json")
        .option("cloudFiles.inferColumnTypes", "true")
        .option("cloudFiles.schemaLocation", SCHEMA_LOC)
        .option("cloudFiles.schemaEvolutionMode", "addNewColumns")
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
spark.read.table(BRONZE_TABLE).select("_ingest_ts", "_source_file").orderBy(F.desc("_ingest_ts")).show(5, truncate=False)

# Databricks notebook source
# MAGIC %md
# MAGIC # bronze · rais_vinculos
# MAGIC
# MAGIC Pipeline em 2 estágios:
# MAGIC 1. **Extract**: descomprime `.7z` → `.txt` (delimitado por `;`, latin-1)
# MAGIC 2. **Auto Loader CSV → Delta append**, mesma estratégia híbrida do
# MAGIC    `bronze_cnes_equipamentos`: BATCH na primeira carga, Auto Loader
# MAGIC    incremental nas execuções seguintes.
# MAGIC
# MAGIC Schema baseado no dicionário PDET/RAIS Vínculos Públicos.
# MAGIC ~62 GB brutos por biênio, ~136M linhas — base do estudo replicado
# MAGIC (Chalhoub 2023, monografia UFRJ MBA Eng. Dados, não publicada).

# COMMAND ----------

# MAGIC %pip install --quiet py7zr
# MAGIC dbutils.library.restartPython()

# COMMAND ----------

dbutils.widgets.text("catalog",        "mirante_prd")
dbutils.widgets.text("zips_dir",       "/Volumes/mirante_prd/bronze/raw/mte/rais")
dbutils.widgets.text("txt_extracted",  "/Volumes/mirante_prd/bronze/raw/mte/rais_txt_extracted")
dbutils.widgets.text("force_reconvert","false")

CATALOG          = dbutils.widgets.get("catalog")
ZIPS_DIR         = dbutils.widgets.get("zips_dir")
TXT_EXTRACTED    = dbutils.widgets.get("txt_extracted")
FORCE_RECONVERT  = dbutils.widgets.get("force_reconvert").lower() in ("true","1","yes")

BRONZE_TABLE   = f"{CATALOG}.bronze.rais_vinculos"
CHECKPOINT_LOC = f"/Volumes/{CATALOG}/bronze/raw/_autoloader/rais_vinculos/_checkpoint"
SCHEMA_LOC     = f"/Volumes/{CATALOG}/bronze/raw/_autoloader/rais_vinculos/_schema"

print(f"zips_dir={ZIPS_DIR}  txt_extracted={TXT_EXTRACTED}  target={BRONZE_TABLE}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 1 — extrair `.7z` → `.txt` (idempotente)

# COMMAND ----------

import re
from pathlib import Path
import py7zr

extracted = 0; skipped = 0
Path(TXT_EXTRACTED).mkdir(parents=True, exist_ok=True)
zips = sorted(Path(ZIPS_DIR).glob("*.7z"))
print(f"7z encontrados: {len(zips)}")

for zp in zips:
    # Marcador por arquivo: <stem>.done — se existe, pulamos
    marker = Path(TXT_EXTRACTED) / f"_{zp.stem}.done"
    if marker.exists() and not FORCE_RECONVERT:
        skipped += 1; continue
    try:
        with py7zr.SevenZipFile(zp, mode='r') as z:
            z.extractall(path=TXT_EXTRACTED)
        marker.write_text("ok")
        extracted += 1
    except Exception as e:
        print(f"  ✗ {zp.name}: {type(e).__name__}: {str(e)[:120]}")

txts = sorted(Path(TXT_EXTRACTED).glob("*.txt"))
print(f"Extraídos {extracted} novos (skipped {skipped}). Total .txt: {len(txts)}")

if not txts:
    print("⚠ Nenhum .txt processável. Verifique ingest_mte_rais.")
    dbutils.notebook.exit("SKIPPED: no .txt to process")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 2 — Auto Loader CSV → Delta append (modo híbrido)

# COMMAND ----------

from pyspark.sql import functions as F

table_exists = spark.catalog.tableExists(BRONZE_TABLE)
existing_rows = spark.read.table(BRONZE_TABLE).count() if table_exists else 0
checkpoint_initialized = False
try: checkpoint_initialized = bool(dbutils.fs.ls(CHECKPOINT_LOC))
except Exception: pass

use_batch = (not table_exists) or (existing_rows == 0) or (not checkpoint_initialized) or FORCE_RECONVERT

if FORCE_RECONVERT and table_exists:
    print("⚠ FORCE_RECONVERT=true → drop bronze + checkpoint")
    spark.sql(f"DROP TABLE IF EXISTS {BRONZE_TABLE}")
    try: dbutils.fs.rm(CHECKPOINT_LOC, True); dbutils.fs.rm(SCHEMA_LOC, True)
    except Exception: pass

if use_batch:
    print(f"▸ MODO BATCH — table_exists={table_exists} rows={existing_rows:,}")
    df = (
        spark.read
            .option("header", "true")
            .option("sep", ";")
            .option("encoding", "latin1")
            .option("inferSchema", "false")  # tudo string no bronze; tipagem no silver
            .csv(TXT_EXTRACTED)
            .withColumn("_source_file", F.col("_metadata.file_path"))
            .withColumn("_ingest_ts",   F.current_timestamp())
    )
    (df.write.format("delta").mode("overwrite")
        .option("overwriteSchema","true")
        .partitionBy("ano")
        .saveAsTable(BRONZE_TABLE))
    # priming Auto Loader checkpoint
    print("  primando checkpoint Auto Loader…")
    init = (
        spark.readStream.format("cloudFiles")
            .option("cloudFiles.format","csv")
            .option("cloudFiles.schemaLocation", SCHEMA_LOC)
            .option("cloudFiles.includeExistingFiles","false")
            .option("header","true").option("sep",";").option("encoding","latin1")
            .load(TXT_EXTRACTED)
            .withColumn("_source_file", F.col("_metadata.file_path"))
            .withColumn("_ingest_ts",   F.current_timestamp())
    )
    (init.writeStream.format("delta")
        .option("checkpointLocation", CHECKPOINT_LOC)
        .option("mergeSchema","true")
        .partitionBy("ano")
        .trigger(availableNow=True)
        .toTable(BRONZE_TABLE).awaitTermination())
else:
    print(f"▸ MODO AUTO LOADER — table_exists=True rows={existing_rows:,}")
    stream = (
        spark.readStream.format("cloudFiles")
            .option("cloudFiles.format","csv")
            .option("cloudFiles.schemaLocation", SCHEMA_LOC)
            .option("cloudFiles.schemaEvolutionMode","addNewColumns")
            .option("header","true").option("sep",";").option("encoding","latin1")
            .load(TXT_EXTRACTED)
            .withColumn("_source_file", F.col("_metadata.file_path"))
            .withColumn("_ingest_ts",   F.current_timestamp())
    )
    (stream.writeStream.format("delta")
        .option("checkpointLocation", CHECKPOINT_LOC)
        .option("mergeSchema","true")
        .partitionBy("ano")
        .trigger(availableNow=True)
        .toTable(BRONZE_TABLE).awaitTermination())

# COMMAND ----------

n = spark.read.table(BRONZE_TABLE).count()
print(f"✔ {BRONZE_TABLE}: {n:,} rows total")
spark.read.table(BRONZE_TABLE).groupBy("ano").count().orderBy("ano").show(30)

# Databricks notebook source
# MAGIC %md
# MAGIC # bronze · emendas_pagamentos
# MAGIC
# MAGIC Mesma esteira do PBF: extrai ZIPs do CGU em CSVs, Auto Loader → Delta append.
# MAGIC Cada CSV vira N rows na bronze, com metadados (ano, _source_file, _ingest_ts).
# MAGIC Headers normalizados pra ASCII snake_case (Delta não aceita acentos/espaços).

# COMMAND ----------

dbutils.widgets.text("catalog",       "mirante_prd")
dbutils.widgets.text("zips_dir",      "/Volumes/mirante_prd/bronze/raw/cgu/emendas")
dbutils.widgets.text("csv_extracted", "/Volumes/mirante_prd/bronze/raw/cgu/emendas_csv_extracted")

CATALOG       = dbutils.widgets.get("catalog")
ZIPS_DIR      = dbutils.widgets.get("zips_dir")
CSV_EXTRACTED = dbutils.widgets.get("csv_extracted")

BRONZE_TABLE   = f"{CATALOG}.bronze.emendas_pagamentos"
CHECKPOINT_LOC = f"/Volumes/{CATALOG}/bronze/raw/_autoloader/emendas_pagamentos/_checkpoint"
SCHEMA_LOC     = f"/Volumes/{CATALOG}/bronze/raw/_autoloader/emendas_pagamentos/_schema"

print(f"zips_dir={ZIPS_DIR}  csv_extracted={CSV_EXTRACTED}  target={BRONZE_TABLE}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 1 — extrair ZIPs novos para CSVs (idempotente)

# COMMAND ----------

import re
import zipfile
from pathlib import Path
from typing import Optional

RE_YEAR = re.compile(r"(?P<year>20\d{2})", re.IGNORECASE)


def year_of(name: str) -> Optional[int]:
    m = RE_YEAR.search(name)
    return int(m.group("year")) if m else None


def find_inner_csv(zip_path: Path) -> Optional[str]:
    with zipfile.ZipFile(zip_path) as zf:
        names = [n for n in zf.namelist() if n.lower().endswith(".csv")]
    if not names: return None
    if len(names) == 1: return names[0]
    with zipfile.ZipFile(zip_path) as zf:
        return max(names, key=lambda n: zf.getinfo(n).file_size)


extracted = 0
skipped = 0
Path(CSV_EXTRACTED).mkdir(parents=True, exist_ok=True)

zips_found = sorted(Path(ZIPS_DIR).glob("*.zip"))
print(f"ZIPs em {ZIPS_DIR}: {len(zips_found)}")

for zp in zips_found:
    year = year_of(zp.name)
    if not year:
        continue
    inner = find_inner_csv(zp)
    if not inner:
        continue
    out = Path(CSV_EXTRACTED) / f"emendas__{year}__{Path(inner).name}"
    if out.exists() and out.stat().st_size > 0:
        skipped += 1
        continue
    with zipfile.ZipFile(zp) as zf, open(out, "wb") as fout:
        fout.write(zf.read(inner))
    extracted += 1

csvs_now = sorted(Path(CSV_EXTRACTED).glob("*.csv"))
print(f"Extracted {extracted} new CSVs (skipped {skipped} already extracted). "
      f"Total CSVs: {len(csvs_now)}")

# Guard: if no CSVs in folder, skip the Auto Loader step gracefully.
# This happens when the upstream ingest task didn't successfully download any
# CGU ZIPs (URL changed, network issue, dataset moved). Without this guard,
# Auto Loader fails with CF_EMPTY_DIR_FOR_SCHEMA_INFERENCE.
if not csvs_now:
    print("⚠ No CSVs to process. Bronze table NOT updated. Investigate the ingest task:")
    print("  - Verify URL pattern at https://portaldatransparencia.gov.br/download-de-dados/emendas")
    print("  - Check the ingest_cgu_emendas task output for HTTP errors")
    print("  - Once URLs are fixed, re-run this job.")
    dbutils.notebook.exit("SKIPPED: no CSV files in source folder")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 2 — Auto Loader CSV → Delta append (com headers normalizados)

# COMMAND ----------

import re as _re
from pyspark.sql import functions as F

_ACCENTS = {"Á":"A","À":"A","Â":"A","Ã":"A","É":"E","Ê":"E","Í":"I","Ó":"O","Ô":"O","Õ":"O","Ú":"U","Ç":"C"}


def normalize_col(c: str) -> str:
    raw = c.strip().upper().replace("MÊS", "MES")
    for a, r in _ACCENTS.items():
        raw = raw.replace(a, r)
    new = _re.sub(r"[^A-Z0-9]+", "_", raw).strip("_").lower()
    return new or c.lower().replace(" ", "_")


raw_stream = (
    spark.readStream
        .format("cloudFiles")
        .option("cloudFiles.format", "csv")
        .option("cloudFiles.inferColumnTypes", "true")
        .option("cloudFiles.schemaLocation", SCHEMA_LOC)
        .option("cloudFiles.schemaEvolutionMode", "addNewColumns")
        .option("header",    "true")
        .option("sep",       ";")
        .option("encoding",  "latin1")
        .option("multiLine", "false")
        .option("quote",     '"')
        .option("escape",    '"')
        .option("mode",      "PERMISSIVE")
        .load(CSV_EXTRACTED)
)

# Rename CSV columns to snake_case BEFORE adding metadata
new_names = [normalize_col(c) for c in raw_stream.columns]
stream = raw_stream.toDF(*new_names)

stream = (
    stream
    .withColumn("_source_file", F.col("_metadata.file_path"))
    .withColumn("_fname",       F.element_at(F.split(F.col("_source_file"), "/"), -1))
    .withColumn("ano_arquivo",  F.split(F.col("_fname"), "__").getItem(1).cast("int"))
    .withColumn("_ingest_ts",   F.current_timestamp())
    .drop("_fname")
)

query = (
    stream.writeStream
        .format("delta")
        .option("checkpointLocation", CHECKPOINT_LOC)
        .option("mergeSchema", "true")
        .partitionBy("ano_arquivo")
        .trigger(availableNow=True)
        .toTable(BRONZE_TABLE)
)
query.awaitTermination()

# COMMAND ----------

n = spark.read.table(BRONZE_TABLE).count()
print(f"✔ {BRONZE_TABLE}: {n:,} rows total")
spark.read.table(BRONZE_TABLE).groupBy("ano_arquivo").count().orderBy("ano_arquivo").show(30)
print("\n--- columns ---")
print(spark.read.table(BRONZE_TABLE).columns)

# Databricks notebook source
# MAGIC %md
# MAGIC # bronze · emendas_pagamentos
# MAGIC
# MAGIC Pipeline em 2 estágios:
# MAGIC
# MAGIC 1. **Extract**: para cada `emendas_parlamentares__{ts}.zip` novo, descomprime
# MAGIC    APENAS `EmendasParlamentares.csv` (principal) — ignora os auxiliares
# MAGIC    (`_Convenios.csv`, `_PorFavorecido.csv`).
# MAGIC 2. **Auto Loader CSV → Delta append**, com headers normalizados pra ASCII snake_case.
# MAGIC    Ano vem da coluna `ano_da_emenda` (não do filename, já que CGU publica um único
# MAGIC    ZIP consolidado cobrindo todos os anos).

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

PRINCIPAL_INNER = "EmendasParlamentares.csv"   # nome canônico dentro do ZIP

print(f"zips_dir={ZIPS_DIR}  csv_extracted={CSV_EXTRACTED}  target={BRONZE_TABLE}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 1 — extrair `EmendasParlamentares.csv` de cada ZIP novo (idempotente)

# COMMAND ----------

import re
import zipfile
from pathlib import Path

# Filename pattern: emendas_parlamentares__YYYYMMDDTHHMMSSZ.zip → keep ts as suffix on output
RE_TS = re.compile(r"__(?P<ts>\d{8}T\d{6}Z)", re.IGNORECASE)


def ts_of(name: str) -> str | None:
    m = RE_TS.search(name)
    return m.group("ts") if m else None


extracted = 0
skipped = 0
Path(CSV_EXTRACTED).mkdir(parents=True, exist_ok=True)

zips_found = sorted(Path(ZIPS_DIR).glob("emendas_parlamentares__*.zip"))
print(f"ZIPs em {ZIPS_DIR}: {len(zips_found)}")

for zp in zips_found:
    ts = ts_of(zp.name) or "unknown"
    out = Path(CSV_EXTRACTED) / f"emendas_parlamentares__{ts}.csv"
    if out.exists() and out.stat().st_size > 0:
        skipped += 1
        continue
    try:
        with zipfile.ZipFile(zp) as zf:
            names = zf.namelist()
            if PRINCIPAL_INNER not in names:
                print(f"  ⚠ {zp.name}: sem {PRINCIPAL_INNER} (achei {names}); pulando.")
                continue
            with zf.open(PRINCIPAL_INNER) as src, open(out, "wb") as fout:
                while chunk := src.read(1 << 20):
                    fout.write(chunk)
        extracted += 1
    except zipfile.BadZipFile as e:
        print(f"  ✗ {zp.name} corrupto: {e}")

csvs_now = sorted(Path(CSV_EXTRACTED).glob("emendas_parlamentares__*.csv"))
print(f"Extracted {extracted} new CSVs (skipped {skipped} already extracted). "
      f"Total CSVs: {len(csvs_now)}")

# Guard: if no CSVs in folder, skip Auto Loader gracefully (avoids
# CF_EMPTY_DIR_FOR_SCHEMA_INFERENCE when upstream ingest failed).
if not csvs_now:
    print("⚠ No CSVs to process. Bronze table NOT updated. Investigate the ingest task:")
    print(f"  - ls {ZIPS_DIR}")
    print("  - URL pattern: https://portaldatransparencia.gov.br/download-de-dados/emendas-parlamentares/2024")
    dbutils.notebook.exit("SKIPPED: no CSV files in source folder")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 2 — Auto Loader CSV → Delta append (com headers normalizados)

# COMMAND ----------

from pyspark.sql import functions as F

_ACCENTS = {"Á":"A","À":"A","Â":"A","Ã":"A","É":"E","Ê":"E","Í":"I",
            "Ó":"O","Ô":"O","Õ":"O","Ú":"U","Ç":"C"}


def normalize_col(c: str) -> str:
    raw = c.strip().upper()
    for a, r in _ACCENTS.items():
        raw = raw.replace(a, r)
    new = re.sub(r"[^A-Z0-9]+", "_", raw).strip("_").lower()
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

# Rename CSV columns to snake_case BEFORE writing — Delta doesn't accept accents/spaces.
new_names = [normalize_col(c) for c in raw_stream.columns]
stream = raw_stream.toDF(*new_names)

stream = (
    stream
    .withColumn("_source_file", F.col("_metadata.file_path"))
    .withColumn("_ingest_ts",   F.current_timestamp())
)

# Partition by ano_da_emenda when available; falls back to "unknown" partition otherwise.
if "ano_da_emenda" in stream.columns:
    stream = stream.withColumn("ano_arquivo", F.col("ano_da_emenda").cast("int"))
else:
    stream = stream.withColumn("ano_arquivo", F.lit(None).cast("int"))

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

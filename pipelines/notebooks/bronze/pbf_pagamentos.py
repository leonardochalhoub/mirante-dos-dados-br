# Databricks notebook source
# MAGIC %md
# MAGIC # bronze · pbf_pagamentos
# MAGIC
# MAGIC Pra PBF, Auto Loader não trabalha bem com ZIPs (não tem reader nativo). Em vez
# MAGIC disso: extraímos cada novo ZIP encontrado em `/Volumes/.../cgu/pbf/` para CSV em
# MAGIC `/Volumes/.../cgu/pbf_csv/` (idempotente: skip extracted), aí Auto Loader monitora
# MAGIC essa pasta de CSVs como source.
# MAGIC
# MAGIC Bronze preserva colunas crus + metadados (origin, ano, mes, source_zip, _ingest_ts).
# MAGIC
# MAGIC | param | default |
# MAGIC | --- | --- |
# MAGIC | `catalog`         | `mirante_prd` |
# MAGIC | `zips_dir`        | `/Volumes/mirante_prd/bronze/raw/cgu/pbf` |
# MAGIC | `csv_extracted`   | `/Volumes/mirante_prd/bronze/raw/cgu/pbf_csv_extracted` |

# COMMAND ----------

dbutils.widgets.text("catalog",       "mirante_prd")
dbutils.widgets.text("zips_dir",      "/Volumes/mirante_prd/bronze/raw/cgu/pbf")
dbutils.widgets.text("csv_extracted", "/Volumes/mirante_prd/bronze/raw/cgu/pbf_csv_extracted")

CATALOG       = dbutils.widgets.get("catalog")
ZIPS_DIR      = dbutils.widgets.get("zips_dir")
CSV_EXTRACTED = dbutils.widgets.get("csv_extracted")

BRONZE_TABLE   = f"{CATALOG}.bronze.pbf_pagamentos"
CHECKPOINT_LOC = f"/Volumes/{CATALOG}/bronze/raw/_autoloader/pbf_pagamentos/_checkpoint"
SCHEMA_LOC     = f"/Volumes/{CATALOG}/bronze/raw/_autoloader/pbf_pagamentos/_schema"

print(f"zips_dir={ZIPS_DIR}  csv_extracted={CSV_EXTRACTED}  target={BRONZE_TABLE}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 1 — extrai ZIPs novos para CSVs nomeados (idempotente)

# COMMAND ----------

import re
import zipfile
from pathlib import Path
from typing import Optional

_MONTH_RE  = re.compile(r"(?P<year>20\d{2})[_-]?(?P<month>0[1-9]|1[0-2])", re.IGNORECASE)
_SOURCE_RE = re.compile(r"^(?P<src>PBF|AUX_BR|AUX|NBF)[_-]", re.IGNORECASE)


def origin_of(name: str) -> str:
    m = _SOURCE_RE.match(name)
    if not m: return "UNK"
    src = m.group("src").upper()
    return {"AUX_BR": "AUX", "AUX": "AUX", "PBF": "PBF", "NBF": "NBF"}.get(src, src)


def yearmonth_of(name: str) -> Optional[tuple[int, int]]:
    m = _MONTH_RE.search(name)
    return (int(m.group("year")), int(m.group("month"))) if m else None


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

for zp in sorted(Path(ZIPS_DIR).glob("*.zip")):
    ym = yearmonth_of(zp.name)
    if not ym: continue
    year, month = ym
    origin = origin_of(zp.name)
    inner = find_inner_csv(zp)
    if not inner: continue

    # Embed metadata in filename for downstream parsing
    out = Path(CSV_EXTRACTED) / f"{origin}__{year}_{month:02d}__{Path(inner).name}"
    if out.exists() and out.stat().st_size > 0:
        skipped += 1
        continue
    with zipfile.ZipFile(zp) as zf, open(out, "wb") as fout:
        fout.write(zf.read(inner))
    extracted += 1

print(f"Extracted {extracted} new CSVs (skipped {skipped} already extracted).")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 2 — Auto Loader nos CSVs → Delta bronze append

# COMMAND ----------

from pyspark.sql import functions as F

stream = (
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
        # Decode origin/year/month from the embedded filename
        .withColumn("_source_file",  F.col("_metadata.file_path"))
        .withColumn("_fname",        F.element_at(F.split(F.col("_source_file"), "/"), -1))
        .withColumn("origin",        F.split(F.col("_fname"), "__").getItem(0))
        .withColumn("ym_str",        F.split(F.col("_fname"), "__").getItem(1))
        .withColumn("ano",           F.split(F.col("ym_str"), "_").getItem(0).cast("int"))
        .withColumn("mes",           F.split(F.col("ym_str"), "_").getItem(1).cast("int"))
        .withColumn("competencia",   F.format_string("%04d%02d", F.col("ano"), F.col("mes")))
        .withColumn("_ingest_ts",    F.current_timestamp())
        .drop("_fname", "ym_str")
)

query = (
    stream.writeStream
        .format("delta")
        .option("checkpointLocation", CHECKPOINT_LOC)
        .option("mergeSchema", "true")
        .partitionBy("origin", "ano")
        .trigger(availableNow=True)
        .toTable(BRONZE_TABLE)
)
query.awaitTermination()

# COMMAND ----------

n = spark.read.table(BRONZE_TABLE).count()
print(f"✔ {BRONZE_TABLE}: {n:,} rows total")
spark.read.table(BRONZE_TABLE).groupBy("origin", "ano").count().orderBy("ano", "origin").show(50)

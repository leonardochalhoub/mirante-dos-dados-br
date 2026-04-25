# Databricks notebook source
# MAGIC %md
# MAGIC # bronze · cnes_equipamentos
# MAGIC
# MAGIC Pipeline em 2 estágios — Auto Loader não lê `.dbc` (binário comprimido):
# MAGIC
# MAGIC 1. **Convert**: `.dbc` → `.dbf` (descomprime via PySUS) → Parquet (pandas)
# MAGIC    Idempotente: pula se o `.parquet` correspondente já existe
# MAGIC 2. **Auto Loader** sobre o folder de Parquet → Delta append
# MAGIC
# MAGIC Filename pattern: `EQ<UF><YY><MM>.dbc` → metadados (estado, ano, mes) extraídos do nome.

# COMMAND ----------

dbutils.widgets.text("catalog",        "mirante_prd")
dbutils.widgets.text("dbc_dir",        "/Volumes/mirante_prd/bronze/raw/datasus/cnes_eq")
dbutils.widgets.text("parquet_dir",    "/Volumes/mirante_prd/bronze/raw/datasus/cnes_eq_parquet")
dbutils.widgets.text("workers",        "8")

CATALOG     = dbutils.widgets.get("catalog")
DBC_DIR     = dbutils.widgets.get("dbc_dir")
PARQUET_DIR = dbutils.widgets.get("parquet_dir")
WORKERS     = int(dbutils.widgets.get("workers"))

BRONZE_TABLE   = f"{CATALOG}.bronze.cnes_equipamentos"
CHECKPOINT_LOC = f"/Volumes/{CATALOG}/bronze/raw/_autoloader/cnes_equipamentos/_checkpoint"
SCHEMA_LOC     = f"/Volumes/{CATALOG}/bronze/raw/_autoloader/cnes_equipamentos/_schema"

print(f"dbc_dir={DBC_DIR}  parquet_dir={PARQUET_DIR}  target={BRONZE_TABLE}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 1 — install PySUS + dbfread (in-notebook)
# MAGIC
# MAGIC PySUS bundles the C `blast_decoder` lib needed pra descomprimir DBC.

# COMMAND ----------

# MAGIC %pip install --quiet pysus dbfread pandas pyarrow
# MAGIC dbutils.library.restartPython()

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 2 — convert .dbc → .parquet (idempotent, parallel)

# COMMAND ----------

import contextlib
import io
import re
import tempfile
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import pandas as pd
from dbfread import DBF
from pysus.utilities.readdbc import dbc2dbf

RE_EQ_FILE = re.compile(r"^EQ(?P<uf>[A-Z]{2})(?P<yy>\d{2})(?P<mm>\d{2})\.dbc$", re.IGNORECASE)


def parse_filename(name: str) -> dict | None:
    m = RE_EQ_FILE.match(name)
    if not m:
        return None
    yy = int(m.group("yy"))
    mm = int(m.group("mm"))
    return {"estado": m.group("uf").upper(), "ano": 2000 + yy, "mes": f"{mm:02d}"}


def convert_one(dbc_path: Path, out_dir: Path) -> tuple[str, str]:
    """Returns (filename, status) ∈ {'ok','cached','empty','error'}."""
    out_path = out_dir / (dbc_path.stem + ".parquet")
    if out_path.exists() and out_path.stat().st_size > 0:
        return dbc_path.name, "cached"

    meta = parse_filename(dbc_path.name)
    if not meta:
        return dbc_path.name, "error"

    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            dbf_path = Path(tmpdir) / dbc_path.with_suffix(".dbf").name
            with contextlib.redirect_stdout(io.StringIO()):
                dbc2dbf(str(dbc_path), str(dbf_path))
            df = pd.DataFrame(iter(DBF(str(dbf_path), encoding="latin-1")))

        if df.empty:
            # Write an empty-but-typed parquet so we don't re-attempt next run
            pd.DataFrame(columns=["source_file", "estado", "ano", "mes"]).to_parquet(out_path, index=False)
            return dbc_path.name, "empty"

        df["source_file"] = dbc_path.name
        df["estado"]      = meta["estado"]
        df["ano"]         = meta["ano"]
        df["mes"]         = meta["mes"]
        df.to_parquet(out_path, index=False)
        return dbc_path.name, "ok"
    except Exception as e:
        if out_path.exists():
            out_path.unlink()
        print(f"  ✗ {dbc_path.name}: {type(e).__name__}: {str(e)[:80]}")
        return dbc_path.name, "error"


# COMMAND ----------

dbc_dir     = Path(DBC_DIR)
parquet_dir = Path(PARQUET_DIR)
parquet_dir.mkdir(parents=True, exist_ok=True)

dbc_files = sorted(dbc_dir.glob("*.dbc"))
print(f"Found {len(dbc_files)} .dbc files. Parallel convert workers={WORKERS}…")

results = {"ok": 0, "cached": 0, "empty": 0, "error": 0}
with ThreadPoolExecutor(max_workers=WORKERS) as ex:
    futures = [ex.submit(convert_one, p, parquet_dir) for p in dbc_files]
    for i, fut in enumerate(as_completed(futures), 1):
        _, status = fut.result()
        results[status] += 1
        if i % 500 == 0 or i == len(dbc_files):
            print(f"  [{i:5d}/{len(dbc_files)}] {results}")

print(f"Convert done: {results}")
print(f"Total .parquet now: {len(list(parquet_dir.glob('*.parquet')))}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 3 — Auto Loader sobre os Parquet → Delta append

# COMMAND ----------

from pyspark.sql import functions as F

stream = (
    spark.readStream
        .format("cloudFiles")
        .option("cloudFiles.format", "parquet")
        .option("cloudFiles.inferColumnTypes", "true")
        .option("cloudFiles.schemaLocation", SCHEMA_LOC)
        .option("cloudFiles.schemaEvolutionMode", "addNewColumns")
        .load(PARQUET_DIR)
        .withColumn("_source_file", F.col("_metadata.file_path"))
        .withColumn("_ingest_ts",   F.current_timestamp())
)

query = (
    stream.writeStream
        .format("delta")
        .option("checkpointLocation", CHECKPOINT_LOC)
        .option("mergeSchema", "true")
        .partitionBy("estado", "ano")
        .trigger(availableNow=True)
        .toTable(BRONZE_TABLE)
)
query.awaitTermination()

# COMMAND ----------

n = spark.read.table(BRONZE_TABLE).count()
print(f"✔ {BRONZE_TABLE}: {n:,} rows total")
spark.read.table(BRONZE_TABLE).groupBy("ano").count().orderBy("ano").show(30)

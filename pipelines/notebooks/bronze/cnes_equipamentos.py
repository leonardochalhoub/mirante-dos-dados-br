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

# MAGIC %md
# MAGIC ## Step 1 — install pyreaddbc + dbfread (in-notebook)
# MAGIC
# MAGIC `pyreaddbc` é o pacote standalone que bundles o C `blast_decoder`
# MAGIC pra descomprimir DBC (anteriormente vivia em `pysus.utilities.readdbc`,
# MAGIC removido em PySUS 1.x+). Mantido pelo time AlertaDengue/PySUS.
# MAGIC
# MAGIC ⚠️ `restartPython()` reinicia o interpretador e **apaga todas as variáveis**
# MAGIC definidas antes — por isso widgets/parâmetros são lidos depois.

# COMMAND ----------

# MAGIC %pip install --quiet pyreaddbc dbfread pandas pyarrow
# MAGIC dbutils.library.restartPython()

# COMMAND ----------

dbutils.widgets.text("catalog",        "mirante_prd")
dbutils.widgets.text("dbc_dir",        "/Volumes/mirante_prd/bronze/raw/datasus/cnes_eq")
dbutils.widgets.text("parquet_dir",    "/Volumes/mirante_prd/bronze/raw/datasus/cnes_eq_parquet")
dbutils.widgets.text("workers",        "8")

CATALOG     = dbutils.widgets.get("catalog")
DBC_DIR     = dbutils.widgets.get("dbc_dir")
PARQUET_DIR = dbutils.widgets.get("parquet_dir")
WORKERS     = int(dbutils.widgets.get("workers"))

BRONZE_TABLE = f"{CATALOG}.bronze.cnes_equipamentos"

print(f"dbc_dir={DBC_DIR}  parquet_dir={PARQUET_DIR}  target={BRONZE_TABLE}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 2 — convert .dbc → .parquet (idempotent, parallel)

# COMMAND ----------

import os
import re
import tempfile
from concurrent.futures import ProcessPoolExecutor, as_completed
from contextlib import contextmanager
from pathlib import Path

import pandas as pd
from dbfread import DBF
from pyreaddbc import dbc2dbf

RE_EQ_FILE = re.compile(r"^EQ(?P<uf>[A-Z]{2})(?P<yy>\d{2})(?P<mm>\d{2})\.dbc$", re.IGNORECASE)


@contextmanager
def silence_fd_stdout():
    # The C decoder writes to fd 1 directly; redirect at the OS level.
    devnull = os.open(os.devnull, os.O_WRONLY)
    saved = os.dup(1)
    try:
        os.dup2(devnull, 1)
        yield
    finally:
        os.dup2(saved, 1)
        os.close(devnull)
        os.close(saved)


def parse_filename(name: str) -> dict | None:
    m = RE_EQ_FILE.match(name)
    if not m:
        return None
    yy = int(m.group("yy"))
    mm = int(m.group("mm"))
    return {"estado": m.group("uf").upper(), "ano": 2000 + yy, "mes": f"{mm:02d}"}


def convert_one(dbc_path_str: str, out_dir_str: str) -> tuple[str, str]:
    """Returns (filename, status) ∈ {'ok','cached','empty','error'}.

    Args are strings (not Path) so they pickle cheaply for ProcessPoolExecutor.
    """
    dbc_path = Path(dbc_path_str)
    out_dir = Path(out_dir_str)
    out_path = out_dir / (dbc_path.stem + ".parquet")
    if out_path.exists() and out_path.stat().st_size > 0:
        return dbc_path.name, "cached"

    meta = parse_filename(dbc_path.name)
    if not meta:
        return dbc_path.name, "error"

    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            dbf_path = Path(tmpdir) / dbc_path.with_suffix(".dbf").name
            with silence_fd_stdout():
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
with ProcessPoolExecutor(max_workers=WORKERS) as ex:
    futures = [ex.submit(convert_one, str(p), str(parquet_dir)) for p in dbc_files]
    for i, fut in enumerate(as_completed(futures), 1):
        _, status = fut.result()
        results[status] += 1
        if i % 250 == 0 or i == len(dbc_files):
            print(f"  [{i:5d}/{len(dbc_files)}] {results}")

print(f"Convert done: {results}")
print(f"Total .parquet now: {len(list(parquet_dir.glob('*.parquet')))}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 3 — Batch read Parquet → Delta (dynamic partition overwrite)
# MAGIC
# MAGIC Auto Loader (`cloudFiles`) era usado aqui mas tinha overhead **enorme**
# MAGIC pra 6614 arquivos pequenos no Free Edition: schema inference por arquivo
# MAGIC + coordenação de micro-batch + checkpoint maintenance ~~ 20+ minutos.
# MAGIC
# MAGIC Padrão batch (matching o repo original Parkinson-BR-Stats):
# MAGIC - `spark.read.parquet(...)` lê tudo em uma operação
# MAGIC - `mode("overwrite") + partitionOverwriteMode=dynamic` reescreve só
# MAGIC   partições que mudaram (idempotente, atômico)
# MAGIC - Sem checkpoint, sem schema location, sem streaming
# MAGIC
# MAGIC Esperado: < 3 minutos pro mesmo workload. Subsequent runs ainda mais
# MAGIC rápidas (convert_one cache + dynamic overwrite só toca novas partições).

# COMMAND ----------

from pyspark.sql import functions as F

# Dynamic partition overwrite: só (estado, ano) com dados novos são reescritos
spark.conf.set("spark.sql.sources.partitionOverwriteMode", "dynamic")

df = (
    spark.read.parquet(PARQUET_DIR)
        .withColumn("_source_file", F.input_file_name())
        .withColumn("_ingest_ts",   F.current_timestamp())
)

(
    df.write
        .format("delta")
        .mode("overwrite")
        .option("mergeSchema", "true")
        .partitionBy("estado", "ano")
        .saveAsTable(BRONZE_TABLE)
)

# COMMAND ----------

n = spark.read.table(BRONZE_TABLE).count()
print(f"✔ {BRONZE_TABLE}: {n:,} rows total")
spark.read.table(BRONZE_TABLE).groupBy("ano").count().orderBy("ano").show(30)

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

BRONZE_TABLE   = f"{CATALOG}.bronze.cnes_equipamentos"
CHECKPOINT_LOC = f"/Volumes/{CATALOG}/bronze/raw/_autoloader/cnes_equipamentos/_checkpoint"
SCHEMA_LOC     = f"/Volumes/{CATALOG}/bronze/raw/_autoloader/cnes_equipamentos/_schema"

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

        # Schema-drift fix: pandas infere int64 quando todos valores são inteiros
        # naquele mês, mas float64 quando há NaN. Spark falha ao ler parquets do
        # mesmo diretório com tipos incompatíveis (LONG vs DOUBLE) na mesma
        # coluna. Coercemos TODAS as colunas numéricas para float64 antes de
        # escrever — float aceita qualquer int sem perda relevante p/ análise
        # epidemiológica deste dataset (contagens de equipamentos, IDs).
        for c in df.columns:
            if c in ("source_file", "estado", "ano", "mes"):
                continue
            if pd.api.types.is_integer_dtype(df[c]) or pd.api.types.is_float_dtype(df[c]):
                df[c] = df[c].astype("float64")

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
# MAGIC ## Step 3 — Parquet → Delta (modo híbrido: batch ou Auto Loader)
# MAGIC
# MAGIC **Decisão automática em runtime:**
# MAGIC - Se a tabela bronze NÃO existe ainda OU está vazia OU o checkpoint do
# MAGIC   Auto Loader não existe: **modo batch** (`spark.read.parquet` +
# MAGIC   `mode("overwrite")` com `partitionOverwriteMode=dynamic`).
# MAGIC   Carga inicial de 6614 arquivos completa em ~2-3 minutos.
# MAGIC - Caso contrário: **Auto Loader** (`cloudFiles` streaming
# MAGIC   `availableNow=True`). Detecta apenas os novos parquets convertidos
# MAGIC   no refresh do mês via checkpoint persistente. Roda em segundos quando
# MAGIC   há poucos arquivos novos.
# MAGIC
# MAGIC Justificativa: Auto Loader tem overhead alto pra carga inicial massiva
# MAGIC mas é ótimo pra detectar deltas em refreshes mensais (~27 novos DBCs
# MAGIC por mês, um por UF).

# COMMAND ----------

from pyspark.sql import functions as F

table_exists = spark.catalog.tableExists(BRONZE_TABLE)
existing_rows = (
    spark.read.table(BRONZE_TABLE).count() if table_exists else 0
)
checkpoint_initialized = False
try:
    checkpoint_initialized = bool(dbutils.fs.ls(CHECKPOINT_LOC))
except Exception:
    pass  # checkpoint dir doesn't exist yet

use_batch = (not table_exists) or (existing_rows == 0) or (not checkpoint_initialized)

if use_batch:
    # ─── MODO BATCH (carga inicial / reset) ──────────────────────────
    # NB: serverless do Free Edition NÃO aceita
    # `partitionOverwriteMode=dynamic`. Como esse caminho roda apenas na
    # primeira carga (tabela não existe ou vazia), full overwrite é OK —
    # não há dados a preservar. Atualizações incrementais ficam pra Auto
    # Loader (caminho de baixo).
    print(f"▸ MODO BATCH — table_exists={table_exists}  rows={existing_rows:,}  "
          f"checkpoint_initialized={checkpoint_initialized}")
    print("  Lendo parquets em batch e reescrevendo Delta (full overwrite — primeira carga).")

    # mergeSchema=true reconcilia parquets com colunas em tipos diferentes
    # (LONG vs DOUBLE etc) — necessário pq parquets antigos foram escritos
    # antes do fix de coerce-to-float64 em convert_one(). Após re-conversão
    # de todos arquivos, pode ser removido (mas não custa nada manter).
    df = (
        spark.read
            .option("mergeSchema", "true")
            .parquet(PARQUET_DIR)
            # Unity Catalog não suporta input_file_name(); usar _metadata.file_path
            .withColumn("_source_file", F.col("_metadata.file_path"))
            .withColumn("_ingest_ts",   F.current_timestamp())
    )
    (
        df.write
            .format("delta")
            .mode("overwrite")
            .option("overwriteSchema", "true")
            .partitionBy("estado", "ano")
            .saveAsTable(BRONZE_TABLE)
    )

    # Após o batch inicial, criamos o checkpoint do Auto Loader vazio para que
    # a próxima execução já entre no modo incremental. Listamos os arquivos
    # atuais como "já vistos" via uma única passagem availableNow.
    print("  Inicializando checkpoint do Auto Loader pra próximas execuções incrementais…")
    init_stream = (
        spark.readStream
            .format("cloudFiles")
            .option("cloudFiles.format", "parquet")
            .option("cloudFiles.inferColumnTypes", "true")
            .option("cloudFiles.schemaLocation", SCHEMA_LOC)
            .option("cloudFiles.includeExistingFiles", "false")  # já carregados via batch
            .load(PARQUET_DIR)
            .withColumn("_source_file", F.col("_metadata.file_path"))
            .withColumn("_ingest_ts",   F.current_timestamp())
    )
    # writeStream com count() vazio só pra o checkpoint registrar "já vi tudo"
    (
        init_stream.writeStream
            .format("delta")
            .option("checkpointLocation", CHECKPOINT_LOC)
            .option("mergeSchema", "true")
            .partitionBy("estado", "ano")
            .trigger(availableNow=True)
            .toTable(BRONZE_TABLE)
            .awaitTermination()
    )

else:
    # ─── MODO AUTO LOADER (incremental mensal) ───────────────────────
    print(f"▸ MODO AUTO LOADER — table_exists={table_exists}  rows={existing_rows:,}  "
          f"checkpoint pré-existente.")
    print("  Detectando apenas parquets novos desde o último checkpoint.")

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
    (
        stream.writeStream
            .format("delta")
            .option("checkpointLocation", CHECKPOINT_LOC)
            .option("mergeSchema", "true")
            .partitionBy("estado", "ano")
            .trigger(availableNow=True)
            .toTable(BRONZE_TABLE)
            .awaitTermination()
    )

# COMMAND ----------

n = spark.read.table(BRONZE_TABLE).count()
print(f"✔ {BRONZE_TABLE}: {n:,} rows total")
spark.read.table(BRONZE_TABLE).groupBy("ano").count().orderBy("ano").show(30)

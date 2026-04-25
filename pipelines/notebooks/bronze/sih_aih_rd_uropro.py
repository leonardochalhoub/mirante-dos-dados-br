# Databricks notebook source
# MAGIC %md
# MAGIC # bronze · sih_aih_rd_uropro
# MAGIC
# MAGIC Pipeline em 2 estágios — Auto Loader não lê `.dbc` (binário PKWARE).
# MAGIC
# MAGIC 1. **Convert+Filter**: `.dbc` → `.dbf` (PySUS/blast_decoder) → filtra
# MAGIC    `PROC_REA ∈ {procs_filter}` → Parquet (uma partição por arquivo)
# MAGIC    Idempotente: pula se o `.parquet` correspondente já existe
# MAGIC 2. **Auto Loader** sobre o folder de Parquet → Delta append
# MAGIC
# MAGIC Filename pattern: `RD<UF><YY><MM>.dbc` → metadados extraídos do nome.
# MAGIC
# MAGIC ## Por que filtrar antes do Delta?
# MAGIC RD bruto é gigantesco (~1-2M linhas por UF×mês). Para a vertical de
# MAGIC Incontinência Urinária, restamos com ~milhares de linhas no total.
# MAGIC Filtrar no convert mantém Delta minúsculo e rápido.
# MAGIC
# MAGIC Para reaproveitar essa pipeline para outras agendas (ex: MEDICINA NUCLEAR,
# MAGIC ortopedia, oncologia), basta passar `procs_filter` diferente em outra task
# MAGIC e mudar `parquet_dir` + `bronze_table`.
# MAGIC
# MAGIC ## Procedimentos (Tatieli, 2022)
# MAGIC - 0409010499 — Incontinência Urinária Via Abdominal
# MAGIC - 0409070270 — Incontinência Urinária Por Via Vaginal
# MAGIC - 0409020117 — Incontinência Urinária (genérico)

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 1 — install pyreaddbc + dbfread (in-notebook)

# COMMAND ----------

# MAGIC %pip install --quiet pyreaddbc dbfread pandas pyarrow
# MAGIC dbutils.library.restartPython()

# COMMAND ----------

dbutils.widgets.text("catalog",       "mirante_prd")
dbutils.widgets.text("dbc_dir",       "/Volumes/mirante_prd/bronze/raw/datasus/sih_rd")
dbutils.widgets.text("parquet_dir",   "/Volumes/mirante_prd/bronze/raw/datasus/sih_rd_uropro_parquet")
dbutils.widgets.text("workers",       "16")
dbutils.widgets.text("procs_filter",  "0409010499,0409070270,0409020117")
dbutils.widgets.text("table_suffix",  "uropro")

CATALOG       = dbutils.widgets.get("catalog")
DBC_DIR       = dbutils.widgets.get("dbc_dir")
PARQUET_DIR   = dbutils.widgets.get("parquet_dir")
WORKERS       = int(dbutils.widgets.get("workers"))
PROCS_FILTER  = tuple(p.strip() for p in dbutils.widgets.get("procs_filter").split(",") if p.strip())
TABLE_SUFFIX  = dbutils.widgets.get("table_suffix").strip()

BRONZE_TABLE   = f"{CATALOG}.bronze.sih_aih_rd_{TABLE_SUFFIX}"
CHECKPOINT_LOC = f"/Volumes/{CATALOG}/bronze/raw/_autoloader/sih_aih_rd_{TABLE_SUFFIX}/_checkpoint"
SCHEMA_LOC     = f"/Volumes/{CATALOG}/bronze/raw/_autoloader/sih_aih_rd_{TABLE_SUFFIX}/_schema"

print(f"dbc_dir={DBC_DIR}")
print(f"parquet_dir={PARQUET_DIR}")
print(f"target={BRONZE_TABLE}")
print(f"procs_filter={PROCS_FILTER}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 2 — convert + filter .dbc → .parquet (idempotent, multi-process)
# MAGIC
# MAGIC `dbc2dbf` é uma extensão C que **não libera o GIL**. Usamos
# MAGIC `ProcessPoolExecutor` (não Thread) para paralelismo real.
# MAGIC Também redirecionamos fd 1 (`os.dup2`) porque o decoder C escreve
# MAGIC "Success"/"Invalid argument" direto no stdout do SO.

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

RE_RD_FILE = re.compile(r"^RD(?P<uf>[A-Z]{2})(?P<yy>\d{2})(?P<mm>\d{2})\.dbc$", re.IGNORECASE)

# Subset de colunas — RD tem ~120 colunas, mantemos só as relevantes pra análise.
# O filtro acontece no convert; mais colunas = mais bytes em memória/disco.
KEEP_COLS = (
    "N_AIH",       # AIH number
    "ANO_CMPT",    # ano de competência
    "MES_CMPT",    # mês de competência
    "UF_ZI",       # UF do estabelecimento
    "MUNIC_RES",   # município de residência (cod IBGE 7-dig)
    "PROC_REA",    # procedimento realizado (SIGTAP)
    "VAL_TOT",     # valor total da AIH
    "VAL_SH",      # valor serviços hospitalares
    "VAL_SP",      # valor serviços profissionais
    "DIAS_PERM",   # dias de permanência
    "MORTE",       # 1=óbito, 0=alta
    "CAR_INT",     # caráter atendimento (01=eletivo, 02=urgência, ...)
    "GESTAO",      # E=estadual, M=municipal, D=dupla
    "IDADE",       # idade
    "COD_IDADE",   # unidade da idade (4=anos, 3=meses, ...)
    "SEXO",        # 1=M, 3=F
    "ESPEC",       # especialidade do leito
    "CGC_HOSP",    # CNPJ do hospital
)


@contextmanager
def silence_fd_stdout():
    """Suprime stdout do SO (fd 1) — escapa do redirect_stdout do Python.
    O decoder C de pyreaddbc escreve "Success"/"Invalid argument" direto."""
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
    m = RE_RD_FILE.match(name)
    if not m:
        return None
    yy = int(m.group("yy"))
    mm = int(m.group("mm"))
    year = 2000 + yy if yy < 50 else 1900 + yy
    return {"estado": m.group("uf").upper(), "ano": year, "mes": f"{mm:02d}"}


def convert_one(dbc_path_str: str, out_dir_str: str, procs_filter: tuple[str, ...]) -> tuple[str, str, int]:
    """Returns (filename, status, n_rows_kept).
    status ∈ {'ok','cached','empty','error'}.
    """
    dbc_path = Path(dbc_path_str)
    out_dir = Path(out_dir_str)
    out_path = out_dir / (dbc_path.stem + ".parquet")
    if out_path.exists() and out_path.stat().st_size > 0:
        return dbc_path.name, "cached", 0

    meta = parse_filename(dbc_path.name)
    if not meta:
        return dbc_path.name, "error", 0

    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            dbf_path = Path(tmpdir) / dbc_path.with_suffix(".dbf").name
            with silence_fd_stdout():
                dbc2dbf(str(dbc_path), str(dbf_path))

            # Stream DBF rows; only keep ones matching the procedure filter.
            # PROC_REA é geralmente armazenado como string "0409010499" (zero-padded).
            # Em alguns layouts antigos pode vir numérico — comparamos como string.
            procs_set = set(procs_filter)
            kept = []
            for rec in DBF(str(dbf_path), encoding="latin-1", lowernames=False, ignore_missing_memofile=True):
                proc = str(rec.get("PROC_REA", "")).strip().zfill(10)
                if proc in procs_set:
                    kept.append({k: rec.get(k) for k in KEEP_COLS})

            df = pd.DataFrame(kept, columns=list(KEEP_COLS))

        if df.empty:
            # Marca arquivo como processado escrevendo um parquet vazio (mas tipado).
            # Idempotência: próxima execução pula via .exists().
            empty = pd.DataFrame(
                columns=list(KEEP_COLS) + ["source_file", "estado", "ano", "mes"]
            )
            empty.to_parquet(out_path, index=False)
            return dbc_path.name, "empty", 0

        df["source_file"] = dbc_path.name
        df["estado"]      = meta["estado"]
        df["ano"]         = meta["ano"]
        df["mes"]         = meta["mes"]
        df.to_parquet(out_path, index=False)
        return dbc_path.name, "ok", len(df)

    except Exception as e:
        if out_path.exists():
            out_path.unlink()
        # Print do worker process — vai pro driver via stderr capture
        print(f"  ✗ {dbc_path.name}: {type(e).__name__}: {str(e)[:120]}")
        return dbc_path.name, "error", 0


# COMMAND ----------

dbc_dir     = Path(DBC_DIR)
parquet_dir = Path(PARQUET_DIR)
parquet_dir.mkdir(parents=True, exist_ok=True)

dbc_files = sorted(dbc_dir.glob("*.dbc"))
print(f"Found {len(dbc_files)} .dbc files. Parallel convert workers={WORKERS}…")

results = {"ok": 0, "cached": 0, "empty": 0, "error": 0}
n_rows_total = 0
with ProcessPoolExecutor(max_workers=WORKERS) as ex:
    futures = [ex.submit(convert_one, str(p), str(parquet_dir), PROCS_FILTER) for p in dbc_files]
    for i, fut in enumerate(as_completed(futures), 1):
        _, status, n_kept = fut.result()
        results[status] += 1
        n_rows_total += n_kept
        if i % 200 == 0 or i == len(dbc_files):
            print(f"  [{i:5d}/{len(dbc_files)}] {results}  rows_kept={n_rows_total:,}")

print(f"Convert done: {results}  rows kept across all files: {n_rows_total:,}")
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

print("\nLinhas por (ano, proc_rea):")
(
    spark.read.table(BRONZE_TABLE)
    .groupBy("ano", "PROC_REA")
    .count()
    .orderBy("ano", "PROC_REA")
    .show(60)
)

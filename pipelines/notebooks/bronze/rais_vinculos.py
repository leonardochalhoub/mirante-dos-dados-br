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
import ftplib
import time
from pathlib import Path
import py7zr

extracted = 0; skipped = 0; redownloaded = 0; quarantined = 0
Path(TXT_EXTRACTED).mkdir(parents=True, exist_ok=True)

# Quarentena: arquivos que continuam corrompidos mesmo após re-download
# vão pra cá pra não bloquear próximas runs e pra investigação manual depois.
QUARANTINE_DIR = Path(ZIPS_DIR) / "_bad"
QUARANTINE_DIR.mkdir(exist_ok=True)

# FTP de origem — deve bater com pipelines/notebooks/ingest/mte_rais.py
FTP_HOST   = "ftp.mtps.gov.br"
FTP_DIR    = "/pdet/microdados/RAIS"
FTP_TIMEOUT = 600


def _parse_year_from_local(name: str) -> int | None:
    """Local filenames são `<orig_stem>_<YYYY>.7z` (sufixo adicionado pelo ingest)."""
    m = re.search(r"_(\d{4})\.7z$", name, flags=re.I)
    return int(m.group(1)) if m else None


def _ftp_redownload(local_path: Path) -> bool:
    """Re-baixa um .7z específico do FTP PDET, sobrescrevendo o local.
    Retorna True se sucesso (size >= 1KB e bate com remote.size se conhecido)."""
    year = _parse_year_from_local(local_path.name)
    if year is None:
        print(f"      ⚠ não consegui extrair ano de {local_path.name}; pulando re-download")
        return False
    orig = re.sub(r"_(\d{4})\.7z$", ".7z", local_path.name, flags=re.I)
    tmp  = local_path.with_suffix(".7z.part")
    tmp.unlink(missing_ok=True)
    try:
        ftp = ftplib.FTP(FTP_HOST, timeout=FTP_TIMEOUT)
        ftp.login()
        ftp.cwd(f"{FTP_DIR}/{year}/")
        ftp.voidcmd("TYPE I")
        try:
            remote_size = ftp.size(orig) or 0
        except Exception:
            remote_size = 0
        with tmp.open("wb") as f:
            ftp.retrbinary(f"RETR {orig}", f.write)
        try: ftp.quit()
        except Exception: pass
        got = tmp.stat().st_size
        if got < 1024 or (remote_size and got < remote_size):
            print(f"      ⚠ re-download incompleto ({got:,} / {remote_size:,} bytes)")
            tmp.unlink(missing_ok=True)
            return False
        tmp.replace(local_path)
        print(f"      ↻ re-baixado: {got:,} bytes (remote {remote_size:,})")
        return True
    except Exception as e:
        tmp.unlink(missing_ok=True)
        print(f"      ⚠ re-download falhou: {type(e).__name__}: {str(e)[:160]}")
        return False


def _try_extract(zp: Path) -> tuple[bool, str]:
    """Retorna (ok, error_kind). error_kind ∈ {'', 'bad_archive', 'other'}."""
    try:
        with py7zr.SevenZipFile(zp, mode='r') as z:
            z.extractall(path=TXT_EXTRACTED)
        return True, ""
    except Exception as e:
        kind = type(e).__name__
        # py7zr.Bad7zFile é o canônico; outras libs podem retornar Bad7zfileError
        if kind in ("Bad7zFile", "Bad7zfileError") or "not a 7z file" in str(e).lower():
            print(f"    ✗ {kind}: {str(e)[:160]}")
            return False, "bad_archive"
        print(f"    ✗ {kind}: {str(e)[:200]}")
        return False, "other"

# DIAGNÓSTICO: o que está no volume antes da extração
print(f"\n=== DIAGNÓSTICO DOS VOLUMES ===")
print(f"ZIPS_DIR    : {ZIPS_DIR}")
try:
    zips_listing = list(Path(ZIPS_DIR).iterdir())
    print(f"  conteúdo total: {len(zips_listing)} entradas")
    for f in sorted(zips_listing)[:20]:
        size = f.stat().st_size if f.is_file() else 0
        print(f"    {f.name:50s}  {size:>14,} bytes")
    if len(zips_listing) > 20:
        print(f"    ... +{len(zips_listing)-20} entradas")
except FileNotFoundError:
    print(f"  ⚠ folder não existe!")
except Exception as e:
    print(f"  ⚠ erro listando: {e}")

print(f"\nTXT_EXTRACTED: {TXT_EXTRACTED}")
try:
    txts_listing = list(Path(TXT_EXTRACTED).iterdir())
    print(f"  conteúdo total: {len(txts_listing)} entradas")
    for f in sorted(txts_listing)[:20]:
        size = f.stat().st_size if f.is_file() else 0
        print(f"    {f.name:50s}  {size:>14,} bytes")
    if len(txts_listing) > 20:
        print(f"    ... +{len(txts_listing)-20} entradas")
except Exception as e:
    print(f"  (vazio ou erro: {e})")
print(f"=== FIM DIAGNÓSTICO ===\n")

zips = sorted(Path(ZIPS_DIR).glob("*.7z"))
print(f".7z encontrados pra extração: {len(zips)}")

if not zips:
    print(f"⚠ NENHUM .7z em {ZIPS_DIR}.")
    print(f"  Causa provável: ingest_mte_rais não baixou nada (PDET URL errada/mudou).")
    print(f"  Workarounds:")
    print(f"  1. Investigar URL_TEMPLATES em pipelines/notebooks/ingest/mte_rais.py")
    print(f"     (PDET reestruturou várias vezes desde 2023)")
    print(f"  2. Fazer upload manual dos .7z direto no Volume:")
    print(f"     UI Databricks → Catalog → mirante_prd → bronze → raw → mte/rais → Upload")
    print(f"  3. Ou copiar via CLI:")
    print(f"     databricks fs cp ./RAIS_VINC_PUB_BR_2021.7z dbfs:{ZIPS_DIR}/")
    dbutils.notebook.exit("SKIPPED: no .7z files to extract")

for zp in zips:
    # Marcador `.done` = extraído com sucesso. Marcador `.bad` = quarentena prévia
    # (não tenta de novo até force_reconvert=true, pra não loopar em fonte ruim).
    marker_ok  = Path(TXT_EXTRACTED) / f"_{zp.stem}.done"
    marker_bad = Path(TXT_EXTRACTED) / f"_{zp.stem}.bad"
    if marker_ok.exists() and not FORCE_RECONVERT:
        skipped += 1; continue
    if marker_bad.exists() and not FORCE_RECONVERT:
        print(f"  ⊘ {zp.name} já em quarentena (.bad marker); use force_reconvert=true pra retentar")
        quarantined += 1; continue

    print(f"  extraindo {zp.name} ({zp.stat().st_size:,} bytes)...")
    ok, err = _try_extract(zp)
    if ok:
        marker_ok.write_text("ok"); extracted += 1
        print(f"    ✓ ok")
        continue

    # Bad7zFile → deleta, re-baixa, tenta uma vez. Outros erros: não tenta re-download.
    if err != "bad_archive":
        continue

    print(f"    → arquivo corrompido; deletando e re-baixando do FTP {FTP_HOST}…")
    try:
        zp.unlink()
    except Exception as e:
        print(f"      ⚠ falha ao deletar: {type(e).__name__}: {e}")
        continue

    if not _ftp_redownload(zp):
        # Não conseguimos re-baixar — registra como bad e segue
        marker_bad.write_text(f"redownload_failed at {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
        quarantined += 1
        continue

    redownloaded += 1
    print(f"    re-tentando extração após re-download…")
    ok, err = _try_extract(zp)
    if ok:
        marker_ok.write_text("ok"); extracted += 1
        print(f"    ✓ ok (após re-download)")
        continue

    # Ainda ruim depois do re-download → quarentena (fonte do PDET deve estar mesmo corrompida)
    bad_dest = QUARANTINE_DIR / zp.name
    try:
        zp.replace(bad_dest)
        print(f"    ⚠ quarentena → {bad_dest}")
    except Exception as e:
        print(f"      ⚠ falha ao mover pra quarentena: {type(e).__name__}: {e}")
    marker_bad.write_text(f"bad_after_redownload at {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
    quarantined += 1

# Lista TODAS extensões pós-extração — alguns .7z contém .csv, .TXT, .dat, etc.
all_after = sorted(Path(TXT_EXTRACTED).iterdir())
by_ext = {}
for f in all_after:
    if f.is_file():
        by_ext.setdefault(f.suffix.lower(), 0)
        by_ext[f.suffix.lower()] += 1
print(f"\nApós extração ({extracted} novos, {skipped} skipped, "
      f"{redownloaded} re-baixados, {quarantined} em quarentena):")
for ext, n in sorted(by_ext.items(), key=lambda kv: -kv[1]):
    print(f"  {ext or '(no ext)':15s}: {n} arquivos")

txts = sorted(Path(TXT_EXTRACTED).glob("*.txt"))
if not txts:
    # Tenta extensões alternativas comuns em datasets PDET históricos
    for alt_ext in ('*.TXT', '*.csv', '*.CSV', '*.dat', '*.DAT'):
        alts = sorted(Path(TXT_EXTRACTED).glob(alt_ext))
        if alts:
            print(f"  ⚠ encontrei {len(alts)} {alt_ext} (não .txt) — ajuste a glob no notebook")
            break
    print("⚠ Nenhum .txt processável. Verifique diagnóstico acima.")
    dbutils.notebook.exit("SKIPPED: no .txt files after extraction")

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

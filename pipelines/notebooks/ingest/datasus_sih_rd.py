# Databricks notebook source
# MAGIC %md
# MAGIC # ingest · datasus_sih_rd
# MAGIC
# MAGIC Baixa todos os arquivos `RD<UF><YYMM>.dbc` (SIH-SUS / AIH Reduced) do FTP
# MAGIC DATASUS para `/Volumes/<catalog>/bronze/raw/datasus/sih_rd/`. SIH-RD é o
# MAGIC microdado de internação hospitalar (uma linha por AIH aprovada).
# MAGIC
# MAGIC ## Layout do FTP DATASUS (importante!)
# MAGIC
# MAGIC O DATASUS divide o histórico SIH-SUS em dois "layouts" (estruturas de
# MAGIC arquivos diferentes), com **folders distintos**:
# MAGIC
# MAGIC | Folder                                                       | Janela        | Arquivos RD |
# MAGIC | ------------------------------------------------------------ | ------------- | ----------- |
# MAGIC | `/dissemin/publicos/SIHSUS/199201_200712/Dados/`             | 1992-01..2007 | ~5.165      |
# MAGIC | `/dissemin/publicos/SIHSUS/200801_/Dados/`                   | 2008-01..hoje | ~5.883+     |
# MAGIC
# MAGIC Em ambos, RD-files ficam **direto no `/Dados/`** (não em `/Dados/RD/`),
# MAGIC misturados com outros tipos (RJ, SP, ER). A regex filtra pelo prefixo `RD`.
# MAGIC
# MAGIC ## Parâmetros
# MAGIC - `min_year` / `max_year` / `max_month`: janela temporal (default 1992..2025-12 = TUDO)
# MAGIC - `volume_dir`: destino no Volume
# MAGIC - `workers`: paralelismo FTP (DATASUS aceita ~100)

# COMMAND ----------

dbutils.widgets.text("min_year",   "1992")   # SIH-RD começa jan/1992 no folder legacy
dbutils.widgets.text("max_year",   "2025")
dbutils.widgets.text("max_month",  "12")
dbutils.widgets.text("volume_dir", "/Volumes/mirante_prd/bronze/raw/datasus/sih_rd")
dbutils.widgets.text("workers",    "100")

MIN_YEAR   = int(dbutils.widgets.get("min_year"))
MAX_YEAR   = int(dbutils.widgets.get("max_year"))
MAX_MONTH  = int(dbutils.widgets.get("max_month"))
VOLUME_DIR = dbutils.widgets.get("volume_dir")
WORKERS    = int(dbutils.widgets.get("workers"))

print(f"window=[{MIN_YEAR}-01..{MAX_YEAR}-{MAX_MONTH:02d}]  dest={VOLUME_DIR}  workers={WORKERS}")

# COMMAND ----------

import ftplib
import re
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

HOST          = "ftp.datasus.gov.br"
FTP_TIMEOUT   = 600          # RD files são maiores que EQ → mais tolerância
MAX_RETRIES   = 3
RETRY_DELAY_S = 5

# Os dois folders SIH-SUS no FTP DATASUS — cada um cobre uma janela distinta.
# Seria conveniente concatenar tudo, mas o DATASUS mantém estruturas separadas:
# o layout pré-2008 tinha colunas diferentes (sem MUNIC_RES detalhado, etc.).
# Para ingestão bruta, ambos servem; o filtro de procedimento na bronze
# mascara as diferenças de layout.
FTP_SOURCES = [
    {"path": "/dissemin/publicos/SIHSUS/199201_200712/Dados/", "year_min": 1992, "year_max": 2007},
    {"path": "/dissemin/publicos/SIHSUS/200801_/Dados/",       "year_min": 2008, "year_max": 9999},
]

# RD<UF><YY><MM>.dbc — ex: RDSP1503.dbc = SP, mar/2015
RE_RD_FILE = re.compile(r"^RD(?P<uf>[A-Z]{2})(?P<yy>\d{2})(?P<mm>\d{2})\.dbc$", re.IGNORECASE)


def yy_to_year(yy: int) -> int:
    """yy=92→1992, yy=07→2007, yy=08→2008, yy=25→2025."""
    return 2000 + yy if yy < 50 else 1900 + yy


def is_within_window(year: int, month: int) -> bool:
    if year < MIN_YEAR or year > MAX_YEAR:
        return False
    if year == MAX_YEAR and month > MAX_MONTH:
        return False
    return True


def download_one(filename: str, ftp_dir: str, out_dir: Path) -> tuple[str, str]:
    """Returns (filename, status) where status ∈ {'ok','cached','error'}."""
    dest = out_dir / filename
    if dest.exists() and dest.stat().st_size > 0:
        return filename, "cached"

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            ftp = ftplib.FTP(HOST, timeout=FTP_TIMEOUT)
            ftp.login()
            ftp.cwd(ftp_dir)
            with open(dest, "wb") as f:
                ftp.retrbinary(f"RETR {filename}", f.write)
            ftp.quit()
            if dest.stat().st_size > 0:
                return filename, "ok"
            dest.unlink()
        except (ftplib.all_errors, EOFError, OSError):
            if attempt < MAX_RETRIES:
                time.sleep(RETRY_DELAY_S * attempt)
                continue
            if dest.exists():
                dest.unlink()
            return filename, "error"
    return filename, "error"


def list_rd_files(ftp_dir: str) -> list[str]:
    """List RD files in a single FTP folder."""
    ftp = ftplib.FTP(HOST, timeout=FTP_TIMEOUT)
    ftp.login()
    ftp.cwd(ftp_dir)
    all_names = ftp.nlst()
    ftp.quit()
    return [n for n in all_names if RE_RD_FILE.match(n)]


# COMMAND ----------

out_dir = Path(VOLUME_DIR)
out_dir.mkdir(parents=True, exist_ok=True)

# Build the (filename, ftp_dir) target list across both folders
targets: list[tuple[str, str]] = []  # (filename, ftp_dir)
for src in FTP_SOURCES:
    print(f"Listing FTP {HOST}{src['path']}…")
    rd_files = list_rd_files(src["path"])
    print(f"  found {len(rd_files)} RD files in this folder")
    for name in rd_files:
        m = RE_RD_FILE.match(name)
        if not m:
            continue
        year = yy_to_year(int(m.group("yy")))
        month = int(m.group("mm"))
        # Only take the file from the folder whose year_range covers it
        # (avoids double-counting if a year overlaps — shouldn't happen but defensive)
        if year < src["year_min"] or year > src["year_max"]:
            continue
        if is_within_window(year, month):
            targets.append((name, src["path"]))

# Sort by filename so progress output is friendly
targets.sort()
print(f"\nTotal target files in window [{MIN_YEAR}-01..{MAX_YEAR}-{MAX_MONTH:02d}]: {len(targets)}")

# COMMAND ----------

results = {"ok": 0, "cached": 0, "error": 0}
errors = []
with ThreadPoolExecutor(max_workers=WORKERS) as ex:
    futures = [ex.submit(download_one, name, ftp_dir, out_dir) for (name, ftp_dir) in targets]
    for i, fut in enumerate(as_completed(futures), 1):
        name, status = fut.result()
        results[status] += 1
        if status == "error":
            errors.append(name)
        if i % 200 == 0 or i == len(targets):
            print(f"  [{i:5d}/{len(targets)}] ok={results['ok']} cached={results['cached']} err={results['error']}")

print()
print(f"Final: {results}")
if errors:
    print(f"Errors in {len(errors)} files (first 10): {errors[:10]}")

n_dbc_now = len(list(out_dir.glob("*.dbc")))
print(f"Total .dbc no Volume: {n_dbc_now}")

# Databricks notebook source
# MAGIC %md
# MAGIC # ingest · datasus_sih_rd
# MAGIC
# MAGIC Baixa todos os arquivos `RD<UF><YYMM>.dbc` (SIH-SUS / AIH Reduced) do FTP
# MAGIC DATASUS para `/Volumes/<catalog>/bronze/raw/datasus/sih_rd/`. São os
# MAGIC microdados de internação hospitalar — uma linha por AIH aprovada.
# MAGIC
# MAGIC FTP: `ftp.datasus.gov.br/dissemin/publicos/SIHSUS/200801_/Dados/RD/`
# MAGIC
# MAGIC Volume típico: 27 UF × 12 mes × N anos. Para janela 2015–2024:
# MAGIC ~3.240 arquivos, ~12 GB (RD é uma das maiores bases do DATASUS).
# MAGIC
# MAGIC Args:
# MAGIC - `min_year` / `max_year` / `max_month`: janela temporal (default 2015..2024-12)
# MAGIC - `volume_dir`: destino no Volume
# MAGIC - `workers`: paralelismo FTP (DATASUS aceita ~100)

# COMMAND ----------

dbutils.widgets.text("min_year",   "2015")
dbutils.widgets.text("max_year",   "2024")
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
RD_DIR        = "/dissemin/publicos/SIHSUS/200801_/Dados/RD/"
FTP_TIMEOUT   = 600          # RD files são maiores que EQ → mais tolerância
MAX_RETRIES   = 3
RETRY_DELAY_S = 5

# Convenção SIH: RD<UF><YY><MM>.dbc — ex: RDSP1503.dbc = SP, mar/2015
RE_RD_FILE = re.compile(r"^RD(?P<uf>[A-Z]{2})(?P<yy>\d{2})(?P<mm>\d{2})\.dbc$", re.IGNORECASE)


def yy_to_year(yy: int) -> int:
    # SIH histórica tem arquivos desde 1992 (formato antigo, fora do escopo aqui).
    # 200801_ tem yy=08+ → 2008+. Janela ainda comporta 2-digit unambiguous.
    return 2000 + yy if yy < 50 else 1900 + yy


def is_within_window(year: int, month: int) -> bool:
    if year < MIN_YEAR or year > MAX_YEAR:
        return False
    if year == MAX_YEAR and month > MAX_MONTH:
        return False
    return True


def download_one(filename: str, out_dir: Path) -> tuple[str, str]:
    """Returns (filename, status) where status ∈ {'ok','cached','error'}."""
    dest = out_dir / filename
    if dest.exists() and dest.stat().st_size > 0:
        return filename, "cached"

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            ftp = ftplib.FTP(HOST, timeout=FTP_TIMEOUT)
            ftp.login()
            ftp.cwd(RD_DIR)
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


# COMMAND ----------

out_dir = Path(VOLUME_DIR)
out_dir.mkdir(parents=True, exist_ok=True)

print(f"Listing FTP {HOST}{RD_DIR}…")
ftp = ftplib.FTP(HOST, timeout=FTP_TIMEOUT)
ftp.login()
ftp.cwd(RD_DIR)
all_names = ftp.nlst()
ftp.quit()
print(f"FTP has {len(all_names)} entries (todos formatos)")

targets = []
for n in all_names:
    m = RE_RD_FILE.match(n)
    if not m:
        continue
    yy = int(m.group("yy"))
    mm = int(m.group("mm"))
    year = yy_to_year(yy)
    if is_within_window(year, mm):
        targets.append(n)
targets.sort()
print(f"Target files in window: {len(targets)}")

# COMMAND ----------

results = {"ok": 0, "cached": 0, "error": 0}
errors = []
with ThreadPoolExecutor(max_workers=WORKERS) as ex:
    futures = [ex.submit(download_one, n, out_dir) for n in targets]
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

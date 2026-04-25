# Databricks notebook source
# MAGIC %md
# MAGIC # ingest · datasus_cnes_eq
# MAGIC
# MAGIC Baixa todos os arquivos `EQ<UF><YYMM>.dbc` do FTP DATASUS para
# MAGIC `/Volumes/<catalog>/bronze/raw/datasus/cnes_eq/`. ~6.6K arquivos (~1.5 GB).
# MAGIC
# MAGIC - 100 workers paralelos (FTP DATASUS aceita)
# MAGIC - Idempotente: pula arquivos que já existem com size > 0
# MAGIC - Cap superior: `(year, month) <= MAX_YEAR/MAX_MONTH` (default 2025-12)

# COMMAND ----------

dbutils.widgets.text("max_year",   "2025")
dbutils.widgets.text("max_month",  "12")
dbutils.widgets.text("volume_dir", "/Volumes/mirante_prd/bronze/raw/datasus/cnes_eq")
dbutils.widgets.text("workers",    "100")

MAX_YEAR   = int(dbutils.widgets.get("max_year"))
MAX_MONTH  = int(dbutils.widgets.get("max_month"))
VOLUME_DIR = dbutils.widgets.get("volume_dir")
WORKERS    = int(dbutils.widgets.get("workers"))

print(f"max=({MAX_YEAR},{MAX_MONTH})  dest={VOLUME_DIR}  workers={WORKERS}")

# COMMAND ----------

import ftplib
import re
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

HOST          = "ftp.datasus.gov.br"
EQ_DIR        = "/dissemin/publicos/CNES/200508_/Dados/EQ/"
FTP_TIMEOUT   = 300
MAX_RETRIES   = 3
RETRY_DELAY_S = 5

RE_EQ_FILE = re.compile(r"^EQ(?P<uf>[A-Z]{2})(?P<yy>\d{2})(?P<mm>\d{2})\.dbc$", re.IGNORECASE)


def is_within_max(year: int, month: int) -> bool:
    return (year, month) <= (MAX_YEAR, MAX_MONTH)


def download_one(filename: str, out_dir: Path) -> tuple[str, str]:
    """Returns (filename, status) where status ∈ {'ok','cached','error'}."""
    dest = out_dir / filename
    if dest.exists() and dest.stat().st_size > 0:
        return filename, "cached"

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            ftp = ftplib.FTP(HOST, timeout=FTP_TIMEOUT)
            ftp.login()
            ftp.cwd(EQ_DIR)
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

print(f"Listing FTP {HOST}{EQ_DIR}…")
ftp = ftplib.FTP(HOST, timeout=FTP_TIMEOUT)
ftp.login()
ftp.cwd(EQ_DIR)
all_names = ftp.nlst()
ftp.quit()
print(f"FTP has {len(all_names)} files total")

targets = []
for n in all_names:
    m = RE_EQ_FILE.match(n)
    if not m:
        continue
    yy = int(m.group("yy"))
    mm = int(m.group("mm"))
    year = 2000 + yy
    if is_within_max(year, mm):
        targets.append(n)
targets.sort()
print(f"Target files (≤ {MAX_YEAR}-{MAX_MONTH:02d}): {len(targets)}")

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
        if i % 500 == 0 or i == len(targets):
            print(f"  [{i:5d}/{len(targets)}] ok={results['ok']} cached={results['cached']} err={results['error']}")

print()
print(f"Final: {results}")
if errors:
    print(f"Errors in {len(errors)} files (first 10): {errors[:10]}")

n_dbc_now = len(list(out_dir.glob("*.dbc")))
print(f"Total .dbc no Volume: {n_dbc_now}")

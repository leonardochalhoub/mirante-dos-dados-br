# Databricks notebook source
# MAGIC %md
# MAGIC # ingest · cgu_emendas
# MAGIC
# MAGIC Baixa os ZIPs anuais de Emendas Parlamentares do Portal da Transparência (CGU)
# MAGIC e grava em UC Volume com filename original (já contém o ano).
# MAGIC
# MAGIC Fonte: https://portaldatransparencia.gov.br/download-de-dados/emendas
# MAGIC
# MAGIC | param | default |
# MAGIC | --- | --- |
# MAGIC | `years`       | `2014-2025` |
# MAGIC | `volume_dir`  | `/Volumes/mirante_prd/bronze/raw/cgu/emendas` |
# MAGIC | `workers`     | `4` |
# MAGIC
# MAGIC **Nota**: a URL exata e estrutura do ZIP/CSV podem variar. Esse notebook tenta
# MAGIC dois patterns conhecidos. Se ambos falharem, ajusta-se aqui.

# COMMAND ----------

dbutils.widgets.text("years",       "2014-2025")
dbutils.widgets.text("volume_dir",  "/Volumes/mirante_prd/bronze/raw/cgu/emendas")
dbutils.widgets.text("workers",     "4")

YEARS_EXPR = dbutils.widgets.get("years")
VOLUME_DIR = dbutils.widgets.get("volume_dir")
WORKERS    = int(dbutils.widgets.get("workers"))

print(f"years={YEARS_EXPR}  dest={VOLUME_DIR}  workers={WORKERS}")

# COMMAND ----------

import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import requests

ZIP_MAGIC       = b"PK\x03\x04"
ZIP_MAGIC_EMPTY = b"PK\x05\x06"
HEADERS         = {"User-Agent": "mirante-dos-dados/1.0", "Accept": "*/*"}

# Two URL patterns to try (CGU has changed format over time)
URL_PATTERNS = [
    "https://portaldatransparencia.gov.br/download-de-dados/emendas/{year}",
    "https://portaldatransparencia.gov.br/download-de-dados/emendas-pagas/{year}",
]


def parse_years(expr: str) -> list[int]:
    out: set[int] = set()
    for part in (p.strip() for p in expr.split(",") if p.strip()):
        if "-" in part:
            a, b = part.split("-", 1)
            out.update(range(int(a), int(b) + 1))
        else:
            out.add(int(part))
    return sorted(out)


def is_valid_zip(p: Path) -> bool:
    try:
        with p.open("rb") as f: head = f.read(4)
        return head in (ZIP_MAGIC, ZIP_MAGIC_EMPTY)
    except OSError:
        return False


def fetch(year: int, dest_dir: Path, timeout: int = 200, retries: int = 3) -> tuple[str, str]:
    """Returns (label, status) ∈ {'ok','cached','missing','error'}."""
    label = f"emendas_{year}"
    dest  = dest_dir / f"emendas_{year}.zip"
    if dest.exists() and dest.stat().st_size > 0 and is_valid_zip(dest):
        return label, "cached"
    dest.parent.mkdir(parents=True, exist_ok=True)
    tmp = dest.with_suffix(dest.suffix + ".part")

    last_url = None
    for url_pattern in URL_PATTERNS:
        url = url_pattern.format(year=year)
        last_url = url
        for attempt in range(1, retries + 1):
            try:
                with requests.get(url, headers=HEADERS, stream=True, timeout=timeout, allow_redirects=True) as r:
                    if r.status_code != 200:
                        break  # try next URL pattern
                    written = 0
                    with tmp.open("wb") as f:
                        for chunk in r.iter_content(chunk_size=1 << 20):
                            if chunk:
                                f.write(chunk); written += len(chunk)
                    if written < 4 or not is_valid_zip(tmp):
                        tmp.unlink(missing_ok=True)
                        break
                    tmp.replace(dest)
                    return label, "ok"
            except (requests.HTTPError, requests.ConnectionError, requests.Timeout):
                if attempt < retries:
                    time.sleep(1.5)
                else:
                    break
    if tmp.exists():
        tmp.unlink()
    print(f"  ✗ {label} — last url tried: {last_url}")
    return label, "missing"

# COMMAND ----------

dest_dir = Path(VOLUME_DIR)
dest_dir.mkdir(parents=True, exist_ok=True)

years = parse_years(YEARS_EXPR)
print(f"Tentando {len(years)} anos: {years}")

results = {"ok": 0, "cached": 0, "missing": 0, "error": 0}
with ThreadPoolExecutor(max_workers=WORKERS) as ex:
    futures = [ex.submit(fetch, y, dest_dir) for y in years]
    for fut in as_completed(futures):
        _, status = fut.result()
        results[status] += 1

print(f"Resultado: {results}")
print(f"ZIPs no Volume agora: {len(sorted(dest_dir.glob('*.zip')))}")

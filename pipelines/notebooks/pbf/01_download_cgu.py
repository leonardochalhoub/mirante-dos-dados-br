# Databricks notebook source
# MAGIC %md
# MAGIC # pbf · 01 · download CGU
# MAGIC
# MAGIC Pré-DLT task: baixa os ZIPs mensais do Portal da Transparência (CGU) e grava em UC Volume.
# MAGIC
# MAGIC Programas:
# MAGIC - **PBF** (Bolsa Família): jan/2013 – nov/2021
# MAGIC - **AUX_BR** (Auxílio Brasil): nov/2021 – fev/2023
# MAGIC - **NBF** (Novo Bolsa Família): mar/2023 em diante
# MAGIC
# MAGIC ## Parâmetros
# MAGIC
# MAGIC | param | default | descrição |
# MAGIC | --- | --- | --- |
# MAGIC | `pbf_years`  | `2013-2021` | anos pra baixar do programa PBF |
# MAGIC | `aux_years`  | `2021-2023` | anos pra Auxílio Brasil |
# MAGIC | `nbf_years`  | `2023-2026` | anos pra Novo Bolsa Família |
# MAGIC | `volume_path`| `/Volumes/mirante/bronze/raw/cgu/pbf` | destino dos ZIPs |
# MAGIC | `workers`    | `4`         | downloads paralelos |
# MAGIC
# MAGIC **Idempotência**: ZIPs válidos já no Volume são pulados (checagem por magic bytes).

# COMMAND ----------

dbutils.widgets.text("pbf_years",   "2013-2021")
dbutils.widgets.text("aux_years",   "2021-2023")
dbutils.widgets.text("nbf_years",   "2023-2026")
dbutils.widgets.text("volume_path", "/Volumes/mirante/bronze/raw/cgu/pbf")
dbutils.widgets.text("workers",     "4")

PBF_YEARS   = dbutils.widgets.get("pbf_years")
AUX_YEARS   = dbutils.widgets.get("aux_years")
NBF_YEARS   = dbutils.widgets.get("nbf_years")
VOLUME_PATH = dbutils.widgets.get("volume_path")
WORKERS     = int(dbutils.widgets.get("workers"))

print(f"pbf={PBF_YEARS}  aux={AUX_YEARS}  nbf={NBF_YEARS}  dest={VOLUME_PATH}  workers={WORKERS}")

# COMMAND ----------

import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import requests

ZIP_MAGIC       = b"PK\x03\x04"
ZIP_MAGIC_EMPTY = b"PK\x05\x06"
HEADERS         = {"User-Agent": "mirante-dos-dados/1.0", "Accept": "*/*"}

CGU_BASES = {
    "PBF":    "http://www.portaltransparencia.gov.br/download-de-dados/bolsa-familia-pagamentos/",
    "AUX_BR": "https://portaldatransparencia.gov.br/download-de-dados/auxilio-brasil/",
    "NBF":    "https://portaldatransparencia.gov.br/download-de-dados/novo-bolsa-familia/",
}


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
        with p.open("rb") as f:
            head = f.read(4)
        return head in (ZIP_MAGIC, ZIP_MAGIC_EMPTY)
    except OSError:
        return False


def fetch(prefix: str, year: int, month: int, dest_dir: Path,
          timeout: int = 200, retries: int = 3) -> tuple[str, str]:
    """Returns (label, status) where status ∈ {'ok','cached','missing','error'}."""
    url   = f"{CGU_BASES[prefix]}{year}{month:02d}"
    dest  = dest_dir / f"{prefix}_{year}_{month:02d}.zip"
    label = f"{prefix} {year}-{month:02d}"

    if dest.exists() and dest.stat().st_size > 0 and is_valid_zip(dest):
        return label, "cached"

    dest.parent.mkdir(parents=True, exist_ok=True)
    tmp = dest.with_suffix(dest.suffix + ".part")

    for attempt in range(1, retries + 1):
        try:
            with requests.get(url, headers=HEADERS, stream=True, timeout=timeout, allow_redirects=True) as r:
                if r.status_code != 200:
                    return label, "missing"
                written = 0
                with tmp.open("wb") as f:
                    for chunk in r.iter_content(chunk_size=1 << 20):
                        if chunk:
                            f.write(chunk)
                            written += len(chunk)
                if written < 4 or not is_valid_zip(tmp):
                    tmp.unlink(missing_ok=True)
                    return label, "missing"
                tmp.replace(dest)
                return label, "ok"
        except (requests.HTTPError, requests.ConnectionError, requests.Timeout) as e:
            if attempt == retries:
                tmp.unlink(missing_ok=True)
                return label, "error"
            time.sleep(1.5)
    return label, "error"

# COMMAND ----------

dest_dir = Path(VOLUME_PATH)
dest_dir.mkdir(parents=True, exist_ok=True)

specs = []
for prefix, years_expr in (("PBF", PBF_YEARS), ("AUX_BR", AUX_YEARS), ("NBF", NBF_YEARS)):
    for y in parse_years(years_expr):
        for m in range(1, 13):
            specs.append((prefix, y, m))

print(f"Tentando {len(specs)} (prefix, year, month) combos…")

results = {"ok": 0, "cached": 0, "missing": 0, "error": 0}
errors  = []
with ThreadPoolExecutor(max_workers=WORKERS) as ex:
    futures = [ex.submit(fetch, p, y, m, dest_dir) for (p, y, m) in specs]
    for fut in as_completed(futures):
        label, status = fut.result()
        results[status] += 1
        if status == "error":
            errors.append(label)

print(f"Resultado: {results}")
if errors:
    print(f"Errors em {len(errors)} downloads (primeiros 10): {errors[:10]}")

zips_total = sorted(dest_dir.glob("*.zip"))
print(f"Total de ZIPs no Volume agora: {len(zips_total)}")

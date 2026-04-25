# Databricks notebook source
# MAGIC %md
# MAGIC # ingest · ibge_populacao
# MAGIC
# MAGIC Baixa o JSON do IBGE/SIDRA Agregados (6579, var 9324) e grava em UC Volume com
# MAGIC **filename timestamped** — Auto Loader detecta cada novo arquivo como uma nova
# MAGIC ingestão, alimentando o append-only Delta bronze.
# MAGIC
# MAGIC | param | default |
# MAGIC | --- | --- |
# MAGIC | `start_year`  | 2013 |
# MAGIC | `end_year`    | 2026 |
# MAGIC | `volume_dir`  | `/Volumes/mirante_prd/bronze/raw/ibge` |

# COMMAND ----------

dbutils.widgets.text("start_year",   "2013")
dbutils.widgets.text("end_year",     "2026")
dbutils.widgets.text("volume_dir",   "/Volumes/mirante_prd/bronze/raw/ibge")
dbutils.widgets.text("fallback_url", "https://raw.githubusercontent.com/leonardochalhoub/mirante-dos-dados-br/main/data/fallback/ibge_populacao_uf.json")

START_YEAR   = int(dbutils.widgets.get("start_year"))
END_YEAR     = int(dbutils.widgets.get("end_year"))
VOLUME_DIR   = dbutils.widgets.get("volume_dir")
FALLBACK_URL = dbutils.widgets.get("fallback_url")

print(f"start_year={START_YEAR} end_year={END_YEAR} dest={VOLUME_DIR}")
print(f"fallback_url={FALLBACK_URL}")

# COMMAND ----------

import json
import time
from datetime import datetime, timezone
from pathlib import Path
import requests

if START_YEAR > END_YEAR:
    raise ValueError(f"start_year ({START_YEAR}) > end_year ({END_YEAR})")

url = (
    "https://servicodados.ibge.gov.br/api/v3/agregados/6579/"
    f"periodos/{START_YEAR}-{END_YEAR}/variaveis/9324"
    "?localidades=N3[all]"
)
print(f"GET {url}")

# IBGE API is flaky — retry with backoff on timeouts/connection errors
MAX_ATTEMPTS = 5
TIMEOUT      = 180   # 3 minutes per attempt
payload      = None
source       = None

for attempt in range(1, MAX_ATTEMPTS + 1):
    try:
        r = requests.get(url, headers={"User-Agent": "mirante-dos-dados/1.0"}, timeout=TIMEOUT)
        r.raise_for_status()
        payload = r.json()
        source  = f"ibge_api_attempt_{attempt}"
        print(f"✔ attempt {attempt}/{MAX_ATTEMPTS}: got {len(str(payload)):,} chars from IBGE")
        break
    except (requests.ConnectTimeout, requests.ReadTimeout, requests.ConnectionError, requests.HTTPError) as e:
        print(f"  attempt {attempt}/{MAX_ATTEMPTS} failed: {type(e).__name__}: {str(e)[:120]}")
        if attempt < MAX_ATTEMPTS:
            sleep_s = 2 ** attempt
            print(f"  backing off {sleep_s}s before retry…")
            time.sleep(sleep_s)

# All IBGE attempts failed — fall back to the static baked-in JSON shipped in the repo.
# Has 27 UFs × 13 years (2013-2025) of population data extracted from the previous
# successful pipeline run. Pipeline can continue; next refresh will retry IBGE.
if payload is None:
    print(f"⚠ All {MAX_ATTEMPTS} IBGE attempts failed. Falling back to {FALLBACK_URL}")
    r = requests.get(FALLBACK_URL, timeout=60)
    r.raise_for_status()
    payload = r.json()
    source  = "github_fallback"
    print(f"✔ fallback loaded ({len(str(payload)):,} chars)")

print(f"data source: {source}")

# Sanity check
years_seen = set()
for item in payload:
    for res in item.get("resultados", []):
        for s in res.get("series", []):
            for ano_str, v in (s.get("serie") or {}).items():
                if v not in (None, "", "..."):
                    years_seen.add(int(ano_str))
print(f"IBGE retornou anos: {sorted(years_seen)}")
print(f"Anos solicitados não retornados: {sorted(set(range(START_YEAR, END_YEAR + 1)) - years_seen)}")

# COMMAND ----------

# Timestamped filename — Auto Loader treats each new file as a new ingestion event
ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
dest = Path(VOLUME_DIR) / f"populacao_uf__{ts}.json"
dest.parent.mkdir(parents=True, exist_ok=True)
dest.write_text(json.dumps(payload), encoding="utf-8")
print(f"✔ {dest}  ({dest.stat().st_size:,} bytes)")

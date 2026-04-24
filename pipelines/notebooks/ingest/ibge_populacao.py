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

dbutils.widgets.text("start_year",  "2013")
dbutils.widgets.text("end_year",    "2026")
dbutils.widgets.text("volume_dir",  "/Volumes/mirante_prd/bronze/raw/ibge")

START_YEAR = int(dbutils.widgets.get("start_year"))
END_YEAR   = int(dbutils.widgets.get("end_year"))
VOLUME_DIR = dbutils.widgets.get("volume_dir")

print(f"start_year={START_YEAR} end_year={END_YEAR} dest={VOLUME_DIR}")

# COMMAND ----------

import json
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

r = requests.get(url, headers={"User-Agent": "mirante-dos-dados/1.0"}, timeout=60)
r.raise_for_status()
payload = r.json()

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

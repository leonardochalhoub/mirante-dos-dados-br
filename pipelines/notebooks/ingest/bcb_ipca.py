# Databricks notebook source
# MAGIC %md
# MAGIC # ingest · bcb_ipca
# MAGIC
# MAGIC Baixa série SGS 433 (IPCA mensal %) e grava com filename timestamped pra Auto Loader.

# COMMAND ----------

dbutils.widgets.text("volume_dir", "/Volumes/mirante_prd/bronze/raw/bcb")
VOLUME_DIR = dbutils.widgets.get("volume_dir")
print(f"dest={VOLUME_DIR}")

# COMMAND ----------

import json
from datetime import datetime, timezone
from pathlib import Path
import requests

url = "https://api.bcb.gov.br/dados/serie/bcdata.sgs.433/dados?formato=json"
print(f"GET {url}")

r = requests.get(url, headers={"User-Agent": "mirante-dos-dados/1.0"}, timeout=60)
r.raise_for_status()
payload = r.json()
print(f"BCB retornou {len(payload)} pontos. Último: {payload[-1] if payload else 'vazio'}")

# COMMAND ----------

ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
dest = Path(VOLUME_DIR) / f"ipca_mensal__{ts}.json"
dest.parent.mkdir(parents=True, exist_ok=True)
dest.write_text(json.dumps(payload), encoding="utf-8")
print(f"✔ {dest}  ({dest.stat().st_size:,} bytes)")

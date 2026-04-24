# Databricks notebook source
# MAGIC %md
# MAGIC # ipca_deflators_2021 · 01 · download BCB
# MAGIC
# MAGIC Pré-DLT task: baixa o JSON da API BCB (SGS série 433 — IPCA mensal %).
# MAGIC
# MAGIC **Independente.** Roda sozinho quando você quiser refrescar o IPCA
# MAGIC (mensal pra acompanhar publicação do IBGE → ranking IPCA).
# MAGIC
# MAGIC ## Parâmetros
# MAGIC
# MAGIC | param | default | descrição |
# MAGIC | --- | --- | --- |
# MAGIC | `volume_path` | `/Volumes/mirante/bronze/raw/bcb` | destino do JSON |

# COMMAND ----------

dbutils.widgets.text("volume_path", "/Volumes/mirante_prd/bronze/raw/bcb")
VOLUME_PATH = dbutils.widgets.get("volume_path")
print(f"dest={VOLUME_PATH}")

# COMMAND ----------

import json
from pathlib import Path
import requests

url = "https://api.bcb.gov.br/dados/serie/bcdata.sgs.433/dados?formato=json"
print(f"GET {url}")

r = requests.get(url, headers={"User-Agent": "mirante-dos-dados/1.0"}, timeout=60)
r.raise_for_status()
payload = r.json()
print(f"BCB retornou {len(payload)} pontos mensais (jan/1980 em diante)")
print(f"Último ponto: {payload[-1] if payload else 'vazio'}")

dest_dir  = Path(VOLUME_PATH)
dest_dir.mkdir(parents=True, exist_ok=True)
dest_file = dest_dir / "ipca_mensal.json"
dest_file.write_text(json.dumps(payload), encoding="utf-8")
print(f"Salvo em {dest_file}  ({dest_file.stat().st_size:,} bytes)")

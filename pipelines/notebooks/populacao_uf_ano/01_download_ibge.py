# Databricks notebook source
# MAGIC %md
# MAGIC # populacao_uf_ano · 01 · download IBGE
# MAGIC
# MAGIC Pré-DLT task: baixa o JSON da API IBGE/SIDRA e grava em UC Volume.
# MAGIC
# MAGIC **Independente de qualquer outra dim.** Pode ser executada sozinha quando você
# MAGIC quiser estender o período (ex: incluir 2027 quando IBGE publicar).
# MAGIC
# MAGIC ## Parâmetros (widgets — sobrescrevem em job-run)
# MAGIC
# MAGIC | param | default | descrição |
# MAGIC | --- | --- | --- |
# MAGIC | `start_year` | 2013 | primeiro ano do range solicitado à API IBGE |
# MAGIC | `end_year`   | 2026 | último ano do range solicitado |
# MAGIC | `volume_path`| `/Volumes/mirante/bronze/raw/ibge` | destino do JSON |
# MAGIC
# MAGIC > Para anos não publicados pelo IBGE: o JSON virá com a chave `ano` faltando.
# MAGIC > A interpolação linear acontece na próxima task (DLT silver).

# COMMAND ----------

dbutils.widgets.text("start_year",  "2013")
dbutils.widgets.text("end_year",    "2026")
dbutils.widgets.text("volume_path", "/Volumes/mirante_prd/bronze/raw/ibge")

START_YEAR  = int(dbutils.widgets.get("start_year"))
END_YEAR    = int(dbutils.widgets.get("end_year"))
VOLUME_PATH = dbutils.widgets.get("volume_path")

print(f"start_year={START_YEAR} end_year={END_YEAR} dest={VOLUME_PATH}")

# COMMAND ----------

import json
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

# Quick sanity: count UF/year cells returned (some years may legitimately be missing)
cells = 0
years_seen = set()
for item in payload:
    for res in item.get("resultados", []):
        for s in res.get("series", []):
            for ano_str, val_str in (s.get("serie") or {}).items():
                if val_str not in (None, "", "..."):
                    cells += 1
                    years_seen.add(int(ano_str))
print(f"IBGE retornou {cells} células válidas. Anos presentes: {sorted(years_seen)}")
print(f"Anos solicitados mas não retornados: {sorted(set(range(START_YEAR, END_YEAR + 1)) - years_seen)}")

# COMMAND ----------

dest_dir  = Path(VOLUME_PATH)
dest_dir.mkdir(parents=True, exist_ok=True)
dest_file = dest_dir / "populacao_uf.json"
dest_file.write_text(json.dumps(payload), encoding="utf-8")
print(f"Salvo em {dest_file}  ({dest_file.stat().st_size:,} bytes)")

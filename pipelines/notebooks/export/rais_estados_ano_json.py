# Databricks notebook source
# MAGIC %md
# MAGIC # export · rais_estados_ano_json
# MAGIC
# MAGIC `<catalog>.gold.rais_estados_ano` → JSON em
# MAGIC `/Volumes/<catalog>/gold/exports/gold_rais_estados_ano.json`,
# MAGIC depois puxado pelo GH Action e commitado em `data/gold/`.

# COMMAND ----------

dbutils.widgets.text("catalog",     "mirante_prd")
dbutils.widgets.text("output_path", "/Volumes/mirante_prd/gold/exports/gold_rais_estados_ano.json")

CATALOG     = dbutils.widgets.get("catalog")
OUTPUT_PATH = dbutils.widgets.get("output_path")
GOLD_TABLE  = f"{CATALOG}.gold.rais_estados_ano"

# COMMAND ----------

import json
from pathlib import Path

if not spark.catalog.tableExists(GOLD_TABLE):
    print(f"⚠ {GOLD_TABLE} não existe — silver provavelmente vazia.")
    dbutils.notebook.exit(f"SKIPPED: {GOLD_TABLE} does not exist")

df  = spark.read.table(GOLD_TABLE).drop("_gold_built_ts").orderBy("Ano", "uf")
pdf = df.toPandas()
if pdf.empty:
    dbutils.notebook.exit(f"SKIPPED: {GOLD_TABLE} is empty")

for c in ("Ano","populacao","n_vinculos_ativos","n_vinculos_total","n_estabelecimentos_proxy"):
    if c in pdf.columns: pdf[c] = pdf[c].astype("Int64")

records = json.loads(pdf.to_json(orient="records"))
print(f"{len(records)} linhas. Sample[0]: {records[0] if records else '(empty)'}")

dest = Path(OUTPUT_PATH); dest.parent.mkdir(parents=True, exist_ok=True)
dest.write_text(json.dumps(records, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
print(f"✔ {dest} ({dest.stat().st_size:,} bytes)")

# Databricks notebook source
# MAGIC %md
# MAGIC # export · emendas_estados_df_json
# MAGIC
# MAGIC Lê `<catalog>.gold.emendas_estados_df` e grava JSON em
# MAGIC `/Volumes/<catalog>/gold/exports/gold_emendas_estados_df.json`. Esse é o arquivo
# MAGIC que o GitHub Action de refresh baixa e commita em `data/gold/` no repo.

# COMMAND ----------

dbutils.widgets.text("catalog",     "mirante_prd")
dbutils.widgets.text("output_path", "/Volumes/mirante_prd/gold/exports/gold_emendas_estados_df.json")

CATALOG     = dbutils.widgets.get("catalog")
OUTPUT_PATH = dbutils.widgets.get("output_path")
GOLD_TABLE  = f"{CATALOG}.gold.emendas_estados_df"

print(f"gold={GOLD_TABLE}  out={OUTPUT_PATH}")

# COMMAND ----------

import json
from pathlib import Path

# Defensive: gold pode não existir ainda se silver estava vazia (cascade do upstream).
# Sai gracefully sem TABLE_OR_VIEW_NOT_FOUND.
if not spark.catalog.tableExists(GOLD_TABLE):
    print(f"⚠ {GOLD_TABLE} não existe — provavelmente o gold pulou por silver vazia.")
    print("  Investigue o upstream (ingest_cgu_emendas → bronze → silver) antes de rodar export.")
    dbutils.notebook.exit(f"SKIPPED: {GOLD_TABLE} does not exist")

df = spark.read.table(GOLD_TABLE).drop("_gold_built_ts").orderBy("Ano", "uf")
pdf = df.toPandas()
if pdf.empty:
    print(f"⚠ {GOLD_TABLE} existe mas está vazia — nada pra exportar.")
    dbutils.notebook.exit(f"SKIPPED: {GOLD_TABLE} is empty")

for c in ("Ano", "populacao", "n_emendas", "n_municipios"):
    if c in pdf.columns:
        pdf[c] = pdf[c].astype("Int64")

records = json.loads(pdf.to_json(orient="records"))
print(f"{len(records)} linhas. Sample[0]: {records[0] if records else '(empty)'}")

dest = Path(OUTPUT_PATH)
dest.parent.mkdir(parents=True, exist_ok=True)
dest.write_text(json.dumps(records, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
print(f"✔ {dest}  ({dest.stat().st_size:,} bytes)")

# Databricks notebook source
# MAGIC %md
# MAGIC # export · pbf_estados_df_json
# MAGIC
# MAGIC Lê `<catalog>.gold.pbf_estados_df` e grava JSON em
# MAGIC `/Volumes/<catalog>/gold/exports/gold_pbf_estados_df.json` — esse é o arquivo
# MAGIC que o GitHub Action de refresh baixa e commita em `data/gold/` no repo.

# COMMAND ----------

dbutils.widgets.text("catalog",     "mirante_prd")
dbutils.widgets.text("output_path", "/Volumes/mirante_prd/gold/exports/gold_pbf_estados_df.json")

CATALOG     = dbutils.widgets.get("catalog")
OUTPUT_PATH = dbutils.widgets.get("output_path")
GOLD_TABLE  = f"{CATALOG}.gold.pbf_estados_df"

print(f"gold={GOLD_TABLE}  out={OUTPUT_PATH}")

# COMMAND ----------

import json
from pathlib import Path

# Drop the lineage column before exporting (front doesn't need _gold_built_ts)
df = spark.read.table(GOLD_TABLE).drop("_gold_built_ts").orderBy("Ano", "uf")

pdf = df.toPandas()
for c in ("Ano", "n_benef", "populacao"):
    if c in pdf.columns:
        pdf[c] = pdf[c].astype("Int64")

records = json.loads(pdf.to_json(orient="records"))
print(f"{len(records)} linhas. Sample[0]: {records[0] if records else '(empty)'}")

# COMMAND ----------

dest = Path(OUTPUT_PATH)
dest.parent.mkdir(parents=True, exist_ok=True)
dest.write_text(json.dumps(records, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
print(f"✔ {dest}  ({dest.stat().st_size:,} bytes)")

# COMMAND ----------

# Sanity check — re-read and audit
sample = json.loads(dest.read_text(encoding="utf-8"))
years = sorted({r["Ano"] for r in sample})
ufs   = sorted({r["uf"]  for r in sample})
print(f"Anos: {years[0]}..{years[-1]} ({len(years)})  UFs: {len(ufs)}")

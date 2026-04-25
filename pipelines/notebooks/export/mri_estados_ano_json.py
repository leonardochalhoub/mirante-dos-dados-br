# Databricks notebook source
# MAGIC %md
# MAGIC # export · mri_estados_ano_json
# MAGIC
# MAGIC Lê `<catalog>.gold.mri_estados_ano` e grava JSON em
# MAGIC `/Volumes/<catalog>/gold/exports/gold_mri_estados_ano.json`. Esse é o arquivo
# MAGIC que o GitHub Action de refresh baixa e commita em `data/gold/` no repo.

# COMMAND ----------

dbutils.widgets.text("catalog",     "mirante_prd")
dbutils.widgets.text("output_path", "/Volumes/mirante_prd/gold/exports/gold_mri_estados_ano.json")

CATALOG     = dbutils.widgets.get("catalog")
OUTPUT_PATH = dbutils.widgets.get("output_path")
GOLD_TABLE  = f"{CATALOG}.gold.mri_estados_ano"

print(f"gold={GOLD_TABLE}  out={OUTPUT_PATH}")

# COMMAND ----------

import json
from pathlib import Path

# Drop lineage column before exporting
df = spark.read.table(GOLD_TABLE).drop("_gold_built_ts").orderBy("estado", "ano")

pdf = df.toPandas()

# Force int dtypes for ID/count columns
for c in ("ano", "cnes_count", "sus_cnes_count", "priv_cnes_count",
          "populacao", "mri_per_capita_scale_pow10"):
    if c in pdf.columns:
        pdf[c] = pdf[c].astype("Int64")

records = json.loads(pdf.to_json(orient="records"))
print(f"{len(records)} linhas. Sample[0]: {records[0] if records else '(empty)'}")

# COMMAND ----------

dest = Path(OUTPUT_PATH)
dest.parent.mkdir(parents=True, exist_ok=True)
dest.write_text(json.dumps(records, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
print(f"✔ {dest}  ({dest.stat().st_size:,} bytes)")

# Sanity check
sample = json.loads(dest.read_text(encoding="utf-8"))
ufs = sorted({r["estado"] for r in sample})
years = sorted({r["ano"] for r in sample})
print(f"UFs: {len(ufs)}  Anos: {years[0]}..{years[-1]} ({len(years)})")

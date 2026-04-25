# Databricks notebook source
# MAGIC %md
# MAGIC # export · uropro_estados_ano_json
# MAGIC
# MAGIC Lê `<catalog>.gold.uropro_estados_ano` e grava JSON em
# MAGIC `/Volumes/<catalog>/gold/exports/gold_uropro_estados_ano.json`.

# COMMAND ----------

dbutils.widgets.text("catalog",     "mirante_prd")
dbutils.widgets.text("output_path", "/Volumes/mirante_prd/gold/exports/gold_uropro_estados_ano.json")

CATALOG     = dbutils.widgets.get("catalog")
OUTPUT_PATH = dbutils.widgets.get("output_path")
GOLD_TABLE  = f"{CATALOG}.gold.uropro_estados_ano"

print(f"gold={GOLD_TABLE}  out={OUTPUT_PATH}")

# COMMAND ----------

import json
from pathlib import Path

df = spark.read.table(GOLD_TABLE).drop("_gold_built_ts").orderBy("uf", "ano", "proc_rea")
pdf = df.toPandas()

# Cast counts → Int64 (nullable int) pra JSON limpo
int_cols = (
    "ano", "populacao", "n_aih", "n_morte",
    "aih_eletivo", "aih_urgencia",
    "aih_gestao_estadual", "aih_gestao_municipal", "aih_gestao_dupla",
    "per_capita_base",
)
for c in int_cols:
    if c in pdf.columns:
        pdf[c] = pdf[c].astype("Int64")

records = json.loads(pdf.to_json(orient="records"))
print(f"{len(records)} linhas. Sample[0]: {records[0] if records else '(empty)'}")

dest = Path(OUTPUT_PATH)
dest.parent.mkdir(parents=True, exist_ok=True)
dest.write_text(json.dumps(records, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
print(f"✔ {dest}  ({dest.stat().st_size:,} bytes)")

ufs   = sorted({r["uf"]       for r in records})
years = sorted({r["ano"]      for r in records})
procs = sorted({r["proc_rea"] for r in records})
print(f"UFs: {len(ufs)}  Anos: {years[0] if years else '?'}..{years[-1] if years else '?'} ({len(years)})  Procedimentos: {len(procs)}")

# Databricks notebook source
# MAGIC %md
# MAGIC # export · equipamentos_estados_ano_json
# MAGIC
# MAGIC Lê `<catalog>.gold.equipamentos_estados_ano` e grava JSON em
# MAGIC `/Volumes/<catalog>/gold/exports/gold_equipamentos_estados_ano.json`.

# COMMAND ----------

dbutils.widgets.text("catalog",     "mirante_prd")
dbutils.widgets.text("output_path", "/Volumes/mirante_prd/gold/exports/gold_equipamentos_estados_ano.json")

CATALOG     = dbutils.widgets.get("catalog")
OUTPUT_PATH = dbutils.widgets.get("output_path")
GOLD_TABLE  = f"{CATALOG}.gold.equipamentos_estados_ano"

print(f"gold={GOLD_TABLE}  out={OUTPUT_PATH}")

# COMMAND ----------

import json
from pathlib import Path

df = spark.read.table(GOLD_TABLE).drop("_gold_built_ts").orderBy(
    "estado", "ano", "tipequip", "codequip",
)
pdf = df.toPandas()

for c in ("ano", "cnes_count", "sus_cnes_count", "priv_cnes_count",
          "populacao", "per_capita_scale_pow10"):
    if c in pdf.columns:
        pdf[c] = pdf[c].astype("Int64")

records = json.loads(pdf.to_json(orient="records"))
print(f"{len(records)} linhas. Sample[0]: {records[0] if records else '(empty)'}")

dest = Path(OUTPUT_PATH)
dest.parent.mkdir(parents=True, exist_ok=True)
dest.write_text(json.dumps(records, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
print(f"✔ {dest}  ({dest.stat().st_size:,} bytes)")

ufs = sorted({r["estado"] for r in records})
years = sorted({r["ano"] for r in records})
combos = sorted({r["equipment_key"] for r in records})
print(f"UFs: {len(ufs)}  Anos: {years[0]}..{years[-1]} ({len(years)})  Combos (TIPEQUIP:CODEQUIP): {len(combos)}")

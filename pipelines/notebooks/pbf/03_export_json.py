# Databricks notebook source
# MAGIC %md
# MAGIC # pbf · 03 · export gold → JSON em Volume
# MAGIC
# MAGIC Pós-DLT task: lê `mirante.gold.pbf_estados_df` e grava como JSON array em UC Volume.
# MAGIC O GitHub Action de refresh baixa esse arquivo e commita em `data/gold/` no repo.
# MAGIC
# MAGIC **Schema produzido** (bate com o arquivo atual em `data/gold/gold_pbf_estados_df.json`):
# MAGIC ```json
# MAGIC [
# MAGIC   {"Ano": 2025, "uf": "AC", "n_benef": 126480,
# MAGIC    "valor_nominal": 1.10, "valor_2021": 0.91,
# MAGIC    "populacao": 884372,
# MAGIC    "pbfPerBenef": 7190.32, "pbfPerCapita": 1028.34},
# MAGIC   ...
# MAGIC ]
# MAGIC ```
# MAGIC
# MAGIC ## Parâmetros
# MAGIC
# MAGIC | param | default |
# MAGIC | --- | --- |
# MAGIC | `output_path` | `/Volumes/mirante/gold/exports/gold_pbf_estados_df.json` |
# MAGIC | `gold_table`  | `mirante.gold.pbf_estados_df` |

# COMMAND ----------

dbutils.widgets.text("output_path", "/Volumes/mirante_prd/gold/exports/gold_pbf_estados_df.json")
dbutils.widgets.text("gold_table",  "mirante_prd.gold.pbf_estados_df")

OUTPUT_PATH = dbutils.widgets.get("output_path")
GOLD_TABLE  = dbutils.widgets.get("gold_table")

print(f"gold_table={GOLD_TABLE}  output_path={OUTPUT_PATH}")

# COMMAND ----------

import json
from pathlib import Path
from pyspark.sql import functions as F

df = spark.read.table(GOLD_TABLE).orderBy("Ano", "uf")

# Convert Spark DataFrame to a single Python list of dicts.
# Volume is small (351 rows × 8 cols) — toPandas → orient='records' is the cleanest path.
pdf = df.toPandas()

# Force int dtypes for ID columns (avoid 2025.0 in the output)
for int_col in ("Ano", "n_benef", "populacao"):
    if int_col in pdf.columns:
        pdf[int_col] = pdf[int_col].astype("Int64")

records = json.loads(pdf.to_json(orient="records"))   # converts NaN → null cleanly
print(f"{len(records)} linhas a exportar. Sample[0]: {records[0] if records else '(empty)'}")

# COMMAND ----------

dest = Path(OUTPUT_PATH)
dest.parent.mkdir(parents=True, exist_ok=True)
dest.write_text(json.dumps(records, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
size = dest.stat().st_size
print(f"Salvo: {dest}  ({size:,} bytes, {len(records)} registros)")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Sanity checks
# MAGIC
# MAGIC Mini-validação antes do GitHub Action puxar o arquivo:

# COMMAND ----------

# Re-load and audit
sample = json.loads(dest.read_text(encoding="utf-8"))
years = sorted({r["Ano"] for r in sample})
ufs   = sorted({r["uf"]  for r in sample})
print(f"Anos: {years[0]}..{years[-1]} ({len(years)})")
print(f"UFs:  {len(ufs)} -> {ufs}")

# Spot-check 2025 valores Brasil
y2025 = [r for r in sample if r["Ano"] == 2025]
if y2025:
    sum_benef = sum((r["n_benef"]    or 0) for r in y2025)
    sum_v2021 = sum((r["valor_2021"] or 0) for r in y2025)
    sum_pop   = sum((r["populacao"]  or 0) for r in y2025)
    per_benef  = (sum_v2021 * 1e9) / sum_benef if sum_benef else None
    per_capita = (sum_v2021 * 1e9) / sum_pop   if sum_pop   else None
    print(f"2025 Brasil: per_benef=R${per_benef:.2f}  per_capita=R${per_capita:.2f}")
    print("(Espera-se per_benef=5825.32, per_capita=608.33 com dados atuais)")

# Databricks notebook source
# MAGIC %md
# MAGIC # export · pbf_municipios_df_json
# MAGIC
# MAGIC Lê `<catalog>.gold.pbf_municipios_df` e grava JSON em
# MAGIC `/Volumes/<catalog>/gold/exports/gold_pbf_municipios_df.json` — esse é o arquivo
# MAGIC que o GitHub Action de refresh baixa e commita em `data/gold/` no repo.
# MAGIC
# MAGIC Tamanho esperado do JSON: ~72k linhas × ~14 colunas ≈ 12 MB minified.
# MAGIC Para reduzir, exportamos um JSON "denso" (todas as colunas) e um JSON "leve"
# MAGIC apenas com (Ano, cod_municipio, n_benef, valor_2021, pbfPerCapita) ~3 MB.

# COMMAND ----------

dbutils.widgets.text("catalog",          "mirante_prd")
dbutils.widgets.text("output_path",      "/Volumes/mirante_prd/gold/exports/gold_pbf_municipios_df.json")
dbutils.widgets.text("output_path_lite", "/Volumes/mirante_prd/gold/exports/gold_pbf_municipios_df.lite.json")

CATALOG          = dbutils.widgets.get("catalog")
OUTPUT_PATH      = dbutils.widgets.get("output_path")
OUTPUT_PATH_LITE = dbutils.widgets.get("output_path_lite")
GOLD_TABLE       = f"{CATALOG}.gold.pbf_municipios_df"

print(f"gold={GOLD_TABLE}  out={OUTPUT_PATH}  out_lite={OUTPUT_PATH_LITE}")

# COMMAND ----------

import json
from pathlib import Path

df = spark.read.table(GOLD_TABLE).drop("_gold_built_ts").orderBy("Ano", "cod_municipio")
pdf = df.toPandas()
for c in ("Ano", "n_benef", "populacao"):
    if c in pdf.columns:
        pdf[c] = pdf[c].astype("Int64")

records = json.loads(pdf.to_json(orient="records"))
print(f"{len(records):,} linhas. Sample[0]: {records[0] if records else '(empty)'}")

# COMMAND ----------

# Versão densa
dest = Path(OUTPUT_PATH)
dest.parent.mkdir(parents=True, exist_ok=True)
dest.write_text(json.dumps(records, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
print(f"✔ dense {dest}  ({dest.stat().st_size:,} bytes)")

# Versão lite (web-friendly)
records_lite = [
    {k: r.get(k) for k in
     ("Ano", "cod_municipio", "uf", "regiao",
      "n_benef", "valor_2021", "pbfPerCapita", "populacao")}
    for r in records
]
dest_lite = Path(OUTPUT_PATH_LITE)
dest_lite.write_text(
    json.dumps(records_lite, ensure_ascii=False, separators=(",", ":")),
    encoding="utf-8",
)
print(f"✔ lite  {dest_lite}  ({dest_lite.stat().st_size:,} bytes)")

# COMMAND ----------

# Sanity check
sample = json.loads(dest.read_text(encoding="utf-8"))
years = sorted({r["Ano"] for r in sample})
ufs   = sorted({r["uf"]  for r in sample})
munis = len({r["cod_municipio"] for r in sample})
print(f"Anos: {years[0]}..{years[-1]} ({len(years)})  UFs: {len(ufs)}  Munis: {munis:,}")
assert munis >= 5500, f"Cobertura municipal: {munis} < 5500 — investigar"
print("✔ export sanity passed")

# Databricks notebook source
# MAGIC %md
# MAGIC # diagnostics · rais_integrity
# MAGIC
# MAGIC Pente-fino de integridade da vertical RAIS, layer por layer:
# MAGIC
# MAGIC 1. **FONTE (FTP PDET)**: lista esperada de arquivos por ano (não acessa FTP — usa snapshot conhecido)
# MAGIC 2. **VOLUME .7z**: o que de fato chegou em `/Volumes/.../mte/rais/` (incluindo `.part` e `_bad/`)
# MAGIC 3. **TXT extraído**: o que está em `<TXT_EXTRACTED>/ano=YYYY/`
# MAGIC 4. **BRONZE**: contagem de linhas em `mirante_prd.bronze.rais_vinculos` por ano
# MAGIC
# MAGIC Cross-tab final mostra, por ano, em cada layer:
# MAGIC - quantos arquivos / linhas existem
# MAGIC - quais .7z deveriam existir mas não estão (gap fonte→volume)
# MAGIC - quais .7z foram para quarentena (`_bad/`) ou ficaram como `.part`
# MAGIC - quais .7z foram extraídos mas não viraram bronze
# MAGIC - inconsistências de tamanho entre .7z e .txt (sinal de extração parcial)

# COMMAND ----------

dbutils.widgets.text("catalog",       "mirante_prd")
dbutils.widgets.text("zips_dir",      "/Volumes/mirante_prd/bronze/raw/mte/rais")
dbutils.widgets.text("txt_extracted", "/Volumes/mirante_prd/bronze/raw/mte/rais_txt_extracted")

CATALOG       = dbutils.widgets.get("catalog")
ZIPS_DIR      = dbutils.widgets.get("zips_dir")
TXT_EXTRACTED = dbutils.widgets.get("txt_extracted")
BRONZE_TABLE  = f"{CATALOG}.bronze.rais_vinculos"

import re
from pathlib import Path
from collections import defaultdict

print(f"catalog={CATALOG}  zips_dir={ZIPS_DIR}  txt={TXT_EXTRACTED}  bronze={BRONZE_TABLE}\n")

# COMMAND ----------

# MAGIC %md ## Layer 1 — Volume `.7z` (estado pós-ingest)

# COMMAND ----------

YEAR_RE = re.compile(r"_(\d{4})\.7z$", re.I)

def parse_year(name: str) -> int | None:
    m = YEAR_RE.search(name)
    return int(m.group(1)) if m else None

zips_by_year   = defaultdict(list)
parts_by_year  = defaultdict(list)
bad_by_year    = defaultdict(list)

zips_dir_path  = Path(ZIPS_DIR)
quarantine_dir = zips_dir_path / "_bad"

for f in zips_dir_path.iterdir():
    if not f.is_file():
        continue
    if f.suffix.lower() == ".7z":
        y = parse_year(f.name)
        if y is not None:
            zips_by_year[y].append((f.name, f.stat().st_size))
    elif f.name.endswith(".7z.part"):
        y = parse_year(f.name.replace(".part", ""))
        if y is not None:
            parts_by_year[y].append((f.name, f.stat().st_size))

if quarantine_dir.exists():
    for f in quarantine_dir.iterdir():
        if f.is_file() and f.suffix.lower() == ".7z":
            y = parse_year(f.name)
            if y is not None:
                bad_by_year[y].append((f.name, f.stat().st_size))

n_zips_total  = sum(len(v) for v in zips_by_year.values())
n_parts_total = sum(len(v) for v in parts_by_year.values())
n_bad_total   = sum(len(v) for v in bad_by_year.values())

print(f"[ZIPS]      {n_zips_total} .7z em {len(zips_by_year)} anos")
print(f"[PARTS]     {n_parts_total} .part (download incompleto)")
print(f"[QUARENTENA]{n_bad_total} em _bad/ (rejeitados pela bronze)\n")

if parts_by_year:
    print("⚠ ARQUIVOS .part (não ingeridos):")
    for y in sorted(parts_by_year):
        for name, size in parts_by_year[y]:
            print(f"  {y}  {name:50s}  {size/1_048_576:>8.0f} MB")
if bad_by_year:
    print("\n⚠ ARQUIVOS EM QUARENTENA:")
    for y in sorted(bad_by_year):
        for name, size in bad_by_year[y]:
            print(f"  {y}  {name:50s}  {size/1_048_576:>8.0f} MB")

# COMMAND ----------

# MAGIC %md ## Layer 2 — TXT extraído (estado pós-bronze step 1)

# COMMAND ----------

txt_path = Path(TXT_EXTRACTED)
markers_done = sorted(txt_path.glob("_*.done"))
markers_bad  = sorted(txt_path.glob("_*.bad"))
year_dirs    = sorted([d for d in txt_path.iterdir() if d.is_dir() and d.name.startswith("ano=")])

txts_by_year = defaultdict(list)
for d in year_dirs:
    y = int(d.name.split("=", 1)[1])
    for f in d.rglob("*"):
        if f.is_file() and f.suffix.lower() in (".txt", ".csv", ".dat"):
            txts_by_year[y].append((f.name, f.stat().st_size))

n_txts_total = sum(len(v) for v in txts_by_year.values())

print(f"[TXT]       {n_txts_total} arquivos em {len(year_dirs)} partições ano=YYYY/")
print(f"[markers]   {len(markers_done)} .done · {len(markers_bad)} .bad\n")

# Sanity: ano que tem .7z mas não tem TXT (extração faltou)
zips_years = set(zips_by_year.keys())
txt_years  = set(txts_by_year.keys())
gap_zip_no_txt = sorted(zips_years - txt_years)
gap_txt_no_zip = sorted(txt_years - zips_years)

if gap_zip_no_txt:
    print(f"⚠ GAP zip→txt — anos com .7z mas sem TXT extraído: {gap_zip_no_txt}")
if gap_txt_no_zip:
    print(f"⚠ GAP txt→zip — anos com TXT mas sem .7z (órfão): {gap_txt_no_zip}")

# COMMAND ----------

# MAGIC %md ## Layer 3 — Bronze table

# COMMAND ----------

from pyspark.sql import functions as F

if not spark.catalog.tableExists(BRONZE_TABLE):
    print(f"⚠ {BRONZE_TABLE} NÃO EXISTE")
    bronze_by_year = {}
else:
    counts_df = (
        spark.read.table(BRONZE_TABLE)
            .groupBy("ano")
            .agg(F.count("*").alias("rows"),
                 F.countDistinct("_source_file").alias("files"))
            .orderBy("ano")
    )
    bronze_by_year = {r["ano"]: (r["rows"], r["files"]) for r in counts_df.collect()}
    n_bronze_rows = sum(rows for rows, _ in bronze_by_year.values())
    print(f"[BRONZE]    {n_bronze_rows:,} linhas em {len(bronze_by_year)} anos")
    counts_df.show(50, truncate=False)

# COMMAND ----------

# MAGIC %md ## Cross-tab final — fonte vs volume vs txt vs bronze

# COMMAND ----------

all_years = sorted(zips_years | txt_years | set(parts_by_year) | set(bad_by_year) | set(bronze_by_year or {}))

print(f"{'ano':>5} | {'.7z':>4} | {'.part':>5} | {'_bad':>4} | {'TXTs':>5} | {'rows BRONZE':>14} | {'files BRONZE':>13} | gap?")
print("-" * 110)
for y in all_years:
    n_zip   = len(zips_by_year.get(y, []))
    n_part  = len(parts_by_year.get(y, []))
    n_bad   = len(bad_by_year.get(y, []))
    n_txt   = len(txts_by_year.get(y, []))
    rows, files = bronze_by_year.get(y, (0, 0)) if bronze_by_year else (0, 0)

    flags = []
    if n_part:                       flags.append(".part!")
    if n_bad:                        flags.append("BAD!")
    if n_zip > 0 and n_txt == 0:     flags.append("zip→txt")
    if n_txt > 0 and rows == 0:      flags.append("txt→bronze")
    if n_zip > 0 and rows == 0:      flags.append("zip→bronze")
    flag_str = " ".join(flags) if flags else "ok"

    print(f"{y:>5} | {n_zip:>4d} | {n_part:>5d} | {n_bad:>4d} | {n_txt:>5d} | {rows:>14,d} | {files:>13d} | {flag_str}")

# COMMAND ----------

# MAGIC %md ## Verificação de tamanho — txt esperado vs txt observado
# MAGIC
# MAGIC Sinal de extração parcial: o tamanho descomprimido típico de um RAIS
# MAGIC ano-completo BR é ~50–80 GB. Se a soma dos .txt de um ano dá <1 GB,
# MAGIC é possível extração interrompida.

# COMMAND ----------

print(f"{'ano':>5} | {'sum 7z (MB)':>13} | {'sum txt (MB)':>13} | {'ratio txt/7z':>13} | nota")
print("-" * 90)
for y in all_years:
    sum_7z  = sum(s for _, s in zips_by_year.get(y, [])) / 1_048_576
    sum_txt = sum(s for _, s in txts_by_year.get(y, [])) / 1_048_576
    if sum_7z > 0 and sum_txt > 0:
        ratio = sum_txt / sum_7z
        nota = "ok"
        if ratio < 2:
            nota = "⚠ baixo (extração parcial?)"
        elif ratio > 50:
            nota = "⚠ alto (formato inesperado?)"
    else:
        ratio = 0.0
        nota = "—"
    print(f"{y:>5} | {sum_7z:>13.1f} | {sum_txt:>13.1f} | {ratio:>13.1f} | {nota}")

# COMMAND ----------

# MAGIC %md ## Conclusão automática

# COMMAND ----------

issues = []
if n_parts_total:
    issues.append(f"{n_parts_total} .part files no Volume — ingest não terminou esses downloads")
if n_bad_total:
    issues.append(f"{n_bad_total} .7z em _bad/ — corrompidos da fonte")
if gap_zip_no_txt:
    issues.append(f"anos com .7z mas sem TXT extraído: {gap_zip_no_txt}")
if bronze_by_year:
    bronze_zero_with_zip = [y for y in zips_years if bronze_by_year.get(y, (0, 0))[0] == 0]
    if bronze_zero_with_zip:
        issues.append(f"anos com .7z mas 0 linhas em bronze: {bronze_zero_with_zip}")

if not issues:
    print("✔ Pente-fino OK — nenhum gap detectado em fonte→volume→txt→bronze")
else:
    print("✗ Pente-fino detectou problemas:")
    for i in issues:
        print(f"  - {i}")
    print("\nAções recomendadas:")
    if n_parts_total:
        print("  • Re-rodar ingest_mte_rais (com fix de FUSE Illegal seek deployado em e0f6815)")
    if n_bad_total:
        print(f"  • Inspecionar manualmente arquivos em {ZIPS_DIR}/_bad/ — fonte PDET pode ter .7z corrompido permanentemente")
    if bronze_zero_with_zip:
        print("  • Re-rodar bronze_rais_vinculos com force_reconvert=true ou inspecionar logs do step 1")

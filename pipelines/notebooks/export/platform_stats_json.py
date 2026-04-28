# Databricks notebook source
# MAGIC %md
# MAGIC # export · platform_stats_json
# MAGIC
# MAGIC Computa estatísticas vivas do lakehouse e grava em
# MAGIC `/Volumes/<catalog>/gold/exports/platform_stats.json`. O front-end consome esse
# MAGIC arquivo na home pra mostrar tamanho do dado público processado.
# MAGIC
# MAGIC Coleta:
# MAGIC - **Raw**: tamanho e contagem dos arquivos em `/Volumes/<catalog>/bronze/raw/`
# MAGIC   (subpastas cgu/pbf, ibge, bcb, e cgu/pbf_csv_extracted após extração)
# MAGIC - **Bronze tables**: linhas + bytes via `DESCRIBE DETAIL`
# MAGIC - **Silver tables**: idem
# MAGIC - **Gold tables**: idem
# MAGIC - **Largest table**: identifica a tabela com mais linhas no lakehouse

# COMMAND ----------

dbutils.widgets.text("catalog",     "mirante_prd")
dbutils.widgets.text("output_path", "/Volumes/mirante_prd/gold/exports/platform_stats.json")

CATALOG     = dbutils.widgets.get("catalog")
OUTPUT_PATH = dbutils.widgets.get("output_path")
RAW_ROOT    = f"/Volumes/{CATALOG}/bronze/raw"

print(f"catalog={CATALOG}  out={OUTPUT_PATH}  raw={RAW_ROOT}")

# COMMAND ----------

import json
from datetime import datetime, timezone
from pathlib import Path

# ─── Helpers ────────────────────────────────────────────────────────────────

def folder_stats(path: str, glob: str = "**/*") -> dict:
    """Returns {files, bytes} — recursive size + count for a folder."""
    p = Path(path)
    if not p.exists():
        return {"files": 0, "bytes": 0}
    files = [f for f in p.glob(glob) if f.is_file() and not f.name.startswith("_")]
    return {"files": len(files), "bytes": sum(f.stat().st_size for f in files)}


def folder_stats_filtered(path: str, suffixes: tuple[str, ...]) -> dict:
    """Same as folder_stats but only counts files with given suffixes."""
    p = Path(path)
    if not p.exists():
        return {"files": 0, "bytes": 0}
    files = [
        f for f in p.rglob("*")
        if f.is_file() and not f.name.startswith("_") and f.suffix.lower() in suffixes
    ]
    return {"files": len(files), "bytes": sum(f.stat().st_size for f in files)}


def table_stats(catalog: str, schema: str) -> list[dict]:
    """Returns [{table, rows, bytes}] for every table in catalog.schema."""
    out = []
    try:
        tables = spark.sql(f"SHOW TABLES IN {catalog}.{schema}").collect()
    except Exception as e:
        print(f"  schema {schema} not accessible: {e}")
        return out
    for row in tables:
        tname = row["tableName"]
        full  = f"{catalog}.{schema}.{tname}"
        try:
            rows  = spark.read.table(full).count()
            detail = spark.sql(f"DESCRIBE DETAIL {full}").first()
            size  = int(detail["sizeInBytes"]) if detail and detail["sizeInBytes"] is not None else 0
            # Delta version = latest entry in DESCRIBE HISTORY (commits to this table over time).
            # Each refresh increments by 1. Used by the front to show "v{N}" badge.
            try:
                hist = spark.sql(f"DESCRIBE HISTORY {full}").orderBy("version", ascending=False).first()
                delta_version = int(hist["version"]) if hist and hist["version"] is not None else 0
            except Exception:
                delta_version = 0
            out.append({"table": tname, "full_name": full, "rows": rows,
                        "bytes": size, "delta_version": delta_version})
        except Exception as e:
            print(f"  could not stat {full}: {e}")
    return out

# ─── Compute ────────────────────────────────────────────────────────────────

print("▸ raw files…")
raw = {
    # PBF (CGU): ZIP downloads → after extraction become CSVs
    "cgu_pbf_zips":           folder_stats_filtered(f"{RAW_ROOT}/cgu/pbf",                 (".zip",)),
    "cgu_pbf_csv_extracted":  folder_stats_filtered(f"{RAW_ROOT}/cgu/pbf_csv_extracted",  (".csv",)),

    # Emendas Parlamentares (CGU): consolidated ZIP → after extraction one CSV per refresh
    "cgu_emendas_zips":       folder_stats_filtered(f"{RAW_ROOT}/cgu/emendas",                  (".zip",)),
    "cgu_emendas_csv":        folder_stats_filtered(f"{RAW_ROOT}/cgu/emendas_csv_extracted",   (".csv",)),

    # Equipamentos (DATASUS/CNES): .dbc files (PKWARE-compressed DBF) → after conversion become .parquet
    "datasus_cnes_eq_dbc":    folder_stats_filtered(f"{RAW_ROOT}/datasus/cnes_eq",        (".dbc",)),
    "datasus_cnes_eq_parquet":folder_stats_filtered(f"{RAW_ROOT}/datasus/cnes_eq_converted", (".parquet", ".csv")),

    # UroPro (DATASUS SIH-AIH-RD): .dbc files → .parquet, mesmo padrão CNES
    "datasus_sih_rd_dbc":     folder_stats_filtered(f"{RAW_ROOT}/datasus/sih_rd",          (".dbc",)),
    "datasus_sih_rd_parquet": folder_stats_filtered(f"{RAW_ROOT}/datasus/sih_rd_parquet",  (".parquet",)),

    # RAIS (MTE/PDET): .7z files → .txt extraídos
    "mte_rais_7z":            folder_stats_filtered(f"{RAW_ROOT}/mte/rais",                (".7z",)),
    "mte_rais_txt":           folder_stats_filtered(f"{RAW_ROOT}/mte/rais_txt_extracted",  (".txt",)),

    # APIs (lightweight JSON)
    "ibge_json":              folder_stats_filtered(f"{RAW_ROOT}/ibge",                   (".json",)),
    "bcb_json":               folder_stats_filtered(f"{RAW_ROOT}/bcb",                    (".json",)),
}
print()
for k, v in raw.items():
    mb = v["bytes"] / (1024 * 1024)
    print(f"  {k:30s} {v['files']:>5} files  {mb:>10.1f} MB")

# COMMAND ----------

print("▸ bronze tables…")
bronze = table_stats(CATALOG, "bronze")
for t in bronze:
    print(f"  {t['full_name']}: {t['rows']:,} rows, {t['bytes']:,} bytes")

print("▸ silver tables…")
silver = table_stats(CATALOG, "silver")
for t in silver:
    print(f"  {t['full_name']}: {t['rows']:,} rows, {t['bytes']:,} bytes")

print("▸ gold tables…")
gold = table_stats(CATALOG, "gold")
for t in gold:
    print(f"  {t['full_name']}: {t['rows']:,} rows, {t['bytes']:,} bytes")

# COMMAND ----------

# ─── Aggregate + serialize ──────────────────────────────────────────────────

all_tables = bronze + silver + gold
largest = max(all_tables, key=lambda t: t["rows"]) if all_tables else None

# Total raw across all sources (zips + extracted csvs + jsons)
raw_total_files = sum(v["files"] for v in raw.values())
raw_total_bytes = sum(v["bytes"] for v in raw.values())

# Total bronze/silver/gold table bytes (Delta sizeInBytes)
bronze_bytes = sum(t["bytes"] for t in bronze)
silver_bytes = sum(t["bytes"] for t in silver)
gold_bytes   = sum(t["bytes"] for t in gold)

# Compression-pipeline summaries (raw upstream → intermediate → Delta) per vertical
verticals = {
    "pbf": {
        "raw_compressed_files": raw["cgu_pbf_zips"]["files"],
        "raw_compressed_bytes": raw["cgu_pbf_zips"]["bytes"],
        "raw_compressed_label": "ZIP",
        "intermediate_files":   raw["cgu_pbf_csv_extracted"]["files"],
        "intermediate_bytes":   raw["cgu_pbf_csv_extracted"]["bytes"],
        "intermediate_label":   "CSV",
        "delta_bronze_bytes":   next((t["bytes"] for t in bronze if t["table"] == "pbf_pagamentos"), 0),
        "delta_bronze_rows":    next((t["rows"]  for t in bronze if t["table"] == "pbf_pagamentos"), 0),
    },
    "equipamentos": {
        "raw_compressed_files": raw["datasus_cnes_eq_dbc"]["files"],
        "raw_compressed_bytes": raw["datasus_cnes_eq_dbc"]["bytes"],
        "raw_compressed_label": "DBC",
        "intermediate_files":   raw["datasus_cnes_eq_parquet"]["files"],
        "intermediate_bytes":   raw["datasus_cnes_eq_parquet"]["bytes"],
        "intermediate_label":   "Parquet",
        "delta_bronze_bytes":   next((t["bytes"] for t in bronze if t["table"] in ("cnes_equipamentos", "datasus_cnes_eq_raw")), 0),
        "delta_bronze_rows":    next((t["rows"]  for t in bronze if t["table"] in ("cnes_equipamentos", "datasus_cnes_eq_raw")), 0),
    },
    "emendas": {
        "raw_compressed_files": raw["cgu_emendas_zips"]["files"],
        "raw_compressed_bytes": raw["cgu_emendas_zips"]["bytes"],
        "raw_compressed_label": "ZIP",
        "intermediate_files":   raw["cgu_emendas_csv"]["files"],
        "intermediate_bytes":   raw["cgu_emendas_csv"]["bytes"],
        "intermediate_label":   "CSV",
        "delta_bronze_bytes":   next((t["bytes"] for t in bronze if t["table"] == "emendas_pagamentos"), 0),
        "delta_bronze_rows":    next((t["rows"]  for t in bronze if t["table"] == "emendas_pagamentos"), 0),
    },
    "uropro": {
        "raw_compressed_files": raw["datasus_sih_rd_dbc"]["files"],
        "raw_compressed_bytes": raw["datasus_sih_rd_dbc"]["bytes"],
        "raw_compressed_label": "DBC",
        "intermediate_files":   raw["datasus_sih_rd_parquet"]["files"],
        "intermediate_bytes":   raw["datasus_sih_rd_parquet"]["bytes"],
        "intermediate_label":   "Parquet",
        "delta_bronze_bytes":   next((t["bytes"] for t in bronze if t["table"] == "sih_aih_rd_uropro"), 0),
        "delta_bronze_rows":    next((t["rows"]  for t in bronze if t["table"] == "sih_aih_rd_uropro"), 0),
    },
    "rais": {
        "raw_compressed_files": raw["mte_rais_7z"]["files"],
        "raw_compressed_bytes": raw["mte_rais_7z"]["bytes"],
        "raw_compressed_label": "7Z",
        "intermediate_files":   raw["mte_rais_txt"]["files"],
        "intermediate_bytes":   raw["mte_rais_txt"]["bytes"],
        "intermediate_label":   "TXT",
        "delta_bronze_bytes":   next((t["bytes"] for t in bronze if t["table"] == "rais_vinculos"), 0),
        "delta_bronze_rows":    next((t["rows"]  for t in bronze if t["table"] == "rais_vinculos"), 0),
    },
    # Reuso do bronze.pbf_pagamentos com nova agregação Município × Ano (WP#7).
    # Não tem raw próprio — é uma re-agregação da mesma fonte CGU. O "intermediate"
    # aqui é a IBGE/SIDRA pop municipal (5.571 munis × 11 anos) que viabiliza o gold
    # municipal; o "delta_bronze" reporta o gold.pbf_municipios_df (~72k linhas).
    "pbf-municipios": {
        "raw_compressed_files": 0,
        "raw_compressed_bytes": 0,
        "raw_compressed_label": "(reuso bronze.pbf_pagamentos)",
        "intermediate_files":   next((t["rows"] for t in silver if t["table"] == "populacao_municipio_ano"), 0),
        "intermediate_bytes":   next((t["bytes"] for t in silver if t["table"] == "populacao_municipio_ano"), 0),
        "intermediate_label":   "silver pop muni",
        "delta_bronze_bytes":   next((t["bytes"] for t in gold if t["table"] == "pbf_municipios_df"), 0),
        "delta_bronze_rows":    next((t["rows"]  for t in gold if t["table"] == "pbf_municipios_df"), 0),
    },
}

# ─── FinOps vertical — special shape (não byte-progression, é spend-progression) ──
# Bronze são system tables do Databricks (não temos arquivos raw). Os "steps"
# aqui no strip viram: dias observados → runs registradas → USD gastos.
# Front (BigDataStrip) detecta `kind: "finops"` e renderiza com Step próprio.
import os as _os
finops_path = f"/Volumes/{CATALOG}/gold/exports/finops_summary.json"
if _os.path.exists(finops_path):
    try:
        with open(finops_path, "r", encoding="utf-8") as fh:
            _fo = json.load(fh)
        verticals["finops"] = {
            "kind":            "finops",  # marker pro front renderizar diferente
            "n_days":          _fo["window"]["n_days"],
            "first_day":       _fo["window"]["first_day"],
            "last_day":        _fo["window"]["last_day"],
            "n_runs":          _fo["kpis"]["n_runs_lifetime"],
            "total_dbus":      _fo["kpis"]["total_dbus_lifetime"],
            "total_cost_usd":  _fo["kpis"]["total_cost_usd_lifetime"],
            "wasted_pct":      _fo["kpis"]["wasted_pct_lifetime"],
        }
        print(f"  ✓ verticals.finops adicionado: {verticals['finops']['n_days']} dias, "
              f"{verticals['finops']['n_runs']} runs, "
              f"USD {verticals['finops']['total_cost_usd']:.2f}")
    except Exception as e:
        print(f"  ⚠ FinOps summary disponível mas não pôde ser lido: {e}")
else:
    print(f"  ⚠ {finops_path} não existe — verticals.finops será omitida")

stats = {
    "generated_at_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    "catalog":          CATALOG,
    "raw": {
        "total_files":  raw_total_files,
        "total_bytes":  raw_total_bytes,
        "by_source":    raw,
    },
    "verticals": verticals,
    "tables": {
        "bronze": bronze,
        "silver": silver,
        "gold":   gold,
        "totals": {
            "bronze_bytes": bronze_bytes,
            "silver_bytes": silver_bytes,
            "gold_bytes":   gold_bytes,
        },
    },
    "largest_table": (
        {"name": largest["full_name"], "rows": largest["rows"], "bytes": largest["bytes"]}
        if largest else None
    ),
}

# Pretty-print per-vertical compression pipeline
print("\n--- compression pipeline per vertical ---")
for v, info in verticals.items():
    raw_mb  = info["raw_compressed_bytes"] / (1024 ** 2)
    int_mb  = info["intermediate_bytes"]   / (1024 ** 2)
    bronze_mb = info["delta_bronze_bytes"] / (1024 ** 2)
    print(f"  {v.upper():4s}  {info['raw_compressed_label']:>5s}: {raw_mb:>9.1f} MB  →  "
          f"{info['intermediate_label']:>12s}: {int_mb:>10.1f} MB  →  "
          f"Delta bronze: {bronze_mb:>9.1f} MB ({info['delta_bronze_rows']:,} rows)")

print("\n--- final stats ---")
print(json.dumps(stats, indent=2))

# COMMAND ----------

dest = Path(OUTPUT_PATH)
dest.parent.mkdir(parents=True, exist_ok=True)
dest.write_text(json.dumps(stats, separators=(",", ":")), encoding="utf-8")
print(f"✔ {dest}  ({dest.stat().st_size:,} bytes)")

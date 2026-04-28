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

# ─── Atribuição silver/gold por vertical (mapping table-name → vertical key) ──
# Bronze/silver/gold são SEMPRE Delta. Tabelas dimensionais compartilhadas
# (ipca_*, populacao_*, geobr_*) ficam em "shared" e não somam pra nenhuma
# vertical específica.
def _vertical_of(table_name):
    n = (table_name or "").lower()
    if n.startswith("pbf_"):                                  return "pbf"
    if n.startswith("emendas_"):                              return "emendas"
    if n.startswith("equipamentos_"):                         return "equipamentos"
    if n.startswith(("sih_uropro_", "uropro_")):              return "uropro"
    if n.startswith("rais_"):                                 return "rais"
    if n.startswith("finops_"):                               return "finops"
    return "shared"

def _agg_by_vertical(tables):
    out = {}
    for t in tables or []:
        v = _vertical_of(t.get("table"))
        out.setdefault(v, {"bytes": 0, "rows": 0})
        out[v]["bytes"] += t.get("bytes", 0) or 0
        out[v]["rows"]  += t.get("rows", 0)  or 0
    return out

silver_by_v = _agg_by_vertical(silver)
gold_by_v   = _agg_by_vertical(gold)

def _silver_b(vk): return silver_by_v.get(vk, {}).get("bytes", 0)
def _silver_r(vk): return silver_by_v.get(vk, {}).get("rows", 0)
def _gold_b(vk):   return gold_by_v.get(vk, {}).get("bytes", 0)
def _gold_r(vk):   return gold_by_v.get(vk, {}).get("rows", 0)


def _build_rais_vertical(raw, bronze, silver_b, silver_r, gold_b, gold_r, raw_root):
    """Monta o dict da vertical `rais` com 3 cards na strip:
    Delta canônico + Iceberg (via UniForm, storage compartilhado) + Hudi
    (escrito local, subido pro Volume — folder walk em
    /Volumes/.../bronze/raw/_open_formats/rais_vinculos_hudi/).

    Hudi pode estar:
    - **Ausente** (folder vazio ou inexistente): card renderiza como `deferred`
      com nota "deferido (serverless)" — usuário vê o slot mas sabe que precisa
      rodar o pipeline local.
    - **Presente**: bytes/rows reais via folder_stats; nota indica "amostra
      ano=YYYY · escrito local" pra ser honesto sobre o subset.
    """
    delta_bytes = next((t["bytes"] for t in bronze if t["table"] == "rais_vinculos"), 0)
    delta_rows  = next((t["rows"]  for t in bronze if t["table"] == "rais_vinculos"), 0)

    # Iceberg bronze paralela: tabela Delta SEPARADA escrita pelo job
    # bronze_rais_vinculos_open_formats com UniForm Iceberg habilitado at-create.
    # Lê o mesmo TXT cru — não compartilha arquivos com o Delta canônico.
    iceberg_bytes = next((t["bytes"] for t in bronze if t["table"] == "rais_vinculos_iceberg"), 0)
    iceberg_rows  = next((t["rows"]  for t in bronze if t["table"] == "rais_vinculos_iceberg"), 0)
    iceberg_card = {
        "label":       "Iceberg",
        "format":      "iceberg",
        "bytes":       iceberg_bytes,
        "rows":        iceberg_rows,
        "note":        "Delta + UniForm Iceberg · paralela ao Delta canônico" if iceberg_bytes > 0
                       else "aguardando bronze_rais_vinculos_open_formats",
        "deferred":    iceberg_bytes == 0,
    }

    # Hudi: walk do folder no Volume. Se vazio/ausente → deferred.
    hudi_dir = f"{raw_root}/_open_formats/rais_vinculos_hudi"
    hudi_walk = folder_stats(hudi_dir, "**/*")
    if hudi_walk["bytes"] > 0:
        # Tenta inferir as partições (ano=YYYY) presentes pra rotular honestamente
        hudi_path_p = Path(hudi_dir)
        years_found = sorted(
            int(d.name.split("=")[1])
            for d in hudi_path_p.iterdir()
            if d.is_dir() and d.name.startswith("ano=")
        ) if hudi_path_p.exists() else []
        if not years_found:
            note = "escrito local · subido via CLI"
        elif len(years_found) == 1:
            note = f"amostra ano={years_found[0]} · escrito local"
        else:
            note = f"amostra anos {years_found[0]}-{years_found[-1]} ({len(years_found)}) · escrito local"
        # Rows não temos sem reader Hudi; deixamos 0 e front mostra só bytes
        hudi_card = {
            "label":  "Hudi bronze",
            "format": "hudi",
            "bytes":  hudi_walk["bytes"],
            "rows":   0,
            "note":   note,
        }
    else:
        hudi_card = {
            "label":   "Hudi bronze",
            "format":  "hudi",
            "bytes":   0,
            "rows":    0,
            "note":    "deferido (serverless) — rode build_rais_hudi_local.py",
            "deferred": True,
        }

    return {
        "raw_compressed_files": raw["mte_rais_7z"]["files"],
        "raw_compressed_bytes": raw["mte_rais_7z"]["bytes"],
        "raw_compressed_label": "7Z",
        "intermediate_files":   raw["mte_rais_txt"]["files"],
        "intermediate_bytes":   raw["mte_rais_txt"]["bytes"],
        "intermediate_label":   "TXT",
        "delta_bronze_bytes":   delta_bytes,
        "delta_bronze_rows":    delta_rows,
        # Bronze paralela em Iceberg — SEPARADA do Delta canônico, lê mesmo TXT
        "delta_iceberg_parallel_bytes": iceberg_bytes,
        "delta_iceberg_parallel_rows":  iceberg_rows,
        "bronze_alt_formats":   [iceberg_card, hudi_card],
        "silver_bytes":         silver_b("rais"),
        "silver_rows":          silver_r("rais"),
        "gold_bytes":           gold_b("rais"),
        "gold_rows":            gold_r("rais"),
    }

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
        "silver_bytes":         _silver_b("pbf"),
        "silver_rows":          _silver_r("pbf"),
        "gold_bytes":           _gold_b("pbf"),
        "gold_rows":            _gold_r("pbf"),
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
        "silver_bytes":         _silver_b("equipamentos"),
        "silver_rows":          _silver_r("equipamentos"),
        "gold_bytes":           _gold_b("equipamentos"),
        "gold_rows":            _gold_r("equipamentos"),
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
        "silver_bytes":         _silver_b("emendas"),
        "silver_rows":          _silver_r("emendas"),
        "gold_bytes":           _gold_b("emendas"),
        "gold_rows":            _gold_r("emendas"),
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
        "silver_bytes":         _silver_b("uropro"),
        "silver_rows":          _silver_r("uropro"),
        "gold_bytes":           _gold_b("uropro"),
        "gold_rows":            _gold_r("uropro"),
    },
    "rais": _build_rais_vertical(raw, bronze, _silver_b, _silver_r, _gold_b, _gold_r, RAW_ROOT),
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

# ─── FinOps vertical — shape size/rows/format alinhado aos outros verticais ──
# Bronze do FinOps = system tables Databricks (delta-shared, sem bytes
# mensuráveis via DESCRIBE DETAIL). Silver/gold são nossas. Strip mostra
# 3 steps no padrão dos outros verticais: source (system tables) → silver
# → gold. Front detecta `kind: "finops"` e usa o mesmo componente Step.
SYSTEM_TABLES_USED = [
    "system.billing.usage",
    "system.compute.warehouses",
    "system.lakeflow.jobs",
    "system.lakeflow.job_run_timeline",
]

def _table_size(catalog, schema, name):
    """DESCRIBE DETAIL → (rows via COUNT, sizeInBytes via DESCRIBE DETAIL)."""
    try:
        rows = spark.sql(f"SELECT COUNT(*) c FROM {catalog}.{schema}.{name}").collect()[0]["c"]
    except Exception:
        rows = 0
    try:
        det = spark.sql(f"DESCRIBE DETAIL {catalog}.{schema}.{name}").collect()[0]
        size = det["sizeInBytes"] or 0
    except Exception:
        size = 0
    return rows, size

def _system_table_rows(fqn):
    try:
        return spark.sql(f"SELECT COUNT(*) c FROM {fqn}").collect()[0]["c"]
    except Exception:
        return 0

# Source: system tables (apenas rows — delta-shared, sem sizeInBytes)
src_total_rows = sum(_system_table_rows(t) for t in SYSTEM_TABLES_USED)

# Silver: finops_daily_spend + finops_run_costs
silv_d_rows, silv_d_bytes = _table_size(CATALOG, "silver", "finops_daily_spend")
silv_r_rows, silv_r_bytes = _table_size(CATALOG, "silver", "finops_run_costs")

# Gold: idem
gold_d_rows, gold_d_bytes = _table_size(CATALOG, "gold", "finops_daily_spend")
gold_r_rows, gold_r_bytes = _table_size(CATALOG, "gold", "finops_run_costs")

if src_total_rows + silv_d_rows + silv_r_rows + gold_d_rows + gold_r_rows > 0:
    verticals["finops"] = {
        "kind":           "finops",
        "source_label":   "Bronze · system tables",
        "source_tables":  len(SYSTEM_TABLES_USED),
        "source_rows":    src_total_rows,
        "silver_label":   "Silver · daily + runs",
        "silver_bytes":   silv_d_bytes + silv_r_bytes,
        "silver_rows":    silv_d_rows  + silv_r_rows,
        "gold_label":     "Gold · daily + runs",
        "gold_bytes":     gold_d_bytes + gold_r_bytes,
        "gold_rows":      gold_d_rows  + gold_r_rows,
    }
    print(f"  ✓ verticals.finops: source={src_total_rows} rows · "
          f"silver={silv_d_rows + silv_r_rows} rows ({silv_d_bytes + silv_r_bytes} B) · "
          f"gold={gold_d_rows + gold_r_rows} rows ({gold_d_bytes + gold_r_bytes} B)")
else:
    print(f"  ⚠ FinOps tables ainda não populadas — verticals.finops omitida")

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

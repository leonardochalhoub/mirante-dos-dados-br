# Databricks notebook source
# MAGIC %md
# MAGIC # pbf · 02 · DLT (Lakeflow Declarative Pipelines)
# MAGIC
# MAGIC Materializa a esteira completa do vertical PBF:
# MAGIC
# MAGIC ```
# MAGIC mirante.bronze.pbf_pagamentos       ← CSVs descomprimidos dos ZIPs CGU, normalizados
# MAGIC mirante.silver.pbf_total_uf_mes     ← UF × Ano × Mes: n beneficiários, total pago
# MAGIC mirante.gold.pbf_estados_df         ← UF × Ano: nominal, R$2021, perBenef, perCapita
# MAGIC ```
# MAGIC
# MAGIC ## Dependências externas (lidas de OUTROS pipelines)
# MAGIC
# MAGIC - `mirante.silver.populacao_uf_ano`     (refresh independente)
# MAGIC - `mirante.silver.ipca_deflators_2021`  (refresh independente)
# MAGIC
# MAGIC Lidos via `spark.read.table()`, **não** via `dlt.read()`, porque pertencem a pipelines DLT
# MAGIC distintas. DLT registra a leitura como dependência cross-pipeline pra lineage.
# MAGIC
# MAGIC ## Parâmetros
# MAGIC
# MAGIC | chave | default | descrição |
# MAGIC | --- | --- | --- |
# MAGIC | `mirante.pbf.raw_path` | `/Volumes/mirante/bronze/raw/cgu/pbf` | onde os ZIPs CGU foram baixados |

# COMMAND ----------

import re
import zipfile
from pathlib import Path
from typing import Optional

import dlt
from pyspark.sql import functions as F, types as T

RAW_PATH = spark.conf.get("mirante.pbf.raw_path", "/Volumes/mirante/bronze/raw/cgu/pbf")
print(f"raw_path={RAW_PATH}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Bronze · `mirante.bronze.pbf_pagamentos`
# MAGIC
# MAGIC Lê todos os CSVs dentro dos ZIPs em `RAW_PATH`. Como Spark não lê ZIPs nativamente,
# MAGIC esta task extrai os CSVs pra um Volume tmp e aponta o `spark.read.csv` pra ele.
# MAGIC
# MAGIC Aplica:
# MAGIC - normalização ASCII snake_case nos headers
# MAGIC - swap de header conhecido em PBF nov/2021 (mes_competencia ↔ mes_referencia)
# MAGIC - colunas de metadado: `origin`, `ano`, `mes`, `competencia`, `source_zip`, `ingest_ts`
# MAGIC - partição sintética `origin="PBF_AUX_SUM"` em 2021-11 somando PBF + AUX

# COMMAND ----------

_MONTH_RE  = re.compile(r"(?P<year>20\d{2})[_-]?(?P<month>0[1-9]|1[0-2])", re.IGNORECASE)
_SOURCE_RE = re.compile(r"^(?P<src>PBF|AUX_BR|AUX|NBF)[_-]", re.IGNORECASE)


def origin_from_name(name: str) -> str:
    m = _SOURCE_RE.match(name)
    if not m:
        return "UNK"
    src = m.group("src").upper()
    return {"AUX_BR": "AUX", "AUX": "AUX", "PBF": "PBF", "NBF": "NBF"}.get(src, src)


def yearmonth_from_name(name: str) -> tuple[int, int]:
    m = _MONTH_RE.search(name)
    if not m:
        raise ValueError(f"cannot infer year/month from {name}")
    return int(m.group("year")), int(m.group("month"))


def find_inner_csv(zip_path: Path) -> Optional[str]:
    with zipfile.ZipFile(zip_path) as zf:
        names = [n for n in zf.namelist() if n.lower().endswith(".csv")]
    if not names:
        return None
    if len(names) == 1:
        return names[0]
    with zipfile.ZipFile(zip_path) as zf:
        return max(names, key=lambda n: zf.getinfo(n).file_size)


_ACCENTS = {"Á": "A", "À": "A", "Â": "A", "Ã": "A", "É": "E", "Ê": "E", "Í": "I",
            "Ó": "O", "Ô": "O", "Õ": "O", "Ú": "U", "Ç": "C"}


def normalize_col(c: str) -> str:
    raw = c.strip().upper().replace("MÊS", "MES")
    for a, r in _ACCENTS.items():
        raw = raw.replace(a, r)
    new = re.sub(r"[^A-Z0-9]+", "_", raw).strip("_").lower()
    return new or c


def extract_zips_to_csv_dir(raw_dir: str, target_dir: str) -> list[dict]:
    """
    Extract every ZIP under raw_dir into target_dir, returning metadata per CSV.
    Idempotent: skips CSVs that already exist with non-zero size.
    """
    out = []
    Path(target_dir).mkdir(parents=True, exist_ok=True)
    for zp in sorted(Path(raw_dir).glob("*.zip")):
        try:
            year, month = yearmonth_from_name(zp.name)
        except ValueError:
            continue
        origin = origin_from_name(zp.name)
        inner  = find_inner_csv(zp)
        if not inner:
            continue
        out_name = f"{origin}__{year}_{month:02d}__{Path(inner).name}"
        out_path = Path(target_dir) / out_name
        if not out_path.exists() or out_path.stat().st_size == 0:
            with zipfile.ZipFile(zp) as zf, open(out_path, "wb") as fout:
                fout.write(zf.read(inner))
        out.append({"path": str(out_path), "origin": origin, "year": year, "month": month,
                    "source_zip": str(zp), "source_inner": inner})
    return out


@dlt.table(
    name="mirante.bronze.pbf_pagamentos",
    comment="Pagamentos PBF/Auxílio Brasil/NBF lidos dos ZIPs do Portal da Transparência (CGU). "
            "Normalização de headers + correção do swap nov/2021 + partição sintética PBF_AUX_SUM em 2021-11.",
    table_properties={"quality": "bronze"},
    partition_cols=["origin", "ano", "mes"],
)
def pbf_pagamentos():
    # Extract all ZIPs into a flat folder of CSVs (idempotent)
    csv_dir = "/Volumes/mirante/bronze/raw/cgu/pbf_csv_extracted"
    meta = extract_zips_to_csv_dir(RAW_PATH, csv_dir)
    if not meta:
        # Return empty conformant DataFrame so DLT doesn't fail on first run
        return spark.createDataFrame([], schema=T.StructType([
            T.StructField("origin",       T.StringType()),
            T.StructField("ano",          T.IntegerType()),
            T.StructField("mes",          T.IntegerType()),
            T.StructField("competencia",  T.StringType()),
            T.StructField("source_zip",   T.StringType()),
            T.StructField("source_inner", T.StringType()),
            T.StructField("ingest_ts",    T.TimestampType()),
        ]))

    # Read all CSVs in one shot — Spark resolves the schema; columns vary across years.
    df = (
        spark.read
            .option("header", "true")
            .option("sep", ";")
            .option("encoding", "latin1")
            .option("multiLine", "false")
            .option("quote", '"')
            .option("escape", '"')
            .option("mode", "PERMISSIVE")
            .csv([m["path"] for m in meta])
    )

    # Normalize columns
    for c in df.columns:
        new = normalize_col(c)
        if new != c:
            df = df.withColumnRenamed(c, new)

    # Tag each row with origin/year/month derived from filename
    df = df.withColumn("input_file", F.input_file_name())

    # Decode origin/year/month from the file name embedded in our flattened CSV name
    df = df.withColumn("_fname",  F.element_at(F.split(F.col("input_file"), "/"), -1))
    df = df.withColumn("origin",  F.split(F.col("_fname"), "__").getItem(0))
    df = df.withColumn("ym_str",  F.split(F.col("_fname"), "__").getItem(1))
    df = df.withColumn("ano",     F.split(F.col("ym_str"), "_").getItem(0).cast("int"))
    df = df.withColumn("mes",     F.split(F.col("ym_str"), "_").getItem(1).cast("int"))
    df = df.withColumn("competencia", F.format_string("%04d%02d", F.col("ano"), F.col("mes")))
    df = df.withColumn("source_zip",   F.lit("CGU"))
    df = df.withColumn("source_inner", F.col("_fname"))
    df = df.withColumn("ingest_ts",    F.current_timestamp())

    # Fix the well-known PBF nov/2021 header swap
    cols_now = set(df.columns)
    if {"mes_competencia", "mes_referencia"}.issubset(cols_now):
        df = df.withColumn(
            "mes_competencia",
            F.when((F.col("ano") == 2021) & (F.col("mes") == 11) & (F.col("origin") == F.lit("PBF")),
                   F.col("mes_referencia")).otherwise(F.col("mes_competencia"))
        )
        # NB: we keep mes_referencia as-is. The downstream Silver only reads mes_competencia.

    df = df.drop("_fname", "ym_str", "input_file")

    # Synthesize the PBF_AUX_SUM partition for 2021-11 (sum of PBF + AUX numeric cols)
    nov21 = df.where((F.col("ano") == 2021) & (F.col("mes") == 11) & (F.col("origin").isin(["PBF", "AUX"])))
    if nov21.head(1):
        meta_cols = {"origin", "ano", "mes", "competencia", "source_zip", "source_inner", "ingest_ts"}
        numeric_cols = [c for c, t in nov21.dtypes
                        if c not in meta_cols and t in ("int", "bigint", "double", "float", "decimal")]
        other_cols   = [c for c in nov21.columns if c not in meta_cols and c not in numeric_cols]
        if numeric_cols:
            agg_exprs = [F.sum(F.col(c)).alias(c) for c in numeric_cols] + \
                        [F.first(F.col(c), ignorenulls=True).alias(c) for c in other_cols]
            summed = (nov21.groupBy("ano", "mes", "competencia").agg(*agg_exprs)
                           .withColumn("origin",       F.lit("PBF_AUX_SUM"))
                           .withColumn("source_zip",   F.lit("MULTI"))
                           .withColumn("source_inner", F.lit("MULTI"))
                           .withColumn("ingest_ts",    F.current_timestamp()))
            df = df.unionByName(summed, allowMissingColumns=True)

    return df

# COMMAND ----------

# MAGIC %md
# MAGIC ## Silver · `mirante.silver.pbf_total_uf_mes`
# MAGIC
# MAGIC Aplica a regra de nov/2021 (PBF_AUX_SUM substitui PBF+AUX), parseia `valor_parcela` como Decimal,
# MAGIC e agrega por (`mes_competencia`, `uf`):
# MAGIC - `n` = beneficiários distintos por mês
# MAGIC - `n_ano` = beneficiários distintos por ano (recomputa pra Gold usar)
# MAGIC - `total_estado` = soma do valor pago

# COMMAND ----------

@dlt.table(
    name="mirante.silver.pbf_total_uf_mes",
    comment="Pagamentos PBF agregados por (Ano, Mes, UF). "
            "n_ano = beneficiários distintos por ano (chave = nis_favorecido, dígitos), repetido em cada mês.",
    table_properties={"quality": "silver"},
    partition_cols=["Ano"],
)
@dlt.expect_or_drop("uf_valida",        "uf IS NOT NULL AND length(uf) = 2")
@dlt.expect_or_drop("ano_no_intervalo", "Ano BETWEEN 2013 AND 2099")
@dlt.expect_or_drop("mes_valido",       "Mes BETWEEN 1 AND 12")
@dlt.expect_or_drop("total_positivo",   "total_estado IS NOT NULL AND total_estado >= 0")
def pbf_total_uf_mes():
    src = dlt.read("mirante.bronze.pbf_pagamentos")

    # Apply the nov/2021 origin rule:
    is_2021_11 = (F.col("ano") == 2021) & (F.col("mes") == 11)
    df = src.where(
        (is_2021_11 & (F.col("origin") == "PBF_AUX_SUM"))
        | (~is_2021_11 & (F.col("origin") != "PBF_AUX_SUM"))
    )

    # Parse valor_parcela "800,00" → Decimal(38,2)
    df = df.withColumn(
        "valor_parcela_dec",
        F.regexp_replace(F.col("valor_parcela"), ",", ".").cast(T.DecimalType(38, 2))
    )

    # Beneficiary key: digits only of nis_favorecido
    df = df.withColumn("_benef_id", F.regexp_replace(F.trim(F.col("nis_favorecido")), r"\D", ""))
    df = df.where(F.length(F.col("_benef_id")) > 0)

    # Annual distinct beneficiaries by (ano, uf), repeated on each month row downstream
    df_year = (
        df.groupBy("ano", "uf")
          .agg(F.countDistinct("_benef_id").cast("long").alias("n_ano"))
          .select(F.col("ano").cast("int").alias("Ano"), "uf", "n_ano")
    )

    out = (
        df.groupBy("mes_competencia", "uf")
          .agg(
              F.countDistinct("_benef_id").cast("long").alias("n"),
              F.sum(F.col("valor_parcela_dec")).alias("total_estado"),
          )
          .withColumn("Ano", F.substring(F.col("mes_competencia"), 1, 4).cast("int"))
          .withColumn("Mes", F.substring(F.col("mes_competencia"), 5, 2).cast("int"))
          .join(df_year, on=["Ano", "uf"], how="left")
          .select("Ano", "Mes", "uf", "mes_competencia", "n", "n_ano",
                  F.col("total_estado").cast("decimal(38,2)").alias("total_estado"))
    )
    return out

# COMMAND ----------

# MAGIC %md
# MAGIC ## Gold · `mirante.gold.pbf_estados_df`
# MAGIC
# MAGIC Une silver + dims compartilhados:
# MAGIC - PBF silver agrega ano/UF (já tem n_ano via Silver)
# MAGIC - join com `silver.populacao_uf_ano` (deflator-friendly per capita)
# MAGIC - join com `silver.ipca_deflators_2021` (calcula valor_2021)
# MAGIC - métricas derivadas: `pbfPerBenef`, `pbfPerCapita`
# MAGIC
# MAGIC **Schema final** (igual ao JSON consumido pelo front):
# MAGIC ```
# MAGIC Ano: int  uf: string  n_benef: long  valor_nominal: double  valor_2021: double
# MAGIC populacao: long  pbfPerBenef: double  pbfPerCapita: double
# MAGIC ```

# COMMAND ----------

@dlt.table(
    name="mirante.gold.pbf_estados_df",
    comment="UF × Ano: PBF beneficiários, valor nominal (R$ bi), valor R$2021 (R$ bi), "
            "população (IBGE), PBF per beneficiário (R$ 2021), PBF per capita (R$ 2021). "
            "Schema bate com /data/gold/gold_pbf_estados_df.json no front.",
    table_properties={"quality": "gold"},
    partition_cols=["Ano"],
)
@dlt.expect_or_drop("uf_valida",          "uf IS NOT NULL AND length(uf) = 2")
@dlt.expect_or_drop("ano_no_intervalo",   "Ano BETWEEN 2013 AND 2099")
@dlt.expect_or_drop("valores_positivos",  "valor_nominal >= 0 AND valor_2021 >= 0")
@dlt.expect_or_drop("populacao_presente", "populacao IS NOT NULL AND populacao > 0")
@dlt.expect("per_capita_razoavel",        "pbfPerCapita BETWEEN 0 AND 5000")
@dlt.expect("per_benef_razoavel",         "pbfPerBenef  BETWEEN 0 AND 50000")
def pbf_estados_df():
    silver = dlt.read("mirante.silver.pbf_total_uf_mes")

    # Cross-pipeline reads: dims compartilhadas
    pop_dim  = spark.read.table("mirante.silver.populacao_uf_ano").select("Ano", "uf", "populacao")
    defl_dim = spark.read.table("mirante.silver.ipca_deflators_2021").select("Ano", "deflator_to_2021")

    # Aggregate UF×Ano values from silver (silver was UF×Ano×Mes)
    valores = (
        silver.groupBy("Ano", "uf")
              .agg((F.sum("total_estado") / F.lit(1e9)).cast("double").alias("valor_nominal"))
    )
    benef = silver.select("Ano", "uf", "n_ano").distinct()\
                   .withColumnRenamed("n_ano", "n_benef")\
                   .withColumn("n_benef", F.col("n_benef").cast("long"))

    df = (
        valores.join(benef,    on=["Ano", "uf"], how="left")
               .join(pop_dim,  on=["Ano", "uf"], how="left")
               .join(defl_dim, on=["Ano"],       how="left")
    )

    df = df.withColumn("valor_2021",  F.col("valor_nominal") * F.col("deflator_to_2021"))
    df = df.withColumn("pbfPerBenef", (F.col("valor_2021") * F.lit(1e9)) / F.col("n_benef"))
    df = df.withColumn("pbfPerCapita",(F.col("valor_2021") * F.lit(1e9)) / F.col("populacao"))

    return df.select(
        "Ano", "uf",
        F.col("n_benef").cast("long").alias("n_benef"),
        F.col("valor_nominal").cast("double").alias("valor_nominal"),
        F.col("valor_2021").cast("double").alias("valor_2021"),
        F.col("populacao").cast("long").alias("populacao"),
        F.col("pbfPerBenef").cast("double").alias("pbfPerBenef"),
        F.col("pbfPerCapita").cast("double").alias("pbfPerCapita"),
    ).orderBy("Ano", "uf")

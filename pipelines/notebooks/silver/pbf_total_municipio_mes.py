# Databricks notebook source
# MAGIC %md
# MAGIC # silver · pbf_total_municipio_mes
# MAGIC
# MAGIC Variante municipal do `silver.pbf_total_uf_mes`. Lê `bronze.pbf_pagamentos`
# MAGIC e agrega por `(Ano, Mes, cod_municipio_ibge, uf)` em vez de UF.
# MAGIC
# MAGIC **Lookup IBGE:** o bronze CGU usa `codigo_municipio_siafi` (4-6 dígitos),
# MAGIC NÃO o IBGE 7-dígitos. Convertemos via join com `silver.populacao_municipio_ano`
# MAGIC em `(uf, normalize(nome_municipio))`. SIDRA/IBGE retorna nomes no formato
# MAGIC "Maricá - RJ" — o silver populacao já parseou em colunas separadas.
# MAGIC
# MAGIC **Saída:** ~5.570 munis × ~150 meses ≈ 835k linhas
# MAGIC (vs ~4.3k linhas do silver UF).
# MAGIC
# MAGIC Schema:
# MAGIC `Ano int, Mes int, cod_municipio string (7 dig IBGE), uf string,
# MAGIC  mes_competencia int, n long, n_ano long, total_municipio decimal(38,2)`

# COMMAND ----------

dbutils.widgets.text("catalog", "mirante_prd")
CATALOG = dbutils.widgets.get("catalog")

BRONZE_TABLE     = f"{CATALOG}.bronze.pbf_pagamentos"
DIM_GEOBR        = f"{CATALOG}.bronze.geobr_municipios_meta"   # canônico IPEA
SILVER_TABLE     = f"{CATALOG}.silver.pbf_total_municipio_mes"

print(f"bronze={BRONZE_TABLE}\nsilver={SILVER_TABLE}\ndim={DIM_GEOBR}")

# COMMAND ----------

from pyspark.sql import functions as F, types as T

bronze = spark.read.table(BRONZE_TABLE)
print(f"bronze rows: {bronze.count():,}")

# COMMAND ----------

# MAGIC %md ## Fix nov/2021 PBF header swap (mesmo do silver UF)

# COMMAND ----------

if {"mes_competencia", "mes_referencia"}.issubset(set(bronze.columns)):
    df = bronze.withColumn(
        "mes_competencia",
        F.when(
            (F.col("ano") == 2021) & (F.col("mes") == 11) & (F.col("origin") == "PBF"),
            F.col("mes_referencia"),
        ).otherwise(F.col("mes_competencia"))
    )
else:
    df = bronze

# Síntese PBF_AUX_SUM em nov/2021 (sobreposição PBF→AB)
nov21_raw = df.where(
    (F.col("ano") == 2021) & (F.col("mes") == 11) & (F.col("origin").isin(["PBF", "AUX"]))
)
if nov21_raw.head(1):
    meta_cols = {"origin", "ano", "mes", "competencia", "_source_file", "_ingest_ts"}
    numeric_cols = [c for c, t in nov21_raw.dtypes
                    if c not in meta_cols and t in ("int", "bigint", "double", "float", "decimal")]
    other_cols = [c for c in nov21_raw.columns if c not in meta_cols and c not in numeric_cols]
    if numeric_cols:
        agg_exprs = ([F.sum(F.col(c)).alias(c) for c in numeric_cols]
                     + [F.first(F.col(c), ignorenulls=True).alias(c) for c in other_cols])
        synthetic = (
            nov21_raw.groupBy("ano", "mes", "competencia").agg(*agg_exprs)
                     .withColumn("origin",       F.lit("PBF_AUX_SUM"))
                     .withColumn("_source_file", F.lit("SYNTHETIC"))
                     .withColumn("_ingest_ts",   F.current_timestamp())
        )
        df = df.unionByName(synthetic, allowMissingColumns=True)

is_2021_11 = (F.col("ano") == 2021) & (F.col("mes") == 11)
df = df.where(
    (is_2021_11 & (F.col("origin") == "PBF_AUX_SUM"))
    | (~is_2021_11 & (F.col("origin") != "PBF_AUX_SUM"))
)

# COMMAND ----------

# MAGIC %md ## Casts numéricos + extrai Ano/Mes de mes_competencia

# COMMAND ----------

# Bronze é STRING-ONLY: valor_parcela vem como "600,00" ou "600.00"; nis vem string
df = (
    df.withColumn("valor_parcela_dec",
                  F.regexp_replace(F.col("valor_parcela"), ",", ".").cast(T.DecimalType(38, 2)))
      .withColumn("_benef_id",
                  F.regexp_replace(F.trim(F.col("nis_favorecido").cast("string")), r"\D", ""))
      .where(F.length(F.col("_benef_id")) > 0)
      .withColumn("Ano",
                  F.substring(F.col("mes_competencia").cast("string"), 1, 4).cast("int"))
      .withColumn("Mes",
                  F.substring(F.col("mes_competencia").cast("string"), 5, 2).cast("int"))
)

# COMMAND ----------

# MAGIC %md ## Lookup IBGE via join com populacao_municipio_ano
# MAGIC
# MAGIC Bronze CGU usa SIAFI 4-6 dig + nome. Convertemos pra IBGE 7-dig fazendo
# MAGIC match por `(uf, normalize(nome_municipio))` contra a dimensão municipal.
# MAGIC Normalização: lowercase, strip acentos, strip espaços+pontuação.

# COMMAND ----------

if not spark.catalog.tableExists(DIM_GEOBR):
    raise RuntimeError(
        f"{DIM_GEOBR} não existe — rode ingest/geobr_municipios.py primeiro."
    )

# Dimensão muni canônica do IPEA (geobr): code_muni IBGE 7-dig + name_muni + abbrev_state
dim_muni = (
    spark.read.table(DIM_GEOBR)
        .select(
            F.col("code_muni").alias("cod_municipio"),
            F.col("name_muni").alias("municipio"),
            F.col("abbrev_state").alias("uf"),
        )
        .where(F.col("cod_municipio").isNotNull() & (F.length("cod_municipio") == 7))
        .distinct()
)
n_dim = dim_muni.count()
print(f"dim_muni: {n_dim:,} (cod_municipio, municipio, uf) distintos")

def normalize_name_col(c):
    """lower → strip diacríticos → remove pontuação/espaços."""
    return F.regexp_replace(
        F.translate(
            F.lower(c),
            "áàâãäéèêëíìîïóòôõöúùûüçñ'.-",
            "aaaaaeeeeiiiiooooouuuuc n   ",
        ),
        r"\s+", "",
    )

bronze_norm = (
    df.withColumn("_uf_norm",       F.upper(F.trim(F.col("uf"))))
      .withColumn("_nome_norm",     normalize_name_col(F.col("nome_municipio")))
)
dim_norm = (
    dim_muni.withColumn("_uf_norm", F.upper(F.trim(F.col("uf"))))
            .withColumn("_nome_norm", normalize_name_col(F.col("municipio")))
            .select("cod_municipio", "_uf_norm", "_nome_norm")
)

# Broadcast a dim — tem só ~5570 linhas
df_with_ibge = (
    bronze_norm.join(F.broadcast(dim_norm),
                     on=["_uf_norm", "_nome_norm"], how="left")
)

# DQ: quantos não bateram?
n_total_pre  = df_with_ibge.count()
n_no_match   = df_with_ibge.where(F.col("cod_municipio").isNull()).count()
n_match_pct  = 100.0 * (n_total_pre - n_no_match) / max(n_total_pre, 1)
print(f"match IBGE: {n_total_pre - n_no_match:,}/{n_total_pre:,} ({n_match_pct:.2f}%)")
if n_no_match > 0:
    print("Sample não-matches (uf, nome_municipio, normalizado):")
    df_with_ibge.where(F.col("cod_municipio").isNull()) \
                .select("uf", "nome_municipio", "_nome_norm").distinct().show(15, truncate=False)

df_with_ibge = df_with_ibge.where(F.col("cod_municipio").isNotNull())

# COMMAND ----------

# MAGIC %md ## Aggregate Município × Ano × Mes

# COMMAND ----------

# Beneficiários distintos por ano (lookup pra cada Ano × cod_municipio)
df_year = (
    df_with_ibge.groupBy("Ano", "cod_municipio")
                 .agg(F.countDistinct("_benef_id").cast("long").alias("n_ano"))
)

silver_df = (
    df_with_ibge
        .groupBy("Ano", "Mes", "cod_municipio", "uf", "mes_competencia")
        .agg(
            F.countDistinct("_benef_id").cast("long").alias("n"),
            F.sum(F.col("valor_parcela_dec")).alias("total_municipio"),
        )
        .join(df_year, on=["Ano", "cod_municipio"], how="left")
        .select(
            "Ano", "Mes", "cod_municipio", "uf", "mes_competencia",
            F.col("n").cast("long"),
            F.col("n_ano").cast("long"),
            F.col("total_municipio").cast("decimal(38,2)"),
        )
        .withColumn("_silver_built_ts", F.current_timestamp())
)

# DQ: range temporal + UFs válidas
VALID_UFS = ["AC","AL","AM","AP","BA","CE","DF","ES","GO","MA","MG","MS","MT",
             "PA","PB","PE","PI","PR","RJ","RN","RO","RR","RS","SC","SE","SP","TO"]
n_before = silver_df.count()
silver_df = silver_df.where(
    F.col("Ano").isNotNull() & (F.col("Ano") >= 2013) & (F.col("Ano") <= F.year(F.current_date()))
    & F.col("Mes").isNotNull() & (F.col("Mes").between(1, 12))
    & F.col("uf").isin(VALID_UFS)
    & F.col("cod_municipio").isNotNull() & (F.length("cod_municipio") == 7)
)
n_after = silver_df.count()
distinct_years = sorted(r["Ano"] for r in silver_df.select("Ano").distinct().collect())
distinct_munis = silver_df.select("cod_municipio").distinct().count()
print(f"silver years ({len(distinct_years)}): {distinct_years[0]}..{distinct_years[-1]}")
print(f"silver municípios distintos: {distinct_munis:,} (esperado ~5570)")
if n_after < n_before:
    print(f"⚠ filtrou {n_before - n_after:,} linhas fora do range; mantém {n_after:,}")

assert distinct_munis >= 5500, (
    f"Munis distintos = {distinct_munis} — esperado ≥ 5500. "
    f"Investigar lookup IBGE no bronze."
)
print("✔ DQ passed")

# COMMAND ----------

(
    silver_df.write.format("delta")
        .mode("overwrite")
        .option("overwriteSchema", "true")
        .partitionBy("Ano")
        .saveAsTable(SILVER_TABLE)
)

# UC metadata
spark.sql(f"""
COMMENT ON TABLE {SILVER_TABLE} IS
'Mirante · PBF agregado Município × Ano × Mes (~5.570 munis × ~150 meses ≈ 835k linhas).
n = beneficiários distintos por mês; n_ano = distintos no ano (broadcast em todas as linhas);
total_municipio = soma valor_parcela em R$ nominais (decimal 38,2).
Origens unificadas: PBF (Lei 10.836/2003) + Auxílio Brasil (MP 1.061/2021) +
Novo Bolsa Família (Lei 14.601/2023). Variante municipal do silver.pbf_total_uf_mes —
usado pelo WP#7 (5.570 clusters para identificação causal robusta a few-clusters do WP#2).
Lookup IBGE feito via join com silver.populacao_municipio_ano em (uf, normalize(nome_municipio)).'
""")

for col, comment in [
    ("Ano",              "Ano de competência (substring de mes_competencia)."),
    ("Mes",              "Mês de competência 1-12."),
    ("cod_municipio",    "Código IBGE 7 dígitos com DV (resolvido via lookup contra populacao_municipio_ano)."),
    ("uf",               "Sigla 2-letter da UF."),
    ("mes_competencia",  "YYYYMM int preservado do bronze."),
    ("n",                "Beneficiários distintos por NIS no mês (countDistinct)."),
    ("n_ano",            "Beneficiários distintos por NIS no ano (broadcast)."),
    ("total_municipio",  "Soma valor_parcela em R$ nominais decimal(38,2)."),
]:
    try:
        spark.sql(f"ALTER TABLE {SILVER_TABLE} ALTER COLUMN `{col}` COMMENT "
                  f"'{comment.replace(chr(39), chr(39)*2)}'")
    except Exception as e:
        print(f"  ⚠ comment {col}: {e}")

spark.sql(f"ALTER TABLE {SILVER_TABLE} SET TAGS ("
          f"'layer' = 'silver', 'domain' = 'social_protection', "
          f"'source' = 'cgu_portal_transparencia', 'pii' = 'false', "
          f"'grain' = 'municipio_ano_mes')")

print(f"✔ {SILVER_TABLE} written ({n_after:,} rows; {distinct_munis} munis × {len(distinct_years)} anos)")

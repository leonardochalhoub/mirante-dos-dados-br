# Databricks notebook source
# MAGIC %md
# MAGIC # silver · pbf_total_municipio_mes
# MAGIC
# MAGIC Variante municipal do `silver.pbf_total_uf_mes`. Lê o mesmo bronze
# MAGIC `<catalog>.bronze.pbf_pagamentos` (string-only) e agrega por
# MAGIC `(Ano, Mes, cod_municipio_ibge)` em vez de UF. Mantém o mesmo
# MAGIC tratamento de nov/2021 (PBF_AUX_SUM substitui PBF+AUX) e a mesma
# MAGIC regra de Ano por `mes_competencia` (não pelo Ano do arquivo).
# MAGIC
# MAGIC Saída tem ~5.570 munis × ~150 meses = ~835k linhas (vs ~4.3k linhas UF).
# MAGIC
# MAGIC | param | default |
# MAGIC | --- | --- |
# MAGIC | `catalog` | `mirante_prd` |
# MAGIC
# MAGIC Output: `<catalog>.silver.pbf_total_municipio_mes`
# MAGIC Schema: `Ano int, Mes int, cod_municipio int, uf string, mes_competencia string,
# MAGIC          n long, n_ano long, total_municipio decimal(38,2)`

# COMMAND ----------

dbutils.widgets.text("catalog", "mirante_prd")
CATALOG = dbutils.widgets.get("catalog")

BRONZE_TABLE = f"{CATALOG}.bronze.pbf_pagamentos"
SILVER_TABLE = f"{CATALOG}.silver.pbf_total_municipio_mes"

print(f"bronze={BRONZE_TABLE}  silver={SILVER_TABLE}")

# COMMAND ----------

from pyspark.sql import functions as F, types as T

bronze = spark.read.table(BRONZE_TABLE)
print(f"bronze rows: {bronze.count():,}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Fix nov/2021 PBF header swap + apply origin rule (idêntico ao silver UF)

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

# MAGIC %md
# MAGIC ## Aggregate Município × Ano × Mes
# MAGIC
# MAGIC O bronze é STRING-ONLY (memory: feedback_bronze_string_only.md). Casts pra
# MAGIC numéricos acontecem aqui no silver. cod_municipio_ibge e uf são preservados
# MAGIC como strings na agregação; cast pra int no schema final.

# COMMAND ----------

df = df.withColumn(
    "valor_parcela_dec",
    F.regexp_replace(F.col("valor_parcela"), ",", ".").cast(T.DecimalType(38, 2))
)
df = df.withColumn("_benef_id", F.regexp_replace(F.trim(F.col("nis_favorecido")), r"\D", ""))
df = df.where(F.length(F.col("_benef_id")) > 0)

# Ano de competência (mesma regra do silver UF)
df = (
    df.withColumn("Ano", F.substring(F.col("mes_competencia"), 1, 4).cast("int"))
      .withColumn("Mes", F.substring(F.col("mes_competencia"), 5, 2).cast("int"))
)

# Município IBGE — campo do CGU é codigo_municipio_ibge (7 dígitos). Algumas
# competências antigas podem ter 6 dígitos (sem dígito verificador) — normalizar.
COD_FIELD = next(
    (c for c in df.columns if c.lower() in
     ("codigo_municipio_ibge", "cod_municipio_ibge", "cd_municipio_ibge",
      "codigo_municipio", "municipio_codigo")),
    None,
)
if COD_FIELD is None:
    raise RuntimeError(
        f"Bronze não tem coluna de código municipal IBGE. "
        f"Colunas disponíveis: {sorted(df.columns)}"
    )
print(f"Coluna municipal escolhida do bronze: {COD_FIELD}")

df = df.withColumn(
    "cod_municipio",
    F.regexp_replace(F.col(COD_FIELD), r"\D", "")
)
# Padronizar para 7 dígitos (IBGE atual). Códigos de 6 dígitos (PBF antigo) recebem
# o dígito verificador IBGE via lookup contra silver.coords_municipios — para
# manter este silver auto-contido, mantemos 6/7 e o gold faz o join.
df = df.where(F.length("cod_municipio").isin(6, 7))

# UF (sigla 2-letter) — campo CGU é sigla_uf ou uf
UF_FIELD = next(
    (c for c in df.columns if c.lower() in ("sigla_uf", "uf")),
    None,
)
if UF_FIELD and UF_FIELD != "uf":
    df = df.withColumnRenamed(UF_FIELD, "uf")

# COMMAND ----------

# Beneficiários distintos por ano (lookup pra cada (Ano, cod_municipio))
df_year = (
    df.groupBy("Ano", "cod_municipio")
      .agg(F.countDistinct("_benef_id").cast("long").alias("n_ano"))
)

silver_df = (
    df.groupBy("Ano", "Mes", "cod_municipio", "uf", "mes_competencia")
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

# DQ: bound de range temporal e UFs válidas (mesma régua do silver UF)
VALID_UFS = ["AC","AL","AM","AP","BA","CE","DF","ES","GO","MA","MG","MS","MT",
             "PA","PB","PE","PI","PR","RJ","RN","RO","RR","RS","SC","SE","SP","TO"]
n_before = silver_df.count()
silver_df = silver_df.where(
    F.col("Ano").isNotNull()
    & (F.col("Ano") >= 2013)
    & (F.col("Ano") <= F.year(F.current_date()))
    & F.col("Mes").isNotNull() & (F.col("Mes").between(1, 12))
    & F.col("uf").isin(VALID_UFS)
    & F.col("cod_municipio").isNotNull()
)
n_after = silver_df.count()
distinct_years = sorted(r["Ano"] for r in silver_df.select("Ano").distinct().collect())
distinct_munis = silver_df.select("cod_municipio").distinct().count()
print(f"silver years kept ({len(distinct_years)}): {distinct_years}")
print(f"silver municípios distintos: {distinct_munis:,} (esperado ~5570)")
if n_after < n_before:
    print(f"⚠ filtrou {n_before - n_after:,} linhas silver fora do range esperado "
          f"(mantém {n_after:,} válidas)")

# COMMAND ----------

assert distinct_munis >= 5500, (
    f"Munis distintos = {distinct_munis} — esperado ≥ 5500. "
    f"Investigar bronze.pbf_pagamentos para perda de cobertura municipal."
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

# UC metadata (memory: feedback_unity_catalog_metadata.md)
spark.sql(f"COMMENT ON TABLE {SILVER_TABLE} IS "
          f"'Mirante · PBF agregado Município × Ano × Mes (~5.570 munis × 150 meses ≈ 835k linhas). "
          f"n = beneficiários distintos por mês; n_ano = distintos no ano (broadcast em todas as linhas do mês); "
          f"total_municipio = soma valor_parcela em R$ nominais (decimal 38,2). "
          f"Origens unificadas: PBF (Lei 10.836/2003) + Auxílio Brasil (MP 1.061/2021) + Novo Bolsa Família "
          f"(Lei 14.601/2023). Variante municipal do silver.pbf_total_uf_mes — usado pelo WP#7 (5.570 clusters '
          f"para identificação causal robusta a few-clusters do WP#2). "
          f"Reaplicar metadata rico via job_apply_catalog_metadata.'")

for col, comment in [
    ("Ano",              "Ano de competência (substring de mes_competencia, NÃO Ano do arquivo)."),
    ("Mes",              "Mês de competência 1–12."),
    ("cod_municipio",    "Código IBGE do município (6 ou 7 dígitos; gold normaliza pra 7)."),
    ("uf",               "Sigla 2-letter da UF do município."),
    ("mes_competencia",  "YYYYMM string preservado do bronze."),
    ("n",                "Beneficiários distintos por NIS no mês (countDistinct)."),
    ("n_ano",            "Beneficiários distintos por NIS no ano (broadcast)."),
    ("total_municipio",  "Soma valor_parcela R$ nominais decimal(38,2)."),
]:
    spark.sql(
        f"ALTER TABLE {SILVER_TABLE} ALTER COLUMN {col} COMMENT '{comment.replace(chr(39), chr(39)*2)}'"
    )

spark.sql(f"ALTER TABLE {SILVER_TABLE} SET TAGS ("
          f"'layer' = 'silver', 'domain' = 'social_protection', "
          f"'source' = 'cgu_portal_transparencia', 'pii' = 'none', "
          f"'grain' = 'municipio_ano_mes')")

print(f"✔ {SILVER_TABLE} written ({n_after:,} rows; {distinct_munis} munis × {len(distinct_years)} anos)")

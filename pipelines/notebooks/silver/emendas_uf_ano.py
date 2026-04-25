# Databricks notebook source
# MAGIC %md
# MAGIC # silver · emendas_uf_ano
# MAGIC
# MAGIC Lê `<catalog>.bronze.emendas_pagamentos`, agrega por `(uf_favorecido, ano)` com
# MAGIC split por **tipo de emenda** (RP6 individual / RP7 bancada / RP9 relator):
# MAGIC
# MAGIC - `valor_empenhado` (R$ nominal)
# MAGIC - `valor_pago` (R$ nominal — execução efetiva)
# MAGIC - `valor_restos_a_pagar` (compromissos pendentes)
# MAGIC - `n_emendas` (distintas)
# MAGIC - `n_municipios_beneficiados` (UFs onde o dinheiro caiu)
# MAGIC
# MAGIC O CSV CGU tem nomes de coluna que variam ano-a-ano. O notebook tenta múltiplos
# MAGIC aliases e registra schema final. Se faltar coluna, log mostra warning.

# COMMAND ----------

dbutils.widgets.text("catalog", "mirante_prd")
CATALOG = dbutils.widgets.get("catalog")

BRONZE_TABLE = f"{CATALOG}.bronze.emendas_pagamentos"
SILVER_TABLE = f"{CATALOG}.silver.emendas_uf_ano"

print(f"bronze={BRONZE_TABLE}  silver={SILVER_TABLE}")

# COMMAND ----------

from pyspark.sql import functions as F, types as T

# Read latest snapshot (one batch worth)
bronze = spark.read.table(BRONZE_TABLE)
if bronze.head(1) == []:
    raise ValueError(f"{BRONZE_TABLE} is empty.")

latest_ts = bronze.agg(F.max("_ingest_ts")).first()[0]
src = bronze.where(F.col("_ingest_ts") == latest_ts)
print(f"bronze latest snapshot: {src.count():,} rows  cols={src.columns[:8]}…")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Resolve column aliases (CGU schema varies year-to-year)

# COMMAND ----------

def first_existing(df, *candidates: str):
    """Return F.col() of the first matching column name, or F.lit(None) if none found."""
    cols = set(df.columns)
    for c in candidates:
        if c in cols:
            return F.col(c)
    return F.lit(None)


# Map possible field names to canonical names.
# Atual schema CGU EmendasParlamentares.csv (2026-04): ano_da_emenda, tipo_de_emenda,
# codigo_da_emenda, codigo_municipio_ibge, uf, valor_empenhado, valor_pago,
# valor_restos_a_pagar_inscritos. Aliases extras cobrem renames históricos.
df = src.select(
    first_existing(src, "ano_da_emenda", "ano", "ano_emenda", "exercicio").cast("int").alias("Ano"),
    first_existing(src, "uf", "uf_favorecido", "uf_beneficiario", "favorecido_uf",
                        "estado_favorecido").cast("string").alias("uf"),
    first_existing(src, "tipo_de_emenda", "tipo_emenda", "tipo", "rp",
                        "resultado_primario").cast("string").alias("tipo_emenda"),
    first_existing(src, "codigo_da_emenda", "codigo_emenda", "id_emenda",
                        "numero_da_emenda", "numero_emenda").cast("string").alias("codigo_emenda"),
    first_existing(src, "valor_empenhado", "vl_empenhado", "empenhado",
                        "valor_total_empenhado").cast("string").alias("vempenhado_str"),
    first_existing(src, "valor_pago", "vl_pago", "pago", "valor_pago_total").cast("string").alias("vpago_str"),
    first_existing(src, "valor_restos_a_pagar_inscritos", "valor_restos_a_pagar",
                        "valor_resto_pagar", "vl_resto_pagar",
                        "valor_restos_pagar_pagos").cast("string").alias("vrap_str"),
    first_existing(src, "codigo_municipio_ibge", "codigo_municipio_siafi",
                        "codigo_ibge_municipio", "municipio_codigo").cast("string").alias("cod_municipio"),
)

# Convert BR numeric strings ("1.234,56") → double
def br_num(col):
    return (F.regexp_replace(F.regexp_replace(col, r"\.", ""), ",", ".")).cast("double")


df = (
    df
    .withColumn("valor_empenhado",      F.coalesce(br_num(F.col("vempenhado_str")), F.lit(0.0)))
    .withColumn("valor_pago",           F.coalesce(br_num(F.col("vpago_str")),      F.lit(0.0)))
    .withColumn("valor_restos_a_pagar", F.coalesce(br_num(F.col("vrap_str")),       F.lit(0.0)))
    .drop("vempenhado_str", "vpago_str", "vrap_str")
)

# CGU envia UF como nome completo em pt-BR ("CEARÁ", "MINAS GERAIS"). Mapear pra 2-letter.
# Strip accents + upper() na lookup pra não depender de variação de acento na fonte.
UF_NAME_TO_CODE = {
    "ACRE": "AC", "ALAGOAS": "AL", "AMAZONAS": "AM", "AMAPA": "AP",
    "BAHIA": "BA", "CEARA": "CE", "DISTRITO FEDERAL": "DF",
    "ESPIRITO SANTO": "ES", "GOIAS": "GO", "MARANHAO": "MA",
    "MINAS GERAIS": "MG", "MATO GROSSO DO SUL": "MS", "MATO GROSSO": "MT",
    "PARA": "PA", "PARAIBA": "PB", "PERNAMBUCO": "PE", "PIAUI": "PI",
    "PARANA": "PR", "RIO DE JANEIRO": "RJ", "RIO GRANDE DO NORTE": "RN",
    "RONDONIA": "RO", "RORAIMA": "RR", "RIO GRANDE DO SUL": "RS",
    "SANTA CATARINA": "SC", "SERGIPE": "SE", "SAO PAULO": "SP",
    "TOCANTINS": "TO",
}

# Strip accents in Spark via translate() (não há unidecode no cluster).
ACCENT_FROM = "ÁÀÂÃÄÉÈÊËÍÌÎÏÓÒÔÕÖÚÙÛÜÇáàâãäéèêëíìîïóòôõöúùûüç"
ACCENT_TO   = "AAAAAEEEEIIIIOOOOOUUUUCaaaaaeeeeiiiiooooouuuuc"
uf_norm = F.upper(F.translate(F.col("uf"), ACCENT_FROM, ACCENT_TO))

# Build mapping expression: chained F.when() based on the dict
uf_mapping = F.lit(None).cast("string")
for full_name, code in UF_NAME_TO_CODE.items():
    uf_mapping = F.when(uf_norm == full_name, F.lit(code)).otherwise(uf_mapping)

# If "uf" already came as 2-letter code (some downstream tools normalize this),
# keep as-is. Otherwise apply the mapping.
df = df.withColumn(
    "uf",
    F.when(F.length(F.col("uf")) == 2, F.upper(F.col("uf"))).otherwise(uf_mapping),
)

# Defensive filter: keep only valid (Ano, uf, tipo_emenda) rows
VALID_UFS = ["AC","AL","AM","AP","BA","CE","DF","ES","GO","MA","MG","MS","MT",
             "PA","PB","PE","PI","PR","RJ","RN","RO","RR","RS","SC","SE","SP","TO"]
df = df.where(
    F.col("Ano").isNotNull() & (F.col("Ano") >= 2014) & (F.col("Ano") <= F.year(F.current_date()))
    & F.col("uf").isin(VALID_UFS)
)

# Normalize tipo_emenda to one of {RP6, RP7, RP8, RP9, OUTRO}.
# CGU values são mixed case ("Emenda Individual - Transferências...") — upper() antes do contains.
te = F.upper(F.coalesce(F.col("tipo_emenda"), F.lit("")))
df = df.withColumn(
    "tipo_emenda",
    F.when(te.contains("RP-6") | te.contains("RP6") | te.contains("INDIVIDUAL"), F.lit("RP6"))
     .when(te.contains("RP-7") | te.contains("RP7") | te.contains("BANCADA"),    F.lit("RP7"))
     .when(te.contains("RP-9") | te.contains("RP9") | te.contains("RELATOR"),    F.lit("RP9"))
     .when(te.contains("RP-8") | te.contains("RP8") | te.contains("COMISSAO"),   F.lit("RP8"))
     .otherwise(F.lit("OUTRO"))
)

# COMMAND ----------

silver_df = (
    df.groupBy("Ano", "uf", "tipo_emenda")
      .agg(
          F.countDistinct("codigo_emenda").cast("long").alias("n_emendas"),
          F.countDistinct("cod_municipio").cast("long").alias("n_municipios"),
          F.sum("valor_empenhado").alias("valor_empenhado"),
          F.sum("valor_pago").alias("valor_pago"),
          F.sum("valor_restos_a_pagar").alias("valor_restos_a_pagar"),
      )
      .withColumn("_silver_built_ts", F.current_timestamp())
      .orderBy("Ano", "uf", "tipo_emenda")
)

# COMMAND ----------

n = silver_df.count()
ufs = silver_df.select("uf").distinct().count()
years = silver_df.select("Ano").distinct().count()
tipos = sorted(r["tipo_emenda"] for r in silver_df.select("tipo_emenda").distinct().collect())
print(f"rows={n}  ufs={ufs}  years={years}  tipos={tipos}")
assert ufs <= 27, f"Got {ufs} UFs"
print("✔ DQ passed")

# COMMAND ----------

(
    silver_df.write.format("delta")
        .mode("overwrite")
        .option("overwriteSchema", "true")
        .partitionBy("Ano")
        .saveAsTable(SILVER_TABLE)
)

spark.sql(f"COMMENT ON TABLE {SILVER_TABLE} IS "
          f"'Mirante · Emendas Parlamentares por UF × Ano × tipo_RP "
          f"(empenhado/pago/restos). Fonte: Portal Transparência CGU.'")

print(f"✔ {SILVER_TABLE} written ({n} rows)")

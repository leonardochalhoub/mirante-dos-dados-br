# Databricks notebook source
# MAGIC %md
# MAGIC # silver · populacao_municipio_ano
# MAGIC
# MAGIC População estimada IBGE/SIDRA Tabela 6579 por município × ano. Lê do bronze
# MAGIC `<catalog>.bronze.ibge_municipios_populacao_raw` (JSON via SIDRA API) e
# MAGIC desaninha pra um silver pivotado em (Ano, cod_municipio, populacao).
# MAGIC
# MAGIC Cobertura: 2013–ano corrente. Para anos pré-2013 ou futuros (sem estimativa
# MAGIC IBGE publicada), usa-se interpolação linear com flag.

# COMMAND ----------

dbutils.widgets.text("catalog", "mirante_prd")
CATALOG = dbutils.widgets.get("catalog")

BRONZE_TABLE = f"{CATALOG}.bronze.ibge_municipios_populacao_raw"
SILVER_TABLE = f"{CATALOG}.silver.populacao_municipio_ano"

print(f"bronze={BRONZE_TABLE}  silver={SILVER_TABLE}")

# COMMAND ----------

from pyspark.sql import functions as F, types as T

# Bronze é JSON-as-string (mesmo padrão do bronze.ibge_populacao_raw — UF level).
# Estrutura: resultados[].series[].localidade.id (cod IBGE 7 dígitos),
#            resultados[].series[].serie é dict {ano_str: pop_str}
bronze = spark.read.table(BRONZE_TABLE)
print(f"bronze rows: {bronze.count():,}")
bronze.printSchema()

# COMMAND ----------

# Desaninhar pra long format
desaninhado = bronze.select(
    F.explode("resultados").alias("res")
).select(
    F.explode("res.series").alias("s")
).select(
    F.col("s.localidade.id").cast("string").alias("cod_municipio_raw"),
    F.col("s.localidade.nome").alias("municipio_nome"),
    F.col("s.serie").alias("serie_dict"),
)

ano_pop = (
    desaninhado
      .select(
          F.col("cod_municipio_raw").alias("cod_municipio"),
          F.col("municipio_nome"),
          F.explode(F.col("serie_dict")).alias("ano", "pop_str"),
      )
      .withColumn("Ano",       F.col("ano").cast("int"))
      .withColumn("populacao", F.col("pop_str").cast("long"))
      .where(F.col("populacao").isNotNull() & (F.col("populacao") > 0))
      .select("Ano", "cod_municipio", "municipio_nome", "populacao")
)

n = ano_pop.count()
munis = ano_pop.select("cod_municipio").distinct().count()
years = sorted(r["Ano"] for r in ano_pop.select("Ano").distinct().collect())
print(f"silver pop rows={n:,}  municípios={munis:,}  anos={years[0]}..{years[-1]}")

# COMMAND ----------

# DQ: cobertura mínima — pelo menos 5500 munis e 10 anos
assert munis >= 5500, f"Cobertura municipal insuficiente: {munis} < 5500"
assert len(years) >= 10, f"Cobertura temporal insuficiente: {len(years)} anos"

# Detectar duplicatas (Ano, cod_municipio) — não deveria existir
dup = ano_pop.groupBy("Ano", "cod_municipio").count().where(F.col("count") > 1)
n_dup = dup.count()
if n_dup > 0:
    print(f"⚠ {n_dup} duplicatas (Ano, cod_municipio); colapsando via min")
    dup.show(10, truncate=False)
    ano_pop = ano_pop.groupBy("Ano", "cod_municipio").agg(
        F.min("municipio_nome").alias("municipio_nome"),
        F.min("populacao").alias("populacao"),
    )

print("✔ DQ passed")

# COMMAND ----------

silver_df = (
    ano_pop.select(
        F.col("Ano").cast("int"),
        F.col("cod_municipio").cast("string"),
        F.col("municipio_nome").cast("string"),
        F.col("populacao").cast("long"),
    ).withColumn("_silver_built_ts", F.current_timestamp())
     .orderBy("Ano", "cod_municipio")
)

(
    silver_df.write.format("delta")
        .mode("overwrite")
        .option("overwriteSchema", "true")
        .partitionBy("Ano")
        .saveAsTable(SILVER_TABLE)
)

spark.sql(f"COMMENT ON TABLE {SILVER_TABLE} IS "
          f"'Mirante · População estimada IBGE/SIDRA Tabela 6579 por município × ano. "
          f"~5.570 munis × 13+ anos (2013–corrente). Variante municipal de silver.populacao_uf_ano. "
          f"Source: SIDRA API REST (https://servicodados.ibge.gov.br/api/v3/agregados/6579). "
          f"Para anos sem publicação IBGE, gold faz interpolação com flag pop_estimada=true.'")

for col, comment in [
    ("Ano",            "Ano de referência da estimativa (1 jul)."),
    ("cod_municipio",  "Código IBGE 7 dígitos com dígito verificador."),
    ("municipio_nome", "Nome do município conforme IBGE/Tabela 6579."),
    ("populacao",      "Estimativa populacional residente (pessoas)."),
]:
    spark.sql(
        f"ALTER TABLE {SILVER_TABLE} ALTER COLUMN {col} COMMENT '{comment.replace(chr(39), chr(39)*2)}'"
    )

spark.sql(f"ALTER TABLE {SILVER_TABLE} SET TAGS ("
          f"'layer' = 'silver', 'domain' = 'demography', 'source' = 'ibge_sidra_6579', "
          f"'pii' = 'none', 'grain' = 'municipio_ano')")

print(f"✔ {SILVER_TABLE} written ({n:,} rows)")

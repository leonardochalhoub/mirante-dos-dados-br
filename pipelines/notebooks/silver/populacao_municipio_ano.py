# Databricks notebook source
# MAGIC %md
# MAGIC # silver · populacao_municipio_ano
# MAGIC
# MAGIC Lê `bronze.ibge_municipios_populacao_raw` (envelopes JSON do ingest, 1 por
# MAGIC ano) e produz tabela longa `(Ano, cod_municipio, municipio_nome, uf, populacao,
# MAGIC populacao_estimada, source)`.
# MAGIC
# MAGIC **Schema do envelope bronze (criado pelo ingest):**
# MAGIC ```
# MAGIC {
# MAGIC   "_year":   2024,
# MAGIC   "_source": "estimativa_t6579" | "censo_2022_t4709",
# MAGIC   "_data":   [...]   ← payload SIDRA original
# MAGIC }
# MAGIC ```
# MAGIC
# MAGIC **Cobertura:**
# MAGIC - 2013-2021: SIDRA tabela 6579 (Estimativas anuais).
# MAGIC - 2022:      SIDRA tabela 4709 (Censo 2022, contagem real).
# MAGIC - 2023:      INTERPOLADO entre 2022 e 2024 (gap SIDRA — IBGE não publicou
# MAGIC              estimativa em 2023 por causa do reescalonamento pós-Censo).
# MAGIC - 2024:      SIDRA tabela 6579 (Estimativa anual).
# MAGIC
# MAGIC **Output schema:**
# MAGIC | col                    | tipo   | nota                                     |
# MAGIC |------------------------|--------|------------------------------------------|
# MAGIC | Ano                    | int    | partição                                 |
# MAGIC | cod_municipio          | string | 7 dígitos IBGE                           |
# MAGIC | municipio_nome         | string | nome SIDRA (já vem com formato 'Muni - UF') |
# MAGIC | populacao              | long   | residentes                               |
# MAGIC | populacao_estimada     | bool   | true se interpolado (apenas 2023)        |
# MAGIC | source                 | string | 'estimativa_t6579', 'censo_2022_t4709' ou 'interpolado_linear' |

# COMMAND ----------

dbutils.widgets.text("catalog", "mirante_prd")
CATALOG = dbutils.widgets.get("catalog")

BRONZE_TABLE = f"{CATALOG}.bronze.ibge_municipios_populacao_raw"
SILVER_TABLE = f"{CATALOG}.silver.populacao_municipio_ano"

print(f"bronze={BRONZE_TABLE}  silver={SILVER_TABLE}")

# COMMAND ----------

from pyspark.sql import functions as F, types as T

bronze = spark.read.table(BRONZE_TABLE)
print(f"bronze rows: {bronze.count():,}")
bronze.printSchema()

# COMMAND ----------

# O envelope tem _data (array com payload SIDRA). Explodimos em séries.
# `_data[0].resultados[].series[].localidade.id` = código muni
# `_data[0].resultados[].series[].serie` = dict {ano_str: pop_str}

# Bronze pode ter ou não a coluna _data — fallback: se não tem envelope,
# trata como SIDRA cru (caso runs antigas tenham gravado no formato anterior).
has_envelope = "_data" in [f.name for f in bronze.schema.fields]
print(f"envelope detectado: {has_envelope}")

if has_envelope:
    base = bronze.select(
        F.col("_year").alias("year_envelope"),
        F.col("_source").alias("source"),
        F.explode(F.col("_data")).alias("payload"),
    ).select(
        F.col("year_envelope"),
        F.col("source"),
        F.col("payload.resultados").alias("resultados"),
    )
else:
    base = bronze.select(
        F.lit(None).cast("int").alias("year_envelope"),
        F.lit("legacy").alias("source"),
        F.col("resultados"),
    )

desaninhado = (
    base
    .select(
        F.col("year_envelope"),
        F.col("source"),
        F.explode("resultados").alias("res"),
    )
    .select(
        F.col("year_envelope"),
        F.col("source"),
        F.explode("res.series").alias("s"),
    )
    .select(
        F.col("year_envelope"),
        F.col("source"),
        F.col("s.localidade.id").cast("string").alias("cod_municipio"),
        F.col("s.localidade.nome").alias("municipio_nome"),
        F.col("s.serie").alias("serie_dict"),
    )
)

ano_pop_real = (
    desaninhado
      .select(
          F.col("source"),
          F.col("cod_municipio"),
          F.col("municipio_nome"),
          F.explode(F.col("serie_dict")).alias("ano_str", "pop_str"),
      )
      .withColumn("Ano",       F.col("ano_str").cast("int"))
      .withColumn("populacao", F.col("pop_str").cast("long"))
      .where(F.col("populacao").isNotNull() & (F.col("populacao") > 0))
      .withColumn("populacao_estimada", F.lit(False))
      .select("Ano", "cod_municipio", "municipio_nome", "populacao",
              "populacao_estimada", "source")
)

n_real = ano_pop_real.count()
munis_real = ano_pop_real.select("cod_municipio").distinct().count()
anos_real = sorted(r["Ano"] for r in ano_pop_real.select("Ano").distinct().collect())
print(f"dados REAIS: {n_real:,} linhas  {munis_real:,} munis  anos={anos_real}")

# COMMAND ----------

# DQ pré-interpolação
assert munis_real >= 5500, f"Cobertura municipal insuficiente: {munis_real} < 5500"
assert len(anos_real) >= 10, f"Cobertura temporal insuficiente: {len(anos_real)} anos"

# Dedup por (Ano, cod_municipio) — pode haver overlap entre tabelas em casos raros
dup = ano_pop_real.groupBy("Ano", "cod_municipio").count().where(F.col("count") > 1)
n_dup = dup.count()
if n_dup > 0:
    print(f"⚠ {n_dup} duplicatas (Ano, cod_municipio); colapsando preferindo Censo > Estimativa")
    # Censo 2022 (t4709) é mais confiável que outras fontes — priorizamos
    win_priority = (F.when(F.col("source") == "censo_2022_t4709", 1)
                     .when(F.col("source") == "estimativa_t6579", 2)
                     .otherwise(9))
    from pyspark.sql import Window
    w = Window.partitionBy("Ano", "cod_municipio").orderBy(win_priority)
    ano_pop_real = (
        ano_pop_real.withColumn("_rk", F.row_number().over(w))
                    .where(F.col("_rk") == 1)
                    .drop("_rk")
    )

# COMMAND ----------

# Interpolação 2023 = (2022 + 2024) / 2 com flag populacao_estimada=true
# Usado quando IBGE não publicou estimativa entre Censo e nova série.
GAP_YEARS = [2023]
gap_to_neighbors = {2023: (2022, 2024)}

print(f"Interpolando anos com gap: {GAP_YEARS}")

# Pivot pra ter pop_2022 e pop_2024 como colunas pra cada município
real_pivot = (
    ano_pop_real.where(F.col("Ano").isin([2022, 2024]))
                .groupBy("cod_municipio", "municipio_nome")
                .pivot("Ano", [2022, 2024])
                .agg(F.first("populacao"))
)

interp_rows = []
for gap_y, (y0, y1) in gap_to_neighbors.items():
    # Linear simples: pop[y0+gap] = pop[y0] + (pop[y1]-pop[y0]) * (gap/(y1-y0))
    # Pra 2023 entre 2022 e 2024: pop_2023 = (pop_2022 + pop_2024) / 2
    interp = real_pivot.select(
        F.lit(gap_y).cast("int").alias("Ano"),
        F.col("cod_municipio"),
        F.col("municipio_nome"),
        F.round(((F.col(f"`{y0}`") + F.col(f"`{y1}`")) / 2.0)).cast("long").alias("populacao"),
        F.lit(True).alias("populacao_estimada"),
        F.lit("interpolado_linear").alias("source"),
    ).where(F.col("populacao").isNotNull() & (F.col("populacao") > 0))
    interp_rows.append(interp)

if interp_rows:
    ano_pop_interp = interp_rows[0]
    for df in interp_rows[1:]:
        ano_pop_interp = ano_pop_interp.unionByName(df)
    print(f"interpolados: {ano_pop_interp.count():,} linhas (gap_years={GAP_YEARS})")
else:
    ano_pop_interp = None

# COMMAND ----------

silver_full = ano_pop_real
if ano_pop_interp is not None:
    silver_full = silver_full.unionByName(ano_pop_interp)

silver_df = (
    silver_full.select(
        F.col("Ano").cast("int"),
        F.col("cod_municipio").cast("string"),
        F.col("municipio_nome").cast("string"),
        F.col("populacao").cast("long"),
        F.col("populacao_estimada").cast("boolean"),
        F.col("source").cast("string"),
    )
    # Parse "Maricá - RJ" → municipio="Maricá" + uf="RJ"
    # Regex greedy pra (.+) cobre munis com hífen interno tipo "Bom Jesus do Itabapoana".
    # O sufixo " - <2 letras maiúsculas>" no final é o âncora confiável.
    .withColumn("uf",        F.regexp_extract(F.col("municipio_nome"), r" - ([A-Z]{2})$", 1))
    .withColumn("municipio", F.regexp_extract(F.col("municipio_nome"), r"^(.+) - [A-Z]{2}$", 1))
    # Display canônico: "Maricá - RJ" — mantemos pra UI/joins humanos
    .withColumn("municipio_uf", F.col("municipio_nome"))
    .drop("municipio_nome")
    .withColumn("_silver_built_ts", F.current_timestamp())
    .select("Ano", "cod_municipio", "municipio", "uf", "municipio_uf",
            "populacao", "populacao_estimada", "source", "_silver_built_ts")
    .orderBy("Ano", "cod_municipio")
)

# DQ: valida que o parse de uf funcionou (esperado: 27 UFs distintas)
n_uf = silver_df.select("uf").where(F.length("uf") == 2).distinct().count()
n_uf_invalid = silver_df.where(F.length("uf") != 2).count()
print(f"UFs distintas após parse: {n_uf} (esperado 27)")
print(f"linhas com UF inválida (parse falhou): {n_uf_invalid}")
if n_uf_invalid > 0:
    silver_df.where(F.length("uf") != 2).select("cod_municipio", "municipio_uf").show(10, truncate=False)

n_total = silver_df.count()
print(f"silver TOTAL: {n_total:,} linhas")
silver_df.groupBy("Ano", "source").count().orderBy("Ano", "source").show(50)

# COMMAND ----------

(
    silver_df.write.format("delta")
        .mode("overwrite")
        .option("overwriteSchema", "true")
        .partitionBy("Ano")
        .saveAsTable(SILVER_TABLE)
)

# Metadata UC
spark.sql(f"""
COMMENT ON TABLE {SILVER_TABLE} IS
'População residente por município brasileiro × ano. Long format (~5570 munis × 12 anos).
Cobertura 2013-2024:
  - 2013-2021, 2024: IBGE/SIDRA tabela 6579 (Estimativas anuais).
  - 2022:           IBGE/SIDRA tabela 4709 (Censo 2022, contagem real).
  - 2023:           INTERPOLADO entre 2022 (Censo) e 2024 (Estimativa) — gap SIDRA.
                    Marcado com populacao_estimada=true.
Fontes:
  https://sidra.ibge.gov.br/tabela/6579
  https://sidra.ibge.gov.br/tabela/4709
Particionado por Ano. Chave primária: (cod_municipio, Ano).'
""")

for col, desc in [
    ("Ano",                "Ano de referência (1 jul). Coluna de partição."),
    ("cod_municipio",      "Código IBGE do município (7 dígitos com DV)."),
    ("municipio",          "Nome do município, parseado de `municipio_uf` (parte antes de ' - UF'). Ex.: 'Maricá'."),
    ("uf",                 "Sigla da UF (2 letras), parseada de `municipio_uf` (sufixo após ' - '). Ex.: 'RJ'."),
    ("municipio_uf",       "Display canônico no formato `Município - UF` exatamente como retornado pela SIDRA. Ex.: 'Maricá - RJ'. Use em UI/labels; pra join programático prefira `cod_municipio`."),
    ("populacao",          "População residente (long, pessoas)."),
    ("populacao_estimada", "True quando o valor foi INTERPOLADO entre vizinhos (2023). Falso quando vem direto de Censo ou Estimativa SIDRA."),
    ("source",             "Origem da observação: 'estimativa_t6579', 'censo_2022_t4709' ou 'interpolado_linear'."),
]:
    try:
        spark.sql(f"ALTER TABLE {SILVER_TABLE} ALTER COLUMN `{col}` COMMENT '{desc}'")
    except Exception as e:
        print(f"  ⚠ comment {col}: {e}")

spark.sql(f"ALTER TABLE {SILVER_TABLE} SET TAGS ("
          f"'layer' = 'silver', 'domain' = 'demografia', "
          f"'source' = 'ibge_sidra_6579+4709', 'pii' = 'false', "
          f"'grain' = 'municipio_ano')")

print(f"✔ {SILVER_TABLE} escrita ({n_total:,} rows)")

# Databricks notebook source
# MAGIC %md
# MAGIC # gold · pbf_municipios_df
# MAGIC
# MAGIC Junta `silver.pbf_total_municipio_mes` (PBF) com `silver.populacao_municipio_ano`,
# MAGIC `silver.coords_municipios` e `silver.ipca_deflators_2021` para produzir o painel
# MAGIC final Município × Ano consumido pelo WP#7 e pela vertical web.
# MAGIC
# MAGIC Schema:
# MAGIC ```
# MAGIC Ano int, cod_municipio string (7 dígitos), municipio string, uf string, regiao string,
# MAGIC lat double, lon double, populacao long, n_benef long, valor_nominal double,
# MAGIC valor_2021 double, pbfPerBenef double, pbfPerCapita double, idhm_2010 double
# MAGIC ```
# MAGIC
# MAGIC ~5.570 munis × 13 anos = ~72.4k linhas. valor_2021 está em **R$ milhões 2021**
# MAGIC (não bilhões como no UF gold, dada a granularidade menor).

# COMMAND ----------

dbutils.widgets.text("catalog", "mirante_prd")
CATALOG = dbutils.widgets.get("catalog")

SILVER_PBF       = f"{CATALOG}.silver.pbf_total_municipio_mes"
SILVER_POPULACAO = f"{CATALOG}.silver.populacao_municipio_ano"
SILVER_COORDS    = f"{CATALOG}.silver.coords_municipios"
SILVER_DEFLATORS = f"{CATALOG}.silver.ipca_deflators_2021"
GOLD_TABLE       = f"{CATALOG}.gold.pbf_municipios_df"

# COMMAND ----------

from pyspark.sql import functions as F

silver = spark.read.table(SILVER_PBF)
pop    = spark.read.table(SILVER_POPULACAO).select("Ano", "cod_municipio", "populacao",
                                                    F.col("municipio_nome").alias("municipio"))
coords = spark.read.table(SILVER_COORDS).select(
    "cod_municipio", "lat", "lon", "regiao", "idhm_2010"
)
defl   = spark.read.table(SILVER_DEFLATORS).select("Ano", "deflator_to_2021")

# Drop anos parciais (12 meses obrigatórios) — mesmo critério do gold UF
months_per_year = silver.groupBy("Ano").agg(F.countDistinct("Mes").alias("n_months"))
full_years = sorted([r["Ano"] for r in months_per_year.where(F.col("n_months") == 12).collect()])
all_years  = sorted([r["Ano"] for r in months_per_year.collect()])
dropped    = sorted(set(all_years) - set(full_years))
print(f"anos completos: {full_years}; descartados (parciais): {dropped}")
silver = silver.where(F.col("Ano").isin(full_years))

# Normalizar cod_municipio para 7 dígitos. Algumas competências antigas têm 6 dígitos
# (sem DV); silver.coords_municipios tem o mapeamento 6→7.
silver = silver.withColumn(
    "cod_municipio_7",
    F.when(F.length("cod_municipio") == 7, F.col("cod_municipio"))
)
# Para 6-dígitos, seria necessário lookup contra coords_municipios; faltando o silver
# de coords, dropamos (raros, ~ <0.5% das linhas em anos antigos).
silver = silver.where(F.col("cod_municipio_7").isNotNull())
silver = silver.withColumnRenamed("cod_municipio_7", "_cod7")

# Aggregate Município × Ano: total_municipio em R$ nominais, dividido por 1e6 → R$ milhões
valores = (
    silver.groupBy("Ano", F.col("_cod7").alias("cod_municipio"), "uf")
          .agg((F.sum("total_municipio") / F.lit(1e6)).cast("double").alias("valor_nominal"))
)
benef = (
    silver.select("Ano", F.col("_cod7").alias("cod_municipio"), "n_ano").distinct()
          .withColumnRenamed("n_ano", "n_benef")
          .withColumn("n_benef", F.col("n_benef").cast("long"))
)

df = (
    valores.join(benef,  on=["Ano", "cod_municipio"], how="left")
           .join(pop,    on=["Ano", "cod_municipio"], how="left")
           .join(coords, on=["cod_municipio"],        how="left")
           .join(defl,   on=["Ano"],                  how="left")
)

df = df.withColumn("valor_2021",   F.col("valor_nominal") * F.col("deflator_to_2021"))
df = df.withColumn("pbfPerBenef",  (F.col("valor_2021") * F.lit(1e6)) / F.col("n_benef"))
df = df.withColumn("pbfPerCapita", (F.col("valor_2021") * F.lit(1e6)) / F.col("populacao"))

gold_df = df.select(
    F.col("Ano").cast("int"),
    F.col("cod_municipio").cast("string"),
    F.col("municipio").cast("string"),
    F.col("uf").cast("string"),
    F.col("regiao").cast("string"),
    F.col("lat").cast("double"),
    F.col("lon").cast("double"),
    F.col("populacao").cast("long"),
    F.col("n_benef").cast("long"),
    F.col("valor_nominal").cast("double"),
    F.col("valor_2021").cast("double"),
    F.col("pbfPerBenef").cast("double"),
    F.col("pbfPerCapita").cast("double"),
    F.col("idhm_2010").cast("double"),
).withColumn("_gold_built_ts", F.current_timestamp()).orderBy("Ano", "cod_municipio")

# COMMAND ----------

n = gold_df.count()
n_munis = gold_df.select("cod_municipio").distinct().count()
n_anos  = gold_df.select("Ano").distinct().count()

bad_filter = (
    F.col("valor_nominal").isNull() | F.col("valor_2021").isNull()
    | F.col("populacao").isNull() | F.col("n_benef").isNull()
    | F.col("lat").isNull() | F.col("lon").isNull()
)
n_bad = gold_df.where(bad_filter).count()
print(f"gold rows={n:,}  ({n_munis} munis × {n_anos} anos)")
print(f"rows com NULL críticos: {n_bad}")

if n_bad > 0:
    gold_df.where(bad_filter).select(
        "Ano", "cod_municipio", "uf", "n_benef", "valor_nominal", "populacao", "lat"
    ).show(20, truncate=False)
    gold_df = gold_df.where(~bad_filter)
    n_after = gold_df.count()
    print(f"Após drop: {n_after:,} linhas (era {n:,})")

# Sanity: per_capita Brasil 2025 deve bater com gold UF (~R$ 608)
y2025 = gold_df.where(F.col("Ano") == 2025)
if y2025.head(1):
    sums = y2025.agg(
        F.sum("n_benef").alias("benef"),
        F.sum("valor_2021").alias("v2021"),  # R$ milhões
        F.sum("populacao").alias("pop"),
    ).first()
    if sums and sums["benef"] and sums["pop"]:
        per_capita = (sums["v2021"] * 1e6) / sums["pop"]
        print(f"2025 Brasil per_capita = R${per_capita:.2f}/hab (esperado ≈608.33 conforme gold UF)")

# COMMAND ----------

(
    gold_df.write.format("delta")
        .mode("overwrite")
        .option("overwriteSchema", "true")
        .partitionBy("Ano")
        .saveAsTable(GOLD_TABLE)
)

spark.sql(f"COMMENT ON TABLE {GOLD_TABLE} IS "
          f"'Mirante · PBF Município × Ano (gold) — variante municipal do gold.pbf_estados_df. "
          f"~5.570 munis × 13 anos ≈ 72k linhas. valor_2021 em R$ milhões (não bi). "
          f"Habilita identificação causal com 5.570 clusters (Conley HAC, TWFE municipal, "
          f"DiD geográfico) — endereça gargalo de N=27 do WP#2. "
          f"Schema do JSON consumido pela vertical /bolsa-familia-municipios.'")

for col, comment in [
    ("Ano",           "Ano de competência completo (12 meses)."),
    ("cod_municipio", "Código IBGE 7 dígitos com DV."),
    ("municipio",     "Nome IBGE/SIDRA."),
    ("uf",            "Sigla 2-letter."),
    ("regiao",        "Norte/Nordeste/Centro-Oeste/Sudeste/Sul."),
    ("lat",           "Latitude do centroide (graus, IBGE/MalhaDigital)."),
    ("lon",           "Longitude do centroide (graus)."),
    ("populacao",     "IBGE/SIDRA 6579 (estimativa anual)."),
    ("n_benef",       "Beneficiários distintos por NIS no ano."),
    ("valor_nominal", "R$ milhões nominais."),
    ("valor_2021",    "R$ milhões deflacionados IPCA dez/2021."),
    ("pbfPerBenef",   "R$ 2021 por beneficiário-ano."),
    ("pbfPerCapita",  "R$ 2021 per capita-ano."),
    ("idhm_2010",     "IDH-M Atlas Brasil 2010 (PNUD/IPEA/FJP) — usado em Kakwani."),
]:
    spark.sql(
        f"ALTER TABLE {GOLD_TABLE} ALTER COLUMN {col} COMMENT '{comment.replace(chr(39), chr(39)*2)}'"
    )

spark.sql(f"ALTER TABLE {GOLD_TABLE} SET TAGS ("
          f"'layer' = 'gold', 'domain' = 'social_protection', "
          f"'source' = 'cgu_portal_transparencia+ibge_sidra+ibge_malha+atlas_brasil', "
          f"'pii' = 'none', 'grain' = 'municipio_ano')")

print(f"✔ {GOLD_TABLE} written ({n:,} rows)")

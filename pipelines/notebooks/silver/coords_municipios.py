# Databricks notebook source
# MAGIC %md
# MAGIC # silver · coords_municipios
# MAGIC
# MAGIC Tabela de referência espacial estática: 5.570 municípios brasileiros com
# MAGIC centroide (lat, lon), região, IDH-M Atlas Brasil 2010, e mapeamento entre
# MAGIC códigos IBGE 6 dígitos (sem DV) e 7 dígitos (com DV).
# MAGIC
# MAGIC Source: bronze.ibge_municipios_meta_raw (JSON do IBGE/MalhaDigital +
# MAGIC scraping Atlas Brasil 2010).
# MAGIC
# MAGIC Schema:
# MAGIC `cod_municipio string (7 dígitos), cod_municipio_6 string,
# MAGIC  municipio string, uf string, regiao string,
# MAGIC  lat double, lon double, area_km2 double, idhm_2010 double`
# MAGIC
# MAGIC Estática — recarregada apenas quando IBGE atualiza a malha digital
# MAGIC (raro; última grande revisão foi Censo 2022).

# COMMAND ----------

dbutils.widgets.text("catalog", "mirante_prd")
CATALOG = dbutils.widgets.get("catalog")

BRONZE_TABLE = f"{CATALOG}.bronze.ibge_municipios_meta_raw"
SILVER_TABLE = f"{CATALOG}.silver.coords_municipios"

# COMMAND ----------

from pyspark.sql import functions as F

bronze = spark.read.table(BRONZE_TABLE)
print(f"bronze rows: {bronze.count():,}")

# COMMAND ----------

# bronze.ibge_municipios_meta_raw é JSON-as-string com schema:
# { id: cod_7, nome: "São Paulo", microrregiao: {mesorregiao: {UF: {sigla, regiao}}},
#   centroide: {lat, lon}, area_km2, idhm_2010 }
silver_df = (
    bronze.select(
        F.col("id").cast("string").alias("cod_municipio"),
        F.expr("substring(id, 1, 6)").alias("cod_municipio_6"),
        F.col("nome").alias("municipio"),
        F.col("microrregiao.mesorregiao.UF.sigla").alias("uf"),
        F.col("microrregiao.mesorregiao.UF.regiao.nome").alias("regiao"),
        F.col("centroide.lat").cast("double").alias("lat"),
        F.col("centroide.lon").cast("double").alias("lon"),
        F.col("area_km2").cast("double").alias("area_km2"),
        F.col("idhm_2010").cast("double").alias("idhm_2010"),
    )
    .where(F.length("cod_municipio") == 7)
    .withColumn("_silver_built_ts", F.current_timestamp())
)

n = silver_df.count()
print(f"silver coords rows: {n:,} (esperado 5.570)")
assert n >= 5500, f"Cobertura insuficiente: {n} < 5500"

# COMMAND ----------

(
    silver_df.write.format("delta")
        .mode("overwrite")
        .option("overwriteSchema", "true")
        .saveAsTable(SILVER_TABLE)
)

spark.sql(f"COMMENT ON TABLE {SILVER_TABLE} IS "
          f"'Mirante · Referência espacial dos 5.570 municípios brasileiros (IBGE Censo 2022 + "
          f"Atlas Brasil PNUD/IPEA/FJP 2010). lat/lon = centroide do polígono IBGE/MalhaDigital. "
          f"idhm_2010 = último IDH-M municipal disponível (não há recorte 2022 publicado). "
          f"cod_municipio_6 = mapeamento p/ formato antigo CGU (sem dígito verificador). "
          f"Estática — atualizar apenas em revisões grandes da malha IBGE.'")

for col, comment in [
    ("cod_municipio",    "Código IBGE 7 dígitos com DV (formato vigente)."),
    ("cod_municipio_6",  "Código IBGE 6 dígitos (sem DV) — usado por CGU em arquivos pré-2018."),
    ("municipio",        "Nome IBGE."),
    ("uf",               "Sigla 2-letter."),
    ("regiao",           "Norte/Nordeste/Centro-Oeste/Sudeste/Sul."),
    ("lat",              "Latitude do centroide do polígono IBGE/MalhaDigital (graus)."),
    ("lon",              "Longitude do centroide (graus)."),
    ("area_km2",         "Área territorial IBGE 2022 (km²)."),
    ("idhm_2010",        "IDH-M Atlas Brasil 2010 (último censo com IDHM publicado)."),
]:
    spark.sql(
        f"ALTER TABLE {SILVER_TABLE} ALTER COLUMN {col} COMMENT '{comment.replace(chr(39), chr(39)*2)}'"
    )

spark.sql(f"ALTER TABLE {SILVER_TABLE} SET TAGS ("
          f"'layer' = 'silver', 'domain' = 'reference', "
          f"'source' = 'ibge_malha_digital+atlas_brasil', "
          f"'pii' = 'none', 'grain' = 'municipio')")

print(f"✔ {SILVER_TABLE} written ({n:,} rows)")

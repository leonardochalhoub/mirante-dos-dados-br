# Databricks notebook source
# MAGIC %md
# MAGIC # ingest · geobr_municipios
# MAGIC
# MAGIC Tabela canônica dos 5.570 municípios brasileiros via pacote `geobr`
# MAGIC (https://github.com/ipeaGIT/geobr) — mesmo dataset usado no R, mantido pelo IPEA.
# MAGIC
# MAGIC Substitui a abordagem antiga (`ibge_municipios_meta.py` complexo com 5570
# MAGIC chamadas API IBGE/Malha + shapely + Atlas CSV) por: 1 chamada `geobr.read_municipality`
# MAGIC que retorna GeoDataFrame com colunas:
# MAGIC
# MAGIC | col           | tipo   | nota                                  |
# MAGIC |---------------|--------|---------------------------------------|
# MAGIC | code_muni     | int    | IBGE 7 dígitos                        |
# MAGIC | name_muni     | string | nome oficial                          |
# MAGIC | code_state    | int    | IBGE UF                               |
# MAGIC | abbrev_state  | string | sigla UF (2 letras)                   |
# MAGIC | name_state    | string | nome UF                               |
# MAGIC | code_region   | int    | IBGE região                           |
# MAGIC | name_region   | string | Norte/Nordeste/Centro-Oeste/Sudeste/Sul |
# MAGIC | geometry      | wkt    | polígono/multipolígono simplificado   |
# MAGIC
# MAGIC Output:
# MAGIC - `bronze.geobr_municipios_meta` — metadata (sem geometry, ~5570 linhas)
# MAGIC - `bronze.geobr_municipios_geo`  — geometry como WKT string

# COMMAND ----------

# MAGIC %pip install --quiet geobr==0.2.2
# MAGIC dbutils.library.restartPython()

# COMMAND ----------

dbutils.widgets.text("catalog", "mirante_prd")
dbutils.widgets.text("year",    "2020")
CATALOG = dbutils.widgets.get("catalog")
YEAR = int(dbutils.widgets.get("year"))

BRONZE_META = f"{CATALOG}.bronze.geobr_municipios_meta"
BRONZE_GEO  = f"{CATALOG}.bronze.geobr_municipios_geo"

print(f"catalog={CATALOG}  year={YEAR}")

# COMMAND ----------

import warnings
warnings.filterwarnings("ignore")

import geobr
import time
from pyspark.sql import functions as F, types as T

t0 = time.monotonic()
gdf = geobr.read_municipality(code_muni="all", year=YEAR, simplified=True, verbose=False)
print(f"geobr.read_municipality: {len(gdf)} munis em {time.monotonic()-t0:.1f}s")

# Normalizar code_muni pra string 7 dígitos
gdf["code_muni"] = gdf["code_muni"].astype("Int64").astype(str).str.zfill(7)
gdf["code_state"] = gdf["code_state"].astype("Int64").astype(str)
gdf["code_region"] = gdf["code_region"].astype("Int64").astype(str)

# COMMAND ----------

# MAGIC %md ## Metadata table (sem geometry — leve, ~268 KB)

# COMMAND ----------

import pandas as pd
meta_pd = gdf[["code_muni", "name_muni", "code_state", "abbrev_state",
               "name_state", "code_region", "name_region"]].copy()

meta_schema = T.StructType([
    T.StructField("code_muni",     T.StringType(), False),
    T.StructField("name_muni",     T.StringType(), False),
    T.StructField("code_state",    T.StringType(), False),
    T.StructField("abbrev_state",  T.StringType(), False),
    T.StructField("name_state",    T.StringType(), False),
    T.StructField("code_region",   T.StringType(), False),
    T.StructField("name_region",   T.StringType(), False),
])
meta_df = (
    spark.createDataFrame(meta_pd, schema=meta_schema)
         .withColumn("_ingest_ts", F.current_timestamp())
         .withColumn("_geobr_year", F.lit(YEAR).cast("int"))
)
print(f"meta_df: {meta_df.count()} linhas")
meta_df.show(5, truncate=False)

(meta_df.write.format("delta").mode("overwrite")
    .option("overwriteSchema", "true")
    .saveAsTable(BRONZE_META))
print(f"✓ {BRONZE_META}")

# COMMAND ----------

# MAGIC %md ## Geometry table (WKT string — substitui shapely.geometry no Delta)

# COMMAND ----------

# Spark Delta não tem tipo geometry nativo. Convertemos pra WKT string:
# downstream silver/gold pode reidratar via shapely.from_wkt() quando necessário,
# ou usar databricks-spatial-sdk se disponível.
geo_pd = gdf[["code_muni", "name_muni", "abbrev_state"]].copy()
geo_pd["geometry_wkt"] = gdf.geometry.apply(lambda g: g.wkt)
geo_pd["geometry_bytes_kb"] = geo_pd["geometry_wkt"].str.len() // 1024

geo_schema = T.StructType([
    T.StructField("code_muni",         T.StringType(), False),
    T.StructField("name_muni",         T.StringType(), False),
    T.StructField("abbrev_state",      T.StringType(), False),
    T.StructField("geometry_wkt",      T.StringType(), False),
    T.StructField("geometry_bytes_kb", T.LongType(),   False),
])
geo_df = (
    spark.createDataFrame(geo_pd, schema=geo_schema)
         .withColumn("_ingest_ts", F.current_timestamp())
         .withColumn("_geobr_year", F.lit(YEAR).cast("int"))
)
print(f"geo_df: {geo_df.count()} linhas; tamanho médio WKT: "
      f"{geo_pd['geometry_bytes_kb'].mean():.1f} KB")

(geo_df.write.format("delta").mode("overwrite")
    .option("overwriteSchema", "true")
    .saveAsTable(BRONZE_GEO))
print(f"✓ {BRONZE_GEO}")

# COMMAND ----------

# MAGIC %md ## Metadata UC

# COMMAND ----------

spark.sql(f"""
COMMENT ON TABLE {BRONZE_META} IS
'IBGE Municipalities Metadata via geobr (Python port do pacote R IPEA).
5.570 municípios brasileiros com código IBGE 7-dígitos, nome oficial, UF
(sigla + nome + código), região (sigla + nome + código). Fonte canônica
para joins entre datasets municipais (CGU/PBF, SIDRA, Atlas, etc).
Source: geobr.read_municipality(code_muni="all", year={YEAR})
Repo: https://github.com/ipeaGIT/geobr'
""")

for col, desc in [
    ("code_muni",    "Código IBGE 7 dígitos com DV (chave primária pra join cross-dataset)."),
    ("name_muni",    "Nome oficial IBGE (sem normalização de acentos/case)."),
    ("code_state",   "Código IBGE da UF (2 dígitos)."),
    ("abbrev_state", "Sigla 2 letras (AC, AL, ..., TO)."),
    ("name_state",   "Nome oficial da UF."),
    ("code_region",  "Código IBGE da região (1 dígito)."),
    ("name_region",  "Norte/Nordeste/Centro-Oeste/Sudeste/Sul."),
]:
    try:
        spark.sql(f"ALTER TABLE {BRONZE_META} ALTER COLUMN `{col}` COMMENT '{desc}'")
    except Exception as e:
        print(f"  ⚠ comment {col}: {e}")

for tag, val in [
    ("layer", "bronze"), ("domain", "reference"),
    ("source", "geobr_python"), ("source_year", str(YEAR)),
    ("pii", "false"), ("grain", "municipio"),
]:
    try: spark.sql(f"ALTER TABLE {BRONZE_META} SET TAGS ('{tag}' = '{val}')")
    except Exception as e: print(f"  ⚠ tag {tag}: {e}")

spark.sql(f"""
COMMENT ON TABLE {BRONZE_GEO} IS
'IBGE Municipalities Geometries via geobr (5.570 munis, simplificada). geometry_wkt
é o polígono/multipolígono em WKT string (Spark não tem tipo geometry nativo;
silver pode reidratar via shapely.from_wkt). Usado pra choropleth maps no front e
análises espaciais no silver/gold.
Source: geobr.read_municipality(code_muni="all", year={YEAR}, simplified=True)'
""")

for tag, val in [
    ("layer", "bronze"), ("domain", "reference"),
    ("source", "geobr_python"), ("source_year", str(YEAR)),
    ("pii", "false"), ("grain", "municipio"), ("geometry", "wkt_string"),
]:
    try: spark.sql(f"ALTER TABLE {BRONZE_GEO} SET TAGS ('{tag}' = '{val}')")
    except Exception as e: print(f"  ⚠ tag {tag}: {e}")

print("✓ metadata UC aplicada")

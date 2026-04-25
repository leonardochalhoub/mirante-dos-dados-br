# Databricks notebook source
# MAGIC %md
# MAGIC # gold · rais_estados_ano
# MAGIC
# MAGIC Junta `silver.rais_uf_ano` com `silver.populacao_uf_ano` e
# MAGIC `silver.ipca_deflators_2021`. Saída em painel UF × Ano com:
# MAGIC - massa_salarial_dezembro_2021 (deflacionado)
# MAGIC - remun_media_2021
# MAGIC - vinculos_per_capita
# MAGIC - taxa_formalizacao_proxy = n_vinculos_ativos / populacao
# MAGIC - share_simples

# COMMAND ----------

dbutils.widgets.text("catalog", "mirante_prd")
CATALOG = dbutils.widgets.get("catalog")
SILVER = f"{CATALOG}.silver.rais_uf_ano"
POP    = f"{CATALOG}.silver.populacao_uf_ano"
DEFL   = f"{CATALOG}.silver.ipca_deflators_2021"
GOLD   = f"{CATALOG}.gold.rais_estados_ano"

# COMMAND ----------

from pyspark.sql import functions as F

silver = spark.read.table(SILVER)
pop    = spark.read.table(POP).select("Ano", "uf", "populacao")
defl   = spark.read.table(DEFL).select("Ano", "deflator_to_2021")

silver_n = silver.count()
print(f"silver={silver_n}  pop={pop.count()}  defl={defl.count()}")
if silver_n == 0:
    dbutils.notebook.exit("SKIPPED: silver is empty")

df = (
    silver
    .join(pop,  on=["Ano","uf"], how="left")
    .join(defl, on=["Ano"],      how="left")
    .withColumn("massa_salarial_dezembro_2021", F.col("massa_salarial_dezembro") * F.col("deflator_to_2021"))
    .withColumn("remun_media_2021",             F.col("remun_media_mes")         * F.col("deflator_to_2021"))
    .withColumn("vinculos_per_capita",
                F.when(F.col("populacao")>0, F.col("n_vinculos_ativos") / F.col("populacao")).otherwise(F.lit(None)))
    .withColumn("taxa_formalizacao_proxy",
                F.when(F.col("populacao")>0, F.col("n_vinculos_ativos") / F.col("populacao")).otherwise(F.lit(None)))
)

gold_df = df.select(
    "Ano", "uf",
    F.col("populacao").cast("long"),
    F.col("n_vinculos_ativos").cast("long"),
    F.col("n_vinculos_total").cast("long"),
    F.col("n_estabelecimentos_proxy").cast("long").alias("n_estabelecimentos_proxy"),
    F.col("massa_salarial_dezembro").cast("double").alias("massa_salarial_nominal"),
    F.col("massa_salarial_dezembro_2021").cast("double").alias("massa_salarial_2021"),
    F.col("remun_media_mes").cast("double").alias("remun_media_nominal"),
    F.col("remun_media_2021").cast("double"),
    F.col("vinculos_per_capita").cast("double"),
    F.col("taxa_formalizacao_proxy").cast("double"),
    F.col("share_simples").cast("double"),
).withColumn("_gold_built_ts", F.current_timestamp()).orderBy("Ano", "uf")

n = gold_df.count()
print(f"gold rows: {n}")

(gold_df.write.format("delta").mode("overwrite")
    .option("overwriteSchema","true")
    .partitionBy("Ano")
    .saveAsTable(GOLD))
print(f"✔ {GOLD} written ({n} rows)")

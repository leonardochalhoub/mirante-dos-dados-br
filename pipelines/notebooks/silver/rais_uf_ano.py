# Databricks notebook source
# MAGIC %md
# MAGIC # silver · rais_uf_ano
# MAGIC
# MAGIC Lê `<catalog>.bronze.rais_vinculos`, agrega por (UF, Ano):
# MAGIC - n_vinculos_ativos (vinculo_ativo_31_12 = 1)
# MAGIC - massa_salarial_dezembro (sum vl_remun_dezembro_nom, R$)
# MAGIC - remun_media_mes (média ponderada vl_remun_media_nom)
# MAGIC - n_vinculos_total (todos os registros)
# MAGIC - n_estabelecimentos (countDistinct mun_trab+cnae proxy)
# MAGIC - share_simples (% optantes do Simples Nacional)
# MAGIC
# MAGIC UF derivada do código IBGE do município (mun_trab) — primeiros 2 dígitos.

# COMMAND ----------

dbutils.widgets.text("catalog", "mirante_prd")
CATALOG = dbutils.widgets.get("catalog")
BRONZE_TABLE = f"{CATALOG}.bronze.rais_vinculos"
SILVER_TABLE = f"{CATALOG}.silver.rais_uf_ano"

# COMMAND ----------

from pyspark.sql import functions as F, types as T

bronze = spark.read.table(BRONZE_TABLE)
print(f"bronze rows: {bronze.count():,}")

# Mapping IBGE 2-digit code → UF sigla
UF_BY_CODE = {
    11:'RO',12:'AC',13:'AM',14:'RR',15:'PA',16:'AP',17:'TO',
    21:'MA',22:'PI',23:'CE',24:'RN',25:'PB',26:'PE',27:'AL',28:'SE',29:'BA',
    31:'MG',32:'ES',33:'RJ',35:'SP',
    41:'PR',42:'SC',43:'RS',
    50:'MS',51:'MT',52:'GO',53:'DF',
}
uf_map_expr = F.create_map(*[v for kv in UF_BY_CODE.items() for v in (F.lit(int(kv[0])), F.lit(kv[1]))])

# BR numeric: "1234,56" → double
def br_num(c):
    return F.regexp_replace(F.regexp_replace(c, r'\.', ''), ',', '.').cast('double')

df = (
    bronze
    .withColumn("ano_int", F.col("ano").cast("int"))
    .withColumn("uf_code", F.substring(F.col("mun_trab").cast("string"), 1, 2).cast("int"))
    .withColumn("uf", uf_map_expr.getItem(F.col("uf_code")))
    .withColumn("vinculo_ativo", F.col("vinculo_ativo_31_12").cast("int"))
    .withColumn("vl_dez", br_num(F.col("vl_remun_dezembro_nom")))
    .withColumn("vl_med", br_num(F.col("vl_remun_media_nom")))
    .withColumn("ind_simples_int", F.col("ind_simples").cast("int"))
    .where(F.col("uf").isNotNull() & F.col("ano_int").isNotNull())
)

silver_df = (
    df.groupBy("uf", "ano_int").agg(
        F.count("*").cast("long").alias("n_vinculos_total"),
        F.sum(F.when(F.col("vinculo_ativo")==1, 1).otherwise(0)).cast("long").alias("n_vinculos_ativos"),
        F.sum(F.coalesce(F.col("vl_dez"), F.lit(0.0))).alias("massa_salarial_dezembro"),
        F.avg(F.col("vl_med")).alias("remun_media_mes"),
        F.countDistinct(F.concat_ws("_", F.col("mun_trab"), F.col("cnae_2_0_classe"))).cast("long").alias("n_estabelecimentos_proxy"),
        F.avg(F.coalesce(F.col("ind_simples_int"), F.lit(0))).alias("share_simples"),
    )
    .withColumnRenamed("ano_int", "Ano")
    .withColumn("_silver_built_ts", F.current_timestamp())
    .orderBy("Ano", "uf")
)

n = silver_df.count()
print(f"silver rows: {n}  (esperado ~27 UFs × N anos)")

(silver_df.write.format("delta").mode("overwrite")
    .option("overwriteSchema","true")
    .partitionBy("Ano")
    .saveAsTable(SILVER_TABLE))
print(f"✔ {SILVER_TABLE} written")

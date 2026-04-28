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

# Defensivo: bronze pode não existir ainda se o ingest do PDET falhou
# (URLs do MTE mudam frequentemente, ou o ano não tem .7z publicado).
# Sai gracefully sem TABLE_OR_VIEW_NOT_FOUND cascade.
if not spark.catalog.tableExists(BRONZE_TABLE):
    print(f"⚠ {BRONZE_TABLE} não existe — provavelmente ingest_mte_rais não baixou nenhum .7z.")
    print("  Investigar:")
    print("  - URL pattern em ingest/mte_rais.py (URL_TEMPLATES)")
    print("  - Listar volume: dbutils.fs.ls('/Volumes/mirante_prd/bronze/raw/mte/rais')")
    dbutils.notebook.exit(f"SKIPPED: {BRONZE_TABLE} does not exist")

bronze = spark.read.table(BRONZE_TABLE)
n_bronze = bronze.count()
print(f"bronze rows: {n_bronze:,}")
print(f"bronze columns ({len(bronze.columns)}): {bronze.columns}")
if n_bronze == 0:
    print(f"⚠ {BRONZE_TABLE} existe mas está vazia.")
    dbutils.notebook.exit(f"SKIPPED: {BRONZE_TABLE} is empty")

# RAIS PDET muda nomes de colunas entre eras (1985-2018 per-UF vs 2019+ per-região,
# e dentro de cada era há variações). Resolvemos cada coluna lógica contra uma
# lista de aliases conhecidos (já em snake_case, pois bronze sanitiza o header).
def _resolve_col(df, *candidates):
    cols = {c.lower(): c for c in df.columns}
    for c in candidates:
        if c.lower() in cols:
            return cols[c.lower()]
    return None

LOGICAL_COLS = {
    # Município de TRABALHO (IBGE 6-7 dig). Em vários anos vem só como "Município".
    "mun_trab":      ("municipio_trabalho", "mun_trab", "municipio", "munic_trab", "cod_municipio"),
    "cnae_classe":   ("cnae_2_0_classe", "cnae_2_0", "cnae_95_classe", "cnae_classe", "cnae20_classe", "cnae"),
    "vinculo_ativo": ("vinculo_ativo_31_12", "vinc_ativo_31_12", "vinculo_ativo", "vinc_ativo"),
    "vl_dez":        ("vl_remun_dezembro_nom", "vl_remun_dezembro", "vl_remun_dezembro_sm", "vlr_remun_dezembro_nom"),
    "vl_med":        ("vl_remun_media_nom", "vl_remun_media", "vl_remun_media_sm", "vlr_remun_media_nom"),
    "ind_simples":   ("ind_simples", "simples", "ind_simples_nacional"),
}
resolved = {logical: _resolve_col(bronze, *aliases) for logical, aliases in LOGICAL_COLS.items()}
print(f"colunas RAIS resolvidas: {resolved}")

missing = [k for k, v in resolved.items() if v is None]
# `mun_trab` é obrigatório (UF deriva dele). Sem ele, abortamos.
if resolved["mun_trab"] is None:
    raise RuntimeError(
        f"Coluna de município de trabalho ausente na bronze. Tentei: "
        f"{LOGICAL_COLS['mun_trab']}. Schema atual: {bronze.columns}"
    )
if missing:
    print(f"⚠ Colunas opcionais ausentes (vão virar null/0 nas agregações): {missing}")

C_MUN     = resolved["mun_trab"]
C_CNAE    = resolved["cnae_classe"]
C_VINC    = resolved["vinculo_ativo"]
C_VL_DEZ  = resolved["vl_dez"]
C_VL_MED  = resolved["vl_med"]
C_SIMPLES = resolved["ind_simples"]

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
    .withColumn("ano_int",         F.col("ano").cast("int"))
    .withColumn("uf_code",         F.substring(F.col(C_MUN).cast("string"), 1, 2).cast("int"))
    .withColumn("uf",              uf_map_expr.getItem(F.col("uf_code")))
    .withColumn("vinculo_ativo",   F.col(C_VINC).cast("int")    if C_VINC    else F.lit(None).cast("int"))
    .withColumn("vl_dez",          br_num(F.col(C_VL_DEZ))      if C_VL_DEZ  else F.lit(None).cast("double"))
    .withColumn("vl_med",          br_num(F.col(C_VL_MED))      if C_VL_MED  else F.lit(None).cast("double"))
    .withColumn("ind_simples_int", F.col(C_SIMPLES).cast("int") if C_SIMPLES else F.lit(None).cast("int"))
    .where(F.col("uf").isNotNull() & F.col("ano_int").isNotNull())
)

# n_estabelecimentos_proxy só é confiável se temos ambos mun_trab + cnae_classe;
# senão cai pra countDistinct(mun_trab) — ainda é um proxy, só mais grosseiro.
estab_expr = (
    F.countDistinct(F.concat_ws("_", F.col(C_MUN), F.col(C_CNAE))) if C_CNAE
    else F.countDistinct(F.col(C_MUN))
)

silver_df = (
    df.groupBy("uf", "ano_int").agg(
        F.count("*").cast("long").alias("n_vinculos_total"),
        F.sum(F.when(F.col("vinculo_ativo")==1, 1).otherwise(0)).cast("long").alias("n_vinculos_ativos"),
        F.sum(F.coalesce(F.col("vl_dez"), F.lit(0.0))).alias("massa_salarial_dezembro"),
        F.avg(F.col("vl_med")).alias("remun_media_mes"),
        estab_expr.cast("long").alias("n_estabelecimentos_proxy"),
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

# Inline minimal COMMENT — full enrichment via _meta/apply_catalog_metadata.py.
spark.sql(f"COMMENT ON TABLE {SILVER_TABLE} IS "
          f"'Mirante · RAIS agregada UF × Ano — n_vinculos_total, n_vinculos_ativos "
          f"(em 31/12), massa_salarial_dezembro (R$ nominais), remun_media_mes, "
          f"n_estabelecimentos_proxy (countDistinct mun_trab+cnae_classe), share_simples. "
          f"Fonte: MTE/PDET RAIS. UF derivada de substring(mun_trab, 1, 2). "
          f"Reaplicar metadata rico via job_apply_catalog_metadata.'")

print(f"✔ {SILVER_TABLE} written")

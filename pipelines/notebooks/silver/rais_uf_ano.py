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

# RAIS PDET muda nomes de colunas entre 3 eras:
#   1985-2017: arquivos UF (.txt sep=';'), headers tipo "Município", "CBO Ocupação"
#   2018-2022: arquivos regionais (.txt sep=';'), headers idem
#   2023+:     arquivos regionais (.COMT sep=','), headers RENOMEADOS com sufixo
#              " - Código" (ex.: "Município Trab - Código", "CNAE 2.0 Classe - Código")
#
# Bronze tem mergeSchema=true, então UMA bronze.rais_vinculos pode ter `municipio`
# (.txt 1985-2022) E `municipio_trab_codigo` (.COMT 2023+) coexistindo — uma
# populada, outra NULL, por linha conforme o arquivo de origem.
#
# Solução: pra cada coluna lógica, COALESCE de TODAS as candidatas que existem
# no schema atual da bronze, na ordem de preferência. Assim 1 linha só
# contribui o seu valor não-null e ignora as colunas alheias do outro era.
def _coalesce_logical(df, candidates):
    """Retorna uma Column COALESCE das candidatas que existem no df (ordem importa).
    Retorna F.lit(None) se nenhuma existir."""
    cols_lower = {c.lower(): c for c in df.columns}
    matching = []
    for cand in candidates:
        if cand.lower() in cols_lower:
            matching.append(F.col(cols_lower[cand.lower()]))
    if not matching:
        return F.lit(None)
    if len(matching) == 1:
        return matching[0]
    return F.coalesce(*matching)

def _list_existing(df, candidates):
    cols_lower = {c.lower(): c for c in df.columns}
    return [cols_lower[c.lower()] for c in candidates if c.lower() in cols_lower]

LOGICAL_COLS = {
    # Município de TRABALHO (IBGE 6-7 dig).
    # 2023+ COMT: 'Município Trab - Código' → municipio_trab_codigo
    # 2018-2022 txt: 'Município Trab' → municipio_trab
    # 1985-2017 txt: 'Município' → municipio (sem trab — fallback)
    "mun_trab":      ("municipio_trab_codigo", "municipio_trabalho", "municipio_trab",
                      "munic_trab", "mun_trab", "cod_municipio",
                      "municipio_codigo", "municipio"),
    "cnae_classe":   ("cnae_2_0_classe_codigo", "cnae_2_0_classe", "cnae_2_0",
                      "cnae_95_classe_codigo", "cnae_95_classe",
                      "cnae_classe", "cnae20_classe", "cnae"),
    "vinculo_ativo": ("ind_vinculo_ativo_31_12_codigo", "vinculo_ativo_31_12",
                      "vinc_ativo_31_12", "vinculo_ativo", "vinc_ativo", "estoque"),
    "vl_dez":        ("vl_rem_dezembro_nom", "vl_remun_dezembro_nom", "vl_remun_dezembro",
                      "vl_rem_dezembro_sm", "vl_remun_dezembro_sm", "vlr_remun_dezembro_nom"),
    "vl_med":        ("vl_rem_media_nom", "vl_remun_media_nom", "vl_remun_media",
                      "vl_rem_media_sm", "vl_remun_media_sm", "vlr_remun_media_nom"),
    "ind_simples":   ("ind_estabelecimento_participante_simples_codigo",
                      "ind_simples", "simples", "ind_simples_nacional"),
}

resolved_lists = {logical: _list_existing(bronze, aliases) for logical, aliases in LOGICAL_COLS.items()}
print("colunas RAIS resolvidas (ordem de COALESCE):")
for logical, cols in resolved_lists.items():
    print(f"  {logical:14s} ← {cols if cols else '(NENHUMA — vira NULL)'}")

# `mun_trab` é obrigatório (UF deriva dele). Sem ele, abortamos.
if not resolved_lists["mun_trab"]:
    raise RuntimeError(
        f"Coluna de município de trabalho ausente na bronze. Tentei: "
        f"{LOGICAL_COLS['mun_trab']}. Schema atual: {bronze.columns}"
    )

missing = [k for k, v in resolved_lists.items() if not v]
if missing:
    print(f"⚠ Colunas opcionais ausentes (vão virar null/0 nas agregações): {missing}")

# COALESCE expressions cross-era — 1 linha contribui só seu valor não-null
EXPR_MUN     = _coalesce_logical(bronze, LOGICAL_COLS["mun_trab"])
EXPR_CNAE    = _coalesce_logical(bronze, LOGICAL_COLS["cnae_classe"])
EXPR_VINC    = _coalesce_logical(bronze, LOGICAL_COLS["vinculo_ativo"])
EXPR_VL_DEZ  = _coalesce_logical(bronze, LOGICAL_COLS["vl_dez"])
EXPR_VL_MED  = _coalesce_logical(bronze, LOGICAL_COLS["vl_med"])
EXPR_SIMPLES = _coalesce_logical(bronze, LOGICAL_COLS["ind_simples"])
HAS_CNAE     = bool(resolved_lists["cnae_classe"])

# Mapping IBGE 2-digit code → UF sigla
UF_BY_CODE = {
    11:'RO',12:'AC',13:'AM',14:'RR',15:'PA',16:'AP',17:'TO',
    21:'MA',22:'PI',23:'CE',24:'RN',25:'PB',26:'PE',27:'AL',28:'SE',29:'BA',
    31:'MG',32:'ES',33:'RJ',35:'SP',
    41:'PR',42:'SC',43:'RS',
    50:'MS',51:'MT',52:'GO',53:'DF',
}
uf_map_expr = F.create_map(*[v for kv in UF_BY_CODE.items() for v in (F.lit(int(kv[0])), F.lit(kv[1]))])

# BR numeric: "1234,56" → double. try_cast tolera lixo (latin-1 leftover, etc.).
def br_num(col_expr):
    cleaned = F.regexp_replace(F.regexp_replace(col_expr, r'\.', ''), ',', '.')
    return F.try_cast(cleaned, T.DoubleType())

# IMPORTANTE: TODAS as conversões de string → numeric usam `try_cast` em vez de
# `cast`. Bronze é STRING-ONLY com encoding latin-1 e arquivos PDET pré-2002 têm
# resíduos não-numéricos como "{ñ", "  ", "00.0,5" em campos que deveriam ser
# inteiros. Spark 4 (DBR 18+) é mais estrito que DBR 16- e cast hard-fails com
# CAST_INVALID_INPUT em vez de retornar NULL silenciosamente. try_cast retorna
# NULL em vez de explodir — que é o comportamento esperado pra agregação.
df = (
    bronze
    .withColumn("ano_int",         F.try_cast(F.col("ano"), T.IntegerType()))
    .withColumn("uf_code",         F.try_cast(F.substring(EXPR_MUN.cast("string"), 1, 2), T.IntegerType()))
    .withColumn("uf",              uf_map_expr.getItem(F.col("uf_code")))
    .withColumn("vinculo_ativo",   F.try_cast(EXPR_VINC,    T.IntegerType()))
    .withColumn("vl_dez",          br_num(EXPR_VL_DEZ))
    .withColumn("vl_med",          br_num(EXPR_VL_MED))
    .withColumn("ind_simples_int", F.try_cast(EXPR_SIMPLES, T.IntegerType()))
    .where(F.col("uf").isNotNull() & F.col("ano_int").isNotNull())
)

# n_estabelecimentos_proxy só é confiável se temos ambos mun_trab + cnae_classe;
# senão cai pra countDistinct(mun_trab) — ainda é um proxy, só mais grosseiro.
estab_expr = (
    F.countDistinct(F.concat_ws("_", EXPR_MUN, EXPR_CNAE)) if HAS_CNAE
    else F.countDistinct(EXPR_MUN)
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

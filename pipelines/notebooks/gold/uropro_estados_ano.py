# Databricks notebook source
# MAGIC %md
# MAGIC # gold · uropro_estados_ano
# MAGIC
# MAGIC Lê `<catalog>.silver.sih_uropro_uf_ano` e produz a granularidade que o
# MAGIC front consome: `(uf, ano, proc_rea)` com:
# MAGIC
# MAGIC - métricas anuais (sum n_aih, val_tot, val_sh, val_sp, dias_perm_avg, mortalidade)
# MAGIC - breakdown por **caráter** (eletivo / urgência) — formato wide
# MAGIC - breakdown por **gestão** (estadual / municipal / dupla) — formato wide
# MAGIC - **valores deflacionados** para R$ Dez/2021 via `silver.ipca_deflators_2021`
# MAGIC - **per capita** via `silver.populacao_uf_ano`
# MAGIC
# MAGIC Quando o front faz multi-seleção de procedimento, re-agrega client-side.

# COMMAND ----------

dbutils.widgets.text("catalog", "mirante_prd")
CATALOG = dbutils.widgets.get("catalog")

SILVER_TABLE     = f"{CATALOG}.silver.sih_uropro_uf_ano"
SILVER_POPULACAO = f"{CATALOG}.silver.populacao_uf_ano"
SILVER_IPCA      = f"{CATALOG}.silver.ipca_deflators_2021"
GOLD_TABLE       = f"{CATALOG}.gold.uropro_estados_ano"

print(f"silver={SILVER_TABLE}  gold={GOLD_TABLE}")

# COMMAND ----------

from pyspark.sql import functions as F

silver = spark.read.table(SILVER_TABLE)
print(f"silver rows: {silver.count():,}")

# Total annual base — somando todos os meses, todos caráteres, todas gestões.
# Importante: NÃO preenchemos UFs ausentes com zero. Se uma UF×ano×proc não
# tem linha aqui, é porque silver/bronze não viu aquela combinação — usuário
# quer ver isso explicitamente (como "sem dado") em vez de mascarar com zeros
# falsos. Diagnóstico de cobertura ao final do notebook ajuda a investigar.
base = (
    silver.groupBy("uf", "ano", "proc_rea", "proc_label")
          .agg(
              F.sum("n_aih").alias("n_aih"),
              F.sum("val_tot").alias("val_tot"),
              F.sum("val_sh").alias("val_sh"),
              F.sum("val_sp").alias("val_sp"),
              F.sum("sum_dias_perm").alias("sum_dias_perm"),
              F.sum("n_morte").alias("n_morte"),
          )
)

# Diagnóstico: quais UFs faltam (vs as 27 esperadas) por (ano, proc)?
all_ufs_set = {r["uf"] for r in spark.read.table(SILVER_POPULACAO).select("uf").distinct().collect()}
silver_ufs_per_year_proc = (
    base.groupBy("ano", "proc_rea")
        .agg(F.collect_set("uf").alias("ufs_present"))
        .collect()
)
print("\n=== Cobertura por (ano, proc): UFs ausentes ===")
for r in sorted(silver_ufs_per_year_proc, key=lambda r: (r["ano"], r["proc_rea"])):
    present = set(r["ufs_present"])
    missing = sorted(all_ufs_set - present)
    if missing:
        print(f"  ano={r['ano']} proc={r['proc_rea']} faltando ({len(missing)}): {missing}")

# Caráter wide
car_pivot = (
    silver
    .groupBy("uf", "ano", "proc_rea")
    .pivot("car_int", ["01", "02"])
    .agg(F.sum("n_aih").alias("aih"), F.sum("val_tot").alias("val"))
    .withColumnRenamed("01_aih", "aih_eletivo")
    .withColumnRenamed("01_val", "val_eletivo")
    .withColumnRenamed("02_aih", "aih_urgencia")
    .withColumnRenamed("02_val", "val_urgencia")
)

# Gestão wide
gestao_pivot = (
    silver
    .groupBy("uf", "ano", "proc_rea")
    .pivot("gestao", ["E", "M", "D"])
    .agg(F.sum("n_aih").alias("aih"), F.sum("val_tot").alias("val"))
    .withColumnRenamed("E_aih", "aih_gestao_estadual")
    .withColumnRenamed("E_val", "val_gestao_estadual")
    .withColumnRenamed("M_aih", "aih_gestao_municipal")
    .withColumnRenamed("M_val", "val_gestao_municipal")
    .withColumnRenamed("D_aih", "aih_gestao_dupla")
    .withColumnRenamed("D_val", "val_gestao_dupla")
)

# COMMAND ----------

# Populacao + IPCA deflator
df_pop = (
    spark.read.table(SILVER_POPULACAO)
         .select(
             F.col("uf").cast("string").alias("uf"),
             F.col("Ano").cast("int").alias("ano"),
             F.col("populacao").cast("long").alias("populacao"),
         )
)
df_ipca = (
    spark.read.table(SILVER_IPCA)
         .select(F.col("Ano").cast("int").alias("ano"),
                 F.col("deflator_to_2021").cast("double").alias("deflator"))
)

# COMMAND ----------

g = (
    base
    .join(car_pivot,    on=["uf", "ano", "proc_rea"], how="left")
    .join(gestao_pivot, on=["uf", "ano", "proc_rea"], how="left")
    .join(df_pop,       on=["uf", "ano"], how="left")
    .join(df_ipca,      on=["ano"], how="left")
)

# Fill NaN nos pivots para 0 — ausência = não houve AIH naquela combinação
fill_zeros = {
    c: 0 for c in [
        "aih_eletivo", "aih_urgencia",
        "aih_gestao_estadual", "aih_gestao_municipal", "aih_gestao_dupla",
        "n_morte",
    ]
}
fill_zeros_d = {
    c: 0.0 for c in [
        "val_eletivo", "val_urgencia",
        "val_gestao_estadual", "val_gestao_municipal", "val_gestao_dupla",
    ]
}
g = g.fillna({**fill_zeros, **fill_zeros_d})

# Per-AIH averages
g = (
    g
    .withColumn("val_tot_avg",   F.when(F.col("n_aih") > 0, F.col("val_tot") / F.col("n_aih")).otherwise(F.lit(0.0)))
    .withColumn("val_sh_avg",    F.when(F.col("n_aih") > 0, F.col("val_sh")  / F.col("n_aih")).otherwise(F.lit(0.0)))
    .withColumn("val_sp_avg",    F.when(F.col("n_aih") > 0, F.col("val_sp")  / F.col("n_aih")).otherwise(F.lit(0.0)))
    .withColumn("dias_perm_avg", F.when(F.col("n_aih") > 0, F.col("sum_dias_perm").cast("double") / F.col("n_aih")).otherwise(F.lit(0.0)))
    .withColumn("mortalidade",   F.when(F.col("n_aih") > 0, F.col("n_morte").cast("double") / F.col("n_aih")).otherwise(F.lit(0.0)))
)

# Deflated values to R$ 2021
defl = F.coalesce(F.col("deflator"), F.lit(1.0))
g = (
    g
    .withColumn("val_tot_2021",     F.col("val_tot")     * defl)
    .withColumn("val_sh_2021",      F.col("val_sh")      * defl)
    .withColumn("val_sp_2021",      F.col("val_sp")      * defl)
    .withColumn("val_tot_avg_2021", F.col("val_tot_avg") * defl)
)

# Per capita (R$ 2021 por 100 mil habitantes — escala apropriada pra
# procedimento raro como cirurgia de IU; valor absoluto seria infinitesimal
# na escala R$/hab.)
PER_CAPITA_BASE = 100_000  # = "por 100 mil habitantes"
pop = F.col("populacao")
g = (
    g
    .withColumn(
        "val_tot_2021_por100k",
        F.when(pop > 0, F.col("val_tot_2021") * F.lit(PER_CAPITA_BASE) / pop).otherwise(F.lit(0.0)),
    )
    .withColumn(
        "n_aih_por100k",
        F.when(pop > 0, F.col("n_aih").cast("double") * F.lit(PER_CAPITA_BASE) / pop).otherwise(F.lit(0.0)),
    )
    .withColumn("per_capita_base", F.lit(PER_CAPITA_BASE).cast("int"))
)

# COMMAND ----------

gold_df = (
    g
    .select(
        "uf", "ano", "proc_rea", "proc_label",
        "populacao",
        # Counts
        "n_aih", "n_morte",
        "aih_eletivo", "aih_urgencia",
        "aih_gestao_estadual", "aih_gestao_municipal", "aih_gestao_dupla",
        # Nominal
        "val_tot", "val_sh", "val_sp",
        "val_eletivo", "val_urgencia",
        "val_gestao_estadual", "val_gestao_municipal", "val_gestao_dupla",
        # Deflated to 2021
        "val_tot_2021", "val_sh_2021", "val_sp_2021",
        # Averages
        "val_tot_avg", "val_sh_avg", "val_sp_avg",
        "val_tot_avg_2021",
        "dias_perm_avg", "mortalidade",
        # Per capita
        "val_tot_2021_por100k", "n_aih_por100k", "per_capita_base",
        # Deflator (transparency — front pode mostrar)
        "deflator",
    )
    .withColumn("_gold_built_ts", F.current_timestamp())
    .orderBy("uf", "ano", "proc_rea")
)

n = gold_df.count()
ufs = gold_df.select("uf").distinct().count()
years = gold_df.select("ano").distinct().count()
procs = gold_df.select("proc_rea").distinct().count()
print(f"gold rows={n}  ufs={ufs}  years={years}  procs={procs}")

# Spot-check
print("\nÚltimo ano · top 5 UFs por n_aih (todos procedimentos somados):")
last_year = gold_df.agg(F.max("ano")).first()[0]
(
    gold_df.where(F.col("ano") == last_year)
           .groupBy("uf").agg(F.sum("n_aih").alias("n_aih"),
                              F.sum("val_tot_2021").alias("val_tot_2021"))
           .orderBy(F.desc("n_aih")).show(5, truncate=False)
)

(
    gold_df.write.format("delta")
        .mode("overwrite")
        .option("overwriteSchema", "true")
        .partitionBy("ano")
        .saveAsTable(GOLD_TABLE)
)
spark.sql(
    f"COMMENT ON TABLE {GOLD_TABLE} IS "
    f"'Mirante · SIH-AIH UroPro por UF × Ano × Procedimento (gold). "
    f"Tratamento cirúrgico de incontinência urinária. Deflacionado IPCA Dez/2021.'"
)
print(f"\n✔ {GOLD_TABLE} written ({n} rows)")

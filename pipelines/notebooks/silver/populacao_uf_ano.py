# Databricks notebook source
# MAGIC %md
# MAGIC # silver · populacao_uf_ano
# MAGIC
# MAGIC Lê snapshot **mais recente** de `<catalog>.bronze.ibge_populacao_raw` (filtrando pelo
# MAGIC último `_ingest_ts`), explode `resultados[].series[]`, mapeia UF id → sigla, e
# MAGIC constrói panel completo `Ano × UF` com **interpolação linear** pra anos que IBGE
# MAGIC não publicou.
# MAGIC
# MAGIC Mode: **OVERWRITE** (Delta time travel preserva snapshots anteriores).
# MAGIC
# MAGIC | param | default |
# MAGIC | --- | --- |
# MAGIC | `catalog`  | `mirante_prd` |
# MAGIC | `year_min` | 2013 |
# MAGIC | `year_max` | 2026 |

# COMMAND ----------

dbutils.widgets.text("catalog",  "mirante_prd")
dbutils.widgets.text("year_min", "2013")
dbutils.widgets.text("year_max", "2026")

CATALOG  = dbutils.widgets.get("catalog")
YEAR_MIN = int(dbutils.widgets.get("year_min"))
YEAR_MAX = int(dbutils.widgets.get("year_max"))

BRONZE_TABLE = f"{CATALOG}.bronze.ibge_populacao_raw"
SILVER_TABLE = f"{CATALOG}.silver.populacao_uf_ano"

print(f"bronze={BRONZE_TABLE}  silver={SILVER_TABLE}  range=[{YEAR_MIN}..{YEAR_MAX}]")

# COMMAND ----------

from pyspark.sql import functions as F, types as T, Window

UF_ID_TO_SIGLA = {
    "11": "RO", "12": "AC", "13": "AM", "14": "RR", "15": "PA", "16": "AP", "17": "TO",
    "21": "MA", "22": "PI", "23": "CE", "24": "RN", "25": "PB", "26": "PE", "27": "AL", "28": "SE", "29": "BA",
    "31": "MG", "32": "ES", "33": "RJ", "35": "SP",
    "41": "PR", "42": "SC", "43": "RS",
    "50": "MS", "51": "MT", "52": "GO", "53": "DF",
}

# COMMAND ----------

# MAGIC %md
# MAGIC ## Read latest bronze snapshot

# COMMAND ----------

bronze = spark.read.table(BRONZE_TABLE)
if bronze.head(1) == []:
    raise ValueError(f"{BRONZE_TABLE} is empty — run the bronze task first.")

# Pick ONLY the latest single source_file. Filtering by max(_ingest_ts) alone
# is NOT enough: if multiple files were ingested in the same Auto Loader
# micro-batch, they share the same _ingest_ts and the snapshot would have
# duplicates (3 rows per UF if you ran ingest 3× for example).
latest_file = (
    bronze
    .orderBy(F.desc("_ingest_ts"), F.desc("_source_file"))
    .select("_source_file")
    .first()[0]
)
src = bronze.where(F.col("_source_file") == latest_file)
latest_ts = src.agg(F.max("_ingest_ts")).first()[0]
print(f"Reading bronze snapshot from {latest_file} (_ingest_ts={latest_ts}, {src.count()} rows)")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Explode resultados[].series[] → (uf, Ano, populacao_raw)

# COMMAND ----------

df = (
    src.select(F.explode("resultados").alias("r"))
       .select(F.explode(F.col("r.series")).alias("s"))
       .select(
           F.col("s.localidade.id").alias("uf_id"),
           F.col("s.serie").alias("serie_struct"),
       )
)

# IBGE 'serie' is JSON object with year-string keys → Spark infers as STRUCT.
# Round-trip through JSON to convert to MapType so we can explode dynamic keys.
SERIE_MAP = T.MapType(T.StringType(), T.StringType())
df = (
    df.withColumn("serie_json", F.to_json("serie_struct"))
      .withColumn("serie_map",  F.from_json("serie_json", SERIE_MAP))
      .select("uf_id", F.explode("serie_map").alias("ano_str", "valor_str"))
      .where(F.col("valor_str").isNotNull() & (F.col("valor_str") != "..."))
)

sigla_expr = F.create_map(*[v for pair in UF_ID_TO_SIGLA.items() for v in (F.lit(pair[0]), F.lit(pair[1]))])
df = (
    df.withColumn("uf",  sigla_expr.getItem(F.col("uf_id")))
      .withColumn("Ano", F.col("ano_str").cast("int"))
      .withColumn("populacao_raw", F.col("valor_str").cast("double"))
      .where(F.col("uf").isNotNull())
      .select("Ano", "uf", "populacao_raw")
)

# COMMAND ----------

# MAGIC %md
# MAGIC ## Build full UF × Ano grid + linear interpolation for missing years

# COMMAND ----------

all_years = spark.range(YEAR_MIN, YEAR_MAX + 1).select(F.col("id").cast("int").alias("Ano"))
all_ufs   = df.select("uf").distinct()
panel     = all_ufs.crossJoin(all_years).join(df, on=["uf", "Ano"], how="left")

w_left  = (Window.partitionBy("uf").orderBy(F.col("Ano").asc())
              .rowsBetween(Window.unboundedPreceding, Window.currentRow))
w_right = (Window.partitionBy("uf").orderBy(F.col("Ano").asc())
              .rowsBetween(Window.currentRow, Window.unboundedFollowing))

panel = (
    panel
    .withColumn("ano_left",  F.last(F.when(F.col("populacao_raw").isNotNull(), F.col("Ano")), ignorenulls=True).over(w_left))
    .withColumn("pop_left",  F.last("populacao_raw", ignorenulls=True).over(w_left))
    .withColumn("ano_right", F.first(F.when(F.col("populacao_raw").isNotNull(), F.col("Ano")), ignorenulls=True).over(w_right))
    .withColumn("pop_right", F.first("populacao_raw", ignorenulls=True).over(w_right))
)

panel = panel.withColumn(
    "populacao_filled",
    F.when(F.col("populacao_raw").isNotNull(), F.col("populacao_raw"))
     .when(
         F.col("ano_left").isNotNull() & F.col("ano_right").isNotNull() & (F.col("ano_right") != F.col("ano_left")),
         F.col("pop_left") + (F.col("Ano") - F.col("ano_left")) *
                             (F.col("pop_right") - F.col("pop_left")) /
                             (F.col("ano_right") - F.col("ano_left")),
     )
     .when(F.col("pop_left").isNotNull(),  F.col("pop_left"))
     .when(F.col("pop_right").isNotNull(), F.col("pop_right"))
     .otherwise(F.lit(None).cast("double"))
)

panel = panel.withColumn(
    "fonte",
    F.when(F.col("populacao_raw").isNotNull(), F.lit("ibge_direto"))
     .when(F.col("ano_left").isNotNull() & F.col("ano_right").isNotNull(), F.lit("interpolado_linear"))
     .when(F.col("pop_left").isNotNull(),  F.lit("carry_forward"))
     .when(F.col("pop_right").isNotNull(), F.lit("carry_backward"))
     .otherwise(F.lit("indisponivel"))
)

silver_df = (
    panel.select(
        F.col("Ano"),
        F.col("uf"),
        F.round(F.col("populacao_filled"), 0).cast("long").alias("populacao"),
        F.col("fonte"),
    )
    .withColumn("_bronze_snapshot_ts", F.lit(latest_ts))
    .withColumn("_silver_built_ts",    F.current_timestamp())
    .orderBy("uf", "Ano")
)

# COMMAND ----------

# MAGIC %md
# MAGIC ## DQ checks

# COMMAND ----------

n_total = silver_df.count()
n_indisp = silver_df.where(F.col("fonte") == "indisponivel").count()
n_bad = silver_df.where(F.col("populacao").isNull() | (F.col("populacao") <= 0)).count()
ufs = silver_df.select("uf").distinct().count()
years = silver_df.select("Ano").distinct().count()

print(f"rows={n_total}  ufs={ufs}  years={years}  indisponivel={n_indisp}  bad_pop={n_bad}")
assert ufs == 27, f"Expected 27 UFs, got {ufs}"
assert years == YEAR_MAX - YEAR_MIN + 1, f"Expected {YEAR_MAX - YEAR_MIN + 1} years, got {years}"
assert n_indisp == 0, f"Got {n_indisp} rows with fonte=indisponivel"
assert n_bad    == 0, f"Got {n_bad} rows with bad populacao"
print("✔ DQ passed")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Write silver Delta (overwrite — Delta history preserves prior snapshots)

# COMMAND ----------

(
    silver_df.write.format("delta")
        .mode("overwrite")
        .option("overwriteSchema", "true")
        .partitionBy("Ano")
        .saveAsTable(SILVER_TABLE)
)

spark.sql(f"COMMENT ON TABLE {SILVER_TABLE} IS "
          f"'Mirante · População UF×Ano (IBGE 6579 + interpolação linear). "
          f"Overwritten each refresh; use Delta time travel to inspect prior snapshots.'")

print(f"✔ {SILVER_TABLE} written ({silver_df.count()} rows)")
spark.sql(f"DESCRIBE HISTORY {SILVER_TABLE}").select("version", "timestamp", "operation").show(5, truncate=False)

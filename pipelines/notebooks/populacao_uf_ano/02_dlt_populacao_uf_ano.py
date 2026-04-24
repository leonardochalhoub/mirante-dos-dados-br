# Databricks notebook source
# MAGIC %md
# MAGIC # populacao_uf_ano · 02 · DLT (Lakeflow Declarative Pipelines)
# MAGIC
# MAGIC Materializa duas tabelas:
# MAGIC
# MAGIC ```
# MAGIC mirante_prd.bronze.ibge_populacao_raw   ← raw payload IBGE (JSON estruturado)
# MAGIC mirante_prd.silver.populacao_uf_ano     ← UF × Ano com interpolação linear de gaps
# MAGIC ```
# MAGIC
# MAGIC ## Lógica de preenchimento
# MAGIC
# MAGIC 1. Se IBGE publicou aquele ano para aquela UF → usa o valor direto.
# MAGIC 2. Se há ano publicado *antes* E *depois* na mesma UF → **interpolação linear**.
# MAGIC 3. Se só há ano antes → carry-forward (último valor conhecido).
# MAGIC 4. Se só há ano depois → carry-backward (primeiro valor futuro).
# MAGIC
# MAGIC Isso preserva a lógica do pipeline original. Quando IBGE publicar 2027, basta:
# MAGIC 1. Rodar `01_download_ibge` com `end_year=2027`
# MAGIC 2. Rodar essa pipeline DLT
# MAGIC
# MAGIC ## Parâmetros do pipeline DLT
# MAGIC
# MAGIC Configurados via `databricks.yml` em `configuration:`:
# MAGIC | chave | default | descrição |
# MAGIC | --- | --- | --- |
# MAGIC | `mirante.populacao.raw_path` | `/Volumes/mirante_prd/bronze/raw/ibge/populacao_uf.json` | onde o JSON foi gravado |
# MAGIC | `mirante.populacao.year_min` | `2013` | primeiro ano do panel completo |
# MAGIC | `mirante.populacao.year_max` | `2026` | último ano (Spark cria o grid completo) |

# COMMAND ----------

import dlt
from pyspark.sql import functions as F, types as T, Window

CATALOG  = spark.conf.get("mirante.catalog", "mirante_prd")
RAW_PATH = spark.conf.get("mirante.populacao.raw_path", f"/Volumes/{CATALOG}/bronze/raw/ibge/populacao_uf.json")
YEAR_MIN = int(spark.conf.get("mirante.populacao.year_min", "2013"))
YEAR_MAX = int(spark.conf.get("mirante.populacao.year_max", "2026"))

print(f"catalog={CATALOG}  raw={RAW_PATH}  year_min={YEAR_MIN}  year_max={YEAR_MAX}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Bronze · `mirante_prd.bronze.ibge_populacao_raw`

# COMMAND ----------

@dlt.table(
    name=f"{CATALOG}.bronze.ibge_populacao_raw",
    comment="Raw payload from IBGE/SIDRA Agregados (6579, var 9324). One JSON per refresh.",
    table_properties={"quality": "bronze"},
)
def ibge_populacao_raw():
    return (
        spark.read.option("multiline", "true").json(RAW_PATH)
    )

# COMMAND ----------

# MAGIC %md
# MAGIC ## Silver · `mirante_prd.silver.populacao_uf_ano`

# COMMAND ----------

UF_ID_TO_SIGLA = {
    "11": "RO", "12": "AC", "13": "AM", "14": "RR", "15": "PA", "16": "AP", "17": "TO",
    "21": "MA", "22": "PI", "23": "CE", "24": "RN", "25": "PB", "26": "PE", "27": "AL", "28": "SE", "29": "BA",
    "31": "MG", "32": "ES", "33": "RJ", "35": "SP",
    "41": "PR", "42": "SC", "43": "RS",
    "50": "MS", "51": "MT", "52": "GO", "53": "DF",
}

@dlt.table(
    name=f"{CATALOG}.silver.populacao_uf_ano",
    comment="População residente estimada por UF × Ano (IBGE/SIDRA tabela 6579, variável 9324). "
            "Anos não publicados pelo IBGE são preenchidos via interpolação linear entre vizinhos "
            "conhecidos; carry-forward/backward nas bordas.",
    table_properties={"quality": "silver"},
)
@dlt.expect_or_drop("uf_valida",          "uf IS NOT NULL AND length(uf) = 2")
@dlt.expect_or_drop("ano_no_intervalo",   "Ano BETWEEN 2000 AND 2100")
@dlt.expect_or_drop("populacao_positiva", "populacao IS NOT NULL AND populacao > 0")
@dlt.expect("ano_dentro_do_range_pedido", f"Ano BETWEEN {YEAR_MIN} AND {YEAR_MAX}")
def populacao_uf_ano():
    src = dlt.read(f"{CATALOG}.bronze.ibge_populacao_raw")

    # Explode resultados[].series[] → (uf_id, serie_struct)
    df = (
        src.select(F.explode("resultados").alias("r"))
           .select(F.explode(F.col("r.series")).alias("s"))
           .select(
               F.col("s.localidade.id").alias("uf_id"),
               F.col("s.serie").alias("serie_struct"),
           )
    )

    # IBGE returns serie as a JSON object with year-string keys (e.g. {"2013": "776463"}).
    # Spark's JSON inference creates a STRUCT with fixed fields per year (changes across responses!),
    # which doesn't work with explode(). Round-trip via JSON to a real MapType so explode works.
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

    # Build complete UF × Ano grid using parameterized [YEAR_MIN, YEAR_MAX]
    all_years = spark.range(YEAR_MIN, YEAR_MAX + 1).select(F.col("id").cast("int").alias("Ano"))
    all_ufs   = df.select("uf").distinct()
    grid      = all_ufs.crossJoin(all_years)

    panel = grid.join(df, on=["uf", "Ano"], how="left")

    w_left = (Window.partitionBy("uf").orderBy(F.col("Ano").asc())
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
         # internal gap → linear interpolation
         .when(
             F.col("ano_left").isNotNull() & F.col("ano_right").isNotNull() & (F.col("ano_right") != F.col("ano_left")),
             F.col("pop_left") + (F.col("Ano") - F.col("ano_left")) *
                                 (F.col("pop_right") - F.col("pop_left")) /
                                 (F.col("ano_right") - F.col("ano_left")),
         )
         # boundary → carry-forward / carry-backward
         .when(F.col("pop_left").isNotNull(),  F.col("pop_left"))
         .when(F.col("pop_right").isNotNull(), F.col("pop_right"))
         .otherwise(F.lit(None).cast("double"))
    )

    # Track lineage of each cell: was it from IBGE, interpolated, or carried?
    panel = panel.withColumn(
        "fonte",
        F.when(F.col("populacao_raw").isNotNull(), F.lit("ibge_direto"))
         .when(F.col("ano_left").isNotNull() & F.col("ano_right").isNotNull(), F.lit("interpolado_linear"))
         .when(F.col("pop_left").isNotNull(),  F.lit("carry_forward"))
         .when(F.col("pop_right").isNotNull(), F.lit("carry_backward"))
         .otherwise(F.lit("indisponivel"))
    )

    return panel.select(
        F.col("Ano"),
        F.col("uf"),
        F.round(F.col("populacao_filled"), 0).cast("long").alias("populacao"),
        F.col("fonte"),
    ).orderBy("uf", "Ano")

# Databricks notebook source
# MAGIC %md
# MAGIC # gold · emendas_estados_df
# MAGIC
# MAGIC Junta `silver.emendas_uf_ano` com dims compartilhados:
# MAGIC - `silver.populacao_uf_ano` (per-capita)
# MAGIC - `silver.ipca_deflators_2021` (R$ 2021)
# MAGIC
# MAGIC Schema final (UF × Ano, agregado tudo, mais split por tipo_RP):
# MAGIC ```
# MAGIC Ano, uf, populacao,
# MAGIC valor_empenhado_nominal, valor_empenhado_2021,
# MAGIC valor_pago_nominal,      valor_pago_2021,
# MAGIC pct_executado,           emendaPerCapita2021,
# MAGIC n_emendas, n_municipios,
# MAGIC empenhado_RP6, empenhado_RP7, empenhado_RP8, empenhado_RP9, empenhado_OUTRO,
# MAGIC pago_RP6,      pago_RP7,      pago_RP8,      pago_RP9,      pago_OUTRO
# MAGIC ```

# COMMAND ----------

dbutils.widgets.text("catalog", "mirante_prd")
CATALOG = dbutils.widgets.get("catalog")

SILVER_EMENDAS  = f"{CATALOG}.silver.emendas_uf_ano"
SILVER_POP      = f"{CATALOG}.silver.populacao_uf_ano"
SILVER_DEFL     = f"{CATALOG}.silver.ipca_deflators_2021"
GOLD_TABLE      = f"{CATALOG}.gold.emendas_estados_df"

print(f"silver_emendas={SILVER_EMENDAS}")
print(f"gold={GOLD_TABLE}")

# COMMAND ----------

from pyspark.sql import functions as F

silver = spark.read.table(SILVER_EMENDAS)
pop    = spark.read.table(SILVER_POP).select("Ano", "uf", "populacao")
defl   = spark.read.table(SILVER_DEFL).select("Ano", "deflator_to_2021")

# Defesa em profundidade: o silver já dropa o ano corrente (Ano <
# year(current_date)) porque a CSV consolidada CGU é atualizada
# continuamente durante o ano. Replicamos o filtro no gold para que,
# se o silver estiver stale (sem refresh recente), o gold ainda
# apresente apenas anos completos (Jan-Dez). Política idêntica em
# silver/pbf_total_uf_mes.py e silver/sih_uropro_uf_ano.py.
current_year = spark.sql("SELECT year(current_date()) AS y").first()["y"]
n_pre = silver.count()
silver = silver.where(F.col("Ano") < F.lit(current_year))
n_post = silver.count()
if n_post < n_pre:
    print(f"⚠ gold dropou {n_pre - n_post} linhas com Ano >= {current_year} "
          f"(ano corrente, parcial — CGU consolidado é atualizado durante o ano)")

silver_n = n_post
print(f"silver_emendas rows={silver_n:,}  pop rows={pop.count()}  defl rows={defl.count()}")

# Defensive: silver pode estar vazia se o ingest CGU falhou ou se a bronze
# foi populada antes de fix de schema. Sai gracefully sem crashar o DAG.
if silver_n == 0:
    print("⚠ silver.emendas_uf_ano está vazia. Investigue o upstream:")
    print("  1. Verifique o run de ingest_cgu_emendas (URL emendas-parlamentares)")
    print("  2. Verifique bronze.emendas_pagamentos: spark.read.table(...).count()")
    print("  3. Re-rode silver após bronze ter dados")
    dbutils.notebook.exit("SKIPPED: silver.emendas_uf_ano is empty")

# COMMAND ----------

# ─── Aggregate UF × Ano (across all tipo_emenda) ───────────────────────────
totals = (
    silver.groupBy("Ano", "uf")
          .agg(
              F.sum("valor_empenhado").alias("valor_empenhado_nominal"),
              F.sum("valor_pago").alias("valor_pago_nominal"),
              F.sum("valor_restos_a_pagar").alias("valor_restos_nominal"),
              F.sum("n_emendas").cast("long").alias("n_emendas"),
              F.max("n_municipios").cast("long").alias("n_municipios"),
          )
)

# ─── Pivot por tipo_emenda ─────────────────────────────────────────────────
pivot_emp = (
    silver.groupBy("Ano", "uf")
          .pivot("tipo_emenda", ["RP6", "RP7", "RP8", "RP9", "OUTRO"])
          .agg(F.sum("valor_empenhado"))
)
for c in ("RP6", "RP7", "RP8", "RP9", "OUTRO"):
    if c not in pivot_emp.columns:
        pivot_emp = pivot_emp.withColumn(c, F.lit(0.0))
    pivot_emp = pivot_emp.withColumnRenamed(c, f"empenhado_{c}")

pivot_pago = (
    silver.groupBy("Ano", "uf")
          .pivot("tipo_emenda", ["RP6", "RP7", "RP8", "RP9", "OUTRO"])
          .agg(F.sum("valor_pago"))
)
for c in ("RP6", "RP7", "RP8", "RP9", "OUTRO"):
    if c not in pivot_pago.columns:
        pivot_pago = pivot_pago.withColumn(c, F.lit(0.0))
    pivot_pago = pivot_pago.withColumnRenamed(c, f"pago_{c}")

# ─── Join everything ───────────────────────────────────────────────────────
df = (
    totals
    .join(pivot_emp,  on=["Ano", "uf"], how="left")
    .join(pivot_pago, on=["Ano", "uf"], how="left")
    .join(pop,        on=["Ano", "uf"], how="left")
    .join(defl,       on=["Ano"],       how="left")
)

# Fill nulls in pivot columns
for c in ["empenhado_RP6","empenhado_RP7","empenhado_RP8","empenhado_RP9","empenhado_OUTRO",
          "pago_RP6","pago_RP7","pago_RP8","pago_RP9","pago_OUTRO"]:
    df = df.fillna(0.0, subset=[c])

# ─── Derived metrics ───────────────────────────────────────────────────────
df = (
    df
    .withColumn("valor_empenhado_2021", F.col("valor_empenhado_nominal") * F.col("deflator_to_2021"))
    .withColumn("valor_pago_2021",      F.col("valor_pago_nominal")      * F.col("deflator_to_2021"))
    .withColumn("pct_executado",
                F.when(F.col("valor_empenhado_nominal") > 0,
                       F.col("valor_pago_nominal") / F.col("valor_empenhado_nominal"))
                 .otherwise(F.lit(None)))
    .withColumn("emendaPerCapita2021",
                F.when(F.col("populacao") > 0,
                       F.col("valor_pago_2021") / F.col("populacao"))
                 .otherwise(F.lit(None)))
)

gold_df = df.select(
    "Ano", "uf",
    F.col("populacao").cast("long"),
    "valor_empenhado_nominal", "valor_empenhado_2021",
    "valor_pago_nominal",      "valor_pago_2021",
    "valor_restos_nominal",
    "pct_executado", "emendaPerCapita2021",
    "n_emendas", "n_municipios",
    "empenhado_RP6","empenhado_RP7","empenhado_RP8","empenhado_RP9","empenhado_OUTRO",
    "pago_RP6","pago_RP7","pago_RP8","pago_RP9","pago_OUTRO",
).withColumn("_gold_built_ts", F.current_timestamp()).orderBy("Ano", "uf")

# COMMAND ----------

n = gold_df.count()
ufs = gold_df.select("uf").distinct().count()
years = gold_df.select("Ano").distinct().count()
print(f"gold rows={n}  ufs={ufs}  years={years}")

# Spot-check most-recent brasil aggregate (defensive: handle empty / null-only Ano)
years = [r["Ano"] for r in gold_df.select("Ano").distinct().collect() if r["Ano"] is not None]
if years:
    y_recent = max(years)
    recent = gold_df.where(F.col("Ano") == y_recent)
    sums = recent.agg(
        F.sum("valor_empenhado_nominal").alias("emp"),
        F.sum("valor_pago_nominal").alias("pago"),
        F.sum("n_emendas").alias("n"),
    ).first()
    print(f"Brasil {y_recent}: empenhado=R${sums['emp']/1e9:.2f}bi  pago=R${sums['pago']/1e9:.2f}bi  n_emendas={sums['n']:,}")
else:
    print("⚠ gold sem Anos válidos — verifique se silver.emendas_uf_ano tem coluna Ano populada")

# COMMAND ----------

(
    gold_df.write.format("delta")
        .mode("overwrite")
        .option("overwriteSchema", "true")
        .partitionBy("Ano")
        .saveAsTable(GOLD_TABLE)
)

# Inline minimal COMMENT — full enrichment via _meta/apply_catalog_metadata.py.
spark.sql(f"COMMENT ON TABLE {GOLD_TABLE} IS "
          f"'Mirante · Emendas Parlamentares UF × Ano (gold). Pivot de silver "
          f"por tipo_RP (RP6/RP7/RP8/RP9/OUTRO) + deflator IPCA-2021 + população "
          f"IBGE para `emendaPerCapita2021`. Achado WP#3 (CHALHOUB 2026d): "
          f"emendas per capita correlacionam-se NEGATIVAMENTE com acesso a "
          f"cirurgia uroginecológica (ρ ≈ -0,45). "
          f"Reaplicar metadata rico via job_apply_catalog_metadata.'")

print(f"✔ {GOLD_TABLE} written ({n} rows)")

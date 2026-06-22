# Databricks notebook source
# MAGIC %md
# MAGIC # silver · pbf_total_uf_mes
# MAGIC
# MAGIC Lê o bronze `<catalog>.bronze.pbf_pagamentos`, parseia `valor_parcela` como
# MAGIC Decimal e agrega por `(Ano, Mes, uf)`. Origens PBF + Auxílio Brasil + NBF
# MAGIC entram cruas: na transição nov/2021 a soma de `valor_parcela` já combina as
# MAGIC duas folhas e `countDistinct(NIS)` deduplica beneficiários (ver célula abaixo):
# MAGIC - `n` = beneficiários distintos por mês (chave: `nis_favorecido` dígitos)
# MAGIC - `n_ano` = beneficiários distintos por ano (replicado em cada linha do mês)
# MAGIC - `total_estado` = soma de `valor_parcela`

# COMMAND ----------

dbutils.widgets.text("catalog", "mirante_prd")
CATALOG = dbutils.widgets.get("catalog")

BRONZE_TABLE = f"{CATALOG}.bronze.pbf_pagamentos"
SILVER_TABLE = f"{CATALOG}.silver.pbf_total_uf_mes"

print(f"bronze={BRONZE_TABLE}  silver={SILVER_TABLE}")

# COMMAND ----------

from pyspark.sql import functions as F, types as T

# Bronze é append-only via Auto Loader. Se um mesmo arquivo aparecer 2× (não deve, mas
# por garantia), tomamos a última versão. Aqui, dedupe pela coluna do filename + linha.
bronze = spark.read.table(BRONZE_TABLE)
print(f"bronze rows: {bronze.count():,}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Nov/2021 PBF→Auxílio Brasil — transição SEM tratamento especial
# MAGIC
# MAGIC Em nov/2021 o PBF (última folha) e o Auxílio Brasil (primeira folha) pagaram
# MAGIC AMBOS na mesma competência (202111): os ~14,36M beneficiários AUX são um
# MAGIC subconjunto EXATO dos ~14,51M do PBF — todo mundo recebeu as duas parcelas.
# MAGIC O total de R$ efetivamente transferido no mês é a SOMA das duas folhas, e a
# MAGIC agregação crua abaixo já produz exatamente isso:
# MAGIC   - `total_estado = sum(valor_parcela)`  soma PBF + AUX (R$ realmente pagos);
# MAGIC   - `n` / `n_ano  = countDistinct(NIS)`  deduplicam beneficiários sozinhos.
# MAGIC
# MAGIC **Por que removemos a síntese antiga `PBF_AUX_SUM`:** ela agrupava por
# MAGIC (ano,mes,competencia) e somava todas as colunas "numéricas". Quando o bronze
# MAGIC passou a tipar `mes_competencia` como INT (28/04/2026), a síntese passou a
# MAGIC SOMAR `mes_competencia` (~5,8×10¹²); `Ano = substring(...,1,4)` virava 5833,
# MAGIC caía fora do range [2013, ano_atual] e a linha era descartada — nov/2021
# MAGIC sumia em silêncio → 2021 com 11 meses → o gold (`n_months == 12`) derrubava
# MAGIC o ano INTEIRO. A agregação crua é correta, idêntica em todo mês, e imune a
# MAGIC drift de tipo no bronze.

# COMMAND ----------

df = bronze

# COMMAND ----------

# MAGIC %md
# MAGIC ## Aggregate UF × Ano × Mes

# COMMAND ----------

# Parse valor_parcela "800,00" → Decimal(38, 2)
df = df.withColumn(
    "valor_parcela_dec",
    F.regexp_replace(F.col("valor_parcela"), ",", ".").cast(T.DecimalType(38, 2))
)

# Beneficiary key: digits only of nis_favorecido
df = df.withColumn("_benef_id", F.regexp_replace(F.trim(F.col("nis_favorecido")), r"\D", ""))
df = df.where(F.length(F.col("_benef_id")) > 0)

# Add Ano (competency year) at the bronze level so all aggregations are consistent.
# IMPORTANT: this Ano comes from mes_competencia (the COMPETENCY year — what the
# payment was FOR), not from bronze.ano (which is the FILE year — when the file
# was published). For PBF/AUX/NBF transition periods, these can differ.
df = (
    df.withColumn("Ano", F.substring(F.col("mes_competencia"), 1, 4).cast("int"))
      .withColumn("Mes", F.substring(F.col("mes_competencia"), 5, 2).cast("int"))
)

# Annual distinct beneficiaries by (Ano, uf) — competency year, NOT file year.
# This guarantees ONE n_ano per (Ano, uf) regardless of how many origins (PBF, AUX,
# NBF) contributed to that competency year.
df_year = (
    df.groupBy("Ano", "uf")
      .agg(F.countDistinct("_benef_id").cast("long").alias("n_ano"))
)

silver_df = (
    df.groupBy("Ano", "Mes", "uf", "mes_competencia")
      .agg(
          F.countDistinct("_benef_id").cast("long").alias("n"),
          F.sum(F.col("valor_parcela_dec")).alias("total_estado"),
      )
      .join(df_year, on=["Ano", "uf"], how="left")
      .select("Ano", "Mes", "uf", "mes_competencia",
              F.col("n").cast("long"),
              F.col("n_ano").cast("long"),
              F.col("total_estado").cast("decimal(38,2)"))
      .withColumn("_silver_built_ts", F.current_timestamp())
)

# Defensive filter: keep only valid 27 UFs + plausible competency year range.
# CGU's NBF files ship rows with retroactive (e.g. court-ordered back payments to
# 2010) or advance-paid (mes_competencia in the future) values. Without bounds,
# silver gets ~36 distinct Ano values instead of ~13 (one per active program year).
VALID_UFS = ["AC","AL","AM","AP","BA","CE","DF","ES","GO","MA","MG","MS","MT",
             "PA","PB","PE","PI","PR","RJ","RN","RO","RR","RS","SC","SE","SP","TO"]

# Bound year range: PBF program started 2013; cap at current year (no future competencies).
# `mes_competencia` may be retro-paid in past programs but our front shows from 2013 onwards.
n_before = silver_df.count()
silver_df = silver_df.where(
    F.col("Ano").isNotNull()
    & (F.col("Ano") >= 2013)
    & (F.col("Ano") <= F.year(F.current_date()))
    & F.col("Mes").isNotNull() & (F.col("Mes").between(1, 12))
    & F.col("uf").isin(VALID_UFS)
)
n_after = silver_df.count()
distinct_years = sorted(r["Ano"] for r in silver_df.select("Ano").distinct().collect())
print(f"silver years kept ({len(distinct_years)}): {distinct_years}")
if n_after < n_before:
    print(f"⚠ filtrou {n_before - n_after} linhas silver com Ano/Mes/uf "
          f"fora do range esperado (mantém {n_after} válidas)")

# COMMAND ----------

n = silver_df.count()
ufs = silver_df.select("uf").distinct().count()
years = silver_df.select("Ano").distinct().count()
print(f"rows={n}  ufs={ufs}  years={years}")
assert ufs == 27, f"Expected 27 UFs, got {ufs}"

# Guard explícito (regressão nov/2021): NENHUM ano passado pode ter < 12 meses de
# competência. O ano corrente pode ser parcial. Falha alto em vez de deixar o gold
# derrubar o ano em silêncio.
months_by_year = {r["Ano"]: r["m"] for r in
                  silver_df.groupBy("Ano").agg(F.countDistinct("Mes").alias("m")).collect()}
current_year = spark.sql("SELECT year(current_date())").first()[0]
incomplete_past = {y: m for y, m in sorted(months_by_year.items())
                   if y < current_year and m != 12}
assert not incomplete_past, (
    f"Anos passados com != 12 meses de competência: {incomplete_past}. "
    f"Provável regressão no tratamento de transição (ex.: nov/2021 PBF→AUX). "
    f"Abortando silver para não propagar ano incompleto ao gold."
)
print("✔ DQ passed")

# COMMAND ----------

(
    silver_df.write.format("delta")
        .mode("overwrite")
        .option("overwriteSchema", "true")
        .partitionBy("Ano")
        .saveAsTable(SILVER_TABLE)
)

# Inline minimal COMMENT — full enrichment via _meta/apply_catalog_metadata.py.
spark.sql(f"COMMENT ON TABLE {SILVER_TABLE} IS "
          f"'Mirante · PBF agregado UF × Ano × Mes — n (distinto/mes), "
          f"n_ano (distinto/ano, broadcast), total_estado (R$ nominais decimal(38,2)). "
          f"Origens unificadas: PBF (Lei 10.836/2003) + Auxílio Brasil "
          f"(MP 1.061/2021) + Novo Bolsa Família (Lei 14.601/2023). "
          f"Reaplicar metadata rico via job_apply_catalog_metadata.'")

print(f"✔ {SILVER_TABLE} written ({n:,} rows)")

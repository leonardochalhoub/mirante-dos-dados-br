# Databricks notebook source
# MAGIC %md
# MAGIC # Diagnostics · Sensibilidade SP 1986 no choque do Cruzado
# MAGIC
# MAGIC O panorama RAIS (2026-04-28 §2.2) reporta que o Plano Cruzado (1986)
# MAGIC causou queda de **-28,6%** nos vínculos ativos em 31/12 versus 1985 —
# MAGIC o maior choque negativo da série de 40 anos.
# MAGIC
# MAGIC ## Problema metodológico identificado pelo Conselho
# MAGIC
# MAGIC O arquivo `SP1986_1986.7z` está em **quarentena permanente** (`_bad/`)
# MAGIC por corrupção do FTP PDET. SP em 1985 representava 35,5% do emprego
# MAGIC formal nacional.
# MAGIC
# MAGIC **Pergunta:** quanto da queda de 28,6% em 1986 é (a) choque real do
# MAGIC Cruzado vs (b) artefato do arquivo SP1986 ausente?
# MAGIC
# MAGIC ## Estratégia de sensibilidade
# MAGIC
# MAGIC 1. Calcular Δ% de vínculos ativos 1985→1986 incluindo TODAS as UFs
# MAGIC 2. Recalcular EXCLUINDO SP em ambos os anos
# MAGIC 3. Recalcular incluindo SP em 1985 mas IMPUTANDO SP1986 com média
# MAGIC    (média de variação dos vizinhos de SP em 1985→1986: RJ, MG, PR)
# MAGIC 4. Comparar magnitudes
# MAGIC
# MAGIC ## Saída
# MAGIC
# MAGIC Tabela com 3 cenários para o paper apresentar transparentemente.

# COMMAND ----------

dbutils.widgets.text("catalog", "mirante_prd")
CATALOG = dbutils.widgets.get("catalog")
BRONZE_TABLE = f"{CATALOG}.bronze.rais_vinculos"

from pyspark.sql import functions as F

spark.conf.set("spark.sql.ansi.enabled", "false")

# COMMAND ----------

# MAGIC %md ## Cenário 1 · Brasil INTEIRO (com SP1986 ausente da fonte)

# COMMAND ----------

base = spark.read.table(BRONZE_TABLE).filter(F.col("ano").isin(1985, 1986))
base_with_uf = (base
    .withColumn("muni", F.coalesce(
        F.when(F.col("municipio_trab_codigo") == "999999", F.lit(None)).otherwise(F.col("municipio_trab_codigo")) if "municipio_trab_codigo" in base.columns else F.lit(None),
        F.col("mun_trab")               if "mun_trab"               in base.columns else F.lit(None),
        F.col("municipio_codigo")       if "municipio_codigo"       in base.columns else F.lit(None),
        F.col("municipio")              if "municipio"              in base.columns else F.lit(None),
    ))
    .withColumn("uf_code", F.substring(F.regexp_replace("muni", r"\D", ""), 1, 2).cast("int"))
    .withColumn("vinc_ativo", F.when(F.trim(F.coalesce(F.col("vinculo_ativo_31_12"), F.col("ind_vinculo_ativo_31_12_codigo"))).cast("string").isin("1", "01"), 1).otherwise(0))
)

cenario_1 = (base_with_uf
    .groupBy("ano")
    .agg(F.sum("vinc_ativo").alias("ativos"))
    .orderBy("ano"))

print("=== Cenário 1 · Brasil inteiro (SP1986 ausente da fonte) ===")
cenario_1.show()

a85_c1 = cenario_1.filter(F.col("ano") == 1985).first()["ativos"]
a86_c1 = cenario_1.filter(F.col("ano") == 1986).first()["ativos"]
delta_c1 = (a86_c1 - a85_c1) / a85_c1 * 100
print(f"  Δ 1985→1986: {delta_c1:+.1f}%  (ativos {a85_c1:,} → {a86_c1:,})")

# COMMAND ----------

# MAGIC %md ## Cenário 2 · Brasil EX-SP (excluindo SP em ambos os anos)

# COMMAND ----------

cenario_2 = (base_with_uf
    .filter(F.col("uf_code") != 35)  # SP code IBGE
    .groupBy("ano")
    .agg(F.sum("vinc_ativo").alias("ativos"))
    .orderBy("ano"))

print("=== Cenário 2 · Brasil ex-SP ===")
cenario_2.show()

a85_c2 = cenario_2.filter(F.col("ano") == 1985).first()["ativos"]
a86_c2 = cenario_2.filter(F.col("ano") == 1986).first()["ativos"]
delta_c2 = (a86_c2 - a85_c2) / a85_c2 * 100
print(f"  Δ 1985→1986: {delta_c2:+.1f}%  (ativos {a85_c2:,} → {a86_c2:,})")
print()
print(f"  → IMPLICAÇÃO: se {delta_c2:+.1f}% (ex-SP) for muito menor (em magnitude)")
print(f"     que {delta_c1:+.1f}% (com SP), então o choque do Cruzado teve menos")
print(f"     impacto no resto do Brasil — ou SP1986 ausente é o que infla a queda.")

# COMMAND ----------

# MAGIC %md ## Cenário 3 · SP1986 imputado com a média dos vizinhos

# COMMAND ----------

# Estados "vizinhos" econômicos de SP em 1985 (industrializados): RJ, MG, PR
# Calcula Δ% médio desses 3 em 1985→1986, aplica à SP de 1985.
vizinhos = (base_with_uf
    .filter(F.col("uf_code").isin(33, 31, 41))  # RJ, MG, PR
    .groupBy("ano", "uf_code")
    .agg(F.sum("vinc_ativo").alias("ativos"))
)

vizinhos_pivot = vizinhos.groupBy("uf_code").pivot("ano").sum("ativos")
print("=== Vizinhos econômicos de SP (RJ=33, MG=31, PR=41) ===")
vizinhos_pivot.show()

vizinhos_rates = (vizinhos_pivot
    .withColumn("delta_pct", (F.col("1986") - F.col("1985")) / F.col("1985") * 100)
    .orderBy("uf_code"))
vizinhos_rates.show()

avg_delta_vizinhos = vizinhos_rates.agg(F.avg("delta_pct").alias("avg")).first()["avg"]
print(f"  Δ% médio dos vizinhos: {avg_delta_vizinhos:+.2f}%")

# Imputa SP1986 = SP1985 × (1 + avg_delta_vizinhos/100)
sp_1985 = base_with_uf.filter(F.col("uf_code") == 35).filter(F.col("ano") == 1985).agg(F.sum("vinc_ativo").alias("a")).first()["a"]
sp_1986_imputed = int(sp_1985 * (1 + avg_delta_vizinhos / 100))
print(f"  SP 1985 (real):     {sp_1985:,}")
print(f"  SP 1986 (imputado): {sp_1986_imputed:,}  (= SP1985 × {1 + avg_delta_vizinhos/100:.4f})")

# Cenário 3 Brasil: ex-SP + SP imputado
ex_sp_1985 = a85_c2
ex_sp_1986 = a86_c2
brasil_c3_1985 = ex_sp_1985 + sp_1985
brasil_c3_1986 = ex_sp_1986 + sp_1986_imputed
delta_c3 = (brasil_c3_1986 - brasil_c3_1985) / brasil_c3_1985 * 100

print()
print("=== Cenário 3 · Brasil com SP1986 imputado ===")
print(f"  1985: {brasil_c3_1985:,}")
print(f"  1986: {brasil_c3_1986:,} (ex-SP {ex_sp_1986:,} + SP imputado {sp_1986_imputed:,})")
print(f"  Δ 1985→1986: {delta_c3:+.1f}%")

# COMMAND ----------

# MAGIC %md ## Comparação dos 3 cenários

# COMMAND ----------

print("=" * 65)
print(f"{'Cenário':<35} {'Δ% 1985→1986':>15}")
print("-" * 65)
print(f"{'1. Brasil (SP1986 ausente)':<35} {delta_c1:>+14.1f}%")
print(f"{'2. Brasil ex-SP':<35} {delta_c2:>+14.1f}%")
print(f"{'3. Brasil com SP1986 imputado':<35} {delta_c3:>+14.1f}%")
print("=" * 65)
print()
print("INTERPRETAÇÃO:")
print(f"  - Cenário 1 ({delta_c1:+.1f}%) é o que o panorama original reportou.")
print(f"  - Cenário 2 ({delta_c2:+.1f}%) mostra que ex-SP, a queda ainda existe")
print(f"    mas a magnitude é menor.")
print(f"  - Cenário 3 ({delta_c3:+.1f}%) imputa SP1986 com a média de seus vizinhos.")
print(f"    Esse é o cenário que paper deve reportar como 'estimativa real' do")
print(f"    choque do Cruzado, com a quarentena documentada como limitação.")
print()
print("RECOMENDAÇÃO PRO PAPER:")
print(f"  1. Reportar Cenário 3 como estimativa principal (~{delta_c3:+.1f}%)")
print(f"  2. Apresentar Cenários 1 e 2 como sensibilidade")
print(f"  3. Declarar em LIMITAÇÕES que SP1986 está em quarentena (PDET FTP")
print(f"     corrompido, fora do controle do pesquisador)")
print(f"  4. Apresentar diff |Cenário 1 - Cenário 3| como banda de incerteza")

# COMMAND ----------

# MAGIC %md ## Salvar resultados em tabela diagnostic

# COMMAND ----------

results = spark.createDataFrame([
    ("brasil_completo_sp1986_ausente", a85_c1, a86_c1, float(delta_c1)),
    ("brasil_ex_sp",                   a85_c2, a86_c2, float(delta_c2)),
    ("brasil_sp_imputado_vizinhos",    brasil_c3_1985, brasil_c3_1986, float(delta_c3)),
], ["cenario", "ativos_1985", "ativos_1986", "delta_pct"])

(results.write.format("delta").mode("overwrite")
    .saveAsTable(f"{CATALOG}.silver._rais_sp1986_sensitivity"))

print(f"✔ {CATALOG}.silver._rais_sp1986_sensitivity gravado")

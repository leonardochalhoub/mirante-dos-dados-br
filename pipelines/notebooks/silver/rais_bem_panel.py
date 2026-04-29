# Databricks notebook source
# MAGIC %md
# MAGIC # silver · rais_bem_panel
# MAGIC
# MAGIC Painel **município × CNAE 2-dígitos × ano** otimizado para análise causal
# MAGIC do **BEm (Benefício Emergencial de Manutenção do Emprego e da Renda)** —
# MAGIC programa criado pela MP 936/2020 (convertida na Lei 14.020/2020) durante
# MAGIC a pandemia de COVID-19.
# MAGIC
# MAGIC ## Por que silver TEMÁTICA, não ampla
# MAGIC
# MAGIC Conselho do Mirante (2026-04-28) recomendou unanimemente: silver-por-questão,
# MAGIC não silver ampla cross-questão. Silver ampla com 30+ outcomes seria
# MAGIC inutilizável pra qualquer DiD/RDD específico — variáveis de controle e
# MAGIC tratamento variam por questão.
# MAGIC
# MAGIC ## Janela
# MAGIC
# MAGIC **2017–2022 (6 anos)**:
# MAGIC - **Pré-tratamento**: 2017–2019 (3 anos para teste de paralelismo de
# MAGIC   tendências — "parallel trends test")
# MAGIC - **Tratamento**: 2020–2021 (BEm em vigor)
# MAGIC - **Pós-tratamento**: 2022 (recuperação, fim do BEm)
# MAGIC
# MAGIC Dados 2023–2024 (era3 .COMT, schema renomeado) DELIBERADAMENTE excluídos
# MAGIC desta silver — diluiriam DiD com período pós-recuperação.
# MAGIC
# MAGIC ## Grain
# MAGIC
# MAGIC `(municipio_codigo, cnae_2_dig, ano)`. ~5571 munis × ~88 CNAE 2-dig × 6
# MAGIC anos = ~2.9 M linhas teóricas (real ~1.5–2 M com sparse cells).
# MAGIC
# MAGIC ## Outcomes
# MAGIC
# MAGIC - `n_vinculos_ativos`: estoque em 31/12 (outcome principal)
# MAGIC - `n_admissoes`: contratações no ano
# MAGIC - `n_demissoes_total`, `n_demissoes_sjc`, `n_demissoes_pedido`,
# MAGIC   `n_aposentadoria` (decomposição de motivo_desligamento)
# MAGIC - `massa_salarial_dezembro_sm`: soma vl_remun_dezembro em SM
# MAGIC - `remun_mediana_sm`: percentile 50
# MAGIC - `n_femininos_ativos`, `n_masculinos_ativos`
# MAGIC - `n_baixa_escolaridade`: <= ensino médio incompleto (proxy salário baixo)
# MAGIC - `idade_media`, `tempo_emprego_medio_meses`

# COMMAND ----------

dbutils.widgets.text("catalog", "mirante_prd")
dbutils.widgets.text("ano_min", "2017")
dbutils.widgets.text("ano_max", "2022")

CATALOG = dbutils.widgets.get("catalog")
ANO_MIN = int(dbutils.widgets.get("ano_min"))
ANO_MAX = int(dbutils.widgets.get("ano_max"))
BRONZE_TABLE = f"{CATALOG}.bronze.rais_vinculos"
SILVER_TABLE = f"{CATALOG}.silver.rais_bem_panel"

# COMMAND ----------

from pyspark.sql import functions as F, types as T

# Spark 4 (DBR 18+) é estrito em ANSI mode — cast hard-fails em strings com
# resíduo latin-1 ('{ñ', '  ', etc.). Bronze é STRING-ONLY com encoding latin-1
# e arquivos PDET pré-2002 têm esses resíduos. ANSI=false restaura semântica
# clássica de cast (NULL em input inválido) — comportamento esperado para
# agregação que já tolera NULL via F.sum/F.coalesce(0).
spark.conf.set("spark.sql.ansi.enabled", "false")

if not spark.catalog.tableExists(BRONZE_TABLE):
    raise RuntimeError(f"{BRONZE_TABLE} não existe. Execute bronze_rais_vinculos antes.")

# COMMAND ----------

# MAGIC %md ## Coalesce cross-era das colunas relevantes
# MAGIC
# MAGIC Bronze tem colunas dos 4 eras coexistindo via mergeSchema (cada linha só
# MAGIC tem populadas as colunas do header do seu próprio arquivo). Coalesce
# MAGIC explícita reconcilia 1985–2017 (era1/2 com headers legacy) e 2018–2024
# MAGIC (era2/3 com headers expandidos + sufixo `_codigo`).
# MAGIC
# MAGIC Atenção: `municipio_trab_codigo` em era3 é frequentemente "999999" (código
# MAGIC de "ignorado", possivelmente trabalho remoto pós-COVID). Tratamos como
# MAGIC NULL e fallback para `mun_trab` ou `municipio_codigo` (estabelecimento).

# COMMAND ----------

bronze = spark.read.table(BRONZE_TABLE).filter(
    (F.col("ano") >= ANO_MIN) & (F.col("ano") <= ANO_MAX)
)
n_bronze = bronze.count()
print(f"bronze rows ({ANO_MIN}-{ANO_MAX}): {n_bronze:,}")
print(f"bronze columns: {len(bronze.columns)}")


def _coalesce_cols(df, *names):
    """COALESCE de TODAS as colunas existentes no df, em ordem de preferência."""
    cols_lower = {c.lower(): c for c in df.columns}
    matching = [F.col(cols_lower[n.lower()]) for n in names if n.lower() in cols_lower]
    if not matching:
        return F.lit(None)
    if len(matching) == 1:
        return matching[0]
    return F.coalesce(*matching)


# Município (geographic unit do panel).
#
# Bronze tem 4 candidatos por era:
#   - municipio_trab_codigo  (era3 .COMT, ~999999 frequente = "ignorado")
#   - mun_trab               (era2 .txt 2018-2022, ~000000 frequente = sub-registro)
#   - municipio_codigo       (era3 .COMT)
#   - municipio              (era1+2 .txt, geralmente código do ESTABELECIMENTO)
#
# Códigos inválidos a tratar como NULL: '000000', '999999', '999997', '' (vazio).
# Estratégia: COALESCE com filtro de inválidos em CADA candidato, nesta ordem:
#   1. municipio_trab_codigo (preferência: trabalho > estab pra DiD do BEm)
#   2. mun_trab
#   3. municipio_codigo
#   4. municipio (estabelecimento, fallback final — sempre tem valor real)
#
# IBGE municipal codes são 6 dígitos (sem DV) ou 7 dígitos (com DV).
# RAIS reporta tipicamente 6 → não fazer lpad pra 7.
def _muni_or_null(col_name):
    """Trim + nullify de códigos inválidos (puro 0s ou puro 9s + variantes 999997/999998).
    Estratégia regex: aceita só 6 ou 7 dígitos NUMÉRICOS começando com [1-5] (códigos
    IBGE válidos têm UF code 11-53, primeiro dígito 1-5)."""
    if col_name not in bronze.columns:
        return F.lit(None).cast("string")
    raw = F.trim(F.col(col_name).cast("string"))
    # Aceita apenas 6 ou 7 dígitos com primeiro dígito [1-5] (UF IBGE válida)
    valid = raw.rlike(r"^[1-5][0-9]{5,6}$")
    return F.when(valid, raw).otherwise(F.lit(None).cast("string"))


EXPR_MUN = F.coalesce(
    _muni_or_null("municipio_trab_codigo"),
    _muni_or_null("mun_trab"),
    _muni_or_null("municipio_codigo"),
    _muni_or_null("municipio"),
)

# CNAE 2.0 (preferência) ou CNAE 95 (fallback pré-2007) — ambas como string
EXPR_CNAE = _coalesce_cols(
    bronze,
    "cnae_2_0_classe_codigo", "cnae_2_0_classe",
    "cnae_95_classe_codigo",  "cnae_95_classe",
)

# Vínculo ativo em 31/12 (outcome principal)
EXPR_VINC = _coalesce_cols(bronze, "ind_vinculo_ativo_31_12_codigo", "vinculo_ativo_31_12")

# Motivo desligamento (decomposição de tipos)
EXPR_MOTIVO = _coalesce_cols(bronze, "motivo_desligamento_codigo", "motivo_desligamento")

# Sexo (1=M, 2=F)
EXPR_SEXO = _coalesce_cols(bronze, "sexo_codigo", "sexo_trabalhador")

# Remuneração dezembro em SM (preferência) ou nominal (fallback)
EXPR_VL_DEZ_SM = _coalesce_cols(bronze, "vl_remun_dezembro_sm", "vl_rem_dezembro_sm")

# Escolaridade — códigos diferem cross-era; harmonização parcial via mapeamento
EXPR_ESCOL = _coalesce_cols(
    bronze,
    "escolaridade_apos_2005_codigo", "escolaridade_apos_2005",
    "grau_instrucao_2005_1985",
)

# Idade em anos (era1+2: faixa_etaria_codigo categórico; era2/3: idade numérica)
EXPR_IDADE = _coalesce_cols(bronze, "idade")

# Tempo emprego em meses
EXPR_TE = _coalesce_cols(bronze, "tempo_emprego")


def _br_num(col_expr):
    """BR numeric '1.234,56' → DOUBLE. Com ANSI=false, lixo vira NULL."""
    return F.regexp_replace(F.regexp_replace(col_expr, r"\.", ""), ",", ".").cast("double")


# COMMAND ----------

# MAGIC %md ## Construção do painel

# COMMAND ----------

df = (
    bronze
    .withColumn("ano_int",       F.col("ano").cast("int"))
    # Muni: 6 ou 7 dígitos IBGE. RAIS reporta tipicamente 6 (sem DV).
    .withColumn("muni",          F.regexp_replace(EXPR_MUN, r"\D", ""))
    # CNAE 2-dig: pega só os 2 primeiros dígitos (alta-nível setorial)
    .withColumn("cnae2",         F.substring(F.regexp_replace(EXPR_CNAE.cast("string"), r"\D", ""), 1, 2))
    .withColumn("vinc_ativo",    F.when(F.trim(EXPR_VINC.cast("string")).isin("1", "01"), 1).otherwise(0))
    .withColumn("motivo",        F.lpad(F.trim(EXPR_MOTIVO.cast("string")), 2, "0"))
    .withColumn("sexo",          F.when(F.trim(EXPR_SEXO.cast("string")).isin("1", "01"), "M")
                                  .when(F.trim(EXPR_SEXO.cast("string")).isin("2", "02"), "F"))
    .withColumn("vl_dez_sm",     _br_num(EXPR_VL_DEZ_SM))
    .withColumn("idade",         F.when(EXPR_IDADE.cast("int").between(14, 80), EXPR_IDADE.cast("int")))
    .withColumn("te_meses",      _br_num(EXPR_TE))
    .withColumn(
        "baixa_escol",
        # Códigos era1/2: 01-04 = analfabeto + fundamental incompleto/completo
        # Códigos era3 (escolaridade_apos_2005_codigo): 01-04 = mesma faixa
        F.when(F.lpad(F.trim(EXPR_ESCOL.cast("string")), 2, "0").isin("01","02","03","04"), 1).otherwise(0)
    )
    # Filtros: ano não-null, muni com 6+ dígitos (IBGE), cnae2 com 2 dígitos
    .where(F.col("ano_int").isNotNull())
    .where(F.col("muni").isNotNull() & (F.length(F.col("muni")) >= 6))
    .where(F.length(F.col("cnae2")) == 2)
)

# Aggregate a panel: (muni, cnae2, ano) → outcomes
silver_df = (
    df.groupBy("muni", "cnae2", "ano_int").agg(
        F.count("*").cast("long").alias("n_vinculos_total"),
        F.sum("vinc_ativo").cast("long").alias("n_vinculos_ativos"),

        # Decomposição motivo_desligamento — códigos PDET:
        # 00 = ainda ativo / sem desligamento; 10/11 = sem justa causa; 12 = c/ justa causa
        # 20/21 = aposentadoria; 30 = morte; 60 = pedido; 50 = transferência
        F.sum(F.when(F.col("motivo").isin("10", "11"), 1).otherwise(0)).cast("long").alias("n_demissoes_sjc"),
        F.sum(F.when(F.col("motivo") == "12",         1).otherwise(0)).cast("long").alias("n_demissoes_cjc"),
        F.sum(F.when(F.col("motivo") == "60",         1).otherwise(0)).cast("long").alias("n_demissoes_pedido"),
        F.sum(F.when(F.col("motivo").isin("20", "21"), 1).otherwise(0)).cast("long").alias("n_aposentadoria"),
        F.sum(F.when(F.col("motivo") == "30",         1).otherwise(0)).cast("long").alias("n_morte"),
        F.sum(F.when(F.col("motivo").rlike(r"^[1-9][0-9]?$"), 1).otherwise(0)).cast("long").alias("n_demissoes_total"),

        # Massa salarial e estatísticas de remuneração (em SM, comparável cross-era)
        F.sum(F.coalesce(F.col("vl_dez_sm"), F.lit(0.0))).alias("massa_salarial_sm"),
        F.percentile_approx("vl_dez_sm", 0.5).alias("remun_mediana_sm"),
        F.percentile_approx("vl_dez_sm", 0.9).alias("remun_p90_sm"),
        F.avg("vl_dez_sm").alias("remun_media_sm"),

        # Demografia
        F.sum(F.when((F.col("sexo") == "F") & (F.col("vinc_ativo") == 1), 1).otherwise(0)).cast("long").alias("n_femininos_ativos"),
        F.sum(F.when((F.col("sexo") == "M") & (F.col("vinc_ativo") == 1), 1).otherwise(0)).cast("long").alias("n_masculinos_ativos"),
        F.sum(F.when(F.col("baixa_escol") == 1, 1).otherwise(0)).cast("long").alias("n_baixa_escolaridade"),

        # Características médias
        F.avg("idade").alias("idade_media"),
        F.avg("te_meses").alias("te_meses_medio"),
    )
    .withColumnRenamed("ano_int", "ano")
    # UF derivada do código IBGE do município (primeiros 2 dígitos)
    .withColumn("uf_code", F.substring("muni", 1, 2).cast("int"))
    .withColumn(
        "uf",
        F.create_map(
            F.lit(11), F.lit("RO"), F.lit(12), F.lit("AC"), F.lit(13), F.lit("AM"), F.lit(14), F.lit("RR"),
            F.lit(15), F.lit("PA"), F.lit(16), F.lit("AP"), F.lit(17), F.lit("TO"), F.lit(21), F.lit("MA"),
            F.lit(22), F.lit("PI"), F.lit(23), F.lit("CE"), F.lit(24), F.lit("RN"), F.lit(25), F.lit("PB"),
            F.lit(26), F.lit("PE"), F.lit(27), F.lit("AL"), F.lit(28), F.lit("SE"), F.lit(29), F.lit("BA"),
            F.lit(31), F.lit("MG"), F.lit(32), F.lit("ES"), F.lit(33), F.lit("RJ"), F.lit(35), F.lit("SP"),
            F.lit(41), F.lit("PR"), F.lit(42), F.lit("SC"), F.lit(43), F.lit("RS"), F.lit(50), F.lit("MS"),
            F.lit(51), F.lit("MT"), F.lit(52), F.lit("GO"), F.lit(53), F.lit("DF"),
        ).getItem("uf_code")
    )
    .where(F.col("uf").isNotNull())
    .drop("uf_code")
    # CNAE 2-dig setor (alta-nível, baseado em CNAE 2.0 / IBGE)
    # Critério para agrupar setores afetados pelo BEm: serviços de turismo,
    # alimentação, eventos, beleza, transporte de passageiros = ALTAMENTE expostos.
    # Indústria pesada, agro, tech, saúde = MENOS expostos.
    .withColumn(
        "setor_bem_exposicao",
        F.when(F.col("cnae2").isin(
            "55", "56",   # alojamento e alimentação
            "79",          # agências de viagem e turismo
            "82",          # serviços administrativos
            "90", "91", "92", "93",   # arte/cultura/esporte/lazer
            "96",          # outras atividades de serviços pessoais
        ), "alta")
        .when(F.col("cnae2").isin(
            "47",          # comércio varejista
            "49", "50",    # transporte terrestre/aquaviário
            "53",          # correio
            "73",          # publicidade/marketing
            "77",          # aluguéis
            "78",          # gestão de RH
        ), "media")
        .otherwise("baixa")
    )
    .withColumn("_silver_built_ts", F.current_timestamp())
    .orderBy("ano", "uf", "muni", "cnae2")
)

# DEBUG: salva amostra do df pré-aggregação numa tabela diagnostic visível via SQL
# (notebook_output API não expõe prints — então persistimos pra inspeção offline)
df_debug_summary = (df
    .groupBy("ano_int")
    .agg(F.count("*").alias("rows_pos_filtro"),
         F.countDistinct("muni").alias("distinct_munis"),
         F.countDistinct("cnae2").alias("distinct_cnaes"))
    .orderBy("ano_int")
)
(df_debug_summary.write.format("delta").mode("overwrite")
    .saveAsTable(f"{CATALOG}.silver._silver_bem_filter_trace"))
print("✓ trace gravado em silver._silver_bem_filter_trace")
df_debug_summary.show()

n_after_full = df.count()
print(f"  após TODOS filtros (df) : {n_after_full:,}")

n_silver = silver_df.count()
print(f"silver panel rows: {n_silver:,}  (esperado ~1.5-2.5M para 6 anos × 5571 munis × 88 CNAEs)")
if n_silver > 0:
    print(f"distinct munis: {silver_df.select('muni').distinct().count()}")
    print(f"distinct cnae2: {silver_df.select('cnae2').distinct().count()}")
    silver_df.groupBy("ano").agg(F.count("*").alias("cells"), F.sum("n_vinculos_ativos").alias("ativos")).orderBy("ano").show()

# COMMAND ----------

(silver_df.write.format("delta").mode("overwrite")
    .option("overwriteSchema", "true")
    .partitionBy("ano")
    .saveAsTable(SILVER_TABLE))

print(f"✔ {SILVER_TABLE} written")

# COMMAND ----------

# MAGIC %md ## Unity Catalog metadata

# COMMAND ----------

# Table COMMENT — verbose, audit trail completa
spark.sql(f"""
    COMMENT ON TABLE {SILVER_TABLE} IS
    'Mirante · RAIS BEm Panel — silver temática para análise causal do
    Benefício Emergencial de Manutenção do Emprego e da Renda (BEm),
    programa criado pela MP 936/2020 (Lei 14.020/2020) durante COVID-19.

    GRAIN: (municipio_codigo, cnae2, ano), painel desbalanceado.
    JANELA: 2017-2022 (3 anos pré + 2 anos tratamento + 1 ano pós).
    OUTCOMES: vínculos ativos, decomposição de motivo_desligamento (sem justa
    causa, com justa causa, pedido, aposentadoria, morte), massa salarial,
    remuneração mediana/p90, demografia (sexo, escolaridade, idade).

    USO PRIMÁRIO: DiD/TWFE com setor_bem_exposicao (alta/média/baixa) ×
    período (pre/treat/post). Conley HAC clustering (raio 100-200 km)
    recomendado por Finanças do Conselho do Mirante.

    LIMITAÇÕES (declarar em LIMITAÇÕES de qualquer manuscrito):
    1. Granularidade anual do RAIS — apenas 2-3 pontos pre-treatment para
       teste de paralelismo de tendências
    2. Não isola BEm de outros choques COVID simultâneos (Auxílio
       Emergencial, PRONAMPE, lockdowns) — exige variação independente
    3. Sem identificador de trabalhador (CPF não público) — análise é em
       nível de painel município×setor, não individual'
""")

# TAGs de governança Mirante
_tags = {
    "layer":          "silver",
    "domain":         "trabalho",
    "source":         "mte_pdet_rais",
    "pii":            "indirect",
    "grain":          "municipio_cnae_ano",
    "janela":         "2017_2022",
    "questao_causal": "bem_covid_lei_14020",
    "uso_primario":   "did_twfe_paineldesbalanceado",
}
for k, v in _tags.items():
    spark.sql(f"ALTER TABLE {SILVER_TABLE} SET TAGS ('{k}' = '{v}')")

# Column COMMENTs
_col_comments = {
    "muni":                "Código IBGE do município de TRABALHO do vínculo (7 dígitos, '999999' tratado como NULL).",
    "cnae2":               "CNAE 2.0 a 2 dígitos (setor de alta-nível). Pré-2007 fallback CNAE 95.",
    "ano":                 "Ano-base RAIS. PARTITION KEY.",
    "uf":                  "UF derivada de substring(muni, 1, 2) → mapeamento IBGE→sigla.",
    "n_vinculos_total":    "Total de vínculos no ano (admitidos + ativos + desligados).",
    "n_vinculos_ativos":   "Vínculos ativos em 31/12 do ano-base. OUTCOME principal do DiD do BEm.",
    "n_demissoes_sjc":     "Demissões sem justa causa (motivo_desligamento ∈ {10, 11}). Outcome secundário do BEm — programa visava REDUZIR demissões involuntárias.",
    "n_demissoes_cjc":     "Demissões com justa causa (motivo 12). Controle (não afetado por BEm).",
    "n_demissoes_pedido":  "Demissões a pedido do empregado (motivo 60). Comportamento voluntário — placebo útil.",
    "n_aposentadoria":     "Aposentadorias (motivos 20/21).",
    "n_morte":             "Desligamentos por morte (motivo 30). Útil pra detectar excess mortality COVID.",
    "n_demissoes_total":   "Soma de TODOS os desligamentos no ano (qualquer motivo numérico não-zero).",
    "massa_salarial_sm":   "Soma vl_remun_dezembro_sm da célula (em salários-mínimos do ano).",
    "remun_mediana_sm":    "Mediana (p50) da remuneração de dezembro em SM, na célula.",
    "remun_p90_sm":        "P90 da remuneração de dezembro em SM (proxy de cauda alta).",
    "remun_media_sm":      "Média aritmética da remuneração de dezembro em SM.",
    "n_femininos_ativos":  "Vínculos ativos em 31/12 com sexo=feminino. Heterogeneidade BEm — mulheres + setores afetados.",
    "n_masculinos_ativos": "Vínculos ativos em 31/12 com sexo=masculino.",
    "n_baixa_escolaridade": "Vínculos com até ensino médio incompleto (códigos 01-04). Proxy renda baixa, mais vulnerável a choques.",
    "idade_media":         "Idade média na célula. Era1 (pré-2002) usa faixa_etaria categórica → NULL aqui.",
    "te_meses_medio":      "Tempo de emprego médio em meses.",
    "setor_bem_exposicao": "Categoria de exposição ao BEm baseada no CNAE2 — alta (turismo/alimentação/eventos/cultura), média (varejo/transporte/serviços), baixa (indústria pesada, agro, saúde, finanças, tech, gov).",
    "_silver_built_ts":    "Timestamp UTC da construção do silver. Audit trail.",
}

_existing = set(silver_df.columns)
_applied = 0
for col, comment in _col_comments.items():
    if col not in _existing:
        continue
    safe = comment.replace("'", "''")
    spark.sql(f"ALTER TABLE {SILVER_TABLE} ALTER COLUMN `{col}` COMMENT '{safe}'")
    _applied += 1
print(f"✓ {_applied} column COMMENTs aplicados em {SILVER_TABLE}")
print(f"✓ TAGs aplicadas: {list(_tags.keys())}")

# COMMAND ----------

# MAGIC %md ## DQ Gate — sanity checks pós-silver

# COMMAND ----------

print("=== DQ GATE silver_rais_bem_panel ===")

# Check 1: cobertura temporal completa
years_in_silver = [r["ano"] for r in silver_df.select("ano").distinct().orderBy("ano").collect()]
expected_years = list(range(ANO_MIN, ANO_MAX + 1))
missing_years = set(expected_years) - set(years_in_silver)
if missing_years:
    raise RuntimeError(f"DQ FAIL: anos faltantes na silver: {sorted(missing_years)}")
print(f"✓ cobertura temporal: {years_in_silver}")

# Check 2: 27 UFs em cada ano (com tolerância para 1986/SP1986 fora da janela)
uf_per_year = silver_df.groupBy("ano").agg(F.countDistinct("uf").alias("n_uf"))
bad_uf = uf_per_year.filter(F.col("n_uf") < 27).collect()
if bad_uf:
    print(f"⚠ anos com < 27 UFs: {[(r['ano'], r['n_uf']) for r in bad_uf]}")
else:
    print(f"✓ 27 UFs em cada ano")

# Check 3: somatório anual de vínculos ativos plausível (entre 35M e 65M para 2017-2022)
totais = silver_df.groupBy("ano").agg(F.sum("n_vinculos_ativos").alias("ativos")).orderBy("ano").collect()
for r in totais:
    if not (35_000_000 <= r["ativos"] <= 65_000_000):
        print(f"⚠ ano {r['ano']}: total ativos {r['ativos']:,} fora do esperado [35M, 65M]")
    else:
        print(f"  ano {r['ano']}: {r['ativos']:,} ativos ✓")

# Check 4: distribuição de exposição BEm (espera ~10-15% alta, ~20-25% média, restante baixa)
bem_dist = (silver_df.groupBy("setor_bem_exposicao")
    .agg(F.sum("n_vinculos_ativos").alias("ativos"))
    .orderBy(F.desc("ativos")).collect())
total_ativos = sum(r["ativos"] for r in bem_dist)
print("\n=== Distribuição setor_bem_exposicao (média 2017-2022) ===")
for r in bem_dist:
    pct = 100 * r["ativos"] / total_ativos if total_ativos else 0
    print(f"  {r['setor_bem_exposicao']:<6}  {r['ativos']:>14,}  ({pct:>5.1f}%)")

print("\n✓ DQ GATE OK")

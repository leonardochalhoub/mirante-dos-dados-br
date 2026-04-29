# Databricks notebook source
# MAGIC %md
# MAGIC # silver · rais_panel
# MAGIC
# MAGIC Painel **município × CNAE 2-dígitos × ano** ABRANGENTE (1985–2024).
# MAGIC Sucessor de `silver.rais_bem_panel` (originalmente 2017–2022 só p/ BEm DiD).
# MAGIC Expandido em 2026-04-29 a pedido do autor — usar como base ampla para:
# MAGIC
# MAGIC - **Working paper BEm COVID** (filtra ano BETWEEN 2017 AND 2022)
# MAGIC - **Artigo imprensa Cruzado 1986** (filtra ano BETWEEN 1985 AND 1989)
# MAGIC - **Análises de choques macro cross-eras** (Plano Real, recessão Dilma,
# MAGIC   COVID — todos juntos no mesmo painel)
# MAGIC - **Forecasting de vínculos** (séries longas ajudam modelagem)
# MAGIC
# MAGIC ## Cobertura efetiva
# MAGIC
# MAGIC Janela teórica 1985–2024 = 40 anos. Janela efetiva onde CNAE existe = 1995–2024
# MAGIC (30 anos). Pré-1995 (1985–1994) tem `cnae` NULL e é filtrada.
# MAGIC Para análises pré-1995 (ex.: Cruzado), criar silver complementar
# MAGIC `silver.rais_panel_ibge` usando `ibge_subsetor` em vez de cnae2 — ADR futuro.
# MAGIC
# MAGIC ## Janela DiD do BEm (subset)
# MAGIC
# MAGIC Para o working paper BEm COVID, restringir em SQL:
# MAGIC
# MAGIC ```sql
# MAGIC SELECT * FROM mirante_prd.silver.rais_panel
# MAGIC  WHERE ano BETWEEN 2017 AND 2022
# MAGIC ```
# MAGIC
# MAGIC - **Pré-tratamento**: 2017–2019 (parallel trends test)
# MAGIC - **Tratamento**: 2020–2021 (BEm em vigor)
# MAGIC - **Pós-tratamento**: 2022–2024 (recuperação, fim do BEm)
# MAGIC
# MAGIC ## Grain
# MAGIC
# MAGIC `(municipio_codigo, cnae_2_dig, ano)`. ~5571 munis × ~88 CNAE 2-dig × 30 anos
# MAGIC efetivos ≈ 14M linhas teóricas (real ~7-10M com sparse cells).
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
dbutils.widgets.text("ano_min", "1985")
dbutils.widgets.text("ano_max", "2024")

CATALOG = dbutils.widgets.get("catalog")
ANO_MIN = int(dbutils.widgets.get("ano_min"))
ANO_MAX = int(dbutils.widgets.get("ano_max"))
BRONZE_TABLE = f"{CATALOG}.bronze.rais_vinculos"
SILVER_TABLE = f"{CATALOG}.silver.rais_panel"

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

        # Massa salarial e estatísticas SIMPLES de remuneração (em SM).
        # Removido percentile_approx — em 1.94B rows × ~10M groups consome
        # tempo proibitivo em Photon 2X-Small (>97min sem commit observados
        # em 2026-04-29). Quem precisar de mediana/p90 pode derivar em
        # silver_rais_panel_percentiles separado.
        F.sum(F.coalesce(F.col("vl_dez_sm"), F.lit(0.0))).alias("massa_salarial_sm"),
        F.avg("vl_dez_sm").alias("remun_media_sm"),
        F.min("vl_dez_sm").alias("remun_min_sm"),
        F.max("vl_dez_sm").alias("remun_max_sm"),

        # Demografia
        F.sum(F.when((F.col("sexo") == "F") & (F.col("vinc_ativo") == 1), 1).otherwise(0)).cast("long").alias("n_femininos_ativos"),
        F.sum(F.when((F.col("sexo") == "M") & (F.col("vinc_ativo") == 1), 1).otherwise(0)).cast("long").alias("n_masculinos_ativos"),
        F.sum(F.when(F.col("baixa_escol") == 1, 1).otherwise(0)).cast("long").alias("n_baixa_escolaridade"),

        # Características médias
        F.avg("idade").alias("idade_media"),
        F.avg("te_meses").alias("te_meses_medio"),
    )
    .withColumnRenamed("ano_int", "ano")
    # UF derivada do código IBGE do município (primeiros 2 dígitos).
    # F.col("muni") explícito — Spark Connect não auto-resolve str em F.substring.
    # Usamos F.substring (resultado é string) e mapeamos via F.when chain
    # comparando string-to-string, mais robusto que F.create_map (que sofre
    # type mismatch Long-vs-Int em Spark Connect).
    .withColumn("uf_code", F.substring(F.col("muni"), 1, 2))
    .withColumn(
        "uf",
        F.when(F.col("uf_code") == "11", "RO")
         .when(F.col("uf_code") == "12", "AC")
         .when(F.col("uf_code") == "13", "AM")
         .when(F.col("uf_code") == "14", "RR")
         .when(F.col("uf_code") == "15", "PA")
         .when(F.col("uf_code") == "16", "AP")
         .when(F.col("uf_code") == "17", "TO")
         .when(F.col("uf_code") == "21", "MA")
         .when(F.col("uf_code") == "22", "PI")
         .when(F.col("uf_code") == "23", "CE")
         .when(F.col("uf_code") == "24", "RN")
         .when(F.col("uf_code") == "25", "PB")
         .when(F.col("uf_code") == "26", "PE")
         .when(F.col("uf_code") == "27", "AL")
         .when(F.col("uf_code") == "28", "SE")
         .when(F.col("uf_code") == "29", "BA")
         .when(F.col("uf_code") == "31", "MG")
         .when(F.col("uf_code") == "32", "ES")
         .when(F.col("uf_code") == "33", "RJ")
         .when(F.col("uf_code") == "35", "SP")
         .when(F.col("uf_code") == "41", "PR")
         .when(F.col("uf_code") == "42", "SC")
         .when(F.col("uf_code") == "43", "RS")
         .when(F.col("uf_code") == "50", "MS")
         .when(F.col("uf_code") == "51", "MT")
         .when(F.col("uf_code") == "52", "GO")
         .when(F.col("uf_code") == "53", "DF")
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
    'Mirante · RAIS Panel — silver ABRANGENTE 1985-2024 para análises causais,
    descritivas e ML cross-tema do mercado formal brasileiro.

    GRAIN: (municipio_codigo, cnae2, ano), painel desbalanceado, ~7-10M linhas.
    JANELA: 1985-2024 teórica; 1995-2024 efetiva (CNAE não existia pré-1995;
    pré-1995 cells filtradas. Para análise pré-1995 ver silver.rais_panel_ibge
    em ADR futuro).

    OUTCOMES: vínculos ativos, decomposição de motivo_desligamento (sem justa
    causa, com justa causa, pedido, aposentadoria, morte), massa salarial,
    remuneração mediana/p90, demografia (sexo, escolaridade, idade).

    USOS DOCUMENTADOS:
    1. WP BEm COVID (DiD 2017-2022 com setor_bem_exposicao alta/média/baixa)
    2. Artigo imprensa Cruzado 1986 (descritivo 1985-1989, mas com CNAE NULL
       — usar silver.rais_panel_ibge quando criada)
    3. Forecasting de vínculos (séries 30+ anos)
    4. Análises cross-choques (Plano Real 1994, Recessão Dilma 2014-16, COVID)

    LIMITAÇÕES (declarar em manuscritos):
    1. Granularidade anual (estoque 31/12) — DiD precisa janela maior pra
       parallel trends. CAGED tem mensalidade pra refinamento.
    2. Não isola tratamentos simultâneos em janelas com múltiplos choques
       (ex.: COVID + BEm + AE em 2020). Exige variação independente.
    3. Sem identificador de trabalhador (CPF não público) — análise é em
       nível de painel município×setor, não individual.
    4. CNAE 1.0 (1995-2007) e 2.0 (2008+) coexistem — tabelas de equivalência
       PDET aplicáveis. Pré-1995 sem CNAE.'
""")

# TAGs de governança Mirante
_tags = {
    "layer":          "silver",
    "domain":         "trabalho",
    "source":         "mte_pdet_rais",
    "pii":            "indirect",
    "grain":          "municipio_cnae_ano",
    "janela":         "1985_2024_efetiva_1995_2024",
    "questao_causal": "multi_uso_did_descritivo_ml",
    "uso_primario":   "did_twfe_painel_amplo",
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
    "remun_media_sm":      "Média aritmética da remuneração de dezembro em SM.",
    "remun_min_sm":        "Mínima da remuneração de dezembro na célula.",
    "remun_max_sm":        "Máxima da remuneração de dezembro na célula.",
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

print("=== DQ GATE silver_rais_panel ===")

# Check 1: cobertura temporal — 1995-2024 (CNAE não existia pré-1995)
years_in_silver = [r["ano"] for r in silver_df.select("ano").distinct().orderBy("ano").collect()]
print(f"  anos no silver: {years_in_silver}")
expected_min_year = 1995  # Antes disso CNAE não existe → cells filtradas
missing_post_1995 = set(range(expected_min_year, ANO_MAX + 1)) - set(years_in_silver)
if missing_post_1995:
    raise RuntimeError(f"DQ FAIL: anos faltantes pós-{expected_min_year}: {sorted(missing_post_1995)}")
print(f"✓ cobertura temporal pós-{expected_min_year}: completa ({len([y for y in years_in_silver if y >= expected_min_year])} anos)")

# Check 2: 27 UFs por ano (tolerância pra 1985-1986 com gaps de fonte: MA1985, PA1986, SP1986)
uf_per_year = silver_df.groupBy("ano").agg(F.countDistinct("uf").alias("n_uf")).orderBy("ano").collect()
bad_uf = [(r["ano"], r["n_uf"]) for r in uf_per_year if r["n_uf"] < 25]
if bad_uf:
    print(f"⚠ anos com < 25 UFs (esperado em 1985-1987 por TO ainda não existir): {bad_uf}")
else:
    print(f"✓ todos anos com >= 25 UFs (TO criado em 1988, esperado 25-27 cross-1985-2024)")

# Check 3: somatório anual de vínculos ativos plausível
# Range: ~14M em 1986 (Cruzado) → ~58M em 2024
totais = silver_df.groupBy("ano").agg(F.sum("n_vinculos_ativos").alias("ativos")).orderBy("ano").collect()
for r in totais:
    if not (10_000_000 <= r["ativos"] <= 70_000_000):
        print(f"⚠ ano {r['ano']}: total ativos {r['ativos']:,} fora do esperado [10M, 70M]")

# Check 4: distribuição de exposição BEm (essa categorização vale só pra recente,
# mas a coluna é informativa cross-anos pra contextualizar)
bem_dist = (silver_df
    .filter(F.col("ano") >= 2017)  # exposição BEm só faz sentido pós-Reforma 2017
    .groupBy("setor_bem_exposicao")
    .agg(F.sum("n_vinculos_ativos").alias("ativos"))
    .orderBy(F.desc("ativos")).collect())
total_ativos = sum(r["ativos"] for r in bem_dist)
print("\n=== Distribuição setor_bem_exposicao (média 2017-2024) ===")
for r in bem_dist:
    pct = 100 * r["ativos"] / total_ativos if total_ativos else 0
    print(f"  {r['setor_bem_exposicao']:<6}  {r['ativos']:>14,}  ({pct:>5.1f}%)")

print("\n✓ DQ GATE OK")

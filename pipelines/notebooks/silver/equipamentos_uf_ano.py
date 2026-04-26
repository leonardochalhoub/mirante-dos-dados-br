# Databricks notebook source
# MAGIC %md
# MAGIC # silver · equipamentos_uf_ano
# MAGIC
# MAGIC Lê `<catalog>.bronze.cnes_equipamentos`, agrega TODOS os equipamentos por
# MAGIC `(estado, ano, tipequip, codequip)` com split de setor (SUS / Privado / Total).
# MAGIC Junta com `silver.populacao_uf_ano` (dim compartilhada) pra completar grid.
# MAGIC
# MAGIC ## Por que `tipequip` é obrigatório
# MAGIC
# MAGIC O DBF de origem (`/dissemin/publicos/CNES/200508_/Dados/EQ/EQ<UF><YYMM>.dbc`)
# MAGIC carrega DUAS chaves de equipamento:
# MAGIC
# MAGIC - `TIPEQUIP CHAR(1)` — categoria (1=Imagem, 2=Infra, 3=Ópticos,
# MAGIC   4=Gráficos, 5=Manutenção da Vida, 6=Outros, 7=Odontologia,
# MAGIC   8=Audiologia, 9=Telemedicina)
# MAGIC - `CODEQUIP CHAR(2)` — código DENTRO da categoria (não é namespace global)
# MAGIC
# MAGIC As 8 categorias REUSAM a faixa numérica `01–99`. Sem `tipequip`,
# MAGIC `CODEQUIP=42` colapsa Eletroencefalógrafo (Cat 4) com qualquer outro
# MAGIC item registrado nessa posição em outras categorias. Versões anteriores
# MAGIC dessa silver descartavam `tipequip` e produziam um colapso silencioso
# MAGIC (descoberto e documentado no Working Paper #7 — Mirante).
# MAGIC
# MAGIC ## Schema
# MAGIC ```
# MAGIC estado, ano, tipequip, codequip, equipment_key, equipment_name,
# MAGIC equipment_category, populacao,
# MAGIC cnes_count, total_avg, per_capita_scaled,
# MAGIC sus_cnes_count, sus_total_avg, sus_per_capita_scaled,
# MAGIC priv_cnes_count, priv_total_avg, priv_per_capita_scaled,
# MAGIC per_capita_scale_pow10
# MAGIC ```
# MAGIC
# MAGIC `equipment_key` é a string composta `"<tipequip>:<codequip>"` (ex. `"1:12"`
# MAGIC para Ressonância Magnética). Use essa chave no front em vez de só `codequip`.

# COMMAND ----------

dbutils.widgets.text("catalog", "mirante_prd")
CATALOG = dbutils.widgets.get("catalog")

BRONZE_TABLE     = f"{CATALOG}.bronze.cnes_equipamentos"
SILVER_POPULACAO = f"{CATALOG}.silver.populacao_uf_ano"
SILVER_TABLE     = f"{CATALOG}.silver.equipamentos_uf_ano"

PER_CAPITA_SCALE_POW10 = 6   # = "equipamentos por milhão de hab."

print(f"bronze={BRONZE_TABLE}  silver={SILVER_TABLE}")

# COMMAND ----------

# DICIONÁRIO CANÔNICO (TIPEQUIP, CODEQUIP) → nome do equipamento.
#
# Fonte: SCNES Manual Técnico (versão 2 / out 2006) cruzado com o catálogo
# de equipamentos do CnesWeb (cnes2.datasus.gov.br/Mod_Ind_Equipamento.asp).
# Validado contra o snapshot Dez/2024 dos 27 UFs (1.123.809 linhas) — todas
# as 111 combinações observadas no snapshot estão no dicionário.
#
# Padrão Mirante: este dicionário é o "vocabulário controlado" da camada
# silver. Combinações ausentes do dicionário aparecem como
# "Cód. <tip>.<cod> (não mapeado)" — sinal pra revisar quando aparecer.
EQUIPMENT_NAMES = {
    # ── TIPEQUIP=1 — Diagnóstico por Imagem ─────────────────────────────
    ("1","01"): "Gama Câmara",
    ("1","02"): "Mamógrafo com Comando Simples",
    ("1","03"): "Mamógrafo com Estereotaxia",
    ("1","04"): "Raio X até 100 mA",
    ("1","05"): "Raio X de 100 a 500 mA",
    ("1","06"): "Raio X mais de 500 mA",
    ("1","07"): "Raio X Odontológico",
    ("1","08"): "Raio X com Fluoroscopia",
    ("1","09"): "Raio X para Densitometria Óssea",
    ("1","10"): "Raio X para Hemodinâmica",
    ("1","11"): "Tomógrafo Computadorizado",
    ("1","12"): "Ressonância Magnética",
    ("1","13"): "Ultrassom Doppler Colorido",
    ("1","14"): "Ultrassom Ecógrafo",
    ("1","15"): "Ultrassom Convencional",
    ("1","16"): "Processadora de Filme Exclusiva para Mamografia",
    ("1","17"): "Mamógrafo Digital",
    ("1","18"): "PET/CT",
    ("1","19"): "Mamógrafo com Tomossíntese",
    ("1","20"): "Raio X Analógico",
    ("1","21"): "Raio X Digital",
    ("1","22"): "Raio X Telecomandado",
    ("1","23"): "Raio X Móvel",
    ("1","24"): "Arco Cirúrgico",
    ("1","25"): "Raio X Panorâmico",
    ("1","26"): "Tomógrafo Computadorizado 4 Canais",
    ("1","27"): "Tomógrafo Computadorizado 16 Canais",
    ("1","28"): "Tomógrafo Computadorizado 32 Canais",
    ("1","29"): "Tomógrafo Computadorizado 64 Canais",
    ("1","30"): "Tomógrafo Computadorizado 128 Canais",
    ("1","31"): "Tomógrafo Simulador para Radioterapia",
    ("1","32"): "Ressonância Magnética 0,5 T",
    ("1","33"): "Ressonância Magnética 1,5 T",
    ("1","34"): "Ressonância Magnética 3 T",
    ("1","35"): "Ressonância Magnética de Campo Aberto",

    # ── TIPEQUIP=2 — Infraestrutura ─────────────────────────────────────
    ("2","19"): "Ar Condicionado",
    ("2","20"): "Câmara Frigorífica",
    ("2","21"): "Controle Ambiental / Ar-condicionado Central",
    ("2","22"): "Grupo Gerador",
    ("2","23"): "Usina de Oxigênio",
    ("2","24"): "Câmara para Conservação de Hemoderivados / Imuno / Termolábeis",
    ("2","25"): "Câmara para Conservação de Imunobiológicos",
    ("2","26"): "Condensador",
    ("2","27"): "Freezer Científico",
    ("2","28"): "Grupo Gerador (101 a 300 KVA)",
    ("2","29"): "Grupo Gerador (8 a 100 KVA)",
    ("2","30"): "Grupo Gerador (acima de 300 KVA)",
    ("2","43"): "Grupo Gerador de 1.500 KVA (mínimo)",
    ("2","65"): "Grupo Gerador Portátil (até 7 KVA)",
    ("2","66"): "Refrigerador",

    # ── TIPEQUIP=3 — Métodos Ópticos ────────────────────────────────────
    ("3","31"): "Endoscópio das Vias Respiratórias",
    ("3","32"): "Endoscópio das Vias Urinárias",
    ("3","33"): "Endoscópio Digestivo",
    ("3","34"): "Equipamentos para Optometria",
    ("3","35"): "Laparoscópio / Vídeo",
    ("3","36"): "Microscópio Cirúrgico",
    ("3","37"): "Cadeira Oftalmológica",
    ("3","38"): "Coluna Oftalmológica",
    ("3","39"): "Refrator",
    ("3","40"): "Lensômetro",
    ("3","44"): "Projetor ou Tabela de Optotipos",
    ("3","45"): "Retinoscópio",
    ("3","46"): "Oftalmoscópio",
    ("3","47"): "Ceratômetro",
    ("3","48"): "Tonômetro de Aplanação",
    ("3","49"): "Biomicroscópio (Lâmpada de Fenda)",
    ("3","50"): "Campímetro",
    ("3","51"): "Histeroscópio",

    # ── TIPEQUIP=4 — Métodos Gráficos ───────────────────────────────────
    ("4","41"): "Eletrocardiógrafo",
    ("4","42"): "Eletroencefalógrafo",

    # ── TIPEQUIP=5 — Manutenção da Vida ─────────────────────────────────
    ("5","51"): "Bomba / Balão Intra-Aórtico",
    ("5","52"): "Bomba de Infusão",
    ("5","53"): "Berço Aquecido",
    ("5","54"): "Bilirrubinômetro",
    ("5","55"): "Debitômetro",
    ("5","56"): "Desfibrilador",
    ("5","57"): "Equipamento de Fototerapia",
    ("5","58"): "Incubadora",
    ("5","59"): "Marcapasso Temporário",
    ("5","60"): "Monitor de ECG",
    ("5","61"): "Monitor de Pressão Invasivo",
    ("5","62"): "Monitor de Pressão Não-Invasivo",
    ("5","63"): "Reanimador Pulmonar / AMBU",
    ("5","64"): "Respirador / Ventilador",
    ("5","65"): "Monitor Multiparâmetro",

    # ── TIPEQUIP=6 — Outros Equipamentos ────────────────────────────────
    ("6","67"): "Caminhão Baú Refrigerado",
    ("6","68"): "Embarcação para Transporte com Motor de Popa (até 12 pessoas)",
    ("6","69"): "Empilhadeira",
    ("6","70"): "Veículo Utilitário (tipo Furgão)",
    ("6","71"): "Aparelho de Diatermia por Ultrassom / Ondas Curtas",
    ("6","72"): "Aparelho de Eletroestimulação",
    ("6","73"): "Bomba de Infusão de Hemoderivados",
    ("6","74"): "Equipamentos de Aférese",
    ("6","76"): "Equipamento de Circulação Extracorpórea",
    ("6","77"): "Equipamento para Hemodiálise",
    ("6","78"): "Forno de Bier",
    ("6","79"): "Veículo Pick-up Cabine Dupla 4x4 (Diesel)",

    # ── TIPEQUIP=7 — Odontologia ────────────────────────────────────────
    ("7","80"): "Equipo Odontológico",
    ("7","81"): "Compressor Odontológico",
    ("7","82"): "Fotopolimerizador",
    ("7","83"): "Caneta de Alta Rotação",
    ("7","84"): "Caneta de Baixa Rotação",
    ("7","85"): "Amalgamador",
    ("7","86"): "Aparelho de Profilaxia c/ Jato de Bicarbonato",

    # ── TIPEQUIP=8 — Audiologia ─────────────────────────────────────────
    ("8","87"): "Emissões Otoacústicas Evocadas Transientes",
    ("8","88"): "Emissões Otoacústicas Evocadas por Produto de Distorção",
    ("8","89"): "Potencial Evocado Auditivo de Tronco Encefálico Automático",
    ("8","90"): "Pot. Evocado Aud. Tronco Encef. de Curta, Média e Longa Latência",
    ("8","91"): "Audiômetro de Um Canal",
    ("8","92"): "Audiômetro de Dois Canais",
    ("8","93"): "Imitanciômetro",
    ("8","94"): "Imitanciômetro Multifrequencial",
    ("8","95"): "Cabine Acústica",
    ("8","96"): "Sistema de Campo Livre",
    ("8","97"): "Sistema Completo de Reforço Visual (VRA)",
    ("8","98"): "Ganho de Inserção",
    ("8","99"): "HI-PRO",

    # ── TIPEQUIP=9 — Telemedicina ───────────────────────────────────────
    ("9","01"): "Câmera para Reconhecimento Facial",
    ("9","02"): "Carrinho de Telemedicina de Videoconferência",
    ("9","03"): "Condensador (Telemedicina)",
    ("9","04"): "Dermatoscópio",
    ("9","05"): "Detector Fetal Portátil",
    ("9","06"): "Kit Dermatoscopia",
    ("9","07"): "Kit Médico de Diagnóstico Audiológico (TAB)",
    ("9","08"): "Mesa Digitalizadora",
    ("9","09"): "Monitor Sinais Vitais Multifuncional Portátil (Telemedicina)",
    ("9","10"): "Retinógrafo Portátil",
    ("9","11"): "Ultrassom Portátil",
    ("9","12"): "Eletrocardiograma (Telemedicina)",

    # ── TIPEQUIP=10 — Diálise ──────────────────────────────────────────
    ("10","01"): "Aparelho de Hemodiálise — Ambulatorial",
    ("10","02"): "Aparelho de Hemodiálise — Hospitalar",
    ("10","03"): "Aparelho de Hemodiálise Reserva",
    ("10","04"): "Aparelho para Diálise Peritoneal",
}

CATEGORY_NAMES = {
    "1":  "Diagnóstico por Imagem",
    "2":  "Infraestrutura",
    "3":  "Métodos Ópticos",
    "4":  "Métodos Gráficos",
    "5":  "Manutenção da Vida",
    "6":  "Outros Equipamentos",
    "7":  "Odontologia",
    "8":  "Audiologia",
    "9":  "Telemedicina",
    "10": "Diálise",
}

# COMMAND ----------

from pyspark.sql import functions as F

# Read bronze + DEDUPLICATE por source_file (= nome do DBC).
#
# Cada arquivo EQ<UF><YYMM>.dbc é convertido pra um único parquet com nome
# determinístico. Cada parquet representa o snapshot de equipamentos de
# (UF, ano, mes) — não há razão pra ter rows duplicadas do mesmo source_file.
#
# MAS: bronze pode ter rows duplicadas se foi ingerido múltiplas vezes
# (ex.: batch overwrite inicial + auto loader stream rodando depois).
# Nesse caso o `_source_file` (path do parquet) pode aparecer com prefixos
# diferentes (`/Volumes/...` vs `dbfs:/Volumes/...`) embora aponte pro mesmo
# arquivo físico. Por isso dedup deve ser feito por `source_file` (a coluna
# adicionada no convert_one() da bronze, contém o nome do DBC, ex.
# "EQSP2412.dbc") combinado com `_ingest_ts` mais recente.
#
# Comparação com o fix do silver UroPro (commit fa869cf): UroPro lê todo
# bronze sem filtro porque NÃO tinha ingestão dupla. Equipamentos precisa
# do dedup explícito.
bronze = spark.read.table(BRONZE_TABLE)
if bronze.head(1) == []:
    raise ValueError(f"{BRONZE_TABLE} is empty.")

print(f"bronze rows brutos: {bronze.count():,}")

ts_per_file = bronze.groupBy("source_file").agg(F.max("_ingest_ts").alias("_latest_ts"))
src = (
    bronze
    .join(ts_per_file, on="source_file", how="inner")
    .where(F.col("_ingest_ts") == F.col("_latest_ts"))
    .drop("_latest_ts")
)
print(f"bronze rows após dedup por (source_file, latest _ingest_ts): {src.count():,}")
print(f"bronze UFs distintas: {src.select('estado').distinct().count()}")

# Normalize types — KEEP both TIPEQUIP and CODEQUIP (composite key).
# IND_SUS=='1' significa equipamento à disposição do SUS (sector split).
#
# IMPORTANTE: bronze pode ter TIPEQUIP em DOIS formatos por causa de
# conversões DBC→parquet diferentes ('1' single-char OU '01' zero-padded).
# Forma canônica: TIPEQUIP sem zeros à esquerda (CHAR(1) per spec DATASUS),
# CODEQUIP com 2 chars zero-padded (CHAR(2) per spec). Isso garante 1
# representação por equipamento.
df = (
    src.select(
        F.col("estado").cast("string"),
        F.col("ano").cast("int"),
        F.col("mes").cast("string"),
        F.col("CNES").cast("string").alias("cnes"),
        # TIPEQUIP: cast to int then to string strips leading zeros ("01"→"1", "5"→"5")
        F.col("TIPEQUIP").cast("int").cast("string").alias("tipequip"),
        # CODEQUIP: lpad to 2 chars zero-padded ("1"→"01", "12"→"12")
        F.lpad(F.col("CODEQUIP"), 2, "0").alias("codequip"),
        F.col("QT_EXIST").cast("double").alias("qt_exist"),
        F.col("IND_SUS").cast("string").alias("ind_sus"),
    )
    .where(F.col("qt_exist").isNotNull())
    .where(F.col("tipequip").isNotNull())
    .where(F.col("codequip").isNotNull())
)

# ─── Drop partial years (must have all 12 monthly DBC files ingested) ──────
months_per_year = df.groupBy("ano").agg(F.countDistinct("mes").alias("n_months"))
month_counts = sorted([(r["ano"], r["n_months"]) for r in months_per_year.collect()])
print(f"meses por Ano: {month_counts}")
full_years = [a for a, n in month_counts if n == 12]
dropped    = [a for a, n in month_counts if n != 12]
print(f"anos completos: {full_years}")
if dropped:
    print(f"⚠ anos parciais descartados: {dropped}")
df = df.where(F.col("ano").isin(full_years))

print("Top 10 (tipequip, codequip) combos by row count:")
df.groupBy("tipequip", "codequip").count().orderBy(F.desc("count")).show(10)

# COMMAND ----------

# MAGIC %md
# MAGIC ## Compute monthly + sector annual averages PER (TIPEQUIP, CODEQUIP)

# COMMAND ----------

GROUP_KEYS = ["estado", "ano", "tipequip", "codequip"]

# ─── DEDUP per (CNES, mês) — fix do double-count crítico ────────────────────
#
# Bug histórico (pré-2026-04): `total_avg` era calculado como `sus_total_avg
# + priv_total_avg` (vide commit `d3b21c6` revertido nesta refatoração). O
# resultado nacional para Ressonância Magnética (equipment_key='1:12') em
# 2025 era 7.592 unidades — aproximadamente 35,6/Mhab, ~2× a mediana OCDE
# (~17/Mhab). O sintoma era de double-counting.
#
# Causa raiz: o CNES permite que um mesmo equipamento físico apareça em
# DUAS linhas no mesmo (CNES, mês) — uma com `IND_SUS=1` (declarando
# disponibilidade para o SUS) e outra com `IND_SUS=0` (declarando
# disponibilidade para uso privado). Somar essas duas linhas double-conta a
# máquina física quando ela é "dual-flagged".
#
# Fix: pivotar IND_SUS em duas colunas por (CNES, mês), e tomar
# `qt_total = GREATEST(qt_sus, qt_priv)` como o número físico canônico.
# Conservador: assume que dual-flag representa a MESMA máquina disponível
# para ambos os setores (interpretação compatível com a banda OECD), não
# duas máquinas físicas.
#
# Invariante pós-fix: `sus_total_avg + priv_total_avg ≥ total_avg`, com
# igualdade quando não há dual-flag. As "shares" (sus/total, priv/total)
# podem ULTRAPASSAR 100% combinadas — isso é matematicamente correto: uma
# máquina dual-flagged é 100% disponível ao SUS E 100% disponível ao
# privado simultaneamente.
per_cnes_mes = (
    df.groupBy(GROUP_KEYS + ["cnes", "mes"])
      .agg(
          F.sum(F.when(F.col("ind_sus") == F.lit("1"), F.col("qt_exist"))
                 .otherwise(F.lit(0.0))).alias("qt_sus"),
          F.sum(F.when(F.col("ind_sus") == F.lit("0"), F.col("qt_exist"))
                 .otherwise(F.lit(0.0))).alias("qt_priv"),
      )
      .withColumn("qt_total", F.greatest(F.col("qt_sus"), F.col("qt_priv")))
)

# Active months per (CNES, key) — shared denominator (only counts months
# em que o CNES declarou pelo menos 1 unidade do equipamento)
cnes_month_count = (
    per_cnes_mes.where(F.col("qt_total") > 0)
                .groupBy(GROUP_KEYS + ["cnes"])
                .agg(F.count("mes").alias("n_months"))
)

# Annual averages per CNES (deduped — total = max(sus, priv) por mês)
cnes_year = (
    per_cnes_mes.groupBy(GROUP_KEYS + ["cnes"])
                .agg(
                    F.sum("qt_total").alias("sum_total"),
                    F.sum("qt_sus").alias("sum_sus"),
                    F.sum("qt_priv").alias("sum_priv"),
                )
                .join(cnes_month_count, on=GROUP_KEYS + ["cnes"], how="left")
                .withColumn("avg_year_total", F.col("sum_total") / F.col("n_months"))
                .withColumn("avg_year_sus",   F.col("sum_sus")   / F.col("n_months"))
                .withColumn("avg_year_priv",  F.col("sum_priv")  / F.col("n_months"))
                .where(F.col("avg_year_total").isNotNull() & (F.col("avg_year_total") > 0))
)

# COMMAND ----------

# State-year-(tipequip,codequip) aggregates — dedup-aware
agg_total = (
    cnes_year.groupBy(GROUP_KEYS).agg(
        F.countDistinct("cnes").cast("long").alias("cnes_count"),
        F.sum("avg_year_total").alias("total_avg"),
        # CNES com pelo menos 1 unidade declarada como SUS-disponível no ano
        F.countDistinct(F.when(F.col("avg_year_sus") > 0, F.col("cnes"))).cast("long").alias("sus_cnes_count"),
        # CNES com pelo menos 1 unidade declarada como Priv-disponível no ano
        F.countDistinct(F.when(F.col("avg_year_priv") > 0, F.col("cnes"))).cast("long").alias("priv_cnes_count"),
        F.sum("avg_year_sus").alias("sus_total_avg"),
        F.sum("avg_year_priv").alias("priv_total_avg"),
    )
)

# COMMAND ----------

# MAGIC %md
# MAGIC ## Cartesian (estado × ano × (tipequip,codequip)) ⨯ populacao

# COMMAND ----------

df_pop = (
    spark.read.table(SILVER_POPULACAO)
         .select(
             F.col("uf").cast("string").alias("estado"),
             F.col("Ano").cast("int").alias("ano"),
             F.col("populacao").cast("long").alias("populacao"),
         )
)

equip_keys = cnes_year.select("tipequip", "codequip").distinct()
print(f"Distinct (tipequip, codequip) combos in bronze: {equip_keys.count()}")

grid = df_pop.crossJoin(equip_keys)

fill_zeros = {
    "cnes_count":      0, "total_avg":      0.0,
    "sus_cnes_count":  0, "sus_total_avg":  0.0,
    "priv_cnes_count": 0, "priv_total_avg": 0.0,
}
df_out = (
    grid
    .join(agg_total, on=GROUP_KEYS, how="left")
    .fillna(fill_zeros)
)
# `total_avg` agora vem direto do agg_total (deduped MAX-per-CNES-mês),
# NÃO mais como `sus_total_avg + priv_total_avg` (que double-contava
# máquinas dual-flagged). Vide bloco de docstring acima sobre o fix.

scale = F.pow(F.lit(10.0), F.lit(PER_CAPITA_SCALE_POW10).cast("double"))
pop = F.col("populacao")
def per_capita_scaled(c):
    return F.when(pop.isNull() | (pop == 0), F.lit(0.0)).otherwise(F.col(c) / pop * scale)

df_out = (
    df_out
    .withColumn("per_capita_scaled",      per_capita_scaled("total_avg"))
    .withColumn("sus_per_capita_scaled",  per_capita_scaled("sus_total_avg"))
    .withColumn("priv_per_capita_scaled", per_capita_scaled("priv_total_avg"))
    .withColumn("per_capita_scale_pow10", F.lit(PER_CAPITA_SCALE_POW10).cast("int"))
)

# Composite equipment_key
df_out = df_out.withColumn(
    "equipment_key",
    F.concat(F.col("tipequip"), F.lit(":"), F.col("codequip")),
)

# Lookup canonical name via join on a tiny in-memory DataFrame.
# Mais robusto que CASE WHEN encadeado de 129 entradas (que vira árvore
# enorme no Catalyst e pode estourar limite de profundidade de expressão).
name_rows = [(t, c, nm) for (t, c), nm in EQUIPMENT_NAMES.items()]
df_names = spark.createDataFrame(name_rows, ["tipequip", "codequip", "_canonical_name"])
df_out = (
    df_out
    .join(df_names, on=["tipequip", "codequip"], how="left")
    .withColumn(
        "equipment_name",
        F.coalesce(
            F.col("_canonical_name"),
            F.concat(F.lit("Cód. "), F.col("tipequip"), F.lit("."),
                     F.col("codequip"), F.lit(" (não mapeado)")),
        ),
    )
    .drop("_canonical_name")
)

cat_rows = [(k, v) for k, v in CATEGORY_NAMES.items()]
df_cats = spark.createDataFrame(cat_rows, ["tipequip", "_category_name"])
df_out = (
    df_out
    .join(df_cats, on="tipequip", how="left")
    .withColumn(
        "equipment_category",
        F.coalesce(F.col("_category_name"), F.concat(F.lit("Cat. "), F.col("tipequip"))),
    )
    .drop("_category_name")
)

# Drop rows with no equipment data at all (avoids cartesian bloat)
df_out = df_out.where((F.col("cnes_count") > 0) | (F.col("sus_cnes_count") > 0) | (F.col("priv_cnes_count") > 0))

silver_df = df_out.select(
    "estado", "ano", "tipequip", "codequip",
    "equipment_key", "equipment_name", "equipment_category",
    "cnes_count",     "total_avg",     "per_capita_scaled",
    "sus_cnes_count", "sus_total_avg", "sus_per_capita_scaled",
    "priv_cnes_count","priv_total_avg","priv_per_capita_scaled",
    "populacao", "per_capita_scale_pow10",
).withColumn("_silver_built_ts", F.current_timestamp()).orderBy(
    "estado", "ano", "tipequip", "codequip",
)

# COMMAND ----------

n = silver_df.count()
ufs = silver_df.select("estado").distinct().count()
n_years = silver_df.select("ano").distinct().count()
combos = silver_df.select("equipment_key").distinct().count()
print(f"rows={n}  ufs={ufs}  years={n_years}  (tipequip,codequip)_combos={combos}")
assert ufs == 27, f"Expected 27 UFs, got {ufs}"

# DQ: validar que RM (1:12) cai dentro da banda OECD (~10-25 unidades por
# milhão de habitantes). Pré-dedup, esse total era ~7,6k em 2025 (35,6/Mhab,
# ~2× a mediana OECD) — sintoma do double-count via dual-flag. Pós-dedup
# espera-se algo em torno de 3,5-4,5k unidades nacionais (15-20/Mhab),
# compatível com a literatura.
last_year = silver_df.agg(F.max("ano").alias("y")).first()["y"]
rm_row = (
    silver_df.where((F.col("ano") == last_year) & (F.col("equipment_key") == "1:12"))
             .agg(
                 F.sum("total_avg").alias("rm_total"),
                 F.sum("sus_total_avg").alias("rm_sus"),
                 F.sum("priv_total_avg").alias("rm_priv"),
                 F.sum("populacao").alias("pop_br"),
             ).first()
)
rm_total = rm_row["rm_total"] or 0
rm_sus   = rm_row["rm_sus"]   or 0
rm_priv  = rm_row["rm_priv"]  or 0
pop_br   = rm_row["pop_br"]   or 0
per_M    = (rm_total / pop_br * 1_000_000) if pop_br else 0
print(f"DQ check — Brasil RM (1:12) ano {last_year}:")
print(f"  total = {rm_total:,.0f} unidades  ({per_M:.1f}/Mhab — esperado OCDE 10-25)")
print(f"  sus   = {rm_sus:,.0f}    priv = {rm_priv:,.0f}    ")
print(f"  sus + priv = {rm_sus + rm_priv:,.0f}  (≥ total quando há dual-flag)")
overlap_pct = ((rm_sus + rm_priv - rm_total) / rm_total * 100) if rm_total else 0
print(f"  overlap (dual-flagged) ≈ {overlap_pct:.1f}% do total")
# Soft-assert: avisa se a magnitude está fora do esperado, mas não derruba o job
if rm_total > 0 and (per_M < 8 or per_M > 30):
    print(f"⚠ DQ WARN: RM/Mhab = {per_M:.1f} fora da banda 8–30. Investigue dual-flag, "
          f"cobertura CNES ou catálogo de TIPEQUIPs.")

# ─── DQ side-by-side: comparação do total deduped (este silver) com a
# abordagem alternativa "AVG por (CNES, ano), SUM por UF" — método mais
# simples mas que ignora o IND_SUS. Ambas devem cair na banda OCDE; a
# diferença empírica entre elas mede o quanto a interpretação dual-flag
# (MAX vs proporção via AVG) afeta o número. Útil pra decidir se vale
# manter a complexidade do dedup explícito ou voltar pra abordagem simples.
alt_avg_per_cnes = (
    df.where((F.col("ano") == last_year) & (F.col("tipequip") == "1") & (F.col("codequip") == "12"))
      .groupBy("cnes", "estado")
      .agg(F.avg("qt_exist").alias("avg_qt"))
)
alt_total = alt_avg_per_cnes.agg(F.sum("avg_qt").alias("t")).first()["t"] or 0
alt_per_M = (alt_total / pop_br * 1_000_000) if pop_br else 0
delta_pct = ((rm_total - alt_total) / alt_total * 100) if alt_total else 0
print(f"  --- comparação metodológica (RM nacional {last_year}) ---")
print(f"  abordagem A (este silver — MAX por CNES-mês):    {rm_total:,.0f}  ({per_M:.1f}/Mhab)")
print(f"  abordagem B (AVG(qt_exist) por (CNES, ano), SUM): {alt_total:,.0f}  ({alt_per_M:.1f}/Mhab)")
print(f"  Δ A vs B: {delta_pct:+.1f}%  (positivo = A maior; negativo = B maior)")

# Log unmapped (tipequip, codequip) combos — sinal pra expandir o dicionário canônico.
unmapped = (
    silver_df.where(F.col("equipment_name").contains("(não mapeado)"))
             .groupBy("tipequip", "codequip")
             .agg(F.sum("total_avg").alias("total"))
             .orderBy(F.desc("total"))
             .limit(40)
             .collect()
)
if unmapped:
    print(f"\n⚠ {len(unmapped)} combos não mapeados (top 40 por volume) — adicionar ao dicionário canônico:")
    for r in unmapped:
        print(f"   ({r['tipequip']!r}, {r['codequip']!r}): total_avg={r['total']:.0f}")
else:
    print("✔ todos os combos mapeados")

print("✔ DQ passed")

(
    silver_df.write.format("delta")
        .mode("overwrite")
        .option("overwriteSchema", "true")
        .partitionBy("ano")
        .saveAsTable(SILVER_TABLE)
)
# Inline minimal COMMENT — full enrichment via _meta/apply_catalog_metadata.py.
spark.sql(f"COMMENT ON TABLE {SILVER_TABLE} IS "
          f"'Mirante · Equipamentos CNES por UF × Ano × (TIPEQUIP, CODEQUIP) — "
          f"split SUS/Privado via IND_SUS, com nomes canônicos DATASUS. "
          f"Composite key equipment_key=TIPEQUIP:CODEQUIP é OBRIGATÓRIA "
          f"(fix WP#4-v1: CODEQUIP=42 sozinho colapsava Eletroencefalógrafo "
          f"com Ressonância Magnética). FIX DEDUP (abr/2026): total_avg agora "
          f"vem de GREATEST(qt_sus, qt_priv) por (CNES, mês), em vez de "
          f"sus+priv que double-contava máquinas dual-flagged. Invariante: "
          f"sus_total_avg + priv_total_avg >= total_avg (igualdade quando "
          f"sem dual-flag). Reaplicar metadata rico via job_apply_catalog_metadata.'")
print(f"✔ {SILVER_TABLE} written ({n} rows)")

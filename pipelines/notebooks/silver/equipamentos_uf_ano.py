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
}

CATEGORY_NAMES = {
    "1": "Diagnóstico por Imagem",
    "2": "Infraestrutura",
    "3": "Métodos Ópticos",
    "4": "Métodos Gráficos",
    "5": "Manutenção da Vida",
    "6": "Outros Equipamentos",
    "7": "Odontologia",
    "8": "Audiologia",
    "9": "Telemedicina",
}

# COMMAND ----------

from pyspark.sql import functions as F

# Read bronze + DEDUPLICATE por _source_file.
#
# Cada arquivo EQ<UF><YYMM>.dbc é convertido pra um único parquet com nome
# determinístico. Cada parquet representa o snapshot de equipamentos de
# (UF, ano, mes) — não há razão pra ter rows duplicadas do mesmo source_file.
#
# MAS: se o bronze foi ingerido múltiplas vezes (ex.: batch run + auto loader
# stream rodando depois), o mesmo source_file pode aparecer com _ingest_ts
# diferentes. NÃO filtrar (silver original UroPro) → perde UFs por causa
# de micro-batches; filtrar tudo (versão anterior) → duplica os equipamentos.
#
# Solução robusta: pra cada _source_file, manter SÓ as rows do _ingest_ts
# MAIS RECENTE. Se ingestions diferentes do mesmo arquivo derem dados
# diferentes (ex.: DATASUS retroativamente corrigiu o DBC), prevalece a versão
# mais recente.
bronze = spark.read.table(BRONZE_TABLE)
if bronze.head(1) == []:
    raise ValueError(f"{BRONZE_TABLE} is empty.")

print(f"bronze rows brutos: {bronze.count():,}")

ts_per_file = bronze.groupBy("_source_file").agg(F.max("_ingest_ts").alias("_latest_ts"))
src = (
    bronze
    .join(ts_per_file, on="_source_file", how="inner")
    .where(F.col("_ingest_ts") == F.col("_latest_ts"))
    .drop("_latest_ts")
)
print(f"bronze rows após dedup por (_source_file, latest _ingest_ts): {src.count():,}")
print(f"bronze UFs distintas: {src.select('estado').distinct().count()}")

# Normalize types — KEEP both TIPEQUIP and CODEQUIP (composite key).
# IND_SUS=='1' significa equipamento à disposição do SUS (sector split).
df = (
    src.select(
        F.col("estado").cast("string"),
        F.col("ano").cast("int"),
        F.col("mes").cast("string"),
        F.col("CNES").cast("string").alias("cnes"),
        F.col("TIPEQUIP").cast("string").alias("tipequip"),
        F.col("CODEQUIP").cast("string").alias("codequip"),
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

# Monthly totals per (CNES, tipequip, codequip, mes) — sum across sectors
monthly_all = (
    df.groupBy(GROUP_KEYS + ["cnes", "mes"])
      .agg(F.sum("qt_exist").alias("monthly_total"))
)

# Active months per (CNES, tipequip, codequip, year) — shared denominator
cnes_month_count = (
    monthly_all.groupBy(GROUP_KEYS + ["cnes"])
               .agg(F.count("mes").alias("n_months"))
)

# All-sector annual average per CNES per (tipequip, codequip)
cnes_all = (
    monthly_all.groupBy(GROUP_KEYS + ["cnes"])
               .agg(F.avg("monthly_total").alias("avg_year"))
               .where(F.col("avg_year").isNotNull())
)


def sector_year_avg(df_sector):
    sector_sum = (
        df_sector.groupBy(GROUP_KEYS + ["cnes"])
                 .agg(F.sum("qt_exist").alias("sector_sum"))
    )
    return (
        sector_sum
        .join(cnes_month_count, on=GROUP_KEYS + ["cnes"], how="left")
        .withColumn("avg_year", F.col("sector_sum") / F.col("n_months"))
        .where(F.col("avg_year").isNotNull())
        .select(GROUP_KEYS + ["cnes", "avg_year"])
    )


cnes_sus  = sector_year_avg(df.where(F.col("ind_sus") == F.lit("1")))
cnes_priv = sector_year_avg(df.where(F.col("ind_sus") == F.lit("0")))

# COMMAND ----------

# State-year-(tipequip,codequip) aggregates per sector
agg_cnes_count = (
    cnes_all.groupBy(GROUP_KEYS)
            .agg(F.countDistinct("cnes").cast("long").alias("cnes_count"))
)

def agg_sector(df_cnes_sector, prefix: str):
    return df_cnes_sector.groupBy(GROUP_KEYS).agg(
        F.countDistinct("cnes").cast("long").alias(f"{prefix}cnes_count"),
        F.sum("avg_year").alias(f"{prefix}total_avg"),
    )

agg_sus  = agg_sector(cnes_sus,  prefix="sus_")
agg_priv = agg_sector(cnes_priv, prefix="priv_")

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

equip_keys = cnes_all.select("tipequip", "codequip").distinct()
print(f"Distinct (tipequip, codequip) combos in bronze: {equip_keys.count()}")

grid = df_pop.crossJoin(equip_keys)

fill_zeros = {
    "cnes_count": 0,
    "sus_cnes_count": 0,  "sus_total_avg":  0.0,
    "priv_cnes_count": 0, "priv_total_avg": 0.0,
}
df_out = (
    grid
    .join(agg_cnes_count, on=GROUP_KEYS, how="left")
    .join(agg_sus,        on=GROUP_KEYS, how="left")
    .join(agg_priv,       on=GROUP_KEYS, how="left")
    .fillna(fill_zeros)
)

df_out = df_out.withColumn("total_avg", F.col("sus_total_avg") + F.col("priv_total_avg"))

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

# DQ: validar que a RM básica (1:12) bate com magnitude esperada (~3-4K nacional)
last_year = silver_df.agg(F.max("ano").alias("y")).first()["y"]
rm_row = (
    silver_df.where((F.col("ano") == last_year) & (F.col("equipment_key") == "1:12"))
             .agg(F.sum("total_avg").alias("rm_total")).first()
)
rm_total = rm_row["rm_total"] or 0
print(f"DQ check — Brasil RM (1:12) ano {last_year}: ~{rm_total:.0f} unidades (esperado: 3000–4500)")

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
spark.sql(f"COMMENT ON TABLE {SILVER_TABLE} IS "
          f"'Mirante · Equipamentos CNES por UF × Ano × (TIPEQUIP, CODEQUIP), "
          f"com split SUS/Privado. Composite key resolve a ambiguidade pré-WP#6 "
          f"em que CODEQUIP sozinho colapsava 8 categorias.'")
print(f"✔ {SILVER_TABLE} written ({n} rows)")

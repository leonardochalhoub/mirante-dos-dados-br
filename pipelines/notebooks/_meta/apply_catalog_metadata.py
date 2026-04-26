# Databricks notebook source
# MAGIC %md
# MAGIC # _meta · apply_catalog_metadata
# MAGIC
# MAGIC **Single source of truth** for Unity Catalog metadata across the
# MAGIC `mirante_prd` catalog. Applies, idempotently:
# MAGIC
# MAGIC - `COMMENT ON CATALOG` for `mirante_prd`
# MAGIC - `COMMENT ON SCHEMA` for `bronze` / `silver` / `gold`
# MAGIC - `COMMENT ON TABLE` (verbose, multi-paragraph) for every table
# MAGIC - `ALTER TABLE ... ALTER COLUMN ... COMMENT` for every meaningful column
# MAGIC - `ALTER TABLE ... SET TAGS` with a normalized tag vocabulary
# MAGIC   (`layer`, `domain`, `source`, `pii`, `grain`, `refresh_cadence`,
# MAGIC   `partition_keys`, `pk_grain`)
# MAGIC
# MAGIC ## Why this notebook exists
# MAGIC
# MAGIC The pipeline notebooks under `bronze/`, `silver/`, `gold/` already emit a
# MAGIC short `COMMENT ON TABLE` after each `saveAsTable`. Those terse comments
# MAGIC act as a **last-line-of-defense** if this notebook hasn't run yet. The
# MAGIC rich metadata you see in Catalog Explorer / AI-BI Genie / dbt docs / MCP
# MAGIC clients is produced **here** and is the source consumers should rely on.
# MAGIC
# MAGIC Reapply this notebook **after every silver/gold refresh**, or as a
# MAGIC trailing task in each `job_*_refresh` (recommended — see
# MAGIC `pipelines/databricks.yml`). It is fully idempotent: comments are
# MAGIC overwritten, tags are merged.
# MAGIC
# MAGIC ## Standing rule (from `feedback_unity_catalog_metadata.md` in agent memory)
# MAGIC
# MAGIC When a **new** table is added to the catalog, the pipeline notebook that
# MAGIC creates it MUST emit `COMMENT ON TABLE`, `ALTER TABLE … ALTER COLUMN …
# MAGIC COMMENT` and `ALTER TABLE … SET TAGS` immediately after `saveAsTable`,
# MAGIC and the table MUST also be added to this central script for full
# MAGIC enrichment.

# COMMAND ----------

dbutils.widgets.text("catalog", "mirante_prd")
CATALOG = dbutils.widgets.get("catalog")

print(f"Applying Unity Catalog metadata to catalog '{CATALOG}'…")


def _esc(s: str) -> str:
    """Escape single quotes for SQL string literals."""
    return s.replace("'", "''")


def comment_catalog(name: str, body: str) -> None:
    spark.sql(f"COMMENT ON CATALOG {name} IS '{_esc(body.strip())}'")
    print(f"  catalog · {name}")


def comment_schema(fqn: str, body: str) -> None:
    spark.sql(f"COMMENT ON SCHEMA {fqn} IS '{_esc(body.strip())}'")
    print(f"  schema  · {fqn}")


def comment_table(fqn: str, body: str) -> None:
    spark.sql(f"COMMENT ON TABLE {fqn} IS '{_esc(body.strip())}'")


def comment_columns(fqn: str, cols: dict) -> None:
    """Apply per-column comments. Silently skips columns that don't exist
    (e.g. when a bronze schema evolves and the central script is stale)."""
    existing = {f.name for f in spark.read.table(fqn).schema.fields}
    for col, body in cols.items():
        if col not in existing:
            print(f"    ⚠ skip column '{col}' on {fqn} (not present)")
            continue
        spark.sql(
            f"ALTER TABLE {fqn} ALTER COLUMN `{col}` COMMENT '{_esc(body.strip())}'"
        )


def set_tags(fqn: str, tags: dict) -> None:
    pairs = ", ".join(f"'{_esc(k)}' = '{_esc(str(v))}'" for k, v in tags.items())
    spark.sql(f"ALTER TABLE {fqn} SET TAGS ({pairs})")


def enrich(fqn: str, table_comment: str, columns: dict, tags: dict) -> None:
    print(f"  table   · {fqn}")
    comment_table(fqn, table_comment)
    comment_columns(fqn, columns)
    set_tags(fqn, tags)


# Common platform-injected column comments (Auto Loader / pipeline-added)
PLATFORM_COLS = {
    "_ingest_ts":
        "Timestamp em que esta linha entrou na camada bronze via Auto Loader "
        "ou via batch carga inicial (UTC, UDF current_timestamp). Vários "
        "valores distintos de _ingest_ts coexistem na mesma tabela porque "
        "(a) Auto Loader emite micro-batches separados e (b) a tabela é "
        "append-only por design. **NÃO** filtrar por max(_ingest_ts) na "
        "silver: esse foi o bug histórico fa869cf que descartava 73% dos "
        "registros do UroPro silver e ocultava 14 das 27 UFs em silêncio. "
        "Use _source_file como chave de snapshot quando precisar do último "
        "arquivo ingerido.",
    "_source_file":
        "Caminho completo do arquivo de origem dentro do UC Volume "
        "(de _metadata.file_path do Auto Loader). É a chave de snapshot "
        "preferida em silver: orderBy(desc(_ingest_ts), desc(_source_file)) "
        "→ first → filter por igualdade reproduz exatamente UM arquivo, "
        "imune ao split em micro-batches.",
}


# =====================================================================
# CATALOG
# =====================================================================
print("\n=== catalog ===")
comment_catalog(CATALOG, """
Mirante dos Dados — catálogo de produção da plataforma de Big Data público
brasileiro publicada em https://leonardochalhoub.github.io/mirante-dos-dados-br.

Unifica seis verticais sob a mesma arquitetura medalhão (bronze → silver →
gold) em Delta Lake puro (sem DLT, sem materialized views — Delta com
history, time travel, OPTIMIZE, MERGE):

  • Emendas Parlamentares (CGU/Portal da Transparência)
  • Bolsa Família / Auxílio Brasil / Novo Bolsa Família (CGU)
  • UroPro — cirurgia uroginecológica no SUS (DATASUS/SIH-AIH-RD)
  • RAIS — vínculos formais e massa salarial (MTE)
  • Equipamentos hospitalares (DATASUS/CNES)
  • Dimensões compartilhadas: populacao IBGE/SIDRA + IPCA BCB

Princípios:
  - Bronze é STRING-ONLY (sem inferência, sem coerção): preserva a fonte
    em sua forma mais auditável; tipagem acontece no silver.
  - Silver é OVERWRITE batch (Delta time travel preserva snapshots).
  - Gold é OVERWRITE batch a partir de joins entre silvers.
  - One notebook per table; folder = camada, filename = nome da tabela.
  - Cascata garantida pelo DAG do job (depends_on).
  - Idempotência por arquivo via checkpoint do Auto Loader.

Bug histórico documentado: filtro `_ingest_ts == max` na silver
(commit fa869cf, abril/2026) descartava silenciosamente 73% das linhas
bronze e 14 das 27 UFs do UroPro. Toda silver foi reescrita para usar
filtro por _source_file do último arquivo (vide pipelines/notebooks/
silver/populacao_uf_ano.py para o padrão canônico).

Referência teórica: ARMBRUST et al. (2021) Lakehouse: a new generation
of open platforms that unify data warehousing and advanced analytics,
11th CIDR. As regras de tipagem por camada seguem o whitepaper
Databricks 2022 sobre lakehouse data modeling.

Texto e código sob licença CC BY 4.0 / MIT. Mantido por Leonardo
Chalhoub (leonardochalhoub@gmail.com).
""")


# =====================================================================
# SCHEMAS
# =====================================================================
print("\n=== schemas ===")
comment_schema(f"{CATALOG}.bronze", """
Camada BRONZE — landing zone do lakehouse Mirante.

Cada tabela é APPEND-ONLY: cada execução do `job_*_refresh` adiciona um
novo conjunto de linhas correspondente ao snapshot de origem (vetor
`_ingest_ts` + `_source_file`), preservando todo o histórico bruto.

Política de tipagem: STRING-ONLY (sem inferência, sem cast). O dado
chega da forma mais próxima possível da fonte original (CSV/JSON/DBC →
Parquet → Delta) e a tipagem ocorre exclusivamente no silver. Isso
permite (a) reconstituir a origem byte a byte se necessário,
(b) descobrir bugs de coerção depois da publicação, e (c) auditar
disputes de dado público.

Volume associado: /Volumes/<catalog>/bronze/raw/  — landing zone do
Auto Loader. /Volumes/<catalog>/bronze/raw/_autoloader/ guarda
checkpoints e schema-locations (gerenciados; NÃO apagar a menos que
queira reprocessar tudo do zero).

History: cada linha bronze persiste para sempre; use
`_ingest_ts` para reconstituir o que foi visto pelo Mirante em qualquer
ponto do tempo.
""")

comment_schema(f"{CATALOG}.silver", """
Camada SILVER — limpeza, normalização e agregação.

Cada tabela é gerada por um único notebook batch que (a) lê o snapshot
mais recente do bronze (filtrando por `_source_file` do último arquivo,
NUNCA por `_ingest_ts == max` — vide bug fa869cf), (b) aplica casts e
validações de domínio, (c) agrega na chave analítica documentada
(em geral UF × ano × mes × procedimento × caráter × gestão), e
(d) sobrescreve a tabela alvo via `mode("overwrite")` com
`overwriteSchema=true`.

History: Delta time travel preserva snapshots anteriores
(`DESCRIBE HISTORY` / `VERSION AS OF` / `TIMESTAMP AS OF`).
Particionamento usual: `Ano` (silvers de série temporal), `Ano+UF`
quando a cardinalidade favorece.

Lineage: cada silver carrega `_bronze_snapshot_ts` e `_silver_built_ts`
para que consumidores possam responder "que versão do bronze gerou
este silver?" sem precisar de tabela de lineage externa.
""")

comment_schema(f"{CATALOG}.gold", """
Camada GOLD — vista analítica colapsada por (UF × Ano [× procedimento]).

Joins entre silvers de domínio + silvers de dimensão compartilhada
(`silver.populacao_uf_ano`, `silver.ipca_deflators_2021`). É a camada
consumida pelo `front-end` da plataforma (via JSONs exportados em
`/Volumes/<catalog>/gold/exports/`) e por dashboards de auditoria.

Cada gold é OVERWRITE batch após cada silver. Particionamento por
`Ano` quase sempre. Schemas estáveis (mudanças quebram o front).

Indicadores deflacionados (`*_2021`) usam IPCA Dez/2021 como base.
""")


# =====================================================================
# BRONZE TABLES
# =====================================================================
print("\n=== bronze ===")

# ---- bronze.ibge_populacao_raw ----
TBL = f"{CATALOG}.bronze.ibge_populacao_raw"
enrich(
    TBL,
    """
    População residente por UF × Ano — payload bruto da API IBGE/SIDRA
    tabela 6579 (Estimativas anuais da população residente). Cada linha
    é um payload JSON completo do servidor IBGE; o silver
    `silver.populacao_uf_ano` faz o explode `resultados[].series[]` e
    monta o painel UF×Ano com interpolação linear para anos não
    publicados.

    Append-only: cada execução do `job_populacao_refresh` (cron anual,
    Jul 1) adiciona um novo arquivo timestamped no Volume IBGE e o
    Auto Loader emite uma linha aqui. NÃO filtrar por max(_ingest_ts)
    no silver — o snapshot único é definido por `_source_file`.

    Fonte: https://servicodados.ibge.gov.br/api/v3/agregados/6579
    Periodicidade: anual (IBGE publica em Jul/Ago do ano corrente).
    """,
    {
        "resultados":
            "Array JSON do payload IBGE. Cada elemento contém um struct "
            "com `series[]`, e cada série tem `localidade.id` (UF id de "
            "2 dígitos, ex.: 31 = MG) e `serie` (mapa STRING→STRING com "
            "anos como chaves e populações como valores).",
        **PLATFORM_COLS,
    },
    {
        "layer": "bronze",
        "domain": "populacao",
        "source": "ibge_sidra",
        "source_endpoint": "agregados/6579",
        "pii": "false",
        "grain": "payload_per_refresh",
        "refresh_cadence": "anual",
        "ingest_mode": "auto_loader_json",
        "append_only": "true",
    },
)

# ---- bronze.bcb_ipca_raw ----
TBL = f"{CATALOG}.bronze.bcb_ipca_raw"
enrich(
    TBL,
    """
    IPCA mensal — payload bruto da API SGS do Banco Central do Brasil
    (série 433: IPCA - Variação % mensal). Cada linha representa um
    objeto da resposta JSON (1 por mês de IPCA). Append-only: o
    `job_ipca_refresh` (cron mensal, dia 15) adiciona o arquivo
    timestamped no Volume e o Auto Loader emite uma linha aqui por mês
    presente no payload — duplicatas entre execuções são esperadas e
    re-deduplicadas no silver.

    O silver `silver.ipca_deflators_2021` calcula o índice cumulativo
    via log-sum-exp e produz `deflator_to_2021` (Dez/2021 = 1.0).

    Fonte: https://api.bcb.gov.br/dados/serie/bcdata.sgs.433/dados
    """,
    {
        "data":
            "String dd/MM/yyyy do primeiro dia do mês de referência do IPCA. "
            "É a chave temporal — silver converte para `dt`.",
        "valor":
            "Variação percentual mensal do IPCA (string com vírgula decimal, "
            "ex.: '0,67'). Silver normaliza via regexp + cast double.",
        **PLATFORM_COLS,
    },
    {
        "layer": "bronze",
        "domain": "ipca",
        "source": "bcb_sgs",
        "source_endpoint": "serie_433_ipca_mensal",
        "pii": "false",
        "grain": "mes_ipca",
        "refresh_cadence": "mensal",
        "ingest_mode": "auto_loader_json",
        "append_only": "true",
    },
)

# ---- bronze.pbf_pagamentos ----
TBL = f"{CATALOG}.bronze.pbf_pagamentos"
enrich(
    TBL,
    """
    Pagamentos do Bolsa Família, Auxílio Brasil e Novo Bolsa Família —
    bronze append-only construído a partir dos CSVs publicados pela
    CGU/Portal da Transparência. Os ZIPs originais são descomprimidos
    no Volume `/Volumes/<catalog>/bronze/raw/cgu/pbf_csv_extracted/` e
    o Auto Loader monitora o diretório.

    Cada linha corresponde a uma parcela paga a um beneficiário no
    mês de competência. As colunas `origin` (PBF/AUX/NBF), `ano`,
    `mes`, `competencia` são derivadas do nome do arquivo
    (`<ORIGIN>__YYYY_MM.zip`) e particionam a tabela.

    Granularidade: linha = (NIS, mes_competencia, origin). Silver
    `silver.pbf_total_uf_mes` agrega por UF × Ano × Mes.

    Fonte: https://portaldatransparencia.gov.br/download-de-dados/
    """,
    {
        "origin":
            "Programa de origem da parcela: 'PBF' (Bolsa Família), "
            "'AUX' (Auxílio Brasil) ou 'NBF' (Novo Bolsa Família). "
            "Derivado do nome do arquivo CGU. Particionamento.",
        "ano":
            "Ano da competência (do nome do arquivo, NÃO da data de "
            "pagamento). Particionamento.",
        "mes":
            "Mês da competência (1-12, do nome do arquivo).",
        "competencia":
            "Concatenação `format_string('%04d%02d', ano, mes)` para "
            "joins e ordenação cronológica eficiente.",
        "_fname":
            "Apenas o basename de _source_file, útil para debug.",
        "ym_str":
            "Substring com 'YYYY_MM' do nome do arquivo (intermediária).",
        **PLATFORM_COLS,
    },
    {
        "layer": "bronze",
        "domain": "pbf",
        "source": "cgu_portal_transparencia",
        "pii": "true",
        "pii_columns": "nis,nome_beneficiario,cpf_beneficiario",
        "grain": "parcela_per_beneficiario_mes",
        "refresh_cadence": "mensal",
        "ingest_mode": "auto_loader_csv",
        "append_only": "true",
        "partition_keys": "origin,ano",
    },
)

# ---- bronze.cnes_equipamentos ----
TBL = f"{CATALOG}.bronze.cnes_equipamentos"
enrich(
    TBL,
    """
    Equipamentos hospitalares CNES — bronze construído em pipeline
    híbrido de 2 estágios: (1) os arquivos `.dbc` (DBF compactado
    PKWARE) baixados do FTP DATASUS são convertidos para Parquet em
    paralelo no Volume `/Volumes/<catalog>/bronze/raw/datasus/cnes/
    parquet/`; (2) Auto Loader monitora esse folder e faz append no
    Delta. A primeira carga vai em modo BATCH (overhead Auto Loader
    ineficiente para 25k+ arquivos); cargas incrementais usam Auto
    Loader.

    Cada linha = um equipamento médico (TIPEQUIP × CODEQUIP) num
    estabelecimento (CNES) num mês. Silver `silver.equipamentos_uf_ano`
    agrega por UF × Ano × (TIPEQUIP, CODEQUIP) com split SUS/Privado
    via IND_SUS, e o gold é pass-through dessa silver.

    Composite key (TIPEQUIP, CODEQUIP) é OBRIGATÓRIA: CODEQUIP=42
    sozinho captura tanto Eletroencefalógrafo (TIPEQUIP=4) quanto
    Ressonância Magnética (TIPEQUIP=1). Esse foi o bug do WP #4 v1.

    Fonte FTP: ftp://ftp.datasus.gov.br/dissemin/publicos/CNES/200508_/
    Catálogo oficial de equipamentos: cnes2.datasus.gov.br/Mod_Ind_Equipamento.asp
    """,
    {
        "estado":
            "Sigla da UF do arquivo CNES (do nome do arquivo "
            "EQ<UF><AAMM>.dbc). Particionamento.",
        "ano":
            "Ano de competência do arquivo CNES. Particionamento.",
        "CNES":
            "Código CNES (Cadastro Nacional de Estabelecimentos de Saúde) "
            "do estabelecimento dono do equipamento. 7 dígitos.",
        "TIPEQUIP":
            "Tipo de equipamento (1 dígito): 1=Imagem, 2=Infraestrutura, "
            "3=Manutenção, 4=Métodos Gráficos, 5=Métodos Ópticos, "
            "6=Odontologia, 7=Por Imagem (subset). Catálogo oficial DATASUS.",
        "CODEQUIP":
            "Código do equipamento dentro do TIPEQUIP. NÃO é único "
            "globalmente — só junto com TIPEQUIP forma chave canônica.",
        "QT_EXIST":
            "Quantidade existente de equipamentos do tipo no estabelecimento "
            "no mês. Pode ser 0.",
        "IND_SUS":
            "Indicador SUS (1=SUS, 0=Privado). Usado pelo silver para split "
            "sus_*/priv_*.",
        **PLATFORM_COLS,
    },
    {
        "layer": "bronze",
        "domain": "equipamentos",
        "source": "datasus_cnes",
        "pii": "false",
        "grain": "equipamento_estabelecimento_mes",
        "refresh_cadence": "mensal",
        "ingest_mode": "auto_loader_parquet_after_dbc_convert",
        "append_only": "true",
        "partition_keys": "estado,ano",
    },
)

# ---- bronze.sih_aih_rd_uropro ----
TBL = f"{CATALOG}.bronze.sih_aih_rd_uropro"
enrich(
    TBL,
    """
    SIH-AIH-RD — Autorizações de Internação Hospitalar reduzidas, filtradas
    para os procedimentos UroPro (Tratamento Cirúrgico de Incontinência
    Urinária). Pipeline híbrido idêntico ao do CNES Equipamentos:
    (1) `.dbc` → Parquet em paralelo (filter `PROC_REA in (0409010499,
    0409070270, 0409020117)` aplicado já na conversão para reduzir
    volume), (2) Auto Loader → Delta append.

    Cada linha = uma AIH (uma internação aprovada). Silver
    `silver.sih_uropro_uf_ano` agrega por UF × Ano × Mes × proc_rea ×
    caráter × gestão; gold `gold.uropro_estados_ano` colapsa por UF ×
    Ano × proc_rea com população IBGE e deflator IPCA.

    Procedimentos SIGTAP cobertos:
      - 0409010499: Tratamento Cirúrgico de IU por Via Abdominal
      - 0409070270: Tratamento Cirúrgico de IU por Via Vaginal
      - 0409020117: Tratamento Genérico (deprecated, sem registros)

    Fonte FTP: ftp://ftp.datasus.gov.br/dissemin/publicos/SIHSUS/
    """,
    {
        "estado":
            "Sigla da UF do arquivo SIH (do nome RD<UF><AAMM>.dbc). "
            "Particionamento. Reflete a UF do hospital, não do paciente.",
        "ano":
            "Ano de competência do arquivo SIH. Particionamento.",
        "PROC_REA":
            "Código SIGTAP do procedimento principal realizado na "
            "internação (10 dígitos, sem ponto). Filtrado já no convert.",
        "UF_ZI":
            "Município de Internação (código IBGE de 6 dígitos). UF do "
            "paciente (primeiros 2 dígitos) pode diferir de `estado` em "
            "casos de Tratamento Fora do Domicílio (TFD).",
        "DT_INTER":
            "Data de internação (string AAAAMMDD).",
        "DT_SAIDA":
            "Data de saída/alta (string AAAAMMDD). Usada para `dias_perm`.",
        "DIAS_PERM":
            "Permanência hospitalar em dias (DT_SAIDA - DT_INTER, com "
            "regras CGU específicas).",
        "MORTE":
            "Indicador de óbito intra-hospitalar (1=óbito, 0=alta).",
        "VAL_TOT":
            "Valor total pago pela AIH (decimal, em reais nominais).",
        "VAL_SH":
            "Valor de Serviços Hospitalares (componente do VAL_TOT).",
        "VAL_SP":
            "Valor de Serviços Profissionais (componente do VAL_TOT).",
        "CAR_INT":
            "Caráter da internação (1=Eletivo, 2=Urgência, 3=Acidente "
            "trabalho, 4=Acidente trânsito, 5=Outras causas externas).",
        "GESTAO":
            "Esfera de gestão do estabelecimento "
            "(E=Estadual, M=Municipal, D=Dupla, X=Outro/NA).",
        **PLATFORM_COLS,
    },
    {
        "layer": "bronze",
        "domain": "uropro",
        "source": "datasus_sih_rd",
        "pii": "true",
        "pii_columns": "n_aih,cnes,municipio_internacao,nasc",
        "grain": "aih",
        "refresh_cadence": "mensal",
        "ingest_mode": "auto_loader_parquet_after_dbc_convert",
        "append_only": "true",
        "partition_keys": "estado,ano",
        "filter_proc_rea": "0409010499,0409070270,0409020117",
    },
)

# ---- bronze.rais_vinculos ----
TBL = f"{CATALOG}.bronze.rais_vinculos"
enrich(
    TBL,
    """
    RAIS — Relação Anual de Informações Sociais (Ministério do Trabalho
    e Emprego). Bronze construído a partir dos CSVs anuais por UF
    publicados pelo MTE. Pipeline híbrido (BATCH na primeira carga,
    Auto Loader incremental nas subsequentes), particionado por `ano`.

    Cada linha = um vínculo formal de trabalho num estabelecimento num
    ano-base RAIS. Silver `silver.rais_uf_ano` agrega por UF × Ano com
    `n_vinculos_total`, `n_vinculos_ativos` (vínculo ativo em 31/12),
    `massa_salarial_dezembro`, `remun_media_mes`, `n_estabelecimentos_proxy`
    (countDistinct concat(mun_trab, cnae_classe)) e `share_simples`.

    O autor do paper RAIS (CHALHOUB 2026c, WP n. 3) foi reprovado duas
    vezes na banca antes da aprovação 8.0 — esse contexto histórico está
    na monografia e na rota /rais da plataforma; não afeta o pipeline.

    Fonte: ftp://ftp.mtps.gov.br/pdet/microdados/RAIS/
    """,
    {
        "ano":
            "Ano-base RAIS (declaração entregue no ano seguinte). "
            "Particionamento.",
        "mun_trab":
            "Código IBGE de 6 dígitos do município do estabelecimento "
            "(2 primeiros dígitos = UF). Silver derive `uf` desta coluna.",
        "vinculo_ativo_31_12":
            "Indicador de vínculo ativo em 31/12 do ano-base (1=ativo). "
            "Define `n_vinculos_ativos`.",
        "vl_remun_dezembro_nom":
            "Remuneração nominal de dezembro (string com vírgula decimal). "
            "Silver normaliza para double.",
        "vl_remun_media_nom":
            "Remuneração média mensal nominal no ano-base (string).",
        "cnae_2_0_classe":
            "Classe CNAE 2.0 do estabelecimento (5 dígitos).",
        "ind_simples":
            "Indicador de Simples Nacional (1=Simples, 0=Lucro Real/Presumido).",
        **PLATFORM_COLS,
    },
    {
        "layer": "bronze",
        "domain": "rais",
        "source": "mte_rais",
        "pii": "true",
        "pii_columns": "cpf,pis,nome_trabalhador",
        "grain": "vinculo_ano",
        "refresh_cadence": "anual",
        "ingest_mode": "auto_loader_csv",
        "append_only": "true",
        "partition_keys": "ano",
    },
)

# ---- bronze.emendas_pagamentos ----
TBL = f"{CATALOG}.bronze.emendas_pagamentos"
enrich(
    TBL,
    """
    Emendas Parlamentares — execução orçamentária por UF. Bronze a
    partir dos CSVs anuais publicados pela CGU/Portal da Transparência
    (categorias RP6 individual, RP7 bancada, RP8 comissão, RP9 relator).
    Auto Loader CSV → Delta append, com headers normalizados para
    snake_case ASCII.

    Cada linha = um pagamento (ou empenho) a uma emenda específica num
    ano. Silver `silver.emendas_uf_ano` agrega por UF × Ano × tipo_RP
    (empenhado/pago/restos a pagar); gold `gold.emendas_estados_df`
    deflaciona para R$2021 e calcula `emendaPerCapita2021`.

    Achado do WP #3 (CHALHOUB 2026d, cross-vertical UroPro × PBF ×
    Emendas): emendas per capita correlacionam-se NEGATIVAMENTE com
    acesso a cirurgia uroginecológica (ρ ≈ -0,45) — UFs mais pobres
    recebem mais emendas, mas isso não se traduz em oferta clínica
    especializada visível.

    Fonte: https://portaldatransparencia.gov.br/emendas
    """,
    {
        "ano_arquivo":
            "Ano da emenda derivado (best-effort) de `ano_da_emenda` ou "
            "do nome do arquivo. Particionamento.",
        "ano_da_emenda":
            "Ano de exercício da emenda (ano fiscal).",
        "uf":
            "UF beneficiária (a quem o recurso foi destinado, não "
            "necessariamente a UF do parlamentar autor).",
        "valor_empenhado":
            "Valor empenhado nominal (string com vírgula decimal). "
            "Silver normaliza.",
        "valor_pago":
            "Valor efetivamente pago no ano (string com vírgula decimal). "
            "Diferença para empenhado = restos a pagar.",
        "tipo_emenda":
            "Bruto da fonte (string longa). Silver mapeia para "
            "{RP6, RP7, RP8, RP9, OUTRO} via regex.",
        "codigo_emenda":
            "Código identificador único da emenda no SIOP. Usado pelo "
            "silver para countDistinct(`n_emendas`).",
        "cod_municipio":
            "Código IBGE de 7 dígitos do município beneficiário (quando "
            "a emenda é municipal). Silver usa countDistinct para "
            "`n_municipios`.",
        **PLATFORM_COLS,
    },
    {
        "layer": "bronze",
        "domain": "emendas",
        "source": "cgu_portal_transparencia",
        "pii": "false",
        "grain": "linha_emenda_csv",
        "refresh_cadence": "mensal",
        "ingest_mode": "auto_loader_csv",
        "append_only": "true",
        "partition_keys": "ano_arquivo",
    },
)


# =====================================================================
# SILVER TABLES
# =====================================================================
print("\n=== silver ===")

# ---- silver.populacao_uf_ano ----
TBL = f"{CATALOG}.silver.populacao_uf_ano"
enrich(
    TBL,
    """
    População residente por UF × Ano — DIMENSÃO COMPARTILHADA do
    Mirante. Construída a partir do snapshot mais recente de
    `bronze.ibge_populacao_raw` (filtrado por `_source_file`, NUNCA
    por max(_ingest_ts) — vide bug fa869cf), com (a) explode de
    `resultados[].series[]`, (b) mapeamento `uf_id → sigla` (códigos
    IBGE de 2 dígitos → 'AC', 'AL', …), (c) painel completo UF×Ano
    via crossJoin, e (d) interpolação linear para anos não publicados
    pelo IBGE (a tabela 6579 não publica todos os anos).

    A coluna `fonte` rastreia explicitamente como cada célula foi
    obtida — crítico para auditoria de dados públicos:
      • ibge_direto         — valor publicado pelo IBGE no período
      • interpolado_linear  — interpolação linear entre dois anos publicados
      • carry_forward       — extrapolação do último ano disponível
      • carry_backward      — extrapolação do primeiro ano disponível
      • indisponivel        — UF não publicada nesse ano (DQ rejeita)

    Mode: OVERWRITE com `partitionBy(Ano)`. Particionamento por `Ano`
    favorece pruning em joins por ano-fixo (que é como gold queries
    consultam).

    Consumida por TODOS os golds de domínio (UroPro, PBF, RAIS,
    Emendas, Equipamentos) — qualquer alteração aqui propaga.
    """,
    {
        "Ano":
            "Ano-calendário (4 dígitos). Particionamento.",
        "uf":
            "Sigla da UF (2 letras, ex.: 'SP', 'MG'). 27 valores "
            "possíveis (26 estados + DF). Chave de domínio.",
        "populacao":
            "Estimativa populacional residente (long, arredondada). "
            "Origem: IBGE/SIDRA tabela 6579 ou interpolação linear.",
        "fonte":
            "Indica COMO a célula foi obtida: 'ibge_direto', "
            "'interpolado_linear', 'carry_forward', 'carry_backward' ou "
            "'indisponivel' (esta última é rejeitada pela DQ).",
        "_bronze_snapshot_ts":
            "Timestamp do _ingest_ts do bronze que originou este silver. "
            "Linhagem entre camadas.",
        "_silver_built_ts":
            "Timestamp UTC em que esta linha do silver foi construída.",
    },
    {
        "layer": "silver",
        "domain": "populacao",
        "source": "ibge_sidra",
        "pii": "false",
        "grain": "uf_ano",
        "refresh_cadence": "anual",
        "shared_dim": "true",
        "partition_keys": "Ano",
        "pk_grain": "Ano,uf",
    },
)

# ---- silver.ipca_deflators_2021 ----
TBL = f"{CATALOG}.silver.ipca_deflators_2021"
enrich(
    TBL,
    """
    Deflator IPCA por Ano com base = Dezembro/2021. DIMENSÃO
    COMPARTILHADA. Construído a partir do bronze BCB IPCA: (a) cast
    `valor` (string '0,67') para double, (b) cumprod via log-sum-exp
    sobre todo o histórico (numericamente estável), (c) extração do
    índice de Dezembro de cada ano, (d) divisão pelo índice de Dez/2021
    para gerar o `deflator_to_2021` (Dez/2021 = 1.0 por construção),
    (e) painel completo Ano via grade + forward-fill para anos
    intermediários sem IPCA disponível.

    Uso típico:
        gold.val_2021 = silver.val_nominal * silver.deflator_to_2021

    Mode: OVERWRITE simples (sem partição — tabela pequena).

    Fonte: BCB SGS série 433 (IPCA - Variação % mensal).
    """,
    {
        "Ano":
            "Ano-calendário. Tipo int. Cobertura: tipicamente 2008-atual.",
        "deflator_to_2021":
            "Multiplicador para converter R$ nominais do `Ano` para R$ "
            "constantes de Dezembro/2021. `1.0` para Ano=2021. >1 para "
            "anos anteriores; <1 para anos posteriores.",
        "_bronze_snapshot_ts":
            "Timestamp do _ingest_ts do bronze BCB que originou este silver.",
        "_silver_built_ts":
            "Timestamp UTC em que esta linha do silver foi construída.",
    },
    {
        "layer": "silver",
        "domain": "ipca",
        "source": "bcb_sgs_433",
        "pii": "false",
        "grain": "ano",
        "refresh_cadence": "mensal",
        "shared_dim": "true",
        "deflator_base": "Dez/2021 = 1.0",
        "pk_grain": "Ano",
    },
)

# ---- silver.pbf_total_uf_mes ----
TBL = f"{CATALOG}.silver.pbf_total_uf_mes"
enrich(
    TBL,
    """
    Bolsa Família agregado por UF × Ano × Mês. Origem: `bronze.pbf_pagamentos`
    (parcelas individuais por NIS-mês). Cobre PBF (Lei 10.836/2003),
    Auxílio Brasil (MP 1.061/2021) e Novo Bolsa Família (Lei
    14.601/2023) sob a mesma chave analítica — a coluna `origin` do
    bronze é colapsada em totalização única do programa em cada
    competência.

    Métricas:
      • `n`         — beneficiários distintos NESTE mês (countDistinct NIS)
      • `n_ano`     — beneficiários distintos no ANO inteiro (broadcast)
      • `total_estado` — soma das parcelas pagas (decimal(38,2), nominal)

    Filtros defensivos: somente as 27 UFs válidas; somente
    `Ano ∈ [2013, ano_atual]` (CGU às vezes ship retro-pagamentos para
    competências fora dessa janela — filtramos para manter
    comparabilidade temporal).

    Mode: OVERWRITE com `partitionBy(Ano)`.

    Achado do WP #2 (CHALHOUB 2026b): a transição PBF → Auxílio Brasil
    (Nov/2021) → Novo Bolsa Família (Mar/2023) **não é uma quebra de
    série** quando se observa a métrica unificada — é uma sucessão de
    três regimes sob continuidade de cobertura, com salto real de
    valor por beneficiário em 2022-2023 e estabilização em 2024-2025.
    """,
    {
        "Ano":
            "Ano-competência (do mes_competencia, NÃO do file_year). "
            "Particionamento. Range: 2013-atual.",
        "Mes":
            "Mês-competência (1-12).",
        "uf":
            "Sigla da UF beneficiária. 27 valores válidos.",
        "mes_competencia":
            "String 'YYYYMM' do mês-competência. Útil para joins "
            "cronológicos.",
        "n":
            "Número distinto de beneficiários (NIS) que receberam parcela "
            "neste (Ano, Mes, uf).",
        "n_ano":
            "Número distinto de beneficiários no (Ano, uf) inteiro "
            "(broadcast — mesmo valor em todas as 12 linhas mês do ano). "
            "Métrica que vai para o front.",
        "total_estado":
            "Soma de todas as parcelas pagas no (Ano, Mes, uf) em reais "
            "nominais. decimal(38,2).",
        "_silver_built_ts":
            "Timestamp UTC da construção desta linha.",
    },
    {
        "layer": "silver",
        "domain": "pbf",
        "source": "cgu_portal_transparencia",
        "pii": "false",
        "pii_aggregated_from": "bronze.pbf_pagamentos",
        "grain": "uf_ano_mes",
        "refresh_cadence": "mensal",
        "partition_keys": "Ano",
        "pk_grain": "Ano,Mes,uf",
        "regimes_unified": "PBF,AUX,NBF",
    },
)

# ---- silver.emendas_uf_ano ----
TBL = f"{CATALOG}.silver.emendas_uf_ano"
enrich(
    TBL,
    """
    Emendas Parlamentares agregadas por UF × Ano × tipo_RP. Origem:
    `bronze.emendas_pagamentos`. Categorias RP (Resultado Primário):

      • RP6 — Individual (deputado/senador, autoria pessoal)
      • RP7 — Bancada (estadual)
      • RP8 — Comissão
      • RP9 — Relator (RP-9, "orçamento secreto" pré-2022)
      • OUTRO

    Métricas:
      • `n_emendas`           — countDistinct(codigo_emenda)
      • `n_municipios`        — countDistinct(cod_municipio)
      • `valor_empenhado`     — soma R$ nominais
      • `valor_pago`          — soma R$ nominais
      • `valor_restos_a_pagar` — diferença empenhado/pago não realizada

    Mode: OVERWRITE com `partitionBy(Ano)`.

    Para análise cross-vertical da relação emendas × pobreza × oferta
    cirúrgica, consultar gold `gold.emendas_estados_df` (já com
    deflator R$2021 e `emendaPerCapita2021`). Achado do WP #3
    (CHALHOUB 2026d): emendas per capita NÃO compensam o gradiente
    pobreza→acesso (ρ ≈ -0,45 — sentido inverso ao esperado).
    """,
    {
        "Ano":
            "Ano de exercício da emenda. Particionamento. Cobertura: 2014-atual.",
        "uf":
            "UF beneficiária do recurso (não necessariamente do parlamentar).",
        "tipo_emenda":
            "Categoria de Resultado Primário normalizada: RP6/RP7/RP8/RP9/OUTRO.",
        "n_emendas":
            "Número distinto de códigos de emenda (countDistinct codigo_emenda) "
            "que financiaram pagamentos para esta combinação.",
        "n_municipios":
            "Número distinto de municípios beneficiários no (Ano, uf, tipo) "
            "(via cod_municipio do bronze).",
        "valor_empenhado":
            "Soma de valor_empenhado em reais nominais. Não-deflacionado.",
        "valor_pago":
            "Soma de valor_pago em reais nominais. Não-deflacionado.",
        "valor_restos_a_pagar":
            "Soma de valor_restos_a_pagar em reais nominais.",
        "_silver_built_ts":
            "Timestamp UTC da construção desta linha.",
    },
    {
        "layer": "silver",
        "domain": "emendas",
        "source": "cgu_portal_transparencia",
        "pii": "false",
        "grain": "uf_ano_tipoRP",
        "refresh_cadence": "mensal",
        "partition_keys": "Ano",
        "pk_grain": "Ano,uf,tipo_emenda",
    },
)

# ---- silver.sih_uropro_uf_ano ----
TBL = f"{CATALOG}.silver.sih_uropro_uf_ano"
enrich(
    TBL,
    """
    SIH-AIH agregado por UF × Ano × Mes × Procedimento × Caráter ×
    Gestão. Origem: `bronze.sih_aih_rd_uropro` (AIHs filtradas para
    procedimentos UroPro). Esta é a silver MAIS GRANULAR do domínio
    UroPro: o gold `gold.uropro_estados_ano` colapsa por UF × Ano ×
    Procedimento, mas a silver mantém a desagregação Mes/Carater/
    Gestao para análises forenses (ex.: "qual fração das AIHs vaginais
    em PE é gestão municipal?", "qual a distribuição mensal pré/pós
    pandemia?").

    Métricas-chave:
      • `n_aih`         — número de internações aprovadas
      • `sum_dias_perm` — soma dias internação (denominador do dias_perm_avg)
      • `n_morte`       — óbitos intra-hospitalares
      • `val_tot/sh/sp` — valores totais/Serviços Hospitalares/Serv. Profissionais
      • `dias_perm_avg` — sum_dias_perm / n_aih (ponderada por AIH)
      • `mortalidade`   — n_morte / n_aih

    Labels (`proc_label`, `car_label`, `gestao_label`) são strings
    legíveis criadas via `create_map`.

    Bug histórico fa869cf: silver anteriormente usava
    `bronze.where(_ingest_ts == max(_ingest_ts))` que descartava 73%
    das linhas e 14 das 27 UFs. Corrigido em abril/2026 para filtrar
    pelo último `_source_file`. Magnitudes pré-correção devem ser
    descartadas; tendências direcionais permanecem válidas.
    """,
    {
        "uf":
            "Sigla da UF do hospital onde a AIH foi processada.",
        "ano":
            "Ano de competência da AIH. Particionamento.",
        "mes":
            "Mês de competência da AIH (1-12).",
        "proc_rea":
            "Código SIGTAP do procedimento principal (10 dígitos).",
        "proc_label":
            "Nome legível do procedimento "
            "('Incontinência Urinária — Via Vaginal' / 'Via Abdominal' / "
            "'Genérico (deprecated)').",
        "car_int":
            "Caráter da internação (int): 1=Eletivo, 2=Urgência, "
            "3=Acid. trabalho, 4=Acid. trânsito, 5=Outras causas externas.",
        "car_label":
            "Nome legível do caráter da internação.",
        "gestao":
            "Esfera de gestão: E=Estadual, M=Municipal, D=Dupla, "
            "X=Outro/NA (do bronze).",
        "gestao_label":
            "Nome legível da gestão.",
        "n_aih":
            "Número de AIHs aprovadas nesta combinação (count).",
        "sum_dias_perm":
            "Soma da permanência hospitalar em dias (denominador para "
            "média ponderada por AIH).",
        "n_morte":
            "Número de óbitos intra-hospitalares nesta combinação.",
        "val_tot":
            "Valor total pago R$ nominais (soma de VAL_TOT do SIH).",
        "val_sh":
            "Valor de Serviços Hospitalares R$ nominais.",
        "val_sp":
            "Valor de Serviços Profissionais R$ nominais.",
        "val_tot_avg":
            "Valor médio por AIH (R$ nominais).",
        "val_sh_avg":
            "Valor médio Serviços Hospitalares por AIH (R$ nominais).",
        "val_sp_avg":
            "Valor médio Serviços Profissionais por AIH (R$ nominais).",
        "dias_perm_avg":
            "Permanência hospitalar média ponderada por AIH (sum_dias_perm/n_aih). "
            "Métrica-chave do WP #5: caiu de 2,39 para 1,43 dias na via "
            "vaginal entre 2008-2025 (-40,2%).",
        "mortalidade":
            "Taxa de óbito intra-hospitalar (n_morte/n_aih). "
            "Estruturalmente <0,05% — segurança clínica do procedimento.",
        "_bronze_snapshot_ts":
            "Timestamp do _ingest_ts do bronze que originou este silver.",
        "_silver_built_ts":
            "Timestamp UTC da construção desta linha.",
    },
    {
        "layer": "silver",
        "domain": "uropro",
        "source": "datasus_sih_rd",
        "pii": "false",
        "pii_aggregated_from": "bronze.sih_aih_rd_uropro",
        "grain": "uf_ano_mes_proc_carater_gestao",
        "refresh_cadence": "mensal",
        "partition_keys": "ano",
        "pk_grain": "uf,ano,mes,proc_rea,car_int,gestao",
        "post_bug_fa869cf": "true",
    },
)

# ---- silver.equipamentos_uf_ano ----
TBL = f"{CATALOG}.silver.equipamentos_uf_ano"
enrich(
    TBL,
    """
    Equipamentos hospitalares CNES agregados por UF × Ano × (TIPEQUIP,
    CODEQUIP). Origem: `bronze.cnes_equipamentos`. Composite key
    `equipment_key = "TIPEQUIP:CODEQUIP"` é a chave canônica — usar
    CODEQUIP sozinho colapsa equipamentos não-relacionados (vide bug
    do WP #4 v1: CODEQUIP=42 capturava Eletroencefalógrafo achando que
    era Ressonância Magnética).

    Pipeline:
      1. Para cada (CNES, mês) calcula a média mensal de QT_EXIST
         (defensivo contra duplicatas mensais).
      2. Calcula `avg_year` por (CNES, ano) = média das médias mensais.
      3. Agrega por (estado, ano, tipequip, codequip) com:
           - cnes_count       (countDistinct CNES)
           - total_avg        (sum de avg_year)
           - sus_*, priv_*    (split por IND_SUS=1/0)
      4. Junta `populacao` da silver compartilhada para `per_capita_scaled`.
      5. Mapeia `(tipequip, codequip)` → `equipment_name` /
         `equipment_category` via dicionário canônico CNES.

    Mode: OVERWRITE com `partitionBy(Ano)`.

    Cobre WPs #4 (Equipamentos × Parkinson, foco em RM) e #6
    (Equipamentos panorama, multi-categoria com correção composite-key).
    """,
    {
        "estado":
            "Sigla da UF (do bronze, particionamento).",
        "ano":
            "Ano de competência. Particionamento.",
        "tipequip":
            "Tipo de equipamento (1 dígito do CNES).",
        "codequip":
            "Código do equipamento dentro do tipo.",
        "equipment_key":
            "Composite key 'TIPEQUIP:CODEQUIP' (ex.: '1:12' = Ressonância "
            "Magnética). É a chave canônica — front filtra por aqui.",
        "equipment_name":
            "Nome canônico do equipamento conforme catálogo DATASUS "
            "(cnes2.datasus.gov.br/Mod_Ind_Equipamento.asp). "
            "'(não mapeado)' indica combo que precisa entrar no dicionário.",
        "equipment_category":
            "Categoria pai do equipamento (Imagem, Métodos Gráficos, etc.).",
        "cnes_count":
            "Número distinto de estabelecimentos CNES com este equipamento "
            "no (UF, ano). Independente de quantidade.",
        "total_avg":
            "Soma das médias anuais por CNES — estimativa do total de "
            "unidades operacionais no UF/ano.",
        "per_capita_scaled":
            "Total per capita escalonado (escala variável por equipamento "
            "tipo, ver `per_capita_scale_pow10`).",
        "sus_cnes_count":
            "Subset de cnes_count restrito a IND_SUS=1.",
        "sus_total_avg":
            "Subset de total_avg restrito a IND_SUS=1.",
        "sus_per_capita_scaled":
            "Subset de per_capita_scaled restrito ao SUS.",
        "priv_cnes_count":
            "Subset privado (IND_SUS=0).",
        "priv_total_avg":
            "Total avg privado.",
        "priv_per_capita_scaled":
            "Per capita privado.",
        "populacao":
            "Estimativa populacional do (UF, Ano) via "
            "silver.populacao_uf_ano (join compartilhado).",
        "per_capita_scale_pow10":
            "Expoente da escala usada em per_capita_scaled "
            "(ex.: 6 → por milhão de habitantes).",
        "_silver_built_ts":
            "Timestamp UTC da construção desta linha.",
    },
    {
        "layer": "silver",
        "domain": "equipamentos",
        "source": "datasus_cnes",
        "pii": "false",
        "grain": "uf_ano_tipequip_codequip",
        "refresh_cadence": "mensal",
        "partition_keys": "ano",
        "pk_grain": "estado,ano,tipequip,codequip",
        "composite_key_required": "true",
    },
)

# ---- silver.rais_uf_ano ----
TBL = f"{CATALOG}.silver.rais_uf_ano"
enrich(
    TBL,
    """
    RAIS agregada por UF × Ano. Origem: `bronze.rais_vinculos`. Usa o
    código do município de trabalho (`mun_trab`, IBGE 6 dígitos) para
    derivar a UF a partir dos 2 primeiros dígitos.

    Métricas:
      • `n_vinculos_total`        — todos os vínculos declarados (count)
      • `n_vinculos_ativos`       — ativos em 31/12 (vinculo_ativo_31_12=1)
      • `massa_salarial_dezembro` — soma vl_remun_dezembro_nom (R$ nominais)
      • `remun_media_mes`         — média de vl_remun_media_nom
      • `n_estabelecimentos_proxy` — countDistinct(mun_trab + cnae_classe)
                                    (proxy porque RAIS não publica id de
                                    estabelecimento estável)
      • `share_simples`           — fração média de ind_simples=1

    Mode: OVERWRITE com `partitionBy(Ano)`.

    Vertical RAIS é o WP #3 v1 da plataforma (numeração antiga, deferida
    no front). O autor do paper foi reprovado duas vezes na banca antes
    da aprovação 8.0 — contexto histórico documentado em /rais.
    """,
    {
        "Ano":
            "Ano-base RAIS. Particionamento.",
        "uf":
            "Sigla da UF derivada de substring(mun_trab, 1, 2) → mapa "
            "uf_code → sigla.",
        "n_vinculos_total":
            "Número total de vínculos declarados na RAIS no (UF, ano).",
        "n_vinculos_ativos":
            "Vínculos ativos em 31/12 do ano-base. Subset de n_vinculos_total.",
        "massa_salarial_dezembro":
            "Soma das remunerações nominais de dezembro (R$ nominais). "
            "Gold deflaciona via IPCA para R$2021.",
        "remun_media_mes":
            "Média mensal nominal das remunerações ao longo do ano (R$ "
            "nominais). Gold deflaciona.",
        "n_estabelecimentos_proxy":
            "PROXY de número de estabelecimentos: countDistinct(mun_trab "
            "concat cnae_classe). RAIS não publica id estável de "
            "estabelecimento, então usamos esta heurística.",
        "share_simples":
            "Fração média de vínculos em estabelecimentos do Simples "
            "Nacional (ind_simples=1) no (UF, ano).",
        "_silver_built_ts":
            "Timestamp UTC da construção desta linha.",
    },
    {
        "layer": "silver",
        "domain": "rais",
        "source": "mte_rais",
        "pii": "false",
        "pii_aggregated_from": "bronze.rais_vinculos",
        "grain": "uf_ano",
        "refresh_cadence": "anual",
        "partition_keys": "Ano",
        "pk_grain": "Ano,uf",
    },
)


# =====================================================================
# GOLD TABLES
# =====================================================================
print("\n=== gold ===")

# ---- gold.pbf_estados_df ----
TBL = f"{CATALOG}.gold.pbf_estados_df"
enrich(
    TBL,
    """
    Bolsa Família por UF × Ano (gold). Schema do JSON consumido pelo
    front-end. Construído a partir de `silver.pbf_total_uf_mes` (12
    meses → 1 ano) com joins na população (silver compartilhada) e no
    deflator IPCA-2021.

    Mecânica:
      • Soma `total_estado` dos 12 meses → `valor_nominal` (em R$ bi).
      • `valor_2021` = valor_nominal * deflator_to_2021.
      • `n_benef` = `n_ano` da silver (countDistinct anual de NIS).
      • `pbfPerBenef` = valor_2021 / n_benef.
      • `pbfPerCapita` = valor_2021 * 1e9 / populacao (R$/hab).

    Mode: OVERWRITE com `partitionBy(Ano)`.

    Achados do WP #2 (CHALHOUB 2026b): a transição PBF → Auxílio
    Brasil (Nov/2021) → Novo Bolsa Família (Mar/2023) é um regime
    contínuo de transferência de renda; o salto de valor por
    beneficiário acontece em 2022-2023 (R$ 5.825 em 2025) e cobertura
    estabiliza em ~22 mi de famílias.
    """,
    {
        "Ano":
            "Ano-competência. Particionamento. Cobertura: 2013-atual.",
        "uf":
            "Sigla da UF beneficiária.",
        "n_benef":
            "Beneficiários distintos no ano (countDistinct NIS, do "
            "silver `n_ano`).",
        "valor_nominal":
            "Total pago em R$ bilhões nominais (sum 12 meses, /1e9).",
        "valor_2021":
            "Total pago em R$ bilhões constantes 2021 (Dez/2021 = base).",
        "populacao":
            "Estimativa populacional residente (long, da silver compartilhada).",
        "pbfPerBenef":
            "Valor anual médio por beneficiário em R$ 2021 (≈5.825 em 2025).",
        "pbfPerCapita":
            "Valor anual per capita em R$ 2021 / habitante (≈608 em 2025).",
        "_gold_built_ts":
            "Timestamp UTC da construção desta linha.",
    },
    {
        "layer": "gold",
        "domain": "pbf",
        "consumer": "front_end_jsonexport",
        "pii": "false",
        "grain": "uf_ano",
        "refresh_cadence": "mensal",
        "partition_keys": "Ano",
        "pk_grain": "Ano,uf",
        "deflator_base": "Dez/2021",
    },
)

# ---- gold.emendas_estados_df ----
TBL = f"{CATALOG}.gold.emendas_estados_df"
enrich(
    TBL,
    """
    Emendas Parlamentares por UF × Ano (gold). Origem: pivot de
    `silver.emendas_uf_ano` (RP6/RP7/RP8/RP9/OUTRO → colunas) +
    deflação IPCA-2021 + população IBGE para `emendaPerCapita2021`.

    Mode: OVERWRITE com `partitionBy(Ano)`.

    Padrão consumido pelo front: o JSON de export tem o mesmo schema.
    Cobertura típica: 2014-atual (CGU/Portal da Transparência publica
    desde 2014 com qualidade estável).
    """,
    {
        "Ano":
            "Ano de exercício da emenda. Particionamento.",
        "uf":
            "UF beneficiária.",
        "populacao":
            "Estimativa populacional residente (long).",
        "valor_empenhado_nominal":
            "Soma do empenho em R$ nominais.",
        "valor_empenhado_2021":
            "Soma do empenho em R$ 2021 (deflacionado).",
        "valor_pago_nominal":
            "Soma do pago em R$ nominais.",
        "valor_pago_2021":
            "Soma do pago em R$ 2021.",
        "valor_restos_nominal":
            "Soma de restos a pagar em R$ nominais.",
        "pct_executado":
            "% executado = valor_pago / valor_empenhado.",
        "emendaPerCapita2021":
            "Pago per capita em R$ 2021 / habitante. Indicador-chave do "
            "WP #3 (CHALHOUB 2026d): ρ ≈ -0,45 com acesso à cirurgia "
            "uroginecológica (sentido inverso ao esperado).",
        "n_emendas":
            "Número distinto de códigos de emenda que financiaram pagamentos.",
        "n_municipios":
            "Número distinto de municípios beneficiários.",
        "empenhado_RP6":
            "Empenho da categoria RP6 — Individual (deputado/senador).",
        "empenhado_RP7":
            "Empenho da categoria RP7 — Bancada estadual.",
        "empenhado_RP8":
            "Empenho da categoria RP8 — Comissão.",
        "empenhado_RP9":
            "Empenho da categoria RP9 — Relator (orçamento secreto pré-2022).",
        "empenhado_OUTRO":
            "Demais categorias / não mapeadas.",
        "pago_RP6":
            "Pago da categoria RP6.",
        "pago_RP7":
            "Pago da categoria RP7.",
        "pago_RP8":
            "Pago da categoria RP8.",
        "pago_RP9":
            "Pago da categoria RP9.",
        "pago_OUTRO":
            "Pago demais categorias.",
        "_gold_built_ts":
            "Timestamp UTC da construção desta linha.",
    },
    {
        "layer": "gold",
        "domain": "emendas",
        "consumer": "front_end_jsonexport",
        "pii": "false",
        "grain": "uf_ano",
        "refresh_cadence": "mensal",
        "partition_keys": "Ano",
        "pk_grain": "Ano,uf",
        "deflator_base": "Dez/2021",
    },
)

# ---- gold.rais_estados_ano ----
TBL = f"{CATALOG}.gold.rais_estados_ano"
enrich(
    TBL,
    """
    RAIS por UF × Ano (gold). Origem: `silver.rais_uf_ano` + população
    + deflator IPCA-2021. Adiciona `vinculos_per_capita`,
    `taxa_formalizacao_proxy` e versões deflacionadas das massas
    salariais.

    Mode: OVERWRITE com `partitionBy(Ano)`.

    Vertical mantida na plataforma como WP #3 (numeração antiga;
    a numeração global atual reserva #3 para UroPro cross-vertical).
    O parecer da banca aprovou em 8,0 após duas reprovações — esse
    contexto não afeta a tabela e é discutido apenas no front (/rais).
    """,
    {
        "Ano":
            "Ano-base RAIS. Particionamento.",
        "uf":
            "Sigla da UF.",
        "populacao":
            "Estimativa populacional residente (long).",
        "n_vinculos_ativos":
            "Vínculos formais ativos em 31/12.",
        "n_vinculos_total":
            "Vínculos totais declarados (incluindo desligados no ano).",
        "n_estabelecimentos_proxy":
            "PROXY de estabelecimentos (countDistinct mun_trab+cnae_classe).",
        "massa_salarial_nominal":
            "Massa salarial de dezembro em R$ nominais.",
        "massa_salarial_2021":
            "Massa salarial de dezembro em R$ 2021 (deflacionada).",
        "remun_media_nominal":
            "Remuneração média mensal nominal.",
        "remun_media_2021":
            "Remuneração média mensal em R$ 2021.",
        "vinculos_per_capita":
            "n_vinculos_ativos / populacao.",
        "taxa_formalizacao_proxy":
            "PROXY de taxa de formalização — vínculos ativos / população. "
            "PROXY porque ignora população em idade ativa e estoque "
            "de informais.",
        "share_simples":
            "Fração média de vínculos em Simples Nacional.",
        "_gold_built_ts":
            "Timestamp UTC da construção desta linha.",
    },
    {
        "layer": "gold",
        "domain": "rais",
        "consumer": "front_end_jsonexport",
        "pii": "false",
        "grain": "uf_ano",
        "refresh_cadence": "anual",
        "partition_keys": "Ano",
        "pk_grain": "Ano,uf",
        "deflator_base": "Dez/2021",
    },
)

# ---- gold.equipamentos_estados_ano ----
TBL = f"{CATALOG}.gold.equipamentos_estados_ano"
enrich(
    TBL,
    """
    Equipamentos hospitalares CNES por UF × Ano × (TIPEQUIP, CODEQUIP)
    — gold pass-through do silver com chave composta `equipment_key`
    e nomes canônicos do catálogo oficial DATASUS.

    Métrica destaque: para Ressonância Magnética
    (`equipment_key = '1:12'`), a soma nacional bate com a mediana OCDE
    de ~17/Mhab. Spot-check no notebook reporta o cálculo e alerta se
    sair muito da banda esperada (3.000-4.500 unidades).

    Mode: OVERWRITE com `partitionBy(ano)`.

    Cobre WP #4 (Equipamentos × Parkinson, RM-foco) e WP #6
    (Equipamentos panorama). Bug do WP#4 v1 (CODEQUIP=42 capturando
    Eletroencefalógrafo) foi resolvido pela introdução do composite
    key — qualquer query que use só CODEQUIP está incorreta.
    """,
    {
        "estado":
            "Sigla da UF.",
        "ano":
            "Ano de competência. Particionamento.",
        "tipequip":
            "Tipo de equipamento.",
        "codequip":
            "Código dentro do tipo.",
        "equipment_key":
            "Chave composta 'TIPEQUIP:CODEQUIP'. É a chave que o front "
            "consome — nunca filtre por codequip sozinho.",
        "equipment_name":
            "Nome canônico DATASUS (ex.: 'Ressonância Magnética', "
            "'Tomógrafo Computadorizado').",
        "equipment_category":
            "Categoria pai (ex.: 'Por imagem', 'Métodos gráficos').",
        "cnes_count":
            "Número de estabelecimentos com o equipamento.",
        "total_avg":
            "Total de unidades operacionais (média anual de QT_EXIST).",
        "per_capita_scaled":
            "Total per capita escalonado (ver per_capita_scale_pow10).",
        "sus_cnes_count":
            "Estabelecimentos SUS (IND_SUS=1).",
        "sus_total_avg":
            "Unidades SUS.",
        "sus_per_capita_scaled":
            "Per capita SUS.",
        "priv_cnes_count":
            "Estabelecimentos privados.",
        "priv_total_avg":
            "Unidades privadas.",
        "priv_per_capita_scaled":
            "Per capita privado.",
        "populacao":
            "Estimativa populacional residente.",
        "per_capita_scale_pow10":
            "Expoente da escala usada (ex.: 6 = por milhão).",
        "_gold_built_ts":
            "Timestamp UTC da construção desta linha.",
    },
    {
        "layer": "gold",
        "domain": "equipamentos",
        "consumer": "front_end_jsonexport",
        "pii": "false",
        "grain": "uf_ano_tipequip_codequip",
        "refresh_cadence": "mensal",
        "partition_keys": "ano",
        "pk_grain": "estado,ano,tipequip,codequip",
        "composite_key_required": "true",
    },
)

# ---- gold.uropro_estados_ano ----
TBL = f"{CATALOG}.gold.uropro_estados_ano"
enrich(
    TBL,
    """
    UroPro por UF × Ano × Procedimento (gold). Tratamento cirúrgico de
    incontinência urinária no SUS, deflacionado IPCA Dez/2021.

    Origem: `silver.sih_uropro_uf_ano` colapsado (sum sobre Mes ×
    Carater × Gestao) + joins com população (silver compartilhada) e
    deflator IPCA. Adiciona splits eletivo/urgência e por gestão
    (estadual/municipal/dupla) preservando o detalhamento que o front
    consome.

    Métricas centrais (WPs #3 e #5 — CHALHOUB 2026d, 2026f):
      • `n_aih_por100k`        — taxa de cirurgias por 100k habitantes.
                                Em 2025: SC 14,71 / RR 0,14 (gap 100×).
      • `dias_perm_avg`        — permanência média ponderada por AIH.
                                Caiu 40% na via vaginal entre 2008-2025.
      • `mortalidade`          — <0,05% estruturalmente.
      • `val_tot_2021_por100k` — despesa per capita deflacionada.

    Mode: OVERWRITE com `partitionBy(ano)`.

    Pós-correção fa869cf: todas as 27 UFs estão presentes em todos os
    anos (cobertura 100%). Pré-correção, apenas 13 UFs apareciam na
    silver — quaisquer extracts antes de abril/2026 devem ser
    descartados (magnitudes prejudicadas, tendências preservadas).
    """,
    {
        "uf":
            "Sigla da UF do hospital.",
        "ano":
            "Ano de competência. Particionamento.",
        "proc_rea":
            "Código SIGTAP (10 dígitos): 0409010499=Vaginal, "
            "0409070270=Vaginal, 0409020117=Genérico (deprecated).",
        "proc_label":
            "Nome legível do procedimento.",
        "populacao":
            "Estimativa populacional do (UF, Ano) — silver compartilhada.",
        "n_aih":
            "Total de AIHs aprovadas no (UF, Ano, proc_rea).",
        "n_morte":
            "Óbitos intra-hospitalares.",
        "aih_eletivo":
            "Subset de n_aih com car_int=1 (eletivo). Espera-se ~95% para "
            "este procedimento.",
        "aih_urgencia":
            "Subset de n_aih com car_int=2 (urgência). Pequena fração.",
        "aih_gestao_estadual":
            "Subset de n_aih com gestao='E' (estabelecimento estadual).",
        "aih_gestao_municipal":
            "Subset de n_aih com gestao='M'.",
        "aih_gestao_dupla":
            "Subset de n_aih com gestao='D' (gestão dupla).",
        "val_tot":
            "Valor total pago em R$ nominais.",
        "val_sh":
            "Serviços Hospitalares R$ nominais.",
        "val_sp":
            "Serviços Profissionais R$ nominais.",
        "val_eletivo":
            "Subset val_tot eletivo.",
        "val_urgencia":
            "Subset val_tot urgência.",
        "val_gestao_estadual":
            "Subset val_tot estadual.",
        "val_gestao_municipal":
            "Subset val_tot municipal.",
        "val_gestao_dupla":
            "Subset val_tot dupla.",
        "val_tot_2021":
            "Total deflacionado para R$ 2021.",
        "val_sh_2021":
            "Serviços Hospitalares R$ 2021.",
        "val_sp_2021":
            "Serviços Profissionais R$ 2021.",
        "val_tot_avg":
            "Valor médio por AIH R$ nominais.",
        "val_sh_avg":
            "Valor médio Serv. Hospitalares por AIH R$ nominais.",
        "val_sp_avg":
            "Valor médio Serv. Profissionais por AIH R$ nominais.",
        "val_tot_avg_2021":
            "Valor médio por AIH em R$ 2021.",
        "dias_perm_avg":
            "Permanência hospitalar média ponderada por AIH (sum_dias_perm/"
            "n_aih). MÉTRICA-CHAVE do WP #5: caiu 40% via vaginal "
            "(2,39→1,43 dias) entre 2008-2025.",
        "mortalidade":
            "Taxa de óbito intra-hospitalar (n_morte/n_aih). "
            "<0,05% estruturalmente — segurança do procedimento "
            "elimina risco como variável de seleção em comparações UF.",
        "val_tot_2021_por100k":
            "Despesa total deflacionada por 100k habitantes — "
            "(val_tot_2021 * 1e5 / populacao).",
        "n_aih_por100k":
            "Cirurgias por 100k habitantes — INDICADOR-CHAVE de acesso. "
            "Em 2025: SC 14,71 → RR 0,14 (diferença ~100×). "
            "Correlação com cobertura PBF: ρ ≈ -0,68. "
            "Correlação com emendas per capita: ρ ≈ -0,45.",
        "per_capita_base":
            "Base do per capita (100000 = por 100k habitantes).",
        "deflator":
            "Deflator IPCA aplicado para chegar de nominal a R$2021. "
            "Replicado da silver compartilhada para transparência.",
        "_gold_built_ts":
            "Timestamp UTC da construção desta linha.",
    },
    {
        "layer": "gold",
        "domain": "uropro",
        "consumer": "front_end_jsonexport",
        "pii": "false",
        "grain": "uf_ano_proc_rea",
        "refresh_cadence": "mensal",
        "partition_keys": "ano",
        "pk_grain": "uf,ano,proc_rea",
        "deflator_base": "Dez/2021",
        "post_bug_fa869cf": "true",
        "wps_referenced": "WP3,WP5",
    },
)


# =====================================================================
# Done
# =====================================================================
print("\n✔ Catalog metadata applied.")
print("\nVerify via:")
print(f"  DESCRIBE CATALOG EXTENDED {CATALOG};")
print(f"  DESCRIBE SCHEMA EXTENDED  {CATALOG}.silver;")
print(f"  DESCRIBE TABLE EXTENDED   {CATALOG}.gold.uropro_estados_ano;")
print(f"  SHOW TBLPROPERTIES         {CATALOG}.gold.uropro_estados_ano;")
print(f"  SHOW TAGS ON TABLE         {CATALOG}.gold.uropro_estados_ano;")

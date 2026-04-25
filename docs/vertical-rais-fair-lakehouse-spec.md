# Vertical futura: RAIS + FAIRness + Lakehouse

> **Origem deste documento:** baseado na monografia de especialização do
> autor *"O Papel dos Metadados em Arquiteturas de Nuvem: FAIRness e
> Governança de Dados em Big Data"* (Chalhoub, UFRJ MBA Engenharia
> de Dados, 2023, não publicada). A vertical futura aqui especificada
> tem como objetivo **replicar e estender** o trabalho original,
> incorporando as melhorias identificadas no parecer técnico de
> avaliação dessa monografia (registrado abaixo).

---

## 1. Parecer técnico da monografia original (referência metodológica)

### 1.1 O que a monografia fez (síntese para reuso)

- **Tema:** intersecção FAIR principles × Lakehouse × Delta Lake
- **Implementação:** Microsoft Azure + Databricks
- **Dataset:** RAIS Vínculos Públicos (Ministério do Trabalho/PDET),
  ~136 milhões de linhas, ~62 GB brutos `.txt` dentro de `.7z`
- **Comparação:** três formatos (CSV / Apache Parquet / Delta)
- **Três métricas:**
  1. Tamanho ocupado em armazenamento
  2. Tempo de processamento e escrita (Bronze → Silver)
  3. Tempo mediano de leitura (mediana de 50 leituras)
- **Resultados-chave a serem reproduzidos:**

  | Formato | Tamanho | Escrita Bronze→Silver | Leitura mediana (50×) |
  |---|---|---|---|
  | CSV     | 55,56 GB | 41,45 min | 2,47 s |
  | Parquet | 10,60 GB | 13,23 min | 0,25 s |
  | Delta   | 9,98 GB  | 23,96 min | 0,12 s |

- **Conclusão:** mapeamento explícito de cada métrica aos princípios
  FAIR (F/A/I/R), demonstrando a tese de que melhor desempenho de
  formato corresponde, na prática, a maior FAIRness operacional.

### 1.2 Avaliação acadêmica (parecer formal, nota sugerida 8,0/10,0)

#### Pontos fortes a preservar na vertical:
- Estrutura ABNT canônica (5 capítulos: Intro / Teoria / Proposta /
  Resultados / Conclusão)
- Referencial bibliográfico sólido (Armbrust 2021, Wilkinson 2016,
  Kukreja 2021, DAMA-DMBOK 2017, Kimball & Ross 2013, Reis & Housley
  2022 — todos já catalogados em `articles/emendas-parlamentares.tex`
  e podem ser reusados)
- Implementação prática real (não meramente conceitual)
- Conexão explícita teoria↔prática

#### Lacunas a corrigir na vertical futura:

1. **Revisão editorial deficiente** (typos visíveis: "púiblicas",
   "pincípior", "aproxidamente", "conretas"). →
   **Mitigação:** todo .tex compila via CI, revisão por linter de
   ortografia (LanguageTool, hunspell-pt-BR) antes do merge.

2. **Rigor experimental modesto.** Conexão métrica↔FAIR é associativa,
   não validada por instrumentos consagrados. →
   **Mitigação na vertical futura:**
   - Usar **FAIR Data Maturity Model** do RDA (Research Data Alliance)
     ou os 21 indicadores oficiais de FAIRness
   - Apresentar score quantitativo por dimensão F/A/I/R, não apenas
     interpretação qualitativa

3. **Variância e generalização não controladas.** Mediana de 50
   execuções sem desvio-padrão / IC, single-cluster, single-dataset. →
   **Mitigação:**
   - Reportar média, mediana, p95, desvio padrão e n
   - Múltiplos tamanhos de cluster (pelo menos 2: Free Edition vs
     paid serverless)
   - Múltiplos datasets (RAIS + outro: CAGED, p.ex.)
   - Teste de significância estatística entre formatos

4. **Originalidade limitada** — a maior parte das conclusões reproduz
   Armbrust 2021. →
   **Mitigação:** estender comparação para incluir Apache Iceberg
   e Apache Hudi (2 outros formatos lakehouse), não apenas Delta.
   Discutir trade-offs específicos do contexto brasileiro (custos
   em USD, preço Databricks vs alternativas open-source).

5. **Análise crítica ausente** (when-NOT-to-use Delta). →
   **Mitigação:** seção dedicada "Limites do padrão Lakehouse" com
   discussão de workloads write-heavy, datasets pequenos, alternativas
   warehouse (BigQuery, Snowflake, Redshift) com tabela de tradeoffs.

6. **Capítulo Proposta curto (1.113 palavras), faltam diagramas
   próprios.** →
   **Mitigação:** gerar todos os diagramas via TikZ (LaTeX vetorial)
   ou matplotlib, próprios e nomeados. Usar `articles/build-figures.py`
   como referência metodológica (já temos 13 figuras Cividis para
   Emendas; replicar o padrão).

7. **Tema central parcialmente entregue** — título promete metadados,
   experimentos medem formato. →
   **Mitigação:** dedicar pelo menos 1/3 do trabalho empírico
   especificamente a Unity Catalog (linhagem automatizada,
   comentários, tags, FAIR scoring via metadados — não apenas
   desempenho de formato).

---

## 2. Especificação da vertical futura no Mirante dos Dados

### 2.1 Identidade

| Campo | Valor |
|---|---|
| Vertical key | `rais` |
| Label PT-BR | `RAIS — Vínculos Públicos` |
| Eyebrow | `Mercado de trabalho · governança de dados` |
| Período | `2020 – ano corrente` |
| Fonte primária | Ministério do Trabalho — PDET (RAIS Estabelecimento + Trabalhador) |
| Working Paper | n. 3 da série (após Emendas n.1 e Bolsa Família n.2) |

### 2.2 Pipeline (arquitetura medallion no Databricks Free Edition)

- **Ingest:** download `.7z` mensais do PDET → Volume UC
- **Bronze:** `.txt` → Auto Loader → Delta append-only (igual padrão
  Emendas/CNES); inclui fix de coerce-to-float64 desde o início
  (lição aprendida com cnes_equipamentos)
- **Silver:** dedup + tipagem + dim populacao_uf_ano (compartilhado)
  + dim ipca_deflators_2021 (compartilhado)
- **Gold:** painel UF × Ano × CNAE × tipo_vínculo, com indicadores
  de mercado de trabalho

### 2.3 Conteúdo do artigo (estende a monografia)

**Diferenças em relação à monografia original:**

| Dimensão | Monografia 2023 | Vertical Mirante (estendida) |
|---|---|---|
| Plataforma | Azure Databricks (paga) | Databricks Free Edition |
| Datasets | RAIS apenas | RAIS + CAGED (2 datasets) |
| Formatos | CSV vs Parquet vs Delta | + Apache Iceberg + Apache Hudi |
| Métricas | 3 (size/write/read) | + variância, p95, IC 95%, n |
| FAIR scoring | qualitativo associativo | RDA FAIR Maturity Model (quant.) |
| Análise crítica | ausente | seção "Limites do Lakehouse" |
| Cluster sizing | single | ≥ 2 configurações comparadas |
| Reprodutibilidade | screenshots | código open-source no repo |

**Estrutura sugerida do .tex** (`articles/rais-fair-lakehouse.tex`):

1. Introdução (motivação + posicionamento como continuação/extensão)
2. Referencial (FAIR + Lakehouse + medallion + governança)
3. Metodologia (pipeline detalhado, diagrama TikZ próprio,
   instrumentação de medição, instrumentos de FAIRness)
4. Resultados (12 figuras geradas via matplotlib, mesma escala
   Cividis das verticais anteriores)
5. Discussão (incluindo when-not-to-use, tradeoffs, comparação
   com warehouses)
6. Considerações finais

### 2.4 Checklist do novo vertical (consulte `feedback_new_vertical_checklist.md`)

- [ ] `data/stats/platform_stats.json` — adicionar `verticals.rais`
- [ ] `pipelines/notebooks/export/platform_stats_json.py` — adicionar
      pasta raw + bronze table
- [ ] `app/src/routes/Home.jsx` — TWO surfaces: `BigDataStrip` +
      `VERTICAIS` const
- [ ] `app/src/components/Layout.jsx` — `VERTICALS` array com
      `firstPublished`
- [ ] `articles/rais-fair-lakehouse.tex` + `articles/build-figures-rais.py`
- [ ] Botões canônicos no route page (Ler PDF / Baixar PDF / .tex / Overleaf)

### 2.5 Lições já incorporáveis desde o início

- **Bronze schema-coerce:** todos os numeric columns → float64 antes
  de `to_parquet` (evitar BIGINT vs DOUBLE merge errors). Schema
  version marker file `_schema_version_v1` no parquet dir para
  self-healing.
- **Hybrid batch + Auto Loader** no bronze: BATCH na primeira carga,
  Auto Loader em refreshes incrementais.
- **Não usar `input_file_name()`** (UC rejeita) → usar
  `_metadata.file_path`.
- **Não usar `partitionOverwriteMode=dynamic`** (serverless rejeita).
- **GH Action compila .tex** automaticamente (`xu-cheng/latex-action`)
  e copia PDF pra `app/public/articles/`.

---

## 3. Status

- [x] Decisão estratégica: replicar + estender a monografia como
      vertical RAIS no Mirante
- [x] Parecer da monografia documentado (este arquivo)
- [ ] Implementação ainda não iniciada

**Trigger para começar:** quando o usuário disser "vamos fazer
RAIS" ou similar. Este documento é a especificação inicial.

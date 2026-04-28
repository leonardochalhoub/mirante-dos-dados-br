<div align="center">

# Mirante dos Dados

**Lakehouse aberta para microdados públicos brasileiros.**
**Apache Spark · Delta Lake · Databricks Asset Bundles · React · LaTeX · GitHub Actions.**

[![Deploy](https://github.com/leonardochalhoub/mirante-dos-dados-br/actions/workflows/deploy-pages.yml/badge.svg)](https://github.com/leonardochalhoub/mirante-dos-dados-br/actions/workflows/deploy-pages.yml)
[![Refresh](https://github.com/leonardochalhoub/mirante-dos-dados-br/actions/workflows/refresh-pipelines.yml/badge.svg)](https://github.com/leonardochalhoub/mirante-dos-dados-br/actions/workflows/refresh-pipelines.yml)
[![Tests](https://img.shields.io/badge/pytest-13%20passando-success)](tests/)
[![Working Papers](https://img.shields.io/badge/working%20papers-7-blueviolet)](articles/)
[![Licença: MIT](https://img.shields.io/badge/licen%C3%A7a-MIT-black.svg)](LICENSE)
[![Custo](https://img.shields.io/badge/custo%20lifetime-US%24%2070-success)](#-finops--disciplina-de-custo)

[**Plataforma ao vivo →**](https://leonardochalhoub.github.io/mirante-dos-dados-br/) ·
[**Arquitetura**](docs/ARCHITECTURE.md) ·
[**Working Papers**](articles/) ·
[**ADRs**](docs/ARCHITECTURE.md#adrs)

</div>

---

## O que é

Uma **lakehouse aberta de produção** que ingere microdados públicos brasileiros heterogêneos (CGU, DATASUS, IBGE, BCB, MTE/PDET), normaliza tudo numa **arquitetura medallion Bronze → Silver → Gold** sobre Delta Lake, e publica artefatos `.json` versionados consumidos por:

1. uma **plataforma web interativa** (React + Vite, deploy em GitHub Pages), e
2. **Working Papers** revisáveis em LaTeX (padrão ABNT), compilados na CI.

Tudo é **open-source, reproduzível, instrumentado em FinOps, e implantado via Asset Bundles + GitHub Actions** — sem passos manuais, sem cola proprietária.

| Métrica (Abr 2026) | Valor |
|---|---|
| Arquivos brutos ingeridos | **18,8 mil** (375 GB comprimidos/expandidos em 9 fontes) |
| Maior tabela Delta | `bronze.pbf_pagamentos` — **2,53 bi linhas · 40 GB** |
| Verticais ativas | **5** de dados + **1** de observabilidade (FinOps) |
| Working Papers | **7** (framework de peer-review com 4 cadeiras simuladas) |
| Custo lifetime | **US$ 70** em 322 dias (≈ US$ 0,40 / job run, 91 runs) |
| Testes | **13 invariantes pytest** rodando na CI em 0,3 s |

---

## 🏗 Arquitetura

Medallion lakehouse padrão, totalmente declarativa, deployada via Asset Bundles.

```
                                                  ┌────────────────────────┐
   ┌──────────────────┐                            │  GitHub Actions        │
   │ Fontes públicas  │                            │  - deploy-pages.yml    │
   │ ───────────────  │                            │  - refresh-pipelines   │
   │ FTP DATASUS      │                            │  - auto-sync-gold      │
   │ Portal CGU       │                            └─────────┬──────────────┘
   │ IBGE/SIDRA       │                                      │ trigger
   │ FTP PDET/MTE     │                                      ▼
   │ BCB SGS          │              ┌──────────────────────────────────────┐
   └────────┬─────────┘              │  Databricks Asset Bundles            │
            │                        │  ───────────────────────────         │
            │ Auto Loader            │  pipelines/databricks.yml            │
            │ + ingest idempotente   │  10 jobs · compute serverless        │
            ▼                        │  Unity Catalog: mirante_prd          │
   ┌──────────────────────────────────────────────────────────────────────┐
   │  🥉  BRONZE   Delta Lake · STRING-ONLY · particionado · UC metadata  │
   │              Sem inferência de tipo, sem coerção (replay auditável)  │
   │              `pbf_pagamentos` · `cnes_equipamentos` · `rais_vinculos`│
   │              `emendas_pagamentos` · `sih_aih_rd_uropro` + 2 dims     │
   └──────────────────────────────┬────────────────────────────────────────┘
                                  │ Spark batch / streaming
                                  ▼
   ┌──────────────────────────────────────────────────────────────────────┐
   │  🥈  SILVER   Casts tipados · joins (população, deflator IPCA)       │
   │              Granularidade UF×Ano e Município×Ano                    │
   │              7 tabelas · particionadas · 100% taggeadas no UC        │
   └──────────────────────────────┬────────────────────────────────────────┘
                                  │
                                  ▼
   ┌──────────────────────────────────────────────────────────────────────┐
   │  🥇  GOLD     Schema estável · COMMENTs por coluna · zero drift      │
   │              Materializado em Delta + exportado JSON pra web         │
   │              4 tabelas → 7 JSONs em `data/gold/` (versionados)       │
   └────────┬───────────────────────────────────────────┬─────────────────┘
            │                                           │
            │ sync JSON (CI)                            │ matplotlib + LaTeX
            ▼                                           ▼
   ┌──────────────────────────┐              ┌──────────────────────────┐
   │  Plataforma web          │              │  Working Papers          │
   │  React 19 + Vite         │              │  ABNT LaTeX · 7 papers   │
   │  Recharts · d3-geo       │              │  Compilados na CI        │
   │  CDN GitHub Pages        │              │  Versionados em /app     │
   └──────────────────────────┘              └──────────────────────────┘
```

**Design completo**: [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) — 11 ADRs cobrindo Delta vs Iceberg, Auto Loader vs batch overwrite, estratégia de dedup, convenção de metadata Unity Catalog, dicionários como código, e racional do Bronze STRING-ONLY.

---

## 🧰 Stack — open source, escalável, sem lock-in

Todo componente é open-source, substituível, e roda em compute de nuvem comum.

### Compute & armazenamento
| Camada | Tecnologia | Por quê |
|---|---|---|
| Compute distribuído | **Apache Spark 3.5+** | Padrão da indústria pra batch + streaming em escala petabyte |
| Formato de tabela aberto | **Delta Lake 3.x** | ACID, time travel, schema evolution, protocolo OSS (Linux Foundation) |
| Catálogo | **Unity Catalog** (Databricks) | Linhagem, controle de acesso fino, metadata e tags por coluna |
| Ingest streaming | **Databricks Auto Loader** | Detecção schema-evolving de arquivos em escala |
| Orquestração | **Databricks Asset Bundles** (`databricks.yml`) | Jobs como código declarativo, multi-target (dev / prd) |
| Runtime do cluster | **Serverless / Photon** | Cobrança por segundo, zero custo ocioso (ver FinOps abaixo) |

### Frontend & docs
| Camada | Tecnologia | Por quê |
|---|---|---|
| Plataforma web | **React 19 + Vite 5** | Sub-200 KB JS gzip, HMR instantâneo |
| Charts e mapas | **Recharts** + **d3-scale-chromatic** + **d3-geo** | SVG puro, acessível, theme-aware |
| Hospedagem estática | **GitHub Pages** | Grátis, atrás de CDN, single-tenant simples |
| Working Papers | **LaTeX (lmodern · newtx · SciencePlots)** | Compatível com ABNT, compilação reproduzível |
| Figuras | **matplotlib 3 + geopandas + adjustText** | Charts editorial-grade compartilhados entre `.tex` e web |

### Engenharia & ops
| Camada | Tecnologia | Por quê |
|---|---|---|
| CI/CD | **GitHub Actions** | 3 workflows: deploy, refresh, auto-sync |
| Testes | **pytest** sobre o gold JSON (sem precisar Spark) | Loop de feedback de 0,3 s, valida o artefato publicado |
| IaC / config | **YAML Asset Bundles** + notebooks no repo | Fonte única de verdade, sem drift de UI |
| Versionamento | **Git + GitHub Releases** | Código, dicionários, gold JSONs todos sob controle de versão |

> **Pegada de fornecedor**: Databricks (compute) + GitHub (hospedagem + CI). Ambos substituíveis — Spark + Delta rodam em EMR / Synapse / on-prem; Pages pode migrar pra Vercel / Cloudflare / S3 + CloudFront.

---

## 💰 FinOps — disciplina de custo como cidadão de primeira classe

Mirante é uma **plataforma pública mantida por uma única pessoa** — visibilidade de custo não é opcional, é existencial. A plataforma se observa via tabelas `system.*` do Databricks e expõe tudo numa vertical dedicada.

### Gasto lifetime (Jun 2025 – Abr 2026, 322 dias)

```
Custo total                US$ 69,99
DBUs consumidos                504
Job runs                        91
Custo médio / run          US$ 0,40
P95 custo / run            US$ 1,49
Run-rate de storage        US$ 8 / mês
% de compute desperdiçado     53,9 %  ← runs ERROR + overhead de sessão
% chargeable                  82,0 %  ← jobs produtivos
Run mais cara              US$ 3,01  (refresh PBF, estado ERROR)
```

A linha **53,9% "wasted"** é intencional e visível — força responsabilização. Runs falhas, sessões warehouse ociosas, retries: tudo aparece em `/finops` com granularidade diária e rollup por job.

### Como é construído

| Camada | Tabelas |
|---|---|
| **Bronze** (system tables, delta-shared, read-only) | `system.billing.usage` · `system.compute.warehouses` · `system.lakeflow.jobs` · `system.lakeflow.job_run_timeline` |
| **Silver** (nossas) | `silver.finops_daily_spend` · `silver.finops_run_costs` |
| **Gold** (nossas, → JSON) | `gold.finops_daily_spend` · `gold.finops_run_costs` |
| **Export** | `data/gold/finops_summary.json` |
| **Web** | rota `/finops` — timeseries diário, rollup por run, KPI de wasted |

### Práticas FinOps integradas

- **Serverless-first**: zero custo ocioso. Compute sobe por job, encerra ao terminar.
- **Alarme de wasted compute**: qualquer run que ERROR ou exceda o budget P95 é flagged em `/finops`.
- **Asset Bundles por env**: dev/prd compartilham notebooks, catálogos diferentes (`mirante_dev` vs `mirante_prd`) — sem rodar prod acidentalmente do dev.
- **Cold path pra dado estável**: jobs ingest são `runs.submit` (one-shot), não streaming sempre-ligado. Mais barato que DLT contínuo pra refresh mensal.
- **Tiering de storage**: gold JSONs estáticos servem o web — sem warehouse SQL cobrado por tráfego de usuário.

> Meta: manter run-rate anual **abaixo de US$ 100** servindo 5 verticais, 7 Working Papers e plataforma web pública. Atualmente projetado em **US$ 79 / ano**.

---

## 📦 Verticais de dados (publicadas)

| # | Vertical | Rota | Fontes | Cobertura | Working Paper |
|---|---|---|---|---|---|
| 1 | **Bolsa Família** | [/bolsa-familia](https://leonardochalhoub.github.io/mirante-dos-dados-br/#/bolsa-familia) | CGU · IBGE · BCB | 2013 – 2025 | [WP #2](articles/bolsa-familia.tex) · [WP #7 (municipal)](articles/bolsa-familia-municipios.tex) |
| 2 | **Equipamentos médicos (CNES)** | [/equipamentos](https://leonardochalhoub.github.io/mirante-dos-dados-br/#/equipamentos) | DATASUS/CNES · IBGE | 2005 – 2025 | [WP #4](articles/equipamentos-rm-parkinson.tex) · [WP #6](articles/equipamentos-panorama-cnes.tex) |
| 3 | **Emendas Parlamentares** | [/emendas](https://leonardochalhoub.github.io/mirante-dos-dados-br/#/emendas) | CGU · IBGE · BCB | 2014 – 2025 | [WP #1](articles/emendas-parlamentares.tex) |
| 4 | **UroPro (SIH-AIH-RD)** | [/incontinencia-urinaria](https://leonardochalhoub.github.io/mirante-dos-dados-br/#/incontinencia-urinaria) | DATASUS/SIH · IBGE · BCB | 2008 – 2025 | [WP #3](articles/uropro-serie-2008-2025.tex) · [WP #5](articles/uropro-saude-publica-2008-2025.tex) |
| 5 | **RAIS — Vínculos Públicos** | [/rais](https://leonardochalhoub.github.io/mirante-dos-dados-br/#/rais) | PDET/MTE · IBGE · BCB | 1985 – 2025 | [draft](articles/rais-fair-lakehouse.tex) |
| ✦ | **FinOps** | [/finops](https://leonardochalhoub.github.io/mirante-dos-dados-br/#/finops) | `system.billing.*` · `system.lakeflow.*` | 2025 – em diante | camada de observabilidade |

Cada vertical: **Bronze → Silver → Gold → exportação JSON → rota React → artigo LaTeX** — mesmo formato, modelo mental único.

---

## 📚 Working Papers + framework de peer-review

7 papers em formato ABNT, cada um com **board simulado de peer-review com 4 cadeiras** (Finanças, Engenharia de Software, Design, Estratégia). Os pareceres formais dos revisores são persistidos em `app/src/data/atas-conselho.js` e renderizados ao lado de cada paper como crítica auditável.

Toda página de paper expõe a **mesma toolbar de 4 botões**:

```
📖 Ler PDF        ⤓ Baixar PDF (ABNT)        ⤓ Baixar fonte .tex        ↗ Abrir no Overleaf
```

Compilação faz parte do CI (`deploy-pages.yml`). Nenhum paper merge sem build limpo.

---

## 🧪 Testes — contrato sobre o artefato publicado

```bash
$ python3 -m pytest tests/ -v
============================== 13 passed in 0.30s ==============================
```

Os testes rodam **direto contra os gold JSONs publicados** — sem Spark, sem credenciais Databricks, sem fixtures. Se um número no site mudar inesperadamente, a CI quebra. Ver [ADR-010](docs/ARCHITECTURE.md#adr-010).

Exemplos do que é validado:

- Todas as 27 UFs presentes em todo snapshot anual
- Densidade de equipamentos bate com a mediana OECD em ordem de grandeza
- Invariante `cnes_count ≤ total_avg` (sem double-count via dual-flag)
- Campos do schema estáveis entre refreshes (sem drift)

---

## 🚀 Início rápido

### Rodar a plataforma web local
```bash
git clone https://github.com/leonardochalhoub/mirante-dos-dados-br
cd mirante-dos-dados-br/app
npm install && npm run dev          # http://localhost:5173
```

### Rodar a suite de testes
```bash
pip install pytest
python3 -m pytest tests/ -v
```

### Deployar / re-rodar pipeline (Databricks)
```bash
cd pipelines
databricks bundle deploy --target dev
databricks bundle run job_pbf_municipios_pipeline --target dev
```

### Compilar um Working Paper localmente
```bash
cd articles
latexmk -pdf -interaction=nonstopmode equipamentos-rm-parkinson.tex
```

---

## 🎯 Princípios de engenharia

1. **Tudo no Git, tudo reproduzível.** Código, dicionários, gold artefacts, papers (`.tex` + `.pdf`). Nenhum "estado mágico" mora em outro lugar.
2. **Bronze STRING-ONLY.** Sem inferência de tipo, sem coerção silenciosa. Todo cast aterrissa em Silver+. Audit trail fiel à fonte ([ADR-003](docs/ARCHITECTURE.md#adr-003)).
3. **Documentação como código.** Architecture Decision Records em `docs/`, `COMMENT ON TABLE` + Unity Catalog tags em toda tabela, docstrings em todo notebook.
4. **Testes como contrato.** `tests/` valida o *artefato publicado* (gold JSON), não a implementação. Refatore à vontade enquanto os números não mudarem.
5. **Custo é uma feature.** Todo job tem budget. Custo ocioso é falha. A vertical FinOps é self-monitored e pública.
6. **Aberto por construção.** Sem serialização proprietária, sem dicionários fechados, sem APIs com muros. Qualquer um pode forkar e rodar.

---

## 📁 Layout do repositório

```
mirante-dos-dados-br/
├── app/                       # plataforma web React + Vite
│   ├── src/
│   │   ├── routes/            # um arquivo por vertical (BolsaFamilia, Equipamentos, FinOps, ...)
│   │   ├── components/        # BrazilMap, KpiCard, ScoreCard, AtaConselho, ...
│   │   ├── data/              # pareceres.js, atas-conselho.js (pareceres do peer-review)
│   │   └── lib/               # data loaders, format helpers, color scales
│   └── public/
│       ├── data/              # gold JSONs sincados de /data/gold
│       └── articles/          # PDFs compilados + fontes .tex
├── pipelines/
│   ├── databricks.yml         # config Asset Bundle (10 jobs, 2 targets)
│   └── notebooks/
│       ├── ingest/            # downloaders de fonte pública (idempotentes)
│       ├── bronze/            # landing STRING-ONLY
│       ├── silver/            # tipado + enriquecido
│       ├── gold/              # publication-ready
│       └── export/            # gold → JSON pro web
├── articles/                  # 7 Working Papers (.tex) + figuras + builders Python
├── tests/                     # invariantes pytest sobre gold JSON
├── docs/
│   └── ARCHITECTURE.md        # 11 ADRs
├── data/
│   ├── gold/                  # gold JSONs versionados
│   ├── stats/                 # platform_stats.json
│   └── reference/             # dicionários canônicos (CNES, geobr, etc.)
└── .github/workflows/
    ├── deploy-pages.yml       # build site + compila PDFs + deploy
    ├── refresh-pipelines.yml  # cron Databricks
    └── auto-sync-gold.yml     # puxa gold artefacts de volta pro Git
```

---

## 📜 Licença

- **Código** (pipelines, web app, scripts): [MIT](LICENSE)
- **Dados curados** (gold JSONs, dicionário canônico CNES): [MIT](LICENSE)
- **Textos** (Working Papers, README): [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/deed.pt-br)

> Citar como: CHALHOUB, L. *Mirante dos Dados — lakehouse aberta para microdados públicos brasileiros*. Repositório GitHub, 2026. <https://github.com/leonardochalhoub/mirante-dos-dados-br>

---

## 👤 Autor

**Leonardo Chalhoub** — Engenheiro de Dados, criador da plataforma.
[github.com/leonardochalhoub](https://github.com/leonardochalhoub) · leonardochalhoub@gmail.com

---

<div align="center">
<sub>
Construído sobre Apache Spark · Delta Lake · Unity Catalog · React · LaTeX · GitHub Actions ·
<strong>lakehouse aberta · dado aberto · paper aberto</strong>
</sub>
</div>

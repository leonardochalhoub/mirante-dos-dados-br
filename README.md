<div align="center">

# Mirante dos Dados

**Open Lakehouse for Brazilian public microdata.**
**Apache Spark · Delta Lake · Databricks Asset Bundles · React · LaTeX · GitHub Actions.**

[![Deploy](https://github.com/leonardochalhoub/mirante-dos-dados-br/actions/workflows/deploy-pages.yml/badge.svg)](https://github.com/leonardochalhoub/mirante-dos-dados-br/actions/workflows/deploy-pages.yml)
[![Refresh](https://github.com/leonardochalhoub/mirante-dos-dados-br/actions/workflows/refresh-pipelines.yml/badge.svg)](https://github.com/leonardochalhoub/mirante-dos-dados-br/actions/workflows/refresh-pipelines.yml)
[![Tests](https://img.shields.io/badge/pytest-13%20passing-success)](tests/)
[![Working Papers](https://img.shields.io/badge/working%20papers-7-blueviolet)](articles/)
[![License: MIT](https://img.shields.io/badge/license-MIT-black.svg)](LICENSE)
[![Cost](https://img.shields.io/badge/lifetime%20cost-US%24%2070-success)](#-finops--cost-discipline)

[**Live platform →**](https://leonardochalhoub.github.io/mirante-dos-dados-br/) ·
[**Architecture**](docs/ARCHITECTURE.md) ·
[**Working Papers**](articles/) ·
[**ADRs**](docs/ARCHITECTURE.md#adrs)

</div>

---

## What this is

A **production-grade open lakehouse** that ingests heterogeneous Brazilian public microdata (CGU, DATASUS, IBGE, BCB, MTE/PDET), normalises it through a **Bronze → Silver → Gold medallion** on Delta Lake, and publishes versioned `.json` artefacts consumed by:

1. an **interactive web platform** (React + Vite, deployed to GitHub Pages), and
2. **peer-reviewable Working Papers** in LaTeX (ABNT), compiled by CI.

Everything is **open-source, reproducible, FinOps-instrumented, and deployed via Asset Bundles + GitHub Actions** — no manual steps, no proprietary glue code.

| Metric (Apr 2026) | Value |
|---|---|
| Raw files ingested | **18.8 K** (375 GB compressed/decompressed across 9 sources) |
| Largest Delta table | `bronze.pbf_pagamentos` — **2.53 B rows · 40 GB** |
| Active verticals | **5** data + **1** FinOps observability |
| Working Papers | **7** (peer-review framework w/ 4 internal reviewer chairs) |
| Lifetime compute cost | **US$ 70** over 322 days (≈ US$ 0.40 / job run, 91 runs) |
| Tests | **13 pytest invariants** running in CI in 0.3 s |

---

## 🏗 Architecture

Standard medallion lakehouse, fully declarative, Asset-Bundles-deployed.

```
                                                  ┌────────────────────────┐
   ┌──────────────────┐                            │  GitHub Actions        │
   │ Public sources   │                            │  - deploy-pages.yml    │
   │ ───────────────  │                            │  - refresh-pipelines   │
   │ FTP DATASUS      │                            │  - auto-sync-gold      │
   │ CGU portal       │                            └─────────┬──────────────┘
   │ IBGE/SIDRA       │                                      │ trigger
   │ MTE PDET FTP     │                                      ▼
   │ BCB SGS          │              ┌──────────────────────────────────────┐
   └────────┬─────────┘              │  Databricks Asset Bundles            │
            │                        │  ───────────────────────────         │
            │ Auto Loader            │  pipelines/databricks.yml            │
            │ + idempotent ingest    │  10 jobs · serverless compute        │
            ▼                        │  Unity Catalog: mirante_prd          │
   ┌──────────────────────────────────────────────────────────────────────┐
   │  🥉  BRONZE   Delta Lake · STRING-ONLY · partitioned · UC metadata    │
   │              No type inference, no coercion (auditable replay)        │
   │              `pbf_pagamentos` · `cnes_equipamentos` · `rais_vinculos` │
   │              `emendas_pagamentos` · `sih_aih_rd_uropro` + 2 dims      │
   └──────────────────────────────┬────────────────────────────────────────┘
                                  │ Spark batch / streaming
                                  ▼
   ┌──────────────────────────────────────────────────────────────────────┐
   │  🥈  SILVER   Typed casts · joins (population, IPCA deflator)         │
   │              UF×Year and Município×Year aggregation grain             │
   │              7 tables · partitioned · 100% UC-tagged                  │
   └──────────────────────────────┬────────────────────────────────────────┘
                                  │
                                  ▼
   ┌──────────────────────────────────────────────────────────────────────┐
   │  🥇  GOLD     Stable schema · column-level COMMENTs · zero drift      │
   │              Materialised in Delta + exported to JSON for the web    │
   │              4 tables → 7 JSONs in `data/gold/` (versioned in Git)   │
   └────────┬───────────────────────────────────────────┬─────────────────┘
            │                                           │
            │ JSON sync (CI)                            │ matplotlib + LaTeX
            ▼                                           ▼
   ┌──────────────────────────┐              ┌──────────────────────────┐
   │  Web platform            │              │  Working Papers          │
   │  React 19 + Vite         │              │  ABNT LaTeX · 7 papers   │
   │  Recharts · d3-geo       │              │  Compiled in CI          │
   │  GitHub Pages CDN        │              │  Auto-versioned in /app  │
   └──────────────────────────┘              └──────────────────────────┘
```

**Full design**: [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) — 11 ADRs covering Delta vs Iceberg, Auto Loader vs batch overwrite, dedup strategy, Unity Catalog metadata convention, dictionaries-as-code, and Bronze STRING-ONLY rationale.

---

## 🧰 Stack — open source, scalable, no lock-in

Every component is open-source, replaceable, and runs on commodity cloud compute.

### Compute & storage
| Layer | Tech | Why |
|---|---|---|
| Distributed compute | **Apache Spark 3.5+** | Industry-standard for petabyte-scale batch + streaming |
| Open table format | **Delta Lake 3.x** | ACID, time travel, schema evolution, OSS protocol (Linux Foundation) |
| Catalog | **Unity Catalog** (Databricks) | Lineage, fine-grained access, column-level metadata + tags |
| Streaming ingest | **Databricks Auto Loader** | Schema-evolving file detection at scale |
| Orchestration | **Databricks Asset Bundles** (`databricks.yml`) | Declarative jobs-as-code, multi-target (dev / prd) |
| Cluster runtime | **Serverless / Photon** | Pay-per-second, no idle cost (see FinOps below) |

### Frontend & docs
| Layer | Tech | Why |
|---|---|---|
| Web platform | **React 19 + Vite 5** | Sub-200 KB gzipped JS, instant HMR |
| Charts & maps | **Recharts** + **d3-scale-chromatic** + **d3-geo** | Pure SVG, accessible, theme-aware |
| Static hosting | **GitHub Pages** | Free, CDN-backed, single-tenant simple |
| Working Papers | **LaTeX (lmodern · newtx · SciencePlots)** | ABNT-compliant, reproducible PDF compilation |
| Figures | **matplotlib 3 + geopandas + adjustText** | Editorial-grade charts shared across `.tex` + web |

### Engineering & ops
| Layer | Tech | Why |
|---|---|---|
| CI/CD | **GitHub Actions** | 3 workflows: deploy, refresh, auto-sync |
| Tests | **pytest** over gold JSON (no Spark needed) | 0.3 s feedback loop, validates published artefact |
| IaC / config | **YAML Asset Bundles** + repo-local notebooks | Single source of truth, no UI drift |
| Versioning | **Git + GitHub Releases** | Code, dictionaries, gold JSONs all in version control |

> **Vendor footprint**: Databricks (compute) + GitHub (hosting + CI). Both replaceable — Spark + Delta run on EMR / Synapse / on-prem; Pages can move to Vercel / Cloudflare / S3 + CloudFront.

---

## 💰 FinOps — cost discipline as a first-class citizen

Mirante is a **public-facing platform run by one person** — cost visibility isn't optional, it's existential. The platform observes itself via Databricks `system.*` tables and exposes everything on a dedicated vertical.

### Lifetime spend (Jun 2025 – Apr 2026, 322 days)

```
Total cost                US$ 69.99
DBUs consumed                504
Job runs                      91
Avg cost / run            US$ 0.40
P95 cost / run            US$ 1.49
Storage run-rate          US$ 8 / month
Wasted compute %             53.9 %  ← ERROR runs + idle session overhead
Chargeable share             82.0 %  ← productive jobs
Most expensive run        US$ 3.01  (PBF refresh, ERROR state)
```

The **53.9 % "wasted" line** is intentional and visible — it forces accountability. Failed runs, idle warehouse sessions, retries: all surfaced at `/finops` with daily granularity and per-job rollups.

### How it's built

| Layer | Tables |
|---|---|
| **Source** (Delta-shared, read-only) | `system.billing.usage` · `system.compute.warehouses` · `system.lakeflow.jobs` · `system.lakeflow.job_run_timeline` |
| **Silver** (ours) | `silver.finops_daily_spend` · `silver.finops_run_costs` |
| **Gold** (ours, → JSON) | `gold.finops_daily_spend` · `gold.finops_run_costs` |
| **Export** | `data/gold/finops_summary.json` |
| **Web** | `/finops` route — daily timeseries, per-run rollup, wasted-compute KPI |

### FinOps practices baked in

- **Serverless-first**: no idle cluster cost. Compute spins up per job, terminates on completion.
- **Wasted-compute alarm**: any run that ERRORs or exceeds P95 budget is flagged at `/finops`.
- **Asset Bundles per env**: dev/prd share the same notebooks, different catalogs (`mirante_dev` vs `mirante_prd`) — no accidental prod runs from local dev.
- **Cold path for stale data**: ingest jobs are `runs.submit` style (single-shot), not always-on streaming. Cheaper than DLT continuous mode for monthly-refresh use cases.
- **Storage tiering**: gold JSON exports replace Delta-table reads on the web layer — no SQL warehouse charged for end-user traffic.

> Goal: keep total annual run-rate **under US$ 100** while serving 5 verticals, 7 Working Papers, and a public web platform. Currently tracking **US$ 79 / year** projected.

---

## 📦 Data verticals (live)

| # | Vertical | Route | Sources | Coverage | Working Paper |
|---|---|---|---|---|---|
| 1 | **Bolsa Família** | [/bolsa-familia](https://leonardochalhoub.github.io/mirante-dos-dados-br/#/bolsa-familia) | CGU · IBGE · BCB | 2013 – 2025 | [WP #2](articles/bolsa-familia.tex) · [WP #7 (municipal)](articles/bolsa-familia-municipios.tex) |
| 2 | **Equipamentos médicos (CNES)** | [/equipamentos](https://leonardochalhoub.github.io/mirante-dos-dados-br/#/equipamentos) | DATASUS/CNES · IBGE | 2005 – 2025 | [WP #4](articles/equipamentos-rm-parkinson.tex) · [WP #6](articles/equipamentos-panorama-cnes.tex) |
| 3 | **Emendas Parlamentares** | [/emendas](https://leonardochalhoub.github.io/mirante-dos-dados-br/#/emendas) | CGU · IBGE · BCB | 2014 – 2025 | [WP #1](articles/emendas-parlamentares.tex) |
| 4 | **UroPro (SIH-AIH-RD)** | [/incontinencia-urinaria](https://leonardochalhoub.github.io/mirante-dos-dados-br/#/incontinencia-urinaria) | DATASUS/SIH · IBGE · BCB | 2008 – 2025 | [WP #3](articles/uropro-serie-2008-2025.tex) · [WP #5](articles/uropro-saude-publica-2008-2025.tex) |
| 5 | **RAIS — Public Sector** | [/rais](https://leonardochalhoub.github.io/mirante-dos-dados-br/#/rais) | PDET/MTE · IBGE · BCB | 1985 – 2025 | [draft](articles/rais-fair-lakehouse.tex) |
| ✦ | **FinOps** | [/finops](https://leonardochalhoub.github.io/mirante-dos-dados-br/#/finops) | `system.billing.*` · `system.lakeflow.*` | 2025 – ongoing | observability layer |

Each vertical: **Bronze → Silver → Gold → JSON export → React route → LaTeX article** — same shape, single mental model.

---

## 📚 Working Papers + peer-review framework

7 papers in ABNT format, each with a **simulated 4-chair peer-review board** (Finance, Software Engineering, Design, Strategy). Reviewers' formal opinions are persisted in `app/src/data/atas-conselho.js` and rendered alongside each paper as auditable critique.

Every paper page exposes the **same 4-button toolbar**:

```
📖 Read PDF        ⤓ Download PDF (ABNT)        ⤓ Download .tex source        ↗ Open in Overleaf
```

Compilation is part of CI (`deploy-pages.yml`). No paper merges without a clean build.

---

## 🧪 Tests — contract over the published artefact

```bash
$ python3 -m pytest tests/ -v
============================== 13 passed in 0.30s ==============================
```

Tests run **directly against the published gold JSONs** — no Spark, no Databricks credentials, no fixtures. If a number on the website changes unexpectedly, CI breaks. See [ADR-010](docs/ARCHITECTURE.md#adr-010).

Examples of what's enforced:

- All 27 UFs present in every annual snapshot
- Equipment density matches OECD median order-of-magnitude
- `cnes_count ≤ total_avg` invariant (no dual-flag double-counting)
- Schema fields stable across refreshes (no drift)

---

## 🚀 Quick start

### Run the web platform locally
```bash
git clone https://github.com/leonardochalhoub/mirante-dos-dados-br
cd mirante-dos-dados-br/app
npm install && npm run dev          # http://localhost:5173
```

### Run the test suite
```bash
pip install pytest
python3 -m pytest tests/ -v
```

### Deploy / re-run a pipeline (Databricks)
```bash
cd pipelines
databricks bundle deploy --target dev
databricks bundle run job_pbf_municipios_pipeline --target dev
```

### Compile a Working Paper locally
```bash
cd articles
latexmk -pdf -interaction=nonstopmode equipamentos-rm-parkinson.tex
```

---

## 🎯 Engineering principles

1. **Everything in Git, everything reproducible.** Code, dictionaries, gold artefacts, papers (`.tex` + `.pdf`). No "magic state" lives anywhere else.
2. **Bronze STRING-ONLY.** No type inference, no silent coercion. All casts land in Silver+. Audit trail stays faithful to source ([ADR-003](docs/ARCHITECTURE.md#adr-003)).
3. **Documentation as code.** Architecture Decision Records in `docs/`, `COMMENT ON TABLE` + Unity Catalog tags on every table, docstrings in every notebook.
4. **Tests as contract.** `tests/` validates the *published artefact* (gold JSON), not the implementation. Refactor freely as long as numbers don't drift.
5. **Cost is a feature.** Every job has a budget. Idle cost is failure. FinOps vertical is self-monitored and public.
6. **Open by construction.** No proprietary serialisation, no closed dictionaries, no walled APIs. Anyone can fork and run.

---

## 📁 Repository layout

```
mirante-dos-dados-br/
├── app/                       # React + Vite web platform
│   ├── src/
│   │   ├── routes/            # one file per vertical (BolsaFamilia, Equipamentos, FinOps, ...)
│   │   ├── components/        # BrazilMap, BrazilMuniMap, KpiCard, ScoreCard, ...
│   │   ├── data/              # pareceres.js, atas-conselho.js (peer-review opinions)
│   │   └── lib/               # data loaders, format helpers, color scales
│   └── public/
│       ├── data/              # gold JSONs synced from /data/gold
│       └── articles/          # compiled PDFs + .tex sources
├── pipelines/
│   ├── databricks.yml         # Asset Bundle config (10 jobs, 2 targets)
│   └── notebooks/
│       ├── ingest/            # public-source downloaders (idempotent)
│       ├── bronze/            # STRING-ONLY landing
│       ├── silver/            # typed + enriched
│       ├── gold/              # publication-ready
│       └── export/            # gold → JSON for the web
├── articles/                  # 7 Working Papers (.tex) + figures + Python builders
├── tests/                     # pytest invariants over gold JSON
├── docs/
│   └── ARCHITECTURE.md        # 11 ADRs
├── data/
│   ├── gold/                  # versioned gold JSONs
│   ├── stats/                 # platform_stats.json
│   └── reference/             # canonical dictionaries (CNES, geobr, etc.)
└── .github/workflows/
    ├── deploy-pages.yml       # build site + compile PDFs + deploy
    ├── refresh-pipelines.yml  # nightly Databricks job runs
    └── auto-sync-gold.yml     # pull gold artefacts back into Git
```

---

## 📜 License

- **Code** (pipelines, web app, scripts): [MIT](LICENSE)
- **Curated data** (gold JSONs, canonical CNES dictionary): [MIT](LICENSE)
- **Texts** (Working Papers, README): [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/)

> Cite as: CHALHOUB, L. *Mirante dos Dados — open lakehouse for Brazilian public microdata*. GitHub repository, 2026. <https://github.com/leonardochalhoub/mirante-dos-dados-br>

---

## 👤 Author

**Leonardo Chalhoub** — Data Engineer, platform creator.
[github.com/leonardochalhoub](https://github.com/leonardochalhoub) · leonardochalhoub@gmail.com

---

<div align="center">
<sub>
Built on Apache Spark · Delta Lake · Unity Catalog · React · LaTeX · GitHub Actions ·
<strong>open lakehouse · open data · open papers</strong>
</sub>
</div>

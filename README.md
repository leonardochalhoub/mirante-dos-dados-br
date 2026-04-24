# Mirante dos Dados

> **Dados públicos do Brasil em um só lugar.**
> Pipelines em arquitetura *medallion* (bronze → silver → gold) sobre fontes oficiais — DATASUS, IBGE, CGU, BCB —
> publicados como JSON versionado e visualizados em um único shell React.

[![Deploy](https://github.com/leonardochalhoub/mirante-dos-dados-br/actions/workflows/deploy-pages.yml/badge.svg)](https://github.com/leonardochalhoub/mirante-dos-dados-br/actions/workflows/deploy-pages.yml)
[![License: MIT](https://img.shields.io/badge/license-MIT-black.svg)](LICENSE)

🌐 **Site:** _em breve_ — `mirantedosdados.com.br`
📦 **Repo:** este aqui (público) — pipelines abertos, dado aberto, código aberto.

---

## O que é

Mirante dos Dados é uma **plataforma aberta de dados públicos brasileiros**. Cada *vertical* é uma rota
do mesmo app, alimentada por um pipeline próprio (notebooks Databricks) que escreve um JSON gold neste repo.

| Vertical                           | Rota                | Fontes                          | Período      | Status |
| ---------------------------------- | ------------------- | ------------------------------- | ------------ | ------ |
| Bolsa Família                      | `/bolsa-familia`    | CGU · IBGE · BCB                | 2013 – 2025  | ✅      |
| Saúde · Equipamentos de RM         | `/saude-mri`        | DATASUS/CNES · IBGE             | 2005 – 2025  | ✅      |
| Emendas Parlamentares              | `/emendas`          | Câmara · Senado · Tesouro       | 2014 –       | 🚧 em breve |

---

## Arquitetura

```
┌─────────────────────────────────────────────────────────────────────────┐
│  CGU · DATASUS · IBGE · BCB     (APIs e CSVs oficiais)                  │
└─────────────────────────────────┬───────────────────────────────────────┘
                                  │
                                  ▼
                  ┌────────────────────────────────┐
                  │   Databricks Free Edition      │
                  │   PySpark · Unity Catalog      │
                  ├────────────────────────────────┤
                  │  bronze  →  raw dump           │
                  │  silver  →  clean, typed       │
                  │  gold    →  agg por vertical   │
                  └─────────────┬──────────────────┘
                                │  gold JSON (MB)
                                ▼
                  ┌────────────────────────────────┐
                  │  GitHub Action (cron mensal)   │
                  │  - dispara job Databricks      │
                  │  - puxa gold JSONs             │
                  │  - commita em /data/gold       │
                  └─────────────┬──────────────────┘
                                ▼
                       ┌──────────────────┐
                       │  GitHub Pages    │
                       │  React shell     │
                       │  rotas/vertical  │
                       └──────────────────┘
```

**Filosofia:** o pipeline é o produto. O site é só a vitrine.

---

## Estrutura do repositório

```
mirante-dos-dados-br/
├── app/                            React shell (Vite + React 18 + Plotly)
│   ├── public/
│   │   ├── data/                   ← copiado de /data/gold no prebuild (gitignored)
│   │   └── geo/                    GeoJSON UFs
│   └── src/
│       ├── routes/                 Home, BolsaFamilia, SaudeMri, NotFound
│       ├── components/             Layout, Panel, KpiCard, BrazilMap, StateRanking, …
│       ├── lib/                    format, data fetcher, plotly defaults
│       ├── hooks/                  useTheme
│       └── styles/                 globals.css (design tokens)
│
├── data/
│   └── gold/                       ← SOURCE OF TRUTH dos JSONs gold
│       ├── gold_pbf_estados_df.json
│       └── gold_mri_estados_ano.json
│
├── pipelines/                      Notebooks Databricks (em construção)
│   ├── bronze/
│   ├── silver/
│   └── gold/
│
├── docs/                           Decisões de arquitetura, contratos
├── scripts/sync-data.mjs           Copia /data/gold → /app/public/data antes do build
└── .github/workflows/deploy-pages.yml
```

---

## Stack

| Camada                  | Tecnologia                              | Custo |
| ----------------------- | --------------------------------------- | ----- |
| Ingestão & Transformação| **Databricks Free Edition** (PySpark, Unity Catalog) | Grátis (cap DBU serverless) |
| Orquestração            | **GitHub Actions** (cron)               | Grátis (repo público)       |
| Hosting                 | **GitHub Pages**                        | Grátis                      |
| Frontend                | **Vite + React 18 + Plotly.js**         | Grátis                      |
| Domínio                 | Registro.br `.com.br`                   | ~R$ 40/ano                  |

**Não usamos:** dbt (versão 1, volume pequeno demais pra justificar); Supabase (dado público gold cabe em JSON estático);
Groq (sem feature LLM no MVP).

---

## Rodando localmente

```bash
# 1. Clonar + instalar
git clone https://github.com/leonardochalhoub/mirante-dos-dados-br.git
cd mirante-dos-dados-br/app
npm install

# 2. Dev server (auto-copia /data/gold → /app/public/data antes)
npm run dev

# 3. Build de produção
npm run build         # gera app/dist/
npm run preview       # serve dist/ em localhost:4173
```

---

## Adicionar um novo vertical

1. Criar notebook(s) em `pipelines/{bronze,silver,gold}/<vertical>.py`.
2. Notebook gold escreve um JSON em `/data/gold/gold_<vertical>_*.json`.
3. Adicionar uma rota nova em `app/src/routes/<Vertical>.jsx` seguindo o padrão de
   `BolsaFamilia.jsx` / `SaudeMri.jsx`.
4. Linkar no `app/src/components/Layout.jsx` (lista `VERTICALS`) e no card da Home (`Home.jsx`).

O contrato entre pipeline e front é simples: **um JSON gold por vertical, schema estável,
agregado a um nível que o front possa renderizar sem cálculos pesados.**

---

## Roadmap

- [x] Shell React unificado (rotas + tema + design system)
- [x] Vertical Bolsa Família (gold já existente)
- [x] Vertical Saúde · RM (gold já existente)
- [ ] Workspace Databricks Free Edition + Unity Catalog setup
- [ ] Migrar pipeline PBF pra Databricks (bronze → silver → gold)
- [ ] Migrar pipeline MRI pra Databricks
- [ ] GitHub Action: cron mensal disparando job Databricks via REST + commit do gold
- [ ] Domínio `mirantedosdados.com.br`
- [ ] Vertical Emendas Parlamentares (RP6/RP9, favorecidos, cidades-alvo)
- [ ] Data contracts em `/docs/contracts/` (schema + freshness + SLA por vertical)

---

## Autor

**Leonardo Chalhoub** — AI Data Engineering Tech Lead (Databricks).
[LinkedIn](https://www.linkedin.com/in/leonardochalhoub/) · [GitHub](https://github.com/leonardochalhoub) · leochalhoub@hotmail.com

---

## Licença

MIT — veja [LICENSE](LICENSE).

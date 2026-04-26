<div align="center">

# 🇧🇷 Mirante dos Dados

### Plataforma aberta e reproduzível de dados públicos brasileiros

*Pipelines em arquitetura medallion sobre microdados oficiais — DATASUS, CGU, IBGE, BCB, MTE — publicados como JSON versionado, visualizados em painel React, e analisados em Working Papers ABNT compilados no CI.*

[![Deploy](https://github.com/leonardochalhoub/mirante-dos-dados-br/actions/workflows/deploy-pages.yml/badge.svg)](https://github.com/leonardochalhoub/mirante-dos-dados-br/actions/workflows/deploy-pages.yml)
[![Tests](https://img.shields.io/badge/tests-13%20passing-success)](tests/)
[![Working Papers](https://img.shields.io/badge/working%20papers-7-blueviolet)](articles/)
[![License: MIT](https://img.shields.io/badge/license-MIT-black.svg)](LICENSE)

🌐 [**Acessar a plataforma →**](https://leonardochalhoub.github.io/mirante-dos-dados-br/) &nbsp;&nbsp;•&nbsp;&nbsp; 📐 [**ARCHITECTURE.md**](docs/ARCHITECTURE.md) &nbsp;&nbsp;•&nbsp;&nbsp; 📊 [**Working Papers**](articles/)

</div>

---

## ✨ Em uma frase

Mirante dos Dados transforma microdados administrativos brasileiros em **datasets reprodutíveis, auditáveis e citáveis** — com pipeline aberto (Apache Spark + Delta Lake), front-end interativo (React + Vite) e Working Papers científicos compilados em LaTeX no CI.

---

## 🗂 Verticais publicadas

| # | Vertical | Rota | Fontes primárias | Cobertura | Working Paper |
|---|----------|------|------------------|-----------|---------------|
| 1 | **Bolsa Família** | [/bolsa-familia](https://leonardochalhoub.github.io/mirante-dos-dados-br/#/bolsa-familia) | CGU · IBGE · BCB | 2013 – 2025 | [WP #2](articles/bolsa-familia.tex) |
| 2 | **Equipamentos médicos (CNES)** | [/equipamentos](https://leonardochalhoub.github.io/mirante-dos-dados-br/#/equipamentos) | DATASUS/CNES · IBGE | 2005 – 2025 | [WP #4 (RM × Parkinson)](articles/equipamentos-rm-parkinson.tex) · [WP #6 (Panorama)](articles/equipamentos-panorama-cnes.tex) |
| 3 | **Emendas Parlamentares** | [/emendas](https://leonardochalhoub.github.io/mirante-dos-dados-br/#/emendas) | CGU · IBGE · BCB | 2014 – 2025 | [WP #1](articles/emendas-parlamentares.tex) |
| 4 | **Incontinência Urinária (SIH)** | [/incontinencia-urinaria](https://leonardochalhoub.github.io/mirante-dos-dados-br/#/incontinencia-urinaria) | DATASUS/SIH-AIH-RD · IBGE · BCB | 2008 – 2025 | [WP #3](articles/uropro-incontinencia-urinaria.tex) · [WP #5](articles/uropro-serie-2008-2025.tex) |
| 5 | **RAIS — Vínculos Públicos** | [/rais](https://leonardochalhoub.github.io/mirante-dos-dados-br/#/rais) | PDET/MTE · IBGE · BCB | 1985 – 2025 | [draft](articles/rais-fair-lakehouse.tex) |

> 📡 **Refresh mensal automatizado** via Databricks Free Edition. Cada vertical tem job dedicado (`job_<vertical>_refresh`).

---

## 🏗 Arquitetura

```
┌──────────────────────────────────────────────────────────────────────┐
│ Fontes públicas (FTP DATASUS, CGU, IBGE/SIDRA, BCB, MTE)              │
└─────────────────────────────┬────────────────────────────────────────┘
                              │ ingest (Python, idempotent)
┌─────────────────────────────▼────────────────────────────────────────┐
│ 🥉  Bronze · Delta Lake STRING-ONLY · partition (estado, ano)          │
│    Auto Loader incremental + batch overwrite na primeira carga       │
└─────────────────────────────┬────────────────────────────────────────┘
                              │ silver (Spark batch)
┌─────────────────────────────▼────────────────────────────────────────┐
│ 🥈  Silver · UF×Ano agregado · casts tipados · dedup · enrichment      │
│    Joins com dim populacao + IPCA + dicionários canonical            │
└─────────────────────────────┬────────────────────────────────────────┘
                              │ gold (pass-through ou aggregation)
┌─────────────────────────────▼────────────────────────────────────────┐
│ 🥇  Gold · UF×Ano final · schema estável publicado · COMMENT          │
│    Materializado em Delta + exportado JSON em data/gold/             │
└─────────────────────────────┬────────────────────────────────────────┘
                              │ export + sync (CI: Databricks → Git)
┌─────────────────────────────▼────────────────────────────────────────┐
│ 🌐 Front · React + Vite · recharts · react-simple-maps               │
│    35 KB CSS gzipped · mobile-first · light/dark · accessibility    │
└──────────────────────────────────────────────────────────────────────┘
```

📐 [**Documento completo de arquitetura → docs/ARCHITECTURE.md**](docs/ARCHITECTURE.md) — 11 ADRs (Architecture Decision Records) cobrindo escolhas de Delta vs Iceberg, Auto Loader vs batch, dedup strategy, dicionários canonical, e mais.

---

## 📚 Working Papers

Cada vertical do Mirante tem um *Working Paper* em padrão ABNT compilado no CI a cada push. Os PDFs são publicados em `app/public/articles/` e os fontes `.tex` ficam abertos para reuso (botão "Baixar fonte" em cada artigo).

| WP | Título resumido | Páginas | Autoria |
|----|-----------------|---------|---------|
| #1 | Emendas parlamentares 2014–2025 | 32 | Chalhoub |
| #2 | Bolsa Família 2013–2025 | 28 | Chalhoub |
| #3 | UroPro — Incontinência Urinária no SUS | 24 | Silva + Chalhoub |
| #4 | **Neuroimagem para Parkinson — RM, CT, PET, DAT-SPECT** | **30** | **Rolim + Chalhoub** |
| #5 | UroPro — série 2008–2025 cross-vertical | 26 | Chalhoub |
| #6 | Panorama nacional de equipamentos do CNES | 24 | Chalhoub |
| #7 | (planejado) Tomografia no SUS | — | — |

🔬 **Cada WP tem 4 botões padrão** na sua página de vertical: `📖 Ler PDF` · `⤓ Baixar PDF (ABNT)` · `⤓ Baixar fonte (.tex)` · `↗ Abrir no Overleaf`.

---

## 🧪 Tests + qualidade

```bash
$ python3 -m pytest tests/ -v
tests/test_equipamentos_gold.py::test_row_count_in_expected_range PASSED
tests/test_equipamentos_gold.py::test_all_27_ufs_present PASSED
tests/test_equipamentos_gold.py::test_year_range PASSED
tests/test_equipamentos_gold.py::test_schema_required_fields PASSED
tests/test_equipamentos_gold.py::test_equipment_key_is_composite PASSED
tests/test_equipamentos_gold.py::test_unmapped_combos_under_tolerance PASSED
tests/test_equipamentos_gold.py::test_rm_count_matches_oecd_magnitude PASSED
tests/test_equipamentos_gold.py::test_rm_density_matches_oecd_median PASSED
tests/test_equipamentos_gold.py::test_tipequip_normalized_no_leading_zeros PASSED
tests/test_equipamentos_gold.py::test_codequip_zero_padded PASSED
tests/test_equipamentos_gold.py::test_sus_priv_sum_equals_total PASSED
tests/test_equipamentos_gold.py::test_cnes_count_le_total_avg_when_one_equipment_per_estab PASSED
tests/test_equipamentos_gold.py::test_rm_density_per_uf_realistic PASSED
============================== 13 passed in 0.30s ==============================
```

Os tests rodam direto contra os JSONs gold versionados — sem dependência de Spark/Databricks. CI rápido (~0.3s) e validação local trivial. Veja [ADR-010](docs/ARCHITECTURE.md#adr-010--por-quê-tests-pytest-sobre-o-gold-json-não-sparkdatabricks).

---

## 📊 Dicionário canonical CNES

Um dos artefatos centrais do projeto é o **dicionário canonical de 133 combinações `(TIPEQUIP, CODEQUIP)` → equipamento**, publicado em [`data/reference/cnes_eq_canonical.csv`](data/reference/cnes_eq_canonical.csv) e usado pelo silver para nomear todos os equipamentos do CNES.

Extraído por *parsing HTML direto* do catálogo oficial DATASUS (`cnes2.datasus.gov.br/Mod_Ind_Equipamento.asp`), validado em **cobertura 100\,%** contra snapshot empírico Dez/2024 (1.123.809 linhas, 27 UFs).

```csv
tipequip,codequip,equipment_key,equipment_name,equipment_category
1,01,1:01,Gama Câmara,Diagnóstico por Imagem
1,11,1:11,Tomógrafo Computadorizado,Diagnóstico por Imagem
1,12,1:12,Ressonância Magnética,Diagnóstico por Imagem
1,18,1:18,PET/CT,Diagnóstico por Imagem
4,42,4:42,Eletroencefalógrafo,Métodos Gráficos
5,52,5:52,Bomba de Infusão,Manutenção da Vida
...
```

> ⚠ **Aviso público:** dicionários inferidos por LLM **NÃO** devem ser usados como referência canônica de identificadores em saúde pública — vide WP #6 (descoberta documentada do bug histórico do projeto).

---

## 🚀 Quick start

### Rodar o site localmente

```bash
git clone https://github.com/leonardochalhoub/mirante-dos-dados-br
cd mirante-dos-dados-br/app
npm install
npm run dev
# Abra http://localhost:5173
```

### Rodar tests

```bash
cd mirante-dos-dados-br
pip install pytest
python3 -m pytest tests/ -v
```

### Reproduzir um pipeline (Databricks Free Edition)

```bash
cd mirante-dos-dados-br/pipelines
databricks bundle deploy --target dev
databricks bundle run job_equipamentos_refresh --target dev
```

### Compilar um Working Paper localmente

```bash
cd mirante-dos-dados-br/articles
pdflatex equipamentos-rm-parkinson.tex
pdflatex equipamentos-rm-parkinson.tex   # 2x para resolver \ref e \listoffigures
```

> 📦 **CI compila todos os WPs automaticamente** a cada push em `articles/**`. Veja `.github/workflows/deploy-pages.yml`.

---

## 🎨 Princípios de design

1. **Tudo aberto, tudo versionado.** Código, dados (gold), papers (tex+pdf), dicionários — tudo em Git. Reprodutibilidade total por design.
2. **Bronze STRING-ONLY.** Casts apenas em silver+. Audit trail fiel à fonte ([ADR-003](docs/ARCHITECTURE.md#adr-003--por-quê-bronze-string-only)).
3. **Documentação como código.** ADRs em `docs/ARCHITECTURE.md`, COMMENT ON TABLE no Unity Catalog, docstrings em notebooks.
4. **Tests como contrato.** `tests/` valida invariantes do artefato publicado. Mudou um número? CI quebra.
5. **Reviewers simulados antes de submissão real.** Pareceres internos cobrem ângulos de Eng. Dados, Finanças e HCI.

---

## 🤝 Stack técnica

<div align="center">

| Camada | Tecnologia |
|--------|------------|
| **Pipeline** | Apache Spark · Delta Lake · Databricks Free Edition |
| **Orquestração** | Databricks Asset Bundles · GitHub Actions |
| **Lookup canonical** | Python (parse HTML direto do DATASUS) |
| **Front-end** | React 19 · Vite · recharts · react-simple-maps |
| **Articles** | LaTeX (lmodern, ABNT) · matplotlib (Cividis) |
| **Tests** | pytest puro · zero dependência de Spark |
| **Hosting** | GitHub Pages (static deploy) |

</div>

---

## 📜 Licença

- **Código** (pipelines, front-end, scripts): [MIT](LICENSE)
- **Dados consolidados** (gold JSON, dicionário canonical): [MIT](LICENSE)
- **Textos** (Working Papers, READMEs): [Creative Commons Atribuição 4.0 (CC BY 4.0)](https://creativecommons.org/licenses/by/4.0/deed.pt-br)

> Citar como: CHALHOUB, L. *Mirante dos Dados — pipeline aberto e reproduzível para microdados públicos brasileiros*. Repositório GitHub, 2026. <https://github.com/leonardochalhoub/mirante-dos-dados-br>

---

## 👤 Autor

**Leonardo Chalhoub** — engenheiro de dados, criador da plataforma Mirante.

🐙 [github.com/leonardochalhoub](https://github.com/leonardochalhoub) &nbsp;•&nbsp; ✉️ leonardochalhoub@gmail.com

### Apps grátis do autor (também open-source)

- 💰 [**Caixa Forte**](https://caixa-forte-app.vercel.app) — controle financeiro pessoal, 100\,% gratuito
- 🏫 [**Amazing School**](https://amazing-school-app.vercel.app) — inglês com IA, gratuito
- 🐾 [**PetZap**](https://pet-zap.vercel.app) — vacinas e gastos do pet, via web ou Telegram

---

<div align="center">
<sub>
🇧🇷 · Feito em São Paulo · Construído sobre Apache Spark, Delta Lake e React · Pipeline aberto, dado aberto, código aberto.
</sub>
</div>

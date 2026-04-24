# Pipelines · Mirante dos Dados

Pipelines de dados rodando em **Databricks Free Edition** com **Lakeflow Declarative Pipelines** (DLT)
em arquitetura medallion. Cada vertical do front (`/bolsa-familia`, `/saude-mri`, ...) consome um
JSON gold que é gerado por um job aqui.

## Arquitetura

```
                    ┌─ download_ibge ──┐
                    │                  ├──→ dlt_populacao_uf_ano (DLT)
                    │                  │       └─ mirante.silver.populacao_uf_ano
                    │                  │
                    └──────────────────┘
                                                                  ┌─ valor_2021
                    ┌─ download_bcb ───┐                          ├─ pbfPerCapita
                    │                  ├──→ dlt_ipca_2021  (DLT)  │
                    │                  │       └─ mirante.silver.ipca_deflators_2021
                    └──────────────────┘                          │
                                                                  ▼
                    ┌─ download_cgu ───┐                       ┌──────────────────────┐
                    │                  ├──→ dlt_pbf_medallion ─→ mirante.gold.       │
                    │                  │       (DLT bronze→     │ pbf_estados_df     │
                    │                  │       silver→gold)     └──────────────────────┘
                    └──────────────────┘                                  │
                                                                          ▼
                                                              export_pbf_json (notebook)
                                                                          │
                                                                          ▼
                                                  /Volumes/mirante/gold/exports/
                                                       gold_pbf_estados_df.json
                                                                          │
                                                                          ▼ (GH Action puxa)
                                                              data/gold/gold_pbf_estados_df.json
                                                                          │
                                                                          ▼
                                                                front (GitHub Pages)
```

## Estrutura

```
pipelines/
├── databricks.yml                     ← DAB config (3 DLT pipelines + 3 jobs)
└── notebooks/
    ├── populacao_uf_ano/              ← shared dim · independente
    │   ├── 01_download_ibge.py        Pre-DLT: HTTP fetch IBGE
    │   └── 02_dlt_populacao_uf_ano.py DLT bronze + silver (interpolação linear)
    ├── ipca_deflators_2021/           ← shared dim · independente
    │   ├── 01_download_bcb.py
    │   └── 02_dlt_ipca_deflators.py
    └── pbf/                           ← vertical · refresh mensal
        ├── 01_download_cgu.py         CGU ZIPs (PBF + Auxílio + NBF)
        ├── 02_dlt_pbf_medallion.py    DLT bronze → silver → gold + 8 expectations
        └── 03_export_json.py          gold table → JSON em UC Volume
```

## Unity Catalog layout

```
mirante (catalog)
├── bronze
│   ├── ibge_populacao_raw          ← raw IBGE JSON (1 linha de struct)
│   ├── bcb_ipca_raw                ← raw BCB IPCA JSON
│   └── pbf_pagamentos              ← CSVs CGU descomprimidos, headers normalizados
│       (partitionBy: origin, ano, mes)
├── silver
│   ├── populacao_uf_ano            ← 🔁 SHARED · 27 UFs × N anos · com `fonte` lineage
│   ├── ipca_deflators_2021         ← 🔁 SHARED · Ano × deflator (Dez/2021 = 1.0)
│   └── pbf_total_uf_mes            ← UF × Ano × Mes · n, n_ano, total_estado
│       (partitionBy: Ano)
└── gold
    └── pbf_estados_df              ← UF × Ano · schema bate com o JSON do front
        (partitionBy: Ano)
```

## Volumes

```
mirante.bronze.raw   (HTTP downloads landing zone)
  ├── ibge/populacao_uf.json
  ├── bcb/ipca_mensal.json
  └── cgu/pbf/{PBF,AUX_BR,NBF}_YYYY_MM.zip      (~150 arquivos)

mirante.gold.exports (front-facing exports)
  └── gold_pbf_estados_df.json                  (puxado pelo GH Action)
```

---

## Deploy (passos manuais — 1× só)

Precisa do Databricks CLI v0.200+ instalado:

```bash
# Linux / macOS via Homebrew
brew tap databricks/tap
brew install databricks

# Linux sem brew
curl -fsSL https://github.com/databricks/cli/releases/latest/download/databricks_cli_linux_amd64.tar.gz \
  | tar -xz -C ~/.local/bin
databricks --version
```

### 1. Autenticar (gere um PAT novo, NÃO use o que veio em chat)
```bash
databricks configure --host https://dbc-cafe0a5f-07e3.cloud.databricks.com --token
# cola o PAT (dapi***) quando pedir
```

### 2. Bootstrap do Unity Catalog (catalog + schemas + volumes)
```bash
cd /home/leochalhoub/mirante-dos-dados-br
bash scripts/databricks/bootstrap.sh
```

### 3. Deploy do bundle (sobe os notebooks + cria DLT pipelines + jobs)
```bash
cd pipelines
databricks bundle deploy --target dev
```

### 4. Aquecer dimensões compartilhadas (1× só na 1ª vez)
```bash
databricks bundle run job_populacao_refresh --target dev
databricks bundle run job_ipca_refresh      --target dev
```

### 5. Rodar PBF end-to-end (download → DLT → export)
```bash
databricks bundle run job_pbf_refresh --target dev
# 5–15 min (download CGU é o gargalo: ~150 ZIPs)
```

### 6. Verificar o JSON gerado
```bash
databricks fs cp dbfs:/Volumes/mirante/gold/exports/gold_pbf_estados_df.json /tmp/check.json
python3 -c "import json; d=json.load(open('/tmp/check.json')); print(len(d), d[0])"
```

### 7. (Opcional) commit manual do gold pra validar antes de habilitar o cron
```bash
cp /tmp/check.json /home/leochalhoub/mirante-dos-dados-br/data/gold/gold_pbf_estados_df.json
cd /home/leochalhoub/mirante-dos-dados-br
git add data/gold/ && git commit -m "chore(data): manual gold refresh"
git push  # dispara o GH Action de Pages → site atualiza com novo dado
```

### 8. Automatizar via GitHub Actions (cron mensal)
- Repo no GitHub → **Settings → Secrets and variables → Actions → New secret**:
  - `DATABRICKS_HOST` = `https://dbc-cafe0a5f-07e3.cloud.databricks.com`
  - `DATABRICKS_TOKEN` = (gere um PAT novo, comment "mirante-gh-actions", nunca cole no chat)
- O workflow `.github/workflows/refresh-pipelines.yml` já está pronto pra:
  - Disparar `job_pbf_refresh` no dia 20 de cada mês às 6h UTC
  - Baixar o gold JSON do Volume
  - Commitar em `data/gold/` se mudou
  - Push → GH Pages re-deploya automático

---

## Adicionar um novo vertical (ex: MRI)

1. Crie `notebooks/mri/01_download_datasus.py` (HTTP/FTP fetch dos arquivos CNES)
2. Crie `notebooks/mri/02_dlt_mri_medallion.py` (DLT bronze → silver → gold).
   No gold, faça `spark.read.table("mirante.silver.populacao_uf_ano")` pra reutilizar a dim.
3. Crie `notebooks/mri/03_export_json.py` (mesmo padrão do PBF)
4. Adicione no `databricks.yml`:
   - DLT pipeline `mri_dlt`
   - Job `job_mri_refresh` com tasks `download_datasus → dlt_mri → export_mri_json`
5. `databricks bundle deploy --target dev` — cria o novo job
6. Adicione um segundo step no GH Action de refresh pra puxar o JSON novo

A dim `populacao_uf_ano` **não** precisa ser republicada — o vertical novo só consome.

---

## Quando refrescar manualmente

| Pipeline | Quando rodar | Comando |
|---|---|---|
| `populacao_uf_ano` | Quando IBGE publicar novo ano (~julho) | `databricks bundle run job_populacao_refresh --target dev` |
| `ipca_deflators_2021` | Mensal automático (cron dia 15) | já agendado quando você unpause |
| `pbf` | Mensal automático (cron dia 20) | já agendado quando você unpause |

Pra **estender o range de anos** (ex: incluir 2027 no panel quando IBGE publicar):
```bash
databricks bundle run job_populacao_refresh --target dev \
  --params start_year=2013,end_year=2027
```
E atualizar o `databricks.yml` (`mirante.populacao.year_max: "2027"`) e redeployar.

---

## Custo (Free Edition)

- DLT serverless: até X DBU/mês grátis no Free Tier
- Os 3 pipelines completos consomem ~5 min de DLT serverless/refresh = ~poucos centavos de DBU equivalente
- Volume de dados em UC: irrisório (CSVs CGU ≈ 200MB total, JSONs < 1MB)
- Fica MUITO dentro do cap mensal do Free Edition

---

## Troubleshooting

**`bundle deploy` falha com "catalog not found"**
→ rode `bash scripts/databricks/bootstrap.sh` primeiro

**DLT pipeline falha com "table not found: mirante.silver.populacao_uf_ano"**
→ rode `job_populacao_refresh` antes do `job_pbf_refresh` (o gold do PBF lê dessa dim)

**Download CGU retorna `missing` em todos**
→ Portal da Transparência às vezes está fora do ar; rode novamente em algumas horas

**JSON gerado tem números errados**
→ Compare com o JSON local em `data/gold/gold_pbf_estados_df.json` antes do refresh.
   Se 2025 per_benef ≠ 5825.32, alguma coisa quebrou na agregação.

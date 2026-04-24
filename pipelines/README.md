# Pipelines · Mirante dos Dados

Pipelines de dados rodando em **Databricks Free Edition**, arquitetura medallion
em **Delta Lake puro** (sem DLT, sem materialized views — Delta com history,
time travel, OPTIMIZE, MERGE, etc.).

## Princípios

- **Auto Loader** (`cloudFiles`) ingere arquivos novos do UC Volume → bronze append-only
- **Bronze** preserva o payload bruto (full struct das APIs / CSVs CGU completos)
- **Silver** lê o snapshot mais recente do bronze, transforma, overwrite
- **Gold** junta silvers, overwrite
- **Cascata:** o DAG do job garante ingest → bronze → silver → gold → export em ordem
- **History:** bronze é append-only (every refresh preserved); silver/gold via Delta time travel
- **One notebook per table:** folder = camada, filename = nome da tabela

## Folder layout

```
pipelines/
├── databricks.yml              DAB config (3 jobs, notebook tasks only)
└── notebooks/
    ├── ingest/                 HTTP downloads → UC Volume (timestamped filenames)
    │   ├── ibge_populacao.py
    │   ├── bcb_ipca.py
    │   └── cgu_pbf_zips.py
    ├── bronze/                 Auto Loader + writeStream(availableNow) → Delta
    │   ├── ibge_populacao_raw.py     →  mirante_prd.bronze.ibge_populacao_raw
    │   ├── bcb_ipca_raw.py           →  mirante_prd.bronze.bcb_ipca_raw
    │   └── pbf_pagamentos.py         →  mirante_prd.bronze.pbf_pagamentos
    ├── silver/                 batch read latest bronze → Delta overwrite
    │   ├── populacao_uf_ano.py       →  mirante_prd.silver.populacao_uf_ano
    │   ├── ipca_deflators_2021.py    →  mirante_prd.silver.ipca_deflators_2021
    │   └── pbf_total_uf_mes.py       →  mirante_prd.silver.pbf_total_uf_mes
    ├── gold/                   batch joins → Delta overwrite
    │   └── pbf_estados_df.py         →  mirante_prd.gold.pbf_estados_df
    └── export/                 gold table → JSON in UC Volume
        └── pbf_estados_df_json.py
```

## Unity Catalog layout

```
mirante_prd (catalog · created via UI on Free Edition)
├── bronze (schema)
│   ├── ibge_populacao_raw     ← append: 1 row por refresh do IBGE (full payload)
│   ├── bcb_ipca_raw           ← append: ~1 linha por mês de IPCA por refresh
│   └── pbf_pagamentos         ← append: linhas dos CSVs CGU (partition: origin, ano)
├── silver (schema)
│   ├── populacao_uf_ano       ← 🔁 SHARED · 27 UFs × N anos · com `fonte` lineage
│   ├── ipca_deflators_2021    ← 🔁 SHARED · Ano × deflator (Dez/2021 = 1.0)
│   └── pbf_total_uf_mes       ← UF × Ano × Mes · n, n_ano, total_estado (partition: Ano)
└── gold (schema)
    └── pbf_estados_df         ← UF × Ano · schema bate com JSON do front (partition: Ano)
```

## Volumes

```
mirante_prd.bronze.raw              Source landing zone (Auto Loader watches these)
  ├── ibge/populacao_uf__YYYYMMDDTHHMMSSZ.json   ← timestamped per refresh
  ├── bcb/ipca_mensal__YYYYMMDDTHHMMSSZ.json
  └── cgu/pbf/<PROGRAM>_YYYY_MM.zip              ← already named by program/period
mirante_prd.bronze._autoloader      Auto Loader checkpoints + schemas (managed)
mirante_prd.bronze.raw/cgu/pbf_csv_extracted    ZIPs descomprimidos (intermediário)
mirante_prd.gold.exports
  └── gold_pbf_estados_df.json                   ← consumido pelo GH Action
```

## Job DAGs

```
job_populacao_refresh    (yearly cron: Jul 1, paused by default)
  ingest_ibge → bronze_ibge_populacao_raw → silver_populacao_uf_ano

job_ipca_refresh         (monthly cron: day 15, paused)
  ingest_bcb → bronze_bcb_ipca_raw → silver_ipca_deflators_2021

job_pbf_refresh          (monthly cron: day 20, paused)
  ingest_cgu_pbf_zips → bronze_pbf_pagamentos → silver_pbf_total_uf_mes →
  gold_pbf_estados_df → export_pbf_estados_df_json
```

Cascata é automática: `depends_on` garante que silver só roda após bronze, etc.

---

## Deploy (1× só)

```bash
# 1. Instala Databricks CLI v0.200+
curl -fsSL https://raw.githubusercontent.com/databricks/setup-cli/main/install.sh | sudo sh

# 2. Autentica (gera PAT NOVO no workspace, NÃO use o que já vazou)
databricks configure --host https://dbc-cafe0a5f-07e3.cloud.databricks.com --token

# 3. Cria catalog mirante_prd via UI (Free Edition limitation):
#    https://dbc-cafe0a5f-07e3.cloud.databricks.com/explore/data
#    → Create catalog → Name: mirante_prd → Storage: Default → Create

# 4. Bootstrap (cria schemas + volumes; catalog já criado pela UI)
cd ~/mirante-dos-dados-br
bash scripts/databricks/bootstrap.sh

# 5. Deploy do bundle (3 jobs)
cd pipelines
databricks bundle deploy --target dev

# 6. Aquecer dimensões compartilhadas (1× só)
databricks bundle run job_populacao_refresh --target dev
databricks bundle run job_ipca_refresh      --target dev

# 7. PBF end-to-end
databricks bundle run job_pbf_refresh --target dev

# 8. Verificar JSON gerado
databricks fs cp dbfs:/Volumes/mirante_prd/gold/exports/gold_pbf_estados_df.json /tmp/check.json
python3 -c "import json; d=json.load(open('/tmp/check.json')); print(len(d), d[0])"
# espera 351 linhas, 2025 per_benef ≈ 5825.32
```

---

## Inspecionar history

Bronze (append-only — every refresh preserved):
```sql
SELECT _ingest_ts, COUNT(*) FROM mirante_prd.bronze.ibge_populacao_raw GROUP BY _ingest_ts ORDER BY _ingest_ts;
```

Silver/Gold (Delta time travel — overwritten each refresh, prior versions still queryable):
```sql
DESCRIBE HISTORY mirante_prd.silver.populacao_uf_ano;
SELECT * FROM mirante_prd.silver.populacao_uf_ano VERSION AS OF 3;
SELECT * FROM mirante_prd.silver.populacao_uf_ano TIMESTAMP AS OF '2026-04-01 00:00:00';
```

---

## Adicionar novo vertical (ex: MRI)

1. `notebooks/ingest/datasus_cnes_eq.py` — fetch CSVs/dbc DATASUS → Volume
2. `notebooks/bronze/cnes_equipamentos.py` — Auto Loader → Delta append
3. `notebooks/silver/mri_uf_ano.py` — agrega CNES por UF×Ano (split SUS/Privado)
4. `notebooks/gold/mri_estados_ano.py` — join `silver.populacao_uf_ano` (dim compartilhada!)
5. `notebooks/export/mri_estados_ano_json.py`
6. Adicionar `job_mri_refresh` no `databricks.yml`
7. `databricks bundle deploy --target dev`
8. Adicionar etapa no GH Action de refresh pra puxar o novo JSON

A dim `populacao_uf_ano` **não** precisa ser republicada — vertical novo só consome.

---

## Estendendo range de anos (ex: 2027 quando IBGE publicar)

```bash
# 1. Roda ingest com novo range
databricks bundle run job_populacao_refresh --target dev \
  --params start_year=2013,end_year=2027

# 2. Atualiza silver year_max no databricks.yml + redeploy
sed -i 's/year_max: "2026"/year_max: "2027"/g' pipelines/databricks.yml
cd pipelines && databricks bundle deploy --target dev
```

---

## Troubleshooting

| Sintoma | Causa | Fix |
|---|---|---|
| `bundle deploy` falha "catalog not found" | Catalog `mirante_prd` não criado via UI | UI Catalog Explorer → Create Catalog |
| Bronze table vazia após task ingest_X | Arquivo não chegou no Volume, ou Auto Loader checkpoint corrompido | `ls /Volumes/.../bronze/raw/...` no notebook; ou apaga `_autoloader/_checkpoint` |
| Silver falha "BRONZE is empty" | Bronze ainda não rodou nessa run | Job DAG já cuida disso via depends_on; se rodando manual, roda bronze antes |
| Gold falha "table not found: silver.populacao_uf_ano" | Esqueceu de aquecer dims compartilhadas | `databricks bundle run job_populacao_refresh --target dev` |
| Auto Loader não pega arquivo novo | Schema location ficou stuck | `dbutils.fs.rm("dbfs:/Volumes/.../_autoloader/_schema", recurse=True)` |

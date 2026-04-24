# Architecture · Mirante dos Dados

## Princípios

1. **O pipeline é o produto.** O site é a vitrine.
2. **Source of truth dos dados:** `/data/gold/*.json` — o que o pipeline grava aqui é o que o front consome.
3. **Stack 100% gratuito** (até estourar caps): Databricks Free Edition, GitHub Actions, GitHub Pages.
4. **Cada vertical é independente.** Pipeline próprio + JSON gold próprio + rota própria. Verticais não compartilham
   schema; compartilham componentes do front.

## Camadas

### 1. Bronze (raw)

- Cada fonte (CGU, DATASUS, IBGE, BCB) é baixada *as-is* (CSV, ZIP, JSON da API).
- Persistida em Unity Catalog como tabela Delta com tipos preservados (string, na maioria).
- Sem cleanup, sem typing forte. Objetivo: idempotência e reproducibilidade.

### 2. Silver (clean / typed / dedup)

- Cast pra tipos corretos.
- Normalização de unidades (R$, ano, UF sigla).
- Deduplicação por chave natural.
- Joins quando faz sentido (ex: PBF + população + IPCA).

### 3. Gold (agregado por vertical)

- Saída em JSON, escala MB, agregado num nível que o front renderize **sem cálculos pesados**.
- Cada gold é um array de objetos com schema estável.
- Schema documentado em `docs/contracts/<vertical>.md` (a fazer).

## Rotação de refresh

- **GitHub Action** cron mensal (`0 6 1 * *`) dispara job no Databricks via REST API
  (`POST /api/2.1/jobs/run-now` com `DATABRICKS_TOKEN`).
- Job termina, action puxa novos golds via REST e commita em `/data/gold/`.
- Push em `main` dispara o workflow de deploy → site atualizado.

## Versionamento de dados

- Cada gold JSON é commitado no repo. Histórico = `git log -- data/gold/<arquivo>.json`.
- Contratos imutáveis: mudança de schema requer bump de major no nome do arquivo
  (ex: `gold_pbf_estados_df.json` → `gold_pbf_estados_df_v2.json`) e duplo-publish até front migrar.

## Trade-offs explícitos

| Decisão                                    | Por quê                                                                |
| ------------------------------------------ | ---------------------------------------------------------------------- |
| Sem dbt na v1                              | Volume pequeno demais (<1M linhas); Spark SQL puro basta              |
| Sem banco transacional                     | Dado público agregado é melhor como JSON estático                      |
| HashRouter (não BrowserRouter)             | GitHub Pages serve estático, não tem rewrite rules                     |
| Gold JSON no git (não release artifact)    | Diff visível, fácil pra contributors auditarem mudança de dados        |
| Plotly (não Recharts/Visx)                 | Mapas choropleth + interatividade já prontos sem custo de dev          |

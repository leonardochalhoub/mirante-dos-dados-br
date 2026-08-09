# Bolsa Família Knowledge Hub — Ledger + Memory + Brain

Servidor [MCP](https://modelcontextprotocol.io) local que dá ao Claude Code
contexto de três tipos sobre o domínio Bolsa Família deste repo, no mesmo
padrão descrito em [`docs/rag-knowledge-hub-kickoff.md`](../docs/rag-knowledge-hub-kickoff.md)
e inspirado no formato do workshop `workshop1-aide`:

| Domínio | Responde | Implementação | Tool |
|---|---|---|---|
| **Ledger** | Números, agregações, séries (só QUERY, ao vivo) | SQL read-only no Unity Catalog `mirante_prd` via `databricks-sql-connector` | `query_ledger`, `list_ledger_tables` |
| **Memory** | Documentos, contexto, "o que isso significa" | Busca vetorial local (Qdrant, container) sobre o artigo WP2 (o que estamos tentando publicar), ADRs, documentação externa curada e os **comentários do Unity Catalog** | `search_memory`, `get_document` |
| **Brain** | Lineage, dependência, impacto | Cypher read-only (Neo4j, container) sobre um grafo construído por **parsing estático** de `pipelines/databricks.yml` + notebooks — não por LLM | `query_brain` |

## Por que não é o docker-compose completo do workshop

O `workshop1-aide` (e o `ws-1-llama-index-rag`) rodam Postgres + Mongo +
Qdrant + Neo4j + SeaweedFS + FastAPI + um gerador de dados sintéticos — faz
sentido lá porque os dados são fictícios e o objetivo é ensinar o padrão
completo. Aqui os dados são reais e já têm dono:

- **Ledger não precisa de Postgres** — os números já vivem, governados, no
  Unity Catalog. Reusar o padrão do `conselho_mcp` (SQL ao vivo) evita
  duplicar dado.
- **Memory não precisa de Mongo/SeaweedFS** — não há logs/documentos
  dinâmicos chegando; o corpus é ~45 arquivos versionados no próprio repo.
- **Sem FastAPI/roteador com LLM próprio** — quem chama este servidor
  (Claude Code) já decide qual tool usar pela descrição de cada uma. Rodar
  um segundo LLM só para rotear seria custo e complexidade sem propósito.

O que sobrou do padrão do workshop — Qdrant e Neo4j containerizados — é
exatamente a parte que faltava (o `conselho_mcp` já cobria Ledger+Memory sem
container nenhum; Brain é novo).

## Setup

```bash
conda activate dev-env
pip install -r bolsa_familia_hub/requirements.txt

cp bolsa_familia_hub/.env.example bolsa_familia_hub/.env
# preencha DATABRICKS_* (mesmas credenciais do conselho_mcp/.env) e NEO4J_PASSWORD
chmod 600 bolsa_familia_hub/.env

docker compose -f bolsa_familia_hub/docker-compose.yml up -d
# Qdrant em localhost:6343 (não 6333 — já ocupado por workshop1-aide neste host)
# Neo4j  em localhost:7688 bolt / :7475 browser (não 7687/7474, mesmo motivo)

cd bolsa_familia_hub
python uc_metadata.py      # extrai comentários do Unity Catalog -> docs_sources/uc_metadata/
python build_index.py      # indexa o corpus (artigo + ADRs + docs externas + UC metadata) no Qdrant
python build_graph.py --load   # parseia databricks.yml + notebooks, carrega lineage no Neo4j
```

Registrado em [`.mcp.json`](../.mcp.json) como `bolsa_familia`. Numa sessão
nova do Claude Code, é só perguntar — ele escolhe a tool certa pela descrição.

## Reindexar

Rode de novo sempre que:
- o artigo (`articles/wp2-ppp.*`) ou os ADRs mudarem → `python build_index.py`
- `pipelines/databricks.yml` ou os notebooks mudarem → `python build_graph.py --load`
- os comentários das tabelas no Unity Catalog mudarem → `python uc_metadata.py && python build_index.py`

`docs_sources/uc_metadata/` é gitignored (artefato reproduzível, como o
índice do `conselho_mcp`). O resto de `docs_sources/` (documentação externa
curada) é versionado — foi buscado uma vez via WebFetch, não é re-scraped em
runtime.

## Fontes externas curadas (docs_sources/)

- `databricks/` — medallion architecture, Auto Loader, Unity Catalog
- `delta-lake/` — time travel, append/overwrite, schema evolution
- `spark/` — DataFrame API, Spark SQL
- `cgu-pbf/` — Portal da Transparência (dataset de pagamentos)
- `ibge-sidra/` — Tabela 6579 (população estimada)

Cada arquivo cita a URL-fonte e, quando relevante, aponta para o notebook/ADR
deste repo que aplica aquele conceito — o objetivo é dar contexto, não só
depositar a doc oficial.

## Credenciais

Mesmo padrão do `conselho_mcp`: `.env` gitignored, perms 600, carregado por
`config.py`. As credenciais Databricks são as mesmas do `conselho_mcp/.env`
(mesmo warehouse `mirante_prd`).

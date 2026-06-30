# Conselho MCP — KB + RAG + MCP para os conselheiros do Mirante

Servidor [MCP](https://modelcontextprotocol.io) local que dá aos 4 conselheiros
(subagents em [`.claude/agents/`](../.claude/agents/)) três capacidades reais —
as mesmas três que aparecem no workshop:

| Sigla | O que é aqui | Implementação |
|-------|--------------|---------------|
| **KB**  | Base de conhecimento curada | [`corpus.py`](corpus.py) — manifesto dos Working Papers (`articles/*.tex`) + ADRs + pareceres do Conselho (`docs/**/*.md`) |
| **RAG** | Retrieval que devolve **trechos** relevantes (não o doc inteiro), com citação | índice vetorial local (embeddings `intfloat/multilingual-e5-small`, 384-d) + cosseno → tool `search_corpus` |
| **MCP** | Protocolo de acesso direto ao Unity Catalog `mirante_prd` | `databricks-sql-connector` contra um SQL warehouse ao vivo → tools `databricks_query` / `list_tables` |

> Nota conceitual: **RAG ≠ "a bíblia inteira no contexto".** O corpus é a fonte;
> RAG é o método que **recupera as passagens relevantes** por consulta. Por isso
> `search_corpus` devolve top-k trechos com `arquivo · seção`, não o texto todo.

## Tools expostas
- `search_corpus(query, k=5)` → top-k trechos relevantes do corpus, com citação e score.
- `get_document(doc_id)` → texto-fonte limpo de um doc (`doc_id` vem das citações).
- `databricks_query(sql_text, max_rows=200)` → SQL **read-only** no `mirante_prd`.
- `list_tables(layer)` → schemas/tabelas; `layer` opcional: `bronze|silver|gold`.

## Setup

```bash
conda activate dev-env
pip install -r conselho_mcp/requirements.txt
python conselho_mcp/build_index.py        # constrói o índice (40 docs → ~1.5k chunks)
```

O índice fica em `conselho_mcp/index/` (gitignored — é reproduzível). Rode
`build_index.py` de novo sempre que os Working Papers/ADRs/pareceres mudarem.

## Credenciais Databricks (para os tools de Databricks ao vivo)

O servidor lê de `conselho_mcp/.env` (gitignored, perms 600), carregado em
`server.py::_load_dotenv()`. Formato:

```dotenv
DATABRICKS_SERVER_HOSTNAME=dbc-cafe0a5f-07e3.cloud.databricks.com
DATABRICKS_HTTP_PATH=/sql/1.0/warehouses/<WAREHOUSE_ID>   # SQL warehouse → Connection details
DATABRICKS_TOKEN=dapi...                                  # PAT (User Settings → Developer)
MIRANTE_CATALOG=mirante_prd
```

Segredos ficam fora do `.mcp.json` e do shell. Variáveis já presentes no
ambiente têm precedência sobre o `.env`. Sem credenciais, `search_corpus`/
`get_document` funcionam normalmente e os tools de Databricks retornam um erro
explicando o que falta (não derrubam o server). Apenas
`SELECT/WITH/SHOW/DESCRIBE/EXPLAIN` são aceitos — escrita é bloqueada.

## Como os conselheiros usam

[`.mcp.json`](../.mcp.json) registra este server como `conselho`; o frontmatter de
cada conselheiro lista `mcp__conselho__*` em `tools:`. Numa nova sessão do Claude
Code, peça a um conselheiro algo como *"fundamente seu parecer no que dizem nossos
ADRs"* e ele chamará `search_corpus`; *"confira o volume real na gold"* e ele
chamará `databricks_query`.

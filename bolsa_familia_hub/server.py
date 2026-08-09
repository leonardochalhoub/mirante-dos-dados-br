"""Servidor MCP do Bolsa Família Knowledge Hub.

Ledger + Memory + Brain, mesmo padrão do `conselho_mcp/`, com um Brain novo:

  Ledger  → query_ledger()/list_ledger_tables(): SQL read-only ao vivo no
            Unity Catalog (mirante_prd). Só QUERY — comentários/metadados de
            tabela NÃO vêm daqui, vêm do Memory (ver uc_metadata.py).
  Memory  → search_memory()/get_document(): busca vetorial local (Qdrant) sobre
            o artigo WP2 (o que estamos tentando publicar), ADRs, documentação
            externa curada (Databricks/Delta/Spark/CGU/IBGE) e os comentários
            extraídos do Unity Catalog.
  Brain   → query_brain(): Cypher read-only no Neo4j sobre o grafo de lineage
            real (Job/Task/Table), construído por parsing estático de
            pipelines/databricks.yml + notebooks — não é um grafo narrativo
            gerado por LLM.

Sem FastAPI e sem roteador com LLM próprio: quem chama este servidor (Claude
Code) já é o roteador — decide qual tool usar pela descrição de cada uma,
exatamente como já funciona no conselho_mcp.

Transporte: stdio. Registrado em <repo>/.mcp.json como "bolsa_familia".
"""
from __future__ import annotations

import re

import numpy as np
from mcp.server.fastmcp import FastMCP

import config
from corpus import REPO_ROOT, load_text

mcp = FastMCP("bolsa_familia")

# ─── Memory (Qdrant) ─────────────────────────────────────────────────────────
_ST_MODEL = None


def _st_model():
    global _ST_MODEL
    if _ST_MODEL is None:
        from sentence_transformers import SentenceTransformer

        _ST_MODEL = SentenceTransformer(config.EMBEDDING_MODEL)
    return _ST_MODEL


def _qdrant_client():
    from qdrant_client import QdrantClient

    return QdrantClient(host=config.QDRANT_HOST, port=config.QDRANT_PORT)


@mcp.tool()
def search_memory(query: str, k: int = 5) -> str:
    """Busca semântica no Memory do Bolsa Família Knowledge Hub.

    Cobre: o artigo WP2 que estamos tentando publicar (texto completo +
    referências), ADRs de arquitetura do pipeline, documentação externa
    curada (medallion architecture, Auto Loader, Delta Lake time travel,
    Spark SQL, Unity Catalog, dataset CGU/PBF, SIDRA/IBGE), e os comentários
    de tabela/coluna extraídos do Unity Catalog (o que cada tabela/coluna
    significa). Use para "o que é X", "por que fizemos Y", "o que essa
    coluna significa", "o que a documentação da fonte diz sobre Z".
    NÃO use para números atuais — isso é query_ledger.

    Retorna os k trechos mais relevantes com citação (doc_id · seção) e score.
    """
    qvec = (
        _st_model()
        .encode([f"query: {query}"], normalize_embeddings=True, convert_to_numpy=True)[0]
        .tolist()
    )
    hits = _qdrant_client().query_points(
        collection_name=config.QDRANT_COLLECTION,
        query=qvec,
        limit=max(1, min(int(k), 20)),
    ).points
    if not hits:
        return "Nenhum resultado."
    out = []
    for rank, h in enumerate(hits, 1):
        p = h.payload
        out.append(f"[{rank}] {p['doc_id']} · {p['section']}  (score {h.score:.3f})\n{p['text']}")
    return "\n\n---\n\n".join(out)


@mcp.tool()
def get_document(doc_id: str) -> str:
    """Retorna o texto-fonte limpo de um documento do Memory.

    doc_id é o caminho relativo ao repo (ex.: 'articles/wp2-ppp.tex' ou
    'bolsa_familia_hub/docs_sources/databricks/medallion-architecture.md'),
    como aparece nas citações de search_memory.
    """
    path = (REPO_ROOT / doc_id).resolve()
    if REPO_ROOT not in path.parents or not path.exists():
        return f"Documento não encontrado ou fora do corpus: {doc_id}"
    return load_text(path)


# ─── Ledger (Databricks — só query, sem metadados) ──────────────────────────
_READONLY_RE = re.compile(r"^\s*(with|select|show|describe|desc|explain)\b", re.IGNORECASE)


@mcp.tool()
def query_ledger(sql_text: str, max_rows: int = 200) -> str:
    """Executa SQL READ-ONLY no Unity Catalog mirante_prd (warehouse ao vivo).

    Ledger é só para NÚMEROS: agregações, séries, top-N sobre as tabelas
    bronze/silver/gold do Bolsa Família (e dimensões compartilhadas como
    população e deflatores IPCA). Para "o que essa tabela/coluna significa",
    use search_memory — os comentários do Unity Catalog já estão lá.
    Apenas SELECT/WITH/SHOW/DESCRIBE/EXPLAIN são permitidos.
    """
    if not _READONLY_RE.match(sql_text):
        return "Bloqueado: apenas consultas read-only (SELECT/WITH/SHOW/DESCRIBE/EXPLAIN)."
    try:
        with config.databricks_connection() as conn, conn.cursor() as cur:
            cur.execute(sql_text)
            cols = [d[0] for d in cur.description] if cur.description else []
            rows = cur.fetchmany(max(1, int(max_rows)))
    except Exception as e:  # noqa: BLE001 — devolve a falha ao agente, não derruba o server
        return f"Erro Databricks: {e}"
    if not cols:
        return "(sem resultado)"
    header = " | ".join(cols)
    body = "\n".join(" | ".join("" if v is None else str(v) for v in r) for r in rows)
    return f"{header}\n{'-' * len(header)}\n{body}\n\n({len(rows)} linha(s))"


@mcp.tool()
def list_ledger_tables(layer: str = "") -> str:
    """Lista tabelas do mirante_prd. layer opcional: bronze | silver | gold."""
    if layer:
        return query_ledger(f"SHOW TABLES IN {config.CATALOG}.{layer}")
    return query_ledger(f"SHOW SCHEMAS IN {config.CATALOG}")


# ─── Brain (Neo4j — lineage real, sem LLM na construção) ────────────────────
_WRITE_CLAUSE_RE = re.compile(
    r"\b(CREATE|MERGE|DELETE|DETACH|SET|REMOVE|DROP|LOAD\s+CSV)\b", re.IGNORECASE
)


@mcp.tool()
def query_brain(cypher: str, max_rows: int = 100) -> str:
    """Executa Cypher READ-ONLY no grafo de lineage (Brain) do pipeline Databricks.

    Schema do grafo (gerado por bolsa_familia_hub/build_graph.py a partir de
    pipelines/databricks.yml + parsing estático dos notebooks — não inferido
    por LLM):

    Nós:
      Table(full_name, schema, name, layer)   ex.: full_name='gold.pbf_estados_df'
      Job(name, domain)                        ex.: domain='pbf'
      Task(key, notebook_path)

    Relacionamentos:
      (Job)-[:HAS_TASK]->(Task)
      (Task)-[:PRECEDES]->(Task)        ordem de execução (depends_on no YAML)
      (Task)-[:READS_FROM]->(Table)
      (Task)-[:WRITES_TO]->(Table)
      (Table)-[:FEEDS]->(Table)         atalho: lineage tabela -> tabela

    Exemplos:
      "De onde vem gold.pbf_estados_df?"
        MATCH (a:Table)-[:FEEDS*1..5]->(b:Table {full_name:'gold.pbf_estados_df'})
        RETURN DISTINCT a.full_name
      "O que quebra se bronze.pbf_pagamentos mudar?"
        MATCH (a:Table {full_name:'bronze.pbf_pagamentos'})-[:FEEDS*1..5]->(b:Table)
        RETURN DISTINCT b.full_name
      "Quais jobs tocam tabelas do domínio pbf?"
        MATCH (j:Job {domain:'pbf'})-[:HAS_TASK]->(t:Task) RETURN j.name, t.key

    Use para perguntas de dependência/impacto: "de onde vem X", "o que
    depende de Y", "quais tasks alimentam essa tabela". Escreva o Cypher
    você mesmo usando o schema acima — este tool só executa e formata,
    não gera a query.
    """
    if _WRITE_CLAUSE_RE.search(cypher):
        return "Bloqueado: apenas leitura (MATCH/RETURN/WITH/UNWIND). CREATE/MERGE/DELETE/SET/DROP não são permitidos."
    from neo4j import GraphDatabase

    driver = GraphDatabase.driver(config.NEO4J_URI, auth=(config.NEO4J_USER, config.NEO4J_PASSWORD))
    try:
        with driver.session() as session:
            result = session.run(cypher)
            rows = [r.data() for r in result][: max(1, int(max_rows))]
    except Exception as e:  # noqa: BLE001
        return f"Erro Neo4j: {e}"
    finally:
        driver.close()
    if not rows:
        return "(sem resultado)"
    return "\n".join(str(r) for r in rows) + f"\n\n({len(rows)} linha(s))"


if __name__ == "__main__":
    mcp.run()

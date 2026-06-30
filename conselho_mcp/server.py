"""Servidor MCP do Conselho do Mirante.

Expõe três capacidades aos conselheiros (subagents do Claude Code):

  KB   → manifesto curado do corpus (corpus.py)
  RAG  → search_corpus(): retrieval vetorial local sobre os Working Papers/ADRs/
         pareceres, devolvendo TRECHOS relevantes com citação (não o doc inteiro)
  MCP  → este servidor é o protocolo; databricks_query()/list_tables() dão acesso
         direto ao Unity Catalog mirante_prd

Transporte: stdio. Registrado em <repo>/.mcp.json como "conselho".

Credenciais Databricks (lidas do ambiente / ~/.databrickscfg):
    DATABRICKS_SERVER_HOSTNAME   ex.: dbc-cafe0a5f-07e3.cloud.databricks.com
    DATABRICKS_HTTP_PATH         ex.: /sql/1.0/warehouses/<warehouse_id>
    DATABRICKS_TOKEN             PAT (dapi...) ou OAuth
"""
from __future__ import annotations

import json
import os
import re
from pathlib import Path

import numpy as np
from mcp.server.fastmcp import FastMCP

from corpus import REPO_ROOT, chunk_text, load_text

def _load_dotenv() -> None:
    """Carrega conselho_mcp/.env (gitignored) para o ambiente, se existir.

    Mantém segredos fora do .mcp.json e do shell — o server lê daqui quando o
    Claude Code o lança. Variáveis já presentes no ambiente têm precedência.
    """
    env_path = Path(__file__).resolve().parent / ".env"
    if not env_path.exists():
        return
    for line in env_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, val = line.partition("=")
        os.environ.setdefault(key.strip(), val.strip().strip('"').strip("'"))


_load_dotenv()

INDEX_DIR = Path(__file__).resolve().parent / "index"
DEFAULT_CATALOG = os.environ.get("MIRANTE_CATALOG", "mirante_prd")

mcp = FastMCP("conselho")

# ─── Estado do índice RAG (lazy) ────────────────────────────────────────────
_STATE: dict = {}


def _load_index() -> dict:
    if _STATE:
        return _STATE
    meta = json.loads((INDEX_DIR / "meta.json").read_text(encoding="utf-8"))
    emb = np.load(INDEX_DIR / "embeddings.npy")
    chunks = [json.loads(line) for line in (INDEX_DIR / "chunks.jsonl").read_text(encoding="utf-8").splitlines() if line.strip()]
    from sentence_transformers import SentenceTransformer

    model = SentenceTransformer(meta["model"])
    _STATE.update(meta=meta, emb=emb, chunks=chunks, model=model)
    return _STATE


# ─── RAG ────────────────────────────────────────────────────────────────────
@mcp.tool()
def search_corpus(query: str, k: int = 5) -> str:
    """Busca semântica nos Working Papers, ADRs e pareceres do Conselho.

    Retorna os k trechos mais relevantes com citação (arquivo · seção) e score.
    Use para fundamentar pareceres em evidência do próprio repositório.
    """
    st = _load_index()
    qprefix = st["meta"].get("query_prefix", "")
    qvec = st["model"].encode([qprefix + query], normalize_embeddings=True, convert_to_numpy=True).astype(np.float32)
    scores = (st["emb"] @ qvec[0])
    k = max(1, min(int(k), len(st["chunks"])))
    top = np.argsort(-scores)[:k]
    out = []
    for rank, i in enumerate(top, 1):
        c = st["chunks"][i]
        out.append(
            f"[{rank}] {c['doc_id']} · {c['section']}  (score {scores[i]:.3f})\n{c['text']}"
        )
    return "\n\n---\n\n".join(out) if out else "Nenhum resultado."


@mcp.tool()
def get_document(doc_id: str) -> str:
    """Retorna o texto-fonte limpo de um documento do corpus.

    doc_id é o caminho relativo ao repo (ex.: 'docs/adrs/ADR-001-...md'),
    como aparece nas citações de search_corpus.
    """
    path = (REPO_ROOT / doc_id).resolve()
    if REPO_ROOT not in path.parents or not path.exists():
        return f"Documento não encontrado ou fora do corpus: {doc_id}"
    return load_text(path)


# ─── Databricks (MCP → Unity Catalog) ───────────────────────────────────────
_READONLY_RE = re.compile(r"^\s*(with|select|show|describe|desc|explain)\b", re.IGNORECASE)


def _dbx_connection():
    host = os.environ.get("DATABRICKS_SERVER_HOSTNAME")
    http_path = os.environ.get("DATABRICKS_HTTP_PATH")
    token = os.environ.get("DATABRICKS_TOKEN")
    missing = [n for n, v in [
        ("DATABRICKS_SERVER_HOSTNAME", host),
        ("DATABRICKS_HTTP_PATH", http_path),
        ("DATABRICKS_TOKEN", token),
    ] if not v]
    if missing:
        raise RuntimeError(f"Credenciais Databricks ausentes: {', '.join(missing)}")
    from databricks import sql

    return sql.connect(server_hostname=host, http_path=http_path, access_token=token)


@mcp.tool()
def databricks_query(sql_text: str, max_rows: int = 200) -> str:
    """Executa SQL READ-ONLY no Unity Catalog mirante_prd (warehouse ao vivo).

    Apenas SELECT/WITH/SHOW/DESCRIBE/EXPLAIN são permitidos. Retorna até
    max_rows linhas em formato tabular. Use para checar dados reais das
    camadas bronze/silver/gold ao emitir pareceres.
    """
    if not _READONLY_RE.match(sql_text):
        return "Bloqueado: apenas consultas read-only (SELECT/WITH/SHOW/DESCRIBE/EXPLAIN)."
    try:
        with _dbx_connection() as conn, conn.cursor() as cur:
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
def list_tables(layer: str = "") -> str:
    """Lista tabelas do mirante_prd. layer opcional: bronze | silver | gold."""
    if layer:
        return databricks_query(f"SHOW TABLES IN {DEFAULT_CATALOG}.{layer}")
    return databricks_query(f"SHOW SCHEMAS IN {DEFAULT_CATALOG}")


if __name__ == "__main__":
    mcp.run()

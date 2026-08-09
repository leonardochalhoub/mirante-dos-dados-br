"""Config compartilhada — carrega bolsa_familia_hub/.env e expõe os valores
que uc_metadata.py, build_index.py, build_graph.py e server.py precisam.

Mesmo padrão de .env do conselho_mcp (gitignored, perms 600, carregado antes
de qualquer leitura de os.environ).
"""
from __future__ import annotations

import os
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
HUB_ROOT = Path(__file__).resolve().parent


def _load_dotenv() -> None:
    env_path = HUB_ROOT / ".env"
    if not env_path.exists():
        return
    for line in env_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, val = line.partition("=")
        os.environ.setdefault(key.strip(), val.strip().strip('"').strip("'"))


_load_dotenv()

DATABRICKS_SERVER_HOSTNAME = os.environ.get("DATABRICKS_SERVER_HOSTNAME", "")
DATABRICKS_HTTP_PATH = os.environ.get("DATABRICKS_HTTP_PATH", "")
DATABRICKS_TOKEN = os.environ.get("DATABRICKS_TOKEN", "")
CATALOG = os.environ.get("MIRANTE_CATALOG", "mirante_prd")

QDRANT_HOST = os.environ.get("QDRANT_HOST", "localhost")
QDRANT_PORT = int(os.environ.get("QDRANT_PORT", "6333"))
QDRANT_COLLECTION = os.environ.get("QDRANT_COLLECTION", "bolsa_familia_memory")

NEO4J_URI = os.environ.get("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.environ.get("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.environ.get("NEO4J_PASSWORD", "")

EMBEDDING_MODEL = "intfloat/multilingual-e5-small"  # mesmo modelo do conselho_mcp


def databricks_connection():
    missing = [
        n
        for n, v in [
            ("DATABRICKS_SERVER_HOSTNAME", DATABRICKS_SERVER_HOSTNAME),
            ("DATABRICKS_HTTP_PATH", DATABRICKS_HTTP_PATH),
            ("DATABRICKS_TOKEN", DATABRICKS_TOKEN),
        ]
        if not v
    ]
    if missing:
        raise RuntimeError(f"Credenciais Databricks ausentes: {', '.join(missing)}")
    from databricks import sql

    return sql.connect(
        server_hostname=DATABRICKS_SERVER_HOSTNAME,
        http_path=DATABRICKS_HTTP_PATH,
        access_token=DATABRICKS_TOKEN,
    )

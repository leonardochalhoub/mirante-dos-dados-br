"""Constrói o Brain (grafo de lineage) a partir de estrutura REAL do repo —
sem LLM, sem grafo narrativo inventado.

Duas fontes, ambas determinísticas:
  1. `pipelines/databricks.yml` — jobs, tasks, `depends_on` (a orquestração
     declarada no Asset Bundle).
  2. Cada notebook referenciado — regex sobre o padrão usado em TODO notebook
     deste repo: `VAR = f"{CATALOG}.schema.tabela"` seguido de
     `spark.read.table(VAR)` (leitura) ou `.saveAsTable(VAR)`/`.toTable(VAR)`
     (escrita). Isso é lineage real de tabela, não inferência de texto.

Emite um seed Cypher em infra/seed-graph.cypher e (se INFRA_LOAD=1 ou
--load) carrega direto no Neo4j via bolt.

Uso:
    conda activate dev-env
    python bolsa_familia_hub/build_graph.py            # só gera o .cypher
    python bolsa_familia_hub/build_graph.py --load      # gera e carrega no Neo4j
"""
from __future__ import annotations

import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

import yaml

import config

PIPELINES_DIR = config.REPO_ROOT / "pipelines"
DATABRICKS_YML = PIPELINES_DIR / "databricks.yml"
SEED_CYPHER_PATH = config.HUB_ROOT / "infra" / "seed-graph.cypher"

_VAR_TABLE_RE = re.compile(
    r'^([A-Z_][A-Z0-9_]*)\s*=\s*f"\{CATALOG\}\.([a-z_]+)\.([a-zA-Z0-9_]+)"', re.MULTILINE
)
_READ_RE = re.compile(r"spark\.read\.table\((\w+)\)")
_WRITE_RE = re.compile(r"\.(?:saveAsTable|toTable)\((\w+)\)")


@dataclass
class Task:
    key: str
    job_name: str
    notebook_path: str
    depends_on: list[str] = field(default_factory=list)
    reads: set[str] = field(default_factory=set)   # full_name das tabelas
    writes: set[str] = field(default_factory=set)
    domain: str = ""


def _parse_notebook_tables(notebook_rel_path: str) -> tuple[set[str], set[str]]:
    """Retorna (tabelas lidas, tabelas escritas) como full_name 'schema.tabela'."""
    nb_path = (PIPELINES_DIR / notebook_rel_path.lstrip("./")).resolve()
    if not nb_path.exists():
        return set(), set()
    src = nb_path.read_text(encoding="utf-8", errors="replace")

    var_to_table: dict[str, str] = {}
    for var, schema, table in _VAR_TABLE_RE.findall(src):
        var_to_table[var] = f"{schema}.{table}"

    reads = {var_to_table[v] for v in _READ_RE.findall(src) if v in var_to_table}
    writes = {var_to_table[v] for v in _WRITE_RE.findall(src) if v in var_to_table}
    return reads, writes


def parse_jobs() -> list[Task]:
    doc = yaml.safe_load(DATABRICKS_YML.read_text(encoding="utf-8"))
    jobs = doc.get("resources", {}).get("jobs", {})

    tasks: list[Task] = []
    for job_key, job in jobs.items():
        job_name = job.get("name", job_key)
        domain = (job.get("tags") or {}).get("domain", "")
        for t in job.get("tasks", []):
            nb = (t.get("notebook_task") or {}).get("notebook_path")
            if not nb:
                continue  # pula tasks sem notebook (raro neste repo)
            deps = [d["task_key"] for d in (t.get("depends_on") or [])]
            task = Task(
                key=f"{job_key}::{t['task_key']}",
                job_name=job_name,
                notebook_path=nb,
                depends_on=[f"{job_key}::{d}" for d in deps],
            )
            reads, writes = _parse_notebook_tables(nb)
            task.reads = reads
            task.writes = writes
            task.domain = domain
            tasks.append(task)
    return tasks


def _layer_of(full_name: str) -> str:
    return full_name.split(".", 1)[0]


def _cypher_escape(s: str) -> str:
    return s.replace("\\", "\\\\").replace("'", "\\'")


def to_cypher(tasks: list[Task]) -> str:
    lines: list[str] = [
        "// Gerado por bolsa_familia_hub/build_graph.py — NÃO editar à mão.",
        "// Fonte: pipelines/databricks.yml + parsing estático dos notebooks.",
        "MATCH (n) DETACH DELETE n;",
        "",
        "CREATE CONSTRAINT table_full_name IF NOT EXISTS FOR (t:Table) REQUIRE t.full_name IS UNIQUE;",
        "CREATE CONSTRAINT job_name IF NOT EXISTS FOR (j:Job) REQUIRE j.name IS UNIQUE;",
        "CREATE CONSTRAINT task_key IF NOT EXISTS FOR (t:Task) REQUIRE t.key IS UNIQUE;",
        "",
    ]

    tables: dict[str, str] = {}  # full_name -> layer
    jobs_seen: set[str] = set()

    for t in tasks:
        for full_name in t.reads | t.writes:
            tables[full_name] = _layer_of(full_name)

    for full_name, layer in sorted(tables.items()):
        schema, name = full_name.split(".", 1)
        lines.append(
            f"CREATE (:Table {{full_name: '{full_name}', schema: '{schema}', "
            f"name: '{name}', layer: '{layer}'}});"
        )

    for t in tasks:
        if t.job_name not in jobs_seen:
            jobs_seen.add(t.job_name)
            lines.append(f"CREATE (:Job {{name: '{_cypher_escape(t.job_name)}', domain: '{t.domain}'}});")

    for t in tasks:
        lines.append(
            f"CREATE (:Task {{key: '{t.key}', notebook_path: '{_cypher_escape(t.notebook_path)}'}});"
        )

    lines.append("")
    for t in tasks:
        lines.append(
            f"MATCH (j:Job {{name: '{_cypher_escape(t.job_name)}'}}), (tk:Task {{key: '{t.key}'}}) "
            "CREATE (j)-[:HAS_TASK]->(tk);"
        )
        for dep_key in t.depends_on:
            lines.append(
                f"MATCH (a:Task {{key: '{dep_key}'}}), (b:Task {{key: '{t.key}'}}) "
                "CREATE (a)-[:PRECEDES]->(b);"
            )
        for full_name in t.reads:
            lines.append(
                f"MATCH (tk:Task {{key: '{t.key}'}}), (tb:Table {{full_name: '{full_name}'}}) "
                "CREATE (tk)-[:READS_FROM]->(tb);"
            )
        for full_name in t.writes:
            lines.append(
                f"MATCH (tk:Task {{key: '{t.key}'}}), (tb:Table {{full_name: '{full_name}'}}) "
                "CREATE (tk)-[:WRITES_TO]->(tb);"
            )

    # Atalho tabela->tabela: se uma task lê A e escreve B, A alimenta B.
    lines.append("")
    for t in tasks:
        for src in t.reads:
            for dst in t.writes:
                lines.append(
                    f"MATCH (a:Table {{full_name: '{src}'}}), (b:Table {{full_name: '{dst}'}}) "
                    "CREATE (a)-[:FEEDS]->(b);"
                )

    return "\n".join(lines) + "\n"


def load_into_neo4j(cypher_text: str) -> None:
    from neo4j import GraphDatabase

    driver = GraphDatabase.driver(config.NEO4J_URI, auth=(config.NEO4J_USER, config.NEO4J_PASSWORD))
    try:
        driver.verify_connectivity()
        statements = [s.strip() for s in cypher_text.split(";") if s.strip() and not s.strip().startswith("//")]
        with driver.session() as session:
            for stmt in statements:
                session.run(stmt)
        print(f"{len(statements)} statement(s) carregados no Neo4j em {config.NEO4J_URI}")
    finally:
        driver.close()


def main() -> None:
    tasks = parse_jobs()
    if not tasks:
        raise SystemExit("Nenhuma task com notebook_path encontrada em pipelines/databricks.yml")

    n_tables = len({f for t in tasks for f in (t.reads | t.writes)})
    print(f"{len(tasks)} task(s) em {len({t.job_name for t in tasks})} job(s) -> {n_tables} tabela(s) com lineage")

    cypher = to_cypher(tasks)
    SEED_CYPHER_PATH.parent.mkdir(parents=True, exist_ok=True)
    SEED_CYPHER_PATH.write_text(cypher, encoding="utf-8")
    print(f"Cypher gerado em {SEED_CYPHER_PATH}")

    if "--load" in sys.argv:
        load_into_neo4j(cypher)


if __name__ == "__main__":
    main()

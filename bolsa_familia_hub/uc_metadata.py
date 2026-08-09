"""Extrai comentários/metadados do Unity Catalog para dentro do Memory (RAG).

Ledger (server.py::query_ledger) só executa SQL ao vivo — não é onde se
pergunta "o que significa a coluna X" ou "por que essa tabela existe". Isso é
documentação, então vira texto indexável no Memory, junto do artigo e ADRs.

Cobre TODO o catálogo (bronze/silver/gold), não só as tabelas de PBF: as
tabelas compartilhadas (populacao, ipca, geobr) fazem parte do contexto de
qualquer pergunta sobre PBF per capita/deflacionado, e comentários de outras
verticais (RAIS, emendas) não custam nada a mais para indexar.

Saída: um .md por tabela em docs_sources/uc_metadata/<schema>.<table>.md
Rode de novo sempre que os notebooks Databricks adicionarem/mudarem
COMMENT ON TABLE/COLUMN. Reproduzível — por isso o diretório é gitignored.
"""
from __future__ import annotations

from collections import defaultdict
from pathlib import Path

import config

OUT_DIR = config.HUB_ROOT / "docs_sources" / "uc_metadata"
SCHEMAS = ("bronze", "silver", "gold")


def _fetch_tables(conn) -> list[tuple[str, str, str | None]]:
    q = f"""
        SELECT table_schema, table_name, comment
        FROM system.information_schema.tables
        WHERE table_catalog = '{config.CATALOG}'
          AND table_schema IN {SCHEMAS}
        ORDER BY table_schema, table_name
    """
    with conn.cursor() as cur:
        cur.execute(q)
        return cur.fetchall()


def _fetch_columns(conn) -> dict[tuple[str, str], list[tuple[str, str, str | None]]]:
    q = f"""
        SELECT table_schema, table_name, column_name, full_data_type, comment
        FROM system.information_schema.columns
        WHERE table_catalog = '{config.CATALOG}'
          AND table_schema IN {SCHEMAS}
        ORDER BY table_schema, table_name, ordinal_position
    """
    by_table: dict[tuple[str, str], list[tuple[str, str, str | None]]] = defaultdict(list)
    with conn.cursor() as cur:
        cur.execute(q)
        for schema, table, col, dtype, comment in cur.fetchall():
            by_table[(schema, table)].append((col, dtype, comment))
    return by_table


def _render(schema: str, table: str, table_comment: str | None, columns: list[tuple[str, str, str | None]]) -> str:
    lines = [f"# {schema}.{table}", ""]
    lines.append(f"**Catálogo:** `{config.CATALOG}.{schema}.{table}`  ")
    lines.append(f"**Descrição:** {table_comment or '(sem comentário registrado no Unity Catalog)'}")
    lines.append("")
    lines.append("## Colunas")
    lines.append("")
    lines.append("| coluna | tipo | comentário |")
    lines.append("|---|---|---|")
    for col, dtype, comment in columns:
        lines.append(f"| `{col}` | {dtype} | {comment or ''} |")
    lines.append("")
    return "\n".join(lines)


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    conn = config.databricks_connection()
    try:
        tables = _fetch_tables(conn)
        columns_by_table = _fetch_columns(conn)
    finally:
        conn.close()

    if not tables:
        print(f"Nenhuma tabela encontrada em {config.CATALOG}.{{{','.join(SCHEMAS)}}}.")
        return

    written = 0
    for schema, table, comment in tables:
        cols = columns_by_table.get((schema, table), [])
        text = _render(schema, table, comment, cols)
        out_path = OUT_DIR / f"{schema}.{table}.md"
        out_path.write_text(text, encoding="utf-8")
        written += 1

    print(f"{written} tabela(s) documentada(s) em {OUT_DIR}")


if __name__ == "__main__":
    main()

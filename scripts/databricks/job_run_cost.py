#!/usr/bin/env python3
"""
Mirante dos Dados — Job run cost calculator.

Algorithm:
  cost(run) = Σ over billing records with usage_metadata.job_run_id = run
                 ( usage_quantity_DBU × list_price_USD_per_DBU )

  list_price_USD_per_DBU is time-versioned: pick the row in system.billing.list_prices
  whose [price_start_time, price_end_time) interval contains the record's
  usage_start_time. Match on (sku_name, cloud, usage_unit).

Sources (Unity Catalog system tables):
  system.billing.usage            — DBUs per (resource, hour)
  system.billing.list_prices      — USD/DBU history per SKU
  system.lakeflow.job_run_timeline — run name + result_state for context

Usage:
  python scripts/databricks/job_run_cost.py                     # top 50 priciest runs, 30 days
  python scripts/databricks/job_run_cost.py --days 7
  python scripts/databricks/job_run_cost.py --job-id 1234567890
  python scripts/databricks/job_run_cost.py --run-id 9988776655 --days 90
  python scripts/databricks/job_run_cost.py --limit 200 --csv > runs.csv
  python scripts/databricks/job_run_cost.py --print-sql        # show the rendered SQL only

Requires: databricks CLI v0.200+ authenticated; a Serverless SQL warehouse.
"""
from __future__ import annotations

import argparse
import csv
import json
import pathlib
import subprocess
import sys
import time

SQL_FILE = pathlib.Path(__file__).with_name("job_run_cost.sql")


def render_sql(*, since_days: int, job_id: str | None, run_id: str | None, limit: int) -> str:
    """Inline parameters into the SQL template (Statement API has no native params)."""
    sql = SQL_FILE.read_text()
    sql = sql.replace(":since_days", str(int(since_days)))
    sql = sql.replace(":limit", str(int(limit)))
    sql = sql.replace(":job_id", f"'{job_id}'" if job_id else "NULL")
    sql = sql.replace(":run_id", f"'{run_id}'" if run_id else "NULL")
    return sql


def pick_warehouse() -> str:
    out = subprocess.check_output(["databricks", "warehouses", "list", "--output", "json"])
    warehouses = json.loads(out)
    if not warehouses:
        sys.exit("No SQL warehouses available. Create a Serverless Starter warehouse first.")
    serverless = [w for w in warehouses if w.get("enable_serverless_compute")]
    pool = serverless or warehouses
    return pool[0]["id"]


def submit(warehouse_id: str, sql: str) -> dict:
    body = {"warehouse_id": warehouse_id, "statement": sql, "wait_timeout": "50s",
            "disposition": "INLINE", "format": "JSON_ARRAY"}
    out = subprocess.check_output(
        ["databricks", "api", "post", "/api/2.0/sql/statements", "--json", json.dumps(body)]
    )
    return json.loads(out)


def poll_until_done(statement_id: str, timeout_s: int = 300) -> dict:
    deadline = time.time() + timeout_s
    while time.time() < deadline:
        out = subprocess.check_output(
            ["databricks", "api", "get", f"/api/2.0/sql/statements/{statement_id}"]
        )
        resp = json.loads(out)
        state = resp.get("status", {}).get("state")
        if state in {"SUCCEEDED", "FAILED", "CANCELED", "CLOSED"}:
            return resp
        time.sleep(2)
    sys.exit(f"Timed out waiting for statement {statement_id}")


def run_query(sql: str) -> tuple[list[str], list[list]]:
    warehouse_id = pick_warehouse()
    resp = submit(warehouse_id, sql)
    state = resp.get("status", {}).get("state")
    if state == "PENDING" or state == "RUNNING":
        resp = poll_until_done(resp["statement_id"])
        state = resp.get("status", {}).get("state")
    if state != "SUCCEEDED":
        err = resp.get("status", {}).get("error", {})
        sys.exit(f"Query {state}: {err.get('message','(no message)')}")
    cols = [c["name"] for c in resp["manifest"]["schema"]["columns"]]
    rows = resp.get("result", {}).get("data_array", []) or []
    return cols, rows


def fmt_table(cols: list[str], rows: list[list]) -> str:
    str_rows = [[str(c) if c is not None else "" for c in r] for r in rows]
    widths = [max(len(c), *(len(r[i]) for r in str_rows) if str_rows else (len(c),)) for i, c in enumerate(cols)]
    sep = "  ".join("-" * w for w in widths)
    out = ["  ".join(c.ljust(w) for c, w in zip(cols, widths)), sep]
    for r in str_rows:
        out.append("  ".join(c.ljust(w) for c, w in zip(r, widths)))
    return "\n".join(out)


def main() -> None:
    ap = argparse.ArgumentParser(description="Compute Databricks job-run cost in USD.")
    ap.add_argument("--days", type=int, default=30, help="lookback window (default 30)")
    ap.add_argument("--job-id", type=str, default=None, help="filter by job_id")
    ap.add_argument("--run-id", type=str, default=None, help="filter by job_run_id")
    ap.add_argument("--limit", type=int, default=50, help="max rows (default 50)")
    ap.add_argument("--csv", action="store_true", help="emit CSV instead of pretty table")
    ap.add_argument("--print-sql", action="store_true", help="print rendered SQL and exit")
    args = ap.parse_args()

    sql = render_sql(since_days=args.days, job_id=args.job_id, run_id=args.run_id, limit=args.limit)

    print("─" * 78, file=sys.stderr)
    print("RENDERED SQL:", file=sys.stderr)
    print("─" * 78, file=sys.stderr)
    print(sql, file=sys.stderr)
    print("─" * 78, file=sys.stderr)

    if args.print_sql:
        return

    cols, rows = run_query(sql)
    if args.csv:
        w = csv.writer(sys.stdout)
        w.writerow(cols)
        w.writerows(rows)
    else:
        if not rows:
            print("(no job runs with billing records in the selected window)")
            return
        print(fmt_table(cols, rows))
        total_idx = cols.index("total_cost_usd")
        total = sum(float(r[total_idx]) for r in rows if r[total_idx] is not None)
        print(f"\nTotal across {len(rows)} runs: USD {total:,.4f}")


if __name__ == "__main__":
    main()

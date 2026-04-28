# Databricks notebook source
# MAGIC %md
# MAGIC # export · finops_summary_json
# MAGIC
# MAGIC Lê `gold.finops_run_costs` + `gold.finops_daily_spend` e emite um **único** JSON
# MAGIC consumido pelo front da vertical FinOps:
# MAGIC `/Volumes/<catalog>/gold/exports/finops_summary.json`.
# MAGIC
# MAGIC Estrutura do output:
# MAGIC ```jsonc
# MAGIC {
# MAGIC   "generated_at_utc":      "ISO datetime",
# MAGIC   "window": {
# MAGIC     "first_day": "YYYY-MM-DD",
# MAGIC     "last_day":  "YYYY-MM-DD",
# MAGIC     "n_days":    127
# MAGIC   },
# MAGIC   "kpis": {
# MAGIC     "total_cost_usd_lifetime":    0.00,
# MAGIC     "total_cost_usd_30d":         0.00,
# MAGIC     "total_cost_usd_7d":          0.00,
# MAGIC     "total_dbus_lifetime":        0.00,
# MAGIC     "n_runs_lifetime":            0,
# MAGIC     "n_runs_30d":                 0,
# MAGIC     "wasted_cost_usd_lifetime":   0.00,
# MAGIC     "wasted_pct_lifetime":        0.00,
# MAGIC     "avg_cost_per_run_usd":       0.00,
# MAGIC     "p95_cost_per_run_usd":       0.00,
# MAGIC     "chargeable_share_pct":       0.00,
# MAGIC     "overhead_share_pct":         0.00,
# MAGIC     "most_expensive_run": { ... }
# MAGIC   },
# MAGIC   "daily":          [ {usage_date, cost_total, ...}, ... ],
# MAGIC   "by_product":     [ {product, cost_usd, share_pct}, ... ],
# MAGIC   "by_outcome":     [ {result_state, n_runs, cost_usd, share_pct, avg_minutes}, ... ],
# MAGIC   "by_job":         [ {job_name, n_runs, cost_usd, succeeded, failed, cancelled, avg_per_run}, ... ],
# MAGIC   "top_runs":       [ {job_name, run_id, day, result_state, cost_usd, billed_minutes}, ... ]
# MAGIC }
# MAGIC ```

# COMMAND ----------

dbutils.widgets.text("catalog",     "mirante_prd")
dbutils.widgets.text("output_path", "/Volumes/mirante_prd/gold/exports/finops_summary.json")
dbutils.widgets.text("top_jobs",    "20")
dbutils.widgets.text("top_runs",    "25")

CATALOG     = dbutils.widgets.get("catalog")
OUTPUT_PATH = dbutils.widgets.get("output_path")
TOP_JOBS    = int(dbutils.widgets.get("top_jobs"))
TOP_RUNS    = int(dbutils.widgets.get("top_runs"))

GOLD_RUNS  = f"{CATALOG}.gold.finops_run_costs"
GOLD_DAILY = f"{CATALOG}.gold.finops_daily_spend"

print(f"runs={GOLD_RUNS}  daily={GOLD_DAILY}  out={OUTPUT_PATH}")

# COMMAND ----------

import json
from pathlib import Path
from datetime import datetime, timezone, timedelta

from pyspark.sql import functions as F
import pandas as pd

# ─── Defensive: skip gracefully if upstream gold is missing/empty ─────────────
if not (spark.catalog.tableExists(GOLD_RUNS) and spark.catalog.tableExists(GOLD_DAILY)):
    print(f"⚠ {GOLD_RUNS} ou {GOLD_DAILY} não existe — investigue silver/gold upstream.")
    dbutils.notebook.exit("SKIPPED: upstream gold table missing")

from pyspark.sql import types as T

# Cast every Decimal column to double in Spark — keeps pandas conversion clean
# (decimal.Decimal doesn't play with float arithmetic in pandas/numpy).
def cast_decimals_to_double(df_):
    for f in df_.schema.fields:
        if isinstance(f.dataType, T.DecimalType):
            df_ = df_.withColumn(f.name, F.col(f.name).cast("double"))
    return df_

runs_pdf  = cast_decimals_to_double(spark.read.table(GOLD_RUNS).drop("_gold_built_ts")).toPandas()
daily_pdf = cast_decimals_to_double(spark.read.table(GOLD_DAILY).drop("_gold_built_ts")).toPandas()

if runs_pdf.empty or daily_pdf.empty:
    print("⚠ gold tables vazias — nada pra exportar.")
    dbutils.notebook.exit("SKIPPED: gold tables are empty")

print(f"runs_pdf={len(runs_pdf)}  daily_pdf={len(daily_pdf)}")

# COMMAND ----------

# ─── Window metadata ──────────────────────────────────────────────────────────
daily_pdf = daily_pdf.sort_values("usage_date").reset_index(drop=True)
first_day = pd.to_datetime(daily_pdf["usage_date"].iloc[0]).date()
last_day  = pd.to_datetime(daily_pdf["usage_date"].iloc[-1]).date()
n_days    = (last_day - first_day).days + 1

print(f"window: {first_day} → {last_day}  ({n_days} days)")

# COMMAND ----------

# ─── KPIs (lifetime + last 30d + last 7d) ─────────────────────────────────────

def f(x):
    """Round + cast to native float (defaults JSON-encode bug-free)."""
    if pd.isna(x):
        return 0.0
    return round(float(x), 6)


def i(x):
    if pd.isna(x):
        return 0
    return int(x)


# daily_pdf.cost_total is authoritative (covers all products including
# overhead). runs_pdf only covers JOBS (workloads tagged to a run_id).
total_cost_lifetime = float(daily_pdf["cost_total"].sum())

# Last 7d / 30d windows
runs_pdf["day"] = pd.to_datetime(runs_pdf["day"])
daily_pdf["usage_date"] = pd.to_datetime(daily_pdf["usage_date"])
cutoff_30 = pd.Timestamp(last_day) - pd.Timedelta(days=29)
cutoff_7  = pd.Timestamp(last_day) - pd.Timedelta(days=6)

runs_30 = runs_pdf[runs_pdf["day"] >= cutoff_30]
runs_7  = runs_pdf[runs_pdf["day"] >= cutoff_7]
daily_30 = daily_pdf[daily_pdf["usage_date"] >= cutoff_30]
daily_7  = daily_pdf[daily_pdf["usage_date"] >= cutoff_7]

# Wasted cost (ERROR + CANCELLED)
wasted_lifetime = runs_pdf[runs_pdf["is_wasted"]]["cost_usd"].sum()
runs_jobs_total = runs_pdf["cost_usd"].sum()
wasted_pct = (100.0 * wasted_lifetime / runs_jobs_total) if runs_jobs_total > 0 else 0.0

# Chargeable vs overhead split (lifetime)
charge_total = daily_pdf["cost_chargeable_total"].sum()
over_total   = daily_pdf["cost_overhead_total"].sum()
total_for_share = charge_total + over_total
charge_pct = (100.0 * charge_total / total_for_share) if total_for_share > 0 else 0.0
over_pct   = (100.0 * over_total   / total_for_share) if total_for_share > 0 else 0.0

# Cost-per-run distribution
costs_per_run = runs_pdf["cost_usd"].dropna().sort_values()
avg_cost_per_run = costs_per_run.mean() if len(costs_per_run) else 0.0
p95_cost_per_run = costs_per_run.quantile(0.95) if len(costs_per_run) else 0.0

# Most expensive run
top_run = runs_pdf.sort_values("cost_usd", ascending=False).head(1)
most_expensive_run = (
    {
        "job_id": str(top_run["job_id"].iloc[0]) if pd.notna(top_run["job_id"].iloc[0]) else None,
        "run_id": str(top_run["run_id"].iloc[0]) if pd.notna(top_run["run_id"].iloc[0]) else None,
        "job_name": top_run["job_name_canonical"].iloc[0] if pd.notna(top_run["job_name_canonical"].iloc[0]) else "(sem nome)",
        "result_state": top_run["result_state"].iloc[0],
        "cost_usd": f(top_run["cost_usd"].iloc[0]),
        "billed_minutes": f(top_run["billed_minutes"].iloc[0]),
        "day": top_run["day"].iloc[0].strftime("%Y-%m-%d") if pd.notna(top_run["day"].iloc[0]) else None,
    }
    if len(top_run) > 0 else None
)

kpis = {
    "total_cost_usd_lifetime":   f(total_cost_lifetime),
    "total_cost_usd_30d":        f(daily_30["cost_total"].sum()),
    "total_cost_usd_7d":         f(daily_7["cost_total"].sum()),
    "total_dbus_lifetime":       f(daily_pdf["dbus_total"].sum()),
    "n_runs_lifetime":           i(len(runs_pdf)),
    "n_runs_30d":                i(len(runs_30)),
    "n_runs_7d":                 i(len(runs_7)),
    "wasted_cost_usd_lifetime":  f(wasted_lifetime),
    "wasted_pct_lifetime":       f(wasted_pct),
    "avg_cost_per_run_usd":      f(avg_cost_per_run),
    "p95_cost_per_run_usd":      f(p95_cost_per_run),
    "chargeable_share_pct":      f(charge_pct),
    "overhead_share_pct":        f(over_pct),
    "most_expensive_run":        most_expensive_run,
}

print("KPIs:", json.dumps(kpis, default=str, indent=2))

# COMMAND ----------

# ─── Daily series (chart fuel) ────────────────────────────────────────────────
daily_out = []
for _, row in daily_pdf.iterrows():
    daily_out.append({
        "usage_date":             row["usage_date"].strftime("%Y-%m-%d"),
        "cost_jobs":              f(row.get("cost_jobs")),
        "cost_sql":               f(row.get("cost_sql")),
        "cost_interactive":       f(row.get("cost_interactive")),
        "cost_dlt":               f(row.get("cost_dlt")),
        "cost_networking":        f(row.get("cost_networking")),
        "cost_storage":           f(row.get("cost_storage")),
        "cost_pred_opt":          f(row.get("cost_pred_opt")),
        "cost_chargeable_total":  f(row.get("cost_chargeable_total")),
        "cost_overhead_total":    f(row.get("cost_overhead_total")),
        "cost_total":             f(row.get("cost_total")),
        "cost_total_cumulative":  f(row.get("cost_total_cumulative")),
        "dbus_total":             f(row.get("dbus_total")),
    })

# COMMAND ----------

# ─── By product breakdown (donut/bar) ─────────────────────────────────────────
prod_cols = {
    "JOBS": "cost_jobs", "SQL": "cost_sql", "INTERACTIVE": "cost_interactive", "DLT": "cost_dlt",
    "NETWORKING": "cost_networking", "DEFAULT_STORAGE": "cost_storage",
    "PREDICTIVE_OPTIMIZATION": "cost_pred_opt",
}
class_of = {
    "JOBS": "chargeable", "SQL": "chargeable", "INTERACTIVE": "chargeable", "DLT": "chargeable",
    "NETWORKING": "overhead", "DEFAULT_STORAGE": "overhead", "PREDICTIVE_OPTIMIZATION": "overhead",
}
by_product = []
for prod, col in prod_cols.items():
    cost = float(daily_pdf[col].sum())
    if cost <= 0:
        continue
    by_product.append({
        "product":        prod,
        "workload_class": class_of[prod],
        "cost_usd":       f(cost),
        "share_pct":      f(100.0 * cost / total_cost_lifetime) if total_cost_lifetime > 0 else 0.0,
    })
by_product.sort(key=lambda r: r["cost_usd"], reverse=True)

# COMMAND ----------

# ─── By outcome (KPI card: how much money was wasted on failures?) ────────────
by_outcome = []
for state in ("SUCCEEDED", "ERROR", "CANCELLED", "UNKNOWN"):
    sub = runs_pdf[runs_pdf["result_state"] == state]
    if len(sub) == 0:
        continue
    cost = float(sub["cost_usd"].sum())
    by_outcome.append({
        "result_state":  state,
        "n_runs":        i(len(sub)),
        "cost_usd":      f(cost),
        "share_pct":     f(100.0 * cost / runs_jobs_total) if runs_jobs_total > 0 else 0.0,
        "avg_per_run":   f(cost / len(sub)) if len(sub) > 0 else 0.0,
        "avg_minutes":   f(sub["billed_minutes"].mean()),
    })

# COMMAND ----------

# ─── By job (per-job rollup with outcome split) ───────────────────────────────
by_job_rows = []
for name, group in runs_pdf.groupby("job_name_canonical"):
    cost = float(group["cost_usd"].sum())
    by_job_rows.append({
        "job_name":     name if name else "(sem nome)",
        "n_runs":       i(len(group)),
        "cost_usd":     f(cost),
        "succeeded":    i((group["result_state"] == "SUCCEEDED").sum()),
        "failed":       i((group["result_state"] == "ERROR").sum()),
        "cancelled":    i((group["result_state"] == "CANCELLED").sum()),
        "avg_per_run":  f(cost / len(group)) if len(group) > 0 else 0.0,
        "wasted_cost":  f(group[group["is_wasted"]]["cost_usd"].sum()),
        "avg_minutes":  f(group["billed_minutes"].mean()),
    })
by_job_rows.sort(key=lambda r: r["cost_usd"], reverse=True)
by_job_rows = by_job_rows[:TOP_JOBS]

# COMMAND ----------

# ─── Top-N most expensive single runs ─────────────────────────────────────────
top_runs_pdf = runs_pdf.sort_values("cost_usd", ascending=False).head(TOP_RUNS)
top_runs_out = []
for _, row in top_runs_pdf.iterrows():
    top_runs_out.append({
        "job_id":         str(row["job_id"]) if pd.notna(row["job_id"]) else None,
        "run_id":         str(row["run_id"]) if pd.notna(row["run_id"]) else None,
        "job_name":       row["job_name_canonical"] or "(sem nome)",
        "result_state":   row["result_state"],
        "is_wasted":      bool(row["is_wasted"]),
        "cost_usd":       f(row["cost_usd"]),
        "dbus":           f(row["dbus"]),
        "billed_minutes": f(row["billed_minutes"]),
        "day":            row["day"].strftime("%Y-%m-%d") if pd.notna(row["day"]) else None,
    })

# COMMAND ----------

# ─── Storage spending (DEFAULT_STORAGE) breakdown ─────────────────────────────
# Storage é cobrado continuamente (cada dia que o dado fica armazenado custa USD).
# Computamos: total lifetime, $/dia médio, $/dia run rate (últimos 30d),
# projeção mensal e anual.
storage_lifetime = float(daily_pdf["cost_storage"].sum())
storage_30d      = float(daily_30["cost_storage"].sum())
# n_days_with_storage: conta dias com pelo menos $0.001 de storage (ignora dias
# pré-storage para não diluir o $/dia médio com zeros artificiais)
days_with_storage = int((daily_pdf["cost_storage"] > 0.001).sum())
days_with_storage_30 = int((daily_30["cost_storage"] > 0.001).sum())

storage_per_day_lifetime = (storage_lifetime / days_with_storage) if days_with_storage > 0 else 0.0
storage_per_day_current  = (storage_30d / days_with_storage_30) if days_with_storage_30 > 0 else 0.0
storage_per_month_run    = storage_per_day_current * 30.0
storage_per_year_run     = storage_per_day_current * 365.0
storage_pct_of_total     = (100.0 * storage_lifetime / total_cost_lifetime) if total_cost_lifetime > 0 else 0.0

storage = {
    "total_usd_lifetime":    f(storage_lifetime),
    "total_usd_30d":         f(storage_30d),
    "days_with_storage":     i(days_with_storage),
    "per_day_avg_lifetime":  f(storage_per_day_lifetime),
    "per_day_current":       f(storage_per_day_current),
    "per_month_run_rate":    f(storage_per_month_run),
    "per_year_run_rate":     f(storage_per_year_run),
    "share_of_total_pct":    f(storage_pct_of_total),
}
print(f"\nstorage: lifetime ${storage_lifetime:.4f}  "
      f"per_day_current ${storage_per_day_current:.4f}  "
      f"per_year ${storage_per_year_run:.2f}")

summary = {
    "generated_at_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    "catalog":          CATALOG,
    "window": {
        "first_day": str(first_day),
        "last_day":  str(last_day),
        "n_days":    i(n_days),
    },
    "kpis":         kpis,
    "storage":      storage,
    "daily":        daily_out,
    "by_product":   by_product,
    "by_outcome":   by_outcome,
    "by_job":       by_job_rows,
    "top_runs":     top_runs_out,
}

print(f"\n--- summary preview ---")
print(f"  total_lifetime: USD {kpis['total_cost_usd_lifetime']}")
print(f"  total_30d:      USD {kpis['total_cost_usd_30d']}")
print(f"  wasted:         USD {kpis['wasted_cost_usd_lifetime']} ({kpis['wasted_pct_lifetime']}%)")
print(f"  daily series:   {len(daily_out)} days")
print(f"  by_product:     {len(by_product)} rows")
print(f"  by_outcome:     {len(by_outcome)} rows")
print(f"  by_job (top):   {len(by_job_rows)} rows")
print(f"  top_runs:       {len(top_runs_out)} rows")

# COMMAND ----------

dest = Path(OUTPUT_PATH)
dest.parent.mkdir(parents=True, exist_ok=True)
dest.write_text(json.dumps(summary, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
print(f"✔ {dest}  ({dest.stat().st_size:,} bytes)")

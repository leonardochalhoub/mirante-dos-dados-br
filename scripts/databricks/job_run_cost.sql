-- ─────────────────────────────────────────────────────────────────────────────
-- Mirante dos Dados — Job run cost calculator
-- ─────────────────────────────────────────────────────────────────────────────
-- Cost = sum over all billing records tagged with the job_run_id of
--        (usage_quantity in DBUs) × (list price USD per DBU at usage_start_time).
--
-- Sources:
--   system.billing.usage        — one row per (resource, hour) with DBU quantity
--   system.billing.list_prices  — historical DBU price per SKU (time-versioned)
--   system.lakeflow.job_run_timeline — run metadata (name, status, period)
--
-- Parameters (replace via the wrapper script or edit inline):
--   :since_days   how far back to scan billing records      (default 30)
--   :job_id       optional filter — single job_id           (NULL = all jobs)
--   :run_id       optional filter — single run_id           (NULL = all runs)
--   :limit        max rows to return                        (default 50)
-- ─────────────────────────────────────────────────────────────────────────────

WITH priced_usage AS (
  SELECT
    u.workspace_id,
    u.usage_metadata.job_id        AS job_id,
    u.usage_metadata.job_run_id    AS run_id,
    u.usage_metadata.job_name      AS job_name,
    u.usage_metadata.run_name      AS run_name,
    u.sku_name,
    u.usage_unit,
    u.usage_start_time,
    u.usage_end_time,
    u.usage_quantity                              AS dbus,
    lp.pricing.default                            AS dbu_rate_usd,
    u.usage_quantity * lp.pricing.default         AS cost_usd,
    u.product_features.is_serverless              AS is_serverless,
    u.product_features.is_photon                  AS is_photon,
    u.billing_origin_product                      AS product
  FROM system.billing.usage u
  LEFT JOIN system.billing.list_prices lp
    ON  u.sku_name        = lp.sku_name
    AND u.cloud           = lp.cloud
    AND u.usage_unit      = lp.usage_unit
    AND u.usage_start_time >= lp.price_start_time
    AND (lp.price_end_time IS NULL OR u.usage_start_time < lp.price_end_time)
  WHERE u.usage_metadata.job_run_id IS NOT NULL
    AND u.usage_date >= current_date() - INTERVAL :since_days DAYS
    AND (:job_id IS NULL OR u.usage_metadata.job_id     = :job_id)
    AND (:run_id IS NULL OR u.usage_metadata.job_run_id = :run_id)
)
SELECT
  pu.job_id,
  pu.run_id,
  COALESCE(pu.job_name, jrt.run_name)                   AS job_name,
  jrt.result_state                                       AS run_status,
  MIN(pu.usage_start_time)                              AS first_usage_at,
  MAX(pu.usage_end_time)                                AS last_usage_at,
  CAST(timestampdiff(SECOND,
       MIN(pu.usage_start_time),
       MAX(pu.usage_end_time)) AS DOUBLE) / 60.0        AS billed_minutes,
  ROUND(SUM(pu.dbus),       4)                          AS total_dbus,
  ROUND(SUM(pu.cost_usd),   4)                          AS total_cost_usd,
  ANY_VALUE(pu.is_serverless)                           AS is_serverless,
  ANY_VALUE(pu.is_photon)                               AS is_photon,
  collect_set(pu.sku_name)                              AS skus,
  collect_set(pu.product)                               AS products
FROM priced_usage pu
LEFT JOIN (
  SELECT job_id, run_id, run_name,
         max_by(result_state, period_end_time) AS result_state
  FROM system.lakeflow.job_run_timeline
  GROUP BY job_id, run_id, run_name
) jrt
  ON jrt.job_id = pu.job_id AND jrt.run_id = pu.run_id
GROUP BY pu.job_id, pu.run_id, COALESCE(pu.job_name, jrt.run_name), jrt.result_state
ORDER BY total_cost_usd DESC NULLS LAST
LIMIT :limit;

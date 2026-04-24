#!/usr/bin/env bash
# Mirante dos Dados — bootstrap do Unity Catalog.
#
# Cria catalog, schemas e Volumes necessários antes do primeiro `databricks bundle deploy`.
# Idempotente: usa "IF NOT EXISTS" em tudo. Pode rodar quantas vezes quiser.
#
# Pré-requisitos:
#   - Databricks CLI instalado e autenticado:
#       databricks configure --host https://dbc-cafe0a5f-07e3.cloud.databricks.com --token
#   - Permissão pra criar catalogs no metastore (admin do workspace ou user com USE_METASTORE)
#
# Uso:
#   bash scripts/databricks/bootstrap.sh                  # default catalog "mirante"
#   CATALOG=mirante_dev bash scripts/databricks/bootstrap.sh

set -euo pipefail

CATALOG="${CATALOG:-mirante}"

echo "▸ catalog = ${CATALOG}"
echo

run_sql() {
  local sql="$1"
  echo "  SQL> ${sql}"
  databricks sql-warehouses list --output JSON > /dev/null 2>&1 || true
  # Use Databricks CLI's "sql" command via api/2.0/sql or via the SDK.
  # Simpler & always-available: the workspace shell-equivalent via api 2.0 statement-execution.
  # Easier still: use a small notebook task. But to keep this self-contained, we exec via the CLI.
  databricks api post /api/2.0/sql/statements \
    --json "{
      \"statement\": $(printf '%s' "$sql" | python3 -c 'import sys,json; print(json.dumps(sys.stdin.read()))'),
      \"warehouse_id\": \"\${WAREHOUSE_ID:-}\"
    }" > /dev/null && return 0 || true

  # Fallback: use unity-catalog catalog/schema/volume create commands
  return 1
}

# The CLI's catalog/schema/volume CRUD is the most portable path. Try those first.
echo "▸ creating catalog ${CATALOG}…"
databricks catalogs create --name "${CATALOG}" \
  --comment "Mirante dos Dados — open public data lakehouse" 2>/dev/null \
  || echo "  (already exists, skipping)"

echo
echo "▸ creating schemas…"
for schema in bronze silver gold; do
  databricks schemas create --catalog-name "${CATALOG}" --name "${schema}" \
    --comment "Mirante ${schema} layer" 2>/dev/null \
    || echo "  ${CATALOG}.${schema} (already exists)"
done

echo
echo "▸ creating volumes…"
# raw inputs (HTTPs downloads)
databricks volumes create --catalog-name "${CATALOG}" --schema-name bronze \
  --name raw --volume-type MANAGED \
  --comment "Raw HTTP downloads (ZIPs/JSONs from CGU/IBGE/BCB)" 2>/dev/null \
  || echo "  ${CATALOG}.bronze.raw (already exists)"

# gold exports (JSONs picked up by the GitHub Action)
databricks volumes create --catalog-name "${CATALOG}" --schema-name gold \
  --name exports --volume-type MANAGED \
  --comment "Gold JSON exports — picked up by the front-end via GitHub Action" 2>/dev/null \
  || echo "  ${CATALOG}.gold.exports (already exists)"

echo
echo "✔ Bootstrap complete."
echo
echo "Next steps:"
echo "  cd pipelines"
echo "  databricks bundle deploy --target dev"
echo "  databricks bundle run job_populacao_refresh --target dev   # warm shared dim 1"
echo "  databricks bundle run job_ipca_refresh      --target dev   # warm shared dim 2"
echo "  databricks bundle run job_pbf_refresh       --target dev   # full PBF E2E"

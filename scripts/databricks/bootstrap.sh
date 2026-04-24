#!/usr/bin/env bash
# Mirante dos Dados — Unity Catalog bootstrap.
#
# Cria o catalog `mirante_prd` (se não existir), os 3 schemas (bronze/silver/gold)
# e os 2 volumes (bronze.raw e gold.exports). Idempotente — pode rodar várias vezes.
#
# IMPORTANT: erros de verdade (ex: permissão, quota) NÃO são silenciados — eles
# aparecem na saída pra você diagnosticar. Apenas a mensagem específica
# "already exists" é tratada como sucesso.
#
# Pré-requisitos:
#   - Databricks CLI v0.200+ instalado e autenticado
#       (databricks current-user me deve voltar seu email)
#   - User tem CREATE_CATALOG no metastore (Free Edition: sim por default no managed metastore)
#
# Uso:
#   bash scripts/databricks/bootstrap.sh                  # default catalog "mirante_prd"
#   CATALOG=outro_nome bash scripts/databricks/bootstrap.sh

set -euo pipefail

CATALOG="${CATALOG:-mirante_prd}"
echo "▸ catalog = ${CATALOG}"
echo

# Helper: run a databricks CLI command, treating "already exists" as success but
# printing the real error otherwise.
try_create() {
  local label="$1"; shift
  local out
  if out=$("$@" 2>&1); then
    echo "  ✔ ${label} created"
    return 0
  fi
  if grep -qiE "already exists|RESOURCE_ALREADY_EXISTS" <<<"$out"; then
    echo "  · ${label} already exists (skip)"
    return 0
  fi
  echo "  ✗ ${label} failed:" >&2
  echo "$out" | sed 's/^/    /' >&2
  return 1
}

# 1. Catalog (check existence first; Free Edition with Default Storage refuses
#    `catalogs create` regardless of whether the catalog already exists)
echo "▸ checking catalog ${CATALOG}…"
if databricks catalogs get "${CATALOG}" >/dev/null 2>&1; then
  echo "  · catalog ${CATALOG} already exists (skip)"
else
  echo "  ! catalog ${CATALOG} does NOT exist."
  echo "    Free Edition / Default Storage does not allow CLI catalog creation."
  echo "    Please create it via the UI:"
  echo "      1. Open https://dbc-cafe0a5f-07e3.cloud.databricks.com/explore/data"
  echo "      2. Click 'Create catalog'"
  echo "      3. Name: ${CATALOG}, Type: Standard, Storage: Default storage"
  echo "      4. Click Create"
  echo "    Then re-run this script."
  exit 2
fi

echo
# 2. Schemas
echo "▸ creating schemas…"
for schema in bronze silver gold; do
  try_create "${CATALOG}.${schema}" \
    databricks schemas create --json "{\"catalog_name\": \"${CATALOG}\", \"name\": \"${schema}\", \"comment\": \"Mirante ${schema} layer\"}"
done

echo
# 3. Volumes
echo "▸ creating volumes…"
try_create "${CATALOG}.bronze.raw" \
  databricks volumes create --json "{\"catalog_name\": \"${CATALOG}\", \"schema_name\": \"bronze\", \"name\": \"raw\", \"volume_type\": \"MANAGED\", \"comment\": \"Raw HTTP downloads (CGU ZIPs / IBGE / BCB JSONs)\"}"

try_create "${CATALOG}.gold.exports" \
  databricks volumes create --json "{\"catalog_name\": \"${CATALOG}\", \"schema_name\": \"gold\", \"name\": \"exports\", \"volume_type\": \"MANAGED\", \"comment\": \"Gold JSON exports — picked up by GitHub Action\"}"

echo
# 4. Verification
echo "▸ verifying…"
echo "  catalogs containing '${CATALOG}':"
databricks catalogs list 2>/dev/null | grep -E "^${CATALOG}\b" | sed 's/^/    /' || echo "    (none — bootstrap may have failed)"
echo "  schemas in ${CATALOG}:"
databricks schemas list "${CATALOG}" 2>/dev/null | sed 's/^/    /' | head -10 || true
echo "  volumes in ${CATALOG}:"
databricks volumes list "${CATALOG}" bronze 2>/dev/null | sed 's/^/    /' | head -5 || true
databricks volumes list "${CATALOG}" gold   2>/dev/null | sed 's/^/    /' | head -5 || true

echo
echo "✔ Bootstrap done."
echo
echo "Next steps:"
echo "  cd pipelines"
echo "  databricks bundle deploy --target dev"
echo "  databricks bundle run job_populacao_refresh --target dev"
echo "  databricks bundle run job_ipca_refresh      --target dev"
echo "  databricks bundle run job_pbf_refresh       --target dev"

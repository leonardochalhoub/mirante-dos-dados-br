#!/usr/bin/env bash
# Sobe arquivos Hudi escritos localmente pro Databricks UC Volume.
#
# Uso:
#   bash articles/scripts/upload_rais_hudi_to_volume.sh <local_output_dir> [catalog]
#
# Onde:
#   <local_output_dir> = mesmo --output-dir passado pra build_rais_hudi_local.py
#                        (deve conter rais_vinculos_hudi/ dentro dele)
#   [catalog]          = default mirante_prd
#
# Pré-requisito: `databricks` CLI autenticado (databricks auth profiles).

set -euo pipefail

LOCAL_OUT="${1:?uso: $0 <local_output_dir> [catalog]}"
CATALOG="${2:-mirante_prd}"

LOCAL_HUDI_DIR="${LOCAL_OUT%/}/rais_vinculos_hudi"
REMOTE_PATH="dbfs:/Volumes/${CATALOG}/bronze/raw/_open_formats/rais_vinculos_hudi"

if [[ ! -d "${LOCAL_HUDI_DIR}" ]]; then
    echo "✗ não achei ${LOCAL_HUDI_DIR}" >&2
    echo "  rode primeiro: python articles/scripts/build_rais_hudi_local.py --output-dir ${LOCAL_OUT}" >&2
    exit 1
fi

local_size_mb=$(du -sm "${LOCAL_HUDI_DIR}" | cut -f1)
local_files=$(find "${LOCAL_HUDI_DIR}" -type f | wc -l)
echo "local source : ${LOCAL_HUDI_DIR}"
echo "  size       : ${local_size_mb} MB"
echo "  arquivos   : ${local_files}"
echo "remote target: ${REMOTE_PATH}"
echo

# Garante que o folder remoto existe (idempotente). Volume root precisa estar
# criado previamente (UC: Catalog → bronze → raw → _open_formats).
echo "▸ preparando path remoto…"
databricks fs mkdirs "${REMOTE_PATH%/*}" 2>/dev/null || true

# Limpa target remoto pra evitar mistura com runs anteriores. Hudi não tolera
# arquivos órfãos entre commits.
echo "▸ limpando ${REMOTE_PATH} (se existir)…"
databricks fs rm -r "${REMOTE_PATH}" 2>/dev/null || true

# Upload recursivo. `databricks fs cp -r` preserva a estrutura interna .hoodie/
# + ano=YYYY/. Pode demorar dependendo do tamanho + banda.
echo "▸ subindo ${LOCAL_HUDI_DIR} → ${REMOTE_PATH}…"
databricks fs cp -r --overwrite "${LOCAL_HUDI_DIR}" "${REMOTE_PATH}"

# Verificação final: lista o folder remoto
echo
echo "▸ verificação remota:"
databricks fs ls --absolute "${REMOTE_PATH}" || true

echo
echo "✔ upload concluído"
echo "  Próximo: rodar export_platform_stats_json.py pra atualizar a strip"
echo "  databricks bundle run job_finops_refresh  # se quiser regen platform_stats"

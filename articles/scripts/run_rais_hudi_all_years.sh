#!/usr/bin/env bash
#
# Orquestrador: rodar Hudi RAIS pra TODOS os anos disponíveis no Volume,
# baixando .7z (12× menor que TXT extraído) e descomprimindo local por ano.
#
# Por que .7z e não TXT? O Volume Databricks tem AMBOS:
#   /Volumes/.../mte/rais/*.7z              ~49 GB total  (976 arquivos)
#   /Volumes/.../mte/rais_txt_extracted/    ~624 GB total (961 arquivos)
# Os .7z são o input cru do PDET — bronze_rais_vinculos.py extrai eles em TXT.
# Pra rodar Hudi local, preferimos baixar os .7z e extrair na máquina:
#   - 12× menos transferência de rede (~2h vs ~28h em 50 Mbps)
#   - py7zr/7z extrai a 50-100 MB/s local — extração ~15 min
#   - peak disk pico: ~50 GB .7z + ~50 GB TXT do ano corrente = ~100 GB
#
# Pipeline:
#   FASE 1 (uma vez): baixa TODOS os .7z do Volume em paralelo (xargs -P 4)
#   FASE 2 (por ano):
#     a. extrai .7z do ano → ./rais_local/txt/ano=YYYY/*.txt
#     b. python build_rais_hudi_local.py --years YYYY --append
#     c. rm -rf TXT do ano (libera disco)
#   FASE 3 (uma vez): upload do Hudi acumulado pro Volume
#
# Resource floor (workstation):
#   - 16-32 GB RAM
#   - ~100 GB disco livre (50 GB .7z permanente + 50 GB TXT rolling)
#   - banda decente (download = 49 GB)
#   - tempo: 2-4h dependendo do hardware (vs 4-8h pelo TXT)
#
# Uso:
#   bash articles/scripts/run_rais_hudi_all_years.sh \
#        [--catalog mirante_prd] \
#        [--years 2002,2003,...]      # default: descobre via Volume listing
#        [--local-root ./rais_local]   # default: ./rais_local
#        [--parallel 4]                # paralelismo no download (default 4)
#        [--keep-txt]                  # não deleta TXT após cada ano (debug)
#        [--keep-7z]                   # não deleta .7z no fim (default deleta)
#        [--skip-upload]               # roda só o build, sem upload final
#        [--skip-download]             # já tem .7z local, pula a fase 1
#
# Pré-req: databricks CLI autenticado + python3 + pyspark instalado local
#          (pip install pyspark==3.5.* py7zr findspark)
#          7z system binary opcional (acelera ~2× se presente: apt install p7zip-full)

set -euo pipefail

CATALOG="mirante_prd"
LOCAL_ROOT="./rais_local"
YEARS_ARG=""
PARALLEL=4
KEEP_TXT=0
KEEP_7Z=0
SKIP_UPLOAD=0
SKIP_DOWNLOAD=0

while [[ $# -gt 0 ]]; do
    case "$1" in
        --catalog)        CATALOG="$2"; shift 2 ;;
        --years)          YEARS_ARG="$2"; shift 2 ;;
        --local-root)     LOCAL_ROOT="$2"; shift 2 ;;
        --parallel)       PARALLEL="$2"; shift 2 ;;
        --keep-txt)       KEEP_TXT=1; shift ;;
        --keep-7z)        KEEP_7Z=1; shift ;;
        --skip-upload)    SKIP_UPLOAD=1; shift ;;
        --skip-download)  SKIP_DOWNLOAD=1; shift ;;
        -h|--help)
            sed -n '2,40p' "$0"; exit 0 ;;
        *) echo "✗ flag desconhecida: $1" >&2; exit 1 ;;
    esac
done

REMOTE_7Z="dbfs:/Volumes/${CATALOG}/bronze/raw/mte/rais"
LOCAL_7Z="${LOCAL_ROOT}/7z"
LOCAL_TXT="${LOCAL_ROOT}/txt"
LOCAL_OUT="${LOCAL_ROOT}/hudi"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

mkdir -p "${LOCAL_7Z}" "${LOCAL_TXT}" "${LOCAL_OUT}"

# Detecta se sistema tem `7z` binário (mais rápido que py7zr quando disponível)
if command -v 7z &>/dev/null; then
    EXTRACTOR="system_7z"
else
    EXTRACTOR="py7zr"
fi

echo "═══════════════════════════════════════════════════════════════════"
echo " RAIS → Hudi · all-years orchestrator (.7z path)"
echo "═══════════════════════════════════════════════════════════════════"
echo "  catalog       : ${CATALOG}"
echo "  remote .7z    : ${REMOTE_7Z}/"
echo "  local .7z     : ${LOCAL_7Z}/"
echo "  local txt     : ${LOCAL_TXT}/ano=*/"
echo "  local hudi    : ${LOCAL_OUT}/rais_vinculos_hudi/"
echo "  parallel dl   : ${PARALLEL}"
echo "  extractor     : ${EXTRACTOR}"
echo "  keep_txt      : ${KEEP_TXT}     keep_7z       : ${KEEP_7Z}"
echo "  skip_download : ${SKIP_DOWNLOAD}     skip_upload   : ${SKIP_UPLOAD}"
echo

# ─── FASE 1 — download paralelo dos .7z ────────────────────────────────────
if [[ "${SKIP_DOWNLOAD}" -eq 0 ]]; then
    echo "▸ [FASE 1] listando .7z no Volume…"
    REMOTE_LIST=$(databricks fs ls --absolute "${REMOTE_7Z}" --output json 2>/dev/null \
                  | python3 -c "
import json, sys
items = json.load(sys.stdin)
for it in items:
    p = it.get('path', '')
    if p.endswith('.7z'):
        print(p)
" || true)
    if [[ -z "${REMOTE_LIST}" ]]; then
        # fallback: listing via output text-mode
        REMOTE_LIST=$(databricks fs ls --absolute "${REMOTE_7Z}" 2>/dev/null \
                      | awk '{print $NF}' | grep -E '\.7z$' || true)
    fi
    if [[ -z "${REMOTE_LIST}" ]]; then
        echo "✗ nenhum .7z encontrado em ${REMOTE_7Z}" >&2
        echo "  rode primeiro: databricks bundle run job_rais_refresh" >&2
        exit 1
    fi
    n_remote=$(echo "${REMOTE_LIST}" | wc -l | tr -d ' ')
    echo "    ${n_remote} arquivos .7z encontrados no Volume"

    echo "▸ baixando em paralelo (${PARALLEL} workers)…"
    DL_START=$(date +%s)
    # Filtra arquivos já presentes localmente com o mesmo nome — resumable.
    NEEDED_FILES=()
    while IFS= read -r remote_path; do
        fname=$(basename "${remote_path}")
        if [[ -f "${LOCAL_7Z}/${fname}" ]]; then
            local_sz=$(stat -c%s "${LOCAL_7Z}/${fname}" 2>/dev/null || stat -f%z "${LOCAL_7Z}/${fname}" 2>/dev/null || echo "0")
            if [[ "${local_sz}" -gt 1024 ]]; then
                continue   # já baixado e tamanho >1 KB
            fi
        fi
        NEEDED_FILES+=("${remote_path}")
    done <<< "${REMOTE_LIST}"

    n_needed=${#NEEDED_FILES[@]}
    echo "    ${n_needed} pendentes ($(( n_remote - n_needed )) já presentes localmente)"
    if [[ "${n_needed}" -gt 0 ]]; then
        printf '%s\n' "${NEEDED_FILES[@]}" \
            | xargs -P "${PARALLEL}" -I {} \
              bash -c 'src="$1"; dst="$2"; databricks fs cp --overwrite "$src" "$dst/" 2>&1 | tail -1' _ {} "${LOCAL_7Z}"
    fi
    DL_ELAPSED=$(($(date +%s) - DL_START))
    DL_SZ_MB=$(du -sm "${LOCAL_7Z}" | cut -f1)
    echo "    ✓ download concluído em ${DL_ELAPSED}s · ${DL_SZ_MB} MB local"
else
    echo "⊘ [FASE 1] --skip-download → usando .7z já em ${LOCAL_7Z}/"
fi
echo

# ─── Discover years ────────────────────────────────────────────────────────
# Naming convention dos .7z (per ingest_mte_rais.py): "<orig_stem>_<YYYY>.7z"
if [[ -z "${YEARS_ARG}" ]]; then
    echo "▸ descobrindo anos via .7z local…"
    YEARS=$(ls "${LOCAL_7Z}/" 2>/dev/null \
            | grep -E '_[0-9]{4}\.7z$' \
            | sed -E 's/.*_([0-9]{4})\.7z$/\1/' \
            | sort -un)
    if [[ -z "${YEARS}" ]]; then
        echo "✗ nenhum .7z em ${LOCAL_7Z}/ — fase de download falhou?" >&2
        exit 1
    fi
else
    YEARS=$(echo "${YEARS_ARG}" | tr ',' '\n' | sort -u)
fi

YEARS_LIST=$(echo "${YEARS}" | tr '\n' ' ')
N_YEARS=$(echo "${YEARS}" | wc -w | tr -d ' ')
echo "▸ anos a processar (${N_YEARS}): ${YEARS_LIST}"
echo

# ─── FASE 2 — loop ano-a-ano (extract .7z → Hudi append → cleanup) ─────────
extract_year() {
    local year="$1"
    local target_dir="$2"

    mkdir -p "${target_dir}"
    local archives
    archives=$(ls "${LOCAL_7Z}/"*"_${year}.7z" 2>/dev/null || true)
    if [[ -z "${archives}" ]]; then
        echo "    ✗ nenhum .7z ano=${year} em ${LOCAL_7Z}/" >&2
        return 1
    fi

    # PDET empacota VINC + ESTAB no mesmo .7z. Hudi target rais_vinculos_hudi
    # é VINC-only — pula ESTB<YYYY>.* (1985-2018) e RAIS_ESTAB_PUB.* (2019+).
    # Filtramos na extração: economiza disco + alinha com bronze Delta.
    while IFS= read -r zp; do
        local zname=$(basename "${zp}")
        echo "    extraindo ${zname} (filtrando ESTAB)…"
        if [[ "${EXTRACTOR}" == "system_7z" ]]; then
            # -ssc-  → case-insensitive matching (cobre ESTB/estb, .TXT/.txt)
            # -xr!… → exclude recursive pelo padrão
            7z x -o"${target_dir}" -y -ssc- "-xr!estb*" "-xr!rais_estab*" "${zp}" >/dev/null 2>&1 || {
                echo "      ⚠ system 7z falhou em ${zname}, tentando py7zr"
                python3 -c "
import py7zr, re, sys
RE = re.compile(r'(?i)(?:^|/)(estb|rais_estab)')
with py7zr.SevenZipFile('${zp}', 'r') as z:
    wanted = [n for n in (z.getnames() or []) if RE.search(n) is None]
    if wanted:
        z.reset()
        z.extract(path='${target_dir}', targets=wanted)
" || return 1
            }
        else
            python3 -c "
import py7zr, re, sys
RE = re.compile(r'(?i)(?:^|/)(estb|rais_estab)')
try:
    with py7zr.SevenZipFile('${zp}', 'r') as z:
        wanted = [n for n in (z.getnames() or []) if RE.search(n) is None]
        if wanted:
            z.reset()
            z.extract(path='${target_dir}', targets=wanted)
except Exception as e:
    print(f'  py7zr error: {type(e).__name__}: {e}', file=sys.stderr)
    sys.exit(1)
" || return 1
        fi
    done <<< "${archives}"
    return 0
}

START_TS=$(date +%s)
i=0
FAILED_YEARS=()
for year in ${YEARS}; do
    i=$((i + 1))
    YEAR_TXT="${LOCAL_TXT}/ano=${year}"

    echo "─── [${i}/${N_YEARS}] ano=${year} ──────────────────────────────"
    YEAR_START=$(date +%s)

    # 1. Extrai .7z → ano=YYYY/*.txt
    if [[ -d "${YEAR_TXT}" ]] && [[ -n "$(ls -A "${YEAR_TXT}" 2>/dev/null)" ]]; then
        echo "  ⊘ ${YEAR_TXT} já existe — pulando extração"
    else
        if ! extract_year "${year}" "${YEAR_TXT}"; then
            echo "  ✗ extração ${year} falhou — pulando ano" >&2
            FAILED_YEARS+=("${year}(extract)")
            continue
        fi
        sz=$(du -sm "${YEAR_TXT}" 2>/dev/null | cut -f1 || echo "?")
        echo "    ✓ TXT extraído: ${sz} MB"
    fi

    # 2. Build Hudi (append mode acumula partições ano por ano)
    echo "  ▸ build_rais_hudi_local.py --years ${year} --append"
    if ! python3 "${SCRIPT_DIR}/build_rais_hudi_local.py" \
            --input-dir  "${LOCAL_TXT}" \
            --output-dir "${LOCAL_OUT}" \
            --years      "${year}" \
            --append; then
        echo "  ✗ build do ano ${year} falhou — TXT preservado em ${YEAR_TXT}" >&2
        FAILED_YEARS+=("${year}(build)")
        continue
    fi

    # 3. Limpa TXT do ano (mantém .7z; default re-extrai se rodar de novo)
    if [[ "${KEEP_TXT}" -eq 0 ]]; then
        echo "  ▸ removendo ${YEAR_TXT}/ pra liberar disco"
        rm -rf "${YEAR_TXT}"
    fi

    YEAR_ELAPSED=$(($(date +%s) - YEAR_START))
    HUDI_SZ_MB=$(du -sm "${LOCAL_OUT}/rais_vinculos_hudi" 2>/dev/null | cut -f1 || echo "?")
    echo "  ✓ ano=${year} concluído em ${YEAR_ELAPSED}s · Hudi acumulado: ${HUDI_SZ_MB} MB"
    echo
done

TOTAL_ELAPSED=$(($(date +%s) - START_TS))
echo "═══════════════════════════════════════════════════════════════════"
echo "  build concluído em ${TOTAL_ELAPSED}s ($((TOTAL_ELAPSED / 60)) min)"
if [[ -d "${LOCAL_OUT}/rais_vinculos_hudi" ]]; then
    final_sz=$(du -sm "${LOCAL_OUT}/rais_vinculos_hudi" | cut -f1)
    final_files=$(find "${LOCAL_OUT}/rais_vinculos_hudi" -type f | wc -l)
    echo "  Hudi final  : ${final_sz} MB · ${final_files} arquivos"
    echo "  path local  : ${LOCAL_OUT}/rais_vinculos_hudi/"
fi
if [[ ${#FAILED_YEARS[@]} -gt 0 ]]; then
    echo "  ⚠ anos com falha: ${FAILED_YEARS[*]}"
    echo "    re-rode sem --skip-download e sem --years pra retentar só os pendentes"
fi
echo "═══════════════════════════════════════════════════════════════════"

# ─── FASE 3 — upload final pro Volume ──────────────────────────────────────
if [[ "${SKIP_UPLOAD}" -eq 1 ]]; then
    echo
    echo "⊘ --skip-upload setado; pra subir manualmente depois:"
    echo "  bash ${SCRIPT_DIR}/upload_rais_hudi_to_volume.sh ${LOCAL_OUT} ${CATALOG}"
    exit 0
fi

echo
echo "▸ [FASE 3] upload final pro Volume…"
bash "${SCRIPT_DIR}/upload_rais_hudi_to_volume.sh" "${LOCAL_OUT}" "${CATALOG}"

# ─── Cleanup .7z opcional ──────────────────────────────────────────────────
if [[ "${KEEP_7Z}" -eq 0 ]]; then
    echo
    echo "▸ removendo ${LOCAL_7Z}/ (use --keep-7z pra preservar)"
    rm -rf "${LOCAL_7Z}"
fi

echo
echo "✔ all-years Hudi concluído"
echo "  Próximo: re-rodar export_platform_stats_json.py pra refletir na strip"
echo "    databricks bundle run job_finops_refresh --no-wait"

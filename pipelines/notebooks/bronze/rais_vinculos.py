# Databricks notebook source
# MAGIC %md
# MAGIC # bronze · rais_vinculos
# MAGIC
# MAGIC Pipeline em 2 estágios:
# MAGIC 1. **Extract**: descomprime `.7z` → `.txt` (delimitado por `;`, latin-1)
# MAGIC 2. **Auto Loader CSV → Delta append**, mesma estratégia híbrida do
# MAGIC    `bronze_cnes_equipamentos`: BATCH na primeira carga, Auto Loader
# MAGIC    incremental nas execuções seguintes.
# MAGIC
# MAGIC Schema baseado no dicionário PDET/RAIS Vínculos Públicos.
# MAGIC ~62 GB brutos por biênio, ~136M linhas — base do estudo replicado
# MAGIC (Chalhoub 2023, monografia UFRJ MBA Eng. Dados, não publicada).

# COMMAND ----------

# MAGIC %pip install --quiet py7zr
# MAGIC dbutils.library.restartPython()

# COMMAND ----------

dbutils.widgets.text("catalog",            "mirante_prd")
dbutils.widgets.text("zips_dir",           "/Volumes/mirante_prd/bronze/raw/mte/rais")
dbutils.widgets.text("txt_extracted",      "/Volumes/mirante_prd/bronze/raw/mte/rais_txt_extracted")
dbutils.widgets.text("force_reconvert",    "false")
# revalidate_content: lê 128KB/.txt + abre cada .7z pra checar central directory.
# Custa ~minutos em runs com muitos arquivos. NÃO é necessário se nada mudou
# desde a última run (Auto Loader + .done markers já garantem idempotência).
# Ligar quando suspeitar de corrupção silenciosa (ex.: PDET re-publicou um .7z
# com mesmo nome mas conteúdo diferente, ou após upgrade de runtime).
dbutils.widgets.text("revalidate_content", "false")

CATALOG            = dbutils.widgets.get("catalog")
ZIPS_DIR           = dbutils.widgets.get("zips_dir")
TXT_EXTRACTED      = dbutils.widgets.get("txt_extracted")
FORCE_RECONVERT    = dbutils.widgets.get("force_reconvert").lower() in ("true","1","yes")
REVALIDATE_CONTENT = dbutils.widgets.get("revalidate_content").lower() in ("true","1","yes")

BRONZE_TABLE   = f"{CATALOG}.bronze.rais_vinculos"
CHECKPOINT_LOC = f"/Volumes/{CATALOG}/bronze/raw/_autoloader/rais_vinculos/_checkpoint"
SCHEMA_LOC     = f"/Volumes/{CATALOG}/bronze/raw/_autoloader/rais_vinculos/_schema"

print(f"zips_dir={ZIPS_DIR}  txt_extracted={TXT_EXTRACTED}  target={BRONZE_TABLE}")
print(f"force_reconvert={FORCE_RECONVERT}  revalidate_content={REVALIDATE_CONTENT}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 1 — extrair `.7z` → `.txt` (idempotente)

# COMMAND ----------

import re
import ftplib
import shutil
import time
import unicodedata
from pathlib import Path
import py7zr

# Esta tabela é VINC-only (vínculos = grain contrato de trabalho). PDET empacota
# VINC + ESTB (estabelecimentos) no mesmo .7z; ESTB tem schema diferente e contamina
# bronze.rais_vinculos com colunas como BAIRRO FORT/BAIRRO RJ/IND PAT/NAT JURID/
# TIPO ESTBL etc. Filtramos no nome do arquivo:
#   1985–2018 : ESTB<YYYY>.7z/.txt
#   2019+     : RAIS_ESTAB_PUB*.7z/.txt
# Regex casa em qualquer ponto do path (no início ou após /).
RAIS_ESTAB_RE = re.compile(r"(?i)(?:^|/)(estb|rais_estab)")


def _is_vinculo_filename(name: str) -> bool:
    """True se o filename pertence ao dataset VINC (vínculos), False se ESTB."""
    return RAIS_ESTAB_RE.search(name) is None


extracted = 0; skipped = 0; redownloaded = 0; quarantined = 0
# Cleanup uma vez por run de eventuais ESTB que escaparam de runs antigas.
purged_estb_legacy = 0
Path(TXT_EXTRACTED).mkdir(parents=True, exist_ok=True)

# Quarentena: arquivos que continuam corrompidos mesmo após re-download
# vão pra cá pra não bloquear próximas runs e pra investigação manual depois.
QUARANTINE_DIR = Path(ZIPS_DIR) / "_bad"
QUARANTINE_DIR.mkdir(exist_ok=True)

# FTP de origem — deve bater com pipelines/notebooks/ingest/mte_rais.py
FTP_HOST   = "ftp.mtps.gov.br"
FTP_DIR    = "/pdet/microdados/RAIS"
FTP_TIMEOUT = 600


def _parse_year_from_local(name: str) -> int | None:
    """Local filenames são `<orig_stem>_<YYYY>.7z` (sufixo adicionado pelo ingest)."""
    m = re.search(r"_(\d{4})\.7z$", name, flags=re.I)
    return int(m.group(1)) if m else None


def _ftp_redownload(local_path: Path) -> bool:
    """Re-baixa um .7z específico do FTP PDET, sobrescrevendo o local.
    Retorna True se sucesso (size >= 1KB e bate com remote.size se conhecido)."""
    year = _parse_year_from_local(local_path.name)
    if year is None:
        print(f"      ⚠ não consegui extrair ano de {local_path.name}; pulando re-download")
        return False
    orig = re.sub(r"_(\d{4})\.7z$", ".7z", local_path.name, flags=re.I)
    tmp  = local_path.with_suffix(".7z.part")
    tmp.unlink(missing_ok=True)
    try:
        ftp = ftplib.FTP(FTP_HOST, timeout=FTP_TIMEOUT)
        ftp.login()
        ftp.cwd(f"{FTP_DIR}/{year}/")
        ftp.voidcmd("TYPE I")
        try:
            remote_size = ftp.size(orig) or 0
        except Exception:
            remote_size = 0
        with tmp.open("wb") as f:
            ftp.retrbinary(f"RETR {orig}", f.write)
        try: ftp.quit()
        except Exception: pass
        got = tmp.stat().st_size
        if got < 1024 or (remote_size and got < remote_size):
            print(f"      ⚠ re-download incompleto ({got:,} / {remote_size:,} bytes)")
            tmp.unlink(missing_ok=True)
            return False
        tmp.replace(local_path)
        print(f"      ↻ re-baixado: {got:,} bytes (remote {remote_size:,})")
        return True
    except Exception as e:
        tmp.unlink(missing_ok=True)
        print(f"      ⚠ re-download falhou: {type(e).__name__}: {str(e)[:160]}")
        return False


def _try_extract(zp: Path, year: int) -> tuple[bool, str]:
    """Retorna (ok, error_kind). error_kind ∈ {'', 'bad_archive', 'other'}.

    Extrai pra <TXT_EXTRACTED>/ano=<year>/ (Hive-style partition).
    - Garante que `ano` é coluna disponível downstream via partition discovery
    - Evita colisão entre .7z de anos diferentes que produzem .txt de mesmo nome
      (comum no PDET 2019+: RAIS_VINC_PUB_BR.7z em /2009/, /2010/, etc, todos
      contendo um RAIS_VINC_PUB_BR.txt que se sobrescreveriam num dir flat).

    Classifica como `bad_archive` (dispara auto-recovery via re-download FTP):
    - Bad7zFile / Bad7zfileError: assinatura inválida
    - LZMAError: dados internos LZMA corrompidos (magic ok mas blocos quebrados)
    - CrcError: checksum interno do .7z não bate
    - UnsupportedCompressionMethodError: método de compressão suportado mas dado inválido
    - Mensagens com "corrupt", "not a 7z file", "checksum"
    """
    BAD_ARCHIVE_TYPES = (
        "Bad7zFile", "Bad7zfileError",
        "LZMAError",
        "CrcError",
        "UnsupportedCompressionMethodError",
        "DecompressionError",
        "InternalError",
    )
    BAD_ARCHIVE_PHRASES = (
        "not a 7z file",
        "corrupt input",
        "corrupt data",
        "checksum",
        "crc mismatch",
    )
    target = Path(TXT_EXTRACTED) / f"ano={year}"
    target.mkdir(parents=True, exist_ok=True)
    try:
        with py7zr.SevenZipFile(zp, mode='r') as z:
            all_names = list(z.getnames() or [])
            wanted = [n for n in all_names if _is_vinculo_filename(n)]
            skipped_estab = [n for n in all_names if not _is_vinculo_filename(n)]
            if skipped_estab:
                print(f"    ⊘ pulando {len(skipped_estab)} arquivo(s) ESTAB "
                      f"(grain estabelecimento, não pertence a rais_vinculos): "
                      f"{skipped_estab[:3]}{'...' if len(skipped_estab) > 3 else ''}")
            if not wanted:
                # Tudo no .7z é ESTAB → marca como ok mas nada extraído.
                # Downstream validators só recebem `wanted` via _list_archive_names,
                # então target_dir vazio não dispara false-positive.
                return True, ""
            # py7zr's reset() é necessário ao reusar o mesmo handle após getnames();
            # `targets=` filtra a extração ao subset desejado.
            z.reset()
            z.extract(path=target, targets=wanted)
        return True, ""
    except Exception as e:
        kind = type(e).__name__
        msg  = str(e)
        msg_low = msg.lower()
        is_bad = (
            kind in BAD_ARCHIVE_TYPES
            or any(phrase in msg_low for phrase in BAD_ARCHIVE_PHRASES)
        )
        if is_bad:
            print(f"    ✗ {kind}: {msg[:160]}  → classificado como bad_archive")
            return False, "bad_archive"
        print(f"    ✗ {kind}: {msg[:200]}")
        return False, "other"


def _list_archive_names(zp: Path) -> list[str]:
    """Lê apenas o central directory pra obter nomes dos arquivos contidos.
    Falha silenciosamente em arquivos com magic bytes inválidos (retorna []).

    Filtra ESTAB-named entries — bronze.rais_vinculos é VINC-only (ver
    `_is_vinculo_filename`). Se _try_extract pula ESTAB, validators downstream
    (reconciliação, cleanup parcial, quality check) também não devem esperá-los."""
    try:
        with py7zr.SevenZipFile(zp, mode='r') as z:
            names = list(z.getnames() or [])
        return [n for n in names if _is_vinculo_filename(n)]
    except Exception:
        return []


def _cleanup_partial_extraction(target_dir: Path, expected_names: list[str]) -> int:
    """Remove arquivos em `target_dir` que correspondem a nomes que UMA extração
    incompleta da .7z pode ter deixado parcialmente escritos. Retorna quantos
    arquivos foram removidos.

    Importante quando LZMAError ocorre no meio da extração: py7zr abre + escreve
    arquivo .txt destino + começa a descomprimir blocos LZMA, e quando bate num
    bloco corrompido aborta — mas o .txt parcial fica em disco. Spark lê depois
    como CSV e produz linhas truncadas.
    """
    n = 0
    for name in expected_names:
        # py7zr extrai preservando a estrutura interna; nomes podem conter subdirs
        f = target_dir / name
        try:
            if f.is_file():
                f.unlink()
                n += 1
        except Exception:
            pass
    return n


def _validate_txt_content(txt_path: Path, sample_kb: int = 64) -> tuple[bool, str]:
    """Validação de conteúdo de um .txt RAIS sem ler o arquivo inteiro.

    Lê apenas primeiros N KB (cabeçalho + amostra) e últimos N KB (verifica
    truncamento). Total de I/O por arquivo: ~128 KB independente do tamanho real.
    Aplicável tanto na reconciliação (gate antes de gravar .done) quanto no
    quality check pós-extração.

    Sidecars não-CSV (ex.: .COMT, .pdf, .doc, README) co-empacotados nos .7z do
    PDET/RAIS são pulados — eles NÃO são CSV PT-BR e fazem o check de ';' falhar
    sempre, gerando falso-positivo que mandava archives saudáveis pra quarentena.

    Checagens (apenas em arquivos .txt):
      1. tamanho > 1 KB (não-vazio nem só header)
      2. primeira linha (header) decodifica em latin-1 e tem ≥ 5 ';' (CSV PT-BR
         da RAIS tem ~40 colunas separadas por ';')
      3. pelo menos 1 linha de dados após o header com nº de ';' próximo do header
         (tolerância ±2 pra cobrir casos raros de ';' embutido em campo)
      4. cauda termina com '\\n' (não foi truncado mid-line)
    """
    if not txt_path.name.lower().endswith(".txt"):
        return True, "non_txt_sidecar_skipped"
    try:
        size = txt_path.stat().st_size
        if size < 1024:
            return False, f"size_too_small({size}B)"

        sample_size = sample_kb * 1024
        with open(txt_path, "rb") as f:
            head = f.read(sample_size)
            if size > 2 * sample_size:
                f.seek(-sample_size, 2)
                tail = f.read(sample_size)
            else:
                tail = head

        # latin-1 sempre decodifica (1:1 byte→codepoint), mas a RAIS pode ter
        # bytes que não são caracteres legíveis — tudo bem, não é nosso job
        head_text = head.decode("latin-1", errors="replace")
        lines = head_text.split("\n")
        if len(lines) < 2:
            return False, "no_data_row_after_header"

        header = lines[0]
        n_cols_header = header.count(";")
        if n_cols_header < 5:
            return False, f"header_no_csv_separator(found_{n_cols_header}_semicolons)"

        # confere que pelo menos 1 das primeiras 5 linhas de dados tem nº de ; consistente
        data_row_ok = False
        for line in lines[1:6]:
            if not line.strip():
                continue
            n_cols = line.count(";")
            if abs(n_cols - n_cols_header) <= 2:
                data_row_ok = True
                break
        if not data_row_ok:
            return False, f"no_consistent_data_row(header_had_{n_cols_header}_cols)"

        tail_text = tail.decode("latin-1", errors="replace")
        if not tail_text.rstrip(" \r\t").endswith("\n"):
            return False, "tail_truncated_no_final_newline"

        return True, "ok"
    except Exception as e:
        return False, f"validation_exception_{type(e).__name__}"


def _validate_7z(zp: Path) -> tuple[bool, str]:
    """Valida assinatura + central directory SEM descomprimir.

    Captura: magic bytes incorretos (HTML/redirect renomeado .7z), arquivos
    truncados (header lê mas central directory está faltando), arquivos vazios.
    NÃO captura: corrupção de bloco interno (só pega na extração real).
    """
    try:
        if not py7zr.is_7zfile(zp):
            return False, "magic_bytes_invalid"
    except Exception as e:
        return False, f"is_7zfile_raised_{type(e).__name__}"
    try:
        with py7zr.SevenZipFile(zp, mode='r') as z:
            names = z.getnames()
        if not names:
            return False, "empty_archive"
        return True, ""
    except Exception as e:
        kind = type(e).__name__
        msg = str(e)[:120]
        return False, f"{kind}: {msg}" if msg else kind

# DIAGNÓSTICO: o que está no volume antes da extração
print(f"\n=== DIAGNÓSTICO DOS VOLUMES ===")
print(f"ZIPS_DIR    : {ZIPS_DIR}")
try:
    zips_listing = list(Path(ZIPS_DIR).iterdir())
    print(f"  conteúdo total: {len(zips_listing)} entradas")
    for f in sorted(zips_listing)[:20]:
        size = f.stat().st_size if f.is_file() else 0
        print(f"    {f.name:50s}  {size:>14,} bytes")
    if len(zips_listing) > 20:
        print(f"    ... +{len(zips_listing)-20} entradas")
except FileNotFoundError:
    print(f"  ⚠ folder não existe!")
except Exception as e:
    print(f"  ⚠ erro listando: {e}")

print(f"\nTXT_EXTRACTED: {TXT_EXTRACTED}")
try:
    txts_listing = list(Path(TXT_EXTRACTED).iterdir())
    print(f"  conteúdo total: {len(txts_listing)} entradas")
    for f in sorted(txts_listing)[:20]:
        size = f.stat().st_size if f.is_file() else 0
        print(f"    {f.name:50s}  {size:>14,} bytes")
    if len(txts_listing) > 20:
        print(f"    ... +{len(txts_listing)-20} entradas")
except Exception as e:
    print(f"  (vazio ou erro: {e})")
print(f"=== FIM DIAGNÓSTICO ===\n")

# ─── Cleanup: ESTB/ESTAB já extraídos por runs antigas ─────────────────────
# Antes do fix VINC-only, _try_extract chamava extractall(); ESTB<YYYY>.txt
# (1985-2018) e RAIS_ESTAB_PUB*.txt (2019+) ficavam misturados nos dirs
# ano=YYYY/. Step 2 lia eles como CSV junto com VINC, contaminando bronze
# com schema mismatch (BAIRRO FORT, NAT JURID, TIPO ESTBL etc).
#
# IMPORTANTE: deletar arquivos do disco NÃO limpa bronze.rais_vinculos —
# rode com force_reconvert=true pra reconstruir a tabela depois.
print("=== CLEANUP ESTAB FILES JÁ EXTRAÍDOS ===")
estab_purged = 0; estab_purged_bytes = 0
year_partitions = [d for d in Path(TXT_EXTRACTED).iterdir() if d.is_dir() and d.name.startswith("ano=")]
for ydir in year_partitions:
    for f in ydir.iterdir():
        if not f.is_file():
            continue
        if RAIS_ESTAB_RE.search(f.name):
            try:
                sz = f.stat().st_size
                f.unlink()
                estab_purged += 1
                estab_purged_bytes += sz
                if estab_purged <= 5:
                    print(f"  ✗ removido {ydir.name}/{f.name}  ({sz/1_048_576:.1f} MB)")
            except Exception as e:
                print(f"  ⚠ falha ao deletar {f}: {type(e).__name__}: {e}")
purged_estb_legacy = estab_purged
if estab_purged > 0:
    print(f"\n  ✓ {estab_purged} arquivos ESTAB removidos · {estab_purged_bytes/1_048_576:,.0f} MB liberado")
    print(f"  ⚠ bronze.rais_vinculos pode ainda ter linhas dessas extrações antigas;")
    print(f"    rode UMA vez com force_reconvert=true pra reconstruir limpo.")
else:
    print(f"  ⊘ nenhum arquivo ESTAB encontrado (já filtrado ou primeira run pós-fix)")
print("=== FIM CLEANUP ESTAB ===\n")

# ─── Migração: detecta .txt FLAT de extrações pré ano=YYYY/ ─────────────────
# Versões antigas extraíam tudo plano em TXT_EXTRACTED. Se Step 2 ler esses
# .txt flat, ele NÃO vai ter coluna `ano` (vinha do partition path agora) e
# falha em partitionBy("ano"). Detecta e força force_reconvert=true.
flat_txts_legacy = [f for f in Path(TXT_EXTRACTED).glob("*.txt") if f.is_file()]
flat_txts_legacy += [f for f in Path(TXT_EXTRACTED).glob("*.TXT") if f.is_file()]
if flat_txts_legacy:
    if FORCE_RECONVERT:
        print(f"⚠ Limpando {len(flat_txts_legacy)} .txt FLAT (resíduo pré-migração ano=YYYY/)…")
        for f in flat_txts_legacy:
            try: f.unlink()
            except Exception as e: print(f"  ⚠ falha ao deletar {f.name}: {e}")
        # Remove também markers .done/.bad antigos pra forçar re-extração e re-validação
        for marker in list(Path(TXT_EXTRACTED).glob("_*.done")) + list(Path(TXT_EXTRACTED).glob("_*.bad")):
            try: marker.unlink()
            except Exception: pass
    else:
        print(f"⚠ DETECTADO {len(flat_txts_legacy)} .txt FLAT em {TXT_EXTRACTED}")
        print(f"  Esses arquivos vêm de uma run anterior (pré-migração ano=YYYY/).")
        print(f"  Step 2 vai falhar lendo eles porque NÃO tem coluna `ano`.")
        print(f"  ")
        print(f"  → SOLUÇÃO: rode UMA VEZ com force_reconvert=true pra:")
        print(f"      1. Limpar .txt flat + markers antigos")
        print(f"      2. Re-extrair tudo em <TXT_EXTRACTED>/ano=YYYY/")
        print(f"      3. Recriar bronze table do zero")
        print(f"  Primeiros 5 .txt flat detectados:")
        for f in flat_txts_legacy[:5]:
            print(f"    {f.name}  ({f.stat().st_size:,} bytes)")
        dbutils.notebook.exit("MIGRATION REQUIRED: legacy flat .txt files; run with force_reconvert=true")

# ─── Restore de quarentena quando force_reconvert=true ─────────────────────
# Runs anteriores podem ter mandado .7z saudáveis pra _bad/ por causa de bugs
# de validação (ex.: sidecar .COMT falhando check de CSV antes do fix que pula
# arquivos não-.txt). Quando force_reconvert=true, devolvemos esses archives
# pro ZIPS_DIR pra que o loop principal os processe novamente.
if FORCE_RECONVERT and QUARANTINE_DIR.exists():
    quarantined_archives = sorted(QUARANTINE_DIR.glob("*.7z"))
    if quarantined_archives:
        print(f"⚠ Restaurando {len(quarantined_archives)} .7z de {QUARANTINE_DIR} → {ZIPS_DIR} (force_reconvert=true)…")
        restored = 0
        for src in quarantined_archives:
            dst = Path(ZIPS_DIR) / src.name
            try:
                if dst.exists():
                    src.unlink()  # já tem cópia ativa, descarta a quarentena
                else:
                    src.replace(dst)
                restored += 1
            except Exception as e:
                print(f"  ⚠ falha ao restaurar {src.name}: {type(e).__name__}: {e}")
        print(f"  ✓ {restored} archives restaurados pra reprocessamento")

zips = sorted(Path(ZIPS_DIR).glob("*.7z"))
print(f".7z encontrados pra extração: {len(zips)}")

if not zips:
    print(f"⚠ NENHUM .7z em {ZIPS_DIR}.")
    print(f"  Causa provável: ingest_mte_rais não baixou nada (PDET URL errada/mudou).")
    print(f"  Workarounds:")
    print(f"  1. Investigar URL_TEMPLATES em pipelines/notebooks/ingest/mte_rais.py")
    print(f"     (PDET reestruturou várias vezes desde 2023)")
    print(f"  2. Fazer upload manual dos .7z direto no Volume:")
    print(f"     UI Databricks → Catalog → mirante_prd → bronze → raw → mte/rais → Upload")
    print(f"  3. Ou copiar via CLI:")
    print(f"     databricks fs cp ./RAIS_VINC_PUB_BR_2021.7z dbfs:{ZIPS_DIR}/")
    dbutils.notebook.exit("SKIPPED: no .7z files to extract")

# ─── Re-validação de markers .done existentes — derruba os falsos-positivos ──
# Se um run anterior gravou .done mas o CONTEÚDO está ruim (ex.: ano=2023
# extraiu .COMT em vez de .txt, ou tail truncado), o conteúdo do bronze fica
# corrompido. Aqui revalidamos cada .done existente; se falhar, REMOVEMOS o
# marker pra forçar re-extração no loop principal (que tem auto-recovery).
#
# Custoso: abre cada .7z (central directory) + lê 128KB de cada .txt. Em runs
# rotineiras (sem suspeita de corrupção), pular pra fast-path.
revalidated_ok = 0
revalidated_removed = 0
revalidate_skipped = 0

if not REVALIDATE_CONTENT and not FORCE_RECONVERT:
    n_done = sum(1 for zp in zips if (Path(TXT_EXTRACTED) / f"_{zp.stem}.done").exists())
    print(f"⊘ FAST PATH: pulando re-validação de {n_done} markers .done "
          f"(revalidate_content=false). Use revalidate_content=true se suspeitar "
          f"de conteúdo corrompido.\n")
    revalidated_ok = n_done
else:
    print("=== RE-VALIDAÇÃO DE MARKERS .done EXISTENTES ===")
    for zp in zips:
        marker_ok = Path(TXT_EXTRACTED) / f"_{zp.stem}.done"
        if not marker_ok.exists():
            continue
        year = _parse_year_from_local(zp.name)
        if year is None:
            revalidate_skipped += 1
            continue
        target_dir = Path(TXT_EXTRACTED) / f"ano={year}"
        if not target_dir.exists():
            # marker .done existe mas dir não existe — situação inconsistente;
            # remove marker pra forçar re-extração
            try: marker_ok.unlink()
            except Exception: pass
            revalidated_removed += 1
            continue

        expected = _list_archive_names(zp)
        if not expected:
            # arquivo .7z corrompido — central directory não retorna nada
            revalidate_skipped += 1
            continue

        bad: list[str] = []
        for name in expected:
            f = target_dir / name
            if not f.exists():
                bad.append(f"{name}(missing)")
                continue
            ok_c, reason_c = _validate_txt_content(f)
            if not ok_c:
                bad.append(f"{name}({reason_c})")

        if bad:
            if revalidated_removed < 5:
                print(f"  ⚠ {zp.name}: {bad[:2]} → removendo .done marker (será re-extraído)")
            try: marker_ok.unlink()
            except Exception: pass
            revalidated_removed += 1
        else:
            revalidated_ok += 1

    print(f"\n  ✓ {revalidated_ok} markers .done revalidados (conteúdo OK)")
    print(f"  ⚠ {revalidated_removed} markers .done REMOVIDOS (conteúdo inválido → re-extrair)")
    print(f"  ⊘ {revalidate_skipped} pulados (sem ano parseável ou .7z corrompido)")
    print("=== FIM RE-VALIDAÇÃO .done ===\n")

# ─── Reconciliação de markers — preserva extrações já feitas ────────────────
# Quando markers .done foram limpos (force_reconvert=true em run anterior, ou
# sumiço inesperado), os .txt em ano=YYYY/ ainda estão lá — preferimos NÃO
# re-extrair (custoso) se o conteúdo parece OK.
#
# Critérios pra reconciliar (gerar .done sem extrair):
#   1. Não há marker .done nem .bad pra esse .7z
#   2. central directory do .7z lista N entradas (getnames)
#   3. TODAS as N entradas existem em ano=YYYY/
#   4. ratio total_txt_size / .7z_size ≥ 2.0 (LZMA típico comprime 5-15× em texto;
#      ratio 2 é piso conservador que pega arquivos parciais mas tolera variação)
#
# Se TODAS as 4 baterem → marker .done com texto "reconciled" + skip da extração.
# Senão, .7z entra normalmente na pré-validação + extração.
print("=== RECONCILIAÇÃO DE MARKERS ===")
reconciled = 0; reconcile_skipped_partial = 0; reconcile_skipped_no_dir = 0
for zp in zips:
    marker_ok  = Path(TXT_EXTRACTED) / f"_{zp.stem}.done"
    marker_bad = Path(TXT_EXTRACTED) / f"_{zp.stem}.bad"
    if marker_ok.exists() or marker_bad.exists():
        continue
    year = _parse_year_from_local(zp.name)
    if year is None:
        continue
    target_dir = Path(TXT_EXTRACTED) / f"ano={year}"
    if not target_dir.exists():
        reconcile_skipped_no_dir += 1
        continue

    expected = _list_archive_names(zp)
    if not expected:
        continue

    all_present = True
    total_txt_size = 0
    missing_or_empty: list[str] = []
    for name in expected:
        f = target_dir / name
        if not f.exists():
            all_present = False
            missing_or_empty.append(f"{name}(missing)")
            break
        sz = f.stat().st_size
        if sz == 0:
            all_present = False
            missing_or_empty.append(f"{name}(empty)")
            break
        total_txt_size += sz

    if not all_present:
        reconcile_skipped_partial += 1
        continue

    zp_size = zp.stat().st_size
    ratio = (total_txt_size / zp_size) if zp_size > 0 else 0
    if ratio < 2.0:
        # Arquivos existem mas ratio suspeito (provável extração parcial) →
        # deixa SEM marker pra que pré-validação + extração lidem com isso
        reconcile_skipped_partial += 1
        if reconcile_skipped_partial <= 5:
            print(f"  ratio baixo ({ratio:.2f}) {zp.name}: txt={total_txt_size:,}B / 7z={zp_size:,}B "
                  f"→ vai re-extrair")
        continue

    # Gate adicional: valida conteúdo do PRIMEIRO .txt real (header CSV + linha de
    # dados + truncamento). Se falhar, não reconcilia — extração vai pegar.
    # Pula sidecars (.COMT, .pdf etc) — `expected` vem alfabético e .COMT < .txt.
    first_txt_name = next((n for n in expected if n.lower().endswith(".txt")), None)
    if first_txt_name is None:
        # Archive sem .txt? Não dá pra validar conteúdo — deixa extração lidar.
        reconcile_skipped_partial += 1
        continue
    first_txt = target_dir / first_txt_name
    content_ok, content_reason = _validate_txt_content(first_txt)
    if not content_ok:
        reconcile_skipped_partial += 1
        if reconcile_skipped_partial <= 5:
            print(f"  conteúdo inválido em {first_txt.name}: {content_reason} → vai re-extrair")
        continue

    marker_ok.write_text(
        f"reconciled at {time.strftime('%Y-%m-%d %H:%M:%S')}\n"
        f"txt_total={total_txt_size} 7z={zp_size} ratio={ratio:.2f}\n"
        f"content_check={content_reason}\n"
    )
    reconciled += 1

print(f"\n  ✓ reconciliados {reconciled} arquivos (markers .done re-criados)")
print(f"  ⊘ pulados {reconcile_skipped_partial} (ratio baixo/parcial → re-extrair)")
print(f"  ⊘ pulados {reconcile_skipped_no_dir} (ano= dir não existe → re-extrair)")
print("=== FIM RECONCILIAÇÃO ===\n")

# ─── Pré-validação: cada .7z é checado antes do loop de extração ────────────
# Pega TODOS os arquivos corrompidos de uma vez (não só os que o glob alcança
# antes do loop falhar). Re-baixa do FTP PDET cada um que falhar a validação;
# se persistir → quarentena. Pula arquivos com .done (já extraídos OK).
print("=== PRÉ-VALIDAÇÃO DE CADA .7z ===")
v_ok = 0; v_bad = 0; v_recovered = 0; v_quarantined = 0
v_still_bad: list[str] = []

for zp in list(zips):  # cópia: vamos re-glob no fim
    marker_ok  = Path(TXT_EXTRACTED) / f"_{zp.stem}.done"
    marker_bad = Path(TXT_EXTRACTED) / f"_{zp.stem}.bad"
    if marker_ok.exists() and not FORCE_RECONVERT:
        # Já foi extraído com sucesso em run anterior → .txt já está em TXT_EXTRACTED;
        # não re-validamos o .7z (irrelevante pro pipeline downstream).
        continue
    if marker_bad.exists() and not FORCE_RECONVERT:
        # Já tentamos antes e falhou re-download; pula até force_reconvert=true.
        continue

    is_valid, why = _validate_7z(zp)
    if is_valid:
        v_ok += 1
        continue

    v_bad += 1
    print(f"  ✗ {zp.name} ({zp.stat().st_size:,} bytes) — {why}")
    print(f"    → deletando e re-baixando do FTP {FTP_HOST}…")
    try:
        zp.unlink()
    except Exception as e:
        print(f"      ⚠ falha ao deletar: {type(e).__name__}: {e}")
        continue

    if not _ftp_redownload(zp):
        marker_bad.write_text(
            f"redownload_failed (validation) at {time.strftime('%Y-%m-%d %H:%M:%S')}\n"
            f"reason: {why}\n"
        )
        v_quarantined += 1
        v_still_bad.append(zp.name)
        continue

    is_valid, why2 = _validate_7z(zp)
    if is_valid:
        v_recovered += 1
        print(f"      ✓ recuperado e validado")
        continue

    print(f"      ✗ ainda inválido após re-download: {why2}")
    bad_dest = QUARANTINE_DIR / zp.name
    try:
        zp.replace(bad_dest)
        print(f"      ⚠ quarentena → {bad_dest}")
    except Exception as e:
        print(f"      ⚠ falha mover quarentena: {type(e).__name__}: {e}")
    marker_bad.write_text(
        f"bad_after_redownload (validation) at {time.strftime('%Y-%m-%d %H:%M:%S')}\n"
        f"reason_before: {why}\nreason_after: {why2}\n"
    )
    v_quarantined += 1
    v_still_bad.append(zp.name)

print(f"\nValidação: {v_ok} válidos, {v_bad} inválidos detectados, "
      f"{v_recovered} recuperados via re-download, {v_quarantined} em quarentena")
if v_still_bad:
    print(f"\nArquivos PERMANENTEMENTE ruins (movidos pra _bad/, não vão pro bronze):")
    for name in v_still_bad:
        print(f"  - {name}")
    print("  → causa provável: fonte PDET hospeda arquivo corrompido nesse path.")
    print("  → pra retentar mais tarde: rode com force_reconvert=true.")

# Re-glob: arquivos podem ter ido pra quarentena (sumiram de ZIPS_DIR)
zips = sorted(Path(ZIPS_DIR).glob("*.7z"))
print(f"\n.7z restantes pra extração: {len(zips)}")
print("=== FIM PRÉ-VALIDAÇÃO ===\n")

for zp in zips:
    # Marcador `.done` = extraído com sucesso. Marcador `.bad` = quarentena prévia
    # (não tenta de novo até force_reconvert=true, pra não loopar em fonte ruim).
    marker_ok  = Path(TXT_EXTRACTED) / f"_{zp.stem}.done"
    marker_bad = Path(TXT_EXTRACTED) / f"_{zp.stem}.bad"
    if marker_ok.exists() and not FORCE_RECONVERT:
        skipped += 1; continue
    if marker_bad.exists() and not FORCE_RECONVERT:
        print(f"  ⊘ {zp.name} já em quarentena (.bad marker); use force_reconvert=true pra retentar")
        quarantined += 1; continue

    year = _parse_year_from_local(zp.name)
    if year is None:
        print(f"  ⚠ {zp.name}: ano não parseável do nome local; pulando")
        marker_bad.write_text(
            f"year_not_parseable at {time.strftime('%Y-%m-%d %H:%M:%S')}\n"
            "esperado: <stem>_<YYYY>.7z; ingest deve adicionar sufixo de ano\n"
        )
        quarantined += 1; continue

    # Antes de extrair: captura lista de nomes contidos no .7z. Se a extração
    # falhar com bad_archive, usamos essa lista pra remover .txt parciais que
    # py7zr escreveu antes de bater num bloco corrompido (típico em LZMAError).
    expected_names = _list_archive_names(zp)
    target_dir = Path(TXT_EXTRACTED) / f"ano={year}"

    print(f"  extraindo {zp.name} ({zp.stat().st_size:,} bytes) → ano={year}/...")
    ok, err = _try_extract(zp, year)
    # GATE: extração completou com sucesso técnico, mas o CONTEÚDO dos .txt
    # pode estar quebrado (header sem ';', cauda truncada, .COMT em vez de
    # .txt etc). Se conteúdo inválido → re-classifica como bad_archive pra
    # entrar no fluxo de auto-recovery (delete + redownload + retry).
    if ok and expected_names and target_dir.exists():
        bad_content_files = []
        for name in expected_names:
            f = target_dir / name
            if not f.exists():
                bad_content_files.append(f"{name}(missing_after_extract)")
                continue
            ok_c, reason_c = _validate_txt_content(f)
            if not ok_c:
                bad_content_files.append(f"{name}({reason_c})")
        if bad_content_files:
            print(f"    ✗ extração técnica OK mas CONTEÚDO inválido em "
                  f"{len(bad_content_files)} arquivo(s): {bad_content_files[:2]}")
            print(f"    → re-classificando como bad_archive p/ auto-recovery")
            ok = False
            err = "bad_archive"

    if ok:
        marker_ok.write_text("ok"); extracted += 1
        print(f"    ✓ ok (conteúdo validado)")
        continue

    # Bad7zFile / LZMAError / CrcError → deleta, re-baixa, tenta uma vez.
    # Outros erros (OSError, MemoryError etc): não tenta re-download, mas LIMPA
    # parciais pra não deixar .txt truncado no Volume.
    if err != "bad_archive":
        if expected_names and target_dir.exists():
            n_cleaned = _cleanup_partial_extraction(target_dir, expected_names)
            if n_cleaned:
                print(f"    ⊘ removidos {n_cleaned} .txt parciais (erro não-recuperável)")
        continue

    # Limpa .txt parciais que py7zr deixou em disco antes de abortar
    if expected_names and target_dir.exists():
        n_cleaned = _cleanup_partial_extraction(target_dir, expected_names)
        if n_cleaned:
            print(f"    ⊘ removidos {n_cleaned} .txt parciais da extração que falhou")

    print(f"    → arquivo corrompido; deletando e re-baixando do FTP {FTP_HOST}…")
    try:
        zp.unlink()
    except Exception as e:
        print(f"      ⚠ falha ao deletar: {type(e).__name__}: {e}")
        continue

    if not _ftp_redownload(zp):
        # Não conseguimos re-baixar — registra como bad e segue
        marker_bad.write_text(f"redownload_failed at {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
        quarantined += 1
        continue

    redownloaded += 1
    # Após re-download: re-captura nomes (pode mudar se source FTP mudou) +
    # garante que dir destino está limpo dos parciais antes de re-extrair
    expected_names_post = _list_archive_names(zp)
    if expected_names_post and target_dir.exists():
        _cleanup_partial_extraction(target_dir, expected_names_post)
    print(f"    re-tentando extração após re-download…")
    ok, err = _try_extract(zp, year)
    # Mesmo gate de conteúdo após re-extract — se PDET source também tem
    # conteúdo inválido (ex.: .COMT em vez de .txt), force quarentena
    if ok and expected_names_post and target_dir.exists():
        bad_after_rd = []
        for name in expected_names_post:
            f = target_dir / name
            if not f.exists():
                bad_after_rd.append(f"{name}(missing)")
                continue
            ok_c, reason_c = _validate_txt_content(f)
            if not ok_c:
                bad_after_rd.append(f"{name}({reason_c})")
        if bad_after_rd:
            print(f"      ✗ ainda CONTEÚDO inválido pós-redownload: {bad_after_rd[:2]}")
            print(f"      → fonte PDET tem problema permanente nesse arquivo")
            ok = False
            err = "bad_archive"
    if ok:
        marker_ok.write_text("ok"); extracted += 1
        print(f"    ✓ ok (após re-download)")
        continue

    # Ainda ruim depois do re-download → quarentena (fonte do PDET deve estar mesmo corrompida)
    # Limpa qualquer .txt parcial gerado pela última tentativa antes de quarantinar
    if expected_names_post and target_dir.exists():
        n_cleaned = _cleanup_partial_extraction(target_dir, expected_names_post)
        if n_cleaned:
            print(f"    ⊘ removidos {n_cleaned} .txt parciais antes da quarentena")
    bad_dest = QUARANTINE_DIR / zp.name
    try:
        zp.replace(bad_dest)
        print(f"    ⚠ quarentena → {bad_dest}")
    except Exception as e:
        print(f"      ⚠ falha ao mover pra quarentena: {type(e).__name__}: {e}")
    marker_bad.write_text(f"bad_after_redownload at {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
    quarantined += 1

# Lista contagem por ano= partição (Hive-style)
year_dirs = sorted([d for d in Path(TXT_EXTRACTED).iterdir() if d.is_dir() and d.name.startswith("ano=")])
print(f"\nApós extração ({extracted} novos, {skipped} skipped, "
      f"{redownloaded} re-baixados, {quarantined} em quarentena):")
total_files = 0
for d in year_dirs:
    inner = list(d.rglob("*"))
    n_files = sum(1 for f in inner if f.is_file())
    total_files += n_files
    by_ext = {}
    for f in inner:
        if f.is_file():
            by_ext.setdefault(f.suffix.lower(), 0)
            by_ext[f.suffix.lower()] += 1
    ext_summary = ", ".join(f"{e or '(no ext)'}:{n}" for e, n in sorted(by_ext.items(), key=lambda kv: -kv[1]))
    print(f"  {d.name:15s}  {n_files} arquivos  [{ext_summary}]")
print(f"  TOTAL: {total_files} arquivos em {len(year_dirs)} partições ano=YYYY/")

# ─── Quality check pós-extração: ratio txt_total / 7z por arquivo .done ────
# Custoso: abre cada .7z + lê 128KB de cada .txt. Mesmo gate que re-validação:
# pula no fast path e só roda quando explicitamente pedido OU quando algo novo
# foi extraído nesta run (validar o que acabou de chegar).
should_quality_check = REVALIDATE_CONTENT or FORCE_RECONVERT or extracted > 0 or redownloaded > 0
if not should_quality_check:
    print(f"\n⊘ FAST PATH: pulando quality check ({skipped} arquivos já com .done, "
          f"nada novo extraído). Use revalidate_content=true pra forçar.\n")
else:
    print("\n=== QUALITY CHECK ===")
    print("Verificando se cada .7z extraído (.done marker) produziu .txt com tamanho consistente…")
    quality_issues: list[str] = []
    quality_ok = 0
    quality_skipped = 0
    for done_marker in sorted(Path(TXT_EXTRACTED).glob("_*.done")):
        stem_with_underscore = done_marker.stem  # _RAIS_VINC_PUB_BR_2009 (no leading _ removed by stem)
        # `.stem` of "_FOO.done" returns "_FOO" — keep the underscore prefix consistent
        if not stem_with_underscore.startswith("_"):
            continue
        file_stem = stem_with_underscore[1:]  # strip leading _
        zp = Path(ZIPS_DIR) / f"{file_stem}.7z"
        if not zp.exists():
            # .7z pode ter ido pra _bad/ ou foi deletado — marker .done sem .7z é orphan
            quality_skipped += 1
            continue
        year = _parse_year_from_local(zp.name)
        if year is None:
            quality_skipped += 1
            continue
        target_dir = Path(TXT_EXTRACTED) / f"ano={year}"
        if not target_dir.exists():
            quality_issues.append(f"  ✗ {zp.name}: marker .done existe mas ano={year}/ não")
            continue

        expected = _list_archive_names(zp)
        if not expected:
            quality_skipped += 1
            continue

        txt_total = 0
        missing = []
        invalid_content: list[str] = []
        for name in expected:
            f = target_dir / name
            if not f.exists():
                missing.append(name)
                continue
            txt_total += f.stat().st_size
            # Content check (header CSV + linha de dados + truncamento)
            ok_c, reason_c = _validate_txt_content(f)
            if not ok_c:
                invalid_content.append(f"{name}({reason_c})")

        zp_size = zp.stat().st_size
        ratio = (txt_total / zp_size) if zp_size > 0 else 0

        if missing:
            quality_issues.append(f"  ✗ {zp.name}: {len(missing)} .txt esperados MISSING: {missing[:3]}")
        elif invalid_content:
            quality_issues.append(f"  ✗ {zp.name}: conteúdo inválido em {len(invalid_content)} arquivo(s): "
                                  f"{invalid_content[:2]}")
        elif ratio < 1.5:
            quality_issues.append(f"  ⚠ {zp.name}: ratio txt/7z={ratio:.2f} (suspeito; "
                                  f"txt_total={txt_total/1_048_576:.1f}MB / 7z={zp_size/1_048_576:.1f}MB)")
        else:
            quality_ok += 1

    print(f"  ✓ {quality_ok} arquivos com tamanhos consistentes")
    print(f"  ⊘ {quality_skipped} pulados (sem .7z source ou metadata)")
    if quality_issues:
        print(f"  ⚠ {len(quality_issues)} arquivos com issues:")
        for issue in quality_issues[:30]:
            print(issue)
        if len(quality_issues) > 30:
            print(f"  ... +{len(quality_issues) - 30}")
    else:
        print(f"  ✓ nenhum issue detectado")
    print("=== FIM QUALITY CHECK ===\n")

# Glob recursivo pelas partições — picks up .txt + .TXT + .csv etc dentro de ano=YYYY/
txts = sorted(Path(TXT_EXTRACTED).glob("ano=*/*.txt")) + sorted(Path(TXT_EXTRACTED).glob("ano=*/*.TXT"))
if not txts:
    for alt_ext in ('*.csv', '*.CSV', '*.dat', '*.DAT'):
        alts = sorted(Path(TXT_EXTRACTED).glob(f"ano=*/{alt_ext}"))
        if alts:
            print(f"  ⚠ encontrei {len(alts)} arquivos {alt_ext} dentro de ano=YYYY/ — ajuste a glob no Step 2")
            break
    print("⚠ Nenhum .txt processável em ano=YYYY/. Verifique diagnóstico acima.")
    dbutils.notebook.exit("SKIPPED: no .txt files after extraction")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 2 — Auto Loader CSV → Delta append (modo híbrido)

# COMMAND ----------

from pyspark.sql import functions as F

table_exists = spark.catalog.tableExists(BRONZE_TABLE)
existing_rows = spark.read.table(BRONZE_TABLE).count() if table_exists else 0
checkpoint_initialized = False
try: checkpoint_initialized = bool(dbutils.fs.ls(CHECKPOINT_LOC))
except Exception: pass

use_batch = (not table_exists) or (existing_rows == 0) or (not checkpoint_initialized) or FORCE_RECONVERT

if FORCE_RECONVERT and table_exists:
    print("⚠ FORCE_RECONVERT=true → drop bronze + checkpoint")
    spark.sql(f"DROP TABLE IF EXISTS {BRONZE_TABLE}")
    try: dbutils.fs.rm(CHECKPOINT_LOC, True); dbutils.fs.rm(SCHEMA_LOC, True)
    except Exception: pass

# Helper: deriva `ano` (int) do path Hive-partition `<TXT_EXTRACTED>/ano=YYYY/<arquivo>`
# usado tanto em batch quanto em Auto Loader (regex em _metadata.file_path)
def _add_ano_from_path(df):
    return (
        df.withColumn("_source_file", F.col("_metadata.file_path"))
          .withColumn("ano",
              F.regexp_extract(F.col("_metadata.file_path"), r"/ano=(\d{4})(?:/|$)", 1).cast("int")
          )
          .withColumn("_ingest_ts", F.current_timestamp())
    )


def _sanitize_col(name: str) -> str:
    """Converte um nome de coluna RAIS pra snake_case ASCII compatível com Delta.
    Delta rejeita ' ,;{}()\n\t=' nos nomes; CSV da RAIS tem todos: 'Bairros SP',
    'Vínculo Ativo 31/12', 'Faixa Remun Dezem (SM)', 'Mês Admissão' etc.

    Estratégia (preserva nomes já snake_case como 'ano', '_source_file'):
    1. NFKD normalize + strip acentos (Vínculo → Vinculo, Mês → Mes)
    2. Replace qualquer não-[a-zA-Z0-9_] por '_' (espaço, /, (), -, etc.)
    3. Collapse múltiplos '_' e strip leading/trailing
    4. Lower-case
    Mantém prefixo `_` se já existir (ex.: _source_file, _ingest_ts).
    """
    if not name:
        return "col"
    leading_underscore = name.startswith("_")
    nfkd = unicodedata.normalize("NFKD", name)
    no_accents = "".join(c for c in nfkd if not unicodedata.combining(c))
    sanitized = re.sub(r"[^a-zA-Z0-9_]+", "_", no_accents)
    sanitized = re.sub(r"_+", "_", sanitized).strip("_").lower()
    if not sanitized:
        sanitized = "col"
    return ("_" + sanitized) if leading_underscore else sanitized


def _sanitize_columns(df):
    """Renomeia TODAS as colunas pra snake_case ASCII. Idempotente (já-clean
    permanece clean). Imprime um sample dos renames pra auditoria.

    Colisões: a RAIS PDET tem variações cross-year do mesmo header (ex.: 'Município'
    em alguns anos, 'MUNICIPIO' em outros — Auto Loader guarda os dois como colunas
    distintas no schema location, e ambas sanitizam pra 'municipio'). Delta rejeita
    duplicatas (`DELTA_DUPLICATE_COLUMNS_FOUND`). Bronze é STRING-ONLY: NÃO podemos
    coalescer/dropar valores aqui — preservamos ambas com sufixo `_dup2`, `_dup3`
    e deixamos pro silver decidir como reconciliar."""
    sanitized = [_sanitize_col(c) for c in df.columns]
    seen: dict[str, int] = {}
    final: list[str] = []
    collisions: list[tuple[str, str, str]] = []
    for orig, san in zip(df.columns, sanitized):
        seen[san] = seen.get(san, 0) + 1
        if seen[san] == 1:
            final.append(san)
        else:
            new = f"{san}_dup{seen[san]}"
            final.append(new)
            collisions.append((orig, san, new))
    renames = list(zip(df.columns, final))
    changed = [(orig, new) for orig, new in renames if orig != new]
    if changed:
        print(f"  sanitizando {len(changed)} colunas; sample: "
              f"{', '.join(f'{a!r}→{b!r}' for a, b in changed[:5])}"
              + (f" (+{len(changed)-5})" if len(changed) > 5 else ""))
    if collisions:
        print(f"  ⚠ {len(collisions)} colisão(ões) de sanitização — preservando com sufixo _dupN:")
        for orig, san, new in collisions[:10]:
            print(f"    {orig!r} colidiu com {san!r} → {new!r}")
        if len(collisions) > 10:
            print(f"    ... +{len(collisions)-10}")
    return df.toDF(*final)

# Path de leitura: glob explícito pelas partições ano=YYYY/ pra evitar
# pegar arquivos órfãos no root de TXT_EXTRACTED (markers .done/.bad ou
# resíduos de runs antigas que sobreviveram à migração).
READ_PATH = f"{TXT_EXTRACTED}/ano=*/"

if use_batch:
    print(f"▸ MODO BATCH — table_exists={table_exists} rows={existing_rows:,}")
    print(f"  lendo: {READ_PATH}")
    df = _sanitize_columns(_add_ano_from_path(
        spark.read
            .option("header", "true")
            .option("sep", ";")
            .option("encoding", "latin1")
            .option("inferSchema", "false")  # tudo string no bronze; tipagem no silver
            .csv(READ_PATH)
    ))
    # Sanity: se algum arquivo cair fora de ano=YYYY/ por algum motivo,
    # `ano` vira null e partitionBy("ano") explode no commit. Falha cedo.
    n_null_ano = df.filter(F.col("ano").isNull()).limit(1).count()
    if n_null_ano > 0:
        bad_sample = df.filter(F.col("ano").isNull()).select("_source_file").limit(3).collect()
        raise RuntimeError(
            f"Há registros sem `ano` derivado do path. Esperado /ano=YYYY/ no _source_file. "
            f"Exemplos: {[r['_source_file'] for r in bad_sample]}"
        )
    (df.write.format("delta").mode("overwrite")
        .option("overwriteSchema","true")
        .partitionBy("ano")
        .saveAsTable(BRONZE_TABLE))
    # priming Auto Loader checkpoint
    print("  primando checkpoint Auto Loader…")
    init = _sanitize_columns(_add_ano_from_path(
        spark.readStream.format("cloudFiles")
            .option("cloudFiles.format","csv")
            .option("cloudFiles.schemaLocation", SCHEMA_LOC)
            .option("cloudFiles.includeExistingFiles","false")
            .option("header","true").option("sep",";").option("encoding","latin1")
            .load(READ_PATH)
    ))
    (init.writeStream.format("delta")
        .option("checkpointLocation", CHECKPOINT_LOC)
        .option("mergeSchema","true")
        .partitionBy("ano")
        .trigger(availableNow=True)
        .toTable(BRONZE_TABLE).awaitTermination())
else:
    print(f"▸ MODO AUTO LOADER — table_exists=True rows={existing_rows:,}")
    print(f"  lendo: {READ_PATH}")
    stream = _sanitize_columns(_add_ano_from_path(
        spark.readStream.format("cloudFiles")
            .option("cloudFiles.format","csv")
            .option("cloudFiles.schemaLocation", SCHEMA_LOC)
            .option("cloudFiles.schemaEvolutionMode","addNewColumns")
            .option("header","true").option("sep",";").option("encoding","latin1")
            .load(READ_PATH)
    ))
    (stream.writeStream.format("delta")
        .option("checkpointLocation", CHECKPOINT_LOC)
        .option("mergeSchema","true")
        .partitionBy("ano")
        .trigger(availableNow=True)
        .toTable(BRONZE_TABLE).awaitTermination())

# COMMAND ----------

n = spark.read.table(BRONZE_TABLE).count()
print(f"✔ {BRONZE_TABLE}: {n:,} rows total")
spark.read.table(BRONZE_TABLE).groupBy("ano").count().orderBy("ano").show(30)

# COMMAND ----------

# MAGIC %md ## Iceberg via Delta UniForm (interop sem duplicação)
# MAGIC
# MAGIC Habilita Apache Iceberg como formato de leitura **na própria tabela
# MAGIC canônica** — Delta writer gera metadata Iceberg sidecar a cada commit.
# MAGIC Clientes Iceberg externos (Trino, Snowflake, Athena, pyiceberg) leem
# MAGIC `bronze.rais_vinculos` diretamente via UC Iceberg REST endpoint.
# MAGIC
# MAGIC Sem objeto duplicado no UC, sem view, sem tabela paralela. Storage
# MAGIC overhead = ~MB de metadata. Idempotente: re-aplicar não custa nada.
# MAGIC Free Edition serverless não permite Iceberg writer nativo (Maven
# MAGIC `org.apache.iceberg` ausente do classpath); UniForm é o caminho honesto.

# COMMAND ----------

print(f"▸ Habilitando UniForm Iceberg em {BRONZE_TABLE}…")
spark.sql(f"""
    ALTER TABLE {BRONZE_TABLE} SET TBLPROPERTIES (
        'delta.universalFormat.enabledFormats' = 'iceberg',
        'delta.enableIcebergCompatV2'          = 'true'
    )
""")

# Tags de discoverability — clientes podem filtrar UC por iceberg_uniform=true
for k, v in [
    ("iceberg_uniform",  "true"),
    ("iceberg_endpoint", "uc_rest"),
]:
    spark.sql(f"ALTER TABLE {BRONZE_TABLE} SET TAGS ('{k}' = '{v}')")

spark.sql(f"""
    COMMENT ON TABLE {BRONZE_TABLE} IS
    'Mirante · RAIS Vínculos Públicos — bronze Delta canônica, também '
    'exposta em Apache Iceberg via Delta UniForm (tag iceberg_uniform=true). '
    'Clientes Iceberg (Trino, Snowflake, Athena, pyiceberg) podem ler esta '
    'tabela via UC Iceberg REST endpoint — Delta writer gera metadata Iceberg '
    'sidecar a cada commit, apontando pros mesmos arquivos Parquet (zero '
    'overhead de storage). Free Edition serverless não permite Iceberg writer '
    'nativo; UniForm é o caminho honesto pra interop sem fingir paralelismo.'
""")

print(f"  ✓ UniForm Iceberg habilitado · sidecar metadata gerada a cada commit Delta")
print(f"  cliente Iceberg externo: leia {BRONZE_TABLE} via UC Iceberg REST")

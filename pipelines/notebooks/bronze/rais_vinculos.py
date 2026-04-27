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

dbutils.widgets.text("catalog",        "mirante_prd")
dbutils.widgets.text("zips_dir",       "/Volumes/mirante_prd/bronze/raw/mte/rais")
dbutils.widgets.text("txt_extracted",  "/Volumes/mirante_prd/bronze/raw/mte/rais_txt_extracted")
dbutils.widgets.text("force_reconvert","false")

CATALOG          = dbutils.widgets.get("catalog")
ZIPS_DIR         = dbutils.widgets.get("zips_dir")
TXT_EXTRACTED    = dbutils.widgets.get("txt_extracted")
FORCE_RECONVERT  = dbutils.widgets.get("force_reconvert").lower() in ("true","1","yes")

BRONZE_TABLE   = f"{CATALOG}.bronze.rais_vinculos"
CHECKPOINT_LOC = f"/Volumes/{CATALOG}/bronze/raw/_autoloader/rais_vinculos/_checkpoint"
SCHEMA_LOC     = f"/Volumes/{CATALOG}/bronze/raw/_autoloader/rais_vinculos/_schema"

print(f"zips_dir={ZIPS_DIR}  txt_extracted={TXT_EXTRACTED}  target={BRONZE_TABLE}")

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

extracted = 0; skipped = 0; redownloaded = 0; quarantined = 0
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
            z.extractall(path=target)
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
    Falha silenciosamente em arquivos com magic bytes inválidos (retorna [])."""
    try:
        with py7zr.SevenZipFile(zp, mode='r') as z:
            return list(z.getnames() or [])
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
    if ok:
        marker_ok.write_text("ok"); extracted += 1
        print(f"    ✓ ok")
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
    permanece clean). Imprime um sample dos renames pra auditoria."""
    renames = [(c, _sanitize_col(c)) for c in df.columns]
    changed = [(orig, new) for orig, new in renames if orig != new]
    if changed:
        print(f"  sanitizando {len(changed)} colunas; sample: "
              f"{', '.join(f'{a!r}→{b!r}' for a, b in changed[:5])}"
              + (f" (+{len(changed)-5})" if len(changed) > 5 else ""))
    return df.toDF(*[new for _, new in renames])

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

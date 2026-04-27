# Databricks notebook source
# MAGIC %md
# MAGIC # ingest · mte_rais
# MAGIC
# MAGIC Baixa os arquivos `.7z` da RAIS (Vínculos + Estabelecimentos) do servidor
# MAGIC FTP do PDET para `/Volumes/<catalog>/bronze/raw/mte/rais/`. Os `.7z` contêm
# MAGIC `.txt` delimitados por `;`, encoding latin-1.
# MAGIC
# MAGIC **Fonte oficial (verificada abr/2026):**
# MAGIC `ftp://ftp.mtps.gov.br/pdet/microdados/RAIS/<ano>/`
# MAGIC
# MAGIC Aliases DNS: `ftp.mtps.gov.br` == `ftp.trabalho.gov.br` (mesmo IP).
# MAGIC O host HTTPS antigo `pdet.mte.gov.br` agora redireciona pra landing
# MAGIC institucional sem links de download diretos. **Use FTP.**
# MAGIC
# MAGIC ## Naming conventions (varia por era)
# MAGIC
# MAGIC | Faixa de anos | Padrão                                | Granularidade |
# MAGIC |---------------|---------------------------------------|---------------|
# MAGIC | 1985–2018     | `<UF><AAAA>.7z`, `ESTB<AAAA>.7z`      | Per-UF        |
# MAGIC | 2019–2024     | `RAIS_VINC_PUB_<REGIÃO>.7z`, `RAIS_ESTAB_PUB.7z` | Per-região |
# MAGIC
# MAGIC O notebook lista o conteúdo do diretório do ano e baixa **tudo que for
# MAGIC `.7z`** — funciona em ambas as eras sem precisar conhecer o nome exato.
# MAGIC
# MAGIC ## Ref histórica
# MAGIC Esta vertical replica e estende Chalhoub (2023, monografia UFRJ MBA Eng.
# MAGIC Dados, não publicada) — vide `docs/vertical-rais-fair-lakehouse-spec.md`.

# COMMAND ----------

dbutils.widgets.text("years",      "1985-2025")
dbutils.widgets.text("volume_dir", "/Volumes/mirante_prd/bronze/raw/mte/rais")
dbutils.widgets.text("workers",    "2")

YEARS_EXPR = dbutils.widgets.get("years")
VOLUME_DIR = dbutils.widgets.get("volume_dir")
WORKERS    = int(dbutils.widgets.get("workers"))

print(f"years={YEARS_EXPR}  dest={VOLUME_DIR}  workers={WORKERS}")

# COMMAND ----------

import ftplib
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

FTP_HOST = "ftp.mtps.gov.br"        # alias de ftp.trabalho.gov.br
FTP_DIR  = "/pdet/microdados/RAIS"
FTP_TIMEOUT = 600
MAX_RETRIES = 3
RETRY_DELAY_S = 3


def parse_years(expr: str) -> list[int]:
    out = set()
    for part in (p.strip() for p in expr.split(",") if p.strip()):
        if "-" in part:
            a, b = part.split("-", 1)
            out.update(range(int(a), int(b) + 1))
        else:
            out.add(int(part))
    return sorted(out)


def list_year(year: int, retries: int = 3) -> list[str]:
    """Returns list of .7z filenames in /pdet/microdados/RAIS/<year>/.
    Empty list ONLY when FTP confirms 550 'file not found' on the year dir.
    Other 5xx (rate-limit, login refused) and network errors retry with backoff
    so transient PDET issues don't masquerade as 'year not published'."""
    last_err: Exception | None = None
    for attempt in range(1, retries + 1):
        try:
            ftp = ftplib.FTP(FTP_HOST, timeout=FTP_TIMEOUT)
            # PDET FTP entrega filenames com bytes não-UTF8 (0x97 = em-dash em
            # cp1252) — ex.: "Comunicado — Microdados RAIS 2024.htm" em /2023/
            # e /2024/. ftplib default 'utf-8' crasha o nlst() inteiro com
            # UnicodeDecodeError, fazendo o ano todo retornar []. latin-1
            # aceita TODOS os bytes 0x00-0xFF sem erro — filtramos .7z depois.
            ftp.encoding = "latin-1"
            ftp.login()
            ftp.cwd(f"{FTP_DIR}/{year}/")
            names = [n for n in ftp.nlst() if n.lower().endswith(".7z")]
            ftp.quit()
            return names
        except ftplib.error_perm as e:
            msg = str(e)
            # 550 = file/dir not found → genuinely missing year (e.g., 2025).
            # Other error_perm (530 login, 553 etc.) → retry, don't mask as empty.
            if msg.startswith("550"):
                return []
            last_err = e
            print(f"  ⚠ list_year({year}) attempt {attempt}/{retries} error_perm: {msg}")
        except Exception as e:
            last_err = e
            print(f"  ⚠ list_year({year}) attempt {attempt}/{retries} {type(e).__name__}: {e}")
        if attempt < retries:
            time.sleep(2 ** attempt)
    print(f"  ✗ list_year({year}) failed after {retries} attempts; last error: {last_err}")
    return []


def download_one(year: int, filename: str, dest_dir: Path) -> tuple[str, str]:
    """Returns (label, status) where status ∈ {'ok','cached','error'}.

    Resumes from `.part` if a previous attempt died mid-stream (uses FTP REST).
    Prints in-flight progress every 30s so multi-GB files don't look hung.
    """
    label = f"RAIS_{year}/{filename}"
    # Local filename includes year suffix to avoid collisions across years
    # (some files are name-identical across years, e.g. RAIS_VINC_PUB_SP.7z
    # exists in both /2022/ and /2023/).
    stem = filename.rsplit(".", 1)[0]
    dest = dest_dir / f"{stem}_{year}.7z"
    if dest.exists() and dest.stat().st_size > 0:
        return label, "cached"

    tmp = dest.with_suffix(dest.suffix + ".part")
    # Volumes Databricks (FUSE) NÃO suportam seek/append-then-write necessário
    # pro FTP REST resume — produz OSError [Errno 29] Illegal seek. Detectamos
    # e refazemos do zero se o resume falhar nesse modo.
    fresh_only = False  # vira True se um resume falhou por OSError neste run
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            ftp = ftplib.FTP(FTP_HOST, timeout=FTP_TIMEOUT)
            # latin-1: aceita filenames com bytes não-UTF8 do PDET (em-dash 0x97)
            ftp.encoding = "latin-1"
            ftp.login()
            ftp.cwd(f"{FTP_DIR}/{year}/")

            try:
                ftp.voidcmd("TYPE I")
                total = ftp.size(filename) or 0
            except Exception:
                total = 0

            # Se o filesystem rejeitou resume antes (OSError), forçamos fresh
            if fresh_only and tmp.exists():
                tmp.unlink(missing_ok=True)
            offset = tmp.stat().st_size if tmp.exists() else 0
            mode = "ab" if offset > 0 else "wb"
            if offset > 0:
                print(f"  ↻ {label}  resuming from {offset/1_048_576:.0f}MB"
                      + (f" / {total/1_048_576:.0f}MB" if total else ""))

            with tmp.open(mode) as f:
                state = {"written": offset, "last": time.monotonic()}

                def cb(chunk: bytes) -> None:
                    f.write(chunk)
                    state["written"] += len(chunk)
                    now = time.monotonic()
                    if now - state["last"] > 30:
                        mb = state["written"] / 1_048_576
                        if total:
                            pct = 100 * state["written"] / total
                            print(f"  ⋯ {label}  {mb:.0f}MB / {total/1_048_576:.0f}MB ({pct:.0f}%)")
                        else:
                            print(f"  ⋯ {label}  {mb:.0f}MB")
                        state["last"] = now

                try:
                    if offset > 0:
                        ftp.retrbinary(f"RETR {filename}", cb, rest=offset)
                    else:
                        ftp.retrbinary(f"RETR {filename}", cb)
                except ftplib.error_perm:
                    # Server refused REST or file moved — start fresh next attempt
                    if offset > 0:
                        f.close()
                        tmp.unlink(missing_ok=True)
                    raise
                except OSError as e:
                    # Filesystem rejeitou seek/append (típico de Databricks FUSE
                    # tentando resume em .part). Marca pra próxima tentativa
                    # ignorar o resume e baixar fresh.
                    if offset > 0 and ("Illegal seek" in str(e) or e.errno == 29):
                        print(f"  ⚠ {label} resume falhou em FUSE ({type(e).__name__}: {e}); "
                              f"refazendo fresh na próxima tentativa")
                        fresh_only = True
                        try: f.close()
                        except Exception: pass
                        tmp.unlink(missing_ok=True)
                    raise

            try:
                ftp.quit()
            except Exception:
                pass

            size = tmp.stat().st_size
            if size >= 1024 and (total == 0 or size >= total):
                tmp.replace(dest)
                return label, "ok"
            # Short or partial — leave .part so next attempt resumes
        except (*ftplib.all_errors, EOFError, OSError) as e:
            if attempt < MAX_RETRIES:
                time.sleep(RETRY_DELAY_S * attempt)
                continue
            print(f"  ✗ {label} — {type(e).__name__}: {str(e)[:120]}  (.part kept for next run)")
            return label, "error"
    return label, "error"


# COMMAND ----------

dest_dir = Path(VOLUME_DIR)
dest_dir.mkdir(parents=True, exist_ok=True)
years = parse_years(YEARS_EXPR)

# Phase 1: list all years to discover the actual files (sequential).
# PDET FTP rate-limits concurrent connections — listing is fast (~1s/year)
# so we serialize to keep results reliable. Parallelism stays in Phase 2.
print(f"Listando {len(years)} anos no FTP {FTP_HOST}{FTP_DIR}/…")
year_to_files: dict[int, list[str]] = {}
for y in years:
    year_to_files[y] = list_year(y)

total_targets = sum(len(v) for v in year_to_files.values())
print(f"\nTotal de .7z descobertos: {total_targets}")
for y in sorted(year_to_files):
    files = year_to_files[y]
    if files:
        print(f"  {y}: {len(files)} arquivos — ex.: {files[0]}")
    else:
        print(f"  {y}: (vazio ou indisponível)")

# Phase 2: download in parallel
print(f"\nBaixando {total_targets} arquivos com {WORKERS} workers…")
results = {"ok": 0, "cached": 0, "error": 0}
errors = []
with ThreadPoolExecutor(max_workers=WORKERS) as ex:
    futures = []
    for y, files in year_to_files.items():
        for fname in files:
            futures.append(ex.submit(download_one, y, fname, dest_dir))
    for i, fut in enumerate(as_completed(futures), 1):
        label, status = fut.result()
        results[status] += 1
        if status == "error":
            errors.append(label)
        if i % 10 == 0 or i == len(futures):
            print(f"  [{i:4d}/{len(futures)}] ok={results['ok']} cached={results['cached']} err={results['error']}")

print(f"\nResultado: {results}")
if errors:
    print(f"Errors em {len(errors)} arquivos (primeiros 10):")
    for e in errors[:10]:
        print(f"  {e}")

print(f"\n.7z no Volume agora: {len(sorted(dest_dir.glob('*.7z')))}")

# ─── Auditoria final por ano: detecta gaps SILENCIOSOS ──────────────────────
# (caso list_year tenha retornado [] após esgotar retries pra um ano que
# historicamente tem dados, o ingest seguia sem alerta visível no orchestrator)
print("\n=== AUDITORIA FINAL — .7z por ano no Volume ===")
year_re = __import__("re").compile(r"_(\d{4})\.7z$", __import__("re").I)
counts: dict[int, int] = {}
for f in dest_dir.iterdir():
    if f.is_file() and f.suffix.lower() == ".7z":
        m = year_re.search(f.name)
        if m:
            y = int(m.group(1))
            counts[y] = counts.get(y, 0) + 1

# Anos esperados: o que list_year reportou ter > 0 arquivos
expected_years = {y for y, files in year_to_files.items() if files}
parts = sorted(dest_dir.glob("*.part"))
print(f"  total .7z: {sum(counts.values())}  ·  total .part: {len(parts)}")

zero_data_years = sorted(expected_years - set(counts.keys()))
if zero_data_years:
    print(f"\n  ⚠⚠ ANOS COM 0 ARQUIVOS no Volume mas FTP listou >0: {zero_data_years}")
    print(f"     Causa provável: download falhou em todos os arquivos ou .part órfão")
    for y in zero_data_years:
        files = year_to_files.get(y, [])
        print(f"       {y}: esperado {len(files)} → {files[:3]}{'...' if len(files)>3 else ''}")

if parts:
    print(f"\n  ⚠ {len(parts)} .part órfãos (download incompleto, podem causar Illegal seek loop):")
    for p in parts[:10]:
        print(f"       {p.name}  ({p.stat().st_size/1_048_576:.0f} MB)")
    if len(parts) > 10:
        print(f"       ... +{len(parts) - 10}")

print("\n  contagem por ano:")
for y in sorted(counts.keys()):
    expected = len(year_to_files.get(y, []))
    flag = "  ✓" if expected and counts[y] >= expected else f"  ⚠ esperado {expected}"
    print(f"    {y}: {counts[y]} arquivos{flag if expected else ''}")
print("=== FIM AUDITORIA ===\n")

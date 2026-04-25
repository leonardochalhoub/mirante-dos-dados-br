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
dbutils.widgets.text("workers",    "4")

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


def list_year(year: int) -> list[str]:
    """Returns list of .7z filenames in /pdet/microdados/RAIS/<year>/.
    Empty list if year doesn't exist on FTP (some early years have gaps)."""
    try:
        ftp = ftplib.FTP(FTP_HOST, timeout=FTP_TIMEOUT)
        ftp.login()
        ftp.cwd(f"{FTP_DIR}/{year}/")
        names = [n for n in ftp.nlst() if n.lower().endswith(".7z")]
        ftp.quit()
        return names
    except ftplib.error_perm:
        # Year directory doesn't exist yet (e.g., 2025 not published)
        return []
    except Exception as e:
        print(f"  ⚠ list_year({year}) failed: {type(e).__name__}: {e}")
        return []


def download_one(year: int, filename: str, dest_dir: Path) -> tuple[str, str]:
    """Returns (label, status) where status ∈ {'ok','cached','error'}."""
    label = f"RAIS_{year}/{filename}"
    # Local filename includes year suffix to avoid collisions across years
    # (some files are name-identical across years, e.g. RAIS_VINC_PUB_SP.7z
    # exists in both /2022/ and /2023/).
    stem = filename.rsplit(".", 1)[0]
    dest = dest_dir / f"{stem}_{year}.7z"
    if dest.exists() and dest.stat().st_size > 0:
        return label, "cached"

    tmp = dest.with_suffix(dest.suffix + ".part")
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            ftp = ftplib.FTP(FTP_HOST, timeout=FTP_TIMEOUT)
            ftp.login()
            ftp.cwd(f"{FTP_DIR}/{year}/")
            with tmp.open("wb") as f:
                ftp.retrbinary(f"RETR {filename}", f.write)
            ftp.quit()
            if tmp.stat().st_size >= 1024:
                tmp.replace(dest)
                return label, "ok"
            tmp.unlink(missing_ok=True)
        except (ftplib.all_errors, EOFError, OSError) as e:
            if attempt < MAX_RETRIES:
                time.sleep(RETRY_DELAY_S * attempt)
                continue
            tmp.unlink(missing_ok=True)
            print(f"  ✗ {label} — {type(e).__name__}: {str(e)[:120]}")
            return label, "error"
    tmp.unlink(missing_ok=True)
    return label, "error"


# COMMAND ----------

dest_dir = Path(VOLUME_DIR)
dest_dir.mkdir(parents=True, exist_ok=True)
years = parse_years(YEARS_EXPR)

# Phase 1: list all years to discover the actual files (parallel)
print(f"Listando {len(years)} anos no FTP {FTP_HOST}{FTP_DIR}/…")
year_to_files: dict[int, list[str]] = {}
with ThreadPoolExecutor(max_workers=WORKERS) as ex:
    futures = {ex.submit(list_year, y): y for y in years}
    for fut in as_completed(futures):
        y = futures[fut]
        files = fut.result()
        year_to_files[y] = files

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

# Databricks notebook source
# MAGIC %md
# MAGIC # ingest · mte_rais
# MAGIC
# MAGIC Baixa os arquivos `.7z` da RAIS (Vínculos Públicos) do Ministério do Trabalho /
# MAGIC PDET para `/Volumes/<catalog>/bronze/raw/mte/rais/`. Os `.7z` contêm `.txt`
# MAGIC delimitados por `;`, encoding latin-1.
# MAGIC
# MAGIC Fonte original: ftp://ftp.mtps.gov.br/pdet/microdados/RAIS/
# MAGIC (caminho exato pode variar por ano — verificar antes de 1ª execução).
# MAGIC
# MAGIC Esta vertical replica e estende o trabalho de Chalhoub (2023, monografia
# MAGIC UFRJ MBA Eng. Dados, não publicada) — vide
# MAGIC `docs/vertical-rais-fair-lakehouse-spec.md`.
# MAGIC
# MAGIC | param | default |
# MAGIC | --- | --- |
# MAGIC | `years`      | `2020-2021` |
# MAGIC | `volume_dir` | `/Volumes/mirante_prd/bronze/raw/mte/rais` |
# MAGIC | `workers`    | `2` |

# COMMAND ----------

dbutils.widgets.text("years",      "2020-2021")
dbutils.widgets.text("volume_dir", "/Volumes/mirante_prd/bronze/raw/mte/rais")
dbutils.widgets.text("workers",    "2")

YEARS_EXPR = dbutils.widgets.get("years")
VOLUME_DIR = dbutils.widgets.get("volume_dir")
WORKERS    = int(dbutils.widgets.get("workers"))

print(f"years={YEARS_EXPR}  dest={VOLUME_DIR}  workers={WORKERS}")

# COMMAND ----------

import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
import requests

# RAIS PDET — URL pattern por ano. Ministério do Trabalho mudou a estrutura
# algumas vezes; mantemos uma lista de templates a tentar.
URL_TEMPLATES = [
    "ftp://ftp.mtps.gov.br/pdet/microdados/RAIS/{year}/RAIS_VINC_PUB_{uf}.7z",
    "https://pdet.mte.gov.br/images/Microdados/RAIS/{year}/RAIS_VINC_PUB_{uf}.7z",
]
HEADERS = {"User-Agent": "mirante-dos-dados/1.0"}

# Por padrão baixamos apenas o arquivo "BR-completo" (RAIS_VINC_PUB_BR.7z) —
# alguns anos publicam por região/UF. Ajustar conforme estrutura encontrada.
SCOPES = ["BR"]   # ['NORDESTE','SUDESTE',...] em anos antigos


def parse_years(expr: str) -> list[int]:
    out = set()
    for part in (p.strip() for p in expr.split(",") if p.strip()):
        if "-" in part:
            a, b = part.split("-", 1)
            out.update(range(int(a), int(b) + 1))
        else:
            out.add(int(part))
    return sorted(out)


def fetch(year: int, uf: str, dest_dir: Path, retries: int = 3) -> tuple[str, str]:
    label = f"RAIS_{year}_{uf}"
    dest = dest_dir / f"RAIS_VINC_PUB_{uf}_{year}.7z"
    if dest.exists() and dest.stat().st_size > 0:
        return label, "cached"
    dest.parent.mkdir(parents=True, exist_ok=True)
    tmp = dest.with_suffix(dest.suffix + ".part")
    last_err = None
    for url_tmpl in URL_TEMPLATES:
        url = url_tmpl.format(year=year, uf=uf)
        for attempt in range(1, retries + 1):
            try:
                with requests.get(url, headers=HEADERS, stream=True, timeout=600) as r:
                    if r.status_code != 200:
                        last_err = f"HTTP {r.status_code}"
                        break  # try next URL template
                    written = 0
                    with tmp.open("wb") as f:
                        for chunk in r.iter_content(chunk_size=1 << 22):
                            if chunk:
                                f.write(chunk); written += len(chunk)
                    if written < 1024:
                        tmp.unlink(missing_ok=True); last_err = "too small"; break
                    tmp.replace(dest)
                    return label, "ok"
            except Exception as e:
                last_err = f"{type(e).__name__}: {e}"
                if attempt < retries:
                    time.sleep(2.0)
    if tmp.exists():
        tmp.unlink()
    print(f"  ✗ {label} — last err: {last_err}")
    return label, "missing"

# COMMAND ----------

dest_dir = Path(VOLUME_DIR)
dest_dir.mkdir(parents=True, exist_ok=True)
years = parse_years(YEARS_EXPR)
print(f"Tentando {len(years)} anos × {len(SCOPES)} escopos = {len(years)*len(SCOPES)} arquivos")

results = {"ok": 0, "cached": 0, "missing": 0}
with ThreadPoolExecutor(max_workers=WORKERS) as ex:
    futures = [ex.submit(fetch, y, uf, dest_dir) for y in years for uf in SCOPES]
    for fut in as_completed(futures):
        _, status = fut.result()
        results[status] += 1
print(f"Resultado: {results}")
print(f".7z no Volume agora: {len(sorted(dest_dir.glob('*.7z')))}")

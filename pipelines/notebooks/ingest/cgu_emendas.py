# Databricks notebook source
# MAGIC %md
# MAGIC # ingest · cgu_emendas
# MAGIC
# MAGIC Baixa o ZIP **consolidado** de Emendas Parlamentares do Portal da Transparência (CGU).
# MAGIC
# MAGIC ⚠️ CGU publica **um único** `EmendasParlamentares.zip` cobrindo todos os anos (2014→atual).
# MAGIC O endpoint `/download-de-dados/emendas-parlamentares/{year}` retorna sempre o mesmo
# MAGIC arquivo (302 redirect pra `dadosabertos-download.cgu.gov.br`); o segmento year é ignorado.
# MAGIC
# MAGIC Estratégia: download timestamped (`emendas_parlamentares__{ts}.zip`) pra Auto Loader
# MAGIC detectar como arquivo novo a cada refresh.
# MAGIC
# MAGIC Conteúdo do ZIP (3 CSVs):
# MAGIC - `EmendasParlamentares.csv`  ← principal, 1 row por emenda × ação × localidade
# MAGIC - `EmendasParlamentares_Convenios.csv`     (auxiliar)
# MAGIC - `EmendasParlamentares_PorFavorecido.csv` (auxiliar)
# MAGIC
# MAGIC Bronze só consome o principal (filtra por filename).

# COMMAND ----------

dbutils.widgets.text("volume_dir", "/Volumes/mirante_prd/bronze/raw/cgu/emendas")

VOLUME_DIR = dbutils.widgets.get("volume_dir")
print(f"dest={VOLUME_DIR}")

# COMMAND ----------

import time
from datetime import datetime, timezone
from pathlib import Path

import requests

ZIP_MAGIC       = b"PK\x03\x04"
ZIP_MAGIC_EMPTY = b"PK\x05\x06"
HEADERS         = {"User-Agent": "mirante-dos-dados/1.0", "Accept": "*/*"}

# Year segment is required by the route but ignored by CGU — same file regardless.
URL = "https://portaldatransparencia.gov.br/download-de-dados/emendas-parlamentares/2024"


def is_valid_zip(p: Path) -> bool:
    try:
        with p.open("rb") as f:
            return f.read(4) in (ZIP_MAGIC, ZIP_MAGIC_EMPTY)
    except OSError:
        return False


# COMMAND ----------

dest_dir = Path(VOLUME_DIR)
dest_dir.mkdir(parents=True, exist_ok=True)

ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
dest = dest_dir / f"emendas_parlamentares__{ts}.zip"
tmp  = dest.with_suffix(dest.suffix + ".part")

print(f"GET {URL} → {dest.name}")

retries = 3
last_err = None
for attempt in range(1, retries + 1):
    try:
        with requests.get(URL, headers=HEADERS, stream=True, timeout=300, allow_redirects=True) as r:
            r.raise_for_status()
            written = 0
            with tmp.open("wb") as f:
                for chunk in r.iter_content(chunk_size=1 << 20):
                    if chunk:
                        f.write(chunk)
                        written += len(chunk)
            if written < 4 or not is_valid_zip(tmp):
                tmp.unlink(missing_ok=True)
                raise ValueError(f"Downloaded file is not a valid ZIP ({written} bytes)")
            tmp.replace(dest)
            print(f"✔ {dest.name}  ({written:,} bytes)")
            break
    except Exception as e:
        last_err = e
        if attempt < retries:
            print(f"  attempt {attempt}/{retries} failed: {e}; retrying…")
            time.sleep(2.0)
        else:
            tmp.unlink(missing_ok=True)
            raise RuntimeError(f"Falha após {retries} tentativas: {last_err}")

print(f"ZIPs no Volume agora: {len(sorted(dest_dir.glob('*.zip')))}")

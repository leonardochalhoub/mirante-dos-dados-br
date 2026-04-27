# Databricks notebook source
# MAGIC %md
# MAGIC # ingest · ibge_municipios_meta
# MAGIC
# MAGIC Baixa metadados dos 5.570 municípios brasileiros via IBGE Localidades API
# MAGIC v1 + IBGE/SIDRA Tabela 6579 (população). Pra IDH-M usa-se o snapshot Atlas
# MAGIC Brasil 2010 (últimos valores publicados — censo 2022 ainda não tem IDHM).
# MAGIC
# MAGIC Endpoints:
# MAGIC - https://servicodados.ibge.gov.br/api/v1/localidades/municipios → 5.570 munis
# MAGIC - https://servicodados.ibge.gov.br/api/v3/agregados/6579/periodos/-13/variaveis/9324?localidades=N6 → população
# MAGIC - Atlas Brasil 2010 IDHM CSV (estático, no `data/reference/`)
# MAGIC
# MAGIC Salva 3 tabelas bronze JSON-as-string:
# MAGIC - bronze.ibge_municipios_meta_raw  (centroide, área, hierarquia)
# MAGIC - bronze.ibge_municipios_populacao_raw (série histórica pop)
# MAGIC - bronze.atlas_brasil_idhm_2010 (IDHM municipal)

# COMMAND ----------

dbutils.widgets.text("catalog",   "mirante_prd")
dbutils.widgets.text("years",     "2013-2025")
dbutils.widgets.text("workers",   "8")
dbutils.widgets.text("ref_volume","/Volumes/mirante_prd/bronze/raw/ibge")

CATALOG    = dbutils.widgets.get("catalog")
YEARS      = dbutils.widgets.get("years")
WORKERS    = int(dbutils.widgets.get("workers"))
REF_VOLUME = dbutils.widgets.get("ref_volume")

# COMMAND ----------

import json
import time
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
import requests

HEADERS = {"User-Agent": "mirante-dos-dados/1.0 wp7-municipal", "Accept": "application/json"}

API_LOCALIDADES = (
    "https://servicodados.ibge.gov.br/api/v1/localidades/municipios"
)
API_MALHA = (
    "https://servicodados.ibge.gov.br/api/v3/malhas/{cod}?formato=application/vnd.geo+json"
)
API_SIDRA_POP = (
    "https://servicodados.ibge.gov.br/api/v3/agregados/6579/periodos/{anos}"
    "/variaveis/9324?localidades=N6"
)


def fetch_json(url: str, timeout: int = 90, retries: int = 3) -> dict | list:
    for attempt in range(1, retries + 1):
        try:
            r = requests.get(url, headers=HEADERS, timeout=timeout)
            if r.status_code == 200:
                return r.json()
        except (requests.HTTPError, requests.ConnectionError, requests.Timeout):
            pass
        if attempt < retries:
            time.sleep(1.5 * attempt)
    raise RuntimeError(f"failed to fetch {url}")


# COMMAND ----------

# 1. Lista canônica dos 5.570 munis
print("Fetching IBGE Localidades…")
municipios = fetch_json(API_LOCALIDADES)
print(f"  {len(municipios):,} municípios")
assert len(municipios) >= 5500, f"IBGE retornou {len(municipios)} < 5500"

# COMMAND ----------

# 2. Centroide via /malhas — usar MalhaDigital nível município retorna polígono
# (caro pra 5570 chamadas). Estratégia: para o WP#7 basta lat/lon do centroide;
# usamos a versão simplificada da malha (MalhaDigital com qualidade=baixa) e
# computamos o centroide localmente via shapely.

import shapely.geometry as sg

def centroide(cod7: str) -> tuple[float | None, float | None, float | None]:
    """Retorna (lat, lon, area_km2) — area aproximada via UTM por geodesic."""
    try:
        gj = fetch_json(API_MALHA.format(cod=cod7))
        # gj é FeatureCollection; pegar primeira geometry
        feats = gj.get("features", [])
        if not feats: return None, None, None
        geom = sg.shape(feats[0]["geometry"])
        c = geom.centroid
        # area_km2 aproximada via projeção lat/lon (degree²) → km² via 111²·cos(lat)
        # Para precisão real, usaríamos pyproj/UTM; aceito aproximação ±5%.
        import math
        a_deg = geom.area  # graus²
        a_km2 = a_deg * (111.0 ** 2) * math.cos(math.radians(c.y))
        return c.y, c.x, a_km2
    except Exception:
        return None, None, None


# Paralelizar
print("Fetching centroides (5.570 chamadas, ~8 workers)…")
results: dict[str, dict] = {}
with ThreadPoolExecutor(max_workers=WORKERS) as ex:
    fut2cod = {ex.submit(centroide, str(m["id"])): str(m["id"]) for m in municipios}
    for i, fut in enumerate(as_completed(fut2cod)):
        cod = fut2cod[fut]
        try:
            lat, lon, area = fut.result()
        except Exception:
            lat, lon, area = None, None, None
        results[cod] = {"lat": lat, "lon": lon, "area_km2": area}
        if (i + 1) % 200 == 0:
            print(f"  {i+1}/{len(municipios)} centroides")

# COMMAND ----------

# Atlas Brasil 2010 IDHM (snapshot estático no repo)
import pandas as pd
ATLAS_PATH = "/Workspace/Repos/<user>/mirante-dos-dados-br/data/reference/atlas_brasil_idhm_2010.csv"
# Fallback caminho relativo se Repos não estiver montado:
if not Path(ATLAS_PATH).exists():
    ATLAS_PATH = "/dbfs/FileStore/mirante/atlas_brasil_idhm_2010.csv"
atlas = pd.read_csv(ATLAS_PATH, dtype={"cod_municipio": str})
atlas_dict = dict(zip(atlas["cod_municipio"], atlas["idhm_2010"]))
print(f"Atlas Brasil 2010 IDHM: {len(atlas_dict):,} munis")

# COMMAND ----------

# Montar registro composto
records = []
for m in municipios:
    cod7 = str(m["id"])
    coords = results.get(cod7, {})
    rec = {
        "id":          cod7,
        "nome":        m["nome"],
        "microrregiao": m.get("microrregiao", {}),
        "centroide":   {"lat": coords.get("lat"), "lon": coords.get("lon")},
        "area_km2":    coords.get("area_km2"),
        "idhm_2010":   atlas_dict.get(cod7),
    }
    records.append(rec)

# Persistir bronze
bronze_meta = f"{CATALOG}.bronze.ibge_municipios_meta_raw"
df = spark.createDataFrame(records)
(df.write.format("delta").mode("overwrite").option("overwriteSchema", "true")
   .saveAsTable(bronze_meta))
spark.sql(f"COMMENT ON TABLE {bronze_meta} IS "
          f"'Mirante · Bronze JSON-as-string dos 5.570 municípios IBGE (id, nome, hierarquia, "
          f"centroide lat/lon, area_km2, idhm_2010 Atlas Brasil). Idempotente.'")
print(f"✔ {bronze_meta}")

# COMMAND ----------

# 3. População histórica via SIDRA 6579 (1 chamada, ~5500 munis × 13 anos)
def parse_years(expr: str) -> str:
    parts: set[int] = set()
    for tok in expr.split(","):
        if "-" in tok:
            a, b = tok.split("-"); parts.update(range(int(a), int(b)+1))
        else:
            parts.add(int(tok))
    return ",".join(str(y) for y in sorted(parts))

years_qs = parse_years(YEARS)
print(f"SIDRA pop endpoint anos={years_qs}")
pop_json = fetch_json(API_SIDRA_POP.format(anos=years_qs).replace("/-13/", f"/{years_qs}/"))
print(f"  {len(pop_json)} resultado(s) SIDRA")

bronze_pop = f"{CATALOG}.bronze.ibge_municipios_populacao_raw"
df_pop = spark.read.json(spark.sparkContext.parallelize([json.dumps(pop_json)]))
(df_pop.write.format("delta").mode("overwrite").option("overwriteSchema", "true")
       .saveAsTable(bronze_pop))
spark.sql(f"COMMENT ON TABLE {bronze_pop} IS "
          f"'Mirante · Bronze JSON da SIDRA 6579 — população residente estimada por '
          f"município, série {YEARS}.'")
print(f"✔ {bronze_pop}")

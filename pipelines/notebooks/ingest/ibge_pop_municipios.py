# Databricks notebook source
# MAGIC %md
# MAGIC # ingest · ibge_pop_municipios
# MAGIC
# MAGIC Estimativas populacionais municipais — IBGE/SIDRA v3 agregados, tabela 6579,
# MAGIC variável 9324, localidade N6 (município).
# MAGIC
# MAGIC **API endpoint:**
# MAGIC `https://servicodados.ibge.gov.br/api/v3/agregados/6579/periodos/<years>/variaveis/9324?localidades=N6`
# MAGIC
# MAGIC O retorno é JSON com estrutura `[{resultados:[{series:[{localidade,serie}]}]}]` —
# MAGIC mesma forma do `bronze.ibge_populacao_raw` (UF, N3). Compatível com o silver
# MAGIC `populacao_municipio_ano.py` existente.
# MAGIC
# MAGIC Cobertura: 2013–2024 anual (estimativas oficiais IBGE pós-Censo 2010).

# COMMAND ----------

dbutils.widgets.text("years",      "2013-2024")
dbutils.widgets.text("volume_dir", "/Volumes/mirante_prd/bronze/raw/ibge/pop_municipios")
dbutils.widgets.text("catalog",    "mirante_prd")

YEARS_EXPR = dbutils.widgets.get("years")
VOLUME_DIR = dbutils.widgets.get("volume_dir")
CATALOG    = dbutils.widgets.get("catalog")

print(f"years={YEARS_EXPR}  dest={VOLUME_DIR}  catalog={CATALOG}")

# COMMAND ----------

import gzip, json, time, urllib.request, urllib.error
from pathlib import Path

USER_AGENT = "Mirante-dos-Dados/ingest-pop-municipios"
TIMEOUT_S = 300


def fetch_json_gz(url: str) -> tuple[bytes, str]:
    """GET URL, retorna (raw_decompressed, content_encoding).
    SIDRA v3 retorna gzip a partir de respostas grandes (>~50KB) sem honrar
    Accept-Encoding: identity. urllib não decodifica auto, então fazemos manualmente."""
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=TIMEOUT_S) as resp:
        ce = resp.headers.get("Content-Encoding", "")
        raw = resp.read()
    if ce == "gzip":
        raw = gzip.decompress(raw)
    return raw, ce


def url_for_year(year: int) -> tuple[str, str]:
    """Retorna (url, source_label) pra cada ano. Cobertura SIDRA municipal:
      2013-2021, 2024: tabela 6579 var 9324 (Estimativas anuais)
      2022:            tabela 4709 var 93   (Censo 2022, contagem real)
      2023:            (gap — sem fonte direta; silver interpola)
    """
    if year == 2022:
        return (f"https://servicodados.ibge.gov.br/api/v3/agregados/4709/periodos/{year}"
                f"/variaveis/93?localidades=N6"), "censo_2022_t4709"
    return (f"https://servicodados.ibge.gov.br/api/v3/agregados/6579/periodos/{year}"
            f"/variaveis/9324?localidades=N6"), "estimativa_t6579"


def parse_years_qs(expr: str) -> str:
    """Converte '2013-2024' em '2013,2014,...,2024' (formato SIDRA v3)."""
    out: set[int] = set()
    for part in (p.strip() for p in expr.split(",") if p.strip()):
        if "-" in part:
            a, b = part.split("-", 1)
            out.update(range(int(a), int(b) + 1))
        else:
            out.add(int(part))
    return ",".join(str(y) for y in sorted(out))


def parse_years_list(expr: str) -> list[int]:
    out: set[int] = set()
    for part in (p.strip() for p in expr.split(",") if p.strip()):
        if "-" in part:
            a, b = part.split("-", 1)
            out.update(range(int(a), int(b) + 1))
        else:
            out.add(int(part))
    return sorted(out)


years_list = parse_years_list(YEARS_EXPR)
print(f"baixando {len(years_list)} anos: {years_list[0]}..{years_list[-1]}")

# SIDRA v3 retorna 500 pra ranges e listas com vírgula em /periodos/. Apenas
# single year funciona. Estratégia: 1 chamada por ano, salvar JSON por ano,
# Spark consolida na bronze depois (ele já agrega múltiplos arquivos JSON).

dest_dir = Path(VOLUME_DIR)
dest_dir.mkdir(parents=True, exist_ok=True)

ok = 0; cached = 0; errors: list[str] = []; skipped_gap: list[int] = []

# 2023: sem dado SIDRA público (Censo 2022 deslocou estimativas). Pulamos no
# ingest; silver vai interpolar entre Censo 2022 e Estimativa 2024.
GAP_YEARS = {2023}

for y in years_list:
    if y in GAP_YEARS:
        skipped_gap.append(y)
        continue
    out_path = dest_dir / f"pop_municipios_{y}.json"
    if out_path.exists() and out_path.stat().st_size > 100_000:
        cached += 1
        continue
    url, source = url_for_year(y)
    last_err = None
    for attempt in range(1, 5):
        try:
            raw, ce = fetch_json_gz(url)
            data = json.loads(raw.decode("utf-8"))
            n_series = sum(len(r.get("series", [])) for r in data[0].get("resultados", [])) if data else 0
            if n_series == 0:
                last_err = f"resposta vazia (ce={ce!r}, {len(raw)} bytes)"
                if attempt < 4:
                    print(f"  ⚠ {y} tentativa {attempt}: 0 séries — {last_err}")
                    time.sleep(2 * attempt)
                    continue
                else:
                    break
            # Marca origem no payload pra silver saber qual schema (Censo vs Estimativa)
            envelope = {"_year": y, "_source": source, "_data": data}
            out_path.write_text(json.dumps(envelope, ensure_ascii=False), encoding="utf-8")
            print(f"  ✓ {y}: {n_series} munis  {out_path.stat().st_size:,} bytes  (source={source})")
            ok += 1
            break
        except Exception as e:
            last_err = e
            if attempt < 4:
                print(f"  ⚠ {y} tentativa {attempt}: {type(e).__name__}: {str(e)[:80]}")
                time.sleep(3 * attempt)
    else:
        errors.append(f"{y}: {last_err}")
        print(f"  ✗ {y}: ABANDONADO após 4 tentativas: {last_err}")
    time.sleep(0.6)  # cortesia c/ rate limit

if skipped_gap:
    print(f"\n  ⊘ {len(skipped_gap)} ano(s) sem fonte SIDRA direta: {skipped_gap}")
    print(f"     Silver vai interpolar usando vizinhos (linear).")

print(f"\nResumo: ok={ok}  cached={cached}  errors={len(errors)}")
if errors:
    for e in errors: print(f"  - {e}")

# COMMAND ----------

# MAGIC %md ## Auto Loader → bronze.ibge_municipios_populacao_raw

# COMMAND ----------

from pyspark.sql import functions as F

# Nome alinhado com silver/populacao_municipio_ano.py
BRONZE_TABLE   = f"{CATALOG}.bronze.ibge_municipios_populacao_raw"
CHECKPOINT_LOC = f"/Volumes/{CATALOG}/bronze/raw/_autoloader/ibge_pop_municipios/_checkpoint"
SCHEMA_LOC     = f"/Volumes/{CATALOG}/bronze/raw/_autoloader/ibge_pop_municipios/_schema"

# Como o JSON SIDRA v3 é um ARRAY no top-level com 1 elemento, usamos batch
# overwrite (não streaming) — é estado natural pra esse tipo de fetch.
#
# TODO[bronze STRING-ONLY]: spark.read.json() infere tipo, criando STRUCT
# aninhado pro campo `serie` (cujas chaves são anos numéricos). Isso obriga
# o silver a fazer round-trip to_json/from_json pra converter STRUCT→MAP.
# Standard da plataforma manda bronze ser string-only (ler como
# `binaryFile` ou `text` e guardar o payload bruto numa coluna). Refatorar
# pra: spark.read.format("text").load(VOLUME_DIR) e silver chama
# from_json(content, schema) com `serie` declarado MapType<StringType>.
df = (
    spark.read
        .option("multiLine", "true")
        .json(VOLUME_DIR)
        .withColumn("_source_file", F.col("_metadata.file_path"))
        .withColumn("_ingest_ts",   F.current_timestamp())
)
print(f"linhas no DataFrame: {df.count()}")

(df.write.format("delta").mode("overwrite")
    .option("overwriteSchema", "true")
    .saveAsTable(BRONZE_TABLE))

n = spark.read.table(BRONZE_TABLE).count()
print(f"✔ {BRONZE_TABLE}: {n} documentos")

# COMMAND ----------

spark.sql(f"""
COMMENT ON TABLE {BRONZE_TABLE} IS
'IBGE Estimativas Populacionais Municipais — JSON bruto da API v3 agregados/6579,
variável 9324 (população residente estimada), localidade N6 (município). Cobertura
2013-2024 anual. Estrutura array com resultados[].series[].(localidade, serie). Silver
populacao_municipio_ano.py explode em (cod_municipio, ano, populacao).
Fonte: https://sidra.ibge.gov.br/tabela/6579'
""")

for tag, val in [
    ("layer", "bronze"), ("domain", "demografia"), ("source", "ibge_sidra"),
    ("source_table", "6579"), ("source_level", "N6"), ("pii", "false"),
    ("grain", "json_array_with_series"),
]:
    try: spark.sql(f"ALTER TABLE {BRONZE_TABLE} SET TAGS ('{tag}' = '{val}')")
    except Exception as e: print(f"  ⚠ tag {tag}: {e}")

print("✓ metadata UC aplicada")

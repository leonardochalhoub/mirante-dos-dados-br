#!/usr/bin/env python3
"""Build RAIS bronze in Apache Hudi (CoW) locally.

Por que LOCAL? Databricks Free Edition é serverless-only e não aceita o JAR
Maven `org.apache.hudi:hudi-spark3.5-bundle_2.12` no classpath. Então rodamos
o write Hudi numa máquina onde podemos controlar `spark.jars.packages` —
geralmente o laptop do dev — e depois sobe os arquivos pro Volume Databricks
com `databricks fs cp -r` (script `upload_rais_hudi_to_volume.sh`).

Pipeline:
    1. Lê CSVs RAIS (semicolon-separated, latin-1) de --input-dir
    2. Aplica EXATAMENTE a mesma sanitização do bronze Delta (NFKD strip
       acentos, snake_case, STRING-ONLY)
    3. Deriva `ano` a partir do path Hive-style `ano=YYYY/`
    4. Escreve Hudi Copy-on-Write particionado por `ano`

Pré-requisito local:
    pip install pyspark==3.5.* findspark

Uso típico:
    # 1. baixa amostra do Volume (ex.: 1 ano)
    databricks fs cp -r \\
      dbfs:/Volumes/mirante_prd/bronze/raw/mte/rais_txt_extracted/ano=2023/ \\
      ./local_rais_txt/ano=2023/

    # 2. roda este script
    python articles/scripts/build_rais_hudi_local.py \\
      --input-dir  ./local_rais_txt \\
      --output-dir ./local_rais_hudi \\
      --years 2023

    # 3. sobe pro Volume
    bash articles/scripts/upload_rais_hudi_to_volume.sh ./local_rais_hudi
"""

from __future__ import annotations

import argparse
import re
import shutil
import sys
import time
import unicodedata
from pathlib import Path


HUDI_PACKAGE = "org.apache.hudi:hudi-spark3.5-bundle_2.12:0.15.0"


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--input-dir",  required=True, type=Path,
                   help="Diretório local com `ano=YYYY/*.txt` (Hive-style, mesmo "
                        "layout do Volume rais_txt_extracted).")
    p.add_argument("--output-dir", required=True, type=Path,
                   help="Diretório local de saída do Hudi (será escrito em "
                        "<output-dir>/rais_vinculos_hudi/).")
    p.add_argument("--years", default=None,
                   help="Lista de anos a processar (ex.: '2023' ou '2021,2022,2023'). "
                        "Se omitido, processa todas as partições ano= encontradas.")
    p.add_argument("--clean", action="store_true",
                   help="Apaga <output-dir>/rais_vinculos_hudi/ antes de escrever. "
                        "Mutuamente exclusivo com --append.")
    p.add_argument("--append", action="store_true",
                   help="Append mode: adiciona partições novas ao Hudi existente "
                        "(usa operation=insert em vez de bulk_insert). Necessário "
                        "quando rodando ano-a-ano em loop (run_rais_hudi_all_years.sh).")
    p.add_argument("--master", default="local[*]",
                   help="Spark master (default: local[*]).")
    p.add_argument("--driver-memory", default="6g",
                   help="spark.driver.memory (default: 6g — caber em laptops 16 GB).")
    return p.parse_args()


def setup_spark(master: str, driver_memory: str):
    from pyspark.sql import SparkSession

    builder = (SparkSession.builder
        .appName("mirante-rais-hudi-local")
        .master(master)
        .config("spark.jars.packages", HUDI_PACKAGE)
        .config("spark.sql.extensions", "org.apache.spark.sql.hudi.HoodieSparkSessionExtension")
        .config("spark.serializer", "org.apache.spark.serializer.KryoSerializer")
        .config("spark.kryo.registrator", "org.apache.spark.HoodieSparkKryoRegistrar")
        .config("spark.driver.memory", driver_memory)
        .config("spark.sql.shuffle.partitions", "32")
    )
    spark = builder.getOrCreate()
    spark.sparkContext.setLogLevel("WARN")
    return spark


def sanitize_col(name: str) -> str:
    """Idêntico ao bronze Delta canônico (rais_vinculos.py): NFKD strip
    acentos + snake_case ASCII + lower."""
    if not name:
        return "col"
    leading = name.startswith("_")
    nfkd = unicodedata.normalize("NFKD", name)
    no_accents = "".join(c for c in nfkd if not unicodedata.combining(c))
    s = re.sub(r"[^a-zA-Z0-9_]+", "_", no_accents)
    s = re.sub(r"_+", "_", s).strip("_").lower() or "col"
    return ("_" + s) if leading else s


def main() -> int:
    args = parse_args()
    in_dir  = args.input_dir.resolve()
    out_dir = args.output_dir.resolve() / "rais_vinculos_hudi"

    if not in_dir.exists():
        print(f"✗ input-dir não existe: {in_dir}", file=sys.stderr)
        return 1

    year_dirs = [d for d in in_dir.iterdir() if d.is_dir() and d.name.startswith("ano=")]
    if not year_dirs:
        print(f"✗ nenhuma partição ano= encontrada em {in_dir}", file=sys.stderr)
        return 1

    if args.years:
        wanted = {int(y.strip()) for y in args.years.split(",")}
        year_dirs = [d for d in year_dirs if int(d.name.split("=")[1]) in wanted]
        if not year_dirs:
            print(f"✗ filtro --years {args.years} não bateu com nenhuma partição", file=sys.stderr)
            return 1

    n_txt_files = sum(1 for d in year_dirs for f in d.glob("*.txt"))
    sum_txt_mb  = sum(f.stat().st_size for d in year_dirs for f in d.glob("*.txt")) / 1_048_576
    print(f"input        : {in_dir}")
    print(f"output       : {out_dir}")
    print(f"partições    : {[d.name for d in year_dirs]}")
    print(f"arquivos .txt: {n_txt_files}  ·  total: {sum_txt_mb:,.0f} MB")
    print(f"hudi package : {HUDI_PACKAGE}")

    if args.clean and out_dir.exists():
        print(f"--clean → removendo {out_dir}…")
        shutil.rmtree(out_dir)

    print("\n▸ inicializando Spark com Hudi packages (pode baixar JARs no primeiro run)…")
    spark = setup_spark(args.master, args.driver_memory)
    from pyspark.sql import functions as F  # após session up

    # Lista paths exatos das partições selecionadas (inclusiveness explícito)
    read_paths = [str(d) for d in year_dirs]
    print(f"\n▸ lendo CSVs PT-BR (sep=';' latin-1, header, STRING-ONLY)…")
    df_raw = (spark.read
        .option("header", "true")
        .option("sep", ";")
        .option("encoding", "latin1")
        .option("inferSchema", "false")
        .csv(read_paths))

    df = df_raw.toDF(*[sanitize_col(c) for c in df_raw.columns])
    df = (df
        .withColumn("_source_file", F.input_file_name())
        .withColumn("ano",
            F.regexp_extract(F.col("_source_file"), r"/ano=(\d{4})(?:/|$)", 1).cast("int"))
        .withColumn("_ingest_ts", F.current_timestamp())
        .withColumn("_hudi_rowid",
            F.sha2(F.concat_ws("||",
                F.col("_source_file"),
                F.monotonically_increasing_id().cast("string"),
            ), 256))
    )

    n_rows = df.count()
    n_cols = len(df.columns)
    print(f"  rows={n_rows:,}  cols={n_cols}")
    if n_rows == 0:
        print("✗ DataFrame vazio — nada a escrever", file=sys.stderr)
        return 1

    if args.clean and args.append:
        print("✗ --clean e --append são mutuamente exclusivos", file=sys.stderr)
        return 1

    # Append: detecta se já existe um Hudi escrito previamente. Se existir,
    # usa operation=insert (não bulk_insert — bulk só roda no primeiro batch
    # pra setup do timeline). Se não existir, faz overwrite + bulk_insert
    # como o primeiro ano do loop.
    is_first_write = not (out_dir / ".hoodie").exists()
    if args.append and is_first_write:
        print(f"  --append mas {out_dir}/.hoodie ainda não existe → tratando como primeiro write")

    write_mode = "overwrite" if (not args.append or is_first_write) else "append"
    operation  = "bulk_insert" if (not args.append or is_first_write) else "insert"
    print(f"  mode={write_mode}  operation={operation}")

    print(f"\n▸ escrevendo Hudi CoW em {out_dir}…")
    t0 = time.time()
    hudi_options = {
        "hoodie.table.name":                              "rais_vinculos_hudi",
        "hoodie.datasource.write.recordkey.field":        "_hudi_rowid",
        "hoodie.datasource.write.partitionpath.field":    "ano",
        "hoodie.datasource.write.table.name":             "rais_vinculos_hudi",
        "hoodie.datasource.write.operation":              operation,
        "hoodie.datasource.write.table.type":             "COPY_ON_WRITE",
        "hoodie.datasource.write.precombine.field":       "_ingest_ts",
        "hoodie.datasource.write.hive_style_partitioning":"true",
        "hoodie.parquet.compression.codec":               "snappy",
        # Append/insert mode: cada ano é uma partição nova; sem clustering
        # automático pra não pagar custo de re-organização entre runs.
        "hoodie.combine.before.insert":                   "false",
        "hoodie.datasource.write.insert.drop.duplicates": "false",
    }

    out_dir.parent.mkdir(parents=True, exist_ok=True)
    (df.write.format("hudi")
        .options(**hudi_options)
        .mode(write_mode)
        .save(str(out_dir)))

    elapsed = time.time() - t0
    # Filesystem walk pra reportar tamanho final
    out_size = sum(f.stat().st_size for f in out_dir.rglob("*") if f.is_file())
    print(f"\n✔ Hudi escrito em {elapsed:,.1f}s")
    print(f"  rows total : {n_rows:,}")
    print(f"  size       : {out_size/1_048_576:,.1f} MB")
    print(f"  path       : {out_dir}")
    print(f"\nPróximo passo: subir pro Volume Databricks")
    print(f"  bash articles/scripts/upload_rais_hudi_to_volume.sh {args.output_dir.resolve()}")

    spark.stop()
    return 0


if __name__ == "__main__":
    sys.exit(main())

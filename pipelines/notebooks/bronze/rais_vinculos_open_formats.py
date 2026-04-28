# Databricks notebook source
# MAGIC %md
# MAGIC # bronze · rais_vinculos_open_formats
# MAGIC
# MAGIC Expõe o `bronze.rais_vinculos` (Delta canônico) também em **Apache
# MAGIC Iceberg** via Delta UniForm — sem duplicação de storage e sem rodar
# MAGIC writer paralelo. Roda DEPOIS do `bronze_rais_vinculos` no DAG (precisa
# MAGIC da tabela existir pra habilitar UniForm).
# MAGIC
# MAGIC | Tabela                          | Formato físico  | Storage          | Origem                  |
# MAGIC |---------------------------------|-----------------|------------------|-------------------------|
# MAGIC | `bronze.rais_vinculos`          | Delta           | ~22 GB           | Auto Loader / batch     |
# MAGIC | `bronze.rais_vinculos_iceberg`  | **VIEW** sobre canônica | 0 (compartilha) | UniForm sidecar |
# MAGIC | `bronze.rais_vinculos_hudi`     | Hudi (external) | ~25 GB           | bulk_insert local       |
# MAGIC
# MAGIC ## Por que UniForm sobre canônica (e não bronze paralela)
# MAGIC
# MAGIC Free Edition serverless **não permite Iceberg writer nativo** (Maven
# MAGIC `org.apache.iceberg` ausente do classpath). Tentar uma "bronze paralela"
# MAGIC seria escrever DUAS Delta tables sobre o mesmo TXT — writer Delta nos
# MAGIC dois lados, ~22 GB de duplicação, e zero ganho de fato (seria fingir
# MAGIC paralelismo). UniForm sobre a canônica é honesto:
# MAGIC
# MAGIC - **Storage overhead**: zero (~MB de metadata sidecar `metadata/v1.metadata.json`)
# MAGIC - **Leitor**: clientes Iceberg (Trino, Snowflake, Athena, pyiceberg) leem
# MAGIC   `bronze.rais_vinculos` direto via Iceberg REST/Hive
# MAGIC - **Posicionamento honesto**: "plataforma é format-agnostic na leitura"
# MAGIC   — não "plataforma roda 2 bronzes em paralelo"
# MAGIC
# MAGIC A VIEW `bronze.rais_vinculos_iceberg` aponta pra `bronze.rais_vinculos`
# MAGIC com COMMENT explícito documentando o setup. Quem buscar "iceberg" no UC
# MAGIC encontra o ponto de entrada nomeado.
# MAGIC
# MAGIC ## Hudi: deferido (constraint de workspace)
# MAGIC
# MAGIC Hudi não tem UniForm equivalente. Escrever Hudi nativo requer
# MAGIC `org.apache.hudi:hudi-spark3.5-bundle_2.12:0.15.0` no classpath do
# MAGIC cluster — não disponível em serverless. Pendente: rodar uma vez em
# MAGIC compute clássico (Maven packages no cluster) — depois o reader serverless
# MAGIC consegue acessar a tabela Hudi externamente registrada.
# MAGIC
# MAGIC Quando classic compute estiver disponível: setar widget `enable_hudi=true`.

# COMMAND ----------

dbutils.widgets.text("catalog",          "mirante_prd")
dbutils.widgets.text("source_table",     "mirante_prd.bronze.rais_vinculos")
dbutils.widgets.text("txt_extracted",    "/Volumes/mirante_prd/bronze/raw/mte/rais_txt_extracted")
dbutils.widgets.text("open_formats_root","/Volumes/mirante_prd/bronze/raw/_open_formats")
dbutils.widgets.text("enable_iceberg",   "true")
dbutils.widgets.text("enable_hudi",      "false")  # default: deferred (serverless workspace)

CATALOG          = dbutils.widgets.get("catalog")
SOURCE_TABLE     = dbutils.widgets.get("source_table")
TXT_EXTRACTED    = dbutils.widgets.get("txt_extracted")
OPEN_ROOT        = dbutils.widgets.get("open_formats_root")
ENABLE_ICEBERG   = dbutils.widgets.get("enable_iceberg").lower() in ("true","1","yes")
ENABLE_HUDI      = dbutils.widgets.get("enable_hudi").lower()    in ("true","1","yes")

ICEBERG_VIEW     = f"{CATALOG}.bronze.rais_vinculos_iceberg"
HUDI_TABLE       = f"{CATALOG}.bronze.rais_vinculos_hudi"
HUDI_LOC         = f"{OPEN_ROOT}/rais_vinculos_hudi"

print(f"source           = {SOURCE_TABLE}")
print(f"iceberg view     = {ICEBERG_VIEW}  (UniForm sidecar sobre {SOURCE_TABLE})")
print(f"hudi table       = {HUDI_TABLE}     @ {HUDI_LOC}")
print(f"enable_iceberg   = {ENABLE_ICEBERG}")
print(f"enable_hudi      = {ENABLE_HUDI}")

# COMMAND ----------

# MAGIC %md ## Iceberg via Delta UniForm

# COMMAND ----------

iceberg_status = "skipped"
iceberg_bytes  = 0
iceberg_rows   = 0

if ENABLE_ICEBERG:
    print("=== ICEBERG (UniForm sidecar sobre Delta canônica) ===")
    try:
        if not spark.catalog.tableExists(SOURCE_TABLE):
            raise RuntimeError(f"{SOURCE_TABLE} não existe — bronze_rais_vinculos não rodou?")

        # 1. Habilita UniForm Iceberg na tabela Delta canônica.
        # Idempotente: re-aplicar não custa nada; metadata sidecar é regenerado
        # quando há novos commits Delta. Requer Delta Reader/Writer >= 2 + 7.
        print(f"  ALTER TABLE {SOURCE_TABLE} SET TBLPROPERTIES UniForm Iceberg…")
        spark.sql(f"""
            ALTER TABLE {SOURCE_TABLE} SET TBLPROPERTIES (
                'delta.universalFormat.enabledFormats' = 'iceberg',
                'delta.enableIcebergCompatV2'          = 'true'
            )
        """)

        # 2. Cria/atualiza a VIEW que sinaliza "leitura como Iceberg" pro front.
        # Não é re-escrita — é um alias semântico pro card "Iceberg" no strip.
        spark.sql(f"DROP VIEW IF EXISTS {ICEBERG_VIEW}")
        spark.sql(f"""
            CREATE VIEW {ICEBERG_VIEW} AS
            SELECT * FROM {SOURCE_TABLE}
        """)
        spark.sql(f"""
            COMMENT ON VIEW {ICEBERG_VIEW} IS
            'Mirante · RAIS Vínculos Públicos — exposição em Apache Iceberg via '
            'Delta UniForm. View aponta pra bronze.rais_vinculos (Delta canônico); '
            'metadata Iceberg gerada pelo Delta writer compartilha os mesmos '
            'arquivos Parquet — zero overhead de storage. Clientes Iceberg '
            '(Trino, Snowflake, Athena, pyiceberg) podem ler bronze.rais_vinculos '
            'diretamente via Iceberg REST. Free Edition serverless não permite '
            'Iceberg writer nativo (Maven org.apache.iceberg ausente do classpath); '
            'UniForm é o caminho honesto pra interop sem fingir paralelismo de write.'
        """)

        # 3. Reporta size/rows do Delta canônico (mesmos arquivos físicos)
        det = spark.sql(f"DESCRIBE DETAIL {SOURCE_TABLE}").first()
        iceberg_bytes = int(det["sizeInBytes"]) if det and det["sizeInBytes"] else 0
        iceberg_rows  = spark.read.table(SOURCE_TABLE).count()
        print(f"  ✓ {ICEBERG_VIEW} criado (storage compartilhado com canônica)")
        print(f"  storage compartilhado: {iceberg_bytes/1_073_741_824:.2f} GB ({iceberg_rows:,} rows)")
        print(f"  → metadata Iceberg sidecar gerada pelo Delta writer no próximo commit")
        iceberg_status = "ok_uniform"
    except Exception as e:
        print(f"  ✗ Iceberg UniForm falhou: {type(e).__name__}: {str(e)[:300]}")
        iceberg_status = f"failed: {type(e).__name__}"

# COMMAND ----------

# MAGIC %md ## Hudi (deferido em serverless · ativar quando classic compute estiver disponível)

# COMMAND ----------

import re
import unicodedata
from pathlib import Path
from pyspark.sql import functions as F

hudi_status = "deferred_serverless"
hudi_bytes  = 0
hudi_rows   = 0

if ENABLE_HUDI:
    print("=== HUDI ===")
    try:
        # Reaproveita o exato CSV-parse + sanitização do bronze Delta canônico
        # pra que o Hudi escreva sobre o mesmo input lógico (TXT cru).
        def _sanitize_col(name: str) -> str:
            if not name: return "col"
            leading = name.startswith("_")
            nfkd = unicodedata.normalize("NFKD", name)
            no_accents = "".join(c for c in nfkd if not unicodedata.combining(c))
            s = re.sub(r"[^a-zA-Z0-9_]+", "_", no_accents)
            s = re.sub(r"_+", "_", s).strip("_").lower() or "col"
            return ("_" + s) if leading else s

        df_raw = (spark.read
            .option("header","true").option("sep",";")
            .option("encoding","latin1").option("inferSchema","false")
            .csv(f"{TXT_EXTRACTED}/ano=*/"))
        df = (df_raw
            .toDF(*[_sanitize_col(c) for c in df_raw.columns])
            .withColumn("_source_file", F.col("_metadata.file_path"))
            .withColumn("ano",
                F.regexp_extract(F.col("_metadata.file_path"), r"/ano=(\d{4})(?:/|$)", 1).cast("int"))
            .withColumn("_ingest_ts", F.current_timestamp())
            .withColumn("_hudi_rowid",
                F.sha2(F.concat_ws("||",
                    F.coalesce(F.col("_metadata.file_path"), F.lit("")),
                    F.monotonically_increasing_id().cast("string"),
                ), 256))
        )

        spark.sql(f"DROP TABLE IF EXISTS {HUDI_TABLE}")
        try: dbutils.fs.rm(HUDI_LOC, True)
        except Exception: pass

        hudi_options = {
            "hoodie.table.name":                              "rais_vinculos_hudi",
            "hoodie.datasource.write.recordkey.field":        "_hudi_rowid",
            "hoodie.datasource.write.partitionpath.field":    "ano",
            "hoodie.datasource.write.table.name":             "rais_vinculos_hudi",
            "hoodie.datasource.write.operation":              "bulk_insert",
            "hoodie.datasource.write.table.type":             "COPY_ON_WRITE",
            "hoodie.datasource.write.precombine.field":       "_ingest_ts",
            "hoodie.datasource.write.hive_style_partitioning":"true",
        }
        (df.write.format("hudi").options(**hudi_options).mode("overwrite").save(HUDI_LOC))
        spark.sql(f"CREATE TABLE {HUDI_TABLE} USING hudi LOCATION '{HUDI_LOC}'")

        hudi_rows = spark.read.table(HUDI_TABLE).count()
        det = spark.sql(f"DESCRIBE DETAIL {HUDI_TABLE}").first()
        hudi_bytes = int(det["sizeInBytes"]) if det and det["sizeInBytes"] else 0
        hudi_status = "ok"
        print(f"  ✓ {HUDI_TABLE}: {hudi_rows:,} rows, {hudi_bytes/1_073_741_824:.2f} GB")
    except Exception as e:
        print(f"  ✗ Hudi write falhou: {type(e).__name__}: {str(e)[:300]}")
        print(f"    Causa provável: package hudi-spark3.5-bundle ausente.")
        print(f"    Workspace é serverless-only — JARs Maven não são suportados.")
        print(f"    Fix: rodar uma vez em compute clássico com")
        print(f"      spark.jars.packages org.apache.hudi:hudi-spark3.5-bundle_2.12:0.15.0")
        hudi_status = f"failed: {type(e).__name__}"
else:
    print("=== HUDI (deferido) ===")
    print(f"  ENABLE_HUDI=false → workspace serverless não suporta Hudi JAR.")
    print(f"  Pra ativar: rodar este notebook uma vez em compute clássico com")
    print(f"    spark.jars.packages = org.apache.hudi:hudi-spark3.5-bundle_2.12:0.15.0")
    print(f"    spark.sql.extensions = org.apache.spark.sql.hudi.HoodieSparkSessionExtension")
    print(f"    spark.serializer = org.apache.spark.serializer.KryoSerializer")
    print(f"  E setar enable_hudi=true no widget.")

# COMMAND ----------

print("\n=== RESUMO ===")
print(f"  iceberg: status={iceberg_status}  rows={iceberg_rows:,}  size={iceberg_bytes/1_073_741_824:.2f} GB (compartilhado com Delta)")
print(f"  hudi:    status={hudi_status}  rows={hudi_rows:,}  size={hudi_bytes/1_073_741_824:.2f} GB")

# Não falha o DAG: front renderiza só o que existe
if iceberg_status.startswith("failed") and (ENABLE_HUDI and hudi_status.startswith("failed")):
    raise RuntimeError(
        f"Open formats falharam: iceberg={iceberg_status}  hudi={hudi_status}"
    )

# Databricks notebook source
# MAGIC %md
# MAGIC # bronze · rais_vinculos_open_formats
# MAGIC
# MAGIC Bronze paralela ao `bronze_rais_vinculos` (Delta canônico). Lê o **mesmo
# MAGIC TXT extraído** pelo `ingest_mte_rais` e escreve em formatos lakehouse
# MAGIC abertos. Roda em PARALELO com o bronze Delta canônico (não depende dele).
# MAGIC
# MAGIC | Tabela                          | Formato         | Storage             | Modo                    |
# MAGIC |---------------------------------|-----------------|---------------------|-------------------------|
# MAGIC | `bronze.rais_vinculos`          | Delta           | ~22 GB (canônico)   | Auto Loader / batch     |
# MAGIC | `bronze.rais_vinculos_iceberg`  | Delta + Iceberg | ~22 GB (espelho)    | **UniForm at create**   |
# MAGIC | `bronze.rais_vinculos_hudi`     | Hudi            | ~25 GB (external)   | bulk_insert (CoW)       |
# MAGIC
# MAGIC ## Iceberg: bronze paralela com UniForm at-create
# MAGIC
# MAGIC O workspace é **serverless-only** — Iceberg writer Maven nativo
# MAGIC (org.apache.iceberg) não está disponível como classpath dependency.
# MAGIC A solução é **Delta UniForm habilitado at-create**: a tabela é escrita
# MAGIC como Delta normal mas com `TBLPROPERTIES ('delta.universalFormat.
# MAGIC enabledFormats' = 'iceberg')`. Cada commit Delta gera o sidecar Iceberg
# MAGIC apontando pros mesmos arquivos Parquet — clientes Iceberg externos
# MAGIC (Trino, Snowflake, Athena, pyiceberg) leem diretamente.
# MAGIC
# MAGIC - **Input**: TXT_EXTRACTED (mesma fonte do Delta canônico)
# MAGIC - **Output**: tabela Delta `bronze.rais_vinculos_iceberg` separada,
# MAGIC   com UniForm Iceberg habilitado desde a criação
# MAGIC - **Storage overhead**: ~22 GB de duplicação (preço da paralelização real)
# MAGIC - **Por que duplicar e não usar VIEW**: o objetivo é demonstrar que a
# MAGIC   plataforma roda DUAS bronzes em paralelo (Delta + Iceberg-via-UniForm)
# MAGIC   sobre o mesmo input. View que aponta pra Delta canônico é interop, não
# MAGIC   é arquitetura paralela.
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
dbutils.widgets.text("txt_extracted",    "/Volumes/mirante_prd/bronze/raw/mte/rais_txt_extracted")
dbutils.widgets.text("open_formats_root","/Volumes/mirante_prd/bronze/raw/_open_formats")
dbutils.widgets.text("enable_iceberg",   "true")
dbutils.widgets.text("enable_hudi",      "false")  # default: deferred (serverless workspace)

CATALOG          = dbutils.widgets.get("catalog")
TXT_EXTRACTED    = dbutils.widgets.get("txt_extracted")
OPEN_ROOT        = dbutils.widgets.get("open_formats_root")
ENABLE_ICEBERG   = dbutils.widgets.get("enable_iceberg").lower() in ("true","1","yes")
ENABLE_HUDI      = dbutils.widgets.get("enable_hudi").lower()    in ("true","1","yes")

ICEBERG_TABLE    = f"{CATALOG}.bronze.rais_vinculos_iceberg"
HUDI_TABLE       = f"{CATALOG}.bronze.rais_vinculos_hudi"
HUDI_LOC         = f"{OPEN_ROOT}/rais_vinculos_hudi"

print(f"input txt        = {TXT_EXTRACTED}/ano=*/")
print(f"iceberg table    = {ICEBERG_TABLE}  (Delta + UniForm Iceberg, paralela ao canônico)")
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
    print("=== ICEBERG (Delta + UniForm at-create, paralelo ao Delta canônico) ===")
    import re
    import unicodedata
    from pyspark.sql import functions as F

    def _sanitize_col(name: str) -> str:
        if not name: return "col"
        leading = name.startswith("_")
        nfkd = unicodedata.normalize("NFKD", name)
        no_accents = "".join(c for c in nfkd if not unicodedata.combining(c))
        s = re.sub(r"[^a-zA-Z0-9_]+", "_", no_accents)
        s = re.sub(r"_+", "_", s).strip("_").lower() or "col"
        return ("_" + s) if leading else s

    try:
        # 1. Lê TXT cru direto (mesma fonte do bronze Delta canônico — paralelo real)
        print(f"  reading {TXT_EXTRACTED}/ano=*/ …")
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
        )

        # 2. Cria a tabela com UniForm Iceberg habilitado AT CREATION TIME
        # (não via ALTER posterior). Cada commit Delta vai gerar metadata
        # Iceberg sidecar imediatamente.
        print(f"  CREATE OR REPLACE TABLE {ICEBERG_TABLE} (Delta + UniForm Iceberg)…")
        spark.sql(f"DROP TABLE IF EXISTS {ICEBERG_TABLE}")
        (df.write.format("delta")
            .partitionBy("ano")
            .option("overwriteSchema", "true")
            .mode("overwrite")
            .saveAsTable(ICEBERG_TABLE))
        spark.sql(f"""
            ALTER TABLE {ICEBERG_TABLE} SET TBLPROPERTIES (
                'delta.universalFormat.enabledFormats' = 'iceberg',
                'delta.enableIcebergCompatV2'          = 'true',
                'delta.columnMapping.mode'             = 'name'
            )
        """)
        spark.sql(f"""
            COMMENT ON TABLE {ICEBERG_TABLE} IS
            'Mirante · RAIS Vínculos Públicos — bronze paralela em Delta + UniForm Iceberg. '
            'Mesma fonte (TXT cru extraído pelo ingest_mte_rais), processo de write '
            'independente do bronze.rais_vinculos canônico. Cada commit Delta gera '
            'metadata Iceberg apontando pros arquivos Parquet — clientes Iceberg '
            '(Trino, Snowflake, Athena, pyiceberg) podem ler diretamente via REST. '
            'Roda em paralelo ao bronze Delta canônico no DAG (ambos dependem só de '
            'ingest_mte_rais). Trade-off: ~22 GB de duplicação de storage.'
        """)
        for k, v in [
            ("layer",  "bronze"),
            ("domain", "rais"),
            ("source", "mte/pdet"),
            ("format", "delta+iceberg"),
            ("grain",  "vinculo_ano_uf"),
            ("pii",    "true"),
        ]:
            spark.sql(f"ALTER TABLE {ICEBERG_TABLE} SET TAGS ('{k}' = '{v}')")

        # 3. Reporta size/rows da bronze paralela
        det = spark.sql(f"DESCRIBE DETAIL {ICEBERG_TABLE}").first()
        iceberg_bytes = int(det["sizeInBytes"]) if det and det["sizeInBytes"] else 0
        iceberg_rows  = spark.read.table(ICEBERG_TABLE).count()
        print(f"  ✓ {ICEBERG_TABLE} criado")
        print(f"  storage: {iceberg_bytes/1_073_741_824:.2f} GB ({iceberg_rows:,} rows)")
        print(f"  metadata Iceberg sidecar gerada por UniForm em cada commit Delta")
        iceberg_status = "ok_parallel"
    except Exception as e:
        print(f"  ✗ Iceberg paralelo falhou: {type(e).__name__}: {str(e)[:300]}")
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

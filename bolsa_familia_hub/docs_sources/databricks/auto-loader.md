# Databricks Auto Loader (cloudFiles)

> Fonte: https://docs.databricks.com/en/ingestion/cloud-object-storage/auto-loader/index.html

## O que é

Solução de ingestão incremental que processa automaticamente novos arquivos conforme chegam ao armazenamento em nuvem. Oferece uma fonte Structured Streaming chamada `cloudFiles`.

## Detecção incremental

Dois modos:
1. **Directory Listing Mode** (padrão) — varre diretórios em busca de novos arquivos.
2. **File Notification Mode** (recomendado) — usa APIs nativas de eventos de armazenamento em nuvem.

Escala para "near real-time ingestion of millions of files per hour"; suporta migrações com bilhões de arquivos.

## Schema inference e evolution

- Detecta novas colunas automaticamente
- Trata mudanças de tipo de dado ("automatic type widening")
- Resgata dados que seriam perdidos por mudança de schema

## Checkpointing

Progresso rastreado via armazenamento chave-valor escalável (RocksDB) no checkpoint. Garante processamento exactly-once e recuperação após falhas sem gerenciamento manual de estado.

## Formatos suportados e limitações

- **Suportados:** JSON, CSV, XML, PARQUET, AVRO, ORC, TEXT, BINARYFILE (com compressão)
- **Limitação conhecida:** não suporta nativamente ZIP ou outros formatos compactados complexos
- Não garante ordem de processamento entre arquivos
- Requer estratégias customizadas para dados desincronizados

## Fontes suportadas

Amazon S3, Azure ADLS, Google Cloud Storage, Unity Catalog volumes, Azure Blob Storage.

## Relação com o pipeline do Mirante

`pipelines/notebooks/bronze/pbf_pagamentos.py` documenta exatamente essa limitação: "Pra PBF, Auto Loader não trabalha bem com ZIPs (não tem reader nativo)". A solução adotada é o padrão recomendado — extrair cada ZIP novo para CSV (idempotente, skip-if-extracted) numa pasta separada, e então apontar o Auto Loader (`cloudFiles`) para essa pasta de CSVs como source.

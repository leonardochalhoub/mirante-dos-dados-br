# Delta Lake — Operações em Batch (time travel, append/overwrite, schema evolution)

> Fonte: https://docs.delta.io/latest/delta-batch.html

## Time Travel

```sql
-- Por timestamp
SELECT * FROM tabela TIMESTAMP AS OF '2018-10-18T22:15:12.013Z'

-- Por versão
SELECT * FROM tabela VERSION AS OF 123
```

O timestamp de cada versão N depende do arquivo de log correspondente — viagens por versão mantêm integridade ao copiar tabelas, enquanto timestamps podem se comportar de forma inconsistente.

**Retenção:**
- Padrão: 30 dias de histórico (`delta.logRetentionDuration`)
- Arquivos deletados retidos por 7 dias (`delta.deletedFileRetentionDuration`)
- `VACUUM` remove dados não referenciados, mas não deleta os logs

## Append vs Overwrite

```sql
-- Append
INSERT INTO tabela SELECT * FROM dados_novos

-- Overwrite total
INSERT OVERWRITE TABLE tabela SELECT * FROM dados_novos

-- Overwrite seletivo
INSERT INTO tabela REPLACE WHERE data >= '2017-01-01' SELECT * FROM dados_novos
```

## Validação e evolução de schema

- Todas as colunas do DataFrame devem existir na tabela; tipos devem corresponder; nomes case-sensitive.
- Evolução automática (Delta 4.3+): `INSERT WITH SCHEMA EVOLUTION INTO tabela_destino ...`
- Versões anteriores: `df.write.option("mergeSchema", "true").mode("append")...` ou `spark.conf.set("spark.databricks.delta.schema.autoMerge.enabled", True)`
- Colunas novas são acrescentadas ao final; linhas existentes recebem `NULL`.

## Relação com o pipeline do Mirante

O comentário no topo de `pipelines/databricks.yml` resume a escolha arquitetural do projeto: "pure Delta tables (no DLT, no materialized views) — Bronze: Auto Loader append; Silver: batch read latest bronze snapshot → Delta overwrite (Delta time travel); Gold: batch joins silver → Delta overwrite." Ou seja, Silver e Gold usam exatamente o padrão overwrite documentado aqui, e o "Delta time travel" citado no comentário é o mecanismo que torna esse overwrite seguro (histórico preservado, reprocessável).

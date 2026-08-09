# Spark SQL e DataFrame API

> Fonte: https://spark.apache.org/docs/latest/sql-programming-guide.html

## O que é um DataFrame

Coleção distribuída de dados organizada em colunas nomeadas. Equivalente a uma tabela relacional, um data frame em R/Python, ou `Dataset[Row]` em Scala/Java.

- Abstração de alto nível sobre RDDs, com otimizações automáticas
- Disponível em Python, Scala, Java e R
- Tipagem em runtime (Python/R) e compile-time (Scala/Java)
- Construído a partir de arquivos estruturados, tabelas Hive, bancos externos, ou RDDs existentes

## Execution engine unificado

"When computing a result, the same execution engine is used, independent of which API/language you are using to express the computation." Operações em DataFrame são transformações lazy — só materializadas quando uma ação é executada. Spark SQL extrai metadados estruturais (schema, tipos) do DataFrame para otimizações automáticas na execução, diferente da API bruta de RDDs.

## Dataset vs DataFrame

- **Dataset:** interface genérica com tipagem forte (Scala/Java) e transformações funcionais.
- **DataFrame:** especialização de Dataset para dados tabulares (`Dataset[Row]`).

## Acesso

Via shell (`spark-shell`, `pyspark`), CLI SQL, ou JDBC/ODBC — inclusive contra warehouses SQL do Databricks, que é como este Knowledge Hub consulta o Ledger (`bolsa_familia_hub/config.py::databricks_connection`, via `databricks-sql-connector`).

## Relação com o pipeline do Mirante

Todos os notebooks `silver/*.py` e `gold/*.py` do pipeline PBF (`pipelines/notebooks/silver/pbf_total_uf_mes.py`, `pipelines/notebooks/gold/pbf_estados_df.py`) são PySpark puro: `spark.read.table(...)`, transformações com `pyspark.sql.functions as F`, e `write` de volta para Delta. A "mesma execution engine" citada acima é o que garante que o SQL usado no Ledger deste hub (`query_ledger`) e as transformações Python dos notebooks produzem resultados consistentes sobre a mesma tabela.

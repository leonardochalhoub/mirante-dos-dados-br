# Arquitetura Medallion (Databricks)

> Fonte: https://docs.databricks.com/en/lakehouse/medallion.html — snapshot capturado para o Memory (RAG) do Bolsa Família Knowledge Hub.

## Visão Geral

A arquitetura medallion descreve "uma série de camadas de dados que denotam a qualidade dos dados armazenados no lakehouse". É um padrão de design que organiza dados logicamente, permitindo melhorias incrementais na estrutura e qualidade conforme os dados fluem através de cada camada.

## Bronze (Dados Brutos)

**O que representa:** camada de ingestão de dados brutos, sem validação ou limpeza. Recebe dados de múltiplas fontes mantendo o estado original.

**Características:**
- Preserva dados em formatos originais das fontes
- Cresce incrementalmente mediante leituras append-only
- Armazena histórico completo para reprocessamento e auditoria
- Fontes suportadas: S3, GCS, ADLS, Kafka, Kinesis e sistemas federados

**Usuários-alvo:** engenheiros de dados, operações de dados, conformidade/auditoria.

**Qualidade e boas práticas:**
- Validação mínima
- Campos armazenados preferencialmente como string, VARIANT ou binary
- Colunas de metadados como `_metadata.file_name` (proveniência)
- Evita perda de dados por mudanças de schema inesperadas

## Silver (Dados Validados)

**O que representa:** camada de validação, limpeza e estruturação de dados para consumo por engenheiros, analistas e cientistas de dados.

**Características:**
- Inclui pelo menos uma representação validada e não agregada de cada registro
- Leitura preferencial em modo streaming desde bronze
- Leituras em batch apenas para datasets pequenos

**Operações de qualidade de dados:**
- Aplicação de schemas
- Tratamento de valores nulos e faltantes
- Deduplicação e normalização
- Resolução de dados atrasados ou fora de ordem
- Evolução de schema, type casting, joins

## Gold (Dados Enriquecidos)

**O que representa:** visões refinadas altamente agregadas, otimizadas para analytics, BI, ML e aplicações operacionais.

**Características:**
- Dados agregados e filtrados por períodos ou regiões específicas
- Datasets semanticamente significativos alinhados com funções de negócio
- Contém menos datasets que silver e bronze

**Modelagem:**
- Modelos dimensionais com relações e medidas estabelecidas
- Funções de agregação: somas, contagens, máximos, mínimos
- Materialized views para cálculos frequentes

## Controle de Custos: Frequência de Ingestão

| Tipo | Custo | Latência | Tecnologia |
|---|---|---|---|
| Contínua | Maior | Menor | Streaming Table com `spark.readStream` contínuo |
| Triggered | Médio | Médio | Streaming Table com scheduled/file arrival trigger |
| Batch Manual | Menor | Máximo | `spark.read` com partition overwrite |

## Garantias de Qualidade

A arquitetura medallion garante atomicidade, consistência, isolamento e durabilidade conforme os dados passam por múltiplas camadas de validações e transformações. Cada camada aplica progressivamente maior refinamento antes do armazenamento otimizado para analytics.

## Relação com o pipeline do Mirante

O pipeline de Bolsa Família deste repositório (`pipelines/databricks.yml`, `pipelines/notebooks/{bronze,silver,gold}/pbf_*.py`) segue esse padrão literalmente: Bronze via Auto Loader append-only, Silver via batch overwrite com deduplicação/joins de dimensão (população, deflatores), Gold via joins finais para o schema consumido pelo front (`pbfPerCapita`, `pbfPerBenef`).

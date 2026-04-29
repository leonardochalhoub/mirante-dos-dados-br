# ADR-001 · Bronze RAIS: leitor dual-format per-year

**Status:** Accepted (2026-04-28)
**Deciders:** Leonardo Chalhoub (autor) + Conselho do Mirante (eng-software)
**Supersedes:** —
**Superseded by:** —

## Contexto

`mirante_prd.bronze.rais_vinculos` ingere 40 anos de microdados RAIS Vínculos (PDET/MTE), 1985–2024, ~2 bilhões de linhas, 977 arquivos brutos. Durante esse período PDET mudou silenciosamente o contrato de dados em 3 momentos:

1. **1994**: header expandiu de ~24 → ~31 colunas (adiciona Bairros Fortaleza, Bairros RJ, CBO 94 Ocupação, CNAE 95 Classe, Distritos SP, Faixa Hora Contrat, Idade, Natureza Jurídica, Regiões Adm DF, Tipo Admissão)
2. **2018**: arquivos passam de UF-individuais (`AC1985.txt`) para regionais (`RAIS_VINC_PUB_NORTE.txt`); header expande pra ~44 cols (adiciona ind_trabalho_intermitente após Lei 13.467/2017, Raça/Cor desde 2003+, Portador Deficiência desde 2008+)
3. **2023**: arquivos viram `.COMT` com **separador `,` em vez de `;`**; header renomeado com sufixo "- Código" em todos os campos categóricos; expande pra ~60 cols (adiciona 12 colunas mensais de remuneração `vl_rem_<mês>_sc`, Causa Afastamento × 3, Tipo Deficiência, Vínculo Abandonado, Ano Chegada Brasil)

Entre janeiro e abril de 2026, três tentativas anteriores de ingestão falharam silenciosamente:

- **Falha #1 (separador)**: `option("sep", ";")` hardcoded → 175M linhas 2023+2024 com 49/50 colunas NULL (sep `,` não foi reconhecido). Detectada no audit do Conselho 2026-04-28.
- **Falha #2 (cloudFiles option name)**: `cloudFiles.pathGlobFilter` (com prefixo) é rejeitado por Auto Loader (`[CF_UNKNOWN_OPTION_KEYS_ERROR]`); o nome correto é `pathGlobFilter` (sem prefixo `cloudFiles.`).
- **Falha #3 (UniForm Iceberg prereqs)**: IcebergCompatV2 exige `delta.columnMapping.mode='name'` + Deletion Vectors disabled + REORG PURGE. Default Delta DBR 18+ tem DV=on e mode=NoMapping. Bronze quebrou no `ALTER TABLE` final.
- **Falha #4 (header drift cross-year)**: `spark.read.csv(path_glob, header=true)` lê o header do **PRIMEIRO arquivo** do glob e usa pra todos. Como o pipeline lia `ano=*/`, todos os 977 arquivos ficaram alinhados ao header de 1985. Resultado: 1.89B linhas (1994-2022) com colunas semanticamente desalinhadas — `municipio` em 1996 continha valores de "Faixa Remun Média (SM)" porque essa era a coluna na posição 11 do header de 1985. DQ gate baseado em NULL ratio NÃO detectou isso (todas colunas estavam "100% populated", só com valores no lugar errado).

## Decisão

Adotamos um **leitor dual-format per-year** com 4 invariantes:

### 1. Detecção dual-format por extensão

```python
.txt + .TXT  →  sep=";"  encoding="latin1"
.COMT        →  sep=","  encoding="latin1"
```

Cada formato é lido em stream cloudFiles separado (`CK_TXT`, `CK_COMT`) com seu próprio `pathGlobFilter` e `schemaLocation`. Streams escrevem na MESMA bronze Delta via `mergeSchema=true`.

### 2. Leitura batch PER-ANO

```python
def _read_batch_per_year(glob: str, sep: str):
    parts = []
    for d in dbutils.fs.ls(TXT_EXTRACTED):
        if not d.isDir() or not d.name.startswith("ano="):
            continue
        df_y = (spark.read
            .option("header", "true")
            .option("sep", sep)
            .option("encoding", "latin1")
            .option("inferSchema", "false")
            .option("ignoreMissingFiles", "true")
            .option("pathGlobFilter", glob)
            .csv(d.path))
        parts.append(_filter_vinc(_sanitize_columns(_add_ano_from_path(df_y))))
    return parts[0].unionByName(parts[1], allowMissingColumns=True) ... if parts else None
```

Dentro de UM ano, todos os arquivos compartilham o mesmo header (PDET libera 1 schema por ano-batch). `spark.read.csv(year_path/*)` é seguro. **Cross-year**, headers diferem — a iteração explícita garante alinhamento por NOME de coluna, não por POSIÇÃO.

### 3. STRING-ONLY com sanitização snake_case

`bronze.rais_vinculos` armazena tudo como string (`inferSchema=false`). Headers PDET são sanitizados pra snake_case ASCII (NFKD + accent strip + non-alnum → `_` + lowercase). Colisões de sanitização (ex.: "Município" + "MUNICIPIO" cross-year) preservam ambas com sufixo `_dupN` — silver decide o coalesce.

### 4. UniForm Iceberg pré-requisitos atomizados

Habilitar IcebergCompatV2 **exige 3 ALTER TABLE separados**:
1. `delta.columnMapping.mode = 'name'` + minReaderVersion=2 + minWriterVersion=5
2. `delta.enableDeletionVectors = 'false'` + REORG TABLE APPLY (PURGE)
3. `delta.universalFormat.enabledFormats = 'iceberg'` + `delta.enableIcebergCompatV2 = 'true'`

Cada um em sua própria transação Delta — não dá pra mudar propriedades incompatíveis no mesmo SET TBLPROPERTIES.

## Consequências

### Positivas

- **Alinhamento semântico cross-year garantido**: cada coluna na bronze contém valores consistentes (município = código IBGE 6-7 dig em todos os anos, sexo = 1/2 ou 01/02 conforme era).
- **Schema evolution honesta**: cada linha tem populadas APENAS as colunas do header do seu próprio arquivo de origem. Coalesce cross-era é trabalho do silver.
- **DQ gate estrutural**: validação NULL ratio + range de valores em colunas críticas (cbo, sexo, motivo) por (`ano`, `_source_file`). Falha cedo se PDET trocar contrato silenciosamente de novo.
- **Reprodutibilidade peer-review**: working paper que cite `mirante_prd.bronze.rais_vinculos@v6` (Time Travel Delta) pode ser reproduzido exatamente. UC Iceberg REST permite leitores externos (Trino, Snowflake, Athena, pyiceberg).

### Negativas

- **Custo de ingestão maior**: 40 reads sequenciais (vs 1 read único no padrão broken). Run inicial ~3-4h em Photon serverless 2X-Small. Aceito porque é one-time.
- **Complexity tax na bronze**: 1500+ linhas de notebook com migration logic, dual checkpoints, REORG PURGE ordering. Documentação inline densa é obrigatória (e está).
- **Force_reconvert é destrutivo**: drop + rebuild de 2B linhas. Necessário quando algum invariante muda (ex.: novo formato PDET 2025+). Mitigado por priming streams com `includeExistingFiles=false`, que registra arquivos no checkpoint sem regravar dados.

### Trade-offs explícitos

- **Não usamos** `spark.read.csv` com glob multi-ano (broken). Trade-off: per-year iteration é mais código, mas única opção correta.
- **Não usamos** Auto Loader cloudFiles em batch mode pra ingestão inicial (cloudFiles também usa header do primeiro arquivo no `latestOffset` calculation). Trade-off: 2 reads → 1 read seria 2x mais rápido, mas perderia alinhamento.
- **Não removemos** colunas legacy depois do migration pra COMT. Bronze tem `municipio` AND `municipio_codigo` AND `municipio_trab_codigo`. Trade-off: schema expandido (88 cols total), mas cada linha tem só seu era populado, e silver coalesce resolve.

## Referências

- Conselho do Mirante 2026-04-28 · pareceres em `docs/conselho/parecer_*_rais_*_2026-04-28.md`
- Notebook implementação: `pipelines/notebooks/bronze/rais_vinculos.py` (commit `2158d65`)
- Audit inicial: `docs/conselho/briefing_rais_bronze_audit_2026-04-28.md`
- Spark CSV header behavior: [Spark Docs § CSV Files](https://spark.apache.org/docs/latest/sql-data-sources-csv.html)
- Databricks Auto Loader cloudFiles options: [docs.databricks.com/aws/en/ingestion/cloud-object-storage/auto-loader/options](https://docs.databricks.com/aws/en/ingestion/cloud-object-storage/auto-loader/options)
- Delta UniForm Iceberg: [docs.delta.io/latest/delta-uniform.html](https://docs.delta.io/latest/delta-uniform.html)

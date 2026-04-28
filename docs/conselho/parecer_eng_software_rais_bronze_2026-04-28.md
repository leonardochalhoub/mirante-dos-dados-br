# Parecer — Eng. Software & Plataforma de Dados
## Auditoria raw → bronze · `mirante_prd.bronze.rais_vinculos`

**Versão avaliada:** pipeline `pipelines/notebooks/bronze/rais_vinculos.py` (commit b6df45d, 2026-04-28)
**Score atribuído:** C+ (1,5 pts) — MAJOR REVISION
**Histórico:** primeira avaliação deste pipeline (não há versão anterior)
**Régua:** mestrado stricto sensu · A=3, B+=2,5, B=2, C=1, D=0 · aprovação ≥ 2,0

---

## Veredicto geral

O pipeline tem uma base de engenharia sólida — o design de idempotência, o auto-recovery via FTP, o sanitizador snake_case com sufixo `_dup`, e a lógica de particionamento Hive estão bem executados. O que o condena à nota C+ é a combinação de dois defeitos CRÍTICOS que resultam em ~197 M de linhas corrompidas ou ausentes (8,8% do total), acrescida de contaminação de grain em ~75 M de linhas adicionais e ausência total de metadados Unity Catalog obrigatórios. A corrupção de 2023–2024 passou silenciosamente pelo quality check, que valida apenas o arquivo `.txt` extraído, não o output do CSV reader. Isso não é um bug isolado — é uma lacuna de arquitetura no design do gate de qualidade.

O pipeline não pode ir para produção de publicação no estado atual. É necessária major revision com DROP + reingest de 2023–2024, correção do bug de separador, gate pós-bronze, e preenchimento obrigatório de UC metadata.

---

## Pontos fortes

- **Idempotência end-to-end** bem implementada: markers `.done`/`.bad`, reconciliação de extrações anteriores, cleanup de parciais em caso de LZMAError, restore de quarentena em `force_reconvert=true`. Isso é raro em pipelines de dados de 40 anos — mostra maturidade de engenharia de plataforma.

- **Auto-recovery via FTP PDET** (`_ftp_redownload`): detecta corrupção de `.7z`, re-baixa da fonte, retenta extração. Logicamente correto e com fallback para quarentena quando PDET também é fonte corrompida. A separação entre `bad_archive` e `other` no `_try_extract` evita loops de retry desnecessários.

- **Sanitizador snake_case + colisão `_dupN`** (`_sanitize_columns`): resolve um problema real de schema drift cross-ano da RAIS (MUNICIPIO vs Município vs municipio) sem dropar informação — preserva ambas as colunas no bronze e delega coalescing para silver. Filosoficamente correto para camada bronze.

- **`_validate_txt_content` como gate de conteúdo pré-bronze**: a ideia de validar HEAD+TAIL (128KB total) sem ler o arquivo inteiro é eficiente para arquivos de 1–6 GB. O tratamento de sidecars não-.txt que passam sem validação (linha 261) evita falso-positivo que mandou arquivos saudáveis para quarentena em versões anteriores.

- **Particionamento Hive-style `ano=YYYY/`**: derivação do `ano` via regex no `_metadata.file_path` com fail-fast (`raise RuntimeError`) para linhas sem `ano` é a abordagem correta — evita corrupção silenciosa da partição.

- **`mergeSchema=true` + Auto Loader `schemaEvolutionMode=addNewColumns`**: design correto para lidar com o schema drift histórico da RAIS (42 colunas em 1985, ~60 em 2023+). A decisão de preservar tudo no bronze é defensável desde que o silver faça a reconciliação.

- **Logging de diagnóstico detalhado**: seção de diagnóstico do Volume, cleanup de ESTAB legacy, reconciliação de markers — tudo impresso com contadores claros. Facilita operação e debug.

---

## Problemas críticos e análise técnica

### Issue A — separador hardcoded `";"` para arquivos `.COMT` (CRÍTICO)

**Causa raiz:** `option("sep", ";")` hardcoded nas três leituras — batch (linha 1039), batch stream priming (linha 1064), e Auto Loader incremental (linha 1081). PDET 2023+ mudou separador para `,` e extensão para `.COMT`. O pipeline não detecta essa mudança.

**Resultado:** ~175 M de linhas em `bronze.rais_vinculos` com 49/50 colunas de dados NULL. A coluna `bairros_sp` recebeu a linha inteira (todos os campos comma-separated como uma única string), o que comprova que o CSV reader abriu o arquivo, reconheceu o header pela primeira coluna que casou (coincidência posicional ou column order), e jogou o restante na primeira coluna por falta de delimitadores reconhecidos.

**Por que o quality check não pegou:** `_validate_txt_content` valida o arquivo `.txt`/`.COMT` **antes do CSV reader**. Ela conta semicolons no header do arquivo; se o arquivo `.COMT` tem zero semicolons (porque é comma-separated), o check deveria ter falhado com `header_no_csv_separator(found_0_semicolons)`. Mas o check contém um bypass explícito na linha 261:

```python
if not txt_path.name.lower().endswith(".txt"):
    return True, "non_txt_sidecar_skipped"
```

Arquivos `.COMT` passam pelo bypass com `True` — validação considerada OK, marker `.done` gravado, CSV reader abre com `sep=";"` e produz 175 M de linhas corrompidas. O fix do sidecar bypass (que foi feito para evitar falso-positivo de PDFs e READMEs co-empacotados) criou um false-negative para o formato canônico de dados de 2023+.

**Gravidade:** CRÍTICO. Não é ruído estatístico — são dois anos inteiros de dados inutilizáveis.

---

### Issue B — SP 2024 ausente (CRÍTICO)

**Causa raiz hipotetizada:** race condition entre extração e checkpoint do Auto Loader. O arquivo `RAIS_VINC_PUB_SP.COMT` (6,2 GB) foi extraído com timestamp 12:26, depois que os outros 6 arquivos do ano=2024 foram processados (~01:55–02:21). O Auto Loader em modo `availableNow` captura um snapshot dos arquivos descobertos no schema location no momento da inicialização do stream. Se o checkpoint foi inicializado antes do SP terminar de extrair, o arquivo entra no Volume depois do snapshot e o stream termina sem processá-lo. Na próxima run com Auto Loader incremental (não-batch), o SP seria detectado como novo arquivo — mas combinado com Issue A, produziria 22 M de linhas corrompidas de qualquer forma.

**Mecanismo técnico:** `trigger(availableNow=True)` faz o stream processar todos os arquivos pendentes no checkpoint e depois terminar. Um arquivo que chega depois do snapshot inicial do run não é garantidamente detectado — depende do tempo de polling do cloudFiles e da janela entre a descoberta inicial e o término do stream. Não há documentação oficial da Databricks garantindo que `availableNow` re-escaneie continuamente enquanto está ativo.

**Gravidade:** CRÍTICO. ~22 M de linhas de SP 2024 perdidas. SP é o maior estado empregador do Brasil (~25-30% do emprego formal).

---

### Issue C — contaminação ESTAB em tabela VINC (ALTO)

**Causa raiz:** o filtro `_is_vinculo_filename` opera no passo de extração (`.7z` → `.txt`), não no passo de leitura (Auto Loader CSV). O `READ_PATH = f"{TXT_EXTRACTED}/ano=*/"` lê **qualquer arquivo** que esteja nos diretórios `ano=YYYY/`, incluindo arquivos ESTAB que foram extraídos por runs anteriores ao fix do filtro. O comentário no código (linha 362-393) documenta o problema e inclui cleanup de ESTAB legacy, mas esse cleanup é apenas para o Volume — não limpa `bronze.rais_vinculos`.

**Schema impact:** ESTAB tem grain de estabelecimento (1 linha por CNPJ), VINC tem grain de vínculo empregatício (1 linha por contrato). Misturar os dois grains em uma tabela bronze viola a garantia implícita de grain consistency que toda camada bronze deve honrar, independentemente da política STRING-ONLY.

**Detalhe estranho 2022:** filename `RAIS_ESTAB_PUB.txt.txt` (duplo `.txt`) indica não-determinismo no step de renomear/copiar de alguma versão anterior. O regex `RAIS_ESTAB_RE` não captura extensão, apenas stem — portanto `RAIS_ESTAB_PUB.txt.txt` é detectado como ESTAB e seria filtrado em novas extrações. Mas se já está no Volume, o Auto Loader o leu.

**Gravidade:** ALTO. ~75 M de linhas com grain errado. Qualquer aggregate naïve em bronze (`COUNT(*) GROUP BY uf`) está errado para anos com contaminação ESTAB.

---

### Issue D — SP 1986 em quarentena permanente (MÉDIO)

**Causa raiz:** PDET FTP serve `SP1986_1986.7z` corrompido. Duas tentativas de re-download via `_ftp_redownload` falharam (conforme lógica do pipeline: `_ftp_redownload` → `_try_extract` → bad_archive → quarentena). Pipeline está funcionando como projetado — o problema é a fonte.

**Impacto:** ~7-13 M de linhas SP 1986 ausentes. Para análise de série histórica que inclua 1986, SP estará subrepresentado. Isso deve ser documentado como limitação conhecida.

**Mitigação disponível:** verificar se IPEA Data, IBGE ou parceiros institucionais têm o arquivo. A cópia original do MTE/PDET foi arquivada antes de 2000 — o FTP atual pode ter bitrot no arquivo de 1986.

---

### Issue E — Unity Catalog metadata completamente ausente (PADRÃO VIOLADO)

**Violação direta da regra de plataforma:** "Unity Catalog metadata mandatory — every new table in mirante_prd ships with verbose table+column COMMENTs and TAGS (layer/domain/source/pii/grain) in the same notebook."

O notebook tem, ao final (linhas 1128-1137), um `COMMENT ON TABLE` que descreve UniForm/Iceberg — mas não descreve o dataset. Mais importante: não tem um único `ALTER TABLE ... ALTER COLUMN ... COMMENT` para nenhuma das 51 colunas de dados. DESCRIBE EXTENDED mostra `null` em todas.

As TAGs `iceberg_uniform` e `iceberg_endpoint` (linhas 1122-1126) existem, mas as TAGs obrigatórias de plataforma `layer`, `domain`, `source`, `pii`, `grain` estão ausentes.

Isso viola contrato explícito de governança. Para uma tabela de 2,2 B de linhas de dados de trabalho (contendo potencialmente dados pessoais — CNPJ, CPF em campos de remuneração), a ausência de TAG `pii` é particularmente problemática do ponto de vista LGPD.

---

## Análise do Quality Check (pergunta direta do briefing)

### O que o QC atual faz e não faz

O quality check atual (linhas 843–920) tem três camadas:
1. Verifica que todos os arquivos esperados do `.7z` existem no Volume
2. Chama `_validate_txt_content` (header CSV + linha de dados + tail não-truncado)
3. Verifica ratio `txt_total / 7z_size >= 1,5`

Todas as três camadas operam **no arquivo extraído no Volume** — antes do CSV reader. Não há nenhuma validação da **tabela bronze resultante**.

### Onde o gate de qualidade deve estar

A pergunta do briefing é: gate pós-bronze pertence ao bronze ou ao silver? A resposta correta é **ambos, com responsabilidades distintas**:

**Bronze é responsável por:**
- Verificar que o que foi lido pelo CSV reader é compatível com o schema declarado
- Detectar NULL ratio anômalo nas colunas que deveriam ser NOT NULL para ser um vínculo válido (ex.: `sexo_trabalhador`, `cbo_ocupacao`, `vinculo_ativo_31_12`)
- Essa verificação deve falhar o pipeline, não apenas logar

**Silver é responsável por:**
- DQ rules de negócio (valores fora de domínio, CNPJs inválidos, datas impossíveis)
- Coalescing de colunas `_dupN`, normalização de schema cross-ano

**O que deveria existir no bronze (e não existe):**

```python
# Gate pós-bronze: verifica NULL ratio em colunas críticas para ano=2023+
# Falha o pipeline se > 90% das linhas de qualquer ano/arquivo tiver
# todas as colunas de dados NULL (sinal de separador errado)

df_check = spark.read.table(BRONZE_TABLE).filter(F.col("ano") >= 2018)
null_ratio = df_check.groupBy("ano", "_source_file").agg(
    F.count("*").alias("total"),
    (F.sum(F.when(F.col("cbo_ocupacao").isNotNull(), 1).otherwise(0)) / F.count("*")).alias("pct_cbo_filled"),
    (F.sum(F.when(F.col("sexo_trabalhador").isNotNull(), 1).otherwise(0)) / F.count("*")).alias("pct_sexo_filled"),
)
broken = null_ratio.filter(
    (F.col("pct_cbo_filled") < 0.01) &
    (~F.col("_source_file").like("%ESTAB%"))  # excluir ESTAB explicitamente
)
broken_count = broken.count()
if broken_count > 0:
    broken.show(20, truncate=False)
    raise RuntimeError(
        f"BRONZE DATA QUALITY GATE FAILURE: {broken_count} arquivo(s) com "
        f"<1% de colunas de vínculo preenchidas. Separador incorreto ou schema drift. "
        f"Verifique Issues A/C no briefing de auditoria."
    )
```

**Por que esse gate NÃO substitui a validação de arquivo:** o gate de arquivo (HEAD/TAIL/ratio) detecta corrupção de extração (arquivo truncado, blocos LZMA corrompidos). O gate pós-bronze detecta problemas semânticos do CSV reader (separador errado, encoding errado, header drift). São camadas complementares. A lacuna atual é que a segunda camada não existe.

**Custo do gate:** para 40 anos de dados, rodar sobre a tabela inteira a cada execução é caro. A solução pragmática é rodar o gate apenas sobre `ano >= MAX(ano) - 1` após cada ingest, ou manter uma tabela de metadados de qualidade (`_bronze_dq_metrics`) atualizada incrementalmente.

---

## Avaliação STRING-ONLY + mergeSchema + snake_case + `_dupN`

### STRING-ONLY (`inferSchema=false`)

Correto e respeitado. Linha 1041: `option("inferSchema", "false")`. Nenhuma coerção de tipo no bronze. A=OK.

### `mergeSchema=true`

Correto conceitualmente — a RAIS tem schema drift real (42 colunas 1985, ~60 em 2023+). O risco é que `mergeSchema=true` aceita silenciosamente schema drift malicioso (ex.: PDET renomeia coluna existente → coluna antiga vira NULL, nova coluna aparece com outro nome). Não há gate que detecta "coluna que existia e agora sumiu do header". Para 40 anos de dados históricos onde o schema muda, isso é aceitável, mas deve ser documentado em ADR.

### `_dupN` para colisões de sanitização

Design correto. `municipio` + `municipio_dup2` preserva ambos sem perda. Silver pode fazer `COALESCE(municipio, municipio_dup2)` com segurança. O risco é proliferação: se uma coluna tiver 3-4 variações de nome cross-ano, você terá `municipio`, `municipio_dup2`, `municipio_dup3`, `municipio_dup4`. Silver precisa conhecer todas para o coalesce. Sem COMMENT nas colunas (Issue E), o silver developer não tem contexto sobre qual `_dupN` veio de qual header original.

**Risco concreto não mitigado:** `_dupN` é gerado com índice sequencial baseado na ordem de aparição no schema do Auto Loader. Se o schema location for re-criado (por `force_reconvert=true`), a ordem pode mudar e os índices `_dup2`/`_dup3` podem ser atribuídos a colunas diferentes entre runs. Isso quebraria silenciosamente qualquer lógica silver que hardcode `municipio_dup2` como "o Município de 2019+".

---

## Plano de correção priorizado

### P1 — Corrija o bug de separador (CRÍTICO, executar PRIMEIRO)

**Tipo:** PATCH no código + DROP+REINGEST de ano=2023 e ano=2024.

**Risco:** DROP de 99,5 M de linhas corrompidas (não há dado útil nelas — são todas NULL exceto `bairros_sp`). O risco real é garantir que a extração aconteça antes do DROP para não perder a janela temporal.

**Comandos:**

```python
# 1. Alterar pipeline: detectar separador por extensão
def _detect_sep(path: str) -> str:
    """Retorna separador correto pelo padrão de filename.
    .COMT = formato PDET 2023+, CSV com ','
    .txt  = formato PDET 1985–2022, CSV com ';'
    """
    return "," if path.lower().endswith(".comt") else ";"

# No step 2, em vez de .option("sep", ";") fixo:
# Para batch, é necessário ler .txt e .COMT separadamente,
# ou usar um UDF de parse (CSV com sep variável não é suportado
# em uma única chamada spark.read.csv).
# Solução mais simples: duas leituras com union:

READ_PATH_TXT  = f"{TXT_EXTRACTED}/ano=*/*.txt"
READ_PATH_COMT = f"{TXT_EXTRACTED}/ano=*/*.COMT"

df_txt = _sanitize_columns(_add_ano_from_path(
    spark.read.option("header","true").option("sep",";")
         .option("encoding","latin1").option("inferSchema","false")
         .csv(READ_PATH_TXT)
))
df_comt = _sanitize_columns(_add_ano_from_path(
    spark.read.option("header","true").option("sep",",")
         .option("encoding","latin1").option("inferSchema","false")
         .csv(READ_PATH_COMT)
))
# mergeSchema via union — alinha por nome (não por posição)
df = df_txt.unionByName(df_comt, allowMissingColumns=True)
```

**Para Auto Loader:** Auto Loader não suporta sep dinâmico por arquivo. A solução para incremental é usar dois streams separados com checkpoints distintos (um para `.txt`, outro para `.COMT`), ou pre-processar `.COMT` para converter separador antes de jogar no Volume lido pelo Auto Loader.

**DROP+REINGEST de 2023–2024:**

```sql
-- Verificar antes de deletar
SELECT ano, COUNT(*) FROM mirante_prd.bronze.rais_vinculos
WHERE ano >= 2023 GROUP BY ano;

-- Deletar partições corrompidas
ALTER TABLE mirante_prd.bronze.rais_vinculos
DROP PARTITION (ano=2023);
ALTER TABLE mirante_prd.bronze.rais_vinculos
DROP PARTITION (ano=2024);

-- Verificar que SP 2024 está no Volume antes de re-ingestar
-- databricks fs ls /Volumes/mirante_prd/bronze/raw/mte/rais_txt_extracted/ano=2024/

-- Re-ingestar com pipeline corrigido (batch mode para essas partições)
-- Usar force_reconvert=false com patch cirúrgico de ano=2023+2024
```

**Ordem de execução:** (a) commitar fix de separador, (b) verificar que SP.COMT está no Volume, (c) DROP partições 2023–2024, (d) rodar pipeline com batch mode apenas para 2023–2024, (e) executar gate pós-bronze para confirmar NULL ratio < 1%.

---

### P2 — Corrija Issue B (SP 2024 ausente) junto com P1

**Tipo:** garantir que SP.COMT entre no reingest de P1.

**Ação:** antes do DROP+REINGEST, confirmar que `/Volumes/mirante_prd/bronze/raw/mte/rais_txt_extracted/ano=2024/RAIS_VINC_PUB_SP.COMT` existe e tem `6,252,611,145 bytes`. Se sim, o reingest batch de P1 vai pegar o arquivo. Se não, verificar se o marker `.done` de SP_2024 existe e, se existir com conteúdo incorreto, deletá-lo para forçar re-extração.

**Para runs futuras:** adicionar ao Step 2 uma verificação de tamanho mínimo esperado por ano (p.ex., SP deve ter > 5 GB por ser o maior arquivo). Se o arquivo existir no Volume mas for menor que threshold, logar warning antes de processar. Não é trivial de implementar genericamente, mas é possível como ADR + regra de negócio.

---

### P3 — Limpe ESTAB da tabela bronze (ALTO)

**Tipo:** DELETE + VACUUM (não é DROP+REINGEST completo).

**Ação:**

```sql
-- Deletar linhas ESTAB de bronze.rais_vinculos
DELETE FROM mirante_prd.bronze.rais_vinculos
WHERE _source_file LIKE '%ESTAB%'
   OR _source_file LIKE '%ESTB%';

-- Após delete, OPTIMIZE + VACUUM para recuperar espaço
OPTIMIZE mirante_prd.bronze.rais_vinculos;
VACUUM mirante_prd.bronze.rais_vinculos RETAIN 168 HOURS;
```

**Risco:** DELETE em tabela de 2,2 B de linhas gera Z-ordering overhead. Estimar: ~75 M de linhas ESTAB = ~3,4% da tabela. O DELETE deve ser rápido com partition pruning se `_source_file` está correlacionado com `ano` (que é partição). Validar que ano=2022 com `RAIS_ESTAB_PUB.txt.txt` é deletado corretamente.

**Prevenção futura:** adicionar filtro explícito no Auto Loader READ_PATH ou via `pathGlobFilter`:

```python
.option("pathGlobFilter", "RAIS_VINC_*.{txt,TXT,COMT}")
```

Isso garante que somente arquivos com nome VINC entram no reader, independente do que está no Volume.

---

### P4 — Adicione gate pós-bronze (CRÍTICO para detecção futura)

**Tipo:** PATCH — novo command no notebook após o writeStream.

Implementar a query de NULL ratio mostrada acima na seção "Análise do Quality Check". Critérios:
- Rodar apenas sobre anos recentes (`MAX(ano) - 1` a `MAX(ano)`) para eficiência
- Falhar com `raise RuntimeError` se NULL ratio > 90% em colunas de vínculo críticas
- Logar métricas em tabela `mirante_prd.bronze._dq_rais_vinculos` para histórico

---

### P5 — UC metadata obrigatório (PADRÃO)

**Tipo:** PATCH — adicionar ao final do notebook.

```python
# Mínimo obrigatório — expandir com descrições verbosas de cada coluna
spark.sql(f"""
    COMMENT ON TABLE {BRONZE_TABLE} IS
    'RAIS Vínculos Públicos — bronze STRING-ONLY. Grain: 1 linha = 1 contrato
     de trabalho (vínculo empregatício ativo ou encerrado no ano-calendário).
     Período: 1985–presente. Fonte: PDET/MTE FTP ftp.mtps.gov.br.
     Obs: separador ; (1985–2022) e , (2023+, extensão .COMT).
     Schema drift por ano: colunas adicionadas em mergeSchema=true; _dupN = colisões
     de sanitização cross-ano. Linhas ESTAB filtradas (grain diferente; ver bronze.rais_estab).
     Não usar COUNT(*) sem filtrar _source_file UNLIKE ESTAB (ver Issue C no ADR-001-rais-bronze).'
""")

for col_name, comment in [
    ("bairros_sp", "Código do bairro (São Paulo). Header drift: 1985–2017 presente em todos os UFs; 2018+ apenas no arquivo SP."),
    ("motivo_desligamento", "Código do motivo de desligamento do vínculo. NULL = vínculo ativo em 31/12 ou linha ESTAB."),
    ("cbo_ocupacao", "CBO 2002 — Código Brasileiro de Ocupações. Presente 2003+. NULL em anos anteriores é correto."),
    ("sexo_trabalhador", "1=Masculino, 3=Feminino (codificação PDET/RAIS, não sequencial). PII: indireto."),
    ("vinculo_ativo_31_12", "1 se vínculo estava ativo em 31/12 do ano-calendário. Coluna mais importante para contar empregos formais."),
    # ... continuar para as 51 colunas
]:
    spark.sql(f"ALTER TABLE {BRONZE_TABLE} ALTER COLUMN {col_name} COMMENT '{comment}'")

# TAGs obrigatórias de plataforma
for k, v in [
    ("layer",  "bronze"),
    ("domain", "trabalho"),
    ("source", "mte_pdet_rais"),
    ("pii",    "indirect"),   # CNPJ + remuneração = potencialmente identificável
    ("grain",  "vinculo_ano"),
]:
    spark.sql(f"ALTER TABLE {BRONZE_TABLE} SET TAGS ('{k}' = '{v}')")
```

---

### P6 — Issue D: SP 1986 (DEFERIR com documentação)

**Tipo:** DEFER — fonte corrompida no FTP PDET. Não há ação imediata viável.

**Ação necessária:**
1. Adicionar comentário na tabela: "SP 1986 ausente: arquivo SP1986_1986.7z corrompido no FTP PDET após 2 tentativas de re-download. Investigar via IPEA Data ou arquivo institucional MTE."
2. Silver deve ter regra documentada: `WHERE ano = 1986 AND uf = 'SP'` retorna zero linhas intencionalmente.
3. Qualquer publicação que use série 1985–2024 deve declarar essa limitação.

---

## ADRs ausentes e necessários

### ADR-001: Tratamento de drift de extensão e separador da fonte PDET

**Contexto:** PDET mudou extensão de `.txt` para `.COMT` e separador de `;` para `,` em 2023. Essa mudança não foi antecipada. O pipeline hardcodava `sep=";"`.

**Decisão:** detectar separador por extensão de arquivo. `.COMT` = `,`, `.txt` = `;`. Implementar duas leituras batch com `unionByName(allowMissingColumns=True)`. Para Auto Loader, manter dois streams com checkpoints distintos.

**Consequências:** complexidade aumenta (dois caminhos de leitura). Benefício: formato correto garantido sem depender de detecção heurística de conteúdo.

**Alternativa rejeitada:** auto-detect de separador via amostra do arquivo. Frágil para arquivos onde o separador pode ocorrer dentro de campos de texto (ex.: campo de nome com vírgula).

---

### ADR-002: Gate de qualidade pós-bronze para NULL ratio de colunas críticas de vínculo

**Contexto:** Issue A passou silenciosamente pelo quality check de arquivo (bypass para `.COMT`). O único gate existente valida o arquivo extraído, não o output do CSV reader.

**Decisão:** adicionar gate pós-bronze que verifica NULL ratio em colunas críticas de vínculo (`cbo_ocupacao`, `sexo_trabalhador`, `vinculo_ativo_31_12`) por combinação (`ano`, `_source_file`). Threshold: arquivos não-ESTAB com < 1% de preenchimento em todas as três colunas falham o pipeline.

**Implementação:** query Delta SQL após o `writeStream.awaitTermination()`. Para eficiência, filtrar apenas anos recentes (`>= MAX(ano) - 1`). Logar métricas em tabela de DQ.

**Responsabilidade de camada:** bronze é responsável por refletividade (o que entrou no arquivo chegou na tabela com schema correto). Silver é responsável por regras de negócio. NULL ratio de 100% não é regra de negócio — é sinal de falha de leitura. Portanto é responsabilidade do bronze detectar.

---

### ADR-003: Grain isolation — bronze.rais_vinculos é VINC-only

**Contexto:** ESTAB e VINC chegam no mesmo Volume após extração de `.7z` PDET. O filtro no passo de extração não cobre arquivos que chegaram antes do filtro existir.

**Decisão:** adicionar `pathGlobFilter` no Auto Loader e no batch reader para garantir que apenas arquivos com nome `RAIS_VINC_*` entram no CSV reader. Executar DELETE cirúrgico de linhas ESTAB históricas da tabela bronze. Criar `bronze.rais_estab` separado quando necessário.

**Consequência:** grain da tabela bronze passa a ser garantido por contrato, não apenas por intenção.

---

### ADR-004: Política de quarentena e série histórica incompleta

**Contexto:** SP 1986 está em quarentena permanente. FTP PDET serve arquivo corrompido. Pipeline auto-recovery falhou.

**Decisão:** aceitar o gap, documentar na tabela via COMMENT e em artigo científico como limitação conhecida. Não bloquear ingest do restante da série por esse arquivo.

**Critério de reabertura:** se fonte alternativa (IPEA, IBGE, arquivo MTE) for identificada, restaurar via `force_reconvert=true` + ingest patch apenas de SP 1986.

---

## Resumo de scoring por dimensão

| Dimensão | Nota | Justificativa |
|---|---|---|
| Arquitetura de idempotência | B+ | Markers, reconciliação, cleanup de parciais: bem feito |
| Correção do output bronze | D | 197 M de linhas corrompidas ou ausentes em 2023–2024 |
| Isolamento de grain | C | ~75 M de linhas ESTAB contaminando tabela VINC |
| Quality gates | C | Gate de arquivo existe; gate pós-bronze ausente; falhou silenciosamente em Issue A |
| STRING-ONLY | A | Respeitado sem exceção |
| Unity Catalog metadata | D | Zero COMMENTs, TAGs de plataforma ausentes |
| Auto-recovery e resiliência | B+ | FTP redownload + quarentena bem implementados |
| Documentação inline | B | Comentários detalhados no código; mas ADRs ausentes |

**Nota global: C+ (1,5 pts) — abaixo do limiar de aprovação de 2,0**

---

## Três ações prioritárias

**P1 (esta semana):** Corrigir `sep` hardcoded — implementar leitura dual (`.txt` com `;`, `.COMT` com `,`) + `unionByName(allowMissingColumns=True)` no batch reader. Adicionar `pathGlobFilter("RAIS_VINC_*.{txt,TXT,COMT}")` para isolar grain. Fazer DROP das partições `ano=2023` e `ano=2024` e re-ingestar com pipeline corrigido. Verificar que SP.COMT (6,2 GB) está no Volume antes do DROP.

**P2 (esta semana, junto com P1):** Adicionar gate pós-bronze com NULL ratio check em `cbo_ocupacao`, `sexo_trabalhador`, `vinculo_ativo_31_12` — falha `raise RuntimeError` se > 90% NULL em arquivo não-ESTAB. Executar DELETE cirúrgico de linhas ESTAB (`_source_file LIKE '%ESTAB%'`) + OPTIMIZE + VACUUM.

**P3 (antes de qualquer publicação):** Preencher COMMENTs verbosos nas 51 colunas + TAGS de plataforma (`layer=bronze`, `domain=trabalho`, `source=mte_pdet_rais`, `pii=indirect`, `grain=vinculo_ano`) + escrever os 4 ADRs acima. Sem isso, qualquer desenvolvedor de silver trabalha no escuro.

---

*Parecer emitido por: Conselheiro de Eng. Software & Plataforma de Dados*
*Data: 2026-04-28*
*Pipeline auditado: `pipelines/notebooks/bronze/rais_vinculos.py` (commit b6df45d)*

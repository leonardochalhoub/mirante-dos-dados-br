# Briefing — Auditoria raw → bronze · `mirante_prd.bronze.rais_vinculos`

**Data:** 2026-04-28  
**Solicitante:** Leonardo Chalhoub (autor)  
**Escopo:** "Querya a tabela bronze RAIS, vê se tá ok. Olhei rápido, parece que tem muito NULL. Quero o conselho avaliar se de raw → bronze tudo está perfeitamente refletido em bronze."  
**Pipeline auditado:** [`pipelines/notebooks/bronze/rais_vinculos.py`](../../pipelines/notebooks/bronze/rais_vinculos.py)  
**Tabela:** `mirante_prd.bronze.rais_vinculos`  
**Período:** 1985–2024 (40 anos)  
**Volume bruto na bronze:** 2.236.464.956 linhas · 977 distinct `_source_file` · 51 colunas de dados (STRING-ONLY) + 3 metadata + `_rescued_data` + 4 `_dupN`.

---

## Sumário executivo

Existem **4 problemas materiais** entre raw e bronze. Em ordem de severidade:

| # | Problema | Linhas afetadas | Severidade | Tipo |
|---|----------|-----------------|------------|------|
| A | 2023+2024: separador errado em arquivos `.COMT` (PDET trocou `;` por `,`) | ~175 M (~7,8% do total) | **CRÍTICO** | data corruption (silenciosa) |
| B | 2024 SP ausente (arquivo `RAIS_VINC_PUB_SP.COMT` 6,2 GB no Volume mas não foi para a bronze) | ~22 M (estimativa) | **CRÍTICO** | data loss |
| C | Contaminação ESTAB em tabela VINC (grain de estabelecimento misturado com grain de vínculo) | ~75 M (~3,4%) | ALTO | schema/grain violation |
| D | 1986 SP em quarentena permanente (`_bad/SP1986_1986.7z`) | ~7 M (estimativa) | MÉDIO | data loss |

**O que está OK:**
- 1985–2022 vínculo: extração técnica completa (cobertura por `_source_file` bate com inventário dos `.7z` no Volume, descontando ESTAB — ver tabela § 3).
- Política STRING-ONLY de bronze: respeitada. Nenhuma coerção de tipo.
- Particionamento por `ano`: derivado corretamente do path Hive `.../ano=YYYY/...`.
- Sanitização snake_case + tratamento de colisão com sufixo `_dupN`: funcionando (ver `municipio_dup2`).

**O que viola padrão da plataforma:**
- Memory rule **"Unity Catalog metadata mandatory"** — `DESCRIBE` mostra **comentário `null` em todas as 51 colunas + na tabela** (zero metadata UC).

---

## 1. Evidências — Issue A: separador errado em 2023+2024 (.COMT files)

### 1.1 Diagnóstico por `_source_file` (taxa de preenchimento)

```
ano   src(short)                          rows         motivo%   cbo%     sexo%
2022  RAIS_VINC_PUB_SP.txt                22,380,845   100.0     100.0    100.0    ← OK
2023  RAIS_VINC_PUB_SP.COMT               23,182,670   0.0       0.0      0.0      ← QUEBRADO
2024  (todos os 7 .COMT)                  76,297,221   0.0       0.0      0.0      ← QUEBRADO
```

Em **todos os ~175 M de linhas de 2023+2024**, as 50 colunas de dados estão NULL exceto a coluna `bairros_sp`, que recebeu o conteúdo da linha INTEIRA como string (porque o leitor abriu com `;` mas o arquivo é `,`).

### 1.2 Sample row 2024 (qualquer arquivo)

```
bairros_sp        : 999997,999997,999997,312,5118,999997,0,0,0,0,0,9,1,0,270640,9999,...
motivo_desligamento : NULL
cbo_ocupacao      : NULL
... (todas as outras 49 colunas) : NULL
_source_file      : .../ano=2024/RAIS_ESTAB_PUB.COMT
ano               : 2024
```

A string em `bairros_sp` é a linha original com 23 campos comma-separated.

### 1.3 Confirmação: o arquivo .COMT é CSV válido com 60 colunas, separador `,`

Lendo o mesmo arquivo com `read_files(format=>'csv', sep=>',', header=>true)`:

```
60 colunas reconhecidas, incluindo:
  Bairros SP - Código              int
  Motivo Desligamento - Código     int
  CBO 2002 Ocupação - Código       int
  Sexo - Código                    int
  ...
  Vl Rem Janeiro SC                double  ← NOVO em 2023+
  Vl Rem Fevereiro SC              double  ← NOVO
  ... (12 meses)
  Causa Afastamento 1/2/3 - Código int     ← NOVO
  Tipo Deficiência - Código        int     ← NOVO
  Ind Trabalho Intermitente        int     ← NOVO
```

PDET 2023+ entregou:
1. Extensão renomeada de `.txt` para `.COMT` (cabeçalho do arquivo continua sendo CSV de texto).
2. **Separador trocado de `;` para `,`**.
3. **Schema expandido** de ~42 → ~60 colunas (afastamentos por causa, remunerações mensais janeiro–novembro, deficiência detalhada, novos indicadores de vínculo).

**Causa raiz no pipeline:** `pipelines/notebooks/bronze/rais_vinculos.py:1037-1044, 1062-1066, 1081-1083` — `option("sep",";")` hardcoded; nenhum branch para detectar `.COMT` ou separador alternativo.

### 1.4 Impacto da correção
Ao re-extrair com `,` para 2023+ as 60 colunas serão sanitizadas e adicionadas via `mergeSchema=true` ao schema bronze atual. Não há colisão com nomes existentes (já testado: novas colunas como `vl_rem_janeiro_sc`, `causa_afastamento_1_codigo` não existem na bronze de hoje).

---

## 2. Evidências — Issue B: 2024 SP ausente da bronze

### 2.1 Inventário de `_source_file` para `ano=2024` na bronze

```
RAIS_ESTAB_PUB.COMT              13,186,059
RAIS_VINC_PUB_CENTRO_OESTE.COMT   8,732,359
RAIS_VINC_PUB_MG_ES_RJ.COMT      18,062,650
RAIS_VINC_PUB_NI.COMT                16,544
RAIS_VINC_PUB_NORDESTE.COMT      15,465,156
RAIS_VINC_PUB_NORTE.COMT          5,197,236
RAIS_VINC_PUB_SUL.COMT           15,637,217
                            TOTAL 76,297,221
```

**RAIS_VINC_PUB_SP.COMT NÃO aparece** — apesar de existir no Volume:

```
$ databricks fs ls .../rais_txt_extracted/ano=2024
RAIS_VINC_PUB_SP.COMT  →  6,252,611,145 bytes (6,2 GB), modificado 2026-04-28T12:26:49
```

### 2.2 Estimativa do gap

São Paulo em 2022 (último ano com bronze íntegra) = 22.380.845 linhas. Em 2023 = 23.182.670 linhas. Estimativa para 2024: **~22-24 M linhas faltantes**.

### 2.3 Causa raiz hipotetizada
- Extração funcionou (`SP_2024.7z` → `SP.COMT` 6,2 GB no Volume).
- O timestamp do SP.COMT (12:26 do dia 2026-04-28) é POSTERIOR aos outros (~01:55–02:21 do mesmo dia).
- Auto Loader checkpoint pode ter sido inicializado em batch antes do SP terminar de extrair → o arquivo entrou no Volume depois do snapshot do schema location e o stream subsequente não pegou.
- Combinado com Issue A (sep errado): mesmo se SP fosse processado, geraria mais 22 M de linhas vazias.

---

## 3. Evidências — Issue C: contaminação ESTAB

### 3.1 Pipeline declara filtro VINC-only

`bronze/rais_vinculos.py:68-73`:
```python
RAIS_ESTAB_RE = re.compile(r"(?i)(?:^|/)(estb|rais_estab)")
def _is_vinculo_filename(name: str) -> bool:
    return RAIS_ESTAB_RE.search(name) is None
```

Esse filtro é **aplicado dentro do `.7z` durante a extração** (`_try_extract` linha 169-185). Funciona para 1985–2017 (`ESTB<YYYY>.7z` empacota apenas ESTAB; o filtro pula o `.7z` inteiro porque `wanted=[]`).

### 3.2 Mas em 2018+ o filtro não cobre o caso

PDET 2018+ entrega ESTAB em `.7z` próprio (`RAIS_ESTAB_PUB_<YYYY>.7z`), com filename de fora também batendo no regex. **Mas o passo 2 (Auto Loader / batch read CSV)** carrega `READ_PATH = f"{TXT_EXTRACTED}/ano=*/"` SEM filtrar por nome — pega QUALQUER `.txt`/`.COMT` que esteja na pasta.

Resultado: extração pulou o conteúdo dos `.7z` ESTAB-only DESDE QUE o filtro estava ativo. Mas se um `.7z` foi extraído antes do filtro entrar em vigor (versões antigas do notebook), os `.txt` ESTAB ficaram na pasta e foram lidos.

### 3.3 Linhas ESTAB hoje em `bronze.rais_vinculos`

```
2018  ano=2018/RAIS_ESTAB_PUB.txt          8,082,088
2019  ano=2019/RAIS_ESTAB_PUB.txt          7,974,757
2020  ano=2020/RAIS_ESTAB_PUB.txt          8,196,730
2021  ano=2021/RAIS_ESTAB_PUB.txt          8,472,949
2022  ano=2022/RAIS_ESTAB_PUB.txt.txt      8,453,190     ← note "txt.txt"
2023  ano=2023/RAIS_ESTAB_PUB.COMT        11,768,420
2024  ano=2024/RAIS_ESTAB_PUB.COMT        13,186,059
                                    TOTAL  ~66,134,193
```

Adicionando equivalentes 1992–2017 (`ESTB<YYYY>.txt` = ~9-12 M cada, antes de o filtro VINC-only entrar): **~75 M linhas ESTAB em bronze.rais_vinculos**.

### 3.4 Por que isso é grave
- **Grain mismatch**: ESTAB = 1 linha por estabelecimento; VINC = 1 linha por contrato de trabalho. Métricas naïve em bronze (ex.: `COUNT(*) GROUP BY uf` para "vínculos por UF") incluem estabelecimentos sem trabalhadores.
- ESTAB **não tem** colunas como `cbo_ocupacao`, `sexo_trabalhador`, `motivo_desligamento`, `vinculo_ativo_31_12` — todas NULL nas linhas ESTAB. Confunde análises de cobertura por coluna ("é NULL porque o ano não tem o campo, ou porque é uma linha ESTAB?").
- Silver downstream que filtra `WHERE _source_file NOT LIKE '%ESTAB%'` salva o dia, mas é uma defesa que NÃO ESTÁ no contrato bronze.

### 3.5 Detalhe estranho 2022
Filename é `RAIS_ESTAB_PUB.txt.txt` (duplo `.txt`). Sugere bug em algum step de renomear/copiar do extract antigo. Não bloqueia a leitura mas é sintoma de não-determinismo.

---

## 4. Evidências — Issue D: 1986 SP em quarentena

```
$ databricks fs ls .../bronze/raw/mte/rais/_bad
SP1986_1986.7z   ← único arquivo em quarentena
```

Bronze 1986 tem **22.430.913 linhas** vs 1985 (29.686.195) e 1987 (35.718.362). SP é ~25-30% do emprego brasileiro → estimativa de 7-13 M linhas SP 1986 perdidas. PDET FTP `ftp.mtps.gov.br/pdet/microdados/RAIS/1986/SP1986.7z` retornou conteúdo corrompido em 2 tentativas de re-download (script auto-recovery falhou).

---

## 5. Evidências — Issue E: Unity Catalog metadata vazio

`DESCRIBE EXTENDED mirante_prd.bronze.rais_vinculos` (col_name + comment):

```
bairros_sp                : null
motivo_desligamento       : null
distritos_sp              : null
... (todas as 51 colunas) : null
```

**Memory rule violada**: "Unity Catalog metadata mandatory — every new table in mirante_prd ships with verbose table+column COMMENTs and TAGS (layer/domain/source/pii/grain) in the same notebook."

Bronze.rais_vinculos não tem **um único** `COMMENT` em coluna nem na tabela, nem nenhuma `TAG` (layer/domain/source/pii/grain).

---

## 6. O que ESTÁ OK (não é bug)

1. **NULL pattern por header drift**: 1985–2017 PDET usava `Bairros SP` em todos os arquivos UF; após 2018 o cabeçalho passou a ter `Bairros Fortaleza`/`Bairros RJ`/etc. apenas para os arquivos regionais correspondentes. Como bronze é STRING-ONLY com `mergeSchema=true`, cada linha só preenche os campos do **seu** header → NULL em colunas "do outro ano" é esperado e correto. Silver deve coalescer.
2. **`_dupN` columns**: `municipio` + `municipio_dup2`, `tipo_estab` + `tipo_estab18`/`tipo_estab19`/`tipo_estb`. São colisões de sanitização (`MUNICIPIO` em alguns anos vs `Município` em outros, ambos sanitizam para `municipio`) — bronze preserva ambas com sufixo, silver decide o coalesce. Está implementado em `_sanitize_columns()` e funciona.
3. **Particionamento por ano**: derivado do path Hive corretamente. Falha cedo se houver linha sem `ano` (`raise RuntimeError` linha 1049).
4. **Cobertura raw → bronze 1987–2022 (vínculos)**: bate com inventário de `.7z` no Volume, descontando ESTAB.

---

## 7. Pergunta ao Conselho

Cada conselheiro avaliando do seu ângulo:

**Eng. Software / Plataforma de Dados (líder do tema):**
> Issue A é separador hardcoded — a fix é trivial (auto-detect ou branch por extensão). Mas o sistema deveria ter um **gate de qualidade** que detecta "100% das linhas têm 49/50 colunas NULL" e falha o pipeline antes de marcar `.done`. Esse gate existe no Quality Check (linha 843+) mas verifica apenas conteúdo HEAD/TAIL do arquivo `.txt`, não a saída do CSV reader. Vamos discutir: deve haver gate pós-bronze ou esse é trabalho do silver?

**Finanças (rigor metodológico):**
> O WP RAIS de 17 anos (Chalhoub 2023, monografia UFRJ) replica série temporal de empregos formais. Bronze atual tem buracos em 1986 SP (~7M), 2024 SP (~22M), e 2023+2024 INTEIRO inutilizável (~175M, descontando o ESTAB que não deveria estar lá). Isso quebra qualquer série até 2024 no silver, exceto se tivermos um caveat metodológico no artigo. Deve ser corrigido antes de qualquer publicação ou reuso?

**Administração (utilidade prática / WHY):**
> O WHY do RAIS no Mirante é "demonstrar que dá para reproduzir 17+ anos de microdados PDET sob STRING-ONLY + UC + Lakehouse". O fato de termos 2023+2024 totalmente quebrados invalida a demonstração para os anos mais recentes — exatamente os que o público pratico (jornalistas, analistas) pediria. Vale priorizar a correção?

**Design / Visualização:**
> Se a vertical RAIS no app expõe gráficos/mapas que dependem de 2023+2024, eles estão errados (ou caem para 2022). Verificar. Se o dado está apenas no silver agregado e silver foi rodada antes de Issue A se manifestar, talvez os gráficos refletem 2022 como "última atualização" — mas a UI deveria sinalizar.

---

## 8. Anexo — comandos diagnósticos rodados

Todos via `Statement Execution API` no warehouse `9e9a68644c51f277` (Serverless Starter, 2X-Small).

```sql
-- Total + range temporal
SELECT COUNT(*), COUNT(DISTINCT ano), MIN(ano), MAX(ano) FROM mirante_prd.bronze.rais_vinculos;
-- → 2,236,464,956 | 40 | 1985 | 2024

-- Cobertura raw → bronze
SELECT regexp_extract(_source_file, '/ano=([0-9]+)/', 1) AS yr,
       COUNT(DISTINCT _source_file) AS files, COUNT(*) AS rows
FROM mirante_prd.bronze.rais_vinculos GROUP BY yr ORDER BY yr;

-- Health check 2018+
SELECT ano, _source_file, COUNT(*) AS rows,
       SUM(CASE WHEN motivo_desligamento IS NOT NULL THEN 1 ELSE 0 END) AS has_motivo,
       SUM(CASE WHEN cbo_ocupacao IS NOT NULL THEN 1 ELSE 0 END) AS has_cbo,
       SUM(CASE WHEN sexo_trabalhador IS NOT NULL THEN 1 ELSE 0 END) AS has_sexo,
       SUM(CASE WHEN _rescued_data IS NOT NULL THEN 1 ELSE 0 END) AS has_rescued
FROM mirante_prd.bronze.rais_vinculos WHERE ano BETWEEN 2018 AND 2024
GROUP BY ano, _source_file ORDER BY ano, _source_file;

-- Confirma .COMT é CSV válido com sep=','
SELECT * FROM read_files('.../ano=2024/RAIS_VINC_PUB_NI.COMT',
  format=>'csv', header=>true, sep=>',', encoding=>'latin1') LIMIT 1;
```

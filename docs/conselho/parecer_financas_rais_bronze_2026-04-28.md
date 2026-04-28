# Parecer — Conselheiro de Finanças e Métodos Quantitativos
## Auditoria raw → bronze · `mirante_prd.bronze.rais_vinculos`

**Versão avaliada:** pipeline `pipelines/notebooks/bronze/rais_vinculos.py` · tabela auditada em 2026-04-28  
**Escopo:** bronze como fonte para análise quantitativa e manuscritos peer-reviewed  
**Score atribuído:** C (1,0 pt) — **INAPTIDÃO PARA INFERÊNCIA, MAJOR REVISION obrigatória**  
**Histórico:** primeira auditoria formal desta camada (não há histórico anterior)  
**Régua:** mestrado stricto sensu (B = 2,0 é o limiar de aprovação)

---

## Veredicto geral

A `bronze.rais_vinculos` na configuração auditada em 2026-04-28 **não sustenta qualquer análise quantitativa séria que inclua 2023 ou 2024**, e tampouco sustenta análises cross-seccional ou de série temporal que ignorem a contaminação ESTAB (Issues A+C). O pipeline de ingestão hardcodeia o separador `;` quando o PDET silenciosamente trocou para `,` a partir de 2023 — resultando em 175 milhões de linhas com 50 colunas NULL, sem qualquer gate de qualidade pós-leitura disparando alarme. A tabela declara 2.236 B linhas de cobertura histórica mas carrega ~280M linhas inválidas, corrompidas ou de grain errado: ~12,5% de ruído estrutural não-documentado. Para uma fonte canônica que downstream passa direto para silver/gold e eventualmente para manuscritos, isso é inaceitável.

---

## 1. Severidade para inferência — estado atual da bronze

### 1.1 Mapa de confiabilidade por janela temporal

| Janela | Status | Usável para causalidade? |
|--------|--------|--------------------------|
| 1985 | OK (cobertura bate raw) | Sim, com ressalva SP86 vizinho |
| 1986 (sem SP) | D em quarentena | Séries SP truncadas; DiD/RDD cruzados com SP 1986 inviáveis |
| 1987–2017 | OK (descontando ESTAB ~9-12M/ano) | Sim, se silver filtra ESTAB corretamente |
| 2018–2022 | OK para vínculos puros; ESTAB ~8M/ano presente | Sim, SE silver tem filtro `_source_file NOT LIKE '%ESTAB%'` |
| 2023 | INTEIRO corrompido (sep errado): 0% preenchimento | **Não** |
| 2024 (sem SP) | INTEIRO corrompido + SP ausente | **Não** |

Isso é o oposto de uma "data quality issue marginal". Para qualquer artigo que queira estender a análise ao governo Lula 3 (2023+) ou ao mercado de trabalho pós-pandemia tardio (2022–2024), a bronze no estado atual gera resultados fabricados via omissão de dado — não porque o script mente, mas porque o leitor não detecta que as 175M linhas de 2023+2024 são lixo estruturado.

### 1.2 Nota e justificativa

Score **C (1,0 pt)**. A bronze ganha crédito por:
- Boa cobertura 1987–2022 (vínculos), confirmada pelo inventário de `_source_file` vs `.7z` no Volume.
- Política STRING-ONLY corretamente aplicada — nenhuma coerção de tipo que distorceria distribuições downstream.
- Particionamento por `ano` derivado do Hive path — facilita auditor identificar o problema por janela.
- Auto Loader + `mergeSchema=true` — infraestrutura correta para schema drift futuro.

Perde crédito por:
- Issue A (175M linhas silenciosamente corrompidas) é falha de ingestão com impacto direto em validade interna.
- Issue C (~75M linhas de grain errado contaminando grain contrato de trabalho) gera bias de medição em COUNT e em NULL-rate por coluna.
- Issue B (SP 2024 ausente) é perda de ~22M vínculos do estado com maior mercado de trabalho formal do país.
- Zero gate pós-leitura para detectar NULL massivo: o pipeline não falha, não alerta, registra `.done` e segue.
- Unity Catalog metadata vazio: 51 colunas sem comentário, sem TAGS — isso não é detalhe cosmético. Quem baixar a tabela amanhã não sabe que a bronze é STRING-ONLY, não sabe que 2023+ está corrompido, não sabe que `bairros_sp` pode conter a linha inteira concatenada. Rastreabilidade zero.

---

## 2. Buracos discutidos — impacto para identificação causal

### 2.1 Buraco 1986 SP: viabiliza ou inviabiliza event studies da transição democrática?

**Resposta curta: inviabiliza análises centradas em SP; não inviabiliza o restante do Brasil.**

Argumentação:

O Plano Cruzado (fev-nov 1986) e a redemocratização (Constituição 1988) são dois choques naturais relevantes para estudos de mercado de trabalho formal. Um event study ou DiD com esses eventos precisaria de: (a) série temporal contínua pré/pós, (b) unidade de controle comparável, (c) common trends verificável.

São Paulo concentrava em 1986 aproximadamente 30–35% do emprego formal registrado no RAIS (estimativa conservadora baseada nas séries 1985/1987 da própria bronze auditada, onde SP gera ~22M linhas/ano contra total nacional de ~29-35M). A exclusão de SP 1986 portanto:

- Cria **descontinuidade artificial** na série temporal de qualquer variável agregada nacional — qualquer tendência pré-tratamento calculada sobre 1985–1986 é enviesada downward em ~30%.
- **Viola common trends** se SP for incluído no painel pós-1987 mas ausente em 1986: o estimador DiD/TWFE vai absorver o "efeito" de SP reaparecer no painel como causalidade do choque.
- **Invalida subgroup analyses** para o estado mais industrializado do país nesse período — exatamente o mais interessante para analisar Plano Cruzado e aberração do emprego formal.

**Mitigação possível mas custosa:** restringir o painel a 1987–2024 para análises que usem janela pré-tratamento ampla, ou usar 1985 + 1987 e interpolar SP 1986 via synthetic control (Abadie & Gardeazabal 2003 / Abadie, Diamond & Hainmueller 2010). Qualquer dessas exige que o artigo declare explicitamente a imputação e reporte robustez sem SP nos anos de ruptura.

**Conclusão operacional:** event studies usando 1986 como ano-base são inviáveis sem caveat ou imputação explícita. Studies que usam 1985 ou 1987 como base não são afetados — desde que o período de análise não inclua 1986 como parte do pré-período de tendência.

### 2.2 Buraco 2024 SP: inviabiliza análise pós-eleição 2022 / governo Lula 3?

**Resposta: sim, inviabiliza análise nacional de 2024 como um todo — não apenas SP.**

Dois problemas se empilham:

**Problema 1 — Issue A (separador errado):** Todas as 76M linhas de 2024 na bronze têm 50/51 colunas NULL. Isso inclui os 7 arquivos de outras regiões (Centro-Oeste, MG/ES/RJ, NI, Nordeste, Norte, Sul). A ausência de SP é o segundo problema; o primeiro é que as linhas existentes não têm conteúdo. Qualquer análise que leia 2024 da bronze atual retorna distribuições completamente espúrias — não missing data, mas zeros e NULLs estruturais onde haveria dados reais.

**Problema 2 — Issue B (SP ausente):** SP representa ~30% do emprego formal. Mesmo que Issues A seja corrigido para os demais arquivos, sem SP 2024 qualquer estimativa nacional de 2024 subestima em ~30% o emprego formal. DiD com 2024 como pós-período e 2022 como pré-período gera ATT viesado em qualquer variável com distribuição SP-dependente (salário médio, formalização, setores intensivos em SP como serviços financeiros, tecnologia, comércio).

**Para governo Lula 3 especificamente:** o tratamento começa em jan/2023. A janela de análise relevante seria 2023–2024 vs 2020–2022. Com 2023+2024 inteiramente corrompidos, **a variável de resultado simplesmente não existe no dado**. Não há estratégia de identificação causal que conserte dado ausente — apenas recoleta.

**Conclusão operacional:** qualquer manuscrito que pretenda analisar o mercado de trabalho formal em 2023 ou 2024 deve aguardar correção de Issue A + B antes de rodar qualquer modelo. Publicar com dados RAIS de 2023/2024 da bronze atual seria equivalente a reportar resultados em dado imputado sem declaração da imputação.

### 2.3 Contaminação ESTAB: que bias entra em quem usa silver derivada de bronze sem o filtro?

**Grain mismatch é o bias mais insidioso porque é silencioso.**

Mecanismo do bias:

ESTAB (1 linha = 1 estabelecimento ativo) tem schema completamente diferente de VINC (1 linha = 1 contrato de trabalho). Quando ESTAB contamina VINC:

1. **Count bias**: `COUNT(*) WHERE uf = 'SP'` conta estabelecimentos como se fossem vínculos. Em 2022, a bronze tem ~8,45M linhas ESTAB + ~22M linhas VINC para SP. Um SELECT ingênuo superestima vínculos SP em ~38% naquele ano. Se essa razão varia por UF e por ano (e varia — SP tem mais estabelecimentos per capita que Acre), o bias é heterogêneo e se traduz em ATT espúrio em qualquer DiD por UF.

2. **NULL-rate contaminado**: ESTAB não tem `cbo_ocupacao`, `sexo_trabalhador`, `motivo_desligamento`, `salario_mensal`, etc. — todas NULL nas linhas ESTAB. Isso faz parecer que há cobertura menor para essas variáveis nos anos com mais ESTAB contaminação. Se o pesquisador usa NULL-rate como proxy de qualidade do dado, vai diagnosticar erroneamente que 2018–2022 tem pior cobertura que anos anteriores. O efeito sobre imputações downstream é enviesamento das distribuições condicionais.

3. **Regression bias**: qualquer regressão que inclua variáveis derivadas de ESTAB (como `nat_juridica` ou `tipo_estab`) vai misturar o valor do estabelecimento com o valor do vínculo — não porque os dois coincidam, mas porque a linha ESTAB tem esses campos preenchidos e a linha VINC correspondente tem NULL. Modelo OLS vai fazer o que OLS faz: usar o dado que tem.

**Análises passadas potencialmente afetadas:**

A pergunta relevante é: algum silver/gold no Mirante foi derivado de bronze RAIS **antes** de haver filtro `_source_file NOT LIKE '%ESTAB%'`? Não tenho visibilidade sobre o histórico de execução de notebooks silver, mas se a monografia UFRJ 2023 usou os mesmos dados com uma silver sem esse filtro explícito, os counts de vínculos de 2018–2022 podem estar inflados em ~30–40% (pela proporção ESTAB/VINC observada nos arquivos desta auditoria). Recomendo que o autor verifique o silver notebook e confirme presença do filtro ESTAB antes de qualquer reuso.

---

## 3. Linguagem de caveat metodológico para manuscritos

### 3.1 Linguagem recomendada — seção LIMITAÇÕES

Para qualquer WP que use RAIS e mencione dados de 2023 ou 2024:

> "Os dados RAIS de 2023 e 2024 disponíveis na plataforma de ingestão Mirante (bronze layer) apresentam corrupção de parsing decorrente de mudança de separador e schema introduzida pelo PDET no ciclo de entrega dessas competências (.COMT, sep=','). As análises deste trabalho restringem-se ao período 1985–2022. Extensão para 2023–2024 requer re-ingestão com tratamento do novo formato PDET, prevista em versão subsequente do pipeline."

Para qualquer WP que use RAIS 2018–2022 sem confirmação de filtro ESTAB na silver:

> "A tabela bronze da RAIS contém linhas de grain estabelecimento (ESTAB) misturadas com linhas de grain vínculo (VINC) para o período 2018–2022, decorrente de extração anterior ao filtro VINC-only. A silver utilizada neste trabalho aplica filtro `_source_file NOT LIKE '%ESTAB%'` [confirmar]. Análises que por ventura tenham sido derivadas de bronze diretamente sem esse filtro podem apresentar superestimação de vínculos em até 30–38% por UF."

Para análises que incluam SP 1986:

> "O arquivo SP 1986 está em quarentena permanente na fonte primária (PDET/MTE, FTP ftp.mtps.gov.br), com duas tentativas de re-download resultando em arquivo corrompido. Análises que utilizem 1986 como pré-período excluem São Paulo e estão sujeitas a viés de downward no emprego formal nacional estimado naquele ano. Estimativa de linhas ausentes: 7–13 M vínculos, representando ~25–30% do total nacional."

### 3.2 Há análise hoje no Mirante que use bronze diretamente?

Não tenho evidência de silver ou gold que leia `bronze.rais_vinculos` diretamente na pipeline auditada. O pipeline auditado (`rais_vinculos.py`) é o notebook de ingestão, não de transformação. Mas a pergunta permanece aberta: se algum notebook silver não existir ou não aplicar o filtro ESTAB, o dado downstream está comprometido. Recomendo que o autor rode `grep -r "rais_vinculos" pipelines/notebooks/silver/ pipelines/notebooks/gold/` e confirme quais notebooks consomem a bronze e se aplicam o filtro.

---

## 4. Reproducibilidade: bronze vs. monografia UFRJ 2023

### 4.1 Anatomia do ruído

| Categoria | Linhas (estimativa) | % do total declarado |
|-----------|--------------------|-----------------------|
| 2023+2024 corrompidos (sep errado) | ~175 M | ~7,8% |
| ESTAB contaminando VINC | ~75 M | ~3,4% |
| SP 2024 ausente | ~22 M | ~1,0% |
| SP 1986 ausente | ~7 M | ~0,3% |
| **Total ruído** | **~279 M** | **~12,5%** |

12,5% de ruído estrutural é alto para uma fonte canônica de dados administrativos públicos. Para comparação: na literatura de credit risk com dados de bureau, 5% de missing data já exige análise de sensitivity (missing not at random); aqui temos 12,5% de linhas que ou não existem ou têm grain errado ou têm conteúdo completamente corrompido.

### 4.2 Impacto sobre a monografia UFRJ 2023

A monografia replica 17 anos (2005–2021, presumivelmente, dado o contexto). As Issues relevantes para esse período são:

- **Issue C (ESTAB):** Se a monografia usou silver com filtro ESTAB, não há problema. Se usou bronze direta ou silver sem filtro, os counts estão inflados para 2018–2021 (4 anos do painel).
- **Issue D (SP 1986):** Irrelevante se a janela começa em 2005.
- **Issues A e B (2023+2024):** Irrelevantes para a janela 2005–2021.

A monografia UFRJ portanto foi produzida em janela onde as Issues mais graves (A, B) não existiam. O pipeline que hoje gera a bronze não existia em 2023 — a tese usou dados RAIS diretamente, provavelmente via Databricks ou script local. A **incompatibilidade de reproducibilidade** não é entre a monografia e a bronze, mas entre a bronze e qualquer tentativa de replicar a monografia usando a bronze atual como fonte única sem filtros documentados.

**Problema de reproducibilidade real:** a monografia não tem um `rais_vinculos.py` equivalente que possa ser rodado contra a bronze atual e produzir os mesmos números. Isso é uma lacuna de reproducibilidade independente dos Issues A–D — é a ausência de um pipeline de ponta-a-ponta documentado que vai do raw (`.7z`) ao resultado do artigo. A bronze é uma peça necessária mas não suficiente para reproducibilidade da monografia.

### 4.3 Nota sobre o WP RAIS futuro

Se o Mirante pretende publicar um WP sobre RAIS que reivindique reproducibilidade do estudo original, ele precisa:
1. Corrigir Issues A, B, C.
2. Documentar o filtro ESTAB na silver (contrato, não defesa ad hoc).
3. Comparar totais bronze + silver com totais publicados pelo PDET (Relatório Anual de Informações Sociais — RAIS Declarações) como ground truth externo.
4. Somente então afirmar "reproduzimos 40 anos de microdados PDET sob Lakehouse".

---

## 5. Priorização das Issues — ótica de valor analítico destravado

Da perspectiva de qual correção destrava mais inferência causal por unidade de esforço:

| Prioridade | Issue | Justificativa |
|------------|-------|---------------|
| **1º — A** | Separador errado 2023+2024 | 175M linhas. Fix trivial (branch `.COMT` → `sep=','`). Destrava análises pós-pandemia e governo Lula 3. Gate de qualidade pós-leitura (NULL-rate > 95% → falha pipeline) impede reincidência. Máximo impacto, mínimo esforço. |
| **2º — C** | ESTAB contamina VINC | ~75M linhas de grain errado. Fix é DELETE das linhas ESTAB + limpeza do Volume. Afeta 2018–2024 (7 anos) e provavelmente retroage a anos anteriores. Sem esse fix, qualquer COUNT de vínculos por UF/setor é não-confiável em ~30–38%. Impacto sobre todos os WPs que usem RAIS como cross-vertical (PBF, equipamentos médicos). |
| **3º — B** | SP 2024 ausente | ~22M linhas. Fix é re-trigger do Auto Loader para o arquivo já presente no Volume. Dependente de A (se A não for corrigido, SP 2024 entrará corrompido). Executar depois de A. |
| **4º — E** | UC metadata vazio | Zero linhas afetadas mas alto custo de governança. Qualquer novo usuário ou WP que leia a tabela sem contexto vai interpretar dados erroneamente. Fix é 1 ALTER TABLE com 51 COMMENTs + TAGs — esforço de 2h, impacto permanente de rastreabilidade. Recomendo executar junto com A (mesmo commit de correção do pipeline). |
| **5º — D** | SP 1986 quarentena | ~7M linhas. Source corrompido no FTP PDET. Fix requer contato com PDET/MTE ou uso de fontes alternativas (IBGE, Censo 1991 como proxy). Esforço alto, impacto limitado a análises do período democrático inicial. Não bloqueia nenhum WP atual do Mirante. Deferível. |

**Racionale da ordem A antes de C:** Issue C afeta 2018–2022 onde há outros controles possíveis (filtro silver). Issue A contamina 2023–2024 onde não há dado alternativo — o conteúdo real simplesmente não chegou à bronze. Sem A corrigido, nenhuma análise recente é possível independentemente de C.

**Racionale de E junto com A:** o caveat mais urgente que um usuário da tabela precisaria ver é exatamente "2023–2024 corrompidos". Isso deveria estar no COMMENT da tabela. Não custa mais do que 2 horas e impede que um analista que abre a tabela amanhã rode um query ingênuo e publique resultado falso.

---

## Pontos fortes

- Política STRING-ONLY de bronze honrada em 100% do pipeline — sem coerção de tipo que distorceria distribuições no silver.
- Cobertura raw → bronze 1987–2022 (vínculos) bate com inventário dos `.7z` — o pipeline faz o que promete para o período sem issue.
- Quarentena explícita de SP 1986 em `_bad/` é boa prática: o problema é visível e não silencioso, ao contrário de Issue A.
- Auto Loader com `mergeSchema=true` e `schemaEvolutionMode=addNewColumns` é a abordagem correta para lidar com drift de schema do PDET — a infraestrutura está certa, a parametrização está errada.
- O regex ESTAB (`r"(?i)(?:^|/)(estb|rais_estab)"`) em `_is_vinculo_filename` está correto e cobriria o problema se aplicado no passo 2 (batch read). O problema é arquitetural (filtro aplicado no unzip mas não na leitura CSV), não de lógica.

## Problemas remanescentes para nota plena

**P1 — Gate de qualidade pós-leitura (bloqueador):** O pipeline não verifica NULL-rate da saída CSV antes de marcar o processo como concluído. Uma verificação `IF (linhas com motivo_desligamento NOT NULL) / COUNT(*) < 0.05 THEN RAISE` teria detectado Issue A no primeiro run de 2023 e evitado 3 anos de dado corrompido em produção.

**P2 — Separador auto-detect ou branch por extensão (bloqueador):** `option("sep", ";")` hardcoded em linhas 1039, 1064, 1081. Correção mínima: branch `if fname.endswith(".COMT"): sep = ","`. Correção robusta: inferir separador do header (contar `,` e `;` na linha 0 e usar o mais frequente).

**P3 — Filtro ESTAB no passo de leitura CSV, não só no unzip (bloqueador):** `READ_PATH = f"{TXT_EXTRACTED}/ano=*/"` sem filtro de filename. Adicionar `cloudFiles.pathGlobFilter` com padrão negativo para `*ESTAB*` ou `*estb*` no Auto Loader. No batch mode, filtrar o DataFrame antes do `.write`.

**P4 — Unity Catalog metadata (padrão de plataforma violado):** 51 colunas sem COMMENT, zero TAGs. Não é cosmético: é o único mecanismo para que um analista de outro WP saiba que a tabela é VINC-only, STRING-ONLY, e que 2023–2024 está em revisão.

**P5 — Checklist de integridade cross-referenciado com fonte primária:** a bronze nunca foi validada contra os totais publicados pelo PDET (Relatório RAIS Declarações, disponível em pdet.mte.gov.br). Sem esse benchmark externo, a cobertura "completa" de 1987–2022 é afirmação do pipeline sobre si mesmo — circular e não-verificável externamente.

## Sugestões para subir de nível

1. Implementar P1 como `_assert_fill_rate(df, min_pct=0.05, cols=["motivo_desligamento","cbo_ocupacao","sexo_trabalhador"])` — se qualquer coluna canônica tiver menos de 5% de preenchimento no arquivo, o pipeline deve falhar com mensagem de diagnóstico clara antes de escrever na bronze.

2. Criar `pipelines/notebooks/bronze/rais_vinculos_qc.py` — notebook separado de quality check que roda após ingestão e produz tabela `mirante_prd.bronze._qc_rais_vinculos` com: `(ano, source_file, total_rows, fill_rate_motivo, fill_rate_cbo, fill_rate_sexo, pct_estab_contamination, validation_ts)`. Isso cria audit trail reproduzível e detecta Issues A e C automaticamente.

3. Adicionar ao briefing de WPs que usem RAIS: "verificar `_qc_rais_vinculos` antes de derivar silver" — torna a governança de dados parte do workflow editorial, não uma checagem ad hoc.

4. Para Issue D (SP 1986): tentar o download via `ftp.mte.gov.br` (domínio alternativo que o PDET manteve por um período) e via Wayback Machine CDX API para verificar se o arquivo esteve disponível. Se corrompido na origem, documentar em nota de dados no WP RAIS: "SP 1986 ausente por corrupção no arquivo PDET original; série 1986 nacional subestimada em ~30%."

---

**Why:** A nota C reflete um pipeline que funciona bem para 35 dos 40 anos mas falha silenciosamente nos anos mais recentes e economicamente relevantes (2023–2024), e que carrega contaminação de grain que invalida qualquer análise naïve de contagem de vínculos. Para um Lakehouse que se propõe a servir de base para manuscritos peer-reviewed, "funciona bem para 87,5% das linhas" não passa no crivo de rigor metodológico — especialmente quando os 12,5% corrompidos são exatamente os anos mais novos, os mais demandados por qualquer análise de política pública contemporânea.

**How to apply:** Corrigir A (sep auto-detect + gate NULL-rate) + C (filtro ESTAB no passo de leitura CSV) em um único commit de patch. Re-rodar ingestão para 2018–2024. Corrigir B (SP 2024, dependente de A). Adicionar E (UC metadata) no mesmo commit. Somente então re-rodar silver. A nota bronze pode subir para B+ (2,5) após essas correções — a infraestrutura está certa, o pipeline está correto nos anos 1987–2022, e o arcabouço STRING-ONLY + Auto Loader + UC é exatamente o padrão correto para esse volume de dados históricos administrativos.

---

## Nota final

**Bronze atual: C (1,0 pt) — INAPTA para sustentar manuscritos peer-reviewed do Mirante.**

**Bronze após correção de Issues A + B + C + E: projeção B+ (2,5 pt) — APTA, com caveats documentados para SP 1986 (Issue D, corrupção na fonte primária).**

Nenhum WP do Mirante deve referenciar dados RAIS de 2023 ou 2024 antes da correção de Issue A. Issues A e C são pré-requisito inegociável para qualquer publicação. Issue D (SP 1986) deve ser declarada como limitação em qualquer análise que use série histórica pré-1990.

---

*Parecer emitido por: Conselheiro de Finanças e Métodos Quantitativos*  
*Data: 2026-04-28*  
*Pipeline auditado: `pipelines/notebooks/bronze/rais_vinculos.py`*  
*Tabela auditada: `mirante_prd.bronze.rais_vinculos` (2.236.464.956 linhas, partição 1985–2024)*

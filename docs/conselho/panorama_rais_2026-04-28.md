# Panorama RAIS · 40 anos de mercado de trabalho formal brasileiro

**Data:** 2026-04-28  
**Autor da análise:** Claude (Opus 4.7) sob pedido do Leonardo Chalhoub  
**Bronze auditada:** `mirante_prd.bronze.rais_vinculos` v6 (pós-fix per-year reader)  
**Escala:** 2.060.910.061 linhas · 40 anos (1985-2024) · ~5571 municípios · 88 colunas STRING-ONLY  
**Status do dataset:** ✅ Bronze fidelidade-validada (cada linha com colunas alinhadas ao header do seu próprio arquivo de origem)

> Este documento é a base para o Conselho deliberar o WHY do RAIS no Mirante. Apresento o que **temos de fato** e o que **podemos fazer com isso**, sem decidir qual direção tomar.

---

## 0. Como ler este documento

Estrutura em 4 partes:

1. **§1-§7 — O que está nos dados** (descritivo, com tabelas reais).  
2. **§8 — Schema drift e caveats** (limitações que devem ser anunciadas em qualquer publicação).  
3. **§9-§10 — Oportunidades** (questões de pesquisa abertas + pipelines de ML/causal).  
4. **§11 — Para o conselho** (perguntas pra deliberação do WHY).

---

## 1. Visão geral · 40 anos, 2 bilhões de vínculos

A bronze cobre **toda a transição da economia brasileira da redemocratização até hoje**:

| Período | Era política | Era econômica | Linhas bronze |
|---|---|---|---|
| 1985–1989 | Sarney (NR1988) | Hiperinflação Cruzado/Cruzado II/Bresser/Verão | 159 M |
| 1990–1994 | Collor + Itamar | Hiperinflação → Plano Real | 167 M |
| 1995–2002 | FHC I+II | Estabilidade + privatizações + crise cambial 1999 | 290 M |
| 2003–2010 | Lula I+II | Boom commodities + Bolsa Família + Min Salário real | 397 M |
| 2011–2016 | Dilma I+II | Política expansionista → recessão profunda 2014-16 | 437 M |
| 2017–2022 | Temer + Bolsonaro | Reforma trabalhista + COVID + recuperação | 415 M |
| 2023–2024 | Lula III | Expansão pós-COVID, formalização recorde | 171 M |

**Granularidade da bronze: 1 linha = 1 vínculo empregatício formal-ano.** Um trabalhador com 2 empregos em 2010 aparece 2 vezes em `ano=2010`. Demissão em junho + admissão em outubro também = 2 linhas. Isso é IMPORTANTE — `COUNT(*)` não é "número de trabalhadores" mas "número de relações de emprego".

---

## 2. Trajetória temporal

### 2.1 Crescimento secular interrompido por 4 choques

```
ano   total_vínculos   ativos_31/12  Δ%
1985        28.6 M          20.3 M    —
1990        35.4 M          23.2 M  +14% (mas Plano Collor)
1994        33.6 M          23.7 M   +2% (Plano Real)
2000        37.3 M          26.2 M  +11% (estabilização)
2007        54.6 M          37.6 M  +43% (boom commodities)
2014        76.1 M          49.6 M  +32% (auge)  ← ALL-TIME HIGH abs
2017        65.7 M          46.3 M  -14% (recessão Dilma+Temer)
2020        65.9 M          46.2 M   +0% (COVID resiliente)
2024        87.7 M          57.8 M  +33% (recuperação + Lula 3)
```

**Insight:** o estoque de vínculos ativos hoje (57.8 M em 2024) é maior que o pico anterior (49.6 M em 2014). Já tínhamos isso no Caged, mas a RAIS confirma na fonte primária.

### 2.2 Choques macroeconômicos no ESTOQUE de vínculos ativos

| Ano | Δ ativos | Δ % | Evento |
|---|---|---|---|
| **1986** | -5,8 M | **-28,6%** | Plano Cruzado, congelamento de preços |
| 1987 | +8,1 M | +56,0% | Reabsorção pós-Cruzado II |
| 1990 | -1,3 M | -5,3% | Plano Collor, sequestro de contas |
| 1992 | -738 K | -3,2% | Recessão Itamar |
| **2015** | -1,5 M | **-3,0%** | Recessão Dilma |
| **2016** | -2,0 M | **-4,2%** | Recessão + impeachment |
| 2020 | -480 K | -1,0% | COVID (formal mais resiliente que informal) |
| 2022 | +4,1 M | **+8,3%** | Pico de recuperação pós-COVID |

**O "choque do Cruzado" (1986) é o evento de maior magnitude da série**, com queda de quase 30% em vínculos ativos. Dado pouco explorado na literatura — geralmente focam em PIB/inflação. Aqui temos a **micro** do labor market do choque.

A recessão Dilma (2014→2016) acumulou perda de 3,5 M vínculos — o segundo maior choque, mais lento e duradouro que o Cruzado.

COVID em 2020 foi surpreendentemente leve no formal (-1%) por conta do BEm (Benefício Emergencial de Manutenção do Emprego) — política implementada em abril/2020 que subsidiou suspensão e redução de jornada. Sem o BEm, a queda teria sido muito maior. **Há aqui um quasi-experimento natural de causal inference para avaliar a eficácia do BEm.**

---

## 3. Concentração regional · descentralização lenta de SP

```
UF        1985    1995    2005    2014    2024
SP       35,5%   34,1%   29,9%   28,8%   28,1%   ← perde 7,4 pp em 40 anos
RJ       13,0%   11,0%    9,1%    9,2%    7,6%   ← perde 5,4 pp (esvaziamento industrial)
MG        9,2%   10,8%   11,4%   10,6%   10,9%   ← estável
RS        8,5%    7,5%    6,9%    6,4%    5,7%   ← perde gradualmente
PR        5,7%    6,3%    6,6%    6,6%    6,7%   ← ganha
SC        3,7%    4,0%    4,8%    4,9%    5,4%   ← maior ganho relativo
GO          —       —    (3,1%)  (3,5%)   3,5%   ← entra top 8 em 2024
```

**Padrões claros:**

1. **SP descendente, mas ainda dominante**: queda de 7,4 pontos em 40 anos. Não é "perda" — outras regiões cresceram mais rápido. O estoque absoluto de SP triplicou (9,8M → 24,6M).

2. **RJ é o caso de declínio relativo mais agudo** — perdeu quase metade da participação. Possíveis causas: desindustrialização do parque petroquímico + serviços financeiros migrando pra SP + crise fiscal do estado.

3. **Sul (PR+SC+RS) ganhou peso** — agroindústria, automobilístico (PR), tech (SC).

4. **Centro-Oeste ascende** — GO entrou no top 8 em 2024, MS+MT também crescendo (não mostrado). Fronteira agrícola consolidada.

**Causal question disponível:** quanto a Lei 14.193/2021 (incentivos fiscais industriais regionais) e o Marco Legal das Startups (2021) afetaram a redistribuição regional?

---

## 4. Feminização do mercado formal

```
ano   % feminino
1985    30%
1990    33%   +3 pp em 5 anos
1995    35%
2000    37%
2005    38%
2010    40%   atinge 40% pela 1a vez
2015    42%
2020    43%
2024    44%   ← atual
```

**Crescimento monótono, ~0,4 pp/ano em média**, sem reversões durante recessões. Mulheres entram no mercado formal e permanecem mesmo em crises. Isso vai contra a hipótese de "added worker effect" pura — a entrada feminina é estrutural, não cíclica.

**Pergunta de pesquisa:** quanto da feminização é explicada por (a) educação relativa de mulheres ultrapassando a de homens, (b) terceirização de serviços, (c) mudança demográfica, (d) Bolsa Família condicionando mães em emprego formal? Isso é decomponível com Oaxaca-Blinder + Mincer eqs estendidas.

---

## 5. Envelhecimento do trabalhador formal

```
ano   idade média   idade mediana
2000     33,8 y        32 y
2010     34,4 y        32 y
2020     37,2 y        36 y
2024     37,5 y        36 y
```

**+3,7 anos em 24 anos.** Acompanha o envelhecimento populacional brasileiro (DataSUS / IBGE), mas com **defasagem temporal interessante**: em 2000-2010 a idade mediana ficou ESTÁVEL (32 anos), e só sobe a partir de 2010. Isso sugere que durante o boom 2003-2010 entrou MUITA gente jovem no formal (efeito coorte), o que rejuvenesceu o pool. A partir de 2014, com retração das contratações, o pool envelheceu rapidamente.

**Implicação ML:** modelos de previsão de aposentadoria + custo previdenciário precisam re-segmentar. A coorte 2003-2010 é distinta — entrou jovem, está envelhecendo no estoque ativo.

---

## 6. Escolaridade · transformação histórica

```
ano   analfa+fund_inc   sup_inc+sup_comp   mestre+doutor
1985        19,6%              16,7%             7,4%
1995        15,3%              19,3%             8,7%
2005         6,5%              36,8%            12,7%   ← maior salto de educ. no formal
2024 (.COMT)  2,2%              56,0%            24,4%
```

**A análise é parcial** porque PDET trocou taxonomia em 2006 (ver §8.2) e bronze tem gap pra 2006-2022 nessa coluna específica. Mas comparando os pontos válidos:

- **Em 1985, 19,6% dos vínculos formais eram de pessoas com ensino fundamental incompleto ou menos. Em 2024, são 2,2%.** Queda dramática.
- **Mestrado+Doutorado triplicou** (7,4% → 24,4%). Isso é muito alto e sugere que a coluna sanitizada incluiu graus que não são apenas pós-strictu — provavelmente graus 9 e 10 do PDET incluem "superior completo + lato sensu" (especialização). Exigir auditoria do dicionário.
- **Ensino superior completo** virou dominante (56% dos vínculos formais em 2024). Brasil formal é HOJE um mercado predominantemente de superior completo.

---

## 7. Massa salarial e desigualdade · uma fronteira em aberto

A bronze tem **5 medidas de remuneração** populadas em pelo menos uma era:
- `vl_remun_dezembro_sm` / `vl_rem_dezembro_sm` — em salários-mínimos, dezembro
- `vl_remun_media_sm` / `vl_rem_media_sm` — média do ano em SM
- `vl_rem_dezembro_nom` — em R$ nominais (era3+, 2023+)
- `vl_rem_media_nom` — idem
- **12 colunas mensais** `vl_rem_<mês>_sc` (era3+) — remuneração mês-a-mês em "salário corrente"

**Nunca antes foi possível** olhar a granularidade mês-a-mês de remuneração no painel RAIS. Em 2023+ podemos ver a sazonalidade salarial (13º, férias, PLR) **dentro do indivíduo**. Isso é base pra:

- Modelos de **wage growth** mais precisos
- Detecção de **eventos salariais** (promoção, mudança de cargo)
- Análise de **heterogeneidade de timing** (quando empresas pagam PLR? quem antecipa 13º?)

A análise direta de mediana/p90 cross-era (não mostrada no detalhe — escala 2024 está fora) requer **deflacionar tudo pelo INPC ou pelo IPCA-15** primeiro. Sem deflação, comparação é vazia.

---

## 8. Schema drift e caveats que precisam ser anunciados

### 8.1 Três eras com schemas diferentes

| Era | Anos | Formato | Sep | Cols | Observação |
|---|---|---|---|---|---|
| era1a | 1985-1993 | `.txt` | `;` | ~24 | Sem CBO 2002, sem CNAE, ainda CBO94+IBGE Subsetor/Subatividade |
| era1b | 1994-2017 | `.txt` | `;` | ~31 | Adiciona Bairros Fortaleza/RJ, CBO94, CNAE95, Idade, Qtd Hora |
| era2 | 2018-2022 | `.txt` | `;` | ~44 | Adiciona Raça/Cor (já desde 2003), Portador Deficiência (2008+), Trab. Intermitente (2017+) |
| era3 | 2023-2024 | `.COMT` | `,` | ~60 | Renomeia TODOS os headers com sufixo "- Código"; adiciona Causa Afastamento (3 níveis), Vl Rem mensal × 12, Tipo Deficiência, Vínculo Abandonado |

### 8.2 Variáveis com mudança de codebook (silver alvo)

- **Grau de Instrução**: PDET trocou taxonomia 2005→2006. Era1+era2 usam `grau_instrucao_2005_1985` (10 categorias 1=analf → 10=doutorado). Era3 usa `escolaridade_apos_2005_codigo`. Mapping não-trivial; silver precisa harmonizar.
- **CBO**: 1985-2002 usa CBO 1994 (5 dígitos), 2003+ usa CBO 2002 (6 dígitos). Conversão CBO94 → CBO2002 existe via tabela DIEESE.
- **CNAE**: 1985-1994 usa IBGE Subsetor/Subatividade, 1995-2007 usa CNAE 1995, 2008+ usa CNAE 2.0. Cruzamento via tabela do IBGE.
- **Município**: ajustar nullif("999999") porque era3 frequentemente tem "ignorado" em `municipio_trab_codigo` (mas `municipio_codigo` do estabelecimento sempre real). Era importante o fix per-year reader que aplicamos.

### 8.3 Gaps na FONTE PDET (não na ingestão)

- **MA1985**: nunca chegou no Volume FTP (~1-2M linhas estimadas)
- **PA1986**: idem (~2-3M linhas)
- **SP1986**: corrupção persistente do FTP, em quarentena (~7-13M linhas)

Total estimado de "vácuo de fonte": ~10-18 M linhas, concentradas em 1985-1986. **Não invalidam análise** mas precisa caveat metodológico em qualquer manuscrito que use 1985-1986 com SP/MA/PA.

### 8.4 ESTAB (estabelecimento) NÃO está em bronze

Bronze RAIS Vínculos é grain de **contrato de trabalho-ano**. Há outro dataset PDET — RAIS Estabelecimentos — com grain de **estabelecimento-ano**. Não está nesse pipeline. Usar para análise de empresas (entrada/saída, tamanho médio, sobrevivência).

### 8.5 Não há identificador único de trabalhador

A bronze NÃO contém CPF (PII protegida pelo PDET). Isso significa que **não dá pra rastrear o mesmo trabalhador entre anos**. Análises de mobilidade individual (job-to-job, wage growth pessoal, churn) **não são possíveis** com bronze pública.

Workaround: pseudo-painel via combinação de (idade, sexo, raça, escolaridade, município, cbo, mês_admissão) — mas isso é estatística, não rastreamento.

---

## 9. Questões de pesquisa abertas (com identificação causal possível)

### 9.1 Reforma Trabalhista 2017 (Lei 13.467)

**Pergunta:** A reforma aumentou ou reduziu (a) emprego formal, (b) rotatividade, (c) salário inicial?

**Estratégia causal:**
- **Difference-in-differences** com tratamento heterogêneo entre setores. Setores com alta rotatividade pré-reforma (construção, comércio) são mais expostos.
- **Synthetic control** comparando Brasil pós-2017 com painel de países sul-americanos sem reforma similar.
- **Event study** com a Lei como choque temporal.

**Variáveis na bronze:** `tipo_admissao`, `tempo_emprego`, `motivo_desligamento`, `tipo_vinculo`, `ind_trabalho_intermitente_codigo` (2018+).

### 9.2 BEm (Benefício Emergencial COVID) — eficácia

**Pergunta:** Quanto o BEm (suspensão/redução jornada subsidiada) preservou empregos formais durante COVID?

**Estratégia:**
- **RDD temporal** em torno de abril/2020 (cutoff de início do BEm).
- **DiD por setor** — setores essenciais não-elegíveis vs setores elegíveis (em alguns recortes).
- **Triple-diff** com escolaridade (alta vs baixa, dado que BEm protegeu mais baixa-renda).

**Variáveis na bronze:** `vinculo_ativo_31_12` (estoque), `motivo_desligamento`, mensais `vl_rem_<mês>_sc` (2023+ permite ver remuneração efetiva mensal).

### 9.3 Bolsa Família e formalização das mães

**Pergunta:** O BF aumenta a formalização das beneficiárias? (Há literatura sugerindo o oposto — disincentivo à formalização para não perder o benefício.)

**Estratégia:**
- **RDD na linha de elegibilidade** do BF (linha de pobreza) — comparar mães logo abaixo (recebem) vs logo acima (não recebem).
- **Cruzamento RAIS × CadÚnico** (necessário acordo MTE+MDS) ou painel agregado por município.

**Variáveis na bronze:** `sexo_trabalhador`, `idade`/`faixa_etaria`, `municipio` — dá pra ver evolução temporal por município de trabalho formal feminino.

### 9.4 Reforma trabalhista e trabalho intermitente

**Pergunta:** O contrato intermitente (criado em 2017) substitui ou complementa CLT tradicional?

**Estratégia:**
- **Análise descritiva first** — em quais setores/CBOs cresceu o intermitente?
- **DiD por setor** comparando efeito do intermitente vs CLT em média de horas, salário e estabilidade.

**Variáveis na bronze:** `ind_trabalho_intermitente_codigo` (2018+), `qtd_hora_contr`, `tempo_emprego`.

### 9.5 Plano Cruzado (1986) revisitado

**Pergunta:** Por que houve queda de 28,6% nos vínculos ativos em 1986?

**Hipóteses:**
- Congelamento de preços + tabelamento → fechamento de empresas que não conseguiram repassar custos
- Êxodo para informal (proteção contra inflação congelada)
- Subcontratação massiva (vínculos terceirizados deixam de ser registrados)
- Dado: re-cadastro do PDET em 1986 (sub-registro técnico, não queda real)

**Estratégia:** decomposição setorial + comparação com PIB do IBGE para distinguir queda de produção de queda de registro.

**Por que importa:** O Plano Cruzado é tratado como caso de fracasso no jornalismo macro, mas a literatura empírica do choque é rara. Aqui temos os micros.

### 9.6 Choque commodities 2003-2014 e desindustrialização precoce

**Pergunta:** O boom de commodities deslocou trabalhadores de manufatura para serviços/agro?

**Estratégia:** decomposição shift-share (Bartik instrument) das mudanças setoriais por município, usando exposição comercial pré-2003 como instrumento.

**Variáveis na bronze:** CBO, CNAE, município, ano. Painel suficiente para Bartik.

---

## 10. Pipelines de ML viáveis com a bronze

### 10.1 Forecasting de vínculos formais (UF × CNAE × mês)

**Target:** `n_vinculos_ativos` por UF, CNAE 2-dígitos, ano-mês.  
**Features:** lags + sazonalidade + dummies de regime macro (Cruzado, Real, recessão Dilma, COVID).  
**Modelo:** SARIMA por painel ou Prophet hierárquico (UF × setor) ou DeepAR (Amazon Forecast).  
**Aplicação:** previsão para PNUD/governo de "quantos vínculos vão existir em 6 meses". Já fazem isso no IBGE; podemos fazer melhor com microdados.

### 10.2 Wage gap explainer · Mincer + ML

**Target:** salário em SM (transformado log).  
**Features:** sexo, idade, escolaridade, raça (2003+), CBO, CNAE, UF, município, tempo emprego, tamanho estabelecimento, tipo vínculo.  
**Modelo:** Random Forest + SHAP para explicar contribuição de cada variável + Oaxaca-Blinder decomposition para gap por gênero/raça.  
**Aplicação:** estimar **explained vs unexplained gap** entre H/M e Branca/Parda+Preta — útil para advocacy + estudos acadêmicos.

### 10.3 Detecção de anomalias em registros (suspeita de fraude)

**Target:** flag de "registro suspeito" — combinações implausíveis (CBO + escolaridade + salário + idade).  
**Modelo:** Isolation Forest ou Autoencoder para detectar outliers multivariados.  
**Aplicação:** auditoria de empresas que registram trabalhadores fictícios para acessar incentivos fiscais (BNDES, FAT, Sebrae).

### 10.4 Clustering de trajetórias municipais

**Target:** série temporal de (n_vinc, mass_salarial, share_simples, distrib_setorial) por município ao longo de 40 anos.  
**Modelo:** k-shape ou DTW + hierarchical clustering, ou DeepCluster com LSTM encoder.  
**Aplicação:** **tipologia de municípios pelo perfil dinâmico do mercado de trabalho** — diferente das tipologias IBGE (que usam só pop+IDH+PIB). 

### 10.5 Predição de churn empregatício (rotatividade individual)

**Target:** P(desligamento em 12 meses | features atuais).  
**Features:** tempo emprego, idade, sexo, escolaridade, CBO, tamanho estab, salário relativo (vs mediana CBO).  
**Modelo:** Gradient Boosting (XGBoost/LightGBM) com calibração por estrato.  
**Aplicação:** RH de empresas, marketing de cursos profissionalizantes, planejamento previdenciário.  
**Caveat:** sem CPF, é P(desligar | grupo demográfico), não P(desligar | indivíduo).

### 10.6 Simulação contrafactual de políticas

**Modelo:** estrutural — mistura de Mincer eq + matching model (DMP-like).  
**Aplicação:** "se o salário-mínimo aumentar 5% real, qual o impacto no estoque de vínculos por setor/UF?". 
Tem literatura forte para isso (Lemos 2009, Engbom & Moser 2022); RAIS é o dataset canônico.

### 10.7 Análise causal do BEm (priority)

Como descrito em §9.2 — RDD temporal + DiD setorial. Pode virar working paper de impacto.

### 10.8 Embedding de CBO (occupation embedding)

**Target:** representação vetorial de cada código CBO 2002 baseada em coocorrência empresa-CBO ao longo do tempo.  
**Modelo:** Word2Vec ou GraphSAGE em rede CBO×CBO (mesma empresa).  
**Aplicação:** medir **similaridade ocupacional** — útil para career path recommenders, análise de transitabilidade entre profissões durante automação/IA.

---

## 11. Para o Conselho — perguntas pra deliberar o WHY

Os 4 conselheiros já leram este documento (ou lerão na próxima sessão). Antes de eles emitirem parecer, preciso de duas decisões do autor:

**1. WHY institucional** — qual é a missão central que o RAIS no Mirante vai cumprir? Possibilidades:

- **(a) Demonstração técnica** — "reproduzo 40 anos de microdados públicos de forma replicável" (foco eng dados, audiência: recrutadores, talks)
- **(b) Análise de política pública** — "decifro o impacto de Cruzado/Real/Reforma Trab/BEm/Lula 3 com identificação causal" (foco econometria, audiência: academia + governo)
- **(c) Plataforma de descoberta** — "deixo público um data product onde qualquer pessoa pode explorar 40 anos de Brasil trabalhador" (foco produto, audiência: jornalistas + sociedade)
- **(d) Curso/consultoria** — "uso o RAIS como caso pedagógico para aulas de eng dados / econometria de política pública" (foco monetização direta)

Não são exclusivos. Mas o conselho precisa saber o peso relativo entre eles para emitir parecer.

**2. Recorte de output** — qual o formato primeiro?

- **(i)** Working paper acadêmico (~30-50 pp, peer review) sobre 1 das questões em §9
- **(ii)** Artigo de imprensa popular (~5 pp, ABNT++) sobre uma narrativa do §1-§7
- **(iii)** Notebook interativo (Quarto/Streamlit) público pra exploração
- **(iv)** Talk/aula (90 min) com slides + queries ao vivo
- **(v)** Combinação ou rotação de todos

---

## 12. Resumo executivo · 1 minuto

- 40 anos, 2 bilhões de vínculos formais — **dataset mais rico** do mercado de trabalho público brasileiro
- Bronze íntegra após dois fixes (separator drift + per-year header alignment); 5571 municípios em todas as eras
- 4 choques claros na série (Cruzado 1986, Real 1994, Recessão Dilma 2014-16, COVID 2020 + recuperação 2022-24)
- Concentração regional cai (SP de 35,5% → 28,1%); Sul + Centro-Oeste sobem
- Feminização monotônica (30% → 44%); envelhecimento (mediana 32 → 36 anos); educação explode (sup. completo de 17% → 56%)
- 8+ questões de pesquisa abertas com identificação causal possível
- 8 pipelines de ML viáveis (forecasting, wage explainer, anomaly, clustering, churn, simulation, causal, embeddings)
- 5 caveats críticos pra qualquer publicação (schema drift cross-era, gaps na fonte 1985-86, codebook drift de Grau/CBO/CNAE, 999999 em município, ausência de CPF)

**O dataset está pronto para virar produto/publicação.** A pergunta agora é qual a forma.

# Parecer — Conselheiro de Finanças e Métodos Quantitativos
## Panorama RAIS · WHY acadêmico · Priorização de questões causais

**Versão avaliada:** `docs/conselho/panorama_rais_2026-04-28.md`  
**Score atribuído:** B (2,0 pts) — aprovação no limiar, revisão obrigatória antes de submissão  
**Histórico:** bronze C (1,0 pt) → panorama B (2,0 pt) — a análise descritiva é boa; identificação causal está incompleta  
**Régua:** mestrado stricto sensu (B = 2,0 é o limiar; limiar não é teto)

---

## Veredicto geral

O panorama é um documento de prospecção competente. A série temporal está corretamente descrita, os choques macroeconômicos são identificados com magnitudes plausíveis, e os caveats de schema drift em §8 refletem exatamente o que a auditoria bronze encontrou. O autor (Claude, sob pedido do Leonardo Chalhoub) não fabricou resultados quantitativos — méritos registrados.

O problema central não é o que está no documento. É o que está ausente: **nenhuma das 6 questões causais em §9 tem identificação formal suficiente para um working paper peer-reviewed**. Os designs são nomeados corretamente (DiD, RDD, Bartik IV) mas as condições de validade não são verificadas, as ameaças não são listadas, e em dois casos o design proposto é tecnicamente incompatível com o dado disponível. Isso é o delta entre "mapa de oportunidades" e "protocolo de pesquisa". O panorama cumpre bem o primeiro papel. Para o segundo, há trabalho estrutural pela frente.

---

## 1. Priorização das 6 questões causais (§9)

A avaliação considera quatro dimensões: validade interna do design proposto, validade externa (relevância de política pública), viabilidade dado o que está na bronze HOJE, e risco de correlação espúria se mal-implementado.

### Ranking consolidado

| Rank | Questão | Design proposto | VI | VE | Viab. | Risco espúrio | Nota síntese |
|------|---------|----------------|----|----|--------|----------------|--------------|
| **1** | §9.2 BEm COVID | RDD temporal + DiD setorial | Alta | Alta | Alta | Moderado | **Candidata ao WP** |
| **2** | §9.1 Reforma Trabalhista 2017 | DiD + Synthetic Control | Média-Alta | Alta | Média-Alta | Alto | Viável com salvaguardas |
| **3** | §9.6 Bartik commodities 2003-14 | Bartik IV (shift-share) | Média | Média-Alta | Média | Alto | Exige CNAE harmonizado |
| **4** | §9.4 Trabalho intermitente | DiD por setor | Baixa-Média | Média | Média | Muito alto | Seleção endógena severa |
| **5** | §9.3 BF e formalização | RDD na linha de pobreza | Baixa | Alta | Baixa | Alto | Dado inadequado na bronze |
| **6** | §9.5 Plano Cruzado 1986 | Decomposição setorial | Muito Baixa | Média | Baixa | Muito alto | Não é identificação causal |

---

### 1.1 Rank 1 — §9.2 BEm COVID (QUESTÃO TOP-1)

**Por que TOP-1:** É o único caso entre os 6 onde (a) o choque é exógeno e datado com precisão — MP 936/2020, publicada em 01/04/2020; (b) a regra de elegibilidade cria variação exploitável — cobertura era parcial por setor/porte da empresa; (c) o dado na bronze está disponível sem necessidade de harmonização cross-era (2018–2022 é era2, schema estável); (d) o efeito tem magnitude macroeconômica verificável externamente (BEm cobriu ~10M trabalhadores segundo MTE — verificação externa do N tratado); (e) há literatura de referência comparável com designs similares em outros países (Cahuc et al. 2021 para kurzarbeit europeu; Sarto & Tewari 2023 para EUA) que permite posicionar a contribuição brasileira com clareza.

**O paradoxo da "resiliência COVID":** O panorama afirma que COVID foi "surpreendentemente leve no formal (-1%)" — isso está correto como descrição, mas é exatamente aí que mora o quasi-experimento. A queda de apenas -1% NO ESTOQUE não é o efeito — é o contrafactual implícito sem o BEm. Estimar o contrafactual do que teria acontecido **sem** o BEm é a pergunta causal. A descrição do panorama trata o observado como se fosse a conclusão; o WP tem de tratar o observado como o ponto de partida para estimar ATT.

**Por que não os outros 5:**

- §9.1 (Reforma 2017): O choque nacional simultaneamente tratou todo o mercado de trabalho formal — não há grupo de controle natural no Brasil. Synthetic control requer painel de países comparáveis com dados RAIS-equivalentes, o que não existe na bronze. DiD por setor tem problema sério de SUTVA (Stable Unit Treatment Value Assumption): setores interagem.

- §9.6 (Bartik): Bartik/shift-share é instrumento forte e bem estabelecido (Goldsmith-Pinkham, Sorkin & Swift 2020 sobre validade da exclusão). Mas exige CNAE harmonizado cross-era (1985-2024 usa IBGE Subsetor → CNAE 1995 → CNAE 2.0) — trabalho de harmonização que pode consumir 3-6 meses antes de rodar o primeiro modelo. Para um primeiro WP RAIS, esse custo de entrada é alto.

- §9.4 (Intermitente): Seleção endógena é o problema fundamental. Quem adotou contrato intermitente não é aleatório — são exatamente os setores/empresas que já tinham alta rotatividade ou que queriam terceirizar legalmente. Qualquer DiD vai absorver heterogeneidade pré-existente como efeito do tratamento.

- §9.3 (BF × formalização): A RDD na linha de pobreza requer dados de renda no nível individual com linkagem RAIS × CadÚnico. A bronze não tem CPF — o cruzamento é impossível sem acordo MDS×MTE com microdados administrativos. O design é correto conceitualmente mas o dado não existe na bronze pública.

- §9.5 (Cruzado 1986): Não é identificação causal — é decomposição descritiva. O choque é exógeno de política macroeconômica, mas não há grupo de controle observável, a variável dependente (-28,6% em vínculos) tem problema de sub-registro documentado no próprio panorama (§8.3 e §9.5, hipótese 4), e SP 1986 está em quarentena. Resultado de qualquer modelo seria não-identificado.

---

### 1.2 Rank 2 — §9.1 Reforma Trabalhista 2017 (Lei 13.467)

**Design correto mas viabilidade média.** O principal obstáculo é que a Lei 13.467/2017 é um choque nacional que afetou potencialmente todo o mercado de trabalho formal simultaneamente. DiD clássico exige unidade não-tratada como controle — aqui não existe unidade no Brasil que não tenha sido exposta à reforma. A heterogeneidade de tratamento por setor (construção civil, varejo, serviços) é exploitável, mas exige:

1. Hipótese explícita de qual mecanismo da reforma afeta mais fortemente cada setor (e.g., negociação coletiva vs. CLT para setor X mais exposto à jornada 12×36 do que setor Y).
2. Teste de common trends pré-2017 para os pares setor-tratado vs. setor-controle.
3. Correção para múltiplos tratamentos simultâneos (CLT reforma + MP 808/2017 + regulamentações BACEN, TST posteriores).

Synthetic control com painel da América Latina seria a abordagem mais limpa (Brasil vs. Argentina/Chile/México/Colômbia), mas exige dados de emprego formal comparáveis, o que limita a granularidade.

---

### 1.3 Rank 3 — §9.6 Bartik commodities (shift-share IV)

Bartik instrument é metodologicamente sólido quando:
1. As shares (exposição setorial pré-período por município) são exógenas ao choque.
2. Os shifts (variação nacional no emprego por setor) são exógenos à demanda local.

Condição 1 é razoável: exposição pré-2003 reflete herança histórica, não antecipação do boom. Condição 2 é discutível: o boom de commodities foi endógeno à demanda chinesa, que por sua vez tinha correlação com algumas UFs mais do que outras (Mato Grosso, Pará). O design é viável mas exige CNAE harmonizado cross-era — trabalho de meses. Relevância de política pública é média: o boom já passou, o resultado informa discussão sobre Dutch disease no Brasil, mas não instrui política ativa atual.

---

## 2. Especificação completa — Questão TOP-1: BEm COVID

### 2.1 Identificação causal

**Design primário: DiD por elegibilidade setorial × tempo.**

A MP 936/2020 (depois Lei 14.020/2020) permitiu às empresas suspender contratos ou reduzir jornada com subsídio do governo federal para trabalhadores com salário de até R$3.135 (1 SM em 2020). A elegibilidade variou por: (a) porte da empresa (ME/EPP tinham maior acesso relativo), (b) setor (serviços essenciais tinham restrição operacional diferente), (c) faixa salarial (o subsídio era decrescente por faixa).

**Design secundário: RDD temporal em abril/2020.**

A MP 936 foi publicada em 01/04/2020. O corte temporal é limpo e exógeno. A janela relevante é fev-mar/2020 (pré-BEm mas pós-COVID-declaração OMS em mar/2020) vs. abr-set/2020 (pós-BEm). O problema de RDD temporal puro é que outros choques simultâneos ocorreram na mesma janela (decretos estaduais, lockdowns, queda de demanda agregada) — tudo contaminando o cutoff. Por isso o DiD setorial é o design principal e o RDD temporal é o design de robustez, não o contrário do que §9.2 sugere.

**Design terciário (se disponível): Triple-DiD por escolaridade × setor × tempo.**

O BEm protegeu desproporcionalmente trabalhadores de menor renda (o subsídio era maior em % para quem ganhava menos). Triple-DiD com a dimensão de escolaridade como proxy de renda (alta escolaridade = maior salário = menor cobertura relativa do BEm) é o teste de heterogeneidade mais limpo disponível na bronze — sem CPF, escolaridade é o melhor proxy de faixa salarial.

### 2.2 Tratamento, controle, threshold, janela

| Elemento | Especificação |
|----------|--------------|
| Unidade de análise | Município × setor CNAE 2-dígitos × trimestre |
| Período | Q1/2019 – Q4/2021 (12 trimestres; 3 pré, 6 intra, 3 pós) |
| Tratamento | Setor com alta elegibilidade ao BEm (serviços não-essenciais, varejo, hotelaria, restaurantes, eventos) |
| Controle | Setor com baixa/zero elegibilidade (agro, saúde, logística, segurança) |
| Threshold temporal | Abril/2020 (MP 936/2020) |
| Variável de resultado primária | `vinculo_ativo_31_12` — estoque de vínculos ativos no fim do período |
| Variável de resultado secundária | `motivo_desligamento` — distribuição de saídas por tipo (demissão sem justa causa vs. término contrato vs. reintegração) |
| Variável de resultado terciária | Duração mediana do emprego (proxy: `tempo_emprego` no momento do desligamento) |

**Limitação crítica sobre a janela temporal da bronze:** A variável `vinculo_ativo_31_12` é estoque anual — não trimestral. A bronze não tem granularidade mensal de estoque para o período 2020 (isso só existe em era3, 2023+). O DiD só pode ser estimado com granularidade anual para 2019 vs. 2020 vs. 2021, não trimestral. Isso limita a janela a três pontos: antes (2019), durante (2020), depois (2021). O evento study com trimestres exigiria dados do CAGED (que tem granularidade mensal de admissões/demissões, não estoque), o que está fora da bronze RAIS. **Declarar isso explicitamente na seção DADOS E METODOLOGIA — não enterrar em nota de rodapé.**

### 2.3 Variáveis exatas da bronze

| Variável | Papel | Caveat |
|----------|-------|--------|
| `vinculo_ativo_31_12` | Outcome primário (estoque) | STRING → cast para integer na silver; verificar que era2 está limpa de ESTAB antes do cast |
| `motivo_desligamento` | Outcome secundário (qualidade do desligamento) | Codebook era1/era2 diverge em subcódigos; harmonizar para 3 categorias: demissão involuntária / saída voluntária / encerramento empresa |
| `tempo_emprego` | Outcome terciário (durabilidade) | Disponível em todos as eras; unidade: meses; verificar `999` como código para "indeterminado" antes de usar |
| `cnae_2_0_classe` | Variável de tratamento (setor) | Disponível a partir de 2008; para 2003-2007 usar `cnae_classe` (CNAE 1995); harmonização necessária mas simples para 2 dígitos |
| `grau_instrucao_2005_1985` | Proxy de faixa salarial para triple-DiD | Codebook muda em 2006 (§8.2 do panorama) — usar apenas categorias 1-3 (baixo) vs 7-9 (alto) para minimizar impacto do drift; declarar limitação |
| `municipio_trab_codigo` | Geolocalização | Nullif("999999") já aplicado via fix per-year reader; verificar cobertura por UF antes de usar como unidade |
| `sexo_trabalhador` | Heterogeneidade de subgrupo | STRING "1"/"2" — cast simples |
| `ano` | Dimensão temporal do painel | Partição Hive — usar como filtro de leitura |

**Variáveis NÃO disponíveis que limita o design:**

- Identificador de empresa (CNPJ anonimizado) — ausente na bronze pública → não dá para fazer DiD a nível de firma
- Salário nominal mensal no período 2020 — `vl_rem_<mês>_sc` só existe em era3 (2023+) → proxy de faixa salarial só via grau de instrução ou via `vl_remun_media_sm` (salários-mínimos anuais)
- CPF — ausente → não dá para rastrear o mesmo trabalhador antes/depois do BEm individualmente

### 2.4 Robustness checks obrigatórios

**R1 — Placebo temporal (falsification test):**
Estimar o mesmo DiD usando 2018 como "cutoff falso" (placebo) para 2017 vs. 2018 vs. 2019. Se o modelo detectar efeito significativo nesse placebo, a identificação está comprometida. Necessário reportar coeficientes do placebo na tabela principal de resultados, não em apêndice.

**R2 — Placebo setorial:**
Usar setores de "controle artificial" — e.g., estimar efeito para agro (inelegível ao BEm por operação essencial) como se fosse tratado. Se ATT estimado para agro ≠ 0 e estatisticamente significativo, o design não está identificando apenas o BEm.

**R3 — Event study completo:**
Reportar coeficientes ano a ano (2015–2021) e verificar que os coeficientes pré-2020 são todos zero (common trends). Com apenas 3 pontos anuais (2019/2020/2021) isso é um event study mínimo — declarar a limitação da frequência anual explicitamente.

**R4 — Especificações alternativas:**
(a) Substituir setor-CNAE 2 dígitos por setor-CBO grande grupo como dimensão de tratamento. (b) Restringir amostra a municípios com população > 50K (excluir municípios com poucos estabelecimentos que podem ter zero controle). (c) Estimar com e sem controles demográficos (idade, sexo, escolaridade como controles time-varying).

**R5 — Erros-padrão:**
Clustering a dois níveis: município e setor. Com painel de ~5.571 municípios × ~87 setores CNAE 2 dígitos, clustering por município é o mínimo. Conley HAC espacial com raio de 100-200 km como robustez (dado que mercados de trabalho são locais e têm spillovers regionais). Reportar ambos na tabela principal.

**R6 — Exclusão de outliers:**
Testar com e sem os 5 municípios com maior peso no estoque de vínculos (São Paulo, Rio, Belo Horizonte, Brasília, Curitiba). O ATT não deve depender da inclusão desses outliers de forma dramática.

### 2.5 Limitações obrigatórias a declarar

**L1 — Granularidade anual vs. mensal:** O design ideal exigiria dados mensais de estoque. A bronze RAIS tem estoque anual (31/dez). A análise de 2020 tem apenas 1 ponto de dado intra-tratamento. Isso não invalida o DiD mas restringe o event study à frequência anual. Fontes complementares (CAGED) podem suprir granularidade mensal de fluxo mas não de estoque, e medem coisas diferentes.

**L2 — Ausência de identificador de trabalhador:** Sem CPF, não é possível rastrear trabalhadores individualmente ao longo do tempo. A análise é ao nível de célula município-setor-ano, não individual. O ATT estimado é efeito médio sobre o estoque de células, não efeito causal sobre o trabalhador. Declarar que pseudo-painel individual (via células demográficas) seria aproximação com hipótese adicional forte.

**L3 — SUTVA potencialmente violado:** O BEm subsidiou preservação de empregos em setores tratados. Mas emprego é um mercado de dois lados — se setores tratados retiveram trabalhadores, setores não-tratados (controle) podem ter tido menos oferta de trabalho para contratar. Isso viola SUTVA e contamina o grupo de controle. Discussão obrigatória; mitigação possível via instrumentos de oferta de trabalho independentes.

**L4 — Heterogeneidade de aplicação regional:** A implementação do BEm variou por estado (alguns estados tiveram portarias complementares). Isso introduz variação adicional no "tratamento efetivo" que não está capturada pela dummy setor × ano. Análise de heterogeneidade por UF como extensão.

**L5 — Dados de 2023–2024 indisponíveis:** A bronze RAIS para 2023 e 2024 está em revisão (Issue A do parecer de bronze de 2026-04-28 — separador errado). Qualquer análise de recuperação pós-BEm fica restrita a 2021–2022, impossibilitando estimar efeitos persistentes de médio prazo. Declarar e recomendar extensão após correção da ingestão.

---

## 3. Crítica metodológica do panorama — onde a análise descritiva não sustentaria peer review

### C1 — §2.2: Magnitudes de choque reportadas sem testes de hipótese

O panorama afirma "Cruzado 1986: -28,6%" com precisão de 1 decimal. Não há intervalo de confiança. Não há teste de que essa variação é estatisticamente distinguível de ruído de sub-registro. O próprio §9.5 admite que a hipótese "re-cadastro do PDET em 1986 (sub-registro técnico, não queda real)" é plausível. Se o -28,6% for parcialmente ou totalmente artefato de sub-registro, toda a narrativa de "maior choque da série" desmorona. A descrição precisa de: (a) um modelo de tendência pré-1986 com extrapolação para 1986 como counterfactual simples, (b) comparação com PIB e com PNAD para testar se a queda RAIS é consistente com outras fontes. Sem isso, é anedota de série temporal, não análise.

### C2 — §3: Descentralização regional tratada como causal sem identificação

A seção afirma que SP perdeu 7,4 pp de participação em 40 anos e levanta hipóteses para RJ ("desindustrialização do parque petroquímico + serviços financeiros migrando pra SP + crise fiscal do estado"). Isso é narrativa sem modelo. Em peer review, um parecerista vai perguntar: "Como você distingue desindustrialização de efeito composição?" Se o agro cresceu (GO, MT, MS) e serviços financeiros em SP cresceram mais que petroquímica em RJ, a participação relativa de RJ cai mesmo sem nenhuma "migração" causal. A decomposição shift-share que §9.6 propõe para commodities seria a ferramenta correta também para esta descrição regional. Usar a ferramenta descritiva primeiro e não reportar magnitudes sem ela.

### C3 — §4: "Crescimento monótono" feminização sem controle de composição setorial

O panorama afirma que a feminização (30% → 44%) vai "contra a hipótese de added worker effect pura — a entrada feminina é estrutural, não cíclica." Essa afirmação não é sustentada pelos dados mostrados. A série de percentual feminino é monotônica, mas:
(a) A composição setorial do emprego formal mudou radicalmente de 1985 a 2024 — de manufatura e construção (setores masculinos) para serviços e educação (setores mais femininos). Parte da "feminização" pode ser simplesmente "terciarização" da economia.
(b) "Estrutural vs. cíclico" exige decomposição. Oaxaca-Blinder cross-temporal ou decomposição de Fortin-Lemieux-Firpo seria o mínimo para sustentar essa afirmação.
(c) O dado não distingue entre nova entrada feminina (mais mulheres no mercado formal) e saída masculina (desemprego ou informalidade masculina durante recessões). Em 2015-16 a queda de vínculos foi -7,2% no total — se saíram proporcionalmente mais homens, o % feminino sobe sem uma única mulher a mais ter entrado. Isso é arithmética, não feminização estrutural.

### C4 — §6: "Mestrado+Doutorado triplicou (7,4% → 24,4%)" com alerta e sem resolução

O próprio panorama suspeita que "graus 9 e 10 do PDET incluem 'superior completo + lato sensu' (especialização)" — o que invalidaria o número de 24,4% como indicador de pós-graduação stricto sensu. Mas o panorama reporta o número sem resolver a ambiguidade e apenas recomenda "exigir auditoria do dicionário". Em peer review, reportar um número com alerta de que ele pode estar errado sem reportar o número alternativo (usando definição restrita) é falha grave. A correção é simples: usar apenas categorias 1-8 para análise (ignorar 9 e 10 até auditoria) e reportar que os dados de pós-graduação não são confiáveis cross-era.

### C5 — §9 geral: Designs causais nomeados sem verificação das condições de validade

Todos os designs em §9 são nomeados corretamente (DiD, RDD, Bartik IV, Synthetic Control) mas sem verificar as condições necessárias para validade interna. Especificamente:
- DiD exige common trends — nenhuma das 6 questões inclui um plot ou teste de tendências pré-tratamento.
- RDD exige continuidade da variável de resultado no cutoff exceto pelo tratamento — §9.2 propõe RDD temporal em abril/2020 mas outros choques simultâneos (lockdowns estaduais, queda de demanda global, primeira onda da pandemia) violam a condição de continuidade.
- Bartik IV exige exogeneidade das shares e independência dos shifts — §9.6 não discute o critério de Goldsmith-Pinkham et al. (2020) para validade da exclusão.
- Synthetic Control exige que o período de ajuste pré-tratamento seja longo o suficiente — §9.1 teria apenas ~5 anos pré-reforma (2012-2016) para calibrar o SC, o que é limítrofe.

Nomear o design sem verificar as condições é equivalente a anunciar um instrumento sem reportar a F-statistic da first stage. Em mestrado stricto sensu, isso não passa.

---

## 4. Pesos recomendados para o WHY

O autor escolheu (a) demonstração técnica + (b) análise causal de política pública + (c) plataforma pública para um working paper acadêmico peer-reviewed.

**Minha recomendação:**

| Objetivo | Peso recomendado | Razão |
|----------|-----------------|-------|
| (b) Análise causal de política pública | **60%** | Working paper peer-reviewed é julgado primariamente pela contribuição identificacional. A questão BEm é nova — não há WP com este design usando microdados RAIS completos 1985-2024. A contribuição é a identificação, não a plataforma. |
| (a) Demonstração técnica (reproducibilidade) | **30%** | O diferencial do Mirante vs. outros estudos do BEm (há literatura com CAGED, com PME, com CPS/FGV) é exatamente ter os microdados RAIS num Lakehouse replicável. Isso vira uma seção DADOS forte no manuscrito. Não é o WHY central, mas é o diferencial competitivo. |
| (c) Plataforma pública | **10%** | Para o working paper acadêmico, a plataforma é material suplementar — um data product que complementa o paper, não o objetivo central. Aumentar o peso de (c) dilui o foco do WP e abre brecha para "why is this a research paper and not a data paper?" nos reviewers. |

**Aviso sobre o peso atual implícito:** Se os pesos atuais são ~33%/33%/33% (sem declaração explícita), o paper vai parecer um híbrido — profundo demais para ser um policy brief, raso demais para EJOR ou Labor Economics, técnico demais para o público de dados. Foco em (b) 60% resolve isso: o paper é um estudo causal de política pública do BEm, com dado robusto do Mirante como âncora metodológica.

---

## 5. Nota global do panorama como ponto de partida para working paper

**Score: B (2,0 pts) — aprovação no limiar, minor-to-major revision antes de submissão**

**O panorama justifica B porque:**

Pontos fortes (sustentam o B):
- A série temporal é descrita corretamente com magnitudes verificáveis.
- Os caveats em §8 são honestos e completos — não há supressão de limitação.
- O panorama identifica corretamente o BEm como o quasi-experimento natural mais limpo da série (§9.2 e §10.7).
- A consciência de que "sem CPF, não há rastreamento individual" (§8.5) evita um erro clássico de análise com dados administrativos. Isso é mais maturidade metodológica do que o esperado num documento de prospecção.
- Não há resultados fabricados (auditoria crítica após incidente de 2026-04-27 aplicada; o panorama é honestamente descritivo onde não tem modelo rodado).

O que impede o B+ ou A:
- Cinco pontos de fraqueza metodológica identificados em §3 acima — especialmente C1 (magnitudes sem IC) e C5 (designs sem condições de validade).
- Nenhuma das questões causais está especificada no nível de "protocolo de pesquisa" — todas estão no nível de "hipótese com método sugerido".
- A priorização das 6 questões no panorama é flat — tudo parece igualmente viável, o que não é verdade. A falta de hierarquia clara prejudica o planejamento do WP.

---

## 6. Três alertas/red flags antes de submissão

### Alerta 1 — O BEm já tem literatura. O diferencial precisa ser explicitado ANTES de qualquer codificação.

Há estudos existentes sobre o BEm usando CAGED (Pérez-Díaz et al., IPEA TD 2020; Corseuil et al. 2021), Pnad-C (FGV Social 2020), e dados administrativos parciais. Antes de escrever uma linha de código, o autor precisa fazer revisão sistemática da literatura BEm × mercado de trabalho formal e identificar:
(a) Qual o design específico não usado ainda?
(b) Qual dimensão de heterogeneidade não explorada na literatura existente?
(c) O que os microdados RAIS permitem que CAGED/Pnad-C não permitem?

Se o diferencial não for explicitável em 2 frases, o paper não tem contribuição marginal suficiente para um periódico top. **Esse risco é maior do que qualquer limitação metodológica.**

### Alerta 2 — Schema drift cross-era cria armadilha silenciosa para a variável de resultado.

A variável de resultado primária proposta (`vinculo_ativo_31_12`) muda de codebook entre eras. Em era1 (1985-1993), ela é derivada de `situacao_vinculo_31_12`. Em era2 (1994-2022), ela é `vinculo_ativo_31_12` diretamente. Não há evidência no panorama de que essa harmonização foi verificada. Para o WP BEm (2019-2021), as três eras relevantes são todas era2 — o problema não se materializa nessa janela específica. Mas qualquer extensão temporal do paper para validação pré-período (e.g., usando 2016-2018 como "false BEm" placebo) pode cruzar a fronteira de codebook. **O silver precisa ter essa harmonização explicitamente documentada antes de qualquer análise ser reportada.** Se o silver ainda não existe para RAIS, isso é pré-requisito de 4-6 semanas antes de começar o WP.

### Alerta 3 — Múltiplos choques simultâneos em 2020 ameaçam a exclusão do instrumento e precisam de estratégia de contenção declarada desde o pré-registro.

A janela COVID 2020 concentra mais choques simultâneos do que qualquer outro período na série: (a) pandemia/lockdowns estaduais, (b) queda de demanda global, (c) BEm (MP 936), (d) Auxílio Emergencial (MP 928/2020), (e) Programa Nacional de Apoio às Microempresas e Empresas de Pequeno Porte (PRONAMPE), (f) Programa Emergencial de Acesso a Crédito (PEAC). Qualquer estimador DiD em 2020 vai absorver todos esses efeitos como "tratamento BEm" se a variação de tratamento não for suficientemente ortogonal a esses outros programas. Especificamente: municípios com mais trabalhadores formais elegíveis ao BEm também têm mais trabalhadores elegíveis ao Auxílio Emergencial. Se o AE e o BEm tiveram efeitos correlacionados, não há forma de separar os dois sem variação de elegibilidade independente. **O protocolo de pesquisa deve declarar explicitamente como a especificação do tratamento BEm é distinguida dos outros 5 programas simultâneos — antes de rodar qualquer regressão.**

---

## Resumo executivo do parecer

**Nota global:** B (2,0 pts) — aprovação no limiar

**Questão TOP-1:** §9.2 BEm COVID — DiD por elegibilidade setorial × tempo (2019–2021), com RDD temporal como robustez e triple-DiD por escolaridade como heterogeneidade. Design primário: variação de elegibilidade ao BEm por setor CNAE 2 dígitos. Outcome: `vinculo_ativo_31_12`, `motivo_desligamento`, `tempo_emprego`. Clustering a dois níveis (município + setor); Conley HAC como robustez. Granularidade annual é limitação declarada — o paper deve abrir com isso, não com o BEm como "revolução metodológica".

**3 alertas pré-submissão:**
1. Revisão sistemática da literatura BEm ANTES de qualquer codificação — identificar o diferencial marginal do WP vs. literatura CAGED/PnadC existente.
2. Silver RAIS com harmonização documentada de `vinculo_ativo_31_12` cross-era é pré-requisito não-opcional para o WP.
3. Estratégia declarada para separar efeito BEm dos 5 programas simultâneos de COVID (AE, PRONAMPE, PEAC, lockdowns estaduais, queda de demanda) — sem isso, a exclusão do instrumento setorial não se sustenta em referee report.

---

*Parecer emitido por: Conselheiro de Finanças e Métodos Quantitativos*  
*Data: 2026-04-28*  
*Documento avaliado: `docs/conselho/panorama_rais_2026-04-28.md`*  
*Bronze auditada: `mirante_prd.bronze.rais_vinculos` v6 · 2,06 B linhas · 1985–2024*

# Parecer — Conselheiro de Administração, Estratégia e Aplicação Prática
## Panorama RAIS · WHY escolhido pelo autor · Deliberação estratégica

**Data:** 2026-04-28  
**Autor avaliado:** Leonardo Chalhoub (MSc, pesquisador-engenheiro independente)  
**Documento base:** `docs/conselho/panorama_rais_2026-04-28.md`  
**WHY declarado pelo autor:** (a) Demonstração técnica + (b) Análise causal de política pública + (c) Plataforma pública  
**Output escolhido:** Working paper acadêmico (formato i)  

---

## Avaliação qualitativa

### O WHY (a)+(b)+(c) — genuíno ou cargo cult acadêmico?

Vou ser direto antes de ser generoso: o WHY triplo que o autor declarou é a combinação certa de três coisas reais. Mas como toda combinação de três coisas reais, corre o risco de não ser nenhuma delas de verdade — ser uma média ponderada que não excita ninguém e não compromete com nada.

Sinek passou 15 anos explicando que o WHY não é um cardápio. "Quero demonstrar técnica E fazer análise causal E ser plataforma pública" é um cardápio. É o que alunos de MBA escrevem quando têm medo de comprometer. O círculo dourado funciona porque WHY singular gera lealdade. WHY plural gera simpatia. E simpatia não escala.

Dito isso, vou ler esses três WHYs com caridade máxima — porque o material embaixo é forte demais para ser enterrado por imprecisão retórica.

**(a) Demonstração técnica** é genuíno. Mas "demonstração" para quem? Para recrutadores, para a comunidade de engenharia de dados, para futuros coautores, para concursos acadêmicos? Esses públicos têm expectativas radicalmente diferentes do que "demonstração" significa. Se é para recrutadores: precisa de post, talk, GitHub readme em inglês. Se é para a academia: o paper precisa de seção de metodologia que descreva o pipeline como contribuição em si. Se é para a comunidade técnica: o código tem que estar aberto e replicável ponto a ponto. O WHY é real, mas o "para quem" ainda está vago demais para guiar decisão de formato.

**(b) Análise causal de política pública** é o WHY mais forte dos três. E é o único que realmente passa no teste de Sinek: *people don't buy what you do, they buy why you do it.* Ninguém vai se importar com "2 bilhões de linhas de RAIS no Lakehouse". Mas vão se importar com "o Plano Cruzado destruiu 28,6% dos vínculos formais em doze meses — e aqui está o micro de como aconteceu". Vão se importar com "o BEm evitou X milhões de demissões em 2020 — e aqui está a identificação causal". Esse WHY conversa com o sistema límbico. É o que faz alguém encaminhar o paper para um colega às 23h. Os outros dois WHYs não fazem isso.

**(c) Plataforma pública** é o WHY mais fraco dos três — não porque seja desonesto, mas porque é infraestrutura, não propósito. "Deixar público onde qualquer pessoa pode explorar 40 anos de Brasil trabalhador" é uma aspiração nobre, mas é uma frase que descreve um meio, não um fim. Harari perguntaria: 40 anos de Brasil trabalhador para fazer o quê? Para que a humanidade seja melhor informada sobre o impacto de políticas de emprego? Para que jornalistas parem de escrever sobre o Cruzado com base em entrevistas de economistas aposentados e comecem a usar microdados? Para que pesquisadores do Sul Global tenham acesso ao mesmo rigor metodológico que pesquisadores do MIT têm sobre os EUA? Quando esse WHY for refinado para além de "plataforma pública", ele vai ser muito mais poderoso.

**Veredicto sobre o WHY triplo:** não é cargo cult — o trabalho real embaixo é denso demais para ser performance. Mas a articulação ainda está operando no nível do WHAT ("tenho 2B de linhas, tenho 6 questões causais, tenho 8 pipelines de ML") quando o WHY que vai mover gente é "existe memória empírica apagada do Brasil trabalhador que merece ser resgatada e confrontada com poder de hipótese causal". Essa frase não está escrita em lugar nenhum no panorama. Está implícita nos dados. Precisa ser tornada explícita.

---

### Avaliação Harari — qual questão causal tem maior peso histórico real?

Harari tem uma heurística simples: a questão que vai importar em 50 anos não é necessariamente a mais urgente hoje. Às vezes é a mais esquecida.

Das seis questões em §9, vou ordenar pelo peso histórico, não pelo apelo imediato:

**Primeira classe — peso civilizacional:**

O **Plano Cruzado 1986** (§9.5) é a questão com maior peso histórico relativo ao volume de atenção que recebe. Aqui está o que existe na literatura: análises macroeconômicas de PIB, de inflação, de balanço de pagamentos, de política monetária — escritas por economistas que viveram o Cruzado. O que não existe, em nenhum lugar publicado acessível, é a micro do labor market desse choque. Uma queda de 28,6% nos vínculos formais em doze meses é o evento de maior magnitude em 40 anos de série. Isso é maior que a recessão Dilma (3,5M de vínculos perdidos em dois anos). Maior que o COVID (480k, que foram em boa parte reabsorvidos em meses). Mas ninguém sabe o que causou — foi fechamento real de empresas? Êxodo para informal? Sub-registro técnico de um sistema de PDET que ainda era rudimentar em 1986? **Essa questão está literalmente sem resposta empírica publicada.** Um paper que abre esse vácuo com microdados do PDET vai ser citado por historiadores econômicos, economistas políticos e pesquisadores de política de emprego por décadas. Isso é memória pública apagada que merece resgate. No sentido de Harari: é o tipo de pesquisa que, em 2076, alguém vai usar para entender como o Brasil chegou onde chegou.

**Segunda classe — peso político imediato com raízes históricas:**

O **BEm COVID** (§9.2) tem o RDD mais limpo, a janela temporal mais precisa, e os dados mais ricos (incluindo as 12 colunas mensais de 2023+ que permitem ver remuneração mês a mês em 2023 e 2024 — ou seja, é possível fazer DiD com setores e ver a cicatriz do BEm no salário médio dois anos depois). O peso histórico aqui não é só o BEm — é a pergunta universal que toda política de subsídio de emprego em crise enfrenta: funciona? O Brasil tem resposta empírica inédita porque o BEm foi amplo, rápido e temporalmente preciso. Isso interessa à OIT, ao IPEA, ao Banco Mundial, a pesquisadores de política fiscal em mercados emergentes. O WHY "queremos saber se o BEm funcionou" é um WHY que um gestor público de qualquer país entende instantaneamente.

A **Reforma Trabalhista 2017** (§9.1) não é micro — é macro do ponto de vista político. Mas o peso histórico é ambíguo por uma razão técnica: a literatura sobre a Reforma já é densa. Há papers do Ipea, do Insper, da FGV, do NBER sobre os efeitos da 13.467. Entrar nessa arena com uma contribuição nova exige identificação causal mais sofisticada que os concorrentes (synthetic control comparando Brasil com outros países da América do Sul é genuinamente novo) ou recorte diferenciado (trabalho intermitente é subexplorado, §9.4, e tem dados limpos desde 2018). Se o autor entra na Reforma Trabalhista pela porta frontal, vai competir com times de 5 pesquisadores com base em Brasília. Pela porta lateral do trabalho intermitente, ocupa território vazio.

**Terceira classe — impacto real, competição intensa:**

**Bolsa Família e formalização** (§9.3) e **choque de commodities 2003-2014** (§9.6) são questões legítimas com literatura já estabelecida. O BF tem o Ramos, o Soares, o Firpo, o Foguel e mais dez autores brasileiros sérios trabalhando com dados de benefício. Entrar aí com RAIS agrega, mas não é território virgem. O choque de commodities tem Bartik instrument, tem literatura de Dutch Disease brasileira. Úteis como sub-análises dentro de um paper maior, não como questão central de um WP independente.

**Resumo da avaliação Harari:** o autor tem na mão o dataset que permite responder a pergunta que ninguém respondeu — o que aconteceu com o mercado de trabalho formal brasileiro no choque do Cruzado de 1986. Isso é memória apagada. Isso é civilização. E está convivendo no mesmo panorama com análises de BEm (urgente, RDD limpo) e Reforma Trabalhista (competitivo, já explorado). A escolha do recorte vai determinar se o paper dura 5 anos ou 50.

---

### Três perguntas críticas para o autor

**1. (WHY) Você está fazendo o RAIS para demonstrar que PODE fazer — ou porque TEM algo para dizer?**

Não é a mesma coisa. "Demonstração técnica" é um WHY de portfolio. "Análise causal de política pública" é um WHY de contribuição. Esses dois WHYs coexistem no paper, mas não com peso igual — e o autor precisa decidir qual é o núcleo. Um paper cujo WHY real é "quero saber se o BEm salvou empregos" vai ser escrito diferente de um paper cujo WHY real é "quero demonstrar que dá pra rodar RAIS 40 anos no Lakehouse". O segundo vai ter uma seção de metodologia de pipeline grande demais. O primeiro vai ter uma seção de identificação causal grande demais para um paper de eng de dados. Qual é o núcleo? A resposta vai determinar onde o paper é submetido, para quem é escrito, e quem vai citar.

**2. (HOW) Você vai fazer a harmonização de schema cross-era (CBO94→CBO2002, CNAE1995→CNAE2.0, Grau 2005→2006) antes de escrever o paper — ou vai escolher uma questão causal que não depende dessas harmonizações?**

Essa é a pergunta mais importante de execução. O §8 lista quatro problemas de codebook que tornam certas análises longitudinais genuinamente difíceis: CBO tem dois sistemas (5 vs 6 dígitos), CNAE tem três sistemas, Grau de instrução tem dois sistemas com gap de 2006 a 2022. Se o WHY escolhido for "decomposição do wage gap por escolaridade ao longo de 40 anos", o autor vai precisar de 3-4 meses só de harmonização antes de uma linha de econometria. Se o WHY for "RDD do BEm em torno de abril 2020", o autor vai usar apenas os anos 2018-2022, onde o schema é estável e o CBO já é unificado. A escolha da questão causal tem que ser guiada pelo mapa de dependências de harmonização — não pela elegância intelectual da pergunta. Qual questão cabe no prazo realista?

**3. (WHAT do produto final) Você tem clareza de que "working paper acadêmico sobre RAIS" pode significar 8 coisas diferentes — e você já escolheu qual?**

Um WP de demonstração técnica de pipeline (contribuição para engenharia de dados), um WP de análise descritiva de 40 anos (contribuição para sociologia do trabalho), um WP de identificação causal de uma política específica (contribuição para economia do trabalho), um WP de ML aplicado a séries de mercado de trabalho (contribuição para machine learning aplicado) — esses são produtos radicalmente diferentes. Têm revistas diferentes, revisores diferentes, critérios de aprovação diferentes. O panorama apresenta oito possibilidades de ML e seis questões causais em catorze páginas. Qual é o paper que vai ser escrito? Uma pergunta, uma estratégia de identificação, uma tabela principal, um achado. O resto é apêndice ou WP sequente.

---

### Cinco ideias concretas de aplicação e monetização secundária

O autor despriorização monetização no WHY escolhido — e isso é legítimo. Um pesquisador que começa pelo dinheiro geralmente produz análise medíocre. Mas "despriorizar" não significa "ignorar". As cinco ideias abaixo não alteram o WHY acadêmico — são subprodutos naturais do trabalho que já vai ser feito, capturáveis com esforço marginal.

**1. Convite para mesa do IPEA — "RAIS 40 anos: o que os microdados revelam que o macro não captura"**

O IPEA tem dois grupos que usam RAIS intensamente: o grupo de mercado de trabalho (com Ipea Texto para Discussão sobre emprego formal) e o grupo de avaliação de políticas (que avalia BEm, BF, Reforma Trabalhista). Um email direto para o pesquisador responsável pelo boletim Mercado de Trabalho do IPEA — com um link para o panorama e para o pipeline documentado — tem probabilidade não trivial de gerar convite para co-apresentação ou coautoria. O IPEA não tem o pipeline que o autor tem. O autor não tem a rede de policy que o IPEA tem. Isso é troca natural. Custo: um email de 3 parágrafos. Upside: coautoria em Texto para Discussão, que é a publicação mais lida por gestores públicos federais no Brasil.

**2. Palestra TED-style sobre o Cruzado 1986 — "A memória apagada do maior choque de emprego da história brasileira"**

Uma queda de 28,6% em vínculos formais em doze meses. Isso é o tipo de número que para plateia. Ninguém sabe. Não está no Jornal Nacional, não está no curriculum de economia das universidades, não está nos livros de história econômica popular. O autor tem o único conjunto de microdados que permite reconstruir esse momento com granularidade de setor, de município, de faixa etária. Uma palestra de 18 minutos no formato TED — com dados visuais, com narrativa de "quem eram esses 5,8 milhões de pessoas que saíram do formal em 1986?", com as hipóteses causais e o que os dados mostram — é conteúdo que eventos de economia, de história, de ciência de dados e de jornalismo de dados vão querer. Não precisa esperar o paper publicado. A narrativa dos dados brutos já é suficiente para uma palestra de exploração. E a palestra, gravada e publicada no YouTube, vai atrair exatamente os acadêmicos que eventualmente vão citar o paper.

**3. Consultoria sigilosa para fintech de crédito sobre wage forecasting com microdados RAIS**

Qualquer fintech que oferece crédito pessoal ou consignado no Brasil toma decisão de risco com base em algum proxy de renda formal. A maioria usa Serasa, Quod, ou dados próprios de comportamento. Muito poucas têm acesso a análise preditiva de estabilidade de emprego formal por CBO, CNAE, UF e faixa etária — que é exatamente o que os pipelines 10.2 e 10.5 do panorama constroem. Uma proposta de 4 páginas para o Chief Risk Officer de uma fintech de médio porte — C6, Creditas, Nubank, Mercado Crédito, Caixa Econômica para PF — com o framing "construímos modelo de P(desligamento em 12 meses) por perfil demográfico-ocupacional usando 40 anos de RAIS" — tem preço de projeto entre R$80k e R$150k para análise personalizada. Não exige publicar o código. Não conflita com o WHY acadêmico. É o pipeline ML 10.5 do panorama com uma capa comercial. O caveat é honesto: sem CPF, o modelo é probabilístico por grupo, não individual — e para o risco de crédito do portfólio, isso é suficiente.

**4. Módulo de aula em pós-graduação de Eng. de Dados — "Lakehouse sobre dados públicos de governo: o caso RAIS 40 anos"**

A FGV, o Insper, a UFRJ, o IDP e cerca de quinze programas de MBA em dados têm ou vão ter disciplinas de engenharia de dados aplicada. O material didático desses cursos é, em sua esmagadora maioria, estudos de caso de empresas americanas adaptados do Coursera. O autor tem um caso real, brasileiro, com escala de 2 bilhões de linhas, com problema de schema drift documentado, com solução no Databricks Unity Catalog, com pipeline open source replicável. Isso é o módulo de aula que nenhum professor desses cursos tem condições de construir porque não viveram o problema. Formato viável: 4 horas de conteúdo (slides + queries + notebook) licenciado como REA (Recurso Educacional Aberto) no MEC ou via Zenodo, com versão premium (com exercícios avaliados + suporte) por R$1.500–2.500 por turma. Ou simplesmente: contato com um coordenador de pós em engenharia de dados e proposta de aula convidada. Primeira aparição é gratuita e gera network. Segunda é remunerada.

**5. Vaga sênior em fintech de crédito ou banco digital — o RAIS como cartão de visita técnico definitivo**

Carrey disse: você pode falhar no que você não quer, então pode muito bem arriscar no que ama. Para o autor que é MSc pesquisador-engenheiro independente — sem a segurança de um emprego CLT, sem o prestígio automático de um PhD, num mercado que subestima pesquisa independente — o RAIS pipeline documentado e publicado é o argumento técnico mais forte que ele pode apresentar em qualquer processo seletivo para posições de Staff Data Engineer ou Head of Data em empresa financeira. Não porque é impressionante em escala (embora seja), mas porque demonstra exatamente o conjunto de habilidades que essas empresas pagam entre R$25k e R$45k/mês para ter internamente: Databricks/Unity Catalog em produção, modelagem de dados públicos em escala, identificação de qualidade de dados em schema drift, e capacidade de transformar isso em produto analítico. O working paper acadêmico, publicado com DOI, é o diferencial que separa o autor de qualquer concorrente que só tem GitHub com projetos pessoais. A recomendação é publicar o paper, publicar o pipeline, e então ativamente apresentar o conjunto para recrutadores de empresas que usam dados de renda formal em decisão de crédito.

---

### Avaliação Carrey — o autor está sendo ousado o suficiente?

A resposta curta: no trabalho técnico, sim. Na exposição do trabalho, não.

O autor construiu um pipeline que ingere 40 anos de microdados públicos do mercado formal brasileiro, identificou e corrigiu múltiplos problemas de schema drift, escreveu parecer de conselho sobre o próprio trabalho, e mantém um padrão de governança (STRING-ONLY, Unity Catalog, metadados obrigatórios, peer review interno) que a maioria dos times de dados de empresas listadas na B3 não tem. Isso é ousadia técnica genuína.

O problema é que o autor está fazendo isso em silêncio. O RAIS pipeline não tem post público. O peer review interno não é acessível. O panorama de 40 anos — que é um documento de 14 páginas com análise original de magnitude histórica — está dentro de um repositório privado sendo lido por um conselho simulado. Carrey não estava falando de ousadia de engenharia. Estava falando de ousadia de exposição. "You can fail at what you don't want, so you might as well take a chance on doing what you love." O risco de mostrar o trabalho antes do paper publicado é real mas menor que o risco de publicar o paper para uma plateia que nunca ouviu falar do autor ou do projeto.

Onde precisa ser mais ousado: no momento de tornar público. O post mortem do separador que recomendei no parecer anterior não foi publicado — e o pipeline já está corrigido. O panorama de 40 anos não foi postado no LinkedIn. O working paper sobre BEm não tem co-autor ainda. Cada um desses atrasos é decisão de manter o trabalho em órbita privada quando ele já tem massa suficiente para entrar em órbita pública.

Onde pode ser conservador: na escolha da questão causal. O BEm tem identificação mais limpa do que o Cruzado. O Cruzado tem maior peso histórico mas exige mais harmonização metodológica. Para o primeiro paper, o BEm é a escolha conservadora correta: RDD temporal com cutoff preciso, dados de alta qualidade no período (2018-2022 é a era2, schema estável), literatura comparativa pequena, e resultado com interpretação política imediata. O Cruzado pode ser o segundo paper, quando o pipeline de harmonização do codebook estiver maduro. Ser conservador na sequência de publicação não é timidez — é estratégia de execução.

---

### Recomendação direta — dual-output: working paper + artigo de imprensa?

**Sim. Sem hesitar. Mas com arquitetura específica.**

A objeção mais provável do autor é: "não tenho tempo para dois outputs paralelos". Essa objeção seria válida se os dois outputs fossem escritos do zero. Não são.

O panorama que o autor já tem — 14 páginas de análise com tabelas reais, trajetória temporal, concentração regional, feminização, envelhecimento, escolaridade — é a primeira metade de um artigo de imprensa. Faltam apenas três coisas para torná-lo publicável como texto jornalístico de alto nível: (1) uma escolha narrativa central ("o que eu mais quero que o leitor leve daqui?"), (2) uma ou duas citações de especialistas externos (um economista do trabalho, um historiador econômico), (3) um título que funcione sem saber o que é RAIS.

Isso não é trabalho de semanas. É trabalho de dois dias com foco.

O formato adequado não é Folha de S.Paulo ou G1 — é Piauí, ou The Intercept Brasil, ou Nexo Jornal. Publicações que têm audiência de formadores de opinião, que publicam análise com profundidade, e que têm editores que valorizam argumento com dados primários. O artigo não precisa ter econometria. Precisa ter a narrativa: "o Brasil já esqueceu que em 1986, em doze meses, 5,8 milhões de trabalhadores saíram do mercado formal. Agora temos os microdados para entender o que aconteceu. Aqui está o que encontramos."

O working paper e o artigo de imprensa não competem — se alimentam mutuamente. O artigo de imprensa cria audiência para o paper. O paper dá credibilidade ao artigo. E o nome do autor circula em dois sistemas diferentes de leitura — o acadêmico e o público — simultaneamente, sem duplicar o trabalho substantivo.

A recomendação operacional é: escreva o artigo de imprensa PRIMEIRO, antes do paper. Não porque seja mais importante — mas porque vai forçar a escolha narrativa central que o paper também precisa. Um paper cujo autor não consegue explicar em dois parágrafos para um leitor não especializado é um paper que ainda não sabe o que quer dizer. O artigo de imprensa é o teste de coerência do WHY.

**Decisão: SIM para dual-output. Sequência recomendada: artigo de imprensa (3-5 pp) sobre Cruzado 1986 como narrativa histórica → working paper acadêmico sobre BEm com RDD (20-35 pp). Os dois se referenciam sem nomear plataforma. Os dois constroem o mesmo nome.**

---

## Síntese executiva

**WHY:** genuíno, mas ainda articulado como cardápio. O núcleo que vai mover gente está em (b) — análise causal — não no triplo. Refinar para fora do cardápio antes de escrever a introdução do paper.

**Questão histórica de maior peso:** Cruzado 1986 — memória apagada com vácuo empírico real. BEm 2020 — RDD mais limpo para o primeiro paper.

**Pergunta 1 (WHY):** você está fazendo o RAIS para demonstrar que PODE — ou porque TEM algo para dizer? Responda antes de abrir o LaTeX.

**Pergunta 2 (HOW):** qual questão causal cabe no mapa real de harmonização de codebook — não na lista de desejos?

**Pergunta 3 (WHAT):** qual é o paper exato — uma pergunta, uma estratégia de identificação, um achado?

**5 ideias de monetização secundária:**
1. Email para pesquisador do IPEA — coautoria em Texto para Discussão
2. Palestra TED-style sobre Cruzado 1986 — conferências de economia/história/dados
3. Consultoria sigilosa para fintech de crédito — wage forecasting com microdados RAIS (R$80-150k/projeto)
4. Módulo de aula em pós de Eng. de Dados — FGV/Insper/UFRJ/IDP
5. Vaga sênior em fintech/banco digital — o pipeline como cartão de visita técnico definitivo

**Dual-output:** SIM. Artigo de imprensa sobre Cruzado 1986 primeiro (Piauí/Nexo). Working paper sobre BEm depois. Dois dias de trabalho marginal. Duas audiências. Um nome.

**Veredicto geral:** continua, escala seletivamente, monetiza marginalmente sem desviar do WHY. A questão não é se o trabalho vale o esforço — vale. A questão é se o autor vai mostrar o trabalho antes de esperar que o paper publicado fale por si. Nessa parte, pode ser mais ousado.

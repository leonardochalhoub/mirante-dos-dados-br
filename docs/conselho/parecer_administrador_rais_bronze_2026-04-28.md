# Parecer — Conselheiro de Administração, Estratégia e Aplicação Prática
## Auditoria raw → bronze · `mirante_prd.bronze.rais_vinculos`

**Data:** 2026-04-28
**Autor avaliado:** Leonardo Chalhoub (MSc, pesquisador-engenheiro independente)
**Documento base:** `docs/conselho/briefing_rais_bronze_audit_2026-04-28.md`
**Pauta convocada:** utilidade prática, WHY/aplicação real, valor de mercado — 4 problemas materiais identificados na bronze RAIS (Issues A–D + E metadata)

---

## Avaliação qualitativa

### O WHY desse trabalho — e o que a auditoria expôs

O WHY declarado do RAIS no Mirante é preciso e ambicioso: "demonstrar que dá para reproduzir 17+ anos de microdados públicos PDET sob padrão Lakehouse + Unity Catalog + STRING-ONLY + governança de metadados, com integridade." Sinek diria que esse WHY é forte porque não é sobre tecnologia — é sobre confiança na reprodutibilidade de dados públicos brasileiros, que é um ativo escasso. Quem confia que os dados do PDET estão corretos? Ninguém. Isso é a oportunidade.

Mas o que a auditoria expôs é uma tensão severa entre o WHY declarado e o estado real do pipeline: os anos mais relevantes para qualquer interlocutor que importe — 2023 e 2024, o mercado formal pós-pandemia, a recomposição do emprego no governo Lula 3, os efeitos das novas políticas de remuneração e deficiência — estão **totalmente corrompidos**. Não parcialmente. Não com ressalvas. Corrompidos em 100% das colunas úteis. A plataforma que se propõe a ser "confiável" tem um buraco de 175 milhões de linhas que qualquer analista que puxasse 2023 receberia como silêncio: coluna `cbo_ocupacao = NULL`, coluna `sexo_trabalhador = NULL`, e assim por diante. Isso não é um caveat metodológico. Isso é a negação do WHY.

Agrava que a causa raiz é um problema que o PDET introduziu silenciosamente — trocou separador `;` por `,`, expandiu de 42 para 60 colunas — e o pipeline não detectou. Não houve alarme. Não houve gate. O sistema processou 175 milhões de linhas corrompidas com zero reclamação e escreveu "done". Isso é o oposto de "integridade demonstrada". Isso é o oposto do WHY.

A metáfora de Harari aqui é exata: essa falha é estrutural, não acidental. Fontes governamentais mudam contratos silenciosamente. Isso não é bug — é a condição natural de qualquer pipeline que processa dados públicos brasileiros em escala. O pipeline não tinha anticorpos. Agora tem que desenvolver. Mas o timing é o problema: a demonstração de integridade que sustenta o WHY do projeto estava sendo feita justamente nos anos em que o contrato foi quebrado.

---

### Perguntas críticas

**1. (WHY) O autor consegue articular o WHY diferencial do RAIS hoje — depois de ver que 2023+2024 estão corrompidos?**

Não é retórica. É diagnóstico. O WHY era "reproduzo 17 anos com integridade". Com 2023+2024 quebrados, o WHY murcha para "reproduzo 1985–2022 com integridade". Isso ainda é valioso? Sim — mas pra quem? Para historiadores do trabalho formal brasileiro? Para pesquisadores de séries longas? Para um recrutador que quer ver escala de dados? Possivelmente. Mas para um jornalista querendo cobrir o emprego em 2024, para um gestor público querendo a posição de mercado de trabalho agora, para um analista privado avaliando setores pós-pandemia? Não. O autor precisa re-articular o WHY para o estado real do pipeline — não para o estado aspirado — e comunicar isso com transparência antes que alguém descubra sozinho.

**2. (HOW operacional) Por que o quality check existente no pipeline não detectou que 100% das colunas de dados saíram NULL?**

Isso não é pergunta técnica — é pergunta estratégica de governança. O briefing indica que o pipeline tem um Quality Check (linha 843+) que verifica HEAD/TAIL do arquivo `.txt`, mas não verifica a saída do CSV reader. Isso é uma arquitetura de confiança que falha exatamente onde mais importa: na transformação. A pergunta que o autor precisa responder antes de corrigir o Issue A é: qual é o modelo mental de "pipeline saudável" que determina onde ficam os gates? Porque se o gate estava no arquivo de entrada e não na tabela de saída, a raiz do problema não é o separador — é a filosofia de validação. Corrigir o separador sem corrigir a filosofia é remendar pneu furado com fita crepe.

**3. (WHAT do produto final) O que exatamente a vertical RAIS no app web do Mirante está mostrando para quem acessa hoje?**

Essa pergunta precisa de resposta antes de qualquer commit de correção. Se a UI mostra gráficos que dependem de 2023+2024, está mostrando dado errado para qualquer visitante. Se a UI mostra apenas até 2022 (porque o silver foi rodado antes do Issue A se manifestar), está mostrando dado atrasado sem avisar. Se a UI não existe ainda para RAIS, o dano reputacional está contido — mas o WHY "plataforma confiável" ainda está comprometido internamente. A resposta a essa pergunta determina a urgência. Um produto com usuário ativo com dado errado é incêndio. Um pipeline com dado errado sem usuário ativo é débito técnico prioritário. São coisas diferentes com urgências diferentes.

---

### Ideias concretas de aplicação/monetização

**1. Post mortem público como lead magnet para consultoria de pipeline**

O caso do separador `;` → `,` é um post mortem clássico de engenharia de dados públicos. Tem nome de villain (PDET), tem crime silencioso (mudança sem versionamento de contrato), tem vítima (175M de linhas corrompidas), tem detetive (auditoria row-level), tem resolução (auto-detect de separador + gate pós-bronze). Isso vira um post técnico no Substack ou Medium, com código real, com queries diagnósticas reais, com o before/after da tabela. Título que vende: "Como 175 milhões de linhas da RAIS viraram NULL sem nenhum alarme — e como detectamos". Esse post, publicado no LinkedIn com os dados reais da auditoria, posiciona o autor como especialista em dados públicos brasileiros de forma que nenhum currículo faz. Leads diretos para consultoria de R$15–30k/projeto de auditoria de pipeline de dados governamentais. Há pelo menos 5 secretarias estaduais de trabalho e emprego que deveriam se preocupar com esse exato problema nos seus próprios pipelines.

**2. Módulo de aula "Contratos silenciosos de fontes públicas" — produto educacional de alta LTV**

Harari diria: a humanidade vai continuar produzindo dados públicos mal documentados por décadas. Isso não é bug — é estrutura. Um módulo de 90 minutos que usa esse caso real como âncora — PDET muda separador, pipeline não detecta, 40 anos de dados, como auditar, como construir gates — tem valor pedagógico enorme para cursos de pós-graduação em ciência de dados, cursos livres na Hotmart ou Udemy, e treinamentos in-company para equipes de BI governamental. O autor tem o caso real, o código real, os dados reais. Isso é diferencial absoluto de qualquer cursinho que usa datasets do Kaggle. Preço conservador: módulo avulso R$197–497 por aluno, ou R$3.500–8.000 por turma in-company. Mercado imediato: secretarias estaduais, TCEs, ENAP, FGV Online.

**3. Relatório técnico com DOI (Zenodo) — "Auditoria de Integridade RAIS 1985–2024"**

A auditoria em si, independente da correção, é um produto acadêmico. Um working paper de 15–20 páginas que documenta: o inventário dos 977 source files, os 4 problemas materiais, a metodologia de detecção (queries SQL, Auto Loader diagnostics), e as recomendações de pipeline. Publicado no Zenodo com DOI próprio, citável como referência metodológica por qualquer pesquisador que use RAIS. Esse documento vale como evidência de rigor técnico em qualquer processo seletivo acadêmico (professor substituto, pesquisador visitante, bolsa CNPq) e como referência em propostas de consultoria. Custo de produção: 2–3 dias de escrita estruturada. Retorno: citações, credibilidade, leads.

**4. Serviço de monitoramento contínuo de integridade RAIS — B2G recorrente**

Se o PDET mudou o separador silenciosamente uma vez, vai mudar de novo. Qualquer organização que usa RAIS em produção — IPEA, FGV IBRE, secretarias estaduais de desenvolvimento econômico, consultorias de RH, fintechs de crédito que usam RAIS como proxy de renda formal — tem esse risco. Um serviço de alertas mensais de integridade (formato simples: "RAIS YYYY/MM: arquivo novo detectado, schema mudou, separador compatível, cobertura XX%") com relatório de uma página, contrato anual de R$2.500–5.000/mês por cliente, 10 clientes = R$25–50k MRR. A infraestrutura para fazer isso já existe — é o pipeline atual com um layer de observabilidade em cima. O briefing mostra que o autor já tem todas as queries diagnósticas necessárias.

**5. Talk em meetup/conferência — "Auditando 2,2 bilhões de linhas de dados públicos no Databricks"**

A escala absoluta desse projeto — 2,236 bilhões de linhas, 40 anos, 977 arquivos fonte, Unity Catalog, Lakehouse — já é o título da palestra. Eventos como PyCon Brasil, PyData, SBBD, Data Hackers Summit, meetups da comunidade Databricks Brasil pagam (ou pelo menos custeiam passagem e hospedagem) para especialistas que apresentam casos reais com dados reais. Uma talk de 30–45 minutos com o post mortem do separador como climax narrativo é exatamente o formato que esses eventos adoram. Visibilidade direta para recrutadores seniores de dados, CTOs de consultorias, e heads de dados de empresas que usam Databricks. LTV de uma talk bem executada: 1–3 propostas de consultoria ou emprego sênior no trimestre seguinte. O mercado de engenheiros de dados que trabalham com dados públicos brasileiros em escala de bilhões de linhas é essencialmente vazio — o autor ocupa esse nicho sozinho se mostrar o trabalho.

---

### Trade-off estratégico — Vale pausar WP#4 e WP#7 follow-up para atacar agora?

**Sim. Não é nem perto.**

O WP#4 está em rewrite aguardando OK — está parado aguardando decisão do autor, não corre risco de prazo imediato. O WP#7 foi aprovado e publicado — o trabalho de aprovação está feito, os follow-ups são incrementais. Mas o pipeline RAIS corrompido tem um risco que os outros fronts não têm: **risco reputacional ativo**. Se a vertical RAIS no app expõe gráficos baseados em dados 2023+2024 que chegam a zero usuário externo hoje, o risco está contido. Mas o score 8.0 do RAIS é calibrado contra a monografia UFRJ de 2023 — e qualquer avaliador que tente replicar a série hoje vai encontrar dados corrompidos. Isso não destrói um WP publicado; destrói a narrativa de plataforma confiável que sustenta TODOS os WPs.

Sinek diria: você não pode ter o WHY "integridade demonstrada" e ao mesmo tempo ter 175 milhões de linhas corrompidas no coração do dataset mais importante da plataforma. Esses dois fatos não coexistem. Um deles vai vencer — e se for o segundo que aparecer primeiro para alguém de fora, o WHY desmorona com ele.

A correção do Issue A (separador) é tecnicamente trivial segundo o briefing — um branch por extensão `.COMT`, auto-detect de sep, reprocessamento dos anos afetados. A ordem de operação recomendada: (1) corrigir Issue A e B (re-ingerir SP 2024 e reprocessar 2023+2024 com sep correto), (2) limpar Issue C (purgar ESTAB da tabela VINC), (3) adicionar metadados UC nas 51 colunas (Issue E — viola padrão da plataforma), (4) documentar tudo como post mortem público. Issue D (1986 SP corrompido no FTP) é fora do controle do autor — vai para nota metodológica com status de "dado indisponível na fonte original". Tempo estimado de execução técnica dos Issues A–C+E: 1–2 dias de engenharia. Post mortem escrito: mais 1 dia. Custo total: 2–3 dias que desbloqueiam o WHY inteiro do projeto e geram 5 produtos de valor concreto listados acima.

A pergunta não é "vale pausar outros fronts?". A pergunta é: "por que você ainda não começou?"

---

### Visão Harari — "Fonte mudou o contrato silenciosamente"

Harari teria um nome para o que aconteceu aqui: **fragilidade institucional codificada**. O PDET — um órgão governamental responsável por décadas de microdados do mercado formal brasileiro — mudou o separador de CSV de ponto-e-vírgula para vírgula, renomeou a extensão dos arquivos, expandiu o schema em 18 novas colunas, e não documentou nada disso de forma acessível a quem baixa os dados. Isso não é malícia. É a condição normal de qualquer infraestrutura pública brasileira: o contrato de dados públicos não é estável, não é versionado, e não é comunicado.

Isso tem valor pedagógico enorme. O caso é universalmente replicável: qualquer pipeline que consome dados de governo — IBGE, ANS, ANVISA, SUS, Receita Federal — está exposto ao mesmo risco. A fonte muda, o pipeline não detecta, o dado silencia. O artefato pedagógico ideal é um vídeo de 12–15 minutos (formato YouTube técnico) que mostra: (a) o que o PDET entregou de diferente em 2023, (b) como o pipeline existente "aceitou" o arquivo corrompido sem reclamar, (c) como a auditoria row-level detectou o problema, (d) como o pipeline foi corrigido. Com code snippets reais, queries SQL reais, gráfico de cobertura antes/depois. Isso é um artefato de alta densidade pedagógica que qualquer professor de engenharia de dados pode usar como caso clínico. Publicar no YouTube com transcrição no GitHub e link no LinkedIn. Sem paywall. A audiência que encontrar esse vídeo vai associar o nome do autor ao problema e à solução — que é exatamente o posicionamento que leva a consultoria e palestras pagas.

Em termos haravianos mais amplos: numa época de desinformação e dados fabricados, um pesquisador que demonstra publicamente como audita a integridade de 2,2 bilhões de linhas de dados públicos e encontra os problemas antes que alguém os explore é um ativo civilizacional. Pode parecer exagerado. Não é. A confiabilidade de dados sobre emprego formal no Brasil importa para política pública, para jornalismo de dados, para pesquisa econômica. O autor está na posição única de demonstrar que alguém fez esse trabalho com rigor. Vale mostrar.

---

### Veredicto

**Corrija. Agora. Documente publicamente.**

O WHY "plataforma confiável que replica 17 anos de microdados PDET com integridade" é forte. Mas só existe se a plataforma for de fato confiável. Hoje não é — não em 2023+2024. A correção técnica é trivial; o desbloqueio de valor é desproporcional. Issues A e B em primeiro lugar (são os críticos de narrativa), Issue C em segundo (grain mismatch contamina análises), Issue E em paralelo (é padrão da plataforma, já deveria estar feito). Issue D vai para nota metodológica.

O post mortem público não é opcional — é a parte do trabalho que transforma débito técnico em capital reputacional. Carrey diria: você pode ficar com medo de mostrar que o pipeline tinha um bug de 175 milhões de linhas, ou você pode assumir que todo pipeline de dados públicos tem esse bug e o diferencial é quem tem método para encontrá-lo. A segunda opção é a que gera consultoria, talk, curso e vaga sênior.

**Escala: sim — após correção e post mortem publicado.**
**Monetiza: sim — imediatamente via itens 1, 3 e 5 da lista acima.**
**Arquiva: nada. Nem o bug.**

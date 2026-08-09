<!-- Front matter da submissão PPP/IPEA — versão ANONIMIZADA (double-blind).
     Autoria e dados de contato NÃO entram no manuscrito: vão apenas no cadastro do sistema.
     Regras: ppp-ipea-submission-rules (memória). Fonte preservada: wp2-rap.tex -->

# Título (3 idiomas)

- **PT:** Três regimes, um programa: documentação, identificação causal e equidade do Bolsa Família
- **EN:** Three regimes, one program: documentation, causal identification, and equity of Bolsa Família
- **ES:** Tres regímenes, un programa: documentación, identificación causal y equidad de Bolsa Família

# Códigos JEL (até 5)

- **H53** — Government Expenditures and Welfare Programs
- **I38** — Welfare, Well-Being, and Poverty: Government Programs; Provision and Effects of Welfare Programs
- **I32** — Measurement and Analysis of Poverty
- **D63** — Equity, Justice, Inequality, and Other Normative Criteria and Measurement
- **C23** — Panel Data Models; Spatio-temporal Models

# Resumo (~200 palavras)

Este trabalho analisa o Bolsa Família entre 2013 e 2025, integrando três dimensões usualmente tratadas em separado: documentação reproduzível dos microdados, identificação causal das transições institucionais e equidade distributiva. Microdados mensais do Portal da Transparência (mais de 2,2 bilhões de registros) são consolidados em painel estado×ano por arquitetura *medallion*, deflacionados pelo IPCA (base dezembro de 2021). A identificação causal aplica diferenças-em-diferenças e efeitos fixos de dois sentidos sobre a Medida Provisória 1.061/2021 e a Lei 14.601/2023, com inferência robusta por *wild-cluster bootstrap*, testes de tendências paralelas, placebo e *leave-one-out*. A equidade é medida pelo índice de Kakwani, ordenado pelo IDH municipal, e por um índice de necessidade; um *benchmark* internacional compara o programa a quatro transferências condicionadas latino-americanas. Em termos reais, o gasto cresceu 283% entre 2018 e 2024. O efeito causal é grande sob erros HC3, mas indistinguível de zero sob *bootstrap* robusto, com tendências paralelas rejeitadas — ilustrando o ônus identificacional com poucos *clusters*. O índice de Kakwani confirma progressividade decrescente entre regimes; o índice de necessidade revela que estados líderes em valor per capita estão subatendidos frente à intensidade local da pobreza. Publicam-se o *pipeline*, os dados e os testes automatizados, viabilizando reprodução integral.

**Palavras-chave:** Bolsa Família; transferência condicionada de renda; avaliação de políticas públicas; equidade distributiva; reprodutibilidade.

# Abstract (~200 words)

This paper analyzes Brazil's Bolsa Família program between 2013 and 2025, integrating three dimensions usually treated separately: reproducible microdata documentation, causal identification of the institutional transitions, and distributive equity. Monthly microdata from the federal Transparency Portal (over 2.2 billion records) are consolidated into a state-by-year panel through a *medallion* architecture, deflated by the IPCA index (December 2021 base). Causal identification applies difference-in-differences and two-way fixed-effects estimators to Provisional Measure 1.061/2021 and Law 14.601/2023, with robust inference via *wild-cluster bootstrap*, parallel-trends tests, placebo, and *leave-one-out* checks. Equity is measured with the Kakwani index ranked by the municipal Human Development Index and with a need index; an international *benchmark* compares the program with four Latin American conditional cash transfers. In real terms, spending grew 283% between 2018 and 2024. The causal effect is large under HC3 errors but indistinguishable from zero under robust *bootstrap*, with parallel trends rejected — illustrating the identification burden with few *clusters*. The Kakwani index confirms progressivity that declines across regimes; the need index reveals that states leading in per-capita value are underprovisioned relative to local poverty intensity. The pipeline, dataset, and automated tests are released, enabling full reproduction.

**Keywords:** Bolsa Família; conditional cash transfers; public policy evaluation; distributive equity; reproducibility.

# Resumen (~200 palabras)

Este trabajo analiza el programa Bolsa Família entre 2013 y 2025, integrando tres dimensiones habitualmente tratadas por separado: documentación reproducible de los microdatos, identificación causal de las transiciones institucionales y equidad distributiva. Microdatos mensuales del Portal de la Transparencia (más de 2.200 millones de registros) se consolidan en un panel estado×año mediante una arquitectura *medallion*, deflactados por el IPCA (base diciembre de 2021). La identificación causal aplica diferencias-en-diferencias y efectos fijos de dos vías sobre la Medida Provisional 1.061/2021 y la Ley 14.601/2023, con inferencia robusta por *wild-cluster bootstrap*, pruebas de tendencias paralelas, placebo y *leave-one-out*. La equidad se mide con el índice de Kakwani, ordenado por el IDH municipal, y con un índice de necesidad; un *benchmark* internacional compara el programa con cuatro transferencias monetarias condicionadas latinoamericanas. En términos reales, el gasto creció 283% entre 2018 y 2024. El efecto causal es grande con errores HC3, pero indistinguible de cero bajo *bootstrap* robusto, con tendencias paralelas rechazadas — ilustrando la carga de identificación con pocos *clusters*. El índice de Kakwani confirma una progresividad decreciente entre regímenes; el índice de necesidad revela que los estados líderes en valor per cápita están subatendidos frente a la intensidad local de la pobreza. Se publican el *pipeline*, los datos y las pruebas, permitiendo su reproducción integral.

**Palabras clave:** Bolsa Família; transferencias monetarias condicionadas; evaluación de políticas públicas; equidad distributiva; reproducibilidad.

---

# RASCUNHO — Declaração de uso de IA (a ser ATESTADA pelos autores)

> ⚠️ **Este texto precisa refletir a verdade dos fatos.** A PPP proíbe redigir "integral ou
> majoritariamente o manuscrito" com IA e usá-la como "principal agente de decisão metodológica
> ou analítica". Só assinem a versão A se, de fato, a redação e as decisões analíticas forem de
> autoria humana, tendo a IA se limitado às categorias permitidas. Caso o texto atual tenha sido
> majoritariamente gerado por IA, é preciso reescrevê-lo substancialmente ANTES de declarar.

**Versão FIXADA (ajustada ao relato de autoria — atestada pelos autores):**

> Declaração sobre uso de inteligência artificial: a concepção da pesquisa, a descoberta, coleta
> e consolidação dos microdados públicos, as decisões metodológicas e analíticas, a obtenção e a
> interpretação dos resultados e a maior parte da redação são de autoria e responsabilidade
> exclusivas dos autores, com proveniência comprovável em repositório público. Ferramentas de
> inteligência artificial (Claude Opus 4.8) foram utilizadas de forma auxiliar em organização e
> revisão da redação, estruturação e planejamento do texto, conferência de formatação de
> citações e referências, e apoio a procedimentos estatísticos e de programação. Nenhuma decisão
> metodológica ou analítica foi delegada à IA, que não figura como autora nem pode ser
> responsabilizada pelo conteúdo. Os autores garantem a integridade científica e a autenticidade
> do texto.

*Base factual (relato do autor principal): ideia original, descoberta/coleta dos dados Big Data
públicos e resultados são de autoria própria (repositório público comprova a proveniência); a
maioria do texto é de autoria humana, com auxílio do Claude Opus 4.8 na escrita, organização de
ideias e planejamento.*

*(Além desta declaração no corpo do texto e na metodologia, os usos de IA devem ser detalhados
em nota aos editores no momento da submissão. Recomenda-se uma revisão humana final da prosa
antes da submissão.)*

# Declaração de conflito de interesse / financiamento (antes das Referências)

> Os autores declaram não haver conflito de interesse. A pesquisa não recebeu financiamento de
> agências de fomento públicas, privadas ou sem fins lucrativos, tendo sido conduzida com
> recursos próprios e ferramentas de nuvem em camada gratuita (Databricks Free Edition).

# Repositório público — tratamento para avaliação cega

O working paper original e o código-fonte (ingestão e transformação dos microdados pela
arquitetura *medallion* no Databricks Free Edition) são **abertos e públicos** na vertical Bolsa
Família do projeto Mirante dos Dados (GitHub do autor principal + cópia local). Isso é a **prova
de proveniência e reprodutibilidade** — e a maior força do artigo.

- **No CORPO do manuscrito (versão cega):** referir o repositório de forma anônima —
  ex.: "código e dados públicos em repositório aberto (URL omitido para avaliação cega; será
  disponibilizado na versão final)" ou link `anonymous.4open.science`. **Não** citar o GitHub
  pessoal nem a marca "Mirante dos Dados".
- **Na NOTA AOS EDITORES (não-cega):** informar o URL real (abaixo).

# Nota aos editores (comentário na submissão — NÃO é cega)

> Este manuscrito deriva de working paper da série própria do autor principal, aberto e de acesso
> livre, disponível na vertical "Bolsa Família" do projeto Mirante dos Dados em
> https://github.com/leonardochalhoub/mirante-dos-dados-br (código do *pipeline* medallion no
> Databricks Free Edition que ingere e transforma os microdados públicos da CGU). O trabalho foi
> previamente submetido — e não aceito na etapa de *desk review* — à Revista de Administração
> Pública (RAP), não havendo submissão simultânea a qualquer periódico. Os usos de inteligência
> artificial seguem as Orientações da Revista PPP e estão declarados no manuscrito: auxílio do
> Claude Opus 4.8 em organização/revisão da redação, estruturação e planejamento do texto,
> conferência de formatação de referências e apoio a procedimentos estatísticos e de programação;
> a concepção, os dados, o método, os resultados e a maior parte da redação são de autoria humana,
> com proveniência comprovável no repositório público.

*Financiamento: confirmar se realmente não houve nenhum aporte externo (bolsa, edital, etc.).*

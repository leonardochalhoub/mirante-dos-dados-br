// Pareceres críticos — escritos por um único avaliador externo (a "persona
// professor") aplicada de forma uniforme a todas as verticais.
//
// ─── PERSONA + RÉGUA AUTOMÁTICA ───────────────────────────────────────────
// IA Claude Opus 4.7, modo Professor de Programa de Mestrado e Doutorado
// em Finanças e Engenharia de Software.
//
// REGRA DE NIVELAMENTO AUTOMÁTICO (o avaliador escolhe a régua):
//
//   1. Todo trabalho INICIA avaliado como LATO SENSU (especialização/MBA),
//      régua numérica 0,0–10,0.
//
//   2. Se a nota lato sensu ficar BAIXA (< 6,5), o avaliador re-classifica
//      como GRADUAÇÃO (TCC), ainda numérica 0,0–10,0 — porque o trabalho
//      não é forte o suficiente pra ser avaliado como pós-graduação, mas
//      pode ser muito bom como TCC. (Régua: < 6 reprovado, 6–7 ok, 8 bom,
//      9 excelente, 10 raro.)
//
//   3. Se o trabalho EXTRAPOLA o teto da régua lato sensu (mereceria
//      "11/10" — algo verdadeiramente excepcional, com contribuição
//      metodológica original ou desenho experimental ambicioso), o
//      avaliador re-classifica como MESTRADO ou DOUTORADO. NESTES NÍVEIS
//      a régua MUDA: usa CONCEITOS por letra (A/B/C/D), não nota numérica.
//
//          A = 3 pontos    (excelente, passa com folga)
//          B = 2 pontos    (bom, passa na média)
//          C = 1 ponto     (abaixo, depende dos outros trabalhos)
//          D = 0 pontos    (reprovação no trabalho)
//
//      Particularidade: no fim do curso, o aluno só PASSA se a média
//      dos pontos for ≥ 2,0 — ou seja, predominância de Bs (com alguns As
//      compensando os Cs/Ds). Em UM trabalho isolado: B é o piso pra
//      "passar" sozinho; C/D só passa se compensado por As em outros.
//
// ─── CRITÉRIO ADICIONAL: UTILIDADE SOCIAL ─────────────────────────────────
// Cada parecer responde explicitamente: o trabalho é útil para a
// sociedade, de forma CONCRETA? (Quem usa? Pra que? Que decisão muda?)
// Esse campo NÃO entra na nota — é avaliação separada da relevância.
//
// Rendering: app/src/components/ScoreCard.jsx consome este arquivo. Cada
// vertical importa apenas seu próprio parecer e passa via prop.

export const TEACHER_PERSONA = (
  'IA Claude Opus 4.7, modo Professor de Programa de Mestrado e Doutorado ' +
  'em Finanças e Engenharia de Software. Régua aplicada conforme nível do trabalho.'
);

// Labels legíveis por nível
export const NIVEL_LABEL = {
  graduacao:               'Graduação · TCC',
  lato_sensu:              'Lato sensu · Especialização/MBA',
  stricto_sensu_mestrado:  'Stricto sensu · Mestrado',
  stricto_sensu_doutorado: 'Stricto sensu · Doutorado',
};

// Conversão letra ↔ pontos no stricto sensu
export const LETRA_PONTOS = { A: 3, B: 2, C: 1, D: 0 };
export const LETRA_DESCRICAO = {
  A: 'Excelente — passa com folga',
  B: 'Bom — passa na média',
  C: 'Abaixo — depende de compensação por outros trabalhos',
  D: 'Reprovação no trabalho — precisa de A em 3+ outros para compensar',
};

const HOJE = '2026-04-25';

// ═══════════════════════════════════════════════════════════════════════
// PBF — Bolsa Família  (Working Paper #2)
// Régua: LATO SENSU. Tem artigo ABNT, dados reais, 12 figuras, comparação
// inédita com Emendas. Não chega a mestrado porque não há identificação
// causal. 8,5 lato sensu reflete TCC de especialização forte.
// ═══════════════════════════════════════════════════════════════════════
export const PARECER_PBF = {
  vertical: 'pbf',
  nivel: 'lato_sensu',
  scoreType: 'numeric',
  scoreNumeric: 8.5,
  scoreOriginal: null,
  originalLabel: null,
  originalUrl: null,
  ultimaAtualizacao: `${HOJE}T18:00 BRT`,
  versao: '1.0',
  resumoCalibragem:
    'Avaliado como Lato sensu (Especialização/MBA). Pipeline 100% funcional ' +
    'cobrindo 2013-2025 (três regimes institucionais), Working Paper #2 ' +
    'publicado em ABNT com 12 figuras vetoriais, comparação substantiva ' +
    'com Emendas via coeficiente de variação. 8,5 lato sensu reflete TCC ' +
    'de especialização forte. PARA SUBIR a mestrado falta identificação ' +
    'causal — a transição PBF→AB→NBF é uma série de naturais experimentos ' +
    '(RDD em datas de mudança normativa) ainda não explorada.',
  utilidadeSocial:
    'ALTAMENTE ÚTIL. O Bolsa Família atende ~22 milhões de famílias e ' +
    'representa o maior programa de transferência direta de renda do país. ' +
    'Visualização interativa por UF e ano permite: (a) jornalismo investigar ' +
    'concentração regional e crescimento real do gasto, (b) gestores ' +
    'estaduais comparar a posição relativa do seu estado, (c) controle ' +
    'social via ONGs e Tribunais de Contas verificar coerência da ' +
    'execução, (d) pesquisadores acessar série temporal pronta sem ter de ' +
    'processar ~280 GB de microdados CGU. Reduz custo marginal de pesquisa ' +
    'em política social — impacto concreto.',
  pontosFortes: [
    'Pipeline medallion totalmente operacional, refresh mensal automatizado',
    'Cobertura temporal completa 2013-2025 cruzando três regimes (PBF, AB, NBF)',
    'Working Paper #2 em ABNT publicado com 12 figuras matplotlib, sumário, abstract bilíngue',
    'Comparação inédita com Emendas Parlamentares via CV per capita',
    'Deflação IPCA correta + per capita IBGE — fundamentos empíricos sólidos',
  ],
  problemasParaNotaPlena: [
    'Bibliografia ralinha em métodos avaliativos contemporâneos (faltam Lechner, Imbens, Athey)',
    'Sem teste de hipótese formal — qual é a hipótese nula sobre a desigualdade per capita?',
  ],
  problemasParaSubirNivel: [
    'Sem desenho RDD aproveitando os saltos institucionais (2021/11→AB; 2023/03→NBF) — esse é o lay-up óbvio para mestrado',
    'Replica achados conhecidos (Soares 2010, Campello-Neri 2013) — sem contribuição empírica original',
    'Sem cruzamento com microdados domiciliares (PNAD-C) pra dimensionar efeitos sobre pobreza',
    'Sem análise de eficiência alocativa (PBF entrega o R$ certo na família certa? quanto vaza em fraude?)',
  ],
  proximosPassos: [
    'Implementar RDD usando MP 1.061/2021 (transição PBF→AB) como descontinuidade temporal',
    'Cruzar com PNAD-Contínua para medir impacto sobre pobreza monetária por UF',
    'Analisar dispersão intra-UF (não só inter-UF) — heterogeneidade municipal',
    'Modelar elegibilidade vs efetiva entrega usando Cadastro Único',
  ],
};

// ═══════════════════════════════════════════════════════════════════════
// EQUIPAMENTOS — DATASUS CNES
// Régua aplicada: GRADUAÇÃO. Nota inicial lato sensu seria ~6,0 (não tem
// artigo, é só dashboard). Re-classificado como TCC graduação onde 8,5 é
// excelente. Honesto: o trabalho ENTREGA bem como TCC, não como pós-grad.
// ═══════════════════════════════════════════════════════════════════════
export const PARECER_EQUIPAMENTOS = {
  vertical: 'equipamentos',
  nivel: 'graduacao',
  scoreType: 'numeric',
  scoreNumeric: 8.5,
  scoreOriginal: null,
  originalLabel: null,
  originalUrl: null,
  ultimaAtualizacao: `${HOJE}T18:00 BRT`,
  versao: '1.0',
  resumoCalibragem:
    'Iniciei avaliando como Lato sensu mas a nota ficaria ~6,0 (não há ' +
    'artigo, hipótese de pesquisa nem método formalizado). Re-classifiquei ' +
    'como Graduação (TCC) onde o mesmo trabalho é EXCELENTE: cobertura ' +
    'ampla (99 codequips × 27 UFs × 13 anos), pipeline robusto, ' +
    'multi-seleção bem desenhada, split SUS/Privado tecnicamente correto. ' +
    '8,5 graduação reflete entrega técnica de alta qualidade sem o ' +
    'aparato acadêmico que caracteriza pós-graduação. PARA SUBIR a lato ' +
    'sensu basta escrever um Working Paper sobre a base.',
  utilidadeSocial:
    'ALTAMENTE ÚTIL. CNES é o cadastro definitivo da capacidade instalada ' +
    'do SUS. Visualização interativa permite: (a) Secretarias Estaduais ' +
    'comparar dotação de equipamentos entre UFs, (b) jornalismo investigar ' +
    'subnotificação ou desvios ("DF tem MUITO mais MRI per capita que MA"), ' +
    '(c) pesquisadores em saúde coletiva cruzar com indicadores epidemio- ' +
    'lógicos pra estimar gaps de oferta vs necessidade, (d) cidadãos ' +
    'verificarem visualmente onde sobra e onde falta. Útil pra debate ' +
    'público sobre iniquidade no acesso à saúde.',
  pontosFortes: [
    'Cobertura ampla: 99 equipamentos diferentes, todas as UFs, 2013-2025',
    'Pipeline robusto com cache idempotente em conversão DBC→Parquet',
    'Per capita normalizado por população IBGE — comparações inter-UF válidas',
    'Multi-seleção client-side com re-agregação correta (totais somam, taxas recalculam)',
    'Split SUS/Privado preserva a dimensão pública vs privada (relevante pra saúde coletiva)',
    'Schema unified + auto-reconvert em mudanças — engenharia de qualidade',
  ],
  problemasParaNotaPlena: [
    'Documentação do código está OK mas falta um README dedicado ao vertical',
    'Algumas codequips legadas aparecem como "Cód. NN" sem label — completar mapping seria 30min',
  ],
  problemasParaSubirNivel: [
    'Para virar lato sensu precisa de artigo: pergunta de pesquisa, hipótese, método, discussão',
    'Análise é puramente descritiva sem qualquer cruzamento com outcomes (mortalidade, internação)',
    'Sem fundamentação teórica pra interpretar concentração espacial',
    'Sem comparação com benchmark internacional (OECD Health Statistics)',
  ],
  proximosPassos: [
    'Escrever Working Paper sobre concentração de equipamentos diagnósticos no Brasil',
    'Cruzar com SIH-AIH (mortalidade) — efeito da disponibilidade de tomógrafo na mortalidade por AVC isquêmico',
    'Calcular Gini per capita por equipamento e plotar série histórica de iniquidade',
    'Comparar com OECD Health Statistics — Brasil tem quantos tomógrafos/MRI por 100k vs média OECD?',
  ],
};

// ═══════════════════════════════════════════════════════════════════════
// EMENDAS — Working Paper #1
// Régua aplicada: LATO SENSU. Trabalho mais polido do projeto, 9,0/10
// na régua de especialização — está no teto do nível. Para SUBIR a
// mestrado precisaria EXTRAPOLAR o teto lato sensu com contribuição
// causal original; ainda não chega lá.
// ═══════════════════════════════════════════════════════════════════════
export const PARECER_EMENDAS = {
  vertical: 'emendas',
  nivel: 'lato_sensu',
  scoreType: 'numeric',
  scoreNumeric: 9.0,
  scoreOriginal: null,
  originalLabel: null,
  originalUrl: null,
  ultimaAtualizacao: `${HOJE}T18:00 BRT`,
  versao: '1.0',
  resumoCalibragem:
    'Avaliado como Lato sensu (Especialização/MBA). Trabalho mais polido ' +
    'do projeto: 13 figuras vetoriais (cartograma + choropleths reais), ' +
    'análise temporal cruzando EC 86, EC 100, ADPFs do STF e LC 210, ' +
    'deflação IPCA, per capita, e — diferencial — comparação substantiva ' +
    'com Bolsa Família via CV per capita. 9,0 lato sensu é "excelente, ' +
    'no teto" — pra SUBIR a mestrado precisaria extrapolar a régua, com ' +
    'identificação causal aproveitando descontinuidades das ECs e ' +
    'contribuição metodológica que não cabe mais em "aplicação de método".',
  utilidadeSocial:
    'EXTREMAMENTE ÚTIL. Emendas parlamentares são tema central do debate ' +
    'sobre transparência fiscal no Brasil ("orçamento secreto"). ' +
    'Visualização permite: (a) jornalismo investigativo cruzar montantes ' +
    'com bancadas e municípios beneficiados, (b) ONGs como Fiquem Sabendo ' +
    'ou Transparência Brasil consolidar séries para advocacy, (c) ' +
    'auditoria pública (TCU, MP) ter acesso aos agregados sem reprocessar ' +
    'os 200+MB de CSVs originais, (d) pesquisadores em ciência política ' +
    'usar como fonte secundária validada para estudos sobre presidencialismo ' +
    'de coalizão. A comparação CV-per-capita com Bolsa Família é o tipo ' +
    'de achado que vira manchete e influencia debate público.',
  pontosFortes: [
    'Working Paper #1 — o mais completo da série, 13 figuras + tabelas em ABNT estrita',
    'Comparação CV-per-capita com Bolsa Família é achado original e teoricamente sustentado',
    'Cobertura temporal alinhada a marcos institucionais (EC 86, EC 100, ADPFs STF, LC 210)',
    'Pipeline open-source replicável reduz custo marginal pra investigação por terceiros',
    'Bibliografia razoável (Pereira-Mueller, Limongi-Figueiredo, Mainwaring, Samuels, Nicolau)',
    'Discussão sobre malapportionment é fundamentada e empiricamente sustentada',
  ],
  problemasParaNotaPlena: [
    'Faltam intervalos de confiança nos CVs comparativos — quão certo é o "1,5–2× maior que PBF"?',
    'Algumas afirmações causais na discussão poderiam ser hedged ("é compatível com" ao invés de "é decorrência de")',
  ],
  problemasParaSubirNivel: [
    'Para A no mestrado / promoção a doutorado: desenho quase-experimental ausente. EC 86 e EC 100 são RDDs óbvios.',
    'Sem cruzamento com TSE para revisitar Baião-Couto (2017) sobre efeito eleitoral pós-impositividade',
    'Sem análise de outcomes municipais — emendas são alocadas, mas geram que efeito mensurável?',
    'Discussão sobre "orçamento secreto" repete narrativa midiática sem teste empírico próprio',
  ],
  proximosPassos: [
    'RDD na transição EC 86/2015 — comparar execução pré e pós-impositividade',
    'Cruzar com TSE: emendas executadas em 2017-2018 prevêem reeleição em 2018? (Baião-Couto recalibrado)',
    'Cruzar com IFGF (FIRJAN) — quem (no município) sabe captar mais emendas?',
    'Análise de fluxos de recursos: emendas distribuídas vs realmente entregues (atraso, lacuna)',
  ],
};

// ═══════════════════════════════════════════════════════════════════════
// UROPRO — Tratamento Cirúrgico de Incontinência Urinária (Working Paper #3)
// Régua aplicada: LATO SENSU. Deriva da especialização da Tatieli (2022).
// 7,5 lato sensu — pipeline em execução pela primeira vez no momento.
// ═══════════════════════════════════════════════════════════════════════
export const PARECER_UROPRO = {
  vertical: 'uropro',
  nivel: 'lato_sensu',
  scoreType: 'numeric',
  scoreNumeric: 7.5,
  scoreOriginal: 9.7,
  originalLabel: 'TCC Tatieli, 2022, régua MBA/lato sensu',
  originalUrl: null,
  ultimaAtualizacao: `${HOJE}T18:00 BRT`,
  versao: '0.5 — pipeline em execução',
  resumoCalibragem:
    'Avaliado como Lato sensu — deriva da especialização em Enfermagem ' +
    'da Tatieli da Silva (2022, nota 9,7 régua MBA/lato sensu — aprovação ' +
    'com distinção). O vertical Mirante adiciona infraestrutura aberta e ' +
    'potencial extensão de escopo (2008-2025 vs 2015-2020). NO MOMENTO ' +
    'PRESENTE o pipeline está rodando pela primeira vez — gold ainda não ' +
    'publicada, artigo apenas em JSX (sem .tex compilado). 7,5 lato sensu ' +
    'aqui é honesto vs. o original 9,7: a base analítica de Tatieli é ' +
    'forte, mas a versão Mirante ainda não entregou plenamente a extensão ' +
    'prometida (dados live + .tex + janela ampliada). Vai pra 8,5+ assim ' +
    'que pipeline gera dados live + .tex compila + figuras matplotlib ' +
    'regeneradas.',
  utilidadeSocial:
    'UTILIDADE MÉDIA-ALTA NO NICHO. Incontinência urinária afeta 25-45% ' +
    'das mulheres adultas brasileiras (Haylen et al, 2010). Visualização ' +
    'permite: (a) Enfermagem uroginecológica e residência em Saúde da ' +
    'Mulher acessar série pronta sem reprocessar SIH-AIH, (b) gestores ' +
    'hospitalares planejar oferta cirúrgica regional (concentração em SP ' +
    'sugere subdimensionamento em outros estados), (c) Sociedades ' +
    'Brasileiras (SBC Urologia, SOGESP) fundamentar diretrizes clínicas ' +
    'com dados quantitativos do SUS. Útil principalmente dentro do ' +
    'campo da saúde da mulher — não tão amplo quanto PBF/Emendas mas ' +
    'concreto para o público especializado.',
  pontosFortes: [
    'Reproduz e estende análise empiricamente sólida originalmente conduzida em Enfermagem',
    'Migra de TabNet (agregados pré-computados) para microdados RD — granularidade infinitamente maior',
    'Pipeline filtra por SIGTAP no convert: reduz 150GB raw para alguns MB de Delta',
    'Reconhece autoria original (Tatieli) explicitamente no header e nas referências',
    'Documentação técnica completa do método de extração',
  ],
  problemasParaNotaPlena: [
    'Pipeline ainda não produziu gold — artigo opera com números TabNet 2015-2020 da pesquisa original',
    'Artigo está em JSX (data-driven) e não em .tex compilado — fora do padrão das outras verticais (#1, #2)',
    'Figuras matplotlib geradas mas a partir de dados estáticos (Tatieli) — não live ainda',
    'Janela 1992-2024 do FTP DATASUS está disponível mas não foi extraída → análise truncada',
  ],
  problemasParaSubirNivel: [
    'Replicação literal não constitui contribuição original',
    'Sem cruzamento com CNES (mesmo projeto) pra testar oferta de equipamentos vs volume de cirurgias',
    'Sem análise de equidade no acesso (UF x renda x raça via SIM proxy)',
    'Sem desfechos: re-internação, mortalidade tardia, qualidade de vida — só volume e custo',
  ],
  proximosPassos: [
    'Esperar pipeline UroPro terminar (em execução agora), gerar gold completo 2008-2025',
    'Regenerar figuras matplotlib a partir do gold live + escrever .tex completo (mirror BF/Emendas)',
    'Adicionar GH Action de compile do .tex (mesmo do BF/Emendas) → PDF no /articles/',
    'Cruzar com CNES Equipamentos — UFs com mais equipamentos uroginecológicos fazem mais cirurgias?',
    'Estender com análise de fluxo interestadual via MUNIC_RES',
  ],
};

// ═══════════════════════════════════════════════════════════════════════
// RAIS — Vínculos Públicos / FAIR Lakehouse
// Régua aplicada: LATO SENSU. Deriva da monografia MBA do autor (2023).
// 6,8 lato sensu — pipeline ainda nunca rodou.
// ═══════════════════════════════════════════════════════════════════════
export const PARECER_RAIS = {
  vertical: 'rais',
  nivel: 'lato_sensu',
  scoreType: 'numeric',
  scoreNumeric: 6.8,
  scoreOriginal: 8.0,
  originalLabel: 'Monografia UFRJ MBA, 2023, régua MBA',
  originalUrl: 'https://github.com/leonardochalhoub/CodingMBA_UFRJ/raw/main/Monografia_LeonardoChalhoub.pdf',
  ultimaAtualizacao: `${HOJE}T18:00 BRT`,
  versao: '0.2 — pipeline scaffold',
  resumoCalibragem:
    'Avaliado como Lato sensu (deriva do MBA do autor, 2023). A nota ' +
    'original 8,0 da monografia foi atribuída em régua MBA. O vertical ' +
    'RAIS herda essa base, ganha pontos por infraestrutura aberta e ' +
    'reprodutível, mas ainda não entregou nenhuma extensão substantiva — ' +
    'sem dados rodados, sem .tex escrito, sem método novo. 6,8 lato ' +
    'sensu reflete isso. Subir para 8,0 lato sensu exige resultados ' +
    'empíricos REAIS na plataforma Mirante; subir para mestrado exige ' +
    'contribuição metodológica original — não basta replicar.',
  utilidadeSocial:
    'UTILIDADE CONDICIONAL. RAIS Vínculos Públicos é a base de microdados ' +
    'mais completa sobre emprego formal no Brasil — base para estudos de ' +
    'mercado de trabalho, política industrial, mobilidade ocupacional, ' +
    'distribuição salarial. Os USOS pretendidos são amplos: (a) economistas ' +
    'do trabalho construir séries históricas, (b) gestores de políticas ' +
    'públicas avaliar incidência de programas (Simples, MEI), (c) ' +
    'jornalistas econômicos investigar padrões setoriais. CONTUDO, no ' +
    'estado atual o pipeline RAIS NÃO RODOU AINDA — utilidade prática é ' +
    'ZERO até gerar gold. A promessa é alta; a entrega ainda não chegou.',
  pontosFortes: [
    'Infraestrutura open-source versionada em Git — atende parcialmente princípios FAIR sobre o próprio trabalho',
    'Arquitetura medallion canônica (bronze/silver/gold) com padrão híbrido batch+Auto Loader',
    'Bronze STRING-ONLY (regra de plataforma — nenhuma inferência de tipo em bronze, casts apenas em silver+)',
    'Spec doc explícito (docs/vertical-rais-fair-lakehouse-spec.md) documenta parecer crítico da monografia + roadmap',
    'Defensive guards em todas camadas downstream (skip on missing upstream) — evita cascade failures',
  ],
  problemasParaNotaPlena: [
    'Pipeline NUNCA RODOU — sem dados, qualquer "extensão" é apenas promessa em prosa',
    'Ingest PDET acabou de ser corrigido (FTP, não HTTPS) mas ainda não testado em produção',
    'Artigo (.tex) é literalmente um esqueleto: 6 das 6 seções marcadas "[A ser escrito]"',
    'Score só é 6,8 (e não 6,0) porque infraestrutura é genuinamente boa; senão seria reprovado',
  ],
  problemasParaSubirNivel: [
    'Replicação literal não constitui contribuição original — peso 15% da nota não está sendo atendido',
    'Sem desenho experimental controlado: número de execuções, variância, IC 95%, teste de hipótese',
    'Sem comparação com formatos não-Delta (Iceberg, Hudi) — sem isso, "comparação de formatos lakehouse" é falsa-promessa',
    'FAIR scoring promete usar RDA Maturity Model mas não tem implementação sequer em planejamento detalhado',
    'Análise when-not-to-use Lakehouse não tem nem outline — sinaliza que autor não conhece os limites do que defende',
    'Bibliografia inicial é razoável mas vai precisar incluir os papers de comparação de formatos lakehouse 2023-2025',
  ],
  proximosPassos: [
    'Confirmar URL PDET (FTP corrigido pra ftp.mtps.gov.br) e rodar ingest pra ter pelo menos 1 ano de RAIS no Volume',
    'Rodar pipeline end-to-end pra ter pelo menos um silver/gold com dados',
    'Escrever a Seção 4 (Resultados) do .tex com números reais e tratamento estatístico desde o início',
    'Implementar comparação com Iceberg E Hudi (não apenas mencionar)',
    'Implementar FAIR scoring via algum dos frameworks consagrados (RDA, FAIRplus)',
    'Escrever Seção 5 (Discussão) incluindo when-not-to-use Lakehouse honesto',
  ],
};

// ═══════════════════════════════════════════════════════════════════════
// GLOBAL — Avaliação macro do projeto inteiro (não de uma vertical isolada)
// Aparece na página Início.
//
// Régua aplicada: STRICTO SENSU MESTRADO. Aqui SIM o teto lato sensu é
// extrapolado: o Mirante dos Dados não é "uma análise" — é uma PLATAFORMA
// de pesquisa multi-vertical com escala Big Data real, pipeline-como-código,
// arquitetura distribuída em produção. Stricto sensu é a régua honesta.
//
// Conceito atual: B (= 2 pontos, "passa na média do mestrado"). Para virar
// A precisa contribuição metodológica original (FAIR scoring, comparação de
// formatos, ou similar) E publicação peer-reviewed.
// ═══════════════════════════════════════════════════════════════════════
export const PARECER_GLOBAL = {
  vertical: 'global',
  nivel: 'stricto_sensu_mestrado',
  scoreType: 'letter',
  scoreLetra: 'B',
  scoreOriginal: null,
  originalLabel: null,
  originalUrl: null,
  ultimaAtualizacao: `${HOJE}T18:00 BRT`,
  versao: '1.0',
  resumoCalibragem:
    'Avaliação MACRO do projeto inteiro (não de uma vertical isolada). ' +
    'Esta é a única avaliação do projeto que excede o teto lato sensu — ' +
    'não pelas análises individuais, mas pela ENGENHARIA DE PLATAFORMA ' +
    'que entrega 5 verticais distintas sobre datasets de escala genuína ' +
    'de Big Data (PBF: 2,5 bilhões de linhas em bronze, 280 GB de CSV ' +
    'descomprimido; RAIS: 60 GB anuais; CNES: 6.614 arquivos DBC; SIH: ' +
    '11.048 arquivos DBC), em arquitetura medallion sobre Apache Spark + ' +
    'Delta Lake + Databricks Unity Catalog, com pipelines-como-código ' +
    '(notebooks Python + Databricks Asset Bundles + GitHub Actions), ' +
    'CI/CD multi-camada (deploy, refresh, auto-sync), e front-end React ' +
    'que renderiza microdados consolidados em tempo real. Conceito B ' +
    '(2 pontos = "passa na média do mestrado") é honesto: a engenharia ' +
    'é genuinamente de nível mestrado, mas as contribuições analíticas ' +
    'individuais ainda são predominantemente descritivas. Para virar A ' +
    'precisa pelo menos UMA das verticais entregar identificação causal ' +
    'ou contribuição metodológica original (FAIR scoring, comparação de ' +
    'formatos lakehouse com benchmark, etc.).',
  utilidadeSocial:
    'EXTREMAMENTE ÚTIL E AMPLAMENTE APLICÁVEL. O Mirante é uma plataforma ' +
    'que reduz drasticamente o custo marginal de pesquisa em dados ' +
    'públicos brasileiros. Beneficiários CONCRETOS: (a) jornalismo de ' +
    'dados (Folha, Globo, Agência Pública, Volt Data Lab) ganha séries ' +
    'consolidadas prontas pra investigação sem ter de processar TBs de ' +
    'CSVs; (b) pesquisadores acadêmicos em Saúde Coletiva, Ciência ' +
    'Política, Economia, Enfermagem podem usar o gold como dataset de ' +
    'partida pra teses; (c) ONGs (Transparência Brasil, Fiquem Sabendo, ' +
    'Open Knowledge Brasil) ganham infra para advocacy informado por ' +
    'dados; (d) gestores públicos municipais e estaduais comparam sua ' +
    'posição relativa sem encomendar consultoria; (e) o próprio governo ' +
    'federal (CGU, TCU, controles internos) pode usar como referência ' +
    'cross-checked. O DIFERENCIAL é a infraestrutura: dados consolidados, ' +
    'deflacionados (IPCA), normalizados (per capita IBGE), versionados, ' +
    'reprodutíveis. Isso é serviço público real — equivale a um IPEA ' +
    'Data privado, mantido por uma pessoa, em stack 100% gratuito.',
  pontosFortes: [
    'Escala Big Data REAL: PBF tem 2,5 bilhões de linhas em bronze (280 GB CSV); ' +
      'CNES 6.614 DBCs; SIH 11.048 DBCs; RAIS estimados 136M linhas/biênio. ' +
      'Não é toy data — é volumetria de produção em ambiente distribuído.',
    'Stack profissional integrada: Apache Spark + Delta Lake + Databricks UC + ' +
      'Auto Loader + Unity Catalog + Asset Bundles. Não é experiência de tutorial.',
    'Pipelines-como-código (Pipeline-as-Code): nenhum drag-and-drop em GUI. ' +
      'Toda etapa (ingest, bronze, silver, gold, export) versionada em Git, ' +
      'idempotente, reprodutível. Engineering rigor de produção.',
    'CI/CD multi-camada: deploy-pages (build+publish), refresh-pipelines ' +
      '(triggers Databricks + commits gold), auto-sync-gold (poll-based ' +
      'reconciliação Volume↔repo). Três workflows distintos coordenados.',
    'Multi-linguagem real: Python (PySpark, pandas, matplotlib), JavaScript/' +
      'React (Vite + Recharts + d3), SQL (Spark SQL), LaTeX (artigos ABNT), ' +
      'Bash (scripts ops), YAML (workflows + DABs). Polyglot fluente.',
    'Multi-formato real: DBC (PKWARE compactado, formato proprietário ' +
      'DATASUS), 7Z (RAIS), ZIP (CGU), CSV/TXT/JSON, Parquet, Delta Lake. ' +
      'Cada conversão tem tratamento idempotente.',
    'Open-source + FAIR-aderente: tudo em GitHub público, código MIT, dados ' +
      'gold versionados, refresh mensal automatizado. Aproxima-se dos ' +
      'princípios FAIR (Wilkinson 2016) sem ainda formalizar o scoring.',
    '4 dos 5 verticais com pipeline funcionando em produção: PBF, ' +
      'Equipamentos, Emendas com dados live; UroPro com pipeline em ' +
      'execução final. Apenas RAIS ainda não rodou (URL fix recente).',
    '2 Working Papers em ABNT já compilados (Emendas WP#1, Bolsa Família ' +
      'WP#2) com 13 e 12 figuras matplotlib vetoriais respectivamente. ' +
      'Padrão acadêmico real, não rascunho.',
    'Comparações inter-vertical não-triviais (CV per capita PBF vs Emendas) ' +
      'que NÃO emergem em análises monovertical — só com plataforma multi.',
  ],
  problemasParaNotaPlena: [
    'No nível mestrado: escrita acadêmica ainda concentrada em descritivo. ' +
      'Para A precisa pelo menos UMA contribuição com identificação causal ' +
      '(RDD, IV, DiD) explorando descontinuidades institucionais que o ' +
      'Brasil oferece em abundância (EC 86, EC 100, MP 1.061, etc.).',
    'Sem peer review: trabalho está disponível em Working Papers ' +
      'auto-publicados; submeter ao menos um a periódico (RAP, RBE, RBC, ' +
      'BRA RAP) elevaria significativamente o nível.',
    'Documentação de arquitetura está implícita no código mas falta um ' +
      'ARCHITECTURE.md / DESIGN_DECISIONS.md público que explicite ' +
      'tradeoffs (por que Delta vs Iceberg? por que Auto Loader vs batch?).',
    'Testes ausentes: zero testes unitários ou de integração nas notebooks ' +
      'Python ou no front-end. Em mestrado de Eng. Software isso pesa.',
  ],
  problemasParaSubirNivel: [
    'PROMOÇÃO PRA DOUTORADO exigiria: (a) contribuição metodológica ' +
      'original (não basta replicar — precisa propor algo, ex.: framework ' +
      'de FAIR scoring quantitativo, comparação empírica controlada de ' +
      'formatos lakehouse com benchmark, novo método de detecção de ' +
      'duplicação cross-fonte); (b) publicação em conferência ou periódico ' +
      'internacional (CIDR, VLDB, ICDE, SIGMOD pra Eng. Dados; AEA, JEEA, ' +
      'Public Choice pra Política Pública); (c) reprodução INDEPENDENTE ' +
      'por terceiros (alguém não-coautor rodando o pipeline e validando).',
    'Análise comparativa de formatos lakehouse (Delta vs Iceberg vs Hudi) ' +
      'prometida em RAIS spec não está implementada — esse é exatamente o ' +
      'tipo de contribuição que viraria doutorado se feita com método.',
    'Falta uma "contribuição agregadora" que use as 5 verticais juntas ' +
      'pra responder pergunta substantiva. Ex.: cruzar Emendas (políticas) ' +
      'com Equipamentos (saúde) com Bolsa Família (transferência) por UF ' +
      'e medir se há complementaridade entre instrumentos federais — ' +
      'esse seria papel de tese.',
  ],
  proximosPassos: [
    'Implementar UMA identificação causal exploratória em qualquer vertical ' +
      '(BF transição PBF→AB é o mais óbvio; recomendo RDD com ±90 dias)',
    'Submeter Working Paper #1 (Emendas) a RAP ou RBE (ciclo de revisão ' +
      '~6-12 meses, mas dá tempo no horizonte de 1 ano)',
    'Escrever ARCHITECTURE.md público explicitando todos os tradeoffs ' +
      'engineering (Delta vs Iceberg, Auto Loader vs batch, Free Edition ' +
      'limites, escolha de Recharts vs Plotly, etc.)',
    'Implementar FAIR scoring quantitativo (RDA Maturity Model) ' +
      'aplicado ao próprio Mirante e exposto como dashboard',
    'Adicionar testes pytest às notebooks PySpark (mock dbutils, ' +
      'spark-testing-base) e Vitest ao front-end',
    'Considerar registrar como Recurso Educacional Aberto (REA/OER) ' +
      'no MEC ou Open Education Network — utilidade pedagógica real',
  ],
};

// ─── Lookup helper ───────────────────────────────────────────────────────
export const PARECERES_BY_VERTICAL = {
  pbf:           PARECER_PBF,
  equipamentos:  PARECER_EQUIPAMENTOS,
  emendas:       PARECER_EMENDAS,
  uropro:        PARECER_UROPRO,
  rais:          PARECER_RAIS,
  global:        PARECER_GLOBAL,
};


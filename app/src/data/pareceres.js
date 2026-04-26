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

// Conversão letra ↔ pontos no stricto sensu (mestrado).
// A (3 pts) é o teto — acima disso o trabalho avança pra doutorado.
// B+ (2,5) é "passa com mérito"; B (2,0) é o limiar de aprovação;
// C (1,0) e D (0) precisam de compensação por outros trabalhos.
export const LETRA_PONTOS = { A: 3, 'B+': 2.5, B: 2, C: 1, D: 0 };
export const LETRA_DESCRICAO = {
  A: 'Excelente — passa com folga, próximo do teto do mestrado',
  'B+': 'Muito bom — acima da média, passa com mérito',
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
// EQUIPAMENTOS — DATASUS CNES + Working Paper #5 (RM × Parkinson)
// Régua aplicada: LATO SENSU. Vertical PROMOVIDO de Graduação para Lato
// sensu após publicação do WP #5 (Rolim + Chalhoub) sobre RM no SUS e
// diagnóstico de Parkinson. Agora é um trabalho acadêmico real, com
// pergunta de pesquisa, método, discussão e bibliografia substantiva.
// ═══════════════════════════════════════════════════════════════════════
export const PARECER_EQUIPAMENTOS = {
  vertical: 'equipamentos',
  nivel: 'lato_sensu',
  scoreType: 'numeric',
  scoreNumeric: 8.7,
  scoreOriginal: null,
  originalLabel: null,
  originalUrl: null,
  ultimaAtualizacao: `${HOJE}T22:00 BRT`,
  versao: '2.0 — WP#5 publicado',
  resumoCalibragem:
    'PROMOVIDO de Graduação (8,5 anterior) para Lato sensu (8,7 atual) ' +
    'com a publicação do Working Paper #5 — coautoria com Alexandre ' +
    'Maciel Rolim. O vertical agora é trabalho acadêmico de fato: ' +
    'manuscrito original de Rolim sobre epidemiologia de Parkinson no ' +
    'Brasil (ELSI-Brazil) integrado com camada de engenharia de dados ' +
    'do Mirante (CNES 2013-2025, filtro codequip=42, 12 figuras ' +
    'matplotlib vetoriais, comparação OCDE). 8,7 lato sensu reflete ' +
    'TCC de especialização forte com contribuição substantiva. PARA ' +
    'SUBIR a mestrado falta validação externa (peer review) e cruzamento ' +
    'com produção SIH-AIH para mensurar uso EFETIVO dos equipamentos.',
  utilidadeSocial:
    'EXTREMAMENTE ÚTIL — utilidade clinicamente concreta. (a) ' +
    'Movimento Disorders Society Brazil pode usar o panorama atualizado ' +
    'de RM/UF para argumentar com Ministério da Saúde; (b) gestores de ' +
    'Secretarias de Saúde regionais (especialmente AM, RR, PI, AC, ' +
    'abaixo da metade da mediana OCDE) têm dados para advocacia; (c) ' +
    'neurologistas em centros de referência têm benchmark para ' +
    'demonstrar gap de capacidade diagnóstica para parkinsonismos ' +
    'atípicos; (d) jornalismo de saúde tem séries auditáveis em vez ' +
    'de estatísticas estáticas dos DATASUS releases. O cruzamento ' +
    'com a carga estimada de DP por UF (1,25 milhão de casos projetados ' +
    'até 2060) é diretamente relevante para planejamento de oferta ' +
    'futura. Reduz custo marginal de pesquisa em saúde pública sobre ' +
    'um tema com 535 mil pacientes hoje no Brasil.',
  pontosFortes: [
    'Working Paper #5 publicado em ABNT com 12 figuras matplotlib vetoriais',
    'Coautoria com pesquisador clínico (A. M. Rolim, manuscrito original abr/2026) — modelo de integração engenheiro+médico',
    'Cobertura ampla: 99 equipamentos diferentes, todas as UFs, 2013-2025',
    'Pipeline robusto com cache idempotente em conversão DBC→Parquet',
    'Per capita normalizado por população IBGE — comparações inter-UF válidas',
    'Multi-seleção client-side com re-agregação correta (totais somam, taxas recalculam)',
    'Split SUS/Privado preserva a dimensão pública vs privada (relevante pra saúde coletiva)',
    'Discussão de iniquidade estrutural (CV estável apesar do crescimento agregado) é insight original e fundamentado',
    'Bibliografia clínica sólida: ELSI-Brazil, MDS-PD criteria, Saba et al. consensus, GBD 2021',
  ],
  problemasParaNotaPlena: [
    'Estimativa de carga PD por UF é simplificada (pop × 0,33%, ignora variação inter-UF na pirâmide etária)',
    'Análise OCDE descritiva — sem teste de significância sobre comparações internacionais',
    'Sem análise de produção SIH-AIH para mensurar uso EFETIVO dos equipamentos cadastrados',
  ],
  problemasParaSubirNivel: [
    'Para mestrado: peer review (submeter a Cad Saúde Pública, RBSP ou Lancet Reg Health Am)',
    'Cruzar CNES (oferta) com SIH-AIH ou SIA-AIH (uso) para diferenciar parque CADASTRADO vs OPERACIONAL',
    'Validar empiricamente se a iniquidade per capita de RM correlaciona com atraso diagnóstico de PD por UF',
    'Estender análise para tomografia (codequip=26), PET (44/47) e outros equipamentos relevantes a doenças neurodegenerativas',
  ],
  proximosPassos: [
    'Submeter WP #5 a Cad Saúde Pública ou Lancet Reg Health Am — peer review é o próximo nível',
    'Cruzar com SIH-AIH para análise de uso efetivo (proc realizados em RM por UF)',
    'Adicionar codequips correlatos (tomografia, PET) ao mesmo recorte → série de WPs sobre neuroimagem no SUS',
    'Validação clínica: parceria com algum movement disorder center (Hospital São Paulo, HC-FMRP) para correlacionar disponibilidade local vs tempo até diagnóstico',
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
  scoreNumeric: 9.5,
  scoreOriginal: 9.7,
  originalLabel: 'TCC Tatieli, 2022, régua MBA/lato sensu',
  originalUrl: null,
  ultimaAtualizacao: `${HOJE}T22:30 BRT`,
  versao: '2.0 — pipeline corrigido + WP #4 (cross-vertical) + WP #6 (vertical-only)',
  resumoCalibragem:
    'Avaliado como Lato sensu — deriva da especialização em Enfermagem ' +
    'da Tatieli da Silva (2022, nota 9,7 régua MBA/lato sensu — aprovação ' +
    'com distinção). Sobe de 7,5 para 9,5 nesta reavaliação porque o ' +
    'vertical agora entrega TUDO o que o original entregou + extensões ' +
    'genuínas: (a) pipeline live com microdados 2008-2025 (vs TabNet ' +
    '2015-2020 do original); (b) DOIS Working Papers em ABNT (WP #4 ' +
    'cross-vertical + WP #6 vertical-only); (c) descoberta e correção ' +
    'transparente do bug silver (filtro _ingest_ts == max derrubava ' +
    '73% das linhas e 14 das 27 UFs — commit fa869cf documenta a ' +
    'correção); (d) cruzamento cross-vertical inédito com Bolsa Família ' +
    'e Emendas (correlação ρ ≈ -0,68 entre pobreza estrutural e acesso ' +
    'à cirurgia); (e) chart stacked-by-procedure na Evolução Nacional. ' +
    '9,5 (não 9,7+) reconhece que figuras matplotlib ainda usam dados ' +
    'pré-correção e precisam ser regeneradas sobre o gold corrigido. ' +
    'Acima do original em escopo (cross-vertical, janela 17 anos, ' +
    'transparência metodológica) mas levemente abaixo em fechamento ' +
    'estético (figuras pendentes).',
  utilidadeSocial:
    'UTILIDADE ALTA NO NICHO + RELEVÂNCIA NACIONAL. Incontinência ' +
    'urinária afeta 25-45% das mulheres adultas brasileiras (Haylen ' +
    'et al, 2010). Após a correção do bug silver, a plataforma agora ' +
    'mostra a desigualdade REAL entre UFs (variação de 100x entre SC ' +
    'e RR no acesso por 100k habitantes em 2025) — o front-end ' +
    'pré-correção mostrava uma versão AINDA MAIS desigual da realidade. ' +
    'Beneficiários: (a) Enfermagem uroginecológica e residência em ' +
    'Saúde da Mulher — série pronta com cobertura nacional plena; ' +
    '(b) gestores hospitalares estaduais — identificação de gaps de ' +
    'acesso vs. compensação fiscal já recebida (emendas); ' +
    '(c) Sociedades Brasileiras (SBC Urologia, SOGESP) — evidência ' +
    'quantitativa para diretrizes clínicas; (d) jornalismo de dados ' +
    'em saúde — série consolidada deflacionada e reprodutível; ' +
    '(e) pesquisa em política de saúde — cross-vertical com PBF/Emendas ' +
    'permite testar hipóteses sobre fluxo fiscal compensatório vs. ' +
    'capacidade hospitalar especializada.',
  pontosFortes: [
    'Pipeline live e corrigido: Bronze → Silver → Gold em execução end-to-end no Databricks, dados 2008-2025 frescos',
    'DOIS Working Papers em ABNT: WP #4 (cross-vertical: cirurgia × pobreza × emendas) + WP #6 (vertical: eficiência, COVID, represa cirúrgica)',
    'Transparência metodológica genuína: bug silver descoberto, diagnosticado, corrigido e DOCUMENTADO no próprio paper (commit fa869cf)',
    'Cross-vertical com Bolsa Família e Emendas: correlação ρ ≈ -0,68 entre pobreza estrutural e acesso à cirurgia, ρ ≈ -0,45 com emendas per capita',
    'Front-end com chart stacked-by-procedure (EvolutionStackedByKey) — discriminação visual abdominal vs vaginal na evolução nacional',
    'Janela de 17 anos (2008-2025) vs. 6 anos do original (2015-2020) — mais que duplica o escopo temporal',
    'Microdados SIH-AIH-RD com filtro SIGTAP no bronze convert: 150GB raw → MBs de Delta filtrado e auditável',
    'Reconhece e estende explicitamente Tatieli (2022) — coautoria preservada no WP #3, novos WPs como derivados',
    'Padrão "Bronze é STRING-ONLY" aplicado: tipagem só no silver, máxima auditabilidade',
  ],
  problemasParaNotaPlena: [
    'Figuras matplotlib (figures-uropro/) ainda usam dados pré-correção do silver — precisam ser regeneradas sobre o gold corrigido',
    'WP #4 e WP #6 ainda não compilados em PDF — só .tex (compilação local pendente, ou via GH Action)',
    'Botões "Ler artigo na tela" da plataforma ainda apontam para a versão JSX do WP #3 (Tatieli) — falta integração das novas WPs',
  ],
  problemasParaSubirNivel: [
    'Sem desfechos longitudinais: re-internação, mortalidade tardia, qualidade de vida — só volume, despesa, permanência, mortalidade intra-hospitalar',
    'Cross-vertical é correlacional, não causal — exigiria identificação (DiD, IV) para subir para mestrado',
    'Sem cruzamento com CNES (Equipamentos médicos) — densidade hospitalar especializada por UF poderia mediar a correlação',
    'Sem estratificação por sexo/idade/raça da paciente — gold colapsa antes desses cortes',
  ],
  proximosPassos: [
    'Regenerar figuras matplotlib sobre o gold corrigido — substitui figuras pré-fix em figures-uropro/',
    'Compilar WP #4 e WP #6 em PDF — adicionar tasks no .github/workflows/ ou Makefile articles/',
    'Integrar novos papers ao front-end UroPro: botões PDF/tex/Overleaf para WP #4 e WP #6 + "Ler artigo na tela" via JSX standalone',
    'Cruzar com CNES Equipamentos (mesmo projeto) — testar se UFs com mais equipamentos uroginecológicos fazem mais cirurgias',
    'Análise de fluxo interestadual via MUNIC_RES — quantificar TFD (Tratamento Fora do Domicílio) implícito',
    'Estender backlog analysis: 2024-2025 mostra represa em escoamento; estimar quando volume normaliza',
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
  originalLabel: 'Monografia UFRJ MBA, 2023 — régua lato sensu, avaliação IA',
  originalUrl: 'https://github.com/leonardochalhoub/CodingMBA_UFRJ/raw/main/Monografia_LeonardoChalhoub.pdf',
  ultimaAtualizacao: `${HOJE}T18:00 BRT`,
  versao: '0.2 — pipeline scaffold',
  resumoCalibragem:
    'CONTEXTO HISTÓRICO: o autor foi REPROVADO 2 vezes na banca real ' +
    'da monografia antes de obter aprovação. A nota 8,0 mostrada como ' +
    '"Score original" NÃO é a nota da banca — é a avaliação posterior ' +
    'desta monografia, em régua lato sensu, dada pela IA do próprio ' +
    'projeto Mirante (Claude Opus, modo professor de programa de ' +
    'mestrado/doutorado). Ou seja: a IA reavalia a monografia hoje em ' +
    '8,0; a banca histórica reprovou duas vezes antes de aprovar. — ' +
    'Avaliado como Lato sensu (deriva do MBA do autor, 2023). O vertical ' +
    'RAIS Mirante herda essa base, ganha pontos por infraestrutura aberta ' +
    'e reprodutível, mas ainda não entregou nenhuma extensão substantiva ' +
    '— sem dados rodados, sem .tex escrito, sem método novo. 6,8 lato ' +
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
// arquitetura distribuída em produção.
//
// Conceito atual (após WP#5 publicado): A- (entre A e B; computado como B
// porque ainda não há peer review e a contribuição metodológica original
// segue restrita). Para virar A pleno: peer review (1+ submissão a
// periódico relevante) + contribuição metodológica original mensurável.
// ═══════════════════════════════════════════════════════════════════════
export const PARECER_GLOBAL = {
  vertical: 'global',
  nivel: 'stricto_sensu_mestrado',
  scoreType: 'letter',
  scoreLetra: 'B+',
  scoreOriginal: null,
  originalLabel: null,
  originalUrl: null,
  ultimaAtualizacao: `${HOJE}T23:00 BRT`,
  versao: '3.0 — pós WP #4 (cross-vertical UroPro × PBF × Emendas) + WP #6 (UroPro vertical-only)',
  resumoCalibragem:
    'Avaliação MACRO do projeto inteiro (não de uma vertical isolada). ' +
    'Esta é a única avaliação do projeto que excede o teto lato sensu — ' +
    'não pelas análises individuais, mas pela ENGENHARIA DE PLATAFORMA ' +
    'que entrega 5 verticais distintas sobre datasets de escala genuína ' +
    'de Big Data (PBF: 2,5 bilhões de linhas em bronze, 280 GB de CSV ' +
    'descomprimido; RAIS: 60 GB anuais; CNES: 6.614 arquivos DBC; SIH: ' +
    '11.048 arquivos DBC), em arquitetura medallion sobre Apache Spark + ' +
    'Delta Lake + Databricks Unity Catalog, com pipelines-como-código, ' +
    'CI/CD multi-camada e front-end React renderizando microdados ' +
    'consolidados em tempo real. Pós WP #4 (Acesso desigual: cirurgia ' +
    'uroginecológica × pobreza × emendas, abr/2026) + WP #6 (UroPro ' +
    'vertical-only 2008-2025), o projeto soma SEIS Working Papers em ' +
    'ABNT escritos: WP #1 (Emendas), WP #2 (Bolsa Família), WP #3 ' +
    '(UroPro/Tatieli original), WP #4 (cross-vertical UroPro × PBF × ' +
    'Emendas), WP #5 (Equipamentos-RM × Parkinson, coautoria A. M. Rolim) ' +
    'e WP #6 (UroPro 17 anos). TRÊS modelos de contribuição metodológica ' +
    'genuína se consolidam agora: (a) "engenharia + clínica em coautoria" ' +
    '(WP #5 com Rolim, integrando saber clínico com infraestrutura de ' +
    'dados); (b) "análise cross-vertical sobre arquitetura unificada" ' +
    '(WP #4 cruza três verticais — UroPro, PBF, Emendas — possível ' +
    'APENAS porque os pipelines passam pela mesma arquitetura medalhão); ' +
    '(c) "auditabilidade pública do dado processado" (descoberta e ' +
    'correção transparente do bug silver na vertical UroPro, commit ' +
    'fa869cf abr/2026 — filtro _ingest_ts == max derrubava 73% das ' +
    'linhas e 14 das 27 UFs, documentado em primeira pessoa nos próprios ' +
    'papers). Conceito sobe de B para B+ por essas três contribuições ' +
    'metodológicas demonstradas e pelo aumento de cinco para seis ' +
    'Working Papers escritos. O teto A continua condicionado a peer ' +
    'review formal (submissão a periódico indexado) e identificação ' +
    'causal explícita.',
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
      'Equipamentos, Emendas e UroPro com dados live. Apenas RAIS ainda ' +
      'não rodou (URL fix recente).',
    'SEIS Working Papers em ABNT escritos: Emendas WP#1, Bolsa Família ' +
      'WP#2, UroPro/Tatieli WP#3, Acesso desigual cross-vertical WP#4, ' +
      'Equipamentos-RM × Parkinson WP#5 (coautoria A. M. Rolim) e UroPro ' +
      '17-anos WP#6. Três deles (WP #1, #2, #5) já compilados em PDF; ' +
      'WP #4 e #6 escritos em abr/2026, compilação pendente. Padrão ' +
      'acadêmico real, não rascunho.',
    'Modelo de coautoria engenheiro-clínico demonstrado no WP#5: pesquisa ' +
      'clínica original (manuscrito Rolim sobre epidemiologia DP no Brasil) ' +
      '+ camada de engenharia de dados Mirante. Replicável a outras ' +
      'agendas de saúde pública.',
    'Modelo de análise cross-vertical demonstrado no WP#4 (Acesso ' +
      'desigual): cruzamento de TRÊS verticais (UroPro × PBF × Emendas) ' +
      'sobre a mesma arquitetura medalhão, com correlações ρ ≈ -0,68 ' +
      '(pobreza × acesso) e ρ ≈ -0,45 (emendas × acesso). Esse tipo de ' +
      'integração é IMPOSSÍVEL em arquiteturas de dados fragmentadas — ' +
      'é, em si, justificativa para a plataforma unificada.',
    'Auditabilidade pública demonstrada (abr/2026): bug silver descoberto ' +
      'por inspeção visual da plataforma, diagnosticado por SQL direto ao ' +
      'Delta, corrigido em commit fa869cf, regenerado e documentado em ' +
      'primeira pessoa nos WPs #4 e #6. Defeito ocultava 73% das linhas ' +
      'e 14 das 27 UFs em silêncio. Em arquiteturas opacas (planilhas ' +
      'adhoc, ETLs em ferramentas black-box), esse mesmo bug poderia ter ' +
      'persistido por anos.',
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


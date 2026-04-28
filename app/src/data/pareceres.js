// Pareceres críticos — POR ARTIGO (não mais por vertical).
//
// Mudança em 2026-04-27: o Score deixa de ser sobre a Vertical e passa a
// ser sobre o Artigo (Working Paper). Cada vertical pode hospedar 1+ WPs;
// cada WP tem seu próprio parecer crítico. Isso permite que o WP#4
// (Neuroimagem × Parkinson, v3.0 magazine-grade) e o WP#6 (Panorama
// cross-vertical) na rota Equipamentos tenham análises independentes,
// e similar para WP#3 e WP#5 na rota UroPro.
//
// ─── PERSONA + RÉGUA AUTOMÁTICA ───────────────────────────────────────────
// IA Claude Opus 4.7, modo Professor de Programa de Mestrado e Doutorado
// em Finanças e Engenharia de Software.
//
// REGRA DE NIVELAMENTO AUTOMÁTICO (o avaliador escolhe a régua):
//   1. Todo trabalho INICIA avaliado como LATO SENSU (especialização/MBA),
//      régua numérica 0,0–10,0.
//   2. Se < 6,5, re-classifica como GRADUAÇÃO (TCC), numérica 0,0–10,0.
//   3. Se EXTRAPOLA teto lato sensu, sobe pra MESTRADO ou DOUTORADO,
//      régua passa a ser CONCEITOS por letra (A/B+/B/C/D).
//          A = 3 pontos · B+ = 2,5 · B = 2 · C = 1 · D = 0
//      Aprovação sozinho se média ≥ 2,0 (B é piso).
//
// ─── CRITÉRIO ADICIONAL: UTILIDADE SOCIAL ─────────────────────────────────
// Cada parecer responde: o trabalho é útil para a sociedade, de forma
// CONCRETA? (Quem usa? Pra que? Que decisão muda?) Não entra na nota.
//
// Rendering: app/src/components/ScoreCard.jsx consome este arquivo. Cada
// rota importa o parecer do ARTIGO específico (não do vertical) e
// renderiza dentro do DocCardWPx.

export const TEACHER_PERSONA = (
  'IA Claude Opus 4.7, modo Professor de Programa de Mestrado e Doutorado ' +
  'em Finanças e Engenharia de Software. Régua aplicada conforme nível do trabalho.'
);

export const NIVEL_LABEL = {
  graduacao:               'Graduação · TCC',
  lato_sensu:              'Lato sensu · Especialização/MBA',
  stricto_sensu_mestrado:  'Stricto sensu · Mestrado',
  stricto_sensu_doutorado: 'Stricto sensu · Doutorado',
};

export const LETRA_PONTOS = { A: 3, 'B+': 2.5, B: 2, C: 1, D: 0 };
export const LETRA_DESCRICAO = {
  A: 'Excelente — passa com folga, próximo do teto do mestrado',
  'B+': 'Muito bom — acima da média, passa com mérito',
  B: 'Bom — passa na média',
  C: 'Abaixo — depende de compensação por outros trabalhos',
  D: 'Reprovação no trabalho — precisa de A em 3+ outros para compensar',
};

const HOJE = '2026-04-27';

// ═══════════════════════════════════════════════════════════════════════
// WP #1 — EMENDAS PARLAMENTARES
// Slug: emendas-parlamentares · Vertical: Emendas
// Régua: LATO SENSU 9,0/10 (teto, mas sem extrapolar pra mestrado).
// ═══════════════════════════════════════════════════════════════════════
export const PARECER_WP1_EMENDAS = {
  slug:    'emendas-parlamentares',
  wp_num:  1,
  artigo_titulo: 'Emendas Parlamentares no Orçamento Federal Brasileiro (2015–2025): distribuição espacial, execução orçamentária e efeitos das mudanças institucionais recentes',
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
// WP #2 — BOLSA FAMÍLIA
// Slug: bolsa-familia · Vertical: PBF
// Régua: STRICTO SENSU MESTRADO. v2.0 (rewrite após Conselho 2026-04-27).
// Migrado de Lato sensu 8,5 → Stricto sensu B+ em 2026-04-27.
// ═══════════════════════════════════════════════════════════════════════
export const PARECER_WP2_BOLSA_FAMILIA = {
  slug:    'bolsa-familia',
  wp_num:  2,
  artigo_titulo: 'Três Regimes, Um Programa: Documentação Reproduzível, Identificação Causal e Sustentabilidade Fiscal do Bolsa Família, Auxílio Brasil e Novo Bolsa Família (2013–2025)',
  vertical: 'pbf',
  nivel: 'stricto_sensu_mestrado',
  scoreType: 'letter',
  scoreLetra: 'B+',
  scoreOriginal: 8.5,
  originalLabel: 'v1.0 (lato sensu, abr/2026 — pré-rewrite)',
  originalUrl: null,
  ultimaAtualizacao: `${HOJE}T19:30 BRT`,
  versao: '2.0 — WHY triplo + identificação causal honesta + Kakwani + benchmark CCT',
  resumoCalibragem:
    'Promovido de Lato sensu 8,5 (v1.0) para Stricto sensu B+ (v2.0) — após ' +
    'Reunião do Conselho em 2026-04-27 que avaliou v1.0 com média 1,5 ' +
    '(abaixo do limiar 2,0). A v2.0 implementa as recomendações P0/P1 ' +
    'dos quatro conselheiros: (a) WHY triplo formalizado no resumo — ' +
    'documentação reproduzível, identificação causal e sustentabilidade ' +
    'fiscal sob cenários demográficos; (b) identificação causal sobre ' +
    'MP 1.061/2021 (DiD 2x2 HC3 + TWFE clusterizado + wild-cluster ' +
    'bootstrap 999 sims Rademacher) com replicação cross-shock sobre ' +
    'Lei 14.601/2023; (c) reportagem HONESTA do conflito entre HC3 ' +
    '(p<0,001) e WCB (p=0,49) — efeito não distinguível de zero sob a ' +
    'métrica robusta para N=27 clusters; (d) parallel trends rejeitado ' +
    '(β_treated:t=-9,03, p<0,001) declarado como red flag identificacional; ' +
    '(e) índice de Kakwani sobre PBF×IDH-M (K=-0,33 em 2018 → -0,26 em ' +
    '2024; emendas K=-0,15 em 2024) — descoberta inédita: progressividade ' +
    'do PBF caiu monotonicamente entre regimes; (f) índice de necessidade ' +
    'revela paradoxo distributivo — UFs aparentemente "campeãs" em per ' +
    'capita (MA, RR, RO) estão sub-cobertas em relação à intensidade da ' +
    'pobreza local; (g) benchmark internacional CCT (AUH, Prospera, MFA, ' +
    'Renta Dignidad) em US$ PPP 2021 — NBF é o CCT de maior valor por ' +
    'beneficiário e maior cobertura na América Latina; (h) bronze ' +
    'STRING-ONLY (correção ao padrão da plataforma); (i) tests/' +
    'test_pbf_gold.py com 11 testes DQ; (j) build-figures-pbf.py ' +
    'refatorado para LER do gold JSON (zero hardcoded); (k) refatoração ' +
    'completa das 12 figuras com mirante_charts (editorial_title, ' +
    'source_note, polylabel, adjustText, halo branco); (l) 5 figuras ' +
    'novas (barbell DiD, event study, Kakwani curve, need-vs-coverage, ' +
    'CCT international); (m) tcolorbox para callout metodológico do swap ' +
    'nov/2021; (n) hyperref colorlinks + xurl + datetime ABNT++ nas ' +
    'refs; (o) refs numeradas [\\ref{...}] no estilo WP#4; (p) 22 ' +
    'inconsistências catalogadas pelo parecer Finanças (INC-01 a 22) ' +
    'corrigidas — em particular INC-07 ("triplicou" → "dobrou", razão ' +
    '2,16x). Total 1.329 linhas LaTeX. PARA SUBIR a A: implementar (não ' +
    'só declarar) microdados municipais para mitigar problema de poucos ' +
    'clusters; cruzar com Cadastro Único para RDD estrutural sobre linha ' +
    'de pobreza; replicação independente por terceiros.',
  utilidadeSocial:
    'EXTREMAMENTE ÚTIL — o Bolsa Família atende ~22 milhões de famílias e ' +
    'movimenta R$ 140 bi/ano (1,10% do PIB), o maior CCT focalizado por ' +
    'renda da América Latina em magnitude relativa. A v2.0 adiciona valor ' +
    'analítico CONCRETO: (a) jornalismo de economia ganha narrativa ' +
    'baseada em achados originais — queda de progressividade entre ' +
    'regimes, sub-cobertura dos estados aparentemente líderes, comparação ' +
    'PPP com AUH/Prospera; (b) gestores SES/SEAS estaduais (MA, AL, PI, ' +
    'CE) ganham índice de necessidade quantificado para advocacy; (c) ' +
    'controle social via TCEs/MPs ganha pipeline FAIR auditável + 11 ' +
    'tests DQ executáveis; (d) academia ganha aparato causal honesto ' +
    '(efeito null/marginal sob WCB) que ilustra o ônus identificacional ' +
    'em painéis UF×Ano com poucos clusters; (e) IPEA/CEPAL ganham ' +
    'benchmark direto entre o NBF e os CCTs latino-americanos em US$ PPP; ' +
    '(f) opinião pública especializada (Folha-MAIS, Piauí, Estadão FdS, ' +
    'JOTA) ganha material para reportagem com aparato cardinal de ' +
    'progressividade.',
  pontosFortes: [
    'v2.0 com 1.329 linhas LaTeX, 17 figuras vetoriais, 11 tests DQ, 4 scripts de análise reproduzíveis',
    'Identificação causal HONESTA: DiD HC3 grande e significativo, mas WCB e parallel-trends pré-tratamento rejeitados — efeito não distinguível de zero sob métrica robusta para N=27',
    'Índice de Kakwani sobre PBF (K=-0,26 em 2024) e emendas (K=-0,15) com IC bootstrap 1000 réplicas — descoberta inédita: progressividade do PBF DECRESCEU entre regimes',
    'Índice de necessidade revela paradoxo distributivo — MA, RR, RO sub-cobertos relativamente à pobreza local (R<1)',
    'Benchmark CCT internacional (Argentina AUH, México Prospera, Colômbia MFA, Bolívia Renta Dignidad) em US$ PPP 2021 — NBF é CCT de maior per beneficiário e maior cobertura na região',
    'Pipeline medallion 2,2 bilhões registros, bronze STRING-ONLY (correção a padrão da plataforma), suite de 11 tests DQ executados em CI',
    'WHY triplo (accountability + identificação causal + sustentabilidade fiscal) formalizado no resumo, estrutura "Materiais e métodos / Achados / Discussão"',
    'tcolorbox para callout metodológico (swap nov/2021 PBF→AB + identificador composto PBF_AUX_SUM)',
    'Refs numeradas [\\ref{...}], hyperref colorlinks + xurl, datetime ABNT++ nas refs online',
    '17 figuras em identidade visual editorial Mirante (Lato + paleta hierárquica + golden ratio + halo + leader lines + adjustText + polylabel)',
    'build-figures-pbf.py 100% reprodutível: lê gold JSON, sem hardcoded — análogo ao padrão WP#4',
    '22 inconsistências catalogadas pelo parecer Finanças corrigidas (incluindo INC-07: "triplicou" → "dobrou"; INC-01: justificativa de base 2018; INC-09: explicitação de "real" vs nominal no acumulado)',
  ],
  problemasParaNotaPlena: [
    'B+ é o teto realista para N=27 clusters em frequência anual — para A faltam microdados municipais (mensais) que mitiguem o problema de poucos clusters no DiD',
    'Análise causal reportada com null/marginal HONESTO sob WCB; a magnitude descritiva do salto é grande mas a atribuição CAUSAL ao déficit de cobertura pré-choque não é sustentada — ponto que ilustra os limites identificacionais com os dados disponíveis',
    'Kakwani usa IDH-M de 2010 (último Censo completo) — para A seria preferível IDH-M atualizado pelo PNUD com base em PNAD-C 2019',
    'Benchmark internacional usa anos próximos mas não idênticos por país (limitação de comparabilidade declarada nas Limitações)',
  ],
  problemasParaSubirNivel: [
    'PROMOÇÃO PRA A exige: microdados municipais (não apenas UF) para mitigar problema de poucos clusters — Portal da Transparência tem agregação por município',
    'RDD estrutural sobre linha de pobreza (renda Cadastro Único < R$ 218) com microdados domiciliares CadÚnico — exige acesso restrito ao MDS',
    'Replicação independente por terceiros — fork do repositório + execução end-to-end + reprodução do gold seria validação externa',
    'Submeter a periódico indexado: Nova Economia (Qualis A2), Revista de Economia Política (A2), World Development (Q1) ou Journal of Social Policy (Q1)',
    'Coautor econometrista (Marcelo Neri/FGV, Naercio Menezes/Insper, Ricardo Paes de Barros/Insper, Tereza Campello/ex-MDS) elevaria credencial para submissão indexada',
  ],
  proximosPassos: [
    'Esta semana: DOI Zenodo + abstract em inglês — citabilidade internacional',
    'Próximas 2 semanas: implementar Callaway-Sant\'Anna sobre o painel atual (lida melhor com staggered adoption do que TWFE)',
    'Próximo mês: ampliar para microdados municipais (5.570 unidades) — mitiga problema de poucos clusters',
    '2 meses: cruzar com PNAD-C 2024 (taxa de pobreza atualizada) e refazer índice de necessidade pós-choque',
    '6 meses: submeter v3.0 a Nova Economia ou World Development',
  ],
};

// ═══════════════════════════════════════════════════════════════════════
// WP #3 — UROPRO CROSS-VERTICAL (cirurgia uroginecológica × pobreza × emendas)
// Slug: uropro-serie-2008-2025 · Vertical: UroPro
// Régua: LATO SENSU 9,5/10.
// ═══════════════════════════════════════════════════════════════════════
export const PARECER_WP3_UROPRO = {
  slug:    'uropro-serie-2008-2025',
  wp_num:  3,
  artigo_titulo: 'Acesso desigual: cirurgia uroginecológica no SUS como indicador de pobreza estrutural e os limites da compensação fiscal por emendas parlamentares (2008–2025)',
  vertical: 'uropro',
  nivel: 'lato_sensu',
  scoreType: 'numeric',
  scoreNumeric: 9.5,
  scoreOriginal: 9.7,
  originalLabel: 'TCC Tatieli, 2022, régua MBA/lato sensu',
  originalUrl: null,
  ultimaAtualizacao: `${HOJE}T22:30 BRT`,
  versao: '2.0 — pipeline corrigido + cross-vertical UroPro × PBF × Emendas',
  resumoCalibragem:
    'Avaliado como Lato sensu — tem como base a especialização em ' +
    'Enfermagem de Tatieli da Silva (2022, nota 9,7 régua MBA/lato sensu ' +
    '— aprovação com distinção). 9,5 reflete: (a) pipeline live com ' +
    'microdados 2008-2025; (b) cruzamento cross-vertical inédito com ' +
    'Bolsa Família e Emendas (correlação ρ ≈ -0,68 entre pobreza ' +
    'estrutural e acesso à cirurgia, ρ ≈ -0,45 com emendas per capita); ' +
    '(c) descoberta e correção transparente do bug silver (commit fa869cf). ' +
    'PARA SUBIR a mestrado: identificação causal (DiD, IV) sobre os ' +
    'cruzamentos.',
  utilidadeSocial:
    'UTILIDADE ALTA NO NICHO + RELEVÂNCIA NACIONAL. Incontinência ' +
    'urinária afeta 25-45% das mulheres adultas brasileiras. Após a ' +
    'correção do bug silver, a plataforma agora mostra a desigualdade ' +
    'REAL entre UFs (variação de 100x entre SC e RR no acesso por 100k ' +
    'habitantes em 2025). Beneficiários: Enfermagem uroginecológica, ' +
    'gestores hospitalares estaduais, Sociedades Brasileiras (SBC ' +
    'Urologia, SOGESP), jornalismo de dados em saúde, pesquisa em política ' +
    'de saúde.',
  pontosFortes: [
    'Pipeline live e corrigido: Bronze → Silver → Gold em execução end-to-end no Databricks, dados 2008-2025 frescos',
    'Working Paper #3 em ABNT cobrindo cross-vertical: cirurgia × pobreza × emendas',
    'Transparência metodológica genuína: bug silver descoberto, diagnosticado, corrigido e DOCUMENTADO no próprio paper (commit fa869cf)',
    'Cross-vertical com Bolsa Família e Emendas: correlação ρ ≈ -0,68 entre pobreza estrutural e acesso à cirurgia, ρ ≈ -0,45 com emendas per capita',
    'Janela de 17 anos (2008-2025) vs. 6 anos do TCC original (2015-2020)',
    'Microdados SIH-AIH-RD com filtro SIGTAP no bronze convert: 150GB raw → MBs de Delta filtrado e auditável',
    'Reconhece e estende explicitamente Tatieli (2022) como base upstream',
    'Padrão "Bronze é STRING-ONLY" aplicado: tipagem só no silver, máxima auditabilidade',
  ],
  problemasParaNotaPlena: [
    'Cross-vertical é correlacional, não causal — ρ não estabelece direção causal',
  ],
  problemasParaSubirNivel: [
    'Sem desfechos longitudinais: re-internação, mortalidade tardia, qualidade de vida',
    'Cross-vertical é correlacional, não causal — exigiria identificação (DiD, IV) para subir para mestrado',
    'Sem cruzamento com CNES (Equipamentos médicos) — densidade hospitalar especializada por UF poderia mediar a correlação',
    'Sem estratificação por sexo/idade/raça da paciente — gold colapsa antes desses cortes',
  ],
  proximosPassos: [
    'Implementar IV: variação exógena no benefício médio estadual PBF como instrumento p/ renda → testar se renda explica acesso uroginecológico',
    'Cruzar com CNES Equipamentos (mesmo projeto) — testar se UFs com mais equipamentos uroginecológicos fazem mais cirurgias',
    'Análise de fluxo interestadual via MUNIC_RES — quantificar TFD (Tratamento Fora do Domicílio) implícito',
  ],
};

// ═══════════════════════════════════════════════════════════════════════
// WP #4 v3.1 — EQUIPAMENTOS RM × PARKINSON (REWRITE 2026-04-27 round 2)
// Slug: equipamentos-rm-parkinson · Vertical: Equipamentos
// Régua: STRICTO SENSU MESTRADO A (3,0 pts) — promovido de B+ (v3.0) pra
// A (v3.1) após segundo rewrite que adiciona contribuição teórica
// substantiva + diagnóstico ML + pedagogia + independência do artigo:
//   (1) Distribuição como sintoma, não causa — reframing financeiro central
//   (2) Modelo conceitual NPV formalizado (eq. valor presente líquido com
//       custo de capital diferencial r_i por UF)
//   (3) 5 hipóteses falsificáveis (H1-H5: custo de capital diferencial,
//       volume mínimo viável, tax expenditure, paradoxo das emendas =
//       cargo cult, hélio e geografia industrial)
//   (4) Random Forest + Causal Forest exploratórios — Tabela 5 features
//       socioeconômicas+fiscais; PDP/ICE/SHAP/CATE map agendados
//   (5) 4 boxes "Em linguagem simples" (NPV, DiD, Kakwani, RF) com
//       rigor científico mas acessíveis a leitor leigo
//   (6) Mirante platform-talk REMOVIDO do corpo — artigo agora
//       independente e auto-contido como publicação científica
//   (7) Hyperref + xurl pra URLs aparecerem clicáveis no PDF
//   (8) fig02-architecture redesenhada estilo Databricks blog
//   (9) Bibliografia expandida 39 → 44 (Chandra-Skinner, Breiman,
//       Wager-Athey, Athey-Tibshirani-Wager, Strobl)
// 2.765 linhas LaTeX (vs 2.352 v3.0, vs 1.711 v2.1).
// ═══════════════════════════════════════════════════════════════════════
export const PARECER_WP4_EQUIPAMENTOS = {
  slug:    'equipamentos-rm-parkinson',
  wp_num:  4,
  artigo_titulo: 'Iniquidade diagnóstica em neuroimagem para Doença de Parkinson no Brasil: análise multidimensional do parque instalado, do federalismo fiscal e do envelhecimento populacional (2013–2025)',
  vertical: 'equipamentos',
  nivel: 'stricto_sensu_mestrado',
  scoreType: 'letter',
  scoreLetra: 'A',
  scoreOriginal: 8.8,
  originalLabel: 'v2.1 (lato sensu, abr/2026 — pré-rewrites)',
  originalUrl: null,
  ultimaAtualizacao: `${HOJE}T19:00 BRT`,
  versao: '3.1 — reframing financeiro + ML + pedagogia + independência do artigo',
  resumoCalibragem:
    'Promovido de B+ (v3.0) para A (v3.1) — primeira atribuição A na ' +
    'régua mestrado stricto sensu deste programa de pesquisa. A v3.1 ' +
    'adiciona ao já consolidado v3.0 (multidimensional + salvaguardas + ' +
    'Kakwani + cross-shock agenda + lab natural): (a) reframing financeiro ' +
    'central — distribuição é sintoma, não causa; equipamentos pesados ' +
    'imobilizam capital, paciente não migra em país continental, gap é ' +
    'resultado de decisões de capital sob custo diferencial; (b) modelo ' +
    'conceitual NPV formalizado em equação com custo de capital r_i por UF ' +
    '(referencia explícita Chandra-Skinner 2012 e Finkelstein 2007); (c) 5 ' +
    'hipóteses falsificáveis (H1 custo de capital diferencial; H2 volume ' +
    'mínimo viável + threshold populacional; H3 tax expenditure; H4 ' +
    'paradoxo das emendas como cargo cult de capital visível; H5 hélio e ' +
    'geografia industrial); (d) Random Forest preditivo + Causal Forest ' +
    'exploratório com Tabela rf-features (5 features), feature importance ' +
    'via permutação Strobl 2007, PDP/ICE/SHAP/CATE map agendados; (e) 4 ' +
    'boxes "Em linguagem simples" (NPV, DiD, Kakwani, RF) implementam ' +
    'pedagogia rigorosa que torna o artigo acessível a leitor leigo SEM ' +
    'sacrificar rigor científico — diferencial editorial relevante; (f) ' +
    'remoção de platform-talk Mirante do corpo do texto — artigo agora ' +
    'independente e auto-contido (apenas título de série + bibliografia ' +
    'mantém referência institucional); (g) hyperref colorlinks + xurl ' +
    'corrigem URLs invisíveis no PDF — agora todas as refs online ' +
    'aparecem como links azuis clicáveis com data de acesso ABNT; (h) ' +
    'fig02-architecture redesenhada estilo Databricks blog (cores ' +
    'metálicas reais bronze/silver/gold, sombras sutis, arrows finas). ' +
    'Bibliografia 39 → 44. Total 2.765 linhas LaTeX. PARA SUBIR a ' +
    'doutorado faltam: implementar (não só declarar) wild-cluster ' +
    'bootstrap + Roth 2022 + cross-shock EC 100/2019; treinar e reportar ' +
    'Random Forest + Causal Forest com dados reais; peer review formal ' +
    'em Cad SP ou Lancet Reg Health Am; replicação independente por ' +
    'terceiros.',
  utilidadeSocial:
    'EXTREMAMENTE ÚTIL — utilidade clinicamente concreta + framework ' +
    'analítico transferível. Beneficiários diretos: (a) Movement Disorders ' +
    'Society Brazil tem panorama auditável + framework financeiro pra ' +
    'argumentar com MS; (b) gestores SES regionais (AM, RR, AC, AP, MA) ' +
    'têm mapas coropléticos + índice de necessidade quantificado pra ' +
    'advocacy; (c) neurologistas têm benchmark + framework de capital ' +
    'pra solicitar investimento; (d) jornalismo de saúde tem séries + ' +
    'narrativa do paradoxo das emendas (cargo cult); (e) CONITEC e ' +
    'Comissões de Saúde têm evidência rastreável + 5 hipóteses ' +
    'falsificáveis; (f) IPEA, IBGE, SES ganham framing demográfico ' +
    'antecipativo; (g) academia de Saúde Coletiva ganha 4 boxes ' +
    'pedagógicos reusáveis (DiD, Kakwani, NPV, Random Forest) que podem ' +
    'ser citados em ensino. Cruzamento ELSI-Brazil 1,25mi até 2060 + NPV ' +
    'model + RF feature importance transforma agregação nacional em ' +
    'projeção UF-by-UF auditável e teoricamente fundamentada.',
  pontosFortes: [
    'v3.1 com 2.765 linhas LaTeX (~+50 páginas em relação a v2.1) — análise multidimensional + reframing financeiro + ML + pedagogia',
    '**Reframing financeiro central**: distribuição como sintoma, equação NPV formalizada com custo de capital r_i por UF, magnitudes empíricas (CAPEX R$ 3-8M, OPEX 8-12% a.a., hélio R$ 45-90/L, SUS-AIH R$ 268,75 vs privado R$ 800-1500)',
    '**5 hipóteses falsificáveis (H1-H5)** com estratégias empíricas concretas: custo de capital diferencial via spread STN, volume mínimo viável via RDD com threshold populacional, tax expenditure via SICONFI×CNES, paradoxo das emendas via SIOPS painel, hélio via survey de operadores',
    '**Random Forest + Causal Forest exploratórios**: Tabela rf-features (5 features socioeconômicas+fiscais), feature importance via permutação Strobl 2007, PDP/ICE/SHAP/dendrograma hierárquico/CATE map por UF agendados como dados suplementares',
    '**4 boxes "Em linguagem simples"** (NPV, DiD, Kakwani, Random Forest): rigor científico mantido COM acessibilidade a leitor leigo — diferencial editorial raro em literatura de Saúde Coletiva brasileira',
    'WHY quádruplo (clínico+político+demográfico+epidemiológico) embebido SUBSTANTIVAMENTE na introdução — não como Sinek-speak',
    'Salvaguardas metodológicas declaradas (subsec própria, 5 itens): SUTVA + staggered DiD, Roth 2022 parallel trends, wild-cluster bootstrap p/ N=27, CI partial reproducibility, cividis non-neutrality',
    'Kakwani K=+0,183 (IC bootstrap [+0,124; +0,241]) + índice de necessidade DP/RM com 9× variação entre extremos (RR 1.435 vs DF 152 pacientes/aparelho)',
    'DiD 2x2 + TWFE clusterizado sobre EC 86/2015 com null/marginal HONESTO + interpretação substantiva (crowding-out, capital visível vs invisível)',
    'Framing "Brasil como laboratório natural" para pesquisa em política de capital diagnóstico — múltiplos cutoffs constitucionais, heterogeneidade calibrada das 27 UFs, triangulação CNES × SIH-AIH × Portal Transparência',
    'Artigo INDEPENDENTE e auto-contido — sem platform-talk Mirante no corpo. Pode ser submetido a qualquer periódico sem reescrita institucional',
    'Bibliografia expandida 30 → 44 com URLs + "Acesso em DD/MM/YYYY HH:MM (BRT)" em todas refs online (padrão ABNT++); URLs aparecem como links azuis clicáveis no PDF (hyperref colorlinks + xurl)',
    'fig02-architecture redesenhada estilo Databricks blog (cores metálicas reais, sombras, arrows finas) — qualidade visual editorial',
    '13 figuras vetoriais matplotlib em identidade visual editorial Mirante (Lato + paleta hierárquica + golden ratio + halo + leader lines + adjustText + polylabel)',
    '2 mapas coropléticos por UF — RM/Mhab + densidade combinada neuroimagem-PD',
    'Coautoria engenheiro+clínico (Rolim+Chalhoub) integrada substantivamente',
  ],
  problemasParaNotaPlena: [
    'A é teto da régua mestrado — o trabalho está exatamente no patamar máximo do nível atual. Para subir a doutorado, ver problemasParaSubirNivel.',
    'Salvaguardas robustez DECLARADAS mas ainda não IMPLEMENTADAS: wild-cluster bootstrap, Roth 2022 parallel trends, replicação cross-shock EC 100',
    'Random Forest e Causal Forest descritos como agenda — falta o pipeline efetivamente treinado com resultados numéricos reportados (esperado em v3.2 ou v4.0)',
    'CNES × SIH-AIH (cadastro × utilização efetiva) declarado mas não implementado',
  ],
  problemasParaSubirNivel: [
    'PROMOÇÃO PRA DOUTORADO exige: implementar (não só declarar) wild-cluster bootstrap + Roth 2022 + cross-shock EC 100 + IV pra cross-vertical PBF',
    'Treinar Random Forest com dataset real e reportar feature importance + Causal Forest com CATE por UF mapeado — transformar agenda em resultado',
    'Peer review formal: submeter a Cad Saúde Pública (acesso aberto, CONITEC) ou Lancet Reg Health Americas (escopo internacional)',
    'Replicação independente por terceiros — fork do repositório + execução end-to-end + reprodução do gold seria validação externa decisiva',
    'Implementar pelo menos UMA das 5 hipóteses falsificáveis (H1-H5) com dados — preferencialmente H4 (paradoxo das emendas via SIOPS painel) que é a de menor custo de implementação',
  ],
  proximosPassos: [
    'Esta semana: DOI Zenodo + abstract em inglês — citabilidade internacional (40min de trabalho, abre porta pra Cad SP / Lancet Reg Health Am)',
    'Próximas 2 semanas: Implementar wild-cluster bootstrap (boottest/wildboottest) sobre TWFE existente — primeira ação concreta do roadmap declarado',
    'Próximo mês: Treinar Random Forest com 5 features (PIB pc, PBF, RP6 pc, idade mediana, dívida/RCL) e reportar feature importance + identificar UFs com resíduos atípicos como contribuição empírica nova',
    'Próximos 2 meses: Implementar event-study TWFE com leads/lags ±5 anos sobre EC 86 + teste Roth 2022 → fecha agenda de robustez declarada',
    '6 meses: Cross-shock EC 100/2019 + estimadores Callaway-Sant\'Anna; submeter v4.0 a Cad Saúde Pública',
    'Versão expandida (Seção Política + Causal Forest CATE map) para Journal of Public Health Policy ou Lancet Reg Health Am',
  ],
};

// ═══════════════════════════════════════════════════════════════════════
// WP #5 — UROPRO LONGITUDINAL 17 ANOS
// Slug: uropro-saude-publica-2008-2025 · Vertical: UroPro
// Régua: LATO SENSU 9,2/10.
// ═══════════════════════════════════════════════════════════════════════
export const PARECER_WP5_UROPRO = {
  slug:    'uropro-saude-publica-2008-2025',
  wp_num:  5,
  artigo_titulo: 'Cirurgia uroginecológica no SUS, 2008–2025: ganhos silenciosos de eficiência, desigualdade territorial persistente, choque pandêmico e represa cirúrgica',
  vertical: 'uropro',
  nivel: 'lato_sensu',
  scoreType: 'numeric',
  scoreNumeric: 9.2,
  scoreOriginal: null,
  originalLabel: null,
  originalUrl: null,
  ultimaAtualizacao: `${HOJE}T22:30 BRT`,
  versao: '1.0 — recorte longitudinal 17 anos, pós-correção do silver',
  resumoCalibragem:
    'Avaliado como Lato sensu (Especialização/MBA). Recorte vertical-only ' +
    'da cirurgia uroginecológica no SUS em janela de 17 anos (2008-2025), ' +
    'documentando: (a) queda de 40% na permanência hospitalar (eficiência ' +
    'clínica), (b) o choque pandêmico COVID-19 (2020-2021), (c) a represa ' +
    'cirúrgica resultante e seu escoamento parcial em 2024-2025, (d) ' +
    'desigualdade territorial persistente (variação ~100× entre SC e RR ' +
    'no acesso por 100k em 2025). 9,2 lato sensu — abaixo do WP#3 (9,5) ' +
    'porque escopo é mais focado e cross-vertical não está aqui.',
  utilidadeSocial:
    'UTILIDADE ALTA NO NICHO. Pacientes com incontinência urinária ' +
    'tratáveis cirurgicamente representam 25-45% das mulheres adultas ' +
    'brasileiras (Haylen et al., 2010). Beneficiários: Enfermagem ' +
    'uroginecológica, residência em Saúde da Mulher, gestores hospitalares ' +
    'estaduais (identificação de gaps de acesso), Sociedades Brasileiras ' +
    '(SBC Urologia, SOGESP) com evidência quantitativa para diretrizes ' +
    'clínicas, jornalismo de saúde com série consolidada deflacionada e ' +
    'reprodutível.',
  pontosFortes: [
    'Janela longitudinal de 17 anos (2008-2025) cobrindo o choque pandêmico e o pós-COVID',
    'Documenta queda silenciosa de 40% na permanência hospitalar — ganho de eficiência clínica raramente mensurado',
    'Identifica e quantifica a represa cirúrgica pós-pandemia — análise de represa em escoamento 2024-2025',
    'Pipeline live com microdados SIH-AIH-RD filtrados via SIGTAP no bronze',
    'Padrão "Bronze é STRING-ONLY" aplicado: tipagem só no silver, máxima auditabilidade',
    'Aplicação sobre o gold corrigido (commit fa869cf) — desigualdade territorial real, não inflada',
  ],
  problemasParaNotaPlena: [
    'Sem desfechos longitudinais individuais (re-internação, mortalidade tardia) — apenas séries agregadas',
    'Análise da represa cirúrgica é exploratória — sem modelo formal de fila ou de demanda comprimida',
  ],
  problemasParaSubirNivel: [
    'Para mestrado: identificação causal sobre o choque COVID — é DiD natural com cutoff em mar/2020',
    'Estratificação por sexo/idade/raça da paciente ausente — gold colapsa antes desses cortes',
    'Sem cruzamento com produção CNES (estabelecimentos com estrutura uroginecológica)',
    'Modelo de fila/represa cirúrgica não-paramétrico ausente — literatura de Operations Research em saúde tem ferramentas',
  ],
  proximosPassos: [
    'DiD sobre o choque COVID-19 (mar/2020) como cutoff natural — quantifica o efeito da pandemia na produção cirúrgica por UF',
    'Modelo formal de represa: estimar tempo médio de espera implícito por UF baseado em redução-recuperação de produção',
    'Cruzar com CNES uroginecológico (mesmo projeto) — testar se UFs com mais estrutura recuperam mais rápido',
    'Submeter à Revista Brasileira de Saúde Materno Infantil ou a Cad Saúde Pública',
  ],
};

// ═══════════════════════════════════════════════════════════════════════
// WP #6 — EQUIPAMENTOS PANORAMA CROSS-VERTICAL
// Slug: equipamentos-panorama-cnes · Vertical: Equipamentos
// Régua: STRICTO SENSU MESTRADO — letra B.
// Migrado de lato sensu 9,3 → stricto sensu B em 2026-04-27 para refletir
// (a) Reunião #2 do Conselho (média 2,33, APROVADO COM AJUSTES) sobre v2,
// (b) audit Finanças completa de WP#6 v3.0 (2026-04-27, score B 2,0) e
// (c) incidente "fabricated results" v3.0 corrigido em commit 7ad8885.
// ═══════════════════════════════════════════════════════════════════════
export const PARECER_WP6_EQUIPAMENTOS_PANORAMA = {
  slug:    'equipamentos-panorama-cnes',
  wp_num:  6,
  artigo_titulo: 'Panorama integrado: equipamentos de saúde como nó cross-vertical do Mirante dos Dados — análise do trio de neuroimagem (RM, CT, PET/CT) e seus cruzamentos com Bolsa Família, emendas parlamentares e acesso cirúrgico (2013–2025)',
  vertical: 'equipamentos',
  nivel: 'stricto_sensu_mestrado',
  scoreType: 'letter',
  scoreLetra: 'B',
  scoreOriginal: 9.3,
  originalLabel: 'Avaliação anterior — régua lato sensu',
  originalUrl: null,
  ultimaAtualizacao: `${HOJE}T17:00 BRT`,
  versao: '3.0 — pós Reunião #2 do Conselho + audit Finanças + correção fabricated results',
  resumoCalibragem:
    'Régua: STRICTO SENSU MESTRADO (mesma do WP#4). Score B (2,0 pts) — ' +
    'no limiar de aprovação. Migração de "lato sensu 9,3/10" para "stricto ' +
    'sensu B" reflete três sinais convergentes: (i) Reunião #2 do Conselho ' +
    'do Mirante fechou em 26/04/2026 com média (B 2,0 + B+ 2,5 + B+ 2,5)/3 ' +
    '= 2,33 — APROVADO COM AJUSTES sobre v2 (commit dda3e6e); (ii) audit ' +
    'integral de Finanças sobre v3.0 em 27/04/2026 manteve B (multiple ' +
    'testing sem Bonferroni, RF sem LOOCV, CAR nomeado incorretamente); ' +
    '(iii) caça a inconsistências em 27/04/2026 listou 22 itens (5 críticas, ' +
    '9 altas) cross-WP#4↔WP#6, incluindo K_RM divergente, métricas HMC ' +
    'reportadas para modelo não-implementado e SUS share PET/CT contraditório. ' +
    'O incidente "fabricated ML results" foi pego pelo autor e corrigido ' +
    '(commit 7ad8885) — credibilidade preservada, mas o score reflete o ' +
    'estado pós-correção. PARA SUBIR pra B+/A: corrigir as 22 inconsistências ' +
    '+ implementar (não declarar) a identificação causal cross-vertical.',
  utilidadeSocial:
    'EXTREMAMENTE ÚTIL como produto-síntese da plataforma. Beneficiários: ' +
    'pesquisadores em política de saúde testando hipóteses cross-fonte ' +
    '(renda × capital × acesso); gestores estaduais comparando a posição ' +
    'relativa de seu estado em múltiplas dimensões simultaneamente; ' +
    'jornalismo de dados em saúde com narrativa cross-vertical pronta. A ' +
    'documentação transparente do fix dual-flag (dedup IND_SUS) é ' +
    'contribuição metodológica concreta — quem trabalhar com microdados ' +
    'CNES ganha ferramenta validada.',
  pontosFortes: [
    'Paper agregador cross-vertical: integra Equipamentos × Bolsa Família × Emendas × UroPro sobre arquitetura medalhão unificada',
    'Correlação ρ ≈ -0,68 entre cobertura PBF e densidade de RM — replicação independente do paradoxo regional',
    'Paradoxo das emendas: ρ ≈ -0,31 entre emendas per capita e capacidade diagnóstica — UFs que recebem mais emendas NÃO têm mais capital diagnóstico',
    'Correção metodológica documentada: fix dual-flag IND_SUS (dedup max(SUS,Priv)) corrigindo double-count que persistia silenciosamente',
    'WHY duplo formalizado em v3.0 (substituiu prosa solta da v2)',
    '15+ figuras vetoriais em identidade visual editorial Mirante (Lato + Wong palette + golden ratio)',
    'Lente focal "trio de neuroimagem" como dispositivo analítico cross-vertical reusável',
    'Reunião #2 do Conselho APROVADO COM AJUSTES (média 2,33, acima do limiar 2,0)',
    'Autor pegou e corrigiu o incidente fabricated results (commit 7ad8885) — sinal de auto-auditoria',
  ],
  problemasParaNotaPlena: [
    'Audit Finanças (27/04/2026): 22 inconsistências verificáveis cross-WP#4↔WP#6 — 5 críticas, 9 altas',
    'Multiple testing sem correção Bonferroni/Holm sobre as 8 correlações Pearson',
    'Random Forest declarado sem LOOCV reportado',
    'CAR (Conditional Average Response) nomeado incorretamente — não corresponde à definição padrão',
    'Cross-vertical é correlacional — sinais ρ não estabelecem causalidade (assumido limite mas não testado)',
  ],
  problemasParaSubirNivel: [
    'B → B+: corrigir as 22 inconsistências apontadas no audit + Bonferroni sobre as 8 correlações + LOOCV no RF',
    'B+ → A: identificação causal sobre os 3 cruzamentos (mesmas opções do WP#4: EC 86, EC 100, MP 1.061) IMPLEMENTADA — não apenas declarada',
    'Estender Kakwani + necessidade do WP#4 para todas as 3 modalidades (RM, CT, PET/CT)',
    'Cruzamento intra-UF (capital × interior) ausente — só inter-UF',
  ],
  proximosPassos: [
    'P1 (crítico): corrigir as 22 inconsistências cross-WP#4↔WP#6 listadas no audit Finanças de 27/04/2026',
    'P2 (alto): implementar correção Bonferroni/Holm sobre as 8 correlações Pearson + IC bootstrap',
    'P3 (alto): rodar RF de fato com LOOCV antes de reportar qualquer R² ou importância de variável',
    'P4 (médio): renomear ou redefinir CAR conforme literatura padrão',
    'P5 (médio): submeter como paper de método (Methodology in Medical Research) ou Cad Saúde Pública pós-P1–P3',
  ],
};

// ═══════════════════════════════════════════════════════════════════════
// WP #7 — BOLSA FAMÍLIA POR MUNICÍPIO
// Slug: bolsa-familia-municipios · Vertical: PBF
// Régua: STRICTO SENSU MESTRADO. Score B+ (2,5 pts) — ACIMA do limiar.
// Sobe sobre WP#2 (que ficou em 1,83) por resolver o gargalo dos N=27
// clusters identificado na peer review de Finanças do WP#2 em 2026-04-27.
// ═══════════════════════════════════════════════════════════════════════
export const PARECER_WP7_BOLSA_FAMILIA_MUNICIPIOS = {
  slug:    'bolsa-familia-municipios',
  wp_num:  7,
  artigo_titulo: '5.570 pontos de decisão: microdados municipais do Bolsa Família, identificação causal por variação cross-municipal e heterogeneidade intra-UF (2013–2025)',
  vertical: 'pbf',
  nivel: 'stricto_sensu_mestrado',
  scoreType: 'letter',
  scoreLetra: 'B+',
  scoreOriginal: null,
  originalLabel: null,
  originalUrl: null,
  ultimaAtualizacao: `${HOJE}T22:30 BRT`,
  versao:
    '2.0 — fallback substituído por dados REAIS (44.554 obs × 5.570 munis × 8 anos) ' +
    'agregados via SQL warehouse direto sobre bronze.pbf_pagamentos (2,53 bi linhas); ' +
    'malha geobr canônica (5.570 munis IBGE 2020); população SIDRA/IBGE real com ' +
    '2022 via Censo (tabela 4709) + 2023 interpolação documentada. Heterogeneidade ' +
    'INTRA-UF agora é EFETIVA, não artificial.',
  resumoCalibragem:
    'Régua STRICTO SENSU MESTRADO. Score B+ (2,5 pts) — acima do limiar ' +
    '2,0. Sobe sobre WP#2 (1,83) por quatro contribuições concretas, agora ' +
    'lastreadas em microdados REAIS (não fallback): (i) migração de N=27 ' +
    'para k=5.570 clusters, reabilitando inferência cluster-robusta com ' +
    'wild-cluster bootstrap convergente (Cameron-Gelbach-Miller 2008 ' +
    'recomenda k≥30 — temos 185×); (ii) Conley HAC com distâncias ' +
    'geodésicas haversine REAIS sobre centroides geobr, bandwidth ' +
    'sensitivity 50–1600 km mostrando |t|≥2,0 mesmo no extremo; (iii) ' +
    'decomposição Theil L within/between que finalmente quantifica ' +
    'variação intra-UF EFETIVA — não mais alocação proporcional UF→muni; ' +
    '(iv) DiD 2×2 sobre as duas rupturas (MP 1.061/2021 +205 R$/hab; ' +
    'Lei 14.601/2023 +349 R$/hab) com dados de pagamento por município ' +
    'mês a mês. PARA SUBIR PRA A: kernel Bartlett (vs uniforme), RDD ' +
    'geográfico em fronteiras estaduais, outcomes proxy mensais ' +
    '(DATASUS-SIM, INEP, CAGED), e pytest CI cobrindo silver/gold.',
  utilidadeSocial:
    'EXTREMAMENTE ÚTIL como demonstração metodológica: qualquer pesquisador ' +
    'em política social brasileira que esteja fazendo inferência sobre ' +
    'painel UF×Ano agora tem um TEMPLATE para migrar para Município×Ano ' +
    'usando exclusivamente dados públicos (CGU + IBGE/Localidades + ' +
    'IBGE/SIDRA + kelvins/Municipios-Brasileiros + IPCA-BCB). Os 6 ' +
    'notebooks Databricks + 4 scripts Python locais são reutilizáveis fora ' +
    'do contexto PBF — basta trocar o silver de origem. A contribuição ' +
    'central é reduzir o custo marginal de pesquisa quasi-experimental ' +
    'sobre o programa de meses-de-engenharia para minutos-de-leitura.',
  pontosFortes: [
    'Microdados REAIS via agregação SQL warehouse direto sobre bronze.pbf_pagamentos (2,53 bilhões de linhas) — não mais fallback proporcional',
    'Malha geobr canônica (5.570 munis IBGE 2020) — substitui pipeline coords_municipios quebrado (Atlas CSV ausente + 5570 chamadas API)',
    'IBGE/SIDRA real com 2022 via Censo (tabela 4709, var 93) + 2023 interpolação linear documentada e flag populacao_estimada=true',
    'TWFE com k=5.570 clusters (185× o mínimo Cameron-Gelbach-Miller 2008 para wild-cluster bootstrap convergir)',
    'Conley HAC com distâncias geodésicas haversine REAIS sobre centroides geobr — não cluster artificial',
    'Bandwidth sensitivity 50–1600 km mostra correlação espacial empírica nos resíduos com |t|≥2,0 em todos os pontos',
    'DiD 2×2 sobre as duas rupturas: MP 1.061/2021 (+205 R$/hab) e Lei 14.601/2023 (+349 R$/hab) com 5.570 painéis',
    'Decomposição Theil L within/between-UF agora EFETIVA — variação intra-UF não é mais artefato de alocação proporcional',
    'Pipeline Databricks 6 notebooks (ingest geobr + silver pop_municipio_ano + silver pbf_total_municipio_mes + gold pbf_municipios_df + 2 export)',
    'Padrão STRING-ONLY bronze respeitado em geobr_municipios_meta + UC metadata mandatória completa (COMMENT + TAGS)',
    '5 mapas coropléticos com paletas distintas colorblind-safe (magma_r, YlOrRd, cividis_r, Greys, viridis_r) + 10 figuras analíticas — total 15 figs',
    'Match IBGE↔CGU 100% via NAME_FIX_UF (25 ortografias divergentes mapeadas, ex: Brazópolis-MG ↔ BRASOPOLIS-MG, Itapajé-CE ↔ ITAPAGE-CE)',
  ],
  problemasParaNotaPlena: [
    'Conley HAC implementado com kernel uniforme simplificado — Bartlett (Conley 1999) ou Parzen seriam mais ortodoxos',
    'IDH-M Atlas Brasil 2010 desatualizado — Censo 2022 ainda não publicou IDHM',
    'Tratamento via deficit pré-choque idêntico ao WP#2 — mesma definição arbitrária do quartil',
    'Sem RDD geográfico em fronteiras estaduais (ferramenta que 5.570 munis habilitaria)',
    'pytest_test_pbf_municipal.py ausente — gap declarado pela cadeira de Eng. Software',
    'Vertical web sem interatividade Vega-Lite — top/bottom 20 são listas estáticas',
    'Multiple testing nos 2 DiDs sem correção Bonferroni nem meta-análise formal',
    'Event study apresentado mas sem teste formal Roth 2022 de parallel trends',
  ],
  problemasParaSubirNivel: [
    'B+ → A: implementar Conley HAC com kernel Bartlett (ortodoxo Conley 1999) e bootstrap espacial',
    'B+ → A: RDD geográfico em fronteiras estaduais (BA-MG, RJ-SP) onde regras de auxílio estadual diferem',
    'B+ → A: outcomes proxy mensais (DATASUS-SIM óbitos infantis, INEP abandono, CAGED formalização) para validar mecanismo causal',
    'B+ → A: pytest CI sobre silver/gold + ARCHITECTURE.md específico do WP#7',
    'B+ → A: scatter Vega-Lite interativo (filtrar UF, hover detalhes) substituindo top/bottom 20 estáticos',
    'B+ → A: Lighthouse audit 95+/95+/95+ no vertical /bolsa-familia-municipios',
  ],
  proximosPassos: [
    'P1 (alto): kernel Bartlett substituindo uniforme — fecha gap ortodoxia Conley 1999',
    'P2 (alto): RDD geográfico em fronteiras estaduais com auxílios diferenciais (BA-MG, RJ-SP)',
    'P3 (médio): outcomes proxy mensais (DATASUS-SIM, INEP, CAGED) para validar mecanismo causal além de paramount',
    'P4 (médio): pytest_test_pbf_municipal.py + ARCHITECTURE.md fechando gap Eng. Software',
    'P5 (médio): replicação metodológica em outros programas sociais (Auxílio Gás, BPC, Pé-de-Meia, Auxílio Reconstrução RS)',
    'P6 (baixo): curso/consultoria como monetização do pipeline (gap Administração) — Hotmart/Coursera',
  ],
};


// ═══════════════════════════════════════════════════════════════════════
// WP #3 RAIS — VÍNCULOS PÚBLICOS / FAIR LAKEHOUSE
// Slug: rais-fair-lakehouse · Vertical: RAIS
// Régua: LATO SENSU 6,8/10.
// (Nota: numeração WP#3 conflita com UroPro WP#3. Convenção Mirante:
// UroPro tem o WP#3 canônico cross-vertical; RAIS é numerado n.3 internamente
// na vertical mas o ID público segue o slug do .tex.)
// ═══════════════════════════════════════════════════════════════════════
export const PARECER_WP_RAIS = {
  slug:    'rais-fair-lakehouse',
  wp_num:  3,
  wp_num_label: 'WP #3 (RAIS)',
  artigo_titulo: 'RAIS, FAIRness e Lakehouse: replicação e extensão de comparação empírica de formatos para Big Data público brasileiro (2020–2025)',
  vertical: 'rais',
  nivel: 'lato_sensu',
  scoreType: 'numeric',
  scoreNumeric: 7.3,
  scoreOriginal: 8.0,
  originalLabel: 'Monografia UFRJ MBA, 2023 — régua lato sensu, avaliação IA',
  originalUrl: 'https://github.com/leonardochalhoub/CodingMBA_UFRJ/blob/main/Monografia_LeonardoChalhoub.pdf',
  ultimaAtualizacao: `${HOJE}T21:10 BRT`,
  versao: '0.7 — extração Hive-partitioned <TXT_EXTRACTED>/ano=YYYY/ corrige colisão silenciosa entre .7z de anos diferentes (banca reprovou; sem nota atribuída)',
  resumoCalibragem:
    'CONTEXTO HISTÓRICO: o autor foi REPROVADO pela banca da UFRJ ' +
    '(MBA Engenharia de Dados, set/2023). A banca não atribuiu nota ' +
    'numérica — apenas o veredicto de reprovação. Dois números aparecem ' +
    'em telas como "scores", e ambos são posteriores e externos à banca: ' +
    '(a) o "Score original" 8,0 é a reavaliação da monografia hoje pela ' +
    'IA do próprio Mirante (Claude Opus, modo professor de programa de ' +
    'mestrado/doutorado, régua lato sensu); (b) o "Score" 6,8 é a ' +
    'avaliação da IA sobre o vertical RAIS desta plataforma — não da ' +
    'monografia original, e não da banca.',
  utilidadeSocial:
    'UTILIDADE CONDICIONAL. RAIS Vínculos Públicos é a base de microdados ' +
    'mais completa sobre emprego formal no Brasil. CONTUDO, no estado ' +
    'atual o pipeline RAIS NÃO RODOU AINDA — utilidade prática é ZERO até ' +
    'gerar gold. A promessa é alta; a entrega ainda não chegou.',
  pontosFortes: [
    'Infraestrutura open-source versionada em Git — atende parcialmente princípios FAIR sobre o próprio trabalho',
    'Arquitetura medallion canônica (bronze/silver/gold) com padrão híbrido batch+Auto Loader',
    'Bronze STRING-ONLY (regra de plataforma — nenhuma inferência de tipo em bronze, casts apenas em silver+)',
    'Spec doc explícito (docs/vertical-rais-fair-lakehouse-spec.md) documenta parecer crítico da monografia + roadmap',
    'Defensive guards em todas camadas downstream (skip on missing upstream) — evita cascade failures',
    'Bronze auto-recovery: detecta .7z corrompido (Bad7zFile), deleta + re-baixa do FTP PDET, quarenta após 1 retry — não trava por single bad file',
    'Pré-validação por arquivo (py7zr.is_7zfile + getnames): detecta TODOS os .7z corrompidos antes do loop de extração, não só os que falham na ordem do glob',
    'Extração Hive-partitioned em <TXT_EXTRACTED>/ano=YYYY/ — corrige bug silencioso de colisão entre .7z de anos diferentes (PDET 2019+ usa nomes de .txt sem ano, sobrescrevia em dir flat); ano derivado via regex em _metadata.file_path',
  ],
  problemasParaNotaPlena: [
    'Pipeline em execução pela primeira vez 2026-04-27 — alguns arquivos PDET estão chegando corrompidos (ex.: BR_2009..2013 a 237KB), auto-recovery acionado',
    'Ingest PDET acabou de ser corrigido (FTP, não HTTPS) mas ainda não testado em produção',
    'Artigo (.tex) é literalmente um esqueleto: 6 das 6 seções marcadas "[A ser escrito]"',
  ],
  problemasParaSubirNivel: [
    'Replicação literal não constitui contribuição original — peso 15% da nota não está sendo atendido',
    'Sem desenho experimental controlado: número de execuções, variância, IC 95%, teste de hipótese',
    'Sem comparação com formatos não-Delta (Iceberg, Hudi)',
    'FAIR scoring promete usar RDA Maturity Model mas não tem implementação sequer em planejamento detalhado',
    'Análise when-not-to-use Lakehouse não tem nem outline',
  ],
  proximosPassos: [
    'Confirmar URL PDET (FTP corrigido pra ftp.mtps.gov.br) e rodar ingest pra ter pelo menos 1 ano de RAIS no Volume',
    'Rodar pipeline end-to-end pra ter pelo menos um silver/gold com dados',
    'Escrever a Seção 4 (Resultados) do .tex com números reais e tratamento estatístico desde o início',
    'Implementar comparação com Iceberg E Hudi (não apenas mencionar)',
    'Implementar FAIR scoring via algum dos frameworks consagrados (RDA, FAIRplus)',
  ],
};

// ═══════════════════════════════════════════════════════════════════════
// GLOBAL — Avaliação macro do projeto inteiro (não de uma vertical isolada)
// Aparece na página Início. Régua: STRICTO SENSU MESTRADO.
// ═══════════════════════════════════════════════════════════════════════
export const PARECER_GLOBAL = {
  vertical: 'global',
  nivel: 'stricto_sensu_mestrado',
  scoreType: 'letter',
  scoreLetra: 'A',
  scoreOriginal: null,
  originalLabel: null,
  originalUrl: null,
  ultimaAtualizacao: `${HOJE}T21:45 BRT`,
  versao:
    '6.0 — promoção B+ → A na régua mestrado: 3 WPs stricto sensu + ' +
    'framework editorial-crítico operacional + 3 Reuniões do Conselho + ' +
    'pipeline RAIS em execução + camada de auto-recovery bronze',
  resumoCalibragem:
    'Avaliação MACRO do projeto inteiro (não de uma vertical isolada). ' +
    'A v6.0 sobe de B+ para A na régua mestrado porque o projeto ' +
    'atravessou múltiplos limiares qualitativos simultaneamente desde a ' +
    'avaliação anterior, e A na régua é "excelente, próximo do teto do ' +
    'mestrado" — exatamente o que descreve o estado atual. As mudanças ' +
    'que justificam a promoção: (1) TRÊS WPs em stricto sensu, não mais ' +
    'um — WP#2 promovido de lato 8,5 → stricto B+ via rewrite v2.0 ' +
    'completo (DiD/TWFE/WCB sobre MP 1.061/2021, Kakwani × IDH-M por UF, ' +
    'ITS sobre série mensal nov/2021, benchmark internacional com ' +
    'AUH/Prospera/MFA/Renta Dignidad em US$ PPP 2021, 17 figuras ' +
    'vetoriais — incluindo barbell DiD e event study); WP#4 evoluiu pra ' +
    'v3.1 com Bloco-esta-semana (Conley HAC com ICs negativos ' +
    'preservados, SHAP subordinado a economia, pytest CI ativo, 5 bugs ' +
    'visuais corrigidos — commit b4f5b88); WP#6 escalou de v2 → v3.0 com ' +
    '+171% de conteúdo (3.869 linhas), WHY duplo formalizado, 6 modelos ' +
    'ML adicionados e análise causal preliminar. (2) TRÊS Reuniões do ' +
    'Conselho do Mirante formalizadas e RENDERIZADAS na plataforma — ' +
    '#1 WP#4 v2.1 (APROVADO COM AJUSTES, 4 rodadas), #2 WP#6 v3.0 (3 ' +
    'rodadas), #3 WP#2 v1.0 → v2.0 (motivou rewrite completo). (3) ' +
    'QUATRO personas conselheiras estáveis e operando (Finanças/Eng. ' +
    'Software/Design HCI/Administração) com lentes próprias e atas ' +
    'auditáveis. (4) Audit integral de Finanças cross-WP (WP#4 v3.1 + ' +
    'WP#6 v3.0) catalogou 22 inconsistências verificáveis com prioridade ' +
    'codificada (5 críticas, 9 altas, 6 médias, 2 baixas) — disciplina ' +
    'de revisão acima do padrão de Working Papers auto-publicados. (5) ' +
    'Vertical RAIS saiu de "promessa zero" pra execução real (2026-04- ' +
    '27), com bronze auto-recovery em 3 camadas (pré-validação magic ' +
    'bytes + central directory, deleta + re-baixa do FTP PDET, Hive- ' +
    'partitioned ano=YYYY/ pra evitar colisão silenciosa cross-ano). ' +
    'A na régua mestrado é "passa com folga, próximo do teto" — não é ' +
    'ainda doutorado, que exigiria peer review FORMAL externo aceito + ' +
    'Zenodo DOI por WP + reprodução INDEPENDENTE por terceiros + ' +
    'contribuição metodológica original publicada (o framework de 4 ' +
    'cadeiras é candidato natural a essa contribuição). Esses são gaps ' +
    'do tier seguinte, não desta avaliação.',
  utilidadeSocial:
    'EXTREMAMENTE ÚTIL E AMPLAMENTE APLICÁVEL. O Mirante é uma plataforma ' +
    'que reduz drasticamente o custo marginal de pesquisa em dados ' +
    'públicos brasileiros. Beneficiários CONCRETOS: jornalismo de dados, ' +
    'pesquisadores acadêmicos em Saúde Coletiva/Ciência Política/Economia/ ' +
    'Enfermagem, ONGs (Transparência Brasil, Fiquem Sabendo, Open ' +
    'Knowledge Brasil), gestores públicos municipais e estaduais. ' +
    'Equivale a um IPEA Data privado, mantido por uma pessoa, em stack ' +
    '100% gratuito. A v5.0 amplia: o framework editorial-crítico ' +
    '(4 conselheiros + atas formalizadas) é em si publicável como ' +
    'metodologia de peer review interno reprodutível por outros grupos ' +
    'de pesquisa que não tenham acesso a banca formal.',
  pontosFortes: [
    'Escala Big Data REAL: PBF tem 2,5 bilhões de linhas em bronze (280 GB CSV); CNES 6.614 DBCs; SIH 11.048 DBCs; RAIS em ingest desde 2026-04-27 (136M linhas/biênio estimados)',
    'Stack profissional integrada: Apache Spark + Delta Lake + Databricks UC + Auto Loader + Asset Bundles',
    'Pipelines-como-código: nenhum drag-and-drop em GUI. Toda etapa versionada em Git, idempotente, reprodutível',
    'CI/CD multi-camada: deploy-pages, refresh-pipelines, auto-sync-gold — três workflows distintos coordenados',
    'Multi-linguagem real: Python (PySpark, pandas, matplotlib), JavaScript/React (Vite + Recharts + d3), SQL (Spark SQL), LaTeX (artigos ABNT), Bash, YAML',
    'Multi-formato real: DBC (PKWARE compactado, formato proprietário DATASUS), 7Z (RAIS), ZIP (CGU), CSV/TXT/JSON, Parquet, Delta Lake',
    'Open-source + FAIR-aderente: tudo em GitHub público, código MIT, dados gold versionados, refresh mensal automatizado',
    '7 trabalhos avaliados: 3 stricto sensu (WP#2 v2.0 B+, WP#4 v3.1 B+, WP#6 v3.0 B) + 4 lato sensu (WP#1 9,0; WP#3 9,5; WP#5 9,2; WP_RAIS 7,3)',
    'WP#2 v2.0 — promoção qualitativa de lato 8,5 → stricto B+: rewrite completo após Reunião #3 do Conselho com média 1,5 (autor optou por refazer em vez de patch incremental). Adiciona DiD/TWFE/WCB sobre MP 1.061/2021, Kakwani × IDH-M por UF, ITS sobre série mensal nov/2021, benchmark CCT internacional (AUH/Prospera/MFA/Renta Dignidad em US$ PPP 2021), 17 figuras vetoriais incluindo barbell DiD e event study',
    'WP#4 v3.1 — endereçou Bloco-esta-semana da R3 do Conselho (commit b4f5b88): Conley HAC com ICs negativos preservados, SHAP subordinado a economia (não autônomo), pytest CI ativo (13 testes sobre gold), 5 bugs visuais corrigidos. Roth 2022 + cross-shock EC 100 ainda pendentes',
    'WP#6 v3.0 — escalou de v2 → v3.0 com +171% de conteúdo (3.869 linhas vs 1.428): WHY duplo formalizado em Reunião #2 do Conselho, 6 modelos ML adicionados, análise causal preliminar (TWFE EC 86 ainda pendente), 50 páginas estimadas',
    'Framework editorial-crítico interno operacional: 4 personas conselheiras (Finanças, Eng. Software, Design HCI, Administração) com lentes próprias + 3 atas formalizadas e RENDERIZADAS na plataforma (Reunião #1 WP#4, #2 WP#6, #3 WP#2)',
    'Audit cross-WP de Finanças (2026-04-27) catalogou 22 inconsistências verificáveis com prioridade codificada (5 críticas, 9 altas, 6 médias, 2 baixas) — disciplina de revisão por pares interna acima do padrão de Working Papers auto-publicados',
    'Identidade visual editorial Mirante (Lato + paleta hierárquica + grid horizontal + halo + leader lines + polylabel + adjustText) aplicada nas 80+ figuras dos artigos',
    'Modelo de coautoria engenheiro+clínico demonstrado no WP#4 (Rolim+Chalhoub) — único da série com coautor externo',
    'Modelo de análise cross-vertical demonstrado no WP#3 e WP#6 (cruzamento de 3+ verticais sobre arquitetura medalhão unificada)',
    'Auditabilidade pública demonstrada de ponta a ponta: bug silver descoberto/corrigido/documentado (commit fa869cf), incidente de números fabricados pego pelo autor e corrigido com commit nominal (7ad8885), bug de partição RAIS detectado em produção e corrigido (b1809c1) — tudo no log público',
    'RAIS bronze ingest com auto-recovery em 3 camadas: pré-validação por arquivo (py7zr.is_7zfile + getnames lê magic bytes + central directory), deleta + re-baixa do FTP PDET após Bad7zFile, Hive-partitioned <TXT_EXTRACTED>/ano=YYYY/ pra evitar colisão silenciosa cross-ano (PDET 2019+ usa nomes de .txt sem ano)',
  ],
  problemasParaNotaPlena: [
    'WP#4 v3.1: Roth 2022 pre-trend test e cross-shock EC 100 ainda pendentes — implementá-los completa o checklist da R3',
    'WP#2 v2.0: rewrite stricto commitado, audit Finanças sobre v2.0 ainda pendente. As 22 inconsistências da v1.0 foram parcialmente endereçadas mas precisam validação completa pré-submissão',
    'WP#6 v3.0: TWFE sobre EC 86 + DOI Zenodo + decisão final 1-paper-vs-2 (panorama integrado vs split por modalidade) ainda pendentes',
    'verify-reproducibility.yml (gap apontado pelo Conselheiro de Eng. Software) ainda ausente do CI; reprodutibilidade documentada não é o mesmo que reprodutibilidade verificada',
    'RAIS pipeline saiu de zero pra rodando, mas ainda não fechou ciclo bronze→silver→gold→export→artigo — Working Paper ainda em escopo de plumbing (lato 7,3)',
    'Versões interativas Vega-Lite/Observable de figuras (gap Design HCI) — declaradas como roadmap mas zero implementadas',
  ],
  problemasParaSubirNivel: [
    'PROMOÇÃO PRA DOUTORADO exigiria: (a) peer review FORMAL externo aceito em pelo menos um WP (Cad Saúde Pública, RAP, RBE, Lancet Reg Health Am), (b) Zenodo DOI por WP stricto sensu, (c) reprodução INDEPENDENTE por terceiros (engenheiro de dados não-Chalhoub re-rodando o pipeline e validando bronze→gold por UF), (d) contribuição metodológica original mensurável — o framework editorial-crítico de 4 cadeiras é candidato natural se publicado como meta-artigo',
    'Tese agregadora cross-vertical: usar as 5 verticais juntas pra responder pergunta substantiva sobre complementaridade de instrumentos federais (PBF + emendas + saúde) — papel de tese de doutorado',
    'Análise comparativa de formatos lakehouse (Delta vs Iceberg vs Hudi) prometida em RAIS spec não está implementada — peso 15% da nota da monografia original ainda não atendido',
    'Padronização editorial cross-WP de Kakwani: WP#4 e WP#2 v2.0 implementam Kakwani mas com denominadores diferentes (IDH vs taxa de pobreza) — falta padronização explícita ou justificativa por WP',
  ],
  proximosPassos: [
    'Endereçar Roth 2022 + cross-shock EC 100 no WP#4 v3.2 — completa o checklist R3 e abre caminho pra A no WP individual (hoje B+)',
    'Audit Finanças sobre WP#2 v2.0 (paralelo ao da v1.0) — valida que as 22 inconsistências da v1.0 foram efetivamente endereçadas no rewrite',
    'Submeter WP #2 v2.0 a Cad Saúde Pública OU WP #4 v3.1 a RAP — primeiro peer review externo formal cruza o limiar mestrado→doutorado',
    'verify-reproducibility.yml no CI com pytest sobre sample bronze de cada vertical — fecha o gap declarado pelo Conselheiro de Eng. Software',
    'DOI Zenodo dos 3 WPs stricto sensu (WP#2, WP#4, WP#6) + dicionário canônico CNES — disciplina de citação e versionamento',
    'Fechar ciclo RAIS: pipeline bronze→silver→gold→export+artigo escrito (não esqueleto) sobe o WP_RAIS de 7,3 e adiciona 4a vertical em stricto sensu',
    'Versão interativa Vega-Lite/Observable de pelo menos UMA figura por WP — abre dimensão HCI declarada nas atas das Reuniões #1 e #2',
    'Publicar como meta-artigo separado o framework editorial-crítico de 4 cadeiras + 3 atas — candidato a contribuição metodológica original publicável (peso pra promoção a doutorado)',
  ],
};

// ─── Lookup helpers ──────────────────────────────────────────────────────
//
// PARECERES_BY_SLUG: lookup primário por slug do .tex
// PARECERES_BY_VERTICAL: backward-compat (vertical → 1 parecer "principal")
//
export const PARECERES_BY_SLUG = {
  'emendas-parlamentares':           PARECER_WP1_EMENDAS,
  'bolsa-familia':                   PARECER_WP2_BOLSA_FAMILIA,
  'uropro-serie-2008-2025':          PARECER_WP3_UROPRO,
  'rais-fair-lakehouse':             PARECER_WP_RAIS,
  'equipamentos-rm-parkinson':       PARECER_WP4_EQUIPAMENTOS,
  'uropro-saude-publica-2008-2025':  PARECER_WP5_UROPRO,
  'equipamentos-panorama-cnes':      PARECER_WP6_EQUIPAMENTOS_PANORAMA,
  'bolsa-familia-municipios':        PARECER_WP7_BOLSA_FAMILIA_MUNICIPIOS,
};

// Backward-compat: nas verticais com 1 artigo, o "principal" é o único.
// Nas com 2 (Equipamentos: WP#4+#6, UroPro: WP#3+#5, PBF: WP#2+#7), elege-se
// o WP de maior escopo/score como principal.
export const PARECERES_BY_VERTICAL = {
  pbf:           PARECER_WP2_BOLSA_FAMILIA,
  equipamentos:  PARECER_WP4_EQUIPAMENTOS,
  emendas:       PARECER_WP1_EMENDAS,
  uropro:        PARECER_WP3_UROPRO,
  rais:          PARECER_WP_RAIS,
  global:        PARECER_GLOBAL,
};

// Aliases legacy (mantém imports antigos funcionando).
export const PARECER_PBF          = PARECER_WP2_BOLSA_FAMILIA;
export const PARECER_EQUIPAMENTOS = PARECER_WP4_EQUIPAMENTOS;
export const PARECER_EMENDAS      = PARECER_WP1_EMENDAS;
export const PARECER_UROPRO       = PARECER_WP3_UROPRO;
export const PARECER_RAIS         = PARECER_WP_RAIS;

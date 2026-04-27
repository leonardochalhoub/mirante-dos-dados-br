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
// Régua: LATO SENSU 8,5/10.
// ═══════════════════════════════════════════════════════════════════════
export const PARECER_WP2_BOLSA_FAMILIA = {
  slug:    'bolsa-familia',
  wp_num:  2,
  artigo_titulo: 'Programa Bolsa Família, Auxílio Brasil e Novo Bolsa Família (2013–2025): transformações institucionais, expansão da cobertura e desigualdade territorial',
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
    'processar ~280 GB de microdados CGU.',
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
  scoreNumeric: 7.0,
  scoreOriginal: 8.0,
  originalLabel: 'Monografia UFRJ MBA, 2023 — régua lato sensu, avaliação IA',
  originalUrl: 'https://github.com/leonardochalhoub/CodingMBA_UFRJ/blob/main/Monografia_LeonardoChalhoub.pdf',
  ultimaAtualizacao: `${HOJE}T20:10 BRT`,
  versao: '0.5 — bronze ingest robusto: detecta Bad7zFile + re-download FTP + quarentena (banca reprovou; sem nota atribuída)',
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
  scoreLetra: 'B+',
  scoreOriginal: null,
  originalLabel: null,
  originalUrl: null,
  ultimaAtualizacao: `${HOJE}T16:30 BRT`,
  versao: '4.0 — pós WP#4 v3.0 rewrite multidimensional + identidade visual editorial Mirante',
  resumoCalibragem:
    'Avaliação MACRO do projeto inteiro (não de uma vertical isolada). ' +
    'Esta é a única avaliação do projeto que excede o teto lato sensu — ' +
    'não pelas análises individuais, mas pela ENGENHARIA DE PLATAFORMA ' +
    'que entrega 5 verticais distintas sobre datasets de escala genuína ' +
    'de Big Data. O projeto soma 6 Working Papers em ABNT escritos: ' +
    'WP #1 (Emendas, lato 9,0), WP #2 (Bolsa Família, lato 8,5), WP #3 ' +
    '(UroPro cross-vertical, lato 9,5), WP #4 (Neuroimagem × Parkinson, ' +
    'STRICTO SENSU MESTRADO B+ após rewrite v3.0 multidimensional), WP #5 ' +
    '(UroPro 17 anos, lato 9,2) e WP #6 (Equipamentos panorama ' +
    'cross-vertical, STRICTO SENSU MESTRADO B após Reunião #2 do Conselho + ' +
    'audit Finanças sobre v3.0). Conceito MACRO permanece B+ na régua ' +
    'mestrado: 6 WPs escritos, plataforma sólida, mas o teto A continua ' +
    'condicionado a peer review formal e a implementação (não só ' +
    'declaração) das salvaguardas de robustez declaradas no WP#4 v3.0.',
  utilidadeSocial:
    'EXTREMAMENTE ÚTIL E AMPLAMENTE APLICÁVEL. O Mirante é uma plataforma ' +
    'que reduz drasticamente o custo marginal de pesquisa em dados ' +
    'públicos brasileiros. Beneficiários CONCRETOS: jornalismo de dados, ' +
    'pesquisadores acadêmicos em Saúde Coletiva/Ciência Política/Economia/ ' +
    'Enfermagem, ONGs (Transparência Brasil, Fiquem Sabendo, Open ' +
    'Knowledge Brasil), gestores públicos municipais e estaduais. ' +
    'Equivale a um IPEA Data privado, mantido por uma pessoa, em stack ' +
    '100% gratuito.',
  pontosFortes: [
    'Escala Big Data REAL: PBF tem 2,5 bilhões de linhas em bronze (280 GB CSV); CNES 6.614 DBCs; SIH 11.048 DBCs; RAIS estimados 136M linhas/biênio',
    'Stack profissional integrada: Apache Spark + Delta Lake + Databricks UC + Auto Loader + Asset Bundles',
    'Pipelines-como-código: nenhum drag-and-drop em GUI. Toda etapa versionada em Git, idempotente, reprodutível',
    'CI/CD multi-camada: deploy-pages, refresh-pipelines, auto-sync-gold — três workflows distintos coordenados',
    'Multi-linguagem real: Python (PySpark, pandas, matplotlib), JavaScript/React (Vite + Recharts + d3), SQL (Spark SQL), LaTeX (artigos ABNT), Bash, YAML',
    'Multi-formato real: DBC (PKWARE compactado, formato proprietário DATASUS), 7Z (RAIS), ZIP (CGU), CSV/TXT/JSON, Parquet, Delta Lake',
    'Open-source + FAIR-aderente: tudo em GitHub público, código MIT, dados gold versionados, refresh mensal automatizado',
    '6 Working Papers em ABNT escritos: WP#1 Emendas, WP#2 PBF, WP#3 UroPro cross-vertical, WP#4 Neuroimagem×Parkinson v3.0 STRICTO SENSU, WP#5 UroPro 17 anos, WP#6 Equipamentos panorama',
    'WP#4 v3.0 demonstra que a plataforma ESCALA pra rigor stricto sensu: salvaguardas declaradas, Kakwani implementado, framing "Brasil laboratório natural"',
    'Identidade visual editorial Mirante (Lato + paleta hierárquica + grid horizontal + halo + leader lines + polylabel + adjustText) aplicada nas 60 figuras dos artigos',
    'Modelo de coautoria engenheiro+clínico demonstrado no WP#4 (Rolim+Chalhoub)',
    'Modelo de análise cross-vertical demonstrado no WP#3 e WP#6 (cruzamento de 3+ verticais sobre arquitetura medalhão unificada)',
    'Auditabilidade pública demonstrada (abr/2026): bug silver descoberto, diagnosticado, corrigido (commit fa869cf) e documentado nos próprios papers',
  ],
  problemasParaNotaPlena: [
    'No nível mestrado: salvaguardas de robustez do WP#4 v3.0 estão DECLARADAS mas não IMPLEMENTADAS. Wild-cluster bootstrap, Roth 2022, cross-shock EC 100 são prioridades imediatas',
    'Sem peer review formal: trabalhos disponíveis em Working Papers auto-publicados; submeter pelo menos um a periódico revisado por pares (Cad SP, Lancet Reg Health Am, RAP, RBE) eleva significativamente o nível',
    'Documentação de arquitetura presente em ARCHITECTURE.md (506 linhas, 11 ADRs) — porém verify-reproducibility.yml ainda ausente do CI',
  ],
  problemasParaSubirNivel: [
    'PROMOÇÃO PRA DOUTORADO exigiria: contribuição metodológica original mensurável (não basta replicar), publicação em conferência ou periódico internacional, reprodução INDEPENDENTE por terceiros',
    'Análise comparativa de formatos lakehouse (Delta vs Iceberg vs Hudi) prometida em RAIS spec não está implementada',
    'Falta uma "contribuição agregadora" que use as 5 verticais juntas pra responder pergunta substantiva sobre complementaridade de instrumentos federais — papel de tese',
  ],
  proximosPassos: [
    'Implementar wild-cluster bootstrap + Roth 2022 + cross-shock EC 100 no WP#4 (sai de B+ pra perto de A)',
    'Submeter WP #4 v3.0 a Cad Saúde Pública após implementação das salvaguardas',
    'verify-reproducibility.yml no CI — fecha o gap de Eng. Software',
    'DOI Zenodo do WP#4 + dicionário canônico CNES (2 deposits)',
    'Versão interativa Vega-Lite/Observable de pelo menos UMA figura por WP — abre dimensão HCI',
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
};

// Backward-compat: nas verticais com 1 artigo, o "principal" é o único.
// Nas com 2 (Equipamentos: WP#4+#6, UroPro: WP#3+#5), elege-se o WP de
// maior escopo/score como principal (WP#4 e WP#3 respectivamente).
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

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

const HOJE = '2026-04-26';

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
// EQUIPAMENTOS — DATASUS CNES + Working Paper #4 (Neuroimagem × Parkinson)
// Régua aplicada: LATO SENSU. WP#4 v2.1 (abr/2026): coautoria
// Alexandre Maciel Rolim (epidemiologia, revisão clínica, recomendações
// de protocolo) + Leonardo Chalhoub (engenharia de dados, 4 modalidades,
// 13 figuras vetoriais incluindo 2 MAPAS COROPLÉTICOS por UF, benchmark
// OCDE e cross-vertical PBF). O manuscrito clínico-epidemiológico que
// serviu de base é tratado como v0 deste artigo, não como obra citável
// separada. Sem cruzamento com SIH-AIH para uso efetivo, sem identificação
// causal, sem peer review formal — segue lato sensu, próximo do teto.
// ═══════════════════════════════════════════════════════════════════════
export const PARECER_EQUIPAMENTOS = {
  vertical: 'equipamentos',
  nivel: 'lato_sensu',
  scoreType: 'numeric',
  scoreNumeric: 8.8,
  scoreOriginal: null,
  originalLabel: null,
  originalUrl: null,
  ultimaAtualizacao: `${HOJE}T11:30 BRT`,
  versao: '2.1 — coautoria mantida + 2 mapas coropléticos + figs degeneradas removidas',
  resumoCalibragem:
    'Calibragem em LATO SENSU (TCC de especialização forte). Score 8,8 ' +
    '(vs 8,7 da v2.0): coautoria Rolim+Chalhoub mantida — o manuscrito ' +
    'clínico-epidemiológico de Rolim é a v0 deste artigo (base ' +
    'epidemiológica e revisão de literatura clínica), não uma obra ' +
    'separada citável; isso foi corrigido na v2.1 retirando a referência ' +
    '[31] que tratava o manuscrito como publicação independente. A v2.1 ' +
    'também adicionou DOIS mapas coropléticos por UF (RM/Mhab e densidade ' +
    'combinada do stack PD = RM+CT+PET+Gama) e removeu duas figuras ' +
    'degeneradas (composição RM por Tesla e CT por canais que tinham ' +
    'apenas uma barra cada, refletindo limitação do schema CNES e não ' +
    'conteúdo analítico). Hoje o WP#4 v2.1 traz 13 figuras vetoriais ' +
    'incluindo 2 mapas, comparação OCDE/EUA/Japão e cross-vertical PBF. ' +
    'PARA SUBIR a mestrado falta cruzamento CNES×SIH-AIH (oferta vs ' +
    'uso efetivo), identificação causal e peer review formal.',
  utilidadeSocial:
    'EXTREMAMENTE ÚTIL — utilidade clinicamente concreta. (a) Movement ' +
    'Disorders Society Brazil pode usar o panorama atualizado de RM/UF ' +
    'para argumentar com Ministério da Saúde; (b) gestores de ' +
    'Secretarias de Saúde regionais (especialmente AM, RR, PI, AC, AP, ' +
    'TO — abaixo da metade da mediana OCDE) têm mapas coropléticos ' +
    'auditáveis para advocacia; (c) neurologistas em centros de ' +
    'referência têm benchmark para demonstrar gap de capacidade ' +
    'diagnóstica para parkinsonismos atípicos; (d) jornalismo de saúde ' +
    'tem séries auditáveis e mapas reproduzíveis em vez de estatísticas ' +
    'estáticas dos releases DATASUS. O cruzamento com a carga estimada ' +
    'de DP por UF (1,25 milhão de casos projetados até 2060) é ' +
    'diretamente relevante para planejamento de oferta futura. Reduz ' +
    'custo marginal de pesquisa em saúde pública sobre um tema com ' +
    '535 mil pacientes hoje no Brasil.',
  pontosFortes: [
    'Working Paper #4 v2.1 publicado em ABNT com 13 figuras matplotlib vetoriais, incluindo DOIS mapas coropléticos por UF',
    'Mapa 1: RM/Mhab por UF — gradiente Norte/Sudeste visual e auditável vs mediana OCDE 2021 (≈17/Mhab)',
    'Mapa 2: densidade combinada do stack neuroimagem-PD (RM + CT + PET/CT + Gama Câmara) — síntese inédita',
    'Cobertura ampla: 4 modalidades CNES, todas as 27 UFs, 2013–2025 (13 anos)',
    'Pipeline robusto com cache idempotente em conversão DBC→Parquet e dicionário canônico de 133 (TIPEQUIP, CODEQUIP)→equipamento',
    'Per capita normalizado por população IBGE — comparações inter-UF válidas',
    'Multi-seleção client-side com re-agregação correta (totais somam, taxas recalculam)',
    'Split SUS/Privado preserva a dimensão pública vs privada — relevante a saúde coletiva',
    'Discussão de iniquidade estrutural (CV inter-UF estável apesar do crescimento agregado) é insight original e fundamentado',
    'Bibliografia clínica sólida: ELSI-Brazil, MDS-PD criteria, Schwarz et al. (swallow-tail), Postuma et al., GBD 2021',
    'Coautoria engenheiro+clínico (Rolim+Chalhoub): epidemiologia/revisão clínica integradas com camada de engenharia de dados em um único artigo',
    'Cross-vertical PBF: correlação ρ entre dependência de Bolsa Família (proxy de pobreza) e densidade de neuroimagem por UF — usa a plataforma multi-vertical do Mirante',
    'Versão v2.1 honrou crítica do revisor: removeu figuras degeneradas (uma única barra cada, refletindo schema CNES) e a citação imprópria do manuscrito de base como obra separada (era v0 deste artigo, não publicação independente)',
  ],
  problemasParaNotaPlena: [
    'Estimativa de carga PD por UF é simplificada (pop × 0,33% como proxy de prevalência ELSI-Brazil — ignora variação inter-UF na pirâmide etária)',
    'Análise OCDE descritiva — sem teste de significância sobre comparações internacionais',
    'Sem análise de produção SIH-AIH para mensurar uso EFETIVO dos equipamentos cadastrados (parque CADASTRADO ≠ OPERACIONAL)',
    'Subcategorias por intensidade de campo magnético (CODEQUIP=32-35) e canais de CT (CODEQUIP=26-30) ainda não são preenchidas pelos cadastradores — análise por Tesla requer fontes externas (ABRADIC)',
  ],
  problemasParaSubirNivel: [
    'Para mestrado: peer review (submeter a Cad Saúde Pública, RBSP ou Lancet Reg Health Am)',
    'Cruzar CNES (oferta) com SIH-AIH ou SIA-AIH (uso) para diferenciar parque CADASTRADO vs OPERACIONAL',
    'Validar empiricamente se a iniquidade per capita de RM correlaciona com atraso diagnóstico de PD por UF',
    'Identificação causal: explorar EC 86 (orçamento impositivo) ou PNAB (atenção primária) como descontinuidades para estimar efeito de financiamento sobre densidade de equipamentos',
  ],
  proximosPassos: [
    'Submeter WP #4 a Cad Saúde Pública ou Lancet Reg Health Am — peer review é o próximo nível',
    'Cruzar com SIH-AIH para análise de uso efetivo (procedimentos realizados em RM por UF)',
    'Complementar fonte oficial CNES com estimativas externas (ABRADIC) para resolver granularidade clínica por Tesla',
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
// UROPRO — Cirurgia uroginecológica no SUS (Working Papers #3 + #5)
// Régua aplicada: LATO SENSU. Tem como base a especialização de TATIELI
// (2022). WP #3 é cross-vertical (UroPro × PBF × Emendas, 2008-2025) e
// WP #5 é vertical-only longitudinal (UroPro 17 anos, eficiência+COVID
// +represa).
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
  versao: '2.0 — pipeline corrigido + WP #3 (cross-vertical) + WP #5 (vertical-only)',
  resumoCalibragem:
    'Avaliado como Lato sensu — tem como base a especialização em ' +
    'Enfermagem de Tatieli da Silva (2022, nota 9,7 régua MBA/lato sensu ' +
    '— aprovação com distinção). Sobe de 7,5 para 9,5 nesta reavaliação ' +
    'porque o vertical agora entrega TUDO o que o original entregou + ' +
    'extensões genuínas: (a) pipeline live com microdados 2008-2025 ' +
    '(vs TabNet 2015-2020 do original); (b) DOIS Working Papers em ABNT ' +
    '(WP #3 cross-vertical + WP #5 vertical-only); (c) descoberta e ' +
    'correção transparente do bug silver (filtro _ingest_ts == max ' +
    'derrubava 73% das linhas e 14 das 27 UFs — commit fa869cf documenta ' +
    'a correção); (d) cruzamento cross-vertical inédito com Bolsa ' +
    'Família e Emendas (correlação ρ ≈ -0,68 entre pobreza estrutural e ' +
    'acesso à cirurgia); (e) chart stacked-by-procedure na Evolução ' +
    'Nacional. 9,5 (não 9,7+) reconhece que figuras matplotlib ainda ' +
    'usam dados pré-correção e precisam ser regeneradas sobre o gold ' +
    'corrigido. Acima do original em escopo (cross-vertical, janela 17 ' +
    'anos, transparência metodológica) mas levemente abaixo em fechamento ' +
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
    'DOIS Working Papers em ABNT: WP #3 (cross-vertical: cirurgia × pobreza × emendas) + WP #5 (vertical: eficiência, COVID, represa cirúrgica)',
    'Transparência metodológica genuína: bug silver descoberto, diagnosticado, corrigido e DOCUMENTADO no próprio paper (commit fa869cf)',
    'Cross-vertical com Bolsa Família e Emendas: correlação ρ ≈ -0,68 entre pobreza estrutural e acesso à cirurgia, ρ ≈ -0,45 com emendas per capita',
    'Front-end com chart stacked-by-procedure (EvolutionStackedByKey) — discriminação visual abdominal vs vaginal na evolução nacional',
    'Janela de 17 anos (2008-2025) vs. 6 anos do original (2015-2020) — mais que duplica o escopo temporal',
    'Microdados SIH-AIH-RD com filtro SIGTAP no bronze convert: 150GB raw → MBs de Delta filtrado e auditável',
    'Reconhece e estende explicitamente Tatieli (2022, especialização em Enfermagem) como base upstream dos dois WPs UroPro',
    'Padrão "Bronze é STRING-ONLY" aplicado: tipagem só no silver, máxima auditabilidade',
  ],
  problemasParaNotaPlena: [
    'WP #3 e WP #5 ainda dependem da compilação CI completa para refletir as últimas edições nos PDFs servidos',
  ],
  problemasParaSubirNivel: [
    'Sem desfechos longitudinais: re-internação, mortalidade tardia, qualidade de vida — só volume, despesa, permanência, mortalidade intra-hospitalar',
    'Cross-vertical é correlacional, não causal — exigiria identificação (DiD, IV) para subir para mestrado',
    'Sem cruzamento com CNES (Equipamentos médicos) — densidade hospitalar especializada por UF poderia mediar a correlação',
    'Sem estratificação por sexo/idade/raça da paciente — gold colapsa antes desses cortes',
  ],
  proximosPassos: [
    'Garantir compilação CI completa de WP #3 e WP #5 (validar deploy-pages.yml após renumeração)',
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
  // GitHub `blob/...` URL renderiza o PDF inline no navegador.
  // `raw/...` força download via Content-Disposition, que não é o desejado aqui.
  originalUrl: 'https://github.com/leonardochalhoub/CodingMBA_UFRJ/blob/main/Monografia_LeonardoChalhoub.pdf',
  ultimaAtualizacao: `${HOJE}T18:45 BRT`,
  versao: '0.4 — pipeline scaffold + contexto histórico (banca reprovou; sem nota atribuída)',
  resumoCalibragem:
    'CONTEXTO HISTÓRICO: o autor foi REPROVADO pela banca da UFRJ ' +
    '(MBA Engenharia de Dados, set/2023). A banca não atribuiu nota ' +
    'numérica — apenas o veredicto de reprovação. Dois números aparecem ' +
    'em telas como "scores", e ambos são posteriores e externos à banca: ' +
    '(a) o "Score original" 8,0 é a reavaliação da monografia hoje pela ' +
    'IA do próprio Mirante (Claude Opus, modo professor de programa de ' +
    'mestrado/doutorado, régua lato sensu); (b) o "Score" 6,8 é a ' +
    'avaliação da IA sobre o vertical RAIS desta plataforma — não da ' +
    'monografia original, e não da banca. — Detalhe relevante: a ' +
    'monografia defendia Delta Lake como núcleo do argumento, conteúdo ' +
    'que em 2023 era considerado vanguardista e hoje (2026) virou ' +
    'consenso técnico em engenharia de dados. O vertical RAIS Mirante ' +
    'herda essa base, ganha pontos por infraestrutura aberta e ' +
    'reprodutível, mas ainda não entregou nenhuma extensão substantiva ' +
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
// Conceito atual (pós WP#4 v2.1 — autoria única + 2 mapas coropléticos):
// B+ (entre A e B). Para virar A pleno: peer review (1+ submissão a
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
  ultimaAtualizacao: `${HOJE}T11:45 BRT`,
  versao: '3.1 — WP#4 v2.1 (coautoria mantida, manuscrito tratado como v0, 2 mapas coropléticos)',
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
    'consolidados em tempo real. O projeto soma CINCO Working Papers em ' +
    'ABNT escritos: WP #1 (Emendas), WP #2 (Bolsa Família), WP #3 ' +
    '(cross-vertical UroPro × PBF × Emendas), WP #4 (Neuroimagem × ' +
    'Parkinson, coautoria Rolim+Chalhoub) e WP #5 (UroPro 17 anos). ' +
    'Atualização v3.1 (abr/2026): o WP#4 foi revisado para v2.1 — a ' +
    'coautoria com Alexandre Maciel Rolim foi mantida (epidemiologia, ' +
    'revisão clínica e recomendações de protocolo) e o manuscrito ' +
    'clínico-epidemiológico passou a ser tratado como a v0 deste artigo ' +
    '(deixou de ser citado como obra independente, o que era impreciso ' +
    'porque o manuscrito é o próprio draft inicial deste WP); foram ' +
    'adicionados DOIS mapas coropléticos por UF (RM/Mhab e densidade ' +
    'combinada do stack neuroimagem-PD) e removidas duas figuras ' +
    'degeneradas que refletiam apenas limitação do schema CNES. TRÊS ' +
    'modelos de contribuição metodológica genuína permanecem ' +
    'consolidados: (a) "engenharia + clínica em coautoria" (WP #4 com ' +
    'Rolim, integrando saber clínico-epidemiológico com infraestrutura ' +
    'de dados); (b) "análise cross-vertical sobre arquitetura ' +
    'unificada" (WP #3 cruza três verticais — UroPro, PBF, Emendas — ' +
    'possível APENAS porque os pipelines passam pela mesma arquitetura ' +
    'medalhão); (c) "auditabilidade pública do dado processado" ' +
    '(descoberta e correção transparente do bug silver na vertical ' +
    'UroPro, commit fa869cf abr/2026 — filtro _ingest_ts == max ' +
    'derrubava 73% das linhas e 14 das 27 UFs, documentado em primeira ' +
    'pessoa nos próprios papers). Conceito permanece B+ na régua ' +
    'mestrado: cinco WPs escritos, plataforma sólida, mas o teto A ' +
    'continua condicionado a peer review formal (submissão a periódico ' +
    'indexado) e identificação causal explícita.',
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
    'CINCO Working Papers em ABNT escritos: Emendas WP#1, Bolsa Família ' +
      'WP#2, Acesso desigual cross-vertical UroPro × PBF × Emendas WP#3, ' +
      'Neuroimagem × Parkinson WP#4 v2.1 (coautoria Rolim+Chalhoub, com ' +
      '2 mapas coropléticos por UF) e UroPro 17 anos WP#5. Compilação em ' +
      'CI via xu-cheng/latex-action sobre cada .tex em padrão ABNT. ' +
      'Padrão acadêmico real, não rascunho.',
    'Modelo de coautoria engenheiro-clínico demonstrado no WP#4 v2.1: ' +
      'Alexandre Maciel Rolim (epidemiologia, revisão clínica, ' +
      'recomendações de protocolo) + Leonardo Chalhoub (engenharia de ' +
      'dados, análise reproduzível, mapas e cross-vertical). O ' +
      'manuscrito clínico-epidemiológico de Rolim é a v0 deste artigo ' +
      '(integrado, não citado como obra separada). Modelo replicável a ' +
      'outras agendas de saúde pública.',
    'WP#4 v2.1 atualizado em abril/2026: dois MAPAS COROPLÉTICOS por UF ' +
      '(RM/Mhab e densidade combinada do stack neuroimagem-PD = RM + CT + ' +
      'PET/CT + Gama Câmara) tornam o gradiente Norte/Sudeste de ' +
      'capacidade diagnóstica visual e auditável. Mapas são essenciais ' +
      'em saúde coletiva — versão anterior tinha gráficos descritivos ' +
      'mas faltava cartografia, lacuna agora resolvida.',
    'Modelo de análise cross-vertical demonstrado no WP#3 (Acesso ' +
      'desigual): cruzamento de TRÊS verticais (UroPro × PBF × Emendas) ' +
      'sobre a mesma arquitetura medalhão, com correlações ρ ≈ -0,68 ' +
      '(pobreza × acesso) e ρ ≈ -0,45 (emendas × acesso). Esse tipo de ' +
      'integração é IMPOSSÍVEL em arquiteturas de dados fragmentadas — ' +
      'é, em si, justificativa para a plataforma unificada.',
    'Auditabilidade pública demonstrada (abr/2026): bug silver descoberto ' +
      'por inspeção visual da plataforma, diagnosticado por SQL direto ao ' +
      'Delta, corrigido em commit fa869cf, regenerado e documentado em ' +
      'primeira pessoa nos WPs #3 e #5. Defeito ocultava 73% das linhas ' +
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
    'Submeter Working Paper #1 (Emendas) ou WP #4 (Neuroimagem × Parkinson, v2.1, coautoria Rolim+Chalhoub) a RAP / RBE / Cad Saúde Pública (ciclo de revisão ' +
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


// Atas do Conselho do Mirante — peer review interno simulando banca
// fictícia com 4 cadeiras: Finanças, Eng. Software, Design (HCI),
// Administração. Cada ata é uma reunião sobre UM artigo (Working Paper).
//
// Schema da ata:
//   meta:                identificação (reunião, artigo, commit, data, status)
//   pareceres_iniciais:  array de pareceres por cadeira (Rodada 1)
//   whys_propostos:      array de WHYs propostos por cadeira (Rodada 2A) — opcional
//   why_consolidado:     decisão final do autor sobre o WHY (Rodada 2B)
//   reavaliacao_administrador: parecer da Rodada 3 do conselheiro de Administração
//
// Renderização: app/src/components/AtaConselho.jsx consome este arquivo.

// ═══════════════════════════════════════════════════════════════════════
// REUNIÃO #1 — WP#4 v2.1 (Neuroimagem × Parkinson, Rolim + Chalhoub)
// Data: 2026-04-26 · 3 rodadas concluídas · APROVADO COM AJUSTES
// ═══════════════════════════════════════════════════════════════════════
export const ATA_WP4_REUNIAO_1 = {
  meta: {
    reuniao: 1,
    artigo: 'WP#4 v3.0 — Iniquidade diagnóstica em neuroimagem para Parkinson no Brasil',
    artigo_titulo_completo:
      'Iniquidade diagnóstica em neuroimagem para Doença de Parkinson no Brasil: ' +
      'análise multidimensional do parque instalado, do federalismo fiscal e do ' +
      'envelhecimento populacional (2013–2025)',
    commit: '822d7a8',
    data: '2026-04-26',
    coautoria: 'Alexandre Maciel Rolim (clínico-epidemiológico) + Leonardo Chalhoub (engenharia de dados)',
    rodadas: 3,
    status: 'APROVADO COM AJUSTES',
    media_quants: 2.5, // (B 2,0 + B+ 2,5 + A 3,0) / 3
    limiar_aprovacao: 2.0,
  },

  pareceres_iniciais: [
    {
      cadeira: 'financas',
      titulo: 'Conselheiro de Finanças & Métodos Quantitativos',
      lente: 'Identificação causal · RDD/IV/DiD/event-study',
      score: { tipo: 'letra', letra: 'B', pontos: 2.0 },
      veredicto: 'major-but-tractable revision',
      epigrafe:
        '"A v2.1 atravessou o limiar metodológico crítico — agora tem identificação causal explícita ' +
        'e um null result honesto. De C para B é meio salto duplo, e isso é raro."',
      argumento_central:
        'A Seção 7 (DiD 2×2 + TWFE clusterizado sobre EC 86/2015) é o que fez o trabalho subir de C → B na v2.1. ' +
        'Tratamento = quartil superior de pago_RP6/Mhab médio 2016-2018; pré 2013-14, pós 2019-25. ' +
        'Resultado null/marginal nos dois modelos (DiD: β=-13,29, p=0,075; TWFE: β=-1,98, p=0,114). ' +
        'Sinais consistentes, magnitudes plausíveis, escrita honesta do null.',
      pendencias: [
        'Parallel trends não testado formalmente (sem placebo, sem event-study com leads/lags)',
        'Wild-cluster bootstrap ausente — com 27 UFs e 12 tratadas, HC3 pode ser otimista',
        'Cross-vertical PBF ainda correlacional; linguagem causal incompatível com desenho',
        'Apenas 1 choque institucional usado; EC 100/2019 e MP 1.061 disponíveis para replicação',
        'OCDE descritivo sem IC bootstrap; estimativa de carga PD por UF é simplificada (pop × 0,33%)',
      ],
      sugestao_para_subir_pra_a:
        'Event-study com leads/lags ±5 anos sobre EC 86 + replicação cross-shock em EC 100 + DiD sobre MP 1.061 ' +
        'para a relação PBF-densidade.',
    },
    {
      cadeira: 'eng-software',
      titulo: 'Conselheiro de Eng. de Software & Plataforma de Dados',
      lente: 'Arquitetura distribuída · reprodutibilidade · platform-as-product',
      score: { tipo: 'letra', letra: 'B+', pontos: 2.5 },
      veredicto: 'minor revision',
      epigrafe:
        '"ARCHITECTURE.md publicado e suite pytest sobre o gold são exatamente o que pedi na rodada anterior. ' +
        'Reprodutibilidade documentada ainda é diferente de reprodutibilidade verificada — falta o último passo."',
      argumento_central:
        'A v2.1 endereçou DUAS das quatro críticas estruturais da v2.0: docs/ARCHITECTURE.md (506 linhas, ' +
        '11 ADRs Nygard cobrindo Delta vs Iceberg, Auto Loader vs batch, bronze STRING-ONLY, dedup, CI/CD, ' +
        'Free Edition) e tests/test_equipamentos_gold.py (13 testes pytest puros, 0,19s, validam row count, ' +
        '27 UFs, schema, composite key, RM 2024 ∈ [3000-4500], densidade ≈ mediana OCDE).',
      pendencias: [
        'verify-reproducibility.yml ausente do CI — deploy-pages.yml não invoca pytest',
        'Data versioning ainda Git-only — sem DVC/lakeFS, sem manifest assinado por WP',
        'Tests só sobre gold output, não sobre código de transformação (faltam mocks de DataFrame Spark)',
        'Sem smoke test do build LaTeX em CI clean (apesar do xu-cheng/latex-action rodar)',
      ],
      sugestao_para_subir_pra_a:
        'GitHub Action verify-reproducibility.yml com pytest-snapshot sobre sample bronze + ' +
        'Zenodo deposit do dicionário canônico (cnes_eq_canonical.csv) com DOI próprio.',
    },
    {
      cadeira: 'design',
      titulo: 'Conselheira de Design Web & Visualização (HCI)',
      lente: 'Tufte · Norman · Bostock — integridade visual + UX + viz interativa',
      score: { tipo: 'letra', letra: 'A', pontos: 3.0 },
      veredicto: 'próximo do teto',
      epigrafe:
        '"Os dois mapas coropléticos resolvem a única lacuna estrutural que a v2.0 tinha. Cividis_r, ' +
        'contraste adaptativo branco/preto em norm > 0,55, design-system documentado em 303 linhas. ' +
        'Para o WP isolado, isso é A."',
      argumento_central:
        'A crítica explícita da v2.0 — "choropleth do Brasil ausente, substituído por bar chart regional, ' +
        'que é inferior visualmente" — foi endereçada DIRETAMENTE: Fig. 5 (Densidade de RM/Mhab por UF, ' +
        'cividis_r invertido, contraste adaptativo, barra de cor com referência clínica OCDE 2021), ' +
        'Fig. 6 (Densidade combinada do stack neuroimagem-PD = RM+CT+PET/CT+Gama). docs/design-system.md ' +
        '(303 linhas) documentando paleta, tipografia, tokens CSS, daltonismo. Limpeza honesta de figs ' +
        'degeneradas (RM por Tesla, CT por canais — uma única barra cada).',
      pendencias: [
        'Visualizações são estáticas (matplotlib) — falta Vega-Lite/Observable interativo',
        'Plataforma sem audit Lighthouse formal ou conformidade WCAG declarada',
        'Sem testes formais de UX (zero usabilidade testing, A/B, ou survey de leitores)',
      ],
      observacao:
        'Lacunas remanescentes são da PLATAFORMA como produto, não do WP isolado em PDF. Não puxam a nota do artigo.',
    },
    {
      cadeira: 'administrador',
      titulo: 'Conselheiro de Administração & Aplicação Prática',
      lente: 'Sinek (WHY) · Harari (escala histórica) · Carrey (ousadia)',
      score: { tipo: 'qualitativo' },
      veredicto: 'Adiar 60-90d, editar em Sinek-mode antes de submeter',
      epigrafe:
        '"O paper sabe O QUE tem (3.900 RM, mediana OCDE alinhada, paradoxo PE/PB/RN). Mas o leitor termina ' +
        'sem saber POR QUE isso importa. WHY-HOW-WHAT está invertido."',
      argumento_central:
        'WHY invertido. Leitor sai sabendo o WHAT, não o WHY. Audiência hoje difusa — paper navega entre ' +
        'neurologistas, gestores, jornalistas, pesquisadores e nenhuma é dominante. Sem "que decisão muda?" ' +
        'explícito.',
      perguntas_criticas: [
        'WHY em uma frase? O autor consegue escrever, em UMA frase, por que o paper existe?',
        'Leitor-alvo único? Hoje navega entre 4 audiências e nenhuma é dominante.',
        'Que decisão muda? Onde está o call-to-action para CONITEC, MS, ou parecer técnico em ADPF?',
      ],
    },
  ],

  whys_propostos_rodada_2A: [
    {
      cadeira: 'financas',
      frase:
        'Existimos porque o Brasil produz, involuntariamente, os melhores experimentos naturais do mundo — ' +
        'e ninguém estava transformando essas descontinuidades institucionais em conhecimento causal replicável.',
      foco: 'Identificação causal sobre cutoffs constitucionais brasileiros',
    },
    {
      cadeira: 'eng-software',
      frase:
        'Provar que ciência de dados públicos brasileiros pode ser reprodutível, auditável e versionada do raw ' +
        'até a conclusão — tornando pesquisa aplicada indistinguível de engenharia de produção.',
      foco: 'Platform-as-research-artifact, reprodutibilidade radical',
    },
    {
      cadeira: 'design',
      frase:
        'Dados públicos brasileiros escondem padrão geoespacial e temporal em tabelas estáticas; o Mirante ' +
        'existe para tornar esses padrões visíveis, honestos e verificáveis — como pré-condição da deliberação democrática.',
      foco: 'Integridade visual como contrato democrático',
    },
    {
      cadeira: 'administrador',
      frase:
        'Acreditamos que todo brasileiro merece tomar decisões sobre sua saúde, sua cidade e seu país com os ' +
        'mesmos dados que os tecnocratas usam pra decidir por ele.',
      foco: 'Redistribuição epistêmica · IPEA-Data privado em stack zero-cost',
    },
  ],

  // Os 4 WHYs acima eram da PLATAFORMA-Mirante. O autor corrigiu o escopo e
  // decidiu que o WHY do ARTIGO WP#4 é QUÁDRUPLO, com 4 ângulos simultâneos
  // sobre o mesmo dataset, cada um com audiência e CTA próprios.
  why_consolidado: {
    tipo: 'quadruplo',
    decidido_pelo_autor: true,
    data_decisao: '2026-04-26',
    nota:
      'Sinek prega UM WHY para marcas (identidade singular). Artigo científico tem audiências múltiplas e ' +
      'vida útil de citação, não fidelidade de cliente — segmentação bem-feita fortalece, não dilui.',
    quadruplo: [
      {
        lente: 'Clínico',
        cor: '#dc2626',
        frase:
          'Existimos para mostrar que parkinsonismos atípicos no Brasil estão sub-diagnosticados por gap de ' +
          'capacidade de neuroimagem regional e mensurável.',
        audiencia: 'Movement Disorders Society Brazil, neurologistas em centros de referência, residentes em Neurologia',
        cta: 'Reabilitar swallow-tail/RM 3T como protocolo regionalmente acessível',
        how_no_paper:
          'Bibliografia clínica sólida (Schwarz et al. swallow-tail, Postuma et al., MDS-PD criteria, ELSI-Brazil) + ' +
          'decomposição por modalidade (RM, CT, PET, Gama Câmara)',
      },
      {
        lente: 'Político',
        cor: '#1d4ed8',
        frase:
          'Existimos para nomear que o gradiente Norte/Sudeste de RM não é geografia — é resultado de escolhas ' +
          'orçamentárias rastreáveis (EC 86).',
        audiencia: 'Comissões de Saúde do Senado/Câmara, CONITEC, Coordenação de Atenção Especializada do MS',
        cta: 'Auditar a alocação de RP6 sob lente de equidade diagnóstica',
        how_no_paper:
          'Seção 7 — DiD 2×2 + TWFE clusterizado sobre EC 86/2015 com null/marginal honesto ' +
          '(β=-13,29, p=0,075; β=-1,98, p=0,114)',
      },
      {
        lente: 'Demográfico',
        cor: '#b45309',
        frase:
          'Existimos para alertar que o envelhecimento populacional brasileiro vai colidir com a iniquidade ' +
          'espacial de neuroimagem nas próximas duas décadas.',
        audiencia: 'Planejadores de longo prazo (IPEA, IBGE projeções), Secretarias Estaduais com pirâmide etária invertendo',
        cta: 'Antecipar capacidade instalada antes do choque demográfico',
        how_no_paper:
          'Cobertura temporal 2013-2025 (13 anos) + projeção ELSI-Brazil 1,25mi até 2060 + benchmark OCDE 2021',
      },
      {
        lente: 'Epidemiológico',
        cor: '#059669',
        frase:
          'Existimos para transformar a projeção de 1,25mi de casos de DP até 2060 (ELSI) em mapa auditável ' +
          'de oferta-demanda por UF.',
        audiencia: 'Saúde Coletiva acadêmica, jornalismo de saúde de dados, ONGs de pacientes',
        cta: 'Trocar estatística agregada por evidência espacial-temporal navegável',
        how_no_paper:
          '2 mapas coropléticos por UF (RM/Mhab e densidade combinada do stack PD = RM+CT+PET+Gama) + ' +
          'cruzamento PBF cross-vertical',
      },
    ],
    tese_central:
      'O Brasil tem hoje 535 mil pacientes com Doença de Parkinson e projeção de 1,25 milhão até 2060. A ' +
      'capacidade diagnóstica disponível para esses pacientes é radicalmente desigual entre UFs — e essa ' +
      'desigualdade é simultaneamente: clinicamente nociva (sub-diagnóstico de parkinsonismos atípicos), ' +
      'politicamente rastreável (resultado de escolhas orçamentárias federais com cutoff em 2015), ' +
      'demograficamente urgente (vai piorar com o envelhecimento) e epidemiologicamente projetável (oferta ' +
      'vs demanda mapeável por UF). Este artigo é o primeiro a expor as 4 dimensões sobre o mesmo dataset ' +
      'auditável.',
  },

  rodada_4_doutorado: {
    titulo: 'Re-avaliação completa do Conselho — direcionamentos para nível de doutorado',
    contexto:
      'Com o WHY quádruplo formalizado, os 4 conselheiros re-avaliaram em paralelo o WP#4 v2.1 sob a lente ' +
      '"como levar este artigo a defesa de doutorado". Cada conselheiro emitiu (a) re-score, (b) diagnóstico ' +
      'do gap mestrado→doutorado na sua lente, (c) roadmap de 5-8 ações concretas, (d) armadilha que o autor ' +
      'pode estar subestimando.',
    pareceres: [
      {
        cadeira: 'financas',
        score_revisado: { tipo: 'letra', letra: 'B', pontos: 2.0, mudou: false },
        re_score_justificativa:
          'WHY quádruplo é ganho de POSICIONAMENTO, não de identificação. Organiza audiências, afina CTAs e ' +
          'torna a contribuição mais legível para revisores de Saúde Coletiva. Mas não move um iota o DiD ' +
          'null/marginal, não adiciona parallel trends, não fecha bootstrap, não transforma correlação PBF ' +
          'em causal. Framing não é dado novo.',
        gap_doutorado:
          'Saúde Coletiva top-tier (Cad SP, IJHP) e Economia Aplicada (JHE, JDE) exigem claim causal ' +
          'defensável OU desenho metodológico original e auditável. O WP#4 entrega análise descritiva séria ' +
          'com quasi-experimento embrionário — DiD sobre EC 86 é a porta certa, mas só entreaberta. Faltam: ' +
          '(a) parallel trends formal com event-study estendido + leads; (b) replicação cross-shock; ' +
          '(c) magnitude economicamente/clinicamente interpretável com IC bootstrap; (d) separação ' +
          'cadastrado vs operacional. Gap é grande mas não intransponível: 4-6 meses de trabalho pesado.',
        roadmap: [
          {
            n: 1,
            titulo: 'Event-study TWFE com leads/lags t-5 a t+6 sobre EC 86/2015',
            tecnica: 'did2s ou Callaway-Sant\'Anna (heterogeneidade); teste Roth (2022); placebo em UFs sem alteração de teto',
            dado: 'CNES público + SIOPS, painel UF×ano 2010-2023',
            why: 'Político',
            tempo: '4 semanas',
          },
          {
            n: 2,
            titulo: 'Cross-shock replication: EC 100/2019 (RP7 bancada) + MP 1.061/2021',
            tecnica: 'Mesmo DiD, 3 choques separados; convergência de direção+magnitude robustece identificação',
            dado: 'CNES + SIOPS + Portal Transparência (RP7)',
            why: 'Político + Demográfico',
            tempo: '6 semanas',
          },
          {
            n: 3,
            titulo: 'Wild-cluster bootstrap sobre TWFE (27 clusters UF)',
            tecnica: 'boottest (Stata) ou wildboottest (R/Python); comparar com HC3',
            dado: 'mesmo painel UF×ano',
            why: 'Transversal — robustez de inferência',
            tempo: '2 semanas (paralelo ao item 1)',
          },
          {
            n: 4,
            titulo: 'Cruzamento CNES (cadastro) × SIH-AIH (procedimentos RM efetivamente realizados)',
            tecnica: 'Construir taxa de utilização real (exames/equip/ano); equipamento cadastrado mas zerado em AIH é ruído no denominador',
            dado: 'DATASUS SIH-AIH-RD',
            why: 'Clínico — ponto mais fraco hoje',
            tempo: '8 semanas',
          },
          {
            n: 5,
            titulo: 'Refinamento de carga DP por UF: pirâmide etária PNADC × prevalência ELSI',
            tecnica: 'Curva etária ELSI sobre pirâmide PNADC UF-a-UF; projeção 2025-2060 com IC explícitos',
            dado: 'PNADC + ELSI-Brazil',
            why: 'Epidemiológico + Demográfico',
            tempo: '3 semanas',
          },
          {
            n: 6,
            titulo: 'Análise de equidade formal: índices de Kakwani + necessidade',
            tecnica: 'Kakwani (capacidade RM/cap vs IDH estadual) + índice de necessidade (carga DP projetada vs oferta atual)',
            dado: 'gold + IBGE',
            why: 'Clínico + Político — linguagem quantitativa que Saúde Coletiva reconhece',
            tempo: '3 semanas',
          },
          {
            n: 7,
            titulo: 'Conexão PBF: especificação IV (instrumento exógeno)',
            tecnica: 'Variação exógena no benefício médio estadual como instrumento p/ renda domiciliar; se IV não sustentar, declarar limitação',
            dado: 'CGU + IBGE + CNES',
            why: 'Demográfico + Epidemiológico',
            tempo: '4 semanas (condicional a instrumento válido)',
          },
        ],
        defendivel_em: 'PPG Saúde Coletiva (Fiocruz, USP-FSP), PPG Economia Aplicada (UFPE, FGV-EPGE), PPG Epidemiologia (USP, UFMG)',
        contribuicao_doutoral:
          'Primeiro estudo causal-quasi-experimental sobre determinantes orçamentários da capacidade de neuroimagem no Brasil, ' +
          'com projeção de demanda auditável UF-a-UF',
        armadilha:
          'EC 86/2015 pode não ser exógena para todas UFs simultaneamente — Estados que lobbied para a emenda têm ' +
          'probabilidade de tratamento correlacionada com pré-tendência (violação de SUTVA). Sem modelar heterogeneidade ' +
          'de adoção (staggered DiD com Callaway-Sant\'Anna ou Sun-Abraham), o TWFE pooled produz coeficientes ponderados ' +
          'por variância negativa em alguns grupos — o null que aparece hoje pode ser ARTEFATO do estimador, não sinal verdadeiro.',
      },
      {
        cadeira: 'eng-software',
        score_revisado: { tipo: 'letra', letra: 'B+', pontos: 2.5, mudou: false },
        re_score_justificativa:
          'WHY quádruplo é narrativa, não entrega de engenharia. Dá coesão ao argumento "platform-as-research-artifact" ' +
          '— agora o leitor entende por que o pipeline precisa ser auditável por 4 comunidades distintas, o que ' +
          'fortalece a motivação do ARCHITECTURE.md. Mas verify-reproducibility.yml ainda não existe, deploy-pages.yml ' +
          'não invoca pytest, sem DVC nem manifest assinado. Score sobe quando o CI bloqueia.',
        gap_doutorado:
          'Doutorado em Eng. Software/Eng. Dados exige contribuição METODOLÓGICA original — não "pipeline que funciona" ' +
          'nem "plataforma bem documentada". WP#4 hoje é caso de uso convincente de medallion aplicado à saúde — ' +
          'dissertação de mestrado FORTE. Para doutorado falta: (a) benchmark empírico controlado Delta vs Iceberg vs ' +
          'Hudi (CIDR/VLDB-tier); (b) WHY quádruplo fragmenta audiência sem unificar metodologia — o que conecta os 4 ' +
          'ângulos é a plataforma, não o conteúdo clínico; (c) UM WP não é tese, é capítulo 1 — a plataforma com 6+ ' +
          'verticais replicáveis É a tese transversal.',
        roadmap: [
          {
            n: 1,
            titulo: 'verify-reproducibility.yml no CI',
            tecnica: 'GitHub Action: pytest-snapshot sobre sample bronze 10MB DBC; pipeline em Ubuntu limpo; compara MD5 do gold contra snapshot esperado; deploy-pages só se passar',
            dado: 'sample CNES 2024',
            why: 'Transversal — fecha lacuna de reprod. dos 4 ângulos',
            tempo: '1 semana',
          },
          {
            n: 2,
            titulo: 'Tests sobre código de transformação silver/gold',
            tecnica: 'pyspark local ou chispa; mock DataFrame; cobre composite key, dedup por source_file, normalização TIPEQUIP',
            dado: 'fixtures sintéticas',
            why: 'Clínico — valida que dedup não oculta equipamentos em UFs com sub-notificação',
            tempo: '3 semanas',
          },
          {
            n: 3,
            titulo: 'Zenodo deposit do cnes_eq_canonical.csv com DOI',
            tecnica: 'parsing HTML direto de cnes2.datasus.gov.br; metadados FAIR; DOI persistente',
            dado: 'dicionário canônico CNES',
            why: 'Epidemiológico — denominador rastreável por epidemiologistas sem Databricks',
            tempo: '3 dias',
          },
          {
            n: 4,
            titulo: 'Benchmark empírico: Delta Lake vs Apache Iceberg vs Apache Hudi',
            tecnica: 'mesmo dataset CNES; métricas: latência escrita, custo storage, merge/upsert, ACID sob concurrent write; cluster Free Edition autoscaling',
            dado: 'CNES bronze→gold completo',
            why: 'Político — autoridade regulatória (CONITEC) não adota pipeline sem comparação independente',
            tempo: '8 semanas',
            destino: 'CIDR 2027 ou VLDB 2027',
          },
          {
            n: 5,
            titulo: 'Cookiecutter mirante-lakehouse-template',
            tecnica: 'extrair padrão bronze-STRING-ONLY/silver/gold/Unity Catalog em template parametrizado; publicar GitHub',
            dado: 'estrutura existente do Mirante',
            why: 'Demográfico + plataforma — IPEA, IBGE, SES precisam de template replicável',
            tempo: '6 semanas',
          },
          {
            n: 6,
            titulo: 'Teste de external validity: replicar para Alzheimer (CNES + SIH)',
            tecnica: 'mesma arquitetura medallion sobre 2º registro de doença neurodegenerativa; documentar onde generaliza',
            dado: 'CNES + SIH-AIH (filtros Alzheimer)',
            why: 'Epidemiológico — Alzheimer colide com mesma infra diagnóstica',
            tempo: '10 semanas',
          },
          {
            n: 7,
            titulo: 'ADR sobre Databricks Free Edition limites',
            tecnica: 'documentar DBUs gratuitas/mês, sem SLA, sem Delta Sharing; estratégia de escape para GCP/Azure',
            dado: 'documentação técnica',
            why: 'Político — banca PPG vai perguntar sustentabilidade computacional',
            tempo: '2 dias',
          },
        ],
        defendivel_em: 'Eng. Dados aplicada à Saúde stricto sensu BR (UFRJ PPGI, USP ICMC, UFMG DCC) ou paper de sistema CIDR/VLDB 2027',
        armadilha:
          'verify-reproducibility.yml vai falhar silenciosamente na Free Edition — pipeline completo não roda em GitHub ' +
          'Actions, roda em cluster Databricks. O CI pode testar Python puro (transformações mockadas) e validade do gold ' +
          'JSON commitado, NÃO o pipeline DBC→bronze→silver→gold ponta a ponta. A "reprodutibilidade" certificada é PARCIAL: ' +
          'valida output, não caminho. Para doutorado, distinção precisa ser EXPLÍCITA no ARCHITECTURE.md como limitação ' +
          'formal, senão revisor de VLDB aponta primeiro.',
      },
      {
        cadeira: 'design',
        score_revisado: { tipo: 'letra', letra: 'A', pontos: 3.0, mudou: false, ressignificado: true },
        re_score_justificativa:
          'A mantido, mas a régua mudou: A aqui é PISO de entrada num programa doutoral, não prêmio final. Em IEEE TVCG ' +
          'ou CHI, o que temos hoje (2 coropléticos cividis_r, contraste adaptativo, design-system 303L) é material de um ' +
          '1º relatório de qualificação BEM FEITO. Não é artigo publicável. WHY quádruplo é o ÚNICO elemento que abre a ' +
          'janela: 4 audiências sobre o mesmo dataset é premissa de contribuição original em InfoVis centrada em audiência ' +
          '— se e somente se medida empiricamente.',
        gap_doutorado:
          'Mapa coroplético é técnica consolidada desde MacEachren (1995). Aplicá-la bem não é contribuição, é EXECUÇÃO. ' +
          'O potencialmente novo é o problema de design: como uma mesma massa de dado deve ser encodada DIFERENTEMENTE ' +
          'para neurologista vs gestor vs epidemiologista vs jornalista, e como essa escolha afeta compreensão, retenção ' +
          'e ação. Audience-specific viz tem literatura (Hullman & Diakopoulos 2011; Boy et al. 2015). WP#4 escolheu ' +
          'encoding ÚNICO para 4 audiências. Sem estudo formal medindo, não há claim doutoral sustentável.',
        roadmap: [
          {
            n: 1,
            titulo: 'Protocolo think-aloud por audiência (12 participantes em 4 grupos)',
            tecnica: '3 neurologistas + 3 gestores + 3 epidemiologistas + 3 jornalistas; semi-estruturado 45min sobre 2 mapas + tese central; gravação + eye-tracking baixo custo (Tobii Spark/webcam); análise temática Atlas.ti',
            dado: 'dado primário coletado',
            why: 'Todos os 4 — mede qual encoding falha por audiência',
            tempo: '10 semanas',
            destino: 'IEEE TVCG ou CHI',
          },
          {
            n: 2,
            titulo: 'Versão Vega-Lite/Observable interativa do choropleth combinado',
            tecnica: 'filtros por modalidade (TC/RM/PET); slider temporal 2013-2025; tooltip com dado bruto auditável + link p/ notebook',
            dado: 'gold existente',
            why: 'Epidemiológico + abre "plataforma como evidência primária"',
            tempo: '4 semanas',
          },
          {
            n: 3,
            titulo: 'Audit Lighthouse + Axe + WAVE no CI; corrigir todas falhas WCAG 2.2 AA',
            tecnica: 'workflow CI; score público no README; pré-requisito para qualquer claim de design-for-policy',
            dado: 'plataforma',
            why: 'Transversal — design-for-policy indefensável sem isso',
            tempo: '3 semanas',
          },
          {
            n: 4,
            titulo: 'Versão print-grade para policy brief CONITEC (8 páginas)',
            tecnica: 'B&W compatível; tabular-nums; hierarquia para leigos; documentar decisões no design-system.md',
            dado: 'PDF print',
            why: 'Político',
            tempo: '2 semanas',
          },
          {
            n: 5,
            titulo: 'Mirante VizKit — framework reusável (pacote npm)',
            tecnica: '5 templates Vega-Lite parametrizáveis (choropleth, evolution stack, ranking, small multiples, sparkline); paleta cividis hardcoded; contraste adaptativo built-in; zero CDN externo',
            dado: 'biblioteca',
            why: 'Todos — vira paper IEEE VIS ou Observable@Observable',
            tempo: '6 semanas',
          },
          {
            n: 6,
            titulo: 'Comparação de encodings alternativos por audiência',
            tecnica: 'cartograma de área (déficit diagnóstico) vs choropleth para neurologista; treemap (dotação) vs ranking bar para gestor; medir tempo-para-decisão',
            dado: 'incluso no item 1',
            why: 'Clínico + Político',
            tempo: 'incluso nas 10s do item 1',
          },
          {
            n: 7,
            titulo: 'Submissão do protocolo ao CEP',
            tecnica: 'aprovação ética antes de qualquer coleta com profissionais de saúde; sem isso, dados não são publicáveis em CHI',
            dado: 'protocolo',
            why: 'Pré-requisito',
            tempo: '6-8 semanas em paralelo (iniciar PRIMEIRO)',
          },
        ],
        defendivel_em: 'PESC/UFRJ, PPGI/UNIRIO, IME-USP; submissão em IEEE VIS Applications track ou CHI Papers track com coautoria do orientador',
        armadilha:
          'A FALSA-NEUTRALIDADE do cividis. Cividis é perceptualmente uniforme e acessível para deuteranopia — correto. ' +
          'Mas "neutro" em relação a quê? Para o neurologista, gradiente Norte/Sudeste em cividis comunica ausência ' +
          'gradual. Para o gestor político, o MESMO gradiente pode ser lido como negligência progressiva. O encoding ' +
          'NÃO é neutro: a sequência de cor implica causalidade direcional para audiências não treinadas em cartografia. ' +
          'Se o think-aloud revelar esse efeito, o próprio dado fica mais rico — mas se o autor não medir, a banca pergunta, ' +
          'e "escolhi cividis porque é acessível" não sustenta defesa doutoral em HCI.',
      },
      {
        cadeira: 'administrador',
        score_revisado: { tipo: 'qualitativo' },
        veredicto_doutorado:
          'WHY sustenta defesa, mas EXIGE ancoragem disciplinar clara — banca não aceita "é interdisciplinar" como ' +
          'escudo. Recomendação: SAÚDE COLETIVA (USP/Fiocruz/UFMG, área 4 CAPES), porque absorve epidemiologia, ' +
          'iniquidade e política de saúde sem exigir neutralidade econométrica pura. Economia Aplicada (EPGE/PUC-Rio) ' +
          'exigiria causalidade robusta que o Conselheiro de Finanças já diagnosticou como ausente — seria chegar ' +
          'numa banca de espada sem escudo. WHY quádruplo é VANTAGEM se programa for Saúde Coletiva; ARMADILHA num ' +
          'programa monodisciplinar puro.',
        analise_longo_prazo:
          'Em 2050, um WP open-source bem citado e replicável pode ter mudado MAIS gestores públicos do que uma tese ' +
          'trancada em repositório CAPES. Tese gera credencial; WP com DOI e uso institucional gera LEGADO. Trade-off: ' +
          'segurar 3-4 anos pra tese congela o dataset numa janela que vai envelhecer mal — janela epidemiológica é AGORA, ' +
          'com envelhecimento acelerado e PPA 2024-2027 aberto. O risco MAIOR é estrutural: autor mantém SOZINHO 5 ' +
          'pipelines (Emendas, PBF, UroPro, RAIS + WP#4). Doutorado formal sustentando 5 paralelos = recipe for burnout.',
        roadmap_estrategico: [
          {
            n: 1,
            titulo: 'DOI Zenodo + abstract em inglês',
            quando: 'esta semana',
            pra_quem: 'comunidade internacional (MDS, Lancet Neurology, LSHTM)',
            why: 'Epidemiológico — mapa auditável global',
            valor: 'R$ 0 + ganho de citabilidade imediata + indexação Google Scholar',
          },
          {
            n: 2,
            titulo: 'Policy brief de 4 páginas para CONITEC',
            quando: 'mês 1',
            pra_quem: 'CONITEC + Câmara Técnica de Neurologia do CFM',
            why: 'Político',
            valor: 'R$ 0 direto, mas abre porta a contrato consultoria R$ 40-80k/projeto com SES',
          },
          {
            n: 3,
            titulo: 'Carta-convite à ABP / Instituto Parkinson Brasil',
            quando: 'mês 1-2',
            pra_quem: 'ABP + neurologia de movimento',
            why: 'Clínico',
            valor: 'Peso institucional → credencial p/ edital + visibilidade p/ tese',
          },
          {
            n: 4,
            titulo: 'Edital INCT/CNPq Doenças Neurológicas ou CAPES Pró-Saúde',
            quando: 'meses 2-4',
            pra_quem: 'CNPq/CAPES, com UFMG ou Fiocruz como instituição-sede',
            why: 'Todos os 4 entram no formulário de relevância social',
            valor: 'R$ 200-800k em bolsas + infra; via natural de entrada no doutorado SEM perder os pipelines (edital financia orientandos que assumem os pipelines paralelos)',
          },
          {
            n: 5,
            titulo: 'Parceria com jornalista de dados',
            quando: 'meses 1-3',
            pra_quem: 'cidadão + gestor via imprensa (Pública, Piauí, Nexo)',
            why: 'Demográfico — urgência 2060 tem alto valor jornalístico',
            valor: 'R$ 0; 10× mais impacto de PP do que 10 papers acadêmicos',
          },
          {
            n: 6,
            titulo: 'Contato LSHTM / Johns Hopkins CIDR (co-autoria internacional)',
            quando: 'meses 3-6',
            pra_quem: 'pesquisadores de equidade em saúde global',
            why: 'Epidemiológico em escala LATAM',
            valor: 'Lancet Regional Health Americas = credencial máxima p/ banca de doutorado',
          },
          {
            n: 7,
            titulo: 'REA/MEC + módulo técnico (cap. de pós-graduação)',
            quando: 'meses 4-8',
            pra_quem: 'PPG Saúde Coletiva + residências médicas',
            why: 'Clínico + pedagógico',
            valor: 'R$ 15-30k/contrato de capacitação por SES; replicável em 27 UFs',
          },
        ],
        unica_acao_que_muda_o_jogo:
          'Depositar no Zenodo esta semana com DOI e abstract em inglês. Custa 40 minutos. Transforma o WP de ' +
          '"arquivo pessoal" em "literatura citável internacionalmente" — e abre todas as outras 6 portas automaticamente.',
        risco_estrategico_subestimado:
          'A maior ousadia (Carrey-style) NÃO é entrar no doutorado — é perceber que este paper pode e deve virar a ' +
          'tese de OUTRA pessoa. O autor tem o dataset, o pipeline, o WHY e a visão de plataforma. Bom orientador de ' +
          'Saúde Coletiva (Fiocruz/UFMG) colocaria mestrando ou doutorando para desenvolver o WP#4 em tese formal, ' +
          'enquanto o autor permanece como CO-ORIENTADOR ou pesquisador-sênior associado. Isso não é ceder o trabalho ' +
          '— é ESCALAR o impacto sem sacrificar os outros 4 projetos vivos. Confundir "minha tese" com "tese do projeto" ' +
          'é o erro que paralisa pesquisadores-empreendedores.',
        frase_final:
          'Deposite no Zenodo esta semana, escreva a carta para ABP este mês, e decida em 30 dias se você quer SER o ' +
          'doutorando ou FORMAR o doutorando — as duas estratégias são legítimas, mas só uma é sustentável dado o ' +
          'tamanho do que você já construiu.',
      },
    ],
    consenso_emergente: [
      {
        topico: 'Score: nenhum dos 3 quants moveu',
        detalhe:
          'Finanças mantém B (2,0) + Eng. Software mantém B+ (2,5) + Design mantém A (3,0). Média 2,5. WHY quádruplo ' +
          'é ganho de POSICIONAMENTO/COESÃO — não cria identificação causal nova, não fecha verify-reproducibility, ' +
          'não roda think-aloud. Para subir as notas é PRECISO ENTREGAR — não basta articular.',
      },
      {
        topico: 'Programa de doutorado: SAÚDE COLETIVA é o consenso',
        detalhe:
          'Finanças (PPG Saúde Coletiva Fiocruz/USP-FSP), Eng. Software (Eng. Dados aplicada à Saúde UFRJ/USP/UFMG), ' +
          'Administrador (Saúde Coletiva USP/Fiocruz/UFMG explicitamente). 3 das 4 cadeiras convergem em programa de ' +
          'Saúde Coletiva como destino. Vantagem: absorve as 4 lentes sem exigir neutralidade econométrica pura.',
      },
      {
        topico: 'Ação imediata: DOI Zenodo esta semana',
        detalhe:
          'Administrador isolado mas convergente com Eng. Software (item 3 do roadmap). Custo 40min, ganho de ' +
          'citabilidade internacional + indexação Google Scholar. Pré-requisito para policy brief, parceria ABP, ' +
          'edital CNPq, co-autoria internacional. É a ÚNICA ação que abre 6 portas simultâneas.',
      },
      {
        topico: 'Decisão estratégica em 30 dias: SER vs FORMAR doutorando',
        detalhe:
          'Administrador isolado, mas é a pergunta de fundo. Autor mantém 5 pipelines paralelos. Doutorado formal ' +
          'sustentando os 5 = recipe for burnout. Alternativa: ser CO-ORIENTADOR de mestrando/doutorando que assume ' +
          'WP#4 como tese, autor permanece como pesquisador-sênior. Confundir "minha tese" com "tese do projeto" é o ' +
          'erro que paralisa pesquisadores-empreendedores.',
      },
      {
        topico: 'Armadilhas técnicas convergentes (cada lente identifica uma)',
        detalhe:
          'Finanças: SUTVA + staggered DiD (TWFE pooled artefato). Eng. Software: CI não roda Databricks Free Edition ' +
          'end-to-end (reprod. parcial). Design: cividis NÃO é neutro para audiência leiga (gradiente lido como ' +
          'causalidade). Cada armadilha é específica da lente, mas as 3 convergem em "honesty about limits" — exigência ' +
          'central de defesa doutoral.',
      },
    ],
  },

  reavaliacao_administrador: {
    rodada: 3,
    cadeira: 'administrador',
    veredicto: 'APROVADO COM AJUSTES',
    epigrafe_aprovacao:
      '"4 WHYs simultâneos sobre o mesmo dataset não é diluição — é segmentação, e segmentação bem-feita ' +
      'fortalece. Cada WHY tem um ‘por que isso importa para mim’ para o leitor certo."',
    ajuste_minimo:
      'A tese central (parágrafo unificador) precisa aparecer textualmente no abstract, nos dois primeiros ' +
      'parágrafos da introdução e na abertura da discussão. Sem esse fio, o leitor de cada silo lê o paper ' +
      'pelo seu WHY e não enxerga os outros três — o que desperdiça o argumento de que são as quatro ' +
      'dimensões simultaneamente sobre o mesmo dataset que tornam o trabalho único.',

    teste_harari: {
      veredicto: 'Antecipador, não registro do presente — se redigido nessa chave',
      texto:
        'Em 50 anos o Brasil terá entre 2 e 3 milhões de parkinsonianos, pirâmide etária completamente ' +
        'invertida e histórico documentado de como o país gerenciou (ou deixou de gerenciar) a transição. ' +
        'Este paper, se entrar na literatura agora, será citado como linha de base daquele período — ' +
        '"em 2025, o gap já era mensurável e a escolha política já era rastreável". Envelhecimento + ' +
        'iniquidade regional é uma das três ou quatro colisões estruturais do século XXI brasileiro.',
    },

    teste_carrey: {
      ousadia_nao_vista:
        'O autor tem um dataset público auditável, um DiD honesto e quatro frentes de impacto. Está deixando ' +
        'tudo isso preso atrás de um paywall acadêmico futuro enquanto o dado já está disponível hoje. A ' +
        'ousadia é publicar os mapas no Mirante AGORA, com DOI Zenodo no dataset, antes de submeter o paper — ' +
        'o que inverte o fluxo: a evidência chega nos decisores antes da lenta fila editorial.',
      portas: [
        {
          nome: 'Policy brief para CONITEC/MS',
          why_associado: 'Político',
          descricao:
            '8 páginas derivadas da Seção 7, linguagem não-acadêmica, entregue diretamente às comissões antes ' +
            'da próxima revisão do PCDT de Parkinson.',
          valor: 'Probabilidade real de citação em audiência pública. Custo marginal: zero, o DiD já está feito.',
        },
        {
          nome: 'Parceria com associações de pacientes (ABP, Instituto Parkinson)',
          why_associado: 'Clínico + Epidemiológico',
          descricao:
            'Co-branding de relatório com ABP e Instituto Parkinson — bases de filiados precisam de evidência ' +
            'espacial para campanhas de expansão de centros de referência.',
          valor: 'R$ 40-80k/projeto de pesquisa encomendada + visibilidade institucional.',
        },
        {
          nome: 'Jornalismo de dados (Pública, Volt, Piauí, Folha)',
          why_associado: 'Epidemiológico',
          descricao:
            'Os 2 mapas coropléticos + projeção 2060 são conteúdo pronto para Agência Pública, Volt Data Lab, Piauí.',
          valor: '10-50× alcance de qualquer periódico acadêmico + citação indireta. Custo: 1 reunião de 30min.',
        },
        {
          nome: 'Edital INCT ou CNPq Universal Faixa C',
          why_associado: 'Demográfico',
          descricao:
            '"Antecipação do choque demográfico" é exatamente o framing que financia projetos de 3-4 anos. ' +
            'O paper bem publicado é o produto 1 da proposta.',
          valor: 'R$ 500k-1,2 milhão (Universal Faixa C ou INCT).',
        },
        {
          nome: 'Consultoria de auditoria de RM para TCEs estaduais',
          why_associado: 'Político + Demográfico',
          descricao:
            'O mesmo pipeline que auditou EC 86 pode ser contratado por Tribunais de Contas estaduais para ' +
            'auditar contratos de locação de equipamentos.',
          valor: 'R$ 80-150k/projeto por estado.',
        },
      ],
    },

    implicacao_editorial: {
      destino_primario: 'Cadernos de Saúde Pública (acesso aberto, leitura por CONITEC)',
      destino_paralelo: 'Journal of Public Health Policy (versão expandida da seção política)',
      destino_aspiracional:
        'Lancet Regional Health — Americas (exige identificação causal mais limpa; β marginal a p=0,075 será cobrado lá)',
      adiar_60_90d: false,
      condicional: 'Submissão imediata é liberada CONDICIONAL a re-redação do abstract',
      reescrever_abstract:
        'Abrir com a tese central unificadora (4 ângulos sobre mesmo dataset), não com "este artigo analisa ' +
        '3.900 RM". Fechar com call-to-action diferenciado por audiência (1 frase por WHY).',
    },

    recomendacoes_taticas: {
      proxima_semana: [
        'Re-escrever abstract: §1 = tese central unificadora dos 4 WHYs; §último = CTAs diferenciados por audiência.',
        'Publicar os 2 mapas coropléticos no Mirante com DOI Zenodo no dataset — inverte o fluxo, dado chega antes do paper.',
      ],
      proximo_mes: [
        'Produzir policy brief de 8 páginas (derivado da Seção 7) e encaminhar diretamente para a assessoria ' +
        'técnica da Comissão de Saúde do Senado e para o GT de Equipamentos da CONITEC.',
        'Submeter para Cadernos de Saúde Pública.',
      ],
      proximos_6_meses: [
        'Usar o paper publicado como produto 1 de proposta CNPq Universal Faixa C com framing de antecipação ' +
        'do choque demográfico.',
      ],
      parar_de_fazer:
        'Parar de tratar o DiD como o coração do paper. Ele é o HOW do WHY Político — um dos quatro. Colocá-lo ' +
        'no centro da narrativa é voltar ao erro original de WHAT-first. O coração é a colisão entre 535 mil ' +
        'casos hoje e iniquidade espacial mensurável agora.',
    },
  },
};

// ═══════════════════════════════════════════════════════════════════════
// REUNIÃO #2 — WP#6 v2 (Panorama integrado cross-vertical, Chalhoub)
// Data: 2026-04-26 · 2 rodadas (R1 pareceres + R2 WHY) + verificação factual
// Status: APROVADO COM AJUSTES · WHY DUPLO formalizado
// ═══════════════════════════════════════════════════════════════════════
export const ATA_WP6_REUNIAO_2 = {
  meta: {
    reuniao: 2,
    artigo: 'WP#6 v2 — Panorama integrado cross-vertical (Equipamentos CNES)',
    artigo_titulo_completo:
      'Panorama integrado: equipamentos de saúde como nó cross-vertical do ' +
      'Mirante dos Dados — análise do trio de neuroimagem (RM, CT, PET/CT) e ' +
      'seus cruzamentos com Bolsa Família, Emendas Parlamentares e UroPro ' +
      '(Brasil, 2013–2025)',
    commit: 'dda3e6e',
    data: '2026-04-26',
    coautoria: 'Leonardo Chalhoub (autor único)',
    rodadas: 2,
    status: 'APROVADO COM AJUSTES',
    media_quants: 2.33, // (B 2,0 + B+ 2,5 + B+ 2,5) / 3
    limiar_aprovacao: 2.0,
  },

  pareceres_iniciais: [
    {
      cadeira: 'financas',
      titulo: 'Conselheiro de Finanças & Métodos Quantitativos',
      lente: 'Identificação causal · regressão multivariada · robustez estatística',
      score: { tipo: 'letra', letra: 'B', pontos: 2.0 },
      veredicto: 'major revision',
      epigrafe:
        '"O paper subiu de C para B pela triangulação cross-domain. Não vai subir além do B enquanto a análise ' +
        'empírica for integralmente baseada em correlação Pearson bivariada sobre 27 pontos."',
      argumento_central:
        'A Fase A editorial (newtx, SciencePlots, float layout, datetime stamp) é costura: muda zero o ' +
        'numerador da equação de aceitação em journal. A análise continua: oito correlações Pearson bivariadas, ' +
        '27 observações (UFs), sem controle por PIB per capita, sem efeitos fixos, sem robustness check, sem ' +
        'identificação causal de nenhuma espécie. Sem regressão multivariada, paper trava em B.',
      pendencias: [
        'Ausência de controle multivariado (PIB, médicos/1000 hab) — desk-reject provável em RAP/RBE',
        'Sem robustness checks (Spearman, leave-one-out excluindo DF, AC) — qualquer revisor mediano pede',
        'Sem painel longitudinal — autor tem 13 anos de dados (351 obs por equação) e não usa',
        'Sem identificação causal — EC 86/2015 listada como agenda mas não implementada',
        'Autocorrelação espacial ignorada (Moran\'s I sobre resíduos)',
      ],
      sugestao_para_subir_pra_a:
        'Regressão OLS HC3 multivariada (PIB + médicos + region_FE), n=27, com Spearman + jackknife como ' +
        'robustness padrão. Essa é a "única ação que muda o jogo" para Finanças no WP#6.',
    },
    {
      cadeira: 'eng-software',
      titulo: 'Conselheiro de Engenharia de Software & Plataforma',
      lente: 'Reprodutibilidade · pipeline auditável · contract tests cross-vertical',
      score: { tipo: 'letra', letra: 'B+', pontos: 2.5 },
      veredicto: 'minor revision',
      epigrafe:
        '"ARCHITECTURE.md existe e tem ADRs completos. Suite de 12 testes invariantes sobre o gold é engenharia ' +
        'de pesquisa séria. Mas testes rodam sobre o gold JSON, não sobre a transformação."',
      argumento_central:
        'O repositório evoluiu em aspectos que a review anterior não havia visto completos — ARCHITECTURE.md ' +
        'tem 6 ADRs Nygard, suite de 12 testes invariantes calibrados contra OCDE, conftest.py com fixtures para ' +
        'todos os 4 golds. Bloqueadores remanescentes: testes só sobre artefato (não sobre transformação), ' +
        'dedup dual-flag não verificado por invariante metodológica, sem DOI Zenodo do código.',
      pendencias: [
        'Testes de transformação ausentes (PySpark sintético) — major revision em JOSS/ESE',
        'Dedup dual-flag verificado por consistência interna, não por invariante metodológica',
        'ARCHITECTURE.md sem URL permanente nem DOI Zenodo — não citável como artefato',
        'Contract tests cross-vertical ausentes — schema drift quebra silenciosamente os 6 WPs',
      ],
      sugestao_para_subir_pra_a:
        'Zenodo DOI do código + ARCHITECTURE.md + dicionário canônico (3 dias). Análoga à "única ação que muda ' +
        'o jogo" do WP#4. Destrava citabilidade como artefato de software de primeira classe.',
    },
    {
      cadeira: 'design',
      titulo: 'Conselheira de Design & Visualização de Dados',
      lente: 'Tufte (data-ink) · Norman (affordance) · Bostock (interatividade)',
      score: { tipo: 'letra', letra: 'B+', pontos: 2.5 },
      veredicto: 'minor revision',
      epigrafe:
        '"As 3 mudanças da Fase A são higiene editorial correta. Não são suficientes para mover o score porque ' +
        'os 3 problemas estruturais — zero interatividade, acessibilidade não documentada, design-system.md ' +
        'ausente — permanecem inalterados."',
      argumento_central:
        'Mantém B+ do WP v1. Tendência positiva (Fase A entregou tipografia + datetime stamp + cache-buster), ' +
        'incremental. A figura central que sustenta o WHY do WP#6 sozinha — small multiple 2×2 com eixo X ' +
        'compartilhado (% PBF) e Cividis por região — não existe ainda. A Tabela 7.2 de correlações deveria ' +
        'ser um forest plot com IC 95% via Fisher z-transform.',
      pendencias: [
        'Zero interatividade — 3 scatters cross-vertical (Fig 13–15) são candidatas naturais a Vega-Lite',
        'Par cromático #1d4ed8 (azul) / #7e22ce (roxo) na Fig 11 colapsa em deuteranopia',
        'docs/design-system.md ausente — sem tokens documentados (cores, tipografia, espaçamento)',
        'Tabela 7.2 (síntese cross-vertical) deveria ser forest plot — anti-storytelling visual atual',
        'Audit Lighthouse + Axe + WAVE não declarado',
      ],
      sugestao_para_subir_pra_a:
        'Forest plot substituindo Tabela 7.2 (1 semana, custo-benefício alto) + corrigir par cromático ' +
        'azul/roxo (1-2 dias) + design-system.md em /docs (1 semana). Subiria pra A.',
    },
    {
      cadeira: 'administrador',
      titulo: 'Conselheiro de Administração & Aplicação Prática',
      lente: 'Sinek (WHY) · Harari (escala histórica) · Carrey (ousadia)',
      score: { tipo: 'qualitativo' },
      veredicto: 'aprovado com ajustes — WHY ausente no manuscrito',
      epigrafe:
        '"O federalismo brasileiro financia a aparência de saúde pública — e durante 12 anos, em dois domínios ' +
        'simultâneos, ninguém havia juntado os dados para provar isso. Esse é o WHY do paper. Mas o paper não ' +
        'diz isso."',
      argumento_central:
        'WHY latente forte mas nunca articulado explicitamente. O texto começa pelo WHAT ("este Working Paper é ' +
        'deliberadamente agregador") e nunca chega ao "por que isso importa". Audiências subutilizadas: TCU/' +
        'SecexSaúde, IFI/Senado, CONASS, DENASUS/AudSUS, Banco Mundial Brasil. Cosplay de paper vs mudança real: ' +
        'autor confortável demais no descritivo-correlacional. EC 86 listada como agenda há vários WPs e nunca ' +
        'implementada.',
      perguntas_criticas: [
        'O WP#6 existe para DOCUMENTAR o paradoxo das emendas — ou para RESOLVER? (Implicações editoriais opostas)',
        'Para quem este paper é evidência operacional — não acadêmica? Quem cita em decisão de auditoria?',
        'Onde está o policy brief de 8 páginas para TCU/CONASS derivado do paper?',
        'Tier 2 BR solo (4 meses) ou Tier 1 internacional com co-autoria FIOCRUZ/UERJ/INCA (12-18 meses)?',
      ],
    },
  ],

  // ═════════ Rodada 2 — definição do WHY do artigo ═════════
  rodada_2_why: {
    titulo: 'Rodada 2 — definição do WHY do artigo',
    contexto:
      'Com o R1 concluído (média 2,33 — acima do limiar 2,0), os 4 conselheiros foram convocados em paralelo ' +
      'para propor o WHY do artigo WP#6 (não da plataforma — escopo travado para evitar o erro da R2A v1 da ' +
      'Reunião #1). Cada cadeira propôs 1-2 WHYs com audiência específica e formato (único / duplo / quádruplo). ' +
      'Resultado: 3 das 4 cadeiras (Finanças, Eng. Software, Administrador) convergiram em DUPLO; Design ' +
      'preferiu ÚNICO com geometria interna de 4 elementos. Nenhuma cadeira propôs quádruplo (rejeição unânime ' +
      'do espelho do WP#4).',
    whys_propostos: [
      {
        cadeira: 'financas',
        formato_proposto: 'duplo',
        why_substantivo:
          'Porque o federalismo fiscal brasileiro financia a aparência de saúde pública: durante doze anos, em ' +
          'dois domínios independentes (cirurgia urológica WP#3, equipamentos de neuroimagem WP#6), as emendas ' +
          'parlamentares per capita correlacionam-se NEGATIVAMENTE com capacidade especializada.',
        why_metodologico:
          'Iniquidade estrutural cross-vertical (gradiente PBF↔infraestrutura ρ ≈ -0,68) como diagnóstico de ' +
          'política de saúde de longo prazo, distinguível do paradoxo fiscal compensatório.',
        audiencia: 'TCU/SecexSaúde · IFI/Senado · STN · Banco Mundial Brasil · Cad SP · RAP',
      },
      {
        cadeira: 'eng-software',
        formato_proposto: 'duplo',
        why_substantivo:
          'Paradoxo das emendas replicado em 2 domínios (cirurgia + neuroimagem) eleva hipótese exploratória a ' +
          'padrão empírico robusto requerendo explicação causal.',
        why_metodologico:
          'Bug semântico CNES (double-count via dual-flag IND_SUS) + pipeline aberto auditável é a primeira ' +
          'documentação pública desse mecanismo com fix testado e replicável — tornando qualquer análise ' +
          'downstream que use raw sus+priv potencialmente questionável.',
        audiencia: 'DATASUS/CGSI/MS · OpenSAFELY · Software Heritage · OBSERVAGov-FGV · IEPS · Empirical SE · JOSS',
      },
      {
        cadeira: 'design',
        formato_proposto: 'único com geometria 4',
        why_substantivo:
          'A desigualdade em saúde no Brasil é coerente através de domínios — só se torna visível quando 4 ' +
          'fontes (CNES, PBF, Emendas, UroPro) são postas na mesma escala e mesmo sistema de coordenadas.',
        why_metodologico:
          '(implícito) Design como método de comensurabilidade entre as 4 dimensões — não como 5ª lente ' +
          'paralela aos 4 WHYs do WP#4.',
        audiencia: 'Núcleo Jornalismo · ENSP/Fiocruz · CONASEMS · IEEE CG&A · Information Design Journal',
      },
      {
        cadeira: 'administrador',
        formato_proposto: 'duplo',
        why_substantivo:
          'Político-institucional — paradoxo fiscal das emendas como ilusão de redistribuição que precisa ' +
          'entrar no debate de revisão do arcabouço fiscal pós-EC 95.',
        why_metodologico:
          'Pipeline público auditável replicável — qualquer SES, TCU ou pesquisador pode rodar a auditoria ' +
          'sobre seus próprios dados.',
        audiencia: 'TCU · IFI · CONASS · DENASUS · Comissões de Saúde do Congresso (substantivo) + ' +
                   'pesquisadores · secretarias estaduais (metodológico)',
      },
    ],

    voto_sobre_formato: {
      unico: 1,        // Design
      duplo: 3,        // Finanças, Eng. Software, Administrador
      quadruplo: 0,
      vencedor: 'duplo',
      observacao:
        'Convergência forte (3-1) em DUPLO. Design dissente em formato mas seu "WHY único com geometria de 4 ' +
        'elementos" é compatível com a leitura de que os 2 WHYs do duplo capturam as 4 dimensões internamente.',
    },

    why_consolidado: {
      tipo: 'duplo',
      decidido_pelo_autor: true,
      data_decisao: '2026-04-26',
      escopo: 'pesquisador (DOCUMENTAR), não policy maker (RESOLVER) — alinhado com escopo de PhD que publica',
      nota:
        'Diferente do WP#4 (quádruplo, 4 audiências distintas para 1 fenômeno clínico-epidemiológico), o WP#6 ' +
        'tem 2 contribuições genuinamente independentes — substantiva e metodológica — que atraem audiências ' +
        'diferentes (Cad SP/RAP vs JOSS/Empirical SE). DUPLO mapeia diretamente para essa estrutura.',
      tese_central:
        'O Brasil cadastra hoje 3.900 ressonâncias magnéticas — 18,27 unidades por milhão de habitantes em 2025, ' +
        'próximo da mediana OECD (17/Mhab). A distribuição dessas máquinas entre as 27 UFs segue o gradiente ' +
        'estadual de pobreza com força marcada (ρ ≈ -0,68 com cobertura do Bolsa Família), e o mesmo padrão ' +
        'reaparece, com sinal e magnitude semelhantes, num segundo domínio empírico independente — o acesso ' +
        'cirúrgico medido pelo UroPro. As emendas parlamentares à saúde, instrumento fiscal de vocação ' +
        'redistributiva, correlacionam-se negativamente com infraestrutura especializada nessas duas dimensões ' +
        'simultaneamente. Este artigo organiza a observação cross-vertical sobre um pipeline aberto, testado e ' +
        'replicável.',
      duplo: [
        {
          lente: 'Político-Institucional',
          cor: '#1d4ed8',
          frase:
            'expor que as emendas parlamentares à saúde não corrigem o gradiente de pobreza — em dois domínios ' +
            'empíricos independentes, UFs que recebem mais emendas per capita têm MENOS infraestrutura ' +
            'especializada por habitante.',
          audiencia:
            'TCU/SecexSaúde · IFI/Senado · CONASS · DENASUS/AudSUS · Comissões de Saúde do Congresso · ' +
            'Banco Mundial Brasil',
          cta:
            'Incluir métrica de RESULTADO (capacidade instalada) nos relatórios de monitoramento das emendas de ' +
            'saúde — não apenas execução financeira',
          how_no_paper:
            'Análise cross-vertical com 8 correlações ρ Pearson UF×UF, replicação independente do paradoxo das ' +
            'emendas em dois domínios (UroPro WP#3 + Equipamentos WP#6) — 2025 cross-section, 27 UFs',
        },
        {
          lente: 'Metodológico-Replicável',
          cor: '#0d9488',
          frase:
            'documentar publicamente o método de auditoria semântica que detectou e corrigiu uma falha de ' +
            'contagem no módulo Equipamentos do CNES — versão pré-fix do Mirante superestimava a densidade ' +
            'nacional de RM em fator ≈2 vs mediana OECD — e entregar o pipeline aberto que torna esse padrão ' +
            'de auditoria replicável para qualquer outro módulo do DATASUS.',
          audiencia:
            'DATASUS/CGSI/MS · OpenSAFELY · Software Heritage · OBSERVAGov-FGV · IEPS · FIOCRUZ-Reprodutibilidade',
          cta:
            'Adicionar nota de aviso na documentação de download do DBC Equipamentos do DATASUS sobre o ' +
            'mecanismo dual-flag IND_SUS — custo zero para o DATASUS, impacto imediato em toda análise downstream',
          how_no_paper:
            'Seção 4.3 documenta anatomia completa: detecção (~35,6 RM/Mhab vs OECD 17 = ~2× = sinal de ' +
            'double-count), hipótese causal (dual-flag IND_SUS), fix (MAX(qt_sus, qt_priv) por (CNES, mês)), ' +
            'verificação (overlap pós-fix), e generalização',
        },
      ],
    },

    verificacao_factual: {
      titulo: 'Verificação factual da tese central — Databricks + gold JSON atual',
      data: '2026-04-26',
      gatilho:
        'Autor questionou a frase original "fator ≈2 inflado na literatura corrente" — não há citação direta ' +
        'da literatura no texto, e o número 35,6/Mhab vinha do Mirante v1 (própria plataforma), não de papers ' +
        'externos.',
      narrativa:
        'Query ao gold JSON publicado (data/gold/gold_equipamentos_estados_ano.json) confirmou que o fix do ' +
        'dual-flag JÁ ESTÁ EM PRODUÇÃO desde os commits 6f4e1ca + 4d47d37 + 08df2b2. Estado atual: RM Brasil ' +
        '2025 = 3.900 unidades = 18,27/Mhab; sus+priv = total_avg = 3.900 (idênticos); overlap dual-flag = ' +
        '0,0% em todos os 13 anos do painel; ratio raw vs deduped = 1,00x. Em 2025, dos 3.082 rows analisáveis, ' +
        'apenas 19 (0,6%) mostram qualquer overlap detectável — e o maior é "Bomba Balão Intra-Aórtico" em SE ' +
        'com diferença de 1 unidade.',
      consequencia:
        'A §4.3 do manuscrito está STALE — afirma overlap ~60% para RM em 2025 e "ainda não materializada em ' +
        'Databricks", o que é empiricamente falso no gold atual. O fator ≈2 é HISTÓRICO (Mirante v1 vs OECD), ' +
        'não atual nem da "literatura corrente". A tese central foi reescrita removendo a autobiografia ' +
        'metodológica e atribuindo o fator ≈2 corretamente como diagnóstico interno do Mirante (não acusação ' +
        'de literatura externa). A §4.3 será reescrita no rewrite v3.0 do manuscrito como "auditoria semântica ' +
        'concluída" — não como problema persistente.',
      licao:
        'Toda afirmação de tese deve ser fato-checada contra dado real ANTES de virar parágrafo do paper. ' +
        'O Conselho falhou em pegar isso na R1; o autor pegou. Esse é o tipo de armadilha que peer review real ' +
        'em journal Tier 1 detecta — e que reproduz o ciclo de "auto-engano por agente de IA enthusiastic". ' +
        'Reforçada a regra: tese central só vai ao manuscrito após query ao dado.',
    },
  },
};

// ═══════════════════════════════════════════════════════════════════════
// REUNIÃO #3 — WP#2 v1.0 → v2.0 (Bolsa Família, Auxílio Brasil, NBF)
// Data: 2026-04-27 · 4 pareceres iniciais paralelos · MAJOR REVISION → v2.0
// Histórico: v1.0 avaliada lato 8,5; após pareceres, autor reescreveu como
// stricto sensu B+ (DiD/TWFE/WCB sobre MP 1.061/2021 + Kakwani + benchmark CCT).
// ═══════════════════════════════════════════════════════════════════════
export const ATA_WP2_REUNIAO_1 = {
  meta: {
    reuniao: 3,
    artigo: 'WP#2 v1.0 → v2.0 — Bolsa Família, Auxílio Brasil, Novo Bolsa Família (2013–2025)',
    artigo_titulo_completo:
      'Três Regimes, Um Programa: Documentação Reproduzível, Identificação Causal e ' +
      'Sustentabilidade Fiscal do Bolsa Família, Auxílio Brasil e Novo Bolsa Família (2013–2025)',
    commit: '44bebea (rewrite v2.0)',
    data: '2026-04-27',
    coautoria: null,
    rodadas: 1,
    status: 'MAJOR REVISION → v2.0 STRICTO SENSU B+',
    media_quants: 1.5, // (C 1,0 + C+ 1,5 + B 2,0 + Adm qualitativo) / 3 = 1,5 → motivou rewrite
    limiar_aprovacao: 2.0,
    nota_promocao:
      'Pareceres da v1.0 produziram média 1,5 (abaixo do limiar 2,0). ' +
      'Autor optou por NÃO ajustar incrementalmente — refez como rewrite ' +
      'stricto sensu v2.0 incorporando P1 (DiD/TWFE/WCB), P2 (Kakwani), ' +
      'P3 (ITS/IV piso R$600), P4 (Granger PBF→pobreza) e benchmark CCT ' +
      'internacional (AUH/Prospera/MFA/Renta Dignidad).',
  },

  pareceres_iniciais: [
    {
      cadeira: 'financas',
      titulo: 'Conselheiro de Finanças & Métodos Quantitativos',
      lente: 'Identificação causal · econometria · inconsistências verificáveis',
      score: { tipo: 'letra', letra: 'C', pontos: 1.0 },
      veredicto: 'major revision — abaixo do limiar 2,0',
      epigrafe:
        '"O paper nomeia DOIS choques quasi-experimentais (MP 1.061/2021 e Lei 14.601/2023) ' +
        'com data precisa, e os deixa inexplorados. WP #4 v3.0 fez DiD/TWFE/WCB com null honesto. ' +
        'Aqui, nada disso. C calibrado contra o WP#4 que atravessou o limiar."',
      argumento_central:
        'Pipeline reproduzível de altíssima qualidade (2,2 bi linhas, 280 GB, deflação IPCA, ' +
        'correção do swap nov/2021). MAS ausência total de identificação causal apesar de dois ' +
        'choques naturais explicitamente nomeados. Resumo afirma "lógicas distintas" e ' +
        '"focalização eficaz" como se fossem achados causais — são associativos. CV PBF×Emendas ' +
        'sem teste de igualdade. Per capita por UF sem covariáveis. RDD da agenda futura está com ' +
        'design INCORRETO (RDD requer descontinuidade em variável contínua, piso é escada → ITS).',
      pendencias: [
        'PC-1 [CRÍTICO]: ausência total de identificação causal apesar de 2 choques naturais (MP 1.061, Lei 14.601)',
        'PC-2 [CRÍTICO]: claims causais não identificados em 10+ pontos do texto ("portanto", "confirmam", "mecanismo")',
        'PC-3 [ALTO]: comparação CV PBF vs Emendas sem inferência estatística (Levene, bootstrap, Granger)',
        'PC-4 [ALTO]: ranking per capita sem covariáveis — IDH, pobreza, PIB ausentes',
        'PC-5 [ALTO]: nov/2021 nomeado mas sem ITS (Interrupted Time Series) sobre série mensal',
        '22 inconsistências verificáveis catalogadas (5 críticas: cherry-picking 2018, INC-07 "triplicou"≠dobrou, INC-09 deflação ambígua)',
        'INC-07 [CRÍTICO]: "valor real triplicou 2021→2022" — razão real é 2,16, não 3,0 (erro factual no texto)',
      ],
      sugestao_para_subir_pra_b:
        'Implementar P1 (event study sobre MP 1.061/2021 com ±6 períodos + Roth 2022 pre-trend + ' +
        'wild-cluster bootstrap N=27) + P4 (Kakwani sobre per capita PBF × IDH-M por UF) + ' +
        'corrigir INC-01 a INC-05 + substituir RDD da agenda por ITS. Resultado null aceitável.',
    },
    {
      cadeira: 'eng-software',
      titulo: 'Conselheiro de Eng. de Software & Plataforma de Dados',
      lente: 'Reprodutibilidade · DQ · padrão STRING-ONLY · testes',
      score: { tipo: 'letra', letra: 'C+', pontos: 1.5 },
      veredicto: 'major revision — abaixo do limiar 2,0',
      epigrafe:
        '"Pipeline Databricks roda — isso é o piso mínimo. Mas o texto e a infraestrutura de suporte ' +
        'ficam aquém do padrão WP#4 em quase todos os critérios técnicos: zero tests, viola STRING-ONLY ' +
        'no bronze, dados hardcoded no gerador de figuras. O delta é no que foi escrito, não no que roda."',
      argumento_central:
        'Cadeia bronze→silver→gold→export end-to-end demonstrável com tratamento correto do swap nov/2021 ' +
        '(union + filtragem por origem é não-trivial). MAS: bronze/pbf_pagamentos.py viola padrão ' +
        'STRING-ONLY do projeto (inferColumnTypes=true), build-figures-pbf.py tem SERIES hardcoded em vez ' +
        'de ler gold JSON, ausência de test_pbf_gold.py (WP#4 já tem 13 testes pytest sobre seu gold), ' +
        'zero DQ declarado (sem Great Expectations, sem dbt-style asserts).',
      pendencias: [
        'CRÍTICO: bronze/pbf_pagamentos.py com inferColumnTypes=true — viola padrão Bronze STRING-ONLY do projeto',
        'CRÍTICO: ausência de tests/test_pbf_gold.py (WP#4 tem 13 testes pytest puros, 0,19s)',
        'CRÍTICO: build-figures-pbf.py usa SERIES = [...] hardcoded em vez de reler /data/gold/gold_pbf_estados_df.json',
        'ALTO: zero validação declarada — sem Great Expectations, sem dbt-style asserts, sem manifests',
        'MÉDIO: referências bibliográficas sem datetime de acesso padronizado (\\xurl{...}{data hh:mm})',
      ],
      sugestao_para_subir_pra_b:
        'Aplicar padrão STRING-ONLY no bronze + criar test_pbf_gold.py espelhando o do WP#4 + refatorar ' +
        'build-figures-pbf.py pra ler gold JSON + adicionar pelo menos uma camada DQ (manifest assinado ' +
        'ou test). Roadmap técnico análogo ao que tirou WP#4 de B → B+.',
    },
    {
      cadeira: 'design',
      titulo: 'Conselheira de Design Web & Visualização (HCI)',
      lente: 'Tufte · Norman · Bostock — identidade visual editorial Mirante',
      score: { tipo: 'letra', letra: 'B', pontos: 2.0 },
      veredicto: 'major revision — no limiar 2,0',
      epigrafe:
        '"Cividis nos coropléticos é correto. Eixo duplo da Fig02 é correto. Mas as 12 figuras saem ' +
        'do build-figures-pbf.py SEM editorial_title, SEM source_note, SEM inline_labels, SEM polylabel — ' +
        'matplotlib padrão com paleta Cividis. A uma camada inteira do magazine-grade do WP#4."',
      argumento_central:
        'O artigo cobre dados sólidos com pipeline correto e estrutura ABNT adequada. A vertical web tem o ' +
        'mínimo funcional. Mas ambos ficam a uma camada inteira de distância do padrão magazine-grade que ' +
        'a identidade Mirante exige e que o WP#4 já demonstrou ser alcançável. O gap não é de dados — é de ' +
        'composição visual. build-figures-pbf.py importa apply_mirante_style() mas não usa NENHUM helper ' +
        'de mirante_charts.py (editorial_title, source_note, inline_labels, chart_skeleton).',
      pendencias: [
        'CRÍTICO: build-figures-pbf.py ignora mirante_charts.py — sem editorial_title stack, sem source_note, sem inline_labels, sem GOLDEN_FIGSIZE',
        'CRÍTICO: fig10 (scatter penetração×per capita) — labels diretamente sobre ponto, sem path_effects halo branco, sem adjustText',
        'CRÍTICO: mapas coropléticos (fig06, fig07) usam centroid simples — para BA/PA/AM/MT pode cair fora do polígono. Padrão exige polylabel (pole of inaccessibility)',
        'ALTO: hyperref usa hidelinks em vez de colorlinks magazine-grade',
        'MÉDIO: botão "Ler artigo na tela" AUSENTE na vertical Web (convenção Mirante)',
      ],
      sugestao_para_subir_pra_b_plus:
        'Refatorar build-figures-pbf.py pra usar mirante_charts.py (editorial_title + source_note + ' +
        'inline_labels + chart_skeleton + GOLDEN_FIGSIZE) em todas as 12 figuras + adjustText+halo na ' +
        'fig10 + polylabel nos coropléticos.',
    },
    {
      cadeira: 'administrador',
      titulo: 'Conselheiro de Administração & Aplicação Prática',
      lente: 'Sinek (WHY) · Harari (escala histórica) · Carrey (ousadia)',
      score: { tipo: 'qualitativo' },
      veredicto: 'continua mas não escala nem monetiza no estado atual',
      epigrafe:
        '"O paper sabe o WHAT mas ainda não articulou o WHY. Resumo descreve quatro achados com ' +
        'precisão técnica admirável — três regimes, 283%, gradiente 7:1, CV menor que emendas. ' +
        'Isso é WHAT. O WHY — a razão pela qual esse paper PRECISA existir — aparece só implícito."',
      argumento_central:
        'WP#2 sem WHY formalizado. Dados excelentes rodando a 40% do potencial. Compare com WP#4: o ' +
        'título já grita WHY ("iniquidade diagnóstica") e o resumo abre com "condição neurodegenerativa ' +
        'de crescimento mais acelerado no mundo". Quem lê já sente urgência. WP#2 abre com "O Programa ' +
        'Bolsa Família, criado pela Lei n. 10.836, de 9 de janeiro de 2004..." — correto, institucional, ' +
        'morto. Audiência hoje difusa: navega entre gestor SEPLAN, economista IPEA, jornalista Folha, ' +
        'deputado da Comissão de Assistência Social — nenhuma é dominante.',
      perguntas_criticas: [
        'WHY em uma frase? O autor consegue escrever, em UMA frase, por que o paper existe?',
        '8 milhões de novas famílias do AB — quem são e de onde vieram? Falsos negativos crônicos do PBF clássico OU famílias que entraram na pobreza durante a pandemia?',
        'R$ 140 bi/ano é sustentável? Até quando? Com qual custo de oportunidade vs SUS, educação, infraestrutura?',
        'Quem fecha esse PDF e faz algo diferente? Sem agente concreto, prazo e mecanismo, é desejo de gestão, não implicação de política',
      ],
      sugestao_v2:
        'Formalizar WHY triplo no resumo: documentação reproduzível + identificação causal + ' +
        'sustentabilidade fiscal sob cenários demográficos. Fazer o título gritar pelo menos uma das ' +
        'três. Resumo abrir com tese, não com lei. Implicações com agente, prazo, mecanismo.',
    },
  ],

  resposta_do_autor: {
    decisao: 'rewrite v2.0 stricto sensu',
    data: '2026-04-27',
    commit: '44bebea',
    nota:
      'Em vez de patch incremental sobre v1.0, autor optou pelo rewrite completo: WHY triplo ' +
      'formalizado no resumo (documentação reproduzível + identificação causal + sustentabilidade ' +
      'fiscal), DiD/TWFE com wild-cluster bootstrap sobre MP 1.061/2021, Kakwani sobre per capita PBF × ' +
      'IDH-M por UF, ITS sobre série mensal nov/2021, benchmark CCT internacional (AUH Argentina, ' +
      'Prospera México, MFA Colômbia, Renta Dignidad Bolívia em US$ PPP 2021), 17 figuras vetoriais ' +
      '(incluindo barbell DiD, event study, curva de Kakwani, razão necessidade/cobertura). Versão ' +
      'promovida de lato 8,5 → stricto sensu B+. Audit Finanças sobre v2.0 ainda pendente — as 22 ' +
      'inconsistências da v1.0 foram parcialmente endereçadas mas precisam validação completa pré-submissão.',
    score_pos_rewrite: 'B+ (2,5) na régua mestrado',
  },
};

// ─── Lookup helper ───────────────────────────────────────────────────────
export const ATAS_BY_ARTIGO = {
  'wp4-equipamentos-rm-parkinson': ATA_WP4_REUNIAO_1,
  'wp6-equipamentos-panorama-cnes': ATA_WP6_REUNIAO_2,
  'wp2-bolsa-familia':              ATA_WP2_REUNIAO_1,
};

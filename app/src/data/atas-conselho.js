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

// ═══════════════════════════════════════════════════════════════════════
// REUNIÃO #4 — WP#7 v2.0 (Bolsa Família por Município, 5.570 munis)
// Data: 2026-04-27 · 4 pareceres iniciais paralelos · APROVADO
// Histórico: WP#7 nasce como resposta direta ao gargalo identificacional
// flagged pelo Conselho de Finanças no WP#2 (k=27 ≪ 30 Cameron-Gelbach-
// Miller). v2.0 substitui o fallback proporcional UF→muni da v1.0 por
// dados REAIS via SQL warehouse direto sobre bronze.pbf_pagamentos
// (2,53 bi linhas) + malha geobr canônica (5.570 munis IBGE 2020).
// Média (B+ + B+ + B+ + B) / 4 = 2,375 — APROVADO ACIMA DO LIMIAR 2,0.
// É a maior média do projeto até hoje (WP#4: 1,83 → 2,5 em v3.1; WP#6:
// 2,33; WP#2: 1,5 → B+ em v2.0; WP#7: 2,375 já no nascimento).
// ═══════════════════════════════════════════════════════════════════════
export const ATA_WP7_REUNIAO_1 = {
  meta: {
    reuniao: 4,
    artigo: 'WP#7 v2.0 — Bolsa Família por Município (2013–2025, 5.570 munis)',
    artigo_titulo_completo:
      '5.570 pontos de decisão: microdados municipais do Bolsa Família, ' +
      'identificação causal por variação cross-municipal e heterogeneidade ' +
      'intra-UF (2013–2025)',
    commit: '8aa1edf (fix LaTeX) + commits anteriores da pipeline real',
    data: '2026-04-27',
    coautoria: 'Leonardo Chalhoub (autor único)',
    rodadas: 1,
    status: 'APROVADO — maior média do projeto',
    media_quants: 2.375, // (B+ 2,5 + B+ 2,5 + B+ 2,5 + B 2,0) / 4 = 2,375
    limiar_aprovacao: 2.0,
    nota_promocao:
      'WP#7 nasce respondendo ao gargalo identificacional do WP#2 (k=27 ' +
      '≪ 30 Cameron-Gelbach-Miller 2008). v2.0 substitui o fallback ' +
      'proporcional UF→muni da v1.0 por dados REAIS agregados via SQL ' +
      'warehouse direto sobre bronze.pbf_pagamentos (2,53 bi linhas) — ' +
      'heterogeneidade intra-UF agora é EFETIVA, não artefato. Aprovação ' +
      'unânime das 4 cadeiras com média 2,375 — primeira vez que o ' +
      'projeto cruza o limiar 2,0 já no R1.',
  },

  pareceres_iniciais: [
    {
      cadeira: 'financas',
      titulo: 'Conselheiro de Finanças & Métodos Quantitativos',
      lente: 'Identificação causal · Conley HAC · cluster-robust inference',
      score: { tipo: 'letra', letra: 'B+', pontos: 2.5 },
      veredicto: 'APROVADO — sobe sobre WP#2',
      epigrafe:
        '"Este é o paper que o WP#2 precisava ter sido. Subi de C (1,0 no WP#2) ' +
        'para B+ (2,5 no WP#7) por três contribuições metodológicas concretas. ' +
        'O gargalo identificacional do WP#2 desaparece estruturalmente."',
      argumento_central:
        'Migração de N=27 para k=5.570 clusters (185× o mínimo Cameron-Gelbach-' +
        'Miller 2008 para wild-cluster bootstrap convergir). Conley HAC com ' +
        'distâncias geodésicas haversine REAIS sobre centroides geobr — não ' +
        'cluster artificial. Bandwidth sensitivity 50–1600 km mostra ' +
        'inflação MONOTÔNICA do SE com bandwidth (h=50: SE=10,9; h=200: SE=36,5; ' +
        'h=800: SE=101,7; h=1600: SE=149,2) — diagnóstico empírico de correlação ' +
        'espacial positiva nos resíduos. Mesmo no extremo (1.600 km), |t| ≥ 2,0 ' +
        '— efeito sobrevive ao teste mais conservador. DiD 2×2 sobre as duas ' +
        'rupturas: MP 1.061/2021 β̂=+205,3 R$/hab (IC 95% [201,2; 209,3]); ' +
        'Lei 14.601/2023 β̂=+349,5 R$/hab (IC 95% [343,9; 355,2]). Magnitude ' +
        'maior na Lei 14.601 é consistente com redesenho duplo (piso + ' +
        'adicionais por composição). Definição de tratamento idêntica ao WP#2 ' +
        '— cross-paper consistente.',
      pendencias: [
        'Kernel Conley uniforme em vez de Bartlett (ortodoxo Conley 1999) ou Parzen — kernel uniforme é menos conservador no decay',
        'RDD geográfico em fronteiras estaduais ausente — com 5.570 munis e lat/lon real é trivialmente possível em pares vizinhos cruzando fronteira (BA-MG, RJ-SP)',
        'Multiple testing nos 2 DiDs sem correção Bonferroni nem combinação por meta-análise (p_combined < 0,001 trivial mas formalmente ausente)',
        'Event study apresentado mas sem teste estatístico formal Roth 2022 de parallel trends — Figura 13 mostra leads/lags visualmente apenas',
        'Heterogeneidade intra-UF da v2.0 ainda precisa ser comparada quantitativamente contra a v1.0 (fallback) para mensurar quanto da variação era artefato',
      ],
      sugestao_para_subir_pra_a:
        'Kernel Bartlett (Conley 1999 ortodoxo) + bootstrap espacial + RDD ' +
        'geográfico em fronteiras BA-MG e RJ-SP onde regras de auxílio ' +
        'estadual diferem. Outcomes proxy mensais (DATASUS-SIM óbitos ' +
        'infantis, INEP abandono, CAGED formalização) validariam o ' +
        'mecanismo causal além do paramount.',
    },
    {
      cadeira: 'eng-software',
      titulo: 'Conselheiro de Engenharia de Software & Plataforma de Dados',
      lente: 'Reprodutibilidade · STRING-ONLY bronze · UC metadata · pytest',
      score: { tipo: 'letra', letra: 'B+', pontos: 2.5 },
      veredicto: 'APROVADO',
      epigrafe:
        '"Pipeline arquitetural completo. Padrões de plataforma respeitados ' +
        'sem exceção. Sobe sobre o WP#2 (B em Eng. Software) por três motivos ' +
        'estruturais. Falta apenas pytest sobre silver/gold pra cruzar o A."',
      argumento_central:
        'Pipeline Databricks 6 notebooks com responsabilidades bem separadas ' +
        '(1 ingest geobr + 2 silver pop_municipio_ano + silver ' +
        'pbf_total_municipio_mes + 1 gold pbf_municipios_df + 1 export). ' +
        'STRING-ONLY bronze (regra de plataforma) preservada — todos os casts ' +
        'em silver. UC metadata mandatória presente: COMMENT ON TABLE + ALTER ' +
        'COLUMN COMMENT por coluna + SET TAGS layer/domain/source/pii/grain ' +
        'em TODAS as tabelas novas. Particionamento Delta consistente ' +
        '(partitionBy("Ano")). Match IBGE↔CGU 100% via NAME_FIX_UF (25 ' +
        'ortografias divergentes mapeadas, ex: Brazópolis-MG ↔ ' +
        'BRASOPOLIS-MG, Itapajé-CE ↔ ITAPAGE-CE) — UF-aware para evitar ' +
        'colisões como "Santa Terezinha" em PE/SC/MT/BA. Substituição da ' +
        'malha coords_municipios (Atlas CSV ausente + 5570 chamadas API ' +
        'shapely) pela malha geobr canônica IBGE 2020 elimina dependência ' +
        'externa frágil.',
      pendencias: [
        'pytest_test_pbf_municipal.py ausente — gap principal vs A: cobrir (a) silver muni mes (regra nov/2021 + Ano de competência), (b) gold muni df (joins dimensionais sem null-blow), (c) match IBGE↔CGU (regra UF-aware + NAME_FIX_UF cobrindo as 25 divergências catalogadas)',
        'CI workflow específico do WP#7 ausente — pipelines/.databricks/bundle/dev/ existe mas job_pbf_municipios_pipeline ainda é manual (não roda em CI no push)',
        'ARCHITECTURE.md específico do WP#7 ausente — manuscrito tem seção 2.2 ("Arquitetura medallion") mas falta documentação técnica auto-contida no repo, com ADRs Nygard ao estilo do WP#6',
        'verify-reproducibility.yml não cobre WP#7 — gap declarado pelo Conselheiro de Eng. Software no audit cross-WP de 2026-04-27',
      ],
      sugestao_para_subir_pra_a:
        'pytest sobre o silver/gold + ARCHITECTURE.md específico do WP#7 + ' +
        'job_pbf_municipios_pipeline rodando em CI no push (não só manual). ' +
        'Análoga à "única ação que muda o jogo" do WP#6 (Zenodo DOI), mas ' +
        'no WP#7 a virada é teste automatizado da transformação, não ' +
        'apenas do artefato.',
    },
    {
      cadeira: 'design',
      titulo: 'Conselheira de Design, Information Visualization & UX',
      lente: 'Tufte (data-ink) · Norman (affordance) · Bostock (interatividade)',
      score: { tipo: 'letra', letra: 'B', pontos: 2.0 },
      veredicto: 'APROVADO no limiar — borderline',
      epigrafe:
        '"As figuras estáticas SÃO editorialmente sólidas. O vertical web É ' +
        'FUNCIONAL. Mas há gaps específicos versus a régua mestrado: zero ' +
        'interatividade Vega-Lite, audit Lighthouse não declarado, e ' +
        'detalhes de polylabel/halo ausentes em algumas figs."',
      argumento_central:
        'Identidade visual editorial preservada — apply_mirante_style + ' +
        'editorial_title + source_note usados em todas as 15 figuras. ' +
        'Tipografia Lato + paleta hierárquica + golden_figsize. Nada de ' +
        'chartjunk. 5 mapas coropléticos com paletas distintas colorblind-' +
        'safe (magma_r densidade demográfica log; YlOrRd PBF per capita; ' +
        'cividis_r cobertura PBF; Greys log valor absoluto; viridis_r ' +
        'crescimento real) — escolha tecnicamente correta de paletas para ' +
        'cada dimensão semântica. Mapa bivariado tratamento × IDH-M (fig08 ' +
        'no WP#2 — replicado aqui em estrutura municipal) usa paleta Joshua ' +
        'Stevens 3×3 — escolha certa pra duas dimensões simultâneas. ' +
        'Decomposição Theil em painéis duais entrega a leitura em dois ' +
        'níveis sem sobrecarregar. Vertical web responsivo usa Panel/' +
        'KpiCard/PageHeader consistente com WP#2; ScopeToggle (Estadual/' +
        'Municipal tabs) é UX claro.',
      pendencias: [
        'fig09 need-ratio sem adjustText — labels de munis sobrepõem-se em densidade alta. Aplicar adjust_text como no WP#2 fig10 penetracao',
        'Figs sem halo branco em labels — path_effects.withStroke ausente em fig04 e fig05; pelo menos as 5 capitais com maior PBF/hab deveriam ter labels com halo',
        'Sem polylabel em fig04 e fig09 — labels horizontais centralizados nas barras seriam mais legíveis com polylabel offset',
        'Vertical web SEM Vega-Lite interativo — top/bottom 20 são listas estáticas. Para subir a B+, transformar em scatter Vega-Lite interativo (filtrar por UF, hover detalhes). É padrão das outras verticais (BrazilMap, EvolutionBar)',
        'Sem audit Lighthouse/WCAG — não tem prova de Performance/Accessibility/SEO scores. Para A, rodar Lighthouse e mostrar 95+/95+/95+',
        'Galeria de figuras com placeholders 📊 emoji em vez de PNGs reais — embed real seria afirmação de qualidade',
      ],
      sugestao_para_subir_pra_a:
        '(a) polylabel + adjustText + halo nas figs 4, 5, 9 (1-2 dias); ' +
        '(b) substituir top/bottom listas por scatter Vega-Lite interativo ' +
        '(1 semana); (c) rodar Lighthouse e adicionar selo de score no ' +
        'rodapé (1 dia); (d) embed PDF/PNG inline na Galeria substituindo ' +
        'placeholder emoji (algumas horas).',
    },
    {
      cadeira: 'administrador',
      titulo: 'Conselheiro de Administração, Estratégia & Aplicação Prática',
      lente: 'Sinek (WHY) · Harari (escala histórica) · Carrey (ousadia)',
      score: { tipo: 'letra', letra: 'B+', pontos: 2.5 },
      veredicto: 'APROVADO',
      epigrafe:
        '"Este paper passa o teste do \'isso aqui pode dar dinheiro?\' mais ' +
        'claramente que o WP#2 — não pelo paper isolado, mas pelo que o ' +
        'paper PROVA: a viabilidade de migração metodológica para ' +
        'granularidade municipal usando exclusivamente dados públicos."',
      argumento_central:
        'WHY duplo bem formulado. Lente 1 (Robustez identificacional): o ' +
        'paper se posiciona como resposta direta a uma falha técnica ' +
        'nomeada do WP#2. Sinek puro (Golden Circle WHY-HOW-WHAT): ' +
        '"existimos para resolver o gargalo de N=27 que invalida wild-' +
        'cluster bootstrap em estudos brasileiros sobre programas sociais". ' +
        'WHY com inimigo nomeado, não genérico. Lente 2 (Heterogeneidade ' +
        'intra-UF revelada): a decomposição Theil within/between é o ' +
        'argumento de venda concreto para gestores e jornalistas — "a ' +
        'média estadual esconde 5–10× de variação interna" é uma frase que ' +
        'pega. Aplicações que monetizam: (1) consultoria CGU/MDS — pipeline ' +
        '+ manuscrito é template para auditorias municipais a baixíssimo ' +
        'custo; (2) jornalismo de dados municipalista — vertical web ' +
        'entrega top/bottom 20 munis filtrável por UF; (3) pesquisadores ' +
        'em Saúde Coletiva e Ciência Política — os 5 cadernos Python locais ' +
        'são plug-and-play, replicáveis em DEZENAS de outros programas ' +
        '(Auxílio Gás, BPC, Pé-de-Meia, Auxílio Reconstrução RS); (4) ' +
        'treinamento técnico — sequência ingest→silver→gold→export é ' +
        'didática e tem valor pedagógico.',
      perguntas_criticas: [
        'Onde está a cobertura PR/Twitter? O paper resolve um problema técnico específico — quantos potenciais leitores SABEM que existe um problema chamado "few clusters bootstrap convergence"? Sem evangelização do CONTEXTO, o paper fica num nicho',
        'A vertical web está sendo usada para gerar leads? DownloadActions tem PDF/tex/Overleaf, mas falta CTA forte tipo "Quer aplicar isso ao seu programa? leonardochalhoub@gmail.com" no rodapé. O paper é bom mas não converte',
        'Por que isso não é um curso? Existe potencial de transformar pipeline + manuscrito em curso prático "Análise causal espacialmente robusta para programas sociais brasileiros" — Hotmart/Coursera. Receita recorrente',
        'Qual SES estadual ou TCE municipal já está usando o pipeline? Sem caso de uso REAL com gestor público (não self-citation), continua demonstração — não impacto',
      ],
      sugestao_para_subir_pra_a:
        '(a) caso de uso REAL com gestor público — relatório de auditoria ' +
        'do TCE-MG ou CGU usando o pipeline; (b) monetização explícita: ' +
        'curso/consultoria/paid newsletter sobre o tema (Hotmart/Coursera); ' +
        '(c) plano de marketing técnico explícito no próximo trimestre — ' +
        'thread no Twitter/LinkedIn cobrindo o WHY duplo + casos de uso.',
    },
  ],

  resposta_do_autor: {
    decisao: 'aprovado, próximas iterações em roadmap explícito',
    data: '2026-04-27',
    commit: '8aa1edf',
    nota:
      'Maior média do projeto até hoje (2,375). Nenhuma cadeira reprovou; ' +
      'todas as 4 cruzaram o limiar 2,0. As pendências mais críticas serão ' +
      'tratadas em iteração v2.1: kernel Bartlett (Finanças) + pytest sobre ' +
      'silver/gold (Eng. Software) + scatter Vega-Lite interativo (Design) ' +
      '+ caso de uso real com gestor público (Administração). RDD geográfico ' +
      'em fronteiras estaduais e outcomes proxy mensais ficam para v2.2 — ' +
      'são gaps de tier doutorado, não de aprovação mestrado. v2.0 está ' +
      'liberada para circulação como demonstração metodológica completa.',
    score_pos_aprovacao: 'B+ (2,5) na régua mestrado · média conselho 2,375',
  },
};

// ═══════════════════════════════════════════════════════════════════════
// REUNIÃO #5 — WP#9 v2.0 (O Cálculo Ausente · 200 anos · 10 países + IB)
// Data: 2026-04-29 · 4 pareceres iniciais paralelos · APROVADO NO LIMIAR
// Histórico: WP de natureza atípica para o Conselho — primeira vez que
// um paper de revisão sistemática + comparada curricular standalone (não
// pipeline sobre microdados) é avaliado. Material-base: parecer pré-
// Conselho do Professor (TEACHER_PERSONA, IA Claude Opus 4.7 modo
// Mestrado/Doutorado), score B (2,0). As 4 cadeiras deliberaram a partir
// dessa base sob suas lentes próprias. Média (B 2,0 + B 2,0 + B 2,0) / 3
// = 2,000 — EXATAMENTE no limiar 2,0. Cadeira de Administração não
// atribui score numérico (parecer qualitativo: "TEM COMO — depende do
// autor decidir se quer ser pesquisador OU agente de mudança").
// Convergência das 4 lentes: paper sólido como advocacy, fechado em B
// pelas 3 cadeiras quants por razões COMPLEMENTARES — não pelos mesmos
// gaps. Eng. Software: reprodutibilidade técnica do levantamento
// curricular. Finanças: experimentos naturais não explorados (Reforma
// Benjamin Constant 1890→1925 é ITS clara) + PISA proxy invertido +
// custo sem IC. Design: zero figuras com identidade visual Mirante.
// Administração: ousadia de aplicação ausente (paper teórico, produto
// pronto). VEREDICTO: APROVADO COM AJUSTES — APROVADO NO LIMIAR.
// ═══════════════════════════════════════════════════════════════════════
export const ATA_WP9_REUNIAO_5 = {
  meta: {
    reuniao: 5,
    artigo: 'WP#9 v2.0 — O Cálculo Ausente · 200 anos de currículo · 10 países + IB',
    artigo_titulo_completo:
      'O Cálculo Ausente: duzentos anos de currículo, dez países de comparação, ' +
      'um vácuo estrutural — análise comparativa do currículo de matemática do ' +
      'ensino médio em dez países e suas implicações para a formação em ' +
      'engenharia no Brasil',
    commit: 'a78bd25 (.tex) + 5c7b00f (vertical) + 35474f7 (R1)',
    data: '2026-04-29',
    coautoria: 'Leonardo Chalhoub (autor único)',
    rodadas: 2, // R1 dentro de mestrado + R2 recalibração para lato sensu
    status: 'APROVADO — régua recalibrada para LATO SENSU 8,0/10',
    media_quants: 2.0, // R1 dentro de mestrado: (B 2,0 + B 2,0 + B 2,0) / 3
    limiar_aprovacao: 2.0,
    score_final: 'LATO SENSU 8,0/10 — pós-recalibração R2',
    nota_promocao:
      'Primeira reunião do Conselho sobre WP de natureza não-pipeline ' +
      '(revisão sistemática + comparada curricular standalone). RODADA 1: ' +
      'as 4 cadeiras deliberaram dentro da régua MESTRADO já dada pelo ' +
      'parecer pré-Conselho do Professor e confirmaram B (2,0) — média ' +
      '2,0 EXATA. RODADA 2 (recalibração honesta após cobrança do autor): ' +
      'o autor questionou se a régua mestrado era apropriada ("achei que ' +
      'era só graduação"). Reauditoria explícita contra a convenção Mirante ' +
      '(linhas 14-21 de pareceres.js: trabalhos INICIAM em lato sensu e só ' +
      'sobem se EXTRAPOLAREM o teto) revelou viés de ancoragem na R1 — a ' +
      'régua mestrado foi assumida por analogia aos demais WPs do projeto, ' +
      'que TÊM dados primários (PBF 2,5 bi linhas) e identificação causal ' +
      '(DiD/TWFE/Conley HAC). WP#9 não tem nem tenta ter; é deliberadamente ' +
      'revisão. Régua corrigida para LATO SENSU 8,0/10. As críticas ' +
      'substantivas das 4 cadeiras permanecem válidas e viram roadmap ' +
      'lato sensu → mestrado.',
  },

  pareceres_iniciais: [
    {
      cadeira: 'eng-software',
      titulo: 'Conselheiro de Engenharia de Software & Plataforma de Dados',
      lente: 'Reprodutibilidade · auditabilidade · ADRs · CI/CD · versionamento de fonte primária',
      score: { tipo: 'letra', letra: 'B', pontos: 2.0 },
      veredicto: 'APROVADO COM AJUSTES — limiar',
      epigrafe:
        '"O paper é sólido como advocacy curricular e como survey comparado, ' +
        'mas carece de auditabilidade automatizada do claim central e de ' +
        'versionamento dos dados primários. B é o teto até que o levantamento ' +
        'curricular seja auditável por pipeline, não por leitura manual."',
      argumento_central:
        'Reprodutibilidade do argumento central é alta para o gênero — cada ' +
        'um dos 10 países tem pelo menos uma referência a documento ' +
        'curricular oficial (MOE Singapore, SEAB 9758, NRW Zentralabitur, ' +
        'MEXT Japan via JASSO/EJU, OECD PISA Vol. I), substancialmente ' +
        'superior à média do campo (revisões em B2 que citam Wikipedia). ' +
        'CI/CD compila o paper via xu-cheng/latex-action no deploy-pages.yml. ' +
        'Honestidade epistêmica explicitada na Seção 3 (currículo prescrito ≠ ' +
        'currículo praticado, inferências causais "plausíveis, não ' +
        'demonstradas"). MAS: o claim "Brasil é o único" depende de leitura ' +
        'manual dos 10 documentos curriculares; qualquer erro de leitura é ' +
        'indetectável. Os 47+ documentos primários são linkados via URLs ' +
        'vivas — três deles (MOE Singapore, SEAB 9758, ministérios europeus) ' +
        'têm risco concreto de link rot em 2–3 anos. Para WPs sobre ' +
        'microdados, isso é menos crítico porque os dados ficam no Delta. ' +
        'Aqui, os dados SÃO os documentos curriculares.',
      pendencias: [
        'Auditoria do achado central não é automatizada — sem script pdftotext + grep nos PDFs curriculares; achado auditável por terceiros em 4h por país (não acontece) em vez de 10 minutos com pipeline',
        'Sem ARCHITECTURE.md nem ADR documentando a decisão de aceitar WPs sem pipeline Databricks — escopo da plataforma fica indefinido para futuros WP#10+ não-pipeline',
        'Versionamento dos documentos curriculares consultados é frágil — 47+ links vivos sem snapshot Wayback nem DVC-tracked PDFs locais',
        'Botão "Ler artigo na tela" ausente no Calculo.jsx — violação de feedback_article_buttons.md (convenção de plataforma)',
        'Nenhum teste de sanidade automatizado sobre as 10 tabelas ano-a-ano — qualquer regressão de edição passa silenciosa',
      ],
      sugestao_para_subir_pra_a:
        'scripts/audit_curricula_keywords.py rodando pdftotext + frequency ' +
        'analysis nos 11 PDFs (BNCC + 10 estrangeiros) commitado e CI-' +
        'integrado + snapshot dos 47+ documentos primários (Wayback + ' +
        'arquivo local) + ADR Nygard documentando padrão "WP standalone" + ' +
        'pytest mínimo nos fixtures das 10 tabelas país × ano.',
    },
    {
      cadeira: 'financas',
      titulo: 'Conselheiro de Finanças & Métodos Quantitativos',
      lente: 'Identificação causal · RDD/IV/DiD/ITS · robustez estatística · IC formal',
      score: { tipo: 'letra', letra: 'B', pontos: 2.0 },
      veredicto: 'APROVADO COM AJUSTES — limiar',
      epigrafe:
        '"O paper identifica os experimentos naturais e não os explora. Tratar a ' +
        'Reforma Benjamin Constant como contexto narrativo e não como potencial ' +
        'ITS é a principal oportunidade perdida. Mas a honestidade declarativa ' +
        'sobre os limites é rara — em 30 anos de peer review li centenas de ' +
        'revisões narrativas que jamais fazem essa distinção."',
      argumento_central:
        'O paper faz algo intelectualmente honesto: declara explicitamente ' +
        '(Seção 9, Três Níveis de Robustez) que o Nível 3 — inferência causal ' +
        '— tem "robustez moderada". Isso eleva o piso. MAS: a Reforma Benjamin ' +
        'Constant (Decreto 981/1890 incluiu cálculo no secundário; Decreto ' +
        '3.890/1901 o removeu, com a morte do ministro como choque exógeno ao ' +
        'desempenho matemático) é descontinuidade institucional com data ' +
        'precisa, exógena ao outcome, e com consequência mensurável 30 anos ' +
        'depois nas coortes da Politécnica/EPUSP. Atas de admissão existem em ' +
        'arquivo histórico — está literalmente na Seção 6 do próprio paper. ' +
        'Tratar isso como contexto e não como ITS é a maior perda. Singapura ' +
        '1981 (Singapore Math) também é janela DiD natural com k~10 países e ' +
        'T~4 ciclos PISA. PISA é proxy do output, não do input — alunos PISA ' +
        'têm 15 anos, ANTES do cálculo em qualquer país (Japão começa cálculo ' +
        'aos 16 no Math II); usar PISA como evidência do efeito da AUSÊNCIA ' +
        'de cálculo no EM é identificação invertida. Custo econômico Seção ' +
        '7.5 (R$2,3–4,6 bi/ano) tem spread 100% sem IC — em pricing isso é ' +
        'inaceitável.',
      pendencias: [
        'Reforma Benjamin Constant 1890→1925 nomeada como contexto mas não explorada como ITS — atas Politécnica/EPUSP/IME do período estão em arquivo histórico acessível',
        'PISA usado como evidência do efeito da ausência de cálculo no EM, mas PISA mede alunos de 15 anos — antes do cálculo em qualquer país. Identificação invertida',
        'Estagnação PISA 2003–2022 atribuída a vácuo curricular sem controlar PIB per capita, gasto por aluno, desigualdade — Singapura/Coreia/Japão são também muito mais ricos',
        'Custo econômico R$2,3–4,6 bi/ano com spread de 100% sem IC bootstrap; três parâmetros (taxa reprovação, volume matrículas, custo por disciplina) multiplicados sem decomposição da variância',
        'Lei 13.415/2017 (Novo EM) permite cálculo nos itinerários formativos — variação cross-estado disponível via SAEB, não verificada',
        'CONFEA "déficit de 1 milhão" citado sem auditoria da metodologia da projeção',
      ],
      sugestao_para_subir_pra_a:
        'ITS sobre Reforma Benjamin Constant 1890→1925 com atas da ' +
        'Politécnica/EPUSP (mesmo rudimentar, mesmo com dados limitados) + ' +
        'DiD cross-country sobre Singapore Math 1981 / Coreia Sul / outras ' +
        'reformas curriculares datadas + reconhecer formalmente PISA como ' +
        'proxy inadequado do canal causal específico + IC bootstrap sobre o ' +
        'custo econômico. Qualquer dos três sobe para B+; os três juntos = A.',
    },
    {
      cadeira: 'design',
      titulo: 'Conselheira de Design, Information Visualization & UX',
      lente: 'Tufte (data-ink) · Norman (affordance) · Bostock (interatividade)',
      score: { tipo: 'letra', letra: 'B', pontos: 2.0 },
      veredicto: 'APROVADO COM AJUSTES — major revision em Design',
      epigrafe:
        '"newtx + ABNT é correto. Os boxes fbox da Seção 8 são funcionais — não é ' +
        'design, é recurso LaTeX de emergência. Zero figuras com identidade visual ' +
        'Mirante não é violação (regra não retroativa) mas é o gatekeeper de B+. ' +
        'Mantém B do Professor por razão diferente: argumento textual de qualidade, ' +
        'integridade epistêmica, zero distorção visual — e zero contribuição visual."',
      argumento_central:
        'Tipografia newtx + ABNT adequada. Hierarquia bfseries + uppercase + ' +
        'titlespacing funciona. Tabelas booktabs sem linhas verticais com ' +
        'data-ink ratio decente. ContextSection do Calculo.jsx explicando "por ' +
        'que não tem dashboard" é decisão acertada — melhor explicar a ausência ' +
        'do que não explicar. 4 botões DocSection seguem feedback_article_' +
        'buttons.md MENOS o "Ler artigo na tela" (rótulo está como "Ler artigo ' +
        '(PDF)" — gap de consistência). MAS: os 6 \\fbox{\\parbox{...}} da ' +
        'Seção 8 (boxes comparativos: Gaokao, Abitur, Baccalauréat, AP Calc BC, ' +
        'H2 Math, ENEM) são 6 itens que o leitor processa linearmente; carga ' +
        'cognitiva alta. Categorical heatmap país × dimensões cognitivas ' +
        '(limites · derivadas · integrais · EDO · séries · geometria diferencial) ' +
        'reduz tempo de compreensão de "ler 6 parágrafos" para "scan de 6 ' +
        'segundos". Para B+: 1 figura obrigatória (heatmap 11×6 com Brasil ' +
        'highlighted vermelho); para consolidar B+: 2 figuras (acrescenta ' +
        'série temporal PISA com banda OECD). Vega-Lite inline na vertical ' +
        'web é oportunidade sub-explorada — dado tabular já está no .tex.',
      pendencias: [
        'Zero figuras com identidade visual Mirante (Lato + Wong palette + golden ratio + halo + leader lines) — gatekeeper de B+',
        'Boxes fbox da Seção 8 são recurso LaTeX de emergência — cabia heatmap síntese país × tópico cálculo no lugar OU ao lado',
        'Rótulo do botão primário "Ler artigo (PDF)" deveria ser "Ler artigo na tela" (feedback_article_buttons.md)',
        'Calculo.jsx sem Vega-Lite inline para PISA 2003–2022 — dado tabular existe no .tex, 20 linhas JSON resolveriam',
        'Lighthouse audit da rota /calculo não declarado — risco de contraste WCAG quando interatividade for adicionada',
        'Conflito de interesse não declarado: Seção 10.3 cita o Clube da Matemática (URL do autor) como iniciativa de educação aberta — em submissão a periódico externo (Bolema, ZDM) o revisor questionará advocacy do projeto do próprio autor',
      ],
      sugestao_para_subir_pra_a:
        '(a) HEATMAP 11×6 país × tópico cálculo no Mirante style: Lato + ' +
        'Wong + halo + Brasil em vermelho — 1 figura única que vira a chave; ' +
        '(b) série temporal PISA 2003–2022 com Brasil destacado e banda OECD; ' +
        '(c) Vega-Lite inline da PISA na vertical web; (d) Lighthouse 95+/95+/' +
        '95+ na /calculo; (e) declaração de CoI sobre Clube da Matemática.',
    },
    {
      cadeira: 'administrador',
      titulo: 'Conselheiro de Administração, Estratégia & Aplicação Prática',
      lente: 'Sinek (WHY) · Harari (escala histórica · pós-verdade × cargo cult × mudança) · Carrey (ousadia)',
      score: { tipo: 'qualitativo', letra: null, pontos: null },
      veredicto: 'TEM COMO — depende do autor decidir se quer ser pesquisador OU agente de mudança',
      epigrafe:
        '"O paper está 80% do caminho para virar produto. O Clube da Matemática ' +
        'já existe, o WHY já está documentado, o benchmark internacional já está ' +
        'feito, o arcabouço pedagógico (Bruner/Vygotsky/Rezende) já está lá. O ' +
        'único insumo faltante é a decisão. Pode dar dinheiro mais rápido do que ' +
        'qualquer outro WP do projeto."',
      argumento_central:
        'WHY (Sinek): existe e é robusto. "Brasil é exceção global e isso custa ' +
        'R$2–5 bi/ano em repetência e 1 milhão de engenheiros que não vão ' +
        'existir" conecta com o sistema límbico. A frase final da conclusão — ' +
        '"O Brasil é exceção curricular. Não precisa continuar sendo." — é ' +
        'destilação em sete palavras. MAS: o WHY vive na capa e na conclusão; ' +
        'some por 50 páginas no meio. Escala histórica (Harari): o recorte de ' +
        '200 anos é substancialmente original — Reforma Benjamin Constant ' +
        '(1890–1925) é fato verificável em decreto federal que a maioria dos ' +
        'educadores brasileiros desconhece. Resiste ao teste de pós-verdade ' +
        '(35 anos de literatura citada, Rezende 2003 com 486 citações, BNCC ' +
        'verificável, PISA série histórica oficial). Não é cargo cult. Ousadia ' +
        '(Carrey): aqui está o gap principal. O autor domina o material, ' +
        'acredita no WHY, já construiu o Clube da Matemática — e o paper está ' +
        'sendo MAIS CAUTELOSO do que o problema merece. Tudo que é necessário ' +
        'para lançar o produto educacional já está fundamentado. O risco de ' +
        'não monetizar é igual ao risco de fazer.',
      ideias_concretas: [
        'Curso pago Hotmart/Eduzz "Cálculo para o ENEM e além" — R$97–197 com 40–60 aulas alinhadas a AP Calculus AB + Bruner. Mercado cursinhos online BR ~ R$3–4 bi/ano',
        'Parceria B2B com Descomplica/Stoodi/Poliedro: white-label do Clube + credencial WP#9. Contratos de R$50–150k/plataforma/ano',
        'Palestra paga ABENGE/CONFEA — R$5–15k/evento; CONFEA já organizou evento citado no paper',
        'Submissão Bolema (UNESP) + press release Nexo/Folha Educação — credencial acadêmica + distribuição público qualificado',
        'Consultoria Secretarias Estaduais (SP/MG/RS têm autonomia complementar à BNCC) — R$40–80k/estado para diagnóstico + plano + formação docente',
        'REA/OER via edital MEC/CAPES — Clube já existe como base; editais R$100–500k regulares',
        'Livro paradidático "Por que o Brasil não ensina Cálculo?" (Contexto/Autêntica) — adiantamento R$5–20k + royalties; Seção 8 do WP é ouro para esse formato',
      ],
      perguntas_criticas: [
        'O Clube da Matemática já existe — por que o curso pago ainda não existe? O que está impedindo: tempo, dinheiro, medo de virar comercial, ou sensação de que o paper precisa estar "pronto"?',
        'O paper documenta que SENGE-RJ discorda da narrativa do "apagão" ("é apagão de condições, não de profissionais"). Você tomou partido ou ficou em cima do muro? Vai ter que tomar partido para palestra/consultoria',
        'O contra-argumento C2 ("não há professores qualificados") é o mais forte empiricamente — mas o Clube é educação direta ao aluno, não formação docente. Você está resolvendo o problema certo para o canal que controla?',
        'Por que não incluir um país da América Latina (Argentina, Chile, México) no recorte? Sem contrafactual regional, o argumento pode ser atacado como cherry-picking de países ricos',
        'A Seção 10 recomenda 5 tópicos conservadores para o 3º ano do EM. Você está preparado para defender publicamente em audiência do CNE — com oposição de professores sindicalizados, editoras de didático e secretarias com orçamento travado?',
      ],
      pode_dar_dinheiro:
        'SIM — e mais rápido do que os outros WPs. Outros dependem de pipeline ' +
        'Databricks + microdados + identidade visual + submissão a periódico de ' +
        'econometria. Este não. Produto educacional (curso + paradidático) sai ' +
        'em 3–6 meses com o que já existe. TAM = ~200k/ano só nos vestibulares ' +
        'das federais. Caminho curto: Hotmart + parceria cursinho, R$100–300k ' +
        'no ano 1. Caminho de impacto médio prazo: consultoria B2G a Sec.Educação.',
    },
  ],

  // ── Rodada 2 — Recalibração honesta de régua ───────────────────────
  // Motivada por cobrança direta do autor após R1: "achei que era só
  // graduação". Documentada como lição de processo para o framework
  // editorial-crítico do Mirante (auditável publicamente). Mantida na
  // ata para que viés de ancoragem fique exposto, não escondido.
  rodada_2_recalibracao: {
    contexto:
      'Após a R1 fechar com média B (2,0) em régua mestrado, o autor ' +
      'do projeto questionou diretamente: "achei que era só graduação". ' +
      'O Conselho reauditou a régua aplicada contra a convenção Mirante ' +
      '(pareceres.js linhas 14-21: trabalhos INICIAM em lato sensu e só ' +
      'sobem se EXTRAPOLAREM o teto). A reauditoria revelou VIÉS DE ' +
      'ANCORAGEM na R1: a régua mestrado foi assumida por analogia aos ' +
      'demais WPs do projeto, sem auditar se WP#9 efetivamente extrapola ' +
      'lato sensu. Não extrapola — WP#9 é deliberadamente revisão ' +
      'sistemática + comparada, sem dados primários nem identificação ' +
      'causal nem contribuição metodológica original.',
    diagnostico_do_vies:
      'Os demais WPs do projeto (WP#2 PBF, WP#4 Equipamentos RM, WP#6 ' +
      'Panorama, WP#7 BF Municípios) têm bilhões de linhas em bronze e ' +
      'identificação causal explícita (DiD/TWFE/Conley HAC). O Professor ' +
      'do parecer pré-Conselho enquadrou WP#9 na mesma régua sem ' +
      'auditar se o trabalho EXTRAPOLA lato sensu — apenas presumiu ' +
      'continuidade de régua. As 4 cadeiras da R1 deliberaram DENTRO ' +
      'desse frame e confirmaram B por consenso. Confirmação dentro de ' +
      'viés é confirmação ainda assim — mas não é validação independente ' +
      'da régua. A R2 corrige.',
    regua_corrigida: {
      nivel: 'lato_sensu',
      score_numerico: 8.0,
      teto_lato_sensu: 9.0,
      justificativa:
        'Sólido como revisão sistemática: 47+ refs verificáveis, 10 países + ' +
        'IB, 200 anos de história curricular brasileira, marco pedagógico ' +
        'bem fundamentado, ABNT impecável, honestidade epistêmica explícita. ' +
        'No meio-teto lato sensu (8,0/9,0). Para extrapolar pra mestrado ' +
        'seriam necessárias contribuições originais — vide roadmap.',
    },
    como_ficaria_em_outras_reguas: [
      { regua: 'Mestrado A/B+/B/C/D', estimativa: 'C (1,0) ou D (0)', motivo: 'REPROVA — ausência de contribuição metodológica original, requisito mínimo de mestrado' },
      { regua: 'Lato sensu 0–10',     estimativa: '8,0/10',           motivo: 'APROVA — sólido como monografia de especialização/MBA; régua correta' },
      { regua: 'Graduação TCC 0–10',  estimativa: '9,5/10',           motivo: 'APROVA com louvor — TCC excepcional; convenção Mirante padroniza lato sensu como default' },
    ],
    licao_de_processo:
      'Para futuros WPs do Mirante: o parecer do Professor (TEACHER_PERSONA) ' +
      'DEVE auditar a régua antes de atribuir score, não presumir continuidade ' +
      'com WPs anteriores. Heurística: "este trabalho EXTRAPOLA o teto lato ' +
      'sensu? Tem dados primários, identificação causal OU contribuição ' +
      'metodológica original?" Se NENHUMA das três, fica em lato sensu. ' +
      'Documentação dessa lição é em si contribuição ao framework editorial-' +
      'crítico do projeto — exatamente o tipo de meta-artefato que pode virar ' +
      'publicação metodológica futura ("peer review interno reprodutível com ' +
      '4 personas IA").',
    pareceres_iniciais_permanecem_validos:
      'IMPORTANTE: as CRÍTICAS substantivas das 4 cadeiras na R1 ' +
      'permanecem válidas e migram para o roadmap lato sensu → mestrado. ' +
      'Eng. Software (auditoria automatizada do achado central + ' +
      'snapshots dos docs primários + ADR), Finanças (ITS sobre Reforma ' +
      'Benjamin Constant + IC bootstrap sobre custo + reconhecer PISA ' +
      'como proxy invertido), Design (heatmap síntese país × cálculo + ' +
      'declaração CoI sobre Clube da Matemática), Administração ' +
      '(decisão pesquisa-vs-produto). O QUE MUDA: a meta dessas ' +
      'pendências passa de "subir B → B+ no mestrado" para "extrapolar ' +
      'lato sensu para subir a régua mestrado". Implementar as 4 + ' +
      'adicionar uma contribuição metodológica original = trabalho ' +
      'extrapola lato sensu e abre R3 do Conselho em régua mestrado.',
  },

  resposta_do_autor: {
    decisao: 'APROVADO em LATO SENSU 8,0/10 — pós-recalibração R2',
    data: '2026-04-29',
    commit: 'pendente (próximo ciclo)',
    nota:
      'R1 fechou em B mestrado (média 2,0 exata). Após cobrança honesta ' +
      'do autor, R2 reauditou a régua e corrigiu para lato sensu 8,0/10 — ' +
      'sólido, no meio-teto, sem extrapolar. As críticas substantivas das ' +
      '4 cadeiras permanecem como roadmap lato → mestrado: (a) HEATMAP ' +
      '11×6 país × tópico cálculo no Mirante style; (b) ITS sobre Reforma ' +
      'Benjamin Constant 1890→1925; (c) script audit_curricula_keywords.py; ' +
      '(d) snapshot dos 47+ docs primários; (e) declaração de Conflito de ' +
      'Interesse sobre Clube da Matemática; (f) IC bootstrap sobre custo ' +
      'econômico. Implementar 4 desses + adicionar contribuição metodológica ' +
      'original = extrapola lato sensu, abre R3 em régua mestrado. Decisão ' +
      'estratégica (Administração) sobre pesquisa-vs-produto fica em aberto ' +
      'explícito; caminhos paper + curso + advocacy não são mutuamente ' +
      'exclusivos.',
    score_pos_aprovacao: 'LATO SENSU 8,0/10 (régua corrigida pós-R2) · sólido, no meio-teto · APROVADO',
  },
};

// ─── Lookup helper ───────────────────────────────────────────────────────
export const ATAS_BY_ARTIGO = {
  'wp4-equipamentos-rm-parkinson':   ATA_WP4_REUNIAO_1,
  'wp6-equipamentos-panorama-cnes':  ATA_WP6_REUNIAO_2,
  'wp2-bolsa-familia':               ATA_WP2_REUNIAO_1,
  'wp7-bolsa-familia-municipios':    ATA_WP7_REUNIAO_1,
  'bolsa-familia-municipios':        ATA_WP7_REUNIAO_1,
  'wp9-calculo-ensino-medio':        ATA_WP9_REUNIAO_5,
  'calculo-ensino-medio-internacional': ATA_WP9_REUNIAO_5,
};

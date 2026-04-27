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

// ─── Lookup helper ───────────────────────────────────────────────────────
export const ATAS_BY_ARTIGO = {
  'wp4-equipamentos-rm-parkinson': ATA_WP4_REUNIAO_1,
};

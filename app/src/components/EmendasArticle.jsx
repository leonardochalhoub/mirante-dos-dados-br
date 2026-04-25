// Artigo acadêmico completo sobre Emendas Parlamentares.
// Estilo: padrão FGV/RBFin/RAP — título bilíngue, Resumo+Abstract, seções numeradas,
// referências em ABNT. Renderizado dentro do toggle "Ver artigo completo" do Emendas.jsx.

export default function EmendasArticle() {
  return (
    <article className="article">

      <header className="article-header">
        <div className="article-meta">
          <span className="article-meta-item">Mirante dos Dados</span>
          <span className="article-meta-sep">·</span>
          <span className="article-meta-item">Working paper</span>
          <span className="article-meta-sep">·</span>
          <span className="article-meta-item">Versão 1.0 — abril de 2026</span>
        </div>

        <h1 className="article-title">
          Emendas Parlamentares no Orçamento Federal Brasileiro (2014–2025):
          distribuição espacial, execução orçamentária e efeitos das mudanças
          institucionais recentes
        </h1>

        <h2 className="article-title-en">
          Brazilian federal parliamentary amendments (2014–2025):
          spatial distribution, budget execution, and the effects of recent
          institutional reforms
        </h2>

        <div className="article-author">
          <div className="article-author-name">Leonardo Chalhoub</div>
          <div className="article-author-affiliation">
            Pesquisador independente · Engenharia de dados aplicada à transparência fiscal<br />
            <a href="mailto:leonardochalhoub@gmail.com">leonardochalhoub@gmail.com</a> ·
            <a href="https://github.com/leonardochalhoub" target="_blank" rel="noreferrer"> github.com/leonardochalhoub</a>
          </div>
        </div>
      </header>

      {/* ─── RESUMO ─────────────────────────────────────────────── */}

      <section className="article-abstract-block">
        <h3 className="article-abstract-label">Resumo</h3>
        <p className="article-abstract-body">
          Este artigo apresenta uma análise integrada da execução de emendas
          parlamentares federais brasileiras entre 2014 e 2025, a partir dos
          microdados do Portal da Transparência da Controladoria-Geral da União
          (CGU). Considerando a crescente importância dessas emendas no orçamento
          federal — superando R$&nbsp;50 bilhões anuais nas modalidades de execução
          obrigatória (RP6 individual e RP7 bancada estadual) — e o impacto das
          mudanças institucionais recentes (EC&nbsp;86/2015, EC&nbsp;100/2019,
          decisões do STF de 2022 sobre o RP9 e LC&nbsp;210/2024), o trabalho
          disponibiliza agregados por unidade federativa, ano e modalidade,
          deflacionados a preços de dezembro de 2021 (IPCA-BCB) e normalizados
          per capita (IBGE/SIDRA). O estudo combina contribuição metodológica —
          construção de pipeline de dados em arquitetura medallion (bronze, silver,
          gold) inteiramente open-source — e contribuição substantiva — caracterização
          empírica do crescimento das emendas após a impositividade,
          do ciclo do "orçamento secreto" via RP9 entre 2020 e 2022, e da
          desigualdade per capita entre unidades federativas. Os resultados sugerem
          que a impositividade ampliou de forma estatisticamente expressiva o volume
          executado, mas não eliminou as assimetrias regionais nem a sub-execução
          relativa em estados de menor representação política.
        </p>
        <p className="article-abstract-keywords">
          <b>Palavras-chave:</b> emendas parlamentares; transparência fiscal;
          execução orçamentária; orçamento público federal; controle social;
          gestão pública.
        </p>
      </section>

      <section className="article-abstract-block">
        <h3 className="article-abstract-label">Abstract</h3>
        <p className="article-abstract-body">
          This paper presents an integrated analysis of the execution of Brazilian
          federal parliamentary amendments between 2014 and 2025, based on the
          microdata of the Portal da Transparência maintained by the Office of
          the Comptroller General of the Union (CGU). Given the increasing weight
          of these amendments in the federal budget — exceeding R$&nbsp;50 billion
          annually in the mandatory-execution modalities (RP6 individual and RP7
          bancada estadual) — and the impact of recent institutional changes
          (Constitutional Amendments 86/2015 and 100/2019, the 2022 Supreme Court
          rulings on RP9, and Complementary Law 210/2024), this work provides
          aggregates by federative unit, year, and modality, deflated to December
          2021 prices (IPCA-BCB) and normalized per capita (IBGE/SIDRA). The study
          combines a methodological contribution — the construction of a fully
          open-source medallion-architecture data pipeline (bronze, silver, gold)
          — and a substantive contribution — empirical characterization of the
          growth of amendments after the introduction of mandatory execution, of
          the "secret budget" cycle via RP9 between 2020 and 2022, and of the
          per-capita disparities between federative units. Results suggest that
          mandatory execution significantly expanded the executed volume but did
          not eliminate regional asymmetries or the relative under-execution in
          less politically represented states.
        </p>
        <p className="article-abstract-keywords">
          <b>Keywords:</b> parliamentary amendments; fiscal transparency; budget
          execution; federal public budget; social control; public management.
        </p>
      </section>

      {/* ─── 1 INTRODUÇÃO ─────────────────────────────────────── */}

      <section className="article-section">
        <h2 className="article-h2">1. Introdução</h2>

        <p>
          As emendas parlamentares ao orçamento federal são, simultaneamente,
          um dos principais instrumentos de atuação do Poder Legislativo sobre
          a alocação de recursos públicos federais e um dos pontos de maior
          controvérsia do presidencialismo de coalizão brasileiro. Por meio
          delas, deputados federais e senadores alteram a proposta orçamentária
          do Executivo, redirecionando recursos para áreas e regiões específicas
          — saúde, educação, infraestrutura, cultura, assistência social.
          Conforme dados consolidados do Portal da Transparência (CGU), as
          modalidades de execução obrigatória — emendas individuais (RP6) e de
          bancada estadual (RP7) — superaram, em 2024, a marca de R$&nbsp;50
          bilhões em valores empenhados, montante equivalente ao orçamento
          de alguns dos maiores ministérios da Esplanada.
        </p>

        <p>
          Esse protagonismo orçamentário não é fenômeno antigo. Até a Emenda
          Constitucional nº&nbsp;86, de 17 de março de 2015, as emendas
          individuais possuíam caráter <i>autorizativo</i>: o Executivo decidia
          discricionariamente se executaria ou não cada emenda aprovada pelo
          Congresso, o que historicamente sustentou um padrão de relações
          Executivo–Legislativo amplamente caracterizado pela literatura como
          troca de apoio parlamentar por execução de emendas
          (PEREIRA; MUELLER, 2002; LIMONGI; FIGUEIREDO, 2005). A EC&nbsp;86/2015
          inaugurou um novo regime ao tornar <i>impositiva</i> a execução das
          emendas individuais, em montante equivalente a 1,2% da Receita
          Corrente Líquida (RCL), com obrigação de aplicar metade desse total
          em ações e serviços públicos de saúde. A EC&nbsp;100, de 26 de junho
          de 2019, estendeu o mesmo regime de impositividade às emendas de
          bancada estadual (RP7), adicionando 1% da RCL ao montante de execução
          obrigatória.
        </p>

        <p>
          Paralelamente, entre 2019 e 2022 consolidou-se uma modalidade
          conhecida como "emendas do relator-geral" (RP9), cuja distribuição
          opaca e ausente de critérios públicos passou a ser denunciada na
          imprensa e na literatura como "orçamento secreto" (VOLPATO, 2022).
          Em dezembro de 2022, o Supremo Tribunal Federal, no julgamento conjunto
          das ADPFs nº&nbsp;850, 851, 854 e 1014, declarou inconstitucional o
          mecanismo de RP9, determinando a publicidade dos beneficiários e o
          fim da modalidade. Mais recentemente, a Lei Complementar nº&nbsp;210,
          de 2024, regulamentou novas regras de transparência aplicáveis às
          emendas de bancada (RP7) e às emendas de comissão (RP8), em resposta
          à demanda do STF por critérios objetivos de rastreabilidade dos
          recursos.
        </p>

        <p>
          Apesar da centralidade do tema, há, no campo da Gestão Pública e
          da Ciência Política, uma persistente dificuldade de acesso integrado
          aos microdados de execução de emendas. O Portal da Transparência da
          CGU disponibiliza um arquivo consolidado anual (~30 MB compactado,
          ~250 MB descompactado), mas sua exploração demanda capacidade técnica
          de processamento e familiaridade com o esquema de dados orçamentários,
          o que limita o alcance da informação a um público especializado.
          Visualizações públicas existentes tendem a ser parciais, frequentemente
          restritas a uma única modalidade ou a um único exercício, e raramente
          incorporam ajustes metodológicos básicos como deflação para preços
          constantes ou normalização per capita.
        </p>

        <p>
          Este artigo busca contribuir para esse cenário em duas dimensões.
          Primeiro, por meio de uma <b>contribuição metodológica</b>: a
          construção de um pipeline de dados open-source, em arquitetura
          medallion, que processa os microdados da CGU desde a ingestão até a
          publicação em formato consumível por aplicações analíticas, garantindo
          reprodutibilidade e auditabilidade. Segundo, por meio de uma
          <b> contribuição substantiva</b>: análise empírica integrada da
          execução das emendas parlamentares federais entre 2014 e 2025, com
          ênfase em quatro dimensões — evolução temporal, distribuição
          geográfica por unidade federativa, taxa de execução
          (pago&nbsp;/&nbsp;empenhado) e composição por tipo de Resultado
          Primário (RP6/RP7/RP8/RP9). A análise é normalizada para preços de
          dezembro de 2021, com base no Índice de Preços ao Consumidor Amplo
          (IPCA, série BCB-SGS&nbsp;433), e por habitante, com base na população
          residente estimada (IBGE/SIDRA, tabela 6579).
        </p>

        <p>
          O artigo está organizado em seis seções, além desta introdução. A
          seção&nbsp;2 revisa o referencial teórico, abordando a tipologia das
          emendas parlamentares, os marcos institucionais relevantes e a
          literatura prévia sobre o tema. A seção&nbsp;3 apresenta a metodologia,
          detalhando as fontes de dados, a arquitetura do pipeline, os indicadores
          construídos e as limitações do estudo. A seção&nbsp;4 expõe os resultados
          empíricos. A seção&nbsp;5 discute as implicações dos achados à luz
          das mudanças institucionais analisadas. A seção&nbsp;6 apresenta as
          considerações finais e sugere uma agenda de pesquisa futura. Por fim,
          a seção&nbsp;de Referências traz o conjunto bibliográfico e as fontes
          oficiais consultadas, em padrão ABNT.
        </p>
      </section>

      {/* ─── 2 REFERENCIAL TEÓRICO ───────────────────────────── */}

      <section className="article-section">
        <h2 className="article-h2">2. Referencial Teórico</h2>

        <h3 className="article-h3">2.1 Conceito e tipologia das emendas parlamentares</h3>

        <p>
          A Constituição Federal de 1988, em seu artigo 166, atribui ao Congresso
          Nacional a prerrogativa de apresentar emendas ao projeto de Lei
          Orçamentária Anual (LOA) encaminhado pelo Poder Executivo. As emendas
          parlamentares constituem, portanto, o instrumento típico pelo qual o
          Legislativo intervém na alocação dos recursos públicos federais. A
          classificação operacional vigente baseia-se na figura do
          <i> Resultado Primário (RP)</i>, parâmetro técnico-orçamentário que
          identifica o ente proponente e o regime de execução aplicável.
          Atualmente, são reconhecidas quatro modalidades principais
          (CONGRESSO NACIONAL, [s.d.]):
        </p>

        <ul>
          <li>
            <b>RP6 — Emendas individuais.</b> Apresentadas individualmente por
            cada parlamentar, observado um teto fixo anual estabelecido em
            função da Receita Corrente Líquida (RCL). Em 2024, cada
            parlamentar dispôs de cota aproximada de R$&nbsp;30 milhões. Por
            força da EC&nbsp;86/2015, a execução é <b>obrigatória</b> em
            montante correspondente a 1,2% da RCL, observado o piso constitucional
            de aplicação em saúde de 50% sobre o total.
          </li>
          <li>
            <b>RP7 — Emendas de bancada estadual.</b> Definidas em conjunto
            pelos parlamentares de cada unidade federativa. Cada bancada elege,
            colegiadamente, projetos prioritários para o estado. A
            EC&nbsp;100/2019 estendeu a essa modalidade o regime de execução
            obrigatória, em montante adicional equivalente a 1% da RCL.
          </li>
          <li>
            <b>RP8 — Emendas de comissão.</b> Apresentadas pelas comissões
            permanentes do Congresso (Câmara, Senado e comissões mistas), em
            geral vinculadas a temas setoriais. A LC&nbsp;210/2024 regulamentou
            novas exigências de transparência aplicáveis a essa modalidade,
            em resposta às determinações do STF.
          </li>
          <li>
            <b>RP9 — Emendas do relator-geral.</b> Modalidade introduzida em
            2019, cujos recursos eram alocados sob coordenação do relator-geral
            do orçamento, sem critérios objetivos de distribuição publicamente
            divulgados, gerando o que veio a ser nomeado como "orçamento
            secreto". A modalidade foi declarada inconstitucional pelo Supremo
            Tribunal Federal em dezembro de 2022, no julgamento conjunto das
            ADPFs&nbsp;850, 851, 854 e 1014 (BRASIL, 2022).
          </li>
        </ul>

        <p>
          Importa notar que o conceito de "execução" envolve etapas
          intermediárias do processo orçamentário — <i>empenho</i>,
          <i> liquidação</i> e <i>pagamento</i> — cada uma associada a uma
          fase do ciclo de execução da despesa pública. O <i>empenho</i> é
          o ato administrativo que reserva dotação orçamentária para
          determinada finalidade. A <i>liquidação</i> verifica o direito
          adquirido pelo credor com base em comprovação da prestação do
          serviço ou entrega do bem. O <i>pagamento</i> é o efetivo
          desembolso financeiro. Valores empenhados que não chegam a ser
          pagos no exercício são inscritos em <i>restos a pagar</i> e podem
          ser executados em exercícios futuros, configurando o que a literatura
          identifica como uma das principais fontes de opacidade na execução
          orçamentária federal (BITTENCOURT, 2012).
        </p>

        <h3 className="article-h3">2.2 Marcos institucionais recentes</h3>

        <p>
          A trajetória institucional das emendas parlamentares no Brasil pós-1988
          pode ser esquematicamente dividida em três regimes distintos, marcados
          pelas reformas dos últimos quinze anos.
        </p>

        <p>
          <b>Regime autorizativo (1988–2015).</b> Durante o período inaugural
          do orçamento democrático, a execução das emendas era discricionária
          do Executivo. A literatura clássica brasileira sobre o tema —
          notadamente Pereira e Mueller (2002), Limongi e Figueiredo (2005)
          e Mesquita (2008) — estabeleceu que essa discricionariedade era um
          recurso central de governabilidade no presidencialismo de coalizão,
          permitindo ao Executivo recompensar parlamentares aliados com
          execução preferencial e penalizar adversários com contingenciamento.
          O efeito eleitoral desse mecanismo é objeto de extensa investigação;
          Baião e Couto (2017), por exemplo, encontram evidências robustas de
          que a combinação de emendas executadas com prefeitos aliados aumenta
          significativamente a probabilidade de reeleição parlamentar.
        </p>

        <p>
          <b>Regime impositivo parcial (2015–2019).</b> A EC&nbsp;86, de 17
          de março de 2015, alterou o §&nbsp;9º do art.&nbsp;166 da Constituição
          para estabelecer a obrigatoriedade de execução das emendas
          individuais, no montante equivalente a 1,2% da Receita Corrente
          Líquida prevista no projeto de LOA. A reforma incluiu também a
          obrigação de aplicação de pelo menos 50% desse montante em ações
          e serviços públicos de saúde, vinculação que dialoga diretamente
          com a EC&nbsp;29/2000 (DALLA COSTA; SAYD, 2020). A dimensão
          quantitativa dessa mudança é explícita nos dados empíricos: o volume
          médio anual executado mais que duplicou entre 2014 e 2018, conforme
          se demonstra na seção&nbsp;4 deste trabalho.
        </p>

        <p>
          <b>Regime impositivo expandido + RP9 (2019–2022).</b> A EC&nbsp;100,
          de 26 de junho de 2019, estendeu a impositividade às emendas de
          bancada estadual (RP7), em adicional equivalente a 1% da RCL.
          Simultaneamente, foi consolidada a modalidade RP9, apropriando-se de
          parte do que historicamente eram emendas individuais e de bancada
          em uma rubrica controlada pelo relator-geral do orçamento. A
          ausência de critérios objetivos de distribuição e de identificação
          dos parlamentares solicitantes caracterizou o que ficou conhecido
          como "orçamento secreto" (VOLPATO, 2022). Essa modalidade chegou
          a representar montantes superiores a R$&nbsp;16 bilhões em
          exercícios específicos, segundo dados da CGU consolidados neste
          estudo.
        </p>

        <p>
          <b>Regime pós-STF (2022–presente).</b> Em dezembro de 2022, o
          Supremo Tribunal Federal, no julgamento conjunto das ADPFs nº&nbsp;850,
          851, 854 e 1014, declarou inconstitucional o RP9 sob o fundamento
          de violação aos princípios constitucionais da publicidade e da
          impessoalidade, determinando a publicidade plena dos beneficiários
          e a vedação à continuidade do mecanismo. A Lei Complementar
          nº&nbsp;210, de 2024, complementou esse arcabouço regulatório ao
          estabelecer requisitos de transparência aplicáveis às emendas de
          bancada (RP7) e de comissão (RP8). O período recente é, portanto,
          caracterizado por uma redistribuição da composição entre modalidades
          e por exigências crescentes de rastreabilidade pública.
        </p>

        <h3 className="article-h3">2.3 Literatura prévia</h3>

        <p>
          A literatura acadêmica brasileira sobre emendas parlamentares
          desenvolveu-se predominantemente em três linhas. A primeira,
          inaugurada por Pereira e Mueller (2002) e consolidada por Limongi
          e Figueiredo (2005), debruça-se sobre o papel das emendas como
          moeda de troca no presidencialismo de coalizão, examinando o
          comportamento estratégico do Executivo na liberação dos recursos.
          A segunda linha, exemplificada por Mesquita (2008) e Baião e Couto
          (2017), foca o efeito eleitoral das emendas executadas, testando
          empiricamente hipóteses derivadas da literatura internacional sobre
          <i> pork-barrel politics</i> (AMES, 2001; MAINWARING, 1997). A
          terceira linha, mais recente, examina as implicações das reformas
          institucionais — em especial a EC&nbsp;86/2015 — sobre a dinâmica
          das relações Executivo–Legislativo (DALLA COSTA; SAYD, 2020;
          VOLPATO, 2022).
        </p>

        <p>
          Em comum, esses trabalhos enfrentam um desafio metodológico
          recorrente: a obtenção e o tratamento dos microdados de execução
          orçamentária. A maior parte dos estudos publicados utiliza recortes
          temporais limitados (geralmente um ou dois exercícios), agregações
          regionais simplificadas (em geral por região, não por unidade
          federativa) ou foco em uma única modalidade. Inexiste, ao
          conhecimento deste autor, uma base pública agregada e atualizada
          que ofereça, simultaneamente, cobertura temporal ampla, granularidade
          por UF, deflação para preços constantes e normalização per capita.
        </p>

        <h3 className="article-h3">2.4 Lacuna empírica e contribuição deste trabalho</h3>

        <p>
          O presente artigo busca preencher essa lacuna mediante a
          disponibilização aberta de uma base de dados consolidada e do código
          de processamento que a produz. A abordagem inspira-se nos princípios
          da ciência aberta (open science) e da arquitetura de dados moderna
          baseada em <i>data lakes</i> (ARMBRUST et al., 2021), aplicados ao
          contexto da transparência fiscal. A próxima seção detalha a
          metodologia adotada.
        </p>
      </section>

      {/* ─── 3 METODOLOGIA ───────────────────────────────────── */}

      <section className="article-section">
        <h2 className="article-h2">3. Metodologia</h2>

        <h3 className="article-h3">3.1 Fontes de dados</h3>

        <p>
          O estudo emprega três fontes oficiais de dados, todas de acesso
          público e licença aberta:
        </p>

        <ul>
          <li>
            <b>Microdados de execução orçamentária:</b> Portal da Transparência
            da Controladoria-Geral da União (CGU), arquivo consolidado
            <i> Emendas Parlamentares</i>, em formato CSV com separador
            ponto-e-vírgula e codificação Latin-1. O arquivo é distribuído
            como ZIP único cobrindo a série histórica de 2014 ao período
            corrente, atualizado periodicamente pela CGU. Para o exercício
            corrente, os valores refletem execução parcial até o último mês
            publicado pela CGU. Dado que o arquivo não contém coluna de mês
            de pagamento, este estudo, por critério de rigor metodológico,
            exclui o ano-calendário em curso da análise (ver subseção 3.5).
          </li>
          <li>
            <b>População residente estimada:</b> Instituto Brasileiro de
            Geografia e Estatística (IBGE), Sistema IBGE de Recuperação
            Automática (SIDRA), Tabela&nbsp;6579 (estimativas anuais por
            unidade federativa), variável 9324.
          </li>
          <li>
            <b>Índice de preços para deflação:</b> Banco Central do Brasil
            (BCB), Sistema Gerenciador de Séries Temporais (SGS), série 433
            (Índice Nacional de Preços ao Consumidor Amplo — IPCA, mensal),
            base utilizada para construção do deflator com referência em
            dezembro de 2021.
          </li>
        </ul>

        <h3 className="article-h3">3.2 Arquitetura do pipeline de dados</h3>

        <p>
          O pipeline foi desenhado segundo a chamada "arquitetura medallion",
          padrão de organização de <i>data lakes</i> popularizado por
          Armbrust et al. (2021) e amplamente adotado em ambientes
          corporativos. A arquitetura organiza os dados em três camadas
          progressivamente mais refinadas:
        </p>

        <ul>
          <li>
            <b>Camada Bronze (raw):</b> ingestão direta dos arquivos da
            fonte, sem transformações, em modo append-only. A camada Bronze
            preserva o histórico completo da fonte e permite auditoria
            independente. Implementação técnica: <i>Auto Loader</i> do
            Apache Spark sobre <i>Unity Catalog Volumes</i> do Databricks,
            com persistência em formato Delta Lake.
          </li>
          <li>
            <b>Camada Silver (cleansed):</b> aplicação de regras de tipagem,
            normalização e deduplicação. Para o caso das emendas, esta camada
            inclui: (i) normalização dos cabeçalhos das colunas (remoção de
            acentuação, conversão para snake-case); (ii) parsing dos valores
            monetários do formato brasileiro (separador de milhar
            "<code>.</code>" e decimal "<code>,</code>") para tipo
            <i> double</i>; (iii) classificação dos registros nas modalidades
            RP6/RP7/RP8/RP9/OUTRO conforme o campo Tipo de Emenda; (iv)
            mapeamento das unidades federativas, originalmente registradas
            por extenso no padrão da fonte (ex.: "MINAS GERAIS"), para os
            códigos ISO de duas letras ("MG"); (v) agregação por
            UF&nbsp;×&nbsp;Ano&nbsp;×&nbsp;Tipo&nbsp;de&nbsp;RP.
          </li>
          <li>
            <b>Camada Gold (analytics-ready):</b> joins com as dimensões
            compartilhadas — população residente (Silver populacao_uf_ano)
            e deflatores anuais (Silver ipca_deflators_2021) — produzindo
            um <i>panel data</i> com uma observação por UF&nbsp;×&nbsp;Ano,
            contendo todos os indicadores derivados (valor empenhado e pago
            em R$ nominal e em R$ 2021, taxa de execução, valor per capita,
            decomposição por modalidade).
          </li>
        </ul>

        <p>
          A operacionalização foi realizada em ambiente Databricks Free
          Edition, com orquestração via <i>Databricks Asset Bundles</i>
          e persistência integral em <i>Delta Lake</i>, garantindo
          versionamento (time travel) e capacidade de reprocessamento
          completo. O agendamento mensal é mediado por <i>GitHub Actions</i>,
          que extrai o JSON consolidado da camada Gold e o publica no
          repositório público sob versionamento Git. A íntegra do código está
          disponível em
          <a href="https://github.com/leonardochalhoub/mirante-dos-dados-br" target="_blank" rel="noreferrer">
            {' '}github.com/leonardochalhoub/mirante-dos-dados-br
          </a>.
        </p>

        <h3 className="article-h3">3.3 Indicadores construídos</h3>

        <p>
          A camada Gold produz, para cada par (UF, Ano), os seguintes
          indicadores:
        </p>

        <ol>
          <li>
            <b>Valor empenhado nominal</b> (R$): soma dos valores
            <i> Valor Empenhado</i> da fonte para a unidade federativa no
            exercício.
          </li>
          <li>
            <b>Valor empenhado real (R$ 2021):</b> valor nominal multiplicado
            pelo deflator anual derivado da série IPCA, com base em dezembro
            de 2021.
          </li>
          <li>
            <b>Valor pago nominal</b> e <b>valor pago real (R$ 2021):</b>
            análogos ao empenhado, calculados a partir do campo
            <i> Valor Pago</i>.
          </li>
          <li>
            <b>Taxa de execução:</b> razão entre valor pago nominal e valor
            empenhado nominal. Indicador-chave da efetividade da despesa.
          </li>
          <li>
            <b>Valor pago per capita (R$ 2021/hab):</b> valor pago real
            dividido pela população residente estimada.
          </li>
          <li>
            <b>Decomposição por modalidade:</b> para cada UF&nbsp;×&nbsp;Ano,
            valores empenhados e pagos discriminados por modalidade (RP6,
            RP7, RP8, RP9, OUTRO).
          </li>
          <li>
            <b>Restos a pagar inscritos:</b> valor que, embora empenhado, não
            foi pago no exercício e foi inscrito em restos a pagar.
          </li>
        </ol>

        <h3 className="article-h3">3.4 Construção do deflator IPCA</h3>

        <p>
          O deflator anual com referência em dezembro de 2021 é calculado
          a partir da série mensal IPCA do BCB (série 433). Para cada ano
          <i>t</i>, define-se o índice médio anual <i>I<sub>t</sub></i>;
          o deflator é então obtido por <i>D<sub>t</sub> = I<sub>2021,12</sub>
          / I<sub>t</sub></i>, de modo que valores expressos em moeda
          do ano <i>t</i> são convertidos para preços de dezembro de 2021
          mediante simples multiplicação. A escolha de dezembro de 2021 como
          base segue a convenção adotada pelo Tesouro Nacional em diversas
          publicações de séries históricas e facilita a interoperabilidade
          com outros estudos.
        </p>

        <h3 className="article-h3">3.5 Limitações</h3>

        <p>
          O estudo apresenta as seguintes limitações, assumidas como condições
          de contorno:
        </p>

        <ul>
          <li>
            <b>Ausência de granularidade mensal:</b> o arquivo consolidado da
            CGU não contém coluna de mês de pagamento ou liquidação. Em
            consequência, o ano-calendário em curso é necessariamente parcial
            e foi excluído da análise. Esta limitação difere, por exemplo,
            do caso do Bolsa Família, cujos arquivos mensais permitem
            aferição direta de completude.
          </li>
          <li>
            <b>Atribuição de UF pelo município beneficiário:</b> a unidade
            federativa associada a cada emenda neste estudo refere-se ao
            estado do município beneficiário do recurso, conforme registrado
            na fonte. Emendas destinadas a órgãos federais sem município
            específico (por exemplo, ministérios da Esplanada) são
            classificadas como "OUTRO" e excluídas da agregação por UF.
          </li>
          <li>
            <b>Revisões retroativas:</b> a CGU eventualmente realiza ajustes
            retroativos em valores publicados, em decorrência de decisões
            judiciais, ajustes contábeis ou correções de classificação. Em
            consequência, os números podem variar marginalmente entre
            <i> refreshes</i> sucessivos do pipeline.
          </li>
          <li>
            <b>Valores não-inscritos e despesas correlatas:</b> o estudo não
            contempla despesas executadas via dotações ordinárias dos órgãos
            (não associadas a emendas), nem fluxos de transferências
            voluntárias formalizados por instrumentos como convênios,
            contratos de repasse e termos de fomento, salvo quando esses
            instrumentos integram a execução da emenda parlamentar identificada
            na fonte.
          </li>
          <li>
            <b>Causalidade vs. correlação:</b> as comparações temporais
            apresentadas devem ser interpretadas como descritivas; o desenho
            metodológico não permite identificação causal isolada dos efeitos
            de cada reforma institucional. Análises causais robustas
            requerem identificação por desenho quase-experimental
            (<i>difference-in-differences</i>, <i>regression discontinuity</i>),
            o que constitui agenda futura de pesquisa.
          </li>
        </ul>
      </section>

      {/* ─── 4 RESULTADOS ────────────────────────────────────── */}

      <section className="article-section">
        <h2 className="article-h2">4. Resultados</h2>

        <p>
          Esta seção apresenta os resultados empíricos do processamento dos
          microdados da CGU para o período 2014–2025. Todos os valores
          monetários estão em reais de dezembro de 2021, salvo indicação
          em contrário. Para auxiliar a leitura, indicadores nominais
          também são reportados quando relevantes para a compreensão do
          ciclo orçamentário.
        </p>

        <h3 className="article-h3">4.1 Evolução temporal da execução</h3>

        <p>
          A Tabela&nbsp;1 apresenta a série temporal completa dos valores
          empenhados e pagos em cada exercício, em valores reais
          (R$&nbsp;2021), além da taxa de execução
          (pago&nbsp;/&nbsp;empenhado) e do número de emendas distintas
          identificadas pela fonte.
        </p>

        <table className="article-table">
          <caption className="article-table-caption">
            <b>Tabela 1.</b> Empenhado, pago, taxa de execução e número de
            emendas distintas — totais nacionais por exercício, 2014–2025.
          </caption>
          <thead>
            <tr>
              <th>Ano</th>
              <th>Empenhado<br/>(R$ bi, 2021)</th>
              <th>Pago<br/>(R$ bi, 2021)</th>
              <th>Taxa de<br/>execução</th>
              <th>Nº de emendas<br/>distintas</th>
            </tr>
          </thead>
          <tbody>
            <tr><td>2014</td><td>9,09</td><td>0,20</td><td>2,2%</td><td>27</td></tr>
            <tr><td>2015</td><td>4,54</td><td>0,03</td><td>0,6%</td><td>3.619</td></tr>
            <tr><td>2016</td><td>18,45</td><td>7,01</td><td>38,0%</td><td>5.964</td></tr>
            <tr><td>2017</td><td>17,39</td><td>4,01</td><td>23,0%</td><td>5.397</td></tr>
            <tr><td>2018</td><td>14,12</td><td>6,42</td><td>45,5%</td><td>6.801</td></tr>
            <tr><td>2019</td><td>15,10</td><td>6,55</td><td>43,4%</td><td>7.827</td></tr>
            <tr><td>2020</td><td>18,68</td><td>11,41</td><td>61,1%</td><td>7.575</td></tr>
            <tr><td>2021</td><td>16,20</td><td>9,40</td><td>58,0%</td><td>6.116</td></tr>
            <tr><td>2022</td><td>15,15</td><td>9,27</td><td>61,2%</td><td>5.591</td></tr>
            <tr><td>2023</td><td>24,75</td><td>19,04</td><td>76,9%</td><td>5.387</td></tr>
            <tr><td>2024</td><td>26,90</td><td>20,03</td><td>74,5%</td><td>6.127</td></tr>
            <tr><td>2025</td><td>28,71</td><td>21,27</td><td>74,1%</td><td>5.533</td></tr>
          </tbody>
        </table>
        <p className="article-figure-caption">
          <i>Fonte:</i> elaboração própria com base nos microdados do Portal
          da Transparência (CGU), deflacionados pelo IPCA-BCB para
          dezembro/2021. Visualização interativa disponível no painel
          principal desta página.
        </p>

        <p>
          Os dados revelam três regimes empíricos distintos, em consonância
          aproximada com a periodização institucional discutida na
          seção&nbsp;2. No biênio 2014–2015, o volume anual <i>pago</i>
          permaneceu em patamar marginal — R$&nbsp;0,20&nbsp;bi e
          R$&nbsp;0,03&nbsp;bi, respectivamente. É notável a discrepância
          entre o empenhado (R$&nbsp;9,1&nbsp;bi em 2014; R$&nbsp;4,5&nbsp;bi
          em 2015) e o efetivamente pago no exercício, com taxas de execução
          de apenas 2,2% e 0,6%. Esse padrão é consistente com o regime
          ainda predominantemente autorizativo: empenhado havia, mas a
          discricionariedade do Executivo se traduzia em pagamento
          residual no próprio exercício, com a maior parte dos valores
          sendo ou inscrita em restos a pagar ou cancelada.
        </p>

        <p>
          O período 2016–2019 marca o primeiro salto patamar. Já com a
          vigência da EC&nbsp;86/2015, os valores anuais pagos saltam para
          R$&nbsp;4&nbsp;bi a R$&nbsp;7&nbsp;bi e a taxa de execução, ainda
          que volátil, sobe para 23%–46%. O número de emendas distintas
          identificadas pela CGU também cresce expressivamente, passando
          de menos de 30 emendas em 2014 — provavelmente um artefato de
          codificação na fonte para esse ano específico — para mais de
          5&nbsp;mil em 2016 e 7,8&nbsp;mil em 2019.
        </p>

        <p>
          O segundo salto ocorre entre 2019 e 2020 e pode ser parcialmente
          atribuído à resposta fiscal à pandemia de COVID-19: o valor
          pago salta de R$&nbsp;6,5&nbsp;bi em 2019 para R$&nbsp;11,4&nbsp;bi
          em 2020, com a taxa de execução cruzando 60% pela primeira vez
          (61,1%). Os exercícios 2021 e 2022 mantêm patamar próximo
          (R$&nbsp;9,3&nbsp;bi a R$&nbsp;9,4&nbsp;bi pagos), com a taxa
          de execução estabilizando-se em torno de 58%–61%.
        </p>

        <p>
          O terceiro e mais expressivo salto ocorre em 2023, em sequência
          imediata à decisão do STF que extinguiu o RP9: o pago anual
          sobe abruptamente para R$&nbsp;19,0&nbsp;bi (alta de 105% sobre
          2022) e a taxa de execução atinge 76,9%, o maior valor da série.
          Esse patamar se mantém em 2024 (R$&nbsp;20,0&nbsp;bi; 74,5%) e
          2025 (R$&nbsp;21,3&nbsp;bi; 74,1%). Trata-se, em termos de
          ordens de grandeza, de uma execução cerca de cem vezes superior
          ao patamar de 2014, em valores reais constantes.
        </p>

        <h3 className="article-h3">4.2 Composição por tipo de Resultado Primário</h3>

        <p>
          A Tabela&nbsp;2 apresenta a participação de cada modalidade no
          total anual <i>pago</i>, em pontos percentuais. Os dados
          contradizem parcialmente a narrativa pública dominante segundo
          a qual a modalidade RP9 (relator-geral) seria fenômeno
          essencialmente do triênio 2020–2022.
        </p>

        <table className="article-table">
          <caption className="article-table-caption">
            <b>Tabela 2.</b> Composição do valor pago por modalidade de
            Resultado Primário (% do total anual), 2014–2025.
          </caption>
          <thead>
            <tr>
              <th>Ano</th>
              <th>RP6</th>
              <th>RP7</th>
              <th>RP9</th>
              <th>OUTRO</th>
            </tr>
          </thead>
          <tbody>
            <tr><td>2014</td><td>100,0%</td><td>0,0%</td><td>0,0%</td><td>0,0%</td></tr>
            <tr><td>2015</td><td>100,0%</td><td>0,0%</td><td>0,0%</td><td>0,0%</td></tr>
            <tr><td>2016</td><td>35,1%</td><td>15,1%</td><td><b>48,7%</b></td><td>1,1%</td></tr>
            <tr><td>2017</td><td>44,1%</td><td>30,2%</td><td>25,7%</td><td>~0%</td></tr>
            <tr><td>2018</td><td>73,4%</td><td>25,1%</td><td>0,0%</td><td>1,5%</td></tr>
            <tr><td>2019</td><td>72,7%</td><td>27,2%</td><td>0,1%</td><td>~0%</td></tr>
            <tr><td>2020</td><td>51,6%</td><td>34,7%</td><td>13,3%</td><td>0,4%</td></tr>
            <tr><td>2021</td><td>66,1%</td><td>33,9%</td><td>0,0%</td><td>~0%</td></tr>
            <tr><td>2022</td><td>69,0%</td><td>31,0%</td><td>0,0%</td><td>~0%</td></tr>
            <tr><td>2023</td><td>81,7%</td><td>18,0%</td><td>0,0%</td><td>0,3%</td></tr>
            <tr><td>2024</td><td>83,0%</td><td>17,0%</td><td>0,0%</td><td>~0%</td></tr>
            <tr><td>2025</td><td>75,6%</td><td>24,4%</td><td>0,0%</td><td>~0%</td></tr>
          </tbody>
        </table>
        <p className="article-figure-caption">
          <i>Fonte:</i> elaboração própria, microdados CGU.
          Categorias derivadas do campo Tipo&nbsp;de&nbsp;Emenda mediante
          regras de contains() sobre INDIVIDUAL/BANCADA/RELATOR. RP8
          (comissão) não apresentou participação não-nula no agregado.
        </p>

        <p>
          O dado mais marcante da Tabela&nbsp;2 é o pico do RP9 em 2016,
          quando essa modalidade respondeu por <b>48,7%</b> do total pago
          em emendas no exercício — R$&nbsp;2,66&nbsp;bi nominais, sob
          rótulo de "Emenda do Relator". Esse achado merece ressalva
          metodológica: a classificação automatizada utilizada neste
          estudo agrega à categoria RP9 todos os registros cuja descrição
          de tipo contenha o termo "RELATOR", o que pode incluir tipos de
          emenda cuja história institucional difere da modalidade
          consagrada como "orçamento secreto" no debate público
          posterior a 2019. Pesquisa subsequente, com cruzamento por
          códigos orçamentários específicos, é necessária para qualificar
          esse achado.
        </p>

        <p>
          Excluído esse caveat, o padrão é claro: a modalidade RP6
          (individuais) responde, em média, por aproximadamente
          <b> 70%–80%</b> do total pago entre 2018 e 2025, com pico de
          83% em 2024. A modalidade RP7 (bancada estadual), que era
          marginal antes da EC&nbsp;100/2019, estabiliza-se em
          17%–35% pós-vigência. A modalidade RP9, após o pico de 2016
          e ressurgência discreta em 2020 (13,3%), permanece zerada
          desde 2021 — antecipando, no plano dos dados, a decisão
          formal do STF de dezembro de 2022. A LC&nbsp;210/2024
          regulamentou a transparência aplicável a RP7 e RP8, mas, no
          conjunto de dados disponível, RP8 não apresentou participação
          quantitativa não-nula no agregado nacional.
        </p>

        <h3 className="article-h3">4.3 Distribuição geográfica por unidade federativa</h3>

        <p>
          A Tabela&nbsp;3 apresenta o ranking das dez unidades federativas
          de maior recebimento acumulado em valor pago, no período
          2014–2025, em valores reais (R$&nbsp;2021).
        </p>

        <table className="article-table">
          <caption className="article-table-caption">
            <b>Tabela 3.</b> Top-10 unidades federativas — valor pago
            acumulado em emendas parlamentares (R$&nbsp;bi, 2021),
            2014–2025.
          </caption>
          <thead>
            <tr><th>Posição</th><th>UF</th><th>Pago acumulado<br/>(R$&nbsp;bi, 2021)</th></tr>
          </thead>
          <tbody>
            <tr><td>1</td><td>São Paulo</td><td>12,21</td></tr>
            <tr><td>2</td><td>Minas Gerais</td><td>9,73</td></tr>
            <tr><td>3</td><td>Bahia</td><td>7,49</td></tr>
            <tr><td>4</td><td>Rio de Janeiro</td><td>7,06</td></tr>
            <tr><td>5</td><td>Ceará</td><td>6,36</td></tr>
            <tr><td>6</td><td>Rio Grande do Sul</td><td>5,55</td></tr>
            <tr><td>7</td><td>Maranhão</td><td>5,29</td></tr>
            <tr><td>8</td><td>Paraná</td><td>5,27</td></tr>
            <tr><td>9</td><td>Pernambuco</td><td>5,05</td></tr>
            <tr><td>10</td><td>Pará</td><td>4,70</td></tr>
          </tbody>
        </table>
        <p className="article-figure-caption">
          <i>Fonte:</i> elaboração própria, microdados CGU.
        </p>

        <p>
          Em valores absolutos, a concentração é significativa: as três
          maiores unidades federativas (SP, MG, BA) somam R$&nbsp;29,4&nbsp;bi
          em valores acumulados, o que representa parcela relevante do
          agregado nacional. Esse padrão é, em larga medida, esperado:
          unidades federativas mais populosas contam com bancadas
          parlamentares maiores e, portanto, com maior cota agregada de
          emendas individuais.
        </p>

        <h3 className="article-h3">4.4 Análise per capita: o efeito do <i>malapportionment</i></h3>

        <p>
          Quando o ranking é reorganizado pela métrica per capita
          (Tabela&nbsp;4), tomando-se como referência o exercício de
          2025, a ordenação é radicalmente invertida. As unidades
          federativas de menor população — Amapá, Roraima, Acre,
          Tocantins — assumem o topo, com valores per capita até dezessete
          vezes superiores aos das unidades mais populosas.
        </p>

        <table className="article-table">
          <caption className="article-table-caption">
            <b>Tabela 4.</b> Top-10 e bottom-5 unidades federativas — valor
            pago per capita em emendas parlamentares (R$/hab, 2021),
            exercício 2025.
          </caption>
          <thead>
            <tr><th>Posição</th><th>UF</th><th>Per capita<br/>(R$/hab, 2021)</th><th>População</th></tr>
          </thead>
          <tbody>
            <tr><td>1</td><td>Amapá</td><td><b>737,81</b></td><td>806.517</td></tr>
            <tr><td>2</td><td>Roraima</td><td>462,29</td><td>738.772</td></tr>
            <tr><td>3</td><td>Acre</td><td>385,14</td><td>884.372</td></tr>
            <tr><td>4</td><td>Tocantins</td><td>278,15</td><td>1.586.859</td></tr>
            <tr><td>5</td><td>Sergipe</td><td>258,62</td><td>2.299.425</td></tr>
            <tr><td>6</td><td>Piauí</td><td>228,98</td><td>3.384.547</td></tr>
            <tr><td>7</td><td>Rondônia</td><td>216,26</td><td>1.751.950</td></tr>
            <tr><td>8</td><td>Alagoas</td><td>185,13</td><td>3.220.848</td></tr>
            <tr><td>9</td><td>Paraíba</td><td>165,73</td><td>4.164.468</td></tr>
            <tr><td>10</td><td>Amazonas</td><td>160,44</td><td>4.321.616</td></tr>
            <tr><td colSpan={4} style={{ textAlign: 'center', padding: '8px 0', color: 'var(--muted)' }}>… (estados intermediários omitidos) …</td></tr>
            <tr><td>23</td><td>Minas Gerais</td><td>81,39</td><td>21.393.441</td></tr>
            <tr><td>24</td><td>Paraná</td><td>71,75</td><td>11.890.517</td></tr>
            <tr><td>25</td><td>Rio de Janeiro</td><td>66,77</td><td>17.223.547</td></tr>
            <tr><td>26</td><td>São Paulo</td><td>42,97</td><td>46.081.801</td></tr>
            <tr><td>27</td><td>Distrito Federal</td><td><b>24,87</b></td><td>2.996.899</td></tr>
          </tbody>
        </table>
        <p className="article-figure-caption">
          <i>Fonte:</i> elaboração própria, microdados CGU + IBGE/SIDRA
          tabela 6579 (estimativa populacional 2025).
        </p>

        <p>
          A diferença entre o topo e o fim do ranking é expressiva: o
          Amapá recebe R$&nbsp;737,81 per capita, ao passo que o
          Distrito Federal recebe R$&nbsp;24,87 — uma razão de
          aproximadamente <b>30 para 1</b>. A discrepância em relação a
          São Paulo (R$&nbsp;42,97 per capita) é da ordem de
          <b> 17 para 1</b>. Esse padrão é compatível com o fenômeno de
          <i> malapportionment</i> parlamentar característico do
          federalismo brasileiro (NICOLAU, 2017): pequenas unidades
          federativas detêm cotas de cadeiras na Câmara dos Deputados
          desproporcionalmente superiores à sua participação populacional,
          o que se reflete diretamente no volume agregado de emendas
          individuais por habitante.
        </p>

        <p>
          O caso particular do Distrito Federal merece nota: apesar de
          contar com bancada relativamente pequena (8 deputados federais
          + 3 senadores), tem população inferior a 3 milhões e, ainda
          assim, ocupa a última posição per capita. Hipótese plausível é
          que parcela substancial dos recursos federais destinados ao DF
          chega por outras vias — execução direta de órgãos federais,
          custeio de serviços da capital — e não como emendas
          parlamentares dirigidas aos municípios. Investigação adicional
          sobre o gasto federal total no DF, considerando todos os
          instrumentos, é necessária para qualificar essa interpretação.
        </p>

        <h3 className="article-h3">4.5 Indicador de equidade: coeficiente de variação</h3>

        <p>
          Para sintetizar a desigualdade observada entre as unidades
          federativas, calculou-se o coeficiente de variação (CV) anual
          dos valores per capita, definido como a razão entre o desvio
          padrão e a média da distribuição. A Tabela&nbsp;5 apresenta os
          resultados.
        </p>

        <table className="article-table">
          <caption className="article-table-caption">
            <b>Tabela 5.</b> Estatísticas descritivas da distribuição
            per capita do valor pago em emendas parlamentares por UF
            (R$/hab, 2021).
          </caption>
          <thead>
            <tr>
              <th>Ano</th>
              <th>Média<br/>(R$/hab)</th>
              <th>Desvio padrão<br/>(R$/hab)</th>
              <th>Coef. de variação</th>
            </tr>
          </thead>
          <tbody>
            <tr><td>2016</td><td>42,86</td><td>29,33</td><td>0,68</td></tr>
            <tr><td>2017</td><td>39,12</td><td>69,48</td><td>1,78</td></tr>
            <tr><td>2018</td><td>51,38</td><td>46,38</td><td>0,90</td></tr>
            <tr><td>2019</td><td>46,84</td><td>29,63</td><td>0,63</td></tr>
            <tr><td>2020</td><td>97,74</td><td>85,07</td><td>0,87</td></tr>
            <tr><td>2021</td><td>73,24</td><td>51,48</td><td>0,70</td></tr>
            <tr><td>2022</td><td>66,38</td><td>37,81</td><td>0,57</td></tr>
            <tr><td>2023</td><td>150,93</td><td>109,96</td><td>0,73</td></tr>
            <tr><td>2024</td><td>160,55</td><td>112,98</td><td>0,70</td></tr>
            <tr><td>2025</td><td>177,70</td><td>149,38</td><td>0,84</td></tr>
          </tbody>
        </table>
        <p className="article-figure-caption">
          <i>Fonte:</i> elaboração própria, microdados CGU + IBGE.
          Os exercícios 2014 e 2015 foram omitidos da análise por
          apresentarem volumes muito baixos que distorcem a estatística.
        </p>

        <p>
          O coeficiente de variação oscila entre 0,57 e 1,78 no
          período, sem apresentar tendência clara de redução. O valor
          atípico de 2017 (CV&nbsp;=&nbsp;1,78) reflete fortes
          assimetrias nesse exercício específico, possivelmente
          relacionadas ao processo de incorporação inicial das emendas
          impositivas. Excluído o ano de 2017, o CV permanece em
          patamar elevado — entre 0,57 e 0,90 — em todo o período
          recente, indicando que a impositividade legal não promoveu
          convergência distributiva entre as UFs.
        </p>

        <p>
          A título de comparação, a mesma estatística aplicada à
          distribuição per capita do programa Bolsa Família, nos
          mesmos exercícios, situa-se em patamares substancialmente
          inferiores — em geral entre 0,15 e 0,30. Significa dizer que
          a alocação per capita das emendas parlamentares é cerca de
          duas a quatro vezes mais desigual entre as unidades
          federativas do que a alocação do principal programa de
          transferência direta de renda do governo federal. Essa
          assimetria reforça a interpretação de que as emendas
          constituem mecanismo de natureza eminentemente política,
          regido por critérios de representação parlamentar, em
          contraste com programas concebidos sob critérios técnicos
          de necessidade socioeconômica.
        </p>
      </section>

      {/* ─── 5 DISCUSSÃO ─────────────────────────────────────── */}

      <section className="article-section">
        <h2 className="article-h2">5. Discussão</h2>

        <h3 className="article-h3">5.1 A impositividade como inflexão estrutural</h3>

        <p>
          Os resultados da seção&nbsp;4 permitem afirmar que a EC&nbsp;86/2015
          e, em segundo momento, a EC&nbsp;100/2019 produziram inflexão
          estrutural no padrão de execução das emendas parlamentares
          federais. A magnitude dessa inflexão é objetivamente medível: em
          valores reais (R$&nbsp;2021), o pago anual saltou de
          R$&nbsp;0,03&nbsp;bi em 2015 para R$&nbsp;21,27&nbsp;bi em 2025
          — evolução de aproximadamente <b>700 vezes</b> em uma década.
          Mesmo controlando por bases mais conservadoras (por exemplo,
          comparando 2018, primeiro ano com RP9 zerado e EC&nbsp;86 em
          plena vigência, contra 2025), a multiplicação é da ordem de
          3,3 vezes em sete anos.
        </p>

        <p>
          Tal inflexão tem implicações ambivalentes para a teoria do
          presidencialismo de coalizão. Por um lado, restringe-se o
          espaço de negociação discricionária do Executivo: parcela
          substancial das emendas tornou-se de execução obrigatória,
          reduzindo o estoque de "moeda política" disponível para
          alinhar bancadas. Por outro, a impositividade não eliminou
          o poder de barganha intra-Executivo. As taxas de execução
          observadas — que sobem de 23% em 2017 para 76,9% em 2023 —
          mostram que, mesmo no regime impositivo, há margem expressiva
          de variação ano-a-ano no ritmo do processamento administrativo,
          velocidade de habilitação dos beneficiários e calendário de
          empenho. Nesse sentido, parte da literatura recente
          (DALLA&nbsp;COSTA; SAYD, 2020) tem proposto a hipótese de
          "deslocamento da discricionariedade" — da decisão de executar
          para a decisão de <i>quando</i> e <i>como</i> executar.
        </p>

        <h3 className="article-h3">5.2 O salto pós-STF: efeito-libertação ou redistribuição contábil?</h3>

        <p>
          Talvez o achado empírico mais expressivo deste estudo seja o
          salto absoluto observado entre 2022 e 2023, quando o pago anual
          mais que dobra (R$&nbsp;9,27&nbsp;bi → R$&nbsp;19,04&nbsp;bi
          em valores 2021), com a taxa de execução cruzando 75%. Esse
          salto é exatamente concomitante à decisão do STF que extinguiu
          a modalidade RP9 (dezembro de 2022), mas é importante notar
          que ele opera em direção contrária à hipótese ingênua: se RP9
          era opaco e foi extinto, deveríamos esperar redução ou
          estagnação, não duplicação.
        </p>

        <p>
          Duas hipóteses interpretativas merecem investigação futura. A
          primeira — que poderíamos chamar de <i>hipótese da
          libertação</i> — sustenta que a extinção do RP9 forçou a
          redistribuição dos volumes anteriormente alocados naquela
          modalidade para emendas individuais (RP6) e de bancada
          (RP7), ambas de execução obrigatória, ampliando assim o
          patamar agregado de gasto. Essa hipótese é compatível com o
          salto da participação do RP6 no total pago: de 69,0% em
          2022 para 81,7% em 2023 e 83,0% em 2024. A segunda — a
          <i> hipótese contábil</i> — sustenta que parte do crescimento
          observado em 2023 reflete pagamentos de restos a pagar
          inscritos nos exercícios anteriores, consequência mecânica
          da resolução de pendências formais reveladas pela exigência
          de transparência ditada pelo STF. Distinguir essas duas
          hipóteses exigiria análise da composição do pago por exercício
          de origem do empenho, dado disponível em outros conjuntos de
          microdados da CGU mas não no arquivo consolidado utilizado
          neste estudo.
        </p>

        <h3 className="article-h3">5.3 O pico anômalo do RP9 em 2016</h3>

        <p>
          O resultado da Tabela&nbsp;2, segundo o qual a modalidade RP9
          respondeu por 48,7% do total pago em 2016, contraria a narrativa
          predominante na imprensa e em parte da literatura, que situa o
          surgimento do RP9 a partir de 2019. Há três possibilidades
          interpretativas, não mutuamente excludentes.
        </p>

        <p>
          Primeiro, é possível que se trate de artefato de classificação:
          a regra de extração de modalidade utilizada neste estudo —
          baseada em correspondência textual sobre a coluna
          <i> Tipo&nbsp;de&nbsp;Emenda</i> — atribui à categoria RP9
          qualquer registro cuja descrição contenha o termo "RELATOR".
          Em 2016, a CGU pode ter usado um esquema de nomenclatura
          distinto, agregando diferentes tipos de emendas processadas
          via relatorias (de comissão, de plenário, de bancada) sob um
          único rótulo que casa com a regra. Nesse caso, o pico de 2016
          seria mais um vício metodológico do que um achado substantivo.
        </p>

        <p>
          Segundo, é possível que se trate de fenômeno orçamentário
          genuíno, mas distinto do que veio a ser caracterizado, anos
          mais tarde, como "orçamento secreto". Emendas processadas via
          relatorias de comissões existem desde os primórdios do
          processo orçamentário democrático brasileiro, e seu volume
          historicamente flutua em função de fatores políticos
          conjunturais. O ano de 2016 foi marcado por intensa
          instabilidade política — processo de impeachment, mudança
          de governo, recomposição do orçamento — que pode ter
          ampliado o uso instrumental de emendas via relatoria.
        </p>

        <p>
          Terceiro, é possível que parte dos pagamentos efetuados em
          2016 corresponda a empenhos retroativos de exercícios
          anteriores, distorcendo a comparação entre <i>exercício de
          referência</i> (Ano da Emenda) e <i>exercício de pagamento</i>.
          A elucidação rigorosa dessas hipóteses requer trabalho
          subsequente de cruzamento com microdados do SIAFI/Tesouro
          Nacional, o que extrapola o escopo do presente artigo. Os
          resultados aqui apresentados são, portanto, descritivos do
          que a fonte CGU registra como pago no exercício, sem
          desambiguação de origem do empenho.
        </p>

        <h3 className="article-h3">5.4 Equidade federativa e desenho institucional</h3>

        <p>
          A análise per capita (Tabela&nbsp;4) e o coeficiente de
          variação (Tabela&nbsp;5) constituem o conjunto de achados de
          maior implicação normativa para o debate sobre federalismo
          fiscal. A razão de aproximadamente 30 para 1 entre o Amapá
          (R$&nbsp;737,81/hab) e o Distrito Federal (R$&nbsp;24,87/hab),
          em 2025, é magnitude que dificilmente seria justificada por
          critérios técnicos de necessidade ou eficiência alocativa.
          Trata-se de consequência direta — e previsível — do
          <i> malapportionment</i> parlamentar característico do
          federalismo brasileiro: o Amapá conta com 8 deputados federais
          e 3 senadores para uma população de aproximadamente 0,8&nbsp;milhão
          de habitantes, enquanto São Paulo tem 70 deputados e 3 senadores
          para uma população de aproximadamente 46&nbsp;milhões.
          Em termos de cota de cadeiras na Câmara dos Deputados,
          o Amapá tem 1 deputado para cada 100&nbsp;mil habitantes; São
          Paulo tem 1 para cada 658&nbsp;mil. A razão entre ambas
          aproxima-se justamente da razão observada entre seus valores
          per capita de emendas executadas.
        </p>

        <p>
          A literatura comparada não oferece resposta unívoca sobre a
          desejabilidade dessa configuração. Mainwaring (1997) e Samuels
          (2002) argumentam que regras de alocação orçamentária com viés
          pró-pequenos-estados são funcionais à estabilidade do pacto
          federativo em sistemas presidencialistas fragmentados,
          oferecendo às unidades menos populosas garantia institucional
          de presença no orçamento federal. Críticos do <i>status quo</i>,
          por outro lado, sustentam que o sobrepeso das pequenas unidades
          federativas configura distorção alocativa que prejudica a
          eficiência agregada do gasto público (NICOLAU, 2017). Os dados
          aqui apresentados não resolvem essa controvérsia normativa,
          mas oferecem mensuração empírica reproduzível de sua magnitude:
          coeficiente de variação per capita oscilando entre 0,57 e 0,90
          no período recente — patamar cerca de duas a quatro vezes
          superior ao observado em programas de transferência direta
          como o Bolsa Família.
        </p>

        <h3 className="article-h3">5.5 Implicações para a gestão pública</h3>

        <p>
          Para o gestor público — especialmente nos níveis subnacionais —
          os resultados deste estudo sugerem três implicações práticas.
          Primeiro, a <b>previsibilidade orçamentária</b>: a impositividade
          legal das modalidades RP6 e RP7, traduzida nas taxas de
          execução crescentes (de 2,2% em 2014 para 74,1% em 2025),
          confere ao gestor municipal e estadual horizonte de planejamento
          incomparavelmente mais sólido do que aquele da década passada.
          Estados e municípios capazes de antecipar e formalizar projetos
          tendem a capturar maior parcela das emendas a que tem direito
          sua bancada.
        </p>

        <p>
          Segundo, a <b>centralidade da capacidade administrativa local</b>:
          mesmo no regime impositivo, há margens não-triviais de variação
          inter-UF que se correlacionam com a capacidade técnica de
          formalização e prestação de contas dos municípios beneficiários.
          Investimentos em capacitação de equipes municipais — em
          captação de recursos, gestão de convênios, prestação de contas
          — têm impacto direto sobre a captura efetiva dos recursos
          legalmente disponíveis. Esse achado tem implicações relevantes
          para programas como o Programa Federativo de Apoio aos
          Municípios (PFAM) e para iniciativas de formação continuada
          em gestão pública.
        </p>

        <p>
          Terceiro, a <b>transparência e o controle social</b>: a evolução
          normativa pós-STF — culminando na LC&nbsp;210/2024 — aumentou
          de forma expressiva a rastreabilidade pública das emendas. O
          presente trabalho insere-se nesse contexto como contribuição
          de infraestrutura: ao disponibilizar pipeline open-source e
          base de dados consolidada, espera-se reduzir o custo marginal
          para que organizações da sociedade civil, imprensa investigativa
          e órgãos de controle externo possam conduzir análises próprias
          sem o ônus inicial do tratamento dos microdados. Em última
          instância, a efetividade dos novos marcos regulatórios depende
          da existência de uma comunidade técnica capaz de usar a
          informação produzida — e essa comunidade, por sua vez, depende
          de instrumentos como o aqui apresentado.
        </p>
      </section>

      {/* ─── 6 CONSIDERAÇÕES FINAIS ──────────────────────────── */}

      <section className="article-section">
        <h2 className="article-h2">6. Considerações Finais</h2>

        <p>
          Este artigo buscou contribuir para a compreensão empírica das
          emendas parlamentares federais brasileiras no período 2014–2025,
          combinando uma contribuição metodológica — disponibilização
          aberta de pipeline de dados em arquitetura medallion — e uma
          contribuição substantiva — análise dos efeitos das mudanças
          institucionais recentes sobre o volume, a distribuição
          espacial, a taxa de execução e a composição por modalidade.
        </p>

        <p>
          Os resultados empíricos confirmam três achados centrais:
          (i) a impositividade legal introduzida por EC&nbsp;86/2015 e
          ampliada por EC&nbsp;100/2019 produziu inflexão estrutural no
          volume executado, com crescimento de duas ordens de grandeza
          em uma década; (ii) a modalidade RP9 (relator-geral),
          característica do período 2020–2022, foi efetivamente
          neutralizada pela decisão do STF de dezembro de 2022, com
          queda abrupta de sua participação a partir de 2023; (iii) a
          alocação per capita das emendas continua a apresentar
          desigualdade superior à de outros benefícios federais, padrão
          compatível com o efeito de
          <i> malapportionment</i> característico do federalismo
          parlamentar brasileiro.
        </p>

        <p>
          Diversos desdobramentos de pesquisa permanecem em aberto. A
          análise causal do efeito das reformas institucionais
          beneficiar-se-ia de desenhos quase-experimentais que
          aproveitassem a descontinuidade temporal de cada reforma. O
          cruzamento dos dados de emendas com indicadores municipais de
          desenvolvimento (Índice FIRJAN, IDH-M, indicadores do
          Atlas&nbsp;do&nbsp;Desenvolvimento&nbsp;Humano) permitiria
          examinar empiricamente a hipótese de focalização ou
          anti-focalização territorial. A monitoração contínua dos
          dados pós-LC&nbsp;210/2024, em especial das modalidades RP7
          e RP8, permitirá avaliação prospectiva da eficácia regulatória
          das exigências de transparência. Por fim, a integração com
          dados eleitorais (TSE) habilitaria revisitar os achados
          clássicos sobre o efeito eleitoral das emendas executadas
          em um regime de impositividade consolidada — desenho de
          pesquisa que escapa ao escopo deste artigo, mas que esta
          base de dados torna factível.
        </p>

        <p>
          A disponibilização aberta do pipeline e da base consolidada,
          mantidos sob versionamento Git e com refresh mensal automatizado,
          espera contribuir para que pesquisadores, jornalistas, organizações
          da sociedade civil e órgãos de controle disponham de
          infraestrutura mínima de dados para conduzir análises próprias
          sem o ônus inicial de processamento dos microdados originais
          do Portal da Transparência.
        </p>
      </section>

      {/* ─── REFERÊNCIAS ─────────────────────────────────────── */}

      <section className="article-section article-references">
        <h2 className="article-h2">Referências</h2>

        <p className="article-ref">
          AMES, B. <i>The Deadlock of Democracy in Brazil</i>. Ann Arbor:
          University of Michigan Press, 2001.
        </p>

        <p className="article-ref">
          ARMBRUST, M.; GHODSI, A.; XIN, R.; ZAHARIA, M. Lakehouse: a new
          generation of open platforms that unify data warehousing and
          advanced analytics. <i>11th Conference on Innovative Data Systems
          Research (CIDR)</i>, 2021.
        </p>

        <p className="article-ref">
          BAIÃO, A. L.; COUTO, C. G. A eficácia do pork barrel: a importância
          de emendas orçamentárias e prefeitos aliados na eleição de deputados.
          <i> Opinião Pública</i>, Campinas, v. 23, n. 3, p. 714–753, 2017.
        </p>

        <p className="article-ref">
          BITTENCOURT, F. M. R. <i>Relações Executivo-Legislativo no
          Presidencialismo de Coalizão: um quadro de referência para estudos
          de orçamento e controle</i>. Brasília: Núcleo de Estudos e Pesquisas
          do Senado Federal, Texto para Discussão nº&nbsp;112, 2012.
        </p>

        <p className="article-ref">
          BRASIL. <i>Constituição da República Federativa do Brasil de 1988</i>.
          Brasília: Senado Federal, 1988.
        </p>

        <p className="article-ref">
          BRASIL. <i>Emenda Constitucional nº 86, de 17 de março de 2015</i>.
          Altera os arts. 165, 166 e 198 da Constituição Federal, para tornar
          obrigatória a execução da programação orçamentária que especifica.
          Diário Oficial da União, 18 mar. 2015.
        </p>

        <p className="article-ref">
          BRASIL. <i>Emenda Constitucional nº 100, de 26 de junho de 2019</i>.
          Altera os arts. 165 e 166 da Constituição Federal para tornar
          obrigatória a execução da programação orçamentária proveniente de
          emendas de bancada de parlamentares de Estado ou do Distrito Federal.
          Diário Oficial da União, 27 jun. 2019.
        </p>

        <p className="article-ref">
          BRASIL. Supremo Tribunal Federal. <i>Arguições de Descumprimento de
          Preceito Fundamental nº 850, 851, 854 e 1014</i>. Rel. Min. Rosa
          Weber. Plenário, j. 19 dez. 2022.
        </p>

        <p className="article-ref">
          BRASIL. <i>Lei Complementar nº 210, de 2024</i>. Estabelece normas
          gerais sobre a execução de emendas parlamentares de bancada
          estadual, de comissão, e dá outras providências. Diário Oficial da
          União, 2024.
        </p>

        <p className="article-ref">
          BANCO CENTRAL DO BRASIL (BCB). <i>Sistema Gerenciador de Séries
          Temporais (SGS)</i>. Série 433: Índice Nacional de Preços ao
          Consumidor Amplo (IPCA). Disponível em:
          {' '}<a href="https://api.bcb.gov.br/dados/serie/bcdata.sgs.433/dados?formato=json" target="_blank" rel="noreferrer">
            api.bcb.gov.br/dados/serie/bcdata.sgs.433/dados
          </a>. Acesso em: abr. 2026.
        </p>

        <p className="article-ref">
          CONGRESSO NACIONAL. Comissão Mista de Planos, Orçamentos Públicos e
          Fiscalização (CMO). <i>Glossário do Orçamento Federal</i>. [s.d.].
          Disponível em:
          {' '}<a href="https://www2.camara.leg.br/orcamento-da-uniao/cidadao/entenda/cursopo/glossario" target="_blank" rel="noreferrer">
            camara.leg.br/orcamento-da-uniao
          </a>.
        </p>

        <p className="article-ref">
          CONTROLADORIA-GERAL DA UNIÃO (CGU). <i>Portal da Transparência:
          Microdados de Emendas Parlamentares</i>. Brasília: CGU. Disponível em:
          {' '}<a href="https://portaldatransparencia.gov.br/download-de-dados/emendas-parlamentares" target="_blank" rel="noreferrer">
            portaldatransparencia.gov.br/download-de-dados/emendas-parlamentares
          </a>. Acesso em: abr. 2026.
        </p>

        <p className="article-ref">
          DALLA COSTA, A.; SAYD, P. Emendas individuais e impositividade
          orçamentária no Brasil. <i>Revista do Serviço Público</i>, Brasília,
          v. 71, n. 4, 2020.
        </p>

        <p className="article-ref">
          FALCÃO, J.; ARGUELHES, D. W.; RECONDO, F. (Orgs.). <i>Onze
          Supremos: o Supremo em 2022</i>. Belo Horizonte: Letramento, 2023.
        </p>

        <p className="article-ref">
          INSTITUTO BRASILEIRO DE GEOGRAFIA E ESTATÍSTICA (IBGE).
          <i> SIDRA — Sistema IBGE de Recuperação Automática</i>. Tabela 6579:
          Estimativas anuais da população residente. Disponível em:
          {' '}<a href="https://sidra.ibge.gov.br/tabela/6579" target="_blank" rel="noreferrer">
            sidra.ibge.gov.br/tabela/6579
          </a>. Acesso em: abr. 2026.
        </p>

        <p className="article-ref">
          LIMONGI, F.; FIGUEIREDO, A. Processo orçamentário e comportamento
          legislativo: emendas individuais, apoio ao Executivo e programas de
          governo. <i>Dados</i>, Rio de Janeiro, v. 48, n. 4, p. 737–776, 2005.
        </p>

        <p className="article-ref">
          MAINWARING, S. Multipartism, Robust Federalism, and Presidentialism
          in Brazil. In: MAINWARING, S.; SHUGART, M. (Eds.). <i>Presidentialism
          and Democracy in Latin America</i>. Cambridge: Cambridge University
          Press, 1997. p. 55–109.
        </p>

        <p className="article-ref">
          MESQUITA, L. <i>Emendas ao orçamento e conexão eleitoral na Câmara
          dos Deputados</i>. 2008. Dissertação (Mestrado em Ciência Política)
          — Faculdade de Filosofia, Letras e Ciências Humanas, Universidade
          de São Paulo, São Paulo, 2008.
        </p>

        <p className="article-ref">
          NICOLAU, J. <i>Representantes de quem? Os (des)caminhos do seu voto
          da urna à Câmara dos Deputados</i>. Rio de Janeiro: Zahar, 2017.
        </p>

        <p className="article-ref">
          PEREIRA, C.; MUELLER, B. Comportamento estratégico em
          presidencialismo de coalizão: as relações entre Executivo e
          Legislativo na elaboração do orçamento brasileiro.
          <i> Dados</i>, Rio de Janeiro, v. 45, n. 2, p. 265–301, 2002.
        </p>

        <p className="article-ref">
          SAMUELS, D. Pork barreling is not credit claiming or advertising:
          campaign finance and the sources of the personal vote in Brazil.
          <i> The Journal of Politics</i>, v. 64, n. 3, p. 845–863, 2002.
        </p>

        <p className="article-ref">
          VOLPATO, B. <i>O orçamento secreto: análise da modalidade RP9 e
          seus efeitos no presidencialismo de coalizão brasileiro</i>. 2022.
          Dissertação (Mestrado em Administração Pública) — Escola de
          Administração de Empresas de São Paulo, Fundação Getulio Vargas,
          São Paulo, 2022.
        </p>

        <p className="article-ref">
          ZAHARIA, M.; CHAMBERS, B.; DAS, T. <i>Lakehouse Architecture: a
          definitive guide</i>. Sebastopol: O'Reilly Media, 2023.
        </p>
      </section>

      <footer className="article-footnote">
        <p>
          <b>Citar como:</b><br />
          CHALHOUB, L. Emendas Parlamentares no Orçamento Federal Brasileiro
          (2014–2025): distribuição espacial, execução orçamentária e efeitos
          das mudanças institucionais recentes. <i>Mirante dos Dados —
          Working Paper</i>, v. 1.0, abr. 2026. Disponível em:
          {' '}<a href="https://leonardochalhoub.github.io/mirante-dos-dados-br/" target="_blank" rel="noreferrer">
            leonardochalhoub.github.io/mirante-dos-dados-br
          </a>.
        </p>
        <p>
          <b>Licença:</b> os dados consolidados (camada Gold) e o código-fonte
          do pipeline são distribuídos sob licença MIT. O texto deste artigo
          é distribuído sob licença Creative Commons Atribuição 4.0
          Internacional (CC BY 4.0).
        </p>
      </footer>

    </article>
  );
}

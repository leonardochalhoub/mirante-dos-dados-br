# Mirante dos Dados — Architecture & Design Decisions

> Último update: 2026-04-26 · v1.0
>
> Este documento responde à pergunta "**por que isso e não aquilo?**"
> em cada decisão arquitetural não-óbvia do projeto Mirante. Cada ADR
> (Architecture Decision Record) abaixo segue o formato Michael Nygard
> simplificado: **Contexto → Decisão → Consequências**.

---

## Visão geral

O Mirante dos Dados é uma plataforma analítica multi-vertical sobre
microdados públicos brasileiros (CNES/DATASUS, CGU, IBGE, BCB, MTE),
publicada como (a) site React/Vite estático em
[GitHub Pages](https://leonardochalhoub.github.io/mirante-dos-dados-br/),
(b) Working Papers ABNT compilados em LaTeX no CI, (c) datasets
reproduzíveis em formato JSON versionados em Git, (d) dicionário
canonical CNES de 133 entradas em CSV aberto, (e) pipeline aberto
medallion (bronze/silver/gold) em Apache Spark sobre Delta Lake.

```
┌─────────────────────────────────────────────────────────────────┐
│  Fontes públicas (FTP DATASUS, CGU, IBGE/SIDRA, BCB, MTE)      │
└──────────────────────────┬──────────────────────────────────────┘
                           ↓ ingest (idempotent, parallel)
┌─────────────────────────────────────────────────────────────────┐
│  Bronze · Delta tables, STRING-ONLY, partition (estado, ano)    │
│  Auto Loader incremental + batch overwrite na primeira carga    │
└──────────────────────────┬──────────────────────────────────────┘
                           ↓ silver (Spark batch transform)
┌─────────────────────────────────────────────────────────────────┐
│  Silver · UF×Ano agregados, casts tipados, dedup, enrichment    │
│  Joins com dim populacao_uf_ano + IPCA + dicionários canonical  │
└──────────────────────────┬──────────────────────────────────────┘
                           ↓ gold (pass-through ou agregação final)
┌─────────────────────────────────────────────────────────────────┐
│  Gold · UF×Ano final, schema estável publicado, com COMMENT     │
│  Materializado em Delta + exportado JSON pra data/gold/         │
└──────────────────────────┬──────────────────────────────────────┘
                           ↓ export + sync (CI Databricks→Git)
┌─────────────────────────────────────────────────────────────────┐
│  Front · React/Vite + recharts + react-simple-maps             │
│  Lê JSON via fetch, agrega client-side, exporta XLSX/PNG/PDF    │
└─────────────────────────────────────────────────────────────────┘
```

---

## ADR-001 — Por quê Delta Lake, não Iceberg ou Hudi?

**Contexto.** Em 2023-2024, três formatos open-table competiam pelo
mind-share em lakehouses: Apache Iceberg (Netflix → Apache Foundation,
ampla adoção em Snowflake/BigQuery), Apache Hudi (Uber → Apache,
forte em CDC), e Delta Lake (Databricks → Linux Foundation, ampla
adoção em workloads Databricks).

**Decisão.** Delta Lake.

**Consequências.**
- ✅ **Free tier viável**: o Mirante roda em Databricks Free Edition,
  que tem suporte nativo e otimizado a Delta. Iceberg/Hudi exigiriam
  setup adicional fora do Databricks.
- ✅ **Time travel + Delta Sharing** para auditabilidade futura sem
  custo adicional.
- ✅ **MERGE INTO** simples e bem-otimizado para SCD Type 2 (não
  usado hoje, mas reservado pra evolução).
- ⚠️ **Lock-in moderado**: Delta é mais portável que Snowflake
  proprietary, mas menos que Iceberg (que tem suporte cross-engine
  amplo). Decisão revisitável se migração para data warehouse
  open-source for prioridade.
- ⚠️ **Performance em queries cross-table**: para joins muito
  grandes, Iceberg tem performance superior em Trino. Não é gargalo
  hoje (gold tables são <100MB).

---

## ADR-002 — Por quê Auto Loader + batch híbrido na bronze, não só batch?

**Contexto.** Cada vertical do Mirante ingere fontes diferentes:
DATASUS publica DBC mensal, CGU publica ZIP mensal, BCB publica JSON
diário (IPCA), IBGE publica anual. O ingest pode ser modelado como
batch puro (run completo a cada refresh) ou streaming (Auto Loader
com checkpoint).

**Decisão.** Híbrido — batch overwrite na primeira carga, Auto Loader
incremental nas subsequentes.

**Consequências.**
- ✅ **Carga inicial rápida**: 6.6K DBCs do CNES em ~2-3 min via
  batch overwrite, vs ~10-15 min se Auto Loader processasse arquivo
  por arquivo.
- ✅ **Refreshes mensais eficientes**: Auto Loader com checkpoint
  detecta apenas os 27 novos DBCs do mês (1 por UF), processa em
  segundos.
- ✅ **Self-healing**: marker `_schema_version_v2` no parquet folder
  dispara reingest se schema mudou.
- ⚠️ **Complexidade**: a lógica de `use_batch = (not table_exists) or
  (existing_rows == 0) or (not checkpoint_initialized)` é
  não-trivial. Fica claramente documentada na bronze notebook.
- ⚠️ **Race condition rara**: se ingest job rodar 2x em paralelo
  (job + manual trigger), a bronze pode ter timestamps duplicados.
  Tratado em silver via dedup por `source_file` + `max(_ingest_ts)`
  (ADR-005).

---

## ADR-003 — Por quê bronze STRING-ONLY?

**Contexto.** Frameworks data engineering tipicamente fazem inferência
de tipo na ingestão (Auto Loader `inferColumnTypes=true`, Pandas
`read_csv` com `dtype` automático). Isso causa heterogeneidade de
schema entre runs (mesmo CSV pode ter coluna lida como `int` num run
e `string` no outro, dependendo dos primeiros N rows).

**Decisão.** Bronze armazena tudo como `string`. Casts acontecem
apenas em silver+, onde há semântica de negócio.

**Consequências.**
- ✅ **Schema bronze é estável**: não há discrepância entre runs.
  `mergeSchema=true` ainda funciona pra evolução de adicionar
  colunas, mas tipos não mudam.
- ✅ **Bronze fiel à fonte**: guarda exatamente o que foi recebido,
  útil pra auditoria e debug ("a fonte mandou string, não nosso bug").
- ✅ **Casts explícitos em silver**: cada cast tem comentário sobre
  por que aquele tipo (int vs double, com leading zero ou sem).
- ⚠️ **Custo de casts repetidos**: silver paga o custo de
  conversão a cada run. Mitigado por silver ser batch overwrite (não
  recalcula gold se silver não mudou).
- ⚠️ **Erros de dados são detectados depois**: row com string
  inválida (`"abc"` numa coluna numérica) só falha em silver. Trade-off
  aceitável — errors em produção são raros e captura tardia é
  preferível a inferência silenciosa.

---

## ADR-004 — Por quê chave composta `(TIPEQUIP, CODEQUIP)` em silver?

**Contexto.** Em abr/2026 descobrimos que silver de equipamentos
estava colapsando 8 categorias de equipamento porque usava só
`CODEQUIP` (CHAR(2)) como chave, ignorando `TIPEQUIP` (CHAR(1)).
Resultado: filtro `CODEQUIP=42` retornava Eletroencefalógrafo
(TIPEQUIP=4) achando que era Ressonância Magnética. Bug
silencioso por 6 meses.

**Decisão.** Silver agrega por chave composta `(estado, ano,
tipequip, codequip)` e materializa coluna derivada
`equipment_key = "tipequip:codequip"` (ex.: `"1:12"` = RM,
`"4:42"` = EEG).

**Consequências.**
- ✅ **Resolve ambiguidade de identificadores**: cada equipamento
  tem chave única no silver+gold.
- ✅ **Front filtra por equipment_key**: vertical Equipamentos
  default de `'1:12'` (RM correta) ao invés do legado `'42'` (EEG
  rotulado errado).
- ✅ **Documentado em WP #6** (Panorama CNES) como contribuição
  metodológica e referência canônica para projetos futuros.
- ⚠️ **Breaking change**: gold antigo (com só `codequip`) não é
  compatível. Front tem fallback `rowKey()` para legacy schemas.
- ⚠️ **Bronze pode ter formatos diferentes** do mesmo TIPEQUIP
  ('1' vs '01'). Tratado por normalize via `cast(int).cast(str)` +
  `lpad(2, "0")` em silver — vide ADR-005.

---

## ADR-005 — Por quê dedup por `source_file` + `max(_ingest_ts)` em silver?

**Contexto.** Bronze pode ter múltiplas ingestões do mesmo arquivo
DBC (ex.: ingest manual + auto-trigger noturno). Sem dedup, silver
duplicaria contagens. Filtrar por `_ingest_ts == max(_ingest_ts)`
global perde UFs (Auto Loader divide ingestão em micro-batches com
timestamps diferentes — bug documentado no silver UroPro, commit
fa869cf).

**Decisão.** Pra cada `source_file` (= nome do DBC original, ex.:
`EQSP2412.dbc`), manter SÓ as rows do `_ingest_ts` mais recente.

**Consequências.**
- ✅ **Idempotente vs ingestão dupla**: bronze com 2x dados →
  silver mantém 1x (correto).
- ✅ **Não perde UFs**: Auto Loader em micro-batches não causa
  filtragem global indevida.
- ✅ **Tolerante a re-conversões**: se DATASUS retroativamente
  corrigir um DBC, prevalece a versão mais recente.
- ⚠️ **Custo de groupBy + join**: ~10-15 min em Spark serverless do
  Free Edition para silver completo. Aceitável dada cadência mensal.

---

## ADR-006 — Por quê dicionário canonical extraído por parsing HTML
(não LLM)?

**Contexto.** O CNES tem ~129 combinações `(TIPEQUIP, CODEQUIP)` que
identificam equipamentos. DATASUS publica um catálogo HTML em
`cnes2.datasus.gov.br/Mod_Ind_Equipamento.asp` mas NÃO disponibiliza
CSV consumível por pipelines analíticos.

**Decisão.** Extraímos por parsing HTML direto do catálogo oficial
(URL parâmetros `?VCod_Equip=N&VTipo_Equip=M` mapeiam 1:1 pra nome).
Resultado: 133 entradas validadas em cobertura 100\,% contra snapshot
empírico Dez/2024. Publicado em
`data/reference/cnes_eq_canonical.csv`.

**Consequências.**
- ✅ **Reprodutível**: qualquer um pode re-rodar o parser e validar
  contra snapshot atual.
- ✅ **Auditabilidade**: cada entrada tem fonte rastreável (URL +
  HTML).
- ❌ **Dicionários AI-inferidos foram a fonte do bug original**: o
  dicionário `EQUIPMENT_NAMES` no silver pré-correção (ABR/2026) foi
  gerado por inferência LLM, contendo erros em ~80\,% das entradas.
  ADR seguinte é portanto **forte**: NUNCA usar LLM para gerar
  dicionários ou tabelas de lookup que serão consumidas por código.
- ⚠️ **Dependência de URL externa**: se DATASUS reestruturar o
  CNES2, parser quebra. Mitigado por (a) parser commitado no repo,
  (b) CSV cacheado em `data/reference/`.

---

## ADR-007 — Por quê React + Vite (vs Next.js, Astro, plain HTML)?

**Contexto.** O front do Mirante é dashboard interativo com mapas,
charts e tabelas. Opções consideradas: Next.js (SSR/SSG), Astro
(static site com islands), plain HTML+vanilla JS.

**Decisão.** React + Vite SPA pura, deployada como static site no
GitHub Pages.

**Consequências.**
- ✅ **Hot reload rápido em dev**: Vite < 200ms, vs Webpack ~5s.
- ✅ **Static deployment grátis**: GitHub Pages serve `dist/`
  diretamente, zero servidor, zero custo runtime.
- ✅ **Bundle pequeno**: ~700 KB gzip total (React + recharts +
  maps + xlsx). Aceitável para conteúdo analítico.
- ❌ **SEO restrito**: SPA puro não pré-renderiza. Aceitável
  porque audiência é especialista (referenciada via link direto).
- ❌ **Loading time inicial**: sem SSR, primeiro paint depende de JS
  hidratar. Mitigado por skeleton em todas verticais.
- ⚠️ **Mobile pesado**: 700 KB gzip em 3G demora ~5s. Aceitável
  porque audiência primária é desktop/notebook.

---

## ADR-008 — Por quê CI compila todos os WPs em LaTeX?

**Contexto.** Working Papers acadêmicos tradicionalmente são
distribuídos em PDF. Compilar LaTeX requer ambiente complexo
(TeXLive ~2GB).

**Decisão.** GitHub Actions + `xu-cheng/latex-action` compila TODOS
os `.tex` da pasta `articles/` na cada push, copia PDFs para
`app/public/articles/` antes do build do Vite.

**Consequências.**
- ✅ **Zero setup local**: contribuidores podem editar `.tex` sem
  instalar TeXLive.
- ✅ **PDFs sempre frescos**: cada commit no `.tex` ou em figura
  trigga novo PDF.
- ✅ **Source aberto**: tex + figs + PDF todos versionados; leitor
  pode baixar source via botão "Baixar fonte (.tex)".
- ⚠️ **CI lento**: cada compile leva ~30-40s; 5 WPs adicionam
  ~3 min ao build. Tolerável dada cadência (não é hot path).
- ⚠️ **Erro silencioso pode passar**: se um `.tex` quebrar, CI
  falha, mas restante dos WPs ainda funciona via versões antigas
  cached em `app/public/articles/`. Mitigação: `latexmk_use_xelatex:
  false` + `interaction=nonstopmode -file-line-error` para erros
  óbvios.

---

## ADR-009 — Por quê verticais como datasets independentes (vs schema único)?

**Contexto.** O Mirante tem 5+ verticais (Bolsa Família, Emendas,
Equipamentos, UroPro/SIH, RAIS). Opções: (a) tabela única
`gold_uf_ano_metricas` com todas as métricas como colunas; (b) uma
tabela por vertical, joinable por (UF, Ano).

**Decisão.** Uma tabela por vertical, joinable por (UF, Ano).

**Consequências.**
- ✅ **Schema evolution local**: adicionar nova métrica em UroPro
  não afeta outras verticais.
- ✅ **Pipeline isolado**: falha em RAIS não bloqueia refresh de
  Equipamentos.
- ✅ **JSON exports separados**: front baixa só o que precisa por
  vertical (10-15MB por vertical, vs 100MB se fosse tudo junto).
- ✅ **Cross-vertical opcional**: WP #4 cruza Equipamentos com PBF
  via join client-side ou em script Python ad-hoc, sem
  pré-materializar gold "wide".
- ⚠️ **Joins repetidos**: análises cross-vertical pagam custo de
  join cada vez. Aceitável porque cross-vertical é raro
  (publicação trimestral, não query operacional).

---

## ADR-010 — Por quê tests pytest sobre o gold JSON (não Spark/Databricks)?

**Contexto.** Testes de pipeline data podem rodar (a) contra Spark
local com sample data, (b) contra Databricks via API, (c) contra os
artefatos finais (gold JSON) em CI/local.

**Decisão.** Tests pytest puramente sobre os JSONs versionados em
`data/gold/`. Sem Spark, sem mock de Databricks.

**Consequências.**
- ✅ **CI ultra-rápido**: 13 tests rodam em 0.3s.
- ✅ **Sem dependência de Databricks**: contribuidores podem
  validar localmente.
- ✅ **Verifica o ARTEFATO PUBLICADO**: tests caem se gold for
  republicado errado, não importa o que silver fez.
- ⚠️ **Não cobre lógica de transformação**: bug que produzir gold
  estatisticamente "razoável" mas semanticamente errado pode passar.
  Mitigado por DQ assertions específicas (ex.: `RM 2024 ∈ [3000,
  4500]` baseado em OECD).
- 📋 **Próximo passo**: adicionar tests de regressão em silver via
  PySpark local com sample data (CSV de 100 rows do bronze).

---

## ADR-011 — Por quê Free Edition do Databricks (vs AWS/GCP/Azure)?

**Contexto.** O projeto Mirante é open-source sem orçamento. Cloud
managed services (AWS Glue, BigQuery, Azure Synapse) cobram por
processamento; Databricks Free Edition oferece serverless sem custo.

**Decisão.** Databricks Free Edition (compute serverless 14 dias
gratuitos rotativos, com limite de DBUs).

**Consequências.**
- ✅ **Zero custo runtime**: Databricks Free Edition mantém
  catálogo + Delta tables + serverless compute em quotas razoáveis.
- ✅ **Bundle deployment via CLI**: `databricks bundle deploy`
  facilita CI/CD.
- ⚠️ **Quota limits**: cluster sleeping após inatividade, run
  scheduling com limite de 24h/dia. Suficiente pra cadência mensal.
- ⚠️ **Lock-in**: pipeline depende de Databricks-specific features
  (Auto Loader, Unity Catalog). Migração pra outro stack exigiria
  reescrita de bronze layer.

---

## ADR-012 — Por quê Recharts (vs Plotly, Visx, D3 puro)?

**Contexto.** O front-end do Mirante precisa renderizar charts
analíticos: barras, linhas, áreas empilhadas, scatters com regressão,
choropleths brasileiros. Opções consideradas:

- **Plotly**: choropleth pronto, interatividade rica, mas bundle
  pesado (~3 MB minified) e estilo padrão difícil de customizar pra
  estética ABNT.
- **Visx (Airbnb)**: composição em React idiomática, baseada em D3
  primitivos. Excelente flexibilidade, mas exige montar cada chart
  da raiz (axes, tooltips, escalas). Custo alto pra time-to-market.
- **Recharts**: API declarativa em JSX, bundle ~150 KB, suporta
  os charts comuns (Line, Bar, Area, ComposedChart, Pie, Scatter)
  out-of-box. Não tem choropleth.
- **D3 puro**: mais flexível, mas afasta-se do paradigma React e
  exige `useEffect` + manipulação imperativa do DOM.

**Decisão.** Recharts pra todos os charts cartesianos +
`react-simple-maps` (sobre `d3-geo`) pra mapas choropleth. D3
auxiliares (`d3-scale`, `d3-scale-chromatic`) usados pra paletas
Cividis e escalas customizadas.

**Consequências.**
- ✅ **Bundle leve**: Recharts (~150 KB) + react-simple-maps
  (~80 KB) somam menos que Plotly sozinho.
- ✅ **API React-idiomática**: `<LineChart><Line dataKey="..."/></LineChart>`
  encaixa naturalmente em componentes funcionais com hooks.
- ✅ **Estilo ABNT-friendly**: Recharts permite controle fino de
  cores via paleta Cividis e tipografia serif sem fight com defaults.
- ⚠️ **Choropleth depende de outra lib**: react-simple-maps tem
  manutenção mais lenta, mas a API é estável e o uso é restrito a
  3 verticais (PBF, UroPro, Equipamentos). Não bloqueador.
- ⚠️ **Sem interatividade Vega-Lite-style**: hover, tooltips, zoom
  funcionam bem; pan + brush + linked views exigiriam escalar pra
  Vega-Lite ou Observable Plot. Trade-off aceito; agenda de
  interatividade rica fica pra Observable embed paralelo (ver
  peer review WP #6, Design Web).
- ⚠️ **Recharts não suporta SSR perfeitamente**: charts renderizam
  client-side. Aceitável porque o site é SPA estático.

---

## ADR-013 — Por quê deflator IPCA Dez/2021 = 1.0 como base?

**Contexto.** Comparações monetárias entre anos exigem deflação. As
verticais Mirante (Emendas, PBF, UroPro, Equipamentos) precisam de
base temporal comum pra que valores sejam comparáveis cross-vertical
e cross-year. Opções: (a) deflacionar pra ano corrente (móvel), (b)
ano-base fixo.

**Decisão.** Ano-base fixo: Dez/2021. Indicador `deflator_to_2021`
em `silver.ipca_deflators_2021` com Dez/2021 = 1.0 por construção.

**Consequências.**
- ✅ **Estabilidade dos números entre publicações**: \rs{} 100 mi
  em 2025 deflacionados não mudam quando publicamos um WP em 2027.
- ✅ **Ano-base recente**: Dez/2021 é próximo o suficiente do
  presente que valores deflacionados são intuitivos pra leitores
  brasileiros (não chocam como uma base 1995 chocaria).
- ✅ **Permite comparação cross-vertical sem ambiguidade**:
  Emendas, PBF e UroPro todos reportam `*_2021` na mesma escala.
- ⚠️ **Eventual revisão**: quando o presente estiver longe de
  2021 (ex.: 2030), pode fazer sentido rebasear pra Dez/2027 ou
  similar. Migração custa só re-rodar `silver.ipca_deflators_2021`
  com `BASE_YEAR=2027` parâmetro — schema do silver não muda.
- ⚠️ **Não captura inflação setorial**: IPCA é cesta de consumo
  geral, não saúde. Pra análises focadas em saúde, IPCA-Saúde ou
  deflator setorial seriam mais apropriados (não usado hoje).

---

## ADR-014 — Por quê dedup `MAX(qt_sus, qt_priv)` na silver de Equipamentos?

**Contexto.** O CNES permite que clínica declare a *mesma máquina
física* em duas linhas: uma com `IND_SUS=1` (disponível ao SUS) e
outra com `IND_SUS=0` (disponível ao privado). A primeira versão da
silver computava `total_avg = sus_total_avg + priv_total_avg`,
double-contando essa máquina. Resultado: RM nacional 2025 = 7,592
unidades (\,$\sim$\,35,6/Mhab, \,$\sim$\,2× a mediana OECD 17/Mhab).

**Decisão.** Pivotar `IND_SUS` em duas colunas `qt_sus` e `qt_priv`
por (CNES, mês, equipment\_key); definir `qt_total = GREATEST(qt_sus,
qt_priv)`; agregar média anual sobre `qt_total` em vez de
`qt_sus + qt_priv`. Mantém `sus_total_avg` e `priv_total_avg` como
subconjuntos (podem incluir dual-flagged).

**Consequências.**
- ✅ **Total deduplicado bate com OECD**: pós-fix RM nacional 2025
  cai pra \,$\sim$\,3,5–4,5K unidades, dentro da banda de 10–25/Mhab
  esperada.
- ✅ **Invariante explícito**: `sus_total_avg + priv_total_avg ≥
  total_avg` (igualdade ⟺ sem dual-flag). Diferença mede
  o `overlap_pct` reportado no DQ check.
- ✅ **Documentação publicável**: WP #6 §4.3 documenta o problema
  e o fix; primeira documentação pública do *double-count* via
  dual-flag em CNES.
- ⚠️ **Shares no front-end podem somar >100\%**: uma máquina
  dual-flagged é 100\% disponível ao SUS \textit{e} 100\% ao
  privado. Front precisa de copy explicando isso. Trade-off
  aceito como matematicamente correto.
- ⚠️ **Interpretação conservadora**: o fix assume que dual-flag =
  mesma máquina. Cenário patológico (CNES com 2 SUS-only e 3
  Priv-only no mesmo mês = 5 máquinas distintas) é sub-contado
  como `MAX(2,3) = 3`. Abordagem alternativa (média anual sobre
  AVG por linha) está documentada no DQ check side-by-side
  pra validação empírica.

---

## ADR-015 — Por quê cap universal "drop ano corrente" no `loadGold`?

**Contexto.** Várias fontes (CGU, DATASUS, MTE) atualizam seus
agregados \textit{durante} o ano corrente — o ano-em-curso é
\textit{parcial} até Dezembro fechar. Comparar Brasil-2025-completo
com Brasil-2026-parcial é apples-to-oranges. Os silvers/golds têm
filtros pra dropar ano parcial, mas o gold publicado no Git pode
ter ficado stale (silver não rerodou após virada de ano), e cada
rota do front replicava lógica de filtro com sutilezas de erro.

**Decisão.** Filtro universal `Ano < new Date().getFullYear()`
aplicado no `loadGold` em `app/src/lib/data.js`. Detecta a chave
de ano (`Ano` ou `ano`) por shape; passa direto se nenhuma das
duas existir (RAIS pré-pipeline-rodar, no-op).

**Consequências.**
- ✅ **Defesa em profundidade**: silver/gold notebooks tentam
  dropar parcial; loadGold é o último firewall. Mesmo se gold
  estiver stale, o front nunca mostra ano parcial.
- ✅ **Zero duplicação de lógica**: as 5 verticais herdam o cap
  automaticamente. Nova vertical funciona sem código adicional.
- ✅ **Reversível por vertical**: se uma vertical futura precisar
  mostrar ano-em-curso (ex.: dashboard operacional em tempo
  real), pode chamar `loadGold(file, { keepCurrentYear: true })`.
  Hoje o flag não existe, mas o ponto de extensão é claro.
- ⚠️ **Vira "verdade" no cliente**: a lógica é JS, validável
  apenas via Vitest. Mitigado por o silver/gold também
  filtrarem (defesa em profundidade) e pelos golds publicados
  no Git serem revisáveis no PR.

---

## Apêndice — princípios transversais

1. **Tudo aberto, tudo versionado.** Código em Git, dados em Git
   (gold), papers em Git (tex+pdf+figs), dicionários em Git
   (CSV). Reprodutibilidade total por design.
2. **STRING-ONLY na bronze**. Casts apenas em silver+. Permite
   audit trail fiel à fonte.
3. **Documentação como código**. ADRs aqui, COMMENT ON TABLE no
   Unity Catalog, docstrings em notebooks. Código sem documentação
   é considerado bug.
4. **Testes como contrato**. `tests/` valida invariantes do
   artefato publicado. Mudou um número? CI quebra.
5. **Reviewers simulados como guia.** Pareceres internos
   (`memory/peer_review_*.md`) cobrem ângulos de Eng. Dados,
   Finanças e HCI antes de qualquer submissão real.

---

**Mantenedor:** Leonardo Chalhoub
**Repositório:** https://github.com/leonardochalhoub/mirante-dos-dados-br
**Licença:** MIT (código), CC BY 4.0 (textos)

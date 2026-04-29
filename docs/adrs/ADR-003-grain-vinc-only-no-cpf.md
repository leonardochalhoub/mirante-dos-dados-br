# ADR-003 · Grain VINC-only · ausência de CPF na bronze

**Status:** Accepted (constraint da fonte, não decisão técnica reversível)
**Deciders:** PDET/MTE (titular dos dados); Mirante apenas registra a consequência
**Supersedes:** —

## Contexto

PDET/MTE publica RAIS em DOIS datasets distintos:

1. **RAIS Vínculos Públicos** (VINC) — 1 linha = 1 contrato de trabalho-ano. Inclui CBO, CNAE, salário, motivo desligamento, sexo, idade, escolaridade, raça (2003+), tempo emprego, etc. **Não inclui CPF nem PIS** (PII protegida).

2. **RAIS Estabelecimentos Públicos** (ESTAB) — 1 linha = 1 estabelecimento-ano. Inclui CNPJ, natureza jurídica, tipo de estabelecimento, qtd vínculos, atividade econômica. **Inclui CNPJ** (registro público).

`mirante_prd.bronze.rais_vinculos` ingere apenas o dataset VINC. ESTAB foi explicitamente filtrado fora (regex `(?i)(estb|rais_estab)` no path glob; ver `_filter_vinc()` em bronze code).

A bronze TAMBÉM removeu vestígios de runs antigas que misturavam ESTAB+VINC (~200M linhas ESTAB contaminavam bronze.rais_vinculos antes do fix de 2026-04-28).

## Decisão

`bronze.rais_vinculos` é **VINC-only, sem identificador único de trabalhador**. Implicações que devem ser declaradas em qualquer manuscrito que use esses dados:

### O que NÃO se pode fazer

1. **Job-to-job mobility individual** — não dá pra rastrear o mesmo trabalhador entre 2 contratos consecutivos (sem CPF/PIS). Análises de mudança de emprego em nível individual NÃO são possíveis.
2. **Wage growth pessoal** — não dá pra acompanhar o salário do João Silva ao longo de 10 anos.
3. **Career path** — não dá pra ver "começou em CBO X, virou CBO Y, depois Z".
4. **Análise de empresa** — `bronze.rais_vinculos` não tem CNPJ. `COUNT(DISTINCT _empresa)` é impossível. Para isso, precisa do dataset ESTAB (ingestão futura).
5. **Sobrevivência empresarial** — entrada/saída de firmas exige ESTAB.

### O que se pode fazer

1. **Pseudo-painel via combinação** de (idade, sexo, raça, município, CBO, CNAE, mês admissão) — estatística, não rastreamento. Útil pra heterogeneidade de tratamento em DiD.
2. **Painel município × setor × ano** — agregação suficiente pra DiD/TWFE/Synthetic Control regional ou setorial. **É o padrão de referência da literatura RAIS pública** (Engbom & Moser 2022, Lemos 2009, Corseuil et al. 2021).
3. **Análise de fluxo agregado** — admissões, demissões, motivo de desligamento, tempo médio de emprego — todas agregáveis sem CPF.
4. **Decomposição cross-sectional** — distribuição de gênero, raça, escolaridade por setor/UF/ano.

### Workarounds de mobilidade individual (limitados)

- **Pseudo-painel sintético**: cell-level fixed effects em (município × idade × sexo × escolaridade × cbo) tratam células como "indivíduos". Não é mobilidade real, mas captura algumas dinâmicas demográficas.
- **Match com PNAD-Contínua via município**: PNAD pega indivíduos via amostra; cruzar agregados RAIS com microdados PNAD em município pode aproximar wage dynamics. Linha de pesquisa aberta.
- **Acesso restrito ao painel CPF identificado**: Fundação Anpec/Cedeplar/IPEA têm acordos com MTE pra acesso a microdados RAIS identificados (com CPF criptografado). Mirante NÃO tem esse acesso e NÃO planeja solicitar (foco no dado público replicável).

## Consequências

### Positivas

- **Compliance LGPD**: bronze pública (zero PII direta). Pode ser publicada como Iceberg via UC REST sem restrição.
- **Reprodutibilidade**: qualquer pesquisador pode baixar os mesmos arquivos PDET FTP e reproduzir o pipeline.
- **Foco em política pública**: análise causal de programas (BEm, BF, Reforma Trab) é viável SEM CPF — usa painel município/setor.

### Negativas

- **8 dos 8 pipelines ML do panorama §10** são limitados:
  - Forecasting agregado: OK
  - Wage gap explainer: OK em grupos demográficos, NÃO em indivíduos
  - Anomaly detection: OK em padrões estatísticos, NÃO em fraudes individuais
  - Clustering municipal: OK
  - **Churn prediction individual: NÃO POSSÍVEL** sem CPF (downgrade pra P(churn|grupo demográfico))
  - Simulação contrafactual de SM: OK em agregados
  - Causal BEm: OK em painel município×setor
  - Embeddings CBO: OK (coocorrência empresa-CBO se tivéssemos ESTAB; sem ESTAB, fica coocorrência município-CBO)

### Trade-offs explícitos

- **Não solicitamos** acesso restrito a CPF mesmo que melhoraria várias análises. Trade-off: análise pública replicável > análise privada superior.
- **Não combinamos** com CadÚnico/Bolsa Família via CPF. Trade-off: análise BF feita em painel município (proxy ATT, não TT individual). Se acordo MTE+MDS for possível no futuro, esta restrição é reavaliável.

## Padrão de declaração em manuscritos

> **LIMITAÇÕES (parágrafo obrigatório):**
> Os microdados RAIS Vínculos Públicos não incluem CPF nem PIS — identificadores
> individuais de trabalhador. As análises são em nível de painel agregado
> (município × setor × ano), com erro padrão clusterizado nesse nível. Não foi
> possível rastrear trabalhadores específicos entre vínculos consecutivos, o
> que limita análises de mobilidade ocupacional individual e wage dynamics
> pessoais. A inferência causal aqui apresentada estima ATT (Average Treatment
> Effect on the Treated) em nível de cluster, não em nível individual.

## Referências

- Bronze pipeline: `pipelines/notebooks/bronze/rais_vinculos.py` (`_filter_vinc()`)
- ADR-001 · dual reader per-year (descreve como ESTAB foi filtrado)
- Conselho 2026-04-28 finanças: "Sem identificador de trabalhador (CPF não público) — análise é em nível de painel município×setor, não individual" — alerta crítico pré-submissão
- Lemos (2009), "Minimum Wage Effects in a Developing Country", Labour Economics — referência metodológica usando RAIS painel
- Engbom & Moser (2022), "Earnings Inequality and the Minimum Wage", AER — usa RAIS identificado (CPF criptografado, acesso restrito)

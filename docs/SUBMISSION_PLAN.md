# Mirante dos Dados — Plano de Submissão a Periódicos

> Última atualização: 2026-04-26 · v1.0
>
> Documento operacional para mover os Working Papers do Mirante de
> "publicação interna no GitHub" para "peer review formal em
> periódico revisado". Endereça frente (e) da agenda do
> WP #6 v2 §9 e responde aos peer reviews fake (Eng. Dados,
> Finanças, Design Web) registrados em `memory/peer_review_*_wp4.md`
> e `peer_review_*_wp6.md`.

---

## 1. Estratégia geral

**Princípio**: cada WP tem um "primeiro alvo" (journal mais alinhado +
menor custo de revisão pré-submissão) e um "alvo backup" (mais
prestigiado mas com mais revisão necessária). Submeter um WP por vez,
em ordem de menor risco para maior, construindo histórico de
publicação progressivamente.

**Sequenciamento sugerido** (ordem de submissão):

| Ordem | WP | Journal alvo | Por quê primeiro |
|------:|----|--------------|------------------|
| 1º    | WP #1 (Emendas) | **RAP — Revista de Administração Pública** (FGV/EBAPE, Qualis A1 Adm. Pública) | Escopo fechado, descritivo defensável, foco institucional ABNT-friendly |
| 2º    | WP #5 (UroPro 17 anos) | **Revista de Saúde Pública** (FSP-USP, Qualis A1 Saúde Coletiva) | Longitudinal, narrativa COVID/represa pronta, achado clínico forte |
| 3º    | WP #2 (PBF/AB/NBF) | **Revista Brasileira de Economia** (FGV-EPGE, Qualis A1 Economia) | Análise institucional clara, comparação inter-regimes |
| 4º    | WP #4 v2 (Equip.×Parkinson + DiD EC 86) | **Cadernos de Saúde Pública** (FIOCRUZ, Qualis A1 Saúde Coletiva) | Tem identificação causal pós-DiD; saúde + epidemiologia |
| 5º    | WP #3 (UroPro cross-vert) | **Cadernos de Saúde Pública** OU **International Journal for Equity in Health** | Cross-vertical pioneer, health equity angle |
| 6º    | WP #6 v2 (panorama cross-vert) | **Lancet Regional Health — Americas** | Mais ambicioso, requer revisão maior; após histórico de publicação |
| 7º    | Methodological case study (dual-flag dedup) | **Empirical Software Engineering** (EMSE, Springer) | Spinoff metodológico — case study isolado |

**Cadência alvo**: 1 submissão a cada 2–3 meses para construir
pipeline. Total ~12–18 meses para 7 submissões.

---

## 2. Mapping detalhado WP → Journal

### WP #1 — Emendas Parlamentares (CHALHOUB, 2026a)

**Resumo do paper**: distribuição espacial e execução orçamentária
de emendas (RP6/RP7/RP8/RP9), 2014–2025, com análise da inflexão
EC 86/2015 (impositividade) e EC 100/2019 (RP-9).

**Alvo primário**: **Revista de Administração Pública (RAP)**.
- Editor: FGV/EBAPE.
- Qualis: A1 (Administração Pública).
- ISSN: 0034-7612 (impressa), 1982-3134 (eletrônica).
- DOI prefix: `10.1590/0034-`.
- Aceita português. Foco em federalismo, governança, políticas públicas.
- Open access (SciELO).
- Tempo médio de revisão: 4–6 meses (declarado pelo periódico).

**Alvo backup**: Brazilian Political Science Review (BPSR), Dados.

**Pre-submission checklist específico**:
- [ ] Adicionar painel longitudinal `(UF × Ano)` com efeitos fixos
  (Finanças peer review crítica forte).
- [ ] *Robustness checks*: excluir DF (UF *outlier*), log-transformação
  de valores `per capita`.
- [ ] Citar EC 86/2015 e EC 100/2019 explicitamente como
  descontinuidades institucionais; idealmente fazer pelo menos um
  RDD em torno de uma delas (parallel window's `causal_analysis_emendas_rm.py`
  é um bom ponto de partida).
- [ ] Adaptar estrutura ABNT atual para template RAP (margem,
  tipografia, espaçamento).
- [ ] Carta de submissão (template seção 4 abaixo).

---

### WP #5 — UroPro 17 anos (CHALHOUB, 2026f)

**Resumo do paper**: análise longitudinal 2008–2025 de cirurgia
uroginecológica no SUS — eficiência clínica (queda 40% permanência),
choque pandêmico (queda 57% em 2020–21), represa cirúrgica em
escoamento 2024–25.

**Alvo primário**: **Revista de Saúde Pública** (FSP-USP).
- ISSN: 0034-8910.
- Qualis: A1 (Saúde Coletiva).
- Aceita português. Foco em saúde pública, epidemiologia,
  organização de serviços de saúde.
- Open access (SciELO).
- Tempo médio: 6–8 meses.

**Alvo backup**: BMC Public Health (open access internacional;
inglês obrigatório), Cadernos de Saúde Pública (FIOCRUZ).

**Pre-submission checklist**:
- [ ] Materializar o dedup do silver UroPro (já documentado em
  silver/sih_uropro_uf_ano.py + WP #5 §3.3) e re-rodar gold.
- [ ] Validar números pós-dedup contra o que está no paper.
- [ ] Adicionar painel longitudinal `(UF × Ano)` para análise
  de tendência por UF (Finanças peer review).
- [ ] *Survival analysis* da represa cirúrgica: estimar quando volume
  retorna à tendência pré-pandêmica via modelo paramétrico.

---

### WP #2 — Bolsa Família, Auxílio Brasil, Novo Bolsa Família (CHALHOUB, 2026b)

**Resumo**: unificação dos três programas de transferência de renda
2013–2025, com decomposição cobertura × valor por beneficiário.

**Alvo primário**: **Revista Brasileira de Economia (RBE)**, FGV-EPGE.
- ISSN: 0034-7140.
- Qualis: A1 (Economia).
- Aceita português. Foco em macroeconomia, economia pública,
  desigualdade.
- Open access (SciELO).

**Alvo backup**: Estudos Econômicos (FEA-USP), Pesquisa e Planejamento
Econômico (IPEA), World Development (internacional).

**Pre-submission checklist**:
- [ ] **Causal ID**: implementar RDD em torno de MP 1.061/2021
  (transição PBF → Auxílio Brasil) com janela ±90 dias. Outcome
  candidatos: valor *per capita*, cobertura, desigualdade entre UFs.
  *Esse é o experimento mais natural pra essa transição institucional.*
- [ ] Comparação cross-program de elasticidade-renda entre PBF
  (até 2021), AB (2021–22) e NBF (2023+).
- [ ] Cobertura PBF como dependente, com *covariates*: PIB pc,
  desemprego, taxa de informalidade.

---

### WP #4 v2 — Equipamentos × Parkinson + DiD EC 86 (CHALHOUB, 2026e)

**Resumo**: distribuição de RM/CT/PET/SPECT como infraestrutura
diagnóstica de Parkinson, com DiD em torno de EC 86/2015.

**Alvo primário**: **Cadernos de Saúde Pública (CSP)** (FIOCRUZ).
- ISSN: 0102-311X.
- Qualis: A1 (Saúde Coletiva).
- Aceita português. Foco em epidemiologia, saúde coletiva, política
  de saúde.
- Open access (SciELO).
- Tempo médio: 5–7 meses.

**Alvo backup**: Health Policy and Planning, BMJ Open
(internacional, inglês).

**Pre-submission checklist**:
- [ ] Validar resultados DiD contra placebo (UFs sem aumento
  proporcional de emendas como controle).
- [ ] Discutir explicitamente as ameaças a validade interna
  (selection on unobservables, *common trends* assumption).
- [ ] Adicionar referência explícita à literatura epidemiológica
  brasileira sobre Parkinson (revisão da literatura mais ampla).

---

### WP #3 — UroPro cross-vertical (CHALHOUB, 2026d)

**Resumo**: cruzamento UroPro × PBF × Emendas como estudo de
desigualdade em saúde + paradoxo das emendas.

**Alvo primário**: **Cadernos de Saúde Pública** OU
**International Journal for Equity in Health (IJEH)**.
- IJEH: BMC, open access internacional, ISSN 1475-9276.
- Qualis equivalente: A1 (Saúde Coletiva).
- Inglês obrigatório.
- Tempo médio: 3–5 meses.

**Alvo backup**: Lancet Regional Health — Americas, Saúde em Debate.

**Pre-submission checklist**:
- [ ] **Tradução completa para inglês** se for IJEH (revisão por
  *native speaker* obrigatória).
- [ ] *Robustness checks*: outliers, log-transform, regressão
  multivariada com PIB pc + densidade médica.
- [ ] Adicionar painel longitudinal (não só *cross-section* 2025).
- [ ] Citar literatura comparada de health equity em sistemas
  universalistas (Canadá, UK).

---

### WP #6 v2 — Panorama integrado cross-vertical (este paper)

**Resumo**: agregador cross-vertical (Equipamentos × PBF × Emendas
× UroPro) com foco em trio de neuroimagem.

**Alvo primário**: **Lancet Regional Health — Americas** (Lancet
group, Elsevier).
- Qualis: equivalente A1 internacional.
- ISSN: 2667-193X.
- Open access.
- Inglês obrigatório.
- Foco em saúde pública nas Américas, com ênfase em análises
  multi-país e multi-fonte.
- Tempo médio: 2–4 meses (rapid review for short reports).

**Alvo backup**: Cadernos de Saúde Pública, Health Policy and
Planning (Oxford).

**Pre-submission checklist**:
- [ ] **Materializar dedup no gold** (Eng. Dados crítica) — re-rodar
  silver Equipamentos.
- [ ] Implementar pelo menos UM RDD em torno de descontinuidade
  institucional. EC 86/2015 ou MP 1.061/2021.
- [ ] *Robustness checks*: log-transformação, exclusão de
  *outliers*.
- [ ] Tradução completa para inglês.
- [ ] Reduzir tamanho para limite (~6.000 palavras + 6 figuras
  típico em journal-format).

---

### Spinoff metodológico — Dual-flag dedup case study

**Resumo**: documentação do bug histórico (`total = sus + priv` →
double-count) e do fix metodológico (MAX por CNES-mês). Inclui
side-by-side comparison de duas abordagens (MAX vs. AVG simples).

**Alvo primário**: **Empirical Software Engineering (EmSE)**, Springer.
- ISSN: 1382-3256.
- Qualis: A1 (Computação).
- Inglês obrigatório.
- Foco em estudos empíricos de engenharia de software, incluindo
  data engineering e pipeline robustness.

**Alvo backup**: ACM Transactions on Software Engineering and
Methodology (TOSEM), Journal of Systems and Software.

**Pre-submission checklist**:
- [ ] Tornar o paper auto-contido (não exige conhecimento prévio
  do Mirante).
- [ ] Adicionar replicação em pelo menos UM outro dataset CNES
  (idealmente fora de equipamentos — talvez médicos ou leitos).
- [ ] Quantificar impacto do bug em outras análises públicas
  brasileiras de CNES (varredura de literatura).
- [ ] Submeter código e dados como replication package (Zenodo).

---

## 3. Pré-submissão: checklist transversal (todos os WPs)

Estes itens aplicam-se a TODOS os WPs antes de qualquer submissão.

### 3.1 Endereçar peer reviews fake

Os peer reviews simulados em `memory/peer_review_*_wp4.md` e
`peer_review_*_wp6.md` cobrem ângulos que avaliadores reais cobririam.
Antes de cada submissão, revisitar e endereçar especificamente:

- **Eng. Dados**: ARCHITECTURE.md ✓, tests ✓ (parallel window),
  dedup materializado em gold ⏳, schema validation cross-vertical ⏳.
- **Finanças**: identificação causal ⏳ (DiD EC 86 in progress),
  painel longitudinal ⏳, *robustness checks* ⏳, log-transform ⏳.
- **Design Web**: design-system docs ✓, interatividade Vega-Lite ⏳,
  audit Lighthouse ⏳, focus management em modais ⏳.

### 3.2 Reproducibility package

Cada submissão deve vir com:

- Link público para o repositório Mirante no estado correspondente
  (snapshot tag ou commit SHA).
- DOI Zenodo para o release específico que reproduz os números do
  paper.
- Instruções de execução em `README.md` da release.
- Hash MD5/SHA256 dos golds JSON usados no paper (anexar como
  apêndice ou *supplementary material*).

### 3.3 Inglês (para journals internacionais)

- Revisão por *native speaker* — proofread profissional ou colega de
  pós-graduação.
- Verificar consistência terminológica (e.g.\ *equipment* vs.
  *equipamento*, *poverty* vs. *pobreza*, *Bolsa Família* não traduzir).
- Abstract e *highlights* em inglês exigem revisão extra (são as
  primeiras impressões dos *editors*).

### 3.4 Conformidade ABNT (para journals brasileiros)

- Verificar template do periódico-alvo (RAP usa NBR 6022, CSP usa
  formato próprio mas similar).
- Tabelas e figuras com fonte explícita.
- Referências em ordem alfabética NBR 6023.
- Espaçamento, margens, tipografia conforme template.

---

## 4. Cover letter — template

```
[Sua cidade, data]

[Editor-Chefe / Nome do periódico]

Prezado(a) Editor(a),

Submeto à apreciação de [PERIÓDICO] o manuscrito intitulado
"[TÍTULO DO WP]", de minha autoria, para publicação na
seção [SEÇÃO PROPOSTA — Artigo de Pesquisa / Comunicação Breve].

Este trabalho [CONTRIBUIÇÃO ORIGINAL EM 1-2 FRASES; ex.: "documenta
empiricamente, com microdados públicos integrados de 4 verticais
analíticas (CNES, CGU/PBF, CGU/Emendas, SIH-AIH-RD), a relação entre
infraestrutura de neuroimagem e gradiente de pobreza estrutural no
Brasil entre 2013 e 2025"].

A novidade do trabalho relativamente à literatura existente é
[POSICIONAMENTO]:
- [DIFERENCIADOR 1; ex.: "primeiro estudo a documentar o paradoxo
  das emendas no domínio de infraestrutura de saúde, replicando o
  achado já existente no domínio de procedimentos cirúrgicos"];
- [DIFERENCIADOR 2; ex.: "uso de pipeline aberto e auditável
  (medallion architecture sobre Apache Spark e Delta Lake) que
  garante reprodutibilidade integral pelos pares"];
- [DIFERENCIADOR 3; ex.: "documentação inédita de bug metodológico
  no módulo CNES Equipamentos (double-count via dual-flag IND_SUS)
  com fix metodológico apresentado e validado"].

Os dados subjacentes são todos públicos (DATASUS, CGU, IBGE/SIDRA,
BCB) e o pipeline analítico está disponível em código aberto sob
licença MIT em
https://github.com/leonardochalhoub/mirante-dos-dados-br
(commit [SHA] / release [TAG]). O manuscrito anexa o repositório
como *supplementary material* para revisão de reprodutibilidade.

Declaro que o manuscrito é original, não foi publicado anteriormente
nem está sob avaliação em outro periódico. Não há conflito de
interesses a declarar. O trabalho não recebeu financiamento externo;
os recursos computacionais utilizados estão sob *Free Edition* do
Databricks e GitHub Pages para distribuição. O *peer review*
informal interno do projeto está documentado nos arquivos
`memory/peer_review_*.md` do repositório.

Sugiro como possíveis revisores:
1. [REVISOR SUGERIDO 1 — nome, instituição, área];
2. [REVISOR SUGERIDO 2 — nome, instituição, área];
3. [REVISOR SUGERIDO 3 — nome, instituição, área].

Solicito, gentilmente, que NÃO sejam considerados como revisores:
[NENHUM ESPECIFICADO ou conflito declarado].

Coloco-me à disposição para esclarecimentos.

Cordialmente,

Leonardo Chalhoub
[Afiliação atual / Independente]
[E-mail / ORCID]
```

---

## 5. Identificação de revisores sugeridos

**Critério**: pesquisadores ativos na área que tenham publicado nos
últimos 3 anos sobre tema próximo. Boas fontes:

- Plataforma Sucupira (CAPES) para programas brasileiros.
- ORCID para perfis individuais.
- DBLP / Google Scholar para histórico de publicação.
- Comissões editoriais do próprio periódico-alvo.

**Política**: 3 sugestões por submissão; idealmente um internacional
e dois nacionais para journals BR; oposto para journals internacionais.

**Conflitos**: declarar coautoria, orientação ou afiliação compartilhada
nos últimos 5 anos.

---

## 6. Pós-submissão — gestão do processo

### 6.1 Tracking

Manter `docs/SUBMISSION_LOG.md` privado (não comitar — adicionar a
`.gitignore`) com:

- Data de submissão por WP.
- Estado atual (sob revisão / decisão recebida / aceito / rejeitado).
- Comentários dos revisores (resumo).
- Próxima ação requerida.

### 6.2 Resposta a revisores

Para *major revision*:
- Rebuttal point-by-point por comentário.
- Marcar mudanças no manuscrito com cor (revisão Word) ou diff
  destacado (LaTeX).
- Não rebater sem evidência — concordar quando o revisor está
  certo.

Para *rejection*:
- Não disputar: agradecer e seguir para o backup.
- Aproveitar comentários para fortalecer o manuscrito antes do
  resubmit.

### 6.3 Pós-aceitação

- DOI permanente no Mirante (ligar release do GitHub ao DOI
  do artigo).
- Adicionar PDF aceito ao site Mirante (rota da vertical
  correspondente).
- Atualizar CV / Lattes.
- Anunciar nas redes profissionais.

---

## 7. Cronograma sugerido

| Mês  | Ação                                                       |
|------|------------------------------------------------------------|
| Mês 1 | Revisar WP #1 endereçando Finanças peer review (RDD/painel) |
| Mês 2 | Submeter WP #1 → RAP                                       |
| Mês 3 | Revisar WP #5 endereçando Finanças peer review              |
| Mês 4 | Submeter WP #5 → Revista de Saúde Pública                   |
| Mês 5 | Revisar WP #2 implementando RDD MP 1.061                    |
| Mês 6 | Submeter WP #2 → RBE                                        |
| Mês 7-9 | Receber primeiras decisões; revisar WP #4 v2 + WP #3        |
| Mês 10 | Submeter WP #4 v2 → Cadernos de Saúde Pública              |
| Mês 11 | Submeter WP #3 → CSP ou IJEH                               |
| Mês 12 | Preparar WP #6 v2 → Lancet Regional Health (tradução EN)   |
| Mês 13–15 | Revisões e *resubmits*                                  |
| Mês 16+ | Methodological case study → EmSE                         |

---

## 8. Recursos

- **Template LaTeX dos periódicos**:
  - RAP: https://www.rap.ebape.fgv.br/
  - CSP: https://cadernos.ensp.fiocruz.br/
  - IJEH: https://equityhealthj.biomedcentral.com/
  - LRH-A: https://www.thelancet.com/journals/lanam
- **Plataformas de submissão**:
  - SciELO Submit (RAP, RSP, CSP, RBE).
  - Editorial Manager (BMC journals — IJEH).
  - Elsevier Editorial System (LRH-A, EmSE).
- **Help**:
  - Editora UFRJ (autores) — guia de publicação acadêmica.
  - SciELO — guia de submissão para periódicos brasileiros.

---

**Mantenedor**: Leonardo Chalhoub
**Última revisão**: 2026-04-26
**Próxima revisão programada**: 2026-07-26 (após primeira submissão)

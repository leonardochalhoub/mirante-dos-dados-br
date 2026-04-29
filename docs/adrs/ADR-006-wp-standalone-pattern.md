# ADR-006 — WP Standalone (Working Papers sem Pipeline Databricks)

**Data:** 2026-04-29
**Status:** Aceito
**Origem:** Reunião #5 do Conselho do Mirante — pendência crítica da cadeira
de Engenharia de Software ("Sem ADR para o padrão 'standalone' — escopo da
plataforma fica indefinido para futuros WP#10+ não-pipeline").
**Contexto histórico:** WP#9 v2.0 (O Cálculo Ausente) é o primeiro Working
Paper do Mirante de natureza distinta dos WP#1–#7 (que são pipelines
medallion sobre microdados públicos brasileiros).

---

## Contexto

Até a v6.0 do Mirante, todos os Working Papers (WP#1–#7) seguiram um padrão
arquitetural homogêneo:

1. **Bronze layer:** ingest de microdados oficiais (PBF/CGU, CNES/DATASUS,
   SIH/DATASUS, Emendas/CGU, RAIS/PDET) → Delta Lake STRING-ONLY no
   Databricks.
2. **Silver layer:** limpeza, tipagem, normalização → tabelas analíticas
   persistidas em `mirante_prd.silver.*`.
3. **Gold layer:** agregações UF×Ano (ou Município×Ano) → JSON exportado
   para `data/gold/*.json` + commit no repo.
4. **Vertical web:** rota React consome o JSON gold + renderiza KPIs,
   ranking, mapa coroplético, série temporal.
5. **Working Paper:** artigo em LaTeX (ABNT) com identificação causal
   (DiD/TWFE/Conley HAC), figuras com identidade visual editorial Mirante,
   submissão a periódico.

WP#9 (O Cálculo Ausente) é uma **revisão sistemática + comparada** sobre
currículos oficiais de matemática em 10 países + IB. **Não há microdados
públicos brasileiros a serem ingeridos**; as fontes primárias são documentos
curriculares oficiais (PDFs de ministérios), séries OECD/PISA já agregadas
e literatura pedagógica acadêmica. O argumento é prescritivo — não exige
identificação causal sobre choque institucional.

**A pergunta:** o Mirante aceita esse tipo de WP como vertical de primeira
classe? E se sim, sob quais condições?

A cadeira de Engenharia de Software flagged a ausência desta decisão
arquitetural na Reunião #5: "Se amanhã um contribuidor quiser submeter um
WP#10 de revisão bibliográfica sobre ensino de física, não há ADR que diga
'é ou não é escopo da plataforma'."

---

## Decisão

**O Mirante aceita Working Papers de natureza "standalone" como verticais
de primeira classe**, sob a denominação técnica `kind: "literature"` no
front e na infra de stats. A aceitação é condicionada a 6 critérios
substantivos (4 obrigatórios, 2 desejáveis), todos auditáveis no repo.

### Critérios obrigatórios

1. **Fonte primária verificável.** O paper cita um documento oficial
   (decreto, lei, currículo nacional, série estatística governamental,
   norma técnica) acessível ao público — não Wikipedia, blog ou imprensa
   secundária.
2. **Manifest de fontes em JSON.** As fontes primárias estão listadas em
   um manifest JSON (ex.: `articles/scripts/sources_calculo_curricula.json`)
   contendo `country/title/url/issuer/year/paper_claim` para cada item.
3. **Auditoria automatizada do achado central.** Existe um script Python
   commitado (ex.: `articles/scripts/audit_curricula_keywords.py`) que,
   dado o manifest, baixa e processa as fontes para verificar
   reproducibilidade do claim do paper. Saída esperada: relatório CSV
   apontando consistente/inconsistente.
4. **Vertical web com botões canônicos.** A rota web da vertical (ex.:
   `/calculo`) expõe os 4 botões padrão do Mirante (Ler artigo na tela,
   Baixar PDF ABNT, Baixar fonte .tex, Abrir no Overleaf) + ScoreCard +
   Ata do Conselho.

### Critérios desejáveis (não-obrigatórios)

5. **Snapshot dos documentos primários** (Wayback Machine ou cópias
   versionadas em `articles/snapshots/<wp>/`). Mitiga link rot — risco
   conhecido para PDFs de ministérios europeus e asiáticos.
6. **Conflito de interesse declarado.** Se o autor possui projetos
   paralelos relacionados ao tema do WP (ex.: cursos pagos, ONGs, blogs),
   isso é declarado em uma seção dedicada do paper.

---

## Consequências

### Positivas

- **Escopo da plataforma fica definido.** Futuros contribuidores podem
  consultar este ADR antes de propor WPs de revisão sistemática /
  estudo comparado / análise documental.
- **Heterogeneidade saudável.** A plataforma deixa de ser exclusivamente
  pipeline-driven; comporta também trabalhos prescritivos e de advocacy
  curricular.
- **Reprodutibilidade preservada.** O critério #3 (auditoria
  automatizada) garante que o achado central de WPs standalone é tão
  auditável quanto o gold de WPs pipeline (que é versionado em Git).
- **Identidade visual mantida.** Critério #4 + a obrigação de figuras
  com identidade visual Mirante (regra `feedback_chart_visual_identity.md`)
  asseguram que WPs standalone não destoam editorialmente.

### Negativas / trade-offs

- **Régua de avaliação distinta.** WPs standalone tipicamente não
  extrapolam lato sensu para mestrado, exceto se adicionarem
  contribuição metodológica original. Isso foi lição da Rodada 2 da
  Reunião #5 (recalibração honesta de mestrado B → lato sensu 8,0).
- **Custo operacional adicional.** Manter o manifest JSON + script de
  auditoria + snapshots é overhead que WPs pipeline não têm (já que o
  bronze é o snapshot).
- **Risco de drift de critério.** Sem disciplina explícita, "standalone"
  pode degenerar em "qualquer trabalho sem pipeline aceito como WP".
  Mitigação: code review de PR que cria nova vertical literature-kind
  deve auditar os 4 critérios obrigatórios contra este ADR.

### Neutras

- A `Big Data público — escala atual` strip da Início renderiza WPs
  standalone com `kind: "literature"` em vez de bronze/silver/gold —
  exibindo "currículos · triangulação · WP" em vez de bytes de Delta.
  A decisão de tornar visível na strip é boa para integridade da
  contagem de verticais; o trade-off é que a strip mistura unidades
  semanticamente distintas (bytes vs. currículos), o que precisa ser
  explicado pela legenda da seção.

---

## Alternativas consideradas

### A1. Recusar WPs standalone como verticais

- **Argumento:** mantém pureza arquitetural (toda vertical = pipeline).
- **Contra:** restringe demais o escopo da plataforma; obriga o autor a
  hospedar o trabalho fora do Mirante (gh.io/clube-da-matematica) e
  perder a integração com o framework editorial-crítico (Conselho,
  ScoreCard, Ata). Rejeitada.

### A2. Aceitar standalone só como sub-página dentro da Início

- **Argumento:** standalone vira "extra" / "sidebar", não vertical de
  primeira classe.
- **Contra:** assimetria de status confusa. Se o trabalho é sólido o
  bastante para ser apresentado, deve ser vertical; se não é, não deve
  estar. Rejeitada.

### A3. Aceitar standalone sem critérios formais

- **Argumento:** simplicidade — qualquer paper pode virar vertical.
- **Contra:** abre porta para ingestão de qualquer revisão bibliográfica.
  Sem auditoria automatizada (critério #3), o achado central vira
  "leitura humana", o que destoa do padrão de reprodutibilidade do
  Mirante. Rejeitada — perde o que torna o Mirante diferente.

---

## Implementação

WP#9 v2.1 (a ser commitada após esta ADR) cumpre os 4 critérios
obrigatórios + 1 dos 2 desejáveis (snapshot via Wayback fica para R3):

| # | Critério                                  | Artefato no repo                                                          |
|---|-------------------------------------------|---------------------------------------------------------------------------|
| 1 | Fonte primária verificável                | 47+ refs com URL + data de acesso no .tex (Seção Bibliografia)            |
| 2 | Manifest de fontes em JSON                | `articles/scripts/sources_calculo_curricula.json`                         |
| 3 | Auditoria automatizada                    | `articles/scripts/audit_curricula_keywords.py`                            |
| 4 | Vertical web canônica                     | `app/src/routes/Calculo.jsx` + ScoreCard + Ata Reunião #5                 |
| 5 | Snapshot dos documentos primários         | `articles/snapshots/calculo/` (parcial — pendente para R3)                |
| 6 | Conflito de interesse declarado           | Seção CoI no .tex sobre Clube da Matemática                               |

WPs futuros de natureza standalone (ex.: hipotético WP#10 — Ensino de
Física Comparado, WP#11 — Saneamento Básico em América Latina) devem
referenciar esta ADR no PR de criação da vertical.

---

## Referências

- Reunião #5 do Conselho do Mirante (2026-04-29): `app/src/data/atas-conselho.js` →
  `ATA_WP9_REUNIAO_5` (parecer da cadeira de Eng. Software).
- ADR Nygard, M. T. (2011). *Documenting Architecture Decisions*. (Padrão
  de ADR seguido aqui.)
- `feedback_new_vertical_checklist.md` (memória do projeto): convenção
  obrigatória de aparecer no Big Data strip + Início + Layout + notebook
  para qualquer nova vertical, independente de kind.

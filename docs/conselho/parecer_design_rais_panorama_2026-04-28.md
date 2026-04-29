# Parecer — Conselheira de Design & Visualização de Dados
## RAIS · Panorama 40 anos · WHY decidido (a+b+c) · Pré-WP

**Cadeira:** Conselheira de Design, Information Visualization & UX
**Data:** 2026-04-28
**Versão avaliada:** `docs/conselho/panorama_rais_2026-04-28.md` (bronze v6 íntegra, pós-fix per-year reader) + `app/src/routes/Rais.jsx` (HEAD main)
**Régua:** Stricto Sensu Mestrado · A=3 / B+=2,5 / B=2 / C=1 / D=0
**Score atribuído:** **C+ (1,3 pt) — MAJOR REVISION com trajetória clara para B+**
**Histórico:** C (1,0 pt) — auditoria bronze 2026-04-28 → **C+ (1,3 pt)** — panorama pós-bronze íntegra
**Veredicto geral:** A bronze está íntegra e isso é condição necessária — mas ainda não suficiente para nota de aprovação. O panorama entregue em `§1–§7` é riquíssimo em substância narrativa (4 choques, feminização monotônica, descentralização lenta, dois bilhões de linhas) e constitui a matéria-prima de um trabalho visualmente poderoso. O problema é que essa matéria-prima ainda não tem forma visual: o documento é integralmente textual + ASCII-table, o app ainda renderiza apenas mapa coroplético + barras estáticas por UF-ano, e o WHY (c) de plataforma pública exige um salto qualitativo em ambas as frentes. A nota sobe de C para C+ porque o dado agora é confiável — Tufte diz que a primeira obrigação do gráfico é ser verdadeiro, e agora a base existe. Mas uma viz que não existe ainda não pode pontuar acima do limiar de aprovação.

---

## 1. Audit visual do panorama — o que existe e o que falta

### 1.1 O que `§1–§7` entrega hoje

O panorama entrega **sete narrativas textuais** com tabelas ASCII embutidas. Substância de altíssima qualidade:

- `§2` — série temporal 1985–2024 de vínculos totais e ativos, com 4 choques identificados e magnitudes calculadas
- `§3` — decomposição regional por UF em 5 cortes temporais (1985/1995/2005/2014/2024)
- `§4` — feminização: 30% → 44%, crescimento monótono, sem reversão em crises
- `§5` — envelhecimento: mediana 32 → 36 anos, com inflexão em 2010 bem explicada
- `§6` — escolaridade: superior completo de 17% → 56% em 40 anos
- `§7` — massa salarial: 5 medidas disponíveis, granularidade mensal em 2023+

O problema: **isso tudo existe como texto**. Para o objetivo (c) de plataforma pública — jornalistas, sociedade — texto com tabela ASCII é barreira de entrada. A pergunta "quantos empregos o Plano Cruzado destruiu?" merece uma resposta que dispense a leitura de tabela.

### 1.2 O que o `Rais.jsx` entrega hoje

Quatro views, condicionadas ao gold JSON estar populado:

- `KpiCards`: 4 KPIs do ano selecionado — estáticos, numéricos, corretos
- `EvolutionBar`: série temporal de UMA métrica agregada nacional por ano
- `BrazilMap`: mapa coroplético de UMA métrica por UF para UM ano
- `StateRanking`: lista ordenada de UFs para o ano selecionado

**Pontos fortes arquiteturais:** `year` dinâmico derivado do gold, `Cividis` como default, fontes explicitadas, fallback "Pipeline em construção" sem crash.

**Limitações críticas para o objetivo (c):**
- `EvolutionBar` é agregado nacional — perde toda a variância regional
- `BrazilMap` é estático no tempo — não mostra trajetória, só fotografia
- Nenhuma anotação de eventos (Cruzado 1986, recessão Dilma 2015–16, COVID 2020)
- Nenhuma dimensão de feminização, envelhecimento ou escolaridade
- Nenhuma interatividade além de seletor de métrica e ano

Um jornalista que abrir a vertical hoje sai com "SP tem mais vínculos que DF". Não sai com "o Plano Cruzado destruiu 28,6% do emprego formal em um ano — o maior choque da série histórica".

---

## 2. Cinco a sete visualizações específicas que contariam a história

A seguir, as visualizações ordenadas por impacto narrativo para o objetivo (c). Não são sugestões decorativas — cada uma responde a uma pergunta que um jornalista ou cidadão formulariam.

### VIZ-1 — "O relógio do emprego formal" · Linha anotada com choques (MONEY SHOT #1)

**Tipo:** linha com área sombreada + anotações editoriais inline
**Dado:** série 1985–2024 de vínculos ativos em 31/12, valores absolutos + linha de crescimento secular (tendência log-linear ajustada aos períodos sem choque)
**Anotações:** 4 caixas de texto com seta apontando para cada choque — Cruzado 1986 (-28,6%), Collor 1990 (-5,3%), Recessão Dilma 2015–16 (-7,2% acumulado), COVID 2020 (-1%). Área hachurada em cinza para cada período recessivo.
**Por que funciona:** segue o princípio tufteano de anotação direta — o dado e a interpretação estão no mesmo espaço visual. Elimina a necessidade de legenda separada ou texto de rodapé. O leitor entende o choque antes de ler qualquer parágrafo.
**Identidade Mirante:** Lato, paleta hierárquica (linha principal em azul Mirante, área em alpha 0.15, anotações em cinza escuro com halo branco), source note inline, editorial_title com subtítulo explicativo.
**Para matplotlib:** `matplotlib.patches.FancyArrowPatch` para as setas; `adjustText` para evitar sobreposição de labels; `SciencePlots` grid; golden ratio (16:9 ≈ 6.4in × 4in a 300 dpi).

### VIZ-2 — "O mapa que se move" · Small multiples UF × período (MONEY SHOT #2)

**Tipo:** small multiples — 7 mapas coropléticos (um por era: 1985, 1990, 1995, 2005, 2010, 2017, 2024) + barra de divergência
**Dado:** share de vínculos ativos por UF em cada corte temporal — não o absoluto, mas a VARIAÇÃO relativa em relação a 1985 (normalizada em 0)
**Escala:** escala divergente — azul para UFs que ganharam share, vermelho para UFs que perderam. O centro (branco) é o valor de 1985. **Escala fixa across todos os 7 painéis** — condição Tufte inegociável para small multiples; sem escala fixa, a comparação é impossível.
**Destaque narrativo automático:** RJ aparecerá em vermelho crescente; SC+PR em azul crescente; SP em azul decrescente mas ainda dominante em absoluto.
**Padrão hatch para daltonismo:** adicionar textura diagonal nos 3 UFs mais extremos de cada painel para garantir legibilidade monocromática.
**Acessibilidade:** Cividis divergente (azul–amarelo, sem vermelho puro) é preferível ao clássico RdBu para protanopia/deuteranopia. Se o cliente editorial exigir azul-vermelho, adicionar hatch.

### VIZ-3 — "As três curvas que definem 40 anos" · Painel 3-em-1 (MONEY SHOT #3)

**Tipo:** three-panel figure (stacked vertical, aspect ratio golden ratio por painel), eixo x compartilhado 1985–2024
**Painel A:** % feminino (30% → 44%) — linha suavizada (LOESS span=0.4) + pontos de dados anuais + intervalo de confiança em alpha 0.1 + linha de tendência linear pontilhada como referência
**Painel B:** idade mediana (32 → 36 anos) — mesmo tratamento + anotação "inflexão 2010" com seta
**Painel C:** % superior completo (17% → 56%) — mesmo tratamento + band hachurado para o período com gap de codebook (2006–2022, §8.2 do panorama) — obrigação de transparência metodológica inline
**Por que funciona:** conta a transformação estrutural do trabalhador formal brasileiro em um único olhar. O leitor não precisa ler três parágrafos separados — a narrativa emerge da justaposição.
**Nota editorial mandatória:** o band hachurado em Painel C para o gap de codebook não é opcional. Omitir esse caveat transformaria a viz em desonestidade por omissão — o leitor interpretaria continuidade onde há descontinuidade metodológica.

### VIZ-4 — Heatmap CBO × ano (ocupações ao longo do tempo)

**Tipo:** heatmap com clustering hierárquico nas linhas (CBO agrupado por similaridade de trajetória), eixo x = anos em intervalos de 5 anos (1985, 1990, …, 2024), cor = share de vínculos no total nacional
**Dado:** silver agrupada por CBO 2-dígitos × ano (compatibilização via tabela DIEESE necessária para a era CBO94)
**Clustering:** Ward linkage na dimensão CBO — agrupa profissões com trajetórias similares visualmente
**Por que importa:** é a única viz que mostra desindustrialização + crescimento de serviços + terceirização em um único frame. Um jornalista de economia vai direto para esse gráfico.
**Caveat técnico:** CBO94 → CBO2002 via tabela DIEESE é imperfecto — registrar na source note que 1985–2002 usa CBO94 mapeado, com imprecisão nos 6 dígitos. Nunca omitir.
**Implementação:** `seaborn.clustermap` ou `scipy.cluster.hierarchy` + `matplotlib.imshow`; Viridis como paleta (sequencial, daltonismo-safe, bom contraste em print monocromático).

### VIZ-5 — "O Brasil que trabalha" · Mapa animado ou slider temporal

**Tipo:** mapa coroplético com slider de ano (1985–2024) — vínculos per capita por município (quando silver municípios estiver disponível) ou por UF (disponível agora)
**Dado:** vínculos ativos / população SIDRA por UF por ano
**Interatividade:** slider de ano com play automático (velocidade 500ms/frame, pausável) + tooltip com UF, valor, rank nacional naquele ano
**Por que cabe no Mirante React:** o app já tem `BrazilMap` + seletor de ano. A animação é a extensão natural — `useEffect` que incrementa `year` a cada 500ms quando `isPlaying === true`. Custo de implementação: ~30 linhas de JSX + lógica de play/pause/reset.
**Cuidado Tufte:** a animação só é válida se a escala de cor for FIXA entre todos os frames. Escala que muda a cada frame (para "usar melhor o range") é desonestidade visual — o leitor compara visualmente entre frames e a comparação é falsa.

### VIZ-6 — "Quem perdeu mais no Cruzado?" · Decomposição setorial do choque 1986

**Tipo:** diverging bar chart horizontal — setores ordenados por queda em vínculos ativos de 1985 para 1986
**Dado:** vínculos ativos por CNAE/subsetor em 1985 vs. 1986 (era1a, separador `;`, schema 24 colunas — requer silver harmonizada)
**Por que esta viz importa:** o choque do Cruzado (-28,6%) é o evento de maior magnitude da série, mas é analisado quase exclusivamente pela ótica macroeconômica (PIB, inflação). Esta viz seria a primeira visualização dos microdados do labor market do choque. Potencial de publicação em Piauí, The Intercept Brasil, Nexo.
**Caveat:** dado que era1a tem schema incompleto (sem CBO 2002, sem CNAE padronizado), a decomposição setorial é limitada às categorias disponíveis no Subsetor IBGE. Registrar.

### VIZ-7 — Scatter animado "feminização × escolaridade × remuneração" por UF

**Tipo:** scatter plot animado no tempo (Gapminder-style) — cada ponto = 1 UF, x = % feminino, y = remuneração média deflacionada, tamanho = total de vínculos, cor = região geográfica
**Dado:** silver agrupada por UF × ano
**Interatividade:** play/pause + trail (rastro do ponto ao longo do tempo, últimos 5 anos em alpha decrescente)
**Por que é poderoso:** permite ao leitor descobrir que UFs com maior % feminino não necessariamente têm menor remuneração — hipótese que o panorama levanta mas não testa. A exploração ativa (Norman: o usuário executa, avalia, corrige) é o mecanismo de descoberta.
**Aviso de carga cognitiva:** Gapminder-style com 27 UFs simultâneos é denso. Usar cores regionais (5 regiões = 5 hues bem separados) + legenda sempre visível + opção de highlight por UF ao hover. Sem highlight, o leitor perde o fio.

---

## 3. Os três "money shots" obrigatórios do WP

Para um working paper com padrão magazine-grade (NYT Graphics / Nexo Políticas Públicas tier), três figuras são condição necessária para não ser arquivado:

**MONEY SHOT #1 — VIZ-1 (linha anotada com choques)**
Razão: é a figura que aparece na capa, no abstract visual, no tweet do autor. Responde "o que aconteceu com o emprego formal em 40 anos" em 5 segundos. Sem ela, o WP não tem figura de referência.

**MONEY SHOT #2 — VIZ-2 (small multiples UF × era)**
Razão: é a figura que jornalistas de regional vão replicar. "O que aconteceu com o emprego formal em SC vs RJ em 40 anos?" é a pergunta que cada redação faz sobre sua praça. Small multiples com escala fixa respondem todas ao mesmo tempo.

**MONEY SHOT #3 — VIZ-3 (três curvas: feminização + envelhecimento + escolaridade)**
Razão: é a figura mais original do paper — não existe na literatura de labor economics brasileira com esses 40 anos juntos num único frame. É o candidato a Figure 1 do WP.

Nenhum dos três existe hoje. Os três precisam ser produzidos antes da submissão.

---

## 4. Componente de plataforma pública — Vega-Lite, Observable ou React?

### 4.1 Análise da decisão

| Canal | Custo | Audiência | Reproducibilidade | Integração Mirante |
|---|---|---|---|---|
| Vega-Lite embutido no WP (Quarto) | baixo | acadêmica + tech | alta (spec JSON) | parcial |
| Observable Notebook público | médio | tech + jornalistas | muito alta (fork) | zero |
| Componente React no Mirante | alto | todos | baixa (requer deploy) | total |
| Notebook Quarto estático publicado | baixo | tech | alta | parcial |

### 4.2 Minha decisão: SIM para componente React no Mirante — mas faseado

**Veredicto: SIM para dashboard interativo — implementar em fases, com Observable como ponte.**

Razão 1 — o Mirante já tem a infraestrutura. `BrazilMap`, `EvolutionBar`, `KpiCard`, `Panel` existem. Adicionar VIZ-5 (slider temporal) e VIZ-7 (scatter animado) é extensão de componentes existentes, não reconstrução.

Razão 2 — o objetivo (c) de "plataforma pública" só se realiza onde o usuário já está. Jornalistas não vão ao Observable para explorar dado; vão ao Mirante porque o card está na Home.

Razão 3 — Observable como ponte de prototipagem. **Antes de implementar no React**, publicar o notebook Observable com VIZ-1 e VIZ-3 estáticos + VIZ-5 interativo. Custo: 1 dia. Benefício: feedback real de jornalistas antes de escrever JSX.

**Plano faseado:**
- **Fase 0 (antes do WP):** matplotlib magazine-grade para VIZ-1, VIZ-2, VIZ-3 — figuras estáticas do WP
- **Fase 1 (junto com publicação do WP):** Observable Notebook público com VIZ-1 e VIZ-5 interativos — link no WP como "dados exploráveis"
- **Fase 2 (pós-publicação WP):** componentes React no Mirante expandindo `Rais.jsx` com VIZ-5 (slider) + VIZ-7 (scatter)

**Quarto público:** adequado para audiência técnica que sabe rodar Python. Não é suficiente para objetivo (c) — jornalistas e sociedade não rodam notebooks. Use Quarto para reproducibilidade acadêmica, não como substituto de produto.

---

## 5. O que da `§1–§7` deveria aparecer no app — proposta de expansão

O `Rais.jsx` atual cobre apenas dimensão geográfica estática (mapa UF × ano, métrica única). Para servir o objetivo (c), proposta de 3 painéis adicionais:

### Painel A — "Linha do tempo dos choques" (VIZ-1 versão React)

**Substituir ou complementar o `EvolutionBar` atual** com uma linha anotada. A diferença é a camada de anotação:
- Props adicionais: `events={[{year: 1986, label: 'Plano Cruzado −28,6%'}, ...]}` passando os 4 choques
- O componente `EvolutionBar` renderiza uma anotação textual com seta (SVG `<line>` + `<text>`) para cada evento
- Custo: ~40 linhas de SVG inline no componente

**Por que isso importa para o objetivo (c):** sem as anotações, o leitor vê uma linha que sobe e desce. Com as anotações, o leitor entende que cada queda tem nome e causa. É a diferença entre dado e narrativa.

### Painel B — "A transformação do trabalhador" (VIZ-3 versão React)

Novo painel abaixo do mapa, com três linhas sobrepostas (usando `recharts LineChart` ou D3 puro via `useRef`):
- Linha 1: % feminino (eixo y esquerdo, 0–50%)
- Linha 2: idade mediana (eixo y direito, 30–40 anos)
- Linhas 3: escolaridade superior completo % (eixo y esquerdo sobreposto ou painel separado)

Filtro por UF opcional: permite ao usuário comparar "como SC vs RJ transformaram seu trabalhador".

### Painel C — "Selecione dois anos, compare UFs" · Diverging map

Dois seletores de ano (Ano A e Ano B). O mapa exibe a VARIAÇÃO percentual de vínculos per capita entre os dois anos. Escala divergente (Cividis divergente). Tooltip com "em [UF], o emprego formal cresceu X% entre [A] e [B]".

Custo de implementação: moderado — requer `useMemo` sobre dois filtros de `rows` e cálculo de delta. O `BrazilMap` existente precisa de prop adicional para escala divergente.

**Por que esse painel é o mais poderoso para jornalistas:** permite ao leitor responder "o que a reforma trabalhista de 2017 fez com o emprego formal na minha UF?" com dois cliques.

---

## 6. Nota mestrado stricto sensu — vertical RAIS hoje (pós-bronze íntegra, pré-WP)

**C+ (1,3 pt) — MAJOR REVISION**

| Dimensão | Estado atual | Nota componente |
|---|---|---|
| Integridade visual | Bronze íntegra (sobe de C para C+); gold ainda não populado; `period` hardcoded ainda não corrigido | C+ → foi de D-latente para C+ |
| Carga cognitiva | Panorama é só texto + ASCII-table; app renderiza 4 views básicas quando gold populado | C |
| Affordances/signifiers | App não comunica choques, feminização, envelhecimento — apenas métrica × UF × ano | C |
| Acessibilidade WCAG | Cividis default correto; sem audit Lighthouse; sem hatch pattern nas figuras do WP | B |
| Reproducibilidade | Bronze documentada; silver a fazer; figuras do WP inexistentes; código de viz ausente | C |
| Tipografia | App: presumidamente correto (KpiCards usam tabular-nums via CSS global); WP: sem figuras, sem tipografia a avaliar | B |
| Interatividade (quando cabe) | Slider + scatter animado ausentes; EvolutionBar sem anotação; mapa sem temporalidade | C |
| Estática (quando cabe) | NENHUMA das 3 money shots existe; panorama é ASCII, não matplotlib | D para figuras WP |
| Cool factor | Potencial altíssimo (2 bilhões de linhas, 40 anos, 4 choques identificados); realização atual: zero | C |

**Por que C+ e não B:** para B, o WP precisaria ter pelo menos VIZ-1 e VIZ-3 produzidas em padrão Mirante, e o `Rais.jsx` precisaria ter o painel de choques anotados e o `period` derivado dinamicamente. Nada disso existe. C+ reflete que a base de dados é agora confiável (sobe do C anterior) mas a forma visual não existe.

**Trajetória clara para B+:** produzir VIZ-1 + VIZ-2 + VIZ-3 em matplotlib magazine-grade (identidade Mirante: Lato, paleta hierárquica, golden ratio, halo branco, adjustText, source_note inline) + corrigir `period` hardcoded no Home.jsx + adicionar painel de choques anotados no EvolutionBar. Essas ações por si sós levam de C+ para B+ sem precisar de Observable nem React adicional.

---

## 7. Três ideias UI concretas (Bostock/D3-style) — choques + concentração regional + feminização na mesma página sem overload

### Ideia UI-1 — "Linha mestra com brushing" · VIZ-1 ampliada para exploração

**Conceito D3:** uma linha principal (vínculos ativos 1985–2024) com um "context chart" (brush) embaixo — padrão clássico de navegação temporal em D3 (Focus+Context, Heer & Shneiderman 2012). O usuário arrasta a janela no context para fazer zoom em qualquer período. Os choques aparecem como bandas verticais hachuradas fixas na linha principal (não no context), com labels que aparecem ao hover.

**Por que resolve o overload:** em vez de mostrar 40 anos comprimidos com todas as anotações simultâneas, o leitor pode focar em 5 anos de cada vez. A narrativa dos choques está lá — mas o leitor chega a ela no seu ritmo, não forçado.

**Integração React/D3:** usar `d3-brush` dentro de um `useEffect` sobre dois `<svg>` stacked. O brush atualiza um `useState([xMin, xMax])` que filtra os dados da linha principal. Custo: ~100 linhas de D3 + CSS.

**Acessibilidade:** os 4 choques devem ter `aria-label` descritivos nas bandas hachuradas (`"Plano Cruzado 1986: queda de 28,6% em vínculos ativos"`). Navegação por teclado: Tab entre as bandas, Enter para tooltip expandido.

### Ideia UI-2 — "Painel 3×1 sincronizado" · feminização + envelhecimento + escolaridade com hover global

**Conceito:** três linhas empilhadas verticalmente (como VIZ-3 estática, mas interativa) com **hover sincronizado** — quando o mouse entra em qualquer linha em x=2010, as três linhas mostram o crosshair e o tooltip simultaneamente. Cada tooltip mostra o valor naquele ano + delta vs. 1985.

**Por que funciona sem overload:** o leitor vê três métricas mas só interage com uma dimensão (o tempo). O hover sincronizado elimina a necessidade de ler três gráficos separados — o ponto de inflexão de 2010 (que aparece em feminização E em envelhecimento) se torna imediatamente visível como evento estrutural compartilhado.

**Implementação React:** `useState(hoveredYear)` compartilhado entre os três sub-componentes via context ou prop drilling. Cada sub-componente renderiza um `<line>` vertical SVG quando `hoveredYear !== null`. Tooltip global posicionado absolutamente sobre o painel maior.

**Por que é Bostock-style:** segue o princípio de linked views (Becker & Cleveland 1987, popularizado por D3 Observable) — múltiplas visões do mesmo dado, sincronizadas no tempo. O leitor descobre correlações sem precisar ser dito que elas existem.

### Ideia UI-3 — "Mapa + linha · detalhe sob demanda" · concentração regional com drill-down

**Conceito:** o `BrazilMap` existente recebe um evento `onClickUF(uf)`. Ao clicar em uma UF, um painel à direita (ou modal) expande mostrando a série temporal dessa UF específica em três dimensões: (a) vínculos ativos, (b) % feminino, (c) remuneração média deflacionada. Fonte de dados: `rows.filter(r => r.uf === selectedUF)` — já disponível em memória.

**Por que não é overload:** o mapa principal mantém a visão geográfica completa. O drill-down é "sob demanda" (Norman: o sistema aguarda a ação do usuário, não a força). O leitor que quer saber o que aconteceu com SC clica em SC e vê SC — sem perder o contexto nacional.

**Mapa de calor + série temporal em um clique:** esse padrão (Overview + Detail, Cockburn & McKenzie 2002) é o mais testado empiricamente para usuários não-técnicos. Jornalistas adoram porque podem "puxar" o dado de qualquer UF sem saber SQL.

**Integração React:** `useState(selectedUF)` + condicional de renderização do painel de detalhe. Nenhum componente novo necessário além dos já existentes (`EvolutionBar` com `rows.filter`). Custo: ~60 linhas de JSX.

---

## 8. Acessibilidade — checklist pré-publicação

### 8.1 Paleta daltonismo-safe

Para as figuras estáticas do WP:

- **VIZ-1 (linha anotada):** usar Lato + azul `#2563EB` (paleta Mirante) para a linha principal. Bandas de recessão em cinza `#9CA3AF` com hatch diagonal (45°, 4px espaçamento) — não depende de cor.
- **VIZ-2 (small multiples):** Cividis divergente. **Não usar RdBu** — protanopes não distinguem vermelho de verde mas distinguem azul de amarelo (Cividis). Adicionalmente, os 3 UFs mais extremos de cada painel recebem hatch pattern (diagonal para positivo, horizontal para negativo) para leitura monocromática/impressão P&B.
- **VIZ-3 (três curvas):** três linhas em hues bem separados do eixo de matiz (hue wheel): azul `#2563EB`, laranja `#D97706`, verde `#16A34A`. Em deuteranopia total, azul e laranja são distinguíveis; o verde pode conflitar com o laranja — portanto adicionar marcadores de forma distintos (círculo, triângulo, quadrado) em cada ponto de dado anual. Teste obrigatório via `daltonize` ou `Coblis`.
- **VIZ-4 (heatmap CBO):** Viridis sequencial — daltonismo-safe por design (luminância monotônica).
- **VIZ-7 (scatter):** 5 regiões = 5 hues. Usar a paleta de 5 cores Wong (2011), padrão de facto em publicações científicas daltonismo-safe: `#000000`, `#E69F00`, `#56B4E9`, `#009E73`, `#F0E442`. Adicionar formas distintas por região (círculo, triângulo, quadrado, losango, cruz).

### 8.2 Contraste WCAG AA mínimo

- Source notes e captions: pelo menos 4.5:1 contra o fundo (WCAG AA texto normal). O cinza `#6B7280` sobre branco tem razão 4.6:1 — limite aceitável.
- Labels inline nas figuras: se sobre área colorida, usar halo branco de 2px (já está na identidade Mirante). Se o halo não for suficiente, usar `#1E293B` (quase preto) com peso 600.
- **Nunca usar texto sobre gradiente sem halo** — o contraste varia ao longo do gradiente e é impossível garantir WCAG em todo o percurso.

### 8.3 Leitor de tela e navegação por teclado

Para as visualizações interativas no React:

- Cada `<svg>` principal deve ter `role="img"` + `aria-label` descritivo (ex: `"Gráfico de linha: vínculos ativos no mercado formal brasileiro, 1985 a 2024"`).
- Tooltips devem ser acessíveis via `role="tooltip"` + `aria-live="polite"` — não apenas via mouseover.
- Os seletores de métrica e ano já são `<select>` nativos — acessíveis por padrão. Manter assim; não substituir por custom dropdowns sem implementar ARIA completo.
- O botão play/pause do slider animado (VIZ-5) deve ter `aria-label` que mude dinamicamente ("Pausar animação" / "Reproduzir animação") e responder a `Space` e `Enter`.

### 8.4 Mobile responsivo

O `BrazilMap` atual usa SVG com viewBox relativo — deve escalar. O `EvolutionBar` precisa ser testado em viewport 375px (iPhone SE). Breakpoint crítico: em mobile, o painel 3×1 sincronizado (Ideia UI-2) deve empilhar verticalmente, não horizontalmente. CSS Grid com `grid-template-columns: 1fr` em `max-width: 640px`.

---

## 9. Pontos fortes (mantidos do parecer anterior + novos)

1. **Bronze íntegra após fix per-year reader** — condição necessária para qualquer viz honesta. Agora existe. O score sobe por isso.
2. **Cividis como default no BrazilMap** — escolha correta, mantida.
3. **Narrativa dos 4 choques no panorama é publicável** — a substância de §2 (Cruzado -28,6%, recessão Dilma -7,2% acumulado, COVID -1%) já está pronta para virar VIZ-1. O trabalho analítico foi feito; falta apenas a forma.
4. **Questão do Plano Cruzado (§9.5) é genuinamente original** — "o maior choque do labor market formal em 40 anos, quase sem literatura empírica de microdados". Isso é o gancho jornalístico natural.
5. **Feminização monotônica sem reversão em crises (§4)** — vai contra o "added worker effect" clássico. É um finding que merece destaque visual (VIZ-3 Painel A) e uma nota editorial.

## 10. Pontos fortes novos nesta versão

1. **Bronze auditada e íntegra em 40 anos** — pela primeira vez, a base de 2.06B linhas tem alinhamento header/dado verificado por ano. Isso permite viz comparativas cross-era que antes seriam fabricação.
2. **Caveats metodológicos bem documentados no panorama (§8)** — o band hachurado que proponho em VIZ-3 Painel C (gap de codebook escolaridade) já tem base documental sólida. Boa prática de transparência que precede a viz.
3. **Granularidade mensal 2023+ (§7)** — os 12 campos `vl_rem_<mês>_sc` permitem uma viz de sazonalidade salarial que não existe na literatura brasileira. Não está nas 7 vizs propostas acima porque exige silver era3+ — mas é candidato a VIZ-8 num segundo momento.

---

## 11. Problemas remanescentes (no escopo do WP)

1. **Nenhuma figura existe** — o WP não pode ser submetido sem VIZ-1 + VIZ-2 + VIZ-3 produzidas em padrão Mirante (matplotlib + `editorial_title` + `source_note` + `adjustText` + `SciencePlots` + golden ratio). Esse é o bloqueador principal.
2. **`period: '1985 – 2025'` hardcoded em `Home.jsx`** — identificado no parecer anterior, ainda não corrigido. Com o gold agora prestes a ser populado, isso materializará como violação ativa (2024 real vs. 2025 prometido) na próxima atualização de deploy.
3. **`EvolutionBar` sem anotação de choques** — o componente exibe a série temporal mas não nomeia os eventos. Para o objetivo (c) de plataforma pública, isso é insuficiente — o usuário vê uma queda em 1986 mas não sabe que é o Plano Cruzado.
4. **Gap de escolaridade 2006–2022 não está marcado em nenhuma viz** — o panorama documenta o gap; nenhuma viz futura pode omiti-lo sem hatch/annotation.
5. **Ausência de "Ler artigo na tela"** — registrado no parecer anterior, remanescente. Botão obrigatório per `feedback_article_buttons.md`.
6. **Silver não existe para as dimensões de feminização/envelhecimento/escolaridade por UF** — as três curvas de VIZ-3 precisam de silver agregada por UF × ano × dimensão. Dependência técnica que bloqueia VIZ-3 e VIZ-7.

## 12. Problemas remanescentes (escopo da plataforma — não puxam o score do WP individual)

- Lighthouse audit da vertical RAIS ausente — remanescente de WPs anteriores.
- Design system docs não publicados — impedem outros contribuidores de replicar o padrão Mirante.
- Vega-Lite interativo ausente em todas as verticais — prometido em WP#4 parecer, ainda não implementado.

---

## 13. Sugestões para subir de nível

**Sugestão 1 — Produzir VIZ-1 antes do WP (bloqueador #1)**
Why: sem a linha anotada com choques, o WP não tem figura de identidade. É a money shot #1.
How to apply: usar `build-figures-rais.py` seguindo o padrão de `build-figures-pbf.py` existente no projeto. Chamar `mirante_charts.editorial_title()`, `mirante_charts.source_note()`, `mirante_charts.inline_labels()`. Para as anotações de choque: `ax.annotate(text, xy=(x_choque, y_choque), xytext=(x_choque+2, y_choque*0.8), arrowprops=dict(arrowstyle='->', color='#475569'), fontsize=8, fontfamily='Lato', color='#1E293B', bbox=dict(boxstyle='round,pad=0.3', fc='white', alpha=0.85, linewidth=0))`. O `bbox` implementa o halo branco mandatório da identidade Mirante.

**Sugestão 2 — Hatch nos small multiples (VIZ-2) antes de cometer escala de cor**
Why: é tentador usar escala divergente colorida e declarar vitória. Mas a única garantia de legibilidade P&B e daltonismo é o hatch combinado com cor.
How to apply: após calcular os 3 UFs mais extremos por painel, adicionar `ax.add_patch(matplotlib.patches.PathPatch(path, hatch='///', fill=False, linewidth=0.5, edgecolor='#1E293B', alpha=0.6))` sobre o polígono SVG do UF no mapa. Para SVG/D3 no React, `fill="url(#hatch-negative)"` onde o `<pattern>` é declarado uma vez no `<defs>` do SVG.

**Sugestão 3 — Observable Notebook como ponte para fase 1 da plataforma pública**
Why: o ciclo de feedback com jornalistas precisa acontecer antes de escrever JSX. Observable permite publicar VIZ-5 (mapa animado) em um dia e compartilhar URL. O custo de reescrever em React após feedback é muito menor que escrever sem feedback.
How to apply: criar `observable/rais-40anos.js` com o gold JSON como dado embutido (< 500 KB para UF × ano × 4 métricas). Publicar em `observablehq.com/@leonardochalhoub/rais-40anos`. Linkar do WP na seção "Dados exploráveis". Após 2-4 semanas de uso real, implementar os componentes React baseados no feedback observado.

---

## Decisão final

**Nota mestrado stricto sensu: C+ (1,3 pt) — MAJOR REVISION**

**Dashboard interativo: SIM — faseado (Observable primeiro, React depois)**

**3 ideias UI:**
1. Linha mestra com brushing (Focus+Context D3) — choques + navegação temporal sem overload
2. Painel 3×1 com hover sincronizado — feminização + envelhecimento + escolaridade em linked views
3. Mapa + série de detalhe sob demanda (Overview+Detail) — concentração regional com drill-down por UF

*Parecer emitido por: Conselheira de Design, Information Visualization & UX — Mirante dos Dados*
*Cadeira de Design — Reunião de Panorama RAIS · 2026-04-28*

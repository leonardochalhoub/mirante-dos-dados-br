# Mirante dos Dados — Design System

> Última atualização: 2026-04-26 · v1.0
>
> Este documento centraliza tokens visuais, padrões de componentes e
> notas de acessibilidade do front-end React/Vite do Mirante dos
> Dados. Complementa `ARCHITECTURE.md` (decisões técnicas) e
> `CLAUDE.md` (convenções de projeto).
>
> Originado em parte como resposta à crítica do peer review fake
> "Design Web" (vide `memory/peer_review_design_web_wp4.md` e
> `peer_review_design_web_wp6.md`), que apontou ausência de
> documentação formal do sistema visual.

---

## 1. Princípios

1. **Estética acadêmica/editorial primeiro**. O Mirante é um veículo
   de Working Papers. Cada rota é uma *página* — não um *aplicativo*.
2. **Cores funcionais, não decorativas**. Toda cor codifica
   informação (categoria, magnitude, presença/ausência).
3. **Tipografia serif para texto, mono para códigos**. Reflete o
   padrão ABNT dos PDFs.
4. **Sem ícone-fluff**. Emojis e ícones decorativos são proibidos
   no conteúdo (excepcionalmente úteis em CTAs como `📖 Ler artigo`).
5. **Dark mode é primeiro-classe**. Cores são tokens, não literais.

---

## 2. Tokens de cor

Definidos em [`app/src/styles/globals.css`](../app/src/styles/globals.css)
sob `:root` (light) e `[data-theme="dark"]`.

### Light mode

| Token             | Valor                | Uso                                   |
|-------------------|----------------------|---------------------------------------|
| `--bg`            | `#f1f5f9`            | fundo da página                       |
| `--bg-soft`       | `#e2e8f0`            | fundo de panel secundário             |
| `--panel`         | `#ffffff`            | superfície de panel principal         |
| `--border`        | `rgba(15,23,42,0.08)` | borda sutil                          |
| `--border-strong` | `rgba(15,23,42,0.16)` | borda visível                        |
| `--text`          | `#0f172a`            | texto principal                       |
| `--muted`         | `#64748b`            | texto secundário, captions            |
| `--faint`         | `#94a3b8`            | texto muito sutil (hints, timestamps) |
| `--accent`        | `#0f172a`            | destaque (CTAs, links em hover)       |
| `--accent-soft`   | `#e2e8f0`            | fundo de chip/badge                   |
| `--link`          | `#1d4ed8`            | links inline                          |

### Dark mode

| Token             | Valor                | Uso                                   |
|-------------------|----------------------|---------------------------------------|
| `--bg`            | `#0d1117`            | fundo da página                       |
| `--bg-soft`       | `#161b22`            | fundo soft                            |
| `--panel`         | `#161b22`            | superfície                            |
| `--border`        | `rgba(255,255,255,0.08)` | borda sutil                       |
| `--text`          | `#e2e8f0`            | texto principal                       |
| `--muted`         | `#94a3b8`            | texto secundário                      |
| `--accent`        | `#f8fafc`            | destaque                              |
| `--link`          | `#93c5fd`            | links inline                          |

### Cores temáticas (cross-tema)

| Token       | Valor     | Uso                                           |
|-------------|-----------|-----------------------------------------------|
| `--bronze`  | `#b45309` | medalha pareceres (lato sensu, score baixo)   |
| `--silver`  | `#64748b` | medalha pareceres (intermediário)             |
| `--gold`    | `#ca8a04` | medalha pareceres (stricto sensu, score alto) |

---

## 3. Paletas de visualização

### Cividis (escala perceptualmente uniforme — primária)

Usada em **todos os charts e mapas analíticos** por padrão. Cividis
é uma das poucas paletas perceptualmente uniformes que são
*colorblind-safe* para todos os tipos comuns de daltonismo
(deuteranopia, protanopia, tritanopia). Padrão científico publicado
em Nuñez, J. R., Anderton, C. R., & Renslow, R. S. (2018) —
*PLOS ONE*.

```js
import { interpolateCividis } from 'd3-scale-chromatic';
// ou para sentido invertido (alto valor = escuro):
import { interpolateCividis as cividisR } from 'd3-scale-chromatic';
const colorReversed = (t) => interpolateCividis(1 - t);
```

Build scripts Python (`articles/build-figures-*.py`) usam
`matplotlib.cm.cividis_r` (a versão invertida — alto valor = escuro
mais saturado).

### Categóricas — discretas

Quando uma figura tem ≤ 5 séries categóricas onde a *ordem* não
importa (ex.: "RP6 vs RP7 vs RP8 vs RP9"), usar paleta tableau-10
ou D3 schemeCategory10. **Evitar** paletas arco-íris (jet, hsv) —
não são perceptualmente uniformes.

### SUS / Privado

Códigos fixos no projeto:

| Setor      | Cor       | Uso                                     |
|------------|-----------|-----------------------------------------|
| SUS        | `#1d4ed8` | barra/área que representa setor público |
| Privado    | `#be185d` | barra/área que representa setor privado |

Esses dois são os únicos pares de cor com semântica fixa cross-vertical.

### Cor de alerta / referência

| Uso                          | Cor       |
|------------------------------|-----------|
| Mediana / linha de referência| `#dc2626` (vermelho) |
| Anotação textual de destaque | `#7f1d1d` (vermelho escuro) |
| COVID-19 (overlay temporal)  | `#b91c1c` (vermelho com α=0.10) |

---

## 4. Tipografia

### Front-end (web)

```css
--font-sans: ui-sans-serif, system-ui, -apple-system, "Segoe UI",
             Roboto, "Helvetica Neue", Arial, sans-serif;
--font-mono: ui-monospace, "JetBrains Mono", "SF Mono",
             "Cascadia Mono", Menlo, Consolas, monospace;
```

Sans-serif é o padrão para texto e UI. Monospace é usado para:

- Códigos inline (`<code>`)
- Siglas de UF nas figuras (`AC`, `MG`, `SP`)
- Equipment keys (`1:12`)

### LaTeX (PDFs ABNT)

Lmodern (Latin Modern) com `\onehalfspacing`. Tipo serif por padrão,
matching estética acadêmica brasileira.

### Hierarquia (front-end)

| Elemento           | Tamanho | Peso | Notas                                     |
|--------------------|---------|------|-------------------------------------------|
| Page title         | 32px    | 700  | em `PageHeader.jsx`                       |
| Section title      | 20px    | 700  | em `Panel.jsx`                            |
| Body (default)     | 14px    | 400  | corrente da página                        |
| KPI value          | 28-32px | 700  | em `KpiCard.jsx`                          |
| KPI label          | 11px    | 600  | uppercase, letter-spacing 0.06em          |
| Caption / footnote | 11-12px | 400  | em `var(--muted)`                         |
| Code inline        | 13px    | 500  | mono, fundo `var(--accent-soft)`          |

---

## 5. Espaçamento e layout

```css
--gap:       14px;   /* espaçamento padrão entre elementos */
--radius:    12px;   /* arredondamento padrão de panels */
--radius-sm: 8px;    /* arredondamento de chips, pills */
```

### Grid das páginas

Cada rota segue:

```
PageHeader (eyebrow + title + right-actions)
  ↓
ScoreCard (parecer simulado da rota)
  ↓
ArticleSection (link pra WP, opcional)
  ↓
KpiRow (4 KpiCards)
  ↓
Panels com filtros + visualizações
  ↓
Footer (fontes, atualizações)
```

Container central: max-width ~1200-1280px, padding lateral
responsivo. Layout de uma coluna em mobile, multi-painel em desktop.

---

## 6. Componentes

### Atomic

| Componente       | Arquivo                                     | Uso                                    |
|------------------|---------------------------------------------|----------------------------------------|
| `KpiCard`        | `app/src/components/KpiCard.jsx`            | KPI numérico com label + sub           |
| `Panel`          | `app/src/components/Panel.jsx`              | Container com label + sub + slot       |
| `PageHeader`     | `app/src/components/PageHeader.jsx`         | Header da rota (eyebrow + title + actions) |
| `StateRanking`   | `app/src/components/StateRanking.jsx`       | Ranking horizontal de UFs              |
| `BrazilMap`      | `app/src/components/BrazilMap.jsx`          | Choropleth via react-simple-maps       |
| `DownloadActions`| `app/src/components/DownloadActions.jsx`    | Botões "Baixar XLSX/PNG"               |
| `TechBadges`     | `app/src/components/TechBadges.jsx`         | Stack badges (Spark, Delta, etc.)      |
| `ScoreCard`      | `app/src/components/ScoreCard.jsx`          | Card com parecer simulado IA            |

### Charts (Recharts wrappers)

| Componente               | Arquivo                                                       | Uso                              |
|--------------------------|---------------------------------------------------------------|----------------------------------|
| `EvolutionBar`           | `app/src/components/charts/EvolutionBar.jsx`                  | Barras temporais simples         |
| `EvolutionStackedByKey`  | `app/src/components/charts/EvolutionStackedByKey.jsx`         | Áreas empilhadas                 |
| `EvolutionStackedComposed` | `app/src/components/charts/EvolutionStackedComposed.jsx`     | Composto bar+line                |
| `ChartTooltip`           | `app/src/components/charts/ChartTooltip.jsx`                  | Tooltip customizado              |

### Convenção: como adicionar uma nova chart

1. Criar arquivo em `app/src/components/charts/<Nome>.jsx`.
2. Receber `data: Array<{...}>`, `theme: 'light' | 'dark'`,
   `format: (v) => string` como props.
3. Usar `var(--text)` / `var(--muted)` / `var(--border)` para cores
   estruturais; usar paleta Cividis para encoding de magnitude.
4. Wrap com `<ResponsiveContainer width="100%" height={N}>`.
5. Tooltip via `<Tooltip content={<ChartTooltip ... />} />`.

---

## 7. Acessibilidade

### Status atual (2026-04)

- ✅ **Cores Cividis em todas as visualizações**: colorblind-safe.
- ✅ **`prefers-reduced-motion`**: animações respeitam preferência
  de sistema.
- ✅ **Dark mode via tokens**: contraste ≥ 4.5:1 (WCAG AA) em
  ambos os temas.
- ⚠️ **Lighthouse audit ausente**: vide `peer_review_design_web_wp6.md`.
  Próximo passo: integrar Lighthouse CI ao workflow.
- ⚠️ **Focus management em modais**: ScoreCard expandable não
  trapeia o foco quando aberto. A corrigir.
- ⚠️ **Screen reader testing**: não testado com VoiceOver/NVDA.
  A fazer.

### Convenções obrigatórias

1. Toda imagem precisa de `alt` informativo (não decorativo).
2. Todo botão precisa de `aria-label` se o conteúdo for só ícone.
3. Headings em ordem hierárquica (h1 → h2 → h3, sem pulos).
4. Inputs sempre com `<label htmlFor="id">` associado.
5. Cores nunca são o único veículo de informação — sempre acompanhada
   de texto/ícone/posição.

---

## 8. Padrões de microcopy

- **Tom**: técnico-acadêmico, primeira pessoa do plural acadêmica
  ("examinamos", "documentamos") nos PDFs; impessoal nos labels do
  front ("Acesso à cirurgia uroginecológica em 2025").
- **Português brasileiro**: sempre.
- **Números**: separador de milhar é ponto (`5.836`); separador
  decimal é vírgula (`12,3`). Em códigos e nomes técnicos preserva
  notação original (`equipment_key=1:12`).
- **Moedas**: `R$ 5,8 mi (2021)` para valores deflacionados;
  sempre indicar ano-base.
- **% sempre com vírgula**: `35,6 %` (não `35.6%`).

---

## 9. Padrões de figuras (LaTeX)

Para figuras estáticas em Working Papers (geradas via
`articles/build-figures-*.py`):

- **DPI**: 200 (suficiente pra PDF; 300 dpi não é necessário).
- **Tipografia**: `serif` em matplotlib (`DejaVu Serif`,
  `Liberation Serif`, `Times New Roman` na ordem).
- **Tamanho**: `figsize=(7-8, 4-6)` polegadas; cabe em página A4
  com margens ABNT (3-2-2-2 cm).
- **Cores**: Cividis sempre que possível.
- **Anotações**: `ρ = +0.42` em caixa branca com borda cinza no
  canto superior direito de scatters.
- **Linhas de referência**: vermelhas (#dc2626), tracejadas,
  α=0.7-0.8.
- **Fundo**: branco para PDFs (não transparente).
- **Salvar**: `bbox_inches='tight'`, `facecolor='white'`.

---

## 10. Referências

- Nuñez, Anderton, Renslow (2018). "Optimizing colormaps with
  consideration for color vision deficiency to enable accurate
  interpretation of scientific data." *PLOS ONE*. (Cividis source.)
- WCAG 2.1 Level AA.
- D3 schemeCategory10 (Tableau-10).
- ABNT NBR 6022 (artigo em publicação periódica).

---

**Mantenedor**: Leonardo Chalhoub
**Repositório**: https://github.com/leonardochalhoub/mirante-dos-dados-br
**Licença**: CC BY 4.0 (texto), MIT (código).

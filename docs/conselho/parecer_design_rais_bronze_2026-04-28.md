# Parecer — Conselheira de Design & Visualização de Dados
## Auditoria de Impacto Visual/UX — Bronze RAIS 2023+2024

**Cadeira:** Conselheira de Design, Information Visualization & UX  
**Data:** 2026-04-28  
**Versão avaliada:** bronze audit `briefing_rais_bronze_audit_2026-04-28.md` + `app/src/routes/Rais.jsx` (branch main, HEAD b6df45d)  
**Régua:** Stricto Sensu Mestrado · A=3 / B+=2,5 / B=2 / C=1 / D=0  
**Score atribuído:** **C (1,0 pt) — MAJOR REVISION**  
**Histórico:** [sem versão anterior desta auditoria]  
**Veredicto geral:** A vertical RAIS NO APP promete "1985–2025" na Home (card `period`) enquanto o arquivo gold está vazio (`[]`, 0 bytes de dados). Isso é uma violação dupla: a UI anuncia um período que nunca existiu na tela do usuário, e quando o gold for populado terá no máximo anos íntegros até 2022 — i.e., 3 anos aquém do anunciado. A integridade visual no sentido tufteano falhou antes mesmo de um único pixel de dado aparecer.

---

## 1. Audit da vertical RAIS no app

### 1.1 O que o `Rais.jsx` exibe

Quatro componentes principais de visualização:

- **KpiCards** (`rais-kpis`): Vínculos ativos, Massa salarial, Remun. média, Vínc. per capita — todos derivados de `rows.filter(r => r.Ano === Number(year))`. O `year` é inicializado como `Math.max(...all.map(r => r.Ano))` — ou seja, o ano mais recente presente no gold JSON.
- **EvolutionBar** (`rais-evolucao`): série temporal de todos os `years` presentes no gold, por métrica selecionada.
- **BrazilMap** (`rais-mapa`): mapa coroplético por UF filtrado pelo `year` selecionado.
- **StateRanking** (`rais-ranking`): ranking de UFs para o `year` selecionado.

### 1.2 Estado atual: gold JSON está vazio

`app/public/data/gold_rais_estados_ano.json` = `[]` (3 bytes, array vazio).

Consequência imediata: o componente renderiza o bloco `rows.length === 0`, exibindo apenas a mensagem "Pipeline em construção". **Nenhum gráfico, mapa, KPI ou ranking é renderizado ao usuário hoje.**

### 1.3 Datas hardcoded e o problema do `year` dinâmico

Não há anos hardcoded diretamente nos gráficos — o `year` inicial é derivado do máximo em `rows`. Isso é arquiteturalmente correto: quando o gold for populado, o ano mais recente disponível será o padrão. **Porém há um hardcode crítico no card da Home:**

```
// Home.jsx linha 47 (VERTICAIS array)
period: '1985 – 2025',
```

Esse `period` é texto estático. Não lê o gold. Não verifica o último ano disponível. Quando o gold for eventualmente populado com dados até 2022 íntegros, o card continuará anunciando "1985–2025".

### 1.4 Fallback se ano não tem dado

O componente trata `rows.length === 0` com um painel de "Pipeline em construção". Não há tratamento explícito para o caso em que o gold tem dados parciais — por exemplo, se 2023 aparecer no JSON mas com todos os campos `null` ou zerados (situação possível se a silver rodar sobre a bronze corrompida). Nesse cenário, o gráfico renderizaria barras de valor 0 ou linhas planas sem nenhum aviso ao usuário.

---

## 2. Impacto Tufte — integridade estatística

### 2.1 O princípio violado

Tufte, *The Visual Display of Quantitative Information* (1983): a representação visual de dados deve ser proporcional à substância dos dados. A violação mais grave não é o chartjunk — é mostrar um período que não existe ou apresentar ausência de dado como dado zero.

A situação atual da bronze cria três cenários de violação potencial, em ordem de gravidade:

**Cenário A — Gold populado a partir da bronze corrompida (o mais grave):**  
Silver roda sobre bronze 2023+2024 sem filtro adequado. O resultado: 175 M de linhas com 50 colunas NULL sendo agregadas. Vínculos ativos = 0 para 2023+2024 (pois `vinculo_ativo_31_12` está NULL). Massa salarial = 0. O gráfico `EvolutionBar` mostraria uma queda abrupta em 2023–2024 — não refletindo uma queda real no emprego formal, mas um artefato de ingestão corrompida. **Isso é fabricação visual por omissão**, equivalente ao eixo truncado que Tufte condena: o dado parece falar quando está mudo.

**Cenário B — Silver filtra 2023+2024 corretamente, gold vai até 2022:**  
O `EvolutionBar` termina em 2022. Os KPIs mostram `Vínculos ativos · 2022`. O `BrazilMap` mostra 2022. Nenhuma violação nos gráficos em si — mas o card na Home diz "1985–2025". Esse delta (2022 real vs. 2025 prometido) é uma **violação de integridade por promessa não cumprida**: o usuário clica esperando 2025 e recebe 2022 sem explicação.

**Cenário C — Estado atual (gold vazio):**  
Nenhum dado renderizado. Menos grave do ponto de vista de viz, mas igualmente problemático: o card promete "1985–2025" e entrega uma tela de "Pipeline em construção". Integridade zero — não pela mentira do gráfico, mas pela promessa não entregue.

### 2.2 Chartjunk reverso

Cunho próprio: "chartjunk reverso" é quando a ausência de dado é apresentada como se fosse dado válido — seja por interpolação silenciosa, por extensão visual do eixo além dos dados disponíveis, ou por promessa de período que o dado não cobre. É tão grave quanto o chartjunk clássico porque confunde o leitor em direção oposta: ao invés de ruído visual acima do dado, há silêncio visual *em vez* do dado — mas o usuário não sabe distinguir.

A violação "1985–2025" no card da Home é chartjunk reverso clássico.

### 2.3 Contaminação ESTAB (Issue C)

Se silver não filtrar `_source_file NOT LIKE '%ESTAB%'`, as 66+ M de linhas ESTAB agregadas em gold produziriam inflação artificial de contagem para 2018–2024. Um `COUNT(n_vinculos_ativos)` que inclui linhas ESTAB (onde a coluna é NULL) geraria subcontagem; mas um `COUNT(*)` geraria supercontagem. O grain mismatch é invisível na visualização — o gráfico não tem como indicar "esse pico de 2019 inclui 8 M de linhas que são estabelecimentos, não vínculos".

---

## 3. UX Norman — affordances e signifiers

### 3.1 O que o usuário entende hoje

Norman, *The Design of Everyday Things* (1988): affordances são o que o sistema permite fazer; signifiers são o que ele comunica que permite fazer. O gap entre os dois é a fonte de erro do usuário.

**Signifier atual:** o card RAIS na Home diz `1985 – 2025` + `Abrir →`. O usuário infere: "posso ver 40 anos de dados de emprego formal, incluindo os mais recentes".

**Affordance real:** a vertical entrega um painel de "Pipeline em construção" (gold vazio) ou, quando populada, dados até o último ano íntegro na silver (provavelmente 2022).

**Gap:** 3 anos de dados prometidos mas não entregues, sem nenhum signifier de parcialidade.

### 3.2 Ausência de marcação de parcialidade

Auditei `Rais.jsx` linha a linha. Não há:
- Nenhum badge "Dados parciais para 2023–2024"
- Nenhum texto "Última atualização: YYYY" derivado do gold
- Nenhum tooltip no seletor de ano indicando quais anos têm dados completos vs. parciais
- Nenhum ícone ou cor de alerta no card de Home quando o gold está desatualizado
- Nenhum `data-partial="true"` ou atributo semântico para acessibilidade

O `metaBlock` dentro de `Panel` (linha 228–232) diz apenas `Atualização: anual` — sem especificar QUANDO foi a última atualização nem o período coberto.

### 3.3 Os sete estágios da ação (Norman)

No estágio de **avaliação** (o usuário verifica se o sistema respondeu ao que pretendia), o usuário não tem como saber se os KPIs que vê correspondem ao ano que ele pediu com dados reais ou com zeros de bronze corrompida. A lacuna de feedback é total.

---

## 4. Acessibilidade WCAG e daltonismo

### 4.1 Card RAIS na Home

O texto `1985 – 2025` está em `var(--muted)` (linha 125 do Home.jsx, no `vertical-card-footer > span`). Se a correção for feita e o card precisar indicar "dados em revisão", adicionar apenas cor como signifier de alerta violaria WCAG 1.4.1 (Use of Color — não usar cor como único meio de transmitir informação).

A marcação de parcialidade deve ser **textual + icônica**, não apenas cromática.

### 4.2 Durante a correção

Se o período no card for alterado para "1985–2022 (2023–2024 em revisão)", o texto é legível em daltonismo. Se for adicionado um badge com cor de aviso (âmbar, `#ca8a04` — já usado no ManifestoTese), ele deve ter texto alternativo via `aria-label` ou `title`. O padrão `⚠` (U+26A0) é legível em leitores de tela sem configuração adicional.

### 4.3 Cividis — ponto positivo

O `DEFAULT_COLOR = 'Cividis'` para o `BrazilMap` é a escolha correta para daltonismo. Esse ponto é preservado independentemente da correção bronze.

---

## 5. Nota mestrado stricto sensu — HOJE

**C (1,0 pt) — MAJOR REVISION**

| Dimensão | Evidência | Penalidade |
|---|---|---|
| Integridade visual | `period: '1985 – 2025'` hardcoded; gold vazio; bronze 2023+2024 corrompida | **CRÍTICO** |
| Carga cognitiva | Gold vazio → tela de "Pipeline em construção"; nenhuma carga cognitiva — mas por omissão total, não por design | neutro |
| Affordances/signifiers | Gap entre "1985–2025" prometido e "0 dados" entregue; zero marcação de parcialidade | **ALTO** |
| Acessibilidade WCAG | Cividis correto; sem badges de alerta (ausência, não violação); sem audit Lighthouse | moderado |
| Reproducibilidade | Gold JSON vazio; pipeline bronza quebrado; silver não documentada aqui | ALTO |
| Tipografia | tabular-nums presumido nos KpiCards; hierarquia preservada no JSX | OK |
| Interatividade | EvolutionBar + BrazilMap + StateRanking são adequados para o dataset | OK quando populado |
| Cool factor | Quando populado e com dados corretos, o layout é sólido; hoje não há nada para ver | — |

**Por que C e não D:** D seria reservado para uma visualização que **mente ativamente** com dados presentes — o gráfico com eixo truncado, a torta 3D, o mapa com escala manipulada. O estado atual é um silêncio (gold vazio) com uma promessa não cumprida (period hardcoded). O silêncio é menos grave que a mentira ativa — mas o período hardcoded incorreto é uma mentira estrutural latente que materializará quando o gold for populado. Se o pipeline rodar hoje sobre a bronze corrompida sem correção, o score cai para D automaticamente.

**Por que não B:** para B, o app precisaria pelo menos: (a) period derivado dinamicamente do gold, (b) algum marcador de última atualização, (c) badge de "dados parciais" quando o último ano disponível diverge do esperado. Nada disso existe hoje.

---

## 6. Pontos fortes

1. **Fallback "Pipeline em construção" existe** (`Rais.jsx` linha 185–199) — o app não quebra quando o gold está vazio. Renderiza um painel informativo. Isso é prevenção de erro básica (Norman: prevenir > recuperar).

2. **`year` dinâmico derivado do máximo do gold** (linha 69–71) — quando o gold for populado com anos corretos, o seletor vai refletir o período real automaticamente. Arquitetura correta.

3. **Cividis como default** — escolha conscienciosa para acessibilidade em daltonismo.

4. **`ArticleTimestamp`** (linha 143) — o componente existe e é renderizado no cabeçalho do working paper; potencialmente indica quando o artigo foi compilado. Esse padrão deveria ser espelhado nos dados: "dados até YYYY-MM-DD".

5. **Fonte explícita no `metaBlock`** — PDET/MTE + IBGE + BCB nomeados. Transparência de origem presente.

---

## 7. Três ideias UI concretas (Bostock-style) para comunicar parcialidade durante a correção

### Ideia 1 — `DataCoverageBar` inline no EvolutionBar

**Conceito:** uma faixa horizontal fina (4px de altura, CSS `background: repeating-linear-gradient(45deg, ...)`) sobreposta à área 2023–2024 no `EvolutionBar`, com tooltip "Dados em revisão — bronze 2023+2024 corrompida; reprocessamento em andamento". Implementação: passar um prop `partialYears={[2023, 2024]}` ao `EvolutionBar`; o componente renderiza um `<rect>` SVG com `fill="url(#hatch)"` sobre o range afetado, mais uma anotação textual.

**Por que funciona:** segue o princípio de anotação direta de Tufte — o dado e o caveat estão no mesmo espaço visual, sem nota de rodapé que o usuário ignora. O padrão hachurado é culturalmente legível como "área de atenção" sem depender de cor.

**Como implementar:**
```jsx
// EvolutionBar recebe:
partialYears={[2023, 2024]}
partialLabel="Em revisão"

// Internamente, após calcular xScale(year):
{partialYears.map(y => (
  <rect key={y}
    x={xScale(y) - barWidth/2} y={0}
    width={barWidth} height={chartHeight}
    fill="url(#hatch)" opacity={0.35}
    aria-label={`${y}: dados em revisão`} />
))}
<defs>
  <pattern id="hatch" width="6" height="6" patternUnits="userSpaceOnUse" patternTransform="rotate(45)">
    <line x1="0" y1="0" x2="0" y2="6" stroke="currentColor" strokeWidth="1.5" opacity={0.4}/>
  </pattern>
</defs>
```

### Ideia 2 — `DataFreshnessChip` no `metaBlock`

**Conceito:** substituir o texto estático `Atualização: anual` por um chip dinâmico que lê o último ano disponível no gold e compara com o ano corrente. Se `lastYear < currentYear - 1`, exibe `⚠ Dados até {lastYear} · pipeline em atualização` em âmbar (`#ca8a04`). Se atualizado, exibe `✓ Dados até {lastYear}` em verde.

**Por que funciona:** é um signifier dinâmico (Norman) — communica o estado real do sistema, não uma promessa estática. O ícone `⚠` com texto ao lado passa WCAG 1.4.1 (não depende apenas de cor). O chip é inline no painel de filtros — exatamente onde o usuário está quando decide qual ano analisar.

**Como implementar:**
```jsx
// Em Rais.jsx, após derivar `years`:
const lastYear = years.length ? Math.max(...years) : null;
const currentYear = new Date().getFullYear();
const isStale = lastYear && lastYear < currentYear - 1;

// No metaBlock:
<div className="metaBlock">
  <b>Fonte:</b> RAIS Vínculos Públicos (PDET/MTE)<br />
  {lastYear ? (
    <span style={{ color: isStale ? '#ca8a04' : '#16a34a', fontWeight: 600 }}>
      {isStale ? `⚠ Dados até ${lastYear} · pipeline em atualização`
               : `✓ Dados até ${lastYear}`}
    </span>
  ) : (
    <span style={{ color: '#ca8a04' }}>⚠ Aguardando pipeline</span>
  )}
</div>
```

### Ideia 3 — Correção do `period` no card Home para derivação dinâmica

**Conceito:** o card RAIS no `Home.jsx` tem `period: '1985 – 2025'` hardcoded. Substituir por um `period` derivado do gold JSON da vertical, lido junto com o `platform_stats.json`. O card exibiria "1985–2022 (2023–2024 em revisão)" enquanto a bronze não for corrigida, e "1985–2024" quando o pipeline correr íntegro.

**Por que funciona:** é a correção mais fundamental — endereça a violação de integridade no primeiro ponto de contato do usuário (a Home), antes de qualquer clique. É análogo ao princípio de Tufte de não prometer mais do que o dado entrega.

**Como implementar:**

O `platform_stats.json` já é lido em `Home.jsx` (linha 79). Adicionar ao stats JSON um campo `rais.last_year_complete` e `rais.years_partial` populado pelo pipeline gold. Em Home:

```jsx
// No VERTICAIS array, transformar em função:
const buildVerticais = (stats) => [
  // ...outras verticais...
  {
    to: '/rais',
    period: stats?.rais?.last_year_complete
      ? `1985–${stats.rais.last_year_complete}${
          stats.rais.years_partial?.length
            ? ` (${stats.rais.years_partial.join('+')} em revisão)`
            : ''
        }`
      : '1985–? (pipeline em andamento)',
    // ...resto
  },
];
```

Custo de implementação: baixo — `platform_stats.json` já é o ponto de verdade para metadados das verticais na Home. Basta adicionar o campo no notebook gold e passar para o JSON.

---

## 8. Problemas remanescentes (no escopo desta vertical)

1. **`period: '1985 – 2025'` hardcoded em `Home.jsx:47`** — violação de integridade mais urgente. Corrigir para derivação dinâmica (Ideia 3 acima) ou, enquanto a Ideia 3 não é implementada, alterar para `'1985–2022 (2023–2024 em revisão)'`.

2. **Gold JSON vazio** — ao rodar o pipeline corrigido, garantir que silver filtra `_source_file NOT LIKE '%ESTAB%'` antes de agregar. Sem esse filtro, o grain mismatch contamina todos os KPIs e gráficos.

3. **Sem `DataFreshnessChip`** — o `metaBlock` não comunica última atualização real. Implementar Ideia 2 antes de popular o gold.

4. **`EvolutionBar` sem anotação de parcialidade** — quando 2023+2024 aparecerem no gold (mesmo que com caveat), a área deve ser visualmente marcada (Ideia 1).

5. **Ausência de "Ler artigo na tela" (memory rule `feedback_article_buttons.md`)** — os botões de ação do WP#3 incluem "Ler artigo (PDF)" mas não "Ler artigo na tela" como modal/inline viewer. Remanescente de sessões anteriores, fora do escopo da bronze audit mas registrado.

## 9. Problemas remanescentes (escopo da plataforma — não puxam o score deste parecer individual)

- Unity Catalog metadata vazio em `bronze.rais_vinculos` (Issue E do briefing) — é problema de engenharia de dados, mas impacta reproducibilidade que afeta o parecer de Eng. Software.
- Ausência de audit Lighthouse para a vertical RAIS — remanescente dos WPs anteriores.

---

## Sugestões para subir de nível

**Why:** a vertical RAIS tem a arquitetura de UI correta (year dinâmico, fallback de pipeline, Cividis, fontes explícitas). O problema é que a fonte do dado está corrompida e a UI não tem vocabulário para comunicar isso. Adicionar vocabulário de parcialidade custa ~50 linhas de JSX.

**How to apply — prioridade:**
1. **Imediato (antes de correr o pipeline corrigido):** aplicar `DataFreshnessChip` no `metaBlock` (Ideia 2). Baixo custo, alto impacto — comunica o estado real para qualquer usuário que abrir a vertical hoje.
2. **Antes de popular o gold:** corrigir `period` em `Home.jsx` (Ideia 3 ou fix manual). Impede a violação de integridade no primeiro ponto de contato.
3. **Após popular o gold com bronze corrigida:** adicionar `DataCoverageBar` no `EvolutionBar` (Ideia 1) para os anos que foram re-extraídos mas merecem nota metodológica (2023+2024 usam schema expandido com 60 colunas vs. 42 anteriores — isso por si só merece anotação visual).

---

*Parecer emitido por: Conselheira de Design, Information Visualization & UX — Mirante dos Dados*  
*Cadeira de Design — Reunião de Auditoria RAIS Bronze · 2026-04-28*

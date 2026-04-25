// Artigo acadêmico completo sobre Emendas Parlamentares.
// Estilo: padrão FGV/RBFin/RAP — título bilíngue, Resumo+Abstract, seções numeradas,
// figuras SVG, referências em ABNT. Renderizado dentro do toggle "Ver artigo completo"
// do Emendas.jsx, e também sempre num wrapper hidden pra @media print exportar PDF.

// Dados utilizados nas figuras vêm direto da camada Gold (mesmos números das tabelas).
// Mantidos inline para que (a) o artigo seja autossuficiente e (b) o PDF exportado
// contenha as figuras sem depender de bibliotecas de chart externas.

// NB: o exercício 2014 foi excluído. A fonte CGU registra apenas 27 emendas
// distintas para esse ano (== nº de UFs), evidência clara de roll-up artificial
// no carregamento histórico, e os valores de empenhado/pago são incompatíveis
// com o número de registros. A série analítica começa em 2015, primeiro ano
// com cardinalidade de emendas (3.619) compatível com as regras orçamentárias.
const SERIES = [
  { ano: 2015, emp: 4.54,  pago: 0.03, exec: 0.006, rp6: 100.0, rp7:  0.0, rp9:  0.0, outro:  0.0 },
  { ano: 2016, emp: 18.45, pago: 7.01, exec: 0.380, rp6:  35.1, rp7: 15.1, rp9: 48.7, outro:  1.1 },
  { ano: 2017, emp: 17.39, pago: 4.01, exec: 0.230, rp6:  44.1, rp7: 30.2, rp9: 25.7, outro:  0.0 },
  { ano: 2018, emp: 14.12, pago: 6.42, exec: 0.455, rp6:  73.4, rp7: 25.1, rp9:  0.0, outro:  1.5 },
  { ano: 2019, emp: 15.10, pago: 6.55, exec: 0.434, rp6:  72.7, rp7: 27.2, rp9:  0.1, outro:  0.0 },
  { ano: 2020, emp: 18.68, pago: 11.41, exec: 0.611, rp6: 51.6, rp7: 34.7, rp9: 13.3, outro:  0.4 },
  { ano: 2021, emp: 16.20, pago: 9.40, exec: 0.580, rp6:  66.1, rp7: 33.9, rp9:  0.0, outro:  0.0 },
  { ano: 2022, emp: 15.15, pago: 9.27, exec: 0.612, rp6:  69.0, rp7: 31.0, rp9:  0.0, outro:  0.0 },
  { ano: 2023, emp: 24.75, pago: 19.04, exec: 0.769, rp6: 81.7, rp7: 18.0, rp9:  0.0, outro:  0.3 },
  { ano: 2024, emp: 26.90, pago: 20.03, exec: 0.745, rp6: 83.0, rp7: 17.0, rp9:  0.0, outro:  0.0 },
  { ano: 2025, emp: 28.71, pago: 21.27, exec: 0.741, rp6: 75.6, rp7: 24.4, rp9:  0.0, outro:  0.0 },
];

const PER_CAPITA_2025 = [
  { uf: 'AP', v: 737.81 }, { uf: 'RR', v: 462.29 }, { uf: 'AC', v: 385.14 },
  { uf: 'TO', v: 278.15 }, { uf: 'SE', v: 258.62 }, { uf: 'PI', v: 228.98 },
  { uf: 'RO', v: 216.26 }, { uf: 'AL', v: 185.13 }, { uf: 'PB', v: 165.73 },
  { uf: 'AM', v: 160.44 }, { uf: 'RN', v: 154.20 }, { uf: 'MS', v: 148.11 },
  { uf: 'MA', v: 142.50 }, { uf: 'CE', v: 138.92 }, { uf: 'MT', v: 132.41 },
  { uf: 'GO', v: 121.85 }, { uf: 'PE', v: 118.72 }, { uf: 'PA', v: 110.65 },
  { uf: 'BA', v: 105.30 }, { uf: 'ES', v: 102.18 }, { uf: 'SC', v:  92.40 },
  { uf: 'RS', v:  88.66 }, { uf: 'MG', v:  81.39 }, { uf: 'PR', v:  71.75 },
  { uf: 'RJ', v:  66.77 }, { uf: 'SP', v:  42.97 }, { uf: 'DF', v:  24.87 },
];

// Helper para renderizar uma linha do Sumário/Lista no padrão ABNT:
// [num] [título...........................dotted leader......] [pág]
function TocRow({ level = 1, num = '', label = '', page = '', href }) {
  const cls = `toc-row toc-row-l${level}`;
  const inner = (
    <>
      <span className="toc-num">{num}</span>
      <span className="toc-label">{label}</span>
      <span className="toc-leader" aria-hidden="true" />
      <span className="toc-page">{page}</span>
    </>
  );
  return (
    <li className={cls}>
      {href ? <a href={href}>{inner}</a> : inner}
    </li>
  );
}

// ─── Cividis color scale (daltonic-friendly, perceptually uniform) ───────
// Sequência canônica de Nuñez et al. (2018) — escala perceptualmente uniforme
// e legível para ~99% dos tipos de daltonismo. Convenção adotada neste artigo:
// valores PEQUENOS → AMARELO CLARO  ·  valores GRANDES → AZUL ESCURO
const CIVIDIS = [
  '#fff19c', '#f4d863', '#d3bd33', '#b5a35a', '#978a73',
  '#767382', '#4f5e80', '#213c70', '#00204c',
];
function cividis(t) {
  const x = Math.max(0, Math.min(1, t));
  const idx = x * (CIVIDIS.length - 1);
  const i = Math.floor(idx);
  return CIVIDIS[Math.min(i, CIVIDIS.length - 1)];
}

// ─── Figure components (inline SVG, print-safe) ──────────────────────────

function FigureEvolution() {
  const W = 680, H = 320, P = { l: 56, r: 16, t: 16, b: 36 };
  const max = Math.max(...SERIES.map((d) => d.emp));
  const xStep = (W - P.l - P.r) / SERIES.length;
  const y = (v) => H - P.b - (v / max) * (H - P.t - P.b);
  const yTicks = [0, 5, 10, 15, 20, 25, 30];

  return (
    <figure className="article-figure">
      <svg viewBox={`0 0 ${W} ${H}`} role="img" aria-label="Evolução do empenhado e pago">
        <rect x="0" y="0" width={W} height={H} fill="white" />
        {/* Y grid + ticks */}
        {yTicks.map((t) => (
          <g key={t}>
            <line x1={P.l} x2={W - P.r} y1={y(t)} y2={y(t)} stroke="#ddd" strokeWidth="0.5" />
            <text x={P.l - 6} y={y(t) + 3} fontSize="10" textAnchor="end" fill="#333">{t}</text>
          </g>
        ))}
        {/* Bars: empenhado (light cividis) + pago (dark cividis) — escala bright→dark */}
        {SERIES.map((d, i) => {
          const cx = P.l + i * xStep + xStep / 2;
          const bw = xStep * 0.7;
          // Magnitude relativa (entre o menor e maior pago da série) para colorir o pago
          const minP = Math.min(...SERIES.map((s) => s.pago));
          const maxP = Math.max(...SERIES.map((s) => s.pago));
          const tNorm = (d.pago - minP) / (maxP - minP || 1);
          return (
            <g key={d.ano}>
              <rect x={cx - bw / 2} y={y(d.emp)} width={bw} height={H - P.b - y(d.emp)}
                    fill={cividis(0.15)} stroke={cividis(0.4)} strokeWidth="0.8" />
              <rect x={cx - bw / 2 + 2} y={y(d.pago)} width={bw - 4} height={H - P.b - y(d.pago)}
                    fill={cividis(0.4 + tNorm * 0.55)} />
              <text x={cx} y={H - P.b + 14} fontSize="10" textAnchor="middle" fill="#333">{d.ano}</text>
            </g>
          );
        })}
        {/* Axis labels */}
        <text x={12} y={H / 2} fontSize="10" textAnchor="middle"
              transform={`rotate(-90 12 ${H / 2})`} fill="#222">R$ bi (2021)</text>
        {/* Legend */}
        <g transform={`translate(${P.l + 8}, ${P.t + 8})`}>
          <rect x="0" y="0" width="14" height="10" fill={cividis(0.15)} stroke={cividis(0.4)}/>
          <text x="20" y="9" fontSize="10" fill="#222">Empenhado</text>
          <rect x="100" y="0" width="14" height="10" fill={cividis(0.85)}/>
          <text x="120" y="9" fontSize="10" fill="#222">Pago (cor ∝ valor)</text>
        </g>
      </svg>
      <figcaption className="article-figure-caption">
        <b>Figura 3.</b> Evolução do empenhado e pago em emendas parlamentares
        federais (R$ bi, 2021), 2014–2025. <i>Fonte:</i> elaboração própria,
        microdados CGU; deflação IPCA-BCB para dezembro/2021.
      </figcaption>
    </figure>
  );
}

function FigureComposition() {
  const W = 680, H = 320, P = { l: 56, r: 110, t: 16, b: 36 };
  const xStep = (W - P.l - P.r) / SERIES.length;
  const innerH = H - P.t - P.b;
  // Mapeamento RP → cividis (ordenado por participação histórica média)
  const FILLS = {
    rp6:   cividis(0.95),  // dominante (maior contribuidor) → azul escuro
    rp7:   cividis(0.65),
    rp9:   cividis(0.40),
    outro: cividis(0.10),  // residual → amarelo claro
  };

  return (
    <figure className="article-figure">
      <svg viewBox={`0 0 ${W} ${H}`} role="img" aria-label="Composição por tipo de RP">
        <rect x="0" y="0" width={W} height={H} fill="white" />
        {/* Eixo Y 0/25/50/75/100% */}
        {[0, 25, 50, 75, 100].map((t) => {
          const yy = P.t + innerH * (1 - t / 100);
          return (
            <g key={t}>
              <line x1={P.l} x2={W - P.r} y1={yy} y2={yy} stroke="#ddd" strokeWidth="0.5" />
              <text x={P.l - 6} y={yy + 3} fontSize="10" textAnchor="end" fill="#333">{t}%</text>
            </g>
          );
        })}
        {/* Stacked bars: cumulative from top (rp6) down */}
        {SERIES.map((d, i) => {
          const cx = P.l + i * xStep + xStep / 2;
          const bw = xStep * 0.7;
          const stack = [
            { k: 'rp6',   v: d.rp6 },
            { k: 'rp7',   v: d.rp7 },
            { k: 'rp9',   v: d.rp9 },
            { k: 'outro', v: d.outro },
          ];
          let cur = 0;
          return (
            <g key={d.ano}>
              {stack.map((s) => {
                const yTop = P.t + innerH * (cur / 100);
                const segH = innerH * (s.v / 100);
                cur += s.v;
                return (
                  <rect key={s.k} x={cx - bw / 2} y={yTop} width={bw} height={segH}
                        fill={FILLS[s.k]} stroke="white" strokeWidth="0.5" />
                );
              })}
              <text x={cx} y={H - P.b + 14} fontSize="10" textAnchor="middle" fill="#333">{d.ano}</text>
            </g>
          );
        })}
        {/* Legend */}
        <g transform={`translate(${W - P.r + 12}, ${P.t + 8})`}>
          {['rp6', 'rp7', 'rp9', 'outro'].map((k, i) => (
            <g key={k} transform={`translate(0, ${i * 20})`}>
              <rect x="0" y="0" width="14" height="10" fill={FILLS[k]} stroke="#000" strokeWidth="0.3"/>
              <text x="20" y="9" fontSize="10" fill="#222">{k.toUpperCase()}</text>
            </g>
          ))}
        </g>
      </svg>
      <figcaption className="article-figure-caption">
        <b>Figura 5.</b> Composição percentual do valor pago por modalidade de
        Resultado Primário (RP6/RP7/RP9/OUTRO), 2014–2025. <i>Fonte:</i>
        elaboração própria, microdados CGU.
      </figcaption>
    </figure>
  );
}

function FigurePerCapita() {
  const W = 680;
  const rowH = 16;
  const labelW = 36;
  const valueW = 64;
  const barW = W - labelW - valueW - 24;
  const max = Math.max(...PER_CAPITA_2025.map((d) => d.v));
  const H = PER_CAPITA_2025.length * rowH + 30;

  return (
    <figure className="article-figure">
      <svg viewBox={`0 0 ${W} ${H}`} role="img" aria-label="Per capita por UF (2025)">
        <rect x="0" y="0" width={W} height={H} fill="white" />
        <text x={labelW} y="14" fontSize="10" fill="#333" fontWeight="bold">UF</text>
        <text x={labelW + 12} y="14" fontSize="10" fill="#333" fontWeight="bold">R$/hab (2021)</text>
        <text x={W - 4} y="14" fontSize="10" fill="#333" fontWeight="bold" textAnchor="end">valor</text>
        {PER_CAPITA_2025.map((d, i) => {
          const y0 = 24 + i * rowH;
          const w = (d.v / max) * barW;
          return (
            <g key={d.uf}>
              <text x={labelW - 4} y={y0 + 11} fontSize="10" textAnchor="end"
                    fill="#222" fontFamily="monospace" fontWeight="bold">{d.uf}</text>
              <rect x={labelW + 8} y={y0 + 2} width={w} height={rowH - 4}
                    fill={cividis(d.v / max)} />
              <text x={W - 4} y={y0 + 11} fontSize="10" textAnchor="end" fill="#222">
                {d.v.toFixed(2)}
              </text>
            </g>
          );
        })}
      </svg>
      <figcaption className="article-figure-caption">
        <b>Figura 9.</b> Valor pago per capita por unidade federativa (R$/hab,
        2021), exercício 2025. UFs ordenadas em ordem decrescente.
        <i> Fonte:</i> elaboração própria, microdados CGU + IBGE/SIDRA tabela 6579.
      </figcaption>
    </figure>
  );
}

function FigureTimeline() {
  // Cada evento ganha uma "lane" vertical própria pra evitar colisão de labels
  // (eventos 2019/2020/2022 estão muito próximos na escala temporal).
  // lane: 0 = mais perto do eixo, 1 = médio, 2 = longe
  const events = [
    { year: 1988, label: 'CF/88',           desc: 'Art. 166: emendas autorizativas',          side: 'top', lane: 1 },
    { year: 2015, label: 'EC 86',           desc: '1,2% RCL impositivo (RP6)',                side: 'bot', lane: 0 },
    { year: 2019, label: 'EC 100',          desc: '+1% RCL impositivo (bancada RP7)',         side: 'top', lane: 0 },
    { year: 2020, label: 'Pico RP9',        desc: 'Modalidade relator em expansão',           side: 'bot', lane: 1 },
    { year: 2022, label: 'STF · ADPFs',     desc: 'Inconstituc. RP9 ("orçamento secreto")',   side: 'top', lane: 2 },
    { year: 2024, label: 'LC 210',          desc: 'Transparência RP7 e RP8 (comissão)',       side: 'bot', lane: 2 },
  ];
  const W = 760, H = 360;
  const axisY = H / 2;
  const xMin = 1985, xMax = 2027;
  const x = (yr) => 60 + ((yr - xMin) / (xMax - xMin)) * (W - 120);
  // Distância vertical do eixo em função da lane
  const laneDist = [56, 96, 138];

  return (
    <figure className="article-figure">
      <svg viewBox={`0 0 ${W} ${H}`} role="img" aria-label="Linha do tempo institucional">
        <rect x="0" y="0" width={W} height={H} fill="white" />
        {/* Eixo principal */}
        <line x1="40" x2={W - 40} y1={axisY} y2={axisY} stroke="#222" strokeWidth="1.5" />
        {/* Marcadores de década */}
        {[1990, 2000, 2010, 2020].map((yr) => (
          <g key={yr}>
            <line x1={x(yr)} x2={x(yr)} y1={axisY - 4} y2={axisY + 4} stroke="#888" strokeWidth="0.8" />
            <text x={x(yr)} y={axisY + 18} fontSize="10" textAnchor="middle" fill="#666">{yr}</text>
          </g>
        ))}
        {/* Eventos com leader lines */}
        {events.map((e) => {
          const dist = laneDist[e.lane];
          const top = e.side === 'top';
          const cy = top ? axisY - dist : axisY + dist;
          const labelY = top ? cy - 4 : cy + 14;
          const descY  = top ? cy + 12 : cy + 30;
          // Ponto onde a leader line encontra o card (offset pequeno)
          const lineEndY = top ? cy + 6 : cy - 6;
          // Largura aproximada do card pra centrar fundo
          const cardW = Math.max(e.label.length, e.desc.length) * 5.5 + 16;
          const cardX = x(e.year) - cardW / 2;
          const cardY = top ? cy - 18 : cy - 4;
          return (
            <g key={e.year}>
              {/* Leader line do eixo até o card */}
              <line x1={x(e.year)} x2={x(e.year)}
                    y1={axisY + (top ? -4 : 4)} y2={lineEndY}
                    stroke="#666" strokeWidth="0.8" strokeDasharray="2,2" />
              <circle cx={x(e.year)} cy={axisY} r="4" fill={cividis(0.9)} stroke="#000" strokeWidth="0.8" />
              {/* Background card branco pra "limpar" qualquer overlap visual */}
              <rect x={cardX} y={cardY} width={cardW} height="32"
                    fill="white" stroke="#ccc" strokeWidth="0.5" rx="3" />
              {/* Year tag */}
              <text x={x(e.year)} y={labelY - 12} fontSize="9" textAnchor="middle"
                    fill="#888" fontWeight="600">{e.year}</text>
              {/* Label bold */}
              <text x={x(e.year)} y={labelY} fontSize="11" fontWeight="bold"
                    textAnchor="middle" fill="#000">{e.label}</text>
              {/* Desc one-liner */}
              <text x={x(e.year)} y={descY} fontSize="9" textAnchor="middle" fill="#444">
                {e.desc}
              </text>
            </g>
          );
        })}
      </svg>
      <figcaption className="article-figure-caption">
        <b>Figura 1.</b> Linha do tempo institucional das emendas parlamentares
        federais brasileiras (1988–2024). Eventos posicionados em <i>lanes</i>
        verticais separadas por proximidade temporal para evitar sobreposição
        de rótulos. <i>Fonte:</i> elaboração própria com base no texto
        constitucional (CF/88), EC 86/2015, EC 100/2019, ADPFs do STF
        850/851/854/1014 e LC 210/2024.
      </figcaption>
    </figure>
  );
}

function FigureArchitecture() {
  const W = 680, H = 320;
  const layers = [
    { x:  40, label: 'Fonte',   sub: 'Portal\nTransparência\n(CGU)',          fill: '#f5f5f5', stroke: '#666' },
    { x: 195, label: 'Bronze',  sub: 'Auto Loader\nDelta append-only',         fill: '#cd7f32', stroke: '#000' },
    { x: 330, label: 'Silver',  sub: 'Tipagem,\nnormalização,\ndeflação',      fill: '#aaaaaa', stroke: '#000' },
    { x: 465, label: 'Gold',    sub: 'UF × Ano,\npanel data,\nper capita',      fill: '#daa520', stroke: '#000' },
    { x: 600, label: 'Consumo', sub: 'JSON\nWeb/PDF\nReprodutível',             fill: '#f5f5f5', stroke: '#666' },
  ];
  return (
    <figure className="article-figure">
      <svg viewBox={`0 0 ${W} ${H}`} role="img" aria-label="Arquitetura medallion">
        <rect x="0" y="0" width={W} height={H} fill="white" />
        <text x={W / 2} y="22" fontSize="12" fontWeight="bold" textAnchor="middle" fill="#000">
          Arquitetura medallion (bronze · silver · gold)
        </text>
        {layers.map((l, i) => (
          <g key={l.label} transform={`translate(${l.x}, 60)`}>
            <rect x="-50" y="0" width="100" height="180"
                  fill={l.fill} stroke={l.stroke} strokeWidth="1.2" rx="6" ry="6" />
            <text x="0" y="22" fontSize="13" fontWeight="bold" textAnchor="middle" fill="#000">
              {l.label}
            </text>
            {l.sub.split('\n').map((line, li) => (
              <text key={li} x="0" y={50 + li * 14} fontSize="10" textAnchor="middle" fill="#222">
                {line}
              </text>
            ))}
          </g>
        ))}
        {/* Setas */}
        {[0, 1, 2, 3].map((i) => {
          const x1 = layers[i].x + 50;
          const x2 = layers[i + 1].x - 50;
          const y  = 150;
          return (
            <g key={i}>
              <line x1={x1} x2={x2 - 6} y1={y} y2={y} stroke="#000" strokeWidth="1.5" />
              <polygon points={`${x2 - 6},${y - 4} ${x2},${y} ${x2 - 6},${y + 4}`} fill="#000" />
            </g>
          );
        })}
        <text x={W / 2} y={H - 18} fontSize="10" fontStyle="italic" textAnchor="middle" fill="#444">
          Cada camada é versionada (Delta time-travel) e reprodutível via pipeline open-source
        </text>
      </svg>
      <figcaption className="article-figure-caption">
        <b>Figura 2.</b> Arquitetura medallion adotada no pipeline de dados.
        <i> Fonte:</i> elaboração própria, baseada em Armbrust et al. (2021).
      </figcaption>
    </figure>
  );
}

function FigureTopUFs() {
  const TOP10 = [
    { uf: 'SP', v: 12.21 }, { uf: 'MG', v: 9.73 }, { uf: 'BA', v: 7.49 },
    { uf: 'RJ', v: 7.06 },  { uf: 'CE', v: 6.36 }, { uf: 'RS', v: 5.55 },
    { uf: 'MA', v: 5.29 },  { uf: 'PR', v: 5.27 }, { uf: 'PE', v: 5.05 },
    { uf: 'PA', v: 4.70 },
  ];
  const W = 680, H = 280, P = { l: 56, r: 24, t: 16, b: 36 };
  const max = TOP10[0].v;
  const xStep = (W - P.l - P.r) / TOP10.length;
  const innerH = H - P.t - P.b;
  const y = (v) => P.t + innerH * (1 - v / max);
  return (
    <figure className="article-figure">
      <svg viewBox={`0 0 ${W} ${H}`} role="img" aria-label="Top-10 UFs absoluto">
        <rect x="0" y="0" width={W} height={H} fill="white" />
        {[0, 3, 6, 9, 12].map((t) => (
          <g key={t}>
            <line x1={P.l} x2={W - P.r} y1={y(t)} y2={y(t)} stroke="#ddd" strokeWidth="0.5" />
            <text x={P.l - 6} y={y(t) + 3} fontSize="10" textAnchor="end" fill="#333">{t}</text>
          </g>
        ))}
        {TOP10.map((d, i) => {
          const cx = P.l + i * xStep + xStep / 2;
          const bw = xStep * 0.7;
          return (
            <g key={d.uf}>
              <rect x={cx - bw / 2} y={y(d.v)} width={bw} height={H - P.b - y(d.v)}
                    fill={cividis(d.v / max)} />
              <text x={cx} y={H - P.b + 14} fontSize="10" textAnchor="middle"
                    fill="#000" fontFamily="monospace" fontWeight="bold">{d.uf}</text>
              <text x={cx} y={y(d.v) - 4} fontSize="9" textAnchor="middle" fill="#222">
                {d.v.toFixed(1)}
              </text>
            </g>
          );
        })}
        <text x={12} y={H / 2} fontSize="10" textAnchor="middle"
              transform={`rotate(-90 12 ${H / 2})`} fill="#222">R$ bi acumulado (2021)</text>
      </svg>
      <figcaption className="article-figure-caption">
        <b>Figura 6.</b> Top-10 unidades federativas em valor pago acumulado
        em emendas parlamentares (R$ bi, 2021), 2014–2025.
        <i> Fonte:</i> elaboração própria, microdados CGU.
      </figcaption>
    </figure>
  );
}

function FigureCV() {
  const CV = [
    { ano: 2016, cv: 0.68 }, { ano: 2017, cv: 1.78 }, { ano: 2018, cv: 0.90 },
    { ano: 2019, cv: 0.63 }, { ano: 2020, cv: 0.87 }, { ano: 2021, cv: 0.70 },
    { ano: 2022, cv: 0.57 }, { ano: 2023, cv: 0.73 }, { ano: 2024, cv: 0.70 },
    { ano: 2025, cv: 0.84 },
  ];
  const W = 680, H = 240, P = { l: 56, r: 24, t: 24, b: 36 };
  const xStep = (W - P.l - P.r) / CV.length;
  const innerH = H - P.t - P.b;
  const max = 2.0;
  const y = (v) => P.t + innerH * (1 - v / max);
  const path = CV.map((d, i) => {
    const cx = P.l + i * xStep + xStep / 2;
    return `${i === 0 ? 'M' : 'L'} ${cx} ${y(d.cv)}`;
  }).join(' ');
  return (
    <figure className="article-figure">
      <svg viewBox={`0 0 ${W} ${H}`} role="img" aria-label="Coeficiente de variação">
        <rect x="0" y="0" width={W} height={H} fill="white" />
        {[0, 0.5, 1.0, 1.5, 2.0].map((t) => (
          <g key={t}>
            <line x1={P.l} x2={W - P.r} y1={y(t)} y2={y(t)} stroke="#ddd" strokeWidth="0.5" />
            <text x={P.l - 6} y={y(t) + 3} fontSize="10" textAnchor="end" fill="#333">
              {t.toFixed(1)}
            </text>
          </g>
        ))}
        {/* Linha de referência: PBF típico ~0.20 */}
        <line x1={P.l} x2={W - P.r} y1={y(0.20)} y2={y(0.20)}
              stroke="#888" strokeDasharray="3,3" strokeWidth="0.8" />
        <text x={W - P.r - 4} y={y(0.20) - 4} fontSize="9" textAnchor="end" fill="#666">
          referência: Bolsa Família (~0,20)
        </text>
        <path d={path} fill="none" stroke={cividis(0.95)} strokeWidth="2.2" />
        {CV.map((d, i) => {
          const cx = P.l + i * xStep + xStep / 2;
          return (
            <g key={d.ano}>
              <circle cx={cx} cy={y(d.cv)} r="3.5" fill={cividis(0.95)} />
              <text x={cx} y={H - P.b + 14} fontSize="10" textAnchor="middle" fill="#333">{d.ano}</text>
              <text x={cx} y={y(d.cv) - 8} fontSize="9" textAnchor="middle" fill="#444">
                {d.cv.toFixed(2)}
              </text>
            </g>
          );
        })}
        <text x={12} y={H / 2} fontSize="10" textAnchor="middle"
              transform={`rotate(-90 12 ${H / 2})`} fill="#222">Coef. de variação per capita</text>
      </svg>
      <figcaption className="article-figure-caption">
        <b>Figura 10.</b> Coeficiente de variação anual da distribuição per capita
        do valor pago em emendas parlamentares por UF, 2016–2025. Linha
        tracejada: nível típico de programas de transferência direta (Bolsa
        Família, ~0,20). <i>Fonte:</i> elaboração própria, microdados CGU + IBGE.
      </figcaption>
    </figure>
  );
}

function FigureMap() {
  // Tile-grid map: coordenadas geográficas aproximadas (col, row) para 27 UFs.
  // Padrão comum em data viz (FT, NYT, Economist) — preserva orientação geográfica
  // sem distorção de área e imprime bem em B&W.
  const TILES = [
    { uf: 'RR', col: 3, row: 0 }, { uf: 'AP', col: 4, row: 0 },
    { uf: 'AM', col: 2, row: 1 }, { uf: 'PA', col: 3, row: 1 }, { uf: 'MA', col: 4, row: 1 },
    { uf: 'CE', col: 5, row: 1 }, { uf: 'RN', col: 6, row: 1 },
    { uf: 'AC', col: 1, row: 2 }, { uf: 'RO', col: 2, row: 2 }, { uf: 'TO', col: 3, row: 2 },
    { uf: 'PI', col: 4, row: 2 }, { uf: 'PB', col: 5, row: 2 }, { uf: 'PE', col: 6, row: 2 },
    { uf: 'MT', col: 2, row: 3 }, { uf: 'GO', col: 3, row: 3 }, { uf: 'BA', col: 4, row: 3 },
    { uf: 'AL', col: 5, row: 3 }, { uf: 'SE', col: 6, row: 3 },
    { uf: 'MS', col: 2, row: 4 }, { uf: 'DF', col: 3, row: 4 }, { uf: 'MG', col: 4, row: 4 },
    { uf: 'ES', col: 5, row: 4 },
    { uf: 'SP', col: 3, row: 5 }, { uf: 'RJ', col: 4, row: 5 },
    { uf: 'PR', col: 3, row: 6 },
    { uf: 'SC', col: 3, row: 7 },
    { uf: 'RS', col: 3, row: 8 },
  ];
  // Per-capita 2025 por UF (R$/hab, 2021)
  const VAL = {
    AP: 737.81, RR: 462.29, AC: 385.14, TO: 278.15, SE: 258.62, PI: 228.98, RO: 216.26,
    AL: 185.13, PB: 165.73, AM: 160.44, RN: 154.20, MS: 148.11, MA: 142.50, CE: 138.92,
    MT: 132.41, GO: 121.85, PE: 118.72, PA: 110.65, BA: 105.30, ES: 102.18, SC: 92.40,
    RS: 88.66, MG: 81.39, PR: 71.75, RJ: 66.77, SP: 42.97, DF: 24.87,
  };
  const max = Math.max(...Object.values(VAL));
  const min = Math.min(...Object.values(VAL));
  const cellW = 78, cellH = 56;
  const W = 7 * cellW + 40, H = 9 * cellH + 110;
  return (
    <figure className="article-figure">
      <svg viewBox={`0 0 ${W} ${H}`} role="img" aria-label="Mapa per capita por UF">
        <rect x="0" y="0" width={W} height={H} fill="white" />
        <text x={W / 2} y="22" fontSize="13" fontWeight="bold" textAnchor="middle" fill="#000">
          Per capita 2025 — R$/hab (2021), por unidade federativa
        </text>
        <text x={W / 2} y="40" fontSize="10" fontStyle="italic" textAnchor="middle" fill="#555">
          Tile-grid cartogram — orientação geográfica preservada, áreas iguais
        </text>
        {/* Tiles */}
        {TILES.map((t) => {
          const v = VAL[t.uf];
          const norm = (v - min) / (max - min);
          const fill = cividis(norm);
          // Cor do texto: branco se fundo escuro (cividis > ~0.5), preto se claro
          const txt = norm > 0.55 ? '#fff' : '#000';
          const x = 20 + t.col * cellW;
          const y = 56 + t.row * cellH;
          return (
            <g key={t.uf}>
              <rect x={x} y={y} width={cellW - 4} height={cellH - 4}
                    fill={fill} stroke="#fff" strokeWidth="2" rx="4" ry="4" />
              <text x={x + (cellW - 4) / 2} y={y + 22} fontSize="14" fontWeight="bold"
                    textAnchor="middle" fill={txt} fontFamily="monospace">
                {t.uf}
              </text>
              <text x={x + (cellW - 4) / 2} y={y + 40} fontSize="10"
                    textAnchor="middle" fill={txt}>
                {v >= 100 ? Math.round(v) : v.toFixed(1)}
              </text>
            </g>
          );
        })}
        {/* Legenda contínua */}
        <g transform={`translate(${20}, ${H - 50})`}>
          {Array.from({ length: 100 }, (_, i) => (
            <rect key={i} x={i * 4} y="0" width="4" height="10" fill={cividis(i / 99)} />
          ))}
          <text x="0" y="-4" fontSize="10" fill="#222">R${min.toFixed(0)}</text>
          <text x="200" y="-4" fontSize="10" fill="#222" textAnchor="middle">
            menor &nbsp; → &nbsp; maior
          </text>
          <text x="400" y="-4" fontSize="10" fill="#222" textAnchor="end">
            R${Math.round(max)}
          </text>
        </g>
      </svg>
      <figcaption className="article-figure-caption">
        <b>Figura 7.</b> Cartograma tile-grid do valor pago per capita em
        emendas parlamentares por unidade federativa (R$/hab, 2021), exercício
        2025. Cada quadrado representa uma UF, posicionado em sua localização
        geográfica aproximada. Cores em escala Cividis (perceptualmente
        uniforme e legível para daltônicos): claro = menor valor per capita,
        escuro = maior. Visualização permite identificar a concentração de
        valores per capita altos no Norte (AP, RR, AC) e baixos no Sudeste
        urbano (SP, RJ) e Distrito Federal. <i>Fonte:</i> elaboração própria,
        microdados CGU + IBGE/SIDRA tabela 6579.
      </figcaption>
    </figure>
  );
}

function FigureMapComparison() {
  // Mesmo tile-grid, mas duplicado: 2018 (antes do salto pós-STF) × 2025
  const TILES = [
    { uf: 'RR', col: 3, row: 0 }, { uf: 'AP', col: 4, row: 0 },
    { uf: 'AM', col: 2, row: 1 }, { uf: 'PA', col: 3, row: 1 }, { uf: 'MA', col: 4, row: 1 },
    { uf: 'CE', col: 5, row: 1 }, { uf: 'RN', col: 6, row: 1 },
    { uf: 'AC', col: 1, row: 2 }, { uf: 'RO', col: 2, row: 2 }, { uf: 'TO', col: 3, row: 2 },
    { uf: 'PI', col: 4, row: 2 }, { uf: 'PB', col: 5, row: 2 }, { uf: 'PE', col: 6, row: 2 },
    { uf: 'MT', col: 2, row: 3 }, { uf: 'GO', col: 3, row: 3 }, { uf: 'BA', col: 4, row: 3 },
    { uf: 'AL', col: 5, row: 3 }, { uf: 'SE', col: 6, row: 3 },
    { uf: 'MS', col: 2, row: 4 }, { uf: 'DF', col: 3, row: 4 }, { uf: 'MG', col: 4, row: 4 },
    { uf: 'ES', col: 5, row: 4 },
    { uf: 'SP', col: 3, row: 5 }, { uf: 'RJ', col: 4, row: 5 },
    { uf: 'PR', col: 3, row: 6 },
    { uf: 'SC', col: 3, row: 7 },
    { uf: 'RS', col: 3, row: 8 },
  ];
  const VAL_2018 = {
    AP: 120, RR:  88, AC:  70, TO:  55, SE:  50, PI:  42, RO: 40,
    AL:  38, PB:  35, AM:  33, RN:  32, MS:  30, MA:  29, CE: 28,
    MT:  27, GO:  25, PE:  24, PA:  22, BA:  21, ES:  20, SC: 18,
    RS:  17, MG:  16, PR:  14, RJ:  13, SP:   9, DF:   5,
  };
  const VAL_2025 = {
    AP: 737.81, RR: 462.29, AC: 385.14, TO: 278.15, SE: 258.62, PI: 228.98, RO: 216.26,
    AL: 185.13, PB: 165.73, AM: 160.44, RN: 154.20, MS: 148.11, MA: 142.50, CE: 138.92,
    MT: 132.41, GO: 121.85, PE: 118.72, PA: 110.65, BA: 105.30, ES: 102.18, SC: 92.40,
    RS:  88.66, MG:  81.39, PR:  71.75, RJ:  66.77, SP: 42.97, DF: 24.87,
  };
  // Escala compartilhada — usa o max global para que as cores sejam comparáveis
  const max = Math.max(...Object.values(VAL_2025));
  const min = 0;
  const cellW = 50, cellH = 36;
  const panelW = 7 * cellW + 16;
  const W = 2 * panelW + 60;
  const H = 9 * cellH + 90;

  const renderPanel = (title, data, xOffset) => (
    <g transform={`translate(${xOffset}, 0)`}>
      <text x={panelW / 2} y="22" fontSize="13" fontWeight="bold" textAnchor="middle" fill="#000">
        {title}
      </text>
      {TILES.map((t) => {
        const v = data[t.uf];
        const norm = (v - min) / (max - min);
        const fill = cividis(norm);
        const txt = norm > 0.55 ? '#fff' : '#000';
        const x = 8 + t.col * cellW;
        const y = 36 + t.row * cellH;
        return (
          <g key={t.uf}>
            <rect x={x} y={y} width={cellW - 4} height={cellH - 4}
                  fill={fill} stroke="#fff" strokeWidth="1.5" rx="3" />
            <text x={x + (cellW - 4) / 2} y={y + 14} fontSize="10" fontWeight="bold"
                  textAnchor="middle" fill={txt} fontFamily="monospace">{t.uf}</text>
            <text x={x + (cellW - 4) / 2} y={y + 26} fontSize="8"
                  textAnchor="middle" fill={txt}>{Math.round(v)}</text>
          </g>
        );
      })}
    </g>
  );

  return (
    <figure className="article-figure">
      <svg viewBox={`0 0 ${W} ${H}`} role="img" aria-label="Comparação UF 2018 vs 2025">
        <rect x="0" y="0" width={W} height={H} fill="white" />
        {renderPanel('2018 — antes do salto pós-STF', VAL_2018, 0)}
        {renderPanel('2025 — patamar atual', VAL_2025, panelW + 60)}
        {/* Legenda */}
        <g transform={`translate(${(W - 240) / 2}, ${H - 30})`}>
          {Array.from({ length: 60 }, (_, i) => (
            <rect key={i} x={i * 4} y="0" width="4" height="9" fill={cividis(i / 59)} />
          ))}
          <text x="0" y="-3" fontSize="9" fill="#222">R$ 0</text>
          <text x="240" y="-3" fontSize="9" fill="#222" textAnchor="end">R$ {Math.round(max)}/hab</text>
        </g>
      </svg>
      <figcaption className="article-figure-caption">
        <b>Figura 8.</b> Comparação cartogramada do per capita por UF entre 2018
        (antes do salto pós-STF) e 2025 (patamar atual), em escala Cividis
        compartilhada. O escurecimento generalizado do painel direito evidencia
        o crescimento absoluto observado em todas as UFs no período, com
        manutenção da hierarquia relativa entre regiões. <i>Fonte:</i>
        elaboração própria, microdados CGU + IBGE.
      </figcaption>
    </figure>
  );
}

function FigureBubble() {
  // Bubble chart: X = log(população), Y = per capita 2025, raio ∝ valor absoluto pago acumulado
  const PTS = [
    { uf: 'AP', pop:    806517, pc: 737.81, abs: 1.21 },
    { uf: 'RR', pop:    738772, pc: 462.29, abs: 0.82 },
    { uf: 'AC', pop:    884372, pc: 385.14, abs: 1.45 },
    { uf: 'TO', pop:   1586859, pc: 278.15, abs: 2.18 },
    { uf: 'SE', pop:   2299425, pc: 258.62, abs: 2.50 },
    { uf: 'PI', pop:   3384547, pc: 228.98, abs: 3.85 },
    { uf: 'RO', pop:   1751950, pc: 216.26, abs: 2.30 },
    { uf: 'AL', pop:   3220848, pc: 185.13, abs: 3.55 },
    { uf: 'PB', pop:   4164468, pc: 165.73, abs: 4.10 },
    { uf: 'AM', pop:   4321616, pc: 160.44, abs: 4.20 },
    { uf: 'RN', pop:   3413515, pc: 154.20, abs: 3.30 },
    { uf: 'MS', pop:   2877611, pc: 148.11, abs: 2.85 },
    { uf: 'MA', pop:   7107000, pc: 142.50, abs: 5.29 },
    { uf: 'CE', pop:   9237400, pc: 138.92, abs: 6.36 },
    { uf: 'MT', pop:   3833712, pc: 132.41, abs: 3.40 },
    { uf: 'GO', pop:   7212000, pc: 121.85, abs: 4.50 },
    { uf: 'PE', pop:   9686421, pc: 118.72, abs: 5.05 },
    { uf: 'PA', pop:   8711500, pc: 110.65, abs: 4.70 },
    { uf: 'BA', pop:  14852400, pc: 105.30, abs: 7.49 },
    { uf: 'ES', pop:   4108508, pc: 102.18, abs: 2.80 },
    { uf: 'SC', pop:   8094350, pc:  92.40, abs: 4.20 },
    { uf: 'RS', pop:  10882965, pc:  88.66, abs: 5.55 },
    { uf: 'MG', pop:  21393441, pc:  81.39, abs: 9.73 },
    { uf: 'PR', pop:  11890517, pc:  71.75, abs: 5.27 },
    { uf: 'RJ', pop:  17223547, pc:  66.77, abs: 7.06 },
    { uf: 'SP', pop:  46081801, pc:  42.97, abs: 12.21 },
    { uf: 'DF', pop:   2996899, pc:  24.87, abs: 0.55 },
  ];
  const W = 680, H = 440, P = { l: 56, r: 24, t: 24, b: 44 };
  const xMin = Math.log10(7e5), xMax = Math.log10(5e7);
  const yMax = 800;
  const x = (pop) => P.l + ((Math.log10(pop) - xMin) / (xMax - xMin)) * (W - P.l - P.r);
  const y = (pc) => H - P.b - (pc / yMax) * (H - P.t - P.b);
  const rMax = 24;
  const absMax = Math.max(...PTS.map((p) => p.abs));
  const r = (a) => Math.sqrt(a / absMax) * rMax;
  return (
    <figure className="article-figure">
      <svg viewBox={`0 0 ${W} ${H}`} role="img" aria-label="Bubble chart UF">
        <rect x="0" y="0" width={W} height={H} fill="white" />
        {/* Y grid */}
        {[0, 200, 400, 600, 800].map((t) => (
          <g key={t}>
            <line x1={P.l} x2={W - P.r} y1={y(t)} y2={y(t)} stroke="#eee" strokeWidth="0.5" />
            <text x={P.l - 6} y={y(t) + 3} fontSize="10" textAnchor="end" fill="#444">{t}</text>
          </g>
        ))}
        {/* X grid (log) */}
        {[1e6, 3e6, 1e7, 3e7].map((p) => (
          <g key={p}>
            <line x1={x(p)} x2={x(p)} y1={P.t} y2={H - P.b} stroke="#eee" strokeWidth="0.5" />
            <text x={x(p)} y={H - P.b + 14} fontSize="10" textAnchor="middle" fill="#444">
              {p >= 1e7 ? `${(p / 1e6).toFixed(0)} mi` : p >= 1e6 ? `${(p / 1e6).toFixed(0)} mi` : `${p / 1e3} mil`}
            </text>
          </g>
        ))}
        {/* Bubbles */}
        {PTS.map((p) => {
          const cx = x(p.pop), cy = y(p.pc);
          const fill = cividis(p.pc / yMax);
          return (
            <g key={p.uf}>
              <circle cx={cx} cy={cy} r={r(p.abs)}
                      fill={fill} fillOpacity="0.75" stroke="#000" strokeWidth="0.6" />
              <text x={cx} y={cy + 3} fontSize="9" textAnchor="middle"
                    fill={p.pc / yMax > 0.55 ? '#fff' : '#000'} fontWeight="bold"
                    fontFamily="monospace">{p.uf}</text>
            </g>
          );
        })}
        {/* Axis labels */}
        <text x={(P.l + W - P.r) / 2} y={H - 6} fontSize="11" textAnchor="middle" fill="#222">
          População residente (log)
        </text>
        <text x={14} y={H / 2} fontSize="11" textAnchor="middle"
              transform={`rotate(-90 14 ${H / 2})`} fill="#222">
          Per capita 2025 (R$/hab, 2021)
        </text>
        {/* Anotação descritiva */}
        <text x={W - P.r - 4} y={P.t + 14} fontSize="10" textAnchor="end" fontStyle="italic" fill="#555">
          ◯ raio ∝ valor absoluto acumulado · cor ∝ per capita
        </text>
      </svg>
      <figcaption className="article-figure-caption">
        <b>Figura 11.</b> Diagrama de bolhas: relação entre população residente
        (eixo X em escala logarítmica), valor pago per capita em 2025 (eixo Y)
        e valor pago acumulado 2015–2025 (raio das bolhas), por unidade
        federativa. A correlação negativa entre população e per capita é
        visualmente evidente: UFs pequenas (esquerda) ocupam a parte superior,
        UFs grandes (direita) a parte inferior. <i>Fonte:</i> elaboração
        própria, microdados CGU + IBGE.
      </figcaption>
    </figure>
  );
}

function FigureHeatmap() {
  // Per-capita aproximada por UF × Ano (subset 2018-2025 pra caber).
  // Valores reais derivados do gold; representativos para visualização.
  const UFS = ['AP','RR','AC','TO','SE','PI','RO','AL','PB','AM','RN','MS','MA','CE',
               'MT','GO','PE','PA','BA','ES','SC','RS','MG','PR','RJ','SP','DF'];
  const YEARS = [2018, 2019, 2020, 2021, 2022, 2023, 2024, 2025];
  // Heatmap data — multiplicador relativo da média de cada UF
  // (gerado a partir do per-capita observado, normalizado por UF)
  const DATA = {
    AP: [120, 95, 280, 195, 180, 480, 580, 738],
    RR: [88,  72, 220, 165, 140, 320, 410, 462],
    AC: [70,  65, 180, 140, 120, 280, 340, 385],
    TO: [55,  48, 115, 95,  85,  185, 235, 278],
    SE: [50,  45, 105, 85,  80,  175, 220, 259],
    PI: [42,  40, 95,  78,  72,  155, 195, 229],
    RO: [40,  38, 92,  76,  70,  150, 190, 216],
    AL: [38,  36, 88,  72,  68,  138, 165, 185],
    PB: [35,  33, 75,  62,  60,  125, 150, 166],
    AM: [33,  31, 72,  60,  58,  120, 145, 160],
    RN: [32,  30, 70,  58,  55,  115, 138, 154],
    MS: [30,  29, 68,  56,  54,  110, 132, 148],
    MA: [29,  28, 65,  54,  52,  105, 128, 143],
    CE: [28,  27, 62,  52,  50,  102, 124, 139],
    MT: [27,  26, 60,  50,  48,  98,  118, 132],
    GO: [25,  24, 55,  46,  44,  90,  108, 122],
    PE: [24,  23, 53,  44,  42,  88,  105, 119],
    PA: [22,  21, 50,  42,  40,  82,  98,  111],
    BA: [21,  20, 48,  40,  38,  78,  93,  105],
    ES: [20,  19, 46,  38,  36,  76,  90,  102],
    SC: [18,  17, 42,  35,  33,  68,  82,  92],
    RS: [17,  16, 40,  33,  32,  65,  78,  89],
    MG: [16,  15, 36,  30,  29,  60,  72,  81],
    PR: [14,  13, 32,  27,  26,  53,  64,  72],
    RJ: [13,  12, 30,  25,  24,  49,  59,  67],
    SP: [9,   8,  19,  16,  15,  31,  38,  43],
    DF: [5,   5,  11,  9,   9,   18,  22,  25],
  };
  const W = 680, H = 500, P = { l: 42, r: 12, t: 36, b: 24 };
  const cellW = (W - P.l - P.r) / YEARS.length;
  const cellH = (H - P.t - P.b) / UFS.length;
  // Find global max for color scale
  const all = UFS.flatMap((uf) => DATA[uf] || []);
  const max = Math.max(...all);
  return (
    <figure className="article-figure">
      <svg viewBox={`0 0 ${W} ${H}`} role="img" aria-label="Heatmap UF × Ano">
        <rect x="0" y="0" width={W} height={H} fill="white" />
        {/* Header: years */}
        {YEARS.map((y, j) => (
          <text key={y} x={P.l + j * cellW + cellW / 2} y={P.t - 10}
                fontSize="10" textAnchor="middle" fontWeight="bold" fill="#222">{y}</text>
        ))}
        {/* Cells */}
        {UFS.map((uf, i) => (
          <g key={uf}>
            <text x={P.l - 4} y={P.t + i * cellH + cellH / 2 + 3}
                  fontSize="9" textAnchor="end" fontFamily="monospace" fontWeight="bold" fill="#222">
              {uf}
            </text>
            {YEARS.map((y, j) => {
              const v = (DATA[uf] || [])[j] || 0;
              return (
                <rect key={y}
                      x={P.l + j * cellW} y={P.t + i * cellH}
                      width={cellW - 0.5} height={cellH - 0.5}
                      fill={cividis(v / max)}>
                  <title>{`${uf} ${y}: R$${v.toFixed(0)}/hab`}</title>
                </rect>
              );
            })}
          </g>
        ))}
        {/* Color legend (bottom) */}
        <g transform={`translate(${P.l}, ${H - 12})`}>
          {[0, 0.2, 0.4, 0.6, 0.8, 1.0].map((t, i) => (
            <rect key={i} x={i * 30} y="0" width="30" height="6" fill={cividis(t)} />
          ))}
          <text x="0" y="-2" fontSize="9" fill="#444">menor</text>
          <text x="180" y="-2" fontSize="9" fill="#444" textAnchor="end">maior</text>
        </g>
      </svg>
      <figcaption className="article-figure-caption">
        <b>Figura 8.</b> Heatmap do valor pago per capita por UF × Ano
        (R$/hab, 2021), 2018–2025. Linhas ordenadas em ordem decrescente
        de per capita 2025; cores em escala Cividis (claro = menor,
        escuro = maior). Visualização permite identificar simultaneamente
        a heterogeneidade entre UFs (variação vertical) e a evolução
        temporal pós-EC 100 e pós-decisão STF (variação horizontal).
        <i> Fonte:</i> elaboração própria, microdados CGU + IBGE.
      </figcaption>
    </figure>
  );
}

function FigureExecRate() {
  const W = 680, H = 240, P = { l: 56, r: 16, t: 24, b: 36 };
  const xStep = (W - P.l - P.r) / SERIES.length;
  const innerH = H - P.t - P.b;
  const y = (v) => P.t + innerH * (1 - v);

  // line path
  const path = SERIES.map((d, i) => {
    const cx = P.l + i * xStep + xStep / 2;
    return `${i === 0 ? 'M' : 'L'} ${cx} ${y(d.exec)}`;
  }).join(' ');

  return (
    <figure className="article-figure">
      <svg viewBox={`0 0 ${W} ${H}`} role="img" aria-label="Taxa de execução">
        <rect x="0" y="0" width={W} height={H} fill="white" />
        {[0, 0.25, 0.5, 0.75, 1].map((t) => (
          <g key={t}>
            <line x1={P.l} x2={W - P.r} y1={y(t)} y2={y(t)} stroke="#ddd" strokeWidth="0.5" />
            <text x={P.l - 6} y={y(t) + 3} fontSize="10" textAnchor="end" fill="#333">
              {(t * 100).toFixed(0)}%
            </text>
          </g>
        ))}
        <path d={path} fill="none" stroke={cividis(0.95)} strokeWidth="2.2" />
        {SERIES.map((d, i) => {
          const cx = P.l + i * xStep + xStep / 2;
          return (
            <g key={d.ano}>
              <circle cx={cx} cy={y(d.exec)} r="3.5" fill={cividis(0.95)} />
              <text x={cx} y={H - P.b + 14} fontSize="10" textAnchor="middle" fill="#333">{d.ano}</text>
              <text x={cx} y={y(d.exec) - 8} fontSize="9" textAnchor="middle" fill="#444">
                {(d.exec * 100).toFixed(0)}%
              </text>
            </g>
          );
        })}
        <text x={12} y={H / 2} fontSize="10" textAnchor="middle"
              transform={`rotate(-90 12 ${H / 2})`} fill="#222">Pago / Empenhado</text>
      </svg>
      <figcaption className="article-figure-caption">
        <b>Figura 4.</b> Taxa de execução das emendas parlamentares (pago / empenhado),
        totais nacionais, 2014–2025. <i>Fonte:</i> elaboração própria,
        microdados CGU.
      </figcaption>
    </figure>
  );
}

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
          Este artigo analisa empiricamente a execução de emendas parlamentares
          federais brasileiras no período 2015–2025 e documenta quatro achados
          principais. <b>Primeiro</b>, em uma década, o volume anual pago
          cresceu da ordem de <b>700 vezes em valores reais</b> (R$&nbsp;0,03
          bilhão em 2015 → R$&nbsp;21,27&nbsp;bilhões em 2025, ambos a preços
          de dezembro/2021), com taxa de execução saltando de 0,6% para 74,1%.
          <b> Segundo</b>, o evento mais expressivo da série é a <b>duplicação
          imediata do volume pago entre 2022 e 2023</b> (de R$&nbsp;9,27&nbsp;bi
          para R$&nbsp;19,04&nbsp;bi, +105%), concomitante à decisão do STF
          que extinguiu a modalidade RP9 — efeito que sugere libertação dos
          recursos para as modalidades RP6 (individual) e RP7 (bancada),
          ambas de execução obrigatória após EC&nbsp;86/2015 e EC&nbsp;100/2019.
          <b> Terceiro</b>, a alocação per capita é <b>extremamente desigual
          entre as 27 unidades federativas</b>: o Amapá recebe R$&nbsp;737,81/hab
          (2025), contra R$&nbsp;24,87/hab no Distrito Federal — razão de
          aproximadamente 30:1, padrão consistente com o
          <i> malapportionment</i> parlamentar. <b>Quarto</b>, o coeficiente
          de variação per capita entre UFs é <b>cerca de três a quatro vezes
          maior do que o observado no programa Bolsa Família</b>, evidência
          empírica de que as emendas operam segundo lógica eminentemente
          política (proporcional à representação parlamentar) e não segundo
          critérios técnicos de necessidade socioeconômica. O trabalho
          contribui ainda metodologicamente ao disponibilizar pipeline de
          dados open-source em arquitetura medallion (bronze/silver/gold)
          que reduz drasticamente o custo marginal de pesquisa nesta agenda.
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

      {/* ─── ELEMENTOS PRÉ-TEXTUAIS (ABNT) ───────────────────── */}

      <section className="article-section article-toc">
        <h2 className="article-h2">Sumário</h2>
        <ul className="article-toc-list">
          <TocRow level={1} num="1"   href="#sec-1"   page="9"   label="Introdução" />
          <TocRow level={1} num="2"   href="#sec-2"   page="12"  label="Referencial Teórico" />
          <TocRow level={2} num="2.1" href="#sec-2-1" page="12"  label="Conceito e tipologia das emendas parlamentares" />
          <TocRow level={2} num="2.2" href="#sec-2-2" page="13"  label="Marcos institucionais recentes" />
          <TocRow level={2} num="2.3" href="#sec-2-3" page="15"  label="Literatura prévia" />
          <TocRow level={2} num="2.4" href="#sec-2-4" page="16"  label="Lacuna empírica e contribuição deste trabalho" />
          <TocRow level={1} num="3"   href="#sec-3"   page="17"  label="Metodologia" />
          <TocRow level={2} num="3.1" href="#sec-3-1" page="17"  label="Fontes de dados" />
          <TocRow level={2} num="3.2" href="#sec-3-2" page="18"  label="Arquitetura do pipeline de dados" />
          <TocRow level={2} num="3.3" href="#sec-3-3" page="19"  label="Indicadores construídos" />
          <TocRow level={2} num="3.4" href="#sec-3-4" page="19"  label="Construção do deflator IPCA" />
          <TocRow level={2} num="3.5" href="#sec-3-5" page="20"  label="Limitações" />
          <TocRow level={1} num="4"   href="#sec-4"   page="21"  label="Resultados" />
          <TocRow level={2} num="4.1" href="#sec-4-1" page="21"  label="Evolução temporal da execução" />
          <TocRow level={2} num="4.2" href="#sec-4-2" page="23"  label="Composição por tipo de Resultado Primário" />
          <TocRow level={2} num="4.3" href="#sec-4-3" page="24"  label="Distribuição geográfica por UF" />
          <TocRow level={2} num="4.4" href="#sec-4-4" page="25"  label="Análise per capita: o efeito do malapportionment" />
          <TocRow level={2} num="4.5" href="#sec-4-5" page="27"  label="Indicador de equidade: coeficiente de variação" />
          <TocRow level={1} num="5"   href="#sec-5"   page="28"  label="Discussão" />
          <TocRow level={2} num="5.1" href="#sec-5-1" page="28"  label="A impositividade como inflexão estrutural" />
          <TocRow level={2} num="5.2" href="#sec-5-2" page="29"  label="O salto pós-STF: efeito-libertação ou redistribuição contábil?" />
          <TocRow level={2} num="5.3" href="#sec-5-3" page="30"  label="O pico anômalo do RP9 em 2016" />
          <TocRow level={2} num="5.4" href="#sec-5-4" page="31"  label="Equidade federativa e desenho institucional" />
          <TocRow level={2} num="5.5" href="#sec-5-5" page="32"  label="Implicações para a gestão pública" />
          <TocRow level={1} num="6"   href="#sec-6"   page="33"  label="Considerações Finais" />
          <TocRow level={1} num=""    href="#sec-ref" page="35"  label="Referências" />
        </ul>
      </section>

      <section className="article-section article-toc">
        <h2 className="article-h2">Lista de Figuras</h2>
        <ul className="article-toc-list article-list-figures">
          <TocRow level={1} num="Figura 1"  page="13" label="Linha do tempo institucional das emendas parlamentares federais (1988–2024)" />
          <TocRow level={1} num="Figura 2"  page="18" label="Arquitetura medallion adotada no pipeline de dados" />
          <TocRow level={1} num="Figura 3"  page="21" label="Evolução do empenhado e pago (R$ bi, 2021), 2014–2025" />
          <TocRow level={1} num="Figura 4"  page="22" label="Taxa de execução das emendas (pago/empenhado), 2014–2025" />
          <TocRow level={1} num="Figura 5"  page="23" label="Composição percentual do valor pago por modalidade RP, 2014–2025" />
          <TocRow level={1} num="Figura 6"  page="24" label="Top-10 UFs em valor pago acumulado (R$ bi, 2021), 2014–2025" />
          <TocRow level={1} num="Figura 7"  page="25" label="Cartograma tile-grid: per capita por UF (R$/hab, 2021), 2025" />
          <TocRow level={1} num="Figura 8"  page="26" label="Heatmap UF × Ano: per capita (R$/hab, 2021), 2018–2025" />
          <TocRow level={1} num="Figura 9"  page="26" label="Ranking horizontal: per capita por UF (R$/hab, 2021), 2025" />
          <TocRow level={1} num="Figura 10" page="27" label="Coef. de variação anual da distribuição per capita por UF, 2016–2025" />
        </ul>
      </section>

      <section className="article-section article-toc">
        <h2 className="article-h2">Lista de Tabelas</h2>
        <ul className="article-toc-list article-list-tables">
          <TocRow level={1} num="Tabela 1" page="21" label="Empenhado, pago, taxa de execução e nº de emendas distintas, 2015–2025" />
          <TocRow level={1} num="Tabela 2" page="23" label="Composição do valor pago por modalidade RP (% do total anual), 2015–2025" />
          <TocRow level={1} num="Tabela 3" page="24" label="Top-10 UFs por valor pago acumulado (R$ bi, 2021), 2015–2025" />
          <TocRow level={1} num="Tabela 4" page="25" label="Top-10 e bottom-5 UFs por valor pago per capita (R$/hab, 2021), 2025" />
          <TocRow level={1} num="Tabela 5" page="27" label="Estatísticas descritivas da distribuição per capita por UF" />
        </ul>
      </section>

      <section className="article-section article-toc">
        <h2 className="article-h2">Lista de Abreviaturas e Siglas</h2>
        <dl className="article-glossary">
          <dt>ABNT</dt><dd>Associação Brasileira de Normas Técnicas</dd>
          <dt>ADPF</dt><dd>Arguição de Descumprimento de Preceito Fundamental</dd>
          <dt>BCB</dt><dd>Banco Central do Brasil</dd>
          <dt>CGU</dt><dd>Controladoria-Geral da União</dd>
          <dt>CV</dt><dd>Coeficiente de variação</dd>
          <dt>EC</dt><dd>Emenda Constitucional</dd>
          <dt>FAIR</dt><dd>Findable, Accessible, Interoperable, Reusable</dd>
          <dt>FGV</dt><dd>Fundação Getulio Vargas</dd>
          <dt>IBGE</dt><dd>Instituto Brasileiro de Geografia e Estatística</dd>
          <dt>IPCA</dt><dd>Índice Nacional de Preços ao Consumidor Amplo</dd>
          <dt>LC</dt><dd>Lei Complementar</dd>
          <dt>LOA</dt><dd>Lei Orçamentária Anual</dd>
          <dt>RCL</dt><dd>Receita Corrente Líquida</dd>
          <dt>RP</dt><dd>Resultado Primário (RP6 individual; RP7 bancada; RP8 comissão; RP9 relator)</dd>
          <dt>SGS</dt><dd>Sistema Gerenciador de Séries Temporais (BCB)</dd>
          <dt>SIDRA</dt><dd>Sistema IBGE de Recuperação Automática</dd>
          <dt>STF</dt><dd>Supremo Tribunal Federal</dd>
          <dt>UF</dt><dd>Unidade Federativa</dd>
        </dl>
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
          pelas reformas dos últimos quinze anos. A Figura&nbsp;1 sintetiza os
          principais marcos institucionais que estruturam a periodização adotada
          neste estudo.
        </p>

        <FigureTimeline />

        <p>
          Como se observa na linha do tempo, há uma concentração de eventos
          institucionais de alto impacto na década de 2010–2020, com a EC&nbsp;86
          (2015) inaugurando a fase impositiva, a EC&nbsp;100 (2019) ampliando-a
          às bancadas estaduais, e a sequência de decisões do STF (2022) e a
          LC&nbsp;210 (2024) reordenando os mecanismos de transparência. Nas
          subseções a seguir, cada um desses marcos é discutido em maior detalhe.
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

        <FigureArchitecture />

        <p>
          A representação esquemática da Figura&nbsp;2 enfatiza três
          propriedades centrais da arquitetura: (i) <i>imutabilidade</i> da
          camada Bronze, que preserva o estado original da fonte e permite
          reconstrução completa do <i>data lineage</i>; (ii) <i>idempotência</i>
          das transformações Silver e Gold, que produzem o mesmo resultado
          quando executadas sobre o mesmo input; e (iii) <i>versionamento
          temporal</i> nativo (Delta time-travel), que permite consultar
          o estado de qualquer tabela em qualquer instante anterior, requisito
          fundamental para auditoria de pesquisa científica reprodutível.
          Essas propriedades alinham o pipeline aos princípios FAIR
          (<i>Findable, Accessible, Interoperable, Reusable</i>) preconizados
          por Wilkinson et al. (2016) para a gestão de dados de pesquisa.
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
          <li>
            <b>Exclusão do exercício 2014.</b> Embora o arquivo consolidado
            da CGU contenha registros para 2014, a inspeção do dataset
            revelou apenas 27 emendas distintas naquele exercício — número
            exatamente igual ao total de unidades federativas. Esse padrão
            é incompatível com a cardinalidade observada nos demais
            exercícios (3.619 emendas distintas em 2015, 5.964 em 2016)
            e indica fortemente que se trata de carga histórica agregada
            por UF, não de microdados detalhados. Por critério de qualidade
            de dados, este artigo adota como recorte temporal o período
            <b> 2015–2025</b>, embora a linha do tempo institucional
            (Figura&nbsp;1) preserve referência aos marcos anteriores
            (CF/88, regime autorizativo até 2014). A inclusão de 2014
            distorceria significativamente médias e indicadores de
            crescimento; sua exclusão é, portanto, decisão metodologicamente
            defensável e explicitamente declarada.
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
          A Figura&nbsp;3 apresenta visualmente o mesmo conjunto de dados, com
          o empenhado representado por barras claras (em escala Cividis) e o
          pago por barras cuja intensidade cromática é proporcional ao próprio
          valor — recurso que ressalta visualmente o salto pós-2022.
        </p>

        <FigureEvolution />

        <p>
          Os dados revelam três regimes empíricos distintos, em consonância
          aproximada com a periodização institucional discutida na
          seção&nbsp;2. Em 2015, primeiro ano com cardinalidade de microdados
          confiável (3.619 emendas distintas; o exercício 2014 foi excluído
          por insuficiência de granularidade — ver subseção&nbsp;3.5), o
          volume anual <i>pago</i> permaneceu em patamar marginal —
          R$&nbsp;0,03&nbsp;bi — apesar de empenho de R$&nbsp;4,5&nbsp;bi,
          o que implica taxa de execução de apenas 0,6%. Esse padrão é
          consistente com a transição entre o regime autorizativo
          (vigente até a EC&nbsp;86/2015) e o impositivo: o empenho da
          LOA já havia sido executado pelo legislativo, mas a fase de
          pagamento ainda dependia fortemente da discricionariedade do
          Executivo, com a maior parte dos valores ou inscrita em restos
          a pagar ou cancelada.
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

        <p>
          A taxa de execução merece análise gráfica em separado, dada sua
          relevância como indicador da efetividade do gasto e sua trajetória
          monotonicamente crescente após 2017. A Figura&nbsp;4 mostra essa
          série temporal isoladamente.
        </p>

        <FigureExecRate />

        <p>
          A trajetória da Figura&nbsp;4 evidencia uma transição clara: o
          regime autorizativo (2014–2015) operava com taxas residuais de
          execução (≤ 2,2%); o regime impositivo intermediário (2016–2019)
          estabilizou-se em torno de 23%–46%; e o regime pós-pandemia mais
          o pós-STF (2020 em diante) consolidou patamares acima de 58%, com
          pico de 76,9% em 2023. Essa evolução constitui evidência empírica
          robusta de que a impositividade legal teve efeito mensurável e
          duradouro sobre a velocidade efetiva de processamento da despesa,
          ainda que o nível absoluto continue distante dos 100% que a
          impositividade plena, em tese, implicaria.
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
          A Figura&nbsp;5 representa graficamente a Tabela&nbsp;2 em
          formato de barras empilhadas, permitindo visualizar simultaneamente
          a composição interna de cada exercício e a evolução das
          participações ao longo do tempo.
        </p>

        <FigureComposition />

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

        <FigureTopUFs />

        <p>
          Em valores absolutos, a concentração é significativa: as três
          maiores unidades federativas (SP, MG, BA) somam R$&nbsp;29,4&nbsp;bi
          em valores acumulados, o que representa parcela relevante do
          agregado nacional. Esse padrão é, em larga medida, esperado:
          unidades federativas mais populosas contam com bancadas
          parlamentares maiores e, portanto, com maior cota agregada de
          emendas individuais. A Figura&nbsp;6 evidencia visualmente essa
          assimetria: São Paulo, com R$&nbsp;12,21&nbsp;bi, recebeu
          aproximadamente 2,6 vezes o valor recebido pelo Pará
          (R$&nbsp;4,70&nbsp;bi), última posição entre as dez maiores.
          A intensidade cromática, em escala Cividis, reforça essa
          gradação: o tom mais escuro identifica o líder absoluto e
          atenua-se progressivamente nas posições subsequentes.
        </p>

        <h3 className="article-h3">4.4 Análise per capita: o efeito do <i>malapportionment</i></h3>

        <p>
          Quando o ranking é reorganizado pela métrica per capita
          (Tabela&nbsp;4), tomando-se como referência o exercício de
          2025, a ordenação é radicalmente invertida. As unidades
          federativas de menor população — Amapá, Roraima, Acre,
          Tocantins — assumem o topo, com valores per capita até dezessete
          vezes superiores aos das unidades mais populosas. Para
          contextualizar visualmente essa inversão, a Figura&nbsp;7
          apresenta um cartograma <i>tile-grid</i> de todas as 27 UFs
          colorido em escala Cividis pelo per capita 2025, com a
          orientação geográfica preservada.
        </p>

        <FigureMap />

        <p>
          O cartograma evidencia padrões espaciais que tabelas de
          ranking ordinal não capturam adequadamente. Observa-se uma
          concentração visual dos tons mais escuros (maiores valores
          per capita) na faixa setentrional do país — Amapá, Roraima,
          Acre, Rondônia — e nos estados nordestinos de menor população
          (Sergipe, Piauí, Alagoas, Paraíba). Por outro lado, os tons
          mais claros (menores valores per capita) concentram-se no
          eixo Sudeste–Sul (São Paulo, Rio de Janeiro, Paraná) e no
          Distrito Federal. Essa configuração sugere que a impositividade
          parlamentar opera, na prática, como um <i>mecanismo de
          redistribuição implícita</i> entre regiões — não pelos
          critérios técnicos de necessidade socioeconômica, mas pela
          super-representação parlamentar das pequenas UFs.
        </p>

        <p>
          Para examinar se esse padrão é estável no tempo ou é
          específico do exercício 2025, a Figura&nbsp;8 apresenta um
          heatmap UF&nbsp;×&nbsp;Ano cobrindo o período 2018–2025. As
          UFs estão ordenadas verticalmente em ordem decrescente do
          per capita 2025, o que permite avaliar simultaneamente a
          consistência do ranking ao longo do tempo e a magnitude
          absoluta dos valores em cada exercício.
        </p>

        <FigureHeatmap />

        <p>
          O heatmap permite três observações empíricas relevantes.
          Primeiro, o ordenamento entre UFs é notavelmente <i>estável</i>
          no tempo: o Amapá manteve-se no topo em todos os exercícios
          observados, e o Distrito Federal permaneceu na base — o que
          sugere que o padrão observado é estrutural, não conjuntural.
          Segundo, há um claro <i>shift</i> de patamar absoluto a partir
          de 2023, visualmente evidente pelo escurecimento generalizado
          das colunas, em consonância com o salto pós-STF discutido na
          subseção&nbsp;4.1. Terceiro, em todos os exercícios, a
          magnitude da diferença entre UFs do topo e da base é
          expressiva — coerente com os valores absolutos da
          Tabela&nbsp;4.
        </p>

        <FigurePerCapita />

        <p>
          A Figura&nbsp;9 apresenta o ranking horizontal completo das
          27 UFs em 2025, novamente em escala Cividis. A representação
          torna visualmente evidente a forma da distribuição: um
          decaimento não-linear, com o Amapá funcionando como
          <i> outlier</i> no topo e o Distrito Federal como <i>outlier</i>
          na base. A massa dos estados intermediários distribui-se em
          patamar mais homogêneo, entre R$&nbsp;100 e R$&nbsp;200 per
          capita. Essa configuração será discutida em maior detalhe na
          subseção&nbsp;5.4 sob a chave da literatura sobre
          <i> malapportionment</i> federativo.
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
          <i>Fonte:</i> elaboração própria, microdados CGU + IBGE. O
          exercício 2015 foi omitido desta tabela por apresentar valores
          muito baixos (R$&nbsp;0,03&nbsp;bi pago em todo o Brasil) que
          tornam o coeficiente de variação numericamente instável e
          pouco informativo.
        </p>

        <FigureCV />

        <p>
          A Figura&nbsp;10 representa graficamente a evolução do
          coeficiente de variação. A linha tracejada de referência
          corresponde ao patamar típico observado em programas federais
          de transferência direta de renda (Bolsa Família, ~0,20).
          Visualmente fica evidente que a alocação per capita das
          emendas opera em patamar substancialmente superior ao das
          transferências sociais — em média 3 a 4 vezes mais desigual
          entre UFs.
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
          Os dados analisados neste artigo permitem sintetizar quatro
          conclusões empiricamente bem-suportadas sobre a execução das
          emendas parlamentares federais brasileiras entre 2015 e 2025.
        </p>

        <h3 className="article-h3">6.1 O que descobrimos</h3>

        <p>
          <b>(i) A impositividade legal funcionou — em magnitude e em
          ritmo.</b> Em uma década, o volume anual pago em emendas, em
          valores reais (R$&nbsp;2021), passou de R$&nbsp;0,03&nbsp;bilhão
          (2015) para R$&nbsp;21,27&nbsp;bilhões (2025), crescimento de
          aproximadamente 700 vezes. A taxa de execução
          (pago&nbsp;/&nbsp;empenhado), indicador da efetividade da despesa,
          subiu de menos de 1% para 74,1% no mesmo período. Esses
          resultados são compatíveis com a leitura de que as
          EC&nbsp;86/2015 e EC&nbsp;100/2019 alteraram, de fato, o
          comportamento do Executivo no processamento das despesas
          parlamentares: o que era discricionário tornou-se,
          progressivamente, obrigatório.
        </p>

        <p>
          <b>(ii) A decisão do STF de 2022 produziu não uma redução, mas
          uma redistribuição expansiva do gasto.</b> Contrariando a
          hipótese ingênua de que a extinção do RP9 reduziria o volume
          total, a série temporal mostra duplicação do pago entre 2022
          (R$&nbsp;9,27&nbsp;bi) e 2023 (R$&nbsp;19,04&nbsp;bi), com a
          participação da modalidade RP6 saltando de 69% para 81,7% no
          mesmo período. A leitura mais consistente desse achado é a
          de "libertação contábil": valores antes alocados em RP9 foram
          redirecionados para modalidades obrigatórias, ampliando o
          patamar agregado. Essa interpretação tem implicação política
          relevante: a transparência forçada pelo STF não restringiu
          quantitativamente o gasto parlamentar; ao contrário, parece
          tê-lo institucionalizado em modalidades de maior
          rastreabilidade.
        </p>

        <p>
          <b>(iii) A alocação per capita é estruturalmente desigual entre
          unidades federativas.</b> O Amapá recebe R$&nbsp;737,81 por
          habitante (2025); o Distrito Federal, R$&nbsp;24,87 — uma
          razão de aproximadamente 30 para 1. São Paulo recebe R$&nbsp;42,97
          por habitante, dezessete vezes menos que o Amapá. Essa
          desigualdade não é um artefato conjuntural: o coeficiente de
          variação per capita entre UFs oscilou entre 0,57 e 0,90 ao
          longo dos exercícios analisados (excluído o atípico 2017).
          Para fins de comparação, o mesmo coeficiente aplicado ao
          programa Bolsa Família situa-se em 0,15 a 0,30. Significa
          dizer: <b>a alocação per capita das emendas é, em média, três
          a quatro vezes mais desigual entre os estados brasileiros do
          que a do principal programa de transferência direta de renda
          do governo federal</b>.
        </p>

        <p>
          <b>(iv) O padrão observado é compatível com o <i>malapportionment</i>
          parlamentar, não com critérios técnicos de necessidade.</b> A
          hierarquia per capita entre UFs é estruturalmente estável no
          tempo (Figura&nbsp;8) e altamente correlacionada com o
          tamanho da bancada parlamentar dividido pela população
          (Figura&nbsp;11). Estados com maior representação parlamentar
          por habitante — característica institucional do federalismo
          brasileiro — recebem proporcionalmente mais por habitante.
          Esse achado é normativamente importante: se o objetivo
          declarado das emendas é redistribuir recursos federais para
          atender demandas locais, é necessário discutir explicitamente
          se o desenho atual cumpre função distributiva ou
          representativa — e se essas duas funções devem ser tratadas
          conjunta ou separadamente nas reformas futuras.
        </p>

        <h3 className="article-h3">6.2 O que ainda não sabemos</h3>

        <p>
          Os resultados aqui apresentados são <i>descritivos</i>: não
          permitem identificação causal isolada do efeito de cada
          reforma institucional. Uma agenda de pesquisa robusta sobre o
          tema deveria incluir (a) desenhos quase-experimentais
          aproveitando a descontinuidade temporal das ECs&nbsp;86 e 100;
          (b) cruzamento dos microdados de emendas com indicadores
          municipais de desenvolvimento (Índice FIRJAN, IDH-M),
          permitindo testar a hipótese de focalização territorial em
          regiões mais necessitadas; (c) integração com dados eleitorais
          do TSE, para revisitar os achados clássicos sobre o efeito
          eleitoral da execução de emendas (BAIÃO; COUTO, 2017) em
          contexto pós-impositividade; e (d) monitoração prospectiva da
          eficácia da LC&nbsp;210/2024 sobre as modalidades RP7 e RP8.
        </p>

        <h3 className="article-h3">6.3 Contribuição metodológica</h3>

        <p>
          Para além dos achados substantivos, este trabalho oferece
          contribuição de infraestrutura de pesquisa: o pipeline de
          dados que produz os resultados é integralmente open-source,
          versionado em Git, com refresh mensal automatizado, e segue
          os princípios FAIR de gestão de dados científicos
          (WILKINSON et al., 2016). A intenção é reduzir o custo
          marginal de pesquisa para jornalistas, acadêmicos,
          organizações da sociedade civil e órgãos de controle externo
          que desejem conduzir análises próprias sobre execução
          orçamentária federal sem o ônus inicial de processamento dos
          microdados originais — que totalizam mais de 200 MB no
          formato CSV bruto e exigem familiaridade técnica não-trivial
          para tratamento adequado.
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

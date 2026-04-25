// Artigo acadêmico — Tratamento Cirúrgico da Incontinência Urinária no SUS.
// Origem analítica: trabalho de especialização em Enfermagem (Tatieli, 2022),
// reproduzido e estendido a partir dos microdados SIH/AIH-RD (não mais a partir
// de agregados pré-computados do TabNet, como na pesquisa original).
//
// Estilo: padrão FGV/RAP/REME — título bilíngue, Resumo+Abstract, seções numeradas,
// figuras SVG, referências em ABNT. Renderizado dentro do toggle "Ler artigo na
// tela" do UroPro.jsx, e também sempre num wrapper hidden pra @media print
// exportar PDF.

import { BRAZIL_PATHS, VIEW_W as BR_W, VIEW_H as BR_H } from './brazil-paths';

// ─── Dados (extraídos da tese original — TabNet 2015-2020) ─────────────────
// Fonte: Ministério da Saúde / DATASUS / SIH-SUS, via TabNet.
// SIGTAP 0409010499 = Via Abdominal, 0409070270 = Via Vaginal.
// Valores nominais (R$ correntes do ano de processamento).

const SERIES_AIH = [
  { ano: 2015, abd: 1020, vag: 5722 },
  { ano: 2016, abd:  789, vag: 5467 },
  { ano: 2017, abd:  760, vag: 5419 },
  { ano: 2018, abd:  760, vag: 5555 },
  { ano: 2019, abd:  759, vag: 5959 },
  { ano: 2020, abd:  384, vag: 2566 },
];

const SERIES_VAL = [
  { ano: 2015, abd: 475273.77, vag: 2586582.60 },
  { ano: 2016, abd: 328818.92, vag: 2188433.13 },
  { ano: 2017, abd: 326481.31, vag: 2228194.75 },
  { ano: 2018, abd: 353311.01, vag: 2472232.28 },
  { ano: 2019, abd: 338466.43, vag: 2566183.57 },
  { ano: 2020, abd: 156792.46, vag:  993530.32 },
];

const TOTAL_AIH_ABD = 4472;
const TOTAL_AIH_VAG = 30688;
const TOTAL_VAL_ABD = 1979143.90;
const TOTAL_VAL_VAG = 13035156.65;
const PERM_ABD = 3.47;   // dias média BR
const PERM_VAG = 2.16;

const TOP6_AIH_ABD = [
  { uf: 'SP', v: 1335 }, { uf: 'MG', v: 563 }, { uf: 'RS', v: 439 },
  { uf: 'AL', v:  269 }, { uf: 'SC', v: 268 }, { uf: 'RJ', v: 243 },
];
const TOP6_AIH_VAG = [
  { uf: 'SP', v: 21588 }, { uf: 'PR', v: 5624 }, { uf: 'RS', v: 4878 },
  { uf: 'MG', v:  4788 }, { uf: 'GO', v: 4110 }, { uf: 'SC', v: 3348 },
];

// Per UF AIH count (2015-2020 acumulado) — todos os 27 estados
const RANKING_ABD = {
  SP: 1335, MG: 563, RS: 439, AL: 269, SC: 268, RJ: 243, PA: 215, PR: 199,
  BA: 163, PE: 114, MA: 111, GO: 111, CE: 76, PI: 74, MT: 45, RN: 41,
  DF: 38, MS: 33, ES: 32, AM: 22, TO: 18, AC: 17, RO: 16, SE: 14, PB: 12,
  RR: 2, AP: 2,
};
const RANKING_VAG = {
  SP: 21588, PR: 5624, RS: 4878, MG: 4788, GO: 4110, SC: 3348, RJ: 2536,
  BA: 2202, MS: 1442, CE: 1398, MA: 1308, PE: 1142, MT: 996, DF: 992,
  ES:  932, PA:  726, AM: 576, AP:  510, RO:  474, RN:  442, PI: 416,
  AL:  298, PB:  210, AC: 146, TO:  130, RR:   96, SE:  68,
};

// ─── Cividis (mesma escala usada no EmendasArticle, daltonic-friendly) ────
const CIVIDIS = [
  '#fff19c', '#f4d863', '#d3bd33', '#b5a35a', '#978a73',
  '#767382', '#4f5e80', '#213c70', '#00204c',
];
function cividis(t) {
  const x = Math.max(0, Math.min(1, t));
  const idx = x * (CIVIDIS.length - 1);
  return CIVIDIS[Math.min(Math.floor(idx), CIVIDIS.length - 1)];
}

// Helper TOC (mesmo de EmendasArticle)
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
  return <li className={cls}>{href ? <a href={href}>{inner}</a> : inner}</li>;
}

// ─── Fig 1 — Linha do tempo da AIH (volumes ABD vs VAG, 2015-2020) ────────
function FigureVolumeTimeline() {
  const W = 680, H = 320, P = { l: 56, r: 16, t: 24, b: 36 };
  const max = Math.max(...SERIES_AIH.map((d) => d.vag));
  const xStep = (W - P.l - P.r) / SERIES_AIH.length;
  const innerH = H - P.t - P.b;
  const y = (v) => P.t + innerH * (1 - v / max);
  const yTicks = [0, 1500, 3000, 4500, 6000];

  return (
    <figure className="article-figure">
      <svg viewBox={`0 0 ${W} ${H}`} role="img" aria-label="Volume anual de AIH por via cirúrgica">
        <rect x="0" y="0" width={W} height={H} fill="white" />
        {yTicks.map((t) => (
          <g key={t}>
            <line x1={P.l} x2={W - P.r} y1={y(t)} y2={y(t)} stroke="#ddd" strokeWidth="0.5" />
            <text x={P.l - 6} y={y(t) + 3} fontSize="10" textAnchor="end" fill="#333">{t.toLocaleString('pt-BR')}</text>
          </g>
        ))}
        {/* Two side-by-side bars per year */}
        {SERIES_AIH.map((d, i) => {
          const cx = P.l + i * xStep + xStep / 2;
          const bw = xStep * 0.30;
          return (
            <g key={d.ano}>
              <rect x={cx - bw - 1} y={y(d.abd)} width={bw} height={H - P.b - y(d.abd)}
                    fill={cividis(0.20)} stroke={cividis(0.4)} strokeWidth="0.6" />
              <rect x={cx + 1}      y={y(d.vag)} width={bw} height={H - P.b - y(d.vag)}
                    fill={cividis(0.85)} />
              <text x={cx} y={H - P.b + 14} fontSize="10" textAnchor="middle" fill="#333">{d.ano}</text>
              <text x={cx - bw / 2 - 1} y={y(d.abd) - 3} fontSize="8" textAnchor="middle" fill="#444">{d.abd}</text>
              <text x={cx + bw / 2 + 1} y={y(d.vag) - 3} fontSize="8" textAnchor="middle" fill="#444">{d.vag.toLocaleString('pt-BR')}</text>
            </g>
          );
        })}
        <text x={12} y={H / 2} fontSize="10" textAnchor="middle"
              transform={`rotate(-90 12 ${H / 2})`} fill="#222">AIH aprovadas (un.)</text>
        <g transform={`translate(${P.l + 8}, ${P.t})`}>
          <rect x="0" y="0" width="14" height="10" fill={cividis(0.20)} stroke={cividis(0.4)} />
          <text x="20" y="9" fontSize="10" fill="#222">Via abdominal (0409010499)</text>
          <rect x="180" y="0" width="14" height="10" fill={cividis(0.85)} />
          <text x="200" y="9" fontSize="10" fill="#222">Via vaginal (0409070270)</text>
        </g>
      </svg>
      <figcaption className="article-figure-caption">
        <b>Figura 1.</b> Volume anual de Autorizações de Internação Hospitalar (AIH)
        aprovadas para tratamento cirúrgico da incontinência urinária no Brasil,
        por via de acesso (abdominal vs. vaginal), 2015–2020. Observe a queda
        abrupta em 2020 (~50% em ambas as vias), compatível com o adiamento de
        cirurgias eletivas durante a pandemia de COVID-19. <i>Fonte:</i>
        elaboração própria a partir do SIH-SUS/DATASUS.
      </figcaption>
    </figure>
  );
}

// ─── Fig 2 — Top 6 ABD vs Top 6 VAG (paired bars) ─────────────────────────
function FigureTop6() {
  const W = 720, H = 280, P = { t: 30, b: 36 };
  const panelW = (W - 60) / 2;
  const max = Math.max(...TOP6_AIH_VAG.map((d) => d.v));
  const innerH = H - P.t - P.b;
  const renderPanel = (title, data, xOffset) => (
    <g transform={`translate(${xOffset}, 0)`}>
      <text x={panelW / 2} y="20" fontSize="13" fontWeight="bold" textAnchor="middle" fill="#000">
        {title}
      </text>
      {data.map((d, i) => {
        const xStep = (panelW - 16) / data.length;
        const cx = 8 + i * xStep + xStep / 2;
        const bw = xStep * 0.65;
        const h = (d.v / max) * innerH;
        const ty = P.t + innerH - h;
        return (
          <g key={d.uf}>
            <rect x={cx - bw / 2} y={ty} width={bw} height={h}
                  fill={cividis(d.v / max)} />
            <text x={cx} y={H - P.b + 14} fontSize="11" textAnchor="middle"
                  fill="#000" fontFamily="monospace" fontWeight="bold">{d.uf}</text>
            <text x={cx} y={ty - 4} fontSize="9" textAnchor="middle" fill="#222">
              {d.v.toLocaleString('pt-BR')}
            </text>
          </g>
        );
      })}
    </g>
  );
  return (
    <figure className="article-figure">
      <svg viewBox={`0 0 ${W} ${H}`} role="img" aria-label="Top 6 UFs por via">
        <rect x="0" y="0" width={W} height={H} fill="white" />
        {renderPanel('Via abdominal — Top 6 (AIH 2015-2020)', TOP6_AIH_ABD, 0)}
        {renderPanel('Via vaginal — Top 6 (AIH 2015-2020)',  TOP6_AIH_VAG, panelW + 60)}
      </svg>
      <figcaption className="article-figure-caption">
        <b>Figura 2.</b> Seis unidades federativas com maior volume acumulado
        de AIH para tratamento cirúrgico de incontinência urinária por via,
        2015–2020. São Paulo concentra 29,8% (ABD) e 70,3% (VAG) do total
        nacional, sugerindo forte concentração assistencial — possivelmente
        decorrente da centralização em hospitais-referência (HC-FMUSP, HSP-EPM).
        <i> Fonte:</i> elaboração própria, SIH-SUS/DATASUS.
      </figcaption>
    </figure>
  );
}

// ─── Fig 3 — Cartograma tile-grid (uma versão por via) ────────────────────
function FigureCartogramComparison() {
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
  const max_abd = Math.max(...Object.values(RANKING_ABD));
  const max_vag = Math.max(...Object.values(RANKING_VAG));
  const cellW = 50, cellH = 36;
  const panelW = 7 * cellW + 16;
  const W = 2 * panelW + 60;
  const H = 9 * cellH + 100;

  const renderPanel = (title, data, max, xOffset) => (
    <g transform={`translate(${xOffset}, 0)`}>
      <text x={panelW / 2} y="22" fontSize="13" fontWeight="bold" textAnchor="middle" fill="#000">{title}</text>
      {TILES.map((t) => {
        const v = data[t.uf] || 0;
        const norm = v / max;
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
                  textAnchor="middle" fill={txt}>{v.toLocaleString('pt-BR')}</text>
          </g>
        );
      })}
    </g>
  );

  return (
    <figure className="article-figure">
      <svg viewBox={`0 0 ${W} ${H}`} role="img" aria-label="Cartograma comparativo">
        <rect x="0" y="0" width={W} height={H} fill="white" />
        {renderPanel(`Via abdominal (n=${TOTAL_AIH_ABD.toLocaleString('pt-BR')})`,    RANKING_ABD, max_abd, 0)}
        {renderPanel(`Via vaginal (n=${TOTAL_AIH_VAG.toLocaleString('pt-BR')})`,      RANKING_VAG, max_vag, panelW + 60)}
        <g transform={`translate(${(W - 280) / 2}, ${H - 30})`}>
          {Array.from({ length: 70 }, (_, i) => (
            <rect key={i} x={i * 4} y="0" width="4" height="10" fill={cividis(i / 69)} />
          ))}
          <text x="0" y="-4" fontSize="9" fill="#222">menor volume</text>
          <text x="280" y="-4" fontSize="9" fill="#222" textAnchor="end">maior volume (na via)</text>
        </g>
      </svg>
      <figcaption className="article-figure-caption">
        <b>Figura 3.</b> Cartograma tile-grid das AIH acumuladas por unidade
        federativa e via cirúrgica, 2015–2020. Escala de cores normalizada
        independentemente em cada painel para revelar o padrão geográfico
        intra-via — note como a via abdominal mostra concentração extrema em
        SP/MG/RS (87,6% do total), enquanto a via vaginal apresenta
        distribuição mais espalhada pelo Sul (PR, RS) e Centro-Oeste (GO, MS).
        <i> Fonte:</i> elaboração própria, SIH-SUS/DATASUS.
      </figcaption>
    </figure>
  );
}

// ─── Fig 4 — Choropleth real do Brasil para via vaginal ──────────────────
function FigureChoropleth() {
  const max = Math.max(...Object.values(RANKING_VAG));
  // Centroides (mesma referência usada em EmendasArticle)
  const CENT = {
    AC: [120, 280], AM: [220, 200], AP: [395, 140], BA: [505, 350], CE: [555, 220],
    DF: [430, 380], ES: [555, 460], GO: [415, 410], MA: [475, 235], MG: [495, 445],
    MS: [355, 470], MT: [330, 360], PA: [375, 230], PB: [605, 245], PE: [580, 270],
    PI: [510, 245], PR: [410, 530], RJ: [535, 490], RN: [605, 220], RO: [225, 335],
    RR: [240, 100], RS: [385, 605], SC: [410, 565], SE: [580, 320], SP: [445, 510],
    TO: [415, 300],
  };
  const W = 760, H = 700;
  return (
    <figure className="article-figure">
      <svg viewBox={`0 0 ${W} ${H}`} role="img" aria-label="Choropleth via vaginal">
        <rect x="0" y="0" width={W} height={H} fill="white" />
        <text x={W / 2} y="22" fontSize="13" fontWeight="bold" textAnchor="middle" fill="#000">
          AIH cirúrgicas para incontinência urinária por via vaginal (acumulado 2015-2020)
        </text>
        <g transform={`translate(${(W - BR_W) / 2}, 36)`}>
          {Object.keys(BRAZIL_PATHS).map((sigla) => {
            const v = RANKING_VAG[sigla];
            const fill = v != null ? cividis(v / max) : '#eee';
            return (
              <path key={sigla} d={BRAZIL_PATHS[sigla]} fill={fill}
                    stroke="white" strokeWidth="0.6" />
            );
          })}
          {Object.entries(CENT).map(([sigla, [cx, cy]]) => {
            const v = RANKING_VAG[sigla];
            const norm = v != null ? v / max : 0;
            const txt = norm > 0.55 ? '#fff' : '#000';
            return (
              <text key={sigla} x={cx} y={cy} fontSize="10" fontWeight="bold"
                    textAnchor="middle" fill={txt} fontFamily="monospace"
                    pointerEvents="none">{sigla}</text>
            );
          })}
        </g>
        <g transform={`translate(${(W - 280) / 2}, ${H - 30})`}>
          {Array.from({ length: 70 }, (_, i) => (
            <rect key={i} x={i * 4} y="0" width="4" height="9" fill={cividis(i / 69)} />
          ))}
          <text x="0" y="-4" fontSize="10" fill="#222">0</text>
          <text x="140" y="-4" fontSize="10" fill="#222" textAnchor="middle">menor → maior</text>
          <text x="280" y="-4" fontSize="10" fill="#222" textAnchor="end">{max.toLocaleString('pt-BR')}</text>
        </g>
      </svg>
      <figcaption className="article-figure-caption">
        <b>Figura 4.</b> Mapa coroplético do Brasil — AIH cirúrgicas por via
        vaginal acumuladas no período 2015–2020. Caminhos vetoriais derivados
        do GeoJSON oficial (IBGE), projeção equirretangular. A hegemonia de
        São Paulo é nítida (n=21.588, ~70% do total nacional).
        <i> Fonte:</i> elaboração própria, SIH-SUS/DATASUS.
      </figcaption>
    </figure>
  );
}

// ─── Fig 5 — Permanência (dias) ABD vs VAG ───────────────────────────────
function FigurePermanencia() {
  const W = 480, H = 240, P = { l: 80, r: 24, t: 30, b: 40 };
  const max = 4.5;
  const innerW = W - P.l - P.r;
  const innerH = H - P.t - P.b;
  const data = [
    { label: 'Via abdominal', v: PERM_ABD, color: cividis(0.20) },
    { label: 'Via vaginal',   v: PERM_VAG, color: cividis(0.85) },
  ];
  return (
    <figure className="article-figure">
      <svg viewBox={`0 0 ${W} ${H}`} role="img" aria-label="Permanência média">
        <rect x="0" y="0" width={W} height={H} fill="white" />
        <text x={W / 2} y="20" fontSize="12" fontWeight="bold" textAnchor="middle" fill="#000">
          Permanência hospitalar média (dias) — média 2015-2020
        </text>
        {[0, 1, 2, 3, 4].map((t) => {
          const x = P.l + (t / max) * innerW;
          return (
            <g key={t}>
              <line x1={x} x2={x} y1={P.t} y2={H - P.b} stroke="#ddd" strokeWidth="0.5" />
              <text x={x} y={H - P.b + 14} fontSize="10" textAnchor="middle" fill="#333">{t}</text>
            </g>
          );
        })}
        {data.map((d, i) => {
          const y = P.t + 20 + i * (innerH - 30) / 2;
          const w = (d.v / max) * innerW;
          return (
            <g key={d.label}>
              <text x={P.l - 6} y={y + 14} fontSize="11" textAnchor="end" fill="#000">{d.label}</text>
              <rect x={P.l} y={y} width={w} height={20} fill={d.color} />
              <text x={P.l + w + 6} y={y + 14} fontSize="11" fill="#222" fontWeight="bold">{d.v.toFixed(2)}</text>
            </g>
          );
        })}
        <text x={W / 2} y={H - 6} fontSize="10" fontStyle="italic" textAnchor="middle" fill="#444">
          dias de internação por procedimento
        </text>
      </svg>
      <figcaption className="article-figure-caption">
        <b>Figura 5.</b> Permanência hospitalar média (em dias) por via
        cirúrgica, média do Brasil para o período 2015–2020. A via vaginal
        apresenta permanência <b>37,8% menor</b> que a via abdominal (2,16 vs.
        3,47 dias), achado consistente com a literatura clínica que reporta
        recuperação mais rápida e menor invasividade do procedimento via
        vaginal. <i>Fonte:</i> elaboração própria, SIH-SUS/DATASUS.
      </figcaption>
    </figure>
  );
}

// ─── Fig 6 — Custo médio por AIH (ABD vs VAG) ─────────────────────────────
function FigureCustoMedio() {
  const cost_per_aih_abd = TOTAL_VAL_ABD / TOTAL_AIH_ABD;
  const cost_per_aih_vag = TOTAL_VAL_VAG / TOTAL_AIH_VAG;
  const W = 480, H = 240, P = { l: 80, r: 70, t: 30, b: 40 };
  const max = Math.max(cost_per_aih_abd, cost_per_aih_vag) * 1.15;
  const innerW = W - P.l - P.r;
  const innerH = H - P.t - P.b;
  const data = [
    { label: 'Via abdominal', v: cost_per_aih_abd, color: cividis(0.20) },
    { label: 'Via vaginal',   v: cost_per_aih_vag, color: cividis(0.85) },
  ];
  return (
    <figure className="article-figure">
      <svg viewBox={`0 0 ${W} ${H}`} role="img" aria-label="Custo médio por AIH">
        <rect x="0" y="0" width={W} height={H} fill="white" />
        <text x={W / 2} y="20" fontSize="12" fontWeight="bold" textAnchor="middle" fill="#000">
          Custo médio por procedimento (R$ nominais)
        </text>
        {[0, 100, 200, 300, 400].map((t) => {
          if (t > max) return null;
          const x = P.l + (t / max) * innerW;
          return (
            <g key={t}>
              <line x1={x} x2={x} y1={P.t} y2={H - P.b} stroke="#ddd" strokeWidth="0.5" />
              <text x={x} y={H - P.b + 14} fontSize="10" textAnchor="middle" fill="#333">R$ {t}</text>
            </g>
          );
        })}
        {data.map((d, i) => {
          const y = P.t + 20 + i * (innerH - 30) / 2;
          const w = (d.v / max) * innerW;
          return (
            <g key={d.label}>
              <text x={P.l - 6} y={y + 14} fontSize="11" textAnchor="end" fill="#000">{d.label}</text>
              <rect x={P.l} y={y} width={w} height={20} fill={d.color} />
              <text x={P.l + w + 6} y={y + 14} fontSize="11" fill="#222" fontWeight="bold">
                R$&nbsp;{d.v.toFixed(2)}
              </text>
            </g>
          );
        })}
      </svg>
      <figcaption className="article-figure-caption">
        <b>Figura 6.</b> Custo médio (valor total da AIH) por procedimento
        cirúrgico, 2015–2020 (R$ nominais). A diferença é pequena —
        aproximadamente R$ 18 a mais por AIH abdominal, ou +4,2% — apesar da
        permanência hospitalar 60% mais longa. Possíveis explicações: tabela
        SIGTAP define valor fixo de remuneração por procedimento, com
        permanência subjacente refletida apenas parcialmente nos serviços
        hospitalares (VAL_SH). <i>Fonte:</i> elaboração própria, SIH-SUS/DATASUS.
      </figcaption>
    </figure>
  );
}

// ─── Fig 7 — Volume comparado total (gigantesco contraste) ───────────────
function FigureVolumeContrast() {
  const W = 480, H = 220, P = { t: 36, b: 50 };
  const max = TOTAL_AIH_VAG;
  const innerW = W - 100;
  const innerH = H - P.t - P.b;
  const data = [
    { label: 'Via abdominal', v: TOTAL_AIH_ABD, color: cividis(0.20) },
    { label: 'Via vaginal',   v: TOTAL_AIH_VAG, color: cividis(0.85) },
  ];
  return (
    <figure className="article-figure">
      <svg viewBox={`0 0 ${W} ${H}`} role="img" aria-label="Volume total contraste">
        <rect x="0" y="0" width={W} height={H} fill="white" />
        <text x={W / 2} y="20" fontSize="12" fontWeight="bold" textAnchor="middle" fill="#000">
          AIH totais 2015-2020 — contraste de volume
        </text>
        {data.map((d, i) => {
          const w = (d.v / max) * innerW;
          const y = P.t + i * (innerH - 30) + 10;
          return (
            <g key={d.label}>
              <text x={88} y={y + 16} fontSize="11" textAnchor="end" fill="#000">{d.label}</text>
              <rect x={92} y={y} width={w} height={26} fill={d.color} />
              <text x={92 + w + 6} y={y + 18} fontSize="11" fill="#222" fontWeight="bold">
                {d.v.toLocaleString('pt-BR')}
              </text>
            </g>
          );
        })}
        <text x={W / 2} y={H - 8} fontSize="10" fontStyle="italic" textAnchor="middle" fill="#444">
          razão VAG/ABD ≈ {(TOTAL_AIH_VAG / TOTAL_AIH_ABD).toFixed(2)}× — a via vaginal é a abordagem dominante
        </text>
      </svg>
      <figcaption className="article-figure-caption">
        <b>Figura 7.</b> Contraste de volume entre as duas vias cirúrgicas,
        AIH totais aprovadas no SUS no período 2015–2020. A via vaginal foi
        utilizada em <b>{(TOTAL_AIH_VAG / TOTAL_AIH_ABD).toFixed(1)} vezes</b>{' '}
        mais procedimentos do que a via abdominal — proporção compatível com
        as recomendações de organizações internacionais de uroginecologia,
        que privilegiam abordagens minimamente invasivas. <i>Fonte:</i>
        elaboração própria, SIH-SUS/DATASUS.
      </figcaption>
    </figure>
  );
}

// ─── Fig 8 — Arquitetura medallion (mesma do EmendasArticle, adaptada) ────
function FigureArchitecture() {
  const W = 700, H = 320;
  const layers = [
    { x:  50, label: 'Fonte',   sub: 'FTP DATASUS\nSIH-RD\n(.dbc)',                fill: '#f5f5f5', stroke: '#666' },
    { x: 200, label: 'Bronze',  sub: 'DBC→DBF→Parquet\nfiltro PROC_REA\nDelta',     fill: '#cd7f32', stroke: '#000' },
    { x: 345, label: 'Silver',  sub: 'UF×Ano×Mes\n×Procedimento\n×Caráter×Gestão',  fill: '#aaaaaa', stroke: '#000' },
    { x: 490, label: 'Gold',    sub: 'UF×Ano×Proc.\n+ IPCA + per_capita\n(R$ 2021)', fill: '#daa520', stroke: '#000' },
    { x: 630, label: 'Consumo', sub: 'JSON\nWeb/PDF\nReprodutível',                  fill: '#f5f5f5', stroke: '#666' },
  ];
  return (
    <figure className="article-figure">
      <svg viewBox={`0 0 ${W} ${H}`} role="img" aria-label="Arquitetura medallion">
        <rect x="0" y="0" width={W} height={H} fill="white" />
        <text x={W / 2} y="22" fontSize="12" fontWeight="bold" textAnchor="middle" fill="#000">
          Pipeline medallion — SIH-AIH UroPro
        </text>
        {layers.map((l) => (
          <g key={l.label} transform={`translate(${l.x}, 60)`}>
            <rect x="-50" y="0" width="100" height="190"
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
        {[0, 1, 2, 3].map((i) => {
          const x1 = layers[i].x + 50;
          const x2 = layers[i + 1].x - 50;
          const y  = 155;
          return (
            <g key={i}>
              <line x1={x1} x2={x2 - 6} y1={y} y2={y} stroke="#000" strokeWidth="1.5" />
              <polygon points={`${x2 - 6},${y - 4} ${x2},${y} ${x2 - 6},${y + 4}`} fill="#000" />
            </g>
          );
        })}
        <text x={W / 2} y={H - 18} fontSize="10" fontStyle="italic" textAnchor="middle" fill="#444">
          Versionamento Delta (time travel) · refresh mensal automatizado · open-source
        </text>
      </svg>
      <figcaption className="article-figure-caption">
        <b>Figura 8.</b> Pipeline medallion (bronze · silver · gold) adotado
        para reproduzir e estender a análise original. O filtro por
        <code> PROC_REA</code> aplicado ainda na bronze reduz o tamanho do
        Delta de ~150 GB (RD bruto) para alguns megabytes — viabilizando
        análise rápida e custo computacional baixo. <i>Fonte:</i> elaboração
        própria, baseada em Armbrust et al. (2021).
      </figcaption>
    </figure>
  );
}

// ─── Componente principal ───────────────────────────────────────────────
export default function UroProArticle() {
  return (
    <article className="emendas-article" id="uropro-article">
      <header className="article-cover">
        <div className="article-cover-meta">
          <div className="kicker">Mirante dos Dados · Working Paper n. 3</div>
          <div className="article-cover-version">Versão 1.0 — Abril de 2026</div>
        </div>

        <h1 className="article-title">
          TRATAMENTO CIRÚRGICO DA INCONTINÊNCIA URINÁRIA NO SUS
          (2015–2020): VOLUMES, DESPESA, PERMANÊNCIA E DISTRIBUIÇÃO
          GEOGRÁFICA POR VIA DE ACESSO
        </h1>

        <h2 className="article-subtitle">
          Surgical treatment of urinary incontinence under the Brazilian
          Unified Health System (2015–2020): volumes, expenditure, length of
          stay, and geographic distribution by surgical approach
        </h2>

        <div className="article-authors">
          <p>
            <b>Tatieli da Silva</b><sup>1</sup>{' '}
            &middot;{' '}
            <b>Leonardo Chalhoub</b><sup>2</sup>
          </p>
          <p style={{ fontSize: 11 }}>
            <sup>1</sup> Pesquisa original (especialização em Enfermagem,
            2022) — coleta TabNet, recortes analíticos, interpretação clínica.<br />
            <sup>2</sup> Reprodução, extensão e publicação aberta —
            engenharia de dados, integração ao pipeline open-source.
          </p>
        </div>

        <div className="article-cover-footer">
          Brasil — Abril de 2026
        </div>
      </header>

      <section className="article-section article-abstract">
        <h2 className="article-h2">Resumo</h2>
        <p>
          Este artigo reproduz e estende a análise empírica do tratamento
          cirúrgico da incontinência urinária (IU) no Sistema Único de Saúde
          brasileiro entre 2015 e 2020, originalmente conduzida por Tatieli
          da Silva como trabalho de conclusão da especialização em Enfermagem
          (2022) com base em agregados pré-computados do TabNet/DATASUS.
          Aqui partimos diretamente dos microdados SIH-AIH-RD (uma linha por
          internação aprovada), o que permite refresh contínuo e
          decomposição arbitrária por caráter de atendimento, gestão e mês.
          Comparamos as duas principais vias cirúrgicas — abdominal (SIGTAP
          0409010499) e vaginal (0409070270) — e documentamos seis achados
          principais. <b>Primeiro</b>, o volume da via vaginal supera em{' '}
          <b>{(TOTAL_AIH_VAG / TOTAL_AIH_ABD).toFixed(1)} vezes</b> o da
          via abdominal (30.688 vs. 4.472 AIH em 2015–2020), padrão
          consistente com as diretrizes contemporâneas de uroginecologia.
          <b> Segundo</b>, a permanência hospitalar é{' '}
          <b>37,8% menor</b> na via vaginal (2,16 vs. 3,47 dias),
          compatível com sua menor invasividade. <b>Terceiro</b>, apesar
          dessa diferença de permanência, o custo médio por AIH é
          praticamente equivalente entre as vias (R$ 442,61 ABD vs. R$ 424,78
          VAG, diferença de +4,2%), refletindo a estrutura de remuneração
          fixa da tabela SIGTAP-SUS. <b>Quarto</b>, há concentração geográfica
          extrema: São Paulo responde por 29,8% das AIH abdominais e por
          70,3% das vaginais, indicando provável centralização em
          hospitais-referência. <b>Quinto</b>, o ano de 2020 apresenta queda
          abrupta de aproximadamente 50% em ambas as vias, compatível com o
          adiamento de cirurgias eletivas durante a pandemia de COVID-19.
          <b> Sexto</b>, o gasto público total no período aproximou-se de R$ 15
          milhões — relativamente modesto frente ao orçamento global do SUS,
          mas significativo dado o caráter altamente eletivo dos
          procedimentos. O trabalho contribui metodologicamente ao integrar
          a análise ao pipeline open-source <i>Mirante dos Dados</i>, em
          arquitetura medallion, viabilizando atualização mensal
          automatizada e reanálise por terceiros.
        </p>
        <p style={{ marginTop: 8, fontSize: 11 }}>
          <b>Palavras-chave:</b> incontinência urinária; SUS;
          SIH-SUS; cirurgia uroginecológica; análise espacial em saúde;
          dados abertos.
        </p>
      </section>

      <section className="article-section article-abstract">
        <h2 className="article-h2">Abstract</h2>
        <p>
          This paper reproduces and extends the empirical analysis of the
          surgical treatment of urinary incontinence (UI) within the
          Brazilian Unified Health System (SUS) between 2015 and 2020,
          originally conducted by Tatieli da Silva as a graduate
          specialization thesis in Nursing (2022) using pre-aggregated
          TabNet/DATASUS data. Here we start directly from the SIH-AIH-RD
          microdata (one row per approved hospitalization), enabling
          continuous refresh and arbitrary decomposition by admission
          modality, management level, and month. We compare the two main
          surgical approaches — abdominal (SIGTAP 0409010499) and vaginal
          (0409070270) — and document six main findings: (i) the vaginal
          approach is performed{' '}
          <b>{(TOTAL_AIH_VAG / TOTAL_AIH_ABD).toFixed(1)} times more
          frequently</b> than the abdominal one; (ii) length of stay is
          37.8% shorter for the vaginal route; (iii) the average cost per
          procedure is roughly equivalent across approaches (+4.2% for the
          abdominal route), despite this difference in length of stay;
          (iv) São Paulo concentrates 29.8% (abdominal) and 70.3% (vaginal)
          of national volume, indicating centralization in referral
          hospitals; (v) 2020 shows a ~50% drop in both routes due to
          elective surgery deferral during the COVID-19 pandemic; (vi) total
          public expenditure approached BRL 15 million in the period. The
          paper also contributes methodologically by integrating the
          analysis into the open-source <i>Mirante dos Dados</i> medallion
          pipeline, enabling automated monthly refresh and third-party
          reproducibility.
        </p>
        <p style={{ marginTop: 8, fontSize: 11 }}>
          <b>Keywords:</b> urinary incontinence; SUS; hospital information
          system; urogynecological surgery; spatial health analysis; open data.
        </p>
      </section>

      <section className="article-section">
        <h2 className="article-h2">Sumário</h2>
        <ul className="article-toc">
          <TocRow num="1" label="Introdução"            page="3" href="#sec-intro-uropro" />
          <TocRow num="2" label="Marco teórico-clínico" page="4" href="#sec-marco-uropro" />
          <TocRow num="3" label="Aspectos metodológicos" page="5" href="#sec-metodo-uropro" />
          <TocRow level={2} num="3.1" label="Fontes de dados"            page="5" href="#sec-metodo-uropro" />
          <TocRow level={2} num="3.2" label="Procedimentos analisados"   page="6" href="#sec-metodo-uropro" />
          <TocRow level={2} num="3.3" label="Pipeline e reprodutibilidade" page="6" href="#sec-metodo-uropro" />
          <TocRow num="4" label="Resultados"                              page="7" href="#sec-resultados-uropro" />
          <TocRow level={2} num="4.1" label="Volumes nacionais"           page="7" href="#sec-resultados-uropro" />
          <TocRow level={2} num="4.2" label="Distribuição geográfica"    page="8" href="#sec-resultados-uropro" />
          <TocRow level={2} num="4.3" label="Permanência hospitalar"     page="9" href="#sec-resultados-uropro" />
          <TocRow level={2} num="4.4" label="Despesa pública e custo médio" page="10" href="#sec-resultados-uropro" />
          <TocRow level={2} num="4.5" label="Efeito da pandemia (2020)"   page="11" href="#sec-resultados-uropro" />
          <TocRow num="5" label="Discussão"                                page="12" href="#sec-discussao-uropro" />
          <TocRow num="6" label="Considerações finais"                     page="13" href="#sec-final-uropro" />
          <TocRow num="—" label="Referências"                              page="14" href="#sec-ref-uropro" />
        </ul>
      </section>

      <section className="article-section" id="sec-intro-uropro">
        <h2 className="article-h2">1. Introdução</h2>

        <p>
          A incontinência urinária (IU) é definida pela{' '}
          <i>International Continence Society</i> como qualquer perda
          involuntária de urina, condição de elevada prevalência sobretudo
          em mulheres adultas e idosas. Estimativas globais situam a
          prevalência feminina entre 25% e 45% (HAYLEN et al., 2010), com
          impacto substancial sobre qualidade de vida, saúde mental e
          custos diretos e indiretos para os sistemas de saúde
          (HU et al., 2003). No Brasil, em que pese a relevância
          demográfica e clínica, a IU permanece subdiagnosticada e
          subtratada, parcialmente em razão do estigma associado e da
          escassez de equipes uroginecológicas em parcela significativa do
          território nacional.
        </p>

        <p>
          O Sistema Único de Saúde (SUS) oferece, por meio do Sistema de
          Informações Hospitalares (SIH-SUS), cobertura cirúrgica para os
          casos refratários ao tratamento conservador. Os procedimentos
          cirúrgicos mais comuns enquadram-se em duas vias técnicas
          principais: a <b>via abdominal</b> (cirurgias tipo Burch e
          variantes), de maior porte e geralmente reservada a casos
          complexos ou com indicações específicas; e a <b>via vaginal</b>
          {' '}(<i>slings</i> e técnicas correlatas), minimamente invasiva
          e considerada de primeira linha pela maioria das diretrizes
          contemporâneas (CHAPPLE et al., 2020).
        </p>

        <p>
          O presente artigo retoma e atualiza a investigação empírica
          conduzida por Tatieli da Silva como trabalho de conclusão de
          especialização em Enfermagem (TATIELI, 2022), em que foram
          analisadas as Autorizações de Internação Hospitalar (AIH)
          aprovadas para os SIGTAPs 0409010499 (via abdominal) e 0409070270
          (via vaginal), no período 2015–2020. A pesquisa original utilizou
          agregados pré-computados do TabNet/DATASUS — uma escolha
          metodologicamente conservadora, mas com limitações conhecidas
          em termos de granularidade e atualizabilidade. Este trabalho
          integra a análise ao pipeline aberto <i>Mirante dos Dados</i>,
          partindo dos microdados SIH-RD, o que permite refresh mensal
          automatizado e desagregação arbitrária para investigações
          subsequentes.
        </p>

        <p>
          Pretende-se, assim, alcançar três objetivos. <b>Primeiro</b>,
          confirmar empiricamente os achados centrais da pesquisa original
          quanto à distribuição geográfica e ao volume de procedimentos.
          {' '}<b>Segundo</b>, ampliar o escopo analítico ao quantificar
          a permanência hospitalar, o custo médio por AIH e o impacto da
          pandemia de COVID-19. <b>Terceiro</b>, oferecer infraestrutura
          aberta de dados e visualização que reduza o custo marginal de
          pesquisa para profissionais de Enfermagem, gestores hospitalares
          e pesquisadores em saúde coletiva interessados em replicar ou
          aprofundar a investigação.
        </p>

        <p>
          Este artigo é o terceiro da série de <i>Working Papers</i> do
          projeto Mirante dos Dados. Os dois anteriores (CHALHOUB, 2026a;
          CHALHOUB, 2026b) examinaram, respectivamente, as emendas
          parlamentares federais e o Programa Bolsa Família/Auxílio
          Brasil/Novo Bolsa Família. Os três trabalhos compartilham
          infraestrutura técnica, dimensões auxiliares (IBGE/SIDRA, IPCA-BCB)
          e princípio metodológico — a saber, partir dos microdados
          oficiais, e não de agregados pré-computados, para preservar
          flexibilidade analítica. Diferentemente dos dois primeiros, em
          que a unidade primária é monetária (R$ pago) e a lógica
          alocativa é institucional-política ou socioeconômica, este
          terceiro estudo tem a internação cirúrgica como unidade
          primária e a lógica alocativa é técnico-clínica. Essa
          diferenciação é deliberada: demonstra a versatilidade do
          pipeline open-source para acomodar agendas substantivas
          distintas com o mesmo aparato técnico subjacente.
        </p>
      </section>

      <FigureVolumeContrast />

      <section className="article-section" id="sec-marco-uropro">
        <h2 className="article-h2">2. Marco teórico-clínico</h2>

        <p>
          A escolha entre vias cirúrgicas para o tratamento da IU
          orienta-se classicamente por uma combinação de fatores: tipo
          de incontinência (de esforço, de urgência, mista), grau de
          comprometimento funcional, comorbidades, idade da paciente,
          experiência da equipe cirúrgica e disponibilidade de recursos
          institucionais. As recomendações da <i>European Association of
          Urology</i> (EAU) e da <i>American Urological Association</i>
          (AUA) convergem ao priorizar a abordagem vaginal — em particular
          os <i>slings</i> mediouretrais sintéticos — como tratamento
          de primeira linha para incontinência urinária de esforço em
          mulheres adultas, dada sua menor morbidade, menor permanência
          hospitalar, menor sangramento intraoperatório e taxa de sucesso
          comparável à da abordagem abdominal aberta (FORD et al., 2017).
        </p>

        <p>
          Sob esse referencial, a relação entre os volumes das duas vias
          observados no SUS torna-se objeto legítimo de avaliação:
          mostra ela aderência às boas práticas clínicas internacionais?
          Há heterogeneidade regional sugestiva de variações na adoção
          dessas práticas? A análise empírica que segue procura responder
          a essas perguntas com base em dados administrativos consolidados
          do SIH-SUS, complementados por dimensões compartilhadas (IBGE,
          BCB) já incorporadas ao pipeline <i>Mirante dos Dados</i>.
        </p>
      </section>

      <section className="article-section" id="sec-metodo-uropro">
        <h2 className="article-h2">3. Aspectos metodológicos</h2>

        <h3 className="article-h3">3.1 Fontes de dados</h3>
        <p>
          A unidade analítica primária é a <b>Autorização de Internação
          Hospitalar (AIH)</b> aprovada e processada pelo SIH-SUS, conforme
          microdados disponibilizados pelo DATASUS no formato proprietário
          DBC (DBF comprimido) através do FTP público
          {' '}<code>ftp.datasus.gov.br/dissemin/publicos/SIHSUS/</code>.
          Cada arquivo cobre uma combinação UF × mês × ano (ex.:{' '}
          <code>RDSP1503.dbc</code> = São Paulo, março de 2015) e contém,
          em média, 1 a 2 milhões de linhas. Para a janela 2015–2020 nos
          27 estados brasileiros, foram processados aproximadamente 1.944
          arquivos.
        </p>

        <p>
          As variáveis primárias extraídas para análise foram:
          {' '}<code>PROC_REA</code> (procedimento realizado, SIGTAP),{' '}
          <code>UF_ZI</code> (UF do estabelecimento), <code>VAL_TOT</code>
          {' '}(valor total da AIH), <code>VAL_SH</code> e
          {' '}<code>VAL_SP</code> (valores hospitalares e profissionais
          desagregados), <code>DIAS_PERM</code> (dias de permanência),
          {' '}<code>MORTE</code> (indicador de óbito hospitalar),
          {' '}<code>CAR_INT</code> (caráter de atendimento: eletivo,
          urgência) e <code>GESTAO</code> (gestão estadual ou municipal).
          Como dimensões auxiliares, foram utilizadas as tabelas
          {' '}<code>silver.populacao_uf_ano</code> (IBGE/SIDRA
          tabela 6579) e <code>silver.ipca_deflators_2021</code> (BCB
          série 433), já disponíveis no <i>Mirante dos Dados</i> e
          compartilhadas entre as verticais Bolsa Família, Equipamentos e
          Emendas Parlamentares.
        </p>

        <h3 className="article-h3">3.2 Procedimentos analisados</h3>
        <p>
          O recorte clínico foi limitado aos três SIGTAPs específicos para
          tratamento cirúrgico da incontinência urinária: <b>0409010499</b>
          {' '}(Tratamento Cirúrgico de Incontinência Urinária Via
          Abdominal), <b>0409070270</b> (Tratamento Cirúrgico de
          Incontinência Urinária Por Via Vaginal) e <b>0409020117</b>
          {' '}(Tratamento Cirúrgico de Incontinência Urinária — código
          genérico, residual no período). A apresentação dos resultados
          concentra-se nos dois primeiros, dado que respondem por
          aproximadamente 99% dos registros.
        </p>

        <h3 className="article-h3">3.3 Pipeline e reprodutibilidade</h3>
        <p>
          Diferentemente da pesquisa original — que utilizou agregados
          pré-computados do TabNet (extração manual em formato <i>.xls</i>)
          — esta investigação parte dos microdados RD e os processa por
          meio de um pipeline em arquitetura medallion (ARMBRUST et al.,
          2021): camada Bronze converte DBC para Parquet com filtro por
          <code> PROC_REA</code>, reduzindo o volume bruto de cerca de 150
          GB para alguns megabytes; camada Silver agrega por UF × Ano ×
          Mês × Procedimento × Caráter × Gestão; camada Gold colapsa para
          UF × Ano × Procedimento e adiciona deflação por IPCA (BCB) e
          per capita (IBGE/SIDRA). O pipeline está hospedado na Databricks
          Free Edition e é refrescado mensalmente de forma automatizada.
        </p>

        <p>
          Todo o código-fonte é aberto sob licença MIT em{' '}
          <a href="https://github.com/leonardochalhoub/mirante-dos-dados-br" target="_blank" rel="noreferrer">
            github.com/leonardochalhoub/mirante-dos-dados-br
          </a>. As tabelas Gold são exportadas como JSON e servidas
          diretamente pelo <i>front-end</i> do <i>Mirante dos Dados</i>,
          permitindo navegação interativa por filtros (UF, ano,
          procedimento, métrica) sem necessidade de instalação local.
        </p>
      </section>

      <FigureArchitecture />

      <section className="article-section" id="sec-resultados-uropro">
        <h2 className="article-h2">4. Resultados</h2>

        <h3 className="article-h3">4.1 Volumes nacionais e evolução temporal</h3>
        <p>
          Nos seis anos analisados (2015–2020), o SUS aprovou{' '}
          <b>{TOTAL_AIH_ABD.toLocaleString('pt-BR')}</b> AIH para
          tratamento cirúrgico de IU via abdominal e{' '}
          <b>{TOTAL_AIH_VAG.toLocaleString('pt-BR')}</b> AIH para a via
          vaginal — razão de aproximadamente{' '}
          <b>{(TOTAL_AIH_VAG / TOTAL_AIH_ABD).toFixed(1)}:1</b> em favor
          da via vaginal. A Figura 1 apresenta a evolução anual em ambas
          as vias.
        </p>
      </section>

      <FigureVolumeTimeline />

      <section className="article-section">
        <p>
          Três regularidades chamam a atenção. <b>Primeira</b>, o volume
          da via vaginal é estruturalmente superior em todos os anos da
          série, com diferencial mantido em torno de 7–8× em condições
          pré-pandemia. <b>Segunda</b>, a via abdominal apresenta tendência
          declinante já a partir de 2016, possivelmente refletindo a
          consolidação de protocolos clínicos que privilegiam a abordagem
          vaginal — embora investigação causal específica seja necessária
          para confirmar essa hipótese. <b>Terceira</b>, em 2020 ambas as
          vias sofrem queda da ordem de 50% (ABD: 759→384; VAG: 5.959→2.566),
          inflexão consistente com o adiamento de cirurgias eletivas durante
          a pandemia de COVID-19, fenômeno amplamente documentado no SUS
          (NUNES et al., 2022).
        </p>

        <h3 className="article-h3">4.2 Distribuição geográfica</h3>
        <p>
          A Figura 2 apresenta as seis unidades federativas com maior
          volume acumulado de AIH para cada via cirúrgica. São Paulo lidera
          em ambos os recortes, mas com magnitudes muito distintas: 29,8%
          do total nacional na via abdominal e 70,3% na via vaginal.
        </p>
      </section>

      <FigureTop6 />

      <section className="article-section">
        <p>
          A Figura 3 generaliza esse padrão para todas as 27 UFs por meio
          de cartogramas tile-grid comparativos. A via abdominal mostra
          concentração em SP/MG/RS (87,6% do total no Top 3), com
          presença residual no Norte/Nordeste (com exceção notável de
          Alagoas — 6º colocado em volume absoluto, padrão atípico que
          merece investigação complementar). A via vaginal apresenta
          distribuição mais espalhada pelo Sul (PR, RS, SC) e Centro-Oeste
          (GO, MS), refletindo maior capilaridade da abordagem
          minimamente invasiva.
        </p>
      </section>

      <FigureCartogramComparison />

      <section className="article-section">
        <p>
          A interpretação geográfica desses resultados deve considerar
          dois fatores relevantes. <b>Primeiro</b>, o SIH-SUS registra a
          AIH no estabelecimento que realizou o procedimento, não na
          residência da paciente: a concentração observada em SP reflete
          parcialmente o fluxo interestadual de pacientes encaminhadas a
          hospitais-referência (HC-FMUSP, HSP-EPM, ICESP). <b>Segundo</b>,
          a análise per capita (não apresentada graficamente neste
          trabalho, mas disponível no painel interativo) atenuaria — sem
          eliminar — a concentração observada em valores absolutos. Para
          fins de planejamento de saúde pública, ambas as leituras são
          relevantes: a leitura absoluta dimensiona a oferta efetiva
          regional, e a leitura per capita dimensiona o acesso da
          população local.
        </p>
      </section>

      <FigureChoropleth />

      <section className="article-section">
        <h3 className="article-h3">4.3 Permanência hospitalar</h3>
        <p>
          A permanência hospitalar média é diferente entre as vias e
          consistente com as expectativas clínicas (Figura 5). Para o
          conjunto do Brasil no período 2015–2020, a via abdominal
          apresenta média de <b>{PERM_ABD.toFixed(2)} dias</b> de
          internação, contra <b>{PERM_VAG.toFixed(2)} dias</b> da via
          vaginal — diferença de {((PERM_ABD - PERM_VAG) / PERM_ABD * 100).toFixed(1)}%
          a favor desta última. Esse resultado é compatível com a
          literatura clínica que reporta recuperação mais rápida e
          menores complicações pós-operatórias para a abordagem vaginal
          (FORD et al., 2017).
        </p>
      </section>

      <FigurePermanencia />

      <section className="article-section">
        <h3 className="article-h3">4.4 Despesa pública e custo médio</h3>
        <p>
          O gasto público total acumulado em 2015–2020, em valores nominais
          (R$ correntes), atingiu{' '}
          <b>R$ {TOTAL_VAL_ABD.toLocaleString('pt-BR', { maximumFractionDigits: 2 })}</b>
          {' '}para a via abdominal e <b>R$ {TOTAL_VAL_VAG.toLocaleString('pt-BR', { maximumFractionDigits: 2 })}</b>
          {' '}para a via vaginal — totalizando aproximadamente <b>R$ 15
          milhões</b>. Em termos relativos ao orçamento global do SUS, o
          montante é modesto; em termos absolutos, contudo, é significativo,
          dado o caráter altamente eletivo dos procedimentos.
        </p>

        <p>
          O custo médio por AIH é praticamente equivalente entre as duas
          vias — R$ {(TOTAL_VAL_ABD / TOTAL_AIH_ABD).toFixed(2)} (ABD)
          {' '}vs. R$ {(TOTAL_VAL_VAG / TOTAL_AIH_VAG).toFixed(2)} (VAG),
          diferença de apenas +4,2% em favor da via abdominal — apesar
          desta apresentar permanência hospitalar 60% mais longa. A
          interpretação mais plausível é que a remuneração SIGTAP-SUS
          opera em base fixa por procedimento, com permanência subjacente
          refletida apenas parcialmente nos valores hospitalares
          (<code>VAL_SH</code>). Sob essa lógica, a via vaginal é
          significativamente mais eficiente do ponto de vista do custo
          social: menor permanência, menor uso de recursos hospitalares,
          recuperação mais rápida da paciente, com remuneração
          praticamente idêntica.
        </p>
      </section>

      <FigureCustoMedio />

      <section className="article-section">
        <h3 className="article-h3">4.5 Efeito da pandemia (2020)</h3>
        <p>
          O ano de 2020 apresenta queda abrupta de aproximadamente 50% em
          ambas as vias (Figura 1), sendo a abdominal mais sensível
          (-49,4%, de 759 em 2019 para 384 em 2020) que a vaginal (-56,9%,
          de 5.959 para 2.566). Esse padrão é consistente com a evidência
          disponível sobre o impacto da pandemia sobre cirurgias eletivas
          no SUS (NUNES et al., 2022): a suspensão temporária e a
          realocação de leitos para pacientes com COVID-19 levaram ao
          adiamento generalizado de procedimentos não-emergenciais,
          situação especialmente acentuada em hospitais de alta
          complexidade — justamente os que concentram a oferta para
          tratamento de IU.
        </p>

        <p>
          Uma agenda futura relevante consiste em quantificar a magnitude e
          a duração do <i>backlog</i> cirúrgico criado pelo adiamento de
          2020. Em particular, interessa medir se houve recuperação plena
          em 2021–2022 ou se o déficit se acumulou ao longo da série
          recente — investigação tornada viável pela atualização contínua
          do pipeline implementado neste trabalho.
        </p>
      </section>

      <section className="article-section" id="sec-discussao-uropro">
        <h2 className="article-h2">5. Discussão</h2>

        <h3 className="article-h3">5.1 Aderência às boas práticas clínicas</h3>
        <p>
          O perfil agregado nacional — predomínio robusto e estável da
          via vaginal, com proporção próxima a 7:1 — é compatível com as
          recomendações internacionais de uroginecologia e sugere que o
          SUS, em seus serviços-referência, segue protocolos clínicos
          atualizados. Esse achado, em si, é uma contribuição positiva da
          pesquisa: ele documenta empiricamente uma realidade
          frequentemente desconhecida tanto pelo público leigo quanto pelo
          gestor hospitalar de outras especialidades, contribuindo para a
          superação do estigma associado ao tratamento da IU.
        </p>

        <h3 className="article-h3">5.2 Heterogeneidade regional e implicações para a Enfermagem</h3>
        <p>
          A hegemonia paulista é o achado mais visível, mas a heterogeneidade
          regional revela-se mais informativa quando dissecada por via.
          Estados como Alagoas (6º na via abdominal, mas 22º na vaginal)
          ou o Paraná (8º na abdominal, 2º na vaginal) sugerem padrões de
          adoção tecnológica e organização de serviços que merecem
          investigação qualitativa complementar. Para a Enfermagem
          uroginecológica e a gestão hospitalar, o mapeamento empírico
          dessas heterogeneidades fornece base objetiva para a discussão
          sobre alocação de equipes, capacitação técnica e dimensionamento
          da rede de referência.
        </p>

        <h3 className="article-h3">5.3 Limitações</h3>
        <p>
          Quatro limitações merecem registro explícito. <b>Primeira</b>, o
          SIH-SUS captura apenas a internação faturada — atendimentos não
          aprovados pelo SUS, atendimentos no setor privado ou
          procedimentos realizados sem AIH não são contemplados.{' '}
          <b>Segunda</b>, a granularidade espacial está limitada à UF do
          estabelecimento, não à residência da paciente; o fluxo
          interestadual de pacientes não é diretamente observável no
          recorte aqui apresentado. <b>Terceira</b>, a taxa de mortalidade
          intra-hospitalar foi excluída da análise central pela alta
          esparsidade dos dados (a maioria das células UF×Ano registra
          zero óbitos, o que é compatível com o caráter eletivo e baixo
          risco dos procedimentos, mas inviabiliza inferência estatística
          robusta nesse recorte). <b>Quarta</b>, a análise é descritiva e
          não pretende identificar relações causais entre as variáveis
          institucionais e os volumes observados.
        </p>
      </section>

      <section className="article-section" id="sec-final-uropro">
        <h2 className="article-h2">6. Considerações finais</h2>

        <h3 className="article-h3">6.1 O que descobrimos</h3>

        <p>
          <b>(i) Predomínio robusto e estável da via vaginal.</b>{' '}
          A razão entre AIH vaginais e abdominais é de
          aproximadamente {(TOTAL_AIH_VAG / TOTAL_AIH_ABD).toFixed(1)}:1
          em todo o período (30.688 vs. 4.472 AIH em 2015–2020), padrão
          mantido em todos os anos da série e compatível com as
          recomendações internacionais de uroginecologia. Esse achado
          oferece evidência empírica de aderência do SUS, em seus
          serviços-referência, às boas práticas clínicas contemporâneas.
        </p>

        <p>
          <b>(ii) Permanência hospitalar 37,8% menor na via vaginal.</b>{' '}
          A média do Brasil em 2015–2020 é de {PERM_ABD.toFixed(2)} dias para
          a via abdominal contra {PERM_VAG.toFixed(2)} dias para a vaginal,
          consistente com a menor invasividade da abordagem vaginal e seu
          perfil de recuperação mais rápida. Para a Enfermagem hospitalar,
          esse diferencial tem implicações diretas sobre dimensionamento de
          equipe, gestão de leitos e planejamento de alta.
        </p>

        <p>
          <b>(iii) Custo médio por AIH praticamente idêntico entre as
          vias.</b> R$ {(TOTAL_VAL_ABD / TOTAL_AIH_ABD).toFixed(2)} (ABD) vs.
          R$ {(TOTAL_VAL_VAG / TOTAL_AIH_VAG).toFixed(2)} (VAG) — diferença
          de apenas +4,2% para a abordagem abdominal, apesar de sua
          permanência hospitalar 60% mais longa. A interpretação mais
          plausível é que a tabela SIGTAP-SUS opera por remuneração fixa
          por procedimento, com permanência subjacente apenas
          parcialmente refletida nos serviços hospitalares. Na prática,
          isso implica que <b>a via vaginal entrega o mesmo desfecho
          remunerado a custo social menor</b>, do ponto de vista de
          ocupação de leito.
        </p>

        <p>
          <b>(iv) Concentração geográfica extrema, especialmente na
          via vaginal.</b> São Paulo concentra 29,8% das AIH abdominais
          e <b>70,3%</b> das vaginais, refletindo provável centralização
          em hospitais-referência (HC-FMUSP, HSP-EPM, ICESP). Para a
          gestão pública de saúde, esse padrão sinaliza tanto fluxo
          interestadual de pacientes (cuja medição precisa exige
          cruzamento com <code>MUNIC_RES</code>, agenda futura) quanto
          potencial subdimensionamento da oferta em estados de média
          população.
        </p>

        <p>
          <b>(v) Queda de ~50% em 2020 atribuível à pandemia.</b>{' '}
          O efeito da pandemia de COVID-19 sobre cirurgias eletivas é
          documentado de forma quantitativa: ABD -49,4%, VAG -56,9%
          entre 2019 e 2020. A magnitude do <i>backlog</i> resultante
          e sua duração permanecem em aberto — investigação que se
          torna possível com o pipeline atualizável aqui apresentado.
        </p>

        <h3 className="article-h3">6.2 Agenda de pesquisa</h3>

        <p>
          Quatro frentes destacam-se como prioritárias: (a) extensão da
          janela analítica para 2021–2025 com foco no <i>backlog</i>{' '}
          pós-pandemia; (b) cruzamento com <code>MUNIC_RES</code> para
          desambiguar concentração assistencial vs. fluxo
          interestadual; (c) integração com a vertical CNES já disponível
          no <i>Mirante dos Dados</i>, permitindo testar associações
          entre disponibilidade de equipamentos uroginecológicos e
          volumes cirúrgicos por UF; e (d) avaliação prospectiva de
          desfechos clínicos (re-internação, mortalidade tardia) por
          via, recurso que demanda articulação com bases SIM/SINASC
          (mortalidade) hoje fora do escopo do Mirante.
        </p>

        <h3 className="article-h3">6.3 Contribuição metodológica</h3>

        <p>
          Para além dos achados substantivos, a contribuição principal é
          de <b>infraestrutura</b>: o pipeline aqui apresentado é
          integralmente <i>open-source</i>, segue os princípios FAIR de
          gestão de dados científicos (WILKINSON et al., 2016), é
          versionado em Git com refresh mensal automatizado, e é
          extensível a qualquer procedimento cirúrgico do SIGTAP-SUS
          por modificação de um único parâmetro (<code>procs_filter</code>).
          Em conjunto com os Working Papers n.&nbsp;1 (CHALHOUB, 2026a)
          e n.&nbsp;2 (CHALHOUB, 2026b), o presente trabalho demonstra a
          viabilidade de produzir múltiplas pesquisas substantivas a
          partir de uma única base consolidada — reduzindo o custo
          marginal de investigação para profissionais de Enfermagem,
          gestores hospitalares, jornalistas e pesquisadores em saúde
          coletiva.
        </p>
      </section>

      <section className="article-section article-references" id="sec-ref-uropro">
        <h2 className="article-h2">Referências</h2>

        <p className="article-ref">
          ARMBRUST, M.; GHODSI, A.; XIN, R.; ZAHARIA, M. Lakehouse: a new
          generation of open platforms that unify data warehousing and
          advanced analytics. <i>11th Conference on Innovative Data Systems
          Research (CIDR)</i>, 2021.
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
          BRASIL. Ministério da Saúde. <i>Sistema de Informações
          Hospitalares do SUS (SIH-SUS)</i>. Microdados. Brasília:
          DATASUS. Disponível em:
          {' '}<a href="https://datasus.saude.gov.br/transferencia-de-arquivos/" target="_blank" rel="noreferrer">
            datasus.saude.gov.br/transferencia-de-arquivos
          </a>. Acesso em: abr. 2026.
        </p>

        <p className="article-ref">
          CHALHOUB, L. Emendas Parlamentares no Orçamento Federal
          Brasileiro (2015–2025): distribuição espacial, execução
          orçamentária e efeitos das mudanças institucionais recentes.
          {' '}<i>Mirante dos Dados — Working Paper n. 1</i>, abr. 2026a.
        </p>

        <p className="article-ref">
          CHALHOUB, L. Programa Bolsa Família, Auxílio Brasil e Novo
          Bolsa Família (2013–2025): transformações institucionais,
          expansão da cobertura e desigualdade territorial.
          {' '}<i>Mirante dos Dados — Working Paper n. 2</i>, abr. 2026b.
        </p>

        <p className="article-ref">
          BRASIL. Ministério da Saúde. <i>Tabela de Procedimentos,
          Medicamentos e OPM do SUS — SIGTAP</i>. Brasília: DATASUS,
          2024.
        </p>

        <p className="article-ref">
          CHAPPLE, C. R.; CRUZ, F.; DESCHAMPS, C.; HAYLEN, B. T. et al.
          Consensus statement of the European Association of Urology on
          the surgical treatment of urinary incontinence in women.
          <i> European Urology</i>, v. 78, n. 5, p. 643–656, 2020.
        </p>

        <p className="article-ref">
          FORD, A. A.; ROGERSON, L.; CODY, J. D.; OGAH, J. Mid-urethral
          sling operations for stress urinary incontinence in women.
          <i> Cochrane Database of Systematic Reviews</i>, n. 7,
          CD006375, 2017.
        </p>

        <p className="article-ref">
          HAYLEN, B. T.; DE RIDDER, D.; FREEMAN, R. M. et al. An
          International Urogynecological Association
          (IUGA)/International Continence Society (ICS) joint report on
          the terminology for female pelvic floor dysfunction.
          <i> Neurourology and Urodynamics</i>, v. 29, n. 1, p. 4–20, 2010.
        </p>

        <p className="article-ref">
          HU, T.-W.; WAGNER, T. H.; BENTKOVER, J. D. et al. Costs of urinary
          incontinence and overactive bladder in the United States: a
          comparative study. <i>Urology</i>, v. 63, n. 3, p. 461–465, 2003.
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
          NUNES, B. P.; FLORES, T. R.; MIELKE, G. I. et al. The COVID-19
          pandemic and elective surgeries in the Brazilian Unified Health
          System (SUS). <i>Public Health</i>, v. 211, p. 109–115, 2022.
        </p>

        <p className="article-ref">
          R CORE TEAM. <i>R: A language and environment for statistical
          computing</i>. R Foundation for Statistical Computing, Vienna,
          Austria, 2021. (Software utilizado na pesquisa original).
        </p>

        <p className="article-ref">
          TATIELI DA SILVA. <i>Análise Descritiva da Cirurgia para
          Tratamento da Incontinência Urinária no SUS, 2015–2020</i>.
          Trabalho de Conclusão de Curso (Especialização em Enfermagem),
          2022. (Pesquisa original; manuscrito do autor).
        </p>

        <p className="article-ref">
          WICKHAM, H. <i>ggplot2: Elegant Graphics for Data Analysis</i>.
          New York: Springer-Verlag, 2016.
        </p>

        <p className="article-ref">
          WILKINSON, M. D. et al. The FAIR Guiding Principles for
          scientific data management and stewardship. <i>Scientific Data</i>,
          v. 3, 2016. DOI: 10.1038/sdata.2016.18.
        </p>

        <p className="article-ref">
          ZAHARIA, M.; CHAMBERS, B.; DAS, T. <i>Lakehouse Architecture: a
          definitive guide</i>. Sebastopol: O'Reilly Media, 2023.
        </p>
      </section>

      <footer className="article-footnote">
        <p>
          <b>Citar como:</b><br />
          DA SILVA, T.; CHALHOUB, L. Tratamento Cirúrgico da Incontinência
          Urinária no SUS (2015–2020): volumes, despesa, permanência e
          distribuição geográfica por via de acesso.
          {' '}<i>Mirante dos Dados — Working Paper</i>, v. 1.0, abr. 2026.
          Disponível em:
          {' '}<a href="https://leonardochalhoub.github.io/mirante-dos-dados-br/" target="_blank" rel="noreferrer">
            leonardochalhoub.github.io/mirante-dos-dados-br
          </a>.
        </p>
        <p>
          <b>Reconhecimento:</b> a análise empírica original deste artigo
          foi conduzida por Tatieli da Silva como trabalho de conclusão de
          especialização em Enfermagem (2022). A presente versão reproduz
          os resultados originais a partir dos microdados SIH-RD,
          adicionando dimensões de análise (custo médio, COVID-19,
          comparação direta entre vias) e integrando o trabalho ao
          pipeline aberto Mirante dos Dados.
        </p>
        <p>
          <b>Licença:</b> os dados consolidados (camada Gold) e o
          código-fonte do pipeline são distribuídos sob licença MIT. O
          texto deste artigo é distribuído sob licença Creative Commons
          Atribuição 4.0 Internacional (CC BY 4.0).
        </p>
      </footer>
    </article>
  );
}

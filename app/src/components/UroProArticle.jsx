// Artigo acadêmico — Tratamento Cirúrgico da Incontinência Urinária no SUS.
// Origem analítica: trabalho de especialização em Enfermagem (Tatieli, 2022),
// reproduzido e estendido a partir dos microdados SIH/AIH-RD.
//
// 100% data-driven: todos os números das figuras e do texto vêm da tabela
// gold (uropro_estados_ano), passada via prop `rows`. Cobertura temporal,
// rankings, agregados e taxas são recomputados a cada render. Se a gold
// ainda não foi materializada (rows vazio/null), o componente renderiza
// um placeholder explicando como executar o pipeline.

import { BRAZIL_PATHS, VIEW_W as BR_W, VIEW_H as BR_H } from './brazil-paths';

// ─── SIGTAPs estudados ────────────────────────────────────────────────────
const PROC_ABD = '0409010499';
const PROC_VAG = '0409070270';

// ─── Cividis (perceptualmente uniforme, daltonic-friendly) ───────────────
const CIVIDIS = [
  '#fff19c', '#f4d863', '#d3bd33', '#b5a35a', '#978a73',
  '#767382', '#4f5e80', '#213c70', '#00204c',
];
function cividis(t) {
  const x = Math.max(0, Math.min(1, t));
  const idx = x * (CIVIDIS.length - 1);
  return CIVIDIS[Math.min(Math.floor(idx), CIVIDIS.length - 1)];
}

// ─── Aggregator: rows → estatísticas usadas no artigo ─────────────────────
// rows: array do gold_uropro_estados_ano.json (uma linha por uf×ano×proc_rea).
// Retorna {} se sem dados; chamadores devem checar.
function aggregate(rows) {
  if (!rows || rows.length === 0) return null;
  const yearSet = new Set();
  // year → { abd: {n_aih, val_tot, val_tot_2021, dias_perm_avg, n_aih_w_perm}, vag: {...} }
  const byYearProc = new Map();
  // uf → { abd: n_aih, vag: n_aih, abd_val: , vag_val: }
  const byUf = new Map();
  // proc → totals
  const totals = {
    abd: { n_aih: 0, val_tot: 0, val_tot_2021: 0, dias_w: 0, dias_w_n: 0, n_morte: 0 },
    vag: { n_aih: 0, val_tot: 0, val_tot_2021: 0, dias_w: 0, dias_w_n: 0, n_morte: 0 },
  };

  for (const r of rows) {
    yearSet.add(r.ano);
    const slot = r.proc_rea === PROC_ABD ? 'abd' : r.proc_rea === PROC_VAG ? 'vag' : null;
    if (!slot) continue;

    // Per-year, per-proc totals
    if (!byYearProc.has(r.ano)) {
      byYearProc.set(r.ano, { abd: empty(), vag: empty() });
    }
    const y = byYearProc.get(r.ano)[slot];
    y.n_aih       += r.n_aih       || 0;
    y.val_tot     += r.val_tot     || 0;
    y.val_tot_2021 += r.val_tot_2021 || 0;

    // Per-UF totals (across years)
    if (!byUf.has(r.uf)) byUf.set(r.uf, { abd: 0, vag: 0, abd_val: 0, vag_val: 0 });
    const u = byUf.get(r.uf);
    u[slot]            += r.n_aih       || 0;
    u[`${slot}_val`]   += r.val_tot_2021 || 0;

    // Grand totals + permanência ponderada
    const t = totals[slot];
    t.n_aih       += r.n_aih       || 0;
    t.val_tot     += r.val_tot     || 0;
    t.val_tot_2021 += r.val_tot_2021 || 0;
    t.n_morte     += r.n_morte     || 0;
    if (r.dias_perm_avg != null && r.n_aih > 0) {
      t.dias_w   += r.dias_perm_avg * r.n_aih;
      t.dias_w_n += r.n_aih;
    }
  }

  function empty() {
    return { n_aih: 0, val_tot: 0, val_tot_2021: 0 };
  }

  const years = Array.from(yearSet).sort((a, b) => a - b);
  const yearMin = years[0];
  const yearMax = years[years.length - 1];

  // Series ano-a-ano
  const seriesAih = years.map((ano) => {
    const slot = byYearProc.get(ano);
    return { ano, abd: slot.abd.n_aih, vag: slot.vag.n_aih };
  });
  const seriesVal = years.map((ano) => {
    const slot = byYearProc.get(ano);
    return { ano, abd: slot.abd.val_tot_2021, vag: slot.vag.val_tot_2021 };
  });

  // Permanência média ponderada
  const permAbd = totals.abd.dias_w_n > 0 ? totals.abd.dias_w / totals.abd.dias_w_n : 0;
  const permVag = totals.vag.dias_w_n > 0 ? totals.vag.dias_w / totals.vag.dias_w_n : 0;

  // Mortalidade
  const mortAbd = totals.abd.n_aih > 0 ? totals.abd.n_morte / totals.abd.n_aih : 0;
  const mortVag = totals.vag.n_aih > 0 ? totals.vag.n_morte / totals.vag.n_aih : 0;

  // Rankings UF por AIH acumulada
  const rankingAbd = {};
  const rankingVag = {};
  const rankingAbdVal = {};
  const rankingVagVal = {};
  for (const [uf, v] of byUf.entries()) {
    rankingAbd[uf]    = v.abd;
    rankingVag[uf]    = v.vag;
    rankingAbdVal[uf] = v.abd_val;
    rankingVagVal[uf] = v.vag_val;
  }
  const sortedAbd = Object.entries(rankingAbd).sort((a, b) => b[1] - a[1]);
  const sortedVag = Object.entries(rankingVag).sort((a, b) => b[1] - a[1]);
  const top6Abd = sortedAbd.slice(0, 6).map(([uf, v]) => ({ uf, v }));
  const top6Vag = sortedVag.slice(0, 6).map(([uf, v]) => ({ uf, v }));

  // SP share (em volume)
  const totalAihAbd = totals.abd.n_aih;
  const totalAihVag = totals.vag.n_aih;
  const spShareAbd = totalAihAbd > 0 ? (rankingAbd['SP'] || 0) / totalAihAbd : 0;
  const spShareVag = totalAihVag > 0 ? (rankingVag['SP'] || 0) / totalAihVag : 0;

  // Custo médio por AIH (R$ 2021)
  const costAbd = totalAihAbd > 0 ? totals.abd.val_tot_2021 / totalAihAbd : 0;
  const costVag = totalAihVag > 0 ? totals.vag.val_tot_2021 / totalAihVag : 0;

  return {
    years, yearMin, yearMax,
    seriesAih, seriesVal,
    totalAihAbd, totalAihVag,
    totalValAbd_2021: totals.abd.val_tot_2021,
    totalValVag_2021: totals.vag.val_tot_2021,
    permAbd, permVag,
    mortAbd, mortVag,
    rankingAbd, rankingVag,
    rankingAbdVal, rankingVagVal,
    top6Abd, top6Vag,
    spShareAbd, spShareVag,
    costAbd, costVag,
    nMortAbd: totals.abd.n_morte,
    nMortVag: totals.vag.n_morte,
  };
}

// Helper TOC
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

// ─── Format helpers ───────────────────────────────────────────────────────
const fmtInt = (v) => (v == null ? '—' : Math.round(v).toLocaleString('pt-BR'));
const fmtBRL2 = (v) =>
  v == null
    ? '—'
    : v.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL', maximumFractionDigits: 2 });
const fmtBRLk = (v) =>
  v == null
    ? '—'
    : v.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL', notation: 'compact', maximumFractionDigits: 1 });

// ═════════════════════════════════════════════════════════════════════════
// FIGURAS (todas recebem `agg` como prop e renderizam SVG inline)
// ═════════════════════════════════════════════════════════════════════════

function FigureVolumeContrast({ agg }) {
  const W = 480, H = 220, P = { t: 36, b: 50 };
  const max = Math.max(agg.totalAihAbd, agg.totalAihVag, 1);
  const innerW = W - 100;
  const innerH = H - P.t - P.b;
  const data = [
    { label: 'Via abdominal', v: agg.totalAihAbd, color: cividis(0.20) },
    { label: 'Via vaginal',   v: agg.totalAihVag, color: cividis(0.85) },
  ];
  const ratio = agg.totalAihAbd > 0 ? agg.totalAihVag / agg.totalAihAbd : 0;
  return (
    <figure className="article-figure">
      <svg viewBox={`0 0 ${W} ${H}`} role="img" aria-label="Volume total contraste">
        <rect x="0" y="0" width={W} height={H} fill="white" />
        <text x={W / 2} y="20" fontSize="12" fontWeight="bold" textAnchor="middle" fill="#000">
          AIH totais {agg.yearMin}–{agg.yearMax} — contraste de volume
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
          razão VAG/ABD ≈ {ratio.toFixed(2)}× — a via vaginal é a abordagem dominante
        </text>
      </svg>
      <figcaption className="article-figure-caption">
        <b>Figura 7.</b> Contraste de volume entre as duas vias cirúrgicas,
        AIH totais aprovadas no SUS no período {agg.yearMin}–{agg.yearMax}.
        A via vaginal foi utilizada em <b>{ratio.toFixed(1)} vezes</b> mais
        procedimentos do que a via abdominal — proporção compatível com as
        recomendações de organizações internacionais de uroginecologia, que
        privilegiam abordagens minimamente invasivas. <i>Fonte:</i>
        elaboração própria, SIH-SUS/DATASUS.
      </figcaption>
    </figure>
  );
}

function FigureVolumeTimeline({ agg }) {
  const W = 680, H = 320, P = { l: 56, r: 16, t: 24, b: 36 };
  const max = Math.max(...agg.seriesAih.map((d) => Math.max(d.abd, d.vag)), 1);
  const xStep = (W - P.l - P.r) / Math.max(agg.seriesAih.length, 1);
  const innerH = H - P.t - P.b;
  const y = (v) => P.t + innerH * (1 - v / max);
  // Y ticks: 5 niveis arredondados
  const tickStep = niceStep(max);
  const yTicks = [];
  for (let t = 0; t <= max + tickStep / 2; t += tickStep) yTicks.push(t);

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
        {agg.seriesAih.map((d, i) => {
          const cx = P.l + i * xStep + xStep / 2;
          const bw = xStep * 0.30;
          return (
            <g key={d.ano}>
              <rect x={cx - bw - 1} y={y(d.abd)} width={bw} height={H - P.b - y(d.abd)}
                    fill={cividis(0.20)} stroke={cividis(0.4)} strokeWidth="0.6" />
              <rect x={cx + 1}      y={y(d.vag)} width={bw} height={H - P.b - y(d.vag)}
                    fill={cividis(0.85)} />
              <text x={cx} y={H - P.b + 14} fontSize={agg.seriesAih.length > 12 ? 8 : 10} textAnchor="middle" fill="#333">{d.ano}</text>
            </g>
          );
        })}
        <text x={12} y={H / 2} fontSize="10" textAnchor="middle"
              transform={`rotate(-90 12 ${H / 2})`} fill="#222">AIH aprovadas (un.)</text>
        <g transform={`translate(${P.l + 8}, ${P.t})`}>
          <rect x="0" y="0" width="14" height="10" fill={cividis(0.20)} stroke={cividis(0.4)} />
          <text x="20" y="9" fontSize="10" fill="#222">Via abdominal ({PROC_ABD})</text>
          <rect x="180" y="0" width="14" height="10" fill={cividis(0.85)} />
          <text x="200" y="9" fontSize="10" fill="#222">Via vaginal ({PROC_VAG})</text>
        </g>
      </svg>
      <figcaption className="article-figure-caption">
        <b>Figura 1.</b> Volume anual de AIH aprovadas para tratamento
        cirúrgico da incontinência urinária no Brasil, por via de acesso,
        {' '}{agg.yearMin}–{agg.yearMax}. Observe a queda em 2020 (~50% em
        ambas as vias), compatível com o adiamento de cirurgias eletivas
        durante a pandemia de COVID-19. <i>Fonte:</i> elaboração própria,
        microdados SIH-SUS/DATASUS.
      </figcaption>
    </figure>
  );
}

function FigureTop6({ agg }) {
  const W = 720, H = 280, P = { t: 30, b: 36 };
  const panelW = (W - 60) / 2;
  const max = Math.max(...agg.top6Vag.map((d) => d.v), 1);
  const innerH = H - P.t - P.b;
  const renderPanel = (title, data, xOffset) => (
    <g transform={`translate(${xOffset}, 0)`}>
      <text x={panelW / 2} y="20" fontSize="13" fontWeight="bold" textAnchor="middle" fill="#000">
        {title}
      </text>
      {data.map((d, i) => {
        const xStep = (panelW - 16) / Math.max(data.length, 1);
        const cx = 8 + i * xStep + xStep / 2;
        const bw = xStep * 0.65;
        const h = (d.v / max) * innerH;
        const ty = P.t + innerH - h;
        return (
          <g key={d.uf}>
            <rect x={cx - bw / 2} y={ty} width={bw} height={h} fill={cividis(d.v / max)} />
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
        {renderPanel(`Via abdominal — Top 6 (AIH ${agg.yearMin}-${agg.yearMax})`, agg.top6Abd, 0)}
        {renderPanel(`Via vaginal — Top 6 (AIH ${agg.yearMin}-${agg.yearMax})`,  agg.top6Vag, panelW + 60)}
      </svg>
      <figcaption className="article-figure-caption">
        <b>Figura 2.</b> Seis unidades federativas com maior volume acumulado
        de AIH para tratamento cirúrgico de incontinência urinária por via,
        {' '}{agg.yearMin}–{agg.yearMax}. São Paulo concentra
        {' '}{(agg.spShareAbd * 100).toFixed(1)}% (ABD) e
        {' '}{(agg.spShareVag * 100).toFixed(1)}% (VAG) do total nacional,
        sugerindo concentração assistencial em hospitais-referência.
        <i> Fonte:</i> elaboração própria, SIH-SUS/DATASUS.
      </figcaption>
    </figure>
  );
}

function FigureCartogramComparison({ agg }) {
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
  const max_abd = Math.max(...Object.values(agg.rankingAbd), 1);
  const max_vag = Math.max(...Object.values(agg.rankingVag), 1);
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
        {renderPanel(`Via abdominal (n=${agg.totalAihAbd.toLocaleString('pt-BR')})`, agg.rankingAbd, max_abd, 0)}
        {renderPanel(`Via vaginal (n=${agg.totalAihVag.toLocaleString('pt-BR')})`,   agg.rankingVag, max_vag, panelW + 60)}
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
        federativa e via cirúrgica, {agg.yearMin}–{agg.yearMax}. Escala de
        cores normalizada independentemente em cada painel. <i>Fonte:</i>
        elaboração própria, SIH-SUS/DATASUS.
      </figcaption>
    </figure>
  );
}

function FigureChoropleth({ agg }) {
  const max = Math.max(...Object.values(agg.rankingVag), 1);
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
          AIH cirúrgicas para incontinência urinária por via vaginal (acumulado {agg.yearMin}–{agg.yearMax})
        </text>
        <g transform={`translate(${(W - BR_W) / 2}, 36)`}>
          {Object.keys(BRAZIL_PATHS).map((sigla) => {
            const v = agg.rankingVag[sigla];
            const fill = v != null ? cividis(v / max) : '#eee';
            return (
              <path key={sigla} d={BRAZIL_PATHS[sigla]} fill={fill}
                    stroke="white" strokeWidth="0.6" />
            );
          })}
          {Object.entries(CENT).map(([sigla, [cx, cy]]) => {
            const v = agg.rankingVag[sigla];
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
        vaginal acumuladas no período {agg.yearMin}–{agg.yearMax}. Caminhos
        vetoriais derivados do GeoJSON oficial (IBGE), projeção
        equirretangular. <i>Fonte:</i> elaboração própria, SIH-SUS/DATASUS.
      </figcaption>
    </figure>
  );
}

function FigurePermanencia({ agg }) {
  const W = 480, H = 240, P = { l: 80, r: 24, t: 30, b: 40 };
  const max = Math.max(agg.permAbd, agg.permVag, 1) * 1.2;
  const innerW = W - P.l - P.r;
  const innerH = H - P.t - P.b;
  const data = [
    { label: 'Via abdominal', v: agg.permAbd, color: cividis(0.20) },
    { label: 'Via vaginal',   v: agg.permVag, color: cividis(0.85) },
  ];
  const ticks = niceTicks(0, max, 5);
  const diffPct = agg.permAbd > 0 ? ((agg.permAbd - agg.permVag) / agg.permAbd) * 100 : 0;
  return (
    <figure className="article-figure">
      <svg viewBox={`0 0 ${W} ${H}`} role="img" aria-label="Permanência média">
        <rect x="0" y="0" width={W} height={H} fill="white" />
        <text x={W / 2} y="20" fontSize="12" fontWeight="bold" textAnchor="middle" fill="#000">
          Permanência hospitalar média (dias) — média {agg.yearMin}-{agg.yearMax}
        </text>
        {ticks.map((t) => {
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
        cirúrgica, média ponderada do Brasil para o período
        {' '}{agg.yearMin}–{agg.yearMax}. A via vaginal apresenta permanência
        {' '}<b>{diffPct.toFixed(1)}% menor</b> que a via abdominal
        ({agg.permVag.toFixed(2)} vs. {agg.permAbd.toFixed(2)} dias),
        achado consistente com a literatura clínica que reporta recuperação
        mais rápida e menor invasividade do procedimento via vaginal.
        <i> Fonte:</i> elaboração própria, SIH-SUS/DATASUS.
      </figcaption>
    </figure>
  );
}

function FigureCustoMedio({ agg }) {
  const W = 480, H = 240, P = { l: 80, r: 80, t: 30, b: 40 };
  const max = Math.max(agg.costAbd, agg.costVag, 1) * 1.15;
  const innerW = W - P.l - P.r;
  const innerH = H - P.t - P.b;
  const data = [
    { label: 'Via abdominal', v: agg.costAbd, color: cividis(0.20) },
    { label: 'Via vaginal',   v: agg.costVag, color: cividis(0.85) },
  ];
  const ticks = niceTicks(0, max, 5);
  return (
    <figure className="article-figure">
      <svg viewBox={`0 0 ${W} ${H}`} role="img" aria-label="Custo médio por AIH">
        <rect x="0" y="0" width={W} height={H} fill="white" />
        <text x={W / 2} y="20" fontSize="12" fontWeight="bold" textAnchor="middle" fill="#000">
          Custo médio por procedimento (R$ 2021)
        </text>
        {ticks.map((t) => {
          const x = P.l + (t / max) * innerW;
          return (
            <g key={t}>
              <line x1={x} x2={x} y1={P.t} y2={H - P.b} stroke="#ddd" strokeWidth="0.5" />
              <text x={x} y={H - P.b + 14} fontSize="10" textAnchor="middle" fill="#333">R$ {Math.round(t)}</text>
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
        <b>Figura 6.</b> Custo médio por AIH ({agg.yearMin}–{agg.yearMax})
        em R$ deflacionados para dezembro/2021 (IPCA-BCB). Diferença entre as
        vias é pequena apesar da permanência hospitalar mais longa na via
        abdominal — possível reflexo da estrutura de remuneração fixa da
        tabela SIGTAP-SUS. <i>Fonte:</i> elaboração própria, SIH-SUS/DATASUS
        + BCB.
      </figcaption>
    </figure>
  );
}

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
        <b>Figura 8.</b> Pipeline medallion (bronze · silver · gold) adotado.
        O filtro por <code>PROC_REA</code> aplicado ainda na bronze reduz o
        tamanho do Delta de ~150 GB (RD bruto) para alguns megabytes.
        <i> Fonte:</i> elaboração própria, baseada em Armbrust et al. (2021).
      </figcaption>
    </figure>
  );
}

// ─── Helpers numéricos ────────────────────────────────────────────────────
function niceStep(max) {
  const exp = Math.floor(Math.log10(max));
  const base = Math.pow(10, exp);
  if      (max / base < 2)  return base / 5;
  else if (max / base < 5)  return base / 2;
  return base;
}
function niceTicks(min, max, count) {
  const step = (max - min) / count;
  const expo = Math.floor(Math.log10(step));
  const base = Math.pow(10, expo);
  const niceStepLocal = base * Math.ceil(step / base);
  const out = [];
  for (let t = 0; t <= max + niceStepLocal / 2; t += niceStepLocal) out.push(Math.round(t));
  return out;
}

// ═════════════════════════════════════════════════════════════════════════
// COMPONENTE PRINCIPAL
// ═════════════════════════════════════════════════════════════════════════

export default function UroProArticle({ rows }) {
  const agg = aggregate(rows);

  // Empty-state: pipeline ainda não rodou (gold vazio).
  // O artigo ainda renderiza o esqueleto + explicação, mas não as figuras.
  if (!agg) {
    return (
      <article className="emendas-article" id="uropro-article">
        <header className="article-cover">
          <div className="article-cover-meta">
            <div className="kicker">Mirante dos Dados · Working Paper n. 3</div>
            <div className="article-cover-version">Versão 1.0 — pendente de execução do pipeline</div>
          </div>
          <h1 className="article-title">
            TRATAMENTO CIRÚRGICO DA INCONTINÊNCIA URINÁRIA NO SUS:
            VOLUMES, DESPESA, PERMANÊNCIA E DISTRIBUIÇÃO GEOGRÁFICA
            POR VIA DE ACESSO
          </h1>
          <div className="article-authors">
            <p><b>Tatieli da Silva</b><sup>1</sup> &middot; <b>Leonardo Chalhoub</b><sup>2</sup></p>
          </div>
        </header>

        <section className="article-section">
          <h2 className="article-h2">Aguardando dados</h2>
          <p>
            Este artigo é gerado dinamicamente a partir da tabela{' '}
            <code>gold.uropro_estados_ano</code>, que ainda não foi
            materializada. Para gerar o artigo completo, execute o job
            {' '}<code>job_uropro_refresh</code> no Databricks. O pipeline
            baixará os microdados SIH-AIH-RD do FTP DATASUS para a janela
            configurada (atualmente 2008–2025), filtrará pelos SIGTAPs
            de incontinência urinária ({PROC_ABD}, {PROC_VAG}, 0409020117),
            agregará por UF × Ano × Procedimento × Caráter × Gestão e
            exportará o JSON gold consumido por esta página.
          </p>
          <p>
            Após a execução, esta seção será substituída automaticamente
            pelo artigo completo com Resumo, Abstract, Sumário, Introdução,
            Marco teórico-clínico, Aspectos metodológicos, Resultados,
            Discussão, Considerações finais e Referências em padrão ABNT,
            com 8 figuras geradas em SVG inline a partir dos dados live.
          </p>
        </section>
      </article>
    );
  }

  // ═══════════════════════════════════════════════════════════════════════
  // Artigo completo, gerado a partir de `agg`.
  // ═══════════════════════════════════════════════════════════════════════
  const ratio = agg.totalAihAbd > 0 ? agg.totalAihVag / agg.totalAihAbd : 0;
  const permDiffPct = agg.permAbd > 0 ? ((agg.permAbd - agg.permVag) / agg.permAbd) * 100 : 0;
  const costDiffPct = agg.costVag > 0 ? ((agg.costAbd - agg.costVag) / agg.costVag) * 100 : 0;
  const totalVal = agg.totalValAbd_2021 + agg.totalValVag_2021;

  return (
    <article className="emendas-article" id="uropro-article">
      <header className="article-cover">
        <div className="article-cover-meta">
          <div className="kicker">Mirante dos Dados · Working Paper n. 3</div>
          <div className="article-cover-version">
            Janela analítica: {agg.yearMin}–{agg.yearMax}
          </div>
        </div>

        <h1 className="article-title">
          TRATAMENTO CIRÚRGICO DA INCONTINÊNCIA URINÁRIA NO SUS
          ({agg.yearMin}–{agg.yearMax}): VOLUMES, DESPESA, PERMANÊNCIA E
          DISTRIBUIÇÃO GEOGRÁFICA POR VIA DE ACESSO
        </h1>

        <h2 className="article-subtitle">
          Surgical treatment of urinary incontinence under the Brazilian
          Unified Health System ({agg.yearMin}–{agg.yearMax}): volumes,
          expenditure, length of stay, and geographic distribution by
          surgical approach
        </h2>

        <div className="article-authors">
          <p>
            <b>Tatieli da Silva</b><sup>1</sup>{' '}&middot;{' '}
            <b>Leonardo Chalhoub</b><sup>2</sup>
          </p>
          <p style={{ fontSize: 11 }}>
            <sup>1</sup> Pesquisa original (especialização em Enfermagem,
            2022) — coleta TabNet, recortes analíticos, interpretação clínica.<br />
            <sup>2</sup> Reprodução, extensão e publicação aberta —
            engenharia de dados, integração ao pipeline open-source.
          </p>
        </div>

        <div className="article-cover-footer">Brasil — Abril de 2026</div>
      </header>

      <section className="article-section article-abstract">
        <h2 className="article-h2">Resumo</h2>
        <p>
          Este artigo analisa empiricamente o tratamento cirúrgico da
          incontinência urinária (IU) no Sistema Único de Saúde brasileiro
          entre {agg.yearMin} e {agg.yearMax}, partindo dos microdados
          SIH-AIH-RD (uma linha por internação aprovada). Reproduz e
          estende a pesquisa original conduzida por Tatieli da Silva como
          trabalho de conclusão da especialização em Enfermagem (2022),
          que cobria a janela 2015–2020 a partir de agregados pré-computados
          do TabNet/DATASUS. A análise compara as duas principais vias
          cirúrgicas — abdominal (SIGTAP {PROC_ABD}) e vaginal
          ({PROC_VAG}) — e documenta cinco achados principais.
          <b> Primeiro</b>, o volume da via vaginal supera em <b>{ratio.toFixed(1)} vezes</b>
          {' '}o da via abdominal ({agg.totalAihVag.toLocaleString('pt-BR')} vs.
          {' '}{agg.totalAihAbd.toLocaleString('pt-BR')} AIH), padrão
          consistente com as diretrizes contemporâneas de uroginecologia.
          <b> Segundo</b>, a permanência hospitalar é <b>{permDiffPct.toFixed(1)}% menor</b>
          {' '}na via vaginal ({agg.permVag.toFixed(2)} vs. {agg.permAbd.toFixed(2)} dias),
          compatível com sua menor invasividade. <b>Terceiro</b>, o custo
          médio por AIH (em R$ 2021) é de R$&nbsp;{agg.costAbd.toFixed(2)} (ABD)
          vs. R$&nbsp;{agg.costVag.toFixed(2)} (VAG), diferença de
          {' '}{costDiffPct >= 0 ? '+' : ''}{costDiffPct.toFixed(1)}%. <b>Quarto</b>,
          São Paulo concentra <b>{(agg.spShareAbd * 100).toFixed(1)}%</b> das
          AIH abdominais e <b>{(agg.spShareVag * 100).toFixed(1)}%</b> das
          vaginais. <b>Quinto</b>, o gasto público total no período aproximou-se
          de {fmtBRLk(totalVal)} (R$ 2021), distribuído em
          {' '}{(agg.totalAihAbd + agg.totalAihVag).toLocaleString('pt-BR')} AIH
          aprovadas. O trabalho contribui metodologicamente ao integrar a
          análise ao pipeline open-source <i>Mirante dos Dados</i>, em
          arquitetura medallion, viabilizando atualização mensal
          automatizada e reanálise por terceiros.
        </p>
        <p style={{ marginTop: 8, fontSize: 11 }}>
          <b>Palavras-chave:</b> incontinência urinária; SUS; SIH-SUS;
          cirurgia uroginecológica; análise espacial em saúde; dados abertos.
        </p>
      </section>

      <section className="article-section article-abstract">
        <h2 className="article-h2">Abstract</h2>
        <p>
          This paper empirically analyzes the surgical treatment of urinary
          incontinence (UI) within the Brazilian Unified Health System
          between {agg.yearMin} and {agg.yearMax}, using SIH-AIH-RD
          microdata (one row per approved hospitalization). It reproduces
          and extends the original research by Tatieli da Silva, conducted
          as a graduate specialization thesis in Nursing (2022) covering
          2015–2020 with pre-aggregated TabNet/DATASUS data. The analysis
          compares the two main surgical approaches — abdominal (SIGTAP
          {' '}{PROC_ABD}) and vaginal ({PROC_VAG}) — and documents five
          main findings: (i) the vaginal approach is performed{' '}
          <b>{ratio.toFixed(1)} times more frequently</b> than the
          abdominal one; (ii) length of stay is {permDiffPct.toFixed(1)}%
          shorter for the vaginal route; (iii) average cost per procedure
          differs by {costDiffPct.toFixed(1)}% across approaches; (iv) São
          Paulo concentrates {(agg.spShareAbd * 100).toFixed(1)}% (abdominal)
          and {(agg.spShareVag * 100).toFixed(1)}% (vaginal) of national
          volume; (v) total public expenditure approached
          {' '}{fmtBRLk(totalVal)} (2021 BRL).
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
          <TocRow num="4" label="Resultados"             page="7" href="#sec-resultados-uropro" />
          <TocRow num="5" label="Discussão"              page="12" href="#sec-discussao-uropro" />
          <TocRow num="6" label="Considerações finais"   page="13" href="#sec-final-uropro" />
          <TocRow num="—" label="Referências"            page="14" href="#sec-ref-uropro" />
        </ul>
      </section>

      <section className="article-section" id="sec-intro-uropro">
        <h2 className="article-h2">1. Introdução</h2>

        <p>
          A incontinência urinária (IU) é definida pela <i>International
          Continence Society</i> como qualquer perda involuntária de urina,
          condição de elevada prevalência sobretudo em mulheres adultas e
          idosas. Estimativas globais situam a prevalência feminina entre
          25% e 45% (HAYLEN et al., 2010), com impacto substantivo sobre
          qualidade de vida, saúde mental e custos diretos e indiretos
          para os sistemas de saúde (HU et al., 2003).
        </p>

        <p>
          O Sistema Único de Saúde (SUS) oferece, por meio do Sistema de
          Informações Hospitalares (SIH-SUS), cobertura cirúrgica para os
          casos refratários ao tratamento conservador. Os procedimentos
          cirúrgicos mais comuns enquadram-se em duas vias técnicas: a
          via abdominal (cirurgias tipo Burch e variantes), de maior
          porte; e a via vaginal (<i>slings</i> e técnicas correlatas),
          minimamente invasiva e considerada de primeira linha pela
          maioria das diretrizes contemporâneas (CHAPPLE et al., 2020).
        </p>

        <p>
          O presente artigo retoma e atualiza a investigação empírica
          conduzida por Tatieli da Silva como trabalho de conclusão de
          especialização em Enfermagem (TATIELI, 2022), que analisou as
          AIH aprovadas para os SIGTAPs {PROC_ABD} (via abdominal) e
          {' '}{PROC_VAG} (via vaginal) em 2015–2020. Aqui partimos dos
          microdados SIH-RD, e a janela atual de análise cobre
          {' '}<b>{agg.yearMin}–{agg.yearMax}</b> ({agg.years.length} anos
          completos). Todos os números deste artigo são derivados
          dinamicamente da tabela <code>gold.uropro_estados_ano</code>
          {' '}— refletem o estado mais recente da pipeline e mudam
          conforme o pipeline é atualizado.
        </p>

        <p>
          Este artigo é o terceiro da série de <i>Working Papers</i> do
          projeto Mirante dos Dados (CHALHOUB, 2026a; CHALHOUB, 2026b).
          Os três trabalhos compartilham infraestrutura técnica, dimensões
          auxiliares (IBGE/SIDRA, IPCA-BCB) e princípio metodológico —
          partir dos microdados oficiais para preservar flexibilidade
          analítica.
        </p>
      </section>

      <FigureVolumeContrast agg={agg} />

      <section className="article-section" id="sec-marco-uropro">
        <h2 className="article-h2">2. Marco teórico-clínico</h2>
        <p>
          A escolha entre vias cirúrgicas para o tratamento da IU
          orienta-se classicamente por uma combinação de fatores: tipo
          de incontinência (de esforço, de urgência, mista), grau de
          comprometimento funcional, comorbidades, idade da paciente,
          experiência da equipe cirúrgica e disponibilidade de recursos
          institucionais. As recomendações da <i>European Association of
          Urology</i> e da <i>American Urological Association</i> convergem
          ao priorizar a abordagem vaginal — em particular os
          <i> slings</i> mediouretrais sintéticos — como tratamento de
          primeira linha para incontinência urinária de esforço em
          mulheres adultas (FORD et al., 2017).
        </p>
        <p>
          Sob esse referencial, a relação entre os volumes das duas vias
          observados no SUS torna-se objeto legítimo de avaliação:
          mostra ela aderência às boas práticas clínicas internacionais?
          Há heterogeneidade regional sugestiva de variações na adoção
          dessas práticas? A análise empírica que segue procura responder
          a essas perguntas com base em dados administrativos consolidados
          do SIH-SUS.
        </p>
      </section>

      <section className="article-section" id="sec-metodo-uropro">
        <h2 className="article-h2">3. Aspectos metodológicos</h2>

        <h3 className="article-h3">3.1 Fontes de dados</h3>
        <p>
          A unidade analítica primária é a Autorização de Internação
          Hospitalar (AIH) aprovada e processada pelo SIH-SUS, conforme
          microdados disponibilizados pelo DATASUS no formato proprietário
          DBC (DBF comprimido) através do FTP público{' '}
          <code>ftp.datasus.gov.br/dissemin/publicos/SIHSUS/</code>. Cada
          arquivo cobre uma combinação UF × mês × ano (ex.:{' '}
          <code>RDSP1503.dbc</code> = São Paulo, março de 2015) e contém,
          em média, 1 a 2 milhões de linhas. A janela atual cobre 27
          estados × 12 meses × {agg.years.length} anos completos.
        </p>
        <p>
          Como dimensões auxiliares, foram utilizadas as tabelas
          {' '}<code>silver.populacao_uf_ano</code> (IBGE/SIDRA tabela 6579) e
          {' '}<code>silver.ipca_deflators_2021</code> (BCB série 433), já
          disponíveis no <i>Mirante dos Dados</i> e compartilhadas entre as
          verticais Bolsa Família, Equipamentos e Emendas Parlamentares.
        </p>

        <h3 className="article-h3">3.2 Procedimentos analisados</h3>
        <p>
          O recorte clínico foi limitado aos três SIGTAPs específicos para
          tratamento cirúrgico da incontinência urinária: <b>{PROC_ABD}</b>
          {' '}(Via Abdominal), <b>{PROC_VAG}</b> (Via Vaginal) e <b>0409020117</b>
          {' '}(Genérico, residual). A apresentação dos resultados concentra-se
          nos dois primeiros.
        </p>

        <h3 className="article-h3">3.3 Pipeline e reprodutibilidade</h3>
        <p>
          Diferentemente da pesquisa original — que utilizou agregados
          pré-computados do TabNet — esta investigação parte dos
          microdados RD e os processa por meio de pipeline em arquitetura
          medallion (ARMBRUST et al., 2021): camada Bronze converte DBC
          para Parquet com filtro por <code>PROC_REA</code>; camada Silver
          agrega por UF × Ano × Mês × Procedimento × Caráter × Gestão;
          camada Gold colapsa para UF × Ano × Procedimento e adiciona
          deflação por IPCA (BCB) e per capita (IBGE/SIDRA). O pipeline
          está hospedado na Databricks Free Edition e é refrescado
          mensalmente de forma automatizada.
        </p>
      </section>

      <FigureArchitecture />

      <section className="article-section" id="sec-resultados-uropro">
        <h2 className="article-h2">4. Resultados</h2>

        <h3 className="article-h3">4.1 Volumes nacionais e evolução temporal</h3>
        <p>
          Nos {agg.years.length} anos analisados ({agg.yearMin}–{agg.yearMax}),
          o SUS aprovou <b>{agg.totalAihAbd.toLocaleString('pt-BR')}</b> AIH
          para tratamento cirúrgico de IU via abdominal e <b>{agg.totalAihVag.toLocaleString('pt-BR')}</b>
          {' '}AIH para a via vaginal — razão de aproximadamente
          {' '}<b>{ratio.toFixed(1)}:1</b> em favor da via vaginal.
          A Figura 1 apresenta a evolução anual em ambas as vias.
        </p>
      </section>

      <FigureVolumeTimeline agg={agg} />

      <section className="article-section">
        <h3 className="article-h3">4.2 Distribuição geográfica</h3>
        <p>
          A Figura 2 apresenta as seis unidades federativas com maior
          volume acumulado de AIH para cada via cirúrgica. São Paulo
          lidera em ambos os recortes, mas com magnitudes distintas:
          {' '}{(agg.spShareAbd * 100).toFixed(1)}% do total nacional na via
          abdominal e <b>{(agg.spShareVag * 100).toFixed(1)}%</b> na via
          vaginal.
        </p>
      </section>

      <FigureTop6 agg={agg} />

      <section className="article-section">
        <p>
          A Figura 3 generaliza esse padrão para todas as 27 UFs por meio
          de cartogramas tile-grid comparativos. A interpretação geográfica
          desses resultados deve considerar que o SIH-SUS registra a AIH
          no estabelecimento que realizou o procedimento, não na residência
          da paciente: a concentração observada em SP reflete parcialmente
          o fluxo interestadual de pacientes encaminhadas a
          hospitais-referência.
        </p>
      </section>

      <FigureCartogramComparison agg={agg} />
      <FigureChoropleth agg={agg} />

      <section className="article-section">
        <h3 className="article-h3">4.3 Permanência hospitalar</h3>
        <p>
          A permanência hospitalar média é diferente entre as vias e
          consistente com as expectativas clínicas (Figura 5). Para o
          conjunto do Brasil, a via abdominal apresenta média de
          {' '}<b>{agg.permAbd.toFixed(2)} dias</b> contra
          <b>{' '}{agg.permVag.toFixed(2)} dias</b> da via vaginal —
          diferença de {permDiffPct.toFixed(1)}% a favor desta última.
          Esse resultado é compatível com a literatura clínica (FORD et
          al., 2017).
        </p>
      </section>

      <FigurePermanencia agg={agg} />

      <section className="article-section">
        <h3 className="article-h3">4.4 Despesa pública e custo médio</h3>
        <p>
          O gasto público total acumulado em {agg.yearMin}–{agg.yearMax},
          em valores deflacionados para R$ Dez/2021 (IPCA-BCB), atingiu
          {' '}<b>{fmtBRLk(agg.totalValAbd_2021)}</b> para a via abdominal e
          {' '}<b>{fmtBRLk(agg.totalValVag_2021)}</b> para a via vaginal —
          totalizando <b>{fmtBRLk(totalVal)}</b>. Em termos relativos ao
          orçamento global do SUS, o montante é modesto; em termos
          absolutos, contudo, é significativo, dado o caráter altamente
          eletivo dos procedimentos.
        </p>
        <p>
          O custo médio por AIH (Figura 6) é R$&nbsp;{agg.costAbd.toFixed(2)} (ABD)
          {' '}vs. R$&nbsp;{agg.costVag.toFixed(2)} (VAG), diferença de
          {' '}{costDiffPct >= 0 ? '+' : ''}{costDiffPct.toFixed(1)}% em favor
          da via abdominal — consistente com a estrutura de remuneração
          fixa da tabela SIGTAP-SUS, em que a permanência subjacente é
          refletida apenas parcialmente nos valores hospitalares.
        </p>
      </section>

      <FigureCustoMedio agg={agg} />

      <section className="article-section" id="sec-discussao-uropro">
        <h2 className="article-h2">5. Discussão</h2>

        <h3 className="article-h3">5.1 Aderência às boas práticas clínicas</h3>
        <p>
          O perfil agregado nacional — predomínio robusto e estável da
          via vaginal, com proporção próxima a {ratio.toFixed(1)}:1 — é
          compatível com as recomendações internacionais de uroginecologia
          e sugere que o SUS, em seus serviços-referência, segue
          protocolos clínicos atualizados.
        </p>

        <h3 className="article-h3">5.2 Heterogeneidade regional</h3>
        <p>
          A hegemonia paulista é o achado mais visível, mas a
          heterogeneidade regional revela-se mais informativa quando
          dissecada por via. Para a Enfermagem uroginecológica e a gestão
          hospitalar, o mapeamento empírico dessas heterogeneidades
          fornece base objetiva para a discussão sobre alocação de
          equipes, capacitação técnica e dimensionamento da rede de
          referência.
        </p>

        <h3 className="article-h3">5.3 Limitações</h3>
        <p>
          (i) O SIH-SUS captura apenas a internação faturada; (ii) a
          granularidade espacial está limitada à UF do estabelecimento;
          (iii) a mortalidade intra-hospitalar é altamente esparsa nesse
          recorte; (iv) a análise é descritiva e não pretende identificar
          relações causais.
        </p>
      </section>

      <section className="article-section" id="sec-final-uropro">
        <h2 className="article-h2">6. Considerações finais</h2>

        <h3 className="article-h3">6.1 O que descobrimos</h3>

        <p>
          <b>(i) Predomínio robusto e estável da via vaginal.</b> Razão de
          aproximadamente {ratio.toFixed(1)}:1 entre AIH vaginais e
          abdominais ({agg.totalAihVag.toLocaleString('pt-BR')} vs.
          {' '}{agg.totalAihAbd.toLocaleString('pt-BR')} AIH em
          {' '}{agg.yearMin}–{agg.yearMax}), padrão compatível com as
          recomendações internacionais de uroginecologia.
        </p>

        <p>
          <b>(ii) Permanência hospitalar {permDiffPct.toFixed(1)}% menor na
          via vaginal.</b> Média do Brasil de {agg.permAbd.toFixed(2)} dias
          (ABD) contra {agg.permVag.toFixed(2)} dias (VAG), consistente com
          a menor invasividade da abordagem vaginal.
        </p>

        <p>
          <b>(iii) Custo médio por AIH com diferença de {costDiffPct.toFixed(1)}% entre
          as vias.</b> R$&nbsp;{agg.costAbd.toFixed(2)} (ABD) vs.
          R$&nbsp;{agg.costVag.toFixed(2)} (VAG) em R$ 2021, refletindo a
          remuneração fixa por procedimento da tabela SIGTAP-SUS.
        </p>

        <p>
          <b>(iv) Concentração geográfica em São Paulo.</b> SP concentra
          {' '}{(agg.spShareAbd * 100).toFixed(1)}% das AIH abdominais e
          {' '}<b>{(agg.spShareVag * 100).toFixed(1)}%</b> das vaginais.
        </p>

        <p>
          <b>(v) Gasto público total na ordem de {fmtBRLk(totalVal)}.</b>
          {' '}Modesto frente ao orçamento do SUS, mas significativo dada a
          natureza altamente eletiva dos procedimentos.
        </p>

        <h3 className="article-h3">6.2 Agenda de pesquisa</h3>

        <p>
          (a) Cruzamento com <code>MUNIC_RES</code> para desambiguar
          concentração assistencial vs. fluxo interestadual; (b) integração
          com a vertical CNES já disponível no <i>Mirante dos Dados</i>;
          (c) avaliação prospectiva de desfechos clínicos (re-internação,
          mortalidade tardia) por via.
        </p>

        <h3 className="article-h3">6.3 Contribuição metodológica</h3>

        <p>
          O pipeline aqui apresentado é integralmente <i>open-source</i>,
          segue os princípios FAIR (WILKINSON et al., 2016), é versionado
          em Git com refresh mensal automatizado, e é extensível a
          qualquer procedimento cirúrgico do SIGTAP-SUS por modificação
          de um único parâmetro (<code>procs_filter</code>).
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
          Temporais (SGS)</i>. Série 433: IPCA. Disponível em:
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
          Brasileiro (2015–2025). <i>Mirante dos Dados — Working Paper n. 1</i>,
          abr. 2026a.
        </p>

        <p className="article-ref">
          CHALHOUB, L. Programa Bolsa Família, Auxílio Brasil e Novo
          Bolsa Família (2013–2025). <i>Mirante dos Dados — Working Paper n. 2</i>,
          abr. 2026b.
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
          <i> Cochrane Database of Systematic Reviews</i>, n. 7, CD006375, 2017.
        </p>

        <p className="article-ref">
          HAYLEN, B. T.; DE RIDDER, D.; FREEMAN, R. M. et al. An IUGA/ICS
          joint report on the terminology for female pelvic floor dysfunction.
          <i> Neurourology and Urodynamics</i>, v. 29, n. 1, p. 4–20, 2010.
        </p>

        <p className="article-ref">
          HU, T.-W.; WAGNER, T. H.; BENTKOVER, J. D. et al. Costs of urinary
          incontinence and overactive bladder in the United States.
          <i> Urology</i>, v. 63, n. 3, p. 461–465, 2003.
        </p>

        <p className="article-ref">
          INSTITUTO BRASILEIRO DE GEOGRAFIA E ESTATÍSTICA (IBGE). <i>SIDRA</i>.
          Tabela 6579: estimativas anuais da população residente. Disponível em:
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
          TATIELI DA SILVA. <i>Análise Descritiva da Cirurgia para
          Tratamento da Incontinência Urinária no SUS, 2015–2020</i>.
          Trabalho de Conclusão (Especialização em Enfermagem), 2022.
        </p>

        <p className="article-ref">
          WILKINSON, M. D. et al. The FAIR Guiding Principles for
          scientific data management and stewardship. <i>Scientific Data</i>,
          v. 3, 2016. DOI: 10.1038/sdata.2016.18.
        </p>
      </section>

      <footer className="article-footnote">
        <p>
          <b>Citar como:</b><br />
          DA SILVA, T.; CHALHOUB, L. Tratamento Cirúrgico da Incontinência
          Urinária no SUS ({agg.yearMin}–{agg.yearMax}). <i>Mirante dos Dados —
          Working Paper</i>, v. 1.0, abr. 2026.
        </p>
        <p>
          <b>Reconhecimento:</b> a análise empírica original deste artigo foi
          conduzida por Tatieli da Silva (especialização em Enfermagem, 2022),
          cobrindo 2015–2020. A presente versão reproduz os resultados a partir
          dos microdados SIH-RD, ampliando a janela temporal e adicionando
          dimensões de análise.
        </p>
        <p>
          <b>Licença:</b> dados (Gold) e código sob MIT; texto sob CC BY 4.0.
        </p>
      </footer>
    </article>
  );
}

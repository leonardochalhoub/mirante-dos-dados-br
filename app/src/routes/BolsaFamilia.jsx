// Vertical: Bolsa Família.
// Source: /data/gold/gold_pbf_estados_df.json
// Schema row: { Ano, uf, n_benef, valor_nominal, valor_2021, populacao, pbfPerBenef, pbfPerCapita }
//
// Aggregation rule (matches original getPBFData/app.js):
//   - For totals (n_benef, valor_*) → sum across UFs.
//   - For ratio metrics (pbfPerCapita, pbfPerBenef) → sum(valor_2021 * 1e9) / sum(denom),
//     NOT a weighted average of the per-UF ratio. This yields the true Brasil-wide ratio.

import { useEffect, useMemo, useState } from 'react';
import PageHeader      from '../components/PageHeader';
import Panel           from '../components/Panel';
import KpiCard         from '../components/KpiCard';
import BrazilMap       from '../components/BrazilMap';
import StateRanking    from '../components/StateRanking';
import EvolutionBar    from '../components/charts/EvolutionBar';
import DownloadActions from '../components/DownloadActions';
import TechBadges      from '../components/TechBadges';
import { useTheme }    from '../hooks/useTheme';
import { loadGold }    from '../lib/data';
import { COLORSCALES } from '../lib/scales';
import { fmtBRL, fmtCompact, fmtDec1, fmtDec2, fmtInt } from '../lib/format';
import { exportToXlsx, exportChartsAsZip } from '../lib/exporters';

const METRICS = {
  pbfPerCapita: {
    label: 'PBF per capita (R$ 2021)',
    short: 'R$/hab',
    yaxisTitle: 'PBF per capita (R$ 2021)',
    fmt: (v) => fmtDec2(v),                 // axis & labels: pure number, no R$ prefix
    fmtRich: (v) => fmtBRL(v),              // tooltip / KPI: with R$
    money: true, isRatio: true, denom: 'populacao',
  },
  pbfPerBenef: {
    label: 'PBF por beneficiário (R$ 2021)',
    short: 'R$/ben',
    yaxisTitle: 'PBF por beneficiário (R$ 2021)',
    fmt: (v) => fmtDec2(v),
    fmtRich: (v) => fmtBRL(v),
    money: true, isRatio: true, denom: 'n_benef',
  },
  valor_2021: {
    label: 'Valor (R$ bi, 2021)',
    short: 'R$ bi',
    yaxisTitle: 'Valor pago (R$ bi, 2021)',
    fmt: (v) => fmtDec2(v),                 // already in billions
    fmtRich: (v) => fmtBRL(v * 1e9, { compact: true }),
    money: true, isRatio: false,
  },
  valor_nominal: {
    label: 'Valor (R$ bi, nominal)',
    short: 'R$ bi',
    yaxisTitle: 'Valor pago (R$ bi, nominal)',
    fmt: (v) => fmtDec2(v),
    fmtRich: (v) => fmtBRL(v * 1e9, { compact: true }),
    money: true, isRatio: false,
  },
  n_benef: {
    label: 'Beneficiários (pessoas)',
    short: 'pessoas',
    yaxisTitle: 'Beneficiários',
    fmt: (v) => fmtCompact(v),
    fmtRich: (v) => fmtInt(v),
    money: false, isRatio: false,
  },
};

const DEFAULT_METRIC = 'pbfPerCapita';
const DEFAULT_COLOR  = 'Cividis';

// ── Aggregation helpers ───────────────────────────────────────────────────

// Compute Brasil-wide value for one (year, metric) using the original app.js rule.
function brazilForYear(rows, metricKey) {
  const m = METRICS[metricKey];
  if (!m.isRatio) return rows.reduce((s, r) => s + (r[metricKey] || 0), 0);
  let num = 0, denom = 0;
  for (const r of rows) {
    const v2021 = r.valor_2021;
    const d     = r[m.denom];
    if (v2021 == null || !Number.isFinite(v2021)) continue;
    if (d == null || !Number.isFinite(d) || d <= 0) continue;
    num   += v2021 * 1e9;  // back to R$
    denom += d;
  }
  return denom > 0 ? num / denom : 0;
}

// Compute UF-level value for a (year, metric). For ratio metrics, recompute from valor_2021/denom
// rather than reading the precomputed per-UF column — keeps numerics consistent with brazilForYear.
function ufValue(row, metricKey) {
  const m = METRICS[metricKey];
  if (!m.isRatio) return row[metricKey] || 0;
  const d = row[m.denom];
  if (d == null || d <= 0) return 0;
  return ((row.valor_2021 || 0) * 1e9) / d;
}

export default function BolsaFamilia() {
  const { theme } = useTheme();
  const [rows, setRows]             = useState(null);
  const [error, setError]           = useState(null);
  const [metricKey, setMetricKey]   = useState(DEFAULT_METRIC);
  const [year, setYear]             = useState('AGG');
  const [colorscale, setColorscale] = useState(DEFAULT_COLOR);

  useEffect(() => {
    loadGold('gold_pbf_estados_df.json')
      .then(setRows)
      .catch((e) => setError(e.message));
  }, []);

  const metric = METRICS[metricKey];

  const years = useMemo(
    () => (rows ? Array.from(new Set(rows.map((r) => r.Ano))).sort() : []),
    [rows],
  );

  // UF map values for the selected year (or weighted aggregate across all years for AGG).
  const filtered = useMemo(() => {
    if (!rows) return [];
    if (year === 'AGG') {
      // For ratio metrics in AGG we aggregate UF-by-UF over all years using the same
      // sum(num)/sum(denom) rule — gives "média ponderada por anos" per UF.
      const byUf = new Map();
      for (const r of rows) {
        const cur = byUf.get(r.uf) || { uf: r.uf, num: 0, denom: 0, sum: 0 };
        if (metric.isRatio) {
          const d = r[metric.denom];
          if (d && Number.isFinite(d) && d > 0) {
            cur.num   += (r.valor_2021 || 0) * 1e9;
            cur.denom += d;
          }
        } else {
          cur.sum += r[metricKey] || 0;
        }
        byUf.set(r.uf, cur);
      }
      return Array.from(byUf.values()).map((d) => ({
        uf: d.uf,
        value: metric.isRatio
          ? (d.denom > 0 ? d.num / d.denom : 0)
          : d.sum,
      }));
    }
    return rows
      .filter((r) => r.Ano === Number(year))
      .map((r) => ({ uf: r.uf, value: ufValue(r, metricKey) }));
  }, [rows, metricKey, year, metric]);

  const ranking = useMemo(
    () => [...filtered].sort((a, b) => b.value - a.value),
    [filtered],
  );

  // ── KPIs reflect the current year selection ────────────────────────────
  const kpis = useMemo(() => {
    if (!rows || years.length === 0) {
      return { y: null, totalBenef: 0, totalValor2021: 0, perBenef: 0, perCapita: 0 };
    }
    const y = year === 'AGG' ? Math.max(...years) : Number(year);
    const yearRows = rows.filter((r) => r.Ano === y);
    return {
      y,
      totalBenef:     yearRows.reduce((s, r) => s + (r.n_benef || 0), 0),
      totalValor2021: yearRows.reduce((s, r) => s + (r.valor_2021 || 0), 0),
      perBenef:       brazilForYear(yearRows, 'pbfPerBenef'),
      perCapita:      brazilForYear(yearRows, 'pbfPerCapita'),
    };
  }, [rows, year, years]);

  // ── Yearly evolution: Brasil-wide value per year for selected metric ────
  const evolutionData = useMemo(() => {
    if (!rows) return [];
    return years.map((y) => ({
      year: String(y),
      value: brazilForYear(rows.filter((r) => r.Ano === y), metricKey),
    }));
  }, [rows, metricKey, years]);

  if (error) return <div className="error-block">Erro ao carregar dados: {error}</div>;
  if (!rows) return <div className="loading-block">Carregando dados…</div>;

  return (
    <>
      <TechBadges />
      <PageHeader
        eyebrow="Vertical · transferências de renda"
        title="Bolsa Família"
        subtitle="Pagamentos, beneficiários e valor real (R$ 2021) por UF e ano. Fontes: Portal da Transparência (CGU), IBGE e BCB."
        right={
          <DownloadActions
            onExportXlsx={() => exportToXlsx('mirante-pbf', { 'pbf_uf_ano': rows })}
            onExportPng={() => exportChartsAsZip('mirante-pbf')}
          />
        }
      />

      <div className="kpiRow" data-export-id="pbf-kpis">
        <KpiCard
          label={`Beneficiários · ${kpis.y ?? '—'}`}
          value={fmtCompact(kpis.totalBenef)}
          sub="soma Brasil"
        />
        <KpiCard
          label={`Valor pago · ${kpis.y ?? '—'}`}
          value={fmtBRL(kpis.totalValor2021 * 1e9, { compact: true })}
          sub="R$ 2021 · acumulado no ano"
          color="#2b6cb0"
        />
        <KpiCard
          label={`Per beneficiário · ${kpis.y ?? '—'}`}
          value={fmtBRL(kpis.perBenef)}
          sub="R$ 2021 / pessoa atendida"
          color="#be185d"
        />
        <KpiCard
          label={`Per capita · ${kpis.y ?? '—'}`}
          value={fmtBRL(kpis.perCapita)}
          sub="R$ 2021 / habitante BR"
          color="#0d9488"
        />
      </div>

      <div className="layout">
        <div className="row row-controls-bar">
          <Panel label="Filtros & dados" sub="CGU · IBGE · BCB">
            <div className="controls">
              <div className="control">
                <label htmlFor="metric">Métrica</label>
                <select id="metric" value={metricKey} onChange={(e) => setMetricKey(e.target.value)}>
                  {Object.entries(METRICS).map(([k, m]) => (
                    <option key={k} value={k}>{m.label}</option>
                  ))}
                </select>
              </div>

              <div className="control">
                <label htmlFor="year">Ano</label>
                <select id="year" value={year} onChange={(e) => setYear(e.target.value)}>
                  <option value="AGG">Acumulado / média 2013–2025</option>
                  {years.map((y) => (<option key={y} value={y}>{y}</option>))}
                </select>
              </div>

              <div className="metaBlock">
                <b>Fonte:</b> Portal da Transparência (CGU): pagamentos PBF, Auxílio Brasil e Novo Bolsa Família.<br />
                <b>População:</b> IBGE/SIDRA tabela 6579.<br />
                <b>Inflação:</b> BCB/SGS série 433 (IPCA), normalizada em dez/2021.
              </div>
            </div>
          </Panel>

          <Panel label="Evolução nacional" sub={metric.label} exportId="pbf-evolucao-nacional">
            <EvolutionBar
              data={evolutionData}
              theme={theme}
              yLabel={metric.yaxisTitle}
              xLabel="Ano"
              format={metric.fmt}
              height={320}
            />
          </Panel>
        </div>

        <div className="row row-ranking-map">
          <Panel label="Ranking por UF" sub={`${metric.label} · ${year === 'AGG' ? 'média ponderada' : year}`} exportId="pbf-ranking-uf">
            <StateRanking
              rows={ranking}
              format={metric.fmtRich}
              accentColor={theme === 'dark' ? '#60a5fa' : '#2b6cb0'}
            />
          </Panel>

          <Panel
            label="Distribuição geográfica"
            exportId="pbf-mapa-uf"
            right={
              <div className="mapControls">
                <label htmlFor="colorscale">Cores</label>
                <select id="colorscale" value={colorscale} onChange={(e) => setColorscale(e.target.value)}>
                  {COLORSCALES.map((c) => (<option key={c.value} value={c.value}>{c.label}</option>))}
                </select>
              </div>
            }
          >
            <BrazilMap
              data={filtered}
              colorscale={colorscale}
              theme={theme}
              hoverFmt={metric.fmtRich}
              unit={metric.short}
            />
          </Panel>
        </div>
      </div>

      <Footer />
    </>
  );
}

function Footer() {
  return (
    <footer className="footer panel" style={{ marginTop: 18 }}>
      <div className="footerSection">
        <div className="footerHeading">Fontes</div>
        <div className="footerSource">
          <a href="https://portaldatransparencia.gov.br/download-de-dados/bolsa-familia-pagamentos" target="_blank" rel="noreferrer">
            Portal da Transparência — Bolsa Família
          </a>
          <span className="footerDesc">jan/2013 – nov/2021 (PBF), nov/2021 – fev/2023 (Auxílio Brasil), mar/2023 em diante (Novo PBF)</span>
        </div>
        <div className="footerSource">
          <a href="https://sidra.ibge.gov.br/tabela/6579" target="_blank" rel="noreferrer">IBGE SIDRA — Tabela 6579</a>
          <span className="footerDesc">População residente estimada por UF</span>
        </div>
        <div className="footerSource">
          <a href="https://api.bcb.gov.br/dados/serie/bcdata.sgs.433/dados?formato=json" target="_blank" rel="noreferrer">BCB SGS — Série 433</a>
          <span className="footerDesc">IPCA mensal · usado pra deflacionar valores em R$ 2021</span>
        </div>
        <div className="footerNote">
          Pipeline: bronze (raw CGU/IBGE/BCB) → silver (clean, typed, dedup) → gold (UF × ano).
          Gold: <code>data/gold/gold_pbf_estados_df.json</code>
        </div>
      </div>

      <div className="footerSection">
        <div className="footerHeading">Notas técnicas</div>
        <div style={{ fontSize: 12, color: 'var(--muted)', lineHeight: 1.7 }}>
          Para métricas <b>per capita</b> e <b>por beneficiário</b>, o agregado Brasil para um ano usa
          <i> Σ(valor_2021 × 10⁹) / Σ(denom)</i>, onde <code>denom</code> é a população (per capita)
          ou o número de beneficiários (per beneficiário). Para <b>valores e contagens</b>, usa <i>soma</i>.
          Valores em R$ 2021 são deflacionados com índice IPCA acumulado por dez/2021.
        </div>
      </div>
    </footer>
  );
}

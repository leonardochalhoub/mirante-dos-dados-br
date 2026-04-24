// Vertical: Saúde · Equipamentos de Ressonância Magnética.
// Source: /data/gold/gold_mri_estados_ano.json
// Schema row: {
//   estado, ano, populacao,
//   cnes_count,           total_mri_avg,           mri_per_capita_scaled,
//   sus_cnes_count,       sus_total_mri_avg,       sus_mri_per_capita_scaled,
//   priv_cnes_count,      priv_total_mri_avg,      priv_mri_per_capita_scaled,
//   mri_per_capita_scale_pow10
// }
// `mri_per_capita_scaled` is already RM per 10^pow10 hab (pow10=6 → RM por milhão).

import { useEffect, useMemo, useState } from 'react';
import PageHeader                    from '../components/PageHeader';
import Panel                         from '../components/Panel';
import KpiCard                       from '../components/KpiCard';
import BrazilMap                     from '../components/BrazilMap';
import StateRanking                  from '../components/StateRanking';
import EvolutionStackedComposed      from '../components/charts/EvolutionStackedComposed';
import DownloadActions               from '../components/DownloadActions';
import TechBadges                    from '../components/TechBadges';
import { useTheme }                  from '../hooks/useTheme';
import { loadGold }                  from '../lib/data';
import { COLORSCALES }               from '../lib/scales';
import { fmtCompact, fmtDec1, fmtInt, fmtPct } from '../lib/format';
import { exportToXlsx, exportChartsAsZip } from '../lib/exporters';

// Pre-renamed accessors so we can swap source schema without touching the rest.
const F = {
  uf:   (r) => r.estado,
  year: (r) => r.ano,
  pop:  (r) => r.populacao || 0,
  total:    (r, setor) => setor === 'sus' ? (r.sus_total_mri_avg || 0)
                       : setor === 'priv' ? (r.priv_total_mri_avg || 0)
                       : (r.total_mri_avg || 0),
  cnes:     (r, setor) => setor === 'sus' ? (r.sus_cnes_count || 0)
                       : setor === 'priv' ? (r.priv_cnes_count || 0)
                       : (r.cnes_count || 0),
  perMillion: (r, setor) => setor === 'sus'  ? (r.sus_mri_per_capita_scaled  || 0)
                          : setor === 'priv' ? (r.priv_mri_per_capita_scaled || 0)
                          : (r.mri_per_capita_scaled || 0),
};

const METRICS = {
  mri_per_million: { label: 'RM por milhão de hab.',       short: 'RM/Mhab',     fmt: fmtDec1, get: (r, s) => F.perMillion(r, s) },
  total_mri:       { label: 'Total de equipamentos',       short: 'equipamentos',fmt: fmtDec1, get: (r, s) => F.total(r, s) },
  cnes:            { label: 'Estabelecimentos com RM',     short: 'estabelec.',  fmt: fmtInt,  get: (r, s) => F.cnes(r, s) },
};

const SETORES = {
  todos: { label: 'Todos',           color: '#1d4ed8', colorDark: '#60a5fa' },
  sus:   { label: 'Público (SUS)',   color: '#1d4ed8', colorDark: '#60a5fa' },
  priv:  { label: 'Privado',         color: '#be185d', colorDark: '#f472b6' },
};

const DEFAULT_METRIC = 'mri_per_million';
const DEFAULT_SETOR  = 'todos';
const DEFAULT_COLOR  = 'Cividis';

// Anos pré-2005 vêm com cobertura CNES muito baixa (sistema ainda em
// implantação) — escondemos pra não distorcer a série visível.
const MIN_YEAR = 2005;

// Brasil-wide aggregation for one year.
//   - total / cnes counts → simple sum across UFs
//   - per-million → recompute as Σ(total) / Σ(pop) * 1e6 (NOT a sum of per-UF ratios)
function brazilForYear(rows, metricKey, setor) {
  if (metricKey === 'mri_per_million') {
    let totEq = 0, totPop = 0;
    for (const r of rows) {
      totEq  += F.total(r, setor);
      totPop += F.pop(r);
    }
    return totPop > 0 ? (totEq / (totPop / 1e6)) : 0;
  }
  return rows.reduce((s, r) => s + METRICS[metricKey].get(r, setor), 0);
}

// UF-level value for one (year, setor, metric).
function ufValue(row, metricKey, setor) {
  return METRICS[metricKey].get(row, setor);
}

export default function SaudeMri() {
  const { theme } = useTheme();
  const [rows, setRows]             = useState(null);
  const [error, setError]           = useState(null);
  const [metricKey, setMetricKey]   = useState(DEFAULT_METRIC);
  const [setor, setSetor]           = useState(DEFAULT_SETOR);
  const [year, setYear]             = useState(null);   // set to last year once data loads
  const [colorscale, setColorscale] = useState(DEFAULT_COLOR);

  useEffect(() => {
    loadGold('gold_mri_estados_ano.json')
      .then((all) => {
        const filtered = all.filter((r) => F.year(r) >= MIN_YEAR);
        setRows(filtered);
        const last = Math.max(...filtered.map(F.year));
        setYear(String(last));     // default to most recent available year
      })
      .catch((e) => setError(e.message));
  }, []);

  const metric = METRICS[metricKey];

  const years = useMemo(
    () => (rows ? Array.from(new Set(rows.map(F.year))).sort() : []),
    [rows],
  );

  // UF-level data for the selected year (or AGG: average across years per UF).
  const filtered = useMemo(() => {
    if (!rows) return [];
    if (year === 'AGG') {
      const byUf = new Map();
      for (const r of rows) {
        const cur = byUf.get(F.uf(r)) || { uf: F.uf(r), totEq: 0, totPop: 0, sumCount: 0, n: 0 };
        if (metricKey === 'mri_per_million') {
          cur.totEq  += F.total(r, setor);
          cur.totPop += F.pop(r);
        } else {
          cur.sumCount += METRICS[metricKey].get(r, setor);
          cur.n        += 1;
        }
        byUf.set(F.uf(r), cur);
      }
      return Array.from(byUf.values()).map((d) => ({
        uf: d.uf,
        value: metricKey === 'mri_per_million'
          ? (d.totPop > 0 ? d.totEq / (d.totPop / 1e6) : 0)
          : (d.n > 0 ? d.sumCount / d.n : 0),
      }));
    }
    return rows
      .filter((r) => F.year(r) === Number(year))
      .map((r) => ({ uf: F.uf(r), value: ufValue(r, metricKey, setor) }));
  }, [rows, metricKey, setor, year]);

  const ranking = useMemo(() => [...filtered].sort((a, b) => b.value - a.value), [filtered]);

  // ── KPIs reflect the currently selected year ────────────────────────────
  const kpis = useMemo(() => {
    if (!rows || years.length === 0) {
      return {
        y: null, total: 0, sus: 0, priv: 0, cnes: 0, susShare: 0, privShare: 0,
        yoySus: null, yoyPriv: null, prevYear: null, ufWithMax: undefined,
      };
    }
    const y = year === 'AGG' ? Math.max(...years) : Number(year);
    const yr = rows.filter((r) => F.year(r) === y);
    const total = yr.reduce((s, r) => s + F.total(r, 'todos'), 0);
    const sus   = yr.reduce((s, r) => s + F.total(r, 'sus'),   0);
    const priv  = yr.reduce((s, r) => s + F.total(r, 'priv'),  0);
    const cnes  = yr.reduce((s, r) => s + F.cnes(r,  'todos'), 0);

    // YoY: compare to (selected year - 1) if it exists in the series
    const prevYear = years.includes(y - 1) ? y - 1 : null;
    let yoySus = null, yoyPriv = null;
    if (prevYear != null) {
      const py = rows.filter((r) => F.year(r) === prevYear);
      const susPrev  = py.reduce((s, r) => s + F.total(r, 'sus'),  0);
      const privPrev = py.reduce((s, r) => s + F.total(r, 'priv'), 0);
      if (susPrev  > 0) yoySus  = (sus  - susPrev)  / susPrev;
      if (privPrev > 0) yoyPriv = (priv - privPrev) / privPrev;
    }

    return {
      y, total, sus, priv, cnes,
      susShare:  total > 0 ? sus  / total : 0,
      privShare: total > 0 ? priv / total : 0,
      yoySus, yoyPriv, prevYear,
      ufWithMax: ranking[0],
    };
  }, [rows, ranking, years, year]);

  // Evolution data shaped for recharts ComposedChart:
  // [{ year, sus, priv, ratio }, ...]
  const evolutionData = useMemo(() => {
    if (!rows) return [];
    return years.map((y) => {
      const yr = rows.filter((r) => F.year(r) === y);
      return {
        year:  String(y),
        sus:   brazilForYear(yr, 'total_mri', 'sus'),
        priv:  brazilForYear(yr, 'total_mri', 'priv'),
        ratio: brazilForYear(yr, 'mri_per_million', setor),
      };
    });
  }, [rows, years, setor]);

  if (error) return <div className="error-block">Erro ao carregar dados: {error}</div>;
  if (!rows) return <div className="loading-block">Carregando dados…</div>;

  const setorLabel = SETORES[setor].label;

  return (
    <>
      <PageHeader
        eyebrow="Vertical · saúde · ressonância magnética"
        title="Infraestrutura de Neuroimagem no Brasil"
        subtitle="Distribuição de equipamentos de Ressonância Magnética por UF — DATASUS/CNES (2005–2025)."
        right={
          <div className="header-right-row">
            <TechBadges />
            <DownloadActions
              onExportXlsx={() => exportToXlsx('mirante-saude-mri', { 'mri_uf_ano': rows })}
              onExportPng={() => exportChartsAsZip('mirante-saude-mri')}
            />
          </div>
        }
      />

      <div className="kpiRow" data-export-id="mri-kpis">
        <KpiCard
          label={`Total RM no Brasil · ${kpis.y ?? '—'}`}
          value={fmtInt(kpis.total)}
          sub="equipamentos"
          color={theme === 'dark' ? '#60a5fa' : '#1d4ed8'}
        />
        <KpiCard
          label={`Equipamentos SUS · ${kpis.y ?? '—'}`}
          value={fmtInt(kpis.sus)}
          sub={`${fmtPct(kpis.susShare)} do total`}
          color={SETORES.sus.color}
        />
        <KpiCard
          label={`Equipamentos privados · ${kpis.y ?? '—'}`}
          value={fmtInt(kpis.priv)}
          sub={`${fmtPct(kpis.privShare)} do total`}
          color={SETORES.priv.color}
        />
        <KpiCard
          label={`Estabelecimentos CNES · ${kpis.y ?? '—'}`}
          value={fmtInt(kpis.cnes)}
          sub="com pelo menos 1 RM"
          color={theme === 'dark' ? '#34d399' : '#059669'}
        />

        {kpis.prevYear != null && (
          <>
            <KpiCard
              label="Cresc. YoY público"
              value={<YoyValue value={kpis.yoySus} />}
              sub={`${kpis.prevYear} → ${kpis.y}`}
              color={theme === 'dark' ? '#34d399' : '#059669'}
            />
            <KpiCard
              label="Cresc. YoY privado"
              value={<YoyValue value={kpis.yoyPriv} sectorTint="priv" />}
              sub={`${kpis.prevYear} → ${kpis.y}`}
              color={SETORES.priv.color}
            />
          </>
        )}
      </div>

      <div className="layout">
        <div className="row row-controls-bar">
          <Panel label="Filtros & dados" sub="DATASUS · IBGE">
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
                <label htmlFor="setor">Setor</label>
                <select id="setor" value={setor} onChange={(e) => setSetor(e.target.value)}>
                  <option value="todos">Todos</option>
                  <option value="sus">Público (SUS)</option>
                  <option value="priv">Privado</option>
                </select>
              </div>

              <div className="control">
                <label htmlFor="year">Ano</label>
                <select id="year" value={year} onChange={(e) => setYear(e.target.value)}>
                  <option value="AGG">Média 2005–2025</option>
                  {years.map((y) => (<option key={y} value={y}>{y}</option>))}
                </select>
              </div>

              <div className="metaBlock">
                <b>Equipamento:</b> Ressonância Magnética (CODEQUIP = 42)<br />
                <b>Período:</b> jan/2005 – dez/2025 (mensal, agregado a média anual)<br />
                <b>SUS:</b> IND_SUS = 1 · <b>Privado:</b> IND_SUS = 0<br />
                <b>Fonte:</b> DATASUS — Cadastro Nacional de Estabelecimentos (CNES/EQ).
              </div>
            </div>
          </Panel>

          <Panel label="Evolução nacional" sub={`Equipamentos · ${setorLabel} + RM por milhão`} exportId="mri-evolucao-nacional">
            <EvolutionStackedComposed
              data={evolutionData}
              setor={setor}
              theme={theme}
              fmtBar={(v) => fmtCompact(v)}
              fmtLine={(v) => fmtDec1(v)}
              yLeftLabel="Equipamentos (média anual)"
              yRightLabel="RM por milhão"
              xLabel="Ano"
              height={340}
            />
          </Panel>
        </div>

        <div className="row row-ranking-map">
          <Panel
            label="Ranking por UF"
            sub={`${metric.label} · ${setorLabel} · ${year === 'AGG' ? 'média' : year}`}
            exportId="mri-ranking-uf"
          >
            <StateRanking
              rows={ranking}
              format={metric.fmt}
              accentColor={
                setor === 'priv'
                  ? (theme === 'dark' ? SETORES.priv.colorDark : SETORES.priv.color)
                  : (theme === 'dark' ? SETORES.sus.colorDark  : SETORES.sus.color)
              }
            />
          </Panel>

          <Panel
            label="Distribuição geográfica"
            exportId="mri-mapa-uf"
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
              hoverFmt={metric.fmt}
              unit={metric.short}
            />
          </Panel>
        </div>
      </div>

      <Footer />
    </>
  );
}

function YoyValue({ value, sectorTint }) {
  if (value == null || !Number.isFinite(value)) return <span className="muted">—</span>;
  const up    = value >= 0;
  const cls   = sectorTint === 'priv' ? 'sector-priv' : (up ? 'up' : 'down');
  const arrow = up ? '▲' : '▼';
  const sign  = up ? '+' : '';
  return (
    <span className={`kpiYoy ${cls}`}>
      <span className="arrow">{arrow}</span>
      <span>{sign}{fmtPct(value)}</span>
    </span>
  );
}

function Footer() {
  return (
    <footer className="footer panel" style={{ marginTop: 18 }}>
      <div className="footerSection">
        <div className="footerHeading">Fontes</div>
        <div className="footerSource">
          <a href="https://datasus.saude.gov.br/transferencia-de-arquivos/" target="_blank" rel="noreferrer">
            DATASUS — CNES/EQ (Equipamentos)
          </a>
          <span className="footerDesc">Cadastro Nacional de Estabelecimentos de Saúde — equipamentos por estabelecimento, mensal, jan/2005 em diante</span>
        </div>
        <div className="footerSource">
          <a href="https://sidra.ibge.gov.br/tabela/6579" target="_blank" rel="noreferrer">
            IBGE SIDRA — Tabela 6579
          </a>
          <span className="footerDesc">População residente estimada por UF (variável 9324)</span>
        </div>
        <div className="footerNote">
          Dados mensais agregados à média anual por CNES, depois somados por UF e separados por <code>IND_SUS</code>.
          <br />Pipeline: bronze (FTP DATASUS) → silver (clean, typed, sectorized) → gold (UF × ano × setor).
        </div>
      </div>

      <div className="footerSection">
        <div className="footerHeading">Notas técnicas</div>
        <div style={{ fontSize: 12, color: 'var(--muted)', lineHeight: 1.7 }}>
          A coluna <code>mri_per_capita_scaled</code> já vem multiplicada por 10⁶ (RM por milhão de hab.).
          Para o Brasil-todo, recomputamos como Σ(equipamentos) / (Σ(pop)/10⁶).
          O split <b>SUS / Privado</b> usa <code>IND_SUS</code> do CNES — alguns estabelecimentos atendem
          ambos; quando isso ocorre, o equipamento é classificado pelo perfil predominante do CNES.
        </div>
      </div>
    </footer>
  );
}

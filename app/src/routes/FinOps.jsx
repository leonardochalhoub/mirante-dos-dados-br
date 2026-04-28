// Vertical: FinOps (Databricks lakehouse spend).
// Source: /data/finops_summary.json (gerado pelo pipeline job_finops_refresh)
//
// "Bronze" desta vertical são as system tables do Databricks
// (system.billing.* + system.lakeflow.*). O JSON consumido aqui já vem com
// KPIs computados — front só renderiza.
//
// Design: smartphone-first, magazine-grade. Editorial framing leva ao
// "headline number" (% wasted) na primeira dobra e segue o ciclo FinOps
// clássico: visibilidade → alocação → otimização.

import { useEffect, useMemo, useState } from 'react';
import {
  AreaChart, Area, BarChart, Bar, PieChart, Pie, Cell, LineChart, Line,
  XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer,
} from 'recharts';
import PageHeader from '../components/PageHeader';
import Panel from '../components/Panel';
import ArticleTimestamp from '../components/ArticleTimestamp';
import { useArticleMeta, articleUrl } from '../hooks/useArticleMeta';
import { useTheme } from '../hooks/useTheme';
import { fmtInt, fmtDec1, fmtDec2 } from '../lib/format';
import { pick } from '../lib/colors';
import { loadStats } from '../lib/data';
import '../styles/finops.css';

const SOURCE_FILE = 'finops_summary.json';

// Format bytes ("42.3 GB" / "256 MB") — used for per-vertical size
function fmtBytes(b) {
  if (b == null || !Number.isFinite(b)) return '—';
  const u = ['B', 'KB', 'MB', 'GB', 'TB'];
  let i = 0; let v = b;
  while (v >= 1024 && i < u.length - 1) { v /= 1024; i += 1; }
  return `${v < 10 ? v.toFixed(1) : Math.round(v)} ${u[i]}`;
}

// ── Formatters ──────────────────────────────────────────────────────────────
const fmtUSD = (v, opts = {}) => {
  if (v == null || Number.isNaN(v)) return '—';
  const { compact = false, dp = 2 } = opts;
  return new Intl.NumberFormat('pt-BR', {
    style: 'currency',
    currency: 'USD',
    notation: compact ? 'compact' : 'standard',
    maximumFractionDigits: dp,
    minimumFractionDigits: dp,
  }).format(v);
};

const fmtUSDCompact = (v) => fmtUSD(v, { compact: true, dp: 1 });

// Localized day-month label for time axis (DD/MMM in pt-BR)
const MONTHS_PT = ['jan', 'fev', 'mar', 'abr', 'mai', 'jun',
                   'jul', 'ago', 'set', 'out', 'nov', 'dez'];
function fmtDayShort(iso) {
  if (!iso) return '';
  const [, m, d] = iso.split('-').map(Number);
  return `${String(d).padStart(2, '0')}/${MONTHS_PT[m - 1]}`;
}
function fmtDayFull(iso) {
  if (!iso) return '';
  const [y, m, d] = iso.split('-').map(Number);
  return `${String(d).padStart(2, '0')}/${MONTHS_PT[m - 1]}/${y}`;
}
function truncate(s, n = 60) {
  if (!s) return '—';
  return s.length > n ? `${s.slice(0, n)}…` : s;
}

// ── Color mappings — only existing palette (primary/pink/amber/teal/emerald/slate)
function outcomeColor(state, theme) {
  switch (state) {
    case 'SUCCEEDED': return pick('emerald',  theme);
    case 'ERROR':     return pick('pink',     theme);
    case 'CANCELLED': return pick('amber',    theme);
    default:          return pick('slate',    theme);
  }
}
function productColor(product, theme) {
  const map = {
    JOBS:                     pick('primary', theme),
    SQL:                      pick('emerald', theme),
    INTERACTIVE:              pick('teal',    theme),
    DLT:                      pick('pink',    theme),
    NETWORKING:               pick('amber',   theme),
    DEFAULT_STORAGE:          pick('slate',   theme),
    PREDICTIVE_OPTIMIZATION:  pick('pink',    theme),
  };
  return map[product] || pick('slate', theme);
}

const PRODUCT_LABEL = {
  JOBS: 'Jobs',
  SQL: 'SQL warehouses',
  INTERACTIVE: 'Clusters interativos',
  DLT: 'DLT pipelines',
  NETWORKING: 'Networking serverless',
  DEFAULT_STORAGE: 'Storage gerenciado',
  PREDICTIVE_OPTIMIZATION: 'Optimization auto.',
};
const OUTCOME_LABEL = {
  SUCCEEDED: 'Bem-sucedidas',
  ERROR:     'Falharam',
  CANCELLED: 'Canceladas',
  UNKNOWN:   'Sem outcome',
};

// ── Page ────────────────────────────────────────────────────────────────────
export default function FinOps() {
  const { theme } = useTheme();
  const [data, setData] = useState(null);
  const [stats, setStats] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    const base = import.meta.env.BASE_URL || '/';
    const url = `${base}data/${SOURCE_FILE}`.replace(/\/{2,}/g, '/');
    fetch(url, { cache: 'no-cache' })
      .then((r) => {
        if (!r.ok) throw new Error(`HTTP ${r.status}`);
        return r.json();
      })
      .then(setData)
      .catch((e) => setError(e.message));
    // Storage attribution depends on per-vertical bronze bytes — load
    // platform_stats. Optional (page renders without it).
    loadStats('platform_stats.json').then(setStats).catch(() => setStats(null));
  }, []);

  if (error) return <div className="finops-error">Erro ao carregar dados FinOps: {error}</div>;
  if (!data) return <div className="finops-loading">Carregando…</div>;

  const k = data.kpis;

  return (
    <div className="finops-page">
      <PageHeader
        eyebrow="FinOps · governança de custo · 100% do histórico"
        title="Quanto custou rodar o Mirante"
        subtitle={
          `Cada DBU consumida e cada centavo em USD desde o primeiro dia da plataforma — ` +
          `${fmtDayFull(data.window.first_day)} a ${fmtDayFull(data.window.last_day)} ` +
          `(${fmtInt(data.window.n_days)} dias, sem lacunas). ` +
          `Bronze: system.billing + system.lakeflow. ` +
          `Custo = Σ DBU × list_price (versionado no tempo).`
        }
      />

      {/* ── Headline hero: the wasted-spend story ─────────────────────────── */}
      <section className="finops-hero">
        <div className="finops-hero-card finops-hero-primary">
          <div className="finops-hero-eyebrow">Custo total · lifetime</div>
          <div className="finops-hero-value">{fmtUSD(k.total_cost_usd_lifetime)}</div>
          <div className="finops-hero-sub">
            {fmtInt(data.window.n_days)} dias contínuos · {fmtDec1(k.total_dbus_lifetime)} DBUs
            consumidas · {fmtInt(k.n_runs_lifetime)} job runs registradas
          </div>
        </div>
        <div className="finops-hero-card finops-hero-warn">
          <div className="finops-hero-eyebrow">Spend desperdiçado · ERROR + CANCELLED</div>
          <div className="finops-hero-value">{fmtDec1(k.wasted_pct_lifetime)}%</div>
          <div className="finops-hero-sub">
            <b>{fmtUSD(k.wasted_cost_usd_lifetime)}</b> em runs que não entregaram resultado.
            DBUs consumidas até o crash ou cancelamento manual.
          </div>
        </div>
      </section>

      {/* ── Quick KPI strip ──────────────────────────────────────────────── */}
      <section className="finops-kpi-strip">
        <Stat label="Últimos 30 dias"     value={fmtUSD(k.total_cost_usd_30d)}
              sub={`Últimos 7 dias: ${fmtUSD(k.total_cost_usd_7d)}`} />
        <Stat label="Custo médio por run" value={fmtUSD(k.avg_cost_per_run_usd)}
              sub={`p95: ${fmtUSD(k.p95_cost_per_run_usd)}`} />
        <Stat label="Chargeable"          value={`${fmtDec1(k.chargeable_share_pct)}%`}
              sub="Código que rodou (jobs, SQL, etc.)" />
        <Stat label="Overhead de plataforma" value={`${fmtDec1(k.overhead_share_pct)}%`}
              sub="Networking + storage + auto-optim." />
      </section>

      {/* ── Editorial pull-quote ─────────────────────────────────────────── */}
      <section className="finops-callout">
        <div className="finops-callout-rule" />
        <div className="finops-callout-body">
          <div className="finops-callout-eyebrow">Por que FinOps importa</div>
          <p>
            Plataformas serverless cobram por uso, não por hora reservada. Cada
            query, cada falha, cada cluster esquecido aceso vira USD na fatura.
            Aqui, <b>{fmtDec1(k.wasted_pct_lifetime)}% do custo de jobs</b> foi
            queimado em runs que falharam ou foram canceladas — DBUs consumidas
            até o crash, sem entregar resultado. Esse é exatamente o tipo de
            custo que o ciclo FinOps clássico — <i>visibility → allocation →
            optimization</i> — ataca primeiro.
          </p>
          {k.most_expensive_run && (
            <p className="finops-callout-pull">
              Run mais cara do histórico: <b>{fmtUSD(k.most_expensive_run.cost_usd)}</b> em{' '}
              <b>{fmtDec1(k.most_expensive_run.billed_minutes)} min</b> —{' '}
              <span style={{ color: outcomeColor(k.most_expensive_run.result_state, theme),
                             fontWeight: 600 }}>
                {OUTCOME_LABEL[k.most_expensive_run.result_state] || k.most_expensive_run.result_state}
              </span>{' '}
              em {fmtDayFull(k.most_expensive_run.day)} ·{' '}
              <span className="finops-callout-job">{truncate(k.most_expensive_run.job_name, 80)}</span>
            </p>
          )}
        </div>
      </section>

      {/* ── Working Paper #8 article block ───────────────────────────────── */}
      <DocCardWP8 />

      {/* ── Cumulative spend over time (the "100% do histórico" headline chart) ── */}
      <Panel
        label="Custo acumulado desde o primeiro dia"
        sub={`USD acumulado dia-a-dia · janela completa de ${fmtInt(data.window.n_days)} dias`}
      >
        <CumulativeSpendChart daily={data.daily} theme={theme} />
      </Panel>

      {/* ── Daily timeseries (área empilhada por workload-class) ─────────── */}
      <Panel
        label="Spend diário ao longo do tempo"
        sub="USD/dia · chargeable (código do usuário) vs overhead (plataforma)"
      >
        <DailySpendArea daily={data.daily} theme={theme} />
      </Panel>

      {/* ── Storage section ──────────────────────────────────────────────── */}
      {data.storage && (
        <StorageSection storage={data.storage} stats={stats} theme={theme} />
      )}

      {/* ── Two-col on desktop, stacked on mobile ────────────────────────── */}
      <div className="finops-twocol">
        <Panel
          label="Pra onde o dinheiro foi"
          sub={`${data.by_product.length} produtos · chargeable ${fmtDec1(k.chargeable_share_pct)}% · overhead ${fmtDec1(k.overhead_share_pct)}%`}
        >
          <ProductDonut byProduct={data.by_product} theme={theme} />
          <ProductLegend byProduct={data.by_product} theme={theme} />
        </Panel>

        <Panel
          label="Quanto custou cada desfecho"
          sub="Falhar custa quase o mesmo que ter sucesso — DBUs queimam até o crash"
        >
          <OutcomeBars byOutcome={data.by_outcome} theme={theme} />
          <OutcomeLegend byOutcome={data.by_outcome} theme={theme} />
        </Panel>
      </div>

      {/* ── Top jobs table ───────────────────────────────────────────────── */}
      <Panel
        label="Jobs mais caros"
        sub={`Top ${data.by_job.length} por custo lifetime — agrupa runs do mesmo job (dev/prod) com split de outcome`}
      >
        <TopJobsTable byJob={data.by_job} theme={theme} />
      </Panel>

      {/* ── Top single runs ──────────────────────────────────────────────── */}
      <Panel
        label={`As ${data.top_runs.length} execuções individuais mais caras`}
        sub="Útil pra investigar spikes, clusters mal-dimensionados, ou jobs que ficaram presos"
      >
        <TopRunsTable topRuns={data.top_runs} theme={theme} />
      </Panel>

      <footer className="finops-footer">
        Gerado em {data.generated_at_utc} · catalog <code>{data.catalog}</code> · {' '}
        pipeline <code>job_finops_refresh</code> (diário 6h UTC)
      </footer>
    </div>
  );
}

// ── Working Paper #8 doc card ───────────────────────────────────────────────
function DocCardWP8() {
  const base       = import.meta.env.BASE_URL || '/';
  const slug       = 'finops-plataforma-dados-publicos';
  const meta       = useArticleMeta(slug);
  const sha        = meta?.tex_last_sha;
  const pdfUrl     = articleUrl(base, slug, 'pdf', sha);
  const texUrl     = articleUrl(base, slug, 'tex', sha);
  const overleafUrl = 'https://www.overleaf.com/docs?snip_uri=' +
    encodeURIComponent(`https://leonardochalhoub.github.io${texUrl}`);
  return (
    <div className="doc-block" style={{ marginBottom: 20 }}>
      <div style={{ display: 'flex', justifyContent: 'space-between',
                    alignItems: 'baseline', flexWrap: 'wrap', gap: 8 }}>
        <div className="kicker">Working Paper n. 8</div>
        <ArticleTimestamp slug={slug} />
      </div>
      <p style={{ marginTop: 6, fontSize: 13.5 }}>
        <b>"Custo real de operar uma plataforma de dados públicos no
        Databricks Free Edition: visibilidade fim-a-fim a partir de
        system tables (junho/2025–abril/2026)"</b> — auditoria de 322 dias
        contínuos, sem lacunas; ledger granular por job-run materializado
        a partir de <code>system.billing.*</code> e
        <code> system.lakeflow.*</code>.
      </p>
      <p style={{ marginTop: 8, fontSize: 13.5, color: 'var(--muted)' }}>
        Achado-chave: <b>53,9% do gasto em jobs foi consumido por runs que
        falharam ou foram canceladas</b> — DBUs queimam até o crash.
        Magnitude próxima ou superior à reportada pela literatura cinza
        FinOps em ambientes empresariais maiores, sugerindo que o ciclo
        <i> visibility → allocation → optimization</i> é estruturalmente
        escala-invariante.
      </p>
      <div className="doc-actions">
        <a className="doc-toggle doc-toggle-primary"
           href={pdfUrl} target="_blank" rel="noreferrer"
           title="Abrir PDF em nova aba">
          📖 Ler artigo (PDF)
        </a>
        <a className="doc-toggle"
           href={pdfUrl} download="Mirante-FinOps-Chalhoub-2026.pdf"
           title="PDF compilado em LaTeX, padrão ABNT">
          ⤓ Baixar PDF (ABNT)
        </a>
        <a className="doc-toggle"
           href={texUrl} download={`${slug}.tex`}
           title="Fonte LaTeX (.tex)">
          ⤓ Baixar fonte (.tex)
        </a>
        <a className="doc-toggle"
           href={overleafUrl} target="_blank" rel="noreferrer"
           title="Compilação online em 1 clique no Overleaf">
          ↗ Abrir no Overleaf
        </a>
      </div>
    </div>
  );
}

// ── Stat (mini KPI card) ────────────────────────────────────────────────────
function Stat({ label, value, sub }) {
  return (
    <div className="finops-stat">
      <div className="finops-stat-label">{label}</div>
      <div className="finops-stat-value">{value}</div>
      {sub && <div className="finops-stat-sub">{sub}</div>}
    </div>
  );
}

// ── Cumulative spend (the headliner — "100% do histórico" auto-adjusts) ────
function CumulativeSpendChart({ daily, theme }) {
  // Reads daily and uses the precomputed cumulative column. Auto-adjusts as
  // new days come in: the rightmost point is always the latest known total.
  const series = useMemo(() => {
    // Trim leading zeros (storage didn't start charging until ~recently)
    const idx = daily.findIndex((d) => (d.cost_total_cumulative || 0) > 0.001);
    return idx >= 0 ? daily.slice(idx) : daily;
  }, [daily]);

  const grid       = theme === 'dark' ? 'rgba(255,255,255,0.08)' : 'rgba(15,23,42,0.06)';
  const tickColor  = theme === 'dark' ? '#94a3b8' : '#475569';
  const cLine      = pick('primary', theme);

  return (
    <div className="finops-chart-tall">
      <ResponsiveContainer>
        <AreaChart data={series} margin={{ top: 16, right: 16, bottom: 24, left: 4 }}>
          <defs>
            <linearGradient id="finops-cum" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%"  stopColor={cLine} stopOpacity={0.45} />
              <stop offset="95%" stopColor={cLine} stopOpacity={0.02} />
            </linearGradient>
          </defs>
          <CartesianGrid stroke={grid} vertical={false} />
          <XAxis dataKey="usage_date" tickFormatter={fmtDayShort}
                 stroke={tickColor} fontSize={10} tickLine={false}
                 axisLine={{ stroke: grid }} interval="preserveStartEnd" minTickGap={36} />
          <YAxis stroke={tickColor} fontSize={11} tickLine={false} axisLine={false}
                 width={56} tickFormatter={(v) => fmtUSDCompact(v)} />
          <Tooltip
            labelFormatter={fmtDayFull}
            formatter={(value) => [fmtUSD(value), 'Acumulado']}
            contentStyle={{
              background: theme === 'dark' ? '#0f172a' : '#fff',
              border: `1px solid ${grid}`, fontSize: 11, borderRadius: 6,
            }}
          />
          <Area type="monotone" dataKey="cost_total_cumulative"
                stroke={cLine} strokeWidth={2.5} fill="url(#finops-cum)" />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
}

// ── Storage section: total spent + run rate + per-vertical attribution ──────
function StorageSection({ storage, stats, theme }) {
  const verticals = stats?.verticals;
  const tables    = stats?.tables;

  // Per-vertical attribution: pro-rate the *current* monthly storage rate by
  // each vertical's bronze bytes share. This gives a back-of-envelope answer
  // to "how much does vertical X cost me to keep stored every month?"
  const verticalsList = useMemo(() => {
    if (!verticals) return null;
    const entries = Object.entries(verticals)
      .filter(([k, v]) => v && v.kind !== 'finops' && (v.delta_bronze_bytes || 0) > 0)
      .map(([k, v]) => ({
        key: k,
        bytes: v.delta_bronze_bytes || 0,
        rows:  v.delta_bronze_rows  || 0,
      }));
    const totalBytes = entries.reduce((s, e) => s + e.bytes, 0);
    return entries
      .map((e) => ({
        ...e,
        share: totalBytes > 0 ? e.bytes / totalBytes : 0,
        usd_per_month: storage.per_month_run_rate * (totalBytes > 0 ? e.bytes / totalBytes : 0),
        usd_per_year:  storage.per_year_run_rate  * (totalBytes > 0 ? e.bytes / totalBytes : 0),
      }))
      .sort((a, b) => b.bytes - a.bytes);
  }, [verticals, storage]);

  // Total bronze bytes across the lakehouse (for headline)
  const totalBronzeBytes = useMemo(() => {
    if (!tables?.bronze) return null;
    return tables.bronze.reduce((s, t) => s + (t.bytes || 0), 0);
  }, [tables]);

  const VERTICAL_LABEL = {
    pbf:                 'Bolsa Família',
    equipamentos:        'Equipamentos médicos',
    'equipamentos-sus':  'Equipamentos SUS',
    emendas:             'Emendas Parlamentares',
    uropro:              'Incontinência urinária',
    rais:                'RAIS',
    'pbf-municipios':    'Bolsa Família · municípios',
  };
  const labelOf = (k) => VERTICAL_LABEL[k] || k.charAt(0).toUpperCase() + k.slice(1).replace(/_/g, ' ');

  return (
    <Panel
      label="Storage acumulado · custo por dia/mês/ano"
      sub={`DEFAULT_STORAGE da Free Edition cobra continuamente — custo cresce mesmo sem rodar nada`}
    >
      <div className="finops-storage-grid">
        <Stat label="Total gasto em storage"
              value={fmtUSD(storage.total_usd_lifetime)}
              sub={`${fmtDec1(storage.share_of_total_pct)}% do custo total · ${fmtInt(storage.days_with_storage)} dias com cobrança`} />
        <Stat label="Custo por dia"
              value={fmtUSD(storage.per_day_current, { dp: 4 })}
              sub={`Média lifetime: ${fmtUSD(storage.per_day_avg_lifetime, { dp: 4 })}/dia`} />
        <Stat label="Run rate mensal"
              value={fmtUSD(storage.per_month_run_rate)}
              sub="Projeção: 30 dias × custo atual" />
        <Stat label="Run rate anual"
              value={fmtUSD(storage.per_year_run_rate)}
              sub="Projeção: 365 dias × custo atual" />
      </div>

      {verticalsList && verticalsList.length > 0 && (
        <>
          <div className="finops-section-rule" />
          <div className="finops-storage-attr-head">
            <div>
              <div className="finops-section-eyebrow">Tamanho de cada vertical</div>
              <div className="finops-section-title">
                Bronze do lakehouse: <b>{fmtBytes(totalBronzeBytes)}</b> totais
              </div>
              <div className="finops-section-sub">
                Storage cost rateado proporcionalmente por bytes em bronze.
                Útil para responder "quanto custa por mês manter X armazenado?"
              </div>
            </div>
          </div>

          <PerVerticalSizeBars verticals={verticalsList} labelOf={labelOf} theme={theme} />

          <div className="finops-table-wrap finops-only-wide">
            <table className="finops-table">
              <thead>
                <tr>
                  <th>Vertical</th>
                  <th className="ar">Bronze (bytes)</th>
                  <th className="ar">Linhas</th>
                  <th className="ar">Share</th>
                  <th className="ar">USD/mês*</th>
                  <th className="ar">USD/ano*</th>
                </tr>
              </thead>
              <tbody>
                {verticalsList.map((v) => (
                  <tr key={v.key}>
                    <td>{labelOf(v.key)}</td>
                    <td className="ar strong">{fmtBytes(v.bytes)}</td>
                    <td className="ar">{fmtInt(v.rows)}</td>
                    <td className="ar">{fmtDec1(v.share * 100)}%</td>
                    <td className="ar">{fmtUSD(v.usd_per_month, { dp: 3 })}</td>
                    <td className="ar">{fmtUSD(v.usd_per_year, { dp: 2 })}</td>
                  </tr>
                ))}
              </tbody>
            </table>
            <div className="finops-footnote">
              * Storage cost rateado pela participação em bytes de bronze.
              Aproximação: o billing real do Databricks não atribui storage por
              schema. Reflete, na prática, "quanto pesa cada vertical na fatura
              mensal de storage".
            </div>
          </div>

          <ul className="finops-cards finops-only-narrow">
            {verticalsList.map((v) => (
              <li key={v.key} className="finops-card">
                <div className="finops-card-head">
                  <span className="finops-card-name">{labelOf(v.key)}</span>
                </div>
                <div className="finops-card-money">
                  <span className="finops-card-cost">{fmtBytes(v.bytes)}</span>
                  <span className="finops-card-runs">{fmtDec1(v.share * 100)}% · {fmtInt(v.rows)} linhas</span>
                </div>
                <div className="finops-card-outcome">
                  <span>{fmtUSD(v.usd_per_month, { dp: 3 })} / mês</span>
                  <span>{fmtUSD(v.usd_per_year, { dp: 2 })} / ano</span>
                </div>
              </li>
            ))}
          </ul>
        </>
      )}
    </Panel>
  );
}

// Horizontal bar chart of per-vertical bronze size (mobile-friendly)
function PerVerticalSizeBars({ verticals, labelOf, theme }) {
  const data = verticals.map((v) => ({
    name: labelOf(v.key),
    bytes: v.bytes,
    usd_per_month: v.usd_per_month,
    share: v.share * 100,
  }));
  const grid       = theme === 'dark' ? 'rgba(255,255,255,0.08)' : 'rgba(15,23,42,0.06)';
  const tickColor  = theme === 'dark' ? '#94a3b8' : '#475569';
  const cBar       = pick('teal', theme);

  return (
    <div className="finops-chart-vertbars" style={{ height: Math.max(180, 36 * data.length + 60) }}>
      <ResponsiveContainer>
        <BarChart data={data} layout="vertical"
                  margin={{ top: 8, right: 80, bottom: 16, left: 8 }}>
          <CartesianGrid stroke={grid} horizontal={false} />
          <XAxis type="number" stroke={tickColor} fontSize={10}
                 tickLine={false} axisLine={false}
                 tickFormatter={(v) => fmtBytes(v)} />
          <YAxis type="category" dataKey="name" stroke={tickColor} fontSize={11}
                 tickLine={false} axisLine={false} width={140}
                 interval={0} />
          <Tooltip
            formatter={(value, name, ctx) => {
              const r = ctx.payload;
              return [
                `${fmtBytes(value)} · ${fmtDec1(r.share)}% · ${fmtUSD(r.usd_per_month, { dp: 3 })}/mês`,
                'Bronze',
              ];
            }}
            contentStyle={{
              background: theme === 'dark' ? '#0f172a' : '#fff',
              border: `1px solid ${grid}`, fontSize: 11, borderRadius: 6,
            }}
          />
          <Bar dataKey="bytes" fill={cBar} radius={[0, 4, 4, 0]}
               label={{ position: 'right', formatter: (v) => fmtBytes(v),
                        fontSize: 10, fill: tickColor }} />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}

// ── Daily area chart ────────────────────────────────────────────────────────
function DailySpendArea({ daily, theme }) {
  const trimmed = useMemo(() => {
    const idx = daily.findIndex((d) => (d.cost_total || 0) > 0.001);
    return idx >= 0 ? daily.slice(idx) : daily;
  }, [daily]);

  const grid       = theme === 'dark' ? 'rgba(255,255,255,0.08)' : 'rgba(15,23,42,0.06)';
  const tickColor  = theme === 'dark' ? '#94a3b8' : '#475569';
  const cChargeable = pick('primary', theme);
  const cOverhead   = pick('amber',   theme);

  return (
    <div className="finops-chart-tall">
      <ResponsiveContainer>
        <AreaChart data={trimmed} margin={{ top: 12, right: 16, bottom: 24, left: 4 }}>
          <defs>
            <linearGradient id="finops-charge" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%"  stopColor={cChargeable} stopOpacity={0.7} />
              <stop offset="95%" stopColor={cChargeable} stopOpacity={0.1} />
            </linearGradient>
            <linearGradient id="finops-overhead" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%"  stopColor={cOverhead} stopOpacity={0.65} />
              <stop offset="95%" stopColor={cOverhead} stopOpacity={0.08} />
            </linearGradient>
          </defs>
          <CartesianGrid stroke={grid} vertical={false} />
          <XAxis dataKey="usage_date" tickFormatter={fmtDayShort}
                 stroke={tickColor} fontSize={10} tickLine={false}
                 axisLine={{ stroke: grid }} interval="preserveStartEnd" minTickGap={36} />
          <YAxis stroke={tickColor} fontSize={11} tickLine={false} axisLine={false}
                 width={52} tickFormatter={(v) => fmtUSDCompact(v)} />
          <Tooltip
            labelFormatter={fmtDayFull}
            formatter={(value, name) => {
              const labels = {
                cost_chargeable_total: 'Chargeable',
                cost_overhead_total:   'Overhead',
              };
              return [fmtUSD(value), labels[name] || name];
            }}
            contentStyle={{
              background: theme === 'dark' ? '#0f172a' : '#fff',
              border: `1px solid ${grid}`, fontSize: 11, borderRadius: 6,
            }}
          />
          <Legend
            verticalAlign="top" height={28} iconType="circle"
            wrapperStyle={{ fontSize: 11, paddingBottom: 4 }}
            formatter={(value) => {
              const labels = {
                cost_chargeable_total: 'Chargeable',
                cost_overhead_total:   'Overhead',
              };
              return labels[value] || value;
            }}
          />
          <Area type="monotone" dataKey="cost_chargeable_total" stackId="1"
                stroke={cChargeable} strokeWidth={1.5} fill="url(#finops-charge)" />
          <Area type="monotone" dataKey="cost_overhead_total" stackId="1"
                stroke={cOverhead} strokeWidth={1.5} fill="url(#finops-overhead)" />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
}

// ── Product donut + legend ──────────────────────────────────────────────────
function ProductDonut({ byProduct, theme }) {
  const data = byProduct.map((r) => ({
    name: PRODUCT_LABEL[r.product] || r.product,
    value: r.cost_usd,
    raw: r,
  }));
  return (
    <div className="finops-chart-medium">
      <ResponsiveContainer>
        <PieChart>
          <Pie
            data={data} dataKey="value" nameKey="name"
            cx="50%" cy="50%" innerRadius="55%" outerRadius="92%"
            paddingAngle={2} stroke="none"
          >
            {data.map((d) => (
              <Cell key={d.name} fill={productColor(d.raw.product, theme)} />
            ))}
          </Pie>
          <Tooltip
            formatter={(value, name, ctx) => [
              `${fmtUSD(value)} (${fmtDec1(ctx.payload.raw.share_pct)}%)`,
              name,
            ]}
            contentStyle={{
              background: theme === 'dark' ? '#0f172a' : '#fff',
              border: `1px solid ${theme === 'dark' ? 'rgba(255,255,255,0.1)' : 'rgba(0,0,0,0.08)'}`,
              fontSize: 11, borderRadius: 6,
            }}
          />
        </PieChart>
      </ResponsiveContainer>
    </div>
  );
}

function ProductLegend({ byProduct, theme }) {
  return (
    <ul className="finops-legend">
      {byProduct.map((r) => (
        <li key={r.product}>
          <span className="finops-legend-row">
            <span className="finops-legend-swatch"
                  style={{ background: productColor(r.product, theme) }} />
            <span className="finops-legend-name">{PRODUCT_LABEL[r.product] || r.product}</span>
            {r.workload_class === 'overhead' && (
              <span className="finops-legend-tag">overhead</span>
            )}
          </span>
          <span className="finops-legend-value">
            {fmtUSD(r.cost_usd)}
            <span className="finops-legend-pct">{fmtDec1(r.share_pct)}%</span>
          </span>
        </li>
      ))}
    </ul>
  );
}

// ── Outcome chart ───────────────────────────────────────────────────────────
function OutcomeBars({ byOutcome, theme }) {
  const data = byOutcome.map((r) => ({
    state: OUTCOME_LABEL[r.result_state] || r.result_state,
    raw_state: r.result_state,
    cost: r.cost_usd,
    n: r.n_runs,
    avg: r.avg_per_run,
    minutes: r.avg_minutes,
    share: r.share_pct,
  }));
  const grid       = theme === 'dark' ? 'rgba(255,255,255,0.08)' : 'rgba(15,23,42,0.06)';
  const tickColor  = theme === 'dark' ? '#94a3b8' : '#475569';
  return (
    <div className="finops-chart-medium">
      <ResponsiveContainer>
        <BarChart data={data} margin={{ top: 16, right: 16, bottom: 24, left: 4 }}>
          <CartesianGrid stroke={grid} vertical={false} />
          <XAxis dataKey="state" stroke={tickColor} fontSize={11}
                 tickLine={false} axisLine={{ stroke: grid }} />
          <YAxis stroke={tickColor} fontSize={11} tickLine={false} axisLine={false}
                 tickFormatter={(v) => fmtUSDCompact(v)} width={52} />
          <Tooltip
            formatter={(value, name, ctx) => {
              if (name === 'cost') {
                const r = ctx.payload;
                return [
                  `${fmtUSD(value)} · ${fmtInt(r.n)} runs · ${fmtUSD(r.avg)} médio · ${fmtDec1(r.minutes)} min`,
                  'Custo',
                ];
              }
              return [value, name];
            }}
            contentStyle={{
              background: theme === 'dark' ? '#0f172a' : '#fff',
              border: `1px solid ${grid}`, fontSize: 11, borderRadius: 6,
            }}
          />
          <Bar dataKey="cost" radius={[6, 6, 0, 0]}>
            {data.map((d) => (
              <Cell key={d.state} fill={outcomeColor(d.raw_state, theme)} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}

function OutcomeLegend({ byOutcome, theme }) {
  return (
    <ul className="finops-legend">
      {byOutcome.map((r) => (
        <li key={r.result_state}>
          <span className="finops-legend-row">
            <span className="finops-legend-swatch"
                  style={{ background: outcomeColor(r.result_state, theme) }} />
            <span className="finops-legend-name">
              {OUTCOME_LABEL[r.result_state] || r.result_state}
            </span>
            <span className="finops-legend-tag">{fmtInt(r.n_runs)} runs</span>
          </span>
          <span className="finops-legend-value">
            {fmtUSD(r.cost_usd)}
            <span className="finops-legend-pct">{fmtDec1(r.share_pct)}%</span>
          </span>
        </li>
      ))}
    </ul>
  );
}

// ── Top jobs table (collapses to cards on mobile) ──────────────────────────
function TopJobsTable({ byJob, theme }) {
  return (
    <>
      {/* Desktop / tablet — table */}
      <div className="finops-table-wrap finops-only-wide">
        <table className="finops-table">
          <thead>
            <tr>
              <th>Job</th>
              <th className="ar">Runs</th>
              <th className="ar">OK · ERR · CAN</th>
              <th className="ar">Custo total</th>
              <th className="ar">Médio</th>
              <th className="ar">Desperdiçado</th>
              <th className="ar">Min/run</th>
            </tr>
          </thead>
          <tbody>
            {byJob.map((j, i) => {
              const wastedRatio = j.cost_usd > 0 ? j.wasted_cost / j.cost_usd : 0;
              return (
                <tr key={i}>
                  <td title={j.job_name}>{truncate(j.job_name, 70)}</td>
                  <td className="ar">{fmtInt(j.n_runs)}</td>
                  <td className="ar">
                    <span style={{ color: outcomeColor('SUCCEEDED', theme) }}>{j.succeeded}</span>
                    {' · '}
                    <span style={{ color: outcomeColor('ERROR', theme) }}>{j.failed}</span>
                    {' · '}
                    <span style={{ color: outcomeColor('CANCELLED', theme) }}>{j.cancelled}</span>
                  </td>
                  <td className="ar strong">{fmtUSD(j.cost_usd)}</td>
                  <td className="ar">{fmtUSD(j.avg_per_run)}</td>
                  <td className="ar"
                      style={{ color: wastedRatio > 0.3 ? outcomeColor('ERROR', theme) : undefined }}>
                    {fmtUSD(j.wasted_cost)}
                    {wastedRatio > 0.05 && (
                      <span className="finops-table-frac"> ({fmtDec1(wastedRatio * 100)}%)</span>
                    )}
                  </td>
                  <td className="ar">{fmtDec1(j.avg_minutes)}</td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      {/* Mobile — card list */}
      <ul className="finops-cards finops-only-narrow">
        {byJob.map((j, i) => {
          const wastedRatio = j.cost_usd > 0 ? j.wasted_cost / j.cost_usd : 0;
          return (
            <li key={i} className="finops-card">
              <div className="finops-card-head">
                <span className="finops-card-rank">#{i + 1}</span>
                <span className="finops-card-name" title={j.job_name}>
                  {truncate(j.job_name, 50)}
                </span>
              </div>
              <div className="finops-card-money">
                <span className="finops-card-cost">{fmtUSD(j.cost_usd)}</span>
                <span className="finops-card-runs">{fmtInt(j.n_runs)} runs · {fmtUSD(j.avg_per_run)}/run</span>
              </div>
              <div className="finops-card-outcome">
                <span style={{ color: outcomeColor('SUCCEEDED', theme) }}>✓ {j.succeeded}</span>
                <span style={{ color: outcomeColor('ERROR', theme) }}>✗ {j.failed}</span>
                <span style={{ color: outcomeColor('CANCELLED', theme) }}>⊘ {j.cancelled}</span>
                <span className="finops-card-min">{fmtDec1(j.avg_minutes)} min/run</span>
              </div>
              {wastedRatio > 0.05 && (
                <div className="finops-card-wasted"
                     style={{ color: outcomeColor('ERROR', theme) }}>
                  {fmtUSD(j.wasted_cost)} desperdiçado ({fmtDec1(wastedRatio * 100)}%)
                </div>
              )}
            </li>
          );
        })}
      </ul>
    </>
  );
}

// ── Top runs table (collapses to cards on mobile) ──────────────────────────
function TopRunsTable({ topRuns, theme }) {
  return (
    <>
      <div className="finops-table-wrap finops-only-wide">
        <table className="finops-table">
          <thead>
            <tr>
              <th className="ar">#</th>
              <th>Dia</th>
              <th>Job</th>
              <th className="ar">Outcome</th>
              <th className="ar">Min</th>
              <th className="ar">DBUs</th>
              <th className="ar">Custo</th>
            </tr>
          </thead>
          <tbody>
            {topRuns.map((r, i) => (
              <tr key={r.run_id || i}
                  className={r.is_wasted ? 'finops-row-wasted' : undefined}>
                <td className="ar muted">{i + 1}</td>
                <td>{fmtDayShort(r.day)}</td>
                <td title={r.job_name}>{truncate(r.job_name, 55)}</td>
                <td className="ar"
                    style={{ color: outcomeColor(r.result_state, theme), fontWeight: 600 }}>
                  {OUTCOME_LABEL[r.result_state] || r.result_state}
                </td>
                <td className="ar">{fmtDec1(r.billed_minutes)}</td>
                <td className="ar">{fmtDec2(r.dbus)}</td>
                <td className="ar strong">{fmtUSD(r.cost_usd)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <ul className="finops-cards finops-only-narrow">
        {topRuns.map((r, i) => (
          <li key={r.run_id || i} className={`finops-card ${r.is_wasted ? 'finops-card-wasted-bg' : ''}`}>
            <div className="finops-card-head">
              <span className="finops-card-rank">#{i + 1}</span>
              <span className="finops-card-name" title={r.job_name}>
                {truncate(r.job_name, 45)}
              </span>
            </div>
            <div className="finops-card-money">
              <span className="finops-card-cost">{fmtUSD(r.cost_usd)}</span>
              <span style={{ color: outcomeColor(r.result_state, theme), fontWeight: 600 }}>
                {OUTCOME_LABEL[r.result_state] || r.result_state}
              </span>
            </div>
            <div className="finops-card-outcome">
              <span>{fmtDayFull(r.day)}</span>
              <span>{fmtDec1(r.billed_minutes)} min</span>
              <span>{fmtDec2(r.dbus)} DBUs</span>
            </div>
          </li>
        ))}
      </ul>
    </>
  );
}

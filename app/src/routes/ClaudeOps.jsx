// Vertical: ClaudeOps — uso pessoal de Claude Code (Anthropic).
// Source: app/public/data/claude_usage.json (gerado pelo sync-claude-usage.mjs).
//
// "Bronze" desta vertical são os JSONLs locais em ~/.claude/projects/, que o
// `ccusage` parseia em totais diários + breakdown por modelo. Aqui só
// renderizamos.
//
// Framing editorial: a primeira dobra mostra o custo total e o pico — "quanto
// IA me custaria se eu pagasse por uso". Em assinatura Max/Pro, esse número é
// o ROI da assinatura, não o gasto real.

import { useEffect, useMemo, useState } from 'react';
import {
  AreaChart, Area, BarChart, Bar,
  XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer,
} from 'recharts';
import PageHeader from '../components/PageHeader';
import Panel from '../components/Panel';
import KpiCard from '../components/KpiCard';
import { useTheme } from '../hooks/useTheme';
import { fmtInt, fmtCompact } from '../lib/format';
import { pick } from '../lib/colors';

const SOURCE_FILE = 'claude_usage.json';

// Valores em USD com locale pt-BR — vírgula decimal, ponto milhar, símbolo "US$".
function fmtUSD(v, opts = {}) {
  if (v == null || Number.isNaN(v)) return '—';
  const { compact = false, dp = 2 } = opts;
  if (!compact && v > 0 && v < 0.01) return '< US$ 0,01';
  return new Intl.NumberFormat('pt-BR', {
    style: 'currency',
    currency: 'USD',
    notation: compact ? 'compact' : 'standard',
    maximumFractionDigits: dp,
    minimumFractionDigits: compact ? 1 : dp,
  }).format(v);
}
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

// Modelo curto pra legendas: "claude-opus-4-7" → "opus 4.7", "haiku-4-5-20251001" → "haiku 4.5".
function shortModel(s) {
  if (!s) return '?';
  return s
    .replace(/^claude-/, '')
    .replace(/-(\d{8})$/, '')
    .replace(/-(\d)-(\d)$/, ' $1.$2');
}

// Cor por família de modelo — usa só a paleta existente.
function modelColor(name, theme) {
  if (name.includes('opus'))   return pick('primary', theme);
  if (name.includes('sonnet')) return pick('teal',    theme);
  if (name.includes('haiku'))  return pick('amber',   theme);
  return pick('slate', theme);
}

// Recharts styling theme-aware (mesmo padrão do FinOps).
function chartStyles(theme) {
  const dark = theme === 'dark';
  const grid      = dark ? 'rgba(255,255,255,0.08)' : 'rgba(15,23,42,0.06)';
  const tickColor = dark ? '#cbd5e1' : '#475569';
  const fg        = dark ? '#e2e8f0' : '#0f172a';
  const muted     = dark ? '#94a3b8' : '#64748b';
  const panel     = dark ? '#0f172a' : '#fff';
  return {
    grid,
    tickColor,
    fg,
    muted,
    tooltipContent: {
      background: panel,
      border: `1px solid ${grid}`,
      fontSize: 11,
      borderRadius: 6,
      color: fg,
    },
    tooltipLabel: { color: muted, fontWeight: 600, marginBottom: 2 },
    tooltipItem:  { color: fg },
    legendWrapper: { fontSize: 11, paddingBottom: 4, color: fg },
  };
}

export default function ClaudeOps() {
  const { theme } = useTheme();
  const [data, setData] = useState(null);
  const [error, setError] = useState(null);
  const cs = useMemo(() => chartStyles(theme), [theme]);

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
  }, []);

  if (error) {
    return (
      <div style={{ padding: 28, color: '#b91c1c' }}>
        Falha ao carregar {SOURCE_FILE}: {error}
      </div>
    );
  }
  if (!data) {
    return <div style={{ padding: 28, color: 'var(--muted)' }}>Carregando…</div>;
  }

  const days = data.daily ?? [];
  const totals = data.totals ?? {};

  // Daily cost series for the line/area chart
  const dailyChart = days.map((d) => ({
    date: d.date,
    label: fmtDayShort(d.date),
    cost: Number(d.total_cost) || 0,
  }));

  // Stacked bar: cost by model per day
  const modelNames = Array.from(
    new Set(days.flatMap((d) => (d.by_model ?? []).map((m) => shortModel(m.model)))),
  );
  const modelChart = days.map((d) => {
    const point = { label: fmtDayShort(d.date) };
    for (const name of modelNames) point[name] = 0;
    for (const m of d.by_model ?? []) point[shortModel(m.model)] = Number(m.cost) || 0;
    return point;
  });

  // Peak day for KPI subtitle
  const peak = days.reduce((best, d) => (!best || d.total_cost > best.total_cost ? d : best), null);

  // Last 7 days vs prior 7 days (when we have ≥ 14)
  const last7 = days.slice(-7).reduce((s, d) => s + d.total_cost, 0);

  // Last refresh timestamp
  const generatedAt = data.generated_at
    ? new Date(data.generated_at).toLocaleString('pt-BR', { timeZone: 'America/Sao_Paulo' })
    : null;

  return (
    <div className="claudeops-page" style={{ fontFeatureSettings: '"tnum" 1, "lnum" 1' }}>
      <PageHeader
        eyebrow="Auto-observabilidade · IA"
        title="Claude Code · custo de uso"
        subtitle="Tokens consumidos por dia, equivalente em US$ pelo preço pay-as-you-go da Anthropic. Em assinatura Max/Pro, esse número é o ROI da assinatura — não o gasto real."
        withFlag={false}
      />

      <div className="kpiRow" style={{ marginTop: 18 }}>
        <KpiCard
          label="Custo total"
          value={fmtUSD(totals.total_cost_usd ?? 0)}
          sub={`em ${totals.days ?? 0} dias`}
          color={pick('primary', theme)}
        />
        <KpiCard
          label="Tokens totais"
          value={fmtCompact(totals.total_tokens ?? 0)}
          sub="input + output + cache"
          color={pick('teal', theme)}
        />
        <KpiCard
          label="Média por dia"
          value={fmtUSD(totals.avg_cost_per_day_usd ?? 0)}
          sub="todos os dias com uso"
          color={pick('emerald', theme)}
        />
        <KpiCard
          label="Pico"
          value={peak ? fmtUSD(peak.total_cost) : '—'}
          sub={peak ? fmtDayFull(peak.date) : '—'}
          color={pick('amber', theme)}
        />
      </div>

      <Panel
        label="Custo diário"
        sub={`últimos 7 dias: ${fmtUSD(last7)}`}
      >
        <div style={{ width: '100%', height: 280 }}>
          <ResponsiveContainer>
            <AreaChart data={dailyChart} margin={{ top: 12, right: 16, bottom: 0, left: 4 }}>
              <defs>
                <linearGradient id="claudeops-cost" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%"  stopColor={pick('primary', theme)} stopOpacity={0.45} />
                  <stop offset="95%" stopColor={pick('primary', theme)} stopOpacity={0}    />
                </linearGradient>
              </defs>
              <CartesianGrid stroke={cs.grid} strokeDasharray="3 3" vertical={false} />
              <XAxis
                dataKey="label"
                tick={{ fill: cs.tickColor, fontSize: 11 }}
                tickLine={false}
                axisLine={{ stroke: cs.grid }}
              />
              <YAxis
                tick={{ fill: cs.tickColor, fontSize: 11 }}
                tickLine={false}
                axisLine={false}
                tickFormatter={fmtUSDCompact}
                width={56}
              />
              <Tooltip
                contentStyle={cs.tooltipContent}
                labelStyle={cs.tooltipLabel}
                itemStyle={cs.tooltipItem}
                formatter={(v) => [fmtUSD(Number(v)), 'Custo']}
              />
              <Area
                type="monotone"
                dataKey="cost"
                stroke={pick('primary', theme)}
                strokeWidth={2}
                fill="url(#claudeops-cost)"
              />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      </Panel>

      <div style={{ height: 16 }} />

      <Panel label="Custo por modelo · stack diário" sub="empilhado em US$">
        <div style={{ width: '100%', height: 320 }}>
          <ResponsiveContainer>
            <BarChart data={modelChart} margin={{ top: 12, right: 16, bottom: 0, left: 4 }}>
              <CartesianGrid stroke={cs.grid} strokeDasharray="3 3" vertical={false} />
              <XAxis
                dataKey="label"
                tick={{ fill: cs.tickColor, fontSize: 11 }}
                tickLine={false}
                axisLine={{ stroke: cs.grid }}
              />
              <YAxis
                tick={{ fill: cs.tickColor, fontSize: 11 }}
                tickLine={false}
                axisLine={false}
                tickFormatter={fmtUSDCompact}
                width={56}
              />
              <Tooltip
                contentStyle={cs.tooltipContent}
                labelStyle={cs.tooltipLabel}
                itemStyle={cs.tooltipItem}
                formatter={(v, name) => [fmtUSD(Number(v)), name]}
              />
              <Legend wrapperStyle={cs.legendWrapper} />
              {modelNames.map((m) => (
                <Bar key={m} dataKey={m} stackId="cost" fill={modelColor(m, theme)} />
              ))}
            </BarChart>
          </ResponsiveContainer>
        </div>
      </Panel>

      <div style={{ height: 16 }} />

      <Panel label="Detalhe diário" sub={`${days.length} dias`}>
        <div style={{ overflowX: 'auto', margin: '-4px -4px' }}>
          <table className="claudeops-table" style={tableStyle}>
            <thead>
              <tr style={theadRowStyle(cs)}>
                <th style={{ ...thStyle, textAlign: 'left' }}>Data</th>
                <th style={thStyle}>Custo</th>
                <th style={thStyle}>Tokens</th>
                <th style={thStyle}>Cache read</th>
                <th style={{ ...thStyle, textAlign: 'left' }}>Modelos</th>
              </tr>
            </thead>
            <tbody>
              {[...days].reverse().map((d) => (
                <tr key={d.date} style={trStyle(cs)}>
                  <td style={{ ...tdStyle, textAlign: 'left' }}>{fmtDayFull(d.date)}</td>
                  <td style={tdStyle}>{fmtUSD(d.total_cost)}</td>
                  <td style={tdStyle}>{fmtInt(d.total_tokens)}</td>
                  <td style={tdStyle}>{fmtInt(d.cache_read_tokens)}</td>
                  <td style={{ ...tdStyle, textAlign: 'left', color: 'var(--muted)' }}>
                    {(d.models ?? []).map(shortModel).join(' · ')}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Panel>

      <p
        style={{
          fontSize: 11,
          color: 'var(--muted)',
          marginTop: 18,
          maxWidth: '70ch',
        }}
      >
        Fonte: <code>~/.claude/projects/</code> via{' '}
        <a href="https://github.com/ryoppippi/ccusage" target="_blank" rel="noreferrer">
          ccusage
        </a>
        . Sync local em <code>predev/prebuild</code>.
        {generatedAt && <> Atualizado em {generatedAt} BRT.</>}
      </p>
    </div>
  );
}

// ── Inline table styles (sem CSS dedicado) ─────────────────────────────────
const tableStyle = {
  width: '100%',
  borderCollapse: 'collapse',
  fontSize: 13,
  fontVariantNumeric: 'tabular-nums',
};
const thStyle = {
  padding: '8px 10px',
  textAlign: 'right',
  fontSize: 10,
  fontWeight: 700,
  letterSpacing: '0.07em',
  textTransform: 'uppercase',
  color: 'var(--muted)',
};
const tdStyle = {
  padding: '8px 10px',
  textAlign: 'right',
  whiteSpace: 'nowrap',
};
const theadRowStyle = (cs) => ({ borderBottom: `1px solid ${cs.grid}` });
const trStyle = (cs) => ({ borderTop: `1px solid ${cs.grid}` });

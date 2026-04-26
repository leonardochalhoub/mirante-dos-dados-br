// Vertical: UroPro — Tratamento Cirúrgico da Incontinência Urinária no SUS.
// Source: /data/gold_uropro_estados_ano.json
// Schema row: {
//   uf, ano, proc_rea, proc_label, populacao,
//   n_aih, n_morte,
//   aih_eletivo, aih_urgencia,
//   aih_gestao_estadual, aih_gestao_municipal, aih_gestao_dupla,
//   val_tot, val_sh, val_sp,
//   val_eletivo, val_urgencia,
//   val_gestao_estadual, val_gestao_municipal, val_gestao_dupla,
//   val_tot_2021, val_sh_2021, val_sp_2021,
//   val_tot_avg, val_sh_avg, val_sp_avg, val_tot_avg_2021,
//   dias_perm_avg, mortalidade,
//   val_tot_2021_por100k, n_aih_por100k, per_capita_base,
//   deflator
// }
//
// Origem analítica: trabalho de especialização em Enfermagem (Tatieli, 2022),
// reproduzido a partir dos microdados SIH-AIH-RD.

import { useEffect, useMemo, useState } from 'react';
import PageHeader     from '../components/PageHeader';
import Panel          from '../components/Panel';
import KpiCard        from '../components/KpiCard';
import BrazilMap      from '../components/BrazilMap';
import StateRanking   from '../components/StateRanking';
import EvolutionStackedByKey from '../components/charts/EvolutionStackedByKey';
import DownloadActions from '../components/DownloadActions';
import TechBadges      from '../components/TechBadges';
import ScoreCard       from '../components/ScoreCard';
import { PARECER_UROPRO } from '../data/pareceres';
import { useTheme }    from '../hooks/useTheme';
import { loadGold }    from '../lib/data';
import { COLORSCALES } from '../lib/scales';
import { fmtBRL, fmtCompact, fmtDec1, fmtDec2, fmtInt, fmtPct } from '../lib/format';
import { exportToXlsx, exportChartsAsZip } from '../lib/exporters';

// Three SIGTAP procedures studied in Tatieli (2022) + extension.
// Multi-select: client re-aggregates across the chosen procedures.
const PROCEDURES = {
  '0409010499': { label: 'Via Abdominal',                short: 'ABD' },
  '0409070270': { label: 'Via Vaginal',                  short: 'VAG' },
  '0409020117': { label: 'Genérico (residual)',          short: 'GEN' },
};
const DEFAULT_PROCS = ['0409010499', '0409070270'];

const METRICS = {
  val_tot_2021: {
    label: 'Valor pago (R$ 2021)',         short: 'R$',
    yaxisTitle: 'Valor pago (R$ 2021)',
    fmt: fmtDec2, fmtRich: (v) => fmtBRL(v, { compact: true }),
  },
  n_aih: {
    label: 'AIH aprovadas (un.)',          short: 'AIH',
    yaxisTitle: 'AIH aprovadas',
    fmt: fmtInt, fmtRich: fmtInt,
  },
  val_tot_avg_2021: {
    label: 'Valor médio por AIH (R$ 2021)', short: 'R$/AIH',
    yaxisTitle: 'R$ por AIH (2021)',
    fmt: fmtDec2, fmtRich: (v) => fmtBRL(v),
  },
  dias_perm_avg: {
    label: 'Permanência média (dias)',      short: 'dias',
    yaxisTitle: 'Dias de internação',
    fmt: fmtDec2, fmtRich: fmtDec2,
  },
  n_aih_por100k: {
    label: 'AIH por 100 mil habitantes',    short: 'AIH/100k',
    yaxisTitle: 'AIH por 100 mil hab.',
    fmt: fmtDec2, fmtRich: fmtDec2,
  },
};
const DEFAULT_METRIC = 'n_aih';
const DEFAULT_COLOR  = 'Cividis';

// Métricas em que a soma entre procedimentos faz sentido (count/value/rate).
// Para weighted-averages (dias_perm_avg, val_tot_avg_2021), o stacked ainda
// mostra cada proc como segmento — útil visualmente — mas não exibimos o
// label de "total" no topo, que seria matematicamente enganoso.
const SUM_METRICS = new Set(['n_aih', 'val_tot_2021', 'n_aih_por100k']);

export default function UroPro() {
  const { theme } = useTheme();
  const [rows, setRows]                 = useState(null);
  const [error, setError]               = useState(null);
  const [metricKey, setMetricKey]       = useState(DEFAULT_METRIC);
  const [year, setYear]                 = useState(null);
  const [colorscale, setColorscale]     = useState(DEFAULT_COLOR);
  const [selectedProcs, setSelectedProcs] = useState(DEFAULT_PROCS);

  useEffect(() => {
    loadGold('gold_uropro_estados_ano.json')
      .then((all) => {
        setRows(all);
        if (all.length === 0) return;
        const last = Math.max(...all.map((r) => r.ano));
        setYear(String(last));
      })
      .catch((e) => setError(e.message));
  }, []);

  const metric = METRICS[metricKey];
  const years = useMemo(
    () => (rows ? Array.from(new Set(rows.map((r) => r.ano))).sort() : []),
    [rows],
  );

  // Procedures que aparecem no menu = só os que têm soma de n_aih > 0 em
  // pelo menos UM (ano, UF) na série inteira. Procedimentos zerados em
  // todo o histórico (ex.: 0409020117 Genérico, código residual) são
  // ocultados — não confundem o usuário com seleção que não rende dado.
  const availableProcs = useMemo(() => {
    if (!rows || !rows.length) return Object.keys(PROCEDURES);
    const sums = new Map();
    for (const r of rows) {
      sums.set(r.proc_rea, (sums.get(r.proc_rea) || 0) + (r.n_aih || 0));
    }
    return Object.keys(PROCEDURES).filter((p) => (sums.get(p) || 0) > 0);
  }, [rows]);

  // Quando availableProcs muda, sane selectedProcs (descarta os ocultos)
  useEffect(() => {
    if (!rows) return;
    const avail = new Set(availableProcs);
    const next = selectedProcs.filter((p) => avail.has(p));
    if (next.length === 0 && availableProcs.length > 0) {
      setSelectedProcs(availableProcs);
    } else if (next.length !== selectedProcs.length) {
      setSelectedProcs(next);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [availableProcs, rows]);

  // Filter to selected year + selected procedures, then aggregate per UF.
  // For per-AIH-style metrics (avg, perm, mortalidade), we recompute weighted
  // average using n_aih as weight; otherwise we sum.
  const filtered = useMemo(() => {
    if (!rows || !year) return [];
    const yNum = Number(year);
    const sel = new Set(selectedProcs);
    const yr = rows.filter((r) => r.ano === yNum && sel.has(r.proc_rea));
    const byUf = new Map();
    for (const r of yr) {
      if (!byUf.has(r.uf)) byUf.set(r.uf, []);
      byUf.get(r.uf).push(r);
    }
    return Array.from(byUf.entries()).map(([uf, rs]) => ({
      uf,
      value: aggregateForMetric(rs, metricKey),
    }));
  }, [rows, year, selectedProcs, metricKey]);

  const ranking = useMemo(
    () => [...filtered].filter((r) => r.value > 0).sort((a, b) => b.value - a.value),
    [filtered],
  );

  const kpis = useMemo(() => {
    if (!rows || !year) return null;
    const yNum = Number(year);
    const sel = new Set(selectedProcs);
    const yr = rows.filter((r) => r.ano === yNum && sel.has(r.proc_rea));
    const totalAih = yr.reduce((s, r) => s + (r.n_aih || 0), 0);
    const totalVal = yr.reduce((s, r) => s + (r.val_tot_2021 || 0), 0);
    const totalDeaths = yr.reduce((s, r) => s + (r.n_morte || 0), 0);
    const sumDias = yr.reduce((s, r) => s + (r.dias_perm_avg || 0) * (r.n_aih || 0), 0);
    const dias_avg = totalAih > 0 ? sumDias / totalAih : 0;
    const mort = totalAih > 0 ? totalDeaths / totalAih : 0;
    const valPerAih = totalAih > 0 ? totalVal / totalAih : 0;
    return { totalAih, totalVal, totalDeaths, dias_avg, mort, valPerAih };
  }, [rows, year, selectedProcs]);

  // Per-procedure breakdown for stacked evolution chart.
  // Cada ano vira { year, [proc1]: value, [proc2]: value, ... } onde value
  // é o agregado nacional do proc nesse ano (mesma semântica do chart antigo,
  // mas decomposto por procedimento ao invés de somado).
  const evolutionData = useMemo(() => {
    if (!rows) return [];
    return years.map((y) => {
      const entry = { year: String(y) };
      for (const proc of selectedProcs) {
        const yr = rows.filter((r) => r.ano === y && r.proc_rea === proc);
        entry[proc] = aggregateForMetric(yr, metricKey, /*nationwide*/ true);
      }
      return entry;
    });
  }, [rows, years, selectedProcs, metricKey]);

  // Keys para o stacked: ordem = ordem de selectedProcs, label vem de PROCEDURES.
  const evolutionKeys = useMemo(
    () => selectedProcs.map((proc) => ({ key: proc, label: PROCEDURES[proc].label })),
    [selectedProcs],
  );

  if (error) return <div className="error-block">Erro ao carregar dados: {error}</div>;

  // Even when rows isn't loaded, we render the article + footer.
  // The "interactive panel" is shown only when data is materialized.

  return (
    <>
      <PageHeader
        eyebrow="Vertical · saúde · cirurgia uroginecológica"
        title="Incontinência Urinária — Cirurgia no SUS"
        subtitle="Microdados SIH-AIH-RD por UF, ano, procedimento, caráter e gestão. Origem analítica: especialização em Enfermagem (Tatieli, 2022)."
        right={
          <div className="header-right-row">
            <TechBadges />
            <DownloadActions
              onExportXlsx={() => exportToXlsx('mirante-uropro', { 'uropro_uf_ano': rows || [] })}
              onExportPng={() => exportChartsAsZip('mirante-uropro')}
            />
          </div>
        }
      />

      <ScoreCard parecer={PARECER_UROPRO} />

      <DocSection />

      {(!rows || rows.length === 0) && (
        <div className="panel" style={{ marginTop: 18 }}>
          <div className="panelHead">
            <span className="panelLabel">Status</span>
            <span className="kicker">Pipeline em construção</span>
          </div>
          <p className="muted" style={{ fontSize: 13, lineHeight: 1.7 }}>
            Os microdados SIH-AIH-RD ainda não foram materializados. O pipeline
            está pronto no Databricks (<code>job_uropro_refresh</code> em
            <code> pipelines/databricks.yml</code>) e será executado quando o
            ciclo mensal disparar (dia 26 às 6h UTC), ou manualmente via
            Workflows na UI do workspace. Quando o JSON gold for commitado em
            <code> /data/gold/gold_uropro_estados_ano.json</code>, esta página
            renderiza automaticamente os KPIs, ranking e mapa. Enquanto isso,
            o artigo acima já contém os achados centrais da pesquisa original
            (Tatieli, 2022) cobrindo 2015–2020 — clique em{' '}
            <b>Ler artigo (PDF)</b> ou <b>Baixar PDF (ABNT)</b>.
          </p>
        </div>
      )}

      {rows && rows.length > 0 && kpis && (
        <>
          <div className="kpiRow" data-export-id="uropro-kpis">
            <KpiCard
              label={`AIH · ${year}`}
              value={fmtInt(kpis.totalAih)}
              sub="internações aprovadas (somadas)"
            />
            <KpiCard
              label={`Pago · ${year}`}
              value={fmtBRL(kpis.totalVal, { compact: true })}
              sub="R$ 2021 (deflacionado)"
              color="#0d9488"
            />
            <KpiCard
              label={`Custo médio · ${year}`}
              value={fmtBRL(kpis.valPerAih)}
              sub="por AIH (R$ 2021)"
              color="#b45309"
            />
            <KpiCard
              label={`Permanência · ${year}`}
              value={`${kpis.dias_avg.toFixed(2)} dias`}
              sub="média ponderada"
              color="#be185d"
            />
            <KpiCard
              label={`Óbitos · ${year}`}
              value={fmtInt(kpis.totalDeaths)}
              sub={`mortalidade ${fmtPct(kpis.mort)}`}
              color="#374151"
            />
          </div>

          <div className="layout">
            <div className="row row-controls-bar">
              <Panel label="Filtros & dados" sub="DATASUS · IBGE · BCB">
                <div className="controls">
                  <div className="control" style={{ gridTemplateColumns: '90px 1fr', alignItems: 'flex-start' }}>
                    <label htmlFor="proc" style={{ paddingTop: 6 }}>Procedimento</label>
                    <ProcedureMultiSelect
                      selected={selectedProcs}
                      onChange={setSelectedProcs}
                      availableProcs={availableProcs}
                    />
                  </div>

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
                    <select id="year" value={year || ''} onChange={(e) => setYear(e.target.value)}>
                      {years.map((y) => (<option key={y} value={y}>{y}</option>))}
                    </select>
                  </div>

                  <div className="metaBlock">
                    <b>Procedimentos:</b><br />
                    0409010499 — Via Abdominal<br />
                    0409070270 — Via Vaginal<br />
                    0409020117 — Genérico<br />
                    <b>Multi-seleção:</b> totais somam, médias ponderam por AIH<br />
                    <b>R$ 2021:</b> deflacionado pelo IPCA (BCB)
                  </div>
                </div>
              </Panel>

              <Panel
                label="Evolução nacional"
                exportId="uropro-evolucao"
                right={
                  <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-end', gap: 2, lineHeight: 1.4 }}>
                    <span className="panelSub">{metric.label}</span>
                    <span
                      style={{ fontSize: 11, color: 'var(--muted)', textAlign: 'right', maxWidth: 380 }}
                      title="Autorização de Internação Hospitalar — documento do SIH-SUS, base de pagamento; 1 AIH = 1 internação aprovada"
                    >
                      <b>AIH</b> = Autorização de Internação Hospitalar (1 AIH = 1 internação aprovada no SIH-SUS)
                    </span>
                  </div>
                }
              >
                <EvolutionStackedByKey
                  data={evolutionData}
                  keys={evolutionKeys}
                  theme={theme}
                  yLabel={metric.yaxisTitle}
                  xLabel="Ano"
                  format={metric.fmt}
                  height={320}
                  showTotalLabel={SUM_METRICS.has(metricKey)}
                />
              </Panel>
            </div>

            <div className="row row-ranking-map">
              <Panel label="Ranking por UF" sub={`${metric.label} · ${year}`} exportId="uropro-ranking">
                <StateRanking rows={ranking} format={metric.fmtRich} />
              </Panel>

              <Panel
                label="Distribuição geográfica"
                exportId="uropro-mapa"
                right={
                  <div className="mapControls">
                    <label htmlFor="colorscale">Cores</label>
                    <select id="colorscale" value={colorscale} onChange={(e) => setColorscale(e.target.value)}>
                      {COLORSCALES.map((c) => (<option key={c.value} value={c.value}>{c.label}</option>))}
                    </select>
                  </div>
                }
              >
                <BrazilMap data={filtered} colorscale={colorscale} theme={theme} hoverFmt={metric.fmtRich} unit={metric.short} />
              </Panel>
            </div>
          </div>
        </>
      )}

      <Footer />
    </>
  );
}

// ─── Aggregation helper ──────────────────────────────────────────────────
// Sums for count/value metrics, weighted-avg for per-AIH metrics, recomputed
// rate for per-100k.
function aggregateForMetric(rows, metricKey, nationwide = false) {
  if (!rows.length) return 0;
  const totalAih = rows.reduce((s, r) => s + (r.n_aih || 0), 0);
  switch (metricKey) {
    case 'n_aih':
      return rows.reduce((s, r) => s + (r.n_aih || 0), 0);
    case 'val_tot_2021':
      return rows.reduce((s, r) => s + (r.val_tot_2021 || 0), 0);
    case 'val_tot_avg_2021': {
      const totVal = rows.reduce((s, r) => s + (r.val_tot_2021 || 0), 0);
      return totalAih > 0 ? totVal / totalAih : 0;
    }
    case 'dias_perm_avg': {
      // Weighted by n_aih
      const num = rows.reduce((s, r) => s + (r.dias_perm_avg || 0) * (r.n_aih || 0), 0);
      return totalAih > 0 ? num / totalAih : 0;
    }
    case 'n_aih_por100k': {
      // Recompute: sum(AIH) / unique pop * 100k
      // Per-UF: rows here belong to one UF, populacao is shared across procs (replicated)
      // Nationwide: sum unique pops across UFs.
      if (nationwide) {
        const ufPop = new Map();
        for (const r of rows) if (!ufPop.has(r.uf)) ufPop.set(r.uf, r.populacao || 0);
        const popBR = Array.from(ufPop.values()).reduce((s, v) => s + v, 0);
        return popBR > 0 ? (totalAih / popBR) * 100_000 : 0;
      }
      const pop = rows[0]?.populacao || 0;
      return pop > 0 ? (totalAih / pop) * 100_000 : 0;
    }
    default:
      return 0;
  }
}

// ─── Procedure multi-select (reused pattern from Equipamentos) ───────────
function ProcedureMultiSelect({ selected, onChange, availableProcs }) {
  const [open, setOpen] = useState(false);
  const sel = new Set(selected);

  const toggle = (proc) => {
    const next = sel.has(proc)
      ? selected.filter((p) => p !== proc)
      : [...selected, proc];
    if (next.length > 0) onChange(next);
  };

  const summary = selected.length === 1
    ? PROCEDURES[selected[0]]?.label || selected[0]
    : selected.length === Object.keys(PROCEDURES).length
      ? 'Todos'
      : `${selected.length} selecionados`;

  return (
    <div className="multi-select">
      <button type="button" className="multi-select-trigger" onClick={() => setOpen((v) => !v)}>
        <span>{summary}</span>
        <span className="multi-select-caret">▾</span>
      </button>
      {open && (
        <div className="multi-select-popover">
          <div className="multi-select-options">
            {Object.entries(PROCEDURES)
              .filter(([code]) => !availableProcs || availableProcs.includes(code))
              .map(([code, info]) => (
              <label key={code} className="multi-select-option">
                <input
                  type="checkbox"
                  checked={sel.has(code)}
                  onChange={() => toggle(code)}
                />
                <span>{info.label}</span>
                <span className="multi-select-code">{code}</span>
              </label>
            ))}
          </div>
          <button type="button" className="multi-select-close" onClick={() => setOpen(false)}>Fechar</button>
        </div>
      )}
    </div>
  );
}

// ─── Doc section: abstract + buttons (padrão Mirante: PDF LaTeX + tex + Overleaf) ─
// Padrão ABNT compilado em CI (xu-cheng/latex-action sobre
// articles/uropro-incontinencia-urinaria.tex), idêntico ao de Emendas/PBF/RAIS.
// Bloco data-driven (UroProArticle) continua acessível via /incontinencia-urinaria/artigo
// como visualização HTML alternativa, mas o PDF estático é a entrada primária.
function DocSection() {
  // UroPro tem TRÊS Working Papers, cada um em seu próprio quadro empilhado:
  //   - WP #3 (Tatieli/Chalhoub) — paper original, recorte 2015-2020
  //   - WP #4 (cross-vertical)   — UroPro × PBF × Emendas, 2008-2025
  //   - WP #6 (vertical-only)    — UroPro 17 anos, eficiência+COVID+represa
  return (
    <section className="emendas-abstract no-print" style={{ marginBottom: 14 }}>
      <DocCardWP3 />
      <DocCardWP4 />
      <DocCardWP6 />
    </section>
  );
}

// WP #3 — Tatieli/Chalhoub (paper original, 2015-2020)
function DocCardWP3() {
  const base       = import.meta.env.BASE_URL || '/';
  const pdfUrl     = `${base}articles/uropro-incontinencia-urinaria.pdf`.replace(/\/{2,}/g, '/');
  const texUrl     = `${base}articles/uropro-incontinencia-urinaria.tex`.replace(/\/{2,}/g, '/');
  const overleafUrl = 'https://www.overleaf.com/docs?snip_uri=' +
    encodeURIComponent(`https://leonardochalhoub.github.io${texUrl}`);
  const standaloneUrl = `${base}#/incontinencia-urinaria/artigo`.replace(/\/{2,}/g, '/');
  return (
    <div className="doc-block" style={{ marginBottom: 14 }}>
      <div className="kicker">Working Paper n. 3 — Mirante dos Dados</div>
      <p style={{ marginTop: 6, fontSize: 13.5 }}>
        <b>"Tratamento Cirúrgico da Incontinência Urinária no Sistema
        Único de Saúde (2015–2020): volumes, despesa, permanência e
        distribuição geográfica por via de acesso"</b> — coautoria com{' '}
        <b>Tatieli da Silva</b> (pesquisa original, especialização em
        Enfermagem, 2022). Análise empírica em padrão ABNT a partir dos
        microdados SIH-AIH-RD, comparando as duas vias cirúrgicas
        (abdominal SIGTAP <code>0409010499</code> e vaginal <code>0409070270</code>)
        em volume, despesa pública (R$ deflacionado IPCA-2021), permanência
        hospitalar e distribuição entre as 27 UFs.
      </p>
      <div className="doc-actions">
        <a className="doc-toggle doc-toggle-primary"
           href={pdfUrl} target="_blank" rel="noreferrer"
           title="Abrir PDF em nova aba (visualizador nativo do navegador)">
          📖 Ler artigo (PDF)
        </a>
        <a className="doc-toggle"
           href={pdfUrl} download="Mirante-UroPro-Incontinencia-Silva-Chalhoub-2026.pdf"
           title="PDF compilado em LaTeX, padrão ABNT">
          ⤓ Baixar PDF (ABNT)
        </a>
        <a className="doc-toggle"
           href={texUrl} download="uropro-incontinencia-urinaria.tex"
           title="Fonte LaTeX (.tex)">
          ⤓ Baixar fonte (.tex)
        </a>
        <a className="doc-toggle"
           href={overleafUrl} target="_blank" rel="noreferrer"
           title="Compilação online em 1 clique no Overleaf">
          ↗ Abrir no Overleaf
        </a>
      </div>
      <p style={{ fontSize: 11, color: 'var(--muted)', marginTop: 10, marginBottom: 0, lineHeight: 1.5 }}>
        <b>Palavras-chave:</b> incontinência urinária; SUS; SIH-SUS;
        cirurgia uroginecológica; análise espacial em saúde; dados abertos.{' '}
        Visualização HTML data-driven alternativa (regenerada a cada refresh
        do gold) disponível em{' '}
        <a href={standaloneUrl} target="_blank" rel="noreferrer">
          <code>/incontinencia-urinaria/artigo</code>
        </a>.
      </p>
    </div>
  );
}

// WP #4 — cross-vertical (UroPro × PBF × Emendas)
function DocCardWP4() {
  const base       = import.meta.env.BASE_URL || '/';
  const pdfUrl     = `${base}articles/uropro-serie-2008-2025.pdf`.replace(/\/{2,}/g, '/');
  const texUrl     = `${base}articles/uropro-serie-2008-2025.tex`.replace(/\/{2,}/g, '/');
  const overleafUrl = 'https://www.overleaf.com/docs?snip_uri=' +
    encodeURIComponent(`https://leonardochalhoub.github.io${texUrl}`);
  return (
    <div className="doc-block" style={{ marginBottom: 14 }}>
      <div className="kicker">Working Paper n. 4 — Mirante dos Dados</div>
      <p style={{ marginTop: 6, fontSize: 13.5 }}>
        <b>"Acesso desigual: cirurgia uroginecológica no SUS como indicador
        de pobreza estrutural e os limites da compensação fiscal por emendas
        parlamentares (2008–2025)"</b> — análise <i>cross-vertical</i> que
        cruza UroPro, Bolsa Família (cobertura PBF como <i>proxy</i> de pobreza)
        e Emendas Parlamentares (execução <i>per capita</i>) sobre a mesma
        arquitetura medalhão. Documenta correlação ρ ≈ -0,68 entre cobertura
        PBF e acesso à cirurgia, e ρ ≈ -0,45 (também negativa) com emendas
        per capita — UFs mais pobres recebem mais emendas, mas isso{' '}
        <i>não</i> se traduz em ampliação de oferta cirúrgica especializada.
      </p>
      <div className="doc-actions">
        <a className="doc-toggle doc-toggle-primary"
           href={pdfUrl} target="_blank" rel="noreferrer"
           title="Abrir PDF em nova aba (visualizador nativo do navegador)">
          📖 Ler artigo (PDF)
        </a>
        <a className="doc-toggle"
           href={pdfUrl} download="Mirante-UroPro-AcessoDesigual-Chalhoub-2026.pdf"
           title="PDF compilado em LaTeX, padrão ABNT">
          ⤓ Baixar PDF (ABNT)
        </a>
        <a className="doc-toggle"
           href={texUrl} download="uropro-serie-2008-2025.tex"
           title="Fonte LaTeX (.tex) — recompilável em qualquer ambiente TeX">
          ⤓ Baixar fonte (.tex)
        </a>
        <a className="doc-toggle"
           href={overleafUrl} target="_blank" rel="noreferrer"
           title="Compilação online em 1 clique no Overleaf">
          ↗ Abrir no Overleaf
        </a>
      </div>
      <p style={{ fontSize: 11, color: 'var(--muted)', marginTop: 10, marginBottom: 0, lineHeight: 1.5 }}>
        <b>Palavras-chave:</b> SUS; equidade em saúde; Bolsa Família; emendas
        parlamentares; federalismo brasileiro; análise <i>cross-vertical</i>.
      </p>
    </div>
  );
}

// WP #6 — vertical-only (17 anos UroPro)
function DocCardWP6() {
  const base       = import.meta.env.BASE_URL || '/';
  const pdfUrl     = `${base}articles/uropro-saude-publica-2008-2025.pdf`.replace(/\/{2,}/g, '/');
  const texUrl     = `${base}articles/uropro-saude-publica-2008-2025.tex`.replace(/\/{2,}/g, '/');
  const overleafUrl = 'https://www.overleaf.com/docs?snip_uri=' +
    encodeURIComponent(`https://leonardochalhoub.github.io${texUrl}`);
  return (
    <div className="doc-block">
      <div className="kicker">Working Paper n. 6 — Mirante dos Dados</div>
      <p style={{ marginTop: 6, fontSize: 13.5 }}>
        <b>"Cirurgia uroginecológica no SUS, 2008–2025: ganhos silenciosos
        de eficiência, desigualdade territorial persistente, choque pandêmico
        e represa cirúrgica"</b> — recorte longitudinal de 17 anos. Documenta
        queda de 40% na permanência hospitalar (eficiência clínica), o
        choque da pandemia (-57% em 2020-2021), a represa cirúrgica em
        escoamento em 2024-2025 (volume acima do baseline pré-COVID), e a
        transparência metodológica sobre o bug silver corrigido em{' '}
        <code>fa869cf</code> (filtro <code>_ingest_ts == max</code> derrubava
        14 das 27 UFs em silêncio).
      </p>
      <div className="doc-actions">
        <a className="doc-toggle doc-toggle-primary"
           href={pdfUrl} target="_blank" rel="noreferrer"
           title="Abrir PDF em nova aba (visualizador nativo do navegador)">
          📖 Ler artigo (PDF)
        </a>
        <a className="doc-toggle"
           href={pdfUrl} download="Mirante-UroPro-SaudePublica-Chalhoub-2026.pdf"
           title="PDF compilado em LaTeX, padrão ABNT">
          ⤓ Baixar PDF (ABNT)
        </a>
        <a className="doc-toggle"
           href={texUrl} download="uropro-saude-publica-2008-2025.tex"
           title="Fonte LaTeX (.tex) — recompilável em qualquer ambiente TeX">
          ⤓ Baixar fonte (.tex)
        </a>
        <a className="doc-toggle"
           href={overleafUrl} target="_blank" rel="noreferrer"
           title="Compilação online em 1 clique no Overleaf">
          ↗ Abrir no Overleaf
        </a>
      </div>
      <p style={{ fontSize: 11, color: 'var(--muted)', marginTop: 10, marginBottom: 0, lineHeight: 1.5 }}>
        <b>Palavras-chave:</b> incontinência urinária; SUS; cirurgia eletiva;
        permanência hospitalar; pandemia COVID-19; represa cirúrgica;
        engenharia de dados.
      </p>
    </div>
  );
}

function Footer() {
  return (
    <footer className="footer panel" style={{ marginTop: 18 }}>
      <div className="footerSection">
        <div className="footerHeading">Origem analítica</div>
        <div style={{ fontSize: 12, color: 'var(--muted)', lineHeight: 1.7 }}>
          A pesquisa empírica desta vertical foi originalmente conduzida por
          <b> Tatieli da Silva</b> como trabalho de conclusão de
          especialização em Enfermagem (2022). A presente versão reproduz
          os achados a partir dos microdados SIH-AIH-RD, adicionando
          dimensões de análise (deflação IPCA, comparação direta entre
          vias, impacto da pandemia) e integrando ao pipeline aberto
          <i> Mirante dos Dados</i>.
        </div>
      </div>

      <div className="footerSection">
        <div className="footerHeading">Fontes</div>
        <div className="footerSource">
          <a href="https://datasus.saude.gov.br/transferencia-de-arquivos/" target="_blank" rel="noreferrer">
            DATASUS — SIH-RD (AIH Reduzida)
          </a>
          <span className="footerDesc">
            FTP <code>/dissemin/publicos/SIHSUS/200801_/Dados/RD/</code> — uma linha por
            internação aprovada, ~1.5M linhas/UF×mês. Filtro por <code>PROC_REA</code> aplicado em bronze.
          </span>
        </div>
        <div className="footerSource">
          <a href="https://sidra.ibge.gov.br/tabela/6579" target="_blank" rel="noreferrer">IBGE SIDRA — Tabela 6579</a>
          <span className="footerDesc">População residente estimada por UF (compartilhada com PBF, Equipamentos, Emendas)</span>
        </div>
        <div className="footerSource">
          <a href="https://api.bcb.gov.br/dados/serie/bcdata.sgs.433/dados?formato=json" target="_blank" rel="noreferrer">BCB SGS — Série 433</a>
          <span className="footerDesc">IPCA mensal · deflator para R$ 2021 (compartilhado entre verticais)</span>
        </div>
        <div className="footerNote">
          Pipeline: bronze (DATASUS DBC → Parquet filtrado por SIGTAP) → silver
          (UF × Ano × Mês × Procedimento × Caráter × Gestão) → gold (UF × Ano ×
          Procedimento, deflacionado, per capita). Reusa as dimensões compartilhadas
          <code> populacao_uf_ano</code> e <code>ipca_deflators_2021</code>.
        </div>
      </div>

      <div className="footerSection">
        <div className="footerHeading">Procedimentos analisados</div>
        <div style={{ fontSize: 12, color: 'var(--muted)', lineHeight: 1.7 }}>
          <b>0409010499</b> — Tratamento Cirúrgico de Incontinência Urinária Via Abdominal<br />
          <b>0409070270</b> — Tratamento Cirúrgico de Incontinência Urinária Por Via Vaginal<br />
          <b>0409020117</b> — Tratamento Cirúrgico de Incontinência Urinária (genérico)<br />
          <i style={{ display: 'block', marginTop: 6 }}>
            Recorte clínico originalmente proposto em TATIELI DA SILVA (2022).
            Para incluir outros procedimentos, basta alterar
            <code> procs_filter</code> na task bronze do job
            <code> job_uropro_refresh</code>.
          </i>
        </div>
      </div>
    </footer>
  );
}

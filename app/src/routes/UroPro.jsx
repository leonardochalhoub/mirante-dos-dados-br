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
import EvolutionBar   from '../components/charts/EvolutionBar';
import DownloadActions from '../components/DownloadActions';
import TechBadges      from '../components/TechBadges';
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

  const evolutionData = useMemo(() => {
    if (!rows) return [];
    const sel = new Set(selectedProcs);
    return years.map((y) => {
      const yr = rows.filter((r) => r.ano === y && sel.has(r.proc_rea));
      // For per-100k, use national totals divided by national pop
      const value = aggregateForMetric(yr, metricKey, /*nationwide*/ true);
      return { year: String(y), value };
    });
  }, [rows, years, selectedProcs, metricKey]);

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
            (Tatieli, 2022) cobrindo 2015–2020 — clique em <b>Ler artigo na tela</b>{' '}
            ou <b>Baixar PDF (ABNT)</b>.
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

              <Panel label="Evolução nacional" sub={metric.label} exportId="uropro-evolucao">
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
function ProcedureMultiSelect({ selected, onChange }) {
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
            {Object.entries(PROCEDURES).map(([code, info]) => (
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

// ─── Doc section: abstract + buttons ─────────────────────────────────────
// CONVENÇÃO Mirante (ver memory/feedback_article_buttons.md): "Ler artigo
// na tela" SEMPRE abre em nova aba (target=_blank) — nunca toggle inline.
// Como UroPro tem artigo data-driven (sem .pdf estático), abrimos a rota
// standalone /incontinencia-urinaria/artigo, que renderiza o artigo
// fora do <Layout> (sem sidebar). O usuário tem o equivalente UX de
// "PDF aberto em nova aba" das outras verticais.
function DocSection() {
  const base = import.meta.env.BASE_URL || '/';
  // HashRouter → o caminho "interno" precisa do prefixo #/.
  const articleUrl = `${base}#/incontinencia-urinaria/artigo`.replace(/\/{2,}/g, '/');

  return (
    <section className="emendas-abstract">
      <div className="doc-block no-print">
        <div className="kicker">Resumo · Working Paper n. 3</div>
        <p style={{ marginTop: 8 }}>
          Este vertical apresenta análise empírica do tratamento cirúrgico
          da incontinência urinária no SUS, partindo dos microdados SIH-AIH-RD
          (uma linha por internação aprovada). Compara as duas vias cirúrgicas
          principais — abdominal (SIGTAP 0409010499) e vaginal (0409070270) —
          em volume, despesa pública (R$ deflacionado IPCA-2021), permanência
          hospitalar e distribuição geográfica entre as 27 unidades federativas.
          A análise reproduz e estende a investigação original de Tatieli
          da Silva, conduzida como trabalho de conclusão de especialização
          em Enfermagem (2022). O artigo é gerado dinamicamente a partir
          da camada Gold — todos os números refletem o estado mais recente do
          pipeline.
        </p>
        <p style={{ fontSize: 12, color: 'var(--muted)', marginTop: 10 }}>
          <b>Palavras-chave:</b> incontinência urinária; SUS; SIH-SUS;
          cirurgia uroginecológica; análise espacial em saúde; dados abertos.
        </p>

        <div className="doc-actions">
          <a
            className="doc-toggle"
            href={articleUrl}
            target="_blank"
            rel="noreferrer"
            title="Abrir o artigo completo em uma nova aba"
          >
            ▾ Ler artigo na tela
          </a>

          <a
            className="doc-toggle doc-toggle-primary"
            href={articleUrl}
            target="_blank"
            rel="noreferrer"
            title="Abrir artigo e usar Ctrl+P / Cmd+P para gerar PDF (formatado em padrão ABNT)"
          >
            ⤓ Baixar PDF (ABNT)
          </a>
        </div>

        <p style={{ fontSize: 11, color: 'var(--muted)', marginTop: 8, marginBottom: 0 }}>
          O artigo abre em nova aba (rota standalone <code>/incontinencia-urinaria/artigo</code>),
          equivalente UX ao "PDF em nova aba" das demais verticais. Para gerar
          um PDF, basta usar a função de impressão do navegador (Ctrl+P / Cmd+P) —
          o CSS <code>@media print</code> formata o artigo em padrão ABNT.
        </p>
      </div>
    </section>
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

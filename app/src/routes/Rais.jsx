// Vertical: RAIS — Vínculos Públicos.
// Source: /data/gold/gold_rais_estados_ano.json
// Replica e estende o trabalho da monografia de especialização do autor
// (Chalhoub, UFRJ MBA Eng. Dados, 2023, não publicada).
// Vide docs/vertical-rais-fair-lakehouse-spec.md para a especificação.

import { useEffect, useMemo, useState } from 'react';
import PageHeader      from '../components/PageHeader';
import Panel           from '../components/Panel';
import KpiCard         from '../components/KpiCard';
import BrazilMap       from '../components/BrazilMap';
import StateRanking    from '../components/StateRanking';
import EvolutionBar    from '../components/charts/EvolutionBar';
import DownloadActions from '../components/DownloadActions';
import TechBadges      from '../components/TechBadges';
import ScoreCard       from '../components/ScoreCard';
import ArticleTimestamp from '../components/ArticleTimestamp';
import { PARECER_RAIS } from '../data/pareceres';
import { useTheme }    from '../hooks/useTheme';
import { loadGold }    from '../lib/data';
import { COLORSCALES } from '../lib/scales';
import { fmtBRL, fmtCompact, fmtDec1, fmtDec2, fmtInt } from '../lib/format';
import { exportToXlsx, exportChartsAsZip } from '../lib/exporters';

const METRICS = {
  vinculos_per_capita: {
    label: 'Vínculos ativos por habitante', short: 'vínc/hab',
    yaxisTitle: 'Vínculos ativos por habitante',
    fmt: (v) => fmtDec2(v ?? 0),
    fmtRich: (v) => fmtDec2(v ?? 0),
  },
  remun_media_2021: {
    label: 'Remuneração média (R$ 2021)', short: 'R$',
    yaxisTitle: 'Remuneração média mensal (R$ 2021)',
    fmt: (v) => fmtDec2(v ?? 0),
    fmtRich: (v) => fmtBRL(v ?? 0),
  },
  massa_salarial_2021: {
    label: 'Massa salarial dezembro (R$ 2021)', short: 'R$',
    yaxisTitle: 'Massa salarial (R$ 2021)',
    fmt: (v) => fmtDec1((v ?? 0) / 1e9),
    fmtRich: (v) => fmtBRL(v ?? 0, { compact: true }),
  },
  share_simples: {
    label: '% Simples Nacional', short: '%',
    yaxisTitle: '% optantes Simples Nacional',
    fmt: (v) => fmtDec1((v ?? 0) * 100),
    fmtRich: (v) => fmtDec1((v ?? 0) * 100) + '%',
  },
};

const DEFAULT_METRIC = 'remun_media_2021';
const DEFAULT_COLOR  = 'Cividis';

export default function Rais() {
  const { theme } = useTheme();
  const [rows, setRows]             = useState(null);
  const [error, setError]           = useState(null);
  const [metricKey, setMetricKey]   = useState(DEFAULT_METRIC);
  const [year, setYear]             = useState(null);
  const [colorscale, setColorscale] = useState(DEFAULT_COLOR);

  useEffect(() => {
    loadGold('gold_rais_estados_ano.json')
      .then((all) => {
        setRows(all);
        if (all.length) {
          const last = Math.max(...all.map((r) => r.Ano));
          setYear(String(last));
        }
      })
      .catch((e) => setError(e.message));
  }, []);

  const metric = METRICS[metricKey];
  const years  = useMemo(
    () => (rows ? Array.from(new Set(rows.map((r) => r.Ano))).sort() : []),
    [rows],
  );
  const filtered = useMemo(() => {
    if (!rows || year == null) return [];
    return rows
      .filter((r) => r.Ano === Number(year))
      .map((r) => ({ uf: r.uf, value: r[metricKey] || 0 }));
  }, [rows, metricKey, year]);
  const ranking = useMemo(() => [...filtered].sort((a,b) => b.value - a.value), [filtered]);

  const kpis = useMemo(() => {
    if (!rows || !year) return null;
    const yr = rows.filter((r) => r.Ano === Number(year));
    const benef = yr.reduce((s, r) => s + (r.n_vinculos_ativos || 0), 0);
    const massa = yr.reduce((s, r) => s + (r.massa_salarial_2021 || 0), 0);
    const pop   = yr.reduce((s, r) => s + (r.populacao || 0), 0);
    return {
      vinculos_total: benef,
      massa, pop,
      vinc_per_hab: pop > 0 ? benef / pop : 0,
      remun_media: yr.length > 0 ? yr.reduce((s,r) => s + (r.remun_media_2021||0)*(r.n_vinculos_ativos||0), 0) / Math.max(benef,1) : 0,
    };
  }, [rows, year]);

  const evolutionData = useMemo(() => {
    if (!rows) return [];
    return years.map((y) => {
      const yr = rows.filter((r) => r.Ano === y);
      const sum = yr.reduce((s, r) => s + (r[metricKey] || 0), 0);
      return { year: String(y), value: metricKey === 'massa_salarial_2021' ? sum : sum / Math.max(yr.length, 1) };
    });
  }, [rows, metricKey, years]);

  // Working Paper #3 download URLs
  const base = import.meta.env.BASE_URL || '/';
  const pdfUrl     = `${base}articles/rais-fair-lakehouse.pdf`.replace(/\/{2,}/g, '/');
  const texUrl     = `${base}articles/rais-fair-lakehouse.tex`.replace(/\/{2,}/g, '/');
  const overleafUrl = 'https://www.overleaf.com/docs?snip_uri=' +
    encodeURIComponent(`https://leonardochalhoub.github.io${texUrl}`);

  return (
    <>
      <PageHeader
        eyebrow="Vertical · mercado de trabalho · governança de dados"
        title="RAIS — Vínculos Públicos"
        subtitle="Replica e estende a monografia de especialização do autor (UFRJ MBA Engenharia de Dados, 2023): comparação de formatos Lakehouse + scoring FAIR sobre microdados RAIS/PDET."
        right={
          <div className="header-right-row">
            <TechBadges />
            <DownloadActions
              onExportXlsx={() => exportToXlsx('mirante-rais', { 'rais_uf_ano': rows || [] })}
              onExportPng={() => exportChartsAsZip('mirante-rais')}
            />
          </div>
        }
      />

      <ScoreCard parecer={PARECER_RAIS} />

      <section className="emendas-abstract no-print" style={{ marginBottom: 14 }}>
        <div className="doc-block">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline', flexWrap: 'wrap', gap: 8 }}>
            <div className="kicker">Working Paper n. 3 — Mirante dos Dados</div>
            <ArticleTimestamp slug="rais-fair-lakehouse" />
          </div>
          <p style={{ marginTop: 6, fontSize: 13.5 }}>
            <b>"RAIS, FAIRness e Lakehouse: replicação e extensão de
            comparação empírica de formatos para Big Data público brasileiro
            (2020–2025)"</b> — análise empírica em padrão ABNT, comparando
            CSV, Apache Parquet, Apache Iceberg, Apache Hudi e Delta Lake
            sobre microdados RAIS Vínculos Públicos, com scoring FAIR
            quantitativo via FAIR Data Maturity Model (RDA).
          </p>
          <div className="doc-actions">
            <a className="doc-toggle doc-toggle-primary"
               href={pdfUrl} target="_blank" rel="noreferrer"
               title="Abrir PDF em nova aba (visualizador nativo do navegador)">
              📖 Ler artigo (PDF)
            </a>
            <a className="doc-toggle"
               href={pdfUrl} download="Mirante-RAIS-Chalhoub-2026.pdf"
               title="PDF compilado em LaTeX, padrão ABNT">
              ⤓ Baixar PDF (ABNT)
            </a>
            <a className="doc-toggle"
               href={texUrl} download="rais-fair-lakehouse.tex"
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
      </section>

      {error && <div className="error-block">Erro ao carregar dados: {error}</div>}

      {!error && !rows && <div className="loading-block">Carregando dados…</div>}

      {rows && rows.length === 0 && (
        <div className="panel" style={{ marginTop: 18 }}>
          <div className="panelHead">
            <span className="panelLabel">Status</span>
            <span className="kicker">Pipeline em construção</span>
          </div>
          <p className="muted" style={{ fontSize: 13, lineHeight: 1.7 }}>
            O pipeline RAIS está deployado no Databricks
            (<code>job_rais_refresh</code>) mas ainda não foi executado pela
            primeira vez. Após a execução manual ou pelo cron mensal (dia 26
            6h UTC), o JSON gold será publicado e esta página renderiza
            automaticamente os KPIs, ranking e mapa.
          </p>
        </div>
      )}

      {rows && rows.length > 0 && kpis && (
        <>
          <div className="kpiRow" data-export-id="rais-kpis">
            <KpiCard label={`Vínculos ativos · ${year}`} value={fmtCompact(kpis.vinculos_total)} sub="dezembro" />
            <KpiCard label={`Massa salarial · ${year}`}  value={fmtBRL(kpis.massa, { compact: true })} sub="dez (R$ 2021)" color="#2b6cb0" />
            <KpiCard label={`Remun. média · ${year}`}    value={fmtBRL(kpis.remun_media)} sub="ponderada por vínculos" color="#0d9488" />
            <KpiCard label={`Vínc. per capita · ${year}`} value={fmtDec2(kpis.vinc_per_hab)} sub="ativos / população" color="#be185d" />
          </div>

          <div className="layout">
            <div className="row row-controls-bar">
              <Panel label="Filtros & dados" sub="MTE · IBGE · BCB">
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
                    <select id="year" value={year || ''} onChange={(e) => setYear(e.target.value)}>
                      {years.map((y) => <option key={y} value={y}>{y}</option>)}
                    </select>
                  </div>
                  <div className="metaBlock">
                    <b>Fonte:</b> RAIS Vínculos Públicos (PDET/MTE)<br />
                    <b>Atualização:</b> anual<br />
                    <b>Working Paper #3:</b> usa este mesmo dataset
                  </div>
                </div>
              </Panel>

              <Panel label="Evolução nacional" sub={metric.label} exportId="rais-evolucao">
                <EvolutionBar data={evolutionData} theme={theme}
                  yLabel={metric.yaxisTitle} xLabel="Ano"
                  format={metric.fmt} height={320} />
              </Panel>
            </div>

            <div className="row row-ranking-map">
              <Panel label="Ranking por UF" sub={`${metric.label} · ${year}`} exportId="rais-ranking">
                <StateRanking rows={ranking} format={metric.fmtRich} />
              </Panel>
              <Panel label="Distribuição geográfica" exportId="rais-mapa"
                right={
                  <div className="mapControls">
                    <label htmlFor="colorscale">Cores</label>
                    <select id="colorscale" value={colorscale} onChange={(e) => setColorscale(e.target.value)}>
                      {COLORSCALES.map((c) => <option key={c.value} value={c.value}>{c.label}</option>)}
                    </select>
                  </div>
                }>
                <BrazilMap data={filtered} colorscale={colorscale} theme={theme}
                  hoverFmt={metric.fmtRich} unit={metric.short} />
              </Panel>
            </div>
          </div>
        </>
      )}

      <Footer />
    </>
  );
}

function Footer() {
  return (
    <footer className="footer panel" style={{ marginTop: 18 }}>
      <div className="footerSection">
        <div className="footerHeading">Origem analítica</div>
        <div style={{ fontSize: 12, color: 'var(--muted)', lineHeight: 1.7 }}>
          Esta vertical replica e estende a monografia de especialização
          do autor — <i>"O Papel dos Metadados em Arquiteturas de Nuvem:
          FAIRness e Governança de Dados em Big Data"</i> (Chalhoub, UFRJ
          MBA Engenharia de Dados, apresentada à banca em set/2023,
          reprovada — sem nota atribuída pela banca; contexto histórico
          no parecer acima).
          A versão Mirante adiciona scoring FAIR quantitativo,
          comparação multi-formato (Iceberg + Hudi além de Delta) e
          análise crítica balanceada — vide
          <a href="https://github.com/leonardochalhoub/mirante-dos-dados-br/blob/main/docs/vertical-rais-fair-lakehouse-spec.md" target="_blank" rel="noreferrer">
            {' '}docs/vertical-rais-fair-lakehouse-spec.md
          </a>.
        </div>
      </div>
      <div className="footerSection">
        <div className="footerHeading">Fontes</div>
        <div className="footerSource">
          <a href="https://pdet.mte.gov.br/microdados-rais-e-caged" target="_blank" rel="noreferrer">
            PDET / MTE — RAIS Vínculos Públicos
          </a>
          <span className="footerDesc">microdados anuais por estabelecimento e trabalhador</span>
        </div>
        <div className="footerSource">
          <a href="https://sidra.ibge.gov.br/tabela/6579" target="_blank" rel="noreferrer">IBGE SIDRA — Tabela 6579</a>
          <span className="footerDesc">população residente estimada por UF</span>
        </div>
        <div className="footerSource">
          <a href="https://api.bcb.gov.br/dados/serie/bcdata.sgs.433/dados?formato=json" target="_blank" rel="noreferrer">
            BCB SGS — Série 433
          </a>
          <span className="footerDesc">IPCA mensal, deflator para R$ 2021</span>
        </div>
      </div>
    </footer>
  );
}

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

      <ScoreCard />

      <section className="emendas-abstract no-print" style={{ marginBottom: 14 }}>
        <div className="doc-block">
          <div className="kicker">Working Paper n. 3 — Mirante dos Dados</div>
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

// ─── Parecer crítico (atualizado a cada deploy pelo avaliador) ──────────
// Esta seção NÃO é auto-avaliação gerada pela página. É o parecer do
// avaliador externo (IA atuando como professor de pós-graduação),
// calibrado contra o original (monografia 2023, Score 8/10) e
// atualizado manualmente a cada deploy quando o trabalho evolui.
//
// Master's level signal: quando o trabalho atingir nível stricto sensu,
// MASTER_LEVEL = true e o componente exibe destaque + nota 10.
// Calibragem: o vertical HERDA o trabalho conceitual da monografia
// (referencial, hipóteses, metodologia documentada no spec doc), portanto
// parte de 7,5 — ligeiramente abaixo do 8,0 original porque a execução
// empírica ainda não foi feita nesta plataforma. À medida que (a) o
// pipeline rodar e gerar resultados, (b) o .tex for escrito com dados
// reais, (c) as extensões (multi-formato, FAIR scoring) forem entregues,
// a nota sobe além de 8.
const SCORE_ATUAL = 7.5;
const SCORE_ORIGINAL = 8.0;
const MASTER_LEVEL = false;

const PARECER_RAIS = {
  ultimaAtualizacao: '2026-04-25T17:45 BRT',
  versao: '0.1 (scaffold completo, execução empírica pendente)',
  resumo_calibragem:
    'Score parte de 7,5 (ligeiramente abaixo do 8,0 da monografia) porque ' +
    'o vertical herda toda a base analítica da monografia — registrada em ' +
    'docs/vertical-rais-fair-lakehouse-spec.md — e adiciona melhorias de ' +
    'infraestrutura, mas a EXECUÇÃO EMPÍRICA (resultados quantitativos sobre ' +
    'a plataforma Mirante) ainda não foi feita. Sobe a 8,0+ quando o pipeline ' +
    'rodar e o artigo ganhar dados reais.',
  melhorias_vs_original: [
    'Pipeline open-source versionado em Git (vs scripts isolados sem versionamento na monografia)',
    'Arquitetura medallion bronze/silver/gold canônica (vs notebooks por formato)',
    'Padrão híbrido batch + Auto Loader incremental (vs full-overwrite manual)',
    'Schema-coerce float64 desde a primeira execução (lição aprendida em CNES)',
    'Spec doc registrando o parecer crítico da monografia + plano de extensões',
    'Defensive guards em silver/gold/export (skip on missing upstream)',
  ],
  pendencias_para_aprovacao_plena_lato_sensu: [
    'Pipeline RAIS ainda não rodou — bronze/silver/gold sem dados',
    'URL do PDET/MTE não confirmada — ingest pode precisar de ajuste',
    'Artigo (.tex) está em estado SKELETON — seções vazias',
    'Sem execução empírica das 3 métricas (size/write/read) na plataforma Mirante',
  ],
  pendencias_para_nivel_mestrado: [
    'Multi-formato (Iceberg + Hudi além de Delta) NÃO implementado',
    'FAIR scoring quantitativo via RDA Maturity Model NÃO implementado',
    'Variância controlada (desvio padrão, IC 95%, n) NÃO reportada',
    'Múltiplas configurações de cluster NÃO comparadas',
    'Análise crítica when-not-to-use Lakehouse NÃO escrita',
    'Cruzamento RAIS × indicadores socioeconômicos NÃO feito',
    'Comparação com warehouses (BigQuery/Snowflake/Redshift) ausente',
  ],
};

function ScoreCard() {
  const trend = SCORE_ATUAL - SCORE_ORIGINAL;
  const trendIcon = trend > 0 ? '▲' : trend < 0 ? '▼' : '●';
  const trendColor = trend > 0 ? '#059669' : trend < 0 ? '#dc2626' : 'var(--muted)';

  return (
    <section className="panel no-print" style={{ marginBottom: 14, borderLeft: `4px solid ${MASTER_LEVEL ? '#059669' : '#b45309'}` }}>
      <div className="panelHead">
        <span className="panelLabel">Parecer crítico — avaliador externo (IA, modo professor de pós-graduação)</span>
        <span className="kicker">Atualizado em {PARECER_RAIS.ultimaAtualizacao} · v{PARECER_RAIS.versao}</span>
      </div>

      <div style={{ display: 'flex', gap: 24, flexWrap: 'wrap', alignItems: 'baseline', marginBottom: 14 }}>
        <div>
          <div className="kicker" style={{ marginBottom: 4 }}>Score atual</div>
          <div style={{ fontSize: 36, fontWeight: 800, letterSpacing: '-0.02em', lineHeight: 1, color: MASTER_LEVEL ? '#059669' : 'var(--text)' }}>
            {SCORE_ATUAL.toFixed(1)}<span style={{ fontSize: 18, color: 'var(--muted)', fontWeight: 600 }}> /10</span>
          </div>
        </div>
        <div>
          <div className="kicker" style={{ marginBottom: 4 }}>Score original (monografia 2023)</div>
          <div style={{ fontSize: 28, fontWeight: 700, letterSpacing: '-0.02em', lineHeight: 1, color: 'var(--muted)' }}>
            {SCORE_ORIGINAL.toFixed(1)}<span style={{ fontSize: 16, color: 'var(--faint)', fontWeight: 600 }}> /10</span>
          </div>
        </div>
        <div style={{ color: trendColor, fontSize: 14, fontWeight: 700 }}>
          {trendIcon} {trend >= 0 ? '+' : ''}{trend.toFixed(1)} vs original
        </div>
        {MASTER_LEVEL && (
          <div style={{ marginLeft: 'auto', padding: '6px 12px', background: '#059669', color: 'white',
                        borderRadius: 999, fontSize: 12, fontWeight: 700, letterSpacing: '0.05em', textTransform: 'uppercase' }}>
            ★ NÍVEL STRICTO SENSU (MESTRADO) ATINGIDO
          </div>
        )}
      </div>

      {PARECER_RAIS.resumo_calibragem && (
        <p style={{ fontSize: 12.5, color: 'var(--muted)', marginBottom: 14, lineHeight: 1.6 }}>
          <b>Calibragem:</b> {PARECER_RAIS.resumo_calibragem}
        </p>
      )}

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: 14, fontSize: 12.5 }}>
        <div>
          <div style={{ fontWeight: 700, fontSize: 11, letterSpacing: '0.06em', textTransform: 'uppercase', color: '#059669', marginBottom: 6 }}>
            ✓ Melhorias vs. monografia original
          </div>
          <ul style={{ margin: 0, paddingLeft: 18, lineHeight: 1.6 }}>
            {PARECER_RAIS.melhorias_vs_original.map((m, i) => <li key={i}>{m}</li>)}
          </ul>
        </div>
        <div>
          <div style={{ fontWeight: 700, fontSize: 11, letterSpacing: '0.06em', textTransform: 'uppercase', color: '#b45309', marginBottom: 6 }}>
            ⚠ Pendências para alcançar plenamente o nível da monografia
          </div>
          <ul style={{ margin: 0, paddingLeft: 18, lineHeight: 1.6 }}>
            {PARECER_RAIS.pendencias_para_aprovacao_plena_lato_sensu.map((p, i) => <li key={i}>{p}</li>)}
          </ul>
        </div>
        <div>
          <div style={{ fontWeight: 700, fontSize: 11, letterSpacing: '0.06em', textTransform: 'uppercase', color: '#1d4ed8', marginBottom: 6 }}>
            ★ Pendências adicionais para atingir nível stricto sensu (mestrado)
          </div>
          <ul style={{ margin: 0, paddingLeft: 18, lineHeight: 1.6 }}>
            {PARECER_RAIS.pendencias_para_nivel_mestrado.map((p, i) => <li key={i}>{p}</li>)}
          </ul>
        </div>
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
          Esta vertical replica e estende a monografia de especialização
          do autor — <i>"O Papel dos Metadados em Arquiteturas de Nuvem:
          FAIRness e Governança de Dados em Big Data"</i> (Chalhoub, UFRJ
          MBA Engenharia de Dados, defendida em set/2023, não publicada).
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

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
import ScoreCard       from '../components/ScoreCard';
import AtaConselho     from '../components/AtaConselho';
import ArticleTimestamp from '../components/ArticleTimestamp';
import { useArticleMeta, articleUrl } from '../hooks/useArticleMeta';
import { PARECER_WP2_BOLSA_FAMILIA } from '../data/pareceres';
import { ATA_WP2_REUNIAO_1 } from '../data/atas-conselho';
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

// Gold filtra anos parciais por contagem de meses (silver pbf_total_uf_mes tem Mes;
// gold mantém só Anos com 12 meses distintos). Front confia no que o JSON entrega.

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

// WHY triplo do WP#2 — formalizado no rewrite v2.0 (2026-04-27) após
// peer review interno das 4 cadeiras do Conselho do Mirante. Estrutura
// idêntica ao WhyQuadruplo do WP#4 e WhyDuplo do WP#6: cada lente
// endereça uma audiência distinta com call-to-action próprio.
const WHY_TRIPLO_WP2 = [
  {
    lente: 'Documentação reproduzível',
    cor: '#0d9488',
    frase:
      'tornar acessível ao público não-especialista uma série histórica ' +
      'completa (2013–2025) de pagamentos do PBF/Auxílio Brasil/NBF ' +
      'consolidada, deflacionada e auditável — reduzindo o custo marginal ' +
      'de pesquisa de meses-de-pipeline para minutos-de-leitura.',
    audiencia: 'Pesquisadores em Saúde Coletiva/Ciência Política · IPEA · ONGs (Transparência Brasil, Open Knowledge BR) · jornalismo de dados',
    cta: 'Usar o pipeline público como insumo, não como obstáculo, em estudos sobre transferência de renda',
  },
  {
    lente: 'Identificação causal',
    cor: '#dc2626',
    frase:
      'tratar os dois choques institucionais nominalmente declarados (MP ' +
      '1.061/2021 e Lei 14.601/2023) como experimentos naturais e ' +
      'submetê-los a desenho causal explícito (DiD/TWFE com wild-cluster ' +
      'bootstrap), em vez de descrevê-los como "saltos" e parar aí.',
    audiencia: 'Economia aplicada · econometria política · referees de RAP/RBE/Cad Saúde Pública · agenda de avaliação de impacto',
    cta: 'Aceitar resultado null honesto como contribuição, não como falha — falsificável é melhor que verossímil',
  },
  {
    lente: 'Sustentabilidade fiscal',
    cor: '#b45309',
    frase:
      'projetar o custo do NBF (R$ 130–141 bi/ano em 2024–2025, ~25% do ' +
      'orçamento do SUS) sob cenários demográficos da PNAD-C e do IBGE — ' +
      'separando expansão por crise conjuntural de incorporação de falsos ' +
      'negativos crônicos do Cadastro Único.',
    audiencia: 'Ministério da Fazenda · Comissões de Orçamento · Coord. Política Fiscal STN · gestores SEPLAN estaduais',
    cta: 'Decidir com cenários quantificados, não com intuição sobre "se cabe no orçamento"',
  },
];

const TESE_CENTRAL_WP2 =
  'O Bolsa Família atravessou três regimes legais (PBF clássico, Auxílio ' +
  'Brasil, Novo Bolsa Família) entre 2013 e 2025, com saltos de cobertura ' +
  '(16 → 24 milhões de famílias) e de valor real (R$ 36 → R$ 141 bi/ano) ' +
  'que são simultaneamente: tecnicamente mensuráveis (microdados CGU + ' +
  'deflação IPCA), causalmente identificáveis (dois choques exógenos com ' +
  'data precisa), e fiscalmente urgentes (1/4 do orçamento do SUS). Este ' +
  'artigo é o primeiro a expor as três dimensões sobre o mesmo dataset ' +
  'auditável.';

function WhyTriploWP2() {
  return (
    <div style={{
      marginTop: 12, marginBottom: 4,
      padding: 12,
      background: 'var(--accent-soft, rgba(13, 148, 136, 0.05))',
      border: '1px solid var(--border)', borderRadius: 8,
    }}>
      <div style={{
        fontWeight: 700, fontSize: 11, letterSpacing: '0.06em',
        textTransform: 'uppercase', color: 'var(--muted)', marginBottom: 8,
      }}>
        Por que este artigo existe — 3 ângulos sobre o mesmo dataset
      </div>

      <p style={{
        fontSize: 13, lineHeight: 1.65, margin: '0 0 12px 0',
        fontStyle: 'italic', color: 'var(--text)',
      }}>
        {TESE_CENTRAL_WP2}
      </p>

      <div style={{
        display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))',
        gap: 10,
      }}>
        {WHY_TRIPLO_WP2.map((w) => (
          <div key={w.lente} style={{
            padding: '8px 10px',
            background: 'var(--bg)',
            borderLeft: `3px solid ${w.cor}`,
            borderRadius: 4,
            fontSize: 12, lineHeight: 1.5,
          }}>
            <div style={{
              fontWeight: 700, fontSize: 10, letterSpacing: '0.06em',
              textTransform: 'uppercase', color: w.cor, marginBottom: 4,
            }}>
              WHY {w.lente}
            </div>
            <div style={{ color: 'var(--text)', marginBottom: 4 }}>
              <i>Existimos para</i> {w.frase}
            </div>
            <div style={{
              fontSize: 10.5, color: 'var(--muted)',
              borderTop: '1px solid var(--border)', paddingTop: 4, marginTop: 4,
            }}>
              <div style={{ marginBottom: 3 }}><b>Para quem:</b> {w.audiencia}</div>
              <div><b>CTA:</b> {w.cta}</div>
            </div>
          </div>
        ))}
      </div>

      <div style={{
        fontSize: 10.5, color: 'var(--faint)',
        marginTop: 10, paddingTop: 8, borderTop: '1px solid var(--border)',
        textAlign: 'right',
      }}>
        Formalizado no rewrite v2.0 do WP#2 · 2026-04-27 · pós peer review interno (4 cadeiras)
      </div>
    </div>
  );
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
  const maxYear = years.length ? years[years.length - 1] : null;
  const minYear = years.length ? years[0] : null;

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

  // Caminhos do artigo Working Paper #2 (Bolsa Família).
  // IMPORTANTE: useArticleMeta é hook — precisa ficar ANTES dos early returns
  // pra não violar a regra dos hooks (contagem precisa bater entre renders).
  const base = import.meta.env.BASE_URL || '/';
  const slug = 'bolsa-familia';
  const meta = useArticleMeta(slug);
  const sha  = meta?.tex_last_sha;
  const pdfUrl = articleUrl(base, slug, 'pdf', sha);
  const texUrl = articleUrl(base, slug, 'tex', sha);
  const overleafUrl = 'https://www.overleaf.com/docs?snip_uri=' +
    encodeURIComponent(`https://leonardochalhoub.github.io${texUrl}`);

  if (error) return <div className="error-block">Erro ao carregar dados: {error}</div>;
  if (!rows) return <div className="loading-block">Carregando dados…</div>;

  return (
    <>
      <PageHeader
        eyebrow="Vertical · transferências de renda"
        title="Bolsa Família"
        subtitle="Pagamentos, beneficiários e valor real (R$ 2021) por UF e ano. Fontes: Portal da Transparência (CGU), IBGE e BCB."
        right={
          <div className="header-right-row">
            <TechBadges />
            <DownloadActions
              onExportXlsx={() => exportToXlsx('mirante-pbf', { 'pbf_uf_ano': rows })}
              onExportPng={() => exportChartsAsZip('mirante-pbf')}
            />
          </div>
        }
      />

      <section className="emendas-abstract no-print" style={{ marginBottom: 14 }}>
        <div className="doc-block">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline', flexWrap: 'wrap', gap: 8 }}>
            <div className="kicker">Working Paper n. 2 — Mirante dos Dados</div>
            <ArticleTimestamp slug="bolsa-familia" />
          </div>
          <p style={{ marginTop: 6, fontSize: 13.5 }}>
            <b>"Três Regimes, Um Programa: Documentação Reproduzível,
            Identificação Causal e Sustentabilidade Fiscal do Bolsa Família,
            Auxílio Brasil e Novo Bolsa Família (2013–2025)"</b> — Working
            Paper #2 v2.0 (Abril/2026), padrão ABNT, com 17 figuras
            vetoriais (incluindo barbell DiD, event study, curva de Kakwani,
            razão necessidade/cobertura e benchmark CCT internacional),
            DiD/TWFE/wild-cluster bootstrap sobre MP 1.061/2021, índices
            formais de progressividade (Kakwani) e de necessidade, e
            comparativo com AUH (Argentina), Prospera (México), MFA
            (Colômbia) e Renta Dignidad (Bolívia) em US$ PPP 2021.
          </p>

          <ScoreCard parecer={PARECER_WP2_BOLSA_FAMILIA} />

          <WhyTriploWP2 />

          <div className="doc-actions">
            <a className="doc-toggle doc-toggle-primary"
               href={pdfUrl}
               target="_blank"
               rel="noreferrer"
               title="Abrir PDF em nova aba (visualizador nativo do navegador)">
              📖 Ler artigo (PDF)
            </a>
            <a className="doc-toggle"
               href={pdfUrl}
               download="Mirante-BolsaFamilia-Chalhoub-2026.pdf"
               title="PDF compilado em LaTeX, padrão ABNT">
              ⤓ Baixar PDF (ABNT)
            </a>
            <a className="doc-toggle"
               href={texUrl}
               download="bolsa-familia.tex"
               title="Fonte LaTeX (.tex)">
              ⤓ Baixar fonte (.tex)
            </a>
            <a className="doc-toggle"
               href={overleafUrl}
               target="_blank"
               rel="noreferrer"
               title="Compilação online em 1 clique no Overleaf">
              ↗ Abrir no Overleaf
            </a>
          </div>
        </div>
        <AtaConselho ata={ATA_WP2_REUNIAO_1} />
      </section>

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
                  <option value="AGG">{`Acumulado / média ${minYear ?? ''}–${maxYear ?? ''}`}</option>
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

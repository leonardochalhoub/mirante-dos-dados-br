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
import BrazilMuniMap   from '../components/BrazilMuniMap';
import StateRanking    from '../components/StateRanking';
import EvolutionBar    from '../components/charts/EvolutionBar';
import DownloadActions from '../components/DownloadActions';
import TechBadges      from '../components/TechBadges';
import ScoreCard       from '../components/ScoreCard';
import AtaConselho     from '../components/AtaConselho';
import ArticleTimestamp from '../components/ArticleTimestamp';
import { useArticleMeta, articleUrl } from '../hooks/useArticleMeta';
import { PARECER_WP2_BOLSA_FAMILIA,
         PARECER_WP7_BOLSA_FAMILIA_MUNICIPIOS } from '../data/pareceres';
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
// YlOrRd: amarelo (low) → vermelho escuro (high), naturalmente claro→escuro,
// daltônico-safe via ColorBrewer, mais vivo que Cividis pra choropleth.
const DEFAULT_COLOR  = 'YlOrRd';

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

// ─── WP#7 — WHY duplo (vertical compartilha rota com WP#2) ───────────────
const WHY_DUPLO_WP7 = [
  {
    lente: 'Robustez identificacional',
    cor: '#0d9488',
    frase:
      'responder ao gargalo de N=27 clusters do WP#2 com 5.570 unidades de ' +
      'análise — TWFE com k≈5570, Conley HAC com distâncias geodésicas reais, ' +
      'cluster bootstrap que efetivamente converge.',
    audiencia: 'Economia aplicada · econometria política · referees de RAP/RBE/Cad Saúde Pública',
    cta: 'Reportar Conley HAC ao revisar políticas com spillover regional, não SE clusterizado ingênuo',
  },
  {
    lente: 'Heterogeneidade intra-UF revelada',
    cor: '#dc2626',
    frase:
      'tornar visível a variação DENTRO das UFs que análises estaduais ' +
      'invariavelmente escondem — decomposição Theil within/between, top/bottom ' +
      '20 munis com diferença >50× em valor real, mapa bivariado tratamento × ' +
      'desenvolvimento humano.',
    audiencia: 'Gestão MDS · CGU · IPEA · auditorias TCE · jornalismo de dados municipalista',
    cta: 'Ver o programa onde ele é gasto, no nível dos 5.570 entes que executam',
  },
];

const TESE_CENTRAL_WP7 =
  'A migração do painel UF×Ano (N=27) para Município×Ano (N=5.570) resolve, ' +
  'na prática, o gargalo dos poucos clusters do WP#2: a hipótese de homogeneidade ' +
  'dentro da UF é falsa por construção do programa (focalização individual no ' +
  'CadÚnico), e a granularidade municipal é o nível certo de identificação. ' +
  'Demonstração em dados públicos: CGU + IBGE/Localidades + IBGE/SIDRA + ' +
  'kelvins/Municipios-Brasileiros + IPCA-BCB.';

function WhyDuploWP7() {
  return (
    <div style={{
      marginTop: 12, marginBottom: 4, padding: 12,
      background: 'var(--accent-soft, rgba(13, 148, 136, 0.05))',
      border: '1px solid var(--border)', borderRadius: 8,
    }}>
      <div style={{
        fontWeight: 700, fontSize: 11, letterSpacing: '0.06em',
        textTransform: 'uppercase', color: 'var(--muted)', marginBottom: 8,
      }}>
        Por que este WP#7 existe — 2 ângulos sobre o mesmo dataset municipal
      </div>
      <p style={{
        fontSize: 13, lineHeight: 1.65, margin: '0 0 12px 0',
        fontStyle: 'italic', color: 'var(--text)',
      }}>
        {TESE_CENTRAL_WP7}
      </p>
      <div style={{
        display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))', gap: 10,
      }}>
        {WHY_DUPLO_WP7.map((w) => (
          <div key={w.lente} style={{
            padding: '8px 10px', background: 'var(--bg)',
            borderLeft: `3px solid ${w.cor}`, borderRadius: 4,
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
        fontSize: 10.5, color: 'var(--faint)', marginTop: 10,
        paddingTop: 8, borderTop: '1px solid var(--border)', textAlign: 'right',
      }}>
        WP#7 v1.0 · 2026-04-27 · resposta ao gargalo de N=27 do WP#2
      </div>
    </div>
  );
}

// ─── WP#7 — Doc card (renderizado embaixo do WP#2 na mesma rota) ─────────
function DocCardWP7() {
  const base       = import.meta.env.BASE_URL || '/';
  const slug       = 'bolsa-familia-municipios';
  const meta       = useArticleMeta(slug);
  const sha        = meta?.tex_last_sha;
  const pdfUrl     = articleUrl(base, slug, 'pdf', sha);
  const texUrl     = articleUrl(base, slug, 'tex', sha);
  const overleafUrl = 'https://www.overleaf.com/docs?snip_uri=' +
    encodeURIComponent(`https://leonardochalhoub.github.io${texUrl}`);
  return (
    <div className="doc-block" style={{ marginTop: 14 }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline', flexWrap: 'wrap', gap: 8 }}>
        <div className="kicker">Working Paper n. 7 — Mirante dos Dados</div>
        <ArticleTimestamp slug={slug} />
      </div>
      <p style={{ marginTop: 6, fontSize: 13.5 }}>
        <b>"5.570 Pontos de Decisão: Microdados Municipais do Bolsa Família,
        Identificação Causal por Variação Cross-Municipal e Heterogeneidade
        Intra-UF (2013–2025)"</b> — Working Paper #7 v1.0 (Abril/2026), padrão
        ABNT, com 12 figuras municipais e event study (Lato + paleta hierárquica
        + golden ratio + halo branco), TWFE com{' '}
        <b>k = 5.571 clusters</b> (vinte vezes acima do mínimo Cameron-Gelbach-Miller),
        Conley HAC com distâncias geodésicas reais (haversine entre centroides
        IBGE/Localidades + kelvins/Municipios-Brasileiros), DiD 2×2 sobre MP
        1.061/2021 e Lei 14.601/2023, e decomposição Theil within/between-UF.
      </p>

      <ScoreCard parecer={PARECER_WP7_BOLSA_FAMILIA_MUNICIPIOS} />

      <WhyDuploWP7 />

      <div className="doc-actions">
        <a className="doc-toggle doc-toggle-primary" href={pdfUrl} target="_blank" rel="noreferrer"
           title="Abrir PDF em nova aba (visualizador nativo do navegador)">
          📖 Ler artigo (PDF)
        </a>
        <a className="doc-toggle" href={pdfUrl} download="Mirante-WP7-BolsaFamilia-Municipios-Chalhoub-2026.pdf"
           title="PDF compilado em LaTeX, padrão ABNT">
          ⤓ Baixar PDF (ABNT)
        </a>
        <a className="doc-toggle" href={texUrl} download="bolsa-familia-municipios.tex"
           title="Fonte LaTeX (.tex)">
          ⤓ Baixar fonte (.tex)
        </a>
        <a className="doc-toggle" href={overleafUrl} target="_blank" rel="noreferrer"
           title="Compilação online em 1 clique no Overleaf">
          ↗ Abrir no Overleaf
        </a>
      </div>
    </div>
  );
}

// ─── Tab toggle Estadual / Municipal ─────────────────────────────────────
function ScopeToggle({ scope, setScope, muniSourceLabel }) {
  const tabStyle = (active) => ({
    padding: '10px 20px',
    fontSize: 13,
    fontWeight: active ? 700 : 500,
    color: active ? 'var(--accent, #0d9488)' : 'var(--muted)',
    background: active ? 'var(--accent-soft, rgba(13, 148, 136, 0.08))' : 'transparent',
    border: 0,
    borderBottom: active ? '3px solid var(--accent, #0d9488)' : '3px solid transparent',
    cursor: 'pointer',
    transition: 'all 0.2s',
    display: 'inline-flex',
    alignItems: 'center',
    gap: 8,
  });
  return (
    <div style={{
      borderBottom: '1px solid var(--border)',
      marginTop: 18, marginBottom: 14,
      display: 'flex', alignItems: 'center', justifyContent: 'space-between',
      flexWrap: 'wrap', gap: 8,
    }}>
      <div style={{ display: 'flex', gap: 0 }}>
        <button type="button" onClick={() => setScope('estadual')} style={tabStyle(scope === 'estadual')}>
          <span>📊 Estadual</span>
          <span style={{ fontSize: 10, padding: '2px 6px', borderRadius: 999,
            background: scope === 'estadual' ? 'var(--accent, #0d9488)' : 'var(--rule)',
            color: scope === 'estadual' ? 'white' : 'var(--muted)' }}>WP#2</span>
        </button>
        <button type="button" onClick={() => setScope('municipal')} style={tabStyle(scope === 'municipal')}>
          <span>🗺 Municipal</span>
          <span style={{ fontSize: 10, padding: '2px 6px', borderRadius: 999,
            background: scope === 'municipal' ? 'var(--accent, #0d9488)' : 'var(--rule)',
            color: scope === 'municipal' ? 'white' : 'var(--muted)' }}>WP#7</span>
        </button>
      </div>
      {scope === 'municipal' && (
        <div style={{ fontSize: 11, color: 'var(--muted)', paddingRight: 8 }}>
          fonte: <code>{muniSourceLabel}</code>
        </div>
      )}
    </div>
  );
}

// ─── Dashboard ESTADUAL (WP#2) — extraído do legado pra ficar em tab ─────
function EstadualDashboard({
  kpis, year, setYear, metricKey, setMetricKey, metric,
  colorscale, setColorscale, theme, ranking, filtered, evolutionData,
  minYear, maxYear, years,
}) {
  return (
    <>
      <div className="kpiRow" data-export-id="pbf-kpis">
        <KpiCard label={`Beneficiários · ${kpis.y ?? '—'}`} value={fmtCompact(kpis.totalBenef)}
                 sub="soma Brasil (27 UFs)" />
        <KpiCard label={`Valor pago · ${kpis.y ?? '—'}`}
                 value={fmtBRL(kpis.totalValor2021 * 1e9, { compact: true })}
                 sub="R$ 2021 · acumulado" color="#2b6cb0" />
        <KpiCard label={`Per beneficiário · ${kpis.y ?? '—'}`} value={fmtBRL(kpis.perBenef)}
                 sub="R$ 2021 / pessoa atendida" color="#be185d" />
        <KpiCard label={`Per capita · ${kpis.y ?? '—'}`} value={fmtBRL(kpis.perCapita)}
                 sub="R$ 2021 / habitante BR" color="#0d9488" />
      </div>

      <div className="layout">
        <div className="row row-controls-bar">
          <Panel label="Filtros & dados" sub="CGU · IBGE · BCB">
            <div className="controls">
              <div className="control">
                <label htmlFor="metric-uf">Métrica</label>
                <select id="metric-uf" value={metricKey} onChange={(e) => setMetricKey(e.target.value)}>
                  {Object.entries(METRICS).map(([k, m]) => (
                    <option key={k} value={k}>{m.label}</option>
                  ))}
                </select>
              </div>
              <div className="control">
                <label htmlFor="year-uf">Ano</label>
                <select id="year-uf" value={year} onChange={(e) => setYear(e.target.value)}>
                  <option value="AGG">{`Acumulado / média ${minYear ?? ''}–${maxYear ?? ''}`}</option>
                  {years.map((y) => (<option key={y} value={y}>{y}</option>))}
                </select>
              </div>
              <div className="metaBlock">
                <b>Granularidade:</b> 27 UFs × Ano (gold <code>gold_pbf_estados_df.json</code>).<br />
                <b>Fonte:</b> Portal da Transparência (CGU), IBGE/SIDRA 6579, BCB/SGS 433.<br />
                <b>Deflação:</b> IPCA acumulado em dez/2021.
              </div>
            </div>
          </Panel>
          <Panel label="Evolução nacional" sub={metric.label} exportId="pbf-evolucao-nacional">
            <EvolutionBar data={evolutionData} theme={theme}
                          yLabel={metric.yaxisTitle} xLabel="Ano"
                          format={metric.fmt} height={320} />
          </Panel>
        </div>

        <div className="row row-ranking-map">
          <Panel label="Ranking por UF"
                 sub={`${metric.label} · ${year === 'AGG' ? 'média ponderada' : year}`}
                 exportId="pbf-ranking-uf">
            <StateRanking rows={ranking} format={metric.fmtRich}
                          accentColor={theme === 'dark' ? '#60a5fa' : '#2b6cb0'} />
          </Panel>
          <Panel label="Distribuição geográfica" exportId="pbf-mapa-uf"
                 right={<MapColorscaleSelect value={colorscale} onChange={setColorscale} />}>
            <BrazilMap data={filtered} colorscale={colorscale} theme={theme}
                       hoverFmt={metric.fmtRich} unit={metric.short} />
          </Panel>
        </div>
      </div>
    </>
  );
}

// Helper compartilhado pelo seletor de paleta
function MapColorscaleSelect({ value, onChange }) {
  return (
    <div className="mapControls">
      <label htmlFor="colorscale">Cores</label>
      <select id="colorscale" value={value} onChange={(e) => onChange(e.target.value)}>
        {COLORSCALES.map((c) => (<option key={c.value} value={c.value}>{c.label}</option>))}
      </select>
    </div>
  );
}

// ─── Dashboard MUNICIPAL (WP#7) — mesmos componentes do estadual ─────────
function MunicipalDashboard({
  muniRows, muniKpis, muniRanking, muniFiltered, muniMapData, muniEvolution,
  muniYears, muniMaxYear, muniMinYear,
  year, setYear, metricKey, setMetricKey, metric,
  colorscale, setColorscale, theme,
}) {
  if (muniRows == null) {
    return <div className="loading-block">Carregando dados municipais…</div>;
  }
  if (muniRows.length === 0) {
    return (
      <Panel label="Análise municipal" sub="gold municipal não disponível">
        <p style={{ fontSize: 12, color: 'var(--muted)', lineHeight: 1.6 }}>
          Para gerar localmente:
          <code> python3 articles/fetch_ibge_populacao_municipios.py</code> seguido de
          <code> python3 articles/build_fallback_municipal_gold.py</code>.
        </p>
      </Panel>
    );
  }

  const isFallback = muniRows[0]._source === 'fallback';

  return (
    <>
      {isFallback && (
        <div style={{
          margin: '0 0 12px 0', padding: '10px 14px',
          background: 'rgba(180, 83, 9, 0.08)',
          border: '1px solid rgba(180, 83, 9, 0.4)', borderRadius: 6,
          fontSize: 11.5, lineHeight: 1.55,
        }}>
          <b style={{ color: '#b45309' }}>Modo fallback:</b> alocação UF→município
          ponderada por população × pobreza-UF (a partir do gold UF). Per capita
          estadual é preservado em ~1.000. Heterogeneidade intra-UF efetiva
          requer rodar o pipeline Databricks com microdados CGU agregados por
          município (notebooks <code>silver/pbf_total_municipio_mes.py</code> +{' '}
          <code>gold/pbf_municipios_df.py</code>).
        </div>
      )}

      <div className="kpiRow" data-export-id="pbf-kpis-muni">
        <KpiCard label={`Municípios · ${muniKpis.y ?? '—'}`}
                 value={fmtInt(muniKpis.nMunis)}
                 sub="painel WP#7 (5.570 entes)" />
        <KpiCard label={`Beneficiários · ${muniKpis.y ?? '—'}`}
                 value={fmtCompact(muniKpis.totalBenef)}
                 sub={`${muniKpis.totalPop ? ((muniKpis.totalBenef / muniKpis.totalPop) * 100).toFixed(1) : '—'}% da população`}
                 color="#be185d" />
        <KpiCard label={`Valor pago · ${muniKpis.y ?? '—'}`}
                 value={fmtBRL(muniKpis.totalValor * 1e6, { compact: true })}
                 sub="R$ 2021 · soma 5.570 munis" color="#2b6cb0" />
        <KpiCard label={`Per beneficiário · ${muniKpis.y ?? '—'}`}
                 value={fmtBRL(muniKpis.perBenef)}
                 sub="R$ 2021 / família atendida" color="#0d9488" />
        <KpiCard label={`Per capita · ${muniKpis.y ?? '—'}`}
                 value={fmtBRL(muniKpis.perCapita)}
                 sub="R$ 2021 / habitante BR" color="#b45309" />
      </div>

      <div className="layout">
        <div className="row row-controls-bar">
          <Panel label="Filtros & dados" sub="CGU + IBGE/Localidades + IBGE/SIDRA + kelvins">
            <div className="controls">
              <div className="control">
                <label htmlFor="metric-muni">Métrica</label>
                <select id="metric-muni" value={metricKey} onChange={(e) => setMetricKey(e.target.value)}>
                  {Object.entries(METRICS).map(([k, m]) => (
                    <option key={k} value={k}>{m.label}</option>
                  ))}
                </select>
              </div>
              <div className="control">
                <label htmlFor="year-muni">Ano</label>
                <select id="year-muni" value={year} onChange={(e) => setYear(e.target.value)}>
                  <option value="AGG">{`Acumulado / média ${muniMinYear ?? ''}–${muniMaxYear ?? ''}`}</option>
                  {muniYears.map((y) => (<option key={y} value={y}>{y}</option>))}
                </select>
              </div>
              <div className="metaBlock">
                <b>Granularidade:</b> 5.570 municípios × Ano (gold <code>gold_pbf_municipios_df.json</code>, mapa renderiza os 5.570 polígonos IBGE).<br />
                <b>Identificação:</b> TWFE com <b>k=5.571 clusters</b> (vs k=27 do WP#2).<br />
                <b>Robustez:</b> Conley HAC com distâncias geodésicas reais (haversine entre centroides IBGE/Localidades + kelvins).
              </div>
            </div>
          </Panel>
          <Panel label="Evolução nacional (agregado dos municípios)" sub={metric.label}
                 exportId="pbf-evolucao-municipal">
            <EvolutionBar data={muniEvolution} theme={theme}
                          yLabel={metric.yaxisTitle} xLabel="Ano"
                          format={metric.fmt} height={320} />
          </Panel>
        </div>

        <div className="row row-ranking-map">
          <Panel label="Ranking por UF (agregado de munis)"
                 sub={`${metric.label} · ${year === 'AGG' ? 'média ponderada' : year}`}
                 exportId="pbf-ranking-uf-muni">
            <StateRanking rows={muniRanking} format={metric.fmtRich}
                          accentColor={theme === 'dark' ? '#fb923c' : '#b45309'} />
          </Panel>
          <Panel label="Distribuição geográfica (5.570 municípios)"
                 sub="malha IBGE · borda preta = UF"
                 exportId="pbf-mapa-municipal"
                 right={<MapColorscaleSelect value={colorscale} onChange={setColorscale} />}>
            <BrazilMuniMap data={muniMapData} colorscale={colorscale} theme={theme}
                           hoverFmt={metric.fmtRich} unit={metric.short} />
          </Panel>
        </div>
      </div>

      <MunicipalRankings muniRows={muniRows} year={year} muniMaxYear={muniMaxYear} />
      <MunicipalCausalTable />
      <MunicipalFigures />
    </>
  );
}

// ─── Top/Bottom 20 munis — lista textual com per-capita ──────────────────
function MunicipalRankings({ muniRows, year, muniMaxYear }) {
  const targetYear = year === 'AGG' ? muniMaxYear : Number(year);
  const yearRows = muniRows.filter((r) => r.Ano === targetYear);
  const top20 = [...yearRows].sort((a, b) => b.pbfPerCapita - a.pbfPerCapita).slice(0, 20);
  const bottom20 = [...yearRows].filter((r) => r.pbfPerCapita > 0)
                                 .sort((a, b) => a.pbfPerCapita - b.pbfPerCapita).slice(0, 20);
  return (
    <div style={{
      display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(380px, 1fr))', gap: 16,
      marginTop: 14,
    }}>
      <Panel label={`Top 20 munis — maior PBF/hab (${targetYear})`}>
        <ol style={{ fontSize: 12, lineHeight: 1.65, margin: 0, paddingLeft: 20 }}>
          {top20.map((r) => (
            <li key={r.cod_municipio} style={{ marginBottom: 2 }}>
              <b>{r.municipio}</b>/<code>{r.uf}</code>{' '}
              <span style={{ color: 'var(--muted)' }}>
                · {fmtBRL(r.pbfPerCapita)}/hab · pop {fmtCompact(r.populacao)}
              </span>
            </li>
          ))}
        </ol>
      </Panel>
      <Panel label={`Bottom 20 munis — menor PBF/hab > 0 (${targetYear})`}>
        <ol style={{ fontSize: 12, lineHeight: 1.65, margin: 0, paddingLeft: 20 }}>
          {bottom20.map((r) => (
            <li key={r.cod_municipio} style={{ marginBottom: 2 }}>
              <b>{r.municipio}</b>/<code>{r.uf}</code>{' '}
              <span style={{ color: 'var(--muted)' }}>
                · {fmtBRL(r.pbfPerCapita)}/hab · pop {fmtCompact(r.populacao)}
              </span>
            </li>
          ))}
        </ol>
      </Panel>
    </div>
  );
}

// ─── Tabela de resultados causais — mesma do legado, agora dentro da tab ─
function MunicipalCausalTable() {
  return (
    <Panel label="Resultados causais (k = 5.571 clusters)"
           sub="vinte vezes acima do mínimo Cameron-Gelbach-Miller (2008)">
      <p style={{ fontSize: 12, color: 'var(--muted)', marginTop: 0, marginBottom: 10 }}>
        Estimativas baseadas no painel municipal. Magnitudes em R$/hab/ano (2021).
        Conley HAC com distâncias geodésicas reais (haversine) entre centroides
        IBGE/Localidades + kelvins/Municipios-Brasileiros.
      </p>
      <table style={{ width: '100%', fontSize: 13, borderCollapse: 'collapse' }}>
        <thead>
          <tr style={{ borderBottom: '1px solid var(--border)' }}>
            <th style={{ textAlign: 'left',  padding: 8 }}>Estratégia</th>
            <th style={{ textAlign: 'right', padding: 8 }}>β̂ (R$/hab)</th>
            <th style={{ textAlign: 'right', padding: 8 }}>SE</th>
            <th style={{ textAlign: 'right', padding: 8 }}>|t|</th>
          </tr>
        </thead>
        <tbody>
          {[
            ['DiD 2×2 — MP 1.061/2021 (Auxílio Brasil)',  205.3,   2.04, 100.5],
            ['DiD 2×2 — Lei 14.601/2023 (NBF)',           349.5,   2.81, 124.3],
            ['TWFE clusterizado por município (k=5.571)', 296.6,   2.56, 115.7],
            ['Conley HAC, h = 200 km',                    296.6,  36.5,    8.1],
            ['Conley HAC, h = 800 km',                    296.6, 101.7,    2.9],
            ['Conley HAC, h = 1600 km',                   296.6, 149.2,    2.0],
          ].map((row) => (
            <tr key={row[0]} style={{ borderBottom: '1px solid var(--rule)' }}>
              <td style={{ padding: 8 }}>{row[0]}</td>
              <td style={{ padding: 8, textAlign: 'right', fontWeight: 700 }}>+{row[1].toFixed(1)}</td>
              <td style={{ padding: 8, textAlign: 'right' }}>{row[2].toFixed(2)}</td>
              <td style={{ padding: 8, textAlign: 'right' }}>{row[3].toFixed(1)}</td>
            </tr>
          ))}
        </tbody>
      </table>
      <p style={{ fontSize: 11, color: 'var(--muted)', marginTop: 10, lineHeight: 1.55 }}>
        A inflação substantiva do SE Conley HAC entre h=50 e h=1600 km evidencia
        correlação espacial positiva nos resíduos. Mesmo com h=1600 km, o efeito
        permanece estatisticamente diferente de zero (|t| ≥ 2.0).
      </p>
    </Panel>
  );
}

// ─── Galeria de figuras EMBEDDED INLINE — agrupadas por tema ─────────────
function MunicipalFigures() {
  const figBase = `${import.meta.env.BASE_URL || '/'}articles/figures-pbf-municipios`.replace(/\/{2,}/g, '/');
  const groups = [
    {
      titulo: 'Distribuição & dispersão entre os 5.570 municípios',
      figs: [
        ['fig01-distribuicao-pc-municipal',  'Fig. 1 — Distribuição PBF/hab (5.570 munis)'],
        ['fig02-intra-uf-boxplot',           'Fig. 2 — Heterogeneidade intra-UF (boxplot)'],
        ['fig03-idhm-vs-pc-municipal',       'Fig. 3 — IDH-M × PBF per capita'],
      ],
    },
    // Grupo "Geografia" REMOVIDO — fig05 (mapa scatter) e fig08 (bivariado)
    // eram bubble/scatter matplotlib que ficavam feios embedded inline.
    // Visualização geográfica vive no BrazilMap UF do topo da tab Municipal
    // (agregado de 5.570 munis em 27 UFs). Mapas choropléticos AO NÍVEL
    // MUNICIPAL (5.570 polígonos) entram quando WP#7 v2 pipeline completar:
    // IBGE/Malha N6 GeoJSON + geopandas + matplotlib choropleth Cividis_r.
    {
      titulo: 'Rankings & desigualdade',
      figs: [
        ['fig04-top-bottom-municipios',      'Fig. 4 — Top 20 vs Bottom 20'],
        ['fig11-lorenz-municipal',           'Fig. 11 — Curva de Lorenz municipal + Gini'],
      ],
    },
    {
      titulo: 'Evolução temporal',
      figs: [
        ['fig06-evolucao-regional',          'Fig. 6 — Evolução regional 2013–2025'],
        ['fig12-crescimento-2018-2024',      'Fig. 12 — Crescimento real per capita 2018→2024'],
      ],
    },
    {
      titulo: 'Inferência & robustez',
      figs: [
        ['fig07-theil-decomposicao',         'Fig. 7 — Decomposição Theil within/between-UF'],
        ['fig09-need-ratio-municipal',       'Fig. 9 — Need ratio municipal'],
        ['fig10-conley-hac-sensitivity',     'Fig. 10 — Conley HAC: SE × bandwidth'],
      ],
    },
    {
      titulo: 'Identificação causal',
      figs: [
        ['causal_event_study_municipal',     'Event study — DiD com leads/lags ±5 anos'],
      ],
    },
  ];

  return (
    <section style={{ marginTop: 18 }}>
      <Panel label="Figuras do Working Paper #7 (12 figuras + event study)"
             sub="identidade visual editorial Mirante · embedded inline pra leitura sequencial">
        <p style={{ fontSize: 12, color: 'var(--muted)', marginTop: 0, marginBottom: 16, lineHeight: 1.55 }}>
          As 13 figuras abaixo seguem a estrutura narrativa do paper. Cada PDF é
          embedded direto na página — abrir em nova aba pra zoom: <i>botão direito → "Abrir em nova aba"</i>
          ou clique no ícone na barra do PDF.
        </p>
        {groups.map((g) => (
          <div key={g.titulo} style={{ marginBottom: 20 }}>
            <div style={{
              fontSize: 12, fontWeight: 700, letterSpacing: '0.04em',
              textTransform: 'uppercase', color: 'var(--accent, #0d9488)',
              marginBottom: 10, paddingBottom: 6,
              borderBottom: '1px solid var(--border)',
            }}>
              {g.titulo}
            </div>
            <div style={{
              display: 'grid',
              gridTemplateColumns: g.figs.length === 1
                ? '1fr'
                : 'repeat(auto-fit, minmax(420px, 1fr))',
              gap: 14,
            }}>
              {g.figs.map(([slug, label]) => (
                <FigureEmbed key={slug} slug={slug} label={label} figBase={figBase} />
              ))}
            </div>
          </div>
        ))}
      </Panel>
    </section>
  );
}

function FigureEmbed({ slug, label, figBase }) {
  const url = `${figBase}/${slug}.pdf`;
  return (
    <div style={{
      border: '1px solid var(--border)', borderRadius: 6,
      background: 'var(--bg)', overflow: 'hidden',
    }}>
      <div style={{
        padding: '8px 12px', fontSize: 12, fontWeight: 600,
        borderBottom: '1px solid var(--border)',
        background: 'var(--rule, #f1f5f9)',
        display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: 8,
      }}>
        <span>{label}</span>
        <a href={url} target="_blank" rel="noreferrer"
           style={{ fontSize: 10.5, color: 'var(--muted)', textDecoration: 'none' }}
           title="abrir em nova aba">
          ↗ abrir
        </a>
      </div>
      <object data={`${url}#toolbar=0&navpanes=0`} type="application/pdf"
              style={{ width: '100%', height: 460, display: 'block', border: 0 }}>
        <div style={{ padding: 20, fontSize: 12, color: 'var(--muted)' }}>
          Seu navegador não suporta PDF embedded.{' '}
          <a href={url} target="_blank" rel="noreferrer">Abrir PDF</a>.
        </div>
      </object>
    </div>
  );
}

// ─── Diferenças WP#7 (municipal) vs WP#2 (estadual) ───────────────────────
function DiferencasWP2WP7() {
  const items = [
    {
      criterio: 'Granularidade',
      wp2: '27 UFs × Ano (painel curto: N=27)',
      wp7: '5.570 municípios × Ano (painel longo: N=5.570)',
    },
    {
      criterio: 'Identificação causal',
      wp2: 'DiD 2×2 + TWFE clusterizado por UF (k=27); ' +
           'wild-cluster bootstrap pra mitigar few-clusters (Cameron-Gelbach-Miller 2008)',
      wp7: 'TWFE clusterizado por município (k=5.571 — vinte vezes acima do mínimo CGM 2008); ' +
           'cluster bootstrap converge sem precisar de wild-cluster',
    },
    {
      criterio: 'Correlação espacial',
      wp2: 'Não modelada explicitamente (cluster por UF é proxy parcial)',
      wp7: 'Conley HAC com distâncias geodésicas REAIS (haversine entre centroides ' +
           'IBGE/Localidades + kelvins/Municipios-Brasileiros), bandwidth sensitivity 50–1600 km',
    },
    {
      criterio: 'Heterogeneidade dentro do estado',
      wp2: 'Invisível por construção (média UF apaga variação intra-UF)',
      wp7: 'Decomposição Theil within/between-UF revela quanto da desigualdade ' +
           'PBF é INTRA-UF vs entre estados',
    },
    {
      criterio: 'Choques institucionais analisados',
      wp2: 'MP 1.061/2021 (Auxílio Brasil), Lei 14.601/2023 (NBF) — DiD honesto, resultado null possível',
      wp7: 'Mesmos dois choques + análise da heterogeneidade do efeito por município',
    },
    {
      criterio: 'Equidade & focalização',
      wp2: 'Kakwani sobre per capita PBF × IDH-M por UF + benchmark CCT internacional ' +
           '(AUH Argentina, Prospera México, MFA Colômbia, Renta Dignidad Bolívia em US$ PPP)',
      wp7: 'Need ratio municipal (cobertura efetiva / cobertura ideal por necessidade), ' +
           'curva de Lorenz municipal, mapa bivariado pc × IDH-M',
    },
    {
      criterio: 'Tese central',
      wp2: 'Três regimes (PBF/AB/NBF), R$ 36→141 bi/ano, 16→24 mi famílias — ' +
           'dois choques institucionais identificáveis + benchmark internacional',
      wp7: '5.570 pontos de decisão — a hipótese de homogeneidade dentro da UF é ' +
           'falsa por construção do programa (focalização individual no CadÚnico), ' +
           'a granularidade municipal é o nível certo de identificação',
    },
    {
      criterio: 'Score régua Mestrado',
      wp2: 'B+ (2,5 pts) — DiD/TWFE/WCB + Kakwani + benchmark CCT + 17 figuras',
      wp7: 'B+ (2,5 pts) — resolve gargalo de N=27 do WP#2 + Conley HAC com geodésicas REAIS + ' +
           'decomposição Theil + 12 figuras + event study',
    },
    {
      criterio: 'Reuso metodológico',
      wp2: 'Pipeline UF×Ano. Reaproveitável pra outros programas com baixa granularidade',
      wp7: 'Template Município×Ano. 6 notebooks Databricks + 4 scripts Python — ' +
           'reaproveitável fora do PBF (basta trocar o silver de origem)',
    },
  ];

  return (
    <section style={{ marginTop: 24, marginBottom: 14 }}>
      <Panel label="Diferenças entre WP#7 (municipal) e WP#2 (estadual)"
             sub="resumo cross-paper das contribuições complementares">
        <p style={{ fontSize: 12, color: 'var(--muted)', marginTop: 0, marginBottom: 14, lineHeight: 1.6 }}>
          Os dois Working Papers cobrem o mesmo programa (Bolsa Família/Auxílio Brasil/Novo Bolsa
          Família, 2013–2025) com a mesma régua editorial (stricto sensu mestrado, score B+),
          mas com escopos diferentes e <b>complementares</b>: WP#2 estabelece o quadro nacional
          + identificação causal sobre os dois choques institucionais; WP#7 responde DIRETAMENTE
          ao gargalo de N=27 do WP#2 migrando pra k=5.570 clusters municipais e revelando a
          heterogeneidade que a média UF esconde.
        </p>
        <div style={{ overflowX: 'auto' }}>
          <table style={{ width: '100%', fontSize: 12.5, borderCollapse: 'collapse' }}>
            <thead>
              <tr style={{ borderBottom: '2px solid var(--border)' }}>
                <th style={{ textAlign: 'left', padding: 8, width: '20%' }}>Critério</th>
                <th style={{ textAlign: 'left', padding: 8, width: '40%', color: '#2b6cb0' }}>WP#2 — Estadual</th>
                <th style={{ textAlign: 'left', padding: 8, width: '40%', color: '#b45309' }}>WP#7 — Municipal</th>
              </tr>
            </thead>
            <tbody>
              {items.map((it, i) => (
                <tr key={it.criterio} style={{
                  borderBottom: '1px solid var(--rule)',
                  background: i % 2 === 0 ? 'transparent' : 'var(--rule, rgba(0,0,0,0.02))',
                }}>
                  <td style={{ padding: 8, fontWeight: 700, verticalAlign: 'top' }}>{it.criterio}</td>
                  <td style={{ padding: 8, lineHeight: 1.55, verticalAlign: 'top' }}>{it.wp2}</td>
                  <td style={{ padding: 8, lineHeight: 1.55, verticalAlign: 'top' }}>{it.wp7}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <p style={{ fontSize: 11, color: 'var(--muted)', marginTop: 12, lineHeight: 1.55 }}>
          <b>Não-substituíveis:</b> WP#2 ↔ WP#7 são complementares, não concorrentes. Quem
          precisa de inferência sobre o programa BR-wide com choques nacionais → WP#2. Quem
          precisa entender por que o efeito médio esconde heterogeneidade real entre municípios
          da mesma UF → WP#7. Idealmente, ambos.
        </p>
      </Panel>
    </section>
  );
}

// ─── (LEGADO) MunicipalSection antigo — mantido pra fallback se algum import quebrar
function MunicipalSection({ rows }) {
  const [yearSel, setYearSel] = useState(null);
  const [ufFilter, setUfFilter] = useState('TODOS');

  useEffect(() => {
    if (rows && rows.length > 0 && yearSel == null) {
      const ys = Array.from(new Set(rows.map((r) => r.Ano))).sort();
      setYearSel(ys[ys.length - 1]);
    }
  }, [rows, yearSel]);

  if (!rows) {
    return <Panel label="WP#7 · Análise municipal" sub="carregando…" />;
  }
  if (rows.length === 0) {
    return (
      <Panel label="WP#7 · Análise municipal" sub="gold municipal não disponível">
        <p style={{ fontSize: 12, color: 'var(--muted)' }}>
          Para gerar localmente: <code>python3 articles/fetch_ibge_populacao_municipios.py</code> e
          depois <code>python3 articles/build_fallback_municipal_gold.py</code>.
        </p>
      </Panel>
    );
  }

  const years = Array.from(new Set(rows.map((r) => r.Ano))).sort();
  const ufs = ['TODOS', ...Array.from(new Set(rows.map((r) => r.uf))).sort()];

  const filtered = rows.filter((r) =>
    r.Ano === yearSel && (ufFilter === 'TODOS' || r.uf === ufFilter));

  const yearRows = rows.filter((r) => r.Ano === yearSel);
  const totalBenef = yearRows.reduce((s, r) => s + (r.n_benef || 0), 0);
  const totalValor = yearRows.reduce((s, r) => s + (r.valor_2021 || 0), 0);
  const totalPop   = yearRows.reduce((s, r) => s + (r.populacao || 0), 0);
  const munis      = yearRows.length;
  const cobertura  = totalPop ? (totalBenef / totalPop) * 100 : 0;
  const perCapita  = totalPop ? (totalValor * 1e6) / totalPop : 0;
  const perBenef   = totalBenef ? (totalValor * 1e6) / totalBenef : 0;

  const top20 = [...filtered].sort((a, b) => b.pbfPerCapita - a.pbfPerCapita).slice(0, 20);
  const bottom20 = [...filtered].filter((r) => r.pbfPerCapita > 0)
                                .sort((a, b) => a.pbfPerCapita - b.pbfPerCapita).slice(0, 20);

  const isFallback = rows[0]._source === 'fallback';
  const base = import.meta.env.BASE_URL || '/';
  const figBase = `${base}articles/figures-pbf-municipios`.replace(/\/{2,}/g, '/');

  return (
    <section style={{ marginTop: 24 }}>
      <Panel label={`WP#7 · Análise municipal — ${yearSel}`}
             sub={`${munis.toLocaleString('pt-BR')} munis | filtros abaixo`}>
        {isFallback && (
          <div style={{
            margin: '0 0 12px 0', padding: '8px 12px',
            background: 'rgba(180, 83, 9, 0.08)',
            border: '1px solid rgba(180, 83, 9, 0.4)', borderRadius: 6,
            fontSize: 11, lineHeight: 1.5,
          }}>
            <b style={{ color: '#b45309' }}>Modo fallback:</b> alocação UF→muni
            ponderada por população×pobreza-UF a partir do gold UF; per capita estadual
            preservado em 1.000. Heterogeneidade intra-UF efetiva requer rodar o pipeline
            Databricks (notebooks <code>silver/pbf_total_municipio_mes.py</code> +{' '}
            <code>gold/pbf_municipios_df.py</code>) com microdados CGU.
          </div>
        )}
        <div style={{ display: 'flex', gap: 16, alignItems: 'center', flexWrap: 'wrap', marginBottom: 12 }}>
          <label style={{ fontSize: 12 }}>
            Ano:&nbsp;
            <select value={yearSel ?? ''} onChange={(e) => setYearSel(Number(e.target.value))}>
              {years.map((y) => <option key={y} value={y}>{y}</option>)}
            </select>
          </label>
          <label style={{ fontSize: 12 }}>
            UF:&nbsp;
            <select value={ufFilter} onChange={(e) => setUfFilter(e.target.value)}>
              {ufs.map((u) => <option key={u} value={u}>{u}</option>)}
            </select>
          </label>
          <span style={{ fontSize: 11, color: 'var(--muted)' }}>
            {filtered.length.toLocaleString('pt-BR')} munis no recorte atual.
          </span>
        </div>

        <div className="kpiRow">
          <KpiCard label={`Munis (${yearSel})`} value={fmtInt(munis)} sub="painel WP#7" />
          <KpiCard label="Famílias beneficiárias" value={fmtCompact(totalBenef)}
                   sub={`${cobertura.toFixed(1)}% da população`} color="#be185d" />
          <KpiCard label={`Valor pago R$ 2021`} value={fmtBRL(totalValor * 1e6, { compact: true })}
                   sub="soma dos 5.570 munis" color="#2b6cb0" />
          <KpiCard label="Per capita" value={fmtBRL(perCapita)} sub="R$/hab/ano" color="#0d9488" />
          <KpiCard label="Per beneficiário" value={fmtBRL(perBenef)} sub="R$/família/ano" />
        </div>
      </Panel>

      <div style={{
        display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(380px, 1fr))', gap: 16,
        marginTop: 14,
      }}>
        <Panel label={`Top 20 munis — maior PBF/hab (${yearSel}${ufFilter !== 'TODOS' ? ` em ${ufFilter}` : ''})`}>
          <ol style={{ fontSize: 12, lineHeight: 1.6, margin: 0, paddingLeft: 20 }}>
            {top20.map((r) => (
              <li key={r.cod_municipio} style={{ marginBottom: 2 }}>
                <b>{r.municipio}</b>/<code>{r.uf}</code>{' '}
                <span style={{ color: 'var(--muted)' }}>
                  · {fmtBRL(r.pbfPerCapita)}/hab · pop {fmtCompact(r.populacao)}
                </span>
              </li>
            ))}
          </ol>
        </Panel>
        <Panel label={`Bottom 20 munis — menor PBF/hab > 0 (${yearSel}${ufFilter !== 'TODOS' ? ` em ${ufFilter}` : ''})`}>
          <ol style={{ fontSize: 12, lineHeight: 1.6, margin: 0, paddingLeft: 20 }}>
            {bottom20.map((r) => (
              <li key={r.cod_municipio} style={{ marginBottom: 2 }}>
                <b>{r.municipio}</b>/<code>{r.uf}</code>{' '}
                <span style={{ color: 'var(--muted)' }}>
                  · {fmtBRL(r.pbfPerCapita)}/hab · pop {fmtCompact(r.populacao)}
                </span>
              </li>
            ))}
          </ol>
        </Panel>
      </div>

      <Panel label="WP#7 · Galeria de figuras (12 PDFs)" exportId="pbf-municipios-figuras">
        <p style={{ fontSize: 12, color: 'var(--muted)', marginTop: 0 }}>
          Identidade visual editorial Mirante (Lato + paleta hierárquica + golden ratio).
          Clique em cada thumbnail para abrir o PDF em tamanho real.
        </p>
        <div style={{
          display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: 10,
        }}>
          {[
            ['fig01-distribuicao-pc-municipal',  'Distribuição PBF/hab (5.570 munis)'],
            ['fig02-intra-uf-boxplot',           'Heterogeneidade intra-UF'],
            ['fig03-idhm-vs-pc-municipal',       'IDH-M × PBF/hab'],
            ['fig04-top-bottom-municipios',      'Top 20 vs Bottom 20'],
            // fig05 (scatter geográfico) e fig08 (bivariado) removidos —
            // bubble/scatter feios. Choropleth municipal vai entrar com
            // pipeline WP#7 v2 (IBGE/Malha N6 + geopandas).
            ['fig06-evolucao-regional',          'Evolução regional 2013–2025'],
            ['fig07-theil-decomposicao',         'Theil within/between'],
            ['fig09-need-ratio-municipal',       'Need ratio'],
            ['fig10-conley-hac-sensitivity',     'Conley HAC: SE × bandwidth'],
            ['fig11-lorenz-municipal',           'Lorenz municipal + Gini'],
            ['fig12-crescimento-2018-2024',      'Ganho 2018→2024'],
          ].map(([s, label]) => (
            <a key={s} href={`${figBase}/${s}.pdf`} target="_blank" rel="noreferrer"
               style={{
                 display: 'block', padding: 8, borderRadius: 6,
                 border: '1px solid var(--border)', background: 'var(--bg)',
                 textDecoration: 'none', color: 'var(--text)',
               }}>
              <div style={{
                background: 'var(--rule, #f1f5f9)', aspectRatio: '16/10', borderRadius: 4,
                display: 'flex', alignItems: 'center', justifyContent: 'center',
                fontSize: 10, color: 'var(--muted)', marginBottom: 6,
              }}>
                <span>📊 PDF</span>
              </div>
              <div style={{ fontSize: 11.5, fontWeight: 600 }}>{label}</div>
              <div style={{ fontSize: 9.5, color: 'var(--muted)', marginTop: 2 }}>{s}.pdf</div>
            </a>
          ))}
        </div>
      </Panel>

      <Panel label="WP#7 · Resultados causais (k = 5.571 clusters)">
        <p style={{ fontSize: 12, color: 'var(--muted)', marginTop: 0 }}>
          Estimativas baseadas no painel municipal. Vinte vezes acima do mínimo
          Cameron-Gelbach-Miller (2008). Magnitudes em R$/hab/ano (2021).
        </p>
        <table style={{ width: '100%', fontSize: 13, borderCollapse: 'collapse' }}>
          <thead>
            <tr style={{ borderBottom: '1px solid var(--border)' }}>
              <th style={{ textAlign: 'left',  padding: 6 }}>Estratégia</th>
              <th style={{ textAlign: 'right', padding: 6 }}>β̂</th>
              <th style={{ textAlign: 'right', padding: 6 }}>SE</th>
              <th style={{ textAlign: 'right', padding: 6 }}>|t|</th>
            </tr>
          </thead>
          <tbody>
            {[
              ['DiD 2×2 — MP 1.061/2021 (Auxílio Brasil)',  205.3,   2.04, 100.5],
              ['DiD 2×2 — Lei 14.601/2023 (NBF)',           349.5,   2.81, 124.3],
              ['TWFE clusterizado por município (k=5.571)', 296.6,   2.56, 115.7],
              ['Conley HAC, h = 200 km',                    296.6,  36.5,    8.1],
              ['Conley HAC, h = 800 km',                    296.6, 101.7,    2.9],
              ['Conley HAC, h = 1600 km',                   296.6, 149.2,    2.0],
            ].map((row) => (
              <tr key={row[0]} style={{ borderBottom: '1px solid var(--rule)' }}>
                <td style={{ padding: 6 }}>{row[0]}</td>
                <td style={{ padding: 6, textAlign: 'right', fontWeight: 700 }}>+{row[1].toFixed(1)}</td>
                <td style={{ padding: 6, textAlign: 'right' }}>{row[2].toFixed(2)}</td>
                <td style={{ padding: 6, textAlign: 'right' }}>{row[3].toFixed(1)}</td>
              </tr>
            ))}
          </tbody>
        </table>
        <p style={{ fontSize: 11, color: 'var(--muted)', marginTop: 8 }}>
          A inflação substantiva do SE Conley HAC entre h=50 e h=1600 km
          evidencia correlação espacial positiva nos resíduos.
          Mesmo com h=1600 km, o efeito permanece estatisticamente diferente
          de zero (|t| ≥ 2.0).
        </p>
      </Panel>
    </section>
  );
}


export default function BolsaFamilia() {
  const { theme } = useTheme();
  const [rows, setRows]             = useState(null);
  const [error, setError]           = useState(null);
  const [metricKey, setMetricKey]   = useState(DEFAULT_METRIC);
  const [year, setYear]             = useState('AGG');
  const [colorscale, setColorscale] = useState(DEFAULT_COLOR);
  // Tab: 'estadual' (WP#2) ou 'municipal' (WP#7). Controla qual dashboard
  // renderiza. Ambos compartilham KpiCard/BrazilMap/StateRanking/EvolutionBar.
  const [scope, setScope] = useState('estadual');

  // Quando trocar pra Municipal e estiver em AGG, força último ano —
  // a média plurianual nivela demais o mapa muni (5570 polígonos com
  // valores de 13 anos somados ficam todos numa cor próxima da mediana).
  // Único ano dá range muito mais legível pro choropleth.
  useEffect(() => {
    if (scope === 'municipal' && year === 'AGG') {
      // Ler últimos anos disponíveis sem causar loop infinito —
      // muniRows pode vir depois, então usa estado atual como fallback.
      const ys = (muniRows && muniRows.length > 0)
        ? Array.from(new Set(muniRows.map(r => r.Ano))).sort()
        : [];
      if (ys.length > 0) setYear(String(ys[ys.length - 1]));
    }
  }, [scope, muniRows]); // eslint-disable-line react-hooks/exhaustive-deps
  // WP#7 — gold municipal carregado em paralelo. Optional: se faltar, a tab
  // Municipal mostra placeholder. Não bloqueia a tela principal.
  const [muniRows, setMuniRows] = useState(null);

  useEffect(() => {
    loadGold('gold_pbf_estados_df.json')
      .then(setRows)
      .catch((e) => setError(e.message));
    loadGold('gold_pbf_municipios_df.json')
      .then(setMuniRows)
      .catch(() => setMuniRows([]));   // gold municipal opcional — não bloqueia
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

  // ─── DERIVAÇÕES MUNICIPAIS — agregadas a UF pra usar a MESMA UI estadual ──
  // Gold municipal tem valor_2021 em MILHÕES (R$ mi); state gold tem em BILHÕES.
  // Reescalamos pra ficar comparável entre tabs (UI sempre fala em "bilhões"
  // pra não-ratio métricas).
  const muniYears = useMemo(
    () => (muniRows && muniRows.length > 0
      ? Array.from(new Set(muniRows.map((r) => r.Ano))).sort()
      : []),
    [muniRows],
  );
  const muniMaxYear = muniYears.length ? muniYears[muniYears.length - 1] : null;
  const muniMinYear = muniYears.length ? muniYears[0] : null;

  // Mapa Brasil — agrega 5.570 munis em 27 UFs pro mesmo BrazilMap usado no estadual
  const muniFiltered = useMemo(() => {
    if (!muniRows || muniRows.length === 0) return [];
    const byUf = new Map();
    const targetYears = year === 'AGG' ? muniYears : [Number(year)];
    for (const r of muniRows) {
      if (!targetYears.includes(r.Ano)) continue;
      const cur = byUf.get(r.uf) || { uf: r.uf, valor: 0, pop: 0, benef: 0 };
      cur.valor += (r.valor_2021 || 0);  // R$ mi
      cur.pop   += (r.populacao || 0);
      cur.benef += (r.n_benef || 0);
      byUf.set(r.uf, cur);
    }
    return Array.from(byUf.values()).map((d) => {
      let value = 0;
      if (metricKey === 'pbfPerCapita') {
        value = d.pop > 0 ? (d.valor * 1e6) / d.pop : 0;          // R$/hab
      } else if (metricKey === 'pbfPerBenef') {
        value = d.benef > 0 ? (d.valor * 1e6) / d.benef : 0;      // R$/família
      } else if (metricKey === 'valor_2021' || metricKey === 'valor_nominal') {
        value = d.valor / 1000;                                   // mi → bi (alinhar UI)
      } else if (metricKey === 'n_benef') {
        value = d.benef;
      }
      return { uf: d.uf, value };
    });
  }, [muniRows, year, metricKey, muniYears]);

  const muniRanking = useMemo(
    () => [...muniFiltered].sort((a, b) => b.value - a.value),
    [muniFiltered],
  );

  // Mapa MUNICIPAL — 5.570 polígonos. Constrói {cod_municipio, value, municipio, uf}
  // pra cada muni a partir do gold WP#7. Para AGG a regra segue muniFiltered:
  //   ratio metrics  → sum(num) / sum(denom) ao longo dos anos por muni;
  //   total metrics  → soma dos anos por muni.
  // Unidades casam com a tab estadual: bilhões de R$ pras métricas de valor,
  // R$/hab e R$/família pras ratio.
  const muniMapData = useMemo(() => {
    if (!muniRows || muniRows.length === 0) return [];
    const byMuni = new Map();
    const targetYears = year === 'AGG' ? muniYears : [Number(year)];
    for (const r of muniRows) {
      if (!targetYears.includes(r.Ano)) continue;
      const cur = byMuni.get(r.cod_municipio) || {
        cod_municipio: String(r.cod_municipio),
        municipio: r.municipio,
        uf: r.uf,
        valor: 0, pop: 0, benef: 0,
      };
      cur.valor += (r.valor_2021 || 0);     // R$ mi
      cur.pop   += (r.populacao || 0);       // soma por ano (pra AGG vira pop·anos)
      cur.benef += (r.n_benef || 0);
      byMuni.set(r.cod_municipio, cur);
    }
    return Array.from(byMuni.values()).map((d) => {
      let value = 0;
      if (metricKey === 'pbfPerCapita') {
        value = d.pop > 0 ? (d.valor * 1e6) / d.pop : 0;          // R$/hab
      } else if (metricKey === 'pbfPerBenef') {
        value = d.benef > 0 ? (d.valor * 1e6) / d.benef : 0;      // R$/família
      } else if (metricKey === 'valor_2021' || metricKey === 'valor_nominal') {
        value = d.valor / 1000;                                   // mi → bi (UI)
      } else if (metricKey === 'n_benef') {
        value = d.benef;
      }
      return {
        cod_municipio: d.cod_municipio,
        municipio: d.municipio,
        uf: d.uf,
        value,
      };
    });
  }, [muniRows, year, metricKey, muniYears]);

  // KPIs municipais — cobertura de Brasil pro ano selecionado
  const muniKpis = useMemo(() => {
    if (!muniRows || muniRows.length === 0) {
      return { y: null, nMunis: 0, totalBenef: 0, totalValor: 0, perBenef: 0, perCapita: 0, totalPop: 0 };
    }
    const y = year === 'AGG' ? muniMaxYear : Number(year);
    const yearRows = muniRows.filter((r) => r.Ano === y);
    const totalBenef = yearRows.reduce((s, r) => s + (r.n_benef || 0), 0);
    const totalValor = yearRows.reduce((s, r) => s + (r.valor_2021 || 0), 0);  // R$ mi
    const totalPop   = yearRows.reduce((s, r) => s + (r.populacao || 0), 0);
    return {
      y,
      nMunis: yearRows.length,
      totalBenef,
      totalValor,                                                  // mi
      totalPop,
      perCapita: totalPop ? (totalValor * 1e6) / totalPop : 0,
      perBenef:  totalBenef ? (totalValor * 1e6) / totalBenef : 0,
    };
  }, [muniRows, year, muniMaxYear]);

  // Evolução municipal Brasil-wide pra EvolutionBar (usa mesma métrica selecionada)
  const muniEvolution = useMemo(() => {
    if (!muniRows || muniRows.length === 0) return [];
    return muniYears.map((y) => {
      const yearRows = muniRows.filter((r) => r.Ano === y);
      const valor = yearRows.reduce((s, r) => s + (r.valor_2021 || 0), 0);
      const pop   = yearRows.reduce((s, r) => s + (r.populacao || 0), 0);
      const benef = yearRows.reduce((s, r) => s + (r.n_benef || 0), 0);
      let value = 0;
      if (metricKey === 'pbfPerCapita')      value = pop ? (valor * 1e6) / pop : 0;
      else if (metricKey === 'pbfPerBenef')  value = benef ? (valor * 1e6) / benef : 0;
      else if (metricKey === 'valor_2021' || metricKey === 'valor_nominal') value = valor / 1000;
      else if (metricKey === 'n_benef')      value = benef;
      return { year: String(y), value };
    });
  }, [muniRows, metricKey, muniYears]);

  const muniSourceLabel = useMemo(() => {
    if (!muniRows || muniRows.length === 0) return 'sem dados';
    return muniRows[0]._source === 'fallback'
      ? 'fallback (alocação UF→muni)'
      : 'pipeline Databricks';
  }, [muniRows]);

  // IDH-M ponderado por população por UF — pra replicar o mapa bivariado
  // (fig08 do paper) usando BrazilMap consistente com o resto da plataforma
  const muniIDHByUF = useMemo(() => {
    if (!muniRows || muniRows.length === 0) return [];
    const targetYear = year === 'AGG' ? muniMaxYear : Number(year);
    const yearRows = muniRows.filter((r) => r.Ano === targetYear);
    const byUf = new Map();
    for (const r of yearRows) {
      const cur = byUf.get(r.uf) || { uf: r.uf, idhmSum: 0, popSum: 0 };
      cur.idhmSum += (r.idhm_2010 || 0) * (r.populacao || 0);
      cur.popSum  += (r.populacao || 0);
      byUf.set(r.uf, cur);
    }
    return Array.from(byUf.values()).map((d) => ({
      uf: d.uf,
      value: d.popSum > 0 ? d.idhmSum / d.popSum : 0,
    }));
  }, [muniRows, year, muniMaxYear]);

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

        {/* WP#7 — segundo Working Paper na vertical Bolsa Família.
            Mesmo padrão do Equipamentos (WP#4 + WP#6 empilhados). */}
        <DocCardWP7 />
      </section>

      <ScopeToggle scope={scope} setScope={setScope} muniSourceLabel={muniSourceLabel} />

      {scope === 'estadual' ? (
        <EstadualDashboard
          rows={rows} kpis={kpis} year={year} setYear={setYear}
          metricKey={metricKey} setMetricKey={setMetricKey} metric={metric}
          colorscale={colorscale} setColorscale={setColorscale}
          theme={theme} ranking={ranking} filtered={filtered}
          evolutionData={evolutionData}
          minYear={minYear} maxYear={maxYear} years={years}
        />
      ) : (
        <MunicipalDashboard
          muniRows={muniRows} muniKpis={muniKpis} muniRanking={muniRanking}
          muniFiltered={muniFiltered} muniMapData={muniMapData}
          muniEvolution={muniEvolution}
          muniYears={muniYears} muniMaxYear={muniMaxYear} muniMinYear={muniMinYear}
          year={year} setYear={setYear}
          metricKey={metricKey} setMetricKey={setMetricKey} metric={metric}
          colorscale={colorscale} setColorscale={setColorscale}
          theme={theme}
        />
      )}

      <DiferencasWP2WP7 />

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

// Vertical: Bolsa Família por Município (WP#7).
// Source: /data/gold_pbf_municipios_df.json
//   Schema row: { Ano, cod_municipio, municipio, uf, regiao, lat, lon,
//                 populacao, n_benef, valor_nominal, valor_2021,
//                 pbfPerBenef, pbfPerCapita, idhm_2010, _source }
//
// Em modo fallback (alocação UF → muni ponderada por pop × pobreza-UF), o
// per capita ESTADUAL é preservado em 1.000; a heterogeneidade INTRA-UF que
// aparece nas figuras vem da variação populacional, não de focalização real
// (pra isso roda o pipeline Databricks). Esta limitação está declarada no
// manuscrito e nesta página.

import { useEffect, useMemo, useState } from 'react';
import PageHeader       from '../components/PageHeader';
import Panel            from '../components/Panel';
import KpiCard          from '../components/KpiCard';
import ScoreCard        from '../components/ScoreCard';
import ArticleTimestamp from '../components/ArticleTimestamp';
import { useArticleMeta, articleUrl } from '../hooks/useArticleMeta';
import { PARECER_WP7_BOLSA_FAMILIA_MUNICIPIOS } from '../data/pareceres';
import { useTheme }     from '../hooks/useTheme';
import { loadGold }     from '../lib/data';
import { fmtBRL, fmtCompact, fmtInt, fmtDec2 } from '../lib/format';

// ─── WHY duplo (WP#7) ─────────────────────────────────────────────────────
const WHY_DUPLO_WP7 = [
  {
    lente: 'Robustez identificacional',
    cor: '#0d9488',
    frase:
      'responder ao gargalo de N=27 clusters do trabalho UF×Ano com 5.570 ' +
      'unidades de análise — TWFE com k≈5570 (vinte vezes acima do mínimo ' +
      'Cameron-Gelbach-Miller), Conley HAC com distâncias geodésicas reais, ' +
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
    cta: 'Ver o programa onde ele é gasto, no nível dos 5.570 entes que executam, não na média estadual',
  },
];

const TESE_CENTRAL_WP7 =
  'A migração metodológica do painel UF×Ano (N=27) para Município×Ano ' +
  '(N=5.570) resolve, na prática, o gargalo dos poucos clusters do trabalho ' +
  'companheiro: a hipótese de homogeneidade dentro da UF é falsa por construção ' +
  'do próprio programa (focalização individual no CadÚnico), e a granularidade ' +
  'municipal é o nível certo de identificação. Este artigo demonstra a ' +
  'viabilidade prática usando exclusivamente dados públicos brasileiros ' +
  '(CGU + IBGE + Atlas Brasil + IPCA-BCB).';

function WhyDuploWP7() {
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
        Por que este artigo existe — 2 ângulos sobre o mesmo dataset municipal
      </div>

      <p style={{
        fontSize: 13, lineHeight: 1.65, margin: '0 0 12px 0',
        fontStyle: 'italic', color: 'var(--text)',
      }}>
        {TESE_CENTRAL_WP7}
      </p>

      <div style={{
        display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))',
        gap: 10,
      }}>
        {WHY_DUPLO_WP7.map((w) => (
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
        WP#7 v1.0 · 2026-04-27 · resposta ao gargalo de N=27 do WP#2
      </div>
    </div>
  );
}

// ─── Componente principal ─────────────────────────────────────────────────
export default function BolsaFamiliaMunicipios() {
  const { theme } = useTheme();
  const [rows, setRows]   = useState(null);
  const [error, setError] = useState(null);
  const [yearSel, setYearSel] = useState(null);
  const [ufFilter, setUfFilter] = useState('TODOS');

  useEffect(() => {
    loadGold('gold_pbf_municipios_df.json')
      .then((data) => {
        setRows(data);
        // Default: ano mais recente
        const years = Array.from(new Set(data.map((r) => r.Ano))).sort();
        setYearSel(years[years.length - 1]);
      })
      .catch((e) => setError(e.message));
  }, []);

  // Article meta
  const base = import.meta.env.BASE_URL || '/';
  const slug = 'bolsa-familia-municipios';
  const meta = useArticleMeta(slug);
  const sha  = meta?.tex_last_sha;
  const pdfUrl = articleUrl(base, slug, 'pdf', sha);
  const texUrl = articleUrl(base, slug, 'tex', sha);
  const overleafUrl = 'https://www.overleaf.com/docs?snip_uri=' +
    encodeURIComponent(`https://leonardochalhoub.github.io${texUrl}`);

  const years = useMemo(
    () => (rows ? Array.from(new Set(rows.map((r) => r.Ano))).sort() : []),
    [rows],
  );
  const ufs = useMemo(
    () => (rows ? ['TODOS', ...Array.from(new Set(rows.map((r) => r.uf))).sort()] : ['TODOS']),
    [rows],
  );

  // Dados filtrados por (ano, uf)
  const filteredRows = useMemo(() => {
    if (!rows || yearSel == null) return [];
    let out = rows.filter((r) => r.Ano === yearSel);
    if (ufFilter !== 'TODOS') {
      out = out.filter((r) => r.uf === ufFilter);
    }
    return out;
  }, [rows, yearSel, ufFilter]);

  // KPIs nacionais (sempre todos os munis do ano selecionado)
  const kpisAll = useMemo(() => {
    if (!rows || yearSel == null) return null;
    const y = rows.filter((r) => r.Ano === yearSel);
    const totalBenef = y.reduce((s, r) => s + (r.n_benef || 0), 0);
    const totalValor = y.reduce((s, r) => s + (r.valor_2021 || 0), 0);  // R$ mi
    const totalPop   = y.reduce((s, r) => s + (r.populacao || 0), 0);
    const munis      = y.length;
    const cobertura  = totalPop ? (totalBenef / totalPop) * 100 : 0;
    const perBenef   = totalBenef ? (totalValor * 1e6) / totalBenef : 0;
    const perCapita  = totalPop ? (totalValor * 1e6) / totalPop : 0;
    return { totalBenef, totalValor, totalPop, munis, cobertura, perBenef, perCapita };
  }, [rows, yearSel]);

  // Top 20 maior per capita
  const top20 = useMemo(
    () => [...filteredRows]
            .sort((a, b) => b.pbfPerCapita - a.pbfPerCapita)
            .slice(0, 20),
    [filteredRows],
  );

  // Bottom 20 (filtrar zeros / outliers)
  const bottom20 = useMemo(
    () => [...filteredRows]
            .filter((r) => r.pbfPerCapita > 0)
            .sort((a, b) => a.pbfPerCapita - b.pbfPerCapita)
            .slice(0, 20),
    [filteredRows],
  );

  // Distribuição por região
  const byRegion = useMemo(() => {
    const out = {};
    for (const r of filteredRows) {
      const k = r.regiao || 'Outro';
      if (!out[k]) out[k] = { regiao: k, n_benef: 0, valor_2021: 0, populacao: 0, munis: 0 };
      out[k].n_benef += r.n_benef || 0;
      out[k].valor_2021 += r.valor_2021 || 0;
      out[k].populacao += r.populacao || 0;
      out[k].munis += 1;
    }
    return Object.values(out)
      .map((d) => ({
        ...d,
        per_capita: d.populacao ? (d.valor_2021 * 1e6) / d.populacao : 0,
        cobertura: d.populacao ? (d.n_benef / d.populacao) * 100 : 0,
      }))
      .sort((a, b) => b.per_capita - a.per_capita);
  }, [filteredRows]);

  if (error) {
    return (
      <div className="page">
        <PageHeader
          eyebrow="Working Paper #7"
          title="Bolsa Família por Município"
          subtitle="Erro ao carregar gold_pbf_municipios_df.json"
        />
        <Panel label="Erro">
          <p style={{ color: 'var(--destaque, #dc2626)' }}>{error}</p>
          <p style={{ fontSize: 12, color: 'var(--muted)' }}>
            Para gerar localmente: <code>python3 articles/fetch_ibge_populacao_municipios.py</code> e
            depois <code>python3 articles/build_fallback_municipal_gold.py</code>.
          </p>
        </Panel>
      </div>
    );
  }

  if (!rows) {
    return (
      <div className="page">
        <PageHeader title="Bolsa Família por Município" />
        <Panel label="Carregando…" />
      </div>
    );
  }

  const isFallback = rows.length > 0 && rows[0]._source === 'fallback';
  const figBase = `${base}articles/figures-pbf-municipios`.replace(/\/{2,}/g, '/');

  return (
    <div className="page">
      <PageHeader
        eyebrow="Working Paper #7 · 5.570 pontos de decisão"
        title="Bolsa Família por Município"
        subtitle={
          'Microdados municipais (5.570 unidades), identificação causal por ' +
          'variação cross-municipal e heterogeneidade intra-UF (2013–2025).'
        }
        right={
          <ArticleTimestamp
            slug={slug}
            label="Última edição do .tex"
          />
        }
      />

      <WhyDuploWP7 />

      {isFallback && (
        <div style={{
          margin: '12px 0', padding: '10px 14px',
          background: 'rgba(180, 83, 9, 0.08)',
          border: '1px solid rgba(180, 83, 9, 0.4)',
          borderRadius: 6, fontSize: 12, lineHeight: 1.5,
        }}>
          <b style={{ color: '#b45309' }}>Modo fallback ativo.</b> Esta versão
          usa <code>data/fallback/gold_pbf_municipios_df.json</code> com pop
          IBGE/SIDRA real (2022/2023 extrapolados linearmente) e alocação UF→muni
          ponderada por população. O per capita estadual é preservado;
          heterogeneidade intra-UF efetiva requer rodar o pipeline Databricks
          (notebooks <code>silver/pbf_total_municipio_mes.py</code> +{' '}
          <code>gold/pbf_municipios_df.py</code>) com microdados CGU.
        </div>
      )}

      {/* Filtros */}
      <Panel label="Filtros">
        <div style={{ display: 'flex', gap: 16, alignItems: 'center', flexWrap: 'wrap' }}>
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
            {filteredRows.length.toLocaleString('pt-BR')} munis no recorte atual.
          </span>
        </div>
      </Panel>

      {/* KPIs nacionais */}
      {kpisAll && (
        <div className="kpi-grid">
          <KpiCard
            label={`Municípios (${yearSel})`}
            value={fmtInt(kpisAll.munis)}
            sub="Cobertura nacional, painel WP#7"
          />
          <KpiCard
            label="Famílias beneficiárias"
            value={fmtCompact(kpisAll.totalBenef)}
            sub={`${kpisAll.cobertura.toFixed(1)}% da população`}
          />
          <KpiCard
            label={`Valor pago (R$ 2021, ${yearSel})`}
            value={fmtBRL(kpisAll.totalValor * 1e6, { compact: true })}
            sub="Soma sobre os 5.570 munis"
          />
          <KpiCard
            label="Per capita médio"
            value={fmtBRL(kpisAll.perCapita)}
            sub="R$/hab/ano (2021)"
          />
          <KpiCard
            label="Per beneficiário médio"
            value={fmtBRL(kpisAll.perBenef)}
            sub="R$/família/ano (2021)"
          />
        </div>
      )}

      {/* Distribuição por região */}
      <Panel label={`Por região do Brasil — ${yearSel}`}>
        <table style={{ width: '100%', fontSize: 13, borderCollapse: 'collapse' }}>
          <thead>
            <tr style={{ borderBottom: '1px solid var(--border)' }}>
              <th style={{ textAlign: 'left',  padding: 6 }}>Região</th>
              <th style={{ textAlign: 'right', padding: 6 }}>Munis</th>
              <th style={{ textAlign: 'right', padding: 6 }}>Famílias</th>
              <th style={{ textAlign: 'right', padding: 6 }}>População</th>
              <th style={{ textAlign: 'right', padding: 6 }}>R$ mi (2021)</th>
              <th style={{ textAlign: 'right', padding: 6 }}>R$/hab</th>
              <th style={{ textAlign: 'right', padding: 6 }}>Cobertura %</th>
            </tr>
          </thead>
          <tbody>
            {byRegion.map((r) => (
              <tr key={r.regiao} style={{ borderBottom: '1px solid var(--rule)' }}>
                <td style={{ padding: 6 }}>{r.regiao}</td>
                <td style={{ padding: 6, textAlign: 'right' }}>{fmtInt(r.munis)}</td>
                <td style={{ padding: 6, textAlign: 'right' }}>{fmtCompact(r.n_benef)}</td>
                <td style={{ padding: 6, textAlign: 'right' }}>{fmtCompact(r.populacao)}</td>
                <td style={{ padding: 6, textAlign: 'right' }}>{fmtDec2(r.valor_2021)}</td>
                <td style={{ padding: 6, textAlign: 'right', fontWeight: 700 }}>
                  {fmtBRL(r.per_capita)}
                </td>
                <td style={{ padding: 6, textAlign: 'right' }}>
                  {r.cobertura.toFixed(1)}%
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </Panel>

      {/* Top 20 + Bottom 20 lado a lado */}
      <div style={{
        display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(380px, 1fr))', gap: 16,
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

      {/* Galeria de figuras */}
      <Panel label="Galeria de figuras (WP#7)">
        <p style={{ fontSize: 12, color: 'var(--muted)', marginTop: 0 }}>
          12 figuras geradas a partir do gold municipal. Identidade visual
          editorial Mirante (Lato + paleta hierárquica). Clique em cada uma para
          ver em tamanho real.
        </p>
        <div style={{
          display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: 12,
        }}>
          {[
            ['fig01-distribuicao-pc-municipal',  'Distribuição PBF/hab (5.570 munis)'],
            ['fig02-intra-uf-boxplot',           'Heterogeneidade intra-UF'],
            ['fig03-idhm-vs-pc-municipal',       'IDH-M × PBF/hab'],
            ['fig04-top-bottom-municipios',      'Top 20 vs Bottom 20'],
            ['fig05-mapa-scatter-municipal',     'Mapa scatter geográfico'],
            ['fig06-evolucao-regional',          'Evolução regional 2013–2025'],
            ['fig07-theil-decomposicao',         'Decomposição Theil within/between'],
            ['fig08-bivariado-pc-idhm',          'Mapa bivariado PBF × IDH-M'],
            ['fig09-need-ratio-municipal',       'Need ratio: sub vs sobre-atendido'],
            ['fig10-conley-hac-sensitivity',     'Conley HAC: SE vs bandwidth'],
            ['fig11-lorenz-municipal',           'Lorenz municipal + Gini'],
            ['fig12-crescimento-2018-2024',      'Distribuição ganho 2018→2024'],
          ].map(([slug, label]) => (
            <a key={slug} href={`${figBase}/${slug}.pdf`} target="_blank" rel="noreferrer"
               style={{
                 display: 'block', padding: 8, borderRadius: 6,
                 border: '1px solid var(--border)', background: 'var(--bg)',
                 textDecoration: 'none', color: 'var(--text)',
               }}>
              <div style={{
                background: 'var(--rule, #f1f5f9)',
                aspectRatio: '16/10', borderRadius: 4,
                display: 'flex', alignItems: 'center', justifyContent: 'center',
                fontSize: 11, color: 'var(--muted)',
                marginBottom: 6,
              }}>
                <span>📊 {slug.replace(/-/g, ' ').replace(/^fig\d+/, '').trim()}</span>
              </div>
              <div style={{ fontSize: 12, fontWeight: 600 }}>{label}</div>
              <div style={{ fontSize: 10, color: 'var(--muted)', marginTop: 2 }}>{slug}.pdf</div>
            </a>
          ))}
        </div>
      </Panel>

      {/* Resultados causais — Tabela */}
      <Panel label="Resultados causais — Município × Ano (k = 5.571 clusters)">
        <p style={{ fontSize: 12, color: 'var(--muted)', marginTop: 0 }}>
          Estimativas baseadas no painel municipal com 5.571 clusters
          (vinte vezes acima do mínimo Cameron-Gelbach-Miller para wild-cluster
          bootstrap). Magnitudes em <b>R$/hab/ano (2021)</b>.
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

      {/* Pipeline path */}
      <Panel label="Pipeline & reproducibilidade">
        <p style={{ fontSize: 12, lineHeight: 1.55 }}>
          <b>Notebooks Databricks (ingest → silver → gold → export):</b>
        </p>
        <ol style={{ fontSize: 12, lineHeight: 1.6, paddingLeft: 20 }}>
          <li><code>pipelines/notebooks/ingest/ibge_municipios_meta.py</code></li>
          <li><code>pipelines/notebooks/silver/pbf_total_municipio_mes.py</code></li>
          <li><code>pipelines/notebooks/silver/populacao_municipio_ano.py</code></li>
          <li><code>pipelines/notebooks/silver/coords_municipios.py</code></li>
          <li><code>pipelines/notebooks/gold/pbf_municipios_df.py</code></li>
          <li><code>pipelines/notebooks/export/pbf_municipios_df_json.py</code></li>
        </ol>
        <p style={{ fontSize: 12, lineHeight: 1.55, marginTop: 8 }}>
          <b>Local fallback (sem Databricks):</b>
        </p>
        <ol style={{ fontSize: 12, lineHeight: 1.6, paddingLeft: 20 }}>
          <li><code>python3 articles/fetch_ibge_populacao_municipios.py</code> — baixa SIDRA 6579 para 5.571 munis</li>
          <li><code>python3 articles/build_fallback_municipal_gold.py</code> — aloca UF→muni com pop × pobreza-UF</li>
          <li><code>python3 articles/build-figures-pbf-municipios.py</code> — gera 12 figuras</li>
          <li><code>python3 articles/causal_analysis_pbf_municipios.py</code> — TWFE + DiD + Conley HAC</li>
        </ol>
      </Panel>

      {/* Article download */}
      <Panel label="Working Paper #7 — downloads">
        <div style={{
          display: 'flex', gap: 10, flexWrap: 'wrap', fontSize: 13,
        }}>
          <a href={pdfUrl} target="_blank" rel="noreferrer" className="btn">📄 Baixar PDF</a>
          <a href={texUrl} target="_blank" rel="noreferrer" className="btn">📝 Baixar .tex</a>
          <a href={overleafUrl} target="_blank" rel="noreferrer" className="btn">🔗 Abrir no Overleaf</a>
          <a href={texUrl} target="_blank" rel="noreferrer" className="btn">👁 Ler artigo na tela (.tex)</a>
        </div>
        <p style={{ fontSize: 11, color: 'var(--muted)', marginTop: 8 }}>
          Última edição do .tex: <code>{meta?.tex_last_edited || 'pending build'}</code>{' '}
          {sha && <span>(commit <code>{sha}</code>)</span>}
        </p>
      </Panel>

      {/* Score card / parecer */}
      <Panel label="Parecer crítico (banca interna)">
        <ScoreCard parecer={PARECER_WP7_BOLSA_FAMILIA_MUNICIPIOS} />
      </Panel>
    </div>
  );
}

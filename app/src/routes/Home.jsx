import { Fragment, useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { DeltaLogoLarge, ClaudeLogoLarge } from '../components/TechBadges';
import ScoreCard from '../components/ScoreCard';
import { PARECER_GLOBAL } from '../data/pareceres';
import { loadStats } from '../lib/data';
import { fmtCompact, fmtInt } from '../lib/format';

const VERTICAIS = [
  {
    to: '/bolsa-familia',
    eyebrow: 'Transferências de renda',
    title: 'Bolsa Família',
    desc: 'Pagamentos, beneficiários e valor real (R$ 2021) por UF e ano. Fontes: CGU · IBGE · BCB.',
    period: '2013 – 2025',
    available: true,
  },
  {
    to: '/equipamentos',
    eyebrow: 'Saúde · equipamentos médicos',
    title: 'Equipamentos médicos (CNES)',
    desc: 'Multi-seleção entre dezenas de tipos de equipamentos (RM, TC, mamógrafos, raio-X, leitos UTI, ventiladores…) por UF, com split público (SUS) e privado. Fontes: DATASUS/CNES · IBGE.',
    period: '2005 – 2025',
    available: true,
  },
  {
    to: '/emendas',
    eyebrow: 'Transparência fiscal',
    title: 'Emendas Parlamentares',
    desc: 'Execução de emendas parlamentares por UF (RP6 individual, RP7 bancada, RP9 relator). Fontes: Portal da Transparência (CGU) · IBGE · BCB.',
    period: '2014 – 2025',
    available: true,
  },
  {
    to: '/incontinencia-urinaria',
    eyebrow: 'Saúde · incontinência urinária',
    title: 'Incontinência Urinária (SIH)',
    desc: 'Tratamento cirúrgico no SUS — vias abdominal vs vaginal (SIGTAP 0409010499 e 0409070270). Volume, despesa pública (R$ 2021), permanência hospitalar e distribuição por UF. Fontes: DATASUS/SIH-AIH-RD · IBGE · BCB.',
    period: '2015 – 2025',
    available: true,
  },
  {
    to: '/rais',
    eyebrow: 'Mercado de trabalho · governança de dados',
    title: 'RAIS — Vínculos Públicos',
    desc: 'Replica e estende a monografia do autor (UFRJ MBA Eng. Dados, 2023) — comparação de formatos Lakehouse (CSV / Parquet / Delta / Iceberg / Hudi) e scoring FAIR sobre microdados RAIS. Cobertura maximalista (anos sem publicação no PDET são ignorados). Fontes: PDET/MTE · IBGE · BCB.',
    period: '1985 – 2025',
    available: true,
  },
];

const MEDALLION = [
  { tier: 'Bronze', color: 'var(--bronze)', desc: 'Ingestão crua: ZIPs do Portal da Transparência, FTP DATASUS, APIs IBGE / BCB.' },
  { tier: 'Silver', color: 'var(--silver)', desc: 'Limpeza, tipagem e normalização. Schemas estáveis, deduplicação, deflação por IPCA.' },
  { tier: 'Gold',   color: 'var(--gold)',   desc: 'Agregados por UF e ano, prontos pro front. Saída: JSON versionado neste repo.' },
];

// Format bytes → "42.3 GB" / "256 MB"
function fmtBytes(b) {
  if (b == null || !Number.isFinite(b)) return '—';
  const u = ['B', 'KB', 'MB', 'GB', 'TB'];
  let i = 0; let v = b;
  while (v >= 1024 && i < u.length - 1) { v /= 1024; i += 1; }
  return `${v < 10 ? v.toFixed(1) : Math.round(v)} ${u[i]}`;
}

export default function Home() {
  const [stats, setStats] = useState(null);

  useEffect(() => {
    loadStats('platform_stats.json').then(setStats).catch(() => setStats(null));
  }, []);

  return (
    <>
      <section className="hero">
        <div className="hero-grid">
          <div className="hero-text">
            <div className="hero-eyebrow">Plataforma aberta · pt-BR · Big Data público</div>
            <h1 className="hero-title">Dados públicos do Brasil em um só lugar.</h1>
            <p className="hero-tagline">
              Pipelines em arquitetura medallion (bronze → silver → gold) sobre fontes oficiais
              — DATASUS, IBGE, CGU, BCB — processados em <b>Apache Spark</b> e armazenados em
              <b> Delta Lake</b> no Databricks. Cada vertical aqui é um app interativo
              alimentado pelo mesmo pipeline open-source.
            </p>
          </div>

          <div className="hero-logos">
            <a className="hero-logo-card hero-logo-card--delta" href="https://delta.io/" target="_blank" rel="noreferrer" title="Powered by Delta Lake">
              <DeltaLogoLarge height={56} />
            </a>
            <a className="hero-logo-card" href="https://spark.apache.org/" target="_blank" rel="noreferrer" title="Powered by Apache Spark">
              <img src={`${import.meta.env.BASE_URL}spark-logo.svg`.replace(/\/{2,}/g, '/')} alt="Apache Spark" />
            </a>
            <a className="hero-logo-card" href="https://www.anthropic.com/claude-code" target="_blank" rel="noreferrer" title="Built with Claude Code (Anthropic)">
              <ClaudeLogoLarge height={56} />
            </a>
          </div>
        </div>
      </section>

      {stats && <BigDataStrip stats={stats} />}

      <ManifestoTese />

      <ScoreCard parecer={PARECER_GLOBAL} />

      <section className="vertical-grid">
        {VERTICAIS.map((v) =>
          v.available ? (
            <Link key={v.to} className="vertical-card" to={v.to}>
              <div className="vertical-card-eyebrow">{v.eyebrow}</div>
              <h3 className="vertical-card-title">{v.title}</h3>
              <p className="vertical-card-desc">{v.desc}</p>
              <div className="vertical-card-footer">
                <span>{v.period}</span>
                <span>Abrir →</span>
              </div>
            </Link>
          ) : (
            <div key={v.to} className="vertical-card is-coming">
              <div className="vertical-card-eyebrow">{v.eyebrow}</div>
              <h3 className="vertical-card-title">{v.title}</h3>
              <p className="vertical-card-desc">{v.desc}</p>
              <div className="vertical-card-footer">
                <span>{v.period}</span>
              </div>
            </div>
          ),
        )}
      </section>

      <section style={{ marginTop: 8 }}>
        <div className="kicker" style={{ marginBottom: 8 }}>Como funciona o pipeline</div>
        <div className="medallion">
          {MEDALLION.map((m) => (
            <div key={m.tier} className="medallion-tier" style={{ '--tier-color': m.color }}>
              <div className="kicker">{m.tier}</div>
              <h4>{m.tier === 'Bronze' ? 'Ingestão' : m.tier === 'Silver' ? 'Limpeza & tipagem' : 'Agregação'}</h4>
              <p>{m.desc}</p>
            </div>
          ))}
        </div>
      </section>

      <section className="panel" style={{ marginTop: 14 }}>
        <div className="panelHead">
          <span className="panelLabel">Nota técnica</span>
          <span className="kicker">Stack 100% gratuito</span>
        </div>
        <div style={{ fontSize: 13, color: 'var(--muted)', lineHeight: 1.7 }}>
          Ingestão e transformação rodam em <b>Databricks Free Edition</b> (PySpark + Unity Catalog).
          Os JSONs gold ficam versionados aqui no repo (em <code>/data/gold</code>) e são consumidos
          diretamente pelo front. O refresh é orquestrado por <b>GitHub Actions</b> em cron mensal.
          O pipeline é o produto — o site é a vitrine.
        </div>
      </section>
    </>
  );
}

// ── Manifesto-tese (Conselho do Mirante, abr/2026) ────────────────────────
// Parágrafo-tese formalizado na Reunião #1 do Conselho do Mirante (2026-04-26)
// como horizonte de doutorado do projeto. Estética sóbria, sem ornamento.
function ManifestoTese() {
  return (
    <section className="panel" style={{
      marginTop: 14,
      borderLeft: '4px solid #ca8a04',
      background: 'linear-gradient(180deg, rgba(202,138,4,0.04), rgba(202,138,4,0.01))',
    }}>
      <div className="panelHead">
        <span className="panelLabel">
          Tese embutida — horizonte de doutorado
        </span>
        <span className="kicker">
          Formalizada na Reunião #1 do Conselho do Mirante · 2026-04-26
        </span>
      </div>
      <p style={{
        fontSize: 14, lineHeight: 1.7, margin: 0,
        fontStyle: 'italic', color: 'var(--text)',
      }}>
        O Mirante dos Dados é, ao mesmo tempo, plataforma e demonstração — uma
        prova-de-conceito de que pesquisa aplicada sobre dados públicos
        brasileiros pode ser construída como artefato de engenharia de
        software (versionada, reprodutível, auditável <i>end-to-end</i>), com
        identificação causal sobre descontinuidades institucionais,
        visualização honesta como evidência primária e acesso democraticamente
        simétrico — e que essa quádrupla virada (engenharia + causalidade +
        viz + redistribuição epistêmica) é em si contribuição metodológica
        original passível de defesa de doutorado.
      </p>
    </section>
  );
}

// ── Big Data público strip ────────────────────────────────────────────────
function BigDataStrip({ stats }) {
  const totalRaw = stats.raw?.total_bytes ?? 0;
  const totalFiles = stats.raw?.total_files ?? 0;
  const largest = stats.largest_table;

  const verticals = stats.verticals || {};
  // Ordem preferida; verticais não listadas aparecem no fim por ordem alfabética.
  // Default genérico pra que novas verticais apareçam automaticamente.
  const PREFERRED_ORDER = ['pbf', 'equipamentos', 'equipamentos-sus', 'emendas', 'uropro', 'rais'];
  const orderedVerticals = [
    ...PREFERRED_ORDER.filter((k) => verticals[k]),
    ...Object.keys(verticals).filter((k) => !PREFERRED_ORDER.includes(k)).sort(),
  ];

  // Label legível por chave; fallback humaniza a chave caso novo vertical não liste aqui
  const verticalLabel = {
    pbf:                 'Bolsa Família',
    equipamentos:        'Equipamentos médicos (CNES)',
    'equipamentos-sus':  'Equipamentos SUS',
    emendas:             'Emendas Parlamentares',
    uropro:              'Incontinência Urinária (SIH)',
    rais:                'RAIS — Vínculos Públicos',
  };
  const labelOf = (k) => verticalLabel[k]
    || k.charAt(0).toUpperCase() + k.slice(1).replace(/_/g, ' ');

  return (
    <section className="bigdata-strip">
      <div className="bigdata-headline">
        <div className="kicker">Big Data público — escala atual</div>
        <div className="bigdata-totals">
          <span><b>{fmtCompact(totalFiles)}</b> arquivos crus</span>
          <span className="dot">·</span>
          <span><b>{fmtBytes(totalRaw)}</b> de raw ingerido</span>
          {largest && (
            <>
              <span className="dot">·</span>
              <span>maior tabela: <b>{fmtCompact(largest.rows)} linhas</b> ({fmtBytes(largest.bytes)})</span>
            </>
          )}
        </div>
      </div>

      <div className="bigdata-pipelines">
        {orderedVerticals.map((k) => {
          const v = verticals[k];
          const steps = [
            {
              label: v.raw_compressed_label,
              files: v.raw_compressed_files,
              bytes: v.raw_compressed_bytes,
            },
            {
              label: v.intermediate_label,
              files: v.intermediate_files,
              bytes: v.intermediate_bytes,
            },
            {
              label: 'Delta bronze',
              bytes: v.delta_bronze_bytes,
              rows: v.delta_bronze_rows,
              highlight: true,
            },
          ].filter((s) => (s.bytes ?? 0) > 0 || (s.files ?? 0) > 0 || (s.rows ?? 0) > 0);
          return (
            <div key={k} className="bigdata-pipeline">
              <div className="bigdata-pipeline-head">
                <span className="kicker">{verticalLabel[k] || k}</span>
              </div>
              <div className="bigdata-pipeline-row">
                {steps.map((s, i) => (
                  <Fragment key={s.label}>
                    {i > 0 && <Arrow />}
                    <Step {...s} />
                  </Fragment>
                ))}
              </div>
            </div>
          );
        })}
      </div>
    </section>
  );
}

function Step({ label, files, bytes, rows, highlight }) {
  return (
    <div className={`bigdata-step${highlight ? ' is-highlight' : ''}`}>
      <div className="bigdata-step-label">{label}</div>
      <div className="bigdata-step-value">{fmtBytes(bytes)}</div>
      <div className="bigdata-step-sub">
        {files != null && `${fmtCompact(files)} arquivos`}
        {rows  != null && `${fmtCompact(rows)} linhas`}
      </div>
    </div>
  );
}

function Arrow() {
  return <span className="bigdata-arrow">→</span>;
}

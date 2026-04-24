import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { DeltaLogoLarge } from '../components/TechBadges';
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
    to: '/saude-mri',
    eyebrow: 'Saúde · ressonância magnética',
    title: 'Ressonância Magnética',
    desc: 'Distribuição de equipamentos de RM no Brasil por UF, com split público (SUS) e privado. Fontes: DATASUS/CNES · IBGE.',
    period: '2005 – 2025',
    available: true,
  },
  {
    to: '/emendas',
    eyebrow: 'Em construção',
    title: 'Emendas Parlamentares',
    desc: 'Próximo vertical: rastreamento de emendas (RP6/RP9), favorecidos e cidades-alvo.',
    period: '— · em breve',
    available: false,
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
          </div>
        </div>
      </section>

      {stats && <BigDataStrip stats={stats} />}

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

// ── Big Data público strip ────────────────────────────────────────────────
function BigDataStrip({ stats }) {
  const totalRaw = stats.raw?.total_bytes ?? 0;
  const totalFiles = stats.raw?.total_files ?? 0;
  const largest = stats.largest_table;

  const verticals = stats.verticals || {};
  const orderedVerticals = ['pbf', 'mri'].filter((k) => verticals[k]);

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
          return (
            <div key={k} className="bigdata-pipeline">
              <div className="bigdata-pipeline-head">
                <span className="kicker">{k === 'pbf' ? 'Bolsa Família' : 'Ressonância Magnética'}</span>
              </div>
              <div className="bigdata-pipeline-row">
                <Step label={v.raw_compressed_label} files={v.raw_compressed_files} bytes={v.raw_compressed_bytes} />
                <Arrow />
                <Step label={v.intermediate_label}    files={v.intermediate_files}   bytes={v.intermediate_bytes} />
                <Arrow />
                <Step label="Delta bronze"            bytes={v.delta_bronze_bytes}   rows={v.delta_bronze_rows} highlight />
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

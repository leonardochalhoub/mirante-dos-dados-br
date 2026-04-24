import { Link } from 'react-router-dom';

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
  {
    tier: 'Bronze',
    color: 'var(--bronze)',
    desc: 'Ingestão crua: ZIPs do Portal da Transparência, FTP DATASUS, APIs IBGE / BCB.',
  },
  {
    tier: 'Silver',
    color: 'var(--silver)',
    desc: 'Limpeza, tipagem e normalização. Schemas estáveis, deduplicação, deflação por IPCA.',
  },
  {
    tier: 'Gold',
    color: 'var(--gold)',
    desc: 'Agregados por UF e ano, prontos pro front. Saída: JSON versionado neste repo.',
  },
];

export default function Home() {
  return (
    <>
      <section className="hero">
        <div className="hero-grid">
          <div className="hero-text">
            <div className="hero-eyebrow">Plataforma aberta · pt-BR</div>
            <h1 className="hero-title">Dados públicos do Brasil em um só lugar.</h1>
            <p className="hero-tagline">
              Pipelines em arquitetura medallion (bronze → silver → gold) sobre fontes oficiais
              — DATASUS, IBGE, CGU, BCB — processados em <b>Apache Spark</b> e armazenados em
              <b> Delta Lake</b> no Databricks. Cada vertical aqui é um app interativo
              alimentado pelo mesmo pipeline open-source.
            </p>
          </div>

          <div className="hero-logos">
            <a
              className="hero-logo-card"
              href="https://delta.io/"
              target="_blank"
              rel="noreferrer"
              title="Powered by Delta Lake"
            >
              <img
                src={`${import.meta.env.BASE_URL}delta-lake-logo.svg`.replace(/\/{2,}/g, '/')}
                alt="Delta Lake"
              />
            </a>
            <a
              className="hero-logo-card"
              href="https://spark.apache.org/"
              target="_blank"
              rel="noreferrer"
              title="Powered by Apache Spark"
            >
              <img
                src={`${import.meta.env.BASE_URL}spark-logo.svg`.replace(/\/{2,}/g, '/')}
                alt="Apache Spark"
              />
            </a>
          </div>
        </div>
      </section>

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

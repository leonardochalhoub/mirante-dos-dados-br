import { useEffect, useState } from 'react';
import { NavLink, Outlet } from 'react-router-dom';
import { useTheme } from '../hooks/useTheme';
import { loadStats } from '../lib/data';

const NAV = [
  { to: '/',               label: 'Início',                  exact: true },
];

// Each vertical's tag (e.g. "v3") is read from platform_stats.json's
// `delta_version` for the listed gold table. Falls back to `defaultTag` while
// stats are loading or if the table is missing.
//
// `firstPublished` is the date the vertical first went to production
// (derived from git log of each route file). Ordering is chronological,
// oldest first → reflects the platform's evolution over time.
const VERTICALS = [
  { to: '/bolsa-familia',          label: 'Bolsa Família',          goldTable: 'pbf_estados_df',           defaultTag: 'v1', firstPublished: '2026-04-24' },
  { to: '/equipamentos',           label: 'Equipamentos',           goldTable: 'equipamentos_estados_ano', defaultTag: 'v1', firstPublished: '2026-04-24' },
  { to: '/emendas',                label: 'Emendas Parlamentares',  goldTable: 'emendas_estados_df',       defaultTag: 'v1', firstPublished: '2026-04-25' },
  { to: '/incontinencia-urinaria', label: 'Incontinência Urinária', goldTable: 'uropro_estados_ano',       defaultTag: 'v1', firstPublished: '2026-04-25' },
].sort((a, b) => a.firstPublished.localeCompare(b.firstPublished));

// Format ISO date as "24/abr/2026"
const MONTHS_PT = ['jan', 'fev', 'mar', 'abr', 'mai', 'jun',
                   'jul', 'ago', 'set', 'out', 'nov', 'dez'];
function fmtPubDate(iso) {
  if (!iso) return '';
  const [y, m, d] = iso.split('-');
  return `${d}/${MONTHS_PT[parseInt(m, 10) - 1]}/${y}`;
}

const flagSrc = `${import.meta.env.BASE_URL}brazil-flag.svg`.replace(/\/{2,}/g, '/');

export default function Layout() {
  const { theme, toggle } = useTheme();
  const [stats, setStats] = useState(null);

  useEffect(() => {
    loadStats('platform_stats.json').then(setStats).catch(() => setStats(null));
  }, []);

  const tagFor = (v) => {
    const goldList = stats?.tables?.gold;
    if (Array.isArray(goldList)) {
      const t = goldList.find((row) => row.table === v.goldTable);
      if (t && Number.isFinite(t.delta_version) && t.delta_version > 0) {
        return `v${t.delta_version}`;
      }
    }
    return v.defaultTag;
  };

  return (
    <div className="app">
      <aside className="sidebar">
        <NavLink to="/" className="brand" end>
          <img className="brand-flag" src={flagSrc} alt="Brasil" />
          <div>
            <div className="brand-name">Mirante dos Dados</div>
            <div className="brand-tag">Dados públicos · BR</div>
          </div>
        </NavLink>

        <nav>
          <div className="nav-section-label">Navegar</div>
          <ul className="nav-list">
            {NAV.map((item) => (
              <li key={item.to}>
                <NavLink
                  to={item.to}
                  end={item.exact}
                  className={({ isActive }) => `nav-link${isActive ? ' is-active' : ''}`}
                >
                  {item.label}
                </NavLink>
              </li>
            ))}
          </ul>
        </nav>

        <nav>
          <div className="nav-section-label">Verticais</div>
          <ul className="nav-list">
            {VERTICALS.map((v) => {
              const tag = tagFor(v);
              const pub = fmtPubDate(v.firstPublished);
              return (
                <li key={v.to}>
                  {v.soon ? (
                    <span className="nav-link nav-link-vertical" style={{ opacity: 0.55, cursor: 'default' }}>
                      <span className="nav-link-row">
                        <span className="nav-link-label">{v.label}</span>
                        <span className="nav-link-tag tag-soon">{tag}</span>
                      </span>
                      {pub && <span className="nav-link-pubdate">desde {pub}</span>}
                    </span>
                  ) : (
                    <NavLink
                      to={v.to}
                      className={({ isActive }) => `nav-link nav-link-vertical${isActive ? ' is-active' : ''}`}
                    >
                      <span className="nav-link-row">
                        <span className="nav-link-label">{v.label}</span>
                        <span className="nav-link-tag" title="Versão da tabela Delta (DESCRIBE HISTORY)">{tag}</span>
                      </span>
                      {pub && <span className="nav-link-pubdate" title="Data da primeira versão publicada">desde {pub}</span>}
                    </NavLink>
                  )}
                </li>
              );
            })}
          </ul>
        </nav>

        <div className="sidebar-footer">
          <div className="themeToggle" onClick={(e) => e.stopPropagation()}>
            <span className="kicker">Claro</span>
            <label className="switch" title="Alternar tema">
              <input type="checkbox" checked={theme === 'dark'} onChange={toggle} />
              <span className="slider" />
            </label>
            <span className="kicker">Escuro</span>
          </div>
          <div>
            <a
              href="https://github.com/leonardochalhoub/mirante-dos-dados-br"
              target="_blank"
              rel="noreferrer"
            >
              github.com/leonardochalhoub
            </a>
          </div>
          <div className="muted" style={{ fontSize: 10 }}>
            Pipeline open-source · Databricks Free Edition
          </div>
        </div>
      </aside>

      <main className="app-main">
        <div className="container">
          <Outlet />
        </div>
      </main>
    </div>
  );
}

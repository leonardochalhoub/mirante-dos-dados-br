import { NavLink, Outlet } from 'react-router-dom';
import { useTheme } from '../hooks/useTheme';

const NAV = [
  { to: '/',               label: 'Início',                  exact: true },
];

const VERTICALS = [
  { to: '/bolsa-familia',  label: 'Bolsa Família',           tag: 'V1' },
  { to: '/saude-mri',      label: 'Ressonância Magnética',   tag: 'V2' },
  { to: '/emendas',        label: 'Emendas Parlamentares',   tag: 'em breve', soon: true },
];

const flagSrc = `${import.meta.env.BASE_URL}brazil-flag.svg`.replace(/\/{2,}/g, '/');

export default function Layout() {
  const { theme, toggle } = useTheme();

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
            {VERTICALS.map((v) => (
              <li key={v.to}>
                {v.soon ? (
                  <span className="nav-link" style={{ opacity: 0.55, cursor: 'default' }}>
                    {v.label}
                    <span className="nav-link-tag tag-soon">{v.tag}</span>
                  </span>
                ) : (
                  <NavLink
                    to={v.to}
                    className={({ isActive }) => `nav-link${isActive ? ' is-active' : ''}`}
                  >
                    {v.label}
                    <span className="nav-link-tag">{v.tag}</span>
                  </NavLink>
                )}
              </li>
            ))}
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

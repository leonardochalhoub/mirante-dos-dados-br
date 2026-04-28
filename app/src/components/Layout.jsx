import { useEffect, useState } from 'react';
import { NavLink, Outlet, useLocation } from 'react-router-dom';
import { useTheme } from '../hooks/useTheme';
import { loadStats } from '../lib/data';

const NAV = [
  { to: '/',               label: 'Início',                  exact: true },
];

// Each vertical's tag (e.g. "v3") is read from platform_stats.json's
// `delta_version` for the listed gold table. Falls back to `defaultTag` while
// stats are loading or if the table is missing.
//
// `firstPublished` é o ISO datetime da primeira versão da vertical em
// produção. Para Equipamentos, usamos a data do scaffold original como
// "Ressonância Magnética / SaudeMri.jsx" (commit ef311b9) — não a data
// do rename para Equipamentos.jsx (63ce79b), que foi só uma expansão
// do mesmo vertical. O usuário desenvolveu Equipamentos ANTES de Emendas.
const VERTICALS = [
  { to: '/bolsa-familia',          label: 'Bolsa Família',          goldTable: 'pbf_estados_df',           defaultTag: 'v1', firstPublished: '2026-04-24T11:47:55-03:00' },
  { to: '/equipamentos',           label: 'Equipamentos',           goldTable: 'equipamentos_estados_ano', defaultTag: 'v1', firstPublished: '2026-04-24T11:47:55-03:00' },
  { to: '/emendas',                label: 'Emendas Parlamentares',  goldTable: 'emendas_estados_df',       defaultTag: 'v1', firstPublished: '2026-04-25T02:29:21-03:00' },
  { to: '/incontinencia-urinaria', label: 'Incontinência Urinária', goldTable: 'uropro_estados_ano',       defaultTag: 'v1', firstPublished: '2026-04-25T15:26:34-03:00' },
  { to: '/rais',                   label: 'RAIS — Vínculos Públicos', goldTable: 'rais_estados_ano',       defaultTag: 'v1', firstPublished: '2026-04-25T17:00:00-03:00' },
  { to: '/finops',                 label: 'FinOps · custo da plataforma', goldTable: 'finops_daily_spend', defaultTag: 'v1', firstPublished: '2026-04-28T00:00:00-03:00' },
].sort((a, b) => a.firstPublished.localeCompare(b.firstPublished));

// Format ISO datetime as "24/abr/2026 · 11h47 BRT".
// Garantia de UTC-3: usa toLocaleString com timeZone='America/Sao_Paulo'
// (independente da fuso do navegador do leitor → sempre BRT).
const MONTHS_PT = ['jan', 'fev', 'mar', 'abr', 'mai', 'jun',
                   'jul', 'ago', 'set', 'out', 'nov', 'dez'];
function fmtPubDate(iso) {
  if (!iso) return '';
  const dt = new Date(iso);
  if (isNaN(dt)) return iso;
  // Converte para UTC-3 explicitamente
  const partsArr = new Intl.DateTimeFormat('pt-BR', {
    timeZone: 'America/Sao_Paulo',
    year: 'numeric', month: '2-digit', day: '2-digit',
    hour: '2-digit', minute: '2-digit', hour12: false,
  }).formatToParts(dt);
  const p = Object.fromEntries(partsArr.map((x) => [x.type, x.value]));
  return `${p.day}/${MONTHS_PT[parseInt(p.month, 10) - 1]}/${p.year} · ${p.hour}h${p.minute} BRT`;
}

const flagSrc = `${import.meta.env.BASE_URL}brazil-flag.svg`.replace(/\/{2,}/g, '/');

// Apps grátis do autor — promo cards renderizados na sidebar (canto superior
// esquerdo) e no drawer mobile. Todos com URLs ao vivo no Vercel.
const FREE_APPS = [
  {
    key: 'caixa-forte',
    name: 'Caixa Forte',
    tagline: 'Controle financeiro pessoal',
    href: 'https://caixa-forte-app.vercel.app',
    icon: 'caixa-forte.svg',
    iconKind: 'currentcolor',  // SVG usa currentColor — adapta ao tema via CSS color
  },
  {
    key: 'amazing-school',
    name: 'Amazing School',
    tagline: 'Inglês com IA, gratuito',
    href: 'https://amazing-school-app.vercel.app',
    icon: 'amazing-school.png',
    iconKind: 'fixed',  // PNG fullcolor — funciona em ambos os temas via fundo branco
  },
  {
    key: 'pet-zap',
    name: 'PetZap',
    tagline: 'Vacinas e gastos do pet',
    href: 'https://pet-zap.vercel.app',
    icon: 'pet-zap.svg',
    iconKind: 'fixed',  // SVG com fills hardcoded — fundo branco garante contraste
  },
];

function FreeAppsBlock() {
  const base = import.meta.env.BASE_URL || '/';
  return (
    <section className="free-apps" aria-label="Apps grátis do autor">
      <div className="free-apps-label">Apps grátis do autor</div>
      <ul className="free-apps-list">
        {FREE_APPS.map((app) => (
          <li key={app.key}>
            <a
              href={app.href}
              target="_blank"
              rel="noreferrer"
              className="free-app-card"
              title={`${app.name} — ${app.tagline}`}
            >
              <span className={`free-app-icon free-app-icon--${app.iconKind}`}>
                <img src={`${base}ads/${app.icon}`.replace(/\/{2,}/g, '/')} alt="" />
              </span>
              <span className="free-app-meta">
                <span className="free-app-name">{app.name}</span>
                <span className="free-app-tagline">{app.tagline}</span>
              </span>
            </a>
          </li>
        ))}
      </ul>
    </section>
  );
}

// Inline SVG icons (no external deps; theme-aware via currentColor).
function IconHamburger() {
  return (
    <svg width="22" height="22" viewBox="0 0 24 24" aria-hidden="true">
      <path d="M3 6h18M3 12h18M3 18h18" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
    </svg>
  );
}
function IconClose() {
  return (
    <svg width="22" height="22" viewBox="0 0 24 24" aria-hidden="true">
      <path d="M6 6l12 12M18 6L6 18" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
    </svg>
  );
}
function IconSun() {
  return (
    <svg width="18" height="18" viewBox="0 0 24 24" aria-hidden="true" fill="none">
      <circle cx="12" cy="12" r="4" stroke="currentColor" strokeWidth="2"/>
      <path d="M12 2v3M12 19v3M2 12h3M19 12h3M4.2 4.2l2.1 2.1M17.7 17.7l2.1 2.1M4.2 19.8l2.1-2.1M17.7 6.3l2.1-2.1"
            stroke="currentColor" strokeWidth="2" strokeLinecap="round"/>
    </svg>
  );
}
function IconMoon() {
  return (
    <svg width="18" height="18" viewBox="0 0 24 24" aria-hidden="true">
      <path d="M21 12.8A9 9 0 1 1 11.2 3a7 7 0 0 0 9.8 9.8z"
            stroke="currentColor" strokeWidth="2" fill="none" strokeLinejoin="round"/>
    </svg>
  );
}

// Reusable theme toggle component — renders identically in sidebar and mobile header.
// Uses semantic <button> with aria-label so screen readers / mobile a11y stays correct.
function ThemeToggle({ theme, toggle, compact = false }) {
  const isDark = theme === 'dark';
  if (compact) {
    return (
      <button
        type="button"
        className="theme-icon-btn"
        onClick={toggle}
        aria-label={`Alternar para tema ${isDark ? 'claro' : 'escuro'}`}
        title={`Tema atual: ${isDark ? 'escuro' : 'claro'} — toque para alternar`}
      >
        {isDark ? <IconSun /> : <IconMoon />}
      </button>
    );
  }
  return (
    <div className="themeToggle" onClick={(e) => e.stopPropagation()}>
      <span className="kicker">Claro</span>
      <label className="switch" title="Alternar tema">
        <input type="checkbox" checked={isDark} onChange={toggle} />
        <span className="slider" />
      </label>
      <span className="kicker">Escuro</span>
    </div>
  );
}

export default function Layout() {
  const { theme, toggle } = useTheme();
  const [stats, setStats] = useState(null);
  const [drawerOpen, setDrawerOpen] = useState(false);
  const location = useLocation();

  useEffect(() => {
    loadStats('platform_stats.json').then(setStats).catch(() => setStats(null));
  }, []);

  // Close drawer on route change (mobile UX: tap a link → drawer closes → see content).
  useEffect(() => { setDrawerOpen(false); }, [location.pathname]);

  // Lock body scroll while drawer is open (mobile only).
  useEffect(() => {
    if (drawerOpen) document.body.classList.add('no-scroll');
    else document.body.classList.remove('no-scroll');
    return () => document.body.classList.remove('no-scroll');
  }, [drawerOpen]);

  // Close drawer on Esc.
  useEffect(() => {
    if (!drawerOpen) return;
    const onKey = (e) => { if (e.key === 'Escape') setDrawerOpen(false); };
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [drawerOpen]);

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

  // Single source of truth for the nav block — used by both sidebar (desktop)
  // and drawer (mobile). Keeps version tags + pub dates in sync everywhere.
  const navBlock = (
    <>
      {/* Theme toggle vai antes do "Navegar" (visibilidade alta, fácil acesso). */}
      <div className="sidebar-theme-toggle">
        <ThemeToggle theme={theme} toggle={toggle} />
      </div>

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

      <FreeAppsBlock />
    </>
  );

  return (
    <div className="app">
      {/* ── Mobile header (top bar): visible only on small viewports ───────── */}
      <header className="mobile-header" role="banner">
        <NavLink to="/" className="mobile-brand" end>
          <img className="brand-flag" src={flagSrc} alt="Brasil" />
          <span className="mobile-brand-name">Mirante dos Dados</span>
        </NavLink>
        <div className="mobile-header-actions">
          <ThemeToggle theme={theme} toggle={toggle} compact />
          <button
            type="button"
            className="mobile-hamburger"
            onClick={() => setDrawerOpen((v) => !v)}
            aria-label={drawerOpen ? 'Fechar menu' : 'Abrir menu'}
            aria-expanded={drawerOpen}
            aria-controls="mobile-drawer"
          >
            {drawerOpen ? <IconClose /> : <IconHamburger />}
          </button>
        </div>
      </header>

      {/* ── Desktop sidebar (≥ 901px) ──────────────────────────────────────── */}
      <aside className="sidebar" aria-label="Navegação principal">
        <NavLink to="/" className="brand" end>
          <img className="brand-flag" src={flagSrc} alt="Brasil" />
          <div>
            <div className="brand-name">Mirante dos Dados</div>
            <div className="brand-tag">Dados públicos · BR</div>
          </div>
        </NavLink>

        {navBlock}

        <div className="sidebar-footer">
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

      {/* ── Mobile drawer (slide-in from right) + scrim ────────────────────── */}
      <div
        className={`mobile-drawer-scrim${drawerOpen ? ' is-open' : ''}`}
        onClick={() => setDrawerOpen(false)}
        aria-hidden="true"
      />
      <aside
        id="mobile-drawer"
        className={`mobile-drawer${drawerOpen ? ' is-open' : ''}`}
        aria-label="Menu de navegação"
        aria-hidden={!drawerOpen}
      >
        <div className="mobile-drawer-header">
          <span className="brand-name" style={{ fontSize: 14 }}>Menu</span>
          <button
            type="button"
            className="theme-icon-btn"
            onClick={() => setDrawerOpen(false)}
            aria-label="Fechar menu"
          >
            <IconClose />
          </button>
        </div>
        <div className="mobile-drawer-body">
          {navBlock}
        </div>
        <div className="mobile-drawer-footer">
          {/* ThemeToggle agora vai antes do "Navegar" via navBlock — não duplica aqui. */}
          <div style={{ fontSize: 11, color: 'var(--muted)' }}>
            <a
              href="https://github.com/leonardochalhoub/mirante-dos-dados-br"
              target="_blank" rel="noreferrer"
            >
              github.com/leonardochalhoub
            </a>
          </div>
          <div className="muted" style={{ fontSize: 10, marginTop: 4 }}>
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

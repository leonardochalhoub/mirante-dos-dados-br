const flagSrc = `${import.meta.env.BASE_URL}brazil-flag.svg`.replace(/\/{2,}/g, '/');

export default function PageHeader({ eyebrow, title, subtitle, withFlag = true, right }) {
  return (
    <header className="page-header">
      <div className="page-header-main">
        {eyebrow && <div className="kicker" style={{ marginBottom: 6 }}>{eyebrow}</div>}
        <div className="titleRow">
          {withFlag && <img src={flagSrc} alt="" style={{ width: 22, height: 22 }} />}
          <h1 className="page-title">{title}</h1>
        </div>
        {subtitle && <p className="page-subtitle">{subtitle}</p>}
      </div>
      {right && <div className="page-header-actions">{right}</div>}
    </header>
  );
}

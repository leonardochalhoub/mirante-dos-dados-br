export default function Panel({ label, sub, right, children, className = '', exportId }) {
  return (
    <section className={`panel ${className}`.trim()} data-export-id={exportId}>
      {(label || sub || right) && (
        <header className="panelHead">
          <span className="panelLabel">{label}</span>
          {right ?? (sub && <span className="panelSub">{sub}</span>)}
        </header>
      )}
      {children}
    </section>
  );
}

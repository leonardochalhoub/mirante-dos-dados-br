// State ranking list — vertical bars per UF, ordered desc by value.
// Pure DOM (no Plotly) — fast, theme-friendly, copy/paste-friendly.

export default function StateRanking({ rows, format, accentColor }) {
  if (!rows || rows.length === 0) {
    return <div className="loading-block">Sem dados</div>;
  }
  const max = Math.max(...rows.map((r) => r.value || 0));
  return (
    <div className="ranking-list">
      {rows.map((r, i) => {
        const pct = max > 0 ? Math.max((r.value / max) * 100, 1) : 0;
        return (
          <div className="ranking-row" key={r.uf}>
            <span className="ranking-rank">{i + 1}</span>
            <span className="ranking-uf">{r.uf}</span>
            <span className="ranking-bar">
              <span
                className="ranking-bar-fill"
                style={{ width: `${pct}%`, background: accentColor || 'var(--accent)' }}
              />
            </span>
            <span className="ranking-value">{format ? format(r.value) : r.value}</span>
          </div>
        );
      })}
    </div>
  );
}

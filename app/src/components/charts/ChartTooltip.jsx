// Custom tooltip used across recharts charts. Theme-aware, monospace numbers.

export default function ChartTooltip({ active, payload, label, format, unit }) {
  if (!active || !payload || payload.length === 0) return null;
  return (
    <div className="chart-tooltip">
      <div className="chart-tooltip-label">{String(label)}</div>
      {payload.map((p, i) => (
        <div key={i} className="chart-tooltip-row">
          <span className="chart-tooltip-swatch" style={{ background: p.color || p.stroke }} />
          <span className="chart-tooltip-name">{p.name}</span>
          <span className="chart-tooltip-value">
            {format ? format(p.value, p.name) : p.value}
            {unit ? <span className="muted"> {unit}</span> : null}
          </span>
        </div>
      ))}
    </div>
  );
}

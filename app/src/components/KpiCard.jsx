export default function KpiCard({ label, value, sub, color }) {
  const style = color ? { '--card-color': color } : undefined;
  return (
    <div className="kpiCard" style={style}>
      <div className="kpiLabel">{label}</div>
      <div className="kpiValue">{value}</div>
      {sub && <div className="kpiSub">{sub}</div>}
    </div>
  );
}

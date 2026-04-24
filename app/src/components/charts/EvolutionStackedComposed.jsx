// Composed chart: stacked bars (SUS + Privado, or single sector) + line on right axis.
// Used by Saúde · MRI to show equipment counts and per-million ratio together.

import {
  ComposedChart, Bar, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer,
} from 'recharts';
import { pick } from '../../lib/colors';
import ChartTooltip from './ChartTooltip';

export default function EvolutionStackedComposed({
  data,                 // [{ year, sus?, priv?, total?, ratio }, ...]
  setor = 'todos',      // 'todos' | 'sus' | 'priv'
  theme = 'light',
  height = 320,
  fmtBar = (v) => String(v),
  fmtLine = (v) => String(v),
  yLeftLabel  = 'Equipamentos',
  yRightLabel = 'RM por milhão',
  xLabel = 'Ano',
}) {
  const grid       = theme === 'dark' ? 'rgba(255,255,255,0.08)' : 'rgba(15,23,42,0.06)';
  const tickColor  = theme === 'dark' ? '#94a3b8' : '#475569';
  const susColor   = pick('primary', theme);
  const privColor  = pick('pink',    theme);
  const lineColor  = pick('amber',   theme);

  const showSus  = setor === 'todos' || setor === 'sus';
  const showPriv = setor === 'todos' || setor === 'priv';

  return (
    <div style={{ width: '100%', height }}>
      <ResponsiveContainer>
        <ComposedChart data={data} margin={{ top: 12, right: 24, bottom: 38, left: 12 }}>
          <CartesianGrid stroke={grid} vertical={false} />
          <XAxis
            dataKey="year"
            stroke={tickColor}
            fontSize={11}
            tickLine={false}
            axisLine={{ stroke: grid }}
            interval={0}
            angle={-30}
            dy={10}
            label={xLabel ? { value: xLabel, position: 'insideBottom', offset: -22, fontSize: 11, fill: tickColor } : undefined}
          />
          <YAxis
            yAxisId="left"
            stroke={tickColor}
            fontSize={11}
            tickLine={false}
            axisLine={false}
            width={60}
            tickFormatter={(v) => fmtBar(v)}
            label={yLeftLabel ? { value: yLeftLabel, angle: -90, position: 'insideLeft', fontSize: 11, fill: tickColor, style: { textAnchor: 'middle' } } : undefined}
          />
          <YAxis
            yAxisId="right"
            orientation="right"
            stroke={tickColor}
            fontSize={11}
            tickLine={false}
            axisLine={false}
            width={56}
            tickFormatter={(v) => fmtLine(v)}
            label={yRightLabel ? { value: yRightLabel, angle: 90, position: 'insideRight', fontSize: 11, fill: tickColor, style: { textAnchor: 'middle' } } : undefined}
          />
          <Tooltip
            cursor={{ fill: theme === 'dark' ? 'rgba(255,255,255,0.05)' : 'rgba(15,23,42,0.04)' }}
            content={<ChartTooltip
              format={(v, name) => (name === 'RM/Mhab' ? fmtLine(v) : fmtBar(v))}
            />}
          />
          <Legend
            verticalAlign="bottom"
            height={28}
            iconType="square"
            wrapperStyle={{ fontSize: 11, paddingTop: 6 }}
          />
          {showSus && (
            <Bar yAxisId="left" dataKey="sus"  stackId="equip" name="Público (SUS)" fill={susColor}  radius={showPriv ? [0,0,0,0] : [4,4,0,0]} />
          )}
          {showPriv && (
            <Bar yAxisId="left" dataKey="priv" stackId="equip" name="Privado"        fill={privColor} radius={[4,4,0,0]} />
          )}
          <Line
            yAxisId="right"
            type="monotone"
            dataKey="ratio"
            name="RM/Mhab"
            stroke={lineColor}
            strokeWidth={2.2}
            dot={{ r: 3, fill: lineColor, strokeWidth: 0 }}
            activeDot={{ r: 5 }}
          />
        </ComposedChart>
      </ResponsiveContainer>
    </div>
  );
}

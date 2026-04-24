// Single-series bar chart of Brasil-wide value per year, with text labels above bars.
// Built on Recharts. Used by Bolsa Família to mirror the original chart style.

import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, LabelList, ResponsiveContainer,
} from 'recharts';
import { pick } from '../../lib/colors';
import ChartTooltip from './ChartTooltip';

export default function EvolutionBar({
  data,                  // [{ year, value }, ...]
  theme = 'light',
  yLabel = '',
  xLabel = 'Ano',
  format = (v) => String(v),
  height = 300,
  colorKey = 'primary',
}) {
  const stroke    = theme === 'dark' ? 'rgba(255,255,255,0.08)' : 'rgba(15,23,42,0.06)';
  const tickColor = theme === 'dark' ? '#94a3b8' : '#475569';
  const labelColor = theme === 'dark' ? '#e2e8f0' : '#0f172a';
  const barColor  = pick(colorKey, theme);

  return (
    <div style={{ width: '100%', height }}>
      <ResponsiveContainer>
        <BarChart data={data} margin={{ top: 28, right: 16, bottom: 30, left: 12 }}>
          <CartesianGrid stroke={stroke} vertical={false} />
          <XAxis
            dataKey="year"
            stroke={tickColor}
            fontSize={11}
            tickLine={false}
            axisLine={{ stroke }}
            interval={0}
            angle={-30}
            dy={10}
            label={xLabel ? { value: xLabel, position: 'insideBottom', offset: -18, fontSize: 11, fill: tickColor } : undefined}
          />
          <YAxis
            stroke={tickColor}
            fontSize={11}
            tickLine={false}
            axisLine={false}
            width={70}
            tickFormatter={(v) => format(v)}
            label={yLabel ? { value: yLabel, angle: -90, position: 'insideLeft', fontSize: 11, fill: tickColor, style: { textAnchor: 'middle' } } : undefined}
          />
          <Tooltip
            cursor={{ fill: theme === 'dark' ? 'rgba(255,255,255,0.05)' : 'rgba(15,23,42,0.04)' }}
            content={<ChartTooltip format={format} unit={yLabel} />}
          />
          <Bar dataKey="value" fill={barColor} radius={[4, 4, 0, 0]} isAnimationActive>
            <LabelList
              dataKey="value"
              position="top"
              formatter={(v) => format(v)}
              style={{ fill: labelColor, fontSize: 11, fontFamily: 'ui-sans-serif, system-ui' }}
            />
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}

// Generic stacked bar chart — N keys empilhadas por ano.
//
// Usado pelo UroPro pra mostrar AIH por ano discriminado por procedimento
// (Via Abdominal vs Via Vaginal vs Genérico). Pode ser reusado por qualquer
// vertical que queira "decomposição empilhada" do total ano-a-ano.
//
// Espera data: [{ year, [key1]: number, [key2]: number, ... }, ...]
// `keys` é o array das chaves a empilhar, na ordem desejada (de baixo pra cima).

import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, LabelList,
} from 'recharts';
import { pick } from '../../lib/colors';
import ChartTooltip from './ChartTooltip';

// Paleta determinística por índice (mesma que o resto do app usa)
const COLOR_KEYS = ['primary', 'pink', 'amber', 'teal', 'violet'];

export default function EvolutionStackedByKey({
  data,                  // [{ year, key1, key2, ... }, ...]
  keys,                  // [{ key, label }, ...]
  theme = 'light',
  height = 320,
  format = (v) => String(v),
  yLabel = '',
  xLabel = 'Ano',
  showTotalLabel = true,
}) {
  const grid       = theme === 'dark' ? 'rgba(255,255,255,0.08)' : 'rgba(15,23,42,0.06)';
  const tickColor  = theme === 'dark' ? '#94a3b8' : '#475569';
  const labelColor = theme === 'dark' ? '#e2e8f0' : '#0f172a';

  const colorFor = (i) => pick(COLOR_KEYS[i % COLOR_KEYS.length], theme);

  // Para o label total no topo de cada barra empilhada
  const dataWithTotal = data.map((d) => ({
    ...d,
    _total: keys.reduce((s, { key }) => s + (d[key] || 0), 0),
  }));

  return (
    <div style={{ width: '100%', height }}>
      <ResponsiveContainer>
        <BarChart data={dataWithTotal} margin={{ top: 28, right: 16, bottom: 32, left: 12 }}>
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
          <Legend
            verticalAlign="bottom"
            height={24}
            iconType="square"
            wrapperStyle={{ fontSize: 11, paddingTop: 4 }}
          />
          {keys.map(({ key, label }, i) => (
            <Bar
              key={key}
              dataKey={key}
              stackId="stack"
              name={label}
              fill={colorFor(i)}
              radius={i === keys.length - 1 ? [4, 4, 0, 0] : [0, 0, 0, 0]}
            >
              {/* Label total no topo da última barra */}
              {showTotalLabel && i === keys.length - 1 && (
                <LabelList
                  dataKey="_total"
                  position="top"
                  formatter={(v) => format(v)}
                  style={{ fill: labelColor, fontSize: 10, fontFamily: 'ui-sans-serif, system-ui' }}
                />
              )}
            </Bar>
          ))}
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}

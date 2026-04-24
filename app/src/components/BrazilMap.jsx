// Choropleth map of Brazil by UF.
// Stack: react-simple-maps + d3-scale (no Plotly).
//
// Renders SVG paths from the Brazil GeoJSON, fills each UF with a sequential
// color scale (light=low → dark=high), and shows a custom HTML tooltip on hover.
// Includes a horizontal color legend at the bottom of the panel.

import { useEffect, useMemo, useState } from 'react';
import { ComposableMap, Geographies, Geography } from 'react-simple-maps';
import { loadGeo } from '../lib/data';
import { buildColorScale } from '../lib/scales';

export default function BrazilMap({
  data,                 // [{ uf, value }, ...]
  colorscale = 'Cividis',
  theme = 'light',
  hoverFmt = (v) => String(v),
  unit = '',
  emptyColor,           // override default
}) {
  const [geo, setGeo]     = useState(null);
  const [hover, setHover] = useState(null); // { uf, value, x, y }

  useEffect(() => {
    loadGeo('brazil-states.geojson').then(setGeo).catch((e) => {
      console.error('geojson load error', e);
    });
  }, []);

  const byUf = useMemo(() => {
    const m = new Map();
    for (const d of data || []) m.set(d.uf, d.value);
    return m;
  }, [data]);

  const [min, max] = useMemo(() => {
    const vals = (data || []).map((d) => d.value).filter((v) => Number.isFinite(v));
    if (vals.length === 0) return [0, 1];
    return [Math.min(...vals), Math.max(...vals)];
  }, [data]);

  const scale       = useMemo(() => buildColorScale(colorscale, [min, max]), [colorscale, min, max]);
  const fallbackBg  = theme === 'dark' ? '#1f2937' : '#e2e8f0';
  const strokeColor = theme === 'dark' ? '#0d1117' : '#ffffff';

  if (!geo) return <div className="loading-block">Carregando mapa…</div>;
  if (!data || data.length === 0) return <div className="loading-block">Sem dados</div>;

  return (
    <div className="brazil-map-wrap">
      <ComposableMap
        projection="geoMercator"
        projectionConfig={{ scale: 750, center: [-54, -15] }}
        width={680}
        height={620}
        style={{ width: '100%', height: 'auto' }}
      >
        <Geographies geography={geo}>
          {({ geographies }) =>
            geographies.map((g) => {
              const uf  = g.properties.sigla;
              const v   = byUf.get(uf);
              const fill = Number.isFinite(v) ? scale(v) : (emptyColor || fallbackBg);
              return (
                <Geography
                  key={g.rsmKey || uf}
                  geography={g}
                  fill={fill}
                  stroke={strokeColor}
                  strokeWidth={0.6}
                  style={{
                    default: { outline: 'none', transition: 'fill 0.18s' },
                    hover:   { outline: 'none', filter: 'brightness(1.18)', cursor: 'pointer' },
                    pressed: { outline: 'none' },
                  }}
                  onMouseEnter={(e) =>
                    setHover({ uf, value: v, x: e.clientX, y: e.clientY })
                  }
                  onMouseMove={(e) =>
                    setHover((h) => h && { ...h, x: e.clientX, y: e.clientY })
                  }
                  onMouseLeave={() => setHover(null)}
                />
              );
            })
          }
        </Geographies>
      </ComposableMap>

      <ColorLegend
        scale={scale}
        min={min}
        max={max}
        unit={unit}
        format={hoverFmt}
      />

      {hover && (
        <div
          className="map-tooltip"
          style={{
            left: Math.min(hover.x + 14, window.innerWidth - 180),
            top:  Math.max(hover.y - 12, 12),
          }}
        >
          <b className="mono">{hover.uf}</b>
          <span>
            {Number.isFinite(hover.value)
              ? `${unit ? unit + ' · ' : ''}${hoverFmt(hover.value)}`
              : 'sem dado'}
          </span>
        </div>
      )}
    </div>
  );
}

function ColorLegend({ scale, min, max, unit, format }) {
  const stops = useMemo(() => {
    const n = 24;
    return Array.from({ length: n }, (_, i) => {
      const t = i / (n - 1);
      return scale(min + t * (max - min));
    });
  }, [scale, min, max]);

  return (
    <div className="map-legend">
      <div className="map-legend-bar">
        {stops.map((c, i) => (
          <span key={i} style={{ background: c }} />
        ))}
      </div>
      <div className="map-legend-axis">
        <span>{format(min)}</span>
        <span className="muted">{unit}</span>
        <span>{format(max)}</span>
      </div>
    </div>
  );
}

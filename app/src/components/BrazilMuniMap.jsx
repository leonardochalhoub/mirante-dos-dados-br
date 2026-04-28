// Choropleth map of Brazil at MUNICIPALITY level (5,570 polygons).
// Stack: react-simple-maps + d3-scale (same primitives as BrazilMap).
// Lookup: geojson `properties.codarea` (IBGE 7-digit) ↔ data `cod_municipio`.
// UF borders are overlaid (transparent fill, dark stroke) so the map reads
// nationally without hiding the muni mosaic.

import { useEffect, useMemo, useState } from 'react';
import { ComposableMap, Geographies, Geography } from 'react-simple-maps';
import { loadGeo } from '../lib/data';
import { buildColorScale } from '../lib/scales';

export default function BrazilMuniMap({
  data,                 // [{ cod_municipio, value, municipio, uf }, ...]
  colorscale = 'Cividis',
  theme = 'light',
  hoverFmt = (v) => String(v),
  unit = '',
  emptyColor,
}) {
  const [geo, setGeo]       = useState(null);
  const [stateGeo, setStateGeo] = useState(null);
  const [hover, setHover]   = useState(null);

  useEffect(() => {
    loadGeo('brazil-municipios.geojson').then(setGeo).catch((e) => {
      console.error('muni geojson load error', e);
    });
    loadGeo('brazil-states.geojson').then(setStateGeo).catch(() => { /* optional */ });
  }, []);

  // Lookup tables from data array — keyed by 7-digit muni code.
  const valByCode = useMemo(() => {
    const m = new Map();
    for (const d of data || []) m.set(String(d.cod_municipio), d.value);
    return m;
  }, [data]);

  const metaByCode = useMemo(() => {
    const m = new Map();
    for (const d of data || []) m.set(String(d.cod_municipio), { municipio: d.municipio, uf: d.uf });
    return m;
  }, [data]);

  // Choropleth com 5.570 polígonos: domain linear [min, max] colapsa visualmente
  // porque a distribuição de pbfPerCapita é heavy-tailed (max ~5× mediana). Usamos
  // [p2, p98] como domain do scale (com clamp). Mediana cai no meio da paleta e a
  // variação local é visível. min/max reais ainda aparecem na legenda. Mesma
  // ideia dos mapas matplotlib do PDF onde vmin/vmax = percentis.
  const [min, max, domainLo, domainHi] = useMemo(() => {
    const vals = (data || []).map((d) => d.value).filter((v) => Number.isFinite(v));
    if (vals.length === 0) return [0, 1, 0, 1];
    const sorted = [...vals].sort((a, b) => a - b);
    const pctile = (p) => sorted[Math.max(0, Math.min(sorted.length - 1, Math.floor(sorted.length * p)))];
    const lo = pctile(0.02);
    const hi = pctile(0.98);
    const safeLo = lo === hi ? sorted[0] : lo;
    const safeHi = lo === hi ? sorted[sorted.length - 1] : hi;
    return [sorted[0], sorted[sorted.length - 1], safeLo, safeHi];
  }, [data]);

  const scale = useMemo(() => {
    const s = buildColorScale(colorscale, [domainLo, domainHi]);
    if (typeof s.clamp === 'function') s.clamp(true);
    return s;
  }, [colorscale, domainLo, domainHi]);
  const fallbackBg  = theme === 'dark' ? '#1f2937' : '#e2e8f0';
  const muniStroke  = theme === 'dark' ? '#0d1117' : '#ffffff';
  const stateStroke = theme === 'dark' ? '#e2e8f0' : '#1f2937';

  if (!geo) return <div className="loading-block">Carregando mapa municipal…</div>;
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
              const code = String(g.properties.codarea);
              const v    = valByCode.get(code);
              const fill = Number.isFinite(v) ? scale(v) : (emptyColor || fallbackBg);
              return (
                <Geography
                  key={g.rsmKey || code}
                  geography={g}
                  fill={fill}
                  stroke={muniStroke}
                  strokeWidth={0.15}
                  style={{
                    default: { outline: 'none' },
                    hover:   { outline: 'none', filter: 'brightness(1.25)', cursor: 'pointer' },
                    pressed: { outline: 'none' },
                  }}
                  onMouseEnter={(e) => {
                    const meta = metaByCode.get(code);
                    setHover({ code, value: v, x: e.clientX, y: e.clientY,
                               municipio: meta?.municipio, uf: meta?.uf });
                  }}
                  onMouseMove={(e) =>
                    setHover((h) => h && { ...h, x: e.clientX, y: e.clientY })
                  }
                  onMouseLeave={() => setHover(null)}
                />
              );
            })
          }
        </Geographies>

        {/* UF borders overlay — gives the eye a national grid over the muni mosaic */}
        {stateGeo && (
          <Geographies geography={stateGeo}>
            {({ geographies }) =>
              geographies.map((g) => (
                <Geography
                  key={`uf-${g.rsmKey || g.properties.sigla}`}
                  geography={g}
                  fill="transparent"
                  stroke={stateStroke}
                  strokeWidth={0.7}
                  style={{
                    default: { outline: 'none', pointerEvents: 'none' },
                    hover:   { outline: 'none', pointerEvents: 'none' },
                    pressed: { outline: 'none', pointerEvents: 'none' },
                  }}
                />
              ))
            }
          </Geographies>
        )}
      </ComposableMap>

      <ColorLegend
        scale={scale}
        min={domainLo}
        max={domainHi}
        actualMin={min}
        actualMax={max}
        unit={unit}
        format={hoverFmt}
      />

      {hover && (
        <div
          className="map-tooltip"
          style={{
            left: Math.min(hover.x + 14, window.innerWidth - 220),
            top:  Math.max(hover.y - 12, 12),
          }}
        >
          <b>{hover.municipio || hover.code}</b>
          {hover.uf && <span className="mono" style={{ opacity: 0.7 }}>/{hover.uf}</span>}
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

function ColorLegend({ scale, min, max, actualMin, actualMax, unit, format }) {
  const stops = useMemo(() => {
    const n = 24;
    return Array.from({ length: n }, (_, i) => {
      const t = i / (n - 1);
      return scale(min + t * (max - min));
    });
  }, [scale, min, max]);

  // Mostrar min/max real apenas se ficaram fora do domain (p2/p98).
  const hasClipping = Number.isFinite(actualMin) && Number.isFinite(actualMax)
    && (actualMin < min - 1e-6 || actualMax > max + 1e-6);

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
      {hasClipping && (
        <div className="map-legend-axis" style={{ fontSize: 10, marginTop: 2, opacity: 0.7 }}>
          <span>min real: {format(actualMin)}</span>
          <span className="muted">escala: percentis 2–98</span>
          <span>max real: {format(actualMax)}</span>
        </div>
      )}
    </div>
  );
}

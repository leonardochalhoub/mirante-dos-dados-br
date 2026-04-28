// Choropleth map of Brazil at MUNICIPALITY level (5,570 polygons).
// Stack: d3-geo + d3-scale (NO react-simple-maps — direct SVG render).
// Lookup: geojson `properties.codarea` (IBGE 7-digit) ↔ data `cod_municipio`.
// UF borders are overlaid (transparent fill, dark stroke) so the map reads
// nationally without hiding the muni mosaic.
//
// HISTÓRICO: react-simple-maps@3 envolve <Geography> em React.memo e o
// style.default sobrepõe a prop fill em algumas combinações de versão —
// resultado: 5569 munis renderizavam com fill ausente/idêntico, só Brasília
// ficava colorida. Render direto resolve sem depender de internals da lib.

import { useEffect, useMemo, useState } from 'react';
import { geoMercator, geoPath } from 'd3-geo';
import { loadGeo } from '../lib/data';
import { buildColorScale } from '../lib/scales';

const WIDTH = 680;
const HEIGHT = 620;

export default function BrazilMuniMap({
  data,                 // [{ cod_municipio, value, municipio, uf }, ...]
  colorscale = 'Cividis',
  theme = 'light',
  hoverFmt = (v) => String(v),
  unit = '',
  emptyColor,
}) {
  const [geo, setGeo]           = useState(null);
  const [stateGeo, setStateGeo] = useState(null);
  const [hover, setHover]       = useState(null);

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
  // porque a distribuição é heavy-tailed (max ~5× mediana). Usamos [p2, p98]
  // como domain do scale (com clamp). Mediana cai no meio da paleta e variação
  // local fica visível. min/max reais aparecem na legenda. Padrão dos mapas
  // matplotlib do PDF (vmin/vmax = percentis).
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

  // d3 projection — mesma do antigo react-simple-maps (geoMercator scale 750
  // center [-54, -15] em viewport 680×620, com offset pra centrar Brasil)
  const projection = useMemo(() => {
    return geoMercator()
      .scale(750)
      .center([-54, -15])
      .translate([WIDTH / 2, HEIGHT / 2]);
  }, []);

  const path = useMemo(() => geoPath(projection), [projection]);

  // Pré-computa svgPath e fill por feature pra evitar trabalho em cada render
  const muniPaths = useMemo(() => {
    if (!geo) return [];
    return geo.features.map((f) => {
      const code = String(f.properties.codarea);
      const v = valByCode.get(code);
      const fill = Number.isFinite(v) ? scale(v) : (emptyColor || fallbackBg(theme));
      return { code, d: path(f.geometry), fill, value: v };
    });
  }, [geo, valByCode, scale, emptyColor, theme]);

  const ufPaths = useMemo(() => {
    if (!stateGeo) return [];
    return stateGeo.features.map((f) => ({
      key: f.properties.sigla || f.properties.UF || f.id,
      d: path(f.geometry),
    }));
  }, [stateGeo, path]);

  const muniStroke  = theme === 'dark' ? '#0d1117' : '#ffffff';
  const stateStroke = theme === 'dark' ? '#e2e8f0' : '#1f2937';

  if (!geo) return <div className="loading-block">Carregando mapa municipal…</div>;
  if (!data || data.length === 0) return <div className="loading-block">Sem dados</div>;

  return (
    <div className="brazil-map-wrap">
      <svg
        viewBox={`0 0 ${WIDTH} ${HEIGHT}`}
        width="100%"
        height="auto"
        style={{ display: 'block' }}
      >
        {/* Camada 1 — 5.570 munis, fill por valor */}
        <g>
          {muniPaths.map((p) => (
            <path
              key={p.code}
              d={p.d}
              fill={p.fill}
              stroke={muniStroke}
              strokeWidth={0.15}
              onMouseEnter={(e) => {
                const meta = metaByCode.get(p.code);
                setHover({
                  code: p.code, value: p.value,
                  x: e.clientX, y: e.clientY,
                  municipio: meta?.municipio, uf: meta?.uf,
                });
              }}
              onMouseMove={(e) =>
                setHover((h) => h && { ...h, x: e.clientX, y: e.clientY })
              }
              onMouseLeave={() => setHover(null)}
              style={{ cursor: 'pointer', outline: 'none' }}
            />
          ))}
        </g>

        {/* Camada 2 — bordas de UF (overlay grosso, visível) */}
        <g style={{ pointerEvents: 'none' }}>
          {ufPaths.map((p) => (
            <path
              key={`uf-${p.key}`}
              d={p.d}
              fill="none"
              stroke={stateStroke}
              strokeWidth={0.7}
            />
          ))}
        </g>
      </svg>

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

function fallbackBg(theme) {
  return theme === 'dark' ? '#1f2937' : '#e2e8f0';
}

function ColorLegend({ scale, min, max, actualMin, actualMax, unit, format }) {
  const stops = useMemo(() => {
    const n = 24;
    return Array.from({ length: n }, (_, i) => {
      const t = i / (n - 1);
      return scale(min + t * (max - min));
    });
  }, [scale, min, max]);

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

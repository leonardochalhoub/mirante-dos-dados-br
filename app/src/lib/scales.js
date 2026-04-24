// Color-scale helpers shared by chart + map.
// Uses d3-scale-chromatic interpolators so the choice of palette is explicit and
// theme-friendly (palettes are continuous, no Plotly-style discrete steps needed).

import {
  interpolateBlues,
  interpolateGreens,
  interpolateGreys,
  interpolateMagma,
  interpolateViridis,
  interpolateCividis,
  interpolateYlGnBu,
  interpolateYlOrRd,
} from 'd3-scale-chromatic';
import { scaleSequential } from 'd3-scale';

const PALETTES = {
  Cividis: interpolateCividis,
  Viridis: interpolateViridis,
  Blues:   interpolateBlues,
  Greens:  interpolateGreens,
  Greys:   interpolateGreys,
  YlGnBu:  interpolateYlGnBu,
  YlOrRd:  interpolateYlOrRd,
  Magma:   interpolateMagma,
};

export const COLORSCALES = [
  { value: 'Cividis', label: 'Cividis (daltônico)' },
  { value: 'Viridis', label: 'Viridis (daltônico)' },
  { value: 'Blues',   label: 'Azuis' },
  { value: 'Greens',  label: 'Verdes' },
  { value: 'Greys',   label: 'Cinzas' },
  { value: 'YlGnBu',  label: 'YlGnBu' },
  { value: 'YlOrRd',  label: 'Calor (YlOrRd)' },
  { value: 'Magma',   label: 'Magma' },
];

// d3-scale-chromatic palettes that naturally go DARK(t=0) → LIGHT(t=1).
// We invert t for those so the rendered map always reads LIGHT=low, DARK=high.
const NATURALLY_DARK_TO_LIGHT = new Set(['Cividis', 'Viridis', 'Magma']);

/**
 * Build a d3 sequential color scale that maps LOW=light → HIGH=dark.
 * For palettes that ship dark→light by default (Cividis, Viridis, Magma),
 * we flip t so the visual orientation is consistent across all palettes.
 */
export function buildColorScale(paletteName, [min, max]) {
  const interp = PALETTES[paletteName] || PALETTES.Cividis;
  const wrapped = NATURALLY_DARK_TO_LIGHT.has(paletteName) ? (t) => interp(1 - t) : interp;
  return scaleSequential(wrapped).domain([min, max]);
}

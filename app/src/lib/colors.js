// Single source of truth for series/sector colors. Theme-aware: each pair has
// a light and a dark variant so SVG fills stay legible across modes.

export const SERIES = {
  primary: { light: '#2b6cb0', dark: '#60a5fa' },   // SUS / blue / "main"
  pink:    { light: '#be185d', dark: '#f472b6' },   // Privado
  amber:   { light: '#b45309', dark: '#fbbf24' },   // overlay line / accent
  teal:    { light: '#0d9488', dark: '#5eead4' },   // tertiary
  emerald: { light: '#059669', dark: '#34d399' },   // tertiary
  slate:   { light: '#475569', dark: '#cbd5e1' },   // neutral
};

export function pick(name, theme) {
  const c = SERIES[name] || SERIES.primary;
  return theme === 'dark' ? c.dark : c.light;
}

// Number / currency / date formatters in pt-BR.

const nfInt    = new Intl.NumberFormat('pt-BR', { maximumFractionDigits: 0 });
const nfDec1   = new Intl.NumberFormat('pt-BR', { minimumFractionDigits: 1, maximumFractionDigits: 1 });
const nfDec2   = new Intl.NumberFormat('pt-BR', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
const nfPct1   = new Intl.NumberFormat('pt-BR', { style: 'percent', minimumFractionDigits: 1, maximumFractionDigits: 1 });

export const fmtInt  = (v) => (v == null || Number.isNaN(v) ? '—' : nfInt.format(v));
export const fmtDec1 = (v) => (v == null || Number.isNaN(v) ? '—' : nfDec1.format(v));
export const fmtDec2 = (v) => (v == null || Number.isNaN(v) ? '—' : nfDec2.format(v));
export const fmtPct  = (v) => (v == null || Number.isNaN(v) ? '—' : nfPct1.format(v));

export const fmtBRL = (v, opts = {}) => {
  if (v == null || Number.isNaN(v)) return '—';
  const { compact = false } = opts;
  return new Intl.NumberFormat('pt-BR', {
    style: 'currency',
    currency: 'BRL',
    notation: compact ? 'compact' : 'standard',
    maximumFractionDigits: compact ? 1 : 2,
  }).format(v);
};

export const fmtCompact = (v) => {
  if (v == null || Number.isNaN(v)) return '—';
  return new Intl.NumberFormat('pt-BR', { notation: 'compact', maximumFractionDigits: 1 }).format(v);
};

// Stable ordering for UFs by region (used in ranking lists & legends)
export const UF_REGION = {
  AC: 'N', AM: 'N', AP: 'N', PA: 'N', RO: 'N', RR: 'N', TO: 'N',
  AL: 'NE', BA: 'NE', CE: 'NE', MA: 'NE', PB: 'NE', PE: 'NE', PI: 'NE', RN: 'NE', SE: 'NE',
  DF: 'CO', GO: 'CO', MT: 'CO', MS: 'CO',
  ES: 'SE', MG: 'SE', RJ: 'SE', SP: 'SE',
  PR: 'S', RS: 'S', SC: 'S',
};

export const REGION_NAME = {
  N: 'Norte', NE: 'Nordeste', CO: 'Centro-Oeste', SE: 'Sudeste', S: 'Sul',
};

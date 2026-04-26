// Tiny fetch helper for gold JSON files served from /data/.
// Honors Vite's BASE_URL so it works on GitHub Pages under /repo-name/.

const base = import.meta.env.BASE_URL || '/';

// Filtro defensivo universal: drop o ano corrente (parcial) de qualquer gold.
// Justificativa: várias fontes (CGU/PBF, CGU/Emendas, MTE/RAIS, DATASUS/SIH,
// CNES) atualizam mensalmente — comparar Brasil-2025 com Brasil-2026-parcial
// é apples-to-oranges. Mantemos só anos completos (Jan–Dez). Aplicado AQUI,
// no loader compartilhado, então TODAS as verticais herdam o cap sem precisar
// duplicar a lógica em cada rota. Os pipelines silver/gold do Databricks já
// tentam aplicar o mesmo filtro, mas a defesa em profundidade aqui protege
// contra silver stale, JSON commitado antes do refresh, etc.
function dropCurrentYear(rows) {
  if (!Array.isArray(rows) || rows.length === 0) return rows;
  const currentYear = new Date().getFullYear();
  // Detecta a chave de ano: 'Ano' (PBF/Emendas) ou 'ano' (UroPro/Equipamentos).
  // Se nenhuma das duas existir (RAIS pré-pipeline-rodar), passa direto.
  const sample = rows[0];
  const yearKey = 'Ano' in sample ? 'Ano' : 'ano' in sample ? 'ano' : null;
  if (!yearKey) return rows;
  return rows.filter((r) => r[yearKey] != null && Number(r[yearKey]) < currentYear);
}

export async function loadGold(filename) {
  const url = `${base}data/${filename}`.replace(/\/{2,}/g, '/');
  // 'no-cache' validates with server via ETag (cheap) instead of trusting stale
  // cached data forever. Critical because gold JSONs are refreshed monthly.
  const res = await fetch(url, { cache: 'no-cache' });
  if (!res.ok) {
    throw new Error(`Falha ao carregar ${filename} (HTTP ${res.status})`);
  }
  const rows = await res.json();
  return dropCurrentYear(rows);
}

export async function loadGeo(filename) {
  const url = `${base}geo/${filename}`.replace(/\/{2,}/g, '/');
  // Geo files are static — safe to cache.
  const res = await fetch(url, { cache: 'force-cache' });
  if (!res.ok) {
    throw new Error(`Falha ao carregar ${filename} (HTTP ${res.status})`);
  }
  return res.json();
}

export async function loadStats(filename = 'platform_stats.json') {
  const url = `${base}stats/${filename}`.replace(/\/{2,}/g, '/');
  const res = await fetch(url, { cache: 'no-cache' });   // stats refreshed monthly, want fresh
  if (!res.ok) return null;                              // optional — Home renders without if missing
  return res.json();
}

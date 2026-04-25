// Tiny fetch helper for gold JSON files served from /data/.
// Honors Vite's BASE_URL so it works on GitHub Pages under /repo-name/.

const base = import.meta.env.BASE_URL || '/';

export async function loadGold(filename) {
  const url = `${base}data/${filename}`.replace(/\/{2,}/g, '/');
  // 'no-cache' validates with server via ETag (cheap) instead of trusting stale
  // cached data forever. Critical because gold JSONs are refreshed monthly.
  const res = await fetch(url, { cache: 'no-cache' });
  if (!res.ok) {
    throw new Error(`Falha ao carregar ${filename} (HTTP ${res.status})`);
  }
  return res.json();
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

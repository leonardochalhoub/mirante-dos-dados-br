// Tiny fetch helper for gold JSON files served from /data/.
// Honors Vite's BASE_URL so it works on GitHub Pages under /repo-name/.

const base = import.meta.env.BASE_URL || '/';

export async function loadGold(filename) {
  const url = `${base}data/${filename}`.replace(/\/{2,}/g, '/');
  const res = await fetch(url, { cache: 'force-cache' });
  if (!res.ok) {
    throw new Error(`Falha ao carregar ${filename} (HTTP ${res.status})`);
  }
  return res.json();
}

export async function loadGeo(filename) {
  const url = `${base}geo/${filename}`.replace(/\/{2,}/g, '/');
  const res = await fetch(url, { cache: 'force-cache' });
  if (!res.ok) {
    throw new Error(`Falha ao carregar ${filename} (HTTP ${res.status})`);
  }
  return res.json();
}

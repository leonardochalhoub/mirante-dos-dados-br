// Copies /data/gold/*.json into /app/public/data so Vite can serve them.
// Source of truth lives at /data/gold (this is what Databricks will write to).
import { mkdir, copyFile, readdir } from 'node:fs/promises';
import { existsSync } from 'node:fs';
import { dirname, join, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

const __dirname = dirname(fileURLToPath(import.meta.url));
const ROOT = resolve(__dirname, '..');

const PAIRS = [
  { src: join(ROOT, 'data', 'gold'),  dst: join(ROOT, 'app', 'public', 'data')  },
  { src: join(ROOT, 'data', 'stats'), dst: join(ROOT, 'app', 'public', 'stats') },
];

async function syncFolder(src, dst) {
  if (!existsSync(src)) {
    console.warn(`[sync-data] source missing: ${src} — skipping.`);
    return;
  }
  await mkdir(dst, { recursive: true });
  const files = (await readdir(src)).filter((f) => f.endsWith('.json'));
  if (files.length === 0) {
    console.warn(`[sync-data] no .json files found under ${src}`);
    return;
  }
  for (const f of files) {
    await copyFile(join(src, f), join(dst, f));
    console.log(`[sync-data] ${f} -> ${dst}/`);
  }
}

async function main() {
  for (const { src, dst } of PAIRS) await syncFolder(src, dst);
}

main().catch((err) => {
  console.error('[sync-data] failed:', err);
  process.exit(1);
});

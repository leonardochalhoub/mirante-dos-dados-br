// Copies /data/gold/*.json into /app/public/data so Vite can serve them.
// Source of truth lives at /data/gold (this is what Databricks will write to).
import { mkdir, copyFile, readdir } from 'node:fs/promises';
import { existsSync } from 'node:fs';
import { dirname, join, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

const __dirname = dirname(fileURLToPath(import.meta.url));
const ROOT = resolve(__dirname, '..');
const SRC  = join(ROOT, 'data', 'gold');
const DST  = join(ROOT, 'app', 'public', 'data');

async function main() {
  if (!existsSync(SRC)) {
    console.warn(`[sync-data] source missing: ${SRC} — skipping.`);
    return;
  }
  await mkdir(DST, { recursive: true });
  const files = (await readdir(SRC)).filter((f) => f.endsWith('.json'));
  if (files.length === 0) {
    console.warn(`[sync-data] no .json files found under ${SRC}`);
    return;
  }
  for (const f of files) {
    await copyFile(join(SRC, f), join(DST, f));
    console.log(`[sync-data] ${f} -> app/public/data/`);
  }
}

main().catch((err) => {
  console.error('[sync-data] failed:', err);
  process.exit(1);
});

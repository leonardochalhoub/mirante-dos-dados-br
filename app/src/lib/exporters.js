// Lazy-loaded export helpers (xlsx + html-to-image + JSZip).
// Heavy libs are only fetched on the first click — keeps initial bundle lean.

function fileSafe(s) {
  return String(s).normalize('NFD').replace(/[̀-ͯ]/g, '')
    .replace(/[^a-zA-Z0-9_-]+/g, '-').replace(/^-+|-+$/g, '').toLowerCase();
}

function todayStamp() {
  const d = new Date();
  return d.toISOString().slice(0, 10);
}

function downloadBlob(blob, filename) {
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url; a.download = filename;
  document.body.appendChild(a); a.click(); a.remove();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}

// Wrap a dynamic-import promise with a friendlier error if it fails.
// IMPORTANT: import() must be called with a STRING LITERAL at the call site
// (not via a helper) so Rollup can statically discover & code-split the chunk.
function withImportErr(p, name) {
  return p.catch((e) => {
    console.error(`Dynamic import failed for ${name}:`, e);
    throw new Error(
      `Falha ao carregar "${name}". ` +
      `Restart o dev server (rm -rf node_modules/.vite && npm run dev) e tente de novo.`
    );
  });
}

/**
 * Export one or more datasets to a single .xlsx workbook.
 * @param {string} basename  e.g. "mirante-pbf"
 * @param {{[sheet: string]: object[]}} sheets  rows grouped by sheet name
 */
export async function exportToXlsx(basename, sheets) {
  const XLSX = await withImportErr(import('xlsx'), 'xlsx');
  const wb = XLSX.utils.book_new();
  for (const [name, rows] of Object.entries(sheets)) {
    const ws = XLSX.utils.json_to_sheet(rows);
    XLSX.utils.book_append_sheet(wb, ws, name.slice(0, 31));   // Excel sheet name 31-char limit
  }
  const out = XLSX.write(wb, { type: 'array', bookType: 'xlsx' });
  downloadBlob(
    new Blob([out], { type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' }),
    `${fileSafe(basename)}-${todayStamp()}.xlsx`,
  );
}

/**
 * Snapshot every element matching the selector to PNG and bundle into a ZIP.
 * Each element should have a `data-export-id` and ideally `data-export-label`.
 * @param {string} basename  e.g. "mirante-pbf"
 * @param {string} selector  default `[data-export-id]`
 */
export async function exportChartsAsZip(basename, selector = '[data-export-id]') {
  const [{ toPng }, JSZipMod] = await Promise.all([
    withImportErr(import('html-to-image'), 'html-to-image'),
    withImportErr(import('jszip'),         'jszip'),
  ]);
  const JSZip = JSZipMod.default || JSZipMod;
  const zip   = new JSZip();
  const nodes = Array.from(document.querySelectorAll(selector));
  if (nodes.length === 0) {
    throw new Error('Nenhum gráfico encontrado para exportar.');
  }

  // Snapshot in parallel — html-to-image is async per node.
  // Resolve background color from the node, walking up if it's transparent.
  const resolveBg = (node) => {
    let el = node;
    while (el) {
      const bg = getComputedStyle(el).backgroundColor;
      if (bg && bg !== 'rgba(0, 0, 0, 0)' && bg !== 'transparent') return bg;
      el = el.parentElement;
    }
    return '#ffffff';
  };

  const png = await Promise.all(
    nodes.map(async (node, i) => {
      const id      = node.getAttribute('data-export-id') || `chart-${i + 1}`;
      const dataUrl = await toPng(node, {
        cacheBust: true,
        pixelRatio: 2,
        backgroundColor: resolveBg(node),
      });
      const base64 = dataUrl.split(',')[1];
      return { id, base64 };
    }),
  );
  for (const { id, base64 } of png) {
    zip.file(`${fileSafe(id)}.png`, base64, { base64: true });
  }
  const blob = await zip.generateAsync({ type: 'blob' });
  downloadBlob(blob, `${fileSafe(basename)}-${todayStamp()}.zip`);
}

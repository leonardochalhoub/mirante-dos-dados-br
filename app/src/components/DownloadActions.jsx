import { useState } from 'react';

export default function DownloadActions({
  onExportXlsx,             // async () => void  — caller orchestrates the data
  onExportPng,              // async () => void
  xlsxLabel = '↓ Baixar Excel',
  pngLabel  = '↓ Baixar PNG (ZIP)',
}) {
  const [busy, setBusy] = useState(null);    // null | 'xlsx' | 'png'

  async function run(kind, fn) {
    if (busy) return;
    setBusy(kind);
    try { await fn(); }
    catch (e) {
      console.error(e);
      alert(`Erro ao gerar ${kind === 'xlsx' ? 'Excel' : 'ZIP'}: ${e.message}`);
    }
    finally { setBusy(null); }
  }

  return (
    <div className="download-actions">
      <button
        type="button"
        className="primary"
        disabled={busy != null}
        onClick={() => run('xlsx', onExportXlsx)}
      >
        {busy === 'xlsx' ? 'Gerando…' : xlsxLabel}
      </button>
      <button
        type="button"
        className="primary"
        disabled={busy != null}
        onClick={() => run('png', onExportPng)}
      >
        {busy === 'png' ? 'Capturando…' : pngLabel}
      </button>
    </div>
  );
}

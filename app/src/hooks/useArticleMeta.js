// Carrega articles/_meta.json (gerado em prebuild) e devolve metadata por slug.
// Inclui helper articleUrl() que anexa ?v=<sha> nos links pra invalidar cache
// do browser sempre que o .tex for tocado em um novo commit.
//
// O fetch é deduplicado via promise compartilhada — múltiplos componentes
// usando o hook em paralelo só fazem 1 GET de _meta.json.

import { useEffect, useState } from 'react';
import { loadArticlesMeta } from '../lib/data';

let sharedPromise = null;
function getMetaShared() {
  if (!sharedPromise) sharedPromise = loadArticlesMeta();
  return sharedPromise;
}

export function useArticleMeta(slug) {
  const [meta, setMeta] = useState(null);

  useEffect(() => {
    let cancelled = false;
    getMetaShared().then((m) => {
      if (cancelled) return;
      setMeta(m?.articles?.[slug] || null);
    }).catch(() => {});
    return () => { cancelled = true; };
  }, [slug]);

  return meta;   // { tex_last_edited, tex_last_sha } | null
}

// Helper puro — gera URL com cache-buster ?v=<sha> se o sha estiver disponível.
// Usado tanto em links PDF/tex quanto no Overleaf URL embedado.
//
//   articleUrl(base, slug, 'pdf', sha)
//     → '/mirante-dos-dados-br/articles/equipamentos-rm-parkinson.pdf?v=e24c78f'
//
// Se sha for null/undefined, devolve a URL bare (compatibilidade com 1ª render
// antes do _meta.json carregar).
export function articleUrl(base, slug, ext, sha) {
  const url = `${base}articles/${slug}.${ext}`.replace(/\/{2,}/g, '/');
  return sha ? `${url}?v=${sha}` : url;
}

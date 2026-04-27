// Mostra "Última geração: <data> · <SHA>" lendo de app/public/articles/_meta.json
// (gerado pelo prebuild em scripts/articles-meta.mjs). O timestamp vem do git log
// do .tex correspondente — proxy fiel de "quando esta versão do artigo nasceu".
//
// Uso: <ArticleTimestamp slug="equipamentos-rm-parkinson" />

import { useEffect, useState } from 'react';
import { loadArticlesMeta } from '../lib/data';

const FMT = new Intl.DateTimeFormat('pt-BR', {
  day: '2-digit', month: '2-digit', year: 'numeric',
  hour: '2-digit', minute: '2-digit',
  timeZone: 'America/Sao_Paulo',
});

export default function ArticleTimestamp({ slug }) {
  const [meta, setMeta] = useState(null);

  useEffect(() => {
    loadArticlesMeta().then(setMeta).catch(() => setMeta(null));
  }, []);

  if (!meta || !meta.articles?.[slug]?.tex_last_edited) return null;

  const { tex_last_edited, tex_last_sha } = meta.articles[slug];
  const dt   = new Date(tex_last_edited);
  const fmt  = FMT.format(dt) + ' BRT';

  return (
    <span style={{
      fontSize: 11, color: 'var(--muted)',
      display: 'inline-flex', alignItems: 'center', gap: 6,
    }}>
      <span title={`commit ${tex_last_sha} em ${tex_last_edited}`}>
        <b>Última geração:</b> {fmt}
      </span>
      {tex_last_sha && (
        <code style={{ fontSize: 10, opacity: 0.7 }}>· {tex_last_sha}</code>
      )}
    </span>
  );
}

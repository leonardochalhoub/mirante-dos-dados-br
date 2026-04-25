// Standalone article view for UroPro.
// Renderizada FORA do <Layout> — sem sidebar, sem header de navegação.
// Equivalente conceitual ao "PDF aberto em nova aba" das outras verticais
// (BolsaFamilia, Emendas), porém com HTML gerado dinamicamente a partir
// da Gold table.
//
// Acesso: /incontinencia-urinaria/artigo (sempre target=_blank do botão
// "Ler artigo na tela" em UroPro.jsx).

import { useEffect, useState } from 'react';
import UroProArticle from '../components/UroProArticle';
import { loadGold }   from '../lib/data';

export default function UroProArticleStandalone() {
  const [rows, setRows]   = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    loadGold('gold_uropro_estados_ano.json')
      .then(setRows)
      .catch((e) => setError(e.message));
    // Fixa título da aba pra ficar amigável quando o usuário tem várias abas.
    document.title = 'Mirante · Incontinência Urinária no SUS — Working Paper n. 3';
  }, []);

  if (error) {
    return (
      <div className="standalone-article-page">
        <div className="error-block">Erro ao carregar dados: {error}</div>
      </div>
    );
  }

  return (
    <div className="standalone-article-page">
      <header className="standalone-article-toolbar no-print">
        <div className="standalone-article-toolbar-left">
          <a href={`${import.meta.env.BASE_URL || '/'}#/incontinencia-urinaria`}
             className="doc-toggle">
            ← Voltar à vertical
          </a>
        </div>
        <div className="standalone-article-toolbar-right">
          <button
            type="button"
            className="doc-toggle doc-toggle-primary"
            onClick={() => window.print()}
            title="Imprimir / Salvar como PDF (Ctrl+P / Cmd+P)"
          >
            ⤓ Baixar PDF (ABNT)
          </button>
        </div>
      </header>

      <main className="standalone-article-body">
        {!rows
          ? <div className="loading-block">Carregando artigo…</div>
          : <UroProArticle rows={rows} />}
      </main>
    </div>
  );
}

// Vertical: Cálculo no Ensino Médio (educação comparada).
// Source: artigo standalone (revisão sistemática + comparada) — não tem
// pipeline bronze/silver/gold sobre microdados públicos. Convive com o
// padrão Mirante via DocSection idêntica às outras verticais (WP#1/2/4/6/7).
//
// Working Paper: articles/calculo-ensino-medio-internacional.tex
// Slug         : calculo-ensino-medio-internacional
// WP num       : 9 — "O Cálculo Ausente: 200 anos de currículo, 10 países,
//                vácuo estrutural"

import PageHeader        from '../components/PageHeader';
import TechBadges        from '../components/TechBadges';
import ScoreCard         from '../components/ScoreCard';
import ArticleTimestamp  from '../components/ArticleTimestamp';
import AtaConselho       from '../components/AtaConselho';
import { useArticleMeta, articleUrl } from '../hooks/useArticleMeta';
import { PARECER_WP9_CALCULO }        from '../data/pareceres';
import { ATA_WP9_REUNIAO_5 }          from '../data/atas-conselho';

export default function Calculo() {
  const base = import.meta.env.BASE_URL || '/';
  const slug = 'calculo-ensino-medio-internacional';
  const meta = useArticleMeta(slug);
  const sha  = meta?.tex_last_sha;
  const pdfUrl = articleUrl(base, slug, 'pdf', sha);
  const texUrl = articleUrl(base, slug, 'tex', sha);
  const overleafUrl = 'https://www.overleaf.com/docs?snip_uri=' +
    encodeURIComponent(`https://leonardochalhoub.github.io${texUrl}`);

  return (
    <>
      <PageHeader
        eyebrow="Vertical · educação comparada · currículo de matemática"
        title="Cálculo no Ensino Médio"
        subtitle={
          'Revisão sistemática do currículo oficial de matemática em 10 países + IB. ' +
          'Brasil é o único país da amostra cujo BNCC não inclui limites, derivadas ou ' +
          'integrais antes da graduação. Fontes: documentos curriculares oficiais · OECD/PISA · ' +
          'IBGE · INEP · CONFEA · Geraldo Ávila (RPM) · Wanderley Rezende (UFF/IME-USP).'
        }
        right={
          <div className="header-right-row">
            <TechBadges />
          </div>
        }
      />

      <DocSection
        slug={slug}
        pdfUrl={pdfUrl}
        texUrl={texUrl}
        overleafUrl={overleafUrl}
      />

      {/* Ata da Reunião #5 do Conselho do Mirante (WP#9, 2026-04-29):
          4 cadeiras em paralelo · média quants 2,0 EXATO · APROVADO NO LIMIAR.
          Renderizada logo abaixo do DocSection no padrão de WP#2 (BolsaFamilia)
          e WP#4/WP#6 (Equipamentos). */}
      <AtaConselho ata={ATA_WP9_REUNIAO_5} />

      <ContextSection />

      <Footer />
    </>
  );
}

// ─── Documentação do Working Paper ──────────────────────────────────────
// Mesmo padrão de WP#1 (Emendas), WP#3 (RAIS): kicker + título + abstract
// curto + ScoreCard + 4 botões canônicos (PDF, baixar PDF ABNT, baixar
// .tex, abrir no Overleaf).
function DocSection({ slug, pdfUrl, texUrl, overleafUrl }) {
  return (
    <section className="emendas-abstract no-print" style={{ marginBottom: 14 }}>
      <div className="doc-block">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline', flexWrap: 'wrap', gap: 8 }}>
          <div className="kicker">Working Paper n. 9 — Mirante dos Dados</div>
          <ArticleTimestamp slug={slug} />
        </div>

        <p style={{ marginTop: 8 }}>
          <b>"O Cálculo Ausente: duzentos anos de currículo, dez países de
          comparação, um vácuo estrutural"</b> — análise comparativa do
          currículo de matemática do ensino médio em dez países (Japão,
          China, Coreia do Sul, Singapura, Alemanha, França, Rússia,
          Finlândia, Estados Unidos, Brasil) e do programa{' '}
          <i>International Baccalaureate</i>, em padrão ABNT, com 47+
          referências verificáveis e cobertura de duzentos anos das reformas
          curriculares brasileiras (Colégio Pedro II 1837 → Reforma Benjamin
          Constant 1890 → Capanema 1942 → Movimento Mat. Moderna 1960 →
          PCN/BNCC 1997–2018).
        </p>

        <p style={{ marginTop: 6, fontSize: 13.5 }}>
          <b>Achado central:</b> o Brasil é o <i>único</i> país da amostra
          cujo currículo nacional (BNCC) não inclui limites, derivadas ou
          integrais antes da graduação. Triangulado com a estagnação
          brasileira em PISA 2003–2022 (~380 pontos · 47–55 abaixo da
          média OECD · 1% top performers vs. 41% Singapura), taxas de
          reprovação em Cálculo I nas engenharias federais brasileiras
          (UFRJ ~70% · Unicamp 77,5% combinada · ABENGE meta-análise ~48%)
          e projeção CONFEA de déficit de até 1 milhão de engenheiros até
          2030.
        </p>

        <ScoreCard parecer={PARECER_WP9_CALCULO} />

        <p style={{ fontSize: 12, color: 'var(--muted)', marginTop: 10 }}>
          <b>Palavras-chave:</b> cálculo diferencial e integral; ensino médio;
          currículo de matemática; BNCC; educação comparada; formação em
          engenharia; PISA; reprovação universitária; reforma educacional;
          Movimento da Matemática Moderna; Reforma Benjamin Constant; Reforma
          Capanema; Bruner; Vygotsky; recursos educacionais abertos.
        </p>

        <div className="doc-actions">
          {/* Convenção de plataforma (feedback_article_buttons.md): rótulo
              primário é "Ler artigo na tela". Aplicado pós-Reunião #5 do
              Conselho (cadeira de Design flagged o gap em 2026-04-29). */}
          <a
            className="doc-toggle doc-toggle-primary"
            href={pdfUrl}
            target="_blank"
            rel="noreferrer"
            title="Abrir PDF em nova aba (visualizador nativo do navegador)"
          >
            📖 Ler artigo na tela
          </a>

          <a
            className="doc-toggle"
            href={pdfUrl}
            download="Mirante-Calculo-Chalhoub-2026.pdf"
            title="Baixar PDF compilado em LaTeX (formatado em padrão ABNT)"
          >
            ⤓ Baixar PDF (ABNT)
          </a>

          <a
            className="doc-toggle"
            href={texUrl}
            download="calculo-ensino-medio-internacional.tex"
            title="Baixar fonte LaTeX (.tex) — recompilável em qualquer ambiente TeX"
          >
            ⤓ Baixar fonte (.tex)
          </a>

          <a
            className="doc-toggle"
            href={overleafUrl}
            target="_blank"
            rel="noreferrer"
            title="Abrir no Overleaf (compilação online em 1 clique)"
          >
            ↗ Abrir no Overleaf
          </a>
        </div>
      </div>
    </section>
  );
}

// ─── Contexto: por que essa vertical não tem dashboard? ─────────────────
function ContextSection() {
  return (
    <section className="panel" style={{ marginTop: 14 }}>
      <div className="panelHead">
        <span className="panelLabel">
          Por que esta vertical não tem dashboard UF × Ano?
        </span>
        <span className="kicker">Working Paper standalone</span>
      </div>
      <div style={{ fontSize: 13, lineHeight: 1.7, color: 'var(--text)' }}>
        <p>
          As demais verticais do Mirante são dashboards interativos
          alimentados por pipelines em arquitetura medallion (bronze →
          silver → gold) sobre microdados públicos brasileiros (PBF, CNES,
          Emendas, SIH, RAIS, FinOps). O <b>WP#9</b> é diferente: é uma{' '}
          <b>revisão sistemática + comparada</b> sobre currículos oficiais
          de matemática em 10 países, cruzada com séries históricas
          OECD/PISA 2003–2022, taxas de reprovação universitária no Brasil
          e duzentos anos de reformas curriculares brasileiras.
        </p>
        <p>
          A unidade de análise é o <i>currículo</i>, não o microdado por UF
          e ano. Por isso o paper é <b>standalone do pipeline Databricks</b>
          {' '}— pode ser submetido a periódico de Educação Matemática
          (Bolema, ZDM Mathematics Education, Educação e Pesquisa) sem
          depender de qualquer outra vertical do Mirante.
        </p>
        <p style={{ marginTop: 8 }}>
          <b>Próximos passos sinalizados pelo Conselho</b> (vide ScoreCard
          acima): figura-síntese com identidade visual Mirante (mapa global
          país × cálculo no ensino médio), text mining sistemático do BNCC,
          análise quasi-experimental sobre a Reforma Benjamin Constant
          (1890–1925) usando exames da Politécnica/EPUSP/IME do período, e
          submissão a peer review formal externo.
        </p>
      </div>
    </section>
  );
}

// ─── Footer com fontes (mesmo padrão das outras verticais) ─────────────
function Footer() {
  return (
    <footer className="footer panel" style={{ marginTop: 18 }}>
      <div className="footerSection">
        <div className="footerHeading">Fontes primárias</div>
        <div className="footerSource">
          <a href="http://basenacionalcomum.mec.gov.br/abase/" target="_blank" rel="noreferrer">
            BNCC — Base Nacional Comum Curricular (MEC, 2018)
          </a>
          <span className="footerDesc">Currículo oficial brasileiro do ensino médio (homologado em dez/2018).</span>
        </div>
        <div className="footerSource">
          <a href="https://www.oecd.org/pisa/" target="_blank" rel="noreferrer">
            OECD · PISA — Programme for International Student Assessment
          </a>
          <span className="footerDesc">Séries 2003 · 2006 · 2009 · 2012 · 2015 · 2018 · 2022 — Matemática.</span>
        </div>
        <div className="footerSource">
          <a href="https://www.confea.org.br/" target="_blank" rel="noreferrer">
            CONFEA — Conselho Federal de Engenharia e Agronomia
          </a>
          <span className="footerDesc">Projeção de déficit de engenheiros até 2030.</span>
        </div>
        <div className="footerSource">
          <a href="https://teses.usp.br/teses/disponiveis/45/45133/tde-30062004-094938/" target="_blank" rel="noreferrer">
            Rezende, W. M. (2003) — "O Ensino de Cálculo: Dificuldades de Natureza Epistemológica" (tese, IME-USP)
          </a>
          <span className="footerDesc">Diagnóstico clássico sobre dificuldades epistemológicas em Cálculo I.</span>
        </div>
        <div className="footerSource">
          <a href="https://rpm.org.br/cdrpm/18/" target="_blank" rel="noreferrer">
            Ávila, G. S. S. (1991) — "O Ensino de Cálculo no 2° Grau" (RPM 18, SBM)
          </a>
          <span className="footerDesc">"Por que não ensinamos cálculo na escola de segundo grau?" — questão pendente desde 1991.</span>
        </div>
      </div>

      <div className="footerSection">
        <div className="footerHeading">Currículos comparados</div>
        <div style={{ fontSize: 12, color: 'var(--muted)', lineHeight: 1.7 }}>
          <b>Japão:</b> Math III · MEXT, fluxo Suugaku I/II/III/A/B.<br />
          <b>China:</b> Gaokao · 数学 (cálculo opcional, mas presente em high-stakes).<br />
          <b>Coreia do Sul:</b> CSAT · 수학 — cálculo via 미적분 (mathematics II).<br />
          <b>Singapura:</b> H2 Mathematics (MOE) — cálculo + estatística inferencial.<br />
          <b>Alemanha:</b> Abitur · Mathematik (NRW Lehrplan, 2014) — cálculo obrigatório.<br />
          <b>França:</b> Baccalauréat · Mathématiques Spécialité (Eduscol).<br />
          <b>Rússia:</b> ЕГЭ Профильный — cálculo obrigatório para acesso a engenharia.<br />
          <b>Finlândia:</b> Pitkä matematiikka (Opetushallitus, 2014) — cálculo obrigatório no nível extenso.<br />
          <b>Estados Unidos:</b> AP Calculus AB/BC (College Board) — opcional, ~400k inscritos/ano.<br />
          <b>IB:</b> Mathematics: Analysis and Approaches HL — cálculo obrigatório.<br />
          <b>Brasil:</b> BNCC 2018 — sem limites/derivadas/integrais.
        </div>
      </div>
    </footer>
  );
}

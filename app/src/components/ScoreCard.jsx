// Generic ScoreCard — "Parecer crítico" rendered on every vertical page.
//
// Lê de app/src/data/pareceres.js (uma única persona, régua adaptativa
// graduacao/lato_sensu/mestrado/doutorado). Renderiza:
//   • Header com nível aplicado + score (numérico OU letra A/B/C/D)
//   • Calibragem (resumo do porquê desta nota)
//   • Utilidade social (concreta — quem usa, pra que, que decisão muda)
//   • 4 colunas: pontos fortes / problemas para nota plena / problemas
//     para subir nível / próximos passos concretos
//
// Score grading:
//   - graduacao + lato_sensu → numeric 0-10 (display "8,5 / 10")
//   - mestrado + doutorado   → letter A/B/C/D (display "B (2 pts) — passa na média")

import { NIVEL_LABEL, LETRA_PONTOS, LETRA_DESCRICAO } from '../data/pareceres';

export default function ScoreCard({ parecer }) {
  if (!parecer) return null;

  const {
    nivel,
    scoreType,
    scoreNumeric,
    scoreLetra,
    scoreOriginal,
    originalLabel,
    originalUrl,
    ultimaAtualizacao,
    versao,
    resumoCalibragem,
    utilidadeSocial,
    pontosFortes,
    problemasParaNotaPlena,
    problemasParaSubirNivel,
    proximosPassos,
  } = parecer;

  const nivelLabel = NIVEL_LABEL[nivel] || nivel;
  const isStrictoSensu = nivel === 'stricto_sensu_mestrado' || nivel === 'stricto_sensu_doutorado';

  // Cor do header conforme nível: vermelho-âmbar pra reprovado/baixo,
  // azul-petróleo pra normal, verde pra mestrado+, dourado pra doutorado+.
  const accentColor = (() => {
    if (nivel === 'stricto_sensu_doutorado') return '#ca8a04';   // dourado
    if (nivel === 'stricto_sensu_mestrado')  return '#059669';   // verde
    if (scoreType === 'numeric' && scoreNumeric < 6.5) return '#dc2626';  // vermelho
    return '#b45309';   // âmbar (default lato sensu / graduação)
  })();

  return (
    <section className="panel no-print" style={{ marginBottom: 14, borderLeft: `4px solid ${accentColor}` }}>
      <div className="panelHead">
        <span className="panelLabel">
          Parecer crítico — Avaliador externo independente
          (IA Claude Opus 4.7, modo Professor de Programa de Mestrado e Doutorado
          em Finanças e Engenharia de Software)
        </span>
        <span className="kicker">Atualizado em {ultimaAtualizacao} · v{versao}</span>
      </div>

      <div style={{ display: 'flex', gap: 24, flexWrap: 'wrap', alignItems: 'baseline', marginBottom: 14 }}>
        {/* Score atual */}
        <div>
          <div className="kicker" style={{ marginBottom: 4 }}>
            Avaliado como
          </div>
          <div style={{ fontSize: 16, fontWeight: 700, marginBottom: 4 }}>
            {nivelLabel}
          </div>
          {scoreType === 'numeric' ? (
            <div style={{
              fontSize: 36, fontWeight: 800, letterSpacing: '-0.02em', lineHeight: 1,
              color: 'var(--text)',
            }}>
              {scoreNumeric.toFixed(1)}
              <span style={{ fontSize: 18, color: 'var(--muted)', fontWeight: 600 }}> /10</span>
            </div>
          ) : (
            <div>
              <div style={{
                fontSize: 36, fontWeight: 800, letterSpacing: '-0.02em', lineHeight: 1,
                color: accentColor,
              }}>
                Conceito {scoreLetra}
                <span style={{ fontSize: 16, color: 'var(--muted)', fontWeight: 600, marginLeft: 8 }}>
                  ({LETRA_PONTOS[scoreLetra]} pts)
                </span>
              </div>
              <div style={{ fontSize: 12, color: 'var(--muted)', marginTop: 4 }}>
                {LETRA_DESCRICAO[scoreLetra]}
              </div>
            </div>
          )}
        </div>

        {/* Score original (precedente, se houver) */}
        {Number.isFinite(scoreOriginal) && (
          <div>
            <div className="kicker" style={{ marginBottom: 4 }}>
              Score original{originalLabel ? ` (${originalLabel})` : ''}
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
              <div style={{
                fontSize: 28, fontWeight: 700, letterSpacing: '-0.02em', lineHeight: 1,
                color: 'var(--muted)',
              }}>
                {scoreOriginal.toFixed(1)}
                <span style={{ fontSize: 14, color: 'var(--faint)', fontWeight: 600 }}> /10</span>
              </div>
              {originalUrl && (
                <a
                  href={originalUrl}
                  target="_blank"
                  rel="noreferrer"
                  style={{
                    display: 'inline-flex', alignItems: 'center', gap: 6,
                    padding: '6px 12px', fontSize: 12, fontWeight: 600,
                    color: 'var(--accent)', background: 'var(--accent-soft)',
                    border: '1px solid var(--border)', borderRadius: 999,
                    textDecoration: 'none', whiteSpace: 'nowrap',
                  }}
                  title="Abre o trabalho original em nova aba"
                >
                  📄 Ler original ↗
                </a>
              )}
            </div>
          </div>
        )}

        {/* Badge de regra de aprovação stricto sensu */}
        {isStrictoSensu && (
          <div style={{
            marginLeft: 'auto',
            padding: '8px 14px',
            background: scoreLetra === 'A' ? '#059669' : scoreLetra === 'B+' ? '#0e9669' : scoreLetra === 'B' ? '#0d9488' : scoreLetra === 'C' ? '#b45309' : '#dc2626',
            color: 'white', borderRadius: 8,
            fontSize: 11, fontWeight: 700, letterSpacing: '0.04em',
            lineHeight: 1.4, textAlign: 'right',
          }}>
            <div style={{ textTransform: 'uppercase' }}>
              Regra do nível: aprovação se média ≥ 2,0
            </div>
            <div style={{ fontSize: 10, fontWeight: 500, opacity: 0.9, marginTop: 2 }}>
              {LETRA_PONTOS[scoreLetra] >= 2
                ? '✓ Este trabalho passa sozinho'
                : `⚠ Precisa de A em ${Math.ceil((2 - LETRA_PONTOS[scoreLetra]) / 1) + 1}+ outros para compensar`}
            </div>
          </div>
        )}
      </div>

      {resumoCalibragem && (
        <p style={{ fontSize: 12.5, color: 'var(--muted)', marginBottom: 12, lineHeight: 1.6 }}>
          <b>Calibragem:</b> {resumoCalibragem}
        </p>
      )}

      {utilidadeSocial && (
        <div style={{
          padding: 12, borderRadius: 6,
          background: 'var(--accent-soft, rgba(13, 148, 136, 0.08))',
          borderLeft: '3px solid #0d9488',
          marginBottom: 14,
        }}>
          <div style={{
            fontWeight: 700, fontSize: 11, letterSpacing: '0.06em',
            textTransform: 'uppercase', color: '#0d9488', marginBottom: 6,
          }}>
            🌍 Utilidade social — útil pra quem, pra fazer o quê?
          </div>
          <p style={{ fontSize: 12.5, lineHeight: 1.6, margin: 0 }}>
            {utilidadeSocial}
          </p>
        </div>
      )}

      <div style={{
        display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))',
        gap: 14, fontSize: 12.5,
      }}>
        <Column color="#059669" title="✓ Pontos fortes" items={pontosFortes} />
        <Column color="#b45309" title="⚠ Problemas para nota plena no nível atual" items={problemasParaNotaPlena} />
        <Column color="#1d4ed8" title="★ Problemas para subir de nível" items={problemasParaSubirNivel} />
        <Column color="var(--muted)" title="→ Próximos passos concretos" items={proximosPassos} />
      </div>
    </section>
  );
}

function Column({ color, title, items }) {
  if (!items || items.length === 0) return null;
  return (
    <div>
      <div style={{
        fontWeight: 700, fontSize: 11, letterSpacing: '0.06em', textTransform: 'uppercase',
        color, marginBottom: 6,
      }}>
        {title}
      </div>
      <ul style={{ margin: 0, paddingLeft: 18, lineHeight: 1.6 }}>
        {items.map((it, i) => <li key={i}>{it}</li>)}
      </ul>
    </div>
  );
}

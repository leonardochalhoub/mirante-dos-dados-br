// Ata do Conselho do Mirante — peer review interno simulando banca fictícia
// com 4 cadeiras (Finanças, Eng. Software, Design HCI, Administração).
//
// Lê uma ata em formato app/src/data/atas-conselho.js e renderiza:
//   1. Header com meta (artigo, commit, data, status, scores)
//   2. Rodada 1 — pareceres iniciais (4 cards, expansíveis)
//   3. Rodada 4 — re-avaliação completa pós-WHY com roadmap doutorado
//   4. Consenso emergente
//   5. Footer — próxima reunião
//
// Designs cards expansíveis usam <details>/<summary> nativos para a11y.

const CADEIRA_META = {
  'financas':       { emoji: '🧮', curto: 'Finanças',          cor: '#1d4ed8' },
  'eng-software':   { emoji: '💻', curto: 'Eng. Software',     cor: '#0d9488' },
  'design':         { emoji: '🎨', curto: 'Design (HCI)',      cor: '#dc2626' },
  'administrador':  { emoji: '🧭', curto: 'Administrador',     cor: '#b45309' },
};

export default function AtaConselho({ ata }) {
  if (!ata) return null;
  const { meta, pareceres_iniciais, rodada_4_doutorado } = ata;

  return (
    <section className="panel no-print" style={{
      marginTop: 18, marginBottom: 14,
      borderTop: '4px solid #ca8a04',
    }}>
      <Header meta={meta} pareceres={pareceres_iniciais} />

      <details style={{ marginTop: 18 }}>
        <summary style={summaryStyle}>
          <b>Rodada 1</b> — pareceres iniciais (4 cadeiras, em paralelo)
          <span style={summaryHintStyle}>clique para expandir</span>
        </summary>
        <div style={{ marginTop: 14, display: 'grid', gap: 12 }}>
          {pareceres_iniciais.map((p) => (
            <ParecerInicialCard key={p.cadeira} parecer={p} />
          ))}
        </div>
      </details>

      <details open style={{ marginTop: 18 }}>
        <summary style={summaryStyle}>
          <b>Rodada 4</b> — re-avaliação completa pós-WHY · {' '}
          <span style={{ color: '#ca8a04' }}>roadmap para nível de DOUTORADO</span>
          <span style={summaryHintStyle}>aberto por padrão</span>
        </summary>
        <div style={{ marginTop: 14 }}>
          <div style={{
            fontSize: 13, lineHeight: 1.6, color: 'var(--muted)', marginBottom: 14,
            padding: '8px 12px',
            background: 'var(--accent-soft, rgba(13, 148, 136, 0.05))',
            borderLeft: '3px solid #ca8a04',
            borderRadius: 4,
          }}>
            <b>Contexto:</b> {rodada_4_doutorado.contexto}
          </div>

          <div style={{ display: 'grid', gap: 12 }}>
            {rodada_4_doutorado.pareceres.map((p) => (
              <ParecerDoutoradoCard key={p.cadeira} parecer={p} />
            ))}
          </div>

          {rodada_4_doutorado.consenso_emergente && (
            <ConsensoEmergente consenso={rodada_4_doutorado.consenso_emergente} />
          )}
        </div>
      </details>

      <Footer meta={meta} />
    </section>
  );
}

// ─── Header ───────────────────────────────────────────────────────────────
function Header({ meta, pareceres }) {
  const statusColor = meta.status?.includes('APROVADO') ? '#059669' : '#b45309';

  return (
    <div>
      <div className="panelHead">
        <span className="panelLabel" style={{ fontSize: 14 }}>
          🏛️ Ata da Reunião #{meta.reuniao} do Conselho do Mirante
        </span>
        <span className="kicker">{meta.data} · {meta.rodadas} rodadas concluídas</span>
      </div>

      <div style={{
        fontSize: 12.5, lineHeight: 1.55,
        marginTop: 8, marginBottom: 12,
        padding: '8px 12px',
        background: 'rgba(202, 138, 4, 0.08)',
        border: '1px solid #ca8a04',
        borderRadius: 6,
      }}>
        <div style={{
          fontSize: 10.5, fontWeight: 700, letterSpacing: '0.06em',
          textTransform: 'uppercase', color: '#ca8a04', marginBottom: 4,
        }}>
          ⚠ Aviso editorial — Peer reviews de IA, não humanos
        </div>
        <div style={{ color: 'var(--text)' }}>
          Os 4 pareceres abaixo são <b>peer reviews simulados por personas de IA</b>{' '}
          (Claude Opus/Sonnet, Anthropic), consolidadas a partir de referências reais
          anonimizadas (PhDs, professores titulares, fundadores e tech leads das áreas
          de Finanças, Eng. de Software, Design/HCI e Administração). <b>Não substituem</b>{' '}
          peer review humano formal — servem como auto-avaliação rigorosa pré-submissão,
          triangulando 4 lentes que avaliadores reais cobririam.
        </div>
      </div>

      <div style={{
        fontSize: 13, color: 'var(--muted)', lineHeight: 1.6,
        marginTop: 4, marginBottom: 12,
      }}>
        <b>Pauta:</b> {meta.artigo} · commit <code>{meta.commit}</code> · coautoria {meta.coautoria}
      </div>

      <div style={{ display: 'flex', gap: 14, flexWrap: 'wrap', alignItems: 'center', marginBottom: 4 }}>
        <div style={{
          padding: '8px 14px',
          background: statusColor, color: 'white', borderRadius: 8,
          fontSize: 11, fontWeight: 700, letterSpacing: '0.04em',
          textTransform: 'uppercase',
        }}>
          Status: {meta.status}
        </div>

        {pareceres && (
          <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', alignItems: 'center', fontSize: 12 }}>
            <span className="kicker">Scores Rodada 1 →</span>
            {pareceres.map((p) => {
              const cm = CADEIRA_META[p.cadeira];
              const score = p.score?.tipo === 'letra'
                ? `${p.score.letra} (${p.score.pontos})`
                : 'qualitativo';
              return (
                <span key={p.cadeira} style={{
                  padding: '3px 10px', borderRadius: 999,
                  background: 'var(--bg)', border: `1px solid ${cm.cor}`,
                  fontSize: 11, fontWeight: 600,
                }}>
                  {cm.emoji} {cm.curto}: <b style={{ color: cm.cor }}>{score}</b>
                </span>
              );
            })}
            {meta.media_quants != null && (
              <span style={{
                padding: '3px 10px', borderRadius: 999,
                background: '#0d9488', color: 'white',
                fontSize: 11, fontWeight: 700,
              }}>
                Média quants: {meta.media_quants.toFixed(1)} (limiar {meta.limiar_aprovacao.toFixed(1)})
              </span>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

// ─── Parecer da Rodada 1 ──────────────────────────────────────────────────
function ParecerInicialCard({ parecer }) {
  const cm = CADEIRA_META[parecer.cadeira];
  const score = parecer.score?.tipo === 'letra'
    ? <span><b style={{ color: cm.cor, fontSize: 16 }}>{parecer.score.letra}</b> ({parecer.score.pontos} pts)</span>
    : <span style={{ color: cm.cor, fontWeight: 700 }}>parecer qualitativo</span>;

  return (
    <div style={{
      padding: 14,
      borderLeft: `3px solid ${cm.cor}`,
      background: 'var(--bg)',
      borderRadius: 4,
    }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: 12, marginBottom: 8 }}>
        <div>
          <div style={{ fontWeight: 700, fontSize: 13.5 }}>
            {cm.emoji} {parecer.titulo}
          </div>
          <div style={{ fontSize: 11, color: 'var(--muted)', marginTop: 2 }}>
            {parecer.lente}
          </div>
        </div>
        <div style={{ textAlign: 'right', fontSize: 12, whiteSpace: 'nowrap' }}>
          {score}
          <div style={{ fontSize: 10.5, color: 'var(--muted)', marginTop: 2, fontStyle: 'italic' }}>
            {parecer.veredicto}
          </div>
        </div>
      </div>

      <blockquote style={{
        margin: '0 0 10px 0', padding: '6px 10px',
        borderLeft: '2px solid var(--border)',
        fontSize: 12, fontStyle: 'italic', color: 'var(--muted)',
        lineHeight: 1.5,
      }}>
        {parecer.epigrafe}
      </blockquote>

      <p style={{ fontSize: 12.5, lineHeight: 1.6, margin: '0 0 10px 0' }}>
        {parecer.argumento_central}
      </p>

      {parecer.pendencias && parecer.pendencias.length > 0 && (
        <div style={{ marginTop: 8 }}>
          <div style={{
            fontSize: 10.5, fontWeight: 700, letterSpacing: '0.06em',
            textTransform: 'uppercase', color: '#b45309', marginBottom: 4,
          }}>
            Pendências
          </div>
          <ul style={{ margin: 0, paddingLeft: 18, fontSize: 11.5, lineHeight: 1.55 }}>
            {parecer.pendencias.map((it, i) => <li key={i}>{it}</li>)}
          </ul>
        </div>
      )}

      {parecer.perguntas_criticas && (
        <div style={{ marginTop: 8 }}>
          <div style={{
            fontSize: 10.5, fontWeight: 700, letterSpacing: '0.06em',
            textTransform: 'uppercase', color: cm.cor, marginBottom: 4,
          }}>
            Perguntas críticas
          </div>
          <ul style={{ margin: 0, paddingLeft: 18, fontSize: 11.5, lineHeight: 1.55 }}>
            {parecer.perguntas_criticas.map((it, i) => <li key={i}>{it}</li>)}
          </ul>
        </div>
      )}

      {parecer.sugestao_para_subir_pra_a && (
        <div style={{
          marginTop: 10, padding: '6px 10px',
          background: 'rgba(5, 150, 105, 0.06)',
          borderLeft: '2px solid #059669', borderRadius: 3,
          fontSize: 11.5, lineHeight: 1.55,
        }}>
          <b style={{ color: '#059669' }}>Sugestão para subir pra A:</b> {parecer.sugestao_para_subir_pra_a}
        </div>
      )}
    </div>
  );
}

// ─── Parecer da Rodada 4 (re-avaliação doutorado) ─────────────────────────
function ParecerDoutoradoCard({ parecer }) {
  const cm = CADEIRA_META[parecer.cadeira];
  const isQual = parecer.score_revisado?.tipo === 'qualitativo';
  const score = isQual
    ? <span style={{ color: cm.cor, fontWeight: 700 }}>visão qualitativa estratégica</span>
    : <span>
        <b style={{ color: cm.cor, fontSize: 16 }}>{parecer.score_revisado.letra}</b> ({parecer.score_revisado.pontos})
        {parecer.score_revisado.mudou === false && (
          <span style={{ fontSize: 10, color: 'var(--muted)', marginLeft: 6 }}>
            {parecer.score_revisado.ressignificado ? '(ressignificado)' : '(mantido)'}
          </span>
        )}
      </span>;

  return (
    <details style={{
      padding: 14,
      borderLeft: `3px solid ${cm.cor}`,
      background: 'var(--bg)',
      borderRadius: 4,
    }}>
      <summary style={{
        cursor: 'pointer', listStyle: 'none', userSelect: 'none',
        display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: 12,
      }}>
        <div>
          <div style={{ fontWeight: 700, fontSize: 13.5 }}>
            {cm.emoji} {cm.curto} — re-avaliação doutorado
          </div>
          <div style={{ fontSize: 11, color: 'var(--muted)', marginTop: 2 }}>
            {parecer.roadmap?.length || parecer.roadmap_estrategico?.length || 0} ações no roadmap · clique para expandir
          </div>
        </div>
        <div style={{ textAlign: 'right', fontSize: 12, whiteSpace: 'nowrap' }}>
          {score}
        </div>
      </summary>

      <div style={{ marginTop: 12 }}>
        {parecer.re_score_justificativa && (
          <div style={{ fontSize: 12.5, lineHeight: 1.6, marginBottom: 12 }}>
            <b style={{ color: cm.cor }}>Re-score:</b> {parecer.re_score_justificativa}
          </div>
        )}

        {parecer.veredicto_doutorado && (
          <div style={{ fontSize: 12.5, lineHeight: 1.6, marginBottom: 12 }}>
            <b style={{ color: cm.cor }}>Veredicto sob lente de doutorado:</b> {parecer.veredicto_doutorado}
          </div>
        )}

        {parecer.gap_doutorado && (
          <div style={{
            padding: 10, marginBottom: 12,
            background: 'rgba(180, 83, 9, 0.05)',
            borderLeft: '2px solid #b45309', borderRadius: 3,
            fontSize: 12, lineHeight: 1.6,
          }}>
            <b style={{ color: '#b45309' }}>Gap mestrado → doutorado:</b> {parecer.gap_doutorado}
          </div>
        )}

        {parecer.analise_longo_prazo && (
          <div style={{
            padding: 10, marginBottom: 12,
            background: 'rgba(180, 83, 9, 0.05)',
            borderLeft: '2px solid #b45309', borderRadius: 3,
            fontSize: 12, lineHeight: 1.6,
          }}>
            <b style={{ color: '#b45309' }}>Análise de longo prazo:</b> {parecer.analise_longo_prazo}
          </div>
        )}

        {parecer.roadmap && (
          <RoadmapTabela roadmap={parecer.roadmap} cor={cm.cor} />
        )}

        {parecer.roadmap_estrategico && (
          <RoadmapEstrategico roadmap={parecer.roadmap_estrategico} cor={cm.cor} />
        )}

        {parecer.defendivel_em && (
          <div style={{
            marginTop: 10, padding: '8px 12px',
            background: 'rgba(5, 150, 105, 0.07)',
            borderLeft: '2px solid #059669', borderRadius: 3,
            fontSize: 12, lineHeight: 1.55,
          }}>
            <b style={{ color: '#059669' }}>Concluído isso, defendível em:</b> {parecer.defendivel_em}
          </div>
        )}

        {parecer.contribuicao_doutoral && (
          <div style={{ fontSize: 12, color: 'var(--muted)', marginTop: 8, fontStyle: 'italic', lineHeight: 1.55 }}>
            <b>Contribuição doutoral:</b> {parecer.contribuicao_doutoral}
          </div>
        )}

        {parecer.unica_acao_que_muda_o_jogo && (
          <div style={{
            marginTop: 12, padding: 12,
            background: 'rgba(202, 138, 4, 0.08)',
            border: '1px solid #ca8a04', borderRadius: 6,
            fontSize: 12.5, lineHeight: 1.6,
          }}>
            <div style={{
              fontSize: 10.5, fontWeight: 700, letterSpacing: '0.06em',
              textTransform: 'uppercase', color: '#ca8a04', marginBottom: 4,
            }}>
              ⚡ A ÚNICA ação que, feita esta semana, muda o jogo
            </div>
            {parecer.unica_acao_que_muda_o_jogo}
          </div>
        )}

        {parecer.frase_final && (
          <blockquote style={{
            margin: '12px 0 0 0', padding: '8px 12px',
            borderLeft: `2px solid ${cm.cor}`,
            fontSize: 12.5, fontStyle: 'italic', color: 'var(--muted)',
            lineHeight: 1.6,
          }}>
            “{parecer.frase_final}”
          </blockquote>
        )}

        {parecer.armadilha && (
          <div style={{
            marginTop: 12, padding: 10,
            background: 'rgba(220, 38, 38, 0.06)',
            borderLeft: '2px solid #dc2626', borderRadius: 3,
            fontSize: 11.5, lineHeight: 1.55,
          }}>
            <b style={{ color: '#dc2626' }}>⚠ Armadilha que o autor pode estar subestimando:</b> {parecer.armadilha}
          </div>
        )}

        {parecer.risco_estrategico_subestimado && (
          <div style={{
            marginTop: 12, padding: 10,
            background: 'rgba(220, 38, 38, 0.06)',
            borderLeft: '2px solid #dc2626', borderRadius: 3,
            fontSize: 11.5, lineHeight: 1.55,
          }}>
            <b style={{ color: '#dc2626' }}>⚠ Risco estratégico subestimado:</b> {parecer.risco_estrategico_subestimado}
          </div>
        )}
      </div>
    </details>
  );
}

// ─── Roadmap técnico (Finanças, Eng., Design) ────────────────────────────
function RoadmapTabela({ roadmap, cor }) {
  return (
    <div style={{ marginTop: 8 }}>
      <div style={{
        fontSize: 10.5, fontWeight: 700, letterSpacing: '0.06em',
        textTransform: 'uppercase', color: cor, marginBottom: 6,
      }}>
        Roadmap concreto para doutorado ({roadmap.length} ações)
      </div>
      <ol style={{ margin: 0, paddingLeft: 22, fontSize: 12, lineHeight: 1.6 }}>
        {roadmap.map((step) => (
          <li key={step.n} style={{ marginBottom: 8 }}>
            <b>{step.titulo}</b>
            {' — '}
            <span style={{ color: 'var(--muted)' }}>{step.tecnica}</span>
            <div style={{
              fontSize: 10.5, color: 'var(--muted)', marginTop: 2,
              display: 'flex', flexWrap: 'wrap', gap: 10,
            }}>
              {step.dado &&  <span><b>Dado:</b> {step.dado}</span>}
              {step.why &&   <span><b>WHY:</b> {step.why}</span>}
              {step.tempo && <span><b>Tempo:</b> {step.tempo}</span>}
              {step.destino && <span style={{ color: cor, fontWeight: 600 }}>→ {step.destino}</span>}
            </div>
          </li>
        ))}
      </ol>
    </div>
  );
}

// ─── Roadmap estratégico (Administrador) ─────────────────────────────────
function RoadmapEstrategico({ roadmap, cor }) {
  return (
    <div style={{ marginTop: 8 }}>
      <div style={{
        fontSize: 10.5, fontWeight: 700, letterSpacing: '0.06em',
        textTransform: 'uppercase', color: cor, marginBottom: 6,
      }}>
        Roadmap estratégico-comercial ({roadmap.length} ações)
      </div>
      <ol style={{ margin: 0, paddingLeft: 22, fontSize: 12, lineHeight: 1.6 }}>
        {roadmap.map((step) => (
          <li key={step.n} style={{ marginBottom: 8 }}>
            <b>{step.titulo}</b>
            {step.quando && <span style={{ color: cor, fontWeight: 600 }}> · {step.quando}</span>}
            <div style={{
              fontSize: 10.5, color: 'var(--muted)', marginTop: 2,
              display: 'flex', flexWrap: 'wrap', gap: 10,
            }}>
              {step.pra_quem && <span><b>Para:</b> {step.pra_quem}</span>}
              {step.why &&      <span><b>WHY:</b> {step.why}</span>}
              {step.valor &&    <span><b>Valor:</b> {step.valor}</span>}
            </div>
          </li>
        ))}
      </ol>
    </div>
  );
}

// ─── Consenso emergente ──────────────────────────────────────────────────
function ConsensoEmergente({ consenso }) {
  return (
    <div style={{
      marginTop: 18, padding: 14,
      background: 'var(--accent-soft, rgba(13, 148, 136, 0.06))',
      border: '1px solid #0d9488', borderRadius: 6,
    }}>
      <div style={{
        fontSize: 11, fontWeight: 700, letterSpacing: '0.06em',
        textTransform: 'uppercase', color: '#0d9488', marginBottom: 10,
      }}>
        🤝 Consenso emergente (síntese das 4 cadeiras)
      </div>
      <ul style={{ margin: 0, paddingLeft: 18, fontSize: 12.5, lineHeight: 1.65 }}>
        {consenso.map((c, i) => (
          <li key={i} style={{ marginBottom: 8 }}>
            <b>{c.topico}.</b> {c.detalhe}
          </li>
        ))}
      </ul>
    </div>
  );
}

// ─── Footer ──────────────────────────────────────────────────────────────
function Footer({ meta }) {
  return (
    <div style={{
      marginTop: 18, paddingTop: 12,
      borderTop: '1px solid var(--border)',
      fontSize: 11, color: 'var(--muted)', lineHeight: 1.5,
      display: 'flex', justifyContent: 'space-between', flexWrap: 'wrap', gap: 8,
    }}>
      <div>
        Conselho fictício · 4 personas IA Claude consolidadas a partir de referências reais
        anonimizadas · régua mestrado, doutorado e pós-doutorado <i>stricto sensu</i>
      </div>
      <div>
        Reunião #{meta.reuniao} · {meta.data} · concluída em {meta.rodadas} rodadas
      </div>
    </div>
  );
}

// ─── Estilos compartilhados ──────────────────────────────────────────────
const summaryStyle = {
  cursor: 'pointer',
  fontSize: 13.5,
  padding: '8px 0',
  borderTop: '1px solid var(--border)',
  userSelect: 'none',
  display: 'flex',
  alignItems: 'center',
  gap: 10,
};

const summaryHintStyle = {
  marginLeft: 'auto',
  fontSize: 10.5,
  color: 'var(--faint)',
  fontStyle: 'italic',
  fontWeight: 400,
};

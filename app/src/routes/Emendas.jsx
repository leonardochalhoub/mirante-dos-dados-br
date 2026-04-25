// Vertical: Emendas Parlamentares.
// Source: /data/gold/gold_emendas_estados_df.json (gerado pelo pipeline Databricks)
//
// Esta vertical tem documentação acima dos gráficos: contexto sobre o que são
// emendas parlamentares, objetivos do vertical, e razões para análise pública.

import { useEffect, useMemo, useState } from 'react';
import PageHeader     from '../components/PageHeader';
import Panel          from '../components/Panel';
import KpiCard        from '../components/KpiCard';
import BrazilMap      from '../components/BrazilMap';
import StateRanking   from '../components/StateRanking';
import EvolutionBar   from '../components/charts/EvolutionBar';
import DownloadActions from '../components/DownloadActions';
import TechBadges      from '../components/TechBadges';
import { useTheme }    from '../hooks/useTheme';
import { loadGold }    from '../lib/data';
import { COLORSCALES } from '../lib/scales';
import { fmtBRL, fmtCompact, fmtDec1, fmtDec2, fmtInt, fmtPct } from '../lib/format';
import { exportToXlsx, exportChartsAsZip } from '../lib/exporters';

// ── Métricas exibidas ────────────────────────────────────────────────────
const METRICS = {
  emendaPerCapita2021: {
    label: 'Pago per capita (R$ 2021)', short: 'R$/hab',
    yaxisTitle: 'Pago per capita (R$ 2021)',
    fmt: fmtDec2, fmtRich: fmtBRL, money: true,
  },
  valor_pago_2021: {
    label: 'Valor pago (R$ bi, 2021)', short: 'R$ bi',
    yaxisTitle: 'Valor pago (R$ bi, 2021)',
    fmt: (v) => fmtDec2(v / 1e9), fmtRich: (v) => fmtBRL(v, { compact: true }),
  },
  valor_empenhado_2021: {
    label: 'Valor empenhado (R$ bi, 2021)', short: 'R$ bi',
    yaxisTitle: 'Valor empenhado (R$ bi, 2021)',
    fmt: (v) => fmtDec2(v / 1e9), fmtRich: (v) => fmtBRL(v, { compact: true }),
  },
  pct_executado: {
    label: '% executado (pago / empenhado)', short: '%',
    yaxisTitle: '% executado',
    fmt: fmtPct, fmtRich: fmtPct,
  },
  n_emendas: {
    label: 'Quantidade de emendas', short: 'emendas',
    yaxisTitle: 'Emendas',
    fmt: fmtCompact, fmtRich: fmtInt,
  },
};

const DEFAULT_METRIC = 'emendaPerCapita2021';
const DEFAULT_COLOR  = 'Cividis';

export default function Emendas() {
  const { theme } = useTheme();
  const [rows, setRows]             = useState(null);
  const [error, setError]           = useState(null);
  const [metricKey, setMetricKey]   = useState(DEFAULT_METRIC);
  const [year, setYear]             = useState(null);
  const [colorscale, setColorscale] = useState(DEFAULT_COLOR);

  useEffect(() => {
    loadGold('gold_emendas_estados_df.json')
      .then((all) => {
        setRows(all);
        const last = Math.max(...all.map((r) => r.Ano));
        setYear(String(last));
      })
      .catch((e) => setError(e.message));
  }, []);

  const metric = METRICS[metricKey];
  const years = useMemo(
    () => (rows ? Array.from(new Set(rows.map((r) => r.Ano))).sort() : []),
    [rows],
  );

  const filtered = useMemo(() => {
    if (!rows || year == null) return [];
    return rows
      .filter((r) => r.Ano === Number(year))
      .map((r) => ({ uf: r.uf, value: r[metricKey] || 0 }));
  }, [rows, metricKey, year]);

  const ranking = useMemo(() => [...filtered].sort((a, b) => b.value - a.value), [filtered]);

  const kpis = useMemo(() => {
    if (!rows || !year) return null;
    const yr = rows.filter((r) => r.Ano === Number(year));
    const empenhado = yr.reduce((s, r) => s + (r.valor_empenhado_nominal || 0), 0);
    const pago      = yr.reduce((s, r) => s + (r.valor_pago_nominal      || 0), 0);
    const totalNEmend = yr.reduce((s, r) => s + (r.n_emendas || 0), 0);
    return {
      empenhado, pago, totalNEmend,
      pct: empenhado > 0 ? pago / empenhado : 0,
    };
  }, [rows, year]);

  const evolutionData = useMemo(() => {
    if (!rows) return [];
    return years.map((y) => {
      const yr = rows.filter((r) => r.Ano === y);
      const sum = yr.reduce((s, r) => s + (r[metricKey] || 0), 0);
      // For per-capita-like metrics we want pop-weighted average
      if (metricKey === 'emendaPerCapita2021' || metricKey === 'pct_executado') {
        const sumW = yr.reduce((s, r) => s + ((r[metricKey] || 0) * (r.populacao || 0)), 0);
        const w    = yr.reduce((s, r) => s + (r.populacao || 0), 0);
        return { year: String(y), value: w > 0 ? sumW / w : 0 };
      }
      return { year: String(y), value: sum };
    });
  }, [rows, metricKey, years]);

  return (
    <>
      <PageHeader
        eyebrow="Vertical · transparência fiscal"
        title="Emendas Parlamentares"
        subtitle="Execução orçamentária por UF — RP6 individual, RP7 bancada, RP9 relator. Fonte: Portal da Transparência (CGU) · IBGE · BCB."
        right={
          <div className="header-right-row">
            <TechBadges />
            <DownloadActions
              onExportXlsx={() => exportToXlsx('mirante-emendas', { 'emendas_uf_ano': rows || [] })}
              onExportPng={() => exportChartsAsZip('mirante-emendas')}
            />
          </div>
        }
      />

      {/* ─── DOCUMENTAÇÃO ─────────────────────────────────────────────── */}
      <DocSection />

      {/* ─── DADOS ───────────────────────────────────────────────────── */}
      {error && <div className="error-block">Erro ao carregar dados: {error}</div>}

      {!error && !rows && (
        <div className="panel" style={{ marginTop: 18 }}>
          <div className="panelHead">
            <span className="panelLabel">Status</span>
            <span className="kicker">Pipeline em construção</span>
          </div>
          <p className="muted" style={{ fontSize: 13, lineHeight: 1.7 }}>
            Os dados ainda não foram materializados. O pipeline está pronto no Databricks
            (<code>job_emendas_refresh</code> em <code>pipelines/databricks.yml</code>) e
            será executado quando o ciclo mensal disparar (dia 24 às 6h UTC), ou manualmente
            via Workflows na UI do workspace. Quando o JSON gold for commitado em
            <code> /data/gold/gold_emendas_estados_df.json</code>, esta página renderiza
            automaticamente os KPIs, ranking e mapa.
          </p>
        </div>
      )}

      {rows && kpis && (
        <>
          <div className="kpiRow" data-export-id="emendas-kpis">
            <KpiCard label={`Empenhado · ${year}`}    value={fmtBRL(kpis.empenhado, { compact: true })} sub="autorizado em lei orçamentária" />
            <KpiCard label={`Pago · ${year}`}         value={fmtBRL(kpis.pago,      { compact: true })} sub="execução efetiva (R$ nominal)" color="#0d9488" />
            <KpiCard label={`Execução · ${year}`}     value={fmtPct(kpis.pct)}                         sub="pago / empenhado" color="#b45309" />
            <KpiCard label={`Emendas · ${year}`}      value={fmtCompact(kpis.totalNEmend)}             sub="distintas no Brasil" color="#be185d" />
          </div>

          <div className="layout">
            <div className="row row-controls-bar">
              <Panel label="Filtros & dados" sub="CGU · IBGE · BCB">
                <div className="controls">
                  <div className="control">
                    <label htmlFor="metric">Métrica</label>
                    <select id="metric" value={metricKey} onChange={(e) => setMetricKey(e.target.value)}>
                      {Object.entries(METRICS).map(([k, m]) => (
                        <option key={k} value={k}>{m.label}</option>
                      ))}
                    </select>
                  </div>
                  <div className="control">
                    <label htmlFor="year">Ano</label>
                    <select id="year" value={year || ''} onChange={(e) => setYear(e.target.value)}>
                      {years.map((y) => (<option key={y} value={y}>{y}</option>))}
                    </select>
                  </div>
                  <div className="metaBlock">
                    <b>Empenhado:</b> valor reservado em lei orçamentária<br />
                    <b>Pago:</b> dinheiro efetivamente transferido<br />
                    <b>Restos a pagar:</b> empenhado mas não pago no exercício<br />
                    <b>R$ 2021:</b> deflacionado pelo IPCA (BCB)
                  </div>
                </div>
              </Panel>

              <Panel label="Evolução nacional" sub={metric.label} exportId="emendas-evolucao">
                <EvolutionBar
                  data={evolutionData}
                  theme={theme}
                  yLabel={metric.yaxisTitle}
                  xLabel="Ano"
                  format={metric.fmt}
                  height={320}
                />
              </Panel>
            </div>

            <div className="row row-ranking-map">
              <Panel label="Ranking por UF" sub={`${metric.label} · ${year}`} exportId="emendas-ranking">
                <StateRanking rows={ranking} format={metric.fmtRich} />
              </Panel>

              <Panel
                label="Distribuição geográfica"
                exportId="emendas-mapa"
                right={
                  <div className="mapControls">
                    <label htmlFor="colorscale">Cores</label>
                    <select id="colorscale" value={colorscale} onChange={(e) => setColorscale(e.target.value)}>
                      {COLORSCALES.map((c) => (<option key={c.value} value={c.value}>{c.label}</option>))}
                    </select>
                  </div>
                }
              >
                <BrazilMap data={filtered} colorscale={colorscale} theme={theme} hoverFmt={metric.fmtRich} unit={metric.short} />
              </Panel>
            </div>
          </div>
        </>
      )}

      <Footer />
    </>
  );
}

// ─── Documentação textual ────────────────────────────────────────────────
function DocSection() {
  return (
    <section className="emendas-doc">
      <div className="doc-block">
        <div className="kicker">Introdução</div>
        <h2 className="doc-h2">O que são emendas parlamentares</h2>
        <p>
          Emendas parlamentares são alterações que deputados federais e senadores fazem na
          proposta de orçamento da União, redirecionando recursos para áreas e regiões
          escolhidas por eles — saúde, educação, infraestrutura, cultura. São o principal
          instrumento que o Legislativo tem para influenciar onde o dinheiro federal chega.
        </p>
        <p>
          A Constituição classifica três tipos principais de emendas pelo <b>Resultado
          Primário (RP)</b> usado no orçamento:
        </p>
        <ul>
          <li><b>RP6 — Emendas individuais</b>: cada parlamentar tem cota fixa anual (~R$30M
            em 2024). Execução obrigatória pelo governo desde EC 86/2015.</li>
          <li><b>RP7 — Emendas de bancada estadual</b>: deputados de cada estado decidem em
            conjunto. Também de execução obrigatória.</li>
          <li><b>RP9 — Emendas do relator</b> (extintas pelo STF em 2022): valores controlados
            pelo relator-geral do orçamento, distribuídos sem regra clara. Origem do
            chamado "orçamento secreto".</li>
        </ul>
      </div>

      <div className="doc-block">
        <div className="kicker">Objetivos do vertical</div>
        <h2 className="doc-h2">O que esta análise mostra</h2>
        <ol>
          <li><b>Distribuição geográfica</b> — quanto cada UF recebeu por ano, em valores
            reais (R$ 2021) e per capita. Permite comparar acesso ao recurso público
            federal entre estados pequenos e grandes em base equivalente.</li>
          <li><b>Taxa de execução</b> — quanto do empenhado virou pagamento de fato. Empenhado
            sem execução vira "restos a pagar" — promessa orçamentária que pode nunca chegar
            ao destino.</li>
          <li><b>Composição por tipo (RP6/RP7/RP9)</b> — quanto da execução vem de cada
            modalidade. Permite ver o peso histórico das emendas de relator e o impacto
            da decisão do STF de 2022.</li>
          <li><b>Evolução temporal 2014–presente</b> — captura o crescimento expressivo das
            emendas no orçamento federal nos últimos anos e momentos-chave (EC 86,
            decisão do STF, Auxílio Brasil → Bolsa Família).</li>
        </ol>
      </div>

      <div className="doc-block">
        <div className="kicker">Por que isso importa</div>
        <h2 className="doc-h2">Razões para a análise pública</h2>
        <ul>
          <li>
            <b>Transparência:</b> emendas individuais e de bancada hoje somam mais de
            R$ 50 bilhões/ano — equivalente a um dos maiores ministérios. Consolidar esse
            dado em uma visualização única, navegável por qualquer cidadão, é prestação
            de contas básica.
          </li>
          <li>
            <b>Accountability eleitoral:</b> permite ao eleitor saber quanto recurso federal
            o conjunto de parlamentares da sua UF efetivamente direcionou ao estado, e
            cobrar quando há subutilização ou subexecução.
          </li>
          <li>
            <b>Análise de equidade:</b> per capita revela se estados com menos representação
            (UFs pequenas) recebem proporcionalmente mais ou menos do que os mais populosos.
            Cruzar com indicadores sociais ajuda a entender se o gasto está alinhado às
            necessidades.
          </li>
          <li>
            <b>Controle social do "orçamento secreto":</b> antes da decisão do STF, RP9 era
            opaco. Esses dados, embora oficiais, ficavam dispersos. Agregar e expor o
            histórico ajuda a documentar o problema e medir os efeitos de mudanças
            institucionais.
          </li>
          <li>
            <b>Pesquisa e jornalismo de dados:</b> o JSON gold (versionado neste repo) e o
            pipeline open-source permitem que jornalistas, pesquisadores e ONGs reproduzam
            cruzamentos próprios sem precisar baixar 10+ GB do Portal da Transparência.
          </li>
        </ul>
      </div>

      <div className="doc-block doc-block-meta">
        <div className="kicker">Notas técnicas e limitações</div>
        <ul style={{ fontSize: 13 }}>
          <li>
            Fonte primária: <b>Portal da Transparência (CGU)</b>. A CGU às vezes revisa
            valores retroativamente (decisões judiciais, ajustes contábeis) — números
            podem mudar minimamente entre refreshes.
          </li>
          <li>
            <b>UF de favorecido</b>: identificamos pelo município beneficiário. Emendas que
            financiam órgãos federais (ministérios) sem destino estadual claro entram
            como "OUTRO" e não aparecem na agregação por UF.
          </li>
          <li>
            <b>Deflação para R$ 2021</b>: usa IPCA acumulado anual (BCB SGS 433),
            normalizado em dezembro/2021 — mesmo método aplicado em Bolsa Família.
          </li>
          <li>
            <b>Per capita</b>: divide pelo total da população residente da UF (IBGE/SIDRA
            tabela 6579). Não considera fluxo migratório interno nem população flutuante.
          </li>
        </ul>
      </div>
    </section>
  );
}

function Footer() {
  return (
    <footer className="footer panel" style={{ marginTop: 18 }}>
      <div className="footerSection">
        <div className="footerHeading">Fontes</div>
        <div className="footerSource">
          <a href="https://portaldatransparencia.gov.br/download-de-dados/emendas" target="_blank" rel="noreferrer">
            Portal da Transparência (CGU) — Emendas Parlamentares
          </a>
          <span className="footerDesc">Execução de emendas individuais (RP6), de bancada (RP7), do relator (RP9) e de comissão (RP8). Atualização anual.</span>
        </div>
        <div className="footerSource">
          <a href="https://sidra.ibge.gov.br/tabela/6579" target="_blank" rel="noreferrer">IBGE SIDRA — Tabela 6579</a>
          <span className="footerDesc">População residente estimada por UF</span>
        </div>
        <div className="footerSource">
          <a href="https://api.bcb.gov.br/dados/serie/bcdata.sgs.433/dados?formato=json" target="_blank" rel="noreferrer">BCB SGS — Série 433</a>
          <span className="footerDesc">IPCA mensal, deflator para R$ 2021</span>
        </div>
        <div className="footerNote">
          Pipeline: bronze (CGU CSVs) → silver (UF × Ano × tipo_RP, valores parseados) →
          gold (join populacao + IPCA). Reutiliza as dimensões compartilhadas
          <code> populacao_uf_ano</code> e <code>ipca_deflators_2021</code>.
        </div>
      </div>

      <div className="footerSection">
        <div className="footerHeading">Referências</div>
        <div style={{ fontSize: 12, color: 'var(--muted)', lineHeight: 1.7 }}>
          <b>EC 86/2015</b>: tornou execução de emendas individuais obrigatória.<br />
          <b>EC 100/2019</b>: estendeu obrigatoriedade às emendas de bancada.<br />
          <b>STF · ADPFs 850/851/854/1014</b> (2022): declarou inconstitucional o
          mecanismo de RP9 (relator-geral) — fim do "orçamento secreto".<br />
          <b>LC 210/2024</b>: regulamentou novas regras de transparência para emendas
          de comissão (RP8) e bancada (RP7).
        </div>
      </div>
    </footer>
  );
}

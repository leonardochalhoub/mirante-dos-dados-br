// Vertical: Equipamentos CNES (todos os tipos, não só Ressonância Magnética).
// Source: /data/gold/gold_equipamentos_estados_ano.json
// Schema row: { estado, ano, tipequip, codequip, equipment_key, equipment_name,
//   equipment_category, populacao,
//   cnes_count, total_avg, per_capita_scaled,
//   sus_cnes_count, sus_total_avg, sus_per_capita_scaled,
//   priv_cnes_count, priv_total_avg, priv_per_capita_scaled,
//   per_capita_scale_pow10 }
//
// `equipment_key` = "TIPEQUIP:CODEQUIP" (ex: "1:12" = RM, "4:42" = EEG).
// Pré-WP#6 a chave era só `codequip`, o que colapsava equipamentos de TIPEQUIPs
// diferentes que reusam o mesmo número (CODEQUIP=42 era mostrado como "RM"
// quando na verdade era Eletroencefalógrafo). Ver memory/feedback_cnes_codequip_bug.
//
// User selects 1+ equipment_keys (multi-select). Front re-aggregates client-side.

import { useEffect, useMemo, useState } from 'react';
import PageHeader                    from '../components/PageHeader';
import Panel                         from '../components/Panel';
import KpiCard                       from '../components/KpiCard';
import BrazilMap                     from '../components/BrazilMap';
import StateRanking                  from '../components/StateRanking';
import EvolutionStackedComposed      from '../components/charts/EvolutionStackedComposed';
import DownloadActions               from '../components/DownloadActions';
import TechBadges                    from '../components/TechBadges';
import ScoreCard                     from '../components/ScoreCard';
import { PARECER_EQUIPAMENTOS }      from '../data/pareceres';
import { useTheme }                  from '../hooks/useTheme';
import { loadGold }                  from '../lib/data';
import { COLORSCALES }               from '../lib/scales';
import { fmtCompact, fmtDec1, fmtInt, fmtPct } from '../lib/format';
import { exportToXlsx, exportChartsAsZip } from '../lib/exporters';

const METRICS = {
  per_million: { label: 'Equip. por milhão de hab.', short: 'eq/Mhab',  fmt: fmtDec1 },
  total:       { label: 'Total de equipamentos',     short: 'equip.',  fmt: fmtDec1 },
  cnes:        { label: 'Estabelecimentos com equip.', short: 'estab.', fmt: fmtInt  },
};

const SETORES = {
  todos: { label: 'Todos',         color: '#1d4ed8', colorDark: '#60a5fa' },
  sus:   { label: 'Público (SUS)', color: '#1d4ed8', colorDark: '#60a5fa' },
  priv:  { label: 'Privado',       color: '#be185d', colorDark: '#f472b6' },
};

const MIN_YEAR        = 2005;
const DEFAULT_METRIC  = 'per_million';
const DEFAULT_SETOR   = 'todos';
const DEFAULT_COLOR   = 'Cividis';
// Default = Ressonância Magnética. Chave canônica TIPEQUIP=1, CODEQUIP=12
// (catálogo oficial DATASUS — cnes2.datasus.gov.br/Mod_Ind_Equipamento.asp).
// Pré-correção, esse default era ['42'] — que era Eletroencefalógrafo.
const DEFAULT_EQUIPMENT_KEYS = ['1:12'];

// Garantir compatibilidade com gold legado (sem equipment_key).
// Se a row não tem equipment_key, sintetiza a partir de tipequip:codequip,
// caindo de volta pra só codequip se tipequip também não existir (legacy).
function rowKey(r) {
  if (r.equipment_key) return r.equipment_key;
  if (r.tipequip != null) return `${r.tipequip}:${r.codequip}`;
  return String(r.codequip);
}

function aggCols(sector) {
  if (sector === 'sus')  return { total: 'sus_total_avg',  cnes: 'sus_cnes_count'  };
  if (sector === 'priv') return { total: 'priv_total_avg', cnes: 'priv_cnes_count' };
  return { total: 'total_avg', cnes: 'cnes_count' };
}

export default function Equipamentos() {
  const { theme } = useTheme();
  const [rows, setRows]                 = useState(null);
  const [error, setError]               = useState(null);
  const [metricKey, setMetricKey]       = useState(DEFAULT_METRIC);
  const [setor, setSetor]               = useState(DEFAULT_SETOR);
  const [year, setYear]                 = useState(null);
  const [colorscale, setColorscale]     = useState(DEFAULT_COLOR);
  const [selectedKeys, setSelectedKeys] = useState(DEFAULT_EQUIPMENT_KEYS);

  useEffect(() => {
    loadGold('gold_equipamentos_estados_ano.json')
      .then((all) => {
        const filtered = all.filter((r) => r.ano >= MIN_YEAR);
        setRows(filtered);
        const last = Math.max(...filtered.map((r) => r.ano));
        setYear(String(last));
        // Backward-compat: se a primeira row é gold legado (só `codequip`),
        // ajusta o default selection do '1:12' para o legacy '42' para
        // não bater em 0 rows. Só dispara antes do refresh do pipeline.
        if (filtered.length > 0 && !filtered[0].equipment_key && filtered[0].tipequip == null) {
          setSelectedKeys(['42']);
        }
      })
      .catch((e) => setError(e.message));
  }, []);

  const metric = METRICS[metricKey];
  const setorLabel = SETORES[setor].label;

  const years = useMemo(
    () => (rows ? Array.from(new Set(rows.map((r) => r.ano))).sort() : []),
    [rows],
  );

  const equipmentOptions = useMemo(() => {
    if (!rows) return [];
    const totals = new Map();
    const names  = new Map();
    const cats   = new Map();
    for (const r of rows) {
      const k = rowKey(r);
      totals.set(k, (totals.get(k) || 0) + (r.total_avg || 0));
      if (!names.has(k)) names.set(k, r.equipment_name);
      if (!cats.has(k))  cats.set(k, r.equipment_category || '');
    }
    return Array.from(totals.entries())
      .sort((a, b) => b[1] - a[1])
      .map(([key]) => ({
        key,
        name: names.get(key) || `Cód. ${key}`,
        category: cats.get(key) || '',
      }));
  }, [rows]);

  const rowsForCurrentYear = useMemo(() => {
    if (!rows || !year) return [];
    const yNum = Number(year);
    const sel  = new Set(selectedKeys);
    return rows.filter((r) => r.ano === yNum && sel.has(rowKey(r)));
  }, [rows, year, selectedKeys]);

  const filtered = useMemo(() => {
    if (!rowsForCurrentYear.length) return [];
    const byUf = new Map();
    for (const r of rowsForCurrentYear) {
      if (!byUf.has(r.estado)) byUf.set(r.estado, []);
      byUf.get(r.estado).push(r);
    }
    const cols = aggCols(setor);
    return Array.from(byUf.entries()).map(([uf, rs]) => {
      const total = rs.reduce((s, r) => s + (r[cols.total] || 0), 0);
      const cnes  = rs.reduce((s, r) => s + (r[cols.cnes]  || 0), 0);
      const pop   = rs[0]?.populacao || 0;
      const value = metricKey === 'per_million' ? (pop > 0 ? (total / pop) * 1e6 : 0)
                  : metricKey === 'total'        ? total
                  :                                 cnes;
      return { uf, value };
    });
  }, [rowsForCurrentYear, setor, metricKey]);

  const ranking = useMemo(() => [...filtered].sort((a, b) => b.value - a.value), [filtered]);

  const kpis = useMemo(() => {
    if (!rowsForCurrentYear.length) {
      return { y: null, total: 0, sus: 0, priv: 0, cnes: 0, susShare: 0, privShare: 0,
               yoyTotal: null, prevYear: null };
    }
    const y = Number(year);
    const sumT = (rs, col) => rs.reduce((s, r) => s + (r[col] || 0), 0);
    const total = sumT(rowsForCurrentYear, 'total_avg');
    const sus   = sumT(rowsForCurrentYear, 'sus_total_avg');
    const priv  = sumT(rowsForCurrentYear, 'priv_total_avg');
    const cnes  = sumT(rowsForCurrentYear, 'cnes_count');
    const prevYear = years.includes(y - 1) ? y - 1 : null;
    let yoyTotal = null;
    if (prevYear != null) {
      const sel = new Set(selectedKeys);
      const prev = rows.filter((r) => r.ano === prevYear && sel.has(rowKey(r)));
      const totalPrev = sumT(prev, 'total_avg');
      if (totalPrev > 0) yoyTotal = (total - totalPrev) / totalPrev;
    }
    return {
      y, total, sus, priv, cnes,
      susShare:  total > 0 ? sus  / total : 0,
      privShare: total > 0 ? priv / total : 0,
      yoyTotal, prevYear,
    };
  }, [rowsForCurrentYear, year, years, rows, selectedKeys]);

  const evolutionData = useMemo(() => {
    if (!rows) return [];
    const sel = new Set(selectedKeys);
    return years.map((y) => {
      const yr = rows.filter((r) => r.ano === y && sel.has(rowKey(r)));
      const susT  = yr.reduce((s, r) => s + (r.sus_total_avg  || 0), 0);
      const privT = yr.reduce((s, r) => s + (r.priv_total_avg || 0), 0);
      const totalT = susT + privT;
      const setorT = setor === 'sus' ? susT : setor === 'priv' ? privT : totalT;
      const ufPop = new Map();
      for (const r of yr) if (!ufPop.has(r.estado)) ufPop.set(r.estado, r.populacao || 0);
      const popBR = Array.from(ufPop.values()).reduce((s, v) => s + v, 0);
      const ratio = popBR > 0 ? (setorT / popBR) * 1e6 : 0;
      return { year: String(y), sus: susT, priv: privT, ratio };
    });
  }, [rows, years, setor, selectedKeys]);

  if (error) return <div className="error-block">Erro ao carregar dados: {error}</div>;
  if (!rows) return <div className="loading-block">Carregando dados…</div>;

  const titleSubject = selectedKeys.length === 1
    ? equipmentOptions.find((e) => e.key === selectedKeys[0])?.name || 'Equipamento'
    : `${selectedKeys.length} equipamentos selecionados`;

  return (
    <>
      <PageHeader
        eyebrow="Vertical · saúde · equipamentos médicos (CNES)"
        title="Equipamentos médicos no Brasil"
        subtitle={`${titleSubject} — DATASUS/CNES (2005–${Math.max(...years)}). População via IBGE/SIDRA.`}
        right={
          <div className="header-right-row">
            <TechBadges />
            <DownloadActions
              onExportXlsx={() => exportToXlsx('mirante-equipamentos', { 'equipamentos_uf_ano': rows })}
              onExportPng={() => exportChartsAsZip('mirante-equipamentos')}
            />
          </div>
        }
      />

      <ScoreCard parecer={PARECER_EQUIPAMENTOS} />

      <ArticleSection />

      <div className="kpiRow" data-export-id="equipamentos-kpis">
        <KpiCard label={`Total · ${kpis.y ?? '—'}`}             value={fmtInt(kpis.total)} sub="equipamentos somados" color={theme === 'dark' ? '#60a5fa' : '#1d4ed8'} />
        <KpiCard label={`SUS · ${kpis.y ?? '—'}`}               value={fmtInt(kpis.sus)}   sub={`${fmtPct(kpis.susShare)} do total`} color={SETORES.sus.color} />
        <KpiCard label={`Privado · ${kpis.y ?? '—'}`}           value={fmtInt(kpis.priv)}  sub={`${fmtPct(kpis.privShare)} do total`} color={SETORES.priv.color} />
        <KpiCard label={`Estabelecimentos · ${kpis.y ?? '—'}`}  value={fmtInt(kpis.cnes)}  sub="com pelo menos 1 unidade" color={theme === 'dark' ? '#34d399' : '#059669'} />
        {kpis.prevYear != null && kpis.yoyTotal != null && (
          <KpiCard
            label="Crescimento YoY"
            value={<YoyValue value={kpis.yoyTotal} />}
            sub={`${kpis.prevYear} → ${kpis.y}`}
            color={theme === 'dark' ? '#34d399' : '#059669'}
          />
        )}
      </div>

      <div className="layout">
        <div className="row row-controls-bar">
          <Panel label="Filtros & dados" sub="DATASUS · IBGE">
            <div className="controls">
              <div className="control" style={{ gridTemplateColumns: '90px 1fr', alignItems: 'flex-start' }}>
                <label htmlFor="equip" style={{ paddingTop: 6 }}>Equipamento</label>
                <EquipmentMultiSelect
                  options={equipmentOptions}
                  selected={selectedKeys}
                  onChange={setSelectedKeys}
                />
              </div>

              <div className="control">
                <label htmlFor="metric">Métrica</label>
                <select id="metric" value={metricKey} onChange={(e) => setMetricKey(e.target.value)}>
                  {Object.entries(METRICS).map(([k, m]) => (
                    <option key={k} value={k}>{m.label}</option>
                  ))}
                </select>
              </div>

              <div className="control">
                <label htmlFor="setor">Setor</label>
                <select id="setor" value={setor} onChange={(e) => setSetor(e.target.value)}>
                  <option value="todos">Todos</option>
                  <option value="sus">Público (SUS)</option>
                  <option value="priv">Privado</option>
                </select>
              </div>

              <div className="control">
                <label htmlFor="year">Ano</label>
                <select id="year" value={year || ''} onChange={(e) => setYear(e.target.value)}>
                  {years.map((y) => (<option key={y} value={y}>{y}</option>))}
                </select>
              </div>

              <div className="metaBlock">
                <b>Fonte:</b> DATASUS — Cadastro Nacional de Estabelecimentos de Saúde<br />
                <b>SUS:</b> IND_SUS = 1 · <b>Privado:</b> IND_SUS = 0<br />
                <b>Multi-seleção:</b> totais somam, per capita recalcula
              </div>
            </div>
          </Panel>

          <Panel
            label="Evolução nacional"
            sub={`${titleSubject} · ${setorLabel} + por milhão de hab.`}
            exportId="equipamentos-evolucao"
          >
            <EvolutionStackedComposed
              data={evolutionData}
              setor={setor}
              theme={theme}
              fmtBar={(v) => fmtCompact(v)}
              fmtLine={(v) => fmtDec1(v)}
              yLeftLabel="Equipamentos (média anual)"
              yRightLabel="por milhão"
              xLabel="Ano"
              height={340}
            />
          </Panel>
        </div>

        <div className="row row-ranking-map">
          <Panel
            label="Ranking por UF"
            sub={`${metric.label} · ${setorLabel} · ${year}`}
            exportId="equipamentos-ranking-uf"
          >
            <StateRanking
              rows={ranking}
              format={metric.fmt}
              accentColor={
                setor === 'priv'
                  ? (theme === 'dark' ? SETORES.priv.colorDark : SETORES.priv.color)
                  : (theme === 'dark' ? SETORES.sus.colorDark  : SETORES.sus.color)
              }
            />
          </Panel>

          <Panel
            label="Distribuição geográfica"
            exportId="equipamentos-mapa-uf"
            right={
              <div className="mapControls">
                <label htmlFor="colorscale">Cores</label>
                <select id="colorscale" value={colorscale} onChange={(e) => setColorscale(e.target.value)}>
                  {COLORSCALES.map((c) => (<option key={c.value} value={c.value}>{c.label}</option>))}
                </select>
              </div>
            }
          >
            <BrazilMap
              data={filtered}
              colorscale={colorscale}
              theme={theme}
              hoverFmt={metric.fmt}
              unit={metric.short}
            />
          </Panel>
        </div>
      </div>

      <Footer />
    </>
  );
}

function EquipmentMultiSelect({ options, selected, onChange }) {
  const [open, setOpen]   = useState(false);
  const [query, setQuery] = useState('');
  const sel = new Set(selected);

  const filtered = options.filter((o) =>
    !query
      || o.name.toLowerCase().includes(query.toLowerCase())
      || o.key.includes(query)
      || (o.category || '').toLowerCase().includes(query.toLowerCase()),
  );

  const toggle = (key) => {
    const next = sel.has(key)
      ? selected.filter((k) => k !== key)
      : [...selected, key];
    if (next.length > 0) onChange(next);   // sempre manter ao menos 1
  };

  const summary = selected.length === 1
    ? options.find((o) => o.key === selected[0])?.name || selected[0]
    : `${selected.length} selecionados`;

  return (
    <div className="multi-select">
      <button type="button" className="multi-select-trigger" onClick={() => setOpen((v) => !v)}>
        <span>{summary}</span>
        <span className="multi-select-caret">▾</span>
      </button>
      {open && (
        <div className="multi-select-popover">
          <input
            type="text"
            placeholder="Buscar (nome, código ou categoria)…"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            className="multi-select-search"
            autoFocus
          />
          <div className="multi-select-options">
            {filtered.map((o) => (
              <label key={o.key} className="multi-select-option">
                <input
                  type="checkbox"
                  checked={sel.has(o.key)}
                  onChange={() => toggle(o.key)}
                />
                <span>
                  {o.name}
                  {o.category && (
                    <span style={{ display: 'block', fontSize: 10, color: 'var(--faint)', marginTop: 1 }}>
                      {o.category}
                    </span>
                  )}
                </span>
                <span className="multi-select-code">{o.key}</span>
              </label>
            ))}
          </div>
          <button type="button" className="multi-select-close" onClick={() => setOpen(false)}>Fechar</button>
        </div>
      )}
    </div>
  );
}

function YoyValue({ value }) {
  if (value == null || !Number.isFinite(value)) return <span className="muted">—</span>;
  const up    = value >= 0;
  const sign  = up ? '+' : '';
  const arrow = up ? '▲' : '▼';
  return (
    <span className={`kpiYoy ${up ? 'up' : 'down'}`}>
      <span className="arrow">{arrow}</span>
      <span>{sign}{fmtPct(value)}</span>
    </span>
  );
}

function Footer() {
  return (
    <footer className="footer panel" style={{ marginTop: 18 }}>
      <div className="footerSection">
        <div className="footerHeading">Fontes</div>
        <div className="footerSource">
          <a href="https://datasus.saude.gov.br/transferencia-de-arquivos/" target="_blank" rel="noreferrer">
            DATASUS — CNES/EQ (Equipamentos)
          </a>
          <span className="footerDesc">Cadastro Nacional de Estabelecimentos de Saúde — equipamentos por estabelecimento, mensal, jan/2005 em diante</span>
        </div>
        <div className="footerSource">
          <a href="https://sidra.ibge.gov.br/tabela/6579" target="_blank" rel="noreferrer">IBGE SIDRA — Tabela 6579</a>
          <span className="footerDesc">População residente estimada por UF (variável 9324)</span>
        </div>
        <div className="footerNote">
          Pipeline: bronze (FTP DATASUS, 6.6K .dbc) → silver (UF × Ano × CODEQUIP, split SUS/Privado) → gold (mesma granularidade, com nome do equipamento). Front re-agrega quando o usuário seleciona múltiplos.
        </div>
      </div>

      <div className="footerSection">
        <div className="footerHeading">Notas técnicas</div>
        <div style={{ fontSize: 12, color: 'var(--muted)', lineHeight: 1.7 }}>
          Quando você seleciona <b>2+ equipamentos</b>, o "Total" é a soma direta dos averages. O "por milhão" é recomputado como (soma de equipamentos) / população × 10⁶ — não é a soma das taxas individuais. Isso garante comparação correta entre UFs com tamanhos diferentes.
        </div>
      </div>

      <div className="footerSection">
        <div className="footerHeading">Limitações da fonte</div>
        <div style={{ fontSize: 12, color: 'var(--muted)', lineHeight: 1.7 }}>
          Caveats estruturais do CNES (não do pipeline) que valem ler antes de
          usar os números pra decisão clínica ou orçamentária:
          <ul style={{ marginTop: 6, marginBottom: 0, paddingLeft: 18 }}>
            <li>
              <b>Cadastrado ≠ operacional.</b> O CNES conta equipamento{' '}
              <i>cadastrado</i>, não necessariamente em uso. O DBF separa{' '}
              <code>QT_EXIST</code> (cadastrado) de <code>QT_USO</code> (em
              uso); este painel usa <code>QT_EXIST</code>.
            </li>
            <li>
              <b>Possível dupla contagem por estabelecimento.</b> A mesma
              máquina física pode, em casos raros, ser registrada por 2
              estabelecimentos diferentes (CNES distintos compartilhando
              equipamento).
            </li>
            <li>
              <b>Latência cadastral.</b> Equipamento cadastrado em mês X pode
              ter sido instalado fisicamente em mês X−3 a X−6 — o CNES não
              expõe data-de-instalação granular.
            </li>
            <li>
              <b>Nenhum dado sobre estado/idade do parque.</b> CNES não
              registra ano-modelo, vida útil restante, manutenção pendente
              ou utilização efetiva (frequência de uso).
            </li>
          </ul>
          Esses são limites da fonte primária (DATASUS), não do nosso
          processamento. Para análise de tendência (comparação entre UFs,
          evolução temporal, % SUS vs Privado), os números são
          confiáveis. Para uso operacional (planejamento de manutenção,
          alocação de turnos), seria necessário cruzamento com produção
          (SIH-RD, SIA-RD).
        </div>
      </div>
    </footer>
  );
}

// ─── Working Paper #5 — Equipamentos × Parkinson (Rolim + Chalhoub) ─────
// Artigo focado em RM (codequip=42) no diagnóstico diferencial da Doença
// de Parkinson. Coautoria com Alexandre Maciel Rolim (manuscrito original
// epidemiológico, abr/2026).
function ArticleSection() {
  const base = import.meta.env.BASE_URL || '/';
  const pdfUrl     = `${base}articles/equipamentos-rm-parkinson.pdf`.replace(/\/{2,}/g, '/');
  const texUrl     = `${base}articles/equipamentos-rm-parkinson.tex`.replace(/\/{2,}/g, '/');
  const overleafUrl = 'https://www.overleaf.com/docs?snip_uri=' +
    encodeURIComponent(`https://leonardochalhoub.github.io${texUrl}`);

  return (
    <section className="emendas-abstract no-print" style={{ marginBottom: 14 }}>
      <div className="doc-block">
        <div className="kicker">Working Paper n. 4 — Mirante dos Dados</div>
        <p style={{ marginTop: 6, fontSize: 13.5 }}>
          <b>"Análise estatística da prevalência da Doença de Parkinson no
          Brasil: desafios, tecnologias de neuroimagem e perspectivas de
          políticas públicas"</b> — coautoria com <b>Alexandre Maciel
          Rolim</b> (manuscrito original epidemiológico, abr/2026). O
          artigo combina os achados do ELSI-Brazil (prevalência de DP de
          0,84% em brasileiros 50+, projeção de 1,25 milhão de casos até
          2060) com análise atualizada e reproduzível da infraestrutura
          de RM no SUS via microdados CNES 2013–2025 (filtro{' '}
          <code>codequip=42</code>): 10.079 aparelhos em 2025 (47,2/Mhab,
          acima da mediana OCDE), com iniquidade regional severa que
          NÃO se reduziu apesar do crescimento agregado.
        </p>
        <div className="doc-actions">
          <a className="doc-toggle doc-toggle-primary"
             href={pdfUrl} target="_blank" rel="noreferrer"
             title="Abrir PDF em nova aba (visualizador nativo do navegador)">
            📖 Ler artigo (PDF)
          </a>
          <a className="doc-toggle"
             href={pdfUrl} download="Mirante-Equipamentos-RM-Parkinson-Rolim-Chalhoub-2026.pdf"
             title="PDF compilado em LaTeX, padrão ABNT">
            ⤓ Baixar PDF (ABNT)
          </a>
          <a className="doc-toggle"
             href={texUrl} download="equipamentos-rm-parkinson.tex"
             title="Fonte LaTeX (.tex)">
            ⤓ Baixar fonte (.tex)
          </a>
          <a className="doc-toggle"
             href={overleafUrl} target="_blank" rel="noreferrer"
             title="Compilação online em 1 clique no Overleaf">
            ↗ Abrir no Overleaf
          </a>
        </div>
        <p style={{ fontSize: 11, color: 'var(--muted)', marginTop: 10, marginBottom: 0, lineHeight: 1.5 }}>
          A vertical Equipamentos suporta multi-seleção entre 99
          códigos CNES; este artigo extrai o subconjunto{' '}
          <code>codequip=42</code> (Ressonância Magnética) e cruza com
          carga estimada de DP por UF.
        </p>
      </div>
    </section>
  );
}

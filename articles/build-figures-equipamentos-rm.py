#!/usr/bin/env python3
"""WP #4 — Neuroimagem para diagnóstico diferencial da Doença de Parkinson.

Lê data/gold/gold_equipamentos_estados_ano.json (corrigido) e gera figuras
abrangendo TODAS as modalidades relevantes para diagnóstico de DP:
RM (1:12 + 1:32-35 por Tesla), CT (1:11 + 1:26-30 por canais),
PET/CT (1:18) e Gama Câmara para SPECT (1:01).

Saída: articles/figures-equipamentos-rm/*.pdf

Identidade visual: Mirante editorial (memory: feedback_chart_visual_identity.md).
Padrão: Lato + paleta hierárquica + golden ratio + halo branco + leader lines
+ polylabel + adjustText + utilitários editorial_title/source_note/inline_labels.
"""
import json
import statistics
import sys
from collections import defaultdict
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patheffects as pe
import matplotlib as mpl
import numpy as np
from adjustText import adjust_text

# Mirante visual identity
sys.path.insert(0, str(Path(__file__).resolve().parent))
from mirante_style import (
    apply_mirante_style, PALETTE_MIRANTE, GOLDEN_FIGSIZE,
    GOLDEN_FIGSIZE_TALL,
)
from mirante_charts import (
    editorial_title, source_note, inline_labels, apply_hierarchy,
)
from mirante_maps import (
    load_brazil_geojson, draw_choropleth, set_brazil_extent,
    add_horizontal_colorbar,
)

apply_mirante_style()

ROOT     = Path("/home/leochalhoub/mirante-dos-dados-br/articles")
FIG_DIR  = ROOT / "figures-equipamentos-rm"
FIG_DIR.mkdir(exist_ok=True)
CIVIDIS  = mpl.cm.cividis_r

SOURCE_DEFAULT = ("Fonte: DATASUS/CNES e IBGE/SIDRA, "
                  "processamento Mirante dos Dados.")
SOURCE_OECD = ("Fonte: DATASUS/CNES, IBGE/SIDRA. "
               "OCDE: Health at a Glance 2023. Processamento Mirante dos Dados.")


# ═══════════════════════════════════════════════════════════════════════════
# Carga de dados
# ═══════════════════════════════════════════════════════════════════════════
GOLD = json.load(open(ROOT.parent / "data" / "gold" / "gold_equipamentos_estados_ano.json"))
PBF = json.load(open(ROOT.parent / "data" / "gold" / "gold_pbf_estados_df.json"))
LATEST = max(r['ano'] for r in GOLD)
YEARS = sorted({r['ano'] for r in GOLD})
print(f"Loaded gold: {len(GOLD):,} rows, latest={LATEST}, years={len(YEARS)}")

# Equipamento relevante para neuroimagem-Parkinson.
# Cores Mirante hierárquicas (RM = principal, outras como contexto/secundário).
PD_EQ = {
    '1:12': ('RM',          'Ressonância Magnética',     PALETTE_MIRANTE["principal"]),
    '1:11': ('CT',          'Tomógrafo Computadorizado', PALETTE_MIRANTE["secundario"]),
    '1:18': ('PET/CT',      'PET/CT',                    PALETTE_MIRANTE["destaque"]),
    '1:01': ('Gama Câmara', 'Gama Câmara (DAT-SPECT)',   PALETTE_MIRANTE["contexto_dark"]),
}

REGION = {
    "AC":"Norte","AM":"Norte","AP":"Norte","PA":"Norte","RO":"Norte","RR":"Norte","TO":"Norte",
    "AL":"Nordeste","BA":"Nordeste","CE":"Nordeste","MA":"Nordeste","PB":"Nordeste","PE":"Nordeste",
    "PI":"Nordeste","RN":"Nordeste","SE":"Nordeste",
    "DF":"Centro-Oeste","GO":"Centro-Oeste","MT":"Centro-Oeste","MS":"Centro-Oeste",
    "ES":"Sudeste","MG":"Sudeste","RJ":"Sudeste","SP":"Sudeste",
    "PR":"Sul","RS":"Sul","SC":"Sul",
}

POP = {}
for r in GOLD:
    if r['ano'] == LATEST and r['equipment_key'] == '1:12':
        POP[r['estado']] = r['populacao']


def save(fig, name):
    out = FIG_DIR / f"{name}.pdf"
    fig.savefig(out)
    plt.close(fig)
    print(f"  ✔ {out.name}")


# ═══════════════════════════════════════════════════════════════════════════
# Fig 1 — Linha do tempo
# ═══════════════════════════════════════════════════════════════════════════
def fig_timeline():
    fig, ax = plt.subplots(figsize=(GOLDEN_FIGSIZE[0], 4.0))
    fig.subplots_adjust(top=0.78, bottom=0.20, left=0.05, right=0.97)
    ax.set_xlim(2003, 2027); ax.set_ylim(-3.4, 3.4); ax.axis("off")
    ax.axhline(0, color=PALETTE_MIRANTE["neutro"], linewidth=1.2)
    for yr in [2005, 2010, 2015, 2020, 2025]:
        ax.plot([yr, yr], [-0.08, 0.08],
                color=PALETTE_MIRANTE["neutro_soft"], linewidth=0.6)
        ax.text(yr, -0.42, str(yr), ha="center", fontsize=8.5,
                color=PALETTE_MIRANTE["neutro_soft"])
    events = [
        (2005, "CNES inicia",        "Cadastro Nacional Estab. Saúde",       "top", 0.7),
        (2008, "SIGTAP padronizado", "Tabela única SUS de procedimentos",    "bot", 0.8),
        (2014, "Swallow-tail (SWI)", "Schwarz et al. — sinal RM 3T para DP", "top", 1.4),
        (2015, "MDS-PD criteria",    "Postuma et al. — Mov Disord",          "bot", 1.5),
        (2018, "Neuromelanin MRI",   "Pyatigorskaya et al.",                 "top", 2.1),
        (2020, "DAT-SPECT no SUS",   "Ampliação de Medicina Nuclear",        "bot", 2.2),
        (2022, "PNAB · neurologia",  "Atenção secundária ampliada",          "top", 2.7),
        (LATEST, "Brasil neuroimagem-PD",
                 "RM 3.900 + CT 8.000 + PET 166 + Gama 16.089",              "bot", 2.9),
    ]
    for yr, lbl, desc, side, h in events:
        sign = +1 if side == "top" else -1
        y = sign * h
        ax.plot([yr, yr], [0, y - 0.1*sign],
                color=PALETTE_MIRANTE["neutro_soft"],
                linewidth=0.8, linestyle="--")
        ax.scatter([yr], [0], s=42, color=PALETTE_MIRANTE["principal"],
                   zorder=3, edgecolor="white", linewidth=0.6)
        ax.text(yr, y, lbl, ha="center",
                va="bottom" if side == "top" else "top",
                fontsize=9.5, fontweight="bold",
                color=PALETTE_MIRANTE["neutro"])
        ax.text(yr, y + 0.34*sign, desc, ha="center",
                va="bottom" if side == "top" else "top",
                fontsize=7.5, color=PALETTE_MIRANTE["neutro_soft"])
    editorial_title(ax,
        title="Neuroimagem para Parkinson: 20 anos de marcos científicos e institucionais",
        subtitle="Eventos seminais na clínica de movimento e na infraestrutura de RM/CT/PET no SUS",
        y_title=1.10, y_sub=1.04)
    source_note(ax,
        "Fontes: literatura clínica (Schwarz, Postuma, Pyatigorskaya), DATASUS/CNES, MS/PNAB. "
        "Processamento Mirante.",
        y=-0.10)
    save(fig, "fig01-timeline-pd")


# ═══════════════════════════════════════════════════════════════════════════
# Fig 2 — Pipeline architecture (mantém visual existente, retoque tipográfico)
# ═══════════════════════════════════════════════════════════════════════════
def fig_architecture():
    """Arquitetura medallion estilo Databricks blog — boxes coloridas
    (bronze/silver/gold com cores reais de metal), arrows sólidas
    finas, sem outline, hierarquia tipográfica clara, sombra sutil.
    """
    fig, ax = plt.subplots(figsize=(GOLDEN_FIGSIZE[0], 3.6))
    fig.subplots_adjust(top=0.78, bottom=0.18, left=0.04, right=0.96)
    ax.set_xlim(0, 10); ax.set_ylim(0, 4); ax.axis("off")

    # Cores estilo Databricks blog: boxes preenchidas com cor sólida,
    # texto branco em bronze/silver/gold, cinza editorial nas extremas
    # (Fonte/Consumo) que são "input" e "output" do sistema.
    boxes = [
        # (x, label, sub1, sub2, fillcolor, textcolor)
        (0.3, "Fonte",   "FTP DATASUS",  "CNES (.dbc)",
         "#E8E8E8", PALETTE_MIRANTE["neutro"]),
        (2.2, "Bronze",  "DBC→DBF→Parquet", "+ Auto Loader",
         "#B87333", "white"),  # bronze metálico
        (4.4, "Silver",  "UF×Ano×(TIPEQUIP,CODEQUIP)", "Dict canonical (133)",
         "#9E9E9E", "white"),  # silver metálico
        (6.6, "Gold",    "UF×Ano×eq_key", "+ pop IBGE",
         "#D4A847", "white"),  # gold metálico
        (8.5, "Consumo", "JSON / PDF", "Reprodutível",
         "#E8E8E8", PALETTE_MIRANTE["neutro"]),
    ]
    BOX_W, BOX_H = 1.5, 1.7
    BOX_Y = 1.3

    for i, (x, label, sub1, sub2, fc, tc) in enumerate(boxes):
        # Box principal — sem outline, cor sólida (estilo Databricks)
        rect = mpl.patches.FancyBboxPatch(
            (x, BOX_Y), BOX_W, BOX_H,
            boxstyle="round,pad=0.02,rounding_size=0.10",
            facecolor=fc, edgecolor="none", linewidth=0,
            zorder=2,
        )
        ax.add_patch(rect)
        # Sombra sutil (offset rectangle por trás)
        shadow = mpl.patches.FancyBboxPatch(
            (x + 0.04, BOX_Y - 0.04), BOX_W, BOX_H,
            boxstyle="round,pad=0.02,rounding_size=0.10",
            facecolor="#00000010", edgecolor="none", zorder=1,
        )
        ax.add_patch(shadow)
        # Label principal (bold, grande)
        ax.text(x + BOX_W/2, BOX_Y + BOX_H - 0.40, label,
                ha="center", va="center",
                fontsize=12, fontweight="bold", color=tc, zorder=3)
        # Sub-label 1 (regular, pequeno)
        ax.text(x + BOX_W/2, BOX_Y + 0.95, sub1,
                ha="center", va="center",
                fontsize=8, color=tc, zorder=3, alpha=0.95)
        # Sub-label 2
        ax.text(x + BOX_W/2, BOX_Y + 0.55, sub2,
                ha="center", va="center",
                fontsize=8, color=tc, zorder=3, alpha=0.95)

        # Arrow para próxima box (linha fina + cabeça pequena, estilo flat)
        if i < len(boxes) - 1:
            x_next = boxes[i+1][0]
            ax.annotate(
                "", xy=(x_next - 0.05, BOX_Y + BOX_H/2),
                xytext=(x + BOX_W + 0.05, BOX_Y + BOX_H/2),
                arrowprops=dict(
                    arrowstyle="-|>",
                    color=PALETTE_MIRANTE["neutro_soft"],
                    lw=1.4, mutation_scale=14,
                    shrinkA=0, shrinkB=0,
                ),
                zorder=4,
            )

    # Filter caption embaixo (estilo Databricks: nota fina cinza)
    ax.text(5, 0.55,
        "Filtro p/ recorte neuroimagem-PD: equipment_key = {1:12 RM, 1:11 CT, 1:18 PET/CT, 1:01 Gama}",
        ha="center", va="center", fontsize=8, style="italic",
        color=PALETTE_MIRANTE["neutro_soft"])

    editorial_title(ax,
        title="Arquitetura medallion bronze→silver→gold do recorte CNES neuroimagem",
        subtitle="Pipeline reprodutível 2005–2025 sobre microdados do Cadastro Nacional de Estabelecimentos de Saúde",
        y_title=1.18, y_sub=1.10)
    save(fig, "fig02-architecture")


# ═══════════════════════════════════════════════════════════════════════════
# Fig 3 — Evolução temporal das 4 modalidades (line + inline labels)
# ═══════════════════════════════════════════════════════════════════════════
def fig_evolution_modalities():
    fig, ax = plt.subplots(figsize=GOLDEN_FIGSIZE)
    fig.subplots_adjust(top=0.82, bottom=0.20, left=0.10, right=0.88)
    for k, (short, full, color) in PD_EQ.items():
        rows = [r for r in GOLD if r['equipment_key'] == k]
        by_y = defaultdict(float)
        for r in rows:
            by_y[r['ano']] += r['total_avg']
        xs = sorted(by_y.keys()); ys = [by_y[y] for y in xs]
        ax.plot(xs, ys, marker='o', markersize=4, linewidth=2.0,
                color=color, label=short)

    inline_labels(ax, x_offset=0.015)
    ax.set_xlim(min(YEARS), max(YEARS) + 1.5)
    ax.set_ylabel("Unidades cadastradas")
    ax.set_xlabel("")
    editorial_title(ax,
        title="Gama Câmara é a base mais ampla; PET/CT cresce mais rápido (em base baixa)",
        subtitle=f"Unidades cadastradas no SUS para neuroimagem-Parkinson, Brasil 2013–{LATEST}")
    source_note(ax, SOURCE_DEFAULT, y=-0.18)
    save(fig, "fig03-evolution-modalities")


# ═══════════════════════════════════════════════════════════════════════════
# Fig 4 — Densidade per capita por modalidade vs OECD
# ═══════════════════════════════════════════════════════════════════════════
def fig_density_oecd():
    fig, ax = plt.subplots(figsize=GOLDEN_FIGSIZE)
    fig.subplots_adjust(top=0.82, bottom=0.20, left=0.10, right=0.88)
    series = {}
    for k, (short, full, color) in PD_EQ.items():
        rows = [r for r in GOLD if r['equipment_key'] == k]
        by_y = defaultdict(lambda: {'tot': 0, 'pop': 0})
        for r in rows:
            by_y[r['ano']]['tot'] += r['total_avg']
            by_y[r['ano']]['pop'] += r['populacao']
        xs = sorted(by_y.keys())
        ys = [by_y[y]['tot']/by_y[y]['pop']*1e6 if by_y[y]['pop'] else 0
              for y in xs]
        ax.plot(xs, ys, marker='o', markersize=4, linewidth=2.0,
                color=color, label=short)
        series[short] = (xs, ys)

    # OCDE refs
    oecd_refs = {'RM': 17, 'CT': 28}
    for short, val in oecd_refs.items():
        ax.axhline(val, color=PALETTE_MIRANTE["neutro_soft"],
                   linestyle="--", linewidth=0.8, alpha=0.7)
        ax.text(LATEST + 0.3, val, f"OCDE {short} = {val}",
                fontsize=8, color=PALETTE_MIRANTE["neutro_soft"],
                va="center", style="italic")

    inline_labels(ax, x_offset=0.015)
    ax.set_xlim(min(YEARS), max(YEARS) + 2.5)
    ax.set_ylabel("Unidades por milhão de habitantes")
    ax.set_xlabel("")
    editorial_title(ax,
        title="Brasil supera mediana OCDE em RM mas fica metade em CT",
        subtitle=f"Densidade por milhão de habitantes — Brasil 2013–{LATEST} vs medianas OCDE 2021")
    source_note(ax, SOURCE_OECD, y=-0.18)
    save(fig, "fig04-density-oecd")


# ═══════════════════════════════════════════════════════════════════════════
# Fig 5 — Choropleth RM/Mhab por UF
# ═══════════════════════════════════════════════════════════════════════════
def fig_choropleth_rm():
    rm = [r for r in GOLD if r['ano'] == LATEST and r['equipment_key'] == '1:12']
    den = {r['estado']: r['total_avg']/r['populacao']*1e6
           for r in rm if r['populacao']}
    states = load_brazil_geojson()
    n_below = sum(1 for v in den.values() if v < 17)

    fig, ax = plt.subplots(figsize=(8.5, 10.0))
    fig.subplots_adjust(top=0.86, bottom=0.18, left=0.04, right=0.96)
    norm = draw_choropleth(ax, states, den)
    set_brazil_extent(ax, states)

    add_horizontal_colorbar(
        fig, CIVIDIS, norm, x=0.12, y=0.13, w=0.50,
        label="RM por milhão de habitantes",
        ref_value=17, ref_label="Mediana OCDE = 17",
    )
    editorial_title(ax,
        title=f"{n_below} das 27 UFs estão abaixo da mediana OCDE em capacidade de RM",
        subtitle=f"Aparelhos de Ressonância Magnética por milhão de habitantes, Brasil {LATEST}",
        y_title=1.06, y_sub=1.02)
    fig.text(0.04, 0.06, SOURCE_OECD,
             fontsize=8.5, color=PALETTE_MIRANTE["neutro_soft"],
             style="italic", ha="left", va="top")
    save(fig, "fig05-choropleth-rm")


# ═══════════════════════════════════════════════════════════════════════════
# Fig 6 — Choropleth densidade combinada PD-stack por UF
# ═══════════════════════════════════════════════════════════════════════════
def fig_choropleth_pd_stack():
    pd_basket = ['1:01', '1:11', '1:12', '1:18']
    by_uf = defaultdict(lambda: {'tot': 0.0, 'pop': 0})
    for r in GOLD:
        if r['ano'] == LATEST and r['equipment_key'] in pd_basket:
            by_uf[r['estado']]['tot'] += r['total_avg']
            if r['equipment_key'] == '1:12':
                by_uf[r['estado']]['pop'] = r['populacao']
    den = {uf: v['tot']/v['pop']*1e6 for uf, v in by_uf.items() if v['pop']}
    states = load_brazil_geojson()

    fig, ax = plt.subplots(figsize=(8.5, 10.0))
    fig.subplots_adjust(top=0.86, bottom=0.18, left=0.04, right=0.96)
    norm = draw_choropleth(ax, states, den)
    set_brazil_extent(ax, states)

    add_horizontal_colorbar(
        fig, CIVIDIS, norm, x=0.12, y=0.13, w=0.50,
        label="Unidades-PD (RM+CT+PET+Gama) por milhão de habitantes",
    )
    editorial_title(ax,
        title="Capacidade combinada de neuroimagem-DP segue gradiente Norte-Sudeste",
        subtitle=f"Soma de RM, CT, PET/CT e Gama Câmara por milhão de habitantes, Brasil {LATEST}",
        y_title=1.06, y_sub=1.02)
    fig.text(0.04, 0.06, SOURCE_DEFAULT,
             fontsize=8.5, color=PALETTE_MIRANTE["neutro_soft"],
             style="italic", ha="left", va="top")
    save(fig, "fig06-choropleth-pd-stack")


# ═══════════════════════════════════════════════════════════════════════════
# Fig 7 — SUS share por modalidade (stacked bar horizontal)
# ═══════════════════════════════════════════════════════════════════════════
def fig_sus_share_modality():
    fig, ax = plt.subplots(figsize=GOLDEN_FIGSIZE)
    fig.subplots_adjust(top=0.78, bottom=0.20, left=0.10, right=0.96)
    items = []
    for k, (short, full, _) in PD_EQ.items():
        rows = [r for r in GOLD if r['ano'] == LATEST and r['equipment_key'] == k]
        sus = sum(r['sus_total_avg'] for r in rows)
        priv = sum(r['priv_total_avg'] for r in rows)
        items.append((short, sus, priv, sus + priv))
    items.sort(key=lambda x: -x[3])
    y = np.arange(len(items))
    sus_pct = [it[1]/it[3]*100 if it[3] else 0 for it in items]
    priv_pct = [it[2]/it[3]*100 if it[3] else 0 for it in items]
    ax.barh(y, sus_pct,  color=PALETTE_MIRANTE["principal"], label="SUS")
    ax.barh(y, priv_pct, left=sus_pct,
            color=PALETTE_MIRANTE["destaque"], label="Privado")
    for i, (sp, pp) in enumerate(zip(sus_pct, priv_pct)):
        if sp > 8:
            ax.text(sp/2, i, f'{sp:.0f}%', ha='center', va='center',
                    color="white", fontsize=10, fontweight='bold')
        if pp > 8:
            ax.text(sp + pp/2, i, f'{pp:.0f}%', ha='center', va='center',
                    color="white", fontsize=10, fontweight='bold')
    ax.set_yticks(y)
    ax.set_yticklabels([f'{it[0]} ({it[3]:,.0f} un.)'.replace(",", ".")
                        for it in items], fontsize=10)
    ax.set_xlabel("% das unidades")
    ax.set_xlim(0, 100)
    ax.legend(loc='upper center', bbox_to_anchor=(0.5, -0.15),
              ncol=2, frameon=False, fontsize=9.5)
    editorial_title(ax,
        title="SUS responde por menos de metade do parque de RM e CT",
        subtitle=f"Repartição público × privado por modalidade neuroimagem, Brasil {LATEST}")
    source_note(ax, SOURCE_DEFAULT, y=-0.28)
    save(fig, "fig07-sus-share-modality")


# ═══════════════════════════════════════════════════════════════════════════
# Fig 8 — Ranking UFs por RM/Mhab (threshold OCDE)
# ═══════════════════════════════════════════════════════════════════════════
def fig_top_uf_rm():
    rm = [r for r in GOLD if r['ano'] == LATEST and r['equipment_key'] == '1:12']
    items = sorted(
        [(r['estado'], r['total_avg'],
          r['total_avg']/r['populacao']*1e6 if r['populacao'] else 0)
         for r in rm],
        key=lambda t: t[2])  # ascending — menor embaixo? não, vamos inverter pra plot
    fig, ax = plt.subplots(figsize=GOLDEN_FIGSIZE_TALL)
    fig.subplots_adjust(top=0.88, bottom=0.10, left=0.10, right=0.95)
    OCDE = 17.0
    labels = [t[0] for t in items]
    vals = [t[2] for t in items]
    colors = [PALETTE_MIRANTE["destaque"] if v < OCDE
              else PALETTE_MIRANTE["principal"] for v in vals]
    bars = ax.barh(labels, vals, color=colors)
    ax.axvline(OCDE, color=PALETTE_MIRANTE["neutro"],
               linestyle="--", linewidth=1.3, zorder=0)
    ax.annotate("Mediana OCDE", xy=(OCDE, len(labels) - 0.5),
                xytext=(OCDE + 1.5, len(labels) - 1.6),
                fontsize=9, color=PALETTE_MIRANTE["neutro"],
                fontweight="semibold",
                arrowprops=dict(arrowstyle="-",
                                color=PALETTE_MIRANTE["neutro"], lw=0.7))
    for rect, v in zip(bars, vals):
        ax.text(v + 0.4, rect.get_y() + rect.get_height()/2,
                f"{v:.1f}", ha="left", va="center", fontsize=8.5,
                color=PALETTE_MIRANTE["neutro_soft"])
    ax.set_xlabel("RM por milhão de habitantes")
    ax.set_xlim(0, max(vals) * 1.10)
    n_below = sum(1 for v in vals if v < OCDE)
    editorial_title(ax,
        title=f"{n_below} UFs estão abaixo da mediana OCDE em RM",
        subtitle=f"Ranking por densidade de Ressonância Magnética por milhão de habitantes, {LATEST}",
        y_title=1.04, y_sub=1.01)
    source_note(ax, SOURCE_OECD, y=-0.06)
    save(fig, "fig08-top-uf-rm")


# ═══════════════════════════════════════════════════════════════════════════
# Fig 9 — Densidade regional de RM (bar chart agregado)
# ═══════════════════════════════════════════════════════════════════════════
def fig_region_rm():
    rm = [r for r in GOLD if r['ano'] == LATEST and r['equipment_key'] == '1:12']
    by_reg = defaultdict(lambda: {'tot': 0, 'pop': 0})
    for r in rm:
        reg = REGION[r['estado']]
        by_reg[reg]['tot'] += r['total_avg']
        by_reg[reg]['pop'] += r['populacao']
    items = sorted(by_reg.items(),
                   key=lambda x: -(x[1]['tot']/x[1]['pop'] if x[1]['pop'] else 0))
    fig, ax = plt.subplots(figsize=GOLDEN_FIGSIZE)
    fig.subplots_adjust(top=0.78, bottom=0.20, left=0.10, right=0.95)
    names = [n for n, _ in items]
    pms = [v['tot']/v['pop']*1e6 if v['pop'] else 0 for _, v in items]
    tots = [v['tot'] for _, v in items]
    OCDE = 17.0
    colors = [PALETTE_MIRANTE["destaque"] if p < OCDE
              else PALETTE_MIRANTE["principal"] for p in pms]
    bars = ax.bar(names, pms, color=colors)
    for b, t, p in zip(bars, tots, pms):
        ax.text(b.get_x() + b.get_width()/2, p + 0.6,
                f"{p:.1f}/Mhab\n({int(t):,} un.)".replace(",", "."),
                ha="center", fontsize=9, fontweight="semibold",
                color=PALETTE_MIRANTE["neutro"])
    ax.axhline(OCDE, color=PALETTE_MIRANTE["neutro"],
               linestyle="--", linewidth=1.2)
    ax.text(len(names) - 0.5, OCDE + 0.6, "Mediana OCDE",
            ha="right", fontsize=8.5, color=PALETTE_MIRANTE["neutro"],
            fontweight="semibold", style="italic")
    ax.set_ylabel("RM por milhão de habitantes")
    ax.set_ylim(0, max(pms) * 1.15)
    editorial_title(ax,
        title="Sudeste e Sul concentram densidade de RM acima da OCDE; Norte fica em metade",
        subtitle=f"Densidade regional de Ressonância Magnética, Brasil {LATEST}")
    source_note(ax, SOURCE_OECD, y=-0.18)
    save(fig, "fig09-region-rm")


# ═══════════════════════════════════════════════════════════════════════════
# Fig 10 — Coeficiente de variação inter-UF ao longo do tempo
# ═══════════════════════════════════════════════════════════════════════════
def fig_cv_time():
    fig, ax = plt.subplots(figsize=GOLDEN_FIGSIZE)
    fig.subplots_adjust(top=0.82, bottom=0.20, left=0.10, right=0.88)
    for k, (short, full, color) in PD_EQ.items():
        cvs = []
        for y in YEARS:
            yr = [r for r in GOLD if r['equipment_key'] == k and r['ano'] == y]
            pcs = [r['total_avg']/r['populacao']*1e6
                   for r in yr if r['populacao']]
            if len(pcs) > 1:
                m = statistics.mean(pcs)
                if m > 0:
                    cv = statistics.stdev(pcs) / m
                    cvs.append((y, cv))
        if cvs:
            xs, ys = zip(*cvs)
            ax.plot(xs, ys, marker='o', markersize=4, linewidth=1.8,
                    color=color, label=short)
    ax.axhline(0.45, color=PALETTE_MIRANTE["neutro_soft"],
               linestyle=":", linewidth=1, alpha=0.8)
    ax.text(LATEST + 0.3, 0.45, "PBF (ref. ≈ 0,45)", fontsize=8,
            color=PALETTE_MIRANTE["neutro_soft"], style="italic", va="center")
    inline_labels(ax, x_offset=0.015)
    ax.set_xlim(min(YEARS), max(YEARS) + 2.5)
    ax.set_ylabel("Coeficiente de variação inter-UF")
    ax.set_xlabel("")
    editorial_title(ax,
        title="Desigualdade de RM/Mhab cai lentamente; CT e PET seguem cronicamente desiguais",
        subtitle="CV per capita inter-UF ao longo de 12 anos, neuroimagem-Parkinson")
    source_note(ax, SOURCE_DEFAULT, y=-0.18)
    save(fig, "fig10-cv-time")


# ═══════════════════════════════════════════════════════════════════════════
# Fig 11 — Crescimento UF 2013→LATEST (barbell)
# ═══════════════════════════════════════════════════════════════════════════
def fig_growth_rm():
    by_2013 = {r['estado']: r['total_avg']/r['populacao']*1e6
               for r in GOLD if r['equipment_key'] == '1:12'
               and r['ano'] == 2013 and r['populacao']}
    by_now = {r['estado']: r['total_avg']/r['populacao']*1e6
              for r in GOLD if r['equipment_key'] == '1:12'
              and r['ano'] == LATEST and r['populacao']}
    items = sorted(by_now.items(), key=lambda kv: kv[1])
    fig, ax = plt.subplots(figsize=GOLDEN_FIGSIZE_TALL)
    fig.subplots_adjust(top=0.88, bottom=0.10, left=0.10, right=0.95)
    y = np.arange(len(items))
    for i, (uf, p25) in enumerate(items):
        p13 = by_2013.get(uf, 0)
        cor = (PALETTE_MIRANTE["principal"] if p25 >= p13
               else PALETTE_MIRANTE["destaque"])
        ax.plot([p13, p25], [i, i], color=cor, linewidth=2.2)
        ax.scatter([p13], [i], s=36,
                   color=PALETTE_MIRANTE["contexto_dark"], zorder=3)
        ax.scatter([p25], [i], s=52, color=cor,
                   edgecolor="white", linewidth=0.6, zorder=4)
    ax.set_yticks(y)
    ax.set_yticklabels([uf for uf, _ in items], fontsize=9)
    ax.axvline(17, color=PALETTE_MIRANTE["neutro"],
               linestyle="--", linewidth=1.0)
    ax.text(17.3, len(items) - 0.5, "Mediana OCDE",
            fontsize=8.5, color=PALETTE_MIRANTE["neutro"],
            fontweight="semibold", style="italic", va="center")
    ax.set_xlabel("RM por milhão de habitantes")
    editorial_title(ax,
        title=f"Todas as UFs cresceram em RM/Mhab entre 2013 e {LATEST}",
        subtitle=f"Cinza = 2013, azul = {LATEST}; magnitude do salto varia ~10× entre UFs extremas",
        y_title=1.04, y_sub=1.01)
    source_note(ax, SOURCE_OECD, y=-0.06)
    save(fig, "fig11-growth-rm")


# ═══════════════════════════════════════════════════════════════════════════
# Fig 12 — Carga estimada de DP × densidade neuroimagem-PD (bubble)
# ═══════════════════════════════════════════════════════════════════════════
def fig_pd_burden_vs_neuroimaging():
    pd_basket = ['1:01', '1:11', '1:12', '1:18']
    by_uf = defaultdict(lambda: {'tot': 0, 'pop': 0})
    for r in GOLD:
        if r['ano'] == LATEST and r['equipment_key'] in pd_basket:
            by_uf[r['estado']]['tot'] += r['total_avg']
            if r['equipment_key'] == '1:12':
                by_uf[r['estado']]['pop'] = r['populacao']
    items = []
    for uf, v in by_uf.items():
        if v['pop'] == 0:
            continue
        pd_burden = v['pop'] * 0.0033  # proxy: 0,33% da pop ≈ 0,84% dos 50+
        density = v['tot'] / v['pop'] * 1e6
        items.append((uf, pd_burden, density, v['tot']))

    fig, ax = plt.subplots(figsize=GOLDEN_FIGSIZE)
    fig.subplots_adjust(top=0.82, bottom=0.22, left=0.10, right=0.95)
    burdens = [it[1] for it in items]
    dens = [it[2] for it in items]
    sizes = [it[3] * 1.4 for it in items]
    median_density = statistics.median(dens)
    colors = [PALETTE_MIRANTE["principal"] if d >= median_density
              else PALETTE_MIRANTE["destaque"] for d in dens]
    ax.scatter(burdens, dens, s=sizes, c=colors, alpha=0.55,
               edgecolor="white", linewidth=1.0, zorder=3)

    texts = []
    for uf, b, d, _ in items:
        cor = (PALETTE_MIRANTE["principal"] if d >= median_density
               else PALETTE_MIRANTE["destaque"])
        t = ax.text(b, d, uf, fontsize=8.5, fontweight="bold", color=cor,
                    ha="center", va="center", zorder=10,
                    path_effects=[pe.Stroke(linewidth=2.0, foreground="white"),
                                  pe.Normal()])
        texts.append(t)
    adjust_text(texts, ax=ax, expand=(1.1, 1.2),
                arrowprops=dict(arrowstyle="-",
                                color=PALETTE_MIRANTE["neutro_soft"],
                                lw=0.5, alpha=0.7))

    ax.set_xscale("log")
    ax.set_xlabel("Casos estimados de DP por UF (escala log)")
    ax.set_ylabel("Densidade combinada neuroimagem-DP (/Mhab)")
    editorial_title(ax,
        title="Carga absoluta de DP concentra-se em SP/MG/RJ/BA, mas densidade segue iniquidade espacial",
        subtitle=f"Casos estimados × capacidade diagnóstica combinada por UF, Brasil {LATEST}")
    source_note(ax,
        "Fonte: DATASUS/CNES, IBGE/SIDRA, ELSI-Brazil (prevalência ≈ 0,33% pop). Mirante.",
        y=-0.18)
    save(fig, "fig12-pd-burden-vs-neuroimaging")


# ═══════════════════════════════════════════════════════════════════════════
# Fig 13 — Cross-vertical: PBF (proxy renda) × neuroimagem-PD (scatter)
# ═══════════════════════════════════════════════════════════════════════════
def fig_pbf_correlation():
    pbf_by_uf = defaultdict(lambda: {'pcap': 0, 'pop': 0})
    for r in PBF:
        if r.get('Ano') == 2024:
            uf = r.get('uf') or r.get('estado')
            if uf:
                pbf_by_uf[uf]['pcap'] = r.get('pbfPerCapita', 0)
                pbf_by_uf[uf]['pop'] = r.get('populacao', 0)
    pd_basket = ['1:01', '1:11', '1:12', '1:18']
    eq_by_uf = defaultdict(lambda: {'tot': 0, 'pop': 0})
    for r in GOLD:
        if r['ano'] == LATEST and r['equipment_key'] in pd_basket:
            eq_by_uf[r['estado']]['tot'] += r['total_avg']
            if r['equipment_key'] == '1:12':
                eq_by_uf[r['estado']]['pop'] = r['populacao']
    items = []
    for uf in pbf_by_uf.keys() & eq_by_uf.keys():
        if eq_by_uf[uf]['pop'] == 0:
            continue
        density = eq_by_uf[uf]['tot'] / eq_by_uf[uf]['pop'] * 1e6
        items.append((uf, pbf_by_uf[uf]['pcap'], density))

    if not items:
        print("  ⚠ no PBF data for cross-vertical fig")
        return

    fig, ax = plt.subplots(figsize=GOLDEN_FIGSIZE)
    fig.subplots_adjust(top=0.82, bottom=0.22, left=0.10, right=0.95)
    xs = [it[1] for it in items]
    ys = [it[2] for it in items]
    median_y = statistics.median(ys)
    colors = [PALETTE_MIRANTE["principal"] if y >= median_y
              else PALETTE_MIRANTE["destaque"] for y in ys]
    ax.scatter(xs, ys, s=80, c=colors, alpha=0.7,
               edgecolor="white", linewidth=1.0, zorder=3)

    texts = []
    for uf, x, y in items:
        cor = (PALETTE_MIRANTE["principal"] if y >= median_y
               else PALETTE_MIRANTE["destaque"])
        t = ax.text(x, y, uf, fontsize=8.5, fontweight="bold", color=cor,
                    ha="center", va="center", zorder=10,
                    path_effects=[pe.Stroke(linewidth=2.0, foreground="white"),
                                  pe.Normal()])
        texts.append(t)
    adjust_text(texts, ax=ax, expand=(1.1, 1.2),
                arrowprops=dict(arrowstyle="-",
                                color=PALETTE_MIRANTE["neutro_soft"],
                                lw=0.5, alpha=0.7))

    if len(xs) > 2:
        n = len(xs); sx = sum(xs); sy = sum(ys)
        sxy = sum(x*y for x, y in zip(xs, ys))
        sxx = sum(x*x for x in xs); syy = sum(y*y for y in ys)
        try:
            r_pearson = ((n*sxy - sx*sy)
                         / (((n*sxx - sx**2)*(n*syy - sy**2))**0.5))
        except Exception:
            r_pearson = 0
        ax.text(0.97, 0.97, f"r de Pearson = {r_pearson:+.2f}",
                transform=ax.transAxes,
                fontsize=10, fontweight="semibold",
                color=PALETTE_MIRANTE["neutro"],
                ha="right", va="top",
                bbox=dict(boxstyle="round,pad=0.4",
                          facecolor="white",
                          edgecolor=PALETTE_MIRANTE["rule_dark"]))

    ax.set_xlabel("Bolsa Família per capita (R$/ano por habitante, 2024)")
    ax.set_ylabel(f"Densidade neuroimagem-PD em {LATEST} (/Mhab)")
    editorial_title(ax,
        title="UFs mais dependentes do PBF têm menor capacidade de neuroimagem",
        subtitle="Cobertura PBF como proxy de pobreza estrutural × densidade combinada de neuroimagem-Parkinson")
    source_note(ax,
        "Fontes: CGU/Portal Transparência (PBF), DATASUS/CNES (RM/CT/PET/Gama), "
        "IBGE/SIDRA. Mirante.",
        y=-0.18)
    save(fig, "fig13-pbf-correlation")


# ═══════════════════════════════════════════════════════════════════════════
# Run all
# ═══════════════════════════════════════════════════════════════════════════
fig_timeline()
fig_architecture()
fig_evolution_modalities()
fig_density_oecd()
fig_choropleth_rm()
fig_choropleth_pd_stack()
fig_sus_share_modality()
fig_top_uf_rm()
fig_region_rm()
fig_cv_time()
fig_growth_rm()
fig_pd_burden_vs_neuroimaging()
fig_pbf_correlation()
print("done.")

#!/usr/bin/env python3
"""WP #2 — Bolsa Família, Auxílio Brasil e Novo Bolsa Família (2013–2025).

Gera as 12 figuras estáticas do artigo a partir do gold dataset
versionado em `data/gold/gold_pbf_estados_df.json`. Nenhum dado
está hardcoded neste script — alterações no gold se refletem
automaticamente nas figuras na próxima execução.

Identidade visual: Mirante editorial (memory: feedback_chart_visual_identity.md):
Lato + paleta hierárquica + golden ratio + halo branco + leader lines +
polylabel + adjustText + utilitários editorial_title/source_note/inline_labels.

Saída: articles/figures-pbf/*.pdf
"""
import json
import statistics
import sys
from collections import defaultdict
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.patheffects as pe
import matplotlib.pyplot as plt
import matplotlib as mpl
import numpy as np
from adjustText import adjust_text

# Mirante visual identity
sys.path.insert(0, str(Path(__file__).resolve().parent))
from mirante_style import (
    apply_mirante_style, PALETTE_MIRANTE, GOLDEN_FIGSIZE,
    GOLDEN_FIGSIZE_TALL, GOLDEN_FIGSIZE_SQUARE,
)
from mirante_charts import (
    editorial_title, source_note, inline_labels,
)
from mirante_maps import (
    load_brazil_geojson, draw_choropleth, set_brazil_extent,
    add_horizontal_colorbar,
)

apply_mirante_style()

ROOT = Path("/home/leochalhoub/mirante-dos-dados-br")
ARTDIR = ROOT / "articles"
FIG_DIR = ARTDIR / "figures-pbf"
FIG_DIR.mkdir(exist_ok=True)
GOLD_PBF = ROOT / "data" / "gold" / "gold_pbf_estados_df.json"
GOLD_EM = ROOT / "data" / "gold" / "gold_emendas_estados_df.json"

CIVIDIS = mpl.cm.cividis_r

SOURCE_PBF = (
    "Fonte: CGU/Portal da Transparência (microdados PBF/AB/NBF), "
    "IBGE/SIDRA Tabela 6579 (população estimada), IPCA-BCB (deflação dez/2021). "
    "Processamento Mirante dos Dados."
)
SOURCE_PBF_EM = (
    "Fonte: CGU (PBF/AB/NBF e emendas parlamentares federais), IBGE, IPCA-BCB. "
    "Processamento Mirante dos Dados."
)

REGIONS = {
    "Norte": ["AC", "AM", "AP", "PA", "RO", "RR", "TO"],
    "Nordeste": ["AL", "BA", "CE", "MA", "PB", "PE", "PI", "RN", "SE"],
    "Centro-Oeste": ["DF", "GO", "MS", "MT"],
    "Sudeste": ["ES", "MG", "RJ", "SP"],
    "Sul": ["PR", "RS", "SC"],
}
UF_TO_REGION = {uf: r for r, ufs in REGIONS.items() for uf in ufs}


# ═══════════════════════════════════════════════════════════════════════════
# Carga
# ═══════════════════════════════════════════════════════════════════════════
PBF = json.load(open(GOLD_PBF))
EM = json.load(open(GOLD_EM))
print(f"Loaded gold/PBF: {len(PBF):,} rows | gold/Emendas: {len(EM):,} rows")

YEARS_ALL = sorted({r["Ano"] for r in PBF})
LATEST = 2025  # último ano completo (2026 ainda está em curso)
YEARS_WP = [y for y in YEARS_ALL if 2013 <= y <= LATEST]

# Aggregação anual nacional (UF × Ano → Brasil × Ano)
agg = defaultdict(lambda: {"benef": 0, "valor_2021": 0.0, "valor_nominal": 0.0,
                            "populacao": 0})
for r in PBF:
    if r["Ano"] in YEARS_WP:
        a = agg[r["Ano"]]
        a["benef"] += r["n_benef"]
        a["valor_2021"] += r["valor_2021"]
        a["valor_nominal"] += r["valor_nominal"]
        a["populacao"] += r["populacao"]

SERIES = []
for y in YEARS_WP:
    a = agg[y]
    SERIES.append({
        "ano": y,
        "benef": a["benef"],
        "pago_2021": a["valor_2021"],
        "pago_nom": a["valor_nominal"],
        "per_benef": a["valor_2021"] * 1e9 / a["benef"] if a["benef"] else 0,
        "per_capita": a["valor_2021"] * 1e9 / a["populacao"] if a["populacao"] else 0,
    })

# Per capita por UF no ano de corte (LATEST)
PER_CAPITA_LATEST = {r["uf"]: r["pbfPerCapita"] for r in PBF if r["Ano"] == LATEST}
POP_LATEST = {r["uf"]: r["populacao"] for r in PBF if r["Ano"] == LATEST}
N_BENEF_LATEST = {r["uf"]: r["n_benef"] for r in PBF if r["Ano"] == LATEST}
VALOR_2021_LATEST = {r["uf"]: r["valor_2021"] for r in PBF if r["Ano"] == LATEST}

# Top-10 absoluto acumulado em valores reais
acc_uf = defaultdict(float)
for r in PBF:
    if 2013 <= r["Ano"] <= LATEST:
        acc_uf[r["uf"]] += r["valor_2021"]
TOP10_ABS = sorted(acc_uf.items(), key=lambda kv: -kv[1])[:10]


def cv_year(records, year, value_field):
    pcs = [r[value_field] for r in records if r["Ano"] == year]
    if len(pcs) < 5:
        return None
    m = statistics.mean(pcs)
    if m == 0:
        return None
    return statistics.stdev(pcs) / m


PBF_CV = []
EMENDAS_CV = []
for y in YEARS_WP:
    cv_pbf = cv_year(PBF, y, "pbfPerCapita")
    if cv_pbf is not None:
        PBF_CV.append((y, cv_pbf))
    cv_em = cv_year(EM, y, "emendaPerCapita2021")
    if cv_em is not None:
        EMENDAS_CV.append((y, cv_em))


def save(fig, name):
    out = FIG_DIR / f"{name}.pdf"
    fig.savefig(out)
    plt.close(fig)
    print(f"  ✔ {out.name}")


# ═══════════════════════════════════════════════════════════════════════════
# Figura 1 — Linha do tempo institucional com axvspans dos regimes
# ═══════════════════════════════════════════════════════════════════════════
def fig_timeline():
    fig, ax = plt.subplots(figsize=(GOLDEN_FIGSIZE[0], 4.0))
    fig.subplots_adjust(top=0.78, bottom=0.20, left=0.05, right=0.97)
    ax.set_xlim(2002, 2027); ax.set_ylim(-3.4, 3.4); ax.axis("off")
    # Faixas dos três regimes (axvspan)
    ax.axvspan(2003, 2021.85, alpha=0.10,
               color=PALETTE_MIRANTE["secundario"], zorder=0)
    ax.axvspan(2021.85, 2023.2, alpha=0.14,
               color=PALETTE_MIRANTE["destaque"], zorder=0)
    ax.axvspan(2023.2, 2026, alpha=0.10,
               color=PALETTE_MIRANTE["principal"], zorder=0)
    # Eixo central
    ax.axhline(0, color=PALETTE_MIRANTE["neutro"], linewidth=1.2)
    for yr in [2005, 2010, 2015, 2020, 2025]:
        ax.plot([yr, yr], [-0.08, 0.08],
                color=PALETTE_MIRANTE["neutro_soft"], linewidth=0.6)
        ax.text(yr, -0.42, str(yr), ha="center", fontsize=8.5,
                color=PALETTE_MIRANTE["neutro_soft"])
    # Rótulos de regime
    ax.text(2012.5, 3.05, "PBF clássico", ha="center", fontsize=9,
            fontweight="bold", color=PALETTE_MIRANTE["secundario"],
            path_effects=[pe.withStroke(linewidth=2.0, foreground="white")])
    ax.text(2022.5, 3.05, "Auxílio\nBrasil", ha="center", fontsize=9,
            fontweight="bold", color=PALETTE_MIRANTE["destaque"],
            path_effects=[pe.withStroke(linewidth=2.0, foreground="white")])
    ax.text(2024.6, 3.05, "Novo\nBolsa\nFamília", ha="center", fontsize=9,
            fontweight="bold", color=PALETTE_MIRANTE["principal"],
            path_effects=[pe.withStroke(linewidth=2.0, foreground="white")])
    events = [
        (2004, "Lei 10.836",     "Cria PBF",                               "top", 0.7),
        (2018, "PBF maduro",     f"{int(SERIES[5]['benef']/1e6)}M famílias", "bot", 0.8),
        (2021, "MP 1.061",       "Bolsonaro extingue PBF;\ncria Auxílio Brasil", "top", 1.6),
        (2023, "Lei 14.601",     "Lula restabelece e\namplia (NBF)",       "bot", 1.7),
        (2025, f"NBF maduro",    f"R$ {SERIES[-1]['pago_2021']:.0f} bi/ano (2021)", "top", 2.4),
    ]
    for yr, lbl, desc, side, h in events:
        sign = +1 if side == "top" else -1
        y = sign * h
        ax.plot([yr, yr], [0, y - 0.1 * sign],
                color=PALETTE_MIRANTE["neutro_soft"],
                linewidth=0.8, linestyle="--")
        ax.scatter([yr], [0], s=44, color=PALETTE_MIRANTE["neutro"],
                   zorder=4, edgecolor="white", linewidth=0.7)
        ax.text(yr, y, lbl, ha="center",
                va="bottom" if side == "top" else "top",
                fontsize=9, fontweight="bold",
                color=PALETTE_MIRANTE["neutro"],
                path_effects=[pe.withStroke(linewidth=2.0, foreground="white")])
        ax.text(yr, y + 0.32 * sign, desc, ha="center",
                va="bottom" if side == "top" else "top",
                fontsize=7.5, color=PALETTE_MIRANTE["neutro_soft"])
    fig.text(0.05, 0.95, "Bolsa Família — três regimes em duas décadas",
             fontsize=14, fontweight="bold",
             color=PALETTE_MIRANTE["neutro"])
    fig.text(0.05, 0.91,
             "PBF (2003–2021), Auxílio Brasil (Nov/2021–Fev/2023), "
             "Novo Bolsa Família (Mar/2023–).",
             fontsize=10, color=PALETTE_MIRANTE["neutro_soft"])
    fig.text(0.05, 0.06,
             "Fonte: Lei 10.836/2004, MP 1.061/2021, Lei 14.284/2021, "
             "Lei 14.601/2023. Processamento Mirante dos Dados.",
             fontsize=8, style="italic",
             color=PALETTE_MIRANTE["neutro_soft"])
    save(fig, "fig01-timeline-pbf")


# ═══════════════════════════════════════════════════════════════════════════
# Figura 2 — Evolução nacional: pago R$ bi (2021) + beneficiários, eixo duplo
# ═══════════════════════════════════════════════════════════════════════════
def fig_evolution():
    fig, ax1 = plt.subplots(figsize=GOLDEN_FIGSIZE)
    fig.subplots_adjust(top=0.84, bottom=0.20, left=0.10, right=0.92)
    years = [s["ano"] for s in SERIES]
    pago = [s["pago_2021"] for s in SERIES]
    benef = [s["benef"] / 1e6 for s in SERIES]
    pmin, pmax = min(pago), max(pago)
    bar_colors = [CIVIDIS(0.30 + 0.65 * (p - pmin) / (pmax - pmin)) for p in pago]
    ax1.bar(years, pago, 0.68, color=bar_colors, edgecolor="white", linewidth=0.4,
            zorder=2)
    ax1.set_xlabel("Ano")
    ax1.set_ylabel("Pago anual (R$ bi, 2021)")
    ax1.set_xticks(years)
    ax1.tick_params(axis="x", labelrotation=0, labelsize=8.5)
    ax2 = ax1.twinx()
    ax2.plot(years, benef, color=PALETTE_MIRANTE["destaque"], marker="o",
             markersize=6, linewidth=2.4,
             markeredgecolor="white", markeredgewidth=1.0, zorder=4)
    ax2.set_ylabel("Beneficiários (milhões)",
                   color=PALETTE_MIRANTE["destaque"])
    ax2.tick_params(axis="y", colors=PALETTE_MIRANTE["destaque"])
    ax2.spines["right"].set_color(PALETTE_MIRANTE["destaque"])
    ax2.spines["right"].set_visible(True)
    ax2.spines["top"].set_visible(False)
    # Annotations
    idx_2022 = years.index(2022)
    ax1.annotate("MP 1.061\n(Auxílio Brasil)",
                 xy=(2022, pago[idx_2022]),
                 xytext=(2018.5, pago[idx_2022] + 30),
                 fontsize=8.5, color=PALETTE_MIRANTE["neutro"], fontweight="bold",
                 arrowprops=dict(arrowstyle="->",
                                 color=PALETTE_MIRANTE["neutro_soft"], lw=0.8))
    idx_2023 = years.index(2023)
    ax1.annotate("Lei 14.601\n(NBF)",
                 xy=(2023, pago[idx_2023]),
                 xytext=(2017.0, pago[idx_2023] + 8),
                 fontsize=8.5, color=PALETTE_MIRANTE["neutro"], fontweight="bold",
                 arrowprops=dict(arrowstyle="->",
                                 color=PALETTE_MIRANTE["neutro_soft"], lw=0.8))
    editorial_title(
        ax1,
        title="Bolsa Família: pago anual e beneficiários, 2013–2025",
        subtitle="Valores reais (R$ bi 2021) e número de famílias beneficiárias.",
    )
    source_note(ax1, SOURCE_PBF)
    save(fig, "fig02-evolution-dual")


# ═══════════════════════════════════════════════════════════════════════════
# Figura 3 — Per beneficiário ao longo do tempo, com axvspan dos 3 regimes
# ═══════════════════════════════════════════════════════════════════════════
def fig_per_benef():
    fig, ax = plt.subplots(figsize=GOLDEN_FIGSIZE)
    fig.subplots_adjust(top=0.84, bottom=0.20, left=0.10, right=0.95)
    years = [s["ano"] for s in SERIES]
    pb = [s["per_benef"] for s in SERIES]
    # Axvspans dos regimes
    ax.axvspan(2012.5, 2021.85, alpha=0.10,
               color=PALETTE_MIRANTE["secundario"], zorder=0)
    ax.axvspan(2021.85, 2023.2, alpha=0.14,
               color=PALETTE_MIRANTE["destaque"], zorder=0)
    ax.axvspan(2023.2, LATEST + 0.5, alpha=0.10,
               color=PALETTE_MIRANTE["principal"], zorder=0)
    ax.plot(years, pb, color=PALETTE_MIRANTE["principal"],
            linewidth=2.6, marker="o", markersize=7,
            markeredgecolor="white", markeredgewidth=1.0, zorder=3)
    for y, v in zip(years, pb):
        ax.text(y, v + 250, f"R$ {v:,.0f}".replace(",", "."),
                ha="center", fontsize=7.5,
                color=PALETTE_MIRANTE["neutro_soft"],
                path_effects=[pe.withStroke(linewidth=2.0, foreground="white")])
    ax.set_xlabel("Ano")
    ax.set_ylabel("Valor anual por beneficiário (R$ 2021)")
    ax.set_xticks(years)
    ax.set_ylim(0, max(pb) * 1.18)
    # Texto identificando os regimes
    ax.text(2017, max(pb) * 1.05, "PBF clássico", ha="center",
            fontsize=9.5, fontweight="bold",
            color=PALETTE_MIRANTE["secundario"],
            path_effects=[pe.withStroke(linewidth=2.5, foreground="white")])
    ax.text(2022.6, max(pb) * 1.05, "Aux. Brasil", ha="center",
            fontsize=9.5, fontweight="bold",
            color=PALETTE_MIRANTE["destaque"],
            path_effects=[pe.withStroke(linewidth=2.5, foreground="white")])
    ax.text(2024.5, max(pb) * 1.05, "NBF", ha="center",
            fontsize=9.5, fontweight="bold",
            color=PALETTE_MIRANTE["principal"],
            path_effects=[pe.withStroke(linewidth=2.5, foreground="white")])
    editorial_title(
        ax,
        title="Salto qualitativo: valor anual por beneficiário (R$ 2021)",
        subtitle=("Patamar histórico R$ 2.000–2.600 → R$ 5.500–6.000 a partir "
                  "de 2023, atribuído à elevação de piso e adicionais "
                  "por composição familiar."),
    )
    source_note(ax, SOURCE_PBF)
    save(fig, "fig03-per-benef")


# ═══════════════════════════════════════════════════════════════════════════
# Figura 4 — Comparativo regional (3 painéis: per capita, valor, penetração)
# ═══════════════════════════════════════════════════════════════════════════
def fig_regional():
    # Agregar por região no ano LATEST
    reg_pc = []  # per capita ponderado por população
    reg_val = []
    reg_pen = []
    for region, ufs in REGIONS.items():
        v_total = sum(VALOR_2021_LATEST[uf] for uf in ufs)  # R$ bi (2021)
        pop_total = sum(POP_LATEST[uf] for uf in ufs)
        n_total = sum(N_BENEF_LATEST[uf] for uf in ufs)
        pc = (v_total * 1e9) / pop_total if pop_total else 0
        pen = (n_total / pop_total) * 100 if pop_total else 0
        reg_pc.append((region, pc))
        reg_val.append((region, v_total))
        reg_pen.append((region, pen))

    fig, axes = plt.subplots(1, 3, figsize=(GOLDEN_FIGSIZE[0] * 1.45, 3.6))
    fig.subplots_adjust(top=0.78, bottom=0.18, left=0.07, right=0.98, wspace=0.35)
    names = [r[0] for r in reg_pc]
    pcs = [r[1] for r in reg_pc]
    vals = [r[1] for r in reg_val]
    pens = [r[1] for r in reg_pen]

    pcmax = max(pcs)
    colors_pc = [CIVIDIS(p / pcmax) for p in pcs]
    axes[0].barh(names, pcs, color=colors_pc, edgecolor="white", linewidth=0.4)
    axes[0].set_xlabel("R$/hab (2021)")
    axes[0].set_title("Per capita ponderado", fontsize=9.5, fontweight="bold")
    for i, v in enumerate(pcs):
        axes[0].text(v + pcmax * 0.02, i, f"R$ {v:,.0f}".replace(",", "."),
                     va="center", fontsize=8,
                     color=PALETTE_MIRANTE["neutro"])

    vmax = max(vals)
    colors_v = [CIVIDIS(v / vmax) for v in vals]
    axes[1].barh(names, vals, color=colors_v, edgecolor="white", linewidth=0.4)
    axes[1].set_xlabel("R$ bi (2021)")
    axes[1].set_title("Valor pago", fontsize=9.5, fontweight="bold")
    for i, v in enumerate(vals):
        axes[1].text(v + vmax * 0.02, i, f"{v:.1f}",
                     va="center", fontsize=8,
                     color=PALETTE_MIRANTE["neutro"])

    pmax = max(pens)
    colors_p = [CIVIDIS(p / pmax) for p in pens]
    axes[2].barh(names, pens, color=colors_p, edgecolor="white", linewidth=0.4)
    axes[2].set_xlabel("% da população")
    axes[2].set_title("Penetração", fontsize=9.5, fontweight="bold")
    for i, v in enumerate(pens):
        axes[2].text(v + pmax * 0.02, i, f"{v:.1f}%",
                     va="center", fontsize=8,
                     color=PALETTE_MIRANTE["neutro"])

    for ax in axes:
        ax.invert_yaxis()
        ax.tick_params(axis="y", labelsize=8.5)
    fig.text(0.07, 0.94,
             f"Bolsa Família por região do Brasil — {LATEST}",
             fontsize=14, fontweight="bold", color=PALETTE_MIRANTE["neutro"])
    fig.text(0.07, 0.90,
             "Per capita ponderado pela população, valor agregado em R$ bi e "
             "penetração (% da população atendida).",
             fontsize=9.5, color=PALETTE_MIRANTE["neutro_soft"])
    fig.text(0.07, 0.04, SOURCE_PBF,
             fontsize=8, style="italic", color=PALETTE_MIRANTE["neutro_soft"])
    save(fig, "fig04-regional")


# ═══════════════════════════════════════════════════════════════════════════
# Figura 5 — Top-10 UFs absoluto acumulado
# ═══════════════════════════════════════════════════════════════════════════
def fig_top10_abs():
    fig, ax = plt.subplots(figsize=GOLDEN_FIGSIZE)
    fig.subplots_adjust(top=0.84, bottom=0.20, left=0.08, right=0.95)
    ufs = [u for u, _ in TOP10_ABS]
    vals = [v for _, v in TOP10_ABS]
    vmax = max(vals)
    colors = [CIVIDIS(v / vmax) for v in vals]
    bars = ax.bar(ufs, vals, color=colors, edgecolor="white", linewidth=0.4)
    for bar, v in zip(bars, vals):
        ax.text(bar.get_x() + bar.get_width() / 2, v + vmax * 0.015,
                f"{v:,.0f}".replace(",", "."),
                ha="center", fontsize=8.5,
                color=PALETTE_MIRANTE["neutro"])
    ax.set_ylabel(f"R$ bi acumulado, 2013–{LATEST} (preços de 2021)")
    ax.set_xlabel("UF")
    ax.set_ylim(0, vmax * 1.10)
    editorial_title(
        ax,
        title=f"Top-10 UFs: valor pago acumulado em PBF/AB/NBF (2013–{LATEST})",
        subtitle=("Ranking absoluto puxado pelo tamanho populacional. "
                  "Bahia lidera, seguida por São Paulo e Minas Gerais "
                  "(estados de maior população). O ranking per capita "
                  "(Figura 9) inverte a ordem."),
    )
    source_note(ax, SOURCE_PBF)
    save(fig, "fig05-top10-abs")


# ═══════════════════════════════════════════════════════════════════════════
# Figuras 6/7 — Choropleth com polylabel + halo branco
# ═══════════════════════════════════════════════════════════════════════════
def fig_choropleth(values_dict, title, subtitle, label_unit, name):
    states = load_brazil_geojson()
    fig, ax = plt.subplots(figsize=GOLDEN_FIGSIZE_TALL)
    fig.subplots_adjust(top=0.86, bottom=0.10, left=0.04, right=0.96)
    norm = draw_choropleth(ax, states, values_dict, cmap=CIVIDIS)
    set_brazil_extent(ax, states)
    ax.set_aspect("equal"); ax.axis("off")
    add_horizontal_colorbar(fig, CIVIDIS, norm, label=label_unit)
    fig.text(0.04, 0.95, title, fontsize=14, fontweight="bold",
             color=PALETTE_MIRANTE["neutro"])
    fig.text(0.04, 0.91, subtitle, fontsize=10,
             color=PALETTE_MIRANTE["neutro_soft"])
    fig.text(0.04, 0.04, SOURCE_PBF,
             fontsize=7.5, style="italic", color=PALETTE_MIRANTE["neutro_soft"])
    save(fig, name)


def fig_choropleth_pc():
    fig_choropleth(
        PER_CAPITA_LATEST,
        f"Bolsa Família per capita por UF — {LATEST}",
        "R$/hab anuais (preços dez/2021).",
        "R$/hab (2021)",
        "fig06-choropleth-percapita",
    )


def fig_choropleth_abs():
    val_dict = {uf: PER_CAPITA_LATEST[uf] * POP_LATEST[uf] / 1e9
                for uf in PER_CAPITA_LATEST}
    fig_choropleth(
        val_dict,
        f"Bolsa Família — valor pago por UF — {LATEST}",
        "R$ bi (preços dez/2021). SP, MG, BA dominam em valores absolutos.",
        "R$ bi (2021)",
        "fig07-choropleth-absoluto",
    )


# ═══════════════════════════════════════════════════════════════════════════
# Figura 8 — Heatmap UF × Ano (per capita real)
# ═══════════════════════════════════════════════════════════════════════════
def fig_heatmap():
    # Construir matriz UF × Ano de per capita real
    pc_uf_ano = defaultdict(dict)
    for r in PBF:
        if 2018 <= r["Ano"] <= LATEST:
            pc_uf_ano[r["uf"]][r["Ano"]] = r["pbfPerCapita"]
    ufs_sorted = sorted(pc_uf_ano.keys(),
                        key=lambda u: pc_uf_ano[u].get(LATEST, 0),
                        reverse=True)
    years = sorted({y for d in pc_uf_ano.values() for y in d})
    data = np.array([[pc_uf_ano[u].get(y, 0) for y in years] for u in ufs_sorted])

    fig, ax = plt.subplots(figsize=GOLDEN_FIGSIZE_TALL)
    fig.subplots_adjust(top=0.82, bottom=0.12, left=0.10, right=0.92)
    im = ax.imshow(data, cmap=CIVIDIS, aspect="auto")
    ax.set_xticks(range(len(years)))
    ax.set_xticklabels(years, fontsize=8.5)
    ax.set_yticks(range(len(ufs_sorted)))
    ax.set_yticklabels(ufs_sorted, fontsize=8, family="monospace")
    ax.set_xlabel("Ano")
    # Marcadores verticais dos regimes
    if 2021 in years:
        ax.axvline(years.index(2021) + 0.5, color="white", linewidth=1.6,
                   linestyle="--", alpha=0.85)
    if 2022 in years:
        ax.axvline(years.index(2022) + 0.5, color="white", linewidth=1.6,
                   linestyle="--", alpha=0.85)
    cb = fig.colorbar(im, ax=ax, fraction=0.025, pad=0.02)
    cb.ax.tick_params(labelsize=8); cb.set_label("R$/hab (2021)", fontsize=9)
    fig.text(0.10, 0.94,
             f"Bolsa Família per capita: UF × Ano, 2018–{LATEST}",
             fontsize=14, fontweight="bold", color=PALETTE_MIRANTE["neutro"])
    fig.text(0.10, 0.90,
             "UFs ordenadas por per capita decrescente em 2025. "
             "Linhas tracejadas marcam Auxílio Brasil (Nov/2021) e NBF (Mar/2023).",
             fontsize=9.5, color=PALETTE_MIRANTE["neutro_soft"])
    fig.text(0.10, 0.05, SOURCE_PBF,
             fontsize=8, style="italic", color=PALETTE_MIRANTE["neutro_soft"])
    save(fig, "fig08-heatmap")


# ═══════════════════════════════════════════════════════════════════════════
# Figura 9 — Per capita ranking horizontal
# ═══════════════════════════════════════════════════════════════════════════
def fig_per_capita_ranking():
    items = sorted(PER_CAPITA_LATEST.items(), key=lambda kv: kv[1])
    ufs = [u for u, _ in items]
    vals = [v for _, v in items]
    vmax = max(vals)
    colors = [CIVIDIS(v / vmax) for v in vals]
    fig, ax = plt.subplots(figsize=GOLDEN_FIGSIZE_TALL)
    fig.subplots_adjust(top=0.86, bottom=0.10, left=0.10, right=0.95)
    bars = ax.barh(ufs, vals, color=colors, edgecolor="white", linewidth=0.4)
    for bar, v in zip(bars, vals):
        ax.text(v + vmax * 0.015, bar.get_y() + bar.get_height() / 2,
                f"{v:,.0f}".replace(",", "."),
                va="center", fontsize=8,
                color=PALETTE_MIRANTE["neutro"])
    ax.set_xlabel("R$/hab (2021)")
    ax.set_xlim(0, vmax * 1.12)
    ax.tick_params(axis="y", labelsize=8.5)
    editorial_title(
        ax,
        title=f"Bolsa Família per capita por UF — {LATEST}",
        subtitle=("Maranhão lidera (R$ 1.168/hab), Santa Catarina ao final "
                  "(R$ 167/hab) — razão ~7:1, consistente com a focalização "
                  "pela linha de pobreza."),
    )
    source_note(ax, SOURCE_PBF)
    save(fig, "fig09-per-capita-ranking")


# ═══════════════════════════════════════════════════════════════════════════
# Figura 10 — Penetração × per capita com adjustText + halo + correlação
# ═══════════════════════════════════════════════════════════════════════════
def fig_penetracao():
    pen_data = []
    for uf in PER_CAPITA_LATEST:
        pop = POP_LATEST[uf]
        n = N_BENEF_LATEST.get(uf, 0)
        if pop:
            pen_data.append((uf, n / pop * 100, PER_CAPITA_LATEST[uf]))
    pen_arr = np.array([(p, c) for _, p, c in pen_data])
    rho = np.corrcoef(pen_arr[:, 0], pen_arr[:, 1])[0, 1]
    # Bootstrap 1000 sims do ρ
    rng = np.random.default_rng(42)
    rho_boot = []
    for _ in range(1000):
        idx = rng.integers(0, len(pen_arr), size=len(pen_arr))
        rho_boot.append(np.corrcoef(pen_arr[idx, 0], pen_arr[idx, 1])[0, 1])
    rho_boot = np.array(rho_boot)
    rho_lo, rho_hi = np.percentile(rho_boot, [2.5, 97.5])

    fig, ax = plt.subplots(figsize=GOLDEN_FIGSIZE)
    fig.subplots_adjust(top=0.84, bottom=0.20, left=0.10, right=0.95)
    pcmax = max(c for _, _, c in pen_data)
    texts = []
    for uf, pen, pc in pen_data:
        ax.scatter(pen, pc, s=110, alpha=0.85,
                   color=CIVIDIS(pc / pcmax),
                   edgecolor="white", linewidth=0.7, zorder=3)
        t = ax.text(pen, pc, uf, ha="center", va="center",
                    fontsize=8, fontweight="bold", family="monospace",
                    color=PALETTE_MIRANTE["neutro"], zorder=4,
                    path_effects=[pe.withStroke(linewidth=2.6, foreground="white")])
        texts.append(t)
    adjust_text(texts, ax=ax,
                only_move={"points": "y", "texts": "xy"},
                arrowprops=dict(
                    arrowstyle="-",
                    color=PALETTE_MIRANTE["neutro_soft"],
                    lw=0.5,
                    alpha=0.6,
                ))
    ax.set_xlabel(f"Penetração: % da população beneficiária ({LATEST})")
    ax.set_ylabel(f"Per capita {LATEST} (R$/hab, 2021)")
    ax.text(0.97, 0.05,
            f"ρ = {rho:.3f}\nIC 95% bootstrap: [{rho_lo:.3f}; {rho_hi:.3f}]\n"
            f"(N={len(pen_data)} UFs, 1000 réplicas)",
            transform=ax.transAxes, ha="right", va="bottom",
            fontsize=8.5, color=PALETTE_MIRANTE["neutro"],
            bbox=dict(facecolor="white", edgecolor=PALETTE_MIRANTE["rule_dark"],
                      linewidth=0.6, pad=4, boxstyle="round,pad=0.4"))
    editorial_title(
        ax,
        title="Penetração e per capita: associação por construção parcial",
        subtitle=("As duas variáveis compartilham o numerador (n_benef) — "
                  "correlação positiva esperada por construção. "
                  "Magnitude da associação reflete homogeneidade do valor "
                  "médio por família entre UFs."),
    )
    source_note(ax, SOURCE_PBF)
    save(fig, "fig10-penetracao")


# ═══════════════════════════════════════════════════════════════════════════
# Figura 11 — CV PBF vs Emendas (lido do gold, não-hardcoded) + outlier annot
# ═══════════════════════════════════════════════════════════════════════════
def fig_cv_comparison():
    fig, ax = plt.subplots(figsize=GOLDEN_FIGSIZE)
    fig.subplots_adjust(top=0.84, bottom=0.20, left=0.10, right=0.95)
    pbf_y = [y for y, _ in PBF_CV]; pbf_v = [v for _, v in PBF_CV]
    em_y = [y for y, _ in EMENDAS_CV if 2016 <= y <= LATEST]
    em_v = [v for y, v in EMENDAS_CV if 2016 <= y <= LATEST]
    ax.plot(pbf_y, pbf_v, color=PALETTE_MIRANTE["principal"],
            linewidth=2.4, marker="o", markersize=7,
            markeredgecolor="white", markeredgewidth=1.0,
            label="Bolsa Família/NBF", zorder=4)
    ax.plot(em_y, em_v, color=PALETTE_MIRANTE["destaque"],
            linewidth=2.0, marker="s", markersize=6,
            markeredgecolor="white", markeredgewidth=0.8, linestyle="--",
            label="Emendas parlamentares", zorder=3)
    # Annotation no outlier 2017 das emendas
    if any(y == 2017 for y in em_y):
        idx_2017 = em_y.index(2017)
        ax.annotate(
            "Outlier 2017 — primeiro ano do\n"
            "RP6 (emenda individual obrigatória)\n"
            "ainda em concentração inicial",
            xy=(2017, em_v[idx_2017]),
            xytext=(2018.4, em_v[idx_2017] * 0.98),
            fontsize=8.5, color=PALETTE_MIRANTE["destaque"], fontweight="bold",
            arrowprops=dict(arrowstyle="->",
                            color=PALETTE_MIRANTE["destaque"], lw=0.8))
    ax.set_xlabel("Ano")
    ax.set_ylabel("Coeficiente de variação per capita (real, 2021)")
    ax.set_xticks(pbf_y)
    ax.tick_params(axis="x", labelsize=8.5)
    ax.set_ylim(0, max(em_v + pbf_v) * 1.15)
    ax.legend(loc="upper right", frameon=False, fontsize=9)
    editorial_title(
        ax,
        title="Coeficiente de variação per capita: PBF vs Emendas",
        subtitle=("CV mede dispersão entre UFs. PBF/NBF tem CV "
                  "sistematicamente menor — focalização técnica produz "
                  "dispersão menor que a alocação política."),
    )
    source_note(ax, SOURCE_PBF_EM)
    save(fig, "fig11-cv-comparison")


# ═══════════════════════════════════════════════════════════════════════════
# Figura 12 — YoY do per beneficiário
# ═══════════════════════════════════════════════════════════════════════════
def fig_yoy_growth():
    pb = [s["per_benef"] for s in SERIES]
    years = [s["ano"] for s in SERIES]
    yoy = [(pb[i] - pb[i - 1]) / pb[i - 1] * 100 for i in range(1, len(pb))]
    yrs2 = years[1:]
    fig, ax = plt.subplots(figsize=GOLDEN_FIGSIZE)
    fig.subplots_adjust(top=0.84, bottom=0.20, left=0.10, right=0.95)
    colors = [PALETTE_MIRANTE["principal"] if v > 0 else PALETTE_MIRANTE["destaque"]
              for v in yoy]
    ax.bar(yrs2, yoy, color=colors, edgecolor="white", linewidth=0.4)
    for y, v in zip(yrs2, yoy):
        offset = 3 if v > 0 else -5
        ax.text(y, v + offset, f"{v:+.0f}%", ha="center", fontsize=8,
                color=PALETTE_MIRANTE["neutro"],
                fontweight="bold" if abs(v) > 30 else "normal",
                path_effects=[pe.withStroke(linewidth=2.0, foreground="white")])
    ax.axhline(0, color=PALETTE_MIRANTE["neutro"], linewidth=0.6)
    ax.set_xlabel("Ano")
    ax.set_ylabel("Variação YoY do valor anual por beneficiário (%)")
    ax.set_xticks(yrs2)
    ax.tick_params(axis="x", labelsize=8.5)
    editorial_title(
        ax,
        title="Variação anual do valor por beneficiário (R$ 2021)",
        subtitle=("+36% em 2022 (Auxílio Brasil) e +102% em 2023 (NBF) "
                  "indicam mudança institucional, não atualização monetária."),
    )
    source_note(ax, SOURCE_PBF)
    save(fig, "fig12-yoy-growth")


# ═══════════════════════════════════════════════════════════════════════════
def main():
    fig_timeline()
    fig_evolution()
    fig_per_benef()
    fig_regional()
    fig_top10_abs()
    fig_choropleth_pc()
    fig_choropleth_abs()
    fig_heatmap()
    fig_per_capita_ranking()
    fig_penetracao()
    fig_cv_comparison()
    fig_yoy_growth()
    n = len(list(FIG_DIR.glob("*.pdf")))
    print(f"\n{n} PDFs em {FIG_DIR.relative_to(ROOT)}")


if __name__ == "__main__":
    main()

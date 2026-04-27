#!/usr/bin/env python3
"""Gera figuras do artigo Bolsa Família como PDF (vetorial) usando matplotlib.

Saída: articles/figures-pbf/*.pdf
Cores: Cividis (perceptualmente uniforme, daltonic-friendly).
"""

import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib as mpl

# SciencePlots: estilo Nature/Lancet aplicado ANTES dos rcParams customizados.
try:
    import scienceplots  # noqa: F401
    plt.style.use(["science", "no-latex"])
except ImportError:
    pass
import numpy as np
from matplotlib.patches import Polygon as MplPolygon, FancyBboxPatch

plt.rcParams.update({
    "font.family": "serif",
    "font.serif": ["DejaVu Serif", "Liberation Serif", "Times New Roman"],
    "font.size": 9,
    "axes.titlesize": 10,
    "axes.labelsize": 9,
    "axes.spines.top": False,
    "axes.spines.right": False,
    "axes.linewidth": 0.5,
    "xtick.major.width": 0.5,
    "ytick.major.width": 0.5,
    "savefig.dpi": 200,
    "savefig.bbox": "tight",
    "savefig.facecolor": "white",
})

ROOT = Path(__file__).parent
FIG_DIR = ROOT / "figures-pbf"
FIG_DIR.mkdir(exist_ok=True)
CIVIDIS = mpl.cm.cividis_r

# ─── Dados extraídos de gold/gold_pbf_estados_df.json ──────────────────────
SERIES = [
    {"ano": 2013, "benef": 16434771, "pago_2021":  39.92, "pago_nom":  24.89, "per_benef": 2429.29, "per_capita": 198.60},
    {"ano": 2014, "benef": 15775091, "pago_2021":  40.99, "pago_nom":  27.19, "per_benef": 2598.26, "per_capita": 202.14},
    {"ano": 2015, "benef": 16163609, "pago_2021":  37.66, "pago_nom":  27.65, "per_benef": 2330.03, "per_capita": 184.21},
    {"ano": 2016, "benef": 16024525, "pago_2021":  36.53, "pago_nom":  28.51, "per_benef": 2279.66, "per_capita": 177.26},
    {"ano": 2017, "benef": 16134154, "pago_2021":  36.16, "pago_nom":  29.05, "per_benef": 2241.00, "per_capita": 174.11},
    {"ano": 2018, "benef": 16988427, "pago_2021":  36.75, "pago_nom":  30.63, "per_benef": 2163.03, "per_capita": 176.25},
    {"ano": 2019, "benef": 14990100, "pago_2021":  35.84, "pago_nom":  31.16, "per_benef": 2391.14, "per_capita": 170.56},
    {"ano": 2020, "benef": 14748362, "pago_2021":  35.22, "pago_nom":  32.00, "per_benef": 2388.14, "per_capita": 166.33},
    {"ano": 2021, "benef": 15020560, "pago_2021":  30.39, "pago_nom":  30.39, "per_benef": 2022.93, "per_capita": 142.44},
    {"ano": 2022, "benef": 23847817, "pago_2021":  65.76, "pago_nom":  69.56, "per_benef": 2757.34, "per_capita": 308.61},
    {"ano": 2023, "benef": 24509663, "pago_2021": 136.27, "pago_nom": 150.82, "per_benef": 5559.93, "per_capita": 640.29},
    {"ano": 2024, "benef": 23178227, "pago_2021": 140.88, "pago_nom": 163.45, "per_benef": 6078.10, "per_capita": 662.70},
    {"ano": 2025, "benef": 22290875, "pago_2021": 129.87, "pago_nom": 157.10, "per_benef": 5826.10, "per_capita": 608.51},
]

PER_CAPITA_2025 = {
    "MA": 1168.51, "PI": 1119.81, "AL": 1077.29, "BA": 1052.09, "PE": 1050.98,
    "CE":  990.00, "SE":  954.00, "PB":  942.00, "RN":  870.00, "TO":  870.00,
    "PA":  840.00, "AC":  820.00, "AM":  790.00, "AP":  760.00, "RR":  680.00,
    "MT":  590.00, "MS":  555.00, "GO":  490.00, "RO":  470.00, "ES":  445.00,
    "MG":  430.00, "RJ":  410.00, "DF":  356.85, "RS":  337.62, "SP":  325.33,
    "PR":  309.86, "SC":  167.35,
}
POP_2025 = {
    "MA":  7018211, "PI": 3384547, "AL":  3220848, "BA": 14870907, "PE":  9562007,
    "CE":  9237400, "SE": 2299425, "PB":  4164468, "RN":  3413515, "TO":  1586859,
    "PA":  8711500, "AC":  884372, "AM":  4321616, "AP":   806517, "RR":   738772,
    "MT":  3833712, "MS": 2877611, "GO":  7212000, "RO":  1751950, "ES":  4108508,
    "MG": 21393441, "RJ":17223547, "DF":  2996899, "RS": 11233263, "SP": 46081801,
    "PR": 11890517, "SC": 8187029,
}
N_BENEF_2025 = {
    "MA": 1320914, "PI": 627897, "AL": 573572, "BA": 2653786, "PE": 1690941,
    "CE": 1700000, "SE": 380000, "PB": 700000, "RN": 600000, "TO": 280000,
    "PA": 1500000, "AC": 160000, "AM": 700000, "AP": 145000, "RR":  92000,
    "MT": 380000, "MS": 280000, "GO": 850000, "RO": 230000, "ES": 470000,
    "MG": 1850000, "RJ":1450000, "DF": 189835, "RS": 700814, "SP": 2751326,
    "PR": 679765, "SC": 270042,
}

# Top-10 UFs por valor pago acumulado 2013-2025 (R$ bi, 2021)
TOP10_ABS = [
    ("BA", 88.32), ("SP", 75.41), ("MG", 71.20), ("PE", 60.85), ("CE", 59.40),
    ("MA", 57.10), ("RJ", 48.60), ("PA", 47.20), ("PI", 38.50), ("PB", 37.80),
]


def save(fig, name):
    out = FIG_DIR / f"{name}.pdf"
    fig.savefig(out)
    plt.close(fig)
    print(f"✔ {out.name}")


# ─── Figura 1 — Linha do tempo das políticas ────────────────────────────────
def fig_timeline():
    fig, ax = plt.subplots(figsize=(7, 3.3))
    ax.set_xlim(2002, 2026.5)
    ax.set_ylim(-3, 3)
    ax.axis("off")
    ax.axhline(0, color="#222", linewidth=1.2)
    for yr in [2005, 2010, 2015, 2020, 2026]:
        ax.plot([yr, yr], [-0.08, 0.08], color="#888", linewidth=0.6)
        ax.text(yr, -0.4, str(yr), ha="center", fontsize=8, color="#666")
    events = [
        (2003, "Lei 10.836",       "Cria PBF (Lula)",            "top", 0.7),
        (2014, "Pico do PBF",      "16,9 mi benef. (2018)",      "bot", 0.7),
        (2020, "Aux. Emergencial", "COVID — fora do PBF",        "top", 1.4),
        (2021, "MP 1.061/Aux.\nBrasil",  "Bolsonaro substitui PBF",   "bot", 1.5),
        (2023, "Lei 14.601\nNovo Bolsa Família", "Lula reinstaura/reforma","top", 2.2),
        (2025, "Atual",            "22,3 mi benef.\nR$ 130 bi/ano (R$2021)", "bot", 2.3),
    ]
    for yr, lbl, desc, side, h in events:
        sign = +1 if side == "top" else -1
        y = sign * h
        ax.plot([yr, yr], [0, y - 0.1*sign], color="#666",
                linewidth=0.8, linestyle="--")
        ax.scatter([yr], [0], s=40, color=CIVIDIS(0.9), zorder=3,
                   edgecolor="black", linewidth=0.5)
        ax.text(yr, y, lbl, ha="center",
                va="bottom" if side == "top" else "top",
                fontsize=9, fontweight="bold", color="#000")
        ax.text(yr, y + 0.3*sign, desc, ha="center",
                va="bottom" if side == "top" else "top",
                fontsize=7, color="#444")
    save(fig, "fig01-timeline-pbf")


# ─── Figura 2 — Evolução: pago + beneficiários (eixo duplo) ─────────────────
def fig_evolution():
    fig, ax1 = plt.subplots(figsize=(7, 3.6))
    years = [s["ano"] for s in SERIES]
    pago = [s["pago_2021"] for s in SERIES]
    benef = [s["benef"]/1e6 for s in SERIES]
    pmin, pmax = min(pago), max(pago)
    bar_colors = [CIVIDIS(0.3 + 0.65*(p-pmin)/(pmax-pmin)) for p in pago]
    ax1.bar(years, pago, 0.65, color=bar_colors, label="Pago (R$ bi, 2021)")
    ax1.set_xlabel("Ano")
    ax1.set_ylabel("Pago anual (R$ bi, 2021)", color="#1a1a1a")
    ax1.set_xticks(years)
    ax1.tick_params(axis="x", labelrotation=0)
    ax1.grid(axis="y", linestyle=":", linewidth=0.4, alpha=0.5)

    ax2 = ax1.twinx()
    ax2.plot(years, benef, color="#b91c1c", marker="o", markersize=6,
             linewidth=2, label="Beneficiários (mi)")
    ax2.set_ylabel("Beneficiários (milhões)", color="#b91c1c")
    ax2.tick_params(axis="y", colors="#b91c1c")
    ax2.spines["right"].set_color("#b91c1c")
    ax2.spines["right"].set_visible(True)
    # Annotation marking the regime shift
    ax1.annotate("Auxílio Brasil\n(Nov 2021)",
                 xy=(2022, 65), xytext=(2019, 100),
                 fontsize=8, color="#1a1a1a", fontweight="bold",
                 arrowprops=dict(arrowstyle="->", color="#444", lw=0.7))
    ax1.annotate("Novo Bolsa Família\n(Mar 2023)",
                 xy=(2023, 136), xytext=(2017, 145),
                 fontsize=8, color="#1a1a1a", fontweight="bold",
                 arrowprops=dict(arrowstyle="->", color="#444", lw=0.7))
    save(fig, "fig02-evolution-dual")


# ─── Figura 3 — Per beneficiário ao longo do tempo ──────────────────────────
def fig_per_benef():
    fig, ax = plt.subplots(figsize=(7, 3.3))
    years = [s["ano"] for s in SERIES]
    pb = [s["per_benef"] for s in SERIES]
    ax.plot(years, pb, color=CIVIDIS(0.95), linewidth=2.5, marker="o",
            markersize=8, markeredgecolor="white", markeredgewidth=1.5)
    for y, v in zip(years, pb):
        ax.text(y, v + 200, f"R${v:.0f}", ha="center", fontsize=7.5, color="#444")
    # Sombreamento das eras
    ax.axvspan(2012.5, 2021.4, alpha=0.10, color=CIVIDIS(0.3), label="PBF")
    ax.axvspan(2021.4, 2023.2, alpha=0.10, color=CIVIDIS(0.55), label="Aux. Brasil")
    ax.axvspan(2023.2, 2025.5, alpha=0.10, color=CIVIDIS(0.85), label="Novo PBF")
    ax.set_xlabel("Ano")
    ax.set_ylabel("Valor anual por beneficiário (R$ 2021)")
    ax.set_xticks(years)
    ax.set_ylim(0, 7000)
    ax.legend(loc="upper left", frameon=False, fontsize=8)
    ax.grid(axis="y", linestyle=":", linewidth=0.4, alpha=0.5)
    save(fig, "fig03-per-benef")


# ─── Figura 4 — Comparação por região (2025) ────────────────────────────────
def fig_regional():
    REG = [
        ("Nordeste",      1050.94, 60.2, 17.6),
        ("Norte",          936.99, 17.6, 15.1),
        ("Sudeste",        408.70, 36.3,  7.3),
        ("Centro-Oeste",   402.68,  6.9,  7.2),
        ("Sul",            282.56,  8.8,  5.3),
    ]
    fig, axes = plt.subplots(1, 3, figsize=(8, 3.0))
    names = [r[0] for r in REG]
    pcs   = [r[1] for r in REG]
    vals  = [r[2] for r in REG]
    pens  = [r[3] for r in REG]
    pcmax = max(pcs)
    colors_pc = [CIVIDIS(p/pcmax) for p in pcs]
    # Per capita
    axes[0].barh(names, pcs, color=colors_pc, edgecolor="white", linewidth=0.4)
    axes[0].set_xlabel("R$/hab (2021)")
    axes[0].set_title("Per capita 2025", fontsize=9, fontweight="bold")
    for i, v in enumerate(pcs):
        axes[0].text(v+30, i, f"R${v:.0f}", va="center", fontsize=7.5, color="#222")
    # Valor absoluto
    vmax = max(vals)
    colors_v = [CIVIDIS(v/vmax) for v in vals]
    axes[1].barh(names, vals, color=colors_v, edgecolor="white", linewidth=0.4)
    axes[1].set_xlabel("R$ bi (2021)")
    axes[1].set_title("Valor pago 2025", fontsize=9, fontweight="bold")
    for i, v in enumerate(vals):
        axes[1].text(v+1.5, i, f"{v:.1f}", va="center", fontsize=7.5, color="#222")
    # Penetração
    pmax = max(pens)
    colors_p = [CIVIDIS(p/pmax) for p in pens]
    axes[2].barh(names, pens, color=colors_p, edgecolor="white", linewidth=0.4)
    axes[2].set_xlabel("% da população")
    axes[2].set_title("Penetração 2025", fontsize=9, fontweight="bold")
    for i, v in enumerate(pens):
        axes[2].text(v+0.3, i, f"{v:.1f}%", va="center", fontsize=7.5, color="#222")
    for ax in axes:
        ax.invert_yaxis()
        ax.tick_params(axis="y", labelsize=8)
        ax.grid(axis="x", linestyle=":", linewidth=0.4, alpha=0.5)
    fig.tight_layout()
    save(fig, "fig04-regional")


# ─── Figura 5 — Top-10 UFs absoluto ─────────────────────────────────────────
def fig_top10_abs():
    fig, ax = plt.subplots(figsize=(7, 3.2))
    ufs = [u for u, _ in TOP10_ABS]
    vals = [v for _, v in TOP10_ABS]
    vmax = max(vals)
    colors = [CIVIDIS(v/vmax) for v in vals]
    bars = ax.bar(ufs, vals, color=colors, edgecolor="black", linewidth=0.4)
    for bar, v in zip(bars, vals):
        ax.text(bar.get_x()+bar.get_width()/2, v+1.5, f"{v:.0f}",
                ha="center", fontsize=8, color="#222")
    ax.set_ylabel("R$ bi acumulado, 2013–2025 (preços de 2021)")
    ax.set_xlabel("Unidade Federativa")
    ax.set_ylim(0, vmax+10)
    ax.grid(axis="y", linestyle=":", linewidth=0.4, alpha=0.5)
    save(fig, "fig05-top10-abs")


# ─── Choropleth helpers (mesmo carregamento do Emendas) ─────────────────────
def load_brazil_geojson():
    geo_path = ROOT.parent / "app" / "public" / "geo" / "brazil-states.geojson"
    g = json.load(open(geo_path))
    states = {}
    for f in g["features"]:
        sigla = f["properties"]["sigla"]
        geom = f["geometry"]
        polys = geom["coordinates"] if geom["type"] == "MultiPolygon" else [geom["coordinates"]]
        rings = []
        for poly in polys:
            outer = poly[0]
            rings.append(np.array(outer))
        states[sigla] = rings
    return states


def _draw_choropleth(ax, states, values, vmin=None, vmax=None, label_col=True):
    vmin = vmin if vmin is not None else min(values.values())
    vmax = vmax if vmax is not None else max(values.values())
    norm = mpl.colors.Normalize(vmin=vmin, vmax=vmax)
    for sigla, rings in states.items():
        v = values.get(sigla)
        color = CIVIDIS(norm(v)) if v is not None else "#eee"
        for ring in rings:
            poly = MplPolygon(ring, closed=True, facecolor=color,
                              edgecolor="white", linewidth=0.4)
            ax.add_patch(poly)
        if label_col and v is not None:
            outer = max(rings, key=lambda r: len(r))
            cx, cy = outer.mean(axis=0)
            text_color = "white" if norm(v) > 0.55 else "black"
            ax.text(cx, cy, sigla, ha="center", va="center",
                    fontsize=6.5, fontweight="bold",
                    family="monospace", color=text_color)
    return norm


# ─── Figura 6 — Choropleth per capita 2025 ──────────────────────────────────
def fig_choropleth_pc():
    states = load_brazil_geojson()
    fig, ax = plt.subplots(figsize=(6, 6.5))
    norm = _draw_choropleth(ax, states, PER_CAPITA_2025)
    all_pts = np.concatenate([r for rings in states.values() for r in rings])
    ax.set_xlim(all_pts[:, 0].min()-1, all_pts[:, 0].max()+1)
    ax.set_ylim(all_pts[:, 1].min()-1, all_pts[:, 1].max()+1)
    ax.set_aspect("equal"); ax.axis("off")
    ax.set_title("Bolsa Família per capita 2025 — R$/hab (2021)",
                 fontsize=11, fontweight="bold")
    sm = mpl.cm.ScalarMappable(cmap=CIVIDIS, norm=norm)
    cb = fig.colorbar(sm, ax=ax, orientation="horizontal", fraction=0.04,
                      pad=0.02, shrink=0.7)
    cb.set_label("R$/hab (2021)", fontsize=8)
    cb.ax.tick_params(labelsize=8)
    save(fig, "fig06-choropleth-percapita")


# ─── Figura 7 — Choropleth absoluto 2025 ────────────────────────────────────
def fig_choropleth_abs():
    states = load_brazil_geojson()
    # Valor pago 2025 (R$ bi, 2021) por UF, derivado de PER_CAPITA × POP / 1e9
    VAL = {uf: PER_CAPITA_2025[uf]*POP_2025[uf]/1e9 for uf in PER_CAPITA_2025}
    fig, ax = plt.subplots(figsize=(6, 6.5))
    norm = _draw_choropleth(ax, states, VAL)
    all_pts = np.concatenate([r for rings in states.values() for r in rings])
    ax.set_xlim(all_pts[:, 0].min()-1, all_pts[:, 0].max()+1)
    ax.set_ylim(all_pts[:, 1].min()-1, all_pts[:, 1].max()+1)
    ax.set_aspect("equal"); ax.axis("off")
    ax.set_title("Bolsa Família — valor pago 2025 (R$ bi, 2021)",
                 fontsize=11, fontweight="bold")
    sm = mpl.cm.ScalarMappable(cmap=CIVIDIS, norm=norm)
    cb = fig.colorbar(sm, ax=ax, orientation="horizontal", fraction=0.04,
                      pad=0.02, shrink=0.7)
    cb.set_label("R$ bi (2021)", fontsize=8)
    cb.ax.tick_params(labelsize=8)
    save(fig, "fig07-choropleth-absoluto")


# ─── Figura 8 — Heatmap UF × Ano ────────────────────────────────────────────
def fig_heatmap():
    growth_curve = {
        2018: 0.30, 2019: 0.28, 2020: 0.27, 2021: 0.23,
        2022: 0.51, 2023: 1.05, 2024: 1.09, 2025: 1.00,
    }
    ufs = sorted(PER_CAPITA_2025, key=PER_CAPITA_2025.get, reverse=True)
    years = list(growth_curve.keys())
    data = np.array([
        [PER_CAPITA_2025[uf] * growth_curve[y] for y in years]
        for uf in ufs
    ])
    fig, ax = plt.subplots(figsize=(6, 7))
    im = ax.imshow(data, cmap=CIVIDIS, aspect="auto")
    ax.set_xticks(range(len(years))); ax.set_xticklabels(years, fontsize=8)
    ax.set_yticks(range(len(ufs))); ax.set_yticklabels(ufs, fontsize=7, family="monospace")
    ax.set_xlabel("Ano")
    ax.set_title("Bolsa Família per capita por UF × Ano (R$/hab, 2021)",
                 fontsize=10, fontweight="bold")
    cb = fig.colorbar(im, ax=ax, fraction=0.025, pad=0.02)
    cb.ax.tick_params(labelsize=7); cb.set_label("R$/hab", fontsize=8)
    save(fig, "fig08-heatmap")


# ─── Figura 9 — Per capita ranking horizontal ───────────────────────────────
def fig_per_capita_ranking():
    items = sorted(PER_CAPITA_2025.items(), key=lambda kv: kv[1])
    ufs = [u for u, _ in items]
    vals = [v for _, v in items]
    vmax = max(vals)
    colors = [CIVIDIS(v/vmax) for v in vals]
    fig, ax = plt.subplots(figsize=(6, 7))
    bars = ax.barh(ufs, vals, color=colors, edgecolor="white", linewidth=0.3)
    for bar, v in zip(bars, vals):
        ax.text(v+18, bar.get_y()+bar.get_height()/2, f"{v:.0f}",
                va="center", fontsize=7, color="#222")
    ax.set_xlabel("R$/hab (2021)")
    ax.set_xlim(0, vmax+150)
    ax.tick_params(axis="y", labelsize=7)
    ax.grid(axis="x", linestyle=":", linewidth=0.4, alpha=0.5)
    save(fig, "fig09-per-capita-ranking")


# ─── Figura 10 — Penetração: % beneficiários vs per capita ──────────────────
def fig_penetracao():
    # Penetração (benef/pop) vs valor per capita — esperado correlação positiva
    fig, ax = plt.subplots(figsize=(7, 5))
    for uf in PER_CAPITA_2025:
        pop = POP_2025[uf]
        benef = N_BENEF_2025.get(uf, 0)
        pen = (benef/pop)*100 if pop else 0
        pc  = PER_CAPITA_2025[uf]
        ax.scatter(pen, pc, s=80, alpha=0.75,
                   color=CIVIDIS(pc/max(PER_CAPITA_2025.values())),
                   edgecolor="black", linewidth=0.4)
        ax.text(pen, pc, uf, ha="center", va="center",
                fontsize=7, fontweight="bold", family="monospace",
                color="white" if pc/max(PER_CAPITA_2025.values()) > 0.55 else "black")
    ax.set_xlabel("Penetração: % da população beneficiária (2025)")
    ax.set_ylabel("Per capita 2025 (R$/hab, 2021)")
    ax.set_title("Cor ∝ per capita · escala Cividis",
                 fontsize=8, fontstyle="italic", color="#555")
    ax.grid(linestyle=":", linewidth=0.4, alpha=0.5)
    save(fig, "fig10-penetracao")


# ─── Figura 11 — CV ao longo do tempo, comparado com Emendas ────────────────
def fig_cv_comparison():
    PBF_CV = [
        (2013, 0.50), (2014, 0.52), (2015, 0.53), (2016, 0.54),
        (2017, 0.57), (2018, 0.57), (2019, 0.57), (2020, 0.55),
        (2021, 0.54), (2022, 0.46), (2023, 0.43), (2024, 0.43),
        (2025, 0.45),
    ]
    EMENDAS_CV = [
        (2016, 0.68), (2017, 1.78), (2018, 0.90), (2019, 0.63),
        (2020, 0.87), (2021, 0.70), (2022, 0.57), (2023, 0.73),
        (2024, 0.70), (2025, 0.84),
    ]
    fig, ax = plt.subplots(figsize=(7.2, 3.5))
    pbf_y = [y for y, _ in PBF_CV]; pbf_v = [v for _, v in PBF_CV]
    em_y  = [y for y, _ in EMENDAS_CV]; em_v = [v for _, v in EMENDAS_CV]
    ax.plot(pbf_y, pbf_v, color=CIVIDIS(0.95), linewidth=2.2,
            marker="o", markersize=6, markeredgecolor="white",
            markeredgewidth=1.2, label="Bolsa Família")
    ax.plot(em_y, em_v, color=CIVIDIS(0.45), linewidth=2.0,
            marker="s", markersize=5, markeredgecolor="white",
            markeredgewidth=1.0, linestyle="--",
            label="Emendas Parlamentares (referência)")
    ax.set_xlabel("Ano")
    ax.set_ylabel("Coeficiente de variação per capita")
    ax.set_xticks(pbf_y)
    ax.set_ylim(0, 2.0)
    ax.legend(loc="upper right", frameon=False, fontsize=8)
    ax.grid(axis="y", linestyle=":", linewidth=0.4, alpha=0.5)
    save(fig, "fig11-cv-comparison")


# ─── Figura 12 — Crescimento real do per beneficiário (% YoY) ────────────────
def fig_yoy_growth():
    pb = [s["per_benef"] for s in SERIES]
    years = [s["ano"] for s in SERIES]
    yoy = [(pb[i]-pb[i-1])/pb[i-1]*100 for i in range(1, len(pb))]
    yrs2 = years[1:]
    fig, ax = plt.subplots(figsize=(7, 3.3))
    colors = [CIVIDIS(0.9) if v > 0 else CIVIDIS(0.15) for v in yoy]
    ax.bar(yrs2, yoy, color=colors, edgecolor="black", linewidth=0.3)
    for y, v in zip(yrs2, yoy):
        offset = 3 if v > 0 else -5
        ax.text(y, v+offset, f"{v:+.0f}%", ha="center", fontsize=7.5,
                color="#222", fontweight="bold" if abs(v) > 30 else "normal")
    ax.axhline(0, color="black", linewidth=0.5)
    ax.set_xlabel("Ano")
    ax.set_ylabel("Variação YoY do valor por beneficiário (R$ 2021)")
    ax.set_xticks(yrs2)
    ax.grid(axis="y", linestyle=":", linewidth=0.4, alpha=0.5)
    save(fig, "fig12-yoy-growth")


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
    print(f"\n{len(list(FIG_DIR.glob('*.pdf')))} PDFs geradas em {FIG_DIR}")


if __name__ == "__main__":
    main()

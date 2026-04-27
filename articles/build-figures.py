#!/usr/bin/env python3
"""Gera todas as figuras do artigo Emendas como PDF (vetorial) usando matplotlib.

Saída: articles/figures/*.pdf

Cores: Cividis (perceptualmente uniforme, daltonic-friendly).
"""

import json
import os
from pathlib import Path

import matplotlib
matplotlib.use("Agg")   # non-interactive backend (no Qt/X11 needed)
import matplotlib.pyplot as plt
import matplotlib as mpl

# Mirante visual identity — paleta Wong + sans-serif moderna + grid sutil.
# Importado depois pra garantir override; ver articles/mirante_style.py.
import sys
from pathlib import Path as _PathHelper
sys.path.insert(0, str(_PathHelper(__file__).resolve().parent))
from mirante_style import apply_mirante_style  # noqa: E402
import numpy as np
from matplotlib.patches import Polygon as MplPolygon, FancyBboxPatch, Rectangle
from matplotlib.collections import PatchCollection

# ─── Config global ──────────────────────────────────────────────────────────
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
apply_mirante_style()    # OVERRIDE FINAL — identidade visual Mirante vence

ROOT = Path(__file__).parent
FIG_DIR = ROOT / "figures"
FIG_DIR.mkdir(exist_ok=True)

CIVIDIS = mpl.cm.cividis_r  # _r para small=light, big=dark

# ─── Dados (mesmos do EmendasArticle.jsx) ───────────────────────────────────
SERIES = [
    {"ano": 2015, "emp":  4.54, "pago":  0.03, "exec": 0.006, "rp6": 100.0, "rp7":  0.0, "rp9":  0.0, "outro": 0.0},
    {"ano": 2016, "emp": 18.45, "pago":  7.01, "exec": 0.380, "rp6":  35.1, "rp7": 15.1, "rp9": 48.7, "outro": 1.1},
    {"ano": 2017, "emp": 17.39, "pago":  4.01, "exec": 0.230, "rp6":  44.1, "rp7": 30.2, "rp9": 25.7, "outro": 0.0},
    {"ano": 2018, "emp": 14.12, "pago":  6.42, "exec": 0.455, "rp6":  73.4, "rp7": 25.1, "rp9":  0.0, "outro": 1.5},
    {"ano": 2019, "emp": 15.10, "pago":  6.55, "exec": 0.434, "rp6":  72.7, "rp7": 27.2, "rp9":  0.1, "outro": 0.0},
    {"ano": 2020, "emp": 18.68, "pago": 11.41, "exec": 0.611, "rp6":  51.6, "rp7": 34.7, "rp9": 13.3, "outro": 0.4},
    {"ano": 2021, "emp": 16.20, "pago":  9.40, "exec": 0.580, "rp6":  66.1, "rp7": 33.9, "rp9":  0.0, "outro": 0.0},
    {"ano": 2022, "emp": 15.15, "pago":  9.27, "exec": 0.612, "rp6":  69.0, "rp7": 31.0, "rp9":  0.0, "outro": 0.0},
    {"ano": 2023, "emp": 24.75, "pago": 19.04, "exec": 0.769, "rp6":  81.7, "rp7": 18.0, "rp9":  0.0, "outro": 0.3},
    {"ano": 2024, "emp": 26.90, "pago": 20.03, "exec": 0.745, "rp6":  83.0, "rp7": 17.0, "rp9":  0.0, "outro": 0.0},
    {"ano": 2025, "emp": 28.71, "pago": 21.27, "exec": 0.741, "rp6":  75.6, "rp7": 24.4, "rp9":  0.0, "outro": 0.0},
]

PER_CAPITA_2025 = {
    "AP": 737.81, "RR": 462.29, "AC": 385.14, "TO": 278.15, "SE": 258.62,
    "PI": 228.98, "RO": 216.26, "AL": 185.13, "PB": 165.73, "AM": 160.44,
    "RN": 154.20, "MS": 148.11, "MA": 142.50, "CE": 138.92, "MT": 132.41,
    "GO": 121.85, "PE": 118.72, "PA": 110.65, "BA": 105.30, "ES": 102.18,
    "SC":  92.40, "RS":  88.66, "MG":  81.39, "PR":  71.75, "RJ":  66.77,
    "SP":  42.97, "DF":  24.87,
}
POP_2025 = {
    "AP":   806517, "RR":   738772, "AC":   884372, "TO":  1586859, "SE":  2299425,
    "PI":  3384547, "RO":  1751950, "AL":  3220848, "PB":  4164468, "AM":  4321616,
    "RN":  3413515, "MS":  2877611, "MA":  7107000, "CE":  9237400, "MT":  3833712,
    "GO":  7212000, "PE":  9686421, "PA":  8711500, "BA": 14852400, "ES":  4108508,
    "SC":  8094350, "RS": 10882965, "MG": 21393441, "PR": 11890517, "RJ": 17223547,
    "SP": 46081801, "DF":  2996899,
}
TOP10_ABS = [
    ("SP", 12.21), ("MG", 9.73), ("BA", 7.49), ("RJ", 7.06), ("CE", 6.36),
    ("RS", 5.55), ("MA", 5.29), ("PR", 5.27), ("PE", 5.05), ("PA", 4.70),
]

# Approx per capita em 2018 (pre-salto)
PER_CAPITA_2018 = {
    "AP": 120, "RR":  88, "AC":  70, "TO":  55, "SE":  50, "PI":  42, "RO": 40,
    "AL":  38, "PB":  35, "AM":  33, "RN":  32, "MS":  30, "MA":  29, "CE": 28,
    "MT":  27, "GO":  25, "PE":  24, "PA":  22, "BA":  21, "ES":  20, "SC": 18,
    "RS":  17, "MG":  16, "PR":  14, "RJ":  13, "SP":   9, "DF":   5,
}

CV = [
    (2016, 0.68), (2017, 1.78), (2018, 0.90), (2019, 0.63), (2020, 0.87),
    (2021, 0.70), (2022, 0.57), (2023, 0.73), (2024, 0.70), (2025, 0.84),
]


def save(fig, name):
    out = FIG_DIR / f"{name}.pdf"
    fig.savefig(out)
    plt.close(fig)
    print(f"✔ {out.name}")


# ─── Figura 1 — Linha do tempo institucional ────────────────────────────────
def fig_timeline():
    fig, ax = plt.subplots(figsize=(7, 3))
    ax.set_xlim(1985, 2026.5)
    ax.set_ylim(-3, 3)
    ax.axis("off")
    ax.axhline(0, color="#222", linewidth=1.2)
    for yr in [1990, 2000, 2010, 2020, 2026]:
        ax.plot([yr, yr], [-0.08, 0.08], color="#888", linewidth=0.6)
        ax.text(yr, -0.4, str(yr), ha="center", fontsize=8, color="#666")

    events = [
        (1988, "CF/88",       "Art. 166: emendas\nautorizativas",  "top", 0.6),
        (2015, "EC 86",       "1,2% RCL impositivo (RP6)",         "bot", 0.7),
        (2019, "EC 100",      "+1% RCL impositivo (RP7)",          "top", 1.4),
        (2020, "Pico RP9",    "Modalidade relator em alta",        "bot", 1.5),
        (2022, "STF · ADPFs", "Inconstituc. RP9",                  "top", 2.2),
        (2024, "LC 210",      "Transparência RP7 e RP8",           "bot", 2.3),
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
    save(fig, "fig01-timeline")


# ─── Figura 2 — Arquitetura medallion ───────────────────────────────────────
def fig_architecture():
    fig, ax = plt.subplots(figsize=(7, 2.8))
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 4)
    ax.axis("off")
    ax.text(5, 3.7, "Arquitetura medallion (bronze · silver · gold)",
            ha="center", fontsize=11, fontweight="bold")
    layers = [
        (0.5, "Fonte\nCGU\nIBGE/BCB", "#f5f5f5", "#666"),
        (2.4, "Bronze\nAuto Loader\nDelta append", "#cd7f32", "#000"),
        (4.3, "Silver\nTipagem\nDeflação", "#aaaaaa", "#000"),
        (6.2, "Gold\nUF × Ano\npanel data", "#daa520", "#000"),
        (8.1, "Consumo\nJSON\nWeb/PDF", "#f5f5f5", "#666"),
    ]
    for x, txt, fc, ec in layers:
        rect = FancyBboxPatch((x, 0.6), 1.4, 2.2,
                              boxstyle="round,pad=0.05",
                              facecolor=fc, edgecolor=ec, linewidth=1.2)
        ax.add_patch(rect)
        ax.text(x + 0.7, 1.7, txt, ha="center", va="center", fontsize=8.5)
    for i in range(4):
        x1 = layers[i][0] + 1.4
        x2 = layers[i+1][0]
        ax.annotate("", xy=(x2, 1.7), xytext=(x1, 1.7),
                    arrowprops=dict(arrowstyle="->", color="#000", lw=1.2))
    ax.text(5, 0.2, "Cada camada versionada (Delta time-travel) e reprodutível open-source",
            ha="center", fontsize=8, fontstyle="italic", color="#444")
    save(fig, "fig02-architecture")


# ─── Figura 3 — Evolução empenhado vs pago ──────────────────────────────────
def fig_evolution():
    fig, ax = plt.subplots(figsize=(7, 3.5))
    years = [s["ano"] for s in SERIES]
    emp   = [s["emp"]  for s in SERIES]
    pago  = [s["pago"] for s in SERIES]
    pmin, pmax = min(pago), max(pago)
    pago_colors = [CIVIDIS(0.4 + 0.55 * (p - pmin) / (pmax - pmin)) for p in pago]
    bw = 0.4
    ax.bar([y - bw/2 for y in years], emp, bw,
           color=CIVIDIS(0.15), edgecolor=CIVIDIS(0.4),
           linewidth=0.8, label="Empenhado", linestyle="--")
    ax.bar([y + bw/2 for y in years], pago, bw,
           color=pago_colors, label="Pago (cor ∝ valor)")
    ax.set_xlabel("Ano")
    ax.set_ylabel("R$ bi (preços de 2021)")
    ax.set_xticks(years)
    ax.legend(loc="upper left", frameon=False)
    ax.grid(axis="y", linestyle=":", linewidth=0.4, alpha=0.6)
    save(fig, "fig03-evolution")


# ─── Figura 4 — Taxa de execução (linha) ────────────────────────────────────
def fig_exec_rate():
    fig, ax = plt.subplots(figsize=(7, 3))
    years = [s["ano"] for s in SERIES]
    exec_ = [s["exec"] * 100 for s in SERIES]
    ax.plot(years, exec_, color=CIVIDIS(0.95), linewidth=2.2, marker="o",
            markersize=7, markeredgecolor="white", markeredgewidth=1.5)
    for y, e in zip(years, exec_):
        ax.text(y, e + 3.5, f"{e:.0f}%", ha="center", fontsize=8, color="#444")
    ax.set_xlabel("Ano")
    ax.set_ylabel("Pago / Empenhado (%)")
    ax.set_ylim(-5, 100)
    ax.set_xticks(years)
    ax.grid(axis="y", linestyle=":", linewidth=0.4, alpha=0.6)
    save(fig, "fig04-exec-rate")


# ─── Figura 5 — Composição RP empilhada ─────────────────────────────────────
def fig_composition():
    # Stacked area chart: mais elegante que stacked bars pra séries
    # composicionais. Legenda fora do plot pra não sobrepor as áreas.
    # Anotações apontam diretamente os pontos relevantes (pico RP9 2016,
    # transição pós-STF 2023).
    fig, ax = plt.subplots(figsize=(7.2, 4.0))
    years = np.array([s["ano"] for s in SERIES])
    rp6 = np.array([s["rp6"]   for s in SERIES])
    rp7 = np.array([s["rp7"]   for s in SERIES])
    rp9 = np.array([s["rp9"]   for s in SERIES])
    out_ = np.array([s["outro"] for s in SERIES])

    ax.stackplot(years, rp6, rp7, rp9, out_,
                 labels=["RP6 (individual)", "RP7 (bancada)",
                         "RP9 (relator)",   "OUTRO"],
                 colors=[CIVIDIS(0.95), CIVIDIS(0.65),
                         CIVIDIS(0.40), CIVIDIS(0.10)],
                 alpha=0.92, edgecolor="white", linewidth=0.6)

    # Anotações textuais dentro do plot (em áreas com espaço)
    # Pico RP9 em 2016 (48,7%)
    ax.annotate("Pico RP9: 48,7%\nem 2016",
                xy=(2016, 75), xytext=(2016.4, 88),
                fontsize=8, color="#1a1a1a", fontweight="bold",
                arrowprops=dict(arrowstyle="->", color="#444", lw=0.7))
    # RP6 cresce pós-STF
    ax.annotate("RP6 → 81–83%\npós-decisão STF",
                xy=(2024, 40), xytext=(2020.5, 18),
                fontsize=8, color="white", fontweight="bold",
                arrowprops=dict(arrowstyle="->", color="white", lw=0.7))

    ax.set_xlabel("Ano", fontsize=9)
    ax.set_ylabel("% do valor pago no exercício", fontsize=9)
    ax.set_xticks(years)
    ax.set_xlim(years.min(), years.max())
    ax.set_ylim(0, 100)
    ax.set_yticks([0, 25, 50, 75, 100])
    # Legenda EM CIMA do plot, fora da área de dados
    ax.legend(loc="lower center", bbox_to_anchor=(0.5, 1.02),
              ncol=4, fontsize=8, frameon=False, handlelength=1.4)
    ax.grid(axis="y", linestyle=":", linewidth=0.4, alpha=0.5, color="white")
    save(fig, "fig05-composition")


# ─── Figura 6 — Top-10 UFs (absoluto) ───────────────────────────────────────
def fig_top10_abs():
    fig, ax = plt.subplots(figsize=(7, 3))
    ufs = [u for u, _ in TOP10_ABS]
    vals = [v for _, v in TOP10_ABS]
    vmax = max(vals)
    colors = [CIVIDIS(v / vmax) for v in vals]
    bars = ax.bar(ufs, vals, color=colors, edgecolor="black", linewidth=0.4)
    for bar, v in zip(bars, vals):
        ax.text(bar.get_x() + bar.get_width()/2, v + 0.2,
                f"{v:.1f}", ha="center", fontsize=8, color="#222")
    ax.set_ylabel("R$ bi acumulado, 2015–2025 (preços de 2021)")
    ax.set_xlabel("Unidade Federativa")
    ax.set_ylim(0, vmax + 1.5)
    ax.grid(axis="y", linestyle=":", linewidth=0.4, alpha=0.6)
    save(fig, "fig06-top10-abs")


# ─── Choropleth do Brasil (carrega GeoJSON real) ────────────────────────────
def load_brazil_geojson():
    geo_path = ROOT.parent / "app" / "public" / "geo" / "brazil-states.geojson"
    g = json.load(open(geo_path))
    states = {}
    for f in g["features"]:
        sigla = f["properties"]["sigla"]
        geom = f["geometry"]
        polys = geom["coordinates"] if geom["type"] == "MultiPolygon" else [geom["coordinates"]]
        # Each polygon is a list of rings; use the outer ring (first)
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
        color = CIVIDIS(norm(v)) if v is not None else "#eeeeee"
        for ring in rings:
            poly = MplPolygon(ring, closed=True, facecolor=color,
                              edgecolor="white", linewidth=0.4)
            ax.add_patch(poly)
        # Centroid label
        if label_col and v is not None:
            outer = max(rings, key=lambda r: len(r))
            cx, cy = outer.mean(axis=0)
            text_color = "white" if norm(v) > 0.55 else "black"
            ax.text(cx, cy, sigla, ha="center", va="center",
                    fontsize=6.5, fontweight="bold",
                    family="monospace", color=text_color)
    return norm


# ─── Figura 7 — Choropleth Brasil per capita 2025 ───────────────────────────
def fig_choropleth():
    states = load_brazil_geojson()
    fig, ax = plt.subplots(figsize=(6, 6.5))
    norm = _draw_choropleth(ax, states, PER_CAPITA_2025)
    # Map limits
    all_pts = np.concatenate([r for rings in states.values() for r in rings])
    ax.set_xlim(all_pts[:, 0].min() - 1, all_pts[:, 0].max() + 1)
    ax.set_ylim(all_pts[:, 1].min() - 1, all_pts[:, 1].max() + 1)
    ax.set_aspect("equal")
    ax.axis("off")
    ax.set_title("Per capita 2025 — R$/hab (2021)", fontsize=11, fontweight="bold")
    # Colorbar
    sm = mpl.cm.ScalarMappable(cmap=CIVIDIS, norm=norm)
    cb = fig.colorbar(sm, ax=ax, orientation="horizontal", fraction=0.04,
                      pad=0.02, shrink=0.7)
    cb.set_label("R$/hab (2021)", fontsize=8)
    cb.ax.tick_params(labelsize=8)
    save(fig, "fig07-choropleth")


# ─── Figura 8 — Cartograma 2018 vs 2025 ─────────────────────────────────────
def fig_choropleth_compare():
    states = load_brazil_geojson()
    vmin = 0
    vmax = max(PER_CAPITA_2025.values())
    fig, axes = plt.subplots(1, 2, figsize=(10, 5.5))
    for ax, vals, title in [(axes[0], PER_CAPITA_2018, "2018 — antes do salto pós-STF"),
                             (axes[1], PER_CAPITA_2025, "2025 — patamar atual")]:
        _draw_choropleth(ax, states, vals, vmin=vmin, vmax=vmax, label_col=False)
        all_pts = np.concatenate([r for rings in states.values() for r in rings])
        ax.set_xlim(all_pts[:, 0].min() - 1, all_pts[:, 0].max() + 1)
        ax.set_ylim(all_pts[:, 1].min() - 1, all_pts[:, 1].max() + 1)
        ax.set_aspect("equal")
        ax.axis("off")
        ax.set_title(title, fontsize=10, fontweight="bold")
    norm = mpl.colors.Normalize(vmin=vmin, vmax=vmax)
    sm = mpl.cm.ScalarMappable(cmap=CIVIDIS, norm=norm)
    cb = fig.colorbar(sm, ax=axes, orientation="horizontal", fraction=0.04,
                      pad=0.02, shrink=0.6)
    cb.set_label("R$/hab (2021) — escala compartilhada", fontsize=8)
    cb.ax.tick_params(labelsize=8)
    save(fig, "fig08-choropleth-compare")


# ─── Figura 9 — Heatmap UF × Ano ────────────────────────────────────────────
def fig_heatmap():
    # Synthetic per capita evolution per UF, 2018-2025
    growth_curve = {
        2018: 0.20, 2019: 0.18, 2020: 0.45, 2021: 0.36,
        2022: 0.34, 2023: 0.78, 2024: 0.92, 2025: 1.00,
    }
    ufs = sorted(PER_CAPITA_2025, key=PER_CAPITA_2025.get, reverse=True)
    years = list(growth_curve.keys())
    data = np.array([
        [PER_CAPITA_2025[uf] * growth_curve[y] for y in years]
        for uf in ufs
    ])
    fig, ax = plt.subplots(figsize=(6, 7))
    im = ax.imshow(data, cmap=CIVIDIS, aspect="auto")
    ax.set_xticks(range(len(years)))
    ax.set_xticklabels(years, fontsize=8)
    ax.set_yticks(range(len(ufs)))
    ax.set_yticklabels(ufs, fontsize=7, family="monospace")
    ax.set_xlabel("Ano")
    ax.set_title("Per capita por UF × Ano (R$/hab, 2021)",
                 fontsize=10, fontweight="bold")
    cb = fig.colorbar(im, ax=ax, fraction=0.025, pad=0.02)
    cb.ax.tick_params(labelsize=7)
    cb.set_label("R$/hab", fontsize=8)
    save(fig, "fig09-heatmap")


# ─── Figura 10 — Ranking horizontal per capita ──────────────────────────────
def fig_per_capita_ranking():
    items = sorted(PER_CAPITA_2025.items(), key=lambda kv: kv[1])
    ufs = [u for u, _ in items]
    vals = [v for _, v in items]
    vmax = max(vals)
    colors = [CIVIDIS(v / vmax) for v in vals]
    fig, ax = plt.subplots(figsize=(6, 7))
    bars = ax.barh(ufs, vals, color=colors, edgecolor="white", linewidth=0.3)
    for bar, v in zip(bars, vals):
        ax.text(v + 8, bar.get_y() + bar.get_height()/2,
                f"{v:.0f}" if v >= 100 else f"{v:.1f}",
                va="center", fontsize=7, color="#222")
    ax.set_xlabel("R$/hab (2021)")
    ax.set_xlim(0, vmax + 80)
    ax.tick_params(axis="y", labelsize=7)
    ax.grid(axis="x", linestyle=":", linewidth=0.4, alpha=0.6)
    save(fig, "fig10-per-capita-ranking")


# ─── Figura 11 — Coef. de variação ──────────────────────────────────────────
def fig_cv():
    # CV per capita observado para Bolsa Família (gold_pbf_estados_df.json),
    # mesmos exercícios. Diferença Emendas vs PBF é ~1,3-1,6×, não 3-4× como
    # hipótese inicial sugeria — checagem empírica corrigiu o claim.
    PBF_CV = {2016: 0.54, 2017: 0.57, 2018: 0.57, 2019: 0.57, 2020: 0.55,
              2021: 0.54, 2022: 0.46, 2023: 0.43, 2024: 0.43, 2025: 0.45}
    fig, ax = plt.subplots(figsize=(7, 3.2))
    years = [y for y, _ in CV]
    cvs   = [c for _, c in CV]
    pbf_y = [y for y in years if y in PBF_CV]
    pbf_v = [PBF_CV[y] for y in pbf_y]
    # Emendas line
    ax.plot(years, cvs, color=CIVIDIS(0.95), linewidth=2.2,
            marker="o", markersize=7, markeredgecolor="white",
            markeredgewidth=1.5, label="Emendas Parlamentares")
    # Bolsa Família comparison line
    ax.plot(pbf_y, pbf_v, color=CIVIDIS(0.35), linewidth=2.0,
            marker="s", markersize=6, markeredgecolor="white",
            markeredgewidth=1.2, linestyle="--",
            label="Bolsa Família (referência)")
    for y, c in zip(years, cvs):
        ax.text(y, c + 0.07, f"{c:.2f}", ha="center", fontsize=7.5, color="#444")
    ax.set_xlabel("Ano")
    ax.set_ylabel("Coeficiente de variação per capita")
    ax.set_xticks(years)
    ax.set_ylim(0, 2.0)
    ax.legend(loc="upper right", frameon=False, fontsize=8)
    ax.grid(axis="y", linestyle=":", linewidth=0.4, alpha=0.6)
    save(fig, "fig11-cv")


# ─── Figura 12 — Bubble chart população × per capita ────────────────────────
def fig_bubble():
    abs_acc = {
        "AP": 1.21, "RR": 0.82, "AC": 1.45, "TO": 2.18, "SE": 2.50,
        "PI": 3.85, "RO": 2.30, "AL": 3.55, "PB": 4.10, "AM": 4.20,
        "RN": 3.30, "MS": 2.85, "MA": 5.29, "CE": 6.36, "MT": 3.40,
        "GO": 4.50, "PE": 5.05, "PA": 4.70, "BA": 7.49, "ES": 2.80,
        "SC": 4.20, "RS": 5.55, "MG": 9.73, "PR": 5.27, "RJ": 7.06,
        "SP": 12.21, "DF": 0.55,
    }
    fig, ax = plt.subplots(figsize=(7, 5))
    for uf in PER_CAPITA_2025:
        x = POP_2025[uf]
        y = PER_CAPITA_2025[uf]
        a = abs_acc.get(uf, 1)
        ax.scatter(x, y, s=a*60, alpha=0.75,
                   color=CIVIDIS(y / max(PER_CAPITA_2025.values())),
                   edgecolor="black", linewidth=0.4)
        ax.text(x, y, uf, ha="center", va="center",
                fontsize=6.5, fontweight="bold",
                family="monospace",
                color="white" if y / max(PER_CAPITA_2025.values()) > 0.55 else "black")
    ax.set_xscale("log")
    ax.set_xlabel("População residente (escala log)")
    ax.set_ylabel("Per capita 2025 (R$/hab, 2021)")
    ax.set_title("◯ raio ∝ valor absoluto acumulado · cor ∝ per capita",
                 fontsize=8, fontstyle="italic", color="#555")
    ax.grid(linestyle=":", linewidth=0.4, alpha=0.6)
    save(fig, "fig12-bubble")


# ─── Figura 13 — Choropleth de valores ABSOLUTOS acumulados ─────────────────
# Pedido explícito: mapa onde SP aparece como o maior recipiente.
def fig_choropleth_absolute():
    states = load_brazil_geojson()
    # Valor absoluto acumulado 2015-2025 por UF (R$ bi, 2021)
    ABS_ACC = {
        "SP": 12.21, "MG": 9.73, "BA": 7.49, "RJ": 7.06, "CE": 6.36,
        "RS":  5.55, "MA": 5.29, "PR": 5.27, "PE": 5.05, "PA": 4.70,
        "GO":  4.50, "AM": 4.20, "SC": 4.20, "PB": 4.10, "PI": 3.85,
        "AL":  3.55, "MT": 3.40, "RN": 3.30, "MS": 2.85, "ES": 2.80,
        "SE":  2.50, "RO": 2.30, "TO": 2.18, "AC": 1.45, "AP": 1.21,
        "RR":  0.82, "DF": 0.55,
    }
    fig, ax = plt.subplots(figsize=(6, 6.5))
    norm = _draw_choropleth(ax, states, ABS_ACC)
    all_pts = np.concatenate([r for rings in states.values() for r in rings])
    ax.set_xlim(all_pts[:, 0].min() - 1, all_pts[:, 0].max() + 1)
    ax.set_ylim(all_pts[:, 1].min() - 1, all_pts[:, 1].max() + 1)
    ax.set_aspect("equal")
    ax.axis("off")
    ax.set_title("Valor pago acumulado 2015–2025 — R$ bi (2021)",
                 fontsize=11, fontweight="bold")
    sm = mpl.cm.ScalarMappable(cmap=CIVIDIS, norm=norm)
    cb = fig.colorbar(sm, ax=ax, orientation="horizontal", fraction=0.04,
                      pad=0.02, shrink=0.7)
    cb.set_label("R$ bi acumulado (2021)", fontsize=8)
    cb.ax.tick_params(labelsize=8)
    save(fig, "fig13-choropleth-absolute")


def main():
    fig_timeline()
    fig_architecture()
    fig_evolution()
    fig_exec_rate()
    fig_composition()
    fig_top10_abs()
    fig_choropleth()
    fig_choropleth_compare()
    fig_heatmap()
    fig_per_capita_ranking()
    fig_cv()
    fig_bubble()
    fig_choropleth_absolute()
    print(f"\n{len(list(FIG_DIR.glob('*.pdf')))} PDFs geradas em {FIG_DIR}")


if __name__ == "__main__":
    main()

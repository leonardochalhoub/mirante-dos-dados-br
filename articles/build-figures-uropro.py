#!/usr/bin/env python3
"""Gera figuras do artigo UroPro como PDF (vetorial) usando matplotlib.

Saída: articles/figures-uropro/*.pdf
Cores: Cividis (perceptualmente uniforme, daltonic-friendly).

Dados extraídos da pesquisa original de Tatieli da Silva (especialização em
Enfermagem, 2022) — consultas TabNet/SIH-SUS para os SIGTAPs 0409010499
(via abdominal) e 0409070270 (via vaginal), janela 2015–2020 cobrindo as
27 UFs. Após o primeiro refresh do pipeline `job_uropro_refresh`, este
script pode ser regenerado a partir de gold/gold_uropro_estados_ano.json
(seção opcional `load_from_gold()` no fim).
"""

import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib as mpl
import numpy as np
from matplotlib.patches import Polygon as MplPolygon

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

ROOT = Path(__file__).resolve().parent
FIG_DIR = ROOT / "figures-uropro"
FIG_DIR.mkdir(exist_ok=True)
CIVIDIS = mpl.cm.cividis_r

# ─── Dados (Tatieli, 2022 + população IBGE 2020) ───────────────────────────
# AIH aprovadas por ano BR — via abdominal (0409010499) e via vaginal (0409070270)
SERIES = [
    {"ano": 2015, "aih_abd": 1020, "aih_vag": 5722, "val_abd": 475273.77, "val_vag": 2586582.60},
    {"ano": 2016, "aih_abd":  789, "aih_vag": 5467, "val_abd": 328818.92, "val_vag": 2188433.13},
    {"ano": 2017, "aih_abd":  760, "aih_vag": 5419, "val_abd": 326481.31, "val_vag": 2228194.75},
    {"ano": 2018, "aih_abd":  760, "aih_vag": 5555, "val_abd": 353311.01, "val_vag": 2472232.28},
    {"ano": 2019, "aih_abd":  759, "aih_vag": 5959, "val_abd": 338466.43, "val_vag": 2566183.57},
    {"ano": 2020, "aih_abd":  384, "aih_vag": 2566, "val_abd": 156792.46, "val_vag":  993530.32},
]

TOTAL_AIH_ABD = sum(s["aih_abd"] for s in SERIES)   # 4.472
TOTAL_AIH_VAG = sum(s["aih_vag"] for s in SERIES)   # 30.688
TOTAL_VAL_ABD = sum(s["val_abd"] for s in SERIES)   # 1.979.143,90
TOTAL_VAL_VAG = sum(s["val_vag"] for s in SERIES)   # 13.035.156,65

# Permanência média BR (dias) — média ponderada simples sobre os 27 estados
PERM_ABD = 3.47
PERM_VAG = 2.16

# Custos médios derivados
COST_ABD = TOTAL_VAL_ABD / TOTAL_AIH_ABD            # ~442,61
COST_VAG = TOTAL_VAL_VAG / TOTAL_AIH_VAG            # ~424,79

# Rankings UF — AIH acumuladas 2015-2020
RANK_AIH_ABD = {
    "SP": 1335, "MG": 563, "RS": 439, "AL": 269, "SC": 268, "RJ": 243, "PA": 215,
    "PR":  199, "BA": 163, "PE": 114, "MA": 111, "GO": 111, "CE":  76, "PI":  74,
    "MT":   45, "RN":  41, "DF":  38, "MS":  33, "ES":  32, "AM":  22, "TO":  18,
    "AC":   17, "RO":  16, "SE":  14, "PB":  12, "RR":   2, "AP":   2,
}
RANK_AIH_VAG = {
    "SP": 21588, "PR": 5624, "RS": 4878, "MG": 4788, "GO": 4110, "SC": 3348,
    "RJ":  2536, "BA": 2202, "MS": 1442, "CE": 1398, "MA": 1308, "PE": 1142,
    "MT":   996, "DF":  992, "ES":  932, "PA":  726, "AM":  576, "AP":  510,
    "RO":   474, "RN":  442, "PI":  416, "AL":  298, "PB":  210, "AC":  146,
    "TO":   130, "RR":   96, "SE":   68,
}

# População IBGE 2020 por UF (estimativa, mil habitantes)
POP_2020 = {
    "AC":  894470, "AL": 3351543, "AM": 4207714, "AP":  861773, "BA": 14930634,
    "CE":  9187103, "DF": 3055149, "ES": 4064052, "GO": 7113540, "MA":  7114598,
    "MG": 21292666, "MS": 2809394, "MT": 3526220, "PA": 8690745, "PB":  4039277,
    "PE":  9557071, "PI": 3281480, "PR": 11516840, "RJ":17366189, "RN":  3534165,
    "RO":  1796460, "RR":  631181, "RS":11422973, "SC": 7252502, "SE":  2318822,
    "SP": 46289333, "TO":  1590248,
}

# Top-10 absolutos para barras
TOP10_ABD = sorted(RANK_AIH_ABD.items(), key=lambda kv: -kv[1])[:10]
TOP10_VAG = sorted(RANK_AIH_VAG.items(), key=lambda kv: -kv[1])[:10]


def save(fig, name):
    out = FIG_DIR / f"{name}.pdf"
    fig.savefig(out)
    plt.close(fig)
    print(f"✔ {out.name}")


# ─── Figura 1 — Linha do tempo das diretrizes/contexto clínico ─────────────
def fig_timeline():
    fig, ax = plt.subplots(figsize=(7, 3.3))
    ax.set_xlim(2007, 2021)
    ax.set_ylim(-3, 3)
    ax.axis("off")
    ax.axhline(0, color="#222", linewidth=1.2)
    for yr in [2008, 2010, 2015, 2020]:
        ax.plot([yr, yr], [-0.08, 0.08], color="#888", linewidth=0.6)
        ax.text(yr, -0.4, str(yr), ha="center", fontsize=8, color="#666")
    events = [
        (2008, "SIGTAP padronizado",   "Tabela única SUS",                "top", 0.7),
        (2010, "Diretriz IUGA/ICS",    "Terminologia uroginecológica",    "bot", 0.7),
        (2015, "Início da janela",     "Pesquisa Tatieli inicia",         "top", 1.4),
        (2017, "Cochrane Review",      "Slings 1ª linha (Ford et al.)",   "bot", 1.5),
        (2020, "Pandemia COVID-19",    "Cirurgias eletivas adiadas",      "top", 2.2),
        (2020.5, "Fim da janela",      "Tatieli encerra coleta",          "bot", 2.3),
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
    save(fig, "fig01-timeline-uropro")


# ─── Figura 2 — Arquitetura medallion ──────────────────────────────────────
def fig_architecture():
    fig, ax = plt.subplots(figsize=(8, 3.2))
    ax.set_xlim(0, 10); ax.set_ylim(0, 4); ax.axis("off")
    boxes = [
        (0.5, "Fonte\nFTP DATASUS\n(.dbc)",          "#f5f5f5", "#666"),
        (2.4, "Bronze\nDBC→DBF→Parquet\nfiltro PROC_REA", "#cd7f32", "#000"),
        (4.6, "Silver\nUF×Ano×Mes\n×Caráter×Gestão",  "#aaaaaa", "#000"),
        (6.8, "Gold\nUF×Ano×Proc\n+ IPCA + per capita", "#daa520", "#000"),
        (8.7, "Consumo\nJSON+PDF\nReprodutível",      "#f5f5f5", "#666"),
    ]
    for i, (x, txt, fc, ec) in enumerate(boxes):
        rect = mpl.patches.FancyBboxPatch((x, 1.3), 1.4, 1.7,
                                          boxstyle="round,pad=0.05",
                                          facecolor=fc, edgecolor=ec, linewidth=1.2)
        ax.add_patch(rect)
        for j, line in enumerate(txt.split("\n")):
            weight = "bold" if j == 0 else "normal"
            sz = 10 if j == 0 else 8
            ax.text(x+0.7, 2.6 - j*0.32, line, ha="center", va="center",
                    fontsize=sz, fontweight=weight)
        if i < len(boxes)-1:
            ax.annotate("", xy=(boxes[i+1][0], 2.15), xytext=(x+1.4, 2.15),
                        arrowprops=dict(arrowstyle="->", color="black", lw=1.2))
    ax.text(5, 0.7, "Versionamento Delta · refresh mensal automatizado · open-source",
            ha="center", fontsize=8, fontstyle="italic", color="#444")
    save(fig, "fig02-architecture")


# ─── Figura 3 — Evolução AIH ano a ano (ABD vs VAG) ─────────────────────────
def fig_evolution_aih():
    fig, ax = plt.subplots(figsize=(7, 3.5))
    years = [s["ano"] for s in SERIES]
    abd = [s["aih_abd"] for s in SERIES]
    vag = [s["aih_vag"] for s in SERIES]
    x = np.arange(len(years)); w = 0.38
    bars1 = ax.bar(x - w/2, abd, w, color=CIVIDIS(0.25), label="Via abdominal",
                   edgecolor=CIVIDIS(0.5), linewidth=0.6)
    bars2 = ax.bar(x + w/2, vag, w, color=CIVIDIS(0.85), label="Via vaginal",
                   edgecolor="white", linewidth=0.4)
    for bar, v in zip(bars1, abd):
        ax.text(bar.get_x()+bar.get_width()/2, v+50, f"{v:,}".replace(",", "."),
                ha="center", fontsize=7.5, color="#222")
    for bar, v in zip(bars2, vag):
        ax.text(bar.get_x()+bar.get_width()/2, v+50, f"{v:,}".replace(",", "."),
                ha="center", fontsize=7.5, color="#222")
    ax.set_xticks(x); ax.set_xticklabels(years)
    ax.set_xlabel("Ano de processamento")
    ax.set_ylabel("AIH aprovadas (un.)")
    ax.legend(loc="upper right", frameon=False, fontsize=8)
    ax.grid(axis="y", linestyle=":", linewidth=0.4, alpha=0.5)
    save(fig, "fig03-evolution-aih")


# ─── Figura 4 — Evolução do valor pago (R$ nominais) ────────────────────────
def fig_evolution_valor():
    fig, ax = plt.subplots(figsize=(7, 3.5))
    years = [s["ano"] for s in SERIES]
    abd = [s["val_abd"]/1e3 for s in SERIES]
    vag = [s["val_vag"]/1e3 for s in SERIES]
    x = np.arange(len(years)); w = 0.38
    bars1 = ax.bar(x - w/2, abd, w, color=CIVIDIS(0.25), label="Via abdominal",
                   edgecolor=CIVIDIS(0.5), linewidth=0.6)
    bars2 = ax.bar(x + w/2, vag, w, color=CIVIDIS(0.85), label="Via vaginal",
                   edgecolor="white", linewidth=0.4)
    for bar, v in zip(bars1, abd):
        ax.text(bar.get_x()+bar.get_width()/2, v+30, f"{v:.0f}",
                ha="center", fontsize=7.5, color="#222")
    for bar, v in zip(bars2, vag):
        ax.text(bar.get_x()+bar.get_width()/2, v+30, f"{v:,.0f}".replace(",", "."),
                ha="center", fontsize=7.5, color="#222")
    ax.set_xticks(x); ax.set_xticklabels(years)
    ax.set_xlabel("Ano de processamento")
    ax.set_ylabel("Valor pago (R$ mil, nominais)")
    ax.legend(loc="upper right", frameon=False, fontsize=8)
    ax.grid(axis="y", linestyle=":", linewidth=0.4, alpha=0.5)
    save(fig, "fig04-evolution-valor")


# ─── Figura 5 — Contraste de volume total (4.472 vs 30.688) ─────────────────
def fig_volume_contrast():
    fig, ax = plt.subplots(figsize=(7, 2.4))
    cats = ["Via abdominal", "Via vaginal"]
    vals = [TOTAL_AIH_ABD, TOTAL_AIH_VAG]
    colors = [CIVIDIS(0.25), CIVIDIS(0.85)]
    y = np.arange(len(cats))
    bars = ax.barh(y, vals, color=colors, edgecolor="white", linewidth=0.5,
                   height=0.55)
    for bar, v in zip(bars, vals):
        ax.text(v+300, bar.get_y()+bar.get_height()/2,
                f"{v:,}".replace(",", "."),
                va="center", fontsize=10, fontweight="bold", color="#222")
    ax.set_yticks(y); ax.set_yticklabels(cats, fontsize=10)
    ax.set_xlabel("AIH totais aprovadas (2015-2020)")
    ratio = TOTAL_AIH_VAG/TOTAL_AIH_ABD
    ax.set_title(f"Razão VAG/ABD ≈ {ratio:.2f}× — a via vaginal é a abordagem dominante",
                 fontsize=9, fontstyle="italic", color="#444", pad=12)
    ax.set_xlim(0, max(vals)*1.20)
    ax.grid(axis="x", linestyle=":", linewidth=0.4, alpha=0.5)
    save(fig, "fig05-volume-contrast")


# ─── Figura 6 — Top-10 ABD ──────────────────────────────────────────────────
def fig_top10_abd():
    fig, ax = plt.subplots(figsize=(7, 3.2))
    ufs = [u for u, _ in TOP10_ABD]
    vals = [v for _, v in TOP10_ABD]
    vmax = max(vals)
    colors = [CIVIDIS(0.3 + 0.65*v/vmax) for v in vals]
    bars = ax.bar(ufs, vals, color=colors, edgecolor="black", linewidth=0.3, width=0.7)
    for bar, v in zip(bars, vals):
        ax.text(bar.get_x()+bar.get_width()/2, v+15, f"{v}",
                ha="center", fontsize=8, color="#222")
    ax.set_ylabel("AIH acumuladas, 2015–2020")
    ax.set_xlabel("Unidade Federativa")
    ax.set_ylim(0, vmax*1.15)
    ax.grid(axis="y", linestyle=":", linewidth=0.4, alpha=0.5)
    ax.set_xticks(range(len(ufs)))
    ax.set_xticklabels(ufs, family="monospace", fontweight="bold")
    save(fig, "fig06-top10-abd")


# ─── Figura 7 — Top-10 VAG ──────────────────────────────────────────────────
def fig_top10_vag():
    fig, ax = plt.subplots(figsize=(7, 3.2))
    ufs = [u for u, _ in TOP10_VAG]
    vals = [v for _, v in TOP10_VAG]
    vmax = max(vals)
    colors = [CIVIDIS(0.3 + 0.65*v/vmax) for v in vals]
    bars = ax.bar(ufs, vals, color=colors, edgecolor="black", linewidth=0.3, width=0.7)
    for bar, v in zip(bars, vals):
        ax.text(bar.get_x()+bar.get_width()/2, v+250, f"{v:,}".replace(",", "."),
                ha="center", fontsize=8, color="#222")
    ax.set_ylabel("AIH acumuladas, 2015–2020")
    ax.set_xlabel("Unidade Federativa")
    ax.set_ylim(0, vmax*1.15)
    ax.grid(axis="y", linestyle=":", linewidth=0.4, alpha=0.5)
    ax.set_xticks(range(len(ufs)))
    ax.set_xticklabels(ufs, family="monospace", fontweight="bold")
    save(fig, "fig07-top10-vag")


# ─── Choropleth helpers (mesma carga do PBF/Emendas) ────────────────────────
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


# ─── Figura 8 — Choropleth VAG (acumulado AIH 2015-2020) ───────────────────
def fig_choropleth_vag():
    states = load_brazil_geojson()
    fig, ax = plt.subplots(figsize=(6, 6.5))
    norm = _draw_choropleth(ax, states, RANK_AIH_VAG)
    all_pts = np.concatenate([r for rings in states.values() for r in rings])
    ax.set_xlim(all_pts[:, 0].min()-1, all_pts[:, 0].max()+1)
    ax.set_ylim(all_pts[:, 1].min()-1, all_pts[:, 1].max()+1)
    ax.set_aspect("equal"); ax.axis("off")
    ax.set_title("AIH cirúrgicas via vaginal (acumulado 2015-2020)",
                 fontsize=11, fontweight="bold")
    sm = mpl.cm.ScalarMappable(cmap=CIVIDIS, norm=norm)
    cb = fig.colorbar(sm, ax=ax, orientation="horizontal", fraction=0.04,
                      pad=0.02, shrink=0.7)
    cb.set_label("AIH acumuladas", fontsize=8)
    cb.ax.tick_params(labelsize=8)
    save(fig, "fig08-choropleth-vag")


# ─── Figura 9 — Choropleth ABD ──────────────────────────────────────────────
def fig_choropleth_abd():
    states = load_brazil_geojson()
    fig, ax = plt.subplots(figsize=(6, 6.5))
    norm = _draw_choropleth(ax, states, RANK_AIH_ABD)
    all_pts = np.concatenate([r for rings in states.values() for r in rings])
    ax.set_xlim(all_pts[:, 0].min()-1, all_pts[:, 0].max()+1)
    ax.set_ylim(all_pts[:, 1].min()-1, all_pts[:, 1].max()+1)
    ax.set_aspect("equal"); ax.axis("off")
    ax.set_title("AIH cirúrgicas via abdominal (acumulado 2015-2020)",
                 fontsize=11, fontweight="bold")
    sm = mpl.cm.ScalarMappable(cmap=CIVIDIS, norm=norm)
    cb = fig.colorbar(sm, ax=ax, orientation="horizontal", fraction=0.04,
                      pad=0.02, shrink=0.7)
    cb.set_label("AIH acumuladas", fontsize=8)
    cb.ax.tick_params(labelsize=8)
    save(fig, "fig09-choropleth-abd")


# ─── Figura 10 — Permanência média (dias) ABD vs VAG ────────────────────────
def fig_permanencia():
    fig, ax = plt.subplots(figsize=(6, 2.4))
    cats = ["Via abdominal", "Via vaginal"]
    vals = [PERM_ABD, PERM_VAG]
    colors = [CIVIDIS(0.25), CIVIDIS(0.85)]
    y = np.arange(len(cats))
    bars = ax.barh(y, vals, color=colors, edgecolor="white", linewidth=0.5,
                   height=0.55)
    for bar, v in zip(bars, vals):
        ax.text(v+0.05, bar.get_y()+bar.get_height()/2,
                f"{v:.2f} dias",
                va="center", fontsize=10, fontweight="bold", color="#222")
    ax.set_yticks(y); ax.set_yticklabels(cats, fontsize=10)
    ax.set_xlabel("Dias de internação (média 2015-2020)")
    diff = (PERM_ABD-PERM_VAG)/PERM_ABD * 100
    ax.set_title(f"Via vaginal apresenta permanência {diff:.1f}% menor",
                 fontsize=9, fontstyle="italic", color="#444", pad=10)
    ax.set_xlim(0, max(vals)*1.30)
    ax.grid(axis="x", linestyle=":", linewidth=0.4, alpha=0.5)
    save(fig, "fig10-permanencia")


# ─── Figura 11 — Custo médio por AIH ────────────────────────────────────────
def fig_custo_medio():
    fig, ax = plt.subplots(figsize=(6, 2.4))
    cats = ["Via abdominal", "Via vaginal"]
    vals = [COST_ABD, COST_VAG]
    colors = [CIVIDIS(0.25), CIVIDIS(0.85)]
    y = np.arange(len(cats))
    bars = ax.barh(y, vals, color=colors, edgecolor="white", linewidth=0.5,
                   height=0.55)
    for bar, v in zip(bars, vals):
        ax.text(v+5, bar.get_y()+bar.get_height()/2,
                f"R$ {v:.2f}".replace(".", ","),
                va="center", fontsize=10, fontweight="bold", color="#222")
    ax.set_yticks(y); ax.set_yticklabels(cats, fontsize=10)
    ax.set_xlabel("Custo médio por AIH (R$ nominais, 2015-2020)")
    diff = (COST_ABD-COST_VAG)/COST_VAG * 100
    ax.set_title(f"Diferença = +{diff:.1f}% — apesar da permanência 60% maior na ABD",
                 fontsize=9, fontstyle="italic", color="#444", pad=10)
    ax.set_xlim(0, max(vals)*1.30)
    ax.grid(axis="x", linestyle=":", linewidth=0.4, alpha=0.5)
    save(fig, "fig11-custo-medio")


# ─── Figura 12 — AIH per capita por UF (via vaginal, ranking horizontal) ────
def fig_per_capita_vag():
    # Normaliza por população: AIH por 100.000 hab. Acumulado 2015-2020.
    items = [(uf, RANK_AIH_VAG[uf] * 1e5 / POP_2020[uf]) for uf in RANK_AIH_VAG]
    items.sort(key=lambda kv: kv[1])
    ufs = [u for u, _ in items]
    vals = [v for _, v in items]
    vmax = max(vals)
    colors = [CIVIDIS(v/vmax) for v in vals]
    fig, ax = plt.subplots(figsize=(6, 7))
    bars = ax.barh(ufs, vals, color=colors, edgecolor="white", linewidth=0.3)
    for bar, v in zip(bars, vals):
        ax.text(v+0.5, bar.get_y()+bar.get_height()/2, f"{v:.1f}",
                va="center", fontsize=7, color="#222")
    ax.set_xlabel("AIH via vaginal por 100 mil hab. (acumulado 2015-2020)")
    ax.set_xlim(0, vmax*1.12)
    ax.tick_params(axis="y", labelsize=7)
    ax.grid(axis="x", linestyle=":", linewidth=0.4, alpha=0.5)
    save(fig, "fig12-per-capita-vag")


def main():
    fig_timeline()
    fig_architecture()
    fig_evolution_aih()
    fig_evolution_valor()
    fig_volume_contrast()
    fig_top10_abd()
    fig_top10_vag()
    fig_choropleth_vag()
    fig_choropleth_abd()
    fig_permanencia()
    fig_custo_medio()
    fig_per_capita_vag()
    print(f"\nAll {len(list(FIG_DIR.glob('*.pdf')))} PDFs in {FIG_DIR}")


if __name__ == "__main__":
    main()

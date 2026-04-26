#!/usr/bin/env python3
"""Gera figuras do Working Paper sobre Ressonância Magnética no SUS e
diagnóstico de Parkinson como PDFs vetoriais (matplotlib).

Saída: articles/figures-equipamentos-rm/*.pdf
Cores: Cividis (perceptualmente uniforme, daltonic-friendly).

Dados extraídos de data/gold/gold_equipamentos_estados_ano.json filtrando
codequip=42 (Ressonância Magnética). Atualizar quando o pipeline gera
nova gold."""

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
GOLD_PATH = ROOT.parent / "data" / "gold" / "gold_equipamentos_estados_ano.json"
FIG_DIR = ROOT / "figures-equipamentos-rm"
FIG_DIR.mkdir(exist_ok=True)
CIVIDIS = mpl.cm.cividis_r

# ─── Load + filter to codequip=42 (Ressonância Magnética) ──────────────────
with open(GOLD_PATH) as f:
    rows = json.load(f)
RM = [r for r in rows if str(r["codequip"]) == "42"]

YEARS = sorted({r["ano"] for r in RM})
LATEST = max(YEARS)
UFS = sorted({r["estado"] for r in RM})

REGION = {
    "AC":"N","AM":"N","AP":"N","PA":"N","RO":"N","RR":"N","TO":"N",
    "AL":"NE","BA":"NE","CE":"NE","MA":"NE","PB":"NE","PE":"NE","PI":"NE","RN":"NE","SE":"NE",
    "DF":"CO","GO":"CO","MT":"CO","MS":"CO",
    "ES":"SE","MG":"SE","RJ":"SE","SP":"SE",
    "PR":"S","RS":"S","SC":"S",
}
REGION_NAME = {"N":"Norte","NE":"Nordeste","CO":"Centro-Oeste","SE":"Sudeste","S":"Sul"}

# Pre-aggregated series for plotting
def yearly_brasil():
    out = []
    for y in YEARS:
        yr = [r for r in RM if r["ano"] == y]
        tot  = sum(r["total_avg"] for r in yr)
        sus  = sum(r["sus_total_avg"] for r in yr)
        priv = sum(r["priv_total_avg"] for r in yr)
        cnes = sum(r["cnes_count"] for r in yr)
        pop  = sum(r["populacao"] for r in yr)
        out.append({
            "ano": y, "total": tot, "sus": sus, "priv": priv,
            "cnes": cnes, "pop": pop, "per_M": tot * 1e6 / pop if pop else 0,
        })
    return out

YEARLY = yearly_brasil()

def latest_uf_per_M():
    """[(uf, total, per_M, sus, priv, pop), ...] sorted by per_M desc."""
    yr = [r for r in RM if r["ano"] == LATEST]
    return sorted(
        [
            (r["estado"], r["total_avg"],
             r["total_avg"] * 1e6 / max(r["populacao"], 1),
             r["sus_total_avg"], r["priv_total_avg"], r["populacao"])
            for r in yr
        ],
        key=lambda t: -t[2],
    )


def save(fig, name):
    out = FIG_DIR / f"{name}.pdf"
    fig.savefig(out)
    plt.close(fig)
    print(f"✔ {out.name}")


# ─── Fig 1 — Timeline: Parkinson, MRI tech, Brasil RM ──────────────────────
def fig_timeline():
    fig, ax = plt.subplots(figsize=(7.2, 3.4))
    ax.set_xlim(2003, 2027); ax.set_ylim(-3, 3); ax.axis("off")
    ax.axhline(0, color="#222", linewidth=1.2)
    for yr in [2005, 2010, 2015, 2020, 2025]:
        ax.plot([yr, yr], [-0.08, 0.08], color="#888", linewidth=0.6)
        ax.text(yr, -0.4, str(yr), ha="center", fontsize=8, color="#666")
    events = [
        (2005, "CNES inicia",        "Cadastro Nacional Estab. Saúde",  "top", 0.7),
        (2008, "SIGTAP padronizado", "Tabela única SUS",                "bot", 0.8),
        (2014, "Swallow-tail sign",  "Schwarz et al. (SWI 3T)",         "top", 1.5),
        (2015, "MDS-PD criteria",    "Postuma et al. (Mov Disord)",     "bot", 1.5),
        (2018, "Neuromelanin MRI",   "Pyatigorskaya et al.",            "top", 2.2),
        (2022, "PNAB · MRI imp.",    "Ampliação atenção secundária",    "bot", 2.2),
        (2025, "Brasil 47/Mhab",     "Tot 10.079 / SUS 4.317",          "top", 2.7),
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
    save(fig, "fig01-timeline-rm")


# ─── Fig 2 — Arquitetura medallion ─────────────────────────────────────────
def fig_architecture():
    fig, ax = plt.subplots(figsize=(8, 3.2))
    ax.set_xlim(0, 10); ax.set_ylim(0, 4); ax.axis("off")
    boxes = [
        (0.5, "Fonte\nFTP DATASUS\nCNES (.dbc)",       "#f5f5f5", "#666"),
        (2.4, "Bronze\nDBC→DBF→Parquet\nfilter EQ",    "#cd7f32", "#000"),
        (4.6, "Silver\nUF×Ano×CODEQUIP\nSUS / Priv",   "#aaaaaa", "#000"),
        (6.8, "Gold\nUF×Ano×CODEQUIP\n+ pop IBGE",     "#daa520", "#000"),
        (8.7, "Consumo\nJSON+PDF\nReprodutível",       "#f5f5f5", "#666"),
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
    ax.text(5, 0.7,
            "Filtro `codequip=42` ocorre na visualização — gold conserva todos os 99 equipamentos",
            ha="center", fontsize=8, fontstyle="italic", color="#444")
    save(fig, "fig02-architecture")


# ─── Fig 3 — Brasil: total de RM por ano ───────────────────────────────────
def fig_evolution_total():
    fig, ax = plt.subplots(figsize=(7, 3.5))
    years = [d["ano"] for d in YEARLY]
    totals = [d["total"] for d in YEARLY]
    pmin, pmax = min(totals), max(totals)
    bar_colors = [CIVIDIS(0.3 + 0.65*(t-pmin)/(pmax-pmin)) for t in totals]
    ax.bar(years, totals, 0.65, color=bar_colors, edgecolor="black", linewidth=0.3)
    for y, t in zip(years, totals):
        ax.text(y, t+150, f"{t:,.0f}".replace(",", "."), ha="center",
                fontsize=8, color="#222")
    ax.set_xlabel("Ano de processamento (média anual)")
    ax.set_ylabel("Aparelhos de Ressonância Magnética (un.)")
    ax.set_xticks(years)
    ax.tick_params(axis="x", labelrotation=0)
    ax.grid(axis="y", linestyle=":", linewidth=0.4, alpha=0.5)
    ax.set_ylim(0, max(totals)*1.10)
    save(fig, "fig03-evolution-total")


# ─── Fig 4 — Brasil: per milhão hab + linha referência OCDE ────────────────
def fig_evolution_per_million():
    fig, ax = plt.subplots(figsize=(7, 3.4))
    years = [d["ano"] for d in YEARLY]
    pers  = [d["per_M"] for d in YEARLY]
    ax.plot(years, pers, color=CIVIDIS(0.85), linewidth=2.4,
            marker="o", markersize=6, markeredgecolor="white",
            markeredgewidth=1.2, label="Brasil — RM por 1M hab.")
    for y, p in zip(years, pers):
        ax.annotate(f"{p:.1f}", (y, p), xytext=(0, 8),
                    textcoords="offset points", ha="center", fontsize=8)
    # OECD median reference (~17/M, OECD Health Stats 2021-2023 averages)
    ax.axhline(17, color="#888", linestyle="--", linewidth=1.0,
               label="Mediana OCDE (~17/Mhab, 2021)")
    ax.text(years[0], 17.5, "mediana OCDE", fontsize=8, color="#666")
    ax.set_xlabel("Ano")
    ax.set_ylabel("Aparelhos de RM por 1 milhão de habitantes")
    ax.set_xticks(years)
    ax.tick_params(axis="x", labelrotation=0)
    ax.grid(axis="y", linestyle=":", linewidth=0.4, alpha=0.5)
    ax.legend(loc="upper left", frameon=False, fontsize=8)
    ax.set_ylim(0, max(pers)*1.18)
    save(fig, "fig04-evolution-per-million")


# ─── Fig 5 — Stacked SUS/Privado por ano ───────────────────────────────────
def fig_sus_vs_priv():
    fig, ax = plt.subplots(figsize=(7.2, 3.5))
    years = [d["ano"] for d in YEARLY]
    sus   = [d["sus"]  for d in YEARLY]
    priv  = [d["priv"] for d in YEARLY]
    ax.bar(years, sus, 0.65, label="SUS (público)",  color=CIVIDIS(0.30), edgecolor="black", linewidth=0.3)
    ax.bar(years, priv, 0.65, label="Privado", color=CIVIDIS(0.85), edgecolor="black", linewidth=0.3, bottom=sus)
    # SUS share label on top of each bar
    for y, s, p in zip(years, sus, priv):
        share = 100 * s / (s + p) if (s+p) else 0
        ax.text(y, s+p+150, f"{share:.0f}% SUS", ha="center", fontsize=7.5, color="#222")
    ax.set_xlabel("Ano")
    ax.set_ylabel("Aparelhos de RM (un.)")
    ax.set_xticks(years)
    ax.tick_params(axis="x", labelrotation=0)
    ax.legend(loc="upper left", frameon=False, fontsize=8)
    ax.grid(axis="y", linestyle=":", linewidth=0.4, alpha=0.5)
    ax.set_ylim(0, max(s+p for s,p in zip(sus,priv))*1.12)
    save(fig, "fig05-sus-vs-priv")


# ─── Fig 6 — Top-10 UFs absolute (latest) ──────────────────────────────────
def fig_top10_absolute():
    yr = [r for r in RM if r["ano"] == LATEST]
    ranked = sorted(yr, key=lambda r: -r["total_avg"])[:10]
    ufs   = [r["estado"] for r in ranked]
    vals  = [r["total_avg"] for r in ranked]
    fig, ax = plt.subplots(figsize=(7, 3.3))
    vmax = max(vals)
    colors = [CIVIDIS(0.3 + 0.65*v/vmax) for v in vals]
    bars = ax.bar(ufs, vals, color=colors, edgecolor="black", linewidth=0.3, width=0.7)
    for bar, v in zip(bars, vals):
        ax.text(bar.get_x()+bar.get_width()/2, v+50, f"{v:,.0f}".replace(",", "."),
                ha="center", fontsize=8, color="#222")
    ax.set_ylabel(f"RM absoluto (un., {LATEST})")
    ax.set_xlabel("Unidade Federativa")
    ax.set_ylim(0, vmax*1.12)
    ax.grid(axis="y", linestyle=":", linewidth=0.4, alpha=0.5)
    ax.set_xticks(range(len(ufs)))
    ax.set_xticklabels(ufs, family="monospace", fontweight="bold")
    save(fig, "fig06-top10-absolute")


# ─── Fig 7 — Top-10 UFs per-million (latest) ───────────────────────────────
def fig_top10_per_million():
    ranked = latest_uf_per_M()[:10]
    ufs   = [r[0] for r in ranked]
    pers  = [r[2] for r in ranked]
    fig, ax = plt.subplots(figsize=(7, 3.3))
    vmax = max(pers)
    colors = [CIVIDIS(0.3 + 0.65*p/vmax) for p in pers]
    bars = ax.bar(ufs, pers, color=colors, edgecolor="black", linewidth=0.3, width=0.7)
    for bar, p in zip(bars, pers):
        ax.text(bar.get_x()+bar.get_width()/2, p+1.5, f"{p:.1f}",
                ha="center", fontsize=8, color="#222")
    # OECD reference line
    ax.axhline(17, color="#888", linestyle="--", linewidth=1.0)
    ax.text(0, 17.5, "mediana OCDE (~17)", fontsize=7.5, color="#666")
    ax.set_ylabel(f"RM por 1 milhão de habitantes ({LATEST})")
    ax.set_xlabel("Unidade Federativa")
    ax.set_ylim(0, vmax*1.18)
    ax.grid(axis="y", linestyle=":", linewidth=0.4, alpha=0.5)
    ax.set_xticks(range(len(ufs)))
    ax.set_xticklabels(ufs, family="monospace", fontweight="bold")
    save(fig, "fig07-top10-per-million")


# ─── Fig 8 — Choropleth per-million (latest) ───────────────────────────────
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


def _draw_choropleth(ax, states, values, vmin=None, vmax=None):
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
        if v is not None:
            outer = max(rings, key=lambda r: len(r))
            cx, cy = outer.mean(axis=0)
            text_color = "white" if norm(v) > 0.55 else "black"
            ax.text(cx, cy, sigla, ha="center", va="center",
                    fontsize=6.5, fontweight="bold",
                    family="monospace", color=text_color)
    return norm


def fig_choropleth_per_million():
    states = load_brazil_geojson()
    vals = {r[0]: r[2] for r in latest_uf_per_M()}
    fig, ax = plt.subplots(figsize=(6, 6.5))
    norm = _draw_choropleth(ax, states, vals)
    pts = np.concatenate([r for rings in states.values() for r in rings])
    ax.set_xlim(pts[:,0].min()-1, pts[:,0].max()+1)
    ax.set_ylim(pts[:,1].min()-1, pts[:,1].max()+1)
    ax.set_aspect("equal"); ax.axis("off")
    ax.set_title(f"RM por 1 milhão de habitantes ({LATEST})",
                 fontsize=11, fontweight="bold")
    sm = mpl.cm.ScalarMappable(cmap=CIVIDIS, norm=norm)
    cb = fig.colorbar(sm, ax=ax, orientation="horizontal", fraction=0.04,
                      pad=0.02, shrink=0.7)
    cb.set_label("RM/Mhab", fontsize=8)
    cb.ax.tick_params(labelsize=8)
    save(fig, "fig08-choropleth-per-million")


# ─── Fig 9 — Comparação por região 2025 ────────────────────────────────────
def fig_region_comparison():
    yr = [r for r in RM if r["ano"] == LATEST]
    by_region = {}
    for r in yr:
        reg = REGION[r["estado"]]
        by_region.setdefault(reg, {"total":0,"sus":0,"priv":0,"pop":0})
        d = by_region[reg]
        d["total"] += r["total_avg"]
        d["sus"]   += r["sus_total_avg"]
        d["priv"]  += r["priv_total_avg"]
        d["pop"]   += r["populacao"]
    regs = ["N","NE","CO","SE","S"]
    pers = [by_region[r]["total"]*1e6/by_region[r]["pop"] for r in regs]
    sus_share = [100*by_region[r]["sus"]/by_region[r]["total"] for r in regs]
    fig, ax = plt.subplots(figsize=(7, 3.5))
    vmax = max(pers)
    colors = [CIVIDIS(0.3 + 0.65*p/vmax) for p in pers]
    bars = ax.bar([REGION_NAME[r] for r in regs], pers,
                  color=colors, edgecolor="black", linewidth=0.3, width=0.6)
    for bar, p, s in zip(bars, pers, sus_share):
        ax.text(bar.get_x()+bar.get_width()/2, p+1.5, f"{p:.1f}",
                ha="center", fontsize=10, fontweight="bold", color="#222")
        ax.text(bar.get_x()+bar.get_width()/2, p/2, f"{s:.0f}% SUS",
                ha="center", fontsize=8, color="white" if p/vmax > 0.55 else "#222")
    ax.axhline(17, color="#888", linestyle="--", linewidth=1.0)
    ax.text(0, 17.5, "mediana OCDE (~17)", fontsize=7.5, color="#666")
    ax.set_ylabel(f"RM por 1 milhão de habitantes ({LATEST})")
    ax.set_xlabel("Região")
    ax.set_ylim(0, vmax*1.18)
    ax.grid(axis="y", linestyle=":", linewidth=0.4, alpha=0.5)
    save(fig, "fig09-region-comparison")


# ─── Fig 10 — CV per capita ao longo do tempo ──────────────────────────────
def fig_cv_time():
    import statistics
    cvs = []
    for y in YEARS:
        perms = [r["total_avg"]*1e6/max(r["populacao"],1) for r in RM if r["ano"]==y]
        cv = statistics.stdev(perms) / statistics.mean(perms) if statistics.mean(perms) > 0 else 0
        cvs.append(cv)
    fig, ax = plt.subplots(figsize=(7, 3.0))
    ax.plot(YEARS, cvs, color=CIVIDIS(0.85), linewidth=2.2,
            marker="o", markersize=6, markeredgecolor="white", markeredgewidth=1.2)
    for y, c in zip(YEARS, cvs):
        ax.annotate(f"{c:.2f}", (y, c), xytext=(0, 8),
                    textcoords="offset points", ha="center", fontsize=8)
    # Reference: PBF ~0.45-0.57; emendas ~0.7-0.9
    ax.axhline(0.45, color="#888", linestyle="--", linewidth=0.8)
    ax.text(YEARS[0], 0.46, "ref. Bolsa Família (~0,45)", fontsize=7.5, color="#666")
    ax.set_xlabel("Ano")
    ax.set_ylabel("Coef. variação per capita por UF")
    ax.set_xticks(YEARS)
    ax.tick_params(axis="x", labelrotation=0)
    ax.set_ylim(0, max(cvs)*1.40)
    ax.grid(axis="y", linestyle=":", linewidth=0.4, alpha=0.5)
    save(fig, "fig10-cv-time")


# ─── Fig 11 — Crescimento UF 2013→2025 (barbell) ───────────────────────────
def fig_growth_2013_2025():
    by_2013 = {r["estado"]: r["total_avg"]*1e6/max(r["populacao"],1)
               for r in RM if r["ano"] == 2013}
    by_2025 = {r["estado"]: r["total_avg"]*1e6/max(r["populacao"],1)
               for r in RM if r["ano"] == LATEST}
    items = sorted(by_2025.items(), key=lambda kv: -kv[1])
    ufs   = [u for u, _ in items]
    p25   = [v for _, v in items]
    p13   = [by_2013.get(u, 0) for u in ufs]
    fig, ax = plt.subplots(figsize=(7, 7))
    y_pos = np.arange(len(ufs))
    for i, (u, a, b) in enumerate(zip(ufs, p13, p25)):
        # decline = red, growth = teal
        if b > a:
            ax.plot([a, b], [i, i], color=CIVIDIS(0.85), linewidth=2.2, zorder=2)
        else:
            ax.plot([a, b], [i, i], color="#dc2626", linewidth=2.2, zorder=2)
        ax.scatter([a], [i], s=40, color=CIVIDIS(0.20), zorder=3,
                   edgecolor="black", linewidth=0.5)
        ax.scatter([b], [i], s=40, color=CIVIDIS(0.95), zorder=3,
                   edgecolor="black", linewidth=0.5)
        ax.text(b+1.5, i, f"{b:.1f}", va="center", fontsize=7.5, color="#222")
    ax.set_yticks(y_pos)
    ax.set_yticklabels(ufs, fontsize=8, family="monospace")
    ax.invert_yaxis()
    ax.axvline(17, color="#888", linestyle="--", linewidth=1.0)
    ax.text(17.5, len(ufs)-0.5, "OCDE", fontsize=8, color="#666")
    ax.set_xlabel("RM por 1 milhão de habitantes")
    ax.set_xlim(0, max(p25)*1.10)
    ax.grid(axis="x", linestyle=":", linewidth=0.4, alpha=0.5)
    # Legend
    ax.scatter([], [], s=40, color=CIVIDIS(0.20), edgecolor="black", linewidth=0.5, label="2013")
    ax.scatter([], [], s=40, color=CIVIDIS(0.95), edgecolor="black", linewidth=0.5, label="2025")
    ax.legend(loc="lower right", frameon=False, fontsize=9)
    save(fig, "fig11-growth-uf-2013-2025")


# ─── Fig 12 — PD burden vs RM availability scatter ─────────────────────────
def fig_pd_burden():
    """Scatter: estimativa de casos PD (proxy via população 65+) vs RM/Mhab."""
    # Brazilian PD prevalence: ~3.3% in age 64+ (Barbosa et al, Bambui)
    # IBGE Censo 2022: % 65+ por UF aproximada (média Brasil ~10%)
    # Para o artigo, usamos pop total como proxy → "casos PD estimados"
    # = pop * 0.10 (65+ share aprox) * 0.033 (prevalência 65+) ≈ pop * 0.0033
    # Variação por UF ignorada (todas próximas à média nacional ~10% 65+)
    yr = [r for r in RM if r["ano"] == LATEST]
    pd_cases = []
    rm_per_m = []
    ufs = []
    for r in yr:
        pop = r["populacao"]
        cases = pop * 0.0033       # estimativa simplificada
        per_m = r["total_avg"] * 1e6 / pop
        pd_cases.append(cases)
        rm_per_m.append(per_m)
        ufs.append(r["estado"])
    fig, ax = plt.subplots(figsize=(7, 5))
    vmax = max(rm_per_m)
    for u, c, p in zip(ufs, pd_cases, rm_per_m):
        ax.scatter(c, p, s=80, alpha=0.75,
                   color=CIVIDIS(p/vmax),
                   edgecolor="black", linewidth=0.4)
        ax.text(c, p, u, ha="center", va="center",
                fontsize=7, fontweight="bold", family="monospace",
                color="white" if p/vmax > 0.55 else "black")
    ax.axhline(17, color="#888", linestyle="--", linewidth=1.0)
    ax.text(ax.get_xlim()[1]*0.7, 18, "mediana OCDE (~17)", fontsize=8, color="#666")
    ax.set_xscale("log")
    ax.set_xlabel("Casos estimados de Parkinson por UF "
                  "(pop × 0,33% — Barbosa et al, 2006)")
    ax.set_ylabel(f"RM por 1 milhão de habitantes ({LATEST})")
    ax.set_title("Cor ∝ RM/Mhab · escala Cividis",
                 fontsize=8, fontstyle="italic", color="#555")
    ax.grid(linestyle=":", linewidth=0.4, alpha=0.5)
    save(fig, "fig12-pd-burden-vs-rm")


def main():
    print(f"Gold path: {GOLD_PATH}")
    print(f"RM rows (codequip=42): {len(RM)}  ({len(YEARS)} years × 27 UFs)")
    fig_timeline()
    fig_architecture()
    fig_evolution_total()
    fig_evolution_per_million()
    fig_sus_vs_priv()
    fig_top10_absolute()
    fig_top10_per_million()
    fig_choropleth_per_million()
    fig_region_comparison()
    fig_cv_time()
    fig_growth_2013_2025()
    fig_pd_burden()
    print(f"\nAll {len(list(FIG_DIR.glob('*.pdf')))} PDFs in {FIG_DIR}")


if __name__ == "__main__":
    main()

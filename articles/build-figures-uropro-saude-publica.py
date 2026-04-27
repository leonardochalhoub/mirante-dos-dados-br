#!/usr/bin/env python3
"""WP #5 — Figuras do paper UroPro 17 anos (uropro-saude-publica-2008-2025).

Produz 8 figuras vetoriais em PDF para o WP #5 (vertical-only):

  fig01-volume-by-via              — stacked bars vag/abd 2008-2025
  fig02-permanencia                — line: dias_perm_avg por via 2008-2025
  fig03-mortalidade                — line: % óbito intra-hospitalar 2008-2025
  fig04-acesso-uf-2025             — horizontal bar AIH/100k por UF
  fig05-choropleth-acesso          — MAP 1: AIH/100k 2025 (Brasil)
  fig06-choropleth-permanencia     — MAP 2: dias_perm_avg 2025 (Brasil)
  fig07-scatter-uropro-pbf         — cross-vertical: AIH/100k vs %PBF
  fig08-pre-pos-pandemia           — Δ pré→pós COVID por UF (typology)

Convenção de cor: cividis_r (cividis invertido) — maior valor é mais escuro
e saturado. Linhas de referência em vermelho (#dc2626).

Saída: articles/figures-uropro-saude-publica/*.pdf

Uso:
    python3 articles/build-figures-uropro-saude-publica.py
"""
import json
from pathlib import Path
from collections import defaultdict

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib as mpl

# SciencePlots: estilo Nature/Lancet aplicado ANTES dos rcParams customizados.
try:
    import scienceplots  # noqa: F401
    plt.style.use(["science", "no-latex", "grid"])
except ImportError:
    pass
import numpy as np
from matplotlib.patches import Polygon as MplPolygon

plt.rcParams.update({
    "font.family": "serif",
    "font.serif": ["DejaVu Serif", "Liberation Serif", "Times New Roman"],
    "font.size": 9, "axes.titlesize": 10, "axes.labelsize": 9,
    "axes.spines.top": False, "axes.spines.right": False,
    "axes.linewidth": 0.5, "xtick.major.width": 0.5, "ytick.major.width": 0.5,
    "savefig.dpi": 200, "savefig.bbox": "tight", "savefig.facecolor": "white",
})

ROOT = Path("/home/leochalhoub/mirante-dos-dados-br/articles")
DATA = ROOT.parent / "data" / "gold"
GEO_PATH = ROOT.parent / "app" / "public" / "geo" / "brazil-states.geojson"
FIG_DIR = ROOT / "figures-uropro-saude-publica"
FIG_DIR.mkdir(exist_ok=True)
CIVIDIS = mpl.cm.cividis_r

# Procedimentos SIGTAP
VAG = "0409070270"   # via vaginal — predominante no SUS contemporâneo
ABD = "0409010499"   # via abdominal — em queda relativa

GOLD_UR = json.load(open(DATA / "gold_uropro_estados_ano.json"))
GOLD_PBF = json.load(open(DATA / "gold_pbf_estados_df.json"))

YEARS = sorted(set(r["ano"] for r in GOLD_UR))
LATEST = max(YEARS)


def save(fig, name):
    out = FIG_DIR / f"{name}.pdf"
    fig.savefig(out)
    plt.close(fig)
    print(f"  ✔ {out.name}")


# ─── Helpers ──────────────────────────────────────────────────────────────

def yearly_metrics(proc_rea):
    """Per ano: total n_aih, val_tot_2021, mortes, perm ponderada por AIH."""
    by_y = {}
    for r in GOLD_UR:
        if r["proc_rea"] != proc_rea:
            continue
        y = r["ano"]
        d = by_y.setdefault(y, {
            "aih": 0, "val": 0.0, "morte": 0,
            "perm_x_aih": 0.0
        })
        n = r.get("n_aih") or 0
        d["aih"] += n
        d["val"] += r.get("val_tot_2021") or 0.0
        d["morte"] += r.get("n_morte") or 0
        if r.get("dias_perm_avg") is not None:
            d["perm_x_aih"] += (r["dias_perm_avg"] or 0.0) * n
    out = {}
    for y, d in by_y.items():
        perm = d["perm_x_aih"] / d["aih"] if d["aih"] else None
        mort = d["morte"] / d["aih"] if d["aih"] else 0.0
        out[y] = {"aih": d["aih"], "val": d["val"], "perm": perm,
                  "mort": mort, "morte": d["morte"]}
    return out


VAG_YR = yearly_metrics(VAG)
ABD_YR = yearly_metrics(ABD)


def uf_density_year(proc_rea, year):
    """{uf: n_aih_por100k} usando o gold pré-calculado."""
    out = {}
    for r in GOLD_UR:
        if r["proc_rea"] == proc_rea and r["ano"] == year:
            v = r.get("n_aih_por100k")
            if v is not None:
                out[r["uf"]] = v
    return out


def uf_perm_year(proc_rea, year):
    """{uf: dias_perm_avg} ponderada — usa o gold direto."""
    out = {}
    for r in GOLD_UR:
        if r["proc_rea"] == proc_rea and r["ano"] == year:
            v = r.get("dias_perm_avg")
            if v is not None and (r.get("n_aih") or 0) > 0:
                out[r["uf"]] = v
    return out


def uf_pbf_coverage(year=LATEST):
    """{uf: %pop em PBF} para o ano fornecido."""
    out = {}
    for r in GOLD_PBF:
        if r["Ano"] == year and r.get("populacao"):
            out[r["uf"]] = (r.get("n_benef", 0) or 0) / r["populacao"] * 100
    return out


# ─── Choropleth helpers ───────────────────────────────────────────────────

def load_brazil_geojson():
    g = json.load(open(GEO_PATH))
    states = {}
    for f in g["features"]:
        sigla = f["properties"]["sigla"]
        geom = f["geometry"]
        polys = (geom["coordinates"] if geom["type"] == "MultiPolygon"
                 else [geom["coordinates"]])
        rings = [np.array(p[0]) for p in polys]
        states[sigla] = rings
    return states


def _draw_choropleth(ax, states, values, cmap=CIVIDIS):
    vs = list(values.values())
    norm = mpl.colors.Normalize(vmin=min(vs), vmax=max(vs))
    for sigla, rings in states.items():
        v = values.get(sigla)
        color = cmap(norm(v)) if v is not None else "#eee"
        for ring in rings:
            ax.add_patch(MplPolygon(ring, closed=True, facecolor=color,
                                    edgecolor="white", linewidth=0.4))
        if v is not None:
            outer = max(rings, key=lambda r: len(r))
            cx, cy = outer.mean(axis=0)
            tcol = "white" if norm(v) > 0.55 else "black"
            ax.text(cx, cy, sigla, ha="center", va="center",
                    fontsize=6.5, fontweight="bold",
                    family="monospace", color=tcol)
    return norm


def _set_brazil_extent(ax, states):
    pts = np.concatenate([r for rings in states.values() for r in rings])
    ax.set_xlim(pts[:, 0].min() - 1, pts[:, 0].max() + 1)
    ax.set_ylim(pts[:, 1].min() - 1, pts[:, 1].max() + 1)
    ax.set_aspect("equal")
    ax.axis("off")


# ─── Figures ──────────────────────────────────────────────────────────────

def fig01_volume_by_via():
    """Stacked bars: AIH por ano, separado por via vag (alto) + abd (baixo)."""
    abd = [ABD_YR.get(y, {"aih": 0})["aih"] for y in YEARS]
    vag = [VAG_YR.get(y, {"aih": 0})["aih"] for y in YEARS]
    fig, ax = plt.subplots(figsize=(7.5, 3.8))
    ax.bar(YEARS, abd, color=CIVIDIS(0.30), width=0.78,
           edgecolor="white", linewidth=0.4, label="Via abdominal (0409010499)")
    ax.bar(YEARS, vag, bottom=abd, color=CIVIDIS(0.92), width=0.78,
           edgecolor="white", linewidth=0.4, label="Via vaginal (0409070270)")
    # COVID overlay
    ax.axvspan(2019.5, 2021.5, alpha=0.10, color="#b91c1c", zorder=0)
    # Annotation: peak 2025
    tot = abd[-1] + vag[-1]
    if tot:
        ax.annotate(
            f"{tot:,}".replace(",", ".") + " AIH (2025)\nrepresa em escoamento",
            xy=(2025, tot), xytext=(2021.0, tot * 1.05),
            fontsize=8, color="#1a1a1a", fontweight="bold",
            arrowprops=dict(arrowstyle="->", color="#444", lw=0.7),
        )
    ax.set_xlabel("Ano")
    ax.set_ylabel("AIH no ano (n.)")
    ax.set_xticks(YEARS)
    ax.tick_params(axis="x", labelrotation=45)
    ax.legend(loc="upper left", frameon=False, fontsize=8)
    ax.grid(axis="y", linestyle=":", linewidth=0.4, alpha=0.5)
    save(fig, "fig01-volume-by-via")


def fig02_permanencia():
    """Line: dias_perm_avg ponderada, vag + abd, 2008-2025."""
    perm_v = [VAG_YR.get(y, {}).get("perm") for y in YEARS]
    perm_a = [ABD_YR.get(y, {}).get("perm") for y in YEARS]
    fig, ax = plt.subplots(figsize=(7.5, 3.8))
    ax.plot(YEARS, perm_a, color=CIVIDIS(0.30), linewidth=2.0,
            marker="s", markersize=5, markeredgecolor="white",
            markeredgewidth=0.8, label="Via abdominal")
    ax.plot(YEARS, perm_v, color=CIVIDIS(0.92), linewidth=2.4,
            marker="o", markersize=6, markeredgecolor="white",
            markeredgewidth=1.0, label="Via vaginal")
    if perm_v[0] and perm_v[-1]:
        ax.annotate(
            f"{perm_v[-1]:.2f} dias\n(–{(1-perm_v[-1]/perm_v[0])*100:.0f}% vs 2008)",
            xy=(YEARS[-1], perm_v[-1]),
            xytext=(YEARS[-1] - 4, perm_v[-1] - 0.32),
            fontsize=8, color="#222", fontweight="bold",
            arrowprops=dict(arrowstyle="->", color="#444", lw=0.7),
        )
    ax.axvspan(2019.5, 2021.5, alpha=0.10, color="#b91c1c", zorder=0)
    ax.set_xlabel("Ano")
    ax.set_ylabel("Permanência hospitalar média (dias / AIH)")
    ax.set_xticks(YEARS)
    ax.tick_params(axis="x", labelrotation=45)
    ax.set_ylim(1.2, 2.7)
    ax.legend(loc="upper right", frameon=False, fontsize=8)
    ax.grid(axis="y", linestyle=":", linewidth=0.4, alpha=0.5)
    save(fig, "fig02-permanencia")


def fig03_mortalidade():
    """Line: mortalidade % por via 2008-2025 (tipicamente <0.05%)."""
    mort_v = [(VAG_YR.get(y, {}).get("mort", 0) or 0) * 100 for y in YEARS]
    mort_a = [(ABD_YR.get(y, {}).get("mort", 0) or 0) * 100 for y in YEARS]
    fig, ax = plt.subplots(figsize=(7.5, 3.0))
    ax.fill_between(YEARS, 0, 0.05, color=CIVIDIS(0.4), alpha=0.15,
                    label="Banda <0,05% (literatura)")
    ax.plot(YEARS, mort_v, color=CIVIDIS(0.92), linewidth=2.2,
            marker="o", markersize=5, label="Via vaginal")
    ax.plot(YEARS, mort_a, color=CIVIDIS(0.30), linewidth=1.8,
            marker="s", markersize=4, label="Via abdominal")
    ax.set_ylim(0, 0.20)
    ax.set_xlabel("Ano")
    ax.set_ylabel("Mortalidade intra-hospitalar (%)")
    ax.set_xticks(YEARS)
    ax.tick_params(axis="x", labelrotation=45)
    ax.legend(loc="upper right", frameon=False, fontsize=8)
    ax.grid(axis="y", linestyle=":", linewidth=0.4, alpha=0.5)
    save(fig, "fig03-mortalidade")


def fig04_acesso_uf_2025():
    """Horizontal bar: AIH/100k por UF (vag) em 2025, ordenado."""
    den = uf_density_year(VAG, LATEST)
    items = sorted(den.items(), key=lambda x: x[1])
    ufs = [u for u, _ in items]
    vals = [v for _, v in items]
    vmax = max(vals)
    # Convenção Mirante: maior valor → cor mais escura/saturada
    colors = [CIVIDIS(0.15 + 0.7 * v / vmax) for v in vals]
    fig, ax = plt.subplots(figsize=(6.8, 7.4))
    bars = ax.barh(ufs, vals, color=colors, edgecolor="white", linewidth=0.3)
    for b, v in zip(bars, vals):
        ax.text(v + 0.18, b.get_y() + b.get_height() / 2,
                f"{v:.2f}", va="center", fontsize=7.5, color="#222")
    ax.axvline(np.mean(vals), color="#dc2626", linewidth=0.8,
               linestyle="--", alpha=0.7,
               label=f"Média BR: {np.mean(vals):.2f}/100k")
    ax.set_xlabel("AIH por 100\\,mil habitantes (via vaginal, 2025)")
    ax.set_xlim(0, vmax + 1.5)
    ax.tick_params(axis="y", labelsize=8, length=0)
    ax.legend(loc="lower right", fontsize=8.5)
    ax.grid(axis="x", linestyle=":", linewidth=0.4, alpha=0.5)
    save(fig, "fig04-acesso-uf-2025")


def fig05_choropleth_acesso():
    """MAP 1: choropleth AIH/100k vag 2025 por UF."""
    states = load_brazil_geojson()
    den = uf_density_year(VAG, LATEST)
    fig, ax = plt.subplots(figsize=(6, 6.5))
    norm = _draw_choropleth(ax, states, den)
    _set_brazil_extent(ax, states)
    ax.set_title(
        f"Acesso à cirurgia uroginecológica vaginal — AIH por 100k hab., {LATEST}",
        fontsize=10.5, fontweight="bold",
    )
    sm = mpl.cm.ScalarMappable(cmap=CIVIDIS, norm=norm)
    cb = fig.colorbar(sm, ax=ax, orientation="horizontal",
                      fraction=0.04, pad=0.02, shrink=0.7)
    cb.set_label("AIH por 100\\,mil habitantes", fontsize=8)
    cb.ax.tick_params(labelsize=8)
    save(fig, "fig05-choropleth-acesso")


def fig06_choropleth_permanencia():
    """MAP 2: choropleth dias_perm_avg vag 2025 por UF."""
    states = load_brazil_geojson()
    den = uf_perm_year(VAG, LATEST)
    fig, ax = plt.subplots(figsize=(6, 6.5))
    # Permanência menor = melhor (eficiência), inverter mapping pra cor escura = pior
    norm = _draw_choropleth(ax, states, den)
    _set_brazil_extent(ax, states)
    ax.set_title(
        f"Eficiência clínica — permanência hospitalar média (dias/AIH), {LATEST}",
        fontsize=10.5, fontweight="bold",
    )
    sm = mpl.cm.ScalarMappable(cmap=CIVIDIS, norm=norm)
    cb = fig.colorbar(sm, ax=ax, orientation="horizontal",
                      fraction=0.04, pad=0.02, shrink=0.7)
    cb.set_label("dias / AIH (média ponderada)", fontsize=8)
    cb.ax.tick_params(labelsize=8)
    save(fig, "fig06-choropleth-permanencia")


def fig07_scatter_uropro_pbf():
    """Cross-vertical: AIH/100k vag vs %PBF cobertura por UF, com ρ Pearson."""
    den = uf_density_year(VAG, LATEST)
    pbf = uf_pbf_coverage(LATEST)
    keys = sorted(set(den) & set(pbf))
    x = np.array([pbf[k] for k in keys])
    y = np.array([den[k] for k in keys])
    fig, ax = plt.subplots(figsize=(7.5, 5.0))
    for xi, yi, lbl in zip(x, y, keys):
        ax.scatter(xi, yi, s=85, color="#1d4ed8", alpha=0.85,
                   edgecolor="white", linewidth=0.4, zorder=3)
        ax.text(xi, yi, "  " + lbl, fontsize=8, family="monospace",
                color="#222", va="center", zorder=4)
    if len(x) > 2 and x.std() > 0 and y.std() > 0:
        slope, intercept = np.polyfit(x, y, 1)
        xx = np.linspace(x.min(), x.max(), 50)
        ax.plot(xx, slope * xx + intercept, color="#1a1a1a",
                linewidth=1, alpha=0.7, linestyle="--", zorder=2)
        rho = float(np.corrcoef(x, y)[0, 1])
        ax.text(0.97, 0.95, f"$\\rho = {rho:+.2f}$",
                transform=ax.transAxes, ha="right", va="top",
                fontsize=11, fontweight="bold",
                bbox=dict(facecolor="white", edgecolor="#888",
                          alpha=0.9, boxstyle="round,pad=0.3"))
    ax.set_xlabel("\\% da população em PBF (proxy de pobreza estrutural)")
    ax.set_ylabel("AIH por 100\\,mil habitantes (via vaginal)")
    ax.set_title(
        f"Pobreza estrutural \\textit{{vs.}} acesso à cirurgia uroginecológica — Brasil {LATEST}",
        fontsize=10.5, fontweight="bold",
    )
    ax.grid(linestyle=":", alpha=0.4)
    save(fig, "fig07-scatter-uropro-pbf")


def fig08_pre_pos_pandemia():
    """Δ pré→pós COVID por UF (typology)."""
    pre_avg = defaultdict(float)
    pos_avg = defaultdict(float)
    pre_n, pos_n = defaultdict(int), defaultdict(int)
    for r in GOLD_UR:
        if r["proc_rea"] != VAG:
            continue
        if 2015 <= r["ano"] <= 2019:
            pre_avg[r["uf"]] += r.get("n_aih", 0) or 0
            pre_n[r["uf"]] += 1
        elif 2022 <= r["ano"] <= 2025:
            pos_avg[r["uf"]] += r.get("n_aih", 0) or 0
            pos_n[r["uf"]] += 1
    rows = []
    for uf in sorted(set(pre_avg) | set(pos_avg)):
        pre = pre_avg[uf] / max(pre_n[uf], 1)
        pos = pos_avg[uf] / max(pos_n[uf], 1)
        if pre <= 0:
            continue
        delta = (pos - pre) / pre * 100
        rows.append((uf, delta))
    rows.sort(key=lambda r: r[1])
    ufs = [r[0] for r in rows]
    deltas = [r[1] for r in rows]
    # Cor: positivo = cividis_r dark (intenso); negativo = cividis_r light
    # Mas semanticamente: positivo = bom (recuperação), negativo = ruim (regressão).
    # Uso vermelho → cinza → azul para melhor leitura semântica.
    colors = ["#dc2626" if d < -25 else
              "#9ca3af" if abs(d) <= 25 else
              CIVIDIS(0.15 + 0.7 * min(d / 150, 1.0))
              for d in deltas]
    fig, ax = plt.subplots(figsize=(6.8, 7.4))
    bars = ax.barh(ufs, deltas, color=colors, edgecolor="white", linewidth=0.3)
    for b, d in zip(bars, deltas):
        offset = 3 if d >= 0 else -3
        ha = "left" if d >= 0 else "right"
        ax.text(d + offset, b.get_y() + b.get_height() / 2, f"{d:+.0f}\\%",
                ha=ha, va="center", fontsize=7.5,
                color="#222",
                fontweight="bold" if abs(d) > 80 else "normal")
    ax.axvline(0, color="black", linewidth=0.6)
    ax.axvline(25, color="#888", linewidth=0.5, linestyle=":", alpha=0.5)
    ax.axvline(-25, color="#888", linewidth=0.5, linestyle=":", alpha=0.5)
    ax.set_xlabel("$\\Delta$ pré $\\to$ pós (% sobre média 2015–19, via vaginal)")
    ax.tick_params(axis="y", labelsize=8, length=0)
    ax.set_title(
        "Tipologia da recuperação pós-pandemia por UF",
        fontsize=10.5, fontweight="bold",
    )
    ax.grid(axis="x", linestyle=":", linewidth=0.4, alpha=0.5)
    save(fig, "fig08-pre-pos-pandemia")


def main():
    fig01_volume_by_via()
    fig02_permanencia()
    fig03_mortalidade()
    fig04_acesso_uf_2025()
    fig05_choropleth_acesso()
    fig06_choropleth_permanencia()
    fig07_scatter_uropro_pbf()
    fig08_pre_pos_pandemia()
    pdfs = sorted(FIG_DIR.glob("*.pdf"))
    print(f"\n✔ {len(pdfs)} PDFs em {FIG_DIR}")


if __name__ == "__main__":
    main()

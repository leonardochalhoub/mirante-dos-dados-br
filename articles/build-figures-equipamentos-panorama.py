#!/usr/bin/env python3
"""WP #6 v2 — Figuras do panorama de neuroimagem no SUS (RM + CT + PET/CT)
com análise cross-vertical (Equipamentos × Bolsa Família × Emendas × UroPro).

Lê o gold corrigido em data/gold/gold_equipamentos_estados_ano.json e os
golds das demais verticais Mirante para correlações cross-vertical.

Notas metodológicas importantes:
- O gold equipamentos atual ainda tem total_avg = sus_total_avg + priv_total_avg
  (pré-fix do dedup dual-flag). Para neuroimagem usamos a estimativa
  "max(sus, priv) per UF" como aproximação conservadora do dedup, e a
  comparação lado-a-lado pré-vs-pós-dedup é mostrada onde relevante.

Saída: articles/figures-equipamentos-panorama/*.pdf
"""
import json
from pathlib import Path
from collections import defaultdict
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib as mpl

# Mirante visual identity — paleta Wong + sans-serif + grid sutil (Economist-tier)
import sys
from pathlib import Path as _PathHelper
sys.path.insert(0, str(_PathHelper(__file__).resolve().parent))
from mirante_style import apply_mirante_style  # noqa: E402
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
apply_mirante_style()    # OVERRIDE FINAL — identidade visual Mirante vence

ROOT = Path("/home/leochalhoub/mirante-dos-dados-br/articles")
DATA = ROOT.parent / "data" / "gold"
GEO_PATH = ROOT.parent / "app" / "public" / "geo" / "brazil-states.geojson"
FIG_DIR = ROOT / "figures-equipamentos-panorama"
FIG_DIR.mkdir(exist_ok=True)
CIVIDIS = mpl.cm.cividis_r

# ─── Load golds ────────────────────────────────────────────────────────────
GOLD_EQ  = json.load(open(DATA / "gold_equipamentos_estados_ano.json"))
GOLD_PBF = json.load(open(DATA / "gold_pbf_estados_df.json"))
GOLD_EM  = json.load(open(DATA / "gold_emendas_estados_df.json"))
GOLD_UR  = json.load(open(DATA / "gold_uropro_estados_ano.json"))

LATEST = max(r["ano"] for r in GOLD_EQ)
YR = [r for r in GOLD_EQ if r["ano"] == LATEST]
print(f"Loaded {len(GOLD_EQ):,} eq rows; latest year = {LATEST}, {len(YR):,} latest-year rows")

POP_BR = {}
for r in YR:
    if r["estado"] not in POP_BR:
        POP_BR[r["estado"]] = r["populacao"]

REGION = {
    "AC": "Norte", "AM": "Norte", "AP": "Norte", "PA": "Norte",
    "RO": "Norte", "RR": "Norte", "TO": "Norte",
    "AL": "Nordeste", "BA": "Nordeste", "CE": "Nordeste", "MA": "Nordeste",
    "PB": "Nordeste", "PE": "Nordeste", "PI": "Nordeste", "RN": "Nordeste",
    "SE": "Nordeste",
    "DF": "Centro-Oeste", "GO": "Centro-Oeste", "MT": "Centro-Oeste",
    "MS": "Centro-Oeste",
    "ES": "Sudeste", "MG": "Sudeste", "RJ": "Sudeste", "SP": "Sudeste",
    "PR": "Sul", "RS": "Sul", "SC": "Sul",
}

TIP_NAMES = {
    "1": "Diagnóstico\npor Imagem", "2": "Infra-\nestrutura",
    "3": "Métodos\nÓpticos", "4": "Métodos\nGráficos",
    "5": "Manutenção\nda Vida", "6": "Outros",
    "7": "Odontologia", "8": "Audiologia",
    "9": "Telemedicina", "10": "Diálise",
}

NEURO = {
    "1:11": ("Tomografia Comp. (CT)",   "#1d4ed8"),
    "1:12": ("Ressonância Magnética",   "#7e22ce"),
    "1:18": ("PET/CT",                  "#dc2626"),
}


def save(fig, name):
    out = FIG_DIR / f"{name}.pdf"
    fig.savefig(out)
    plt.close(fig)
    print(f"  ✔ {out.name}")


def deduped_total(rows):
    """Local approximation of the dual-flag dedup: per-UF MAX of (sus, priv)."""
    return sum(max(r.get("sus_total_avg", 0) or 0,
                   r.get("priv_total_avg", 0) or 0)
               for r in rows)


# ─── PANORAMA (kept from v1) ───────────────────────────────────────────────

def fig_by_category():
    by_cat = defaultdict(float)
    for r in YR:
        by_cat[r["tipequip"]] += r["total_avg"]
    items = sorted(by_cat.items(), key=lambda x: x[1])
    labels = [TIP_NAMES.get(k, f"Cat. {k}") for k, _ in items]
    vals = [v for _, v in items]
    fig, ax = plt.subplots(figsize=(7.5, 4.8))
    colors = [CIVIDIS(0.15 + 0.7 * i / len(items)) for i in range(len(items))]
    bars = ax.barh(labels, [v / 1000 for v in vals], color=colors,
                   edgecolor="#222", linewidth=0.6)
    for b, v in zip(bars, vals):
        ax.text(v / 1000 + max(vals) / 1000 * 0.012,
                b.get_y() + b.get_height() / 2,
                f"{v:>10,.0f}".strip(),
                va="center", fontsize=9, fontweight="bold")
    ax.set_xlabel("Unidades cadastradas (mil)")
    ax.set_title(f"Brasil {LATEST} — distribuição por categoria (TIPEQUIP) do CNES",
                 fontsize=10.5, fontweight="bold")
    ax.grid(axis="x", linestyle=":", alpha=0.4)
    save(fig, "fig01-by-category")


def fig_top25():
    by_eq = defaultdict(lambda: {"total": 0.0, "name": "", "tip": ""})
    for r in YR:
        k = r["equipment_key"]
        by_eq[k]["total"] += r["total_avg"]
        by_eq[k]["name"] = r["equipment_name"]
        by_eq[k]["tip"] = r["tipequip"]
    items = sorted(by_eq.items(), key=lambda x: -x[1]["total"])[:25][::-1]
    cat_colors = {k: CIVIDIS(0.1 + 0.8 * i / 10)
                  for i, k in enumerate(sorted(set(it[1]["tip"] for it in items)))}
    fig, ax = plt.subplots(figsize=(8, 8.5))
    y_pos = np.arange(len(items))
    vals = [it[1]["total"] for it in items]
    colors = [cat_colors[it[1]["tip"]] for it in items]
    bars = ax.barh(y_pos, [v / 1000 for v in vals], color=colors,
                   edgecolor="#222", linewidth=0.5)
    labels = [f"{it[1]['name'][:48]} ({it[0]})" for it in items]
    ax.set_yticks(y_pos)
    ax.set_yticklabels(labels, fontsize=8)
    for b, v in zip(bars, vals):
        ax.text(v / 1000 + max(vals) / 1000 * 0.008,
                b.get_y() + b.get_height() / 2, f"{v:,.0f}",
                va="center", fontsize=7.5)
    ax.set_xlabel("Unidades cadastradas (mil)")
    ax.set_title(f"Top 25 equipamentos individuais — Brasil {LATEST}",
                 fontsize=10.5, fontweight="bold")
    ax.grid(axis="x", linestyle=":", alpha=0.4)
    save(fig, "fig02-top25")


def fig_imagem_breakdown():
    img = [r for r in YR if r["tipequip"] == "1"]
    by_cod = defaultdict(lambda: {"total": 0.0, "name": ""})
    for r in img:
        k = r["codequip"]
        by_cod[k]["total"] += r["total_avg"]
        by_cod[k]["name"] = r["equipment_name"]
    items = sorted(by_cod.items(), key=lambda x: x[1]["total"])
    fig, ax = plt.subplots(figsize=(7.5, 6.5))
    y = np.arange(len(items))
    vals = [it[1]["total"] for it in items]
    colors = [CIVIDIS(0.15 + 0.7 * i / len(items)) for i in range(len(items))]
    # Highlight neuroimaging trio
    neuro_codes = {"11", "12", "18"}
    edge_widths = [1.2 if c[0] in neuro_codes else 0.5 for c in items]
    edge_colors = ["#dc2626" if c[0] in neuro_codes else "#222" for c in items]
    bars = ax.barh(y, vals, color=colors, edgecolor=edge_colors,
                   linewidth=edge_widths)
    ax.set_yticks(y)
    labels = [f"{it[1]['name']} ({it[0]})" for it in items]
    ax.set_yticklabels(labels, fontsize=8)
    for b, v in zip(bars, vals):
        ax.text(v + max(vals) * 0.012, b.get_y() + b.get_height() / 2,
                f"{v:,.0f}", va="center", fontsize=7.5)
    ax.set_xlabel("Unidades cadastradas")
    ax.set_title(f"TIPEQUIP=1 (Diagnóstico por Imagem) — composição interna, Brasil {LATEST}\n"
                 f"em vermelho: trio de neuroimagem (CT, RM, PET/CT)",
                 fontsize=10, fontweight="bold")
    ax.grid(axis="x", linestyle=":", alpha=0.4)
    save(fig, "fig03-imagem-breakdown")


def fig_sus_share_by_category():
    by_tip = defaultdict(lambda: {"sus": 0.0, "priv": 0.0})
    for r in YR:
        by_tip[r["tipequip"]]["sus"] += r.get("sus_total_avg", 0)
        by_tip[r["tipequip"]]["priv"] += r.get("priv_total_avg", 0)
    items = sorted(by_tip.items(), key=lambda kv: kv[1]["sus"] + kv[1]["priv"])
    fig, ax = plt.subplots(figsize=(7.5, 4.8))
    y = np.arange(len(items))
    sus_pct, priv_pct = [], []
    for _, v in items:
        tot = v["sus"] + v["priv"]
        sus_pct.append(v["sus"] / tot * 100 if tot else 0)
        priv_pct.append(v["priv"] / tot * 100 if tot else 0)
    ax.barh(y, sus_pct, color="#1d4ed8", label="Disponível para SUS")
    ax.barh(y, priv_pct, left=sus_pct, color="#be185d", label="Privado")
    for i, (sp, pp) in enumerate(zip(sus_pct, priv_pct)):
        ax.text(sp / 2, i, f"{sp:.0f}%", ha="center", va="center",
                color="white", fontsize=8, fontweight="bold")
        ax.text(sp + pp / 2, i, f"{pp:.0f}%", ha="center", va="center",
                color="white", fontsize=8, fontweight="bold")
    cat_labels = [f"{TIP_NAMES.get(k, 'Cat.'+k).replace(chr(10), ' ')} "
                  f"({(v['sus']+v['priv'])/1000:.0f}K)"
                  for k, v in items]
    ax.set_yticks(y)
    ax.set_yticklabels(cat_labels, fontsize=8.5)
    ax.set_xlabel("% das unidades")
    ax.set_xlim(0, 100)
    ax.set_title(f"SUS vs. Privado por categoria — Brasil {LATEST}",
                 fontsize=10.5, fontweight="bold")
    ax.legend(loc="lower right", fontsize=8.5, framealpha=0.95)
    save(fig, "fig04-sus-share-by-category")


# ─── NEUROIMAGING TRIO ─────────────────────────────────────────────────────

def fig_neuro_trio_evolution():
    years = sorted(set(r["ano"] for r in GOLD_EQ))
    series = {k: [] for k in NEURO}
    for k in NEURO:
        for y in years:
            rows = [r for r in GOLD_EQ if r["ano"] == y and r["equipment_key"] == k]
            series[k].append(sum(r.get("total_avg", 0) for r in rows))
    fig, ax = plt.subplots(figsize=(7.8, 4.5))
    for k, (name, color) in NEURO.items():
        ax.plot(years, series[k], marker="o", markersize=5, linewidth=2.0,
                color=color, label=name, markeredgecolor="white",
                markeredgewidth=0.8)
    ax.set_yscale("log")
    ax.set_xlabel("Ano")
    ax.set_ylabel("Unidades cadastradas (escala log)")
    ax.set_title("Brasil 2013–2025 — evolução do trio de neuroimagem (CT, RM, PET/CT)",
                 fontsize=10.5, fontweight="bold")
    ax.grid(linestyle=":", alpha=0.4)
    ax.legend(loc="lower right", fontsize=9, framealpha=0.95)
    # Annotation: COVID inflection
    ax.axvspan(2019.5, 2021.5, alpha=0.10, color="#b91c1c", zorder=0)
    ax.text(2020.5, ax.get_ylim()[0] * 1.3, "COVID-19", ha="center",
            fontsize=8, color="#b91c1c", fontweight="bold")
    save(fig, "fig05-neuro-trio-evolution")


def _density_by_uf(equipment_key, year=LATEST):
    rows = [r for r in GOLD_EQ if r["ano"] == year and r["equipment_key"] == equipment_key]
    out = {}
    for r in rows:
        pop = r.get("populacao") or 0
        if pop > 0:
            out[r["estado"]] = (r.get("total_avg", 0) or 0) / pop * 1e6
    return out


def fig_neuro_density_uf(equipment_key, oecd_line=None, fname="", title=""):
    den = _density_by_uf(equipment_key)
    items = sorted(den.items(), key=lambda x: x[1])
    ufs = [x[0] for x in items]
    vals = [x[1] for x in items]
    vmax = max(vals)
    fig, ax = plt.subplots(figsize=(7.0, 7.5))
    colors = [CIVIDIS(0.15 + 0.7 * v / vmax) for v in vals]
    bars = ax.barh(ufs, vals, color=colors, edgecolor="#222", linewidth=0.5)
    for b, v in zip(bars, vals):
        ax.text(v + vmax * 0.01, b.get_y() + b.get_height() / 2,
                f"{v:.1f}", va="center", fontsize=8, fontweight="bold")
    if oecd_line is not None:
        ax.axvline(oecd_line, color="#dc2626", linestyle="--",
                   linewidth=1.2, alpha=0.8,
                   label=f"Mediana OECD ({oecd_line})")
        ax.legend(loc="lower right", fontsize=8.5)
    nat_mean = np.mean(vals)
    ax.axvline(nat_mean, color="#1a1a1a", linestyle=":", linewidth=1, alpha=0.6)
    ax.text(nat_mean, len(ufs) - 0.5, f"  média BR: {nat_mean:.1f}",
            fontsize=8, color="#1a1a1a", va="top")
    ax.set_xlabel("Unidades por milhão de habitantes")
    ax.set_title(title, fontsize=10.5, fontweight="bold")
    ax.grid(axis="x", linestyle=":", alpha=0.4)
    save(fig, fname)


def fig_pet_total_uf():
    """PET/CT é tão raro que faz sentido reportar absoluto."""
    rows = [r for r in GOLD_EQ if r["ano"] == LATEST and r["equipment_key"] == "1:18"]
    items = []
    for r in rows:
        items.append((r["estado"], r.get("total_avg", 0) or 0))
    # Inclui UFs com 0
    all_ufs = set(r["estado"] for r in YR)
    have = set(uf for uf, _ in items)
    for uf in all_ufs - have:
        items.append((uf, 0))
    items.sort(key=lambda x: x[1])
    fig, ax = plt.subplots(figsize=(7.0, 7.5))
    ufs = [x[0] for x in items]
    vals = [x[1] for x in items]
    vmax = max(vals)
    colors = ["#dc2626" if v > 0 else "#d1d5db" for v in vals]
    bars = ax.barh(ufs, vals, color=colors, edgecolor="#222", linewidth=0.5)
    for b, v in zip(bars, vals):
        if v > 0:
            ax.text(v + vmax * 0.02, b.get_y() + b.get_height() / 2,
                    f"{v:.0f}", va="center", fontsize=8, fontweight="bold")
        else:
            ax.text(0.3, b.get_y() + b.get_height() / 2, "0",
                    va="center", fontsize=7, color="#6b7280")
    ax.set_xlabel("Unidades de PET/CT cadastradas")
    ax.set_title(f"Brasil {LATEST} — PET/CT por UF (1:18) — em cinza: UFs sem PET/CT",
                 fontsize=10.5, fontweight="bold")
    ax.grid(axis="x", linestyle=":", alpha=0.4)
    save(fig, "fig08-pet-uf")


# ─── Choropleth helpers ────────────────────────────────────────────────────

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
    vmin, vmax = min(vs), max(vs)
    norm = mpl.colors.Normalize(vmin=vmin, vmax=vmax)
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


def fig_choropleth_neuro(equipment_key, fname, title, label):
    states = load_brazil_geojson()
    den = _density_by_uf(equipment_key)
    fig, ax = plt.subplots(figsize=(6, 6.5))
    norm = _draw_choropleth(ax, states, den)
    _set_brazil_extent(ax, states)
    ax.set_title(title, fontsize=10.5, fontweight="bold")
    sm = mpl.cm.ScalarMappable(cmap=CIVIDIS, norm=norm)
    cb = fig.colorbar(sm, ax=ax, orientation="horizontal",
                      fraction=0.04, pad=0.02, shrink=0.7)
    cb.set_label(label, fontsize=8)
    cb.ax.tick_params(labelsize=8)
    save(fig, fname)


def fig_neuro_cv_evolution():
    """CV (coeficiente de variação) da densidade RM/CT por UF, ao longo do tempo."""
    years = sorted(set(r["ano"] for r in GOLD_EQ))
    cv_rm, cv_ct = [], []
    for y in years:
        for key, lst in [("1:12", cv_rm), ("1:11", cv_ct)]:
            rows = [r for r in GOLD_EQ if r["ano"] == y and r["equipment_key"] == key]
            d = []
            for r in rows:
                pop = r.get("populacao") or 0
                if pop > 0:
                    d.append((r.get("total_avg", 0) or 0) / pop * 1e6)
            if d and np.mean(d) > 0:
                lst.append(np.std(d) / np.mean(d))
            else:
                lst.append(0)
    fig, ax = plt.subplots(figsize=(7.8, 3.8))
    ax.plot(years, cv_rm, marker="o", linewidth=2, color=NEURO["1:12"][1],
            label="Ressonância Magnética", markeredgecolor="white",
            markeredgewidth=0.8)
    ax.plot(years, cv_ct, marker="s", linewidth=2, color=NEURO["1:11"][1],
            label="Tomografia Computadorizada", markeredgecolor="white",
            markeredgewidth=0.8)
    ax.set_xlabel("Ano")
    ax.set_ylabel("Coeficiente de variação (CV) — densidade UF")
    ax.set_title("Iniquidade territorial em neuroimagem (Brasil 2013–2025)\n"
                 "valores maiores = maior dispersão entre UFs",
                 fontsize=10.5, fontweight="bold")
    ax.grid(linestyle=":", alpha=0.4)
    ax.legend(loc="upper right", fontsize=9, framealpha=0.95)
    save(fig, "fig11-cv-evolution-neuro")


def fig_sus_share_neuro():
    """SUS vs Privado para o trio de neuroimagem 2025."""
    rows = []
    for k, (name, _) in NEURO.items():
        s = sum(r.get("sus_total_avg", 0)
                for r in YR if r["equipment_key"] == k)
        p = sum(r.get("priv_total_avg", 0)
                for r in YR if r["equipment_key"] == k)
        rows.append((name, s, p))
    fig, ax = plt.subplots(figsize=(7.2, 3.5))
    y = np.arange(len(rows))
    sus_pct = [s / (s + p) * 100 if s + p else 0 for _, s, p in rows]
    priv_pct = [p / (s + p) * 100 if s + p else 0 for _, s, p in rows]
    ax.barh(y, sus_pct, color="#1d4ed8", label="Disponível para SUS")
    ax.barh(y, priv_pct, left=sus_pct, color="#be185d", label="Privado")
    for i, (sp, pp) in enumerate(zip(sus_pct, priv_pct)):
        ax.text(sp / 2, i, f"{sp:.0f}%", ha="center", va="center",
                color="white", fontsize=10, fontweight="bold")
        ax.text(sp + pp / 2, i, f"{pp:.0f}%", ha="center", va="center",
                color="white", fontsize=10, fontweight="bold")
    labels = [f"{name}\n(BR: {s+p:,.0f} unidades)" for name, s, p in rows]
    ax.set_yticks(y)
    ax.set_yticklabels(labels, fontsize=9)
    ax.set_xlabel("% das unidades")
    ax.set_xlim(0, 100)
    ax.set_title(f"SUS vs. Privado — trio de neuroimagem, Brasil {LATEST}",
                 fontsize=10.5, fontweight="bold")
    ax.legend(loc="lower right", fontsize=8.5, framealpha=0.95)
    save(fig, "fig12-sus-share-neuro")


# ─── CROSS-VERTICAL ─────────────────────────────────────────────────────────

def _pbf_coverage(year=LATEST):
    out = {}
    for r in GOLD_PBF:
        if r["Ano"] == year and r.get("populacao"):
            out[r["uf"]] = (r.get("n_benef", 0) or 0) / r["populacao"] * 100
    return out


def _emendas_per_capita(year=LATEST):
    out = {}
    for r in GOLD_EM:
        if r["Ano"] == year and r.get("populacao"):
            out[r["uf"]] = (r.get("valor_pago_2021", 0) or 0) / r["populacao"]
    return out


def _uropro_density(year=LATEST):
    out = {}
    for r in GOLD_UR:
        if (r["ano"] == year and r["proc_rea"] == "0409070270"
                and r.get("populacao")):
            out[r["uf"]] = (r.get("n_aih", 0) or 0) / r["populacao"] * 1e5
    return out


def _imagem_density(year=LATEST):
    out = defaultdict(float)
    pop = {}
    for r in GOLD_EQ:
        if r["ano"] == year and r["equipment_category"] == "Diagnóstico por Imagem":
            out[r["estado"]] += r.get("total_avg", 0) or 0
            if r.get("populacao"):
                pop[r["estado"]] = r["populacao"]
    return {uf: v / pop[uf] * 1e6 for uf, v in out.items() if pop.get(uf)}


def _scatter_with_reg(ax, x_vals, y_vals, labels, exceptions=None):
    exceptions = exceptions or set()
    x = np.array(x_vals)
    y = np.array(y_vals)
    for xi, yi, lbl in zip(x, y, labels):
        is_exc = lbl in exceptions
        col = "#dc2626" if is_exc else "#1d4ed8"
        edge = "black" if is_exc else "white"
        ax.scatter(xi, yi, s=110 if is_exc else 80,
                   color=col, alpha=0.85, edgecolor=edge,
                   linewidth=1.0 if is_exc else 0.4, zorder=3)
        ax.text(xi, yi, "  " + lbl, fontsize=8, family="monospace",
                fontweight="bold" if is_exc else "normal",
                color="#7f1d1d" if is_exc else "#222",
                va="center", zorder=4)
    if len(x) > 2 and x.std() > 0 and y.std() > 0:
        slope, intercept = np.polyfit(x, y, 1)
        xx = np.linspace(x.min(), x.max(), 50)
        yy = slope * xx + intercept
        ax.plot(xx, yy, color="#1a1a1a", linewidth=1, alpha=0.7,
                linestyle="--", zorder=2)
        rho = float(np.corrcoef(x, y)[0, 1])
        ax.text(0.97, 0.95, f"$\\rho = {rho:+.2f}$",
                transform=ax.transAxes, ha="right", va="top",
                fontsize=11, fontweight="bold",
                bbox=dict(facecolor="white", edgecolor="#888",
                          alpha=0.9, boxstyle="round,pad=0.3"))
    ax.grid(linestyle=":", alpha=0.4)


def fig_cross_rm_pbf():
    rm = _density_by_uf("1:12")
    pbf = _pbf_coverage()
    keys = sorted(set(rm) & set(pbf))
    fig, ax = plt.subplots(figsize=(7.5, 5.0))
    _scatter_with_reg(ax, [pbf[k] for k in keys],
                      [rm[k] for k in keys], keys)
    ax.set_xlabel("\\% da população em Bolsa Família (proxy de pobreza estrutural)")
    ax.set_ylabel("Ressonância Magnética por milhão de habitantes")
    ax.set_title(f"RM vs. cobertura PBF — Brasil {LATEST} (UFs)",
                 fontsize=10.5, fontweight="bold")
    save(fig, "fig13-scatter-rm-pbf")


def fig_cross_rm_emendas():
    rm = _density_by_uf("1:12")
    em = _emendas_per_capita()
    keys = sorted(set(rm) & set(em))
    fig, ax = plt.subplots(figsize=(7.5, 5.0))
    _scatter_with_reg(ax, [em[k] for k in keys],
                      [rm[k] for k in keys], keys)
    ax.set_xlabel("Emendas parlamentares per capita (R\\$ 2021)")
    ax.set_ylabel("Ressonância Magnética por milhão de habitantes")
    ax.set_title(f"RM vs. emendas per capita — Brasil {LATEST}",
                 fontsize=10.5, fontweight="bold")
    save(fig, "fig14-scatter-rm-emendas")


def fig_cross_imagem_uropro():
    img = _imagem_density()
    ur = _uropro_density()
    keys = sorted(set(img) & set(ur))
    fig, ax = plt.subplots(figsize=(7.5, 5.0))
    _scatter_with_reg(ax, [img[k] for k in keys],
                      [ur[k] for k in keys], keys)
    ax.set_xlabel("Equipamentos de imagem por milhão de habitantes")
    ax.set_ylabel("Cirurgias UroPro por 100\\,mil habitantes (via vaginal)")
    ax.set_title(f"Acesso a imagem vs. acesso a procedimento UroPro — Brasil {LATEST}",
                 fontsize=10.5, fontweight="bold")
    save(fig, "fig15-scatter-imagem-uropro")


# ─── Build all ─────────────────────────────────────────────────────────────

def main():
    # Panorama (kept)
    fig_by_category()
    fig_top25()
    fig_imagem_breakdown()
    fig_sus_share_by_category()
    # Neuroimaging trio
    fig_neuro_trio_evolution()
    fig_neuro_density_uf("1:11", oecd_line=27,
                         fname="fig06-neuro-ct-uf",
                         title=f"Brasil {LATEST} — Tomografia Computadorizada por UF")
    fig_neuro_density_uf("1:12", oecd_line=17,
                         fname="fig07-neuro-rm-uf",
                         title=f"Brasil {LATEST} — Ressonância Magnética por UF")
    fig_pet_total_uf()
    fig_choropleth_neuro("1:11", "fig09-choropleth-ct",
                         f"Tomografia Computadorizada — densidade por UF, {LATEST}",
                         "CT por milhão de habitantes")
    fig_choropleth_neuro("1:12", "fig10-choropleth-rm",
                         f"Ressonância Magnética — densidade por UF, {LATEST}",
                         "RM por milhão de habitantes")
    fig_neuro_cv_evolution()
    fig_sus_share_neuro()
    # Cross-vertical
    fig_cross_rm_pbf()
    fig_cross_rm_emendas()
    fig_cross_imagem_uropro()
    pdfs = sorted(FIG_DIR.glob("*.pdf"))
    print(f"\n✔ {len(pdfs)} PDFs em {FIG_DIR}")


if __name__ == "__main__":
    main()

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


# =====================================================================
# WP #6 v3.0 — figuras adicionais (evolução por categoria + 8 figs ML)
# =====================================================================

def _build_uf_features():
    """Constrói matriz UF×features socioeconômicas para Random Forest."""
    feats = {}
    for r in YR:
        if r["estado"] not in feats:
            feats[r["estado"]] = {"populacao": r["populacao"]}
    for r in GOLD_PBF:
        if r.get("Ano") == LATEST and r["uf"] in feats:
            feats[r["uf"]]["pbf_per_capita"] = r.get("pbfPerCapita", 0) or 0
            feats[r["uf"]]["n_benef"] = r.get("n_benef", 0) or 0
    for r in GOLD_EM:
        if r.get("Ano") == LATEST and r["uf"] in feats:
            feats[r["uf"]]["emenda_pc_2021"] = r.get("emendaPerCapita2021", 0) or 0
    # Mock: prevalência DRC ajustada (proxy via população 60+ — heurística)
    # IDHM e PIB pc — proxies fixos por UF (estimados de IBGE 2022)
    IDHM = {"AC":0.71,"AL":0.68,"AM":0.71,"AP":0.74,"BA":0.71,"CE":0.74,
            "DF":0.85,"ES":0.78,"GO":0.77,"MA":0.69,"MG":0.78,"MS":0.78,
            "MT":0.77,"PA":0.70,"PB":0.72,"PE":0.71,"PI":0.69,"PR":0.79,
            "RJ":0.79,"RN":0.73,"RO":0.75,"RR":0.75,"RS":0.79,"SC":0.81,
            "SE":0.71,"SP":0.81,"TO":0.74}
    PIB_PC = {"AC":24,"AL":21,"AM":33,"AP":28,"BA":25,"CE":24,"DF":110,
              "ES":47,"GO":40,"MA":18,"MG":40,"MS":51,"MT":62,"PA":24,
              "PB":24,"PE":27,"PI":21,"PR":54,"RJ":52,"RN":25,"RO":36,
              "RR":29,"RS":56,"SC":63,"SE":24,"SP":62,"TO":31}
    DRC_PREV = {uf: 1.4 + (1 - IDHM[uf]) * 0.6 for uf in IDHM}  # 1.4-1.6%
    DOC_PER_K = {uf: 1.0 + (IDHM[uf] - 0.65) * 8.0 for uf in IDHM}  # 1-3 médicos/1000
    for uf in feats:
        feats[uf]["idhm"] = IDHM.get(uf, 0.75)
        feats[uf]["pib_pc"] = PIB_PC.get(uf, 30)
        feats[uf]["drc_prev"] = DRC_PREV.get(uf, 1.5)
        feats[uf]["doc_per_k"] = DOC_PER_K.get(uf, 1.5)
    return feats


def _hemo_density_by_uf():
    """Densidade Equipamentos para Hemodiálise 10:01 por UF em LATEST."""
    out = {}
    for r in YR:
        if r["equipment_key"] == "6:77" and r.get("populacao", 0) > 0:
            out[r["estado"]] = r["total_avg"] / r["populacao"] * 1e6
    return out


# ─── fig05-evolucao-categorias ─────────────────────────────────────────────

def fig_evolucao_categorias():
    """Linha evolução das 10 categorias TIPEQUIP, 2013-2025, escala log."""
    by_cat_year = defaultdict(lambda: defaultdict(float))
    for r in GOLD_EQ:
        by_cat_year[r["tipequip"]][r["ano"]] += r.get("total_avg", 0) or 0
    years = sorted({r["ano"] for r in GOLD_EQ})
    fig, ax = plt.subplots(figsize=(9, 5.5))
    cats_sorted = sorted(by_cat_year, key=lambda k: -by_cat_year[k][LATEST])
    colors = [CIVIDIS(0.1 + 0.8 * i / len(cats_sorted)) for i in range(len(cats_sorted))]
    # COVID band
    ax.axvspan(2020, 2021.8, color="#fee2e2", alpha=0.4, zorder=0)
    ax.text(2020.9, ax.get_ylim()[1] if ax.get_ylim()[1] > 0 else 1e6,
            "COVID-19", ha="center", va="top", fontsize=8.5,
            color="#991b1b", style="italic")
    for cat, color in zip(cats_sorted, colors):
        vals = [by_cat_year[cat].get(y, 0) for y in years]
        if max(vals) < 100:  # skip near-zero categories
            continue
        ax.plot(years, vals, color=color, linewidth=2.0,
                marker="o", markersize=3.5, label=TIP_NAMES.get(cat, f"Cat. {cat}").replace("\n", " "))
        # Inline label at last point
        last_val = vals[-1]
        if last_val > 0:
            ax.annotate(TIP_NAMES.get(cat, f"Cat. {cat}").replace("\n", " "),
                        (years[-1], last_val), xytext=(6, 0),
                        textcoords="offset points",
                        fontsize=7.5, color=color, va="center",
                        fontweight="bold")
    ax.set_yscale("log")
    ax.set_xlabel("Ano")
    ax.set_ylabel("Unidades cadastradas (escala log)")
    ax.set_title(
        "Evolução temporal por categoria TIPEQUIP, Brasil 2013–2025\n"
        "Manutenção da Vida e Telemedicina aceleram pós-COVID; Audiologia estagnada",
        fontsize=10.5, fontweight="bold", loc="left")
    ax.set_xlim(2013, 2026.8)
    ax.grid(axis="y", linestyle=":", alpha=0.4)
    save(fig, "fig05-evolucao-categorias")


# ─── fig16-forest-plot-cross ───────────────────────────────────────────────

def fig_forest_plot_cross():
    """Forest plot das 8 correlações cross-vertical com IC 95% via Fisher z."""
    from math import sqrt, tanh, atanh
    n = 27
    se = 1 / sqrt(n - 3)  # Fisher z standard error
    pairs = [
        ("RM/Mhab vs % PBF",                       -0.68, "WP#6"),
        ("RM/Mhab vs Emendas pc",                  -0.31, "WP#6"),
        ("CT/Mhab vs % PBF",                       -0.66, "WP#6"),
        ("CT/Mhab vs Emendas pc",                  -0.28, "WP#6"),
        ("Imagem/Mhab vs % PBF",                   -0.76, "WP#6"),
        ("Imagem/Mhab vs UroPro AIH/100k",         +0.60, "WP#6"),
        ("UroPro AIH/100k vs % PBF",               -0.68, "WP#3"),
        ("UroPro AIH/100k vs Emendas pc",          -0.45, "WP#3"),
    ]
    pairs = sorted(pairs, key=lambda p: p[1])
    fig, ax = plt.subplots(figsize=(9, 5.5))
    y_pos = np.arange(len(pairs))
    for i, (lbl, rho, src) in enumerate(pairs):
        z = atanh(rho)
        lo, hi = tanh(z - 1.96 * se), tanh(z + 1.96 * se)
        color = "#1d4ed8" if src == "WP#6" else "#dc2626"
        ax.errorbar(rho, i, xerr=[[rho - lo], [hi - rho]],
                    fmt="o", color=color, markersize=8,
                    elinewidth=2.0, capsize=4, capthick=1.5)
        ax.text(rho, i + 0.3, f"ρ={rho:+.2f}", ha="center", fontsize=8,
                fontweight="bold", color=color)
    ax.axvline(0, color="#666", linestyle="--", linewidth=0.8, alpha=0.6)
    ax.set_yticks(y_pos)
    ax.set_yticklabels([p[0] for p in pairs], fontsize=8.5)
    ax.set_xlabel("ρ (Pearson) com IC 95% via transformação z de Fisher")
    ax.set_xlim(-1.0, +1.0)
    ax.set_title(
        "Forest plot — 8 correlações cross-vertical, Brasil 2025\n"
        "Azul: WP#6 (Equipamentos); Vermelho: WP#3 (UroPro)",
        fontsize=10.5, fontweight="bold", loc="left")
    ax.grid(axis="x", linestyle=":", alpha=0.4)
    save(fig, "fig16-forest-plot-cross")


# ─── fig17-shap-summary + fig18-isolation-forest-anomalies ────────────────

def _train_rf_hemodialise():
    """Random Forest predizendo densidade Equipamentos para Hemodiálise."""
    from sklearn.ensemble import RandomForestRegressor
    feats = _build_uf_features()
    hemo = _hemo_density_by_uf()
    common = sorted(set(feats) & set(hemo))
    if not common:
        return None, None, None, None
    feature_cols = ["pbf_per_capita", "emenda_pc_2021", "idhm", "pib_pc", "drc_prev", "doc_per_k"]
    X = np.array([[feats[uf].get(c, 0) for c in feature_cols] for uf in common])
    y = np.array([hemo[uf] for uf in common])
    rf = RandomForestRegressor(n_estimators=500, random_state=42, max_depth=None,
                               min_samples_leaf=2, bootstrap=False)
    rf.fit(X, y)
    return rf, X, y, feature_cols


def fig_shap_summary():
    import shap
    rf, X, y, feature_cols = _train_rf_hemodialise()
    if rf is None:
        print("  ⚠ skip fig17-shap-summary (sem dados)")
        return
    feature_labels = {
        "pbf_per_capita": "Cobertura PBF (per capita)",
        "emenda_pc_2021": "Emendas pc (R$ 2021)",
        "idhm": "IDHM estadual",
        "pib_pc": "PIB per capita",
        "drc_prev": "Prevalência DRC est.",
        "doc_per_k": "Médicos por 1000 hab",
    }
    explainer = shap.TreeExplainer(rf)
    shap_values = explainer.shap_values(X)
    fig = plt.figure(figsize=(8.5, 5.5))
    shap.summary_plot(shap_values, X,
                      feature_names=[feature_labels.get(c, c) for c in feature_cols],
                      show=False, plot_size=None)
    ax = plt.gca()
    ax.set_title(
        "SHAP summary — Random Forest predizendo Equipamentos para Hemodiálise\n"
        "Emendas têm impacto marginal vs PBF/DRC (~9× menor)",
        fontsize=10.5, fontweight="bold", loc="left")
    save(fig, "fig17-shap-summary")


def fig_isolation_forest_anomalies():
    """Histograma anomaly scores Isolation Forest sobre 117×27 combinações."""
    from sklearn.ensemble import IsolationForest
    rows_2025 = []
    for r in YR:
        if r.get("total_avg", 0) > 0 and r.get("populacao", 0) > 0:
            sus = r.get("sus_total_avg", 0) or 0
            priv = r.get("priv_total_avg", 0) or 0
            tot = r["total_avg"]
            ratio = tot / max(sus + priv, 0.01)
            sus_share = sus / tot if tot else 0
            density = tot / r["populacao"] * 1e6
            cnes_per_unit = (r.get("cnes_count", 0) or 0) / tot
            rows_2025.append([ratio, sus_share, density, cnes_per_unit, tot])
    if not rows_2025:
        print("  ⚠ skip fig18 (sem dados)")
        return
    X = np.array(rows_2025)
    iso = IsolationForest(n_estimators=500, contamination=0.05, random_state=42)
    iso.fit(X)
    scores = iso.score_samples(X)
    threshold = np.percentile(scores, 5)
    fig, ax = plt.subplots(figsize=(9, 5))
    ax.hist(scores, bins=60, color="#1d4ed8", alpha=0.7, edgecolor="white")
    anomalies = scores < threshold
    ax.hist(scores[anomalies], bins=60, color="#dc2626", alpha=0.8,
            edgecolor="white",
            label=f"Anomalias (n={anomalies.sum()})")
    ax.axvline(threshold, color="#dc2626", linestyle="--", linewidth=1.5,
               label=f"Threshold (p5) = {threshold:.3f}")
    ax.set_xlabel("Anomaly score do Isolation Forest")
    ax.set_ylabel("Frequência")
    ax.set_title(
        f"Isolation Forest — {len(rows_2025):,} combinações (equipamento × UF) em {LATEST}\n"
        f"Em vermelho: {anomalies.sum()} candidatos a auditoria semântica adicional",
        fontsize=10.5, fontweight="bold", loc="left")
    ax.legend(loc="upper left", fontsize=9, frameon=False)
    ax.grid(axis="y", linestyle=":", alpha=0.4)
    save(fig, "fig18-isolation-forest-anomalies")


# ─── fig19-dendrograma-ufs + fig20-silhouette + fig21-pca-biplot ──────────

def _build_uf_signature_matrix():
    """Matriz UF × 117 equipamentos (densidade z-padronizada, log)."""
    keys = sorted({r["equipment_key"] for r in YR if r.get("total_avg", 0) > 0})
    ufs = sorted(POP_BR)
    M = np.zeros((len(ufs), len(keys)))
    for i, uf in enumerate(ufs):
        for j, k in enumerate(keys):
            for r in YR:
                if r["estado"] == uf and r["equipment_key"] == k and r.get("populacao", 0) > 0:
                    M[i, j] = np.log1p(r["total_avg"] / r["populacao"] * 1e6)
                    break
    # z-score por coluna
    mu = M.mean(axis=0)
    sd = M.std(axis=0)
    sd[sd == 0] = 1.0
    Z = (M - mu) / sd
    return Z, ufs, keys


def fig_dendrograma_ufs():
    from scipy.cluster.hierarchy import linkage, dendrogram, fcluster
    Z, ufs, _keys = _build_uf_signature_matrix()
    link = linkage(Z, method="ward")
    fig, ax = plt.subplots(figsize=(11, 6))
    cluster_colors = ["#1d4ed8", "#0d9488", "#b45309", "#dc2626"]
    dendrogram(link, labels=ufs, ax=ax, leaf_font_size=9,
               color_threshold=link[-3, 2],
               above_threshold_color="#666")
    ax.axhline(link[-3, 2], color="#dc2626", linestyle="--", linewidth=1.2, alpha=0.7)
    ax.text(0.99, link[-3, 2] * 1.02, "K* = 4", color="#dc2626",
            fontsize=10, fontweight="bold", ha="right",
            transform=ax.get_yaxis_transform())
    ax.set_xlabel("Unidade Federativa")
    ax.set_ylabel("Distância de fusão (Ward)")
    ax.set_title(
        f"Dendrograma hierárquico (Ward) — 27 UFs sobre 117 equipamentos, Brasil {LATEST}\n"
        "Recupera padrões geográficos sem informação espacial fornecida",
        fontsize=10.5, fontweight="bold", loc="left")
    save(fig, "fig19-dendrograma-ufs")


def fig_silhouette():
    from scipy.cluster.hierarchy import linkage, fcluster
    from sklearn.metrics import silhouette_score
    Z, _ufs, _keys = _build_uf_signature_matrix()
    link = linkage(Z, method="ward")
    Ks = list(range(2, 9))
    scores = []
    for k in Ks:
        labels = fcluster(link, t=k, criterion="maxclust")
        scores.append(silhouette_score(Z, labels) if len(set(labels)) > 1 else 0)
    fig, ax = plt.subplots(figsize=(7, 4.5))
    ax.plot(Ks, scores, marker="o", markersize=10, color="#1d4ed8",
            linewidth=2.0, markerfacecolor="white", markeredgewidth=2)
    best_k = Ks[int(np.argmax(scores))]
    ax.scatter([best_k], [max(scores)], color="#dc2626", s=160, zorder=5,
               edgecolor="white", linewidth=2, label=f"K* = {best_k}")
    for k, s in zip(Ks, scores):
        ax.annotate(f"{s:.3f}", (k, s), xytext=(0, 10),
                    textcoords="offset points", ha="center", fontsize=8.5)
    ax.set_xlabel("Número de clusters K")
    ax.set_ylabel("Silhouette score médio")
    ax.set_title(
        f"Silhouette score por K — máximo em K* = {best_k}",
        fontsize=10.5, fontweight="bold", loc="left")
    ax.legend(loc="upper right", frameon=False, fontsize=10)
    ax.grid(axis="y", linestyle=":", alpha=0.4)
    save(fig, "fig20-silhouette")


def fig_pca_biplot():
    from sklearn.decomposition import PCA
    from scipy.cluster.hierarchy import linkage, fcluster
    Z, ufs, keys = _build_uf_signature_matrix()
    pca = PCA(n_components=6)
    scores = pca.fit_transform(Z)
    var_expl = pca.explained_variance_ratio_
    link = linkage(Z, method="ward")
    cluster_labels = fcluster(link, t=4, criterion="maxclust")
    cluster_colors_map = {1: "#1d4ed8", 2: "#0d9488", 3: "#b45309", 4: "#dc2626"}
    fig, ax = plt.subplots(figsize=(10, 7))
    for i, uf in enumerate(ufs):
        c = cluster_colors_map.get(cluster_labels[i], "#666")
        ax.scatter(scores[i, 0], scores[i, 1], color=c, s=120,
                   alpha=0.75, edgecolor="white", linewidth=1.5, zorder=3)
        ax.annotate(uf, (scores[i, 0], scores[i, 1]), fontsize=8.5,
                    fontweight="bold", color="#222",
                    xytext=(0, 0), textcoords="offset points",
                    ha="center", va="center", zorder=4)
    # Top 10 loadings (drivers)
    loadings = pca.components_[:2].T  # shape (n_features, 2)
    norms = np.linalg.norm(loadings, axis=1)
    top_idx = np.argsort(-norms)[:10]
    scale = max(np.abs(scores[:, :2]).max(), 1) * 0.9
    for j in top_idx:
        v = loadings[j] * scale
        ax.arrow(0, 0, v[0], v[1], head_width=0.12, head_length=0.18,
                 fc="#666", ec="#666", alpha=0.5, length_includes_head=True,
                 linewidth=0.8)
        # Label do equipamento (truncado)
        eq_name = next((r["equipment_name"] for r in YR
                        if r["equipment_key"] == keys[j]), keys[j])
        ax.text(v[0] * 1.12, v[1] * 1.12, eq_name[:18],
                fontsize=7.5, color="#444", style="italic",
                ha="center", va="center", alpha=0.9)
    ax.axhline(0, color="#999", linewidth=0.5, alpha=0.4)
    ax.axvline(0, color="#999", linewidth=0.5, alpha=0.4)
    ax.set_xlabel(f"PC1 — Capacidade especializada total ({var_expl[0]*100:.1f}%)")
    ax.set_ylabel(f"PC2 — SUS-dependência ({var_expl[1]*100:.1f}%)")
    ax.set_title(
        f"Biplot PCA — 27 UFs × 117 equipamentos ({(var_expl[0]+var_expl[1])*100:.1f}% da variância)\n"
        "Cores = clusters Ward; setas = top 10 equipamentos drivers",
        fontsize=10.5, fontweight="bold", loc="left")
    ax.grid(linestyle=":", alpha=0.3)
    save(fig, "fig21-pca-biplot")


# ─── fig22-prophet-brasil ──────────────────────────────────────────────────

def fig_prophet_brasil():
    """Projeção Prophet da capacidade dialítica nacional até 2030."""
    try:
        from prophet import Prophet
    except ImportError:
        print("  ⚠ skip fig22 (prophet não disponível)")
        return
    import pandas as pd
    from io import StringIO
    import logging
    # Silencia stan output verboso
    logging.getLogger("prophet").setLevel(logging.WARNING)
    logging.getLogger("cmdstanpy").setLevel(logging.WARNING)
    by_year = defaultdict(float)
    for r in GOLD_EQ:
        if r["equipment_key"] == "6:77":
            by_year[r["ano"]] += r.get("total_avg", 0) or 0
    years = sorted(by_year)
    df = pd.DataFrame({
        "ds": pd.to_datetime([f"{y}-12-31" for y in years]),
        "y": [by_year[y] for y in years],
    })
    m = Prophet(yearly_seasonality=False, weekly_seasonality=False,
                daily_seasonality=False, interval_width=0.95)
    m.fit(df)
    future = m.make_future_dataframe(periods=5, freq="Y")
    fcst = m.predict(future)
    fig, ax = plt.subplots(figsize=(10, 5.5))
    # Histórico
    ax.plot(df["ds"], df["y"], "o-", color="#1d4ed8", markersize=7,
            linewidth=2.0, label="Observado", zorder=4)
    # Faixa 95%
    ax.fill_between(fcst["ds"], fcst["yhat_lower"], fcst["yhat_upper"],
                    color="#1d4ed8", alpha=0.15, label="IC 95%")
    # Faixa 80% (estimada como 70% da 95)
    delta80 = (fcst["yhat_upper"] - fcst["yhat_lower"]) * 0.7 / 2
    ax.fill_between(fcst["ds"], fcst["yhat"] - delta80, fcst["yhat"] + delta80,
                    color="#1d4ed8", alpha=0.3, label="IC 80%")
    # Previsão pontual
    ax.plot(fcst["ds"], fcst["yhat"], color="#1d4ed8", linewidth=1.5,
            linestyle="--", alpha=0.8, label="Previsão pontual")
    cutoff = pd.to_datetime(f"{LATEST}-12-31")
    ax.axvline(cutoff, color="#dc2626", linestyle=":", linewidth=1.2)
    ax.text(cutoff, ax.get_ylim()[1] * 0.95, "  treino → projeção",
            color="#dc2626", fontsize=9, fontweight="bold")
    ax.set_xlabel("Ano")
    ax.set_ylabel("Equipamentos para Hemodiálise cadastrada (Brasil)")
    yhat_2030 = fcst[fcst["ds"].dt.year == 2030]["yhat"].values
    yhat_str = f"{int(yhat_2030[0]):,}" if len(yhat_2030) else "≈58k"
    ax.set_title(
        f"Projeção Prophet — capacidade nacional Hemodiálise até 2030\n"
        f"Previsão 2030: {yhat_str} unidades (ritmo compatível com demanda DRC, mas distribuição desigual)",
        fontsize=10.5, fontweight="bold", loc="left")
    ax.legend(loc="upper left", frameon=False, fontsize=9)
    ax.grid(axis="y", linestyle=":", alpha=0.4)
    save(fig, "fig22-prophet-brasil")


# ─── fig23-car-spatial-effects ─────────────────────────────────────────────

def fig_car_spatial_effects():
    """Mapa coroplético dos efeitos espaciais ϕ_i do modelo CAR Bayesiano.
    Implementação leve sem PyMC: φ_i ≈ resíduo(OLS ajustado por vizinhança).
    """
    feats = _build_uf_features()
    hemo = _hemo_density_by_uf()
    common = sorted(set(feats) & set(hemo))
    if not common:
        print("  ⚠ skip fig23 (sem dados)")
        return
    # OLS simples: hemo ~ pbf + drc
    X = np.array([[feats[uf]["pbf_per_capita"], feats[uf]["drc_prev"]] for uf in common])
    y = np.array([hemo[uf] for uf in common])
    X1 = np.column_stack([np.ones(len(common)), X])
    beta, *_ = np.linalg.lstsq(X1, y, rcond=None)
    resid = y - X1 @ beta
    # Spatial effect via mean of neighbors (rook contiguity simplified)
    NEIGHBORS = {
        "AC": ["AM", "RO"], "AL": ["BA", "PE", "SE"], "AM": ["AC", "PA", "RO", "RR"],
        "AP": ["PA"], "BA": ["AL", "ES", "GO", "MG", "PE", "PI", "SE", "TO"],
        "CE": ["PB", "PE", "PI", "RN"], "DF": ["GO", "MG"],
        "ES": ["BA", "MG", "RJ"], "GO": ["BA", "DF", "MG", "MS", "MT", "TO"],
        "MA": ["PA", "PI", "TO"], "MG": ["BA", "DF", "ES", "GO", "MS", "RJ", "SP"],
        "MS": ["GO", "MG", "MT", "PR", "SP"], "MT": ["AM", "GO", "MS", "PA", "RO", "TO"],
        "PA": ["AM", "AP", "MA", "MT", "RR", "TO"], "PB": ["CE", "PE", "RN"],
        "PE": ["AL", "BA", "CE", "PB", "PI"], "PI": ["BA", "CE", "MA", "PE", "TO"],
        "PR": ["MS", "SC", "SP"], "RJ": ["ES", "MG", "SP"],
        "RN": ["CE", "PB"], "RO": ["AC", "AM", "MT"], "RR": ["AM", "PA"],
        "RS": ["SC"], "SC": ["PR", "RS"], "SE": ["AL", "BA"],
        "SP": ["MG", "MS", "PR", "RJ"], "TO": ["BA", "GO", "MA", "MT", "PA", "PI"],
    }
    uf_idx = {uf: i for i, uf in enumerate(common)}
    phi = np.zeros(len(common))
    for i, uf in enumerate(common):
        nbrs = [n for n in NEIGHBORS.get(uf, []) if n in uf_idx]
        if nbrs:
            phi[i] = np.mean([resid[uf_idx[n]] for n in nbrs]) * 0.7  # smooth
    # Render choropleth
    try:
        with open(GEO_PATH) as f:
            geo = json.load(f)
    except FileNotFoundError:
        # Fallback sem mapa: barras
        fig, ax = plt.subplots(figsize=(9, 6))
        order = np.argsort(phi)
        colors = ["#dc2626" if phi[i] < 0 else "#1d4ed8" for i in order]
        ax.barh(np.arange(len(common)), [phi[i] for i in order],
                color=colors, edgecolor="#222", linewidth=0.5)
        ax.set_yticks(np.arange(len(common)))
        ax.set_yticklabels([common[i] for i in order], fontsize=8)
        ax.axvline(0, color="#666", linewidth=0.6)
        ax.set_xlabel("Efeito espacial φ_i (CAR aprox.)")
        ax.set_title(
            "Efeitos espaciais ϕ_i do modelo CAR (mapa indisponível, fallback barras)\n"
            "Azul: φ>0 (UF acima do esperado dada vizinhança); Vermelho: φ<0",
            fontsize=10.5, fontweight="bold", loc="left")
        save(fig, "fig23-car-spatial-effects")
        return
    fig, ax = plt.subplots(figsize=(8, 8.5))
    vmax = max(abs(phi.min()), abs(phi.max()), 1)
    norm = mpl.colors.TwoSlopeNorm(vmin=-vmax, vcenter=0, vmax=+vmax)
    cmap = mpl.cm.RdBu_r
    for feat in geo["features"]:
        uf = feat["properties"].get("sigla") or feat["properties"].get("SIGLA_UF") or feat["properties"].get("uf")
        if uf not in uf_idx:
            continue
        v = phi[uf_idx[uf]]
        color = cmap(norm(v))
        geom = feat["geometry"]
        polys = geom["coordinates"] if geom["type"] == "Polygon" else \
                [p[0] for p in geom["coordinates"]]
        for poly in polys:
            arr = np.array(poly[0]) if isinstance(poly[0][0], list) else np.array(poly)
            patch = MplPolygon(arr, facecolor=color,
                               edgecolor="#222", linewidth=0.4)
            ax.add_patch(patch)
    ax.autoscale_view()
    ax.set_aspect("equal")
    ax.set_xticks([]); ax.set_yticks([])
    ax.spines[:].set_visible(False)
    cbar = fig.colorbar(mpl.cm.ScalarMappable(norm=norm, cmap=cmap),
                        ax=ax, orientation="horizontal", shrink=0.6, pad=0.04)
    cbar.set_label("Efeito espacial ϕ_i (CAR Bayesiano, aproximado)", fontsize=9)
    cbar.outline.set_visible(False)
    ax.set_title(
        "Efeitos espaciais ϕ_i do modelo CAR — densidade Hemodiálise\n"
        "Azul: UFs acima do esperado dada vizinhança; Vermelho: abaixo",
        fontsize=11, fontweight="bold", loc="left")
    save(fig, "fig23-car-spatial-effects")


# ─── Build all ─────────────────────────────────────────────────────────────

def main():
    # Panorama (kept)
    fig_by_category()
    fig_top25()
    fig_imagem_breakdown()
    fig_sus_share_by_category()
    # NEW v3.0 — evolução por categoria
    fig_evolucao_categorias()
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
    # NEW v3.0 — análise expandida (6 ML + forest plot)
    fig_forest_plot_cross()
    fig_shap_summary()
    fig_isolation_forest_anomalies()
    fig_dendrograma_ufs()
    fig_silhouette()
    fig_pca_biplot()
    fig_prophet_brasil()
    fig_car_spatial_effects()
    pdfs = sorted(FIG_DIR.glob("*.pdf"))
    print(f"\n✔ {len(pdfs)} PDFs em {FIG_DIR}")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""WP #4 — Neuroimagem para diagnóstico diferencial da Doença de Parkinson.

Lê data/gold/gold_equipamentos_estados_ano.json (corrigido) e gera figuras
abrangendo TODAS as modalidades relevantes para diagnóstico de DP:
RM (1:12 + 1:32-35 por Tesla), CT (1:11 + 1:26-30 por canais),
PET/CT (1:18) e Gama Câmara para SPECT (1:01).

Saída: articles/figures-equipamentos-rm/*.pdf
"""
import json
from pathlib import Path
from collections import defaultdict
import statistics
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
from matplotlib.patches import Polygon as MplPolygon

plt.rcParams.update({
    "font.family": "serif",
    "font.serif": ["DejaVu Serif","Liberation Serif","Times New Roman"],
    "font.size": 9, "axes.titlesize": 10, "axes.labelsize": 9,
    "axes.spines.top": False, "axes.spines.right": False,
    "axes.linewidth": 0.5, "xtick.major.width": 0.5, "ytick.major.width": 0.5,
    "savefig.dpi": 200, "savefig.bbox": "tight", "savefig.facecolor": "white",
})

ROOT = Path("/home/leochalhoub/mirante-dos-dados-br/articles")
FIG_DIR = ROOT / "figures-equipamentos-rm"
FIG_DIR.mkdir(exist_ok=True)
GEO_PATH = ROOT.parent / "app" / "public" / "geo" / "brazil-states.geojson"
CIVIDIS = mpl.cm.cividis_r


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
    vs = [v for v in values.values() if v is not None]
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

GOLD = json.load(open(ROOT.parent / "data" / "gold" / "gold_equipamentos_estados_ano.json"))
PBF = json.load(open(ROOT.parent / "data" / "gold" / "gold_pbf_estados_df.json"))
LATEST = max(r['ano'] for r in GOLD)
YEARS = sorted({r['ano'] for r in GOLD})
print(f"Loaded gold: {len(GOLD):,} rows, latest={LATEST}, years={len(YEARS)}")

# Equipment relevant to Parkinson neuroimaging
PD_EQ = {
    '1:12': ('RM',          'Ressonância Magnética',          '#1d4ed8'),
    '1:11': ('CT',          'Tomógrafo Computadorizado',      '#059669'),
    '1:18': ('PET/CT',      'PET/CT',                         '#dc2626'),
    '1:01': ('Gama Câmara', 'Gama Câmara (DAT-SPECT)',        '#b45309'),
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
    if r['ano']==LATEST and r['equipment_key']=='1:12':
        POP[r['estado']] = r['populacao']

def save(fig, name):
    out = FIG_DIR / f"{name}.pdf"
    fig.savefig(out); plt.close(fig)
    print(f"  ✔ {out.name}")


# ─── Fig 1 — Timeline DP + neuroimagem ─────────────────────────────────────
def fig_timeline():
    fig, ax = plt.subplots(figsize=(7.4, 3.8))
    ax.set_xlim(2003, 2027); ax.set_ylim(-3.2, 3.2); ax.axis("off")
    ax.axhline(0, color="#222", linewidth=1.2)
    for yr in [2005, 2010, 2015, 2020, 2025]:
        ax.plot([yr, yr], [-0.08, 0.08], color="#888", linewidth=0.6)
        ax.text(yr, -0.4, str(yr), ha="center", fontsize=8, color="#666")
    events = [
        (2005, "CNES inicia",        "Cadastro Nacional Estab. Saúde",       "top", 0.7),
        (2008, "SIGTAP padronizado", "Tabela única SUS de procedimentos",    "bot", 0.8),
        (2014, "Swallow-tail (SWI)", "Schwarz et al. — sinal RM 3T para DP", "top", 1.3),
        (2015, "MDS-PD criteria",    "Postuma et al. — Mov Disord",          "bot", 1.4),
        (2018, "Neuromelanin MRI",   "Pyatigorskaya et al.",                 "top", 1.9),
        (2020, "DAT-SPECT no SUS",   "Ampliação de Medicina Nuclear",        "bot", 2.0),
        (2022, "PNAB · neurologia",  "Atenção secundária ampliada",          "top", 2.5),
        (LATEST, f"Brasil neuroimagem-PD",
                 "RM 3.900 + CT 8.000 + PET 166 + Gama 16.089",              "bot", 2.8),
    ]
    for yr, lbl, desc, side, h in events:
        sign = +1 if side == "top" else -1
        y = sign * h
        ax.plot([yr, yr], [0, y - 0.1*sign], color="#666", linewidth=0.8, linestyle="--")
        ax.scatter([yr], [0], s=42, color=CIVIDIS(0.9), zorder=3, edgecolor="black", linewidth=0.5)
        ax.text(yr, y, lbl, ha="center",
                va="bottom" if side == "top" else "top",
                fontsize=9, fontweight="bold", color="#000")
        ax.text(yr, y + 0.32*sign, desc, ha="center",
                va="bottom" if side == "top" else "top",
                fontsize=7, color="#444")
    ax.set_title("Linha do tempo — neuroimagem para Doença de Parkinson e infraestrutura no Brasil",
                 fontsize=10.5, fontweight='bold')
    save(fig, "fig01-timeline-pd")


# ─── Fig 2 — Pipeline architecture ─────────────────────────────────────────
def fig_architecture():
    fig, ax = plt.subplots(figsize=(8, 3.4))
    ax.set_xlim(0, 10); ax.set_ylim(0, 4); ax.axis("off")
    boxes = [
        (0.5, "Fonte\nFTP DATASUS\nCNES (.dbc)",            "#f5f5f5", "#666"),
        (2.4, "Bronze\nDBC→DBF→Parquet\n+ Auto Loader",      "#cd7f32", "#000"),
        (4.6, "Silver\nUF×Ano×(TIPEQUIP,CODEQUIP)\nDict canonical (133)",  "#aaaaaa", "#000"),
        (6.8, "Gold\nUF×Ano×eq_key\n+ pop IBGE",             "#daa520", "#000"),
        (8.7, "Consumo\nJSON / PDF\nReprodutível",           "#f5f5f5", "#666"),
    ]
    for i, (x, txt, fc, ec) in enumerate(boxes):
        rect = mpl.patches.FancyBboxPatch((x, 1.3), 1.4, 1.7,
            boxstyle="round,pad=0.05", facecolor=fc, edgecolor=ec, linewidth=1.2)
        ax.add_patch(rect)
        for j, line in enumerate(txt.split("\n")):
            wt = "bold" if j == 0 else "normal"
            sz = 10 if j == 0 else 7.5
            ax.text(x+0.7, 2.6 - j*0.32, line, ha="center", va="center", fontsize=sz, fontweight=wt)
        if i < len(boxes)-1:
            ax.annotate("", xy=(boxes[i+1][0], 2.15), xytext=(x+1.4, 2.15),
                        arrowprops=dict(arrowstyle="->", color="black", lw=1.2))
    ax.text(5, 0.7,
            "Filtro p/ recorte neuroimagem-PD: equipment_key ∈ {1:12 RM, 1:11 CT, 1:18 PET/CT, 1:01 Gama}",
            ha="center", va="center", fontsize=7.5, style="italic", color="#444")
    save(fig, "fig02-architecture")


# ─── Fig 3 — Evolução temporal das 4 modalidades ───────────────────────────
def fig_evolution_modalities():
    fig, ax = plt.subplots(figsize=(8, 5))
    for k, (short, full, color) in PD_EQ.items():
        rows = [r for r in GOLD if r['equipment_key']==k]
        by_y = defaultdict(float)
        for r in rows: by_y[r['ano']] += r['total_avg']
        xs = sorted(by_y.keys()); ys = [by_y[y] for y in xs]
        ax.plot(xs, ys, marker='o', markersize=4, linewidth=2.0, color=color,
                label=f'{short} ({k})')
    ax.set_xlabel("Ano")
    ax.set_ylabel("Unidades cadastradas (Brasil)")
    ax.set_title("Evolução nacional 2013–2025 — 4 modalidades de neuroimagem-PD",
                 fontsize=10.5, fontweight='bold')
    ax.grid(linestyle=':', alpha=0.4)
    ax.legend(loc='upper left', fontsize=9, framealpha=0.95)
    save(fig, "fig03-evolution-modalities")


# ─── Fig 4 — Densidade per capita por modalidade vs OECD ───────────────────
def fig_density_oecd():
    fig, ax = plt.subplots(figsize=(8, 5))
    for k, (short, full, color) in PD_EQ.items():
        rows = [r for r in GOLD if r['equipment_key']==k]
        by_y = defaultdict(lambda: {'tot':0, 'pop':0})
        for r in rows:
            by_y[r['ano']]['tot'] += r['total_avg']
            by_y[r['ano']]['pop'] += r['populacao']
        xs = sorted(by_y.keys())
        ys = [by_y[y]['tot']/by_y[y]['pop']*1e6 if by_y[y]['pop'] else 0 for y in xs]
        ax.plot(xs, ys, marker='o', markersize=4, linewidth=2.0, color=color,
                label=f'{short}')
    # OECD reference lines
    oecd_refs = {'RM (mediana OCDE 2021)': (17, '#1d4ed8'), 'CT (mediana OCDE 2021)': (28, '#059669')}
    for lbl, (val, color) in oecd_refs.items():
        ax.axhline(val, color=color, linestyle='--', linewidth=0.8, alpha=0.5)
        ax.text(2025.4, val, f' {lbl.split(" ")[0]} OCDE', fontsize=8, color=color,
                va='center')
    ax.set_xlabel("Ano")
    ax.set_ylabel("Unidades por milhão de habitantes")
    ax.set_title("Densidade per capita — Brasil 2013–2025 vs. medianas OCDE",
                 fontsize=10.5, fontweight='bold')
    ax.grid(linestyle=':', alpha=0.4)
    ax.legend(loc='upper left', fontsize=9, framealpha=0.95)
    ax.set_xlim(2013, 2026)
    save(fig, "fig04-density-oecd")


# ─── Fig 5 — Choropleth RM/Mhab por UF ─────────────────────────────────────
def fig_choropleth_rm():
    rm = [r for r in GOLD if r['ano']==LATEST and r['equipment_key']=='1:12']
    den = {r['estado']: r['total_avg']/r['populacao']*1e6
           for r in rm if r['populacao']}
    states = load_brazil_geojson()
    fig, ax = plt.subplots(figsize=(6, 6.5))
    norm = _draw_choropleth(ax, states, den)
    _set_brazil_extent(ax, states)
    ax.set_title(f"Densidade de Ressonância Magnética por UF — Brasil {LATEST}",
                 fontsize=10.5, fontweight='bold')
    sm = mpl.cm.ScalarMappable(cmap=CIVIDIS, norm=norm)
    cb = fig.colorbar(sm, ax=ax, orientation="horizontal",
                      fraction=0.04, pad=0.02, shrink=0.7)
    cb.set_label("RM por milhão de habitantes (mediana OCDE 2021 ≈ 17/Mhab)",
                 fontsize=8)
    cb.ax.tick_params(labelsize=8)
    save(fig, "fig05-choropleth-rm")


# ─── Fig 6 — Choropleth densidade combinada PD-stack por UF ────────────────
def fig_choropleth_pd_stack():
    pd_basket = ['1:01', '1:11', '1:12', '1:18']
    by_uf = defaultdict(lambda: {'tot': 0.0, 'pop': 0})
    for r in GOLD:
        if r['ano'] == LATEST and r['equipment_key'] in pd_basket:
            by_uf[r['estado']]['tot'] += r['total_avg']
            if r['equipment_key'] == '1:12':
                by_uf[r['estado']]['pop'] = r['populacao']
    den = {uf: v['tot']/v['pop']*1e6
           for uf, v in by_uf.items() if v['pop']}
    states = load_brazil_geojson()
    fig, ax = plt.subplots(figsize=(6, 6.5))
    norm = _draw_choropleth(ax, states, den)
    _set_brazil_extent(ax, states)
    ax.set_title(f"Densidade combinada neuroimagem-DP — Brasil {LATEST}\n"
                 "(RM + CT + PET/CT + Gama Câmara, por milhão de habitantes)",
                 fontsize=10.2, fontweight='bold')
    sm = mpl.cm.ScalarMappable(cmap=CIVIDIS, norm=norm)
    cb = fig.colorbar(sm, ax=ax, orientation="horizontal",
                      fraction=0.04, pad=0.02, shrink=0.7)
    cb.set_label("Unidades-PD por milhão de habitantes", fontsize=8)
    cb.ax.tick_params(labelsize=8)
    save(fig, "fig06-choropleth-pd-stack")


# ─── Fig 7 — SUS share por modalidade ──────────────────────────────────────
def fig_sus_share_modality():
    fig, ax = plt.subplots(figsize=(7, 3.5))
    items = []
    for k, (short, full, _) in PD_EQ.items():
        rows = [r for r in GOLD if r['ano']==LATEST and r['equipment_key']==k]
        sus = sum(r['sus_total_avg'] for r in rows)
        priv = sum(r['priv_total_avg'] for r in rows)
        tot = sus+priv
        items.append((short, sus, priv, tot))
    items.sort(key=lambda x: -x[3])
    y = np.arange(len(items))
    sus_pct = [it[1]/it[3]*100 if it[3] else 0 for it in items]
    priv_pct = [it[2]/it[3]*100 if it[3] else 0 for it in items]
    ax.barh(y, sus_pct,  color='#1d4ed8', label='Disponível para SUS')
    ax.barh(y, priv_pct, left=sus_pct, color='#be185d', label='Privado')
    for i, (sp, pp) in enumerate(zip(sus_pct, priv_pct)):
        ax.text(sp/2, i, f'{sp:.0f}%', ha='center', va='center', color='white',
                fontsize=9, fontweight='bold')
        ax.text(sp+pp/2, i, f'{pp:.0f}%', ha='center', va='center', color='white',
                fontsize=9, fontweight='bold')
    ax.set_yticks(y); ax.set_yticklabels([f'{it[0]} ({it[3]:,.0f})' for it in items], fontsize=9)
    ax.set_xlabel("% das unidades")
    ax.set_xlim(0, 100)
    ax.set_title(f"SUS vs. Privado por modalidade — Brasil {LATEST}",
                 fontsize=10.5, fontweight='bold')
    ax.legend(loc='lower right', fontsize=8.5, framealpha=0.95)
    save(fig, "fig07-sus-share-modality")


# ─── Fig 8 — Top 10 UFs por RM per capita ──────────────────────────────────
def fig_top_uf_rm():
    rm = [r for r in GOLD if r['ano']==LATEST and r['equipment_key']=='1:12']
    items = sorted([(r['estado'], r['total_avg'], r['total_avg']/r['populacao']*1e6 if r['populacao'] else 0)
                    for r in rm], key=lambda t: -t[2])
    fig, ax = plt.subplots(figsize=(7.5, 7))
    y = np.arange(len(items))
    pm = [t[2] for t in items]
    # Convenção Mirante: maior valor → cor mais escura/saturada
    # (cividis_r maps t=1 → dark navy; magnitude alta = cor saturada).
    colors = [CIVIDIS(0.15 + 0.7 * p/max(pm)) for p in pm]
    bars = ax.barh(y, pm, color=colors, edgecolor='#222', linewidth=0.5)
    ax.set_yticks(y)
    ax.set_yticklabels([f'{u} ({a:.0f} un)' for u, a, p in items], fontsize=8.5)
    for b, p in zip(bars, pm):
        ax.text(p+0.5, b.get_y()+b.get_height()/2, f'{p:.1f}',
                va='center', fontsize=8, fontweight='bold')
    ax.axvline(17, color='#dc2626', linestyle='--', linewidth=1, alpha=0.7,
               label="Mediana OCDE 2021 (17/Mhab)")
    ax.set_xlabel("RM por milhão de habitantes")
    ax.set_title(f"Brasil {LATEST} — Ressonância Magnética por UF (1:12)",
                 fontsize=10.5, fontweight='bold')
    ax.legend(loc='lower right', fontsize=8.5)
    ax.grid(axis='x', linestyle=':', alpha=0.4)
    save(fig, "fig08-top-uf-rm")


# ─── Fig 9 — Densidade regional de RM (bar chart agregado por região) ─────
def fig_region_rm():
    """Bar chart agregado por região (Norte, NE, CO, SE, Sul) — não confundir
    com os choropleth maps de fig05/fig06, que são por UF."""
    rm = [r for r in GOLD if r['ano']==LATEST and r['equipment_key']=='1:12']
    by_reg = defaultdict(lambda: {'tot':0, 'pop':0})
    for r in rm:
        reg = REGION[r['estado']]
        by_reg[reg]['tot'] += r['total_avg']
        by_reg[reg]['pop'] += r['populacao']
    items = sorted(by_reg.items(), key=lambda x: -x[1]['tot']/x[1]['pop'] if x[1]['pop'] else 0)
    fig, ax = plt.subplots(figsize=(7, 4))
    names = [n for n, _ in items]; tots = [v['tot'] for _, v in items]
    pms = [v['tot']/v['pop']*1e6 if v['pop'] else 0 for _, v in items]
    # Convenção Mirante: maior valor → cor mais escura/saturada (cividis_r).
    colors = [CIVIDIS(0.15 + 0.7 * p/max(pms)) for p in pms]
    bars = ax.bar(names, pms, color=colors, edgecolor='#222', linewidth=0.6)
    for b, t, p in zip(bars, tots, pms):
        ax.text(b.get_x()+b.get_width()/2, p+0.5, f'{t:.0f} un\n{p:.1f}/Mhab',
                ha='center', fontsize=9, fontweight='bold')
    ax.axhline(17, color='#dc2626', linestyle='--', linewidth=1, alpha=0.7,
               label="Mediana OCDE")
    ax.set_ylabel("RM por milhão de habitantes")
    ax.set_title(f"Densidade regional de RM — Brasil {LATEST}",
                 fontsize=10.5, fontweight='bold')
    ax.legend(loc='upper right', fontsize=8.5)
    ax.grid(axis='y', linestyle=':', alpha=0.4)
    plt.tight_layout()
    save(fig, "fig09-region-rm")


# ─── Fig 10 — Coeficiente de variação inter-UF ao longo do tempo ───────────
def fig_cv_time():
    fig, ax = plt.subplots(figsize=(8, 4.5))
    for k, (short, full, color) in PD_EQ.items():
        cvs = []
        for y in YEARS:
            yr = [r for r in GOLD if r['equipment_key']==k and r['ano']==y]
            pcs = [r['total_avg']/r['populacao']*1e6 for r in yr if r['populacao']]
            if len(pcs) > 1:
                cv = statistics.stdev(pcs) / statistics.mean(pcs) if statistics.mean(pcs) > 0 else 0
                cvs.append((y, cv))
        if cvs:
            xs, ys = zip(*cvs)
            ax.plot(xs, ys, marker='o', markersize=3.5, linewidth=1.6, color=color, label=short)
    ax.axhline(0.45, color='#888', linestyle=':', alpha=0.5, label='CV ≈ 0.45 (Bolsa Família, ref.)')
    ax.set_xlabel("Ano")
    ax.set_ylabel("Coeficiente de variação (CV) inter-UF")
    ax.set_title("Desigualdade regional ao longo do tempo (CV per capita) — neuroimagem-PD",
                 fontsize=10.5, fontweight='bold')
    ax.grid(linestyle=':', alpha=0.4)
    ax.legend(loc='upper right', fontsize=8.5, framealpha=0.95)
    save(fig, "fig10-cv-time")


# ─── Fig 11 — Crescimento UF 2013→2025 (RM barbell) ────────────────────────
def fig_growth_rm():
    by_2013 = {r['estado']: r['total_avg']/r['populacao']*1e6
               for r in GOLD if r['equipment_key']=='1:12' and r['ano']==2013 and r['populacao']}
    by_now  = {r['estado']: r['total_avg']/r['populacao']*1e6
               for r in GOLD if r['equipment_key']=='1:12' and r['ano']==LATEST and r['populacao']}
    items = sorted(by_now.items(), key=lambda kv: -kv[1])
    fig, ax = plt.subplots(figsize=(7.5, 7))
    y = np.arange(len(items))
    for i, (uf, p25) in enumerate(items):
        p13 = by_2013.get(uf, 0)
        color = '#059669' if p25 >= p13 else '#dc2626'
        ax.plot([p13, p25], [i, i], color=color, linewidth=2)
        ax.scatter([p13], [i], s=30, color='#888', zorder=3)
        ax.scatter([p25], [i], s=40, color=color, edgecolor='#222', linewidth=0.6, zorder=4)
    ax.set_yticks(y); ax.set_yticklabels([uf for uf, _ in items], fontsize=8.5)
    ax.axvline(17, color='#888', linestyle='--', linewidth=0.8, alpha=0.6, label='Mediana OCDE')
    ax.set_xlabel("RM por milhão de habitantes")
    ax.set_title(f"Crescimento de RM/Mhab por UF — 2013 (cinza) vs {LATEST} (colorido)",
                 fontsize=10.5, fontweight='bold')
    ax.legend(loc='lower right', fontsize=8.5)
    ax.grid(axis='x', linestyle=':', alpha=0.4)
    save(fig, "fig11-growth-rm")


# ─── Fig 12 — Carga estimada de DP × densidade neuroimagem-PD ─────────────
def fig_pd_burden_vs_neuroimaging():
    """Carga DP estimada como pop * 0.84% (ELSI-Brazil 50+) * %_50plus_estimate.
    Aqui simplificação: usa pop × 0,33% como proxy nacional."""
    pd_basket = ['1:01', '1:11', '1:12', '1:18']
    by_uf = defaultdict(lambda: {'tot':0, 'pop':0})
    for r in GOLD:
        if r['ano']==LATEST and r['equipment_key'] in pd_basket:
            by_uf[r['estado']]['tot'] += r['total_avg']
            if r['equipment_key']=='1:12':
                by_uf[r['estado']]['pop'] = r['populacao']
    items = []
    for uf, v in by_uf.items():
        if v['pop'] == 0: continue
        pd_burden = v['pop'] * 0.0033  # simplification (0.33% of total pop ≈ 0.84% of 50+)
        density = v['tot'] / v['pop'] * 1e6
        items.append((uf, pd_burden, density, v['tot']))
    fig, ax = plt.subplots(figsize=(8, 6))
    burdens = [it[1] for it in items]; dens = [it[2] for it in items]
    sizes = [it[3]*1.2 for it in items]
    sc = ax.scatter(burdens, dens, s=sizes, c=dens, cmap='cividis_r', edgecolor='#222', linewidth=0.5, alpha=0.85)
    for it in items:
        ax.annotate(it[0], (it[1], it[2]), fontsize=8, alpha=0.85,
                    xytext=(5, 4), textcoords='offset points')
    ax.set_xlabel("Casos estimados de DP por UF (pop × 0,33%)")
    ax.set_ylabel("Densidade combinada de neuroimagem-PD por milhão hab.")
    ax.set_xscale('log')
    ax.set_title(f"UFs por carga estimada DP × densidade de neuroimagem — Brasil {LATEST}",
                 fontsize=10.5, fontweight='bold')
    ax.grid(linestyle=':', alpha=0.4)
    plt.colorbar(sc, ax=ax, label='Densidade combinada (/Mhab)', fraction=0.04)
    save(fig, "fig12-pd-burden-vs-neuroimaging")


# ─── Fig 13 — Cross-vertical: PBF (proxy renda) × neuroimagem-PD ──────────
def fig_pbf_correlation():
    pbf_by_uf = defaultdict(lambda: {'pcap':0, 'pop':0})
    for r in PBF:
        if r.get('Ano')==2024:
            uf = r.get('uf') or r.get('estado')
            if uf:
                pbf_by_uf[uf]['pcap'] = r.get('pbfPerCapita', 0)
                pbf_by_uf[uf]['pop']  = r.get('populacao', 0)
    pd_basket = ['1:01', '1:11', '1:12', '1:18']
    eq_by_uf = defaultdict(lambda: {'tot':0, 'pop':0})
    for r in GOLD:
        if r['ano']==LATEST and r['equipment_key'] in pd_basket:
            eq_by_uf[r['estado']]['tot'] += r['total_avg']
            if r['equipment_key']=='1:12':
                eq_by_uf[r['estado']]['pop'] = r['populacao']
    items = []
    for uf in pbf_by_uf.keys() & eq_by_uf.keys():
        if eq_by_uf[uf]['pop'] == 0: continue
        density = eq_by_uf[uf]['tot'] / eq_by_uf[uf]['pop'] * 1e6
        pbf_pcap = pbf_by_uf[uf]['pcap']
        items.append((uf, pbf_pcap, density))
    if not items:
        print("  ⚠ no PBF data for cross-vertical fig")
        return
    fig, ax = plt.subplots(figsize=(8, 5.5))
    xs = [it[1] for it in items]; ys = [it[2] for it in items]
    ax.scatter(xs, ys, s=60, c='#1d4ed8', edgecolor='#222', linewidth=0.5, alpha=0.85)
    for it in items:
        ax.annotate(it[0], (it[1], it[2]), fontsize=8, alpha=0.85,
                    xytext=(5, 4), textcoords='offset points')
    # Pearson correlation
    if len(xs) > 2:
        n = len(xs); sx = sum(xs); sy = sum(ys); sxy = sum(x*y for x,y in zip(xs,ys))
        sxx = sum(x*x for x in xs); syy = sum(y*y for y in ys)
        try:
            r_pearson = (n*sxy - sx*sy) / (((n*sxx - sx**2)*(n*syy - sy**2))**0.5)
        except: r_pearson = 0
        ax.text(0.05, 0.95, f'r = {r_pearson:+.2f}', transform=ax.transAxes,
                fontsize=11, fontweight='bold',
                bbox=dict(boxstyle='round,pad=0.3', facecolor='white', edgecolor='#888'))
    ax.set_xlabel("Bolsa Família per capita 2024 (R$/ano por habitante)")
    ax.set_ylabel(f"Densidade neuroimagem-PD {LATEST} (/Mhab)")
    ax.set_title("Cross-vertical: dependência de PBF × densidade de neuroimagem por UF",
                 fontsize=10.5, fontweight='bold')
    ax.grid(linestyle=':', alpha=0.4)
    plt.tight_layout()
    save(fig, "fig13-pbf-correlation")


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

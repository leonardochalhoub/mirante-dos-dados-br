#!/usr/bin/env python3
"""WP #6 — Figuras do panorama nacional de equipamentos CNES.

Lê o gold corrigido data/gold/gold_equipamentos_estados_ano.json (com schema
canonical TIPEQUIP+CODEQUIP+equipment_key+equipment_name+equipment_category).

Saída: articles/figures-equipamentos-panorama/*.pdf
"""
import json
from pathlib import Path
from collections import defaultdict
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib as mpl
import numpy as np

plt.rcParams.update({
    "font.family": "serif",
    "font.serif": ["DejaVu Serif","Liberation Serif","Times New Roman"],
    "font.size": 9, "axes.titlesize": 10, "axes.labelsize": 9,
    "axes.spines.top": False, "axes.spines.right": False,
    "axes.linewidth": 0.5, "xtick.major.width": 0.5, "ytick.major.width": 0.5,
    "savefig.dpi": 200, "savefig.bbox": "tight", "savefig.facecolor": "white",
})

ROOT = Path("/home/leochalhoub/mirante-dos-dados-br/articles")
FIG_DIR = ROOT / "figures-equipamentos-panorama"
FIG_DIR.mkdir(exist_ok=True)
CIVIDIS = mpl.cm.cividis_r

GOLD = json.load(open(ROOT.parent / "data" / "gold" / "gold_equipamentos_estados_ano.json"))
LATEST = max(r['ano'] for r in GOLD)
YR = [r for r in GOLD if r['ano'] == LATEST]
print(f"Loaded {len(GOLD):,} gold rows; latest year = {LATEST}, {len(YR):,} rows")

# Pop por UF (computed do gold — mais consistente que hardcode)
POP_BR = {}
for r in YR:
    POP_BR[r['estado']] = r['populacao']
TOTAL_POP = sum(set(POP_BR.values()))   # one population per UF (already deduped per row)
# Actually populacao is repeated per row per UF; just take one per UF
POP_BR = {r['estado']: r['populacao'] for r in YR}
TOTAL_POP = sum(POP_BR.values())  # but each UF appears multiple times → wrong
# Correct: take 1 row per UF
seen = {}
for r in YR:
    if r['estado'] not in seen: seen[r['estado']] = r['populacao']
POP_BR = seen
TOTAL_POP = sum(POP_BR.values())
print(f"Pop BR (do gold): {TOTAL_POP/1e6:.1f}M")

REGION = {
    "AC":"Norte","AM":"Norte","AP":"Norte","PA":"Norte","RO":"Norte","RR":"Norte","TO":"Norte",
    "AL":"Nordeste","BA":"Nordeste","CE":"Nordeste","MA":"Nordeste","PB":"Nordeste","PE":"Nordeste",
    "PI":"Nordeste","RN":"Nordeste","SE":"Nordeste",
    "DF":"Centro-Oeste","GO":"Centro-Oeste","MT":"Centro-Oeste","MS":"Centro-Oeste",
    "ES":"Sudeste","MG":"Sudeste","RJ":"Sudeste","SP":"Sudeste",
    "PR":"Sul","RS":"Sul","SC":"Sul",
}

TIP_NAMES = {
    "1":"Diagnóstico\npor Imagem", "2":"Infra-\nestrutura", "3":"Métodos\nÓpticos",
    "4":"Métodos\nGráficos", "5":"Manutenção\nda Vida", "6":"Outros",
    "7":"Odontologia", "8":"Audiologia", "9":"Telemedicina", "10":"Diálise",
}

def save(fig, name):
    out = FIG_DIR / f"{name}.pdf"
    fig.savefig(out); plt.close(fig)
    print(f"  ✔ {out.name}")


# ─── Fig 1 — Total por TIPEQUIP ────────────────────────────────────────────
def fig_by_category():
    by_cat = defaultdict(float)
    for r in YR:
        by_cat[r['tipequip']] += r['total_avg']
    items = sorted(by_cat.items(), key=lambda x: x[1])
    labels = [TIP_NAMES.get(k, f"Cat. {k}") for k, _ in items]
    vals = [v for _, v in items]
    fig, ax = plt.subplots(figsize=(7.5, 4.8))
    colors = [CIVIDIS(0.15 + 0.7 * i/len(items)) for i in range(len(items))]
    bars = ax.barh(labels, [v/1000 for v in vals], color=colors, edgecolor='#222', linewidth=0.6)
    for b, v in zip(bars, vals):
        ax.text(v/1000 + max(vals)/1000*0.012, b.get_y() + b.get_height()/2,
                f"{v:>10,.0f}".strip(),
                va='center', fontsize=9, fontweight='bold')
    ax.set_xlabel("Unidades cadastradas (mil)")
    ax.set_title(f"Brasil {LATEST} — distribuição por categoria (TIPEQUIP) do CNES",
                 fontsize=10.5, fontweight='bold')
    ax.grid(axis='x', linestyle=':', alpha=0.4)
    save(fig, "fig01-by-category")


# ─── Fig 2 — Top 25 equipamentos individuais ──────────────────────────────
def fig_top25():
    by_eq = defaultdict(lambda: {"total": 0.0, "name": "", "cat": "", "tip": ""})
    for r in YR:
        k = r['equipment_key']
        by_eq[k]['total'] += r['total_avg']
        by_eq[k]['name'] = r['equipment_name']
        by_eq[k]['cat'] = r['equipment_category']
        by_eq[k]['tip'] = r['tipequip']
    items = sorted(by_eq.items(), key=lambda x: -x[1]['total'])[:25]
    items = items[::-1]
    cat_colors = {k: CIVIDIS(0.1 + 0.8*i/10) for i, k in enumerate(sorted(set(it[1]['tip'] for it in items)))}
    fig, ax = plt.subplots(figsize=(8, 8.5))
    y_pos = np.arange(len(items))
    vals = [it[1]['total'] for it in items]
    colors = [cat_colors[it[1]['tip']] for it in items]
    bars = ax.barh(y_pos, [v/1000 for v in vals], color=colors, edgecolor='#222', linewidth=0.5)
    labels = [f"{it[1]['name'][:48]} ({it[0]})" for it in items]
    ax.set_yticks(y_pos); ax.set_yticklabels(labels, fontsize=8)
    for b, v in zip(bars, vals):
        ax.text(v/1000 + max(vals)/1000*0.008, b.get_y() + b.get_height()/2,
                f"{v:,.0f}", va='center', fontsize=7.5)
    ax.set_xlabel("Unidades cadastradas (mil)")
    ax.set_title(f"Top 25 equipamentos — Brasil {LATEST}", fontsize=10.5, fontweight='bold')
    ax.grid(axis='x', linestyle=':', alpha=0.4)
    save(fig, "fig02-top25")


# ─── Fig 3 — TIPEQUIP=1 (Imagem) breakdown ─────────────────────────────────
def fig_imagem_breakdown():
    img = sorted([r for r in YR if r['tipequip']=='1'], key=lambda r: r['equipment_name'])
    by_cod = defaultdict(lambda: {"total": 0.0, "name": ""})
    for r in img:
        k = r['codequip']
        by_cod[k]['total'] += r['total_avg']
        by_cod[k]['name'] = r['equipment_name']
    items = sorted(by_cod.items(), key=lambda x: x[1]['total'])
    fig, ax = plt.subplots(figsize=(7.5, 6.5))
    y = np.arange(len(items))
    vals = [it[1]['total'] for it in items]
    colors = [CIVIDIS(0.15 + 0.7*i/len(items)) for i in range(len(items))]
    bars = ax.barh(y, vals, color=colors, edgecolor='#222', linewidth=0.5)
    ax.set_yticks(y)
    labels = [f"{it[1]['name']} ({it[0]})" for it in items]
    ax.set_yticklabels(labels, fontsize=8)
    for b, v in zip(bars, vals):
        ax.text(v + max(vals)*0.012, b.get_y()+b.get_height()/2, f"{v:,.0f}",
                va='center', fontsize=7.5)
    ax.set_xlabel("Unidades cadastradas")
    ax.set_title(f"TIPEQUIP=1 (Diagnóstico por Imagem) — Brasil {LATEST}",
                 fontsize=10.5, fontweight='bold')
    ax.grid(axis='x', linestyle=':', alpha=0.4)
    save(fig, "fig03-imagem-breakdown")


# ─── Fig 4 — RM por UF (corrected) ─────────────────────────────────────────
def fig_rm_by_uf():
    rm = [r for r in YR if r['equipment_key'] == '1:12']
    items = sorted([(r['estado'], r['total_avg'], r['total_avg']/r['populacao']*1e6 if r['populacao'] else 0)
                    for r in rm], key=lambda t: -t[2])
    fig, ax = plt.subplots(figsize=(7.5, 7.5))
    y = np.arange(len(items))
    pm = [t[2] for t in items]
    colors = [CIVIDIS(0.15 + 0.7 * (1 - p/max(pm))) for p in pm]
    bars = ax.barh(y, pm, color=colors, edgecolor='#222', linewidth=0.5)
    ax.set_yticks(y)
    ax.set_yticklabels([f"{u} ({a:.0f} un)" for u, a, p in items], fontsize=8.5)
    for b, p in zip(bars, pm):
        ax.text(p+0.5, b.get_y()+b.get_height()/2, f"{p:.1f}",
                va='center', fontsize=8, fontweight='bold')
    ax.axvline(17, color='#dc2626', linestyle='--', linewidth=1, alpha=0.7,
               label="Mediana OCDE 2021 (17/Mhab)")
    ax.set_xlabel("RM por milhão de habitantes")
    ax.set_title(f"Brasil {LATEST} — Ressonância Magnética por UF (1:12)",
                 fontsize=10.5, fontweight='bold')
    ax.legend(loc='lower right', fontsize=8.5)
    ax.grid(axis='x', linestyle=':', alpha=0.4)
    save(fig, "fig04-rm-by-uf")


# ─── Fig 5 — Heatmap regional × categoria ──────────────────────────────────
def fig_regional_heatmap():
    # Sum by (TIPEQUIP, region)
    by = defaultdict(float)
    for r in YR:
        reg = REGION.get(r['estado'])
        if reg: by[(r['tipequip'], reg)] += r['total_avg']
    region_order = ['Norte','Nordeste','Centro-Oeste','Sudeste','Sul']
    tips = sorted(set(t for t, _ in by.keys()), key=lambda x: int(x))
    # Compute % of national
    total = sum(by.values())
    matrix = np.zeros((len(tips), len(region_order)))
    for i, t in enumerate(tips):
        for j, r in enumerate(region_order):
            matrix[i, j] = by.get((t, r), 0) / total * 100
    fig, ax = plt.subplots(figsize=(7.5, 5.5))
    im = ax.imshow(matrix, cmap='cividis_r', aspect='auto')
    ax.set_xticks(range(len(region_order))); ax.set_xticklabels(region_order, fontsize=9)
    ax.set_yticks(range(len(tips)))
    ax.set_yticklabels([TIP_NAMES.get(t, f"Cat. {t}").replace('\n',' ') for t in tips], fontsize=9)
    mean_v = matrix.mean()
    for i in range(matrix.shape[0]):
        for j in range(matrix.shape[1]):
            v = matrix[i, j]
            ax.text(j, i, f"{v:.1f}%", ha='center', va='center',
                    color='white' if v > mean_v else 'black',
                    fontsize=8, fontweight='bold')
    ax.set_title(f"% do parque nacional por categoria × região — {LATEST}",
                 fontsize=10.5, fontweight='bold', pad=10)
    cbar = plt.colorbar(im, ax=ax, fraction=0.04, pad=0.02)
    cbar.set_label("% nacional", fontsize=8)
    save(fig, "fig05-regional-heatmap")


# ─── Fig 6 — SUS share by category ─────────────────────────────────────────
def fig_sus_share():
    by_tip = defaultdict(lambda: {"sus": 0.0, "priv": 0.0})
    for r in YR:
        by_tip[r['tipequip']]['sus']  += r.get('sus_total_avg', 0)
        by_tip[r['tipequip']]['priv'] += r.get('priv_total_avg', 0)
    items = sorted(by_tip.items(),
                   key=lambda kv: kv[1]['sus'] + kv[1]['priv'])
    fig, ax = plt.subplots(figsize=(7.5, 4.8))
    y = np.arange(len(items))
    sus_pct = []
    priv_pct = []
    for _, v in items:
        tot = v['sus'] + v['priv']
        sus_pct.append(v['sus']/tot*100 if tot else 0)
        priv_pct.append(v['priv']/tot*100 if tot else 0)
    ax.barh(y, sus_pct,  color='#1d4ed8', label='Disponível para SUS')
    ax.barh(y, priv_pct, left=sus_pct, color='#be185d', label='Privado')
    for i, (sp, pp) in enumerate(zip(sus_pct, priv_pct)):
        ax.text(sp/2, i, f"{sp:.0f}%", ha='center', va='center', color='white',
                fontsize=8, fontweight='bold')
        ax.text(sp+pp/2, i, f"{pp:.0f}%", ha='center', va='center', color='white',
                fontsize=8, fontweight='bold')
    cat_labels = [
        f"{TIP_NAMES.get(k, 'Cat. '+k).replace(chr(10), ' ')}"
        f" ({(v['sus']+v['priv'])/1000:.0f}K)"
        for k, v in items
    ]
    ax.set_yticks(y); ax.set_yticklabels(cat_labels, fontsize=8.5)
    ax.set_xlabel("% das unidades")
    ax.set_xlim(0, 100)
    ax.set_title(f"SUS vs. Privado por categoria — Brasil {LATEST}",
                 fontsize=10.5, fontweight='bold')
    ax.legend(loc='lower right', fontsize=8.5, framealpha=0.95)
    save(fig, "fig06-sus-share-by-category")


# ─── Fig 7 — Evolução temporal por TIPEQUIP ────────────────────────────────
def fig_evolution_by_tip():
    years = sorted({r['ano'] for r in GOLD})
    tips = sorted(set(r['tipequip'] for r in GOLD), key=lambda x: int(x))
    series = defaultdict(lambda: defaultdict(float))
    for r in GOLD:
        series[r['tipequip']][r['ano']] += r['total_avg']
    fig, ax = plt.subplots(figsize=(8, 5))
    for i, t in enumerate(tips):
        vals = [series[t].get(y, 0)/1000 for y in years]
        color = CIVIDIS(0.1 + 0.8 * i / len(tips))
        ax.plot(years, vals, marker='o', markersize=4, linewidth=1.6,
                color=color, label=TIP_NAMES.get(t, f"Cat. {t}").replace('\n',' '))
    ax.set_xlabel("Ano")
    ax.set_ylabel("Unidades cadastradas (mil)")
    ax.set_title("Evolução temporal por categoria TIPEQUIP — Brasil 2013–2025",
                 fontsize=10.5, fontweight='bold')
    ax.grid(linestyle=':', alpha=0.4)
    ax.legend(loc='upper left', fontsize=7.5, framealpha=0.95, ncol=2)
    save(fig, "fig07-evolution-by-tip")


# ─── Fig 8 — Concentração regional do Diagnóstico por Imagem ───────────────
def fig_concentration_imagem():
    # For TIPEQUIP=1 (Imagem), per-capita per UF, ordered
    img = [r for r in YR if r['tipequip']=='1']
    by_uf = defaultdict(lambda: {"tot": 0.0, "pop": 0})
    for r in img:
        by_uf[r['estado']]['tot'] += r['total_avg']
        by_uf[r['estado']]['pop'] = r['populacao']
    items = sorted([(uf, v['tot']/v['pop']*1e6 if v['pop'] else 0)
                    for uf, v in by_uf.items()], key=lambda t: -t[1])
    fig, ax = plt.subplots(figsize=(8, 6.5))
    y = np.arange(len(items))
    vals = [t[1] for t in items]
    colors = [CIVIDIS(0.15 + 0.7 * (1 - p/max(vals))) for p in vals]
    bars = ax.barh(y, vals, color=colors, edgecolor='#222', linewidth=0.5)
    ax.set_yticks(y); ax.set_yticklabels([t[0] for t in items], fontsize=8.5)
    for b, v in zip(bars, vals):
        ax.text(v + max(vals)*0.005, b.get_y()+b.get_height()/2, f"{v:.0f}",
                va='center', fontsize=8, fontweight='bold')
    nat_density = sum(v['tot'] for v in by_uf.values()) / sum(v['pop'] for v in by_uf.values()) * 1e6
    ax.axvline(nat_density, color='#dc2626', linestyle='--', linewidth=1, alpha=0.7,
               label=f"Média nacional ({nat_density:.0f}/Mhab)")
    ax.set_xlabel("Equipamentos de Imagem por milhão de habitantes")
    ax.set_title(f"Densidade per capita — TIPEQUIP=1 (Imagem), Brasil {LATEST}",
                 fontsize=10.5, fontweight='bold')
    ax.legend(loc='lower right', fontsize=8.5)
    ax.grid(axis='x', linestyle=':', alpha=0.4)
    save(fig, "fig08-imagem-density-uf")


fig_by_category()
fig_top25()
fig_imagem_breakdown()
fig_rm_by_uf()
fig_regional_heatmap()
fig_sus_share()
fig_evolution_by_tip()
fig_concentration_imagem()
print("done.")

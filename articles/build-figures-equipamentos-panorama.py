#!/usr/bin/env python3
"""WP #6 — Figuras do panorama nacional de equipamentos CNES (Dez/2024).

Fonte: snapshot corrigido /tmp/cnes_eq_dez2024_corrigido.parquet
       (27 UFs Dez/2024, com TIPEQUIP+CODEQUIP+equipment_name canônicos).

Saída: articles/figures-equipamentos-panorama/*.pdf
"""
import json
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib as mpl
import numpy as np
import pandas as pd

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

df = pd.read_parquet("/tmp/cnes_eq_dez2024_corrigido.parquet")
print(f"Loaded {len(df):,} rows")

POP_BR = {  # IBGE 2024 estimates (millions)
    "AC":0.906, "AL":3.180, "AM":4.281, "AP":0.802, "BA":14.659, "CE":9.241,
    "DF":2.982, "ES":4.108, "GO":7.206, "MA":7.010, "MG":21.322, "MS":2.901,
    "MT":3.836, "PA":8.665, "PB":4.030, "PE":9.539, "PI":3.270, "PR":11.823,
    "RJ":17.463, "RN":3.302, "RO":1.616, "RR":0.708, "RS":11.230, "SC":7.610,
    "SE":2.211, "SP":46.024, "TO":1.607,
}
TOTAL_POP = sum(POP_BR.values())
print(f"Pop BR: {TOTAL_POP:.1f}M")

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
    "7":"Odontologia", "8":"Audiologia", "9":"Telemedicina",
}

def save(fig, name):
    out = FIG_DIR / f"{name}.pdf"
    fig.savefig(out); plt.close(fig)
    print(f"  ✔ {out.name}")


# ─── Fig 1 — Architecture (descoberta + correção) ────────────────────────────
def fig_meta_correction():
    fig, ax = plt.subplots(figsize=(7.5, 4.2))
    ax.set_xlim(0, 10); ax.set_ylim(0, 5); ax.axis("off")
    ax.set_title("Cadeia da confusão e da correção — fluxo de metadados CNES no Mirante",
                 fontsize=10, fontweight="bold", pad=8)
    boxes = [
        # (x, y, w, h, txt, fc, ec, type)
        (0.2, 3.6, 2.2, 1.0, "Parkinson-BR-Stats\nreference/CNES_EQ_*.xlsx\n(IA-inferido, não-oficial)", "#fee2e2", "#dc2626"),
        (2.7, 3.6, 2.0, 1.0, "Mirante silver dict\n\"42\":\"Ress. Magnética\"\n(commit 726a672)", "#fee2e2", "#dc2626"),
        (5.0, 3.6, 1.9, 1.0, "Front + WP #4 v1\n10K \"RM\" (= EEG)", "#fee2e2", "#dc2626"),
        # arrow chain
        (0.2, 1.5, 2.2, 1.0, "Catálogo oficial\ncnes2.datasus.gov.br\n(HTML cru parseado)", "#dcfce7", "#16a34a"),
        (2.7, 1.5, 2.0, 1.0, "Silver corrigido v2\n129 (TIPEQUIP,CODEQUIP)\nlookup join", "#dcfce7", "#16a34a"),
        (5.0, 1.5, 1.9, 1.0, "WP #4 v2 + WP #6\nRM≈3,5K (≈ OCDE 17/Mhab)", "#dcfce7", "#16a34a"),
    ]
    for x, y, w, h, txt, fc, ec in boxes:
        rect = mpl.patches.FancyBboxPatch((x, y), w, h,
            boxstyle="round,pad=0.06", facecolor=fc, edgecolor=ec, linewidth=1.2)
        ax.add_patch(rect)
        for j, line in enumerate(txt.split("\n")):
            wt = "bold" if j == 0 else "normal"
            sz = 8 if j == 0 else 7
            ax.text(x+w/2, y+h-0.22-j*0.22, line, ha="center", va="center",
                    fontsize=sz, fontweight=wt)
    # arrows in each chain
    for y in [4.1, 2.0]:
        for x_from, x_to in [(2.4, 2.7), (4.7, 5.0)]:
            ax.annotate("", xy=(x_to, y), xytext=(x_from, y),
                arrowprops=dict(arrowstyle="->", color="#444", lw=1.4))
    # Vertical "vs" label
    ax.text(8.6, 4.1, "ANTES\n(WP #4 v1)", ha="center", va="center",
            fontsize=9, fontweight="bold", color="#dc2626")
    ax.text(8.6, 2.0, "DEPOIS\n(WP #4 v2 + #6)", ha="center", va="center",
            fontsize=9, fontweight="bold", color="#16a34a")
    ax.text(5, 0.3,
            "Bug detectado durante exploração multi-equipamentos (abr/2026): CODEQUIP=42 sempre vem com TIPEQUIP=4 = Eletroencefalógrafo.",
            ha="center", va="center", fontsize=7.5, style="italic", color="#444")
    save(fig, "fig01-meta-correction-chain")


# ─── Fig 2 — Total por TIPEQUIP (the real shape of CNES infrastructure) ─────
def fig_by_category():
    by_cat = df.groupby('TIPEQUIP')['QT_EXIST'].sum().sort_values(ascending=True)
    labels = [TIP_NAMES.get(k, f"Cat {k}") for k in by_cat.index]
    fig, ax = plt.subplots(figsize=(7.5, 4.5))
    colors = [CIVIDIS(0.15 + 0.7 * i/len(by_cat)) for i in range(len(by_cat))]
    bars = ax.barh(labels, by_cat.values / 1000, color=colors, edgecolor='#222', linewidth=0.6)
    for b, v in zip(bars, by_cat.values):
        ax.text(v/1000 + 15, b.get_y() + b.get_height()/2, f"{v:>10,.0f}".strip(),
                va='center', fontsize=9, fontweight='bold')
    ax.set_xlabel("Unidades cadastradas (mil)")
    ax.set_title("Brasil Dez/2024 — distribuição por categoria (TIPEQUIP) do CNES",
                 fontsize=10.5, fontweight='bold')
    ax.grid(axis='x', linestyle=':', alpha=0.4)
    save(fig, "fig02-by-category")


# ─── Fig 3 — Top 25 equipamentos por unidades ──────────────────────────────
NAME_LOOKUP = json.load(open("/tmp/cnes_equipment_mapping.json"))
def name_for(tip, cod):
    return NAME_LOOKUP.get(f"{tip}|{cod}", f"Cód. {tip}.{cod}")

def fig_top25():
    g = df.groupby(['TIPEQUIP','CODEQUIP'])['QT_EXIST'].sum().reset_index()
    g['name'] = g.apply(lambda r: name_for(r['TIPEQUIP'], r['CODEQUIP']), axis=1)
    g['cat'] = g['TIPEQUIP'].map(TIP_NAMES).str.replace("\n", " ")
    g = g.sort_values('QT_EXIST', ascending=False).head(25).iloc[::-1]
    
    cat_colors = {k: CIVIDIS(0.1 + 0.8*i/9) for i, k in enumerate(sorted(TIP_NAMES.keys()))}
    colors = [cat_colors[r['TIPEQUIP']] for _, r in g.iterrows()]
    
    fig, ax = plt.subplots(figsize=(8, 8.5))
    y_pos = np.arange(len(g))
    bars = ax.barh(y_pos, g['QT_EXIST']/1000, color=colors, edgecolor='#222', linewidth=0.5)
    
    labels = [f"{r['name'][:48]} ({r['TIPEQUIP']}.{r['CODEQUIP']})" for _, r in g.iterrows()]
    ax.set_yticks(y_pos); ax.set_yticklabels(labels, fontsize=8)
    for b, v in zip(bars, g['QT_EXIST']):
        ax.text(v/1000 + 4, b.get_y() + b.get_height()/2, f"{v:,.0f}",
                va='center', fontsize=7.5)
    ax.set_xlabel("Unidades cadastradas (mil)")
    ax.set_title("Top 25 equipamentos — Brasil Dez/2024", fontsize=10.5, fontweight='bold')
    ax.grid(axis='x', linestyle=':', alpha=0.4)
    
    # Legenda de categorias presentes
    present_cats = sorted(g['TIPEQUIP'].unique())
    handles = [mpl.patches.Patch(facecolor=cat_colors[k], edgecolor='#222',
                                  label=TIP_NAMES.get(k,'?').replace('\n',' '))
               for k in present_cats]
    ax.legend(handles=handles, loc='lower right', fontsize=7.5, framealpha=0.9)
    save(fig, "fig03-top25")


# ─── Fig 4 — Bug demonstration (42=EEG vs 1:12=RM) ──────────────────────────
def fig_bug_demo():
    rm_real = df[(df['TIPEQUIP']=='1') & (df['CODEQUIP']=='12')]
    eeg = df[(df['TIPEQUIP']=='4') & (df['CODEQUIP']=='42')]
    cod42_all = df[df['CODEQUIP']=='42']
    
    fig, axes = plt.subplots(1, 2, figsize=(8.5, 4))
    
    # LEFT: side-by-side magnitudes
    ax = axes[0]
    items = [
        ("RM real\n(TIPEQUIP=1\nCODEQUIP=12)", rm_real['QT_EXIST'].sum(), '#16a34a'),
        ("Filtro WP#4 v1\nCODEQUIP=42\n(= EEG)", cod42_all['QT_EXIST'].sum(), '#dc2626'),
    ]
    labels = [t[0] for t in items]; vals = [t[1] for t in items]; cols = [t[2] for t in items]
    bars = ax.bar(labels, vals, color=cols, edgecolor='#222', linewidth=0.8, width=0.6)
    for b, v in zip(bars, vals):
        ax.text(b.get_x()+b.get_width()/2, v+200, f"{v:,.0f}",
                ha='center', fontsize=10, fontweight='bold')
    ax.set_ylabel("Unidades nacional Dez/2024")
    ax.set_title("Magnitudes — RM real vs. filtro buggy", fontsize=9.5, fontweight='bold')
    ax.set_ylim(0, max(vals)*1.18)
    ax.grid(axis='y', linestyle=':', alpha=0.4)
    
    # RIGHT: per Mhab vs OECD median
    ax = axes[1]
    rm_pm  = rm_real['QT_EXIST'].sum() / TOTAL_POP
    eeg_pm = cod42_all['QT_EXIST'].sum() / TOTAL_POP
    items = [
        ("RM real\n(1:12)",       rm_pm, '#16a34a'),
        ("\"RM\" do WP#4 v1\n(= 4:42 EEG)", eeg_pm, '#dc2626'),
        ("OCDE mediana\n(2021)",  17.0,  '#888'),
    ]
    labels = [t[0] for t in items]; vals = [t[1] for t in items]; cols = [t[2] for t in items]
    bars = ax.bar(labels, vals, color=cols, edgecolor='#222', linewidth=0.8, width=0.6)
    for b, v in zip(bars, vals):
        ax.text(b.get_x()+b.get_width()/2, v+1, f"{v:.1f}",
                ha='center', fontsize=10, fontweight='bold')
    ax.axhline(17, color='#888', linestyle='--', linewidth=0.8, alpha=0.6)
    ax.set_ylabel("Unidades por milhão de hab.")
    ax.set_title("Densidade per capita vs. OCDE", fontsize=9.5, fontweight='bold')
    ax.set_ylim(0, max(vals)*1.18)
    ax.grid(axis='y', linestyle=':', alpha=0.4)
    
    plt.suptitle("Demonstração empírica do erro de metadados — Brasil Dez/2024",
                 fontsize=10.5, fontweight='bold', y=1.02)
    plt.tight_layout()
    save(fig, "fig04-bug-demonstration")


# ─── Fig 5 — RM REAL distribution by UF (corrected) ────────────────────────
def fig_rm_corrected_by_uf():
    rm = df[(df['TIPEQUIP']=='1') & (df['CODEQUIP']=='12')]
    by_uf = rm.groupby('UF')['QT_EXIST'].sum().to_dict()
    items = sorted([(uf, units, units/POP_BR[uf])
                    for uf, units in by_uf.items() if uf in POP_BR],
                   key=lambda t: -t[2])
    fig, ax = plt.subplots(figsize=(7.5, 7.5))
    y = np.arange(len(items))
    pm = [t[2] for t in items]; ufs = [t[0] for t in items]; absol = [t[1] for t in items]
    colors = [CIVIDIS(0.15 + 0.7 * (1 - p/max(pm))) for p in pm]
    bars = ax.barh(y, pm, color=colors, edgecolor='#222', linewidth=0.5)
    ax.set_yticks(y); ax.set_yticklabels([f"{u} ({a:.0f} un)" for u, a, p in items], fontsize=8.5)
    for b, p in zip(bars, pm):
        ax.text(p+0.5, b.get_y()+b.get_height()/2, f"{p:.1f}",
                va='center', fontsize=8, fontweight='bold')
    ax.axvline(17, color='#dc2626', linestyle='--', linewidth=1, alpha=0.7,
               label="Mediana OCDE 2021 (17/Mhab)")
    ax.set_xlabel("RM por milhão de habitantes")
    ax.set_title("Brasil Dez/2024 — RM REAL por UF (TIPEQUIP=1, CODEQUIP=12)",
                 fontsize=10.5, fontweight='bold')
    ax.legend(loc='lower right', fontsize=8.5)
    ax.grid(axis='x', linestyle=':', alpha=0.4)
    save(fig, "fig05-rm-corrected-by-uf")


# ─── Fig 6 — TIPEQUIP=1 (Imagem) breakdown ─────────────────────────────────
def fig_imagem_breakdown():
    img = df[df['TIPEQUIP']=='1'].groupby('CODEQUIP')['QT_EXIST'].sum().reset_index()
    img['name'] = img['CODEQUIP'].apply(lambda c: name_for('1', c))
    img = img.sort_values('QT_EXIST', ascending=True)
    fig, ax = plt.subplots(figsize=(7.5, 6.5))
    y = np.arange(len(img))
    colors = [CIVIDIS(0.15 + 0.7*i/len(img)) for i in range(len(img))]
    bars = ax.barh(y, img['QT_EXIST'], color=colors, edgecolor='#222', linewidth=0.5)
    ax.set_yticks(y)
    labels = [f"{r['name']} ({r['CODEQUIP']})" for _, r in img.iterrows()]
    ax.set_yticklabels(labels, fontsize=8)
    for b, v in zip(bars, img['QT_EXIST']):
        ax.text(v+200, b.get_y()+b.get_height()/2, f"{v:,.0f}",
                va='center', fontsize=7.5)
    ax.set_xlabel("Unidades cadastradas")
    ax.set_title("TIPEQUIP=1 (Diagnóstico por Imagem) — Brasil Dez/2024",
                 fontsize=10.5, fontweight='bold')
    ax.grid(axis='x', linestyle=':', alpha=0.4)
    save(fig, "fig06-imagem-breakdown")


# ─── Fig 7 — Regional concentration heatmap (TIPEQUIP × Region) ────────────
def fig_regional_heatmap():
    df['region'] = df['UF'].map(REGION)
    pivot = df.pivot_table(values='QT_EXIST', index='TIPEQUIP', columns='region',
                            aggfunc='sum', fill_value=0)
    pivot.index = [TIP_NAMES.get(k,'?').replace('\n',' ') for k in pivot.index]
    region_order = ['Norte','Nordeste','Centro-Oeste','Sudeste','Sul']
    pivot = pivot[region_order]
    
    region_pop = {r: sum(POP_BR[u] for u in POP_BR if REGION[u]==r) for r in region_order}
    pivot_pm = pivot.div(pivot.sum().sum()) * 100  # % of national total per cell
    
    fig, ax = plt.subplots(figsize=(7.5, 5.5))
    im = ax.imshow(pivot_pm.values, cmap='cividis_r', aspect='auto')
    ax.set_xticks(range(len(region_order))); ax.set_xticklabels(region_order, fontsize=9)
    ax.set_yticks(range(len(pivot.index))); ax.set_yticklabels(pivot.index, fontsize=9)
    for i in range(pivot_pm.shape[0]):
        for j in range(pivot_pm.shape[1]):
            v = pivot_pm.iloc[i, j]
            ax.text(j, i, f"{v:.1f}%", ha='center', va='center',
                    color='white' if v > pivot_pm.values.mean() else 'black',
                    fontsize=8, fontweight='bold')
    ax.set_title("% do parque nacional por categoria × região — Dez/2024",
                 fontsize=10.5, fontweight='bold', pad=10)
    cbar = plt.colorbar(im, ax=ax, fraction=0.04, pad=0.02)
    cbar.set_label("% nacional", fontsize=8)
    save(fig, "fig07-regional-heatmap")


# ─── Fig 8 — SUS share by category ─────────────────────────────────────────
def fig_sus_share():
    df['is_sus'] = df['IND_SUS'] == '1'
    g = df.groupby(['TIPEQUIP', 'is_sus'])['QT_EXIST'].sum().unstack(fill_value=0)
    g.columns = ['Privado', 'SUS']
    g['total'] = g['SUS'] + g['Privado']
    g['sus_share'] = g['SUS'] / g['total'] * 100
    g = g.sort_values('total', ascending=True)
    
    fig, ax = plt.subplots(figsize=(7.5, 4.8))
    y = np.arange(len(g))
    sus_pct  = g['SUS']  / g['total'] * 100
    priv_pct = g['Privado'] / g['total'] * 100
    ax.barh(y, sus_pct,  color='#1d4ed8', label='Disponível para SUS')
    ax.barh(y, priv_pct, left=sus_pct, color='#be185d', label='Privado')
    for i, (yi, sp, p) in enumerate(zip(y, sus_pct, priv_pct)):
        ax.text(sp/2, yi, f"{sp:.0f}%", ha='center', va='center', color='white',
                fontsize=8, fontweight='bold')
        ax.text(sp+p/2, yi, f"{p:.0f}%", ha='center', va='center', color='white',
                fontsize=8, fontweight='bold')
    
    cat_labels = [TIP_NAMES.get(k, f"Cat {k}").replace('\n', ' ')
                  + f" ({g.loc[k,'total']/1000:.0f}K)" for k in g.index]
    ax.set_yticks(y); ax.set_yticklabels(cat_labels, fontsize=8.5)
    ax.set_xlabel("% das unidades")
    ax.set_xlim(0, 100)
    ax.set_title("SUS vs. Privado por categoria — Brasil Dez/2024", fontsize=10.5, fontweight='bold')
    ax.legend(loc='lower right', fontsize=8.5, framealpha=0.95)
    save(fig, "fig08-sus-share-by-category")


fig_meta_correction()
fig_by_category()
fig_top25()
fig_bug_demo()
fig_rm_corrected_by_uf()
fig_imagem_breakdown()
fig_regional_heatmap()
fig_sus_share()
print("done.")

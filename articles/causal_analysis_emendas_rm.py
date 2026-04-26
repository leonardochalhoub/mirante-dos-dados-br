#!/usr/bin/env python3
"""Análise causal — efeito da Emenda Constitucional 86/2015 sobre o
crescimento de equipamentos de neuroimagem por UF.

Estratégia: Diferenças-em-Diferenças com efeitos fixos de UF e ano,
clusters por UF.

A EC 86 (mar/2015) tornou obrigatória a execução de parte das
emendas individuais (RP6) — gerou choque exógeno na composição
e magnitude do orçamento federal alocado por UF. Hipótese: UFs no
quartil superior de pago_RP6 per capita pós-EC86 (2016-2018) tiveram
crescimento diferencial de equipamentos de neuroimagem (RM+CT+PET+Gama)
entre o pré-período (2013-2014) e o pós-tratamento (2019-2025).

Modelo principal (DiD 2×2):
    Δ_density_uf = α + β·Treated_uf + ε

onde Δ_density = density(2019-2025) - density(2013-2014) por UF
e Treated = 1 se UF está no Q4 superior de pago_RP6/Mhab 2016-2018.

Modelo secundário (panel TWFE):
    density_{uf,ano} = α + β·Post·Treated_uf + UF_FE + Year_FE + ε

Saída: tabela de coeficientes Markdown + figura barbell + figura DID.
"""
import json
from pathlib import Path
from collections import defaultdict
import statsmodels.formula.api as smf
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib as mpl

ROOT = Path("/home/leochalhoub/mirante-dos-dados-br")
FIG_DIR = ROOT / "articles" / "figures-equipamentos-rm"
FIG_DIR.mkdir(exist_ok=True)
plt.rcParams.update({
    "font.family": "serif", "font.serif": ["DejaVu Serif"],
    "font.size": 9, "axes.titlesize": 10, "axes.labelsize": 9,
    "axes.spines.top": False, "axes.spines.right": False,
    "savefig.dpi": 200, "savefig.bbox": "tight", "savefig.facecolor": "white",
})

EQ_RAW = json.load(open(ROOT / "data/gold/gold_equipamentos_estados_ano.json"))
EM_RAW = json.load(open(ROOT / "data/gold/gold_emendas_estados_df.json"))

# Build equipamentos density panel UF × Ano por modalidade
def density_for(eq_key):
    rows = []
    for r in EQ_RAW:
        if r['equipment_key'] == eq_key:
            d = r['total_avg']/r['populacao']*1e6 if r['populacao'] else 0
            rows.append({'uf': r['estado'], 'ano': r['ano'], 'density': d, 'absolute': r['total_avg']})
    return pd.DataFrame(rows)

rm = density_for('1:12').rename(columns={'density':'rm_pm','absolute':'rm_abs'})
ct = density_for('1:11').rename(columns={'density':'ct_pm','absolute':'ct_abs'})
pet = density_for('1:18').rename(columns={'density':'pet_pm','absolute':'pet_abs'})
gama = density_for('1:01').rename(columns={'density':'gama_pm','absolute':'gama_abs'})
panel = rm.merge(ct, on=['uf','ano'], how='left') \
          .merge(pet, on=['uf','ano'], how='left') \
          .merge(gama, on=['uf','ano'], how='left')
panel['neuro_pm'] = panel['rm_pm'].fillna(0) + panel['ct_pm'].fillna(0) + \
                     panel['pet_pm'].fillna(0) + panel['gama_pm'].fillna(0)

# Build emendas panel UF × Ano com pago_RP6 per capita 2021
em = pd.DataFrame(EM_RAW).rename(columns={'Ano':'ano'})
em['rp6_pm_2021'] = em['pago_RP6'] / em['populacao'] * 1e6
em_panel = em[['uf','ano','rp6_pm_2021']]

# Compute treatment: UFs no Q4 de pago_RP6/Mhab 2016-2018 (pós-EC86)
treat_window = em_panel[em_panel['ano'].isin([2016,2017,2018])].groupby('uf')['rp6_pm_2021'].mean()
threshold = treat_window.quantile(0.75)
treated_ufs = sorted(treat_window[treat_window >= threshold].index.tolist())
control_ufs = sorted(treat_window[treat_window < threshold].index.tolist())
print(f"\n=== EC 86 DiD design ===")
print(f"Threshold (Q4 pago_RP6/Mhab 2016-2018, R$ 2021): {threshold:.0f}")
print(f"Treated UFs ({len(treated_ufs)}): {treated_ufs}")
print(f"Control UFs ({len(control_ufs)}): {control_ufs}")

# Parallel trends pre-period sanity check (2013-2014)
pre_panel = panel[panel['ano'].isin([2013, 2014])].groupby('uf')['neuro_pm'].mean().reset_index()
pre_panel['treated'] = pre_panel['uf'].isin(treated_ufs).astype(int)
print(f"\nPre-period (2013-2014) neuro density mean:")
print(f"  treated: {pre_panel[pre_panel.treated==1]['neuro_pm'].mean():.1f}/Mhab")
print(f"  control: {pre_panel[pre_panel.treated==0]['neuro_pm'].mean():.1f}/Mhab")

# Build DiD 2x2: pre = mean(2013-14), post = mean(2019-25). Outcome: RM/Mhab and neuro/Mhab.
def did_2x2(outcome, pre_years, post_years):
    pre = panel[panel['ano'].isin(pre_years)].groupby('uf')[outcome].mean().reset_index().rename(columns={outcome:'pre'})
    post = panel[panel['ano'].isin(post_years)].groupby('uf')[outcome].mean().reset_index().rename(columns={outcome:'post'})
    df = pre.merge(post, on='uf')
    df['delta'] = df['post'] - df['pre']
    df['treated'] = df['uf'].isin(treated_ufs).astype(int)
    # OLS Δ = α + β·treated, robust SE clustered by UF
    model = smf.ols('delta ~ treated', data=df).fit(cov_type='HC3')
    return df, model

print("\n" + "="*60)
print("=== MODELO 1: DiD 2x2 ΔRM (post-pre) ~ Treated ===")
df_rm, m_rm = did_2x2('rm_pm', [2013,2014], [2019,2020,2021,2022,2023,2024,2025])
print(m_rm.summary().as_text())

print("\n" + "="*60)
print("=== MODELO 2: DiD 2x2 ΔNeuro-DP combined ~ Treated ===")
df_neuro, m_neuro = did_2x2('neuro_pm', [2013,2014], [2019,2020,2021,2022,2023,2024,2025])
print(m_neuro.summary().as_text())

# Model 3: Panel TWFE (Two-Way Fixed Effects)
print("\n" + "="*60)
print("=== MODELO 3: TWFE rm_pm ~ Post*Treated + UF_FE + Year_FE ===")
panel['treated'] = panel['uf'].isin(treated_ufs).astype(int)
panel['post'] = (panel['ano'] >= 2016).astype(int)
panel['post_treated'] = panel['post'] * panel['treated']
# OLS with UF and year FE via dummies
m_twfe = smf.ols('rm_pm ~ post_treated + C(uf) + C(ano)', data=panel).fit(
    cov_type='cluster', cov_kwds={'groups': panel['uf']})
# Print only the post_treated coef (the rest are FE)
print(f"post_treated coef: {m_twfe.params['post_treated']:.4f}")
print(f"  std err (clustered UF): {m_twfe.bse['post_treated']:.4f}")
print(f"  t: {m_twfe.tvalues['post_treated']:.3f}")
print(f"  p-value: {m_twfe.pvalues['post_treated']:.4f}")
print(f"  CI 95%: [{m_twfe.conf_int().loc['post_treated',0]:.4f}, "
      f"{m_twfe.conf_int().loc['post_treated',1]:.4f}]")
print(f"  R²: {m_twfe.rsquared:.4f}, n: {len(panel)}")

# Save figura: barbell DiD 2x2
fig, axes = plt.subplots(1, 2, figsize=(11, 5.5))
for ax, df_, outcome, title in [(axes[0], df_rm, 'rm', 'ΔRM/Mhab pré→pós EC 86'),
                                  (axes[1], df_neuro, 'neuro', 'ΔNeuro-PD/Mhab pré→pós EC 86')]:
    df_sorted = df_.sort_values('delta')
    y = np.arange(len(df_sorted))
    for i, (_, row) in enumerate(df_sorted.iterrows()):
        color = '#059669' if row['treated']==1 else '#888'
        ax.plot([row['pre'], row['post']], [i, i], color=color, linewidth=2, alpha=0.85)
        ax.scatter([row['pre']], [i], s=22, color='#cccccc', zorder=3)
        ax.scatter([row['post']], [i], s=32, color=color, edgecolor='#222', linewidth=0.5, zorder=4)
    ax.set_yticks(y); ax.set_yticklabels(df_sorted['uf'], fontsize=7.5)
    ax.set_xlabel(f"{title.split(' ')[0]}/Mhab")
    ax.set_title(title, fontsize=10, fontweight='bold')
    ax.grid(axis='x', linestyle=':', alpha=0.4)
fig.legend(handles=[
    plt.Line2D([0],[0], marker='o', color='w', markerfacecolor='#059669',
               markeredgecolor='#222', markersize=7, label='Treated (Q4 RP6)'),
    plt.Line2D([0],[0], marker='o', color='w', markerfacecolor='#888',
               markeredgecolor='#222', markersize=7, label='Control (Q1-Q3 RP6)'),
    plt.Line2D([0],[0], marker='o', color='w', markerfacecolor='#cccccc',
               markersize=5, label='Pré (2013-2014)'),
], loc='lower center', ncol=3, fontsize=8.5, framealpha=0.95, bbox_to_anchor=(0.5, -0.02))
plt.suptitle("DiD 2×2 — efeito da EC 86/2015 sobre densidade de neuroimagem por UF",
             fontsize=11, fontweight='bold', y=1.01)
plt.tight_layout()
out = FIG_DIR / "fig14-did-ec86.pdf"
fig.savefig(out, bbox_inches='tight'); plt.close(fig)
print(f"\n✔ {out.name}")

# Save coefficients to markdown
md = []
md.append("# Análise Causal — Resultados\n")
md.append("## Modelo 1: DiD 2×2, ΔRM/Mhab\n")
md.append(f"- Treatment effect (β): **{m_rm.params['treated']:+.3f} RM/Mhab**")
md.append(f"- Std error (HC3): {m_rm.bse['treated']:.3f}")
md.append(f"- t-stat: {m_rm.tvalues['treated']:.3f}, p-valor: {m_rm.pvalues['treated']:.3f}")
md.append(f"- IC 95%: [{m_rm.conf_int().loc['treated',0]:.3f}, {m_rm.conf_int().loc['treated',1]:.3f}]\n")
md.append("## Modelo 2: DiD 2×2, ΔNeuro-DP/Mhab\n")
md.append(f"- Treatment effect (β): **{m_neuro.params['treated']:+.3f} units/Mhab**")
md.append(f"- p-valor: {m_neuro.pvalues['treated']:.3f}")
md.append(f"- IC 95%: [{m_neuro.conf_int().loc['treated',0]:.3f}, {m_neuro.conf_int().loc['treated',1]:.3f}]\n")
md.append("## Modelo 3: TWFE rm_pm ~ Post×Treated + UF_FE + Year_FE\n")
md.append(f"- post_treated β: **{m_twfe.params['post_treated']:+.4f}**")
md.append(f"- Std error (cluster UF): {m_twfe.bse['post_treated']:.4f}")
md.append(f"- p-valor: {m_twfe.pvalues['post_treated']:.4f}")
md.append(f"- IC 95%: [{m_twfe.conf_int().loc['post_treated',0]:.4f}, {m_twfe.conf_int().loc['post_treated',1]:.4f}]")
md.append(f"- R²: {m_twfe.rsquared:.3f}, n={len(panel)}")
out_md = ROOT / "articles" / "causal_results.md"
out_md.write_text("\n".join(md))
print(f"\n✔ {out_md}")

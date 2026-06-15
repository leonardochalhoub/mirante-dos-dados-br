# -*- coding: utf-8 -*-
"""WP#2 — Camada de aprendizado de máquina (dados reais, UF × 2024).

Testa o Bolsa Família como *proxy* de pobreza e de desenvolvimento, em três
níveis didáticos: (1) correlação + regressão log-log interpretável;
(2) clustering K-means não supervisionado; (3) modelo supervisionado avançado
(Random Forest) com validação leave-one-out. Tudo reprodutível a partir do
gold dataset versionado, sem nenhum número hardcoded no texto.

    python3 articles/ml_pbf.py
"""
import json
from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.api as sm
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
from sklearn.metrics import silhouette_score, r2_score, mean_absolute_error
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import LinearRegression
from sklearn.model_selection import LeaveOneOut

ROOT = Path(__file__).resolve().parents[1]
GOLD = ROOT / "data" / "gold" / "gold_pbf_estados_df.json"
FIGDIR = ROOT / "articles" / "figures-pbf"
OUTMD = ROOT / "articles" / "ml_results_pbf.md"
YEAR = 2024

IDHM_2010 = {
    "AC": 0.663, "AL": 0.631, "AM": 0.674, "AP": 0.708, "BA": 0.660,
    "CE": 0.682, "DF": 0.824, "ES": 0.740, "GO": 0.735, "MA": 0.639,
    "MG": 0.731, "MS": 0.729, "MT": 0.725, "PA": 0.646, "PB": 0.658,
    "PE": 0.673, "PI": 0.646, "PR": 0.749, "RJ": 0.761, "RN": 0.684,
    "RO": 0.690, "RR": 0.707, "RS": 0.746, "SC": 0.774, "SE": 0.665,
    "SP": 0.783, "TO": 0.699,
}
POBREZA_2019 = {
    "AC": 36.4, "AL": 47.4, "AM": 41.7, "AP": 35.5, "BA": 38.2,
    "CE": 41.9, "DF": 12.4, "ES": 17.1, "GO": 17.9, "MA": 51.9,
    "MG": 19.7, "MS": 17.0, "MT": 19.3, "PA": 41.4, "PB": 43.5,
    "PE": 41.0, "PI": 47.5, "PR": 13.7, "RJ": 19.1, "RN": 39.4,
    "RO": 22.8, "RR": 38.1, "RS": 12.1, "SC": 9.8, "SE": 41.9,
    "SP": 13.8, "TO": 28.6,
}

RNG = 42

# ─────────────────────────────────────────── 1. montagem do dataset
df = pd.DataFrame(json.load(open(GOLD)))
df = df[df["Ano"] == YEAR].copy()
df["penetracao"] = df["n_benef"] / df["populacao"] * 100        # % da população
df["pbf_pc"] = df["pbfPerCapita"]                               # R$/hab (2021)
df["pbf_pb"] = df["pbfPerBenef"]                                # R$/benef (2021)
df["idhm"] = df["uf"].map(IDHM_2010)
df["pobreza"] = df["uf"].map(POBREZA_2019)
df = df.dropna().reset_index(drop=True)
N = len(df)

lines = ["# Camada de ML — WP#2 Bolsa Família",
         "",
         f"Gerado por `ml_pbf.py`. Unidade: 27 UFs no exercício {YEAR}. "
         "Features do BF (penetração, per capita, per beneficiário) testadas "
         "como *proxy* de pobreza (PNAD-C 2019) e desenvolvimento (IDH-M 2010).",
         f"\nN = {N} UFs.", ""]

# ─────────────────────────────────────────── 2. correlações
lines.append("## 1. Correlações de Pearson")
cols = ["penetracao", "pbf_pc", "pbf_pb", "pobreza", "idhm"]
corr = df[cols].corr()
for a in ["penetracao", "pbf_pc"]:
    for b in ["pobreza", "idhm"]:
        lines.append(f"- r({a}, {b}) = {corr.loc[a,b]:+.3f}")
lines.append("")

# ─────────────────────────────────────────── 3. regressão log-log interpretável
lines.append("## 2. Regressão log–log (pobreza ~ penetração)")
x = np.log(df["penetracao"].values)
y = np.log(df["pobreza"].values)
X = sm.add_constant(x)
m = sm.OLS(y, X).fit()
b0, b1 = m.params
lines += [
    f"- log(pobreza) = {b0:+.3f} + {b1:+.3f}·log(penetração)",
    f"- elasticidade β1 = {b1:+.3f} (p = {m.pvalues[1]:.2e})",
    f"- R² = {m.rsquared:.3f}  | R² ajustado = {m.rsquared_adj:.3f}",
    f"- Leitura: +1% na penetração associa-se a {b1:+.2f}% na taxa de pobreza.",
    "",
]
# desenvolvimento: idhm ~ penetração (nível)
Xd = sm.add_constant(df["penetracao"].values)
md = sm.OLS(df["idhm"].values, Xd).fit()
lines += [
    "## 3. Regressão (IDH-M ~ penetração)",
    f"- IDH-M = {md.params[0]:+.4f} {md.params[1]:+.5f}·penetração",
    f"- β1 = {md.params[1]:+.5f} (p = {md.pvalues[1]:.2e}) | R² = {md.rsquared:.3f}",
    f"- Leitura: cada +1 p.p. de penetração associa-se a {md.params[1]:+.4f} no IDH-M.",
    "",
]

# ─────────────────────────────────────────── 4. K-means clustering
lines.append("## 4. Clustering K-means (não supervisionado)")
feat = ["penetracao", "pbf_pc", "idhm", "pobreza"]
Z = StandardScaler().fit_transform(df[feat].values)
sil = {}
for k in (2, 3, 4):
    km = KMeans(n_clusters=k, random_state=RNG, n_init=10).fit(Z)
    sil[k] = silhouette_score(Z, km.labels_)
kbest = max(sil, key=sil.get)
lines.append("- Silhouette: " + ", ".join(f"k={k}: {v:.3f}" for k, v in sil.items())
             + f"  → escolhido k={kbest}")
km = KMeans(n_clusters=kbest, random_state=RNG, n_init=10).fit(Z)
df["cluster"] = km.labels_
# ordena clusters por pobreza média (0 = menos pobre) p/ leitura estável
order = df.groupby("cluster")["pobreza"].mean().sort_values().index.tolist()
remap = {c: i for i, c in enumerate(order)}
df["cluster"] = df["cluster"].map(remap)
for c in range(kbest):
    g = df[df["cluster"] == c]
    lines.append(
        f"  - Cluster {c} (n={len(g)}): pobreza méd {g['pobreza'].mean():.1f}%, "
        f"IDH-M {g['idhm'].mean():.3f}, penetração {g['penetracao'].mean():.1f}%, "
        f"per capita R$ {g['pbf_pc'].mean():.0f} | UFs: {', '.join(sorted(g['uf']))}")
lines.append("")

# ─────────────────────────────────────────── 5. supervisionado avançado (LOO-CV)
lines.append("## 5. Modelo supervisionado — prever pobreza só com features do BF")
Xs = df[["penetracao", "pbf_pc", "pbf_pb"]].values
ys = df["pobreza"].values
loo = LeaveOneOut()
def loo_pred(model_factory):
    pred = np.empty(N)
    for tr, te in loo.split(Xs):
        mdl = model_factory()
        mdl.fit(Xs[tr], ys[tr])
        pred[te] = mdl.predict(Xs[te])
    return pred
pred_lin = loo_pred(lambda: LinearRegression())
pred_rf = loo_pred(lambda: RandomForestRegressor(
    n_estimators=400, max_depth=4, random_state=RNG))
for name, pr in [("Regressão linear", pred_lin), ("Random Forest", pred_rf)]:
    lines.append(f"- {name}: R²(LOO) = {r2_score(ys, pr):+.3f} | "
                 f"MAE = {mean_absolute_error(ys, pr):.2f} p.p.")
# importâncias (fit no conjunto completo, só p/ ranking)
rf = RandomForestRegressor(n_estimators=400, max_depth=4, random_state=RNG).fit(Xs, ys)
imp = sorted(zip(["penetração", "per capita", "per beneficiário"],
                 rf.feature_importances_), key=lambda t: -t[1])
lines.append("- Importância (Random Forest): "
             + ", ".join(f"{n} {v:.2f}" for n, v in imp))
lines.append("")

OUTMD.write_text("\n".join(lines), encoding="utf-8")
print("\n".join(lines))

# ─────────────────────────────────────────── 6. figuras (estilo Mirante)
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patheffects as pe
from mirante_style import apply_mirante_style, PALETTE_MIRANTE, GOLDEN_FIGSIZE
from mirante_charts import editorial_title, source_note
apply_mirante_style()

CL = [PALETTE_MIRANTE["principal"], PALETTE_MIRANTE["destaque"],
      PALETTE_MIRANTE["secundario"], PALETTE_MIRANTE["neutro"]]
HALO = [pe.withStroke(linewidth=2.2, foreground="white")]
SRC = "Elaboração própria a partir do gold dataset (CGU/PBF), IDH-M (PNUD/Atlas Brasil 2010) e pobreza (IBGE/PNAD-C 2019). Processamento Mirante dos Dados."

# Fig 20 — scatter penetração × pobreza (o proxy, intuitivo), por cluster + reta
fig, ax = plt.subplots(figsize=GOLDEN_FIGSIZE)
for c in range(kbest):
    g = df[df["cluster"] == c]
    ax.scatter(g["penetracao"], g["pobreza"], s=130, c=CL[c],
               edgecolor="white", linewidth=1.1, zorder=3,
               label=("Cluster 0 — mais desenvolvido" if c == 0
                      else "Cluster 1 — Nordeste + Norte"))
xs = np.linspace(df["penetracao"].min(), df["penetracao"].max(), 100)
fit = np.polyfit(df["penetracao"], df["pobreza"], 1)
ax.plot(xs, np.polyval(fit, xs), color=PALETTE_MIRANTE["neutro"],
        linewidth=1.6, linestyle="--", zorder=2,
        label=f"reta de ajuste (r = {corr.loc['penetracao','pobreza']:+.2f})")
for i, uf in enumerate(df["uf"]):
    ax.annotate(uf, (df["penetracao"].iloc[i], df["pobreza"].iloc[i]),
                fontsize=7.5, ha="center", va="center", color="white",
                fontweight="bold", zorder=4)
ax.set_xlabel("Penetração do Bolsa Família (% da população beneficiária, 2024)")
ax.set_ylabel("Taxa de pobreza monetária (PNAD-C 2019, %)")
ax.grid(axis="both", color=PALETTE_MIRANTE["rule"], linewidth=0.8)
ax.legend(frameon=False, fontsize=9, loc="upper left")
editorial_title(ax, "O Bolsa Família como proxy de pobreza",
                "Quanto maior a cobertura do programa numa UF, maior a pobreza — associação quase perfeita.")
source_note(ax, SRC)
fig.savefig(FIGDIR / "fig20-ml-scatter.pdf", bbox_inches="tight")
plt.close(fig)

# Fig 18 — clusters no plano das componentes principais (PCA)
pca = PCA(n_components=2, random_state=RNG).fit(Z)
P = pca.transform(Z)
fig, ax = plt.subplots(figsize=GOLDEN_FIGSIZE)
for c in range(kbest):
    msk = df["cluster"].values == c
    ax.scatter(P[msk, 0], P[msk, 1], s=150, c=CL[c], edgecolor="white",
               linewidth=1.1, zorder=3,
               label=("Cluster 0 — mais desenvolvido" if c == 0
                      else "Cluster 1 — Nordeste + Norte"))
for i, uf in enumerate(df["uf"]):
    ax.annotate(uf, (P[i, 0], P[i, 1]), fontsize=7.5, ha="center", va="center",
                color="white", fontweight="bold", zorder=4)
ax.set_xlabel(f"Componente principal 1 ({pca.explained_variance_ratio_[0]*100:.0f}% da variância)")
ax.set_ylabel(f"Componente principal 2 ({pca.explained_variance_ratio_[1]*100:.0f}%)")
ax.grid(color=PALETTE_MIRANTE["rule"], linewidth=0.8)
ax.legend(frameon=False, fontsize=9, loc="best")
editorial_title(ax, "Duas Brasis emergem sem rótulos",
                "K-means (k=2) sobre penetração, per capita, IDH-M e pobreza padronizados.")
source_note(ax, SRC)
fig.savefig(FIGDIR / "fig18-ml-clusters.pdf", bbox_inches="tight")
plt.close(fig)

# Fig 19 — pobreza observada vs prevista (Random Forest, leave-one-out)
fig, ax = plt.subplots(figsize=GOLDEN_FIGSIZE)
lim = [ys.min() - 3, ys.max() + 3]
ax.plot(lim, lim, "--", color=PALETTE_MIRANTE["contexto_dark"], zorder=2,
        label="previsão perfeita (y = x)")
ax.scatter(ys, pred_rf, s=130, c=PALETTE_MIRANTE["principal"],
           edgecolor="white", linewidth=1.1, zorder=3)
for i, uf in enumerate(df["uf"]):
    ax.annotate(uf, (ys[i], pred_rf[i]), fontsize=7, ha="left", va="bottom",
                color=PALETTE_MIRANTE["neutro_soft"])
ax.set_xlabel("Pobreza observada (PNAD-C 2019, %)")
ax.set_ylabel("Pobreza prevista só com variáveis do BF (Random Forest, LOO, %)")
ax.grid(color=PALETTE_MIRANTE["rule"], linewidth=0.8)
ax.legend(frameon=False, fontsize=9, loc="upper left")
editorial_title(ax, f"Previsão fora da amostra — R²(LOO) = {r2_score(ys, pred_rf):.2f}",
                "Cada UF é prevista por um modelo treinado nas outras 26.")
source_note(ax, SRC)
fig.savefig(FIGDIR / "fig19-ml-proxy-fit.pdf", bbox_inches="tight")
plt.close(fig)

print("\nFiguras: fig18-ml-clusters.pdf, fig19-ml-proxy-fit.pdf, fig20-ml-scatter.pdf")

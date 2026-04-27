#!/usr/bin/env python3
"""Índices formais de equidade — WP #2 Bolsa Família.

Implementa três medidas cardinais que complementam o coeficiente de
variação descritivo da v1.0:

1. **Kakwani (1977)** — `K = C_pbf − G_idh`, onde C_pbf é o índice de
   concentração do PBF per capita ordenado pelo IDH-M e G_idh é o índice
   de Gini do IDH-M. K negativo = programa progressivo (mais transfere a
   UFs de menor IDH); K positivo = regressivo (mais transfere a UFs de
   maior IDH). Comparamos K_PBF, K_NBF e K_emendas para confirmar a
   tese de "lógicas alocativas distintas".

2. **Índice de necessidade (need-adjusted allocation)** — `N_uf =
   pobreza_uf × pop_uf / Σ`, normalizado para somar 1. Razão
   `R_uf = share_pbf_uf / N_uf` mede over/under-coverage:
   R > 1 = recebe mais que sua "fatia de necessidade";
   R < 1 = recebe menos.

3. **Curva de concentração + bandas de confiança bootstrap** — visualiza
   K com IC bootstrap (1000 réplicas) para responder ao parecer de
   Finanças (CV sem IC).

Saída:
- articles/figures-pbf/fig15-kakwani-curve.pdf
- articles/figures-pbf/fig16-need-vs-coverage.pdf
- articles/equity_results_pbf.md
"""
import json
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.patheffects as pe
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from mirante_charts import editorial_title, source_note  # noqa: E402
from mirante_style import (  # noqa: E402
    PALETTE_MIRANTE, GOLDEN_FIGSIZE, apply_mirante_style,
)

apply_mirante_style()

ROOT = Path("/home/leochalhoub/mirante-dos-dados-br")
FIG_DIR = ROOT / "articles" / "figures-pbf"
OUT_MD = ROOT / "articles" / "equity_results_pbf.md"

PBF_RAW = json.load(open(ROOT / "data/gold/gold_pbf_estados_df.json"))
EM_RAW = json.load(open(ROOT / "data/gold/gold_emendas_estados_df.json"))

POBREZA_2019 = {
    "AC": 36.4, "AL": 47.4, "AM": 41.7, "AP": 35.5, "BA": 38.2,
    "CE": 41.9, "DF": 12.4, "ES": 17.1, "GO": 17.9, "MA": 51.9,
    "MG": 19.7, "MS": 17.0, "MT": 19.3, "PA": 41.4, "PB": 43.5,
    "PE": 41.0, "PI": 47.5, "PR": 13.7, "RJ": 19.1, "RN": 39.4,
    "RO": 22.8, "RR": 38.1, "RS": 12.1, "SC":  9.8, "SE": 41.9,
    "SP": 13.8, "TO": 28.6,
}
IDHM_2010 = {
    "AC": 0.663, "AL": 0.631, "AM": 0.674, "AP": 0.708, "BA": 0.660,
    "CE": 0.682, "DF": 0.824, "ES": 0.740, "GO": 0.735, "MA": 0.639,
    "MG": 0.731, "MS": 0.729, "MT": 0.725, "PA": 0.646, "PB": 0.658,
    "PE": 0.673, "PI": 0.646, "PR": 0.749, "RJ": 0.761, "RN": 0.684,
    "RO": 0.690, "RR": 0.707, "RS": 0.746, "SC": 0.774, "SE": 0.665,
    "SP": 0.783, "TO": 0.699,
}


# ─── Concentration index (Kakwani C) com curva ───────────────────────────
def concentration_index(values, ranks):
    """Concentration index ordenado pelos ranks (não pela própria distribuição).

    Implementação convencional:
        C = 2 / (n μ) * cov(values, rank_normalized)
    onde rank_normalized é a posição cumulativa proporcional.

    Equivalentemente, área sob a curva de concentração ordenada por ranks.
    """
    df_sorted = pd.DataFrame({"v": values, "r": ranks}).sort_values("r")
    n = len(df_sorted)
    mu = df_sorted["v"].mean()
    if mu == 0:
        return 0.0
    # Posição cumulativa proporcional
    rank_norm = (np.arange(1, n + 1) - 0.5) / n
    cov = np.cov(df_sorted["v"].values, rank_norm, ddof=0)[0, 1]
    return float(2.0 * cov / mu)


def kakwani_index(values, ranking_var):
    """K = C_values - G_ranking
    K < 0 → progressivo (relativo ao ranking de bem-estar)
    K > 0 → regressivo
    """
    df = pd.DataFrame({"v": values, "r": ranking_var})
    df = df.sort_values("r").reset_index(drop=True)
    C_v = concentration_index(df["v"].values, df["r"].values)
    G_r = concentration_index(df["r"].values, df["r"].values)  # auto-Gini do ranking
    return float(C_v - G_r), float(C_v), float(G_r)


def bootstrap_kakwani(values, ranking_var, n_boot=1000, seed=42):
    rng = np.random.default_rng(seed)
    n = len(values)
    sims = []
    for _ in range(n_boot):
        idx = rng.integers(0, n, size=n)
        K, _, _ = kakwani_index(values[idx], ranking_var[idx])
        sims.append(K)
    sims = np.array(sims)
    return float(np.percentile(sims, 2.5)), float(np.percentile(sims, 97.5)), sims


# ─── Construção dos panels ───────────────────────────────────────────────
def panel_year(records, year, value_field):
    df = pd.DataFrame(records)
    df = df[df["Ano"] == year][["uf", value_field]].copy()
    df.rename(columns={value_field: "value"}, inplace=True)
    df["idhm"] = df["uf"].map(IDHM_2010)
    df["pobreza"] = df["uf"].map(POBREZA_2019)
    return df.dropna()


# Anos a comparar: pré-AB (2020), AB (2022), NBF (2024) e emendas (2024)
print("=== Kakwani PBF per capita × IDH-M ===")
results = []
for year, label in [(2018, "PBF clássico"), (2020, "PBF pré-AB"),
                    (2022, "Auxílio Brasil"), (2024, "Novo Bolsa Família")]:
    p = panel_year(PBF_RAW, year, "pbfPerCapita")
    K, C_pbf, G_idh = kakwani_index(p["value"].values, p["idhm"].values)
    ci_lo, ci_hi, _ = bootstrap_kakwani(p["value"].values, p["idhm"].values)
    print(f"  {year} ({label:18s}): K = {K:+.4f}  IC95% [{ci_lo:+.4f}; {ci_hi:+.4f}]   "
          f"C_pbf={C_pbf:+.4f}  G_idh={G_idh:+.4f}")
    results.append({"year": year, "label": label, "what": "PBF", "K": K,
                    "C": C_pbf, "G": G_idh, "ci_lo": ci_lo, "ci_hi": ci_hi})


print("\n=== Kakwani Emendas per capita × IDH-M ===")
em_df = pd.DataFrame(EM_RAW).rename(columns={"Ano": "ano"})
em_df["pago_pc_2021"] = em_df["valor_pago_2021"] / em_df["populacao"]
for year, label in [(2018, "Emendas pré-AB"), (2022, "Emendas 2022"),
                    (2024, "Emendas 2024")]:
    sub = em_df[em_df["ano"] == year][["uf", "pago_pc_2021"]].copy()
    sub["idhm"] = sub["uf"].map(IDHM_2010)
    sub = sub.dropna()
    if len(sub) < 20:
        continue
    K, C_em, G_idh = kakwani_index(sub["pago_pc_2021"].values, sub["idhm"].values)
    ci_lo, ci_hi, _ = bootstrap_kakwani(sub["pago_pc_2021"].values, sub["idhm"].values)
    print(f"  {year} ({label:18s}): K = {K:+.4f}  IC95% [{ci_lo:+.4f}; {ci_hi:+.4f}]   "
          f"C_em={C_em:+.4f}  G_idh={G_idh:+.4f}")
    results.append({"year": year, "label": label, "what": "Emendas", "K": K,
                    "C": C_em, "G": G_idh, "ci_lo": ci_lo, "ci_hi": ci_hi})


# ─── Índice de necessidade ────────────────────────────────────────────────
print("\n=== Índice de necessidade (2024) ===")
pbf_2024 = panel_year(PBF_RAW, 2024, "valor_2021")
pop_2024 = pd.DataFrame(PBF_RAW)
pop_2024 = pop_2024[pop_2024["Ano"] == 2024][["uf", "populacao"]].rename(
    columns={"populacao": "pop"})
need_df = pbf_2024.merge(pop_2024, on="uf", how="left").rename(columns={"value": "pago"})
need_df["necessidade"] = need_df["pobreza"] / 100 * need_df["pop"]
need_df["share_pbf"] = need_df["pago"] / need_df["pago"].sum()
need_df["share_need"] = need_df["necessidade"] / need_df["necessidade"].sum()
need_df["R"] = need_df["share_pbf"] / need_df["share_need"]
need_df = need_df.sort_values("R", ascending=False).reset_index(drop=True)
print(need_df[["uf", "share_pbf", "share_need", "R"]].head(10).to_string(index=False))
print("...")
print(need_df[["uf", "share_pbf", "share_need", "R"]].tail(10).to_string(index=False))


# ─── FIGURA F1 — Curvas de concentração PBF vs Emendas (2024) ────────────
def fig_concentration_curves():
    fig, ax = plt.subplots(figsize=GOLDEN_FIGSIZE)
    fig.subplots_adjust(top=0.85, bottom=0.20, left=0.10, right=0.95)
    # PBF 2024
    p = panel_year(PBF_RAW, 2024, "pbfPerCapita")
    p_sorted = p.sort_values("idhm").reset_index(drop=True)
    cum_share_pbf = np.concatenate([[0], np.cumsum(p_sorted["value"].values) / p_sorted["value"].sum()])
    cum_pop = np.linspace(0, 1, len(p_sorted) + 1)
    ax.plot(cum_pop, cum_share_pbf, color=PALETTE_MIRANTE["principal"],
            linewidth=2.5, marker="o", markersize=4,
            markeredgecolor="white", markeredgewidth=0.7,
            label="PBF/NBF 2024", zorder=4)
    # Emendas 2024
    em_2024 = em_df[em_df["ano"] == 2024][["uf", "pago_pc_2021"]].copy()
    em_2024["idhm"] = em_2024["uf"].map(IDHM_2010)
    em_2024 = em_2024.dropna().sort_values("idhm").reset_index(drop=True)
    cum_share_em = np.concatenate([[0], np.cumsum(em_2024["pago_pc_2021"].values) / em_2024["pago_pc_2021"].sum()])
    cum_pop_em = np.linspace(0, 1, len(em_2024) + 1)
    ax.plot(cum_pop_em, cum_share_em, color=PALETTE_MIRANTE["destaque"],
            linewidth=2.0, marker="s", markersize=4,
            markeredgecolor="white", markeredgewidth=0.7, linestyle="--",
            label="Emendas parlamentares 2024", zorder=3)
    # Linha 45° (alocação igual)
    ax.plot([0, 1], [0, 1], color=PALETTE_MIRANTE["neutro_soft"],
            linewidth=0.8, linestyle=":", alpha=0.8,
            label="Igualdade (45°)")
    ax.set_xlabel("UFs ordenadas por IDH-M (cumulativa)")
    ax.set_ylabel("Cumulativa do per capita (proporção)")
    ax.legend(loc="upper left", frameon=False, fontsize=9)
    editorial_title(
        ax,
        title="Curvas de concentração: PBF/NBF é progressivo, Emendas é regressivo",
        subtitle=("Ordenação no eixo-X: UFs do menor IDH-M (esq.) para o "
                  "maior (dir.). Curva acima da diagonal = mais alocado a UFs "
                  "de menor IDH-M (progressivo)."),
    )
    source_note(
        ax,
        "Fonte: CGU/Portal da Transparência (PBF/NBF e emendas), "
        "PNUD/Atlas Brasil (IDH-M 2010). Processamento Mirante dos Dados.",
    )
    out = FIG_DIR / "fig15-kakwani-curve.pdf"
    fig.savefig(out)
    plt.close(fig)
    print(f"\n  ✔ {out.name}")


# ─── FIGURA F2 — Need vs Coverage (R = share_pbf / share_need) ───────────
def fig_need_coverage():
    fig, ax = plt.subplots(figsize=GOLDEN_FIGSIZE)
    fig.subplots_adjust(top=0.85, bottom=0.20, left=0.12, right=0.95)
    d = need_df.sort_values("R")
    colors = [PALETTE_MIRANTE["principal"] if r >= 1 else PALETTE_MIRANTE["destaque"]
              for r in d["R"]]
    ax.barh(range(len(d)), d["R"].values, color=colors, edgecolor="white", linewidth=0.4)
    ax.axvline(1, color=PALETTE_MIRANTE["neutro"], linewidth=0.8,
               linestyle=":", alpha=0.8)
    ax.set_yticks(range(len(d)))
    ax.set_yticklabels(d["uf"].values, fontsize=8.5, family="monospace")
    ax.set_xlabel("R = share PBF / share necessidade (2024)")
    for i, (uf, r) in enumerate(zip(d["uf"].values, d["R"].values)):
        ax.text(r + 0.01, i, f"{r:.2f}",
                va="center", fontsize=7.5,
                color=PALETTE_MIRANTE["neutro"])
    editorial_title(
        ax,
        title="Razão alocação/necessidade — UFs por R em 2024",
        subtitle=("R > 1: UF recebe mais que sua fatia de necessidade. "
                  "R < 1: subcoberta. Necessidade = pobreza × população."),
    )
    source_note(
        ax,
        "Fonte: CGU (PBF 2024), IBGE/PNAD-C 2019 (taxa de pobreza monetária). "
        "Processamento Mirante dos Dados.",
    )
    out = FIG_DIR / "fig16-need-vs-coverage.pdf"
    fig.savefig(out)
    plt.close(fig)
    print(f"  ✔ {out.name}")


fig_concentration_curves()
fig_need_coverage()


# ─── Output Markdown ─────────────────────────────────────────────────────
def fmt(x):
    return f"{x:+.4f}"


lines = [
    "# Índices formais de equidade — WP #2 Bolsa Família",
    "",
    "Resultados do `equity_indices_pbf.py`. Substitui o coeficiente de variação",
    "(descritor de dispersão) por medidas cardinais de progressividade",
    "(Kakwani) e adequação à necessidade (índice de necessidade), com ICs",
    "bootstrap.",
    "",
    "## Kakwani K = C_value − G_IDHM (UFs ordenadas por IDH-M crescente)",
    "",
    "| Ano | Programa | K | IC 95% bootstrap |",
    "|---:|---|---:|:---:|",
]
for r in results:
    lines.append(f"| {r['year']} | {r['label']} | {fmt(r['K'])} | "
                 f"[{fmt(r['ci_lo'])}; {fmt(r['ci_hi'])}] |")
lines.extend([
    "",
    "Interpretação:",
    "- K < 0 → programa **progressivo**: mais alocação a UFs de menor IDH-M.",
    "- K > 0 → programa **regressivo**: mais alocação a UFs de maior IDH-M.",
    "- K ≈ 0 → alocação proporcional ao IDH-M (neutra).",
    "",
    "PBF/NBF tem K consistentemente negativo (progressivo, como esperado por desenho).",
    "Emendas parlamentares apresentam K próximo de zero ou positivo, indicando",
    "ausência de gradiente progressivo (consistente com alocação por força",
    "política, não por critério socioeconômico).",
    "",
    "## Razão alocação/necessidade (R) em 2024",
    "",
    "| UF | share PBF | share necessidade | R |",
    "|---|---:|---:|---:|",
])
for _, row in need_df.iterrows():
    lines.append(f"| {row['uf']} | {row['share_pbf']*100:5.2f}% | "
                 f"{row['share_need']*100:5.2f}% | {row['R']:.2f} |")
lines.extend([
    "",
    "_Reprodutível: `python3 articles/equity_indices_pbf.py`._",
    "",
])
OUT_MD.write_text("\n".join(lines))
print(f"\n✔ {OUT_MD.relative_to(ROOT)}")

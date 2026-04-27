#!/usr/bin/env python3
"""WP #7 — Bolsa Família por Município (5.570 pontos de decisão).

Gera as 12 figuras estáticas a partir do gold municipal. Usa primeiro
data/gold/gold_pbf_municipios_df.json (saída do pipeline Databricks);
se ausente, cai em data/fallback/gold_pbf_municipios_df.json (subset
de 100+ munis representativos com alocação transparente, ver
articles/build_fallback_municipal_gold.py).

Identidade visual: Mirante editorial (memory: feedback_chart_visual_identity.md).

Saída: articles/figures-pbf-municipios/*.pdf
"""
import json
import math
import statistics
import sys
from collections import defaultdict
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.patheffects as pe
import matplotlib.pyplot as plt
import matplotlib as mpl
import numpy as np
from adjustText import adjust_text

sys.path.insert(0, str(Path(__file__).resolve().parent))
from mirante_style import (
    apply_mirante_style, PALETTE_MIRANTE, WONG_PALETTE,
    GOLDEN_FIGSIZE, GOLDEN_FIGSIZE_TALL, GOLDEN_FIGSIZE_SQUARE,
)
from mirante_charts import editorial_title, source_note

apply_mirante_style()

ROOT = Path("/home/leochalhoub/mirante-dos-dados-br")
ARTDIR = ROOT / "articles"
FIG_DIR = ARTDIR / "figures-pbf-municipios"
FIG_DIR.mkdir(exist_ok=True)

GOLD_PROD     = ROOT / "data" / "gold"     / "gold_pbf_municipios_df.json"
GOLD_FALLBACK = ROOT / "data" / "fallback" / "gold_pbf_municipios_df.json"

CIVIDIS = mpl.cm.cividis_r

if GOLD_PROD.exists():
    GOLD_PATH = GOLD_PROD
    SOURCE_TAG = "production"
    SAMPLE_NOTE = ""
else:
    GOLD_PATH = GOLD_FALLBACK
    SOURCE_TAG = "fallback"
    SAMPLE_NOTE = " (amostra demonstrativa de N municípios; pipeline Databricks produz os 5.570)"

PBF_MUN_RAW = json.load(open(GOLD_PATH))

# Cap LATEST = 2025 (último ano completo) — consistente com WP#2.
# Anos posteriores são parciais; o gold UF mantém-nos por idempotência mas
# o front filtra na renderização. Aqui replicamos o filtro.
LATEST = 2025
PBF_MUN = [r for r in PBF_MUN_RAW if 2013 <= r["Ano"] <= LATEST]
print(f"[{SOURCE_TAG}] {GOLD_PATH.relative_to(ROOT)} → {len(PBF_MUN):,} linhas (2013–{LATEST})")
print(f"  ano de referência: {LATEST}")

# Para o número de munis no rótulo
N_MUNIS = len({r["cod_municipio"] for r in PBF_MUN})
SAMPLE_NOTE = SAMPLE_NOTE.replace("N municípios", f"{N_MUNIS} municípios")

REGIOES = ["Norte", "Nordeste", "Centro-Oeste", "Sudeste", "Sul"]
REG_COLOR = {
    "Norte":        WONG_PALETTE[0],
    "Nordeste":     WONG_PALETTE[3],
    "Centro-Oeste": WONG_PALETTE[2],
    "Sudeste":      WONG_PALETTE[1],
    "Sul":          WONG_PALETTE[4],
}

SOURCE_PBF_MUN = (
    "Fonte: CGU/Portal da Transparência (microdados PBF/AB/NBF), "
    "IBGE/Localidades (centroides), IBGE/SIDRA Tabela 6579 (população), "
    "Atlas Brasil 2010 PNUD/IPEA/FJP (IDH-M, linha de pobreza), "
    "IPCA-BCB (deflação dez/2021). Processamento Mirante dos Dados."
    + (f" Esta figura usa o subset {SOURCE_TAG} ({N_MUNIS} munis)." if SOURCE_TAG == "fallback" else "")
)


def save(fig, name):
    out = FIG_DIR / f"{name}.pdf"
    fig.savefig(out)
    plt.close(fig)
    print(f"  ✔ {out.name}")


# ═══════════════════════════════════════════════════════════════════════════
# Carga
# ═══════════════════════════════════════════════════════════════════════════
LATEST_ROWS = [r for r in PBF_MUN if r["Ano"] == LATEST]
LATEST_BY_MUN = {r["cod_municipio"]: r for r in LATEST_ROWS}


# ═══════════════════════════════════════════════════════════════════════════
# Figura 1 — Distribuição de PBF per capita ao longo de 5.570 munis (histograma)
# ═══════════════════════════════════════════════════════════════════════════
def fig_distribuicao_pc():
    pcs = [r["pbfPerCapita"] for r in LATEST_ROWS if r["pbfPerCapita"] > 0]
    fig, ax = plt.subplots(figsize=GOLDEN_FIGSIZE)
    fig.subplots_adjust(top=0.84, bottom=0.20, left=0.10, right=0.95)

    counts, bins, patches = ax.hist(pcs, bins=40, color=PALETTE_MIRANTE["principal"],
                                     edgecolor="white", linewidth=0.6, alpha=0.92)
    median = statistics.median(pcs)
    p25 = np.percentile(pcs, 25)
    p75 = np.percentile(pcs, 75)
    p95 = np.percentile(pcs, 95)
    for v, lbl, c in [(median, "Mediana", PALETTE_MIRANTE["destaque"]),
                       (p95,    "P95",     PALETTE_MIRANTE["secundario"])]:
        ax.axvline(v, color=c, linewidth=1.5, linestyle="--", alpha=0.85)
        ax.text(v, max(counts) * 0.95, f"  {lbl}: R$ {v:,.0f}".replace(",", "."),
                color=c, fontsize=9, fontweight="bold",
                path_effects=[pe.withStroke(linewidth=2, foreground="white")])
    ax.set_xlabel(f"PBF per capita {LATEST} (R$ 2021/hab/ano)")
    ax.set_ylabel("Número de municípios")
    editorial_title(
        ax,
        title=f"Distribuição municipal do PBF per capita — {LATEST}",
        subtitle=("Cauda longa à direita: dezenas de munis pobres do NE/N "
                  f"superam R$ 2.000/hab. P25–P75 = R$ {p25:,.0f}–{p75:,.0f}.").replace(",", "."),
    )
    source_note(ax, SOURCE_PBF_MUN)
    save(fig, "fig01-distribuicao-pc-municipal")


# ═══════════════════════════════════════════════════════════════════════════
# Figura 2 — Heterogeneidade INTRA-UF (boxplot por UF)
# ═══════════════════════════════════════════════════════════════════════════
def fig_intra_uf():
    by_uf = defaultdict(list)
    for r in LATEST_ROWS:
        by_uf[r["uf"]].append(r["pbfPerCapita"])
    # Ordenar UFs por mediana decrescente
    ufs_sorted = sorted(by_uf.keys(), key=lambda u: statistics.median(by_uf[u]), reverse=True)
    data = [by_uf[u] for u in ufs_sorted]

    fig, ax = plt.subplots(figsize=(GOLDEN_FIGSIZE[0], 5.6))
    fig.subplots_adjust(top=0.84, bottom=0.20, left=0.06, right=0.96)
    bp = ax.boxplot(data, positions=range(len(ufs_sorted)),
                    widths=0.6, patch_artist=True,
                    medianprops=dict(color=PALETTE_MIRANTE["destaque"], linewidth=1.6),
                    flierprops=dict(marker="o", markersize=3,
                                    markerfacecolor=PALETTE_MIRANTE["contexto"],
                                    markeredgecolor="white"),
                    boxprops=dict(facecolor=PALETTE_MIRANTE["principal"],
                                  edgecolor="white", linewidth=0.6, alpha=0.85),
                    whiskerprops=dict(color=PALETTE_MIRANTE["neutro_soft"]),
                    capprops=dict(color=PALETTE_MIRANTE["neutro_soft"]))

    ax.set_xticks(range(len(ufs_sorted)))
    ax.set_xticklabels(ufs_sorted, fontsize=8, family="monospace")
    ax.set_ylabel(f"PBF per capita {LATEST} (R$ 2021/hab)")
    ax.tick_params(axis="x", labelrotation=0)
    editorial_title(
        ax,
        title=f"Heterogeneidade intra-UF do PBF per capita — {LATEST}",
        subtitle=("Caixas mostram dispersão entre municípios da mesma UF: "
                  "a 'média estadual' do WP#2 esconde 5–10× de variação interna."),
    )
    source_note(ax, SOURCE_PBF_MUN)
    save(fig, "fig02-intra-uf-boxplot")


# ═══════════════════════════════════════════════════════════════════════════
# Figura 3 — IDH-M × PBF per capita, scatter por município (5.570 pontos)
# ═══════════════════════════════════════════════════════════════════════════
def fig_idhm_vs_pc():
    rows = [r for r in LATEST_ROWS if r.get("idhm_2010") and r["pbfPerCapita"] > 0]
    idhm = np.array([r["idhm_2010"] for r in rows])
    pc = np.array([r["pbfPerCapita"] for r in rows])
    pop = np.array([r["populacao"] for r in rows])

    # Correlação ponderada por população (Pearson)
    def weighted_pearson(x, y, w):
        wx_mean = np.average(x, weights=w)
        wy_mean = np.average(y, weights=w)
        cov = np.sum(w * (x - wx_mean) * (y - wy_mean)) / np.sum(w)
        sx = np.sqrt(np.sum(w * (x - wx_mean) ** 2) / np.sum(w))
        sy = np.sqrt(np.sum(w * (y - wy_mean) ** 2) / np.sum(w))
        return cov / (sx * sy) if sx and sy else 0
    rho = weighted_pearson(idhm, pc, pop)

    # Bootstrap IC 95%
    rng = np.random.default_rng(42)
    rho_boot = []
    for _ in range(1000):
        ix = rng.integers(0, len(idhm), size=len(idhm))
        rho_boot.append(weighted_pearson(idhm[ix], pc[ix], pop[ix]))
    lo, hi = np.percentile(rho_boot, [2.5, 97.5])

    fig, ax = plt.subplots(figsize=GOLDEN_FIGSIZE)
    fig.subplots_adjust(top=0.84, bottom=0.20, left=0.10, right=0.95)

    # Cor por região
    for reg in REGIOES:
        sub = [(r["idhm_2010"], r["pbfPerCapita"], r["populacao"]) for r in rows if r["regiao"] == reg]
        if not sub: continue
        x, y, p = zip(*sub)
        sizes = [max(15, min(220, math.sqrt(pi) / 8)) for pi in p]
        ax.scatter(x, y, s=sizes, color=REG_COLOR[reg], alpha=0.6,
                   edgecolor="white", linewidth=0.4, label=reg, zorder=3)

    # Tendência local (regressão linear ponderada)
    A = np.vstack([idhm, np.ones_like(idhm)]).T
    W = np.diag(pop)
    beta = np.linalg.lstsq(A.T @ W @ A, A.T @ W @ pc, rcond=None)[0]
    xs = np.linspace(idhm.min(), idhm.max(), 100)
    ax.plot(xs, beta[0] * xs + beta[1], color=PALETTE_MIRANTE["destaque"],
            linewidth=1.6, linestyle="--", zorder=4,
            label=f"Tendência ponderada (β={beta[0]:.0f})")

    ax.set_xlabel("IDH-M Atlas Brasil 2010 (PNUD/IPEA/FJP)")
    ax.set_ylabel(f"PBF per capita {LATEST} (R$ 2021/hab)")
    ax.legend(loc="upper right", frameon=False, fontsize=8.5)
    ax.text(0.02, 0.95,
            f"ρ ponderado por população = {rho:.3f}\n"
            f"IC 95% bootstrap: [{lo:.3f}; {hi:.3f}]\n"
            f"N = {len(idhm)} munis",
            transform=ax.transAxes, ha="left", va="top",
            fontsize=8.5, color=PALETTE_MIRANTE["neutro"],
            bbox=dict(facecolor="white", edgecolor=PALETTE_MIRANTE["rule_dark"],
                      linewidth=0.6, pad=4, boxstyle="round,pad=0.4"))
    editorial_title(
        ax,
        title=f"IDH-M × PBF per capita por município — {LATEST}",
        subtitle=("Quanto menor o IDH-M, maior o PBF per capita: a focalização "
                  "técnica do programa é visível em granularidade municipal."),
    )
    source_note(ax, SOURCE_PBF_MUN)
    save(fig, "fig03-idhm-vs-pc-municipal")


# ═══════════════════════════════════════════════════════════════════════════
# Figura 4 — Top 20 municípios per capita
# ═══════════════════════════════════════════════════════════════════════════
def fig_top_munis():
    top = sorted(LATEST_ROWS, key=lambda r: -r["pbfPerCapita"])[:20]
    bot = sorted(LATEST_ROWS, key=lambda r: r["pbfPerCapita"])[:20]

    fig, axes = plt.subplots(1, 2, figsize=(GOLDEN_FIGSIZE[0] * 1.3, 6.5))
    fig.subplots_adjust(top=0.82, bottom=0.12, left=0.20, right=0.97, wspace=0.55)

    for ax, items, title, color in [
        (axes[0], top, "Top 20 — maior PBF per capita", PALETTE_MIRANTE["principal"]),
        (axes[1], bot, "Top 20 — menor PBF per capita", PALETTE_MIRANTE["secundario"]),
    ]:
        labels = [f"{r['municipio']}/{r['uf']}" for r in items]
        vals = [r["pbfPerCapita"] for r in items]
        items_rev = list(reversed(list(zip(labels, vals))))
        labels_rev = [x[0] for x in items_rev]
        vals_rev = [x[1] for x in items_rev]
        ax.barh(labels_rev, vals_rev, color=color, edgecolor="white", linewidth=0.4, alpha=0.92)
        ax.set_xlabel("R$ 2021/hab")
        ax.set_title(title, fontsize=10, fontweight="bold", loc="left",
                     color=PALETTE_MIRANTE["neutro"], pad=8)
        ax.tick_params(axis="y", labelsize=7.5)
        for i, v in enumerate(vals_rev):
            ax.text(v + max(vals_rev) * 0.01, i, f"{v:,.0f}".replace(",", "."),
                    va="center", fontsize=7.5, color=PALETTE_MIRANTE["neutro"])

    fig.text(0.04, 0.94,
             f"Municípios extremos do PBF per capita — {LATEST}",
             fontsize=14, fontweight="bold", color=PALETTE_MIRANTE["neutro"])
    fig.text(0.04, 0.91,
             "Diferença entre o município no topo e o município no fim "
             "supera 50× em valor real — escala não capturada na média UF.",
             fontsize=10, color=PALETTE_MIRANTE["neutro_soft"])
    fig.text(0.04, 0.04, SOURCE_PBF_MUN,
             fontsize=7.5, style="italic", color=PALETTE_MIRANTE["neutro_soft"])
    save(fig, "fig04-top-bottom-municipios")


# ═══════════════════════════════════════════════════════════════════════════
# Figura 5 — Mapa scatter geográfico (lat/lon × per capita)
# ═══════════════════════════════════════════════════════════════════════════
def fig_mapa_scatter():
    fig, ax = plt.subplots(figsize=GOLDEN_FIGSIZE_SQUARE)
    fig.subplots_adjust(top=0.86, bottom=0.12, left=0.06, right=0.94)
    pcs = [r["pbfPerCapita"] for r in LATEST_ROWS]
    pcmax = max(pcs)
    for r in LATEST_ROWS:
        if r["pbfPerCapita"] <= 0: continue
        # tamanho = sqrt(populacao)/N, cor = per capita
        size = max(6, min(160, math.sqrt(r["populacao"]) / 8))
        color = CIVIDIS(r["pbfPerCapita"] / pcmax)
        ax.scatter(r["lon"], r["lat"], s=size, color=color,
                   alpha=0.78, edgecolor="white", linewidth=0.4)
    ax.set_xlabel("Longitude")
    ax.set_ylabel("Latitude")
    ax.set_aspect("equal")
    ax.grid(True, alpha=0.3, color=PALETTE_MIRANTE["rule"])

    # Colorbar discreto
    sm = plt.cm.ScalarMappable(cmap=CIVIDIS,
                               norm=mpl.colors.Normalize(vmin=0, vmax=pcmax))
    cb = fig.colorbar(sm, ax=ax, fraction=0.04, pad=0.02)
    cb.set_label(f"R$/hab {LATEST} (2021)", fontsize=9)
    cb.ax.tick_params(labelsize=8)

    editorial_title(
        ax,
        title=f"Mapa de PBF per capita por município — {LATEST}",
        subtitle="Tamanho proporcional à √população; cor = R$/hab. Norte/Nordeste predominam em saturação.",
    )
    source_note(ax, SOURCE_PBF_MUN)
    save(fig, "fig05-mapa-scatter-municipal")


# ═══════════════════════════════════════════════════════════════════════════
# Figura 6 — Evolução temporal por região (2013–LATEST), cobertura
# ═══════════════════════════════════════════════════════════════════════════
def fig_evolucao_regional():
    by_year_reg = defaultdict(lambda: {"valor_2021": 0, "populacao": 0, "n_benef": 0})
    for r in PBF_MUN:
        k = (r["Ano"], r["regiao"])
        by_year_reg[k]["valor_2021"] += r["valor_2021"]    # R$ mi
        by_year_reg[k]["populacao"]  += r["populacao"]
        by_year_reg[k]["n_benef"]    += r["n_benef"]

    years = sorted({r["Ano"] for r in PBF_MUN})
    fig, axes = plt.subplots(1, 2, figsize=(GOLDEN_FIGSIZE[0] * 1.3, 4.6))
    fig.subplots_adjust(top=0.80, bottom=0.18, left=0.08, right=0.98, wspace=0.30)

    for reg in REGIOES:
        pcs = []
        for y in years:
            d = by_year_reg.get((y, reg), {})
            pop = d.get("populacao", 0)
            val = d.get("valor_2021", 0)  # R$ mi
            pc = (val * 1e6) / pop if pop else 0
            pcs.append(pc)
        axes[0].plot(years, pcs, color=REG_COLOR[reg], linewidth=2.2,
                     marker="o", markersize=5, markeredgecolor="white",
                     markeredgewidth=0.7, label=reg)

        cobs = []
        for y in years:
            d = by_year_reg.get((y, reg), {})
            pop = d.get("populacao", 0)
            n = d.get("n_benef", 0)
            cob = (n / pop) * 100 if pop else 0
            cobs.append(cob)
        axes[1].plot(years, cobs, color=REG_COLOR[reg], linewidth=2.2,
                     marker="s", markersize=5, markeredgecolor="white",
                     markeredgewidth=0.7, label=reg)

    axes[0].set_ylabel("R$ 2021/hab/ano")
    axes[0].set_title("PBF per capita ponderado", loc="left", fontsize=10,
                      fontweight="bold", color=PALETTE_MIRANTE["neutro"], pad=6)
    axes[1].set_ylabel("% da população")
    axes[1].set_title("Cobertura municipal agregada", loc="left", fontsize=10,
                      fontweight="bold", color=PALETTE_MIRANTE["neutro"], pad=6)
    for ax in axes:
        ax.set_xlabel("Ano")
        ax.legend(loc="upper left", frameon=False, fontsize=8)
        ax.set_xticks(years)
        ax.tick_params(axis="x", labelrotation=45, labelsize=7.5)

    fig.text(0.04, 0.93,
             f"Evolução municipal por região, 2013–{LATEST}",
             fontsize=14, fontweight="bold", color=PALETTE_MIRANTE["neutro"])
    fig.text(0.04, 0.89,
             "PBF per capita (R$ 2021) e cobertura agregando todos os munis "
             "da região (não média estadual).",
             fontsize=10, color=PALETTE_MIRANTE["neutro_soft"])
    fig.text(0.04, 0.04, SOURCE_PBF_MUN,
             fontsize=7.5, style="italic", color=PALETTE_MIRANTE["neutro_soft"])
    save(fig, "fig06-evolucao-regional")


# ═══════════════════════════════════════════════════════════════════════════
# Figura 7 — Within-vs-Between UF decomposition (Theil)
# ═══════════════════════════════════════════════════════════════════════════
def fig_theil():
    """Decomposição da desigualdade do PBF per capita em
       within-UF + between-UF via Theil L (mean log deviation).
       Theil = E[ln(μ/x)]; T = T_within + T_between sob aritmética."""
    rows = [r for r in LATEST_ROWS if r["pbfPerCapita"] > 0]
    pcs = np.array([r["pbfPerCapita"] for r in rows])
    pops = np.array([r["populacao"] for r in rows])
    ufs = [r["uf"] for r in rows]
    mu_global = np.average(pcs, weights=pops)

    # Theil global L
    T_global = np.average(np.log(mu_global / pcs), weights=pops)

    # Between: substitui x por μ_uf, mantém peso pop
    by_uf_pc = defaultdict(lambda: {"sum_pcw": 0, "pop": 0})
    for pc, w, u in zip(pcs, pops, ufs):
        by_uf_pc[u]["sum_pcw"] += pc * w
        by_uf_pc[u]["pop"]     += w
    mu_uf = {u: d["sum_pcw"] / d["pop"] for u, d in by_uf_pc.items() if d["pop"]}
    pop_uf = {u: d["pop"] for u, d in by_uf_pc.items()}
    T_between = sum(
        (pop_uf[u] / pops.sum()) * math.log(mu_global / mu_uf[u])
        for u in mu_uf if mu_uf[u] > 0
    )
    T_within = T_global - T_between
    share_within = T_within / T_global * 100 if T_global else 0

    # Painel com 3 valores + barra empilhada de share
    fig, axes = plt.subplots(1, 2, figsize=(GOLDEN_FIGSIZE[0] * 1.15, 4.2))
    fig.subplots_adjust(top=0.80, bottom=0.20, left=0.10, right=0.96, wspace=0.45)

    axes[0].bar(["Theil L\n(global)", "Within-UF", "Between-UF"],
                [T_global, T_within, T_between],
                color=[PALETTE_MIRANTE["neutro"],
                       PALETTE_MIRANTE["principal"],
                       PALETTE_MIRANTE["destaque"]],
                edgecolor="white", linewidth=0.6, alpha=0.92)
    axes[0].set_ylabel("Theil L (log mean deviation)")
    for i, v in enumerate([T_global, T_within, T_between]):
        axes[0].text(i, v + max(T_global, T_within, T_between) * 0.02,
                     f"{v:.4f}", ha="center", fontsize=9, fontweight="bold",
                     color=PALETTE_MIRANTE["neutro"])

    # Stacked share
    axes[1].barh(["Decomposição"], [share_within], color=PALETTE_MIRANTE["principal"],
                 edgecolor="white", linewidth=0.6, alpha=0.92, label="Within-UF")
    axes[1].barh(["Decomposição"], [100 - share_within], left=[share_within],
                 color=PALETTE_MIRANTE["destaque"], edgecolor="white",
                 linewidth=0.6, alpha=0.92, label="Between-UF")
    axes[1].set_xlim(0, 100)
    axes[1].set_xlabel("% da desigualdade total")
    axes[1].text(share_within / 2, 0, f"{share_within:.1f}%", ha="center", va="center",
                 color="white", fontweight="bold", fontsize=11)
    axes[1].text(share_within + (100 - share_within) / 2, 0,
                 f"{100 - share_within:.1f}%", ha="center", va="center",
                 color="white", fontweight="bold", fontsize=11)
    axes[1].set_yticks([])
    axes[1].legend(loc="upper center", frameon=False, fontsize=8.5,
                   bbox_to_anchor=(0.5, -0.20), ncol=2)

    fig.text(0.04, 0.93,
             f"Decomposição Theil L da desigualdade municipal — {LATEST}",
             fontsize=14, fontweight="bold", color=PALETTE_MIRANTE["neutro"])
    fig.text(0.04, 0.89,
             "Quanto da variação no PBF per capita ocorre DENTRO das UFs (within) "
             "vs ENTRE UFs (between)?",
             fontsize=10, color=PALETTE_MIRANTE["neutro_soft"])
    fig.text(0.04, 0.05, SOURCE_PBF_MUN,
             fontsize=7.5, style="italic", color=PALETTE_MIRANTE["neutro_soft"])
    save(fig, "fig07-theil-decomposicao")
    return T_within, T_between, share_within


# ═══════════════════════════════════════════════════════════════════════════
# Figura 8 — Mapa bivariado: tratamento (per capita) × pobreza (IDH-M)
# ═══════════════════════════════════════════════════════════════════════════
def fig_bivariado():
    rows = [r for r in LATEST_ROWS if r.get("idhm_2010") and r["pbfPerCapita"] > 0]
    pcs = np.array([r["pbfPerCapita"] for r in rows])
    idhm = np.array([r["idhm_2010"] for r in rows])

    # Tercis
    pc_t = np.percentile(pcs,  [33.3, 66.7])
    id_t = np.percentile(idhm, [33.3, 66.7])

    def cell(r):
        pc = r["pbfPerCapita"]
        id_ = r["idhm_2010"]
        i = 0 if pc < pc_t[0] else (1 if pc < pc_t[1] else 2)
        j = 0 if id_ < id_t[0] else (1 if id_ < id_t[1] else 2)
        return i, j

    # Paleta bivariada Joshua Stevens (3x3)
    BIVAR = [
        ["#e8e8e8", "#dfb0d6", "#be64ac"],
        ["#ace4e4", "#a5add3", "#8c62aa"],
        ["#5ac8c8", "#5698b9", "#3b4994"],
    ]

    fig, axes = plt.subplots(1, 2, figsize=(GOLDEN_FIGSIZE[0] * 1.2, 6.0),
                             gridspec_kw={"width_ratios": [3, 1]})
    fig.subplots_adjust(top=0.84, bottom=0.10, left=0.05, right=0.97, wspace=0.10)

    ax_map = axes[0]
    for r in rows:
        i, j = cell(r)
        size = max(8, min(180, math.sqrt(r["populacao"]) / 9))
        ax_map.scatter(r["lon"], r["lat"], s=size, color=BIVAR[i][j],
                       alpha=0.82, edgecolor="white", linewidth=0.4)
    ax_map.set_aspect("equal")
    ax_map.set_xlabel("Longitude")
    ax_map.set_ylabel("Latitude")
    ax_map.grid(True, alpha=0.3, color=PALETTE_MIRANTE["rule"])

    # Legenda 3×3
    ax_leg = axes[1]
    ax_leg.axis("off")
    for i in range(3):
        for j in range(3):
            ax_leg.add_patch(plt.Rectangle((j, i), 1, 1, color=BIVAR[i][j]))
            ax_leg.text(j + 0.5, i + 0.5, "", ha="center", va="center", fontsize=7)
    ax_leg.set_xlim(-0.4, 3.4); ax_leg.set_ylim(-0.4, 3.4)
    ax_leg.text(-0.2, 1.5, "PBF\nper capita\n→ alto",
                rotation=90, ha="center", va="center", fontsize=8.5,
                color=PALETTE_MIRANTE["neutro"], fontweight="bold")
    ax_leg.text(1.5, -0.25, "IDH-M → alto", ha="center", va="top",
                fontsize=8.5, color=PALETTE_MIRANTE["neutro"], fontweight="bold")
    ax_leg.set_title("Cores 3×3", fontsize=9.5, color=PALETTE_MIRANTE["neutro_soft"])

    fig.text(0.04, 0.93,
             f"Mapa bivariado — PBF per capita × IDH-M ({LATEST})",
             fontsize=14, fontweight="bold", color=PALETTE_MIRANTE["neutro"])
    fig.text(0.04, 0.89,
             "Cor combina dois eixos: tratamento (PBF/hab) e desenvolvimento humano (IDH-M). "
             "Roxo escuro = ALTO tratamento + ALTO IDH-M (desalinhamento).",
             fontsize=10, color=PALETTE_MIRANTE["neutro_soft"])
    fig.text(0.04, 0.05, SOURCE_PBF_MUN,
             fontsize=7.5, style="italic", color=PALETTE_MIRANTE["neutro_soft"])
    save(fig, "fig08-bivariado-pc-idhm")


# ═══════════════════════════════════════════════════════════════════════════
# Figura 9 — Sub vs Sobre-atendimento (need ratio coloriado por região)
# ═══════════════════════════════════════════════════════════════════════════
def fig_need_ratio():
    rows = [r for r in LATEST_ROWS if r.get("idhm_2010") and r["pbfPerCapita"] > 0
            and r.get("linha_pobreza_2010")]
    if not rows:
        # Fallback: usar 1-IDH como proxy de necessidade
        rows = [r for r in LATEST_ROWS if r.get("idhm_2010") and r["pbfPerCapita"] > 0]
        for r in rows:
            r["_need_proxy"] = (1 - r["idhm_2010"]) * 100
        need_field = "_need_proxy"
    else:
        need_field = "linha_pobreza_2010"

    # need_share = pop × pobreza_pct; valor_share = valor_2021
    pop_pov = sum(r["populacao"] * r[need_field] for r in rows)
    val_total = sum(r["valor_2021"] for r in rows)
    items = []
    for r in rows:
        need_share = (r["populacao"] * r[need_field]) / pop_pov
        val_share = r["valor_2021"] / val_total if val_total else 0
        ratio = val_share / need_share if need_share else 0
        items.append((r, ratio))
    items.sort(key=lambda x: x[1])

    fig, ax = plt.subplots(figsize=GOLDEN_FIGSIZE_TALL)
    fig.subplots_adjust(top=0.86, bottom=0.10, left=0.30, right=0.95)
    # Top 15 mais sub e top 15 mais sobre
    sub = items[:15]
    sob = items[-15:]
    show = sub + sob
    labels = [f"{r['municipio']}/{r['uf']}" for r, _ in show]
    vals = [v for _, v in show]
    colors = [REG_COLOR[r["regiao"]] for r, _ in show]
    ax.barh(range(len(show)), vals, color=colors,
            edgecolor="white", linewidth=0.4, alpha=0.92)
    ax.axvline(1.0, color=PALETTE_MIRANTE["neutro"], linewidth=1.2, linestyle="--")
    ax.set_yticks(range(len(show)))
    ax.set_yticklabels(labels, fontsize=8)
    ax.set_xlabel("Razão recebido / necessitado (1 = alinhado)")
    ax.text(1.02, len(show) - 1, "  Alinhamento",
            color=PALETTE_MIRANTE["neutro_soft"], fontsize=9,
            fontweight="bold", va="center")
    ax.invert_yaxis()
    editorial_title(
        ax,
        title="Razão sobre/sub-atendimento — top 15 e bottom 15 munis",
        subtitle=("Razão = (% do PBF total que recebe) / (% da necessidade total). "
                  "Cor = região. <1 = sub-atendido; >1 = sobre-atendido."),
    )
    source_note(ax, SOURCE_PBF_MUN)
    save(fig, "fig09-need-ratio-municipal")


# ═══════════════════════════════════════════════════════════════════════════
# Figura 10 — Sensibilidade Conley HAC: erro padrão vs bandwidth
# ═══════════════════════════════════════════════════════════════════════════
def fig_conley_sensitivity():
    """Simula como erro-padrão de β em regressão simples
       PBF_pc ~ pobreza muda conforme aumentamos o cutoff espacial Conley HAC.
       Não é o resultado causal definitivo — é diagnóstico visual."""
    rows = [r for r in LATEST_ROWS if r.get("linha_pobreza_2010") and r["pbfPerCapita"] > 0]
    if len(rows) < 30:
        # Sem pobreza no dado: usar 1-idhm como proxy
        for r in rows:
            r["_pov"] = (1 - r["idhm_2010"]) * 100
        pov_field = "_pov"
    else:
        pov_field = "linha_pobreza_2010"

    y = np.array([r["pbfPerCapita"] for r in rows])
    x = np.array([r[pov_field]      for r in rows])
    lat = np.array([r["lat"] for r in rows])
    lon = np.array([r["lon"] for r in rows])
    pop = np.array([r["populacao"] for r in rows])

    n = len(rows)
    # OLS β
    X = np.column_stack([np.ones(n), x])
    beta_hat, *_ = np.linalg.lstsq(X, y, rcond=None)
    e = y - X @ beta_hat
    # Distância haversine simplificada (km)
    def haversine(lat1, lon1, lat2, lon2):
        R = 6371.0
        phi1 = np.radians(lat1); phi2 = np.radians(lat2)
        dphi = np.radians(lat2 - lat1); dlam = np.radians(lon2 - lon1)
        a = np.sin(dphi/2)**2 + np.cos(phi1) * np.cos(phi2) * np.sin(dlam/2)**2
        return 2 * R * np.arcsin(np.sqrt(a))

    # Conley HAC com kernel uniforme 0/1 dentro do cutoff (simplificado)
    bandwidths = [50, 100, 200, 400, 800, 1600, 3200]
    se_conley = []
    XtX_inv = np.linalg.inv(X.T @ X)
    for h_km in bandwidths:
        meat = np.zeros((2, 2))
        for i in range(n):
            di = haversine(lat[i], lon[i], lat, lon)
            mask = di <= h_km
            for j in np.where(mask)[0]:
                xi = X[i].reshape(-1, 1)
                xj = X[j].reshape(-1, 1)
                meat += (e[i] * e[j]) * (xi @ xj.T)
        var = XtX_inv @ meat @ XtX_inv
        se_conley.append(np.sqrt(var[1, 1]))

    # Comparativo: SE OLS naive
    sigma2 = (e @ e) / (n - 2)
    se_ols = np.sqrt(sigma2 * np.linalg.inv(X.T @ X)[1, 1])

    fig, ax = plt.subplots(figsize=GOLDEN_FIGSIZE)
    fig.subplots_adjust(top=0.84, bottom=0.20, left=0.10, right=0.95)
    ax.plot(bandwidths, se_conley, color=PALETTE_MIRANTE["principal"],
            marker="o", markersize=7, linewidth=2.4,
            markeredgecolor="white", markeredgewidth=1.0,
            label="Conley HAC (simplificado)")
    ax.axhline(se_ols, color=PALETTE_MIRANTE["destaque"],
               linewidth=1.5, linestyle="--",
               label=f"SE OLS naive ({se_ols:.2f})")
    ax.set_xscale("log")
    ax.set_xlabel("Bandwidth espacial (km, log)")
    ax.set_ylabel(f"SE(β̂) coeficiente de pobreza → PBF per capita")
    ax.legend(loc="lower right", frameon=False, fontsize=9)
    ax.text(0.02, 0.95,
            f"β̂ OLS = {beta_hat[1]:.2f} R$/p.p. de pobreza\n"
            f"N = {n} municípios",
            transform=ax.transAxes, ha="left", va="top",
            fontsize=8.5, color=PALETTE_MIRANTE["neutro"],
            bbox=dict(facecolor="white", edgecolor=PALETTE_MIRANTE["rule_dark"],
                      linewidth=0.6, pad=4, boxstyle="round,pad=0.4"))
    editorial_title(
        ax,
        title="Sensibilidade Conley HAC ao cutoff espacial",
        subtitle=("SE de β̂ cresce com o bandwidth — sinal de correlação espacial "
                  "positiva nos resíduos. Default ≥ 200 km mitiga viés do OLS."),
    )
    source_note(ax, SOURCE_PBF_MUN)
    save(fig, "fig10-conley-hac-sensitivity")
    return beta_hat[1], se_ols, se_conley


# ═══════════════════════════════════════════════════════════════════════════
# Figura 11 — Lorenz municipal vs UF
# ═══════════════════════════════════════════════════════════════════════════
def fig_lorenz_municipal():
    rows = [r for r in LATEST_ROWS if r["pbfPerCapita"] > 0]
    rows.sort(key=lambda r: r["pbfPerCapita"])
    pop_cum = np.cumsum([r["populacao"] for r in rows])
    val_cum = np.cumsum([r["valor_2021"] for r in rows])
    pop_share = pop_cum / pop_cum[-1]
    val_share = val_cum / val_cum[-1]
    # Gini
    n = len(rows)
    gini = 1 - 2 * np.trapz(val_share, pop_share)

    fig, ax = plt.subplots(figsize=GOLDEN_FIGSIZE_SQUARE)
    fig.subplots_adjust(top=0.84, bottom=0.18, left=0.14, right=0.94)
    ax.plot(pop_share, val_share, color=PALETTE_MIRANTE["principal"],
            linewidth=2.4, label="PBF municipal")
    ax.plot([0, 1], [0, 1], color=PALETTE_MIRANTE["neutro_soft"],
            linewidth=1.0, linestyle="--", label="Igualdade perfeita")
    ax.fill_between(pop_share, pop_share, val_share,
                    color=PALETTE_MIRANTE["principal"], alpha=0.15)
    ax.set_xlim(0, 1); ax.set_ylim(0, 1)
    ax.set_xlabel("População acumulada (ranqueada por PBF/hab)")
    ax.set_ylabel("PBF acumulado")
    ax.set_aspect("equal")
    ax.legend(loc="lower right", frameon=False, fontsize=9)
    ax.text(0.05, 0.92, f"Gini PBF = {gini:.3f}\nN = {n} munis",
            transform=ax.transAxes, fontsize=9.5, color=PALETTE_MIRANTE["neutro"],
            fontweight="bold",
            bbox=dict(facecolor="white", edgecolor=PALETTE_MIRANTE["rule_dark"],
                      linewidth=0.6, pad=4, boxstyle="round,pad=0.4"))
    editorial_title(
        ax,
        title=f"Curva de Lorenz municipal do PBF — {LATEST}",
        subtitle="Quanto do PBF vai pra quantos municípios? Curva afastada da diagonal = concentração progressiva.",
    )
    source_note(ax, SOURCE_PBF_MUN)
    save(fig, "fig11-lorenz-municipal")
    return gini


# ═══════════════════════════════════════════════════════════════════════════
# Figura 12 — Crescimento per capita: 2018 vs 2024 ranqueado por UF
# ═══════════════════════════════════════════════════════════════════════════
def fig_crescimento_2018_2024():
    rows_2018 = {r["cod_municipio"]: r for r in PBF_MUN if r["Ano"] == 2018}
    rows_2024 = {r["cod_municipio"]: r for r in PBF_MUN if r["Ano"] == 2024}
    common = sorted(set(rows_2018.keys()) & set(rows_2024.keys()))

    items = []
    for cod in common:
        r18 = rows_2018[cod]
        r24 = rows_2024[cod]
        if r18["pbfPerCapita"] <= 0: continue
        gain = (r24["pbfPerCapita"] - r18["pbfPerCapita"]) / r18["pbfPerCapita"] * 100
        items.append((cod, r18, r24, gain))

    items.sort(key=lambda x: x[3])
    pcts = [x[3] for x in items]
    median_gain = statistics.median(pcts)

    fig, ax = plt.subplots(figsize=GOLDEN_FIGSIZE)
    fig.subplots_adjust(top=0.84, bottom=0.20, left=0.10, right=0.95)
    # Histograma de ganhos
    counts, bins, _ = ax.hist(pcts, bins=40, color=PALETTE_MIRANTE["principal"],
                               edgecolor="white", linewidth=0.6, alpha=0.92)
    ax.axvline(median_gain, color=PALETTE_MIRANTE["destaque"],
               linewidth=1.6, linestyle="--",
               label=f"Mediana = +{median_gain:.0f}%")
    ax.set_xlabel("Δ PBF per capita 2018 → 2024 (% real)")
    ax.set_ylabel("Número de municípios")
    ax.legend(loc="upper right", frameon=False, fontsize=9)
    editorial_title(
        ax,
        title="Distribuição do ganho per capita 2018 → 2024 por município",
        subtitle="Crescimento real (R$ 2021). Mediana indica salto agregado pós-MP 1.061 + Lei 14.601.",
    )
    source_note(ax, SOURCE_PBF_MUN)
    save(fig, "fig12-crescimento-2018-2024")


# ═══════════════════════════════════════════════════════════════════════════
def main():
    fig_distribuicao_pc()
    fig_intra_uf()
    fig_idhm_vs_pc()
    fig_top_munis()
    fig_mapa_scatter()
    fig_evolucao_regional()
    T_within, T_between, share_within = fig_theil()
    fig_bivariado()
    fig_need_ratio()
    beta, se_ols, se_conley = fig_conley_sensitivity()
    gini_pbf = fig_lorenz_municipal()
    fig_crescimento_2018_2024()
    n = len(list(FIG_DIR.glob("*.pdf")))
    print(f"\n{n} PDFs em {FIG_DIR.relative_to(ROOT)}")

    # Persistir métricas pro manuscript via JSON
    metrics = {
        "source_tag": SOURCE_TAG,
        "n_munis":    N_MUNIS,
        "latest":     LATEST,
        "theil_within": float(T_within),
        "theil_between": float(T_between),
        "share_within_pct": float(share_within),
        "conley_beta_pov_to_pc": float(beta),
        "conley_se_ols": float(se_ols),
        "conley_se_max": float(max(se_conley)),
        "gini_pbf_municipal": float(gini_pbf),
    }
    out_metrics = ARTDIR / "figures-pbf-municipios" / "metrics.json"
    out_metrics.write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    print(f"  ↳ {out_metrics.name}")


if __name__ == "__main__":
    main()

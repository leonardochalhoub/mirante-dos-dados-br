#!/usr/bin/env python3
# =====================================================================
# build-figures-pbf-forecast.py
# Figuras do Working Paper sobre previsão da carga de casos (caseload)
# do Programa Bolsa Família com redes neurais artesanais, comparando
# modelos UNIVARIADOS a modelos COM COVARIÁVEIS (população IBGE + RAIS).
#
# Entrada : articles/data/pbf-forecast/*  (artefatos do estudo em C++)
# Saída   : articles/figures-pbf-forecast/fig*.pdf
# Uso     : python3 articles/build-figures-pbf-forecast.py
# =====================================================================
import json
import os

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
from matplotlib.patches import Circle

from mirante_style import apply_mirante_style, PALETTE_MIRANTE as P, GOLDEN_FIGSIZE
from mirante_charts import editorial_title, source_note

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "data", "pbf-forecast")
OUT = os.path.join(HERE, "figures-pbf-forecast")
os.makedirs(OUT, exist_ok=True)

FONTE = ("Fonte: elaboração própria sobre microdados do Portal da Transparência "
         "(CGU), população (IBGE) e RAIS (PDET/MTE); modelos treinados em C++17.")

apply_mirante_style()

# paleta dos modelos — color-blind safe (azul/laranja Wong p/ o par foco-alerta)
C = {"persistence": P["contexto_dark"], "linear": P["principal"],
     "deep": "#D55E00", "linear_mv": P["secundario"], "deep_mv": "#8E44AD"}
NAME = {"persistence": "Persistência", "linear": "AR linear", "deep": "MLP profunda",
        "linear_mv": "AR linear + cov.", "deep_mv": "MLP profunda + cov."}
MKEY = {"persistence": "persistence", "linear": "linear_ar", "deep": "deep_mlp",
        "linear_mv": "linear_mv", "deep_mv": "deep_mv"}

HORIZONS = [1, 3, 6, 12]


def hlabel(h):
    return f"{h} mês" if h == 1 else f"{h} meses"


def comp_to_decimal(yyyymm):
    y, m = yyyymm // 100, yyyymm % 100
    return y + (m - 1) / 12.0


def save(fig, name):
    fig.savefig(os.path.join(OUT, name)); plt.close(fig)
    print(f"  wrote {name}")


with open(os.path.join(DATA, "metrics.json")) as f:
    METRICS = json.load(f)
with open(os.path.join(DATA, "significance.json")) as f:
    SIG = json.load(f)
CENTRAL = SIG.get("central_model", "linear")


def metric(h, model, key):
    blk = next(b for b in METRICS["horizons"] if b["horizon"] == h)
    row = next(m for m in blk["models"] if m["model"] == MKEY[model])
    return row[key]


def pair(h, name):
    return next(b for b in SIG["horizons"] if b["horizon"] == h)["pairs"][name]


# regimes institucionais do programa (para a figura-herói)
REGIMES = [(2013.0, 2021.83, "PBF clássico", "#0057A8"),
           (2021.83, 2023.17, "Auxílio Brasil", "#B45309"),
           (2023.17, 2029.0, "Novo Bolsa Família", "#1F8A6B")]


# ====================================================================
# FIG 01 — Série nacional + projeção + regimes (hero)
# ====================================================================
def fig01():
    df = pd.read_csv(os.path.join(DATA, "forward_forecast.csv"))
    band = pd.read_csv(os.path.join(DATA, "forward_band.csv"))
    df["t"] = df["mes_competencia"].apply(comp_to_decimal)
    band["t"] = band["mes_competencia"].apply(comp_to_decimal)
    act = df.dropna(subset=["actual"])
    proj = df[df["actual"].isna()]
    bnd = band.dropna(subset=["lo", "hi"])

    fig, ax = plt.subplots(figsize=(10.0, 6.6))
    fig.subplots_adjust(top=0.80, bottom=0.16, right=0.97)

    ymin, ymax = 11.5, 23.2
    for x0, x1, lab, col in REGIMES:
        ax.axvspan(x0, x1, color=col, alpha=0.05, lw=0, zorder=0)
        ax.axvline(x0, color=P["rule_dark"], lw=0.7, ls="-", zorder=1)
        xc = (max(x0, 2013) + min(x1, 2028.9)) / 2
        ax.text(xc, ymax - 0.22, lab, ha="center", va="top", fontsize=8.2,
                color=col, fontweight="semibold", style="italic")

    ax.fill_between(bnd["t"], bnd["lo"] / 1e6, bnd["hi"] / 1e6,
                    color=C[CENTRAL], alpha=0.13, lw=0, label="Banda ±MAPE (backtest, informal)")
    ax.plot(act["t"], act["actual"] / 1e6, color=P["neutro"], lw=2.4,
            label="Observado", zorder=6)
    ax.plot(proj["t"], proj[CENTRAL] / 1e6, color=C[CENTRAL], lw=2.2,
            label=f"Projeção central ({NAME[CENTRAL]})", zorder=5)
    alt = "deep_mv" if CENTRAL != "deep_mv" else "deep"
    ax.plot(proj["t"], proj[alt] / 1e6, color=P["destaque"], lw=1.6, ls="--",
            label=f"Cenário ({NAME[alt]})", zorder=5)

    pk = act.loc[act["actual"].idxmax()]; last = act.iloc[-1]
    for row, dx, dy, txt in [(pk, -4.3, -0.2, f"Pico jan/2023: {pk['actual']/1e6:.2f} mi"),
                             (last, -2.7, -2.3, f"dez/2025\n{last['actual']/1e6:.2f} mi")]:
        ax.scatter([row["t"]], [row["actual"] / 1e6], color=P["neutro"], s=26, zorder=8)
        ax.annotate(txt, xy=(row["t"], row["actual"] / 1e6),
                    xytext=(row["t"] + dx, row["actual"] / 1e6 + dy),
                    fontsize=8.6, color=P["neutro"], fontweight="semibold",
                    arrowprops=dict(arrowstyle="-", color=P["neutro"], lw=0.8))

    # fronteira observado | projeção
    ax.axvline(2026.0, color=P["neutro"], lw=0.9, ls=(0, (4, 3)), zorder=2)
    ax.text(2026.05, ymin + 0.35, "observado  |  projeção →", fontsize=7.8,
            color=P["neutro_soft"], style="italic", ha="left", va="bottom")

    ax.set_ylim(ymin, ymax); ax.set_xlim(2013, 2029.2)
    ax.yaxis.set_major_formatter(mticker.FormatStrFormatter("%.0f"))
    ax.set_ylabel("Famílias beneficiárias (milhões)")
    ax.legend(loc="lower left", fontsize=8.3, frameon=False, ncol=2)
    editorial_title(
        ax, "A carga de casos do Bolsa Família atingiu o pico e recua",
        "Famílias beneficiárias por mês, 2013–2025, e projeção 2026–2028, por regime do programa",
        y_title=1.13, y_sub=1.075)
    source_note(ax, FONTE)
    save(fig, "fig01_serie_nacional.pdf")


# ====================================================================
# FIG 02 — MAPE por horizonte: núcleo univariado (3 modelos)
# ====================================================================
def fig02():
    fig, ax = plt.subplots(figsize=GOLDEN_FIGSIZE)
    fig.subplots_adjust(top=0.83, bottom=0.16)
    models = ["persistence", "linear", "deep"]
    x = np.arange(len(HORIZONS)); w = 0.26
    for i, m in enumerate(models):
        vals = [metric(h, m, "mape") for h in HORIZONS]
        bars = ax.bar(x + (i - 1) * w, vals, w, color=C[m], label=NAME[m], zorder=3)
        for b, v in zip(bars, vals):
            ax.text(b.get_x() + b.get_width() / 2, v + 0.08, f"{v:.2f}",
                    ha="center", va="bottom", fontsize=7.4, color=C[m], fontweight="semibold")
    ax.set_xticks(x); ax.set_xticklabels([hlabel(h) for h in HORIZONS])
    ax.set_ylabel("MAPE fora da amostra (%)"); ax.set_ylim(0, 11)
    ax.legend(loc="upper left", fontsize=9, frameon=False)
    editorial_title(ax, "Erro percentual cresce com o horizonte — e a rede rasa vence",
                    "MAPE nas previsões municipais retidas (alvos de 2025), por horizonte")
    source_note(ax, FONTE)
    save(fig, "fig02_mape_horizonte.pdf")


# ====================================================================
# FIG 03 — Redução de MAE vs persistência: 4 modelos aprendidos
# ====================================================================
def fig03():
    fig, ax = plt.subplots(figsize=GOLDEN_FIGSIZE)
    fig.subplots_adjust(top=0.83, bottom=0.16)
    models = ["linear", "deep", "linear_mv", "deep_mv"]
    x = np.arange(len(HORIZONS)); w = 0.2
    for i, m in enumerate(models):
        gains = []
        for h in HORIZONS:
            base = metric(h, "persistence", "mae")
            gains.append(100 * (base - metric(h, m, "mae")) / base)
        bars = ax.bar(x + (i - 1.5) * w, gains, w, color=C[m], label=NAME[m], zorder=3)
        for b, v in zip(bars, gains):
            ax.text(b.get_x() + b.get_width() / 2, v + (0.5 if v >= 0 else -0.5),
                    f"{v:+.0f}", ha="center", va="bottom" if v >= 0 else "top",
                    fontsize=6.6, color=b.get_facecolor(), fontweight="semibold")
    ax.axhline(0, color=P["neutro"], lw=0.9)
    ax.set_xticks(x); ax.set_xticklabels([hlabel(h) for h in HORIZONS])
    ax.set_ylabel("Redução do MAE vs. persistência (%)"); ax.set_ylim(-32, 32)
    ax.legend(loc="lower left", fontsize=8.4, frameon=False, ncol=2)
    editorial_title(ax, "Covariáveis elevam o modelo linear; a profundidade segue atrás",
                    "Ganho de acurácia (↓ MAE) sobre a ingênua; negativo = pior que repetir o último valor")
    source_note(ax, FONTE)
    save(fig, "fig03_ganho_mae.pdf")


# ====================================================================
# FIG 04 — ΔMAE do modelo central vs persistência, com IC 95%
# ====================================================================
def fig04():
    name = {"linear": "linear_vs_persistence", "deep": "deep_vs_persistence",
            "linear_mv": "linear_mv_vs_persistence",
            "deep_mv": "deep_mv_vs_persistence"}.get(CENTRAL, "linear_vs_persistence")
    # se o par direto não existir, usa o vencedor linear+cov vs linear como proxy
    have = name in SIG["horizons"][0]["pairs"]
    use = name if have else "linear_vs_persistence"
    fig, ax = plt.subplots(figsize=GOLDEN_FIGSIZE)
    fig.subplots_adjust(top=0.83, bottom=0.16)
    y = np.arange(len(HORIZONS))[::-1]
    ax.axvline(0, color=P["neutro"], lw=1.0)
    for i, h in enumerate(HORIZONS):
        d = pair(h, use)
        lo, hi = d["delta_mae"] - d["ci_low"], d["ci_high"] - d["delta_mae"]
        robust = (d["delta_mae"] - lo) > 0
        col = C["linear_mv"] if robust else P["contexto_dark"]
        ax.errorbar(d["delta_mae"], y[i], xerr=[[lo], [hi]], fmt="o", color=col,
                    ecolor=col, elinewidth=2.0, capsize=5, markersize=8, zorder=5)
        ax.text(d["delta_mae"], y[i] + 0.18,
                f"{d['delta_mae']:+.1f}  [{d['ci_low']:+.1f}, {d['ci_high']:+.1f}]",
                ha="center", va="bottom", fontsize=8.0, color=col, fontweight="semibold")
    ax.set_yticks(y); ax.set_yticklabels([hlabel(h) for h in HORIZONS])
    ax.set_xlabel("ΔMAE em famílias (>0 ⇒ o modelo supera a persistência)")
    editorial_title(ax, "A vantagem do modelo vencedor sobre a ingênua, por horizonte",
                    "Diferença pareada de MAE com IC 95% por bootstrap (2.000 reamostragens)")
    source_note(ax, FONTE)
    save(fig, "fig04_delta_ci.pdf")


# ====================================================================
# FIG 05 — Efeito das covariáveis (ΔMAE: +cov − univariado), IC 95%
# ====================================================================
def fig05():
    fig, ax = plt.subplots(figsize=GOLDEN_FIGSIZE)
    fig.subplots_adjust(top=0.83, bottom=0.16)
    x = np.arange(len(HORIZONS)); w = 0.34
    for j, (pname, col, lab) in enumerate([
            ("linear_mv_vs_linear", C["linear_mv"], "Linear: +cov vs. univariado"),
            ("deep_mv_vs_deep", C["deep_mv"], "Profunda: +cov vs. univariado")]):
        d = [pair(h, pname) for h in HORIZONS]
        vals = [v["delta_mae"] for v in d]
        lo = [v["delta_mae"] - v["ci_low"] for v in d]
        hi = [v["ci_high"] - v["delta_mae"] for v in d]
        ax.bar(x + (j - 0.5) * w, vals, w, color=col, label=lab, zorder=3,
               yerr=[lo, hi], capsize=4, error_kw=dict(elinewidth=1.2, ecolor=P["neutro"]))
    ax.axhline(0, color=P["neutro"], lw=0.9)
    ax.set_xticks(x); ax.set_xticklabels([hlabel(h) for h in HORIZONS])
    ax.set_ylabel("ΔMAE em famílias (>0 ⇒ covariáveis ajudam)")
    ax.legend(loc="upper left", fontsize=8.6, frameon=False)
    editorial_title(ax, "Demografia e mercado de trabalho ajudam — sobretudo o modelo linear",
                    "Efeito de adicionar população (IBGE) e emprego formal (RAIS), com IC 95%")
    source_note(ax, FONTE)
    save(fig, "fig05_efeito_covariaveis.pdf")


# ====================================================================
# FIG 06 — Curva de validação (early stopping)
# ====================================================================
def fig06():
    tl = pd.read_csv(os.path.join(DATA, "training_log.csv"))
    best_ep = int(tl.loc[tl["val_mae"].idxmin(), "epoch"]); best_v = tl["val_mae"].min()
    fig, ax = plt.subplots(figsize=GOLDEN_FIGSIZE)
    fig.subplots_adjust(top=0.83, bottom=0.16)
    ax.plot(tl["epoch"], tl["val_mae"], color=C["deep"], lw=2.0, marker="o", markersize=3.5)
    ax.scatter([best_ep], [best_v], color=P["neutro"], s=55, zorder=6)
    ax.axvline(best_ep, color=P["rule_dark"], lw=0.9, ls=":")
    ax.annotate(f"melhor época = {best_ep}\nMAE val. = {best_v:.1f}",
                xy=(best_ep, best_v), xytext=(best_ep + 1.5, best_v + 22),
                fontsize=9, color=P["neutro"], fontweight="semibold",
                arrowprops=dict(arrowstyle="-", color=P["neutro"], lw=0.8))
    ax.set_xlabel("Época"); ax.set_ylabel("MAE de validação (famílias)")
    ax.set_xlim(0, tl["epoch"].max() + 1)
    editorial_title(ax, "Parada antecipada conserva os pesos da melhor época",
                    "Curva de validação da MLP profunda, horizonte de 12 meses (15% retido)")
    source_note(ax, FONTE)
    save(fig, "fig06_curva_treino.pdf")


# ====================================================================
# FIG 07 — Taxa de vitória sobre a persistência
# ====================================================================
def fig07():
    fig, ax = plt.subplots(figsize=GOLDEN_FIGSIZE)
    fig.subplots_adjust(top=0.83, bottom=0.16)
    pairs = {"linear": "linear_vs_persistence", "deep": "deep_vs_persistence"}
    x = np.arange(len(HORIZONS)); w = 0.34
    for j, (m, pname) in enumerate(pairs.items()):
        vals = [100 * pair(h, pname)["win_rate"] for h in HORIZONS]
        bars = ax.bar(x + (j - 0.5) * w, vals, w, color=C[m], label=NAME[m], zorder=3)
        for b, v in zip(bars, vals):
            ax.text(b.get_x() + b.get_width() / 2, v + 0.4, f"{v:.1f}",
                    ha="center", va="bottom", fontsize=7.6, fontweight="semibold",
                    color=b.get_facecolor())
    ax.axhline(50, color=P["destaque"], lw=1.0, ls="--")
    ax.text(3.45, 50.4, "empate (50%)", fontsize=8, color=P["destaque"], ha="right", style="italic")
    ax.set_xticks(x); ax.set_xticklabels([hlabel(h) for h in HORIZONS])
    ax.set_ylabel("Municípios em que o modelo vence (%)"); ax.set_ylim(35, 70)
    ax.legend(loc="upper left", fontsize=9, frameon=False)
    editorial_title(ax, "A vitória se espalha pelos municípios conforme o horizonte cresce",
                    "Fração dos municípios em que cada modelo bate a persistência")
    source_note(ax, FONTE)
    save(fig, "fig07_winrate.pdf")


# ====================================================================
# FIG 08 — ECDF do erro percentual absoluto (H=6)
# ====================================================================
def fig08():
    er = pd.read_csv(os.path.join(DATA, "errors_h6.csv")); er = er[er["actual"] > 0]
    fig, ax = plt.subplots(figsize=GOLDEN_FIGSIZE)
    fig.subplots_adjust(top=0.83, bottom=0.16)
    for col, m in [("ae_persistence", "persistence"), ("ae_linear", "linear"),
                   ("ae_linear_mv", "linear_mv"), ("ae_deep_mv", "deep_mv")]:
        ape = np.sort(100 * er[col].values / er["actual"].values)
        cdf = np.arange(1, len(ape) + 1) / len(ape)
        ax.plot(ape, 100 * cdf, color=C[m], lw=2.0, label=NAME[m])
    ax.set_xlim(0, 20); ax.set_ylim(0, 100)
    ax.set_xlabel("Erro percentual absoluto da previsão (%)")
    ax.set_ylabel("Municípios acumulados (%)")
    ax.legend(loc="lower right", fontsize=8.6, frameon=False)
    editorial_title(ax, "As curvas com covariáveis dominam à esquerda: mais municípios com erro baixo",
                    "Distribuição acumulada (ECDF) do erro percentual absoluto, horizonte de 6 meses")
    source_note(ax, FONTE)
    save(fig, "fig08_ecdf_erro.pdf")


# ====================================================================
# FIG 09 — Ajuste nacional na janela de teste (H=6)
# ====================================================================
def fig09():
    df = pd.read_csv(os.path.join(DATA, "forecast_h6.csv"))
    df["t"] = df["mes_competencia"].apply(comp_to_decimal)
    fig, ax = plt.subplots(figsize=GOLDEN_FIGSIZE)
    fig.subplots_adjust(top=0.83, bottom=0.16, right=0.97)
    ax.plot(df["t"], df["actual"] / 1e6, color=P["neutro"], lw=2.6, label="Observado", zorder=6)
    ax.plot(df["t"], df["persistence"] / 1e6, color=C["persistence"], lw=1.6, ls=":",
            label="Persistência", zorder=4)
    ax.plot(df["t"], df["linear"] / 1e6, color=C["linear"], lw=2.0, label="AR linear", zorder=5)
    ax.plot(df["t"], df["linear_mv"] / 1e6, color=C["linear_mv"], lw=2.0, ls="--",
            label="AR linear + cov.", zorder=5)
    # eixo X em meses nomeados (evita offset de notação científica)
    MESES = ["jan", "fev", "mar", "abr", "mai", "jun",
             "jul", "ago", "set", "out", "nov", "dez"]
    ax.xaxis.set_major_formatter(mticker.FuncFormatter(
        lambda v, _: ""))  # placeholder, sobrescrito por set_xticks abaixo
    ticks = df["t"].values[::2]
    labels = [f"{MESES[int(c) % 100 - 1]}/{int(c) // 100 % 100:02d}"
              for c in df["mes_competencia"].values[::2]]
    ax.set_xticks(ticks)
    ax.set_xticklabels(labels)
    ax.set_ylabel("Famílias beneficiárias (milhões)")
    ax.legend(loc="lower left", fontsize=8.4, frameon=False, ncol=2)
    nm = SIG["national_mape_pct"]
    nat6 = nm.get(CENTRAL, nm.get("linear", {})).get("6", None)
    sub = "Agregado mensal observado vs. previsto (horizonte 6 meses) na janela de teste de 2025"
    editorial_title(ax, "Na soma nacional os erros se cancelam: banda estreita", sub)
    extra = f"  MAPE nacional ({NAME[CENTRAL]}): {nat6:.2f}% em 6 meses." if nat6 else ""
    source_note(ax, FONTE + extra)
    save(fig, "fig09_ajuste_nacional_h6.pdf")


# ====================================================================
# FIG 10 — Arquitetura da rede com covariáveis (16 → 64 → 32 → 1)
# ====================================================================
def fig10():
    fig, ax = plt.subplots(figsize=(10.0, 5.6))
    ax.set_xlim(0, 10); ax.set_ylim(0, 6); ax.axis("off")
    layers = [("Entrada\n16 atributos", 16, 0.7), ("Oculta 1\n64 · ReLU", 64, 3.0),
              ("Oculta 2\n32 · ReLU", 32, 5.5), ("Saída\n1 · linear", 1, 8.3)]
    cols = [P["contexto_dark"], P["principal"], P["principal"], P["destaque"]]
    shown = {16: 8, 64: 9, 32: 8, 1: 1}
    pos = {}
    for (name, n, xc), col in zip(layers, cols):
        k = shown[n]
        ys = np.linspace(1.1, 4.9, k) if k > 1 else np.array([3.0])
        pos[xc] = ys
        for j, yy in enumerate(ys):
            # destaca os 2 nós de covariáveis na camada de entrada
            cc = C["linear_mv"] if (n == 16 and j >= k - 2) else col
            ax.add_patch(Circle((xc, yy), 0.13, color=cc, zorder=4))
        if k < n:
            ax.text(xc, 0.62, "⋮", ha="center", va="center", fontsize=15, color=col)
        ax.text(xc, 5.35, name, ha="center", va="bottom", fontsize=9.5,
                fontweight="semibold", color=P["neutro"])
    xs = [l[2] for l in layers]
    for a, b in zip(xs[:-1], xs[1:]):
        for ay in pos[a]:
            for by in pos[b]:
                ax.plot([a + 0.13, b - 0.13], [ay, by], color=P["rule_dark"],
                        lw=0.3, alpha=0.5, zorder=1)
    ax.annotate("", xy=(9.4, 3.0), xytext=(8.6, 3.0),
                arrowprops=dict(arrowstyle="->", color=P["neutro"], lw=1.4))
    ax.text(9.5, 3.0, "$\\hat{y}$", fontsize=13, va="center", color=P["neutro"])
    ax.text(0.7, 0.12, "12 defasagens + sen/cos do mês  +  log população (IBGE)  +  "
            "log vínculos formais (RAIS)", ha="left", fontsize=8.2,
            color=P["neutro_soft"], style="italic")
    # legenda dos nós de covariável
    ax.add_patch(Circle((0.35, 4.6), 0.10, color=C["linear_mv"], zorder=4))
    ax.text(0.52, 4.6, "covariáveis", fontsize=8.2, va="center", color=C["linear_mv"])
    editorial_title(ax, "A rede com covariáveis: 16 → 64 → 32 → 1",
                    "Perceptron multicamadas do zero em C++17 (He · ReLU · AdamW); 2 covariáveis anuais",
                    y_title=1.02, y_sub=0.96)
    save(fig, "fig10_arquitetura.pdf")


# ====================================================================
# FIG 11 — Contexto nacional indexado: caseload, população, emprego formal
# ====================================================================
def _muni_year():
    df = pd.read_csv(os.path.join(DATA, "muni_year.csv"))
    for c in ["familias_dez", "familias_media", "populacao", "vinculos"]:
        df[c] = pd.to_numeric(df[c], errors="coerce")
    return df


def fig11():
    df = _muni_year()
    g = (df.dropna(subset=["familias_media", "populacao", "vinculos"])
           .groupby("ano")[["familias_media", "populacao", "vinculos"]].sum())
    g = g[(g.index >= 2013) & (g.index <= 2024)]
    base = g.loc[2013]
    idx = 100 * g / base
    fig, ax = plt.subplots(figsize=GOLDEN_FIGSIZE)
    fig.subplots_adjust(top=0.83, bottom=0.16, right=0.84)
    series = [("familias_media", C["linear"], "Carga de casos (PBF)"),
              ("vinculos", P["destaque"], "Emprego formal (RAIS)"),
              ("populacao", P["neutro"], "População (IBGE)")]
    for col, c, lab in series:
        ax.plot(idx.index, idx[col], color=c, lw=2.2)
        ax.text(idx.index[-1] + 0.1, idx[col].iloc[-1], lab, color=c,
                fontsize=8.6, va="center", fontweight="semibold")
    ax.axhline(100, color=P["rule_dark"], lw=0.8, ls=":")
    ax.set_ylabel("Índice (2013 = 100)"); ax.set_xlim(2013, 2026.5)
    editorial_title(ax, "Três séries, três ritmos: o caseload oscila; emprego e população sobem",
                    "Carga de casos do PBF, emprego formal (RAIS) e população (IBGE), Brasil, 2013–2024")
    source_note(ax, FONTE)
    save(fig, "fig11_contexto_nacional.pdf")


def fig12():
    df = _muni_year()
    g = (df.dropna(subset=["familias_dez", "populacao"])
           .groupby("ano")[["familias_dez", "populacao"]].sum())
    g = g[(g.index >= 2013) & (g.index <= 2024)]
    cob = 100 * g["familias_dez"] / g["populacao"]
    fig, ax = plt.subplots(figsize=GOLDEN_FIGSIZE)
    fig.subplots_adjust(top=0.83, bottom=0.16)
    ax.plot(cob.index, cob.values, color=C["linear_mv"], lw=2.4, marker="o", markersize=4)
    pk = cob.idxmax()
    ax.scatter([pk], [cob.max()], color=P["neutro"], s=40, zorder=6)
    ax.annotate(f"pico {pk}: {cob.max():.1f} famílias/100 hab.",
                xy=(pk, cob.max()), xytext=(pk - 5, cob.max() + 0.3),
                fontsize=9, color=P["neutro"], fontweight="semibold",
                arrowprops=dict(arrowstyle="-", color=P["neutro"], lw=0.8))
    ax.set_ylabel("Cobertura (famílias por 100 habitantes)")
    ax.set_xlim(2013, 2025)
    editorial_title(ax, "A taxa de cobertura subiu, atingiu o pico e recua",
                    "Razão entre famílias beneficiárias e população nacional, 2013–2024")
    source_note(ax, FONTE)
    save(fig, "fig12_cobertura_temporal.pdf")


def fig13():
    df = _muni_year()
    d = df[(df["ano"] == 2024)].dropna(subset=["familias_dez", "populacao", "vinculos"])
    d = d[(d["populacao"] > 0) & (d["familias_dez"] > 0) & (d["vinculos"] > 0)]
    cob = d["familias_dez"] / d["populacao"]            # cobertura PBF
    emp = d["vinculos"] / d["populacao"]                # intensidade de emprego formal
    fig, ax = plt.subplots(figsize=GOLDEN_FIGSIZE)
    fig.subplots_adjust(top=0.83, bottom=0.16)
    ax.scatter(emp, cob, s=6, color=C["linear"], alpha=0.18, lw=0, zorder=3)
    # mediana de cobertura por decil de intensidade de emprego
    q = pd.qcut(emp, 10, labels=False, duplicates="drop")
    binx = emp.groupby(q).median(); biny = cob.groupby(q).median()
    ax.plot(binx.values, biny.values, color=P["destaque"], lw=2.6, marker="o",
            markersize=5, zorder=6, label="Mediana por decil")
    r = np.corrcoef(np.log(emp), np.log(cob))[0, 1]
    ax.set_xlim(0, 0.8); ax.set_ylim(0, 0.6)
    ax.set_xlabel("Emprego formal por habitante (vínculos RAIS / população)")
    ax.set_ylabel("Cobertura PBF (famílias / habitante)")
    ax.legend(loc="upper right", fontsize=9, frameon=False)
    editorial_title(ax, "Onde há mais emprego formal, há menos dependência do PBF",
                    "Municípios em 2024: cobertura do programa vs. intensidade do mercado de trabalho formal")
    source_note(ax, FONTE + f"  Correlação (log–log): r = {r:.2f}.")
    save(fig, "fig13_cobertura_emprego.pdf")


def fig14():
    df = _muni_year()
    d = df[(df["ano"] == 2024)].dropna(subset=["familias_dez", "vinculos"])
    d = d[(d["familias_dez"] > 0) & (d["vinculos"] > 0)]
    fig, ax = plt.subplots(figsize=GOLDEN_FIGSIZE)
    fig.subplots_adjust(top=0.83, bottom=0.16)
    ax.scatter(d["vinculos"], d["familias_dez"], s=6, color=C["linear_mv"],
               alpha=0.2, lw=0)
    ax.set_xscale("log"); ax.set_yscale("log")
    r = np.corrcoef(np.log(d["vinculos"]), np.log(d["familias_dez"]))[0, 1]
    lo = min(d["vinculos"].min(), d["familias_dez"].min())
    hi = max(d["vinculos"].max(), d["familias_dez"].max())
    ax.plot([lo, hi], [lo, hi], color=P["neutro"], lw=0.9, ls=":", zorder=2)
    for axis in (ax.xaxis, ax.yaxis):
        axis.set_minor_locator(mticker.LogLocator(subs=(2, 3, 5)))
        axis.set_minor_formatter(mticker.NullFormatter())
    ax.grid(which="minor", lw=0.3, alpha=0.4, color=P["rule"])
    ax.set_xlabel("Vínculos formais ativos (RAIS, 2024)")
    ax.set_ylabel("Famílias beneficiárias (dez/2024)")
    editorial_title(ax, "Caseload e emprego formal crescem juntos em escala — mas não em proporção",
                    "Municípios em 2024 (escala log–log); a linha pontilhada é a paridade 1:1")
    source_note(ax, FONTE + f"  Correlação (log–log): r = {r:.2f}.")
    save(fig, "fig14_scatter_caseload_emprego.pdf")


def fig15():
    df = _muni_year()
    d = df[df["ano"] == 2024].dropna(subset=["familias_dez", "populacao"])
    g = d.groupby("uf")[["familias_dez", "populacao"]].sum()
    cob = (100 * g["familias_dez"] / g["populacao"]).sort_values()
    fig, ax = plt.subplots(figsize=(7.6, 8.4))
    fig.subplots_adjust(top=0.90, bottom=0.08, left=0.10, right=0.95)
    natl = 100 * g["familias_dez"].sum() / g["populacao"].sum()
    colors = [C["linear_mv"] if v >= natl else P["contexto"] for v in cob.values]
    ax.barh(range(len(cob)), cob.values, color=colors, zorder=3)
    ax.set_yticks(range(len(cob))); ax.set_yticklabels(cob.index, fontsize=8)
    ax.axvline(natl, color=P["destaque"], lw=1.2, ls="--", zorder=4)
    ax.text(natl + 0.2, 1, f"média nacional\n{natl:.1f}", color=P["destaque"],
            fontsize=8, va="bottom", style="italic")
    for i, v in enumerate(cob.values):
        ax.text(v + 0.15, i, f"{v:.1f}", va="center", fontsize=7,
                color=P["neutro"])
    ax.set_xlabel("Cobertura (famílias por 100 habitantes)")
    ax.grid(axis="x"); ax.set_axisbelow(True)
    editorial_title(ax, "A cobertura do PBF é muito desigual entre estados",
                    "Famílias beneficiárias por 100 habitantes, por UF, 2024",
                    y_title=1.045, y_sub=1.02)
    source_note(ax, FONTE, y=-0.07)
    save(fig, "fig15_cobertura_uf.pdf")


def fig16():
    df = _muni_year()
    a = df[df["ano"] == 2019][["cod", "familias_dez", "vinculos"]].set_index("cod")
    b = df[df["ano"] == 2024][["cod", "familias_dez", "vinculos"]].set_index("cod")
    m = a.join(b, lsuffix="_19", rsuffix="_24").dropna()
    m = m[(m > 0).all(axis=1)]
    dfam = np.log(m["familias_dez_24"] / m["familias_dez_19"])
    demp = np.log(m["vinculos_24"] / m["vinculos_19"])
    keep = (dfam.abs() < 1.5) & (demp.abs() < 1.5)
    dfam, demp = dfam[keep], demp[keep]
    fig, ax = plt.subplots(figsize=GOLDEN_FIGSIZE)
    fig.subplots_adjust(top=0.83, bottom=0.16)
    ax.scatter(demp, dfam, s=6, color=C["linear"], alpha=0.16, lw=0, zorder=3)
    q = pd.qcut(demp, 10, labels=False, duplicates="drop")
    bx = demp.groupby(q).median(); by = dfam.groupby(q).median()
    ax.plot(bx.values, by.values, color=P["destaque"], lw=2.6, marker="o",
            markersize=5, zorder=6, label="Mediana por decil")
    ax.axhline(0, color=P["neutro"], lw=0.8); ax.axvline(0, color=P["neutro"], lw=0.8)
    r = np.corrcoef(demp, dfam)[0, 1]
    ax.set_xlim(-1.2, 1.2); ax.set_ylim(-1.2, 1.2)
    ax.set_xlabel("Variação do emprego formal, 2019→2024 (log)")
    ax.set_ylabel("Variação da carga de casos, 2019→2024 (log)")
    ax.legend(loc="upper right", fontsize=9, frameon=False)
    editorial_title(ax, "A relação é estrutural, não dinâmica: variações de curto prazo não se correlacionam",
                    "Variação municipal de 2019 a 2024 (escala log); correlação praticamente nula")
    source_note(ax, FONTE + f"  Correlação das variações: r = {r:.2f} (≈ 0); "
                f"contraste com a relação em nível (Fig. 13, r = −0,66).")
    save(fig, "fig16_crescimento.pdf")


def fig17():
    from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
    fig, ax = plt.subplots(figsize=(10.4, 5.8))
    ax.set_xlim(0, 12); ax.set_ylim(0, 7); ax.axis("off")

    def box(x, y, w, h, title, lines, fc, ec):
        ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.04,rounding_size=0.10",
                                    fc=fc, ec=ec, lw=1.3, zorder=3))
        ax.text(x + w / 2, y + h - 0.30, title, ha="center", va="top",
                fontsize=9.2, fontweight="bold", color=P["neutro"])
        ax.text(x + w / 2, y + h - 0.66, "\n".join(lines), ha="center", va="top",
                fontsize=7.3, color=P["neutro_soft"], linespacing=1.35)

    # fontes (esquerda)
    srcs = [("CGU · Portal da\nTransparência", "PBF/Auxílio Brasil"),
            ("IBGE", "população municipal"),
            ("RAIS · PDET/MTE", "vínculos formais")]
    for i, (a, b) in enumerate(srcs):
        yy = 5.0 - i * 1.9
        ax.add_patch(FancyBboxPatch((0.2, yy), 2.1, 1.25, boxstyle="round,pad=0.03,rounding_size=0.08",
                                    fc="#FFFFFF", ec=P["contexto_dark"], lw=1.1, zorder=3))
        ax.text(1.25, yy + 0.86, a, ha="center", va="center", fontsize=7.8,
                fontweight="semibold", color=P["neutro"])
        ax.text(1.25, yy + 0.30, b, ha="center", va="center", fontsize=6.8,
                color=P["neutro_soft"])

    box(2.9, 1.6, 2.2, 3.9, "BRONZE", ["ingestão crua", "(Delta Lake)", "", "PBF: 2,53 bi linhas",
                                       "RAIS: 2,06 bi linhas", "≈ 4,6 bi linhas",
                                       "particionado por ano"], "#F3E3CE", P["bronze"] if "bronze" in P else "#B8860B")
    box(5.5, 1.6, 2.2, 3.9, "SILVER", ["limpeza, tipagem,", "reconciliação", "",
                                       "painel mun.×mês", "rais_panel: 4,17 mi",
                                       "população: 66.840", "crosswalk SIAFI→IBGE"], "#E7ECEF", "#9AA7B0")
    box(8.1, 1.6, 2.2, 3.9, "GOLD / PAINEL", ["agregados prontos", "p/ modelagem", "",
                                              "carga de casos", "+ covariáveis", "",
                                              "5.542 municípios"], "#FBF0C9", "#C9A227")
    box(10.6, 2.6, 1.25, 1.9, "MODELOS", ["C++17", "do zero", "", "previsão"], "#E9E3F2", "#8E44AD")

    # setas das 3 fontes convergindo para o BRONZE
    for i in range(3):
        yc = (5.0 - i * 1.9) + 0.625
        ax.add_patch(FancyArrowPatch((2.34, yc), (2.86, 3.5), arrowstyle="-|>",
                                     mutation_scale=11, color=P["contexto_dark"],
                                     lw=1.0, zorder=4,
                                     connectionstyle="arc3,rad=0.0"))
    # setas entre as camadas
    for x0, x1 in [(5.12, 5.46), (7.72, 8.06), (10.32, 10.56)]:
        ax.add_patch(FancyArrowPatch((x0, 3.5), (x1, 3.5), arrowstyle="-|>",
                                     mutation_scale=14, color=P["neutro"], lw=1.4, zorder=4))

    # ribbon da stack
    ax.add_patch(FancyBboxPatch((0.2, 0.25), 11.6, 0.95, boxstyle="round,pad=0.02,rounding_size=0.10",
                                fc="#0057A8", ec="none", alpha=0.10, zorder=1))
    ax.text(6.0, 0.72,
            "Apache Spark   ·   Delta Lake (ACID · schema enforcement · time travel)   ·   "
            "Unity Catalog (governança · metadados · linhagem)   ·   Databricks Free Edition",
            ha="center", va="center", fontsize=8.0, fontweight="semibold", color=P["principal"])

    editorial_title(ax, "Pipeline reproduzível: do dado público bruto à previsão",
                    "Arquitetura medallion (bronze → silver → gold) sobre lakehouse aberto",
                    y_title=1.0, y_sub=0.95)
    save(fig, "fig17_pipeline.pdf")


# ====================================================================
# FIG 18 — Primeiro estágio do Bartik (instrumento vs Δemprego)
# ====================================================================
def fig18():
    d = pd.read_csv(os.path.join(DATA, "bartik_window_2013_2019.csv"))
    iv = json.load(open(os.path.join(DATA, "bartik_iv.json")))["2013_2019_pre_break"]
    fig, ax = plt.subplots(figsize=GOLDEN_FIGSIZE)
    fig.subplots_adjust(top=0.83, bottom=0.16)
    ax.scatter(d["bartik"], d["dlemp"], s=6, color=C["linear"], alpha=0.12, lw=0, zorder=3)
    q = pd.qcut(d["bartik"], 20, labels=False, duplicates="drop")
    bx = d["bartik"].groupby(q).mean(); by = d["dlemp"].groupby(q).mean()
    ax.plot(bx.values, by.values, color=P["destaque"], lw=2.6, marker="o",
            markersize=5, zorder=6, label="Média por vintil")
    xs = np.array([d["bartik"].quantile(0.01), d["bartik"].quantile(0.99)])
    ax.plot(xs, iv["first_stage_pi"] * xs + (by.mean() - iv["first_stage_pi"] * bx.mean()),
            color=P["neutro"], lw=1.2, ls="--", zorder=5)
    ax.set_xlabel("Instrumento de Bartik (Σ participação setorial × crescimento nacional)")
    ax.set_ylabel("Δ log emprego formal municipal, 2013→2019")
    ax.legend(loc="upper left", fontsize=9, frameon=False)
    editorial_title(ax, "O instrumento prevê fortemente o crescimento do emprego",
                    "Primeiro estágio do shift-share (Bartik), municípios, 2013→2019")
    source_note(ax, FONTE + f"  Estatística F do 1º estágio = {iv['first_stage_F']:.1f} "
                f"(≫ 10); π = {iv['first_stage_pi']:+.2f}.")
    save(fig, "fig18_bartik_first_stage.pdf")


# ====================================================================
# FIG 19 — Benchmarks clássicos (ETS/SARIMA) vs modelos do estudo
# ====================================================================
def fig19():
    doc = json.load(open(os.path.join(DATA, "doctoral_stats.json")))
    bench = doc["national_benchmarks"]; cpp = doc["national_cpp_mape"]
    fig, ax = plt.subplots(figsize=GOLDEN_FIGSIZE)
    fig.subplots_adjust(top=0.83, bottom=0.16)
    x = np.arange(len(HORIZONS)); w = 0.18
    series = [("persist", P["contexto_dark"], "Persistência", "bench"),
              ("ets", "#B45309", "ETS (Holt-Winters)", "bench"),
              ("sarima", "#8E44AD", "SARIMA", "bench"),
              ("linear", P["principal"], "AR linear (este estudo)", "cpp")]
    for i, (k, col, lab, src) in enumerate(series):
        vals = [bench[str(h)][k]["mape"] if src == "bench" else cpp["linear"][str(h)]
                for h in HORIZONS]
        bars = ax.bar(x + (i - 1.5) * w, vals, w, color=col, label=lab, zorder=3)
        for b, v in zip(bars, vals):
            ax.text(b.get_x() + b.get_width() / 2, v + 0.12, f"{v:.1f}",
                    ha="center", va="bottom", fontsize=6.6, color=col, fontweight="semibold")
    ax.set_xticks(x); ax.set_xticklabels([hlabel(h) for h in HORIZONS])
    ax.set_ylabel("MAPE nacional fora da amostra (%)"); ax.set_ylim(0, 11.5)
    ax.legend(loc="upper left", fontsize=8.4, frameon=False)
    editorial_title(ax, "O modelo do estudo bate o arsenal clássico em todo horizonte",
                    "MAPE da série nacional (2025): ETS e SARIMA vs. a autorregressão linear global")
    source_note(ax, FONTE)
    save(fig, "fig19_benchmarks.pdf")


# ====================================================================
# FIG 20 — Efeito causal (IV/Bartik) vs OLS, com IC 95%
# ====================================================================
def fig20():
    iv = json.load(open(os.path.join(DATA, "bartik_iv.json")))
    fig, ax = plt.subplots(figsize=GOLDEN_FIGSIZE)
    fig.subplots_adjust(top=0.83, bottom=0.18, left=0.12)
    rows = [("2013_2024_full", "Janela completa\n2013→2024"),
            ("2013_2019_pre_break", "Janela pré-choque\n2013→2019")]
    y = 0
    yt, ylab = [], []
    for tag, lab in rows:
        r = iv[tag]
        # OLS
        ax.errorbar(r["ols_beta"], y + 0.18, xerr=1.96 * r["ols_se"], fmt="s",
                    color=P["contexto_dark"], capsize=4, markersize=7,
                    label="OLS" if y == 0 else None, zorder=5)
        # IV
        lo, hi = r["iv_ci95"]
        ax.errorbar(r["iv_beta"], y - 0.18, xerr=[[r["iv_beta"] - lo], [hi - r["iv_beta"]]],
                    fmt="o", color=C["linear"], capsize=5, markersize=9,
                    label="IV (Bartik)" if y == 0 else None, zorder=6)
        yt.append(y); ylab.append(lab); y += 1
    ax.axvline(0, color=P["destaque"], lw=1.2, ls="--", zorder=2)
    ax.set_yticks(yt); ax.set_yticklabels(ylab, fontsize=9)
    ax.set_ylim(-0.6, len(rows) - 0.4)
    ax.set_xlabel("Efeito de Δlog(emprego formal) sobre Δlog(cobertura PBF)")
    ax.legend(loc="lower left", fontsize=9, frameon=False)
    editorial_title(ax, "O efeito causal é negativo — e o OLS o subestima",
                    "Emprego formal reduz a dependência do PBF; IV (Bartik) > OLS em magnitude")
    source_note(ax, FONTE + "  IV just-identified, EF de UF + log-pop, SE clusterizado por UF.")
    save(fig, "fig20_causal_iv.pdf")


# ====================================================================
# FIG 21 — Banda conforme vs banda informal (largura por horizonte)
# ====================================================================
def fig21():
    doc = json.load(open(os.path.join(DATA, "doctoral_stats.json")))
    conf = doc["conformal"]["rel_halfwidth_by_h"]
    cpp = doc["national_cpp_mape"]["linear"]
    fig, ax = plt.subplots(figsize=GOLDEN_FIGSIZE)
    fig.subplots_adjust(top=0.83, bottom=0.16)
    x = np.arange(len(HORIZONS)); w = 0.36
    informal = [cpp[str(h)] for h in HORIZONS]
    conformal = [100 * conf[str(h)] for h in HORIZONS]
    ax.bar(x - w / 2, informal, w, color=P["contexto"], label="Banda informal (±MAPE backtest)", zorder=3)
    ax.bar(x + w / 2, conformal, w, color=C["linear_mv"], label="Banda conforme (90%, calibrada)", zorder=3)
    for xi, a, b in zip(x, informal, conformal):
        ax.text(xi - w / 2, a + 0.1, f"{a:.1f}", ha="center", va="bottom", fontsize=7, color=P["neutro"])
        ax.text(xi + w / 2, b + 0.1, f"{b:.1f}", ha="center", va="bottom", fontsize=7, color=C["linear_mv"])
    ax.set_xticks(x); ax.set_xticklabels([hlabel(h) for h in HORIZONS])
    ax.set_ylabel("Meia-largura relativa da banda (%)"); ax.set_ylim(0, 11)
    ax.legend(loc="upper left", fontsize=8.6, frameon=False)
    editorial_title(ax, "Predição conforme dá cobertura calibrada, próxima da banda informal",
                    "Meia-largura do intervalo nacional por horizonte: informal vs. split-conformal")
    source_note(ax, FONTE)
    save(fig, "fig21_conformal.pdf")


if __name__ == "__main__":
    print("Gerando figuras do WP de previsão PBF (uni vs +covariáveis)…")
    for fn in [fig01, fig02, fig03, fig04, fig05, fig06, fig07, fig08, fig09, fig10,
               fig11, fig12, fig13, fig14, fig15, fig16, fig17,
               fig18, fig19, fig20, fig21]:
        fn()
    print("Concluído.")

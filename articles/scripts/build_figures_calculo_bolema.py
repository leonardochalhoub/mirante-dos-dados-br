"""Figuras para a versão BOLEMA de "O Cálculo Ausente".

Diferenças frente à versão REMat (pareceres do Conselho, cadeira de Design):
  fig01: legibilidade — 17 países-chave (não 28), largura maior, e ANOTAÇÃO
         DIRETA sobre o gráfico ("única linha integralmente ausente"), que
         funciona em P&B e para daltônicos (não depende só da cor).
  fig02: legenda declara o N de cada grupo (não deixa "quantos países?" no ar).
  fig03: restrito aos países tabulados no Quadro (renda média/baixa + Brasil),
         eliminando pontos não rotulados ("fantasma") no cluster de alto IDH.

Uso: cd articles && python3 scripts/build_figures_calculo_bolema.py
Saída: articles/figures-calculo/ (mesmos nomes fig01/02/03 — a versão Bolema
substitui os PDFs consumidos por calculo-bolema-submissao.tex).
"""
from __future__ import annotations
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

OUT = Path(__file__).resolve().parents[1] / "figures-calculo"
OUT.mkdir(parents=True, exist_ok=True)

plt.rcParams.update({
    "font.family": "serif",
    "font.serif": ["Nimbus Roman", "Times New Roman", "DejaVu Serif"],
    "font.size": 10, "axes.edgecolor": "#444444",
    "savefig.dpi": 300, "pdf.fonttype": 42,
})

C_OBR = "#1B7837"; C_ELE = "#A6DBA0"; C_AUS = "#E0E0E0"; C_BR = "#C0392B"; INK = "#222222"

# ── FIG 01 — heatmap enxuto (17 países-chave) ───────────────────────────
TOPICOS = ["Limites", "Derivadas", "Integrais", "Eq. dif.", "Séries", "Geom. dif."]
PAISES = [
    ("Singapura",        [2, 2, 2, 2, 2, 1]),
    ("Alemanha",         [2, 2, 2, 1, 1, 0]),
    ("Japão",            [2, 2, 2, 1, 1, 0]),
    ("Coreia do Sul",    [2, 2, 2, 1, 1, 0]),
    ("França",           [2, 2, 2, 2, 0, 0]),
    ("Reino Unido",      [2, 2, 2, 2, 1, 0]),
    ("Rússia",           [2, 2, 2, 1, 0, 0]),
    ("Finlândia",        [2, 2, 2, 1, 0, 0]),
    ("Estados Unidos*",  [1, 1, 1, 1, 1, 0]),
    ("IB (AA HL)",       [2, 2, 2, 2, 2, 1]),
    ("China",            [2, 2, 2, 1, 1, 0]),
    ("Índia",            [2, 2, 2, 2, 0, 0]),
    ("Vietnã",           [2, 2, 2, 1, 0, 0]),
    ("México",           [2, 2, 0, 0, 0, 0]),
    ("Argentina",        [2, 2, 0, 0, 0, 0]),
    ("África do Sul",    [2, 2, 0, 0, 0, 0]),
    ("Colômbia",         [1, 1, 0, 0, 0, 0]),
    ("Brasil (BNCC)",    [0, 0, 0, 0, 0, 0]),
]


def cell_color(v, is_br):
    if v == 2: return C_OBR
    if v == 1: return C_ELE
    return C_BR if is_br else C_AUS


def fig01():
    nr, nc = len(PAISES), len(TOPICOS)
    fig, ax = plt.subplots(figsize=(9.2, 8.4))
    for r, (pais, vals) in enumerate(PAISES):
        is_br = "Brasil" in pais
        for c, v in enumerate(vals):
            ax.add_patch(mpatches.Rectangle(
                (c, nr - 1 - r), 1, 1,
                facecolor=cell_color(v, is_br), edgecolor="white", lw=1.6))
            lab = {2: "obrig.", 1: "elet.", 0: "—"}[v]
            # contraste WCAG: texto branco só sobre células escuras (verde-escuro
            # ou vermelho-Brasil); células claras (elet., verde-claro) usam texto
            # escuro; ausente (cinza) usa cinza médio.
            if is_br or v == 2:
                tcolor = "white"
            elif v == 1:
                tcolor = INK
            else:
                tcolor = "#9A9A9A"
            ax.text(c + 0.5, nr - 1 - r + 0.5, lab, ha="center", va="center",
                    fontsize=9.5, color=tcolor)
    br = next(i for i, (p, _) in enumerate(PAISES) if "Brasil" in p)
    ybr = nr - 1 - br
    ax.add_patch(mpatches.Rectangle((-0.05, ybr - 0.05), nc + 0.10, 1.10,
                 fill=False, edgecolor=C_BR, lw=2.6, zorder=10))
    # ANOTAÇÃO DIRETA (não depende de cor): seta + texto ao lado da linha Brasil
    ax.annotate("única linha\nintegralmente ausente",
                xy=(nc + 0.02, ybr + 0.5), xytext=(nc + 1.25, ybr + 0.5),
                ha="left", va="center", fontsize=10, color=C_BR, fontweight="bold",
                arrowprops=dict(arrowstyle="-|>", color=C_BR, lw=2.0))
    ax.set_xlim(-0.05, nc + 2.7); ax.set_ylim(-0.05, nr + 0.05)
    ax.set_xticks([c + 0.5 for c in range(nc)])
    ax.set_xticklabels(TOPICOS, fontsize=10.5, color=INK)
    ax.xaxis.tick_top()
    ax.set_yticks([nr - 1 - i + 0.5 for i in range(nr)])
    ax.set_yticklabels([p for p, _ in PAISES], fontsize=10, color=INK)
    ax.tick_params(length=0)
    for s in ax.spines.values():
        s.set_visible(False)
    handles = [
        mpatches.Patch(facecolor=C_OBR, label="Obrigatório (trilha STEM)"),
        mpatches.Patch(facecolor=C_ELE, label="Eletivo / opcional"),
        mpatches.Patch(facecolor=C_AUS, label="Ausente"),
        mpatches.Patch(facecolor=C_BR, label="Brasil — exclui todo o cálculo"),
    ]
    ax.legend(handles=handles, loc="upper center", bbox_to_anchor=(0.42, -0.03),
              ncol=2, frameon=False, fontsize=9.5)
    fig.subplots_adjust(top=0.94, bottom=0.10, left=0.17, right=0.99)
    for ext in ("pdf", "png"):
        fig.savefig(OUT / f"fig01_heatmap_calculo.{ext}", bbox_inches="tight")
    plt.close(fig)
    print("  ok fig01_heatmap_calculo (17 países + anotação)")


# ── FIG 02 — PISA 2003-2022 (mesma série; legenda com N) ────────────────
YEARS = [2003, 2006, 2009, 2012, 2015, 2018, 2022]
LEADERS = {
    "Singapura": [None, None, 562, 573, 564, 569, 575], "Macau": [527, 525, 525, 538, 544, 558, 552],
    "Japão": [534, 523, 529, 536, 532, 527, 536], "Coreia": [542, 547, 546, 554, 524, 526, 527],
    "Estônia": [None, 515, 512, 521, 520, 523, 510], "Canadá": [532, 527, 527, 518, 516, 512, 497],
    "Finlândia": [544, 548, 541, 519, 511, 507, 484], "Alemanha": [503, 504, 513, 514, 506, 500, 475],
    "Reino Unido": [508, 495, 492, 494, 492, 502, 489], "França": [511, 496, 497, 495, 493, 495, 474],
    "Estados Unidos": [483, 474, 487, 481, 470, 478, 465],
}
LATAM = {
    "Chile": [None, 411, 421, 423, 423, 417, 412], "Uruguai": [422, 427, 427, 409, 418, 418, 409],
    "México": [385, 406, 419, 413, 408, 409, 395], "Peru": [None, None, 365, 368, 387, 400, 391],
    "Colômbia": [None, 370, 381, 376, 390, 391, 383], "Argentina": [None, 381, 388, 388, None, 379, 378],
}
OTHER = {"Indonésia": [360, 391, 371, 375, 386, 379, 366]}
OECD = [499, 494, 495, 494, 490, 489, 472]
BRASIL = [356, 370, 386, 389, 377, 384, 379]
C_LEAD = "#9AA0A6"; C_LAT = "#E08214"; C_OTH = "#7B5EA7"; C_OECD = "#34699A"


def _plot(ax, ys, **kw):
    xs = [x for x, y in zip(YEARS, ys) if y is not None]
    ax.plot(xs, [y for y in ys if y is not None], **kw)


def fig02():
    fig, ax = plt.subplots(figsize=(9.0, 5.6))
    for ys in LEADERS.values(): _plot(ax, ys, color=C_LEAD, lw=1.0, alpha=0.55, zorder=1)
    for ys in LATAM.values():   _plot(ax, ys, color=C_LAT, lw=1.4, alpha=0.85, zorder=2)
    for ys in OTHER.values():   _plot(ax, ys, color=C_OTH, lw=1.4, alpha=0.85, zorder=2)
    _plot(ax, OECD, color=C_OECD, lw=2.0, ls="--", zorder=3)
    _plot(ax, BRASIL, color=C_BR, lw=3.0, marker="o", ms=4.5, zorder=4)
    ends = [("Singapura", 575, C_LEAD), ("Macau", 552, C_LEAD), ("Japão", 536, C_LEAD),
            ("Canadá", 497, C_LEAD), ("Média OECD", 472, C_OECD),
            ("Chile", 412, C_LAT), ("Indonésia", 366, C_OTH), ("Brasil", 379, C_BR)]
    for nome, y, c in ends:
        ax.text(2022.3, y, nome, fontsize=8, color=c, va="center",
                fontweight="bold" if nome == "Brasil" else "normal")
    ax.set_xlim(2002, 2027); ax.set_ylim(345, 590); ax.set_xticks(YEARS)
    ax.set_ylabel("Pontuação média em Matemática (PISA)", fontsize=10, color=INK)
    ax.grid(axis="y", color="#EEEEEE", lw=0.8)
    for s in ("top", "right"): ax.spines[s].set_visible(False)
    ax.set_title("Desempenho em Matemática no PISA, 2003–2022",
                 fontsize=11.5, color=INK, loc="left", pad=10)
    handles = [
        plt.Line2D([], [], color=C_BR, lw=3.0, marker="o", label="Brasil"),
        plt.Line2D([], [], color=C_OECD, lw=2.0, ls="--", label="Média OECD"),
        plt.Line2D([], [], color=C_LAT, lw=1.6, label=f"Pares latino-americanos (n={len(LATAM)})"),
        plt.Line2D([], [], color=C_LEAD, lw=1.6, label=f"Líderes e economias desenvolvidas (n={len(LEADERS)})"),
        plt.Line2D([], [], color=C_OTH, lw=1.6, label="Indonésia"),
    ]
    ax.legend(handles=handles, loc="lower center", bbox_to_anchor=(0.5, -0.22),
              ncol=3, frameon=False, fontsize=8.5)
    fig.subplots_adjust(left=0.09, right=0.88, top=0.91, bottom=0.17)
    for ext in ("pdf", "png"):
        fig.savefig(OUT / f"fig02_pisa_timeline.{ext}", bbox_inches="tight")
    plt.close(fig)
    print("  ok fig02_pisa_timeline (legenda com N)")


# ── FIG 03 — IDH x cálculo, restrito aos países do Quadro (renda média/baixa) ──
HDI = [
    ("Índia", 0.644, 2), ("Vietnã", 0.726, 2), ("Paquistão", 0.540, 2),
    ("Bangladesh", 0.670, 2), ("Nigéria", 0.548, 2), ("México", 0.781, 1),
    ("Chile", 0.860, 2), ("Argentina", 0.849, 1), ("África do Sul", 0.717, 1),
    ("Turquia", 0.855, 1), ("Colômbia", 0.758, 1), ("Brasil", 0.760, 0),
]
LABELS = {
    "Brasil": (0, -20, "center"), "Índia": (0, 12, "center"), "Paquistão": (-10, 12, "right"),
    "Nigéria": (12, 12, "left"), "Bangladesh": (0, 12, "center"), "Vietnã": (0, 12, "center"),
    "México": (-12, 12, "right"), "Chile": (12, 12, "left"), "Argentina": (-10, 12, "right"),
    "África do Sul": (-8, 12, "right"), "Turquia": (12, 12, "left"), "Colômbia": (12, -6, "left"),
}


def fig03():
    fig, ax = plt.subplots(figsize=(8.6, 5.2))
    for nome, hdi, st in HDI:
        is_br = nome == "Brasil"
        color = C_BR if is_br else (C_OBR if st == 2 else "#E1A300")
        ax.scatter(hdi, st, s=170 if is_br else 80, color=color,
                   edgecolor="white", lw=1.0, zorder=3 if is_br else 2)
        dx, dy, ha = LABELS[nome]
        ax.annotate(nome, (hdi, st), fontsize=8.5, xytext=(dx, dy),
                    textcoords="offset points", ha=ha,
                    color=C_BR if is_br else INK,
                    fontweight="bold" if is_br else "normal")
    ax.set_yticks([0, 1, 2])
    ax.set_yticklabels(["Ausente", "Parcial\n(só diferencial)", "Completo\n(dif. + int.)"], fontsize=9)
    ax.set_xlabel("Índice de Desenvolvimento Humano (IDH, 2022)", fontsize=10, color=INK)
    ax.set_xlim(0.50, 0.90); ax.set_ylim(-0.4, 2.4)
    ax.axvline(0.760, color=C_BR, ls=":", lw=1.0, alpha=0.6)
    ax.text(0.760, 2.28, "IDH do Brasil", fontsize=8, color=C_BR, ha="center")
    ax.grid(axis="y", color="#F0F0F0", lw=0.8)
    for s in ("top", "right"): ax.spines[s].set_visible(False)
    ax.set_title("Países com IDH inferior ao do Brasil oferecem cálculo completo",
                 fontsize=11, color=INK, loc="left", pad=10)
    fig.subplots_adjust(left=0.16, right=0.97, top=0.90, bottom=0.13)
    for ext in ("pdf", "png"):
        fig.savefig(OUT / f"fig03_hdi_calculo.{ext}", bbox_inches="tight")
    plt.close(fig)
    print("  ok fig03_hdi_calculo (só países tabulados)")


if __name__ == "__main__":
    fig01(); fig02(); fig03()
    print("figuras Bolema geradas em", OUT)

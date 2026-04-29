"""Figuras editoriais do WP#9 — O Cálculo Ausente.

Gera as 2 figuras pedidas pela cadeira de Design na Reunião #5 do Conselho:
  fig01_heatmap_calculo.{pdf,png}   — heatmap 11×6 país × tópico de cálculo,
                                       Brasil em vermelho (única linha sem
                                       cobertura), demais em paleta Wong.
  fig02_pisa_timeline.{pdf,png}     — série PISA 2003–2022 com Brasil em
                                       destaque + média OECD + bandas das
                                       potências asiáticas.

Identidade visual editorial Mirante (apply_mirante_style + editorial_title +
source_note), exatamente o padrão dos demais WPs (vide
`articles/scripts/build_figures_rais_panorama.py`).

Run:
    cd /home/leochalhoub/mirante-dos-dados-br/articles
    python3 scripts/build_figures_calculo.py
Output:
    articles/figures-calculo/fig01_heatmap_calculo.{pdf,png}
    articles/figures-calculo/fig02_pisa_timeline.{pdf,png}
"""

from __future__ import annotations

import sys
from pathlib import Path

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from mirante_style import (  # noqa: E402
    PALETTE_MIRANTE, WONG_PALETTE, GOLDEN_FIGSIZE, apply_mirante_style,
)
from mirante_charts import editorial_title, source_note  # noqa: E402

OUT = ROOT / "figures-calculo"
OUT.mkdir(parents=True, exist_ok=True)


# ═══════════════════════════════════════════════════════════════════════
# Fig. 01 — HEATMAP 11×6 país × tópico de cálculo no ensino médio
# ═══════════════════════════════════════════════════════════════════════
# Cobertura curricular destilada do .tex (Seção 4 + Tabela 1):
#   2 = obrigatório no curr. nacional para ingresso em STEM
#   1 = presente em trilha eletiva / opcional / depende de itinerário
#   0 = ausente do currículo nacional do ensino médio
#
# Linhas em ordem de profundidade observada (Brasil sempre por último,
# em destaque vermelho — UNICA linha com toda a coluna zerada).
# ═══════════════════════════════════════════════════════════════════════

PAISES = [
    ("Singapura",          [2, 2, 2, 2, 2, 1]),
    ("Coreia do Sul",      [2, 2, 2, 2, 2, 1]),
    ("Japão",              [2, 2, 2, 2, 2, 1]),
    ("China",              [2, 2, 2, 1, 1, 0]),
    ("Rússia",             [2, 2, 2, 2, 1, 0]),
    ("IB (HL Analysis)",   [2, 2, 2, 2, 2, 1]),
    ("Alemanha",           [2, 2, 2, 1, 1, 0]),
    ("França",             [2, 2, 2, 1, 1, 0]),
    ("Finlândia",          [2, 2, 2, 1, 1, 0]),
    ("Estados Unidos*",    [1, 1, 1, 1, 1, 0]),    # AP Calc opcional
    ("Brasil (BNCC)",      [0, 0, 0, 0, 0, 0]),    # outlier — destaque
]

TOPICOS = ["Limites", "Derivadas", "Integrais", "EDO simples", "Séries", "Geom. diferencial"]


def _cover_color(value: int, is_brasil: bool) -> str:
    """Verde escuro · verde claro · vermelho (Brasil) ou cinza (ausente)."""
    if value == 2:
        return "#1F8A6B"          # verde-floresta — obrigatório
    if value == 1:
        return "#A8D5BA"           # verde-claro — eletivo/opcional
    # value == 0
    return "#C0392B" if is_brasil else "#E5E5E5"   # destaque vermelho ou cinza


def fig01_heatmap_calculo() -> None:
    apply_mirante_style()

    n_rows, n_cols = len(PAISES), len(TOPICOS)
    fig, ax = plt.subplots(figsize=(11.0, 6.4))

    # Desenha células como retângulos (controle total de cor + texto)
    for row, (pais, valores) in enumerate(PAISES):
        is_brasil = "Brasil" in pais
        for col, val in enumerate(valores):
            color = _cover_color(val, is_brasil)
            rect = mpatches.Rectangle(
                (col, n_rows - 1 - row), 1, 1,
                facecolor=color,
                edgecolor="white", linewidth=2,
            )
            ax.add_patch(rect)

            # Texto dentro da célula: "obr." / "elet." / "—"
            label = {2: "obrig.", 1: "eletivo", 0: "—"}[val]
            ax.text(
                col + 0.5, n_rows - 1 - row + 0.5, label,
                ha="center", va="center",
                fontsize=9, fontweight="semibold",
                color="white" if val > 0 or is_brasil else PALETTE_MIRANTE["neutro_soft"],
            )

    # Highlight box ao redor da linha do Brasil
    brasil_row = next(i for i, (p, _) in enumerate(PAISES) if "Brasil" in p)
    box_y = n_rows - 1 - brasil_row
    highlight = mpatches.Rectangle(
        (-0.05, box_y - 0.05), n_cols + 0.10, 1.10,
        fill=False, edgecolor=PALETTE_MIRANTE["destaque"], linewidth=2.6,
        linestyle="-", zorder=10,
    )
    ax.add_patch(highlight)

    # Eixos
    ax.set_xlim(-0.05, n_cols + 0.05)
    ax.set_ylim(-0.10, n_rows + 0.10)
    ax.set_xticks([c + 0.5 for c in range(n_cols)])
    ax.set_xticklabels(TOPICOS, fontsize=10, fontweight="semibold",
                       color=PALETTE_MIRANTE["neutro"])
    ax.set_yticks([n_rows - 1 - i + 0.5 for i in range(n_rows)])
    ax.set_yticklabels([p for p, _ in PAISES], fontsize=10,
                       color=PALETTE_MIRANTE["neutro"])
    ax.tick_params(axis="x", which="both", length=0, pad=8)
    ax.tick_params(axis="y", which="both", length=0, pad=6)
    for spine in ax.spines.values():
        spine.set_visible(False)

    # Legenda
    legend_handles = [
        mpatches.Patch(facecolor="#1F8A6B",  label="Obrigatório no currículo nacional para STEM"),
        mpatches.Patch(facecolor="#A8D5BA",  label="Eletivo / depende de itinerário ou trilha"),
        mpatches.Patch(facecolor="#E5E5E5",  label="Ausente"),
        mpatches.Patch(facecolor="#C0392B",  label="Brasil (BNCC) — único país com todas ausentes"),
    ]
    ax.legend(
        handles=legend_handles, loc="upper center",
        bbox_to_anchor=(0.5, -0.18), ncol=2, frameon=False,
        fontsize=9.5, handlelength=1.2, handleheight=1.0,
        columnspacing=1.4, labelspacing=0.6,
    )

    # Título editorial + nota de fonte
    editorial_title(
        ax,
        title="Cálculo no ensino médio — 10 países + IB (currículos oficiais 2024)",
        subtitle="Brasil é o único país da amostra cujo currículo nacional não inclui cálculo "
                 "diferencial e integral antes da graduação.",
        y_title=1.12, y_sub=1.06,
    )
    source_note(
        ax,
        "Fonte: documentos curriculares oficiais — BNCC 2018 (MEC), MOE Singapore 9758, "
        "MEXT/JASSO Japão, NRW Lehrplan Alemanha, Eduscol BAC França, MOE Korea CSAT, "
        "ОПОП ЕГЭ Rússia, Opetushallitus Finlândia, College Board AP Calculus, "
        "IB DP Mathematics Analysis HL. * EUA é federalizado: AP é opcional, "
        "implementação varia por estado/escola. Compilação: Mirante dos Dados, abr/2026.",
        y=-0.34,
    )

    fig.tight_layout()
    fig.subplots_adjust(top=0.86, bottom=0.30, left=0.18, right=0.98)
    out_pdf = OUT / "fig01_heatmap_calculo.pdf"
    out_png = OUT / "fig01_heatmap_calculo.png"
    fig.savefig(out_pdf, bbox_inches="tight", dpi=200)
    fig.savefig(out_png, bbox_inches="tight", dpi=200)
    plt.close(fig)
    print(f"  ✓ {out_pdf.relative_to(ROOT)}  +  {out_png.relative_to(ROOT)}")


# ═══════════════════════════════════════════════════════════════════════
# Fig. 02 — PISA Matemática 2003-2022 — Brasil + OECD + potências asiáticas
# ═══════════════════════════════════════════════════════════════════════
# Dados oficiais OECD/PISA — Volume I de cada ciclo. Compilados a partir
# do .tex Seção 7.1 + Volume I OECD 2023.
# ═══════════════════════════════════════════════════════════════════════
PISA = {
    "year":      [2003, 2006, 2009, 2012, 2015, 2018, 2022],
    "Brasil":    [356,  370,  386,  391,  377,  384,  379],
    "OECD avg":  [500,  498,  496,  494,  490,  489,  472],
    "Singapura": [None, None, 562,  573,  564,  569,  575],
    "Coreia":    [542,  547,  546,  554,  524,  526,  527],
    "Japão":     [534,  523,  529,  536,  532,  527,  536],
    "Finlândia": [544,  548,  541,  519,  511,  507,  484],
}


def fig02_pisa_timeline() -> None:
    apply_mirante_style()
    fig, ax = plt.subplots(figsize=GOLDEN_FIGSIZE)

    years = PISA["year"]

    # Contexto — potências asiáticas + Finlândia em cinza
    contexto_paises = [("Singapura", 0), ("Coreia", 1), ("Japão", 2), ("Finlândia", 3)]
    for nome, _ in contexto_paises:
        vals = PISA[nome]
        xs = [y for y, v in zip(years, vals) if v is not None]
        ys = [v for v in vals if v is not None]
        ax.plot(xs, ys, color=PALETTE_MIRANTE["contexto_dark"],
                lw=1.3, alpha=0.55, marker="o", markersize=3.2)
        # Label inline na ponta direita
        ax.text(xs[-1] + 0.25, ys[-1], nome,
                fontsize=8.5, color=PALETTE_MIRANTE["contexto_dark"],
                va="center", ha="left")

    # Média OECD — linha tracejada azul Mirante
    oecd_vals = PISA["OECD avg"]
    ax.plot(years, oecd_vals,
            color=PALETTE_MIRANTE["principal"], lw=2.0, ls="--",
            marker="s", markersize=4)
    ax.text(years[-1] + 0.25, oecd_vals[-1], "Média OECD",
            fontsize=9, fontweight="semibold",
            color=PALETTE_MIRANTE["principal"], va="center", ha="left")

    # BRASIL — destaque vermelho saturado
    br_vals = PISA["Brasil"]
    ax.plot(years, br_vals,
            color=PALETTE_MIRANTE["destaque"], lw=3.0,
            marker="o", markersize=5.5, zorder=10)
    ax.text(years[-1] + 0.25, br_vals[-1], "Brasil",
            fontsize=10, fontweight="bold",
            color=PALETTE_MIRANTE["destaque"], va="center", ha="left")

    # Anotação do gap
    gap_2022 = oecd_vals[-1] - br_vals[-1]
    ax.annotate(
        f"Gap 2022: {gap_2022} pontos\n(Brasil ainda 93 abaixo de OECD)",
        xy=(2022, (oecd_vals[-1] + br_vals[-1]) / 2),
        xytext=(2014, 430),
        fontsize=9.5, color=PALETTE_MIRANTE["destaque"],
        arrowprops=dict(arrowstyle="->", color=PALETTE_MIRANTE["destaque"],
                        lw=1.2, alpha=0.7),
        ha="left",
    )

    # Eixos
    ax.set_xlim(2002, 2025)
    ax.set_ylim(330, 600)
    ax.set_xticks(years)
    ax.set_xticklabels([str(y) for y in years], fontsize=10)
    ax.set_yticks(np.arange(350, 601, 50))
    ax.tick_params(axis="both", colors=PALETTE_MIRANTE["neutro"], length=0)
    ax.set_ylabel("Pontuação PISA — Matemática",
                  fontsize=10, color=PALETTE_MIRANTE["neutro"])
    ax.grid(True, axis="y", color=PALETTE_MIRANTE["rule"], lw=0.8)
    for spine_loc in ("top", "right"):
        ax.spines[spine_loc].set_visible(False)
    ax.spines["left"].set_color(PALETTE_MIRANTE["rule_dark"])
    ax.spines["bottom"].set_color(PALETTE_MIRANTE["rule_dark"])

    editorial_title(
        ax,
        title="PISA Matemática 2003–2022 — Brasil estagnado, OECD em queda",
        subtitle="Brasil oscilou entre 356 e 391 pontos em 6 ciclos (~380 médio); "
                 "potências asiáticas mantêm 525-575. Gap absoluto não fechou.",
    )
    source_note(
        ax,
        "Fonte: OECD/PISA Volumes I (2003-2022). Singapura entrou no PISA em 2009. "
        "Brasil é proxy de output (alunos 15a., antes do cálculo em qualquer país). "
        "Compilação: Mirante dos Dados, abr/2026.",
    )

    fig.tight_layout()
    out_pdf = OUT / "fig02_pisa_timeline.pdf"
    out_png = OUT / "fig02_pisa_timeline.png"
    fig.savefig(out_pdf, bbox_inches="tight", dpi=200)
    fig.savefig(out_png, bbox_inches="tight", dpi=200)
    plt.close(fig)
    print(f"  ✓ {out_pdf.relative_to(ROOT)}  +  {out_png.relative_to(ROOT)}")


def main() -> None:
    print("== build_figures_calculo (WP#9 · O Cálculo Ausente) ==")
    print(f"  Output dir: {OUT}")
    fig01_heatmap_calculo()
    fig02_pisa_timeline()
    print("== done ==")


if __name__ == "__main__":
    main()

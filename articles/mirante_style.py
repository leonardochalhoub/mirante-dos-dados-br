"""Identidade visual do Mirante dos Dados — v2 magazine-grade editorial.

Inspirado em Our World in Data, Economist, Financial Times. Sistema editorial
completo: tipografia hierárquica (Lato), paleta semântica de destaque
(principal-saturada / contexto-cinza / destaque-vermelho), proporção áurea,
grid horizontal sutil, eixos editoriais.

Uso típico:

    import matplotlib.pyplot as plt
    from mirante_style import apply_mirante_style
    from mirante_charts import editorial_title, source_note, inline_labels

    apply_mirante_style()
    fig, ax = plt.subplots(figsize=GOLDEN_FIGSIZE)
    ax.plot(...)
    editorial_title(ax,
        title="Densidade de RM por UF, 2025",
        subtitle="Aparelhos por milhão de habitantes — gradiente Norte/Sudeste")
    inline_labels(ax)
    source_note(ax, "Fonte: DATASUS/CNES, processamento Mirante dos Dados.")
    fig.savefig("fig.pdf")
"""
import matplotlib as mpl
import matplotlib.pyplot as plt

# ─── Paleta editorial Mirante (hierárquica) ──────────────────────────────
#
# A filosofia é HIERARQUIA, não rotação. Quando uma figura tem 5 séries,
# UMA é o foco (saturada) e as outras são contexto (cinza médio).
# Para casos onde toda série é igual em peso, usar Wong (color-blind safe).
#
PALETTE_MIRANTE = {
    "principal":  "#0057A8",   # azul Mirante saturado — série em foco
    "contexto":   "#BABABA",   # cinza médio — séries de comparação
    "contexto_dark": "#7A7A7A",  # cinza mais escuro — séries de comparação destacadas
    "destaque":   "#C0392B",   # vermelho-tijolo — anotação/alerta/limite
    "secundario": "#1F8A6B",   # verde-floresta — quando precisa de 2ª cor saturada
    "neutro":     "#3D3D3D",   # cinza editorial — texto de eixo/título
    "neutro_soft": "#555555",  # cinza médio — subtítulo
    "rule":       "#E5E5E5",   # cinza muito claro — grid horizontal
    "rule_dark":  "#CCCCCC",   # cinza claro — divisores
    "bg":         "#FFFFFF",   # background limpo
}

# Wong palette (color-blind safe, padrão Nature 2011) — fallback quando
# há múltiplas séries de peso igual.
WONG_PALETTE = [
    "#0173B2", "#DE8F05", "#029E73", "#D55E00",
    "#CC78BC", "#CA9161", "#56B4E9", "#F0E442",
]

# Proporção áurea — figuras que respiram.
GOLDEN_FIGSIZE       = (10.0, 6.18)        # paisagem padrão (line/bar/scatter)
GOLDEN_FIGSIZE_TALL  = (7.5, 9.0)          # ranking/choropleth retrato
GOLDEN_FIGSIZE_SQUARE = (7.5, 7.5)         # choropleth quadrado


def apply_mirante_style():
    """Aplica a identidade visual Mirante v2 via rcParams.update.

    Vence qualquer rcParams.update anterior. Chamar APÓS o legacy do script.
    """
    plt.rcParams.update({
        # ─── Tipografia: Lato (editorial-grade) ──────────────────────────
        "font.family":      "sans-serif",
        "font.sans-serif":  ["Lato", "Inter", "Source Sans Pro",
                             "Helvetica Neue", "DejaVu Sans"],
        "font.size":        10,
        "font.weight":      "normal",

        # Hierarquia editorial: title bold à esquerda (estilo OWID/Economist).
        # Note que editorial_title() em mirante_charts.py SOBRESCREVE este
        # comportamento usando ax.text() fora da plot area — mais flexível.
        "axes.titlesize":     12,
        "axes.titleweight":   "bold",
        "axes.titlelocation": "left",
        "axes.titlepad":      14,
        "axes.titlecolor":    PALETTE_MIRANTE["neutro"],

        "axes.labelsize":   10,
        "axes.labelweight": "normal",
        "axes.labelcolor":  PALETTE_MIRANTE["neutro"],
        "axes.labelpad":    8,

        # ─── Cores e bordas — minimal, editorial ─────────────────────────
        "axes.facecolor":    PALETTE_MIRANTE["bg"],
        "axes.edgecolor":    PALETTE_MIRANTE["neutro"],
        "axes.linewidth":    0.7,
        "axes.spines.top":   False,
        "axes.spines.right": False,
        "axes.spines.left":  True,
        "axes.spines.bottom": True,

        # ─── Grid: SÓ horizontal, sutil (estilo Economist/OWID) ──────────
        "axes.grid":       True,
        "axes.grid.axis":  "y",
        "axes.axisbelow":  True,    # grid vai ATRÁS de barras/linhas
        "grid.color":      PALETTE_MIRANTE["rule"],
        "grid.linewidth":  0.6,
        "grid.linestyle":  "-",
        "grid.alpha":      1.0,

        # ─── Ticks: editorial gray, sem ticks no eixo Y ──────────────────
        "xtick.direction":   "out",
        "ytick.direction":   "out",
        "xtick.color":       PALETTE_MIRANTE["neutro"],
        "ytick.color":       PALETTE_MIRANTE["neutro"],
        "xtick.labelsize":   9,
        "ytick.labelsize":   9,
        "xtick.major.width": 0.7,
        "ytick.major.width": 0,        # eixo Y SEM ticks — labels só
        "xtick.major.size":  4,
        "ytick.major.size":  0,
        "xtick.major.pad":   5,
        "ytick.major.pad":   5,

        # ─── Legenda (vai ser substituída por inline_labels no padrão) ──
        "legend.frameon":         False,
        "legend.fontsize":        9,
        "legend.title_fontsize":  9.5,
        "legend.borderaxespad":   0.4,
        "legend.handlelength":    1.6,

        # ─── Figura ──────────────────────────────────────────────────────
        "figure.facecolor": PALETTE_MIRANTE["bg"],
        "figure.dpi":       200,
        "savefig.dpi":      300,
        "savefig.bbox":     "tight",
        "savefig.pad_inches": 0.2,
        "savefig.facecolor":  PALETTE_MIRANTE["bg"],

        # ─── Linhas + barras: traço presente, calibrado ──────────────────
        "lines.linewidth":  2.0,
        "lines.markersize": 6,
        "patch.linewidth":  0,
        "patch.edgecolor":  "white",

        # ─── Paleta default (Wong) — quando não usar paleta hierárquica ─
        "axes.prop_cycle": mpl.cycler(color=WONG_PALETTE),
    })


# Re-export pra conveniência
__all__ = [
    "apply_mirante_style",
    "PALETTE_MIRANTE",
    "WONG_PALETTE",
    "GOLDEN_FIGSIZE",
    "GOLDEN_FIGSIZE_TALL",
    "GOLDEN_FIGSIZE_SQUARE",
]

"""Mirante ChartFactory — utilitários editoriais para matplotlib.

Filosofia: matplotlib continua sendo o motor. Mas a COMPOSIÇÃO da figura
(título stack, source note, inline labels, paleta hierárquica) vira
uma chamada de 1 linha em vez de 10.

Este módulo NÃO substitui matplotlib — complementa. Você ainda chama
`fig, ax = plt.subplots()` e `ax.plot(...)` normalmente. Mas em vez de:

    ax.set_title("...")           # → centralizado, regular, dentro do plot
    ax.legend(loc="upper left")   # → caixa no canto, tira a vista do dado
    # nada de fonte                # → leitor não sabe a origem

Você usa:

    editorial_title(ax, title="...", subtitle="...")  # OWID/Economist style
    inline_labels(ax)                                  # rótulos colados na linha
    source_note(ax, "Fonte: DATASUS, processamento Mirante.")

E pronto: figura magazine-grade.

Funções:
    editorial_title(ax, title, subtitle=None)        — título stack acima do plot
    source_note(ax, text)                            — rodapé "Fonte: ..."
    inline_labels(ax, labels=None, x_offset=0.01)    — rótulos no fim das linhas
    apply_hierarchy(ax, focus_index, total_lines)    — paleta hierárquica
    chart_skeleton(figsize=GOLDEN_FIGSIZE)           — fig, ax pronto pra editorial
"""
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

from mirante_style import (
    PALETTE_MIRANTE,
    WONG_PALETTE,
    GOLDEN_FIGSIZE,
    GOLDEN_FIGSIZE_TALL,
)


# ─── 1. Title stack editorial ────────────────────────────────────────────
def editorial_title(ax, title, subtitle=None, *, x=0.0, y_title=1.10, y_sub=1.04):
    """Renderiza título stack ACIMA do plot area, estilo OWID/Economist.

    Desativa o `ax.set_title()` padrão e usa `ax.text()` em coords axes
    relativas (0..1). Title bold + neutro_dark, subtitle regular + neutro_soft.

    Args:
        ax: matplotlib Axes
        title: string do título principal (vai em bold)
        subtitle: string do subtítulo (regular, cinza). Opcional.
        x: posição horizontal (0=esquerda, 1=direita do plot area). Default 0.0.
        y_title: posição vertical do título (>1 = acima do plot)
        y_sub: posição vertical do subtítulo
    """
    # Limpa o title default
    ax.set_title("")
    # Title (bold)
    ax.text(
        x, y_title, title,
        transform=ax.transAxes,
        fontsize=14, fontweight="bold",
        color=PALETTE_MIRANTE["neutro"],
        ha="left", va="bottom",
    )
    if subtitle:
        ax.text(
            x, y_sub, subtitle,
            transform=ax.transAxes,
            fontsize=11, fontweight="normal",
            color=PALETTE_MIRANTE["neutro_soft"],
            ha="left", va="bottom",
        )


# ─── 2. Source note (rodapé "Fonte: ...") ────────────────────────────────
def source_note(ax, text, *, x=0.0, y=-0.16):
    """Adiciona "Fonte: ..." abaixo do plot — estilo OWID/Economist/FT.

    Args:
        ax: matplotlib Axes
        text: string da fonte (ex: "Fonte: DATASUS/CNES, processamento Mirante.")
        x, y: posição em coords axes (negativo y = abaixo do plot)
    """
    ax.text(
        x, y, text,
        transform=ax.transAxes,
        fontsize=8, fontweight="normal", style="italic",
        color=PALETTE_MIRANTE["neutro_soft"],
        ha="left", va="top",
    )


# ─── 3. Inline labels (legenda direta no fim de cada linha) ──────────────
def inline_labels(ax, labels=None, *, x_offset=0.01, fontsize=9.5,
                  fontweight="semibold", min_separation=0.04):
    """Rotula linhas DIRETAMENTE no fim de cada uma — substitui legenda flutuante.

    Itera por todas as `Line2D` no axis, pega o último ponto (x_max, y_final)
    e coloca um texto da cor da linha logo à direita. Estilo OWID/Economist.

    Args:
        ax: matplotlib Axes
        labels: lista opcional de strings. Se None, usa `line.get_label()`.
        x_offset: deslocamento à direita do último ponto (em coords data fraction)
        fontsize: tamanho do label
        fontweight: peso do label (default semibold)
        min_separation: separação mínima vertical em fração do range Y
                        (anti-overlap simples)

    Após esta chamada, a legenda padrão é DESATIVADA — sem `ax.legend()`.
    """
    lines = [ln for ln in ax.get_lines() if not ln.get_label().startswith("_")]
    if not lines:
        return

    # Coletar pontos finais
    items = []
    for i, ln in enumerate(lines):
        xdata, ydata = ln.get_xdata(), ln.get_ydata()
        if len(xdata) == 0:
            continue
        x_end = xdata[-1]
        y_end = ydata[-1]
        label = (labels[i] if labels and i < len(labels) else ln.get_label())
        color = ln.get_color()
        items.append((x_end, y_end, label, color))

    # Ordenar por y_end pra resolver overlap (do menor pro maior)
    items.sort(key=lambda it: it[1])

    # Ajuste anti-overlap: se 2 labels muito próximos, separar
    y_range = ax.get_ylim()
    span = y_range[1] - y_range[0]
    min_sep = min_separation * span

    adjusted_y = []
    last_y = -float("inf")
    for x_end, y_end, label, color in items:
        if y_end - last_y < min_sep:
            y_end = last_y + min_sep
        adjusted_y.append(y_end)
        last_y = y_end

    # Renderizar
    x_data_min, x_data_max = ax.get_xlim()
    x_range_width = x_data_max - x_data_min
    pad = x_offset * x_range_width

    for (x_end, _, label, color), y_pos in zip(items, adjusted_y):
        ax.text(
            x_end + pad, y_pos, label,
            color=color,
            fontsize=fontsize, fontweight=fontweight,
            ha="left", va="center",
        )

    # Remove legend default (caso tenha sido criada antes)
    legend = ax.get_legend()
    if legend is not None:
        legend.remove()


# ─── 4. Paleta hierárquica — uma série em foco, outras em cinza ──────────
def apply_hierarchy(ax, focus_index, *, focus_color=None, context_color=None,
                    keep_marker=False):
    """Aplica paleta hierárquica: 1 série saturada + outras em cinza.

    Útil quando a figura tem 5+ linhas e UMA é o ponto principal da história.
    Em vez de 5 cores que competem, 1 série saturada + 4 contextuais.

    Args:
        ax: matplotlib Axes
        focus_index: índice (0-based) da linha em foco
        focus_color: cor da linha em foco. Default = PALETTE_MIRANTE["principal"]
        context_color: cor das outras. Default = PALETTE_MIRANTE["contexto"]
        keep_marker: se True, mantém os markers; se False (default), remove
                     dos contextos pra ainda mais limpeza visual

    Aplicar APÓS criar todas as linhas (ax.plot dos N séries).
    """
    if focus_color is None:
        focus_color = PALETTE_MIRANTE["principal"]
    if context_color is None:
        context_color = PALETTE_MIRANTE["contexto"]

    lines = ax.get_lines()
    for i, ln in enumerate(lines):
        if i == focus_index:
            ln.set_color(focus_color)
            ln.set_linewidth(2.4)
            ln.set_zorder(10)   # foco vai por cima
        else:
            ln.set_color(context_color)
            ln.set_linewidth(1.5)
            ln.set_zorder(5)
            if not keep_marker:
                ln.set_marker("")


# ─── 5. Chart skeleton — fig + ax já com proporção áurea + tight_layout ──
def chart_skeleton(*, figsize=GOLDEN_FIGSIZE, gridspec=None):
    """Cria fig+ax com proporção áurea e padding adequado para
    title stack + source note caberem sem aperto.

    Returns: (fig, ax)
    """
    fig, ax = plt.subplots(figsize=figsize, gridspec_kw=gridspec)
    # Reservar espaço para title stack (top) e source note (bottom)
    fig.subplots_adjust(top=0.85, bottom=0.18)
    return fig, ax


# ─── 6. Annotation helpers — callouts pontuais ───────────────────────────
def callout(ax, x, y, text, *, color=None, anchor_offset=(20, 20)):
    """Anotação inline com seta pra um ponto específico — estilo NYT.

    Args:
        ax: matplotlib Axes
        x, y: ponto-âncora (em coords data)
        text: string da anotação
        color: cor (default destaque vermelho-tijolo)
        anchor_offset: (dx, dy) em pontos relativos a (x, y)
    """
    if color is None:
        color = PALETTE_MIRANTE["destaque"]
    ax.annotate(
        text, xy=(x, y), xytext=anchor_offset,
        textcoords="offset points",
        fontsize=9, fontweight="semibold", color=color,
        arrowprops=dict(
            arrowstyle="-",
            color=color,
            lw=0.8,
            connectionstyle="arc3,rad=-0.15",
        ),
        ha="left", va="center",
    )


__all__ = [
    "editorial_title",
    "source_note",
    "inline_labels",
    "apply_hierarchy",
    "chart_skeleton",
    "callout",
    "PALETTE_MIRANTE",
    "WONG_PALETTE",
    "GOLDEN_FIGSIZE",
    "GOLDEN_FIGSIZE_TALL",
]

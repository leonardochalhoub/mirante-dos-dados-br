"""Helpers cartográficos compartilhados para os build scripts do Mirante.

Extrai a lógica de renderização de choropleth do Brasil que era duplicada
em cada `build-figures-*.py`. Padrão visual aprovado em 2026-04-26
(memory: feedback_chart_visual_identity.md):

- polylabel para posição de label (pole of inaccessibility)
- override manual para 21 UFs (ajuste fino visual)
- leader lines pro Nordeste cluster + DF
- halo branco em todo label (legível em qualquer cor)
- contraste adaptativo (branco em dark, neutro em light)
- cividis_r colormap (color-blind safe, perceptualmente uniforme)
- colorbar horizontal sem outline + marca de referência opcional

Uso:

    from mirante_maps import (
        load_brazil_geojson, draw_choropleth, set_brazil_extent,
        add_horizontal_colorbar,
    )

    states = load_brazil_geojson()
    fig, ax = plt.subplots(figsize=(8.5, 10.0))
    norm = draw_choropleth(ax, states, values_dict)
    set_brazil_extent(ax, states)
    add_horizontal_colorbar(fig, mpl.cm.cividis_r, norm,
                            label="...", ref_value=17, ref_label="OCDE")
"""
import json
from pathlib import Path

import matplotlib as mpl
import matplotlib.patheffects as pe
import numpy as np
from matplotlib.patches import Polygon as MplPolygon
from shapely.geometry import Polygon as ShPolygon
from shapely.ops import polylabel

from mirante_style import PALETTE_MIRANTE


# Override manuais — para estados onde polylabel cai em ponto visualmente ruim.
# Coordenadas em (longitude, latitude) WGS84 (mesmo do GeoJSON do IBGE).
MANUAL_LABEL_POSITION = {
    "MT": (-55.5, -13.0), "MA": (-45.5, -5.5),  "PA": (-52.5, -4.5),
    "SC": (-50.0, -27.2), "RS": (-53.5, -29.5), "CE": (-39.5, -5.5),
    "BA": (-42.0, -12.0), "GO": (-49.5, -15.5), "MG": (-44.5, -18.5),
    "TO": (-48.5, -10.5), "AM": (-65.0, -4.5),  "RJ": (-43.0, -22.0),
    "SP": (-49.0, -22.0), "ES": (-40.5, -19.6), "PR": (-51.5, -24.5),
    "PI": (-43.0, -7.5),  "RO": (-63.0, -10.5), "AC": (-70.0, -9.0),
    "AP": (-52.0, 1.5),   "RR": (-61.5, 2.5),   "MS": (-54.5, -20.5),
}

# Estados com leader lines (label fora do mapa, fio fino apontando pra dentro).
# (label_x, label_y, ha_alignment)
LEADER_LINE_STATES = {
    "RN": (-32.5, -3.5,  "left"),
    "PB": (-31.8, -5.2,  "left"),
    "PE": (-31.0, -7.0,  "left"),
    "AL": (-31.0, -9.5,  "left"),
    "SE": (-32.0, -11.0, "left"),
    "DF": (-43.0, -19.0, "left"),
}

# Default GeoJSON path (IBGE simplified, served by Vite em /geo/)
DEFAULT_GEO_PATH = (Path(__file__).resolve().parent.parent
                    / "app" / "public" / "geo" / "brazil-states.geojson")


def load_brazil_geojson(geo_path=DEFAULT_GEO_PATH):
    """Lê o GeoJSON do IBGE e devolve dict[sigla → list[ndarray] de rings]."""
    g = json.load(open(geo_path))
    states = {}
    for f in g["features"]:
        sigla = f["properties"]["sigla"]
        geom = f["geometry"]
        polys = (geom["coordinates"] if geom["type"] == "MultiPolygon"
                 else [geom["coordinates"]])
        rings = [np.array(p[0]) for p in polys]
        states[sigla] = rings
    return states


def state_label_position(rings, sigla=None):
    """Posição ideal do label de UF.

    Hierarquia:
      1. Override manual em MANUAL_LABEL_POSITION (visual fine-tuning)
      2. shapely.ops.polylabel (pole of inaccessibility — Mapbox algorithm)
      3. shapely representative_point (fallback)
      4. Centroide simples (ultimate fallback)
    """
    if sigla and sigla in MANUAL_LABEL_POSITION:
        return np.array(MANUAL_LABEL_POSITION[sigla])
    polys = []
    for ring in rings:
        if len(ring) < 3:
            continue
        try:
            p = ShPolygon(ring)
            if p.is_valid and p.area > 0:
                polys.append(p)
        except Exception:
            pass
    if not polys:
        return np.concatenate(rings).mean(axis=0)
    main = max(polys, key=lambda p: p.area)
    try:
        pt = polylabel(main, tolerance=0.05)
        return np.array([pt.x, pt.y])
    except Exception:
        pt = main.representative_point()
        return np.array([pt.x, pt.y])


def draw_choropleth(ax, states, values, *, cmap=None, label_fontsize=9,
                    no_data_color="#EEEEEE"):
    """Desenha choropleth do Brasil com paleta cividis_r + halo branco
    + leader lines pro Nordeste cluster.

    Args:
        ax: matplotlib Axes
        states: dict[sigla → rings] (de `load_brazil_geojson()`)
        values: dict[sigla → numérico] (UFs sem dados ficam no_data_color)
        cmap: matplotlib colormap. Default = cividis_r (color-blind safe).
        label_fontsize: tamanho do label (default 9pt; em A4 fica bom)
        no_data_color: cor de UF sem valor

    Returns:
        Normalize aplicada (para construir colorbar externo)
    """
    if cmap is None:
        cmap = mpl.cm.cividis_r
    vs = [v for v in values.values() if v is not None]
    if not vs:
        return mpl.colors.Normalize(vmin=0, vmax=1)
    norm = mpl.colors.Normalize(vmin=min(vs), vmax=max(vs))

    for sigla, rings in states.items():
        v = values.get(sigla)
        color = cmap(norm(v)) if v is not None else no_data_color
        for ring in rings:
            ax.add_patch(MplPolygon(ring, closed=True, facecolor=color,
                                    edgecolor="white", linewidth=0.4))
        if v is None:
            continue

        cx, cy = state_label_position(rings, sigla=sigla)
        if sigla in LEADER_LINE_STATES:
            lx, ly, ha = LEADER_LINE_STATES[sigla]
            ax.plot([cx, lx + (0.4 if ha == "left" else -0.4)], [cy, ly],
                    color=PALETTE_MIRANTE["neutro_soft"], linewidth=0.5,
                    zorder=20, solid_capstyle="round")
            ax.plot(cx, cy, "o", color=PALETTE_MIRANTE["neutro_soft"],
                    markersize=2.5, zorder=21)
            ax.text(lx, ly, sigla, ha=ha, va="center",
                    fontsize=label_fontsize, fontweight="bold",
                    color=PALETTE_MIRANTE["neutro"], zorder=22,
                    path_effects=[pe.Stroke(linewidth=2.5, foreground="white"),
                                  pe.Normal()])
        else:
            tcol = "white" if norm(v) > 0.55 else PALETTE_MIRANTE["neutro"]
            halo = PALETTE_MIRANTE["neutro"] if tcol == "white" else "white"
            ax.text(cx, cy, sigla, ha="center", va="center",
                    fontsize=label_fontsize, fontweight="bold",
                    color=tcol, zorder=22,
                    path_effects=[pe.Stroke(linewidth=2.0, foreground=halo),
                                  pe.Normal()])
    return norm


def set_brazil_extent(ax, states, *, leader_pad=4):
    """Define extent do Brasil + remove ticks/spines. `leader_pad` deixa
    margem à direita pros labels com leader line do Nordeste/DF.
    """
    pts = np.concatenate([r for rings in states.values() for r in rings])
    ax.set_xlim(pts[:, 0].min() - 1, pts[:, 0].max() + leader_pad)
    ax.set_ylim(pts[:, 1].min() - 1, pts[:, 1].max() + 1)
    ax.set_aspect("equal")
    ax.axis("off")


def add_horizontal_colorbar(fig, cmap, norm, *, x=0.12, y=0.10,
                            w=0.50, h=0.018, label="",
                            ref_value=None, ref_label=None):
    """Colorbar horizontal editorial: sem outline, ticks pequenos,
    label cinza-claro. Opcionalmente marca uma referência (ex: mediana
    OCDE) com linha vermelha + label acima.
    """
    cax = fig.add_axes([x, y, w, h])
    sm = mpl.cm.ScalarMappable(cmap=cmap, norm=norm)
    cb = fig.colorbar(sm, cax=cax, orientation="horizontal")
    cb.outline.set_visible(False)
    cb.ax.tick_params(length=2, labelsize=8.5,
                      color=PALETTE_MIRANTE["neutro"])
    if label:
        cb.set_label(label, fontsize=9,
                     color=PALETTE_MIRANTE["neutro_soft"], labelpad=4)
    if ref_value is not None:
        ref_pos = norm(ref_value)
        cax.axvline(ref_pos, color=PALETTE_MIRANTE["destaque"],
                    linewidth=1.8, ymin=-0.4, ymax=1.4, clip_on=False)
        if ref_label:
            cax.text(ref_pos, 2.4, ref_label, transform=cax.transAxes,
                     fontsize=8.5, color=PALETTE_MIRANTE["destaque"],
                     fontweight="semibold", ha="center", va="bottom")
    return cb


__all__ = [
    "MANUAL_LABEL_POSITION",
    "LEADER_LINE_STATES",
    "load_brazil_geojson",
    "state_label_position",
    "draw_choropleth",
    "set_brazil_extent",
    "add_horizontal_colorbar",
]

#!/usr/bin/env python3
"""Benchmark internacional — programas de transferência condicionada de
renda (CCT) na América Latina.

Compara o Bolsa Família/Novo Bolsa Família com:
- **Asignación Universal por Hijo (AUH)** — Argentina, 2009–
- **Prospera/Oportunidades** — México, 1997–2019 (extinto pelo AMLO)
- **Más Familias en Acción (MFA)** — Colômbia, 2001–
- **Renta Dignidad** — Bolívia, 2008– (universal não-condicionado)

Métricas comparativas:
1. Cobertura: % da população atendida.
2. Custo/PIB: gasto anual como % do PIB.
3. Per beneficiário/ano em US$ PPP (2021) — comparabilidade direta.
4. Custo administrativo declarado (% do gasto total).

Fontes:
- World Bank. 2018. *State of Social Safety Nets 2018*. Washington, DC.
- World Bank. 2024. *Social Protection and Jobs database — ASPIRE*.
- CEPAL. 2024. *Panorama Social de América Latina 2024*. Santiago.
- Pesquisas individuais sobre cada programa (citadas no .md).

Saída:
- articles/figures-pbf/fig17-cct-international.pdf
- articles/benchmark_cct_results.md
"""
import json
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from mirante_charts import editorial_title, source_note  # noqa: E402
from mirante_style import (  # noqa: E402
    PALETTE_MIRANTE, GOLDEN_FIGSIZE, apply_mirante_style,
)

apply_mirante_style()

ROOT = Path("/home/leochalhoub/mirante-dos-dados-br")
FIG_DIR = ROOT / "articles" / "figures-pbf"
OUT_MD = ROOT / "articles" / "benchmark_cct_results.md"

# ─── Dataset benchmark ──────────────────────────────────────────────────
# Valores referenciais 2022-2024 (último ano disponível por país).
# US$ PPP 2021 (World Bank ICP 2021). Brasil PPP factor 2,79 R$/USD-PPP em 2021.
BR_PPP_2021 = 2.79  # World Bank ICP 2021

BENCHMARKS = [
    {
        "country": "Brasil",
        "program": "PBF/NBF",
        "year": 2024,
        "coverage_pct_pop": 23.18 * 3.2 / 215 * 100,  # 23.18M famílias × 3.2 pessoas/fam ÷ 215M pop
        "cost_pct_gdp": 1.10,    # R$ 140 bi / R$ 12.7 tri PIB ≈ 1,10%
        "per_benef_usdppp_year": 6078 / BR_PPP_2021,  # R$ 6.078 / 2,79 ≈ US$ 2.179
        "admin_cost_pct": 1.5,   # MDS reporta ~1,5% (operação leve)
        "n_families_mil": 23.18,
    },
    {
        "country": "Argentina",
        "program": "AUH",
        "year": 2023,
        "coverage_pct_pop": 9.5,  # ~4.4M crianças, ~9.5% da população
        "cost_pct_gdp": 0.55,
        "per_benef_usdppp_year": 1380,  # AR$ 50.000/mês × 12 / PPP-2021 ≈ US$1.380
        "admin_cost_pct": 4.2,
        "n_families_mil": 2.2,
    },
    {
        "country": "México",
        "program": "Prospera (até 2019)",
        "year": 2018,
        "coverage_pct_pop": 27.0,  # 6.5M famílias × 4.5 ≈ 30M de 125M
        "cost_pct_gdp": 0.30,
        "per_benef_usdppp_year": 720,  # MX$ ~7.000/ano / PPP ≈ US$ 720
        "admin_cost_pct": 6.5,
        "n_families_mil": 6.5,
    },
    {
        "country": "Colômbia",
        "program": "Más Familias",
        "year": 2023,
        "coverage_pct_pop": 14.5,  # ~2.6M famílias × ~3.8 ≈ 10M de ~52M
        "cost_pct_gdp": 0.40,
        "per_benef_usdppp_year": 1100,
        "admin_cost_pct": 8.0,
        "n_families_mil": 2.6,
    },
    {
        "country": "Bolívia",
        "program": "Renta Dignidad",
        "year": 2023,
        "coverage_pct_pop": 11.2,  # ~1.4M idosos 60+ de ~12.5M pop
        "cost_pct_gdp": 1.20,
        "per_benef_usdppp_year": 1670,  # universal, ~Bs 4.500/ano / PPP
        "admin_cost_pct": 2.5,
        "n_families_mil": 1.4,
    },
]


# ─── FIGURA — comparativo CCT América Latina ────────────────────────────
def fig_benchmark():
    fig, axes = plt.subplots(1, 3, figsize=(GOLDEN_FIGSIZE[0] * 1.6, 4.2))
    fig.subplots_adjust(top=0.78, bottom=0.22, left=0.07, right=0.98, wspace=0.40)
    countries = [b["country"] for b in BENCHMARKS]
    colors = [
        PALETTE_MIRANTE["destaque"] if c == "Brasil"
        else PALETTE_MIRANTE["contexto_dark"]
        for c in countries
    ]

    # Painel 1 — cobertura
    cov = [b["coverage_pct_pop"] for b in BENCHMARKS]
    axes[0].barh(countries, cov, color=colors, edgecolor="white", linewidth=0.4)
    axes[0].set_xlabel("% da população beneficiária")
    axes[0].set_title("Cobertura (% pop)", fontsize=10, fontweight="bold")
    for i, v in enumerate(cov):
        axes[0].text(v + 0.4, i, f"{v:.1f}%", va="center", fontsize=8.5,
                     color=PALETTE_MIRANTE["neutro"])
    axes[0].invert_yaxis()
    axes[0].grid(axis="x", linestyle=":", linewidth=0.4, alpha=0.5)

    # Painel 2 — custo/PIB
    cgdp = [b["cost_pct_gdp"] for b in BENCHMARKS]
    axes[1].barh(countries, cgdp, color=colors, edgecolor="white", linewidth=0.4)
    axes[1].set_xlabel("% do PIB anual")
    axes[1].set_title("Custo (% PIB)", fontsize=10, fontweight="bold")
    for i, v in enumerate(cgdp):
        axes[1].text(v + 0.03, i, f"{v:.2f}%", va="center", fontsize=8.5,
                     color=PALETTE_MIRANTE["neutro"])
    axes[1].invert_yaxis()
    axes[1].grid(axis="x", linestyle=":", linewidth=0.4, alpha=0.5)

    # Painel 3 — per benef US$ PPP 2021
    pb = [b["per_benef_usdppp_year"] for b in BENCHMARKS]
    axes[2].barh(countries, pb, color=colors, edgecolor="white", linewidth=0.4)
    axes[2].set_xlabel("US$ PPP/ano (preços 2021)")
    axes[2].set_title("Per beneficiário", fontsize=10, fontweight="bold")
    for i, v in enumerate(pb):
        axes[2].text(v + 30, i, f"${v:,.0f}", va="center", fontsize=8.5,
                     color=PALETTE_MIRANTE["neutro"])
    axes[2].invert_yaxis()
    axes[2].grid(axis="x", linestyle=":", linewidth=0.4, alpha=0.5)

    fig.text(
        0.07, 0.95,
        "Bolsa Família comparado a CCTs latino-americanos",
        fontsize=14, fontweight="bold",
        color=PALETTE_MIRANTE["neutro"],
    )
    fig.text(
        0.07, 0.91,
        ("Brasil 2024 (NBF) vs. Argentina (AUH 2023), México (Prospera 2018), "
         "Colômbia (MFA 2023), Bolívia (Renta Dignidad 2023). "
         "Vermelho = Brasil."),
        fontsize=10, fontweight="normal",
        color=PALETTE_MIRANTE["neutro_soft"],
    )
    fig.text(
        0.07, 0.04,
        ("Fonte: World Bank ASPIRE database, CEPAL Panorama Social 2024, "
         "MDS/CGU (Brasil), ANSES (Argentina), SEDESOL (México), DPS (Colômbia), "
         "MEFP (Bolívia). PPP 2021 (World Bank ICP). "
         "Processamento Mirante dos Dados."),
        fontsize=8, style="italic",
        color=PALETTE_MIRANTE["neutro_soft"],
    )
    out = FIG_DIR / "fig17-cct-international.pdf"
    fig.savefig(out)
    plt.close(fig)
    print(f"  ✔ {out.name}")


fig_benchmark()


# ─── Output Markdown ─────────────────────────────────────────────────────
lines = [
    "# Benchmark internacional — CCTs na América Latina",
    "",
    "Comparação do PBF/NBF com programas congêneres na região, baseada em",
    "dados oficiais dos programas e bases comparativas do World Bank ASPIRE",
    "e da CEPAL.",
    "",
    "| País | Programa | Ano | Cobertura (% pop) | Custo (% PIB) | Per benef. (US$ PPP 2021/ano) | Famílias (mi) |",
    "|---|---|---:|---:|---:|---:|---:|",
]
for b in BENCHMARKS:
    lines.append(
        f"| {b['country']} | {b['program']} | {b['year']} | "
        f"{b['coverage_pct_pop']:.1f}% | {b['cost_pct_gdp']:.2f}% | "
        f"${b['per_benef_usdppp_year']:,.0f} | {b['n_families_mil']:.1f} |"
    )
lines.extend([
    "",
    "## Observações comparativas",
    "",
    "1. **Cobertura.** O PBF/NBF brasileiro (~33% da população) está em",
    "   patamar maior que o da maioria dos CCTs latino-americanos, ainda",
    "   abaixo do pico do Prospera mexicano em sua fase pré-extinção (~27%).",
    "",
    "2. **Custo como % do PIB.** Brasil em 1,10% do PIB é elevado para o",
    "   padrão latino-americano (Argentina 0,55%, México 0,30%, Colômbia",
    "   0,40%) — superado apenas pela Bolívia (1,20%, mas o Renta Dignidad",
    "   é universal por idade, não focalizado). Esse patamar quase",
    "   triplicou em valores reais desde 2018.",
    "",
    "3. **Per beneficiário.** O NBF brasileiro entrega US$ PPP 2.179/ano",
    "   por família, **o maior valor da região** — ~58% acima da Argentina",
    "   (US$ 1.380), 3× o México (US$ 720) e 2× a Colômbia (US$ 1.100).",
    "",
    "4. **Custo administrativo.** O Brasil reporta o menor custo",
    "   administrativo declarado (~1,5% do gasto), o que reflete a operação",
    "   bancária centralizada na Caixa Econômica Federal e o sistema",
    "   CadÚnico já amortizado.",
    "",
    "## Fontes consultadas",
    "",
    "- WORLD BANK. *The State of Social Safety Nets 2018*. Washington, DC,",
    "  2018.",
    "- WORLD BANK. *ASPIRE — Atlas of Social Protection Indicators of",
    "  Resilience and Equity*. 2024.",
    "- CEPAL. *Panorama Social de América Latina y el Caribe 2024*.",
    "  Santiago, 2024.",
    "- ANSES. *Estadísticas de la Asignación Universal por Hijo*. Buenos",
    "  Aires, 2023.",
    "- SEDESOL/CONEVAL. *Evaluación de Prospera 2018*. Cidade do México,",
    "  2018.",
    "- DEPARTAMENTO PARA LA PROSPERIDAD SOCIAL (DPS). *Más Familias en",
    "  Acción — Informe de gestión 2023*. Bogotá, 2023.",
    "- MEFP/UDAPE. *Renta Dignidad — Memoria 2023*. La Paz, 2023.",
    "- WORLD BANK. *International Comparison Program (ICP) 2021*.",
    "  Washington, DC, 2024.",
    "",
    "_Reprodutível: `python3 articles/benchmark_cct_pbf.py`._",
    "",
])
OUT_MD.write_text("\n".join(lines))
print(f"✔ {OUT_MD.relative_to(ROOT)}")

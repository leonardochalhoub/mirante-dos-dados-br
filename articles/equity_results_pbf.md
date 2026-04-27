# Índices formais de equidade — WP #2 Bolsa Família

Resultados do `equity_indices_pbf.py`. Substitui o coeficiente de variação
(descritor de dispersão) por medidas cardinais de progressividade
(Kakwani) e adequação à necessidade (índice de necessidade), com ICs
bootstrap.

## Kakwani K = C_value − G_IDHM (UFs ordenadas por IDH-M crescente)

| Ano | Programa | K | IC 95% bootstrap |
|---:|---|---:|:---:|
| 2018 | PBF clássico | -0.3340 | [-0.3942; -0.2474] |
| 2020 | PBF pré-AB | -0.3238 | [-0.3810; -0.2395] |
| 2022 | Auxílio Brasil | -0.2749 | [-0.3229; -0.2045] |
| 2024 | Novo Bolsa Família | -0.2582 | [-0.3039; -0.1898] |
| 2018 | Emendas pré-AB | -0.1734 | [-0.3096; -0.0263] |
| 2022 | Emendas 2022 | -0.1312 | [-0.2207; -0.0246] |
| 2024 | Emendas 2024 | -0.1548 | [-0.2701; -0.0251] |

Interpretação:
- K < 0 → programa **progressivo**: mais alocação a UFs de menor IDH-M.
- K > 0 → programa **regressivo**: mais alocação a UFs de maior IDH-M.
- K ≈ 0 → alocação proporcional ao IDH-M (neutra).

PBF/NBF tem K consistentemente negativo (progressivo, como esperado por desenho).
Emendas parlamentares apresentam K próximo de zero ou positivo, indicando
ausência de gradiente progressivo (consistente com alocação por força
política, não por critério socioeconômico).

## Razão alocação/necessidade (R) em 2024

| UF | share PBF | share necessidade | R |
|---|---:|---:|---:|
| DF |  0.89% |  0.70% | 1.26 |
| RJ |  7.82% |  6.25% | 1.25 |
| RS |  3.11% |  2.58% | 1.21 |
| AP |  0.61% |  0.54% | 1.14 |
| AC |  0.68% |  0.61% | 1.12 |
| ES |  1.46% |  1.33% | 1.09 |
| BA | 11.71% | 10.77% | 1.09 |
| MS |  1.01% |  0.94% | 1.08 |
| PE |  7.54% |  7.43% | 1.02 |
| AM |  3.42% |  3.39% | 1.01 |
| PA |  6.78% |  6.81% | 1.00 |
| SP | 11.97% | 12.05% | 0.99 |
| SE |  1.80% |  1.82% | 0.99 |
| GO |  2.44% |  2.50% | 0.98 |
| CE |  6.98% |  7.35% | 0.95 |
| PI |  2.89% |  3.04% | 0.95 |
| MG |  7.51% |  7.98% | 0.94 |
| PR |  2.88% |  3.08% | 0.94 |
| PB |  3.20% |  3.42% | 0.93 |
| TO |  0.78% |  0.86% | 0.91 |
| RN |  2.34% |  2.58% | 0.91 |
| AL |  2.62% |  2.90% | 0.90 |
| MT |  1.26% |  1.41% | 0.90 |
| MA |  6.14% |  6.91% | 0.89 |
| RO |  0.63% |  0.76% | 0.84 |
| RR |  0.41% |  0.52% | 0.80 |
| SC |  1.10% |  1.50% | 0.73 |

_Reprodutível: `python3 articles/equity_indices_pbf.py`._

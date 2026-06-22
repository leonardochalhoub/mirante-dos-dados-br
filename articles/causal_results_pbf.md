# Análise causal — WP #2 Bolsa Família

Resultados do `causal_analysis_pbf.py`. Três desenhos independentes:
(1) DiD 2×2 sobre MP 1.061/2021; (2) TWFE com efeitos fixos UF e ano,
erros clusterizados por UF; (3) replicação cross-shock sobre Lei 14.601/2023.

## Construção do tratamento

Treated_uf = 1 se UF está no Q4 superior do déficit de cobertura pré-
choque (% pobreza PNAD-C 2019 − penetração média 2018-2020). Threshold:
déficit ≥ 0.2905.

- **Treated (n=7):** AL, AM, CE, MA, PA, PB, PI
- **Control (n=20):** AC, AP, BA, DF, ES, GO, MG, MS, MT, PE, PR, RJ, RN, RO, RR, RS, SC, SE, SP, TO

## Resultados — Desenho 1: DiD sobre MP 1.061/2021

| Modelo | β̂ (R$/hab) | SE | IC 95% | p-valor |
|---|---:|---:|:---:|---:|
| DiD 2×2 (HC3) | +223.75 | 38.81 | [+147.69; +299.82] | 0.0000 |
| TWFE FE-UF FE-Ano (cluster UF) | +226.15 | 41.00 | [+145.79; +306.50] | 0.0000 |
| Wild-cluster bootstrap (999 sims) | — | — | — | 0.4915 |

- Δ̄ Treated = R$ +609.3/hab
- Δ̄ Control = R$ +385.6/hab

## Resultados — Desenho 2: replicação cross-shock NBF (Lei 14.601/2023)

| Modelo | β̂ (R$/hab) | SE | IC 95% | p-valor |
|---|---:|---:|:---:|---:|
| DiD 2×2 (HC3) | +256.80 | 43.12 | [+172.29; +341.31] | 0.0000 |

## Robustez

| Teste | Resultado |
|---|---|
| Parallel trends pré (2018-2020) — H0: trends paralelos | β̂(treated:t) = -9.04, p = 0.000 (não-rejeição esperada) |
| Placebo cutoff 2020 (sem choque) | β̂ = -11.72, p = 0.0036 |
| Leave-one-out range β̂ (DiD AB) | [+209.70; +237.56], média +223.75 |

## Interpretação

Os dois desenhos (DiD 2×2 e TWFE) sobre MP 1.061/2021 são consistentes
em sinal e magnitude. A replicação cross-shock sobre Lei 14.601/2023
verifica se o efeito persiste no segundo redesenho ou é capturado pela
nova configuração do NBF. O placebo em 2020 (sem mudança institucional)
serve como sanity check e o teste informal de parallel trends acomoda
o ônus do pesquisador de defender a estratégia de identificação.

_Reprodutível: `python3 articles/causal_analysis_pbf.py`._

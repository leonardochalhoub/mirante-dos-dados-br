# Análise Causal — Resultados

## Modelo 1: DiD 2×2, ΔRM/Mhab

- Treatment effect (β): **-2.321 RM/Mhab**
- Std error (HC3): 1.757
- t-stat: -1.321, p-valor: 0.187
- IC 95%: [-5.764, 1.123]

## Modelo 2: DiD 2×2, ΔNeuro-DP/Mhab

- Treatment effect (β): **-13.293 units/Mhab**
- p-valor: 0.075
- IC 95%: [-27.906, 1.320]

## Modelo 3: TWFE rm_pm ~ Post×Treated + UF_FE + Year_FE

- post_treated β: **-1.9831**
- Std error (cluster UF): 1.2548
- p-valor: 0.1140
- IC 95%: [-4.4425, 0.4763]
- R²: 0.942, n=351
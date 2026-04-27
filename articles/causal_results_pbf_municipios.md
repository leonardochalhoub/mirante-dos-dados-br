# WP #7 · Análise Causal Municipal — Resultados

Subset: **fallback** (5571 munis × 13 anos = 72423 obs).
Tratamento: pobreza_2010 ≥ p75 ∧ penetração_2018-20 ≤ p25.
  - treated: 1393
  - control: 4178

## DiD 2×2 — MP 1.061/2021
- ΔT = +458.31 R$/hab
- ΔC = +252.97 R$/hab
- DiD = **+205.34 R$/hab** IC95% [201.24; 209.32]; p = 0.0000

## DiD 2×2 — Lei 14.601/2023
- DiD = **+349.45 R$/hab** IC95% [343.94; 355.15]; p = 0.0000

## TWFE μ-clustered
- β̂ = +296.57 R$/hab (SE = 2.56, t = 115.73)
- n_obs = 44568, k_munis = 5571

## Conley HAC
- h = 50 km → SE(β̂) = 10.86
- h = 100 km → SE(β̂) = 20.15
- h = 200 km → SE(β̂) = 36.52
- h = 400 km → SE(β̂) = 63.45
- h = 800 km → SE(β̂) = 101.72
- h = 1600 km → SE(β̂) = 149.22

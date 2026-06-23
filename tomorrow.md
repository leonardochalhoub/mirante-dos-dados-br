# WP#10 — doctoral upgrade (v1.2): TOMORROW

Goal: lift **WP#10 itself** (not a new WP) to **doctoral-publishable**. Council is unanimous Mestrado now (Finanças 83 · Design 88 · Admin 87 · Eng 62 · avg ~80). The gate to doctoral = **causal identification** of employment→PBF + classical benchmarks + calibrated uncertainty + engineering rigor.

Article: `articles/bolsa-familia-previsao.tex` (44pg, compile with `tectonic`).
Study repo (separate): `/home/leochalhoub/professional-presentations/demo/`.
Mirante repo clean at commit `754d5e4`. "Mirante" only in reproducibility footnote. AI disclosure (Claude Opus 4.8) stays honest.

---

## 0. First thing — quota & quick wins (offline, no Databricks)
- [ ] Run the already-written rigor module:
      `cd /home/leochalhoub/professional-presentations/demo && python3 doctoral_analysis.py`
      → writes `articles/data/pbf-forecast/{doctoral_stats.json, conformal_band.csv}`.
      Gives: **clustered-by-UF SE** of the −0.36 FE slope (Finanças P2), **ETS+SARIMA national benchmarks** (Finanças P1), **split-conformal band** (Finanças P3), **Mincer–Zarnowitz + Diebold–Mariano** (Finanças P4). Sanity-check the numbers print sensibly.

## 1. KEYSTONE — causal identification (needs Databricks reset)
- [ ] Pull RAIS **sectoral** panel `silver.rais_panel` (has `muni, cnae2, ano, n_vinculos_ativos`) for base year (2013) + end (2024). Write `demo/fetch_bartik.py`.
- [ ] Build **shift-share / Bartik instrument**: B_c = Σ_s (sector s share of muni c employment at 2013) × (national leave-one-out growth of sector s, 2013→2024).
- [ ] First stage: Δlog(emp)_c ~ B_c + controls → report **first-stage F** (want >10). Reduced form + **2SLS**: Δlog(PBF coverage)_c on instrumented Δlog(emp)_c, **clustered SE by UF**.
- [ ] Diagnostics: first-stage F, overid not applicable (just-identified), optionally Rotemberg weights. Cite Goldsmith-Pinkham, Sorkin & Swift (2020, AER).
- [ ] New article section **"Identificação causal: o efeito do emprego formal sobre a demanda por transferência"** + 1–2 figures (first stage, 2SLS effect). This is what makes it doctoral — frame as identified causal effect (with the Bartik exogeneity assumption stated).

## 2. Classical benchmarks — finish
- [ ] National ETS/SARIMA done in `doctoral_analysis.py`. Consider a **municipal head-to-head**: re-run C++ emitting per-(muni,comp,horizon) predictions, then ETS/seasonal-naive on same sample. Add a benchmarks table to the article.

## 3. Calibrated uncertainty
- [ ] Replace the "informal band" figure/table with the **conformal band** (`conformal_band.csv`) — update `build-figures-pbf-forecast.py` fig01 + analysis; keep coverage caveat (12-month calibration set).

## 4. Engineering rigor (Eng chair, get 62 → 80+)
- [ ] Clarify in §4: forward projection uses ALL observed data (no held-out future → not leakage); backtest is strictly train-only. (Or add `cutoff` param to `load_series` for a leak-free variant + state it.)
- [ ] Add `demo/tests/`: (a) determinism (two runs, same `metrics.json` hash); (b) finite-difference gradient check vs `accumulate_grad` (tol 1e-5); (c) no-leak normalization test (build_dataset stats only use comp<CUTOFF).
- [ ] `train.cpp`: write `training_log_h{H}.csv` for ALL horizons (not just H=12).
- [ ] CI workflow: compile C++, run on sample, compare hash.

## 5. NEW — real spending in R$ 2021 (IPCA-deflated, à la WP#2)
- [ ] Panel has `total_reais` (nominal). Deflate to **R$ 2021** using IPCA, reusing WP#2's approach: `pipelines/notebooks/silver/ipca_deflators_2021.py` (+ `data/fallback/` IPCA if offline). 
- [ ] Use it to: (a) show **real spending** trajectory alongside the caseload (new figure / national table column), and (b) make the **MAPE→R$** translation rigorous (real R$ 2021, not "illustrative R$700"). Ties the cost equation custo = caseload × benefício to actual deflated values.
- [ ] Keep the caseload (count) as the primary forecast target — deflation is for the fiscal-reading layer only.

## 6. Reframe to doctoral + positioning (Admin chair)
- [ ] Move the **R$ result into the abstract**; give the **causal agenda/finding its own prominence** in conclusions (not buried in extensions).
- [ ] Add clustered SE to the −0.36 in §3.3 (from doctoral_stats.json).
- [ ] Add benchmarks + conformal + MZ/DM tables/appendix.
- [ ] Consider retitle to foreground the causal contribution.
- [ ] Mint a **Zenodo DOI** for citability (Admin priority).

## 7. Close
- [ ] Recompile (tectonic), verify pages/refs, sync PDF to `app/public/articles/`, regenerate figures.
- [ ] Re-run the 4-chair council to confirm the jump toward doctoral.
- [ ] Commit + push.

---
**Open question for Leo:** how far on the municipal SARIMA/ETS head-to-head (needs C++ re-run with per-muni preds) vs. national-only benchmark? And confirm Bartik base year (2013 vs 2010) and outcome window (2013→2024 long-difference).

# Camada de ML — WP#2 Bolsa Família

Gerado por `ml_pbf.py`. Unidade: 27 UFs no exercício 2024. Features do BF (penetração, per capita, per beneficiário) testadas como *proxy* de pobreza (PNAD-C 2019) e desenvolvimento (IDH-M 2010).

N = 27 UFs.

## 1. Correlações de Pearson
- r(penetracao, pobreza) = +0.971
- r(penetracao, idhm) = -0.881
- r(pbf_pc, pobreza) = +0.971
- r(pbf_pc, idhm) = -0.877

## 2. Regressão log–log (pobreza ~ penetração)
- log(pobreza) = +0.714 + +1.051·log(penetração)
- elasticidade β1 = +1.051 (p = 3.79e-17)
- R² = 0.944  | R² ajustado = 0.942
- Leitura: +1% na penetração associa-se a +1.05% na taxa de pobreza.

## 3. Regressão (IDH-M ~ penetração)
- IDH-M = +0.8109 -0.00837·penetração
- β1 = -0.00837 (p = 1.32e-09) | R² = 0.776
- Leitura: cada +1 p.p. de penetração associa-se a -0.0084 no IDH-M.

## 4. Clustering K-means (não supervisionado)
- Silhouette: k=2: 0.695, k=3: 0.562, k=4: 0.451  → escolhido k=2
  - Cluster 0 (n=13): pobreza méd 17.2%, IDH-M 0.745, penetração 7.8%, per capita R$ 460 | UFs: DF, ES, GO, MG, MS, MT, PR, RJ, RO, RS, SC, SP, TO
  - Cluster 1 (n=14): pobreza méd 41.8%, IDH-M 0.667, penetração 17.3%, per capita R$ 1088 | UFs: AC, AL, AM, AP, BA, CE, MA, PA, PB, PE, PI, RN, RR, SE

## 5. Modelo supervisionado — prever pobreza só com features do BF
- Regressão linear: R²(LOO) = +0.934 | MAE = 2.61 p.p.
- Random Forest: R²(LOO) = +0.916 | MAE = 3.17 p.p.
- Importância (Random Forest): penetração 0.50, per capita 0.47, per beneficiário 0.03

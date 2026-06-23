# Working Paper #10 — Previsão da Carga de Casos do Bolsa Família

Versionamento semântico: **MAJOR.MINOR.PATCH**.
- **MAJOR**: mudança de tese/escopo ou reescrita estrutural.
- **MINOR**: nova análise, seção, figura ou resultado (retrocompatível).
- **PATCH**: correções de texto, números, tipografia, bugs de figura.

## v1.0.0 — 23 de junho de 2026
Primeira versão pública (doutorado-publicável; parecer do Conselho do Mirante: média 88/100).

- Previsão da carga de casos com perceptrons multicamadas implementados do zero em C++17 (He · ReLU · AdamW), univariado vs. com covariáveis (população IBGE + emprego formal RAIS).
- Avaliação fora do tempo (alvos de 2025, ~66 mil previsões/horizonte), bootstrap pareado + Wilcoxon, projeção nacional até 2028.
- Benchmarks clássicos ETS e SARIMA (nacional e municipal): o modelo global vence em todos os horizontes.
- Identificação causal por instrumento shift-share (Bartik) com pesos de Rotemberg e testes de placebo (evidência sugestiva, honestamente rebaixada).
- Banda de predição conforme; testes de Mincer-Zarnowitz e Diebold-Mariano.
- Deflação IPCA → R$ 2021: decomposição custo = carga × benefício (gasto real R$41→144 bi conduzido pelo benefício, não pela carga).
- 52 páginas, 22 figuras, padrão ABNT. Teste de unidade do motor (gradient check 7,5e-10).

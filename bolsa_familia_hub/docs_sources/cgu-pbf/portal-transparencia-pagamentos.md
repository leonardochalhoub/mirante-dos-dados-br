# Portal da Transparência (CGU) — Dataset de Pagamentos do Bolsa Família

> Fonte: https://portaldatransparencia.gov.br/download-de-dados/bolsa-familia-pagamentos
> Citado em `articles/wp2-ppp.references-abnt.md`: CGU — CONTROLADORIA-GERAL DA UNIÃO. Portal da Transparência: microdados de pagamentos do Bolsa Família, Auxílio Brasil e Novo Bolsa Família. 2025.

## Estrutura e acesso

Disponível na seção "Dados Abertos" do Portal da Transparência. Arquivos obtidos selecionando exercício (ano) e mês. Nomenclatura padrão: `BolsaFamilia_Pagamentos`, com estrutura documentada em dicionário de dados dedicado.

## Periodicidade

- Granularidade: mensal
- Múltiplos exercícios (anos) disponíveis
- Cobertura: Bolsa Família (2013-2021), Auxílio Brasil (2021-2023), Novo Bolsa Família (2023-presente) — três regimes de nomenclatura para o mesmo programa contínuo de transferência de renda

## Acesso técnico

Além do download direto (ZIP por mês/ano), o Portal oferece API de Dados para acesso programático.

## Relação com o pipeline do Mirante

`pipelines/notebooks/ingest/cgu_pbf_zips.py` baixa esses ZIPs por faixa de anos (`pbf_years=2013-2021, aux_years=2021-2023, nbf_years=2023-2026`) — a unificação dos três regimes em uma única tabela contínua (`bronze.pbf_pagamentos` → `gold.pbf_estados_df`) é uma decisão de modelagem deste projeto, não do dataset-fonte (que trata os três como programas nominalmente distintos). O CSV bronze usa `codigo_municipio_siafi` (4-6 dígitos), não o código IBGE de 7 dígitos — daí o join com `silver.populacao_municipio_ano` via `(uf, nome_municipio normalizado)` em vez de código direto.

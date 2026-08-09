# SIDRA/IBGE — Tabela 6579: População Residente Estimada

> Fonte: https://sidra.ibge.gov.br/tabela/6579
> Citado em `articles/wp2-ppp.references-abnt.md`: IBGE. SIDRA: Tabela 6579: população residente estimada. 2024.

## O que a tabela mede

População residente estimada, catalogada na seção "População" do SIDRA, vinculada ao módulo EstimaPop (Estimativas de População).

## Cobertura geográfica

O SIDRA permite download de recortes territoriais em múltiplos níveis administrativos (Brasil, UF, município).

## Relação com o pipeline do Mirante

`pipelines/notebooks/ingest/ibge_populacao.py` → `bronze.ibge_populacao_raw` → `silver.populacao_uf_ano` / `silver.populacao_municipio_ano` é a dimensão populacional compartilhada usada por **todo** o pipeline gold que calcula métricas per capita — não só PBF (`pbfPerCapita`), mas também RAIS e outras verticais. É a razão pela qual `gold.pbf_estados_df` faz join com `silver.populacao_uf_ano` (ver `pipelines/notebooks/gold/pbf_estados_df.py`).

## Nota metodológica

O IBGE não detalha nesta página a metodologia de estimativa; para maior rigor, publicações complementares do EstimaPop deveriam ser consultadas antes de usar esses números para afirmações causais fortes no artigo — ponto já levantado pelo Conselheiro de Finanças em outras revisões deste repositório.

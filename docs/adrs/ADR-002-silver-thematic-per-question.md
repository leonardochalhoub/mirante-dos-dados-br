# ADR-002 · Silver TEMÁTICA por questão de pesquisa, não silver ampla

**Status:** Accepted (2026-04-28)
**Deciders:** Leonardo Chalhoub + Conselho do Mirante (eng-software, finanças)
**Supersedes:** —

## Contexto

Padrão Medallion clássico (bronze → silver → gold) sugere que silver é uma camada **horizontal**: 1 silver por entidade canonical (ex.: `silver.rais_vinculos_clean`) com TODAS as variáveis, e gold agrega para questões específicas.

Aplicando isso ao RAIS, a primeira tentativa foi `silver.rais_uf_ano` — agrega vínculos ativos, massa salarial e share Simples por UF×ano. Cobre dimensão geográfica + temporal, não cobre setorial, demográfica ou de motivo de desligamento.

O Conselho do Mirante (2026-04-28) audit identificou que **nenhuma das 6 questões causais abertas** (Reforma Trabalhista 2017, BEm COVID, Bolsa Família, Cruzado 1986, Boom Commodities, Trabalho Intermitente) pode ser respondida com a silver atual:

- Reforma 2017: precisa `tempo_emprego × cnae × motivo_desligamento`
- **BEm COVID**: precisa `município × cnae2 × ano × {ativos, demissões SJC, massa salarial, sexo, escolaridade}`
- Bolsa Família: precisa `município × ano × sexo × idade × tempo_emprego`
- Cruzado 1986: precisa `cnae × uf × ano × {ativos, admissões}`

Construir UMA silver com todas essas colunas + granularidade × dimensões viraria um cubo gigante (~50M linhas) com a maioria das células vazias e queries ineficientes. Pior: silver "ampla" tipicamente vira silver "incompleta" — alguma combinação esquecida quebra o paper.

## Decisão

**Adotamos silver TEMÁTICA: 1 silver por questão de pesquisa**, cada uma desenhada com:

- **Janela temporal mínima** suficiente pra responder a questão (não toda a série 1985-2024)
- **Grain otimizado** pra a estratégia causal (DiD, RDD, IV, Synthetic Control)
- **Outcomes específicos** (não toda variável imaginável)
- **Variáveis de controle relevantes** (não toda variável imaginável)
- **Documentação UC** com a estratégia identificacional pretendida

Convenção de nomenclatura:

```
mirante_prd.silver.rais_<questao>_<grain>
```

Exemplos:

- `silver.rais_bem_panel` — município × cnae2 × ano (2017-2022) → DiD do BEm
- `silver.rais_cruzado_setor_uf` — cnae × uf × ano (1985-1989) → análise descritiva do choque do Cruzado
- `silver.rais_reforma_2017_panel` — empresa × ano (2014-2020) → DiD da Reforma Trabalhista
- `silver.rais_bf_municipio` — município × ano (2003-2014) → RDD da linha de elegibilidade do Bolsa Família

## Consequências

### Positivas

- **Cada silver tem propósito claro e testável** — `tests/test_rais_<questao>_silver.py` valida exatamente o que aquele paper precisa
- **Performance**: cada silver é ~1-3M linhas (manageable), não 50M+ (cubo amplo)
- **Iteração rápida**: pesquisador descobriu nova hipótese? Cria nova silver. Não precisa esperar refactor da silver canônica.
- **Documentação granular**: cada silver vira um pre-registration plan implícito — "esses são os dados, esses os outcomes, essa é a janela, esse é o grain"
- **Audit trail por paper**: working paper cita `silver.rais_bem_panel@v3` específico, não silver-canônica-onde-tudo-mudou-cross-year.

### Negativas

- **Duplicação**: variáveis comuns (sexo, idade, escolaridade) aparecem em múltiplas silvers. Storage cost. Aceito porque storage de silver é ~10-50 MB por questão (vs ~22 GB da bronze).
- **Drift cross-silver**: se a definição de "vínculo ativo" mudar, precisa mudar em N silvers. Mitigação: macros/funcs compartilhadas em `pipelines/notebooks/_lib/rais_common.py` (futuro).
- **Onboarding**: novo pesquisador precisa entender quais silvers existem. Mitigação: index em `docs/silvers/RAIS_silvers_index.md` (futuro).

### Quando NÃO adotar (anti-pattern)

- Se 5+ questões compartilham EXATAMENTE o mesmo grain (ex.: município × cnae × ano), aí faz sentido ter UMA silver canônica. Mas no RAIS isso não é o caso — cada questão tem grain próprio.
- Se a silver vira "playground" pra exploração ad-hoc (não serve uma questão definida), aí volta a ser silver ampla. Use o gold pra exploração e silvers temáticas pra papers.

## Compromisso de manutenção

Cada silver temática DEVE ter:

1. **Header MAGIC com %md** explicando: questão de pesquisa, janela, grain, outcomes, estratégia causal pretendida, limitações
2. **Table COMMENT** verboso (≥ 200 chars) com USO PRIMÁRIO + LIMITAÇÕES declaradas
3. **TAGs UC obrigatórias**: `layer=silver`, `domain=trabalho`, `source=mte_pdet_rais`, `pii=indirect`, `grain=<grain>`, `janela=<min_max>`, `questao_causal=<id>`, `uso_primario=<metodo>`
4. **Column COMMENTs** em todas as colunas (não só as obvious — incluindo metadata `_silver_built_ts`)
5. **DQ gate pós-build**: cobertura temporal, cobertura UF/grain, sanity de magnitudes
6. **Test pytest correspondente** em `tests/test_rais_<questao>_silver.py`

## Referências

- Conselho 2026-04-28 — pareceres eng-software + finanças unanimemente recomendaram silver-por-questão
- Bronze RAIS íntegra: ADR-001
- Primeiro silver temática: `pipelines/notebooks/silver/rais_bem_panel.py`

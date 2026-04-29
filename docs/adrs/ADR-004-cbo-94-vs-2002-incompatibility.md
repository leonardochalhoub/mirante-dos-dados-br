# ADR-004 · CBO 1994 ≠ CBO 2002 · incompatibilidade cross-era

**Status:** Accepted (constraint codebook PDET, irreversível)
**Deciders:** PDET/MTE; Mirante registra a consequência metodológica
**Supersedes:** —

## Contexto

CBO = Classificação Brasileira de Ocupações. PDET usou DUAS taxonomias incompatíveis:

- **CBO 1994** (5 dígitos): vigente 1985–2002. ~2.350 códigos. Estrutura "Grande Grupo / Sub-Grupo / Família / Ocupação / Especialização".
- **CBO 2002** (6 dígitos): vigente 2003+. ~2.500 códigos. Estrutura "Grande Grupo / Sub-Grupo Principal / Sub-Grupo / Família / Ocupação".

A bronze tem AMBOS:
- `cbo_94_ocupacao` (era1+2, 1985-2002): código de 5 dígitos
- `cbo_ocupacao` (era1+2, 2003+, .txt): código CBO 2002 6 dígitos
- `cbo_2002_ocupacao_codigo` (era3, .COMT 2023+): código CBO 2002 6 dígitos com sufixo

A mudança NÃO é uma simples re-numeração — várias ocupações foram **desagregadas**, **reagrupadas** ou **eliminadas** entre as duas taxonomias.

Exemplos de incompatibilidade:

| CBO94 | CBO94 nome | CBO2002 | CBO2002 nome |
|---|---|---|---|
| 39105 | Programador de computador | 212405, 212410, 212415, 212420 | Engenheiro de software, Tecnólogo, Programador especializado, etc. |
| 41710 | Vendedor pracista | 521110 | Vendedor (no comércio em geral) |
| 23105 | Médico | 223110, 223115, 223120, ... | Subdivido em 50+ especialidades |

**Mapeamento "1-pra-1" não existe** — a literatura usa "tabelas de equivalência" (DIEESE, IPEA) que aplicam pesos probabilísticos de mapeamento.

## Decisão

`bronze.rais_vinculos` PRESERVA AMBOS os códigos CBO sem fazer harmonização. Cabe ao SILVER decidir como tratar.

### Política de harmonização para silver

**Para questões de pesquisa que cruzam fronteira 2002/2003**, o silver DEVE optar por uma de 3 estratégias declaradas:

#### Estratégia A · Restringir janela a CBO2002-only (2003+)

Mais simples, mais conservadora. Janelas pós-2003 (BEm 2017-2022, Reforma 2017, Boom Commodities 2003-2014) cabem nessa estratégia.

**Quando usar:** sempre que a janela permitir. **Default recomendado.**

#### Estratégia B · Mapear CBO94 → CBO2002 com tabela DIEESE

DIEESE publica tabela de equivalência probabilística (cada CBO94 mapeia pra 1+ CBO2002 com peso). Aplicar a tabela na transformação bronze → silver, declarar limitação no manuscrito.

**Quando usar:** análises cross-1985-2024 ininterruptas (ex.: feminização cross-era).

**Limitação obrigatória declarada:** "Códigos CBO94 (1985–2002) foram mapeados para CBO2002 via tabela DIEESE 2010 com pesos probabilísticos. O mapeamento é imperfeito; ocupações com mais granularidade em CBO2002 (ex.: medicina) podem aparecer agregadas no período pré-2003."

#### Estratégia C · Análise paralela em ambas as taxonomias

Rodar regressões duplicadas — uma com CBO94 (1985–2002), outra com CBO2002 (2003+) — e comparar magnitudes. Se direção do efeito é estável, conclusão mantida; se diverge, declara que cross-era não é interpretável.

**Quando usar:** cross-1985-2024 com poder estatístico suficiente em cada janela.

### Que CBO usar em silver?

```python
# Estratégia A (default — janela pós-2003)
EXPR_CBO = COALESCE(cbo_2002_ocupacao_codigo, cbo_ocupacao)

# Estratégia B (mapeamento DIEESE)
EXPR_CBO = COALESCE(cbo_2002_ocupacao_codigo, cbo_ocupacao,
                    map_cbo94_to_2002(cbo_94_ocupacao))

# Estratégia C (paralelo)
EXPR_CBO_PRE  = cbo_94_ocupacao        # filter ano <= 2002
EXPR_CBO_POST = COALESCE(cbo_2002_ocupacao_codigo, cbo_ocupacao)  # filter ano >= 2003
```

## Consequências

### Positivas

- **Bronze fiel à fonte**: nenhuma harmonização "silenciosa" que apague a transição taxonômica.
- **Silver explicita escolha**: cada paper declara qual estratégia usou; reviewer pode auditar.
- **Análises pós-2003 são clean**: ~80% das questões causais relevantes (BEm, Reforma 2017, etc.) ficam dentro da janela CBO2002-only.

### Negativas

- **Análises 40-anos requerem trabalho extra** (mapping DIEESE ou paralelo).
- **CBO94 → CBO2002 mapping não é replicável de forma simples** — requer baixar tabela DIEESE (não está em pacote Python padrão), aplicar como look-up table, declarar metodologia.
- **Algumas análises de classe ocupacional (ex.: ISCO-08 cross-country)** precisam mapeamento adicional CBO2002 → ISCO-08, multiplicando incerteza.

### Trade-offs explícitos

- **Não harmonizamos no bronze** porque (a) bronze é STRING-ONLY, sem business logic; (b) harmonização inadequada apaga informação que silver/paper podem precisar; (c) versões diferentes de mapping (DIEESE 2002, 2010, 2018) levariam a bronze incompatíveis cross-snapshot.
- **Não rejeitamos CBO94** mesmo que CBO2002 seja "padrão atual". Rejeitar CBO94 = perder 1985-2002 = perder o Cruzado, Plano Real, FHC. Conservar é a escolha certa.

## Casos práticos no Mirante

| Questão | Janela | Estratégia recomendada |
|---|---|---|
| BEm COVID (2017-2022) | CBO2002-only | A (default) |
| Reforma Trabalhista (2014-2020) | CBO2002-only | A |
| Boom Commodities (2003-2014) | CBO2002-only | A |
| Cruzado 1986 (1985-1989) | CBO94-only | A com CBO94 |
| Mobilidade ocupacional 1985-2024 | mista | C (paralelo) ou B (mapping) |
| Feminização da força de trabalho 1985-2024 | mista | B (mapping DIEESE) |

## Referências

- DIEESE, "CBO 2002 vs CBO 94: tabela de equivalência" (não mais disponível online; backup interno em `docs/refs/dieese_cbo94_to_2002.csv` — TODO ingestar)
- IBGE — [Tabela de conversão CBO 1994 - 2002](https://www.ibge.gov.br/estatisticas/sociais/trabalho.html)
- IPEA Data — base de equivalência ocupacional
- Conselho 2026-04-28 finanças P5: "CBO94 ≠ CBO2002 (comparação cross-era de ocupação está errada sem tabela de equivalência DIEESE)"
- Bronze schema: `cbo_94_ocupacao`, `cbo_ocupacao`, `cbo_2002_ocupacao_codigo`

# ADR-005 · Grau de Instrução · drift de codebook 1985→2005→2023

**Status:** Accepted (constraint codebook PDET)
**Deciders:** PDET/MTE
**Supersedes:** —

## Contexto

A variável "Grau de Instrução" do trabalhador no RAIS sofreu **três regimes de codebook**:

### Regime 1: 1985–2005 ("Grau Instrução 2005-1985")

Coluna `grau_instrucao_2005_1985`. Códigos:

| Código | Significado |
|---|---|
| 01 | Analfabeto |
| 02 | Até 5ª incompleta (Ensino Fundamental incompleto) |
| 03 | 5ª completa fundamental |
| 04 | 6ª a 9ª fundamental |
| 05 | Fundamental completo |
| 06 | Médio incompleto |
| 07 | Médio completo |
| 08 | Superior incompleto |
| 09 | Superior completo |
| 10 | Mestrado / Doutorado |

Total: 10 categorias.

### Regime 2: 2006–2022 ("Escolaridade após 2005")

PDET trocou em 2006 — coluna `escolaridade_apos_2005` (sem sufixo `_codigo` em era1+2 .txt). Códigos:

| Código | Significado (PDET 2006-2022) |
|---|---|
| 01 | Analfabeto |
| 02 | Até 5ª incompleta |
| 03 | 5ª completa |
| 04 | 6ª a 9ª |
| 05 | Fundamental completo |
| 06 | Médio incompleto |
| 07 | Médio completo |
| 08 | Superior incompleto |
| 09 | Superior completo |
| 10 | Mestrado |
| 11 | Doutorado |

Total: 11 categorias. Diferença chave: **mestrado e doutorado virou 2 códigos separados** (10 e 11). Códigos 01-09 são compatíveis 1-pra-1.

### Regime 3: 2023+ (.COMT, "Escolaridade após 2005 - Código")

Coluna `escolaridade_apos_2005_codigo`. **Mesmos códigos do regime 2** (1-11). Só mudou o nome da coluna (sufixo `_codigo`).

## A confusão na bronze

Bronze RAIS preserva os 3 nomes coexistindo:
- `grau_instrucao_2005_1985` (era1+2: 1985-2005, mas registros pós-2005 podem ter populado essa coluna por alguns anos de transição)
- `escolaridade_apos_2005` (era2: 2006-2022)
- `escolaridade_apos_2005_codigo` (era3: 2023+)

Coalesce ingênua é INCORRETA: códigos 01-09 são compatíveis cross-regimes, mas códigos 10 e 11 mudaram de significado:

- Regime 1: `10` = Mestrado E Doutorado juntos
- Regime 2/3: `10` = Mestrado, `11` = Doutorado

## Decisão

`bronze.rais_vinculos` PRESERVA AMBOS os campos sem harmonizar. Cabe ao silver decidir.

### Política de harmonização para silver

Para silver que use Grau de Instrução, criar 2 columns:

```python
# Coluna primária: 4 categorias agregadas (compatível cross-regimes)
EXPR_ESCOL_CAT = F.when(F.lpad(F.trim(escol).cast("string"), 2, "0").isin("01", "02", "03", "04"),
                        "fund_inc")
                  .when(F.lpad(F.trim(escol).cast("string"), 2, "0").isin("05", "06"), "fund_med_inc")
                  .when(F.lpad(F.trim(escol).cast("string"), 2, "0") == "07", "med_completo")
                  .when(F.lpad(F.trim(escol).cast("string"), 2, "0").isin("08", "09"), "sup")
                  .when(F.lpad(F.trim(escol).cast("string"), 2, "0").isin("10", "11"), "pos_grad")

# Coluna secundária: 11 categorias (apenas compatível regime 2+3)
EXPR_ESCOL_CODE = F.lpad(F.trim(escol).cast("string"), 2, "0")
# Aplicável APENAS em janela ano >= 2006. Para ano <= 2005, nullif.
```

**4 categorias é o nível de agregação onde os 3 regimes são compatíveis 1-pra-1.** Pra qualquer análise que precise distinguir mestrado de doutorado, restringir janela a 2006+.

### Regra de validação no silver

```python
# Sanity check: distribuição cross-anos da categoria pos_grad
silver.groupBy("ano").agg(
    F.avg(F.when(F.col("escol_cat") == "pos_grad", 1).otherwise(0)).alias("pct_posgrad")
).show()
# Espera-se trajetória monotônica suave (~5-10% em 1985 → ~15-25% em 2024)
# Se há salto entre 2005 e 2006 maior que 2 pontos percentuais, há problema
```

## Consequências

### Positivas

- **Análises 4-categorias funcionam cross-1985-2024**.
- **Análises pós-2006 podem distinguir mestrado vs doutorado**.
- **Não há perda de informação na bronze** — silver escolhe granularidade conforme o paper.

### Negativas

- **Análises de pós-graduação no Brasil pré-2006 são impossíveis com RAIS** (mestrado e doutorado vêm agregados).
- **Necessário declarar a escolha de granularidade em LIMITAÇÕES** de qualquer paper que use educação.

### Risco caso a regra não seja seguida

Audit de silver_rais_uf_ano antes desta ADR (no panorama §6) mostrou:
- 2006-2022: pct_posgrad = 0.0% (porque o silver não populou `escolaridade_apos_2005`)
- 2023-2024: pct_posgrad = 24.4% (porque pegou regime 3 sem harmonização)

Resultado: o panorama afirmou que "mestrado+doutorado triplicou de 7,4% pra 24,4%". **Esse pulo de 17 pontos é PARCIALMENTE artefato de codebook**, não trajetória real. Em silver harmonizada (4-categorias), a categoria `pos_grad` provavelmente cresce de ~7% (1985) pra ~15-20% (2024), não 24%.

## Padrão de declaração em manuscritos

> **VARIÁVEL EDUCAÇÃO:**
> Harmonizamos os 3 regimes de codebook PDET (1985–2005, 2006–2022, 2023+) em
> 4 categorias agregadas: fundamental incompleto, fundamental/médio incompleto,
> médio completo, superior, pós-graduação. Em janelas restritas a 2006+,
> reportamos também a granularidade 11-níveis original. Apesar da harmonização,
> mudanças de definição PDET podem introduzir descontinuidades entre 2005 e
> 2006 (mestrado/doutorado separados em códigos distintos a partir de 2006).
> Recomendamos cautela ao interpretar trajetórias de pós-graduação cross-2005.

## Referências

- PDET, "Manual de Orientação da RAIS" 2005, 2006, 2023 (versões diferentes do dicionário)
- Bronze schema: `grau_instrucao_2005_1985`, `escolaridade_apos_2005`, `escolaridade_apos_2005_codigo`
- Audit 2026-04-28 panorama §6 — "mestrado+doutorado triplicou" sinalizado como suspeito pelo Conselho

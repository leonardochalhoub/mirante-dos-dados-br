# Architecture Decision Records (ADRs) — Mirante dos Dados

Este diretório registra **decisões arquitetônicas significativas** do Mirante. Cada ADR é um documento curto (1-2 pp) explicando UMA decisão: o contexto, a decisão, e as consequências.

Inspirado em [adr.github.io](https://adr.github.io/) e [Michael Nygard's "Documenting Architecture Decisions"](https://www.cognitect.com/blog/2011/11/15/documenting-architecture-decisions).

## Índice

| ID | Título | Status | Data |
|---|---|---|---|
| [ADR-001](ADR-001-bronze-rais-dual-reader-per-year.md) | Bronze RAIS: leitor dual-format per-year | Accepted | 2026-04-28 |
| [ADR-002](ADR-002-silver-thematic-per-question.md) | Silver TEMÁTICA por questão de pesquisa | Accepted | 2026-04-28 |
| [ADR-003](ADR-003-grain-vinc-only-no-cpf.md) | Grain VINC-only · ausência de CPF na bronze | Accepted | 2026-04-28 |
| [ADR-004](ADR-004-cbo-94-vs-2002-incompatibility.md) | CBO 1994 ≠ CBO 2002 · incompatibilidade cross-era | Accepted | 2026-04-28 |
| [ADR-005](ADR-005-grau-instrucao-codebook-drift.md) | Grau de Instrução · drift de codebook 1985→2005→2023 | Accepted | 2026-04-28 |

## Quando criar uma ADR

- Mudança de arquitetura que afeta múltiplos times/notebooks
- Decisão que tem consequências de longo prazo (>6 meses)
- Decisão que envolve trade-offs não-óbvios
- Decisão que precisa ser revisada ao onboarding de novo dev

## Quando NÃO criar uma ADR

- Mudança trivial de código (ex.: rename de variável)
- Decisão reversível em horas (ex.: ajuste de parâmetro)
- Documentação de funcionalidade (use docstring/README)

## Template

```markdown
# ADR-XXX · Título

**Status:** Proposed | Accepted | Deprecated | Superseded by ADR-YYY
**Deciders:** Nomes
**Supersedes:** —

## Contexto
O problema, restrições, alternativas consideradas.

## Decisão
A escolha feita, em prosa direta.

## Consequências
### Positivas
### Negativas
### Trade-offs explícitos

## Referências
Links, papers, threads de Slack, decisões prévias.
```

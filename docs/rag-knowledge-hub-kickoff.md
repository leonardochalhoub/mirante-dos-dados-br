# RAG Knowledge Hub — proposta de kickoff

**Status:** proposta, não implementada. Escrito numa sessão externa (workshop `w1-llama-index-rag`), a pedido do Leo, pra dar ponto de partida à próxima sessão que for implementar isto no Mirante.

## Objetivo

Aplicar ao Mirante o mesmo padrão de RAG multi-domínio validado no workshop `ws-1-llama-index-rag`: rotear perguntas de negócio entre três motores de busca, cada um no formato certo pro tipo de dado, em vez de forçar tudo em vector search.

## O padrão: Ledger + Memory + Brain

| Domínio | Responde | No workshop | No Mirante |
|---|---|---|---|
| **Ledger** | Números, agregações, top-N | PostgreSQL + NL-to-SQL | **Databricks Unity Catalog**, via SQL Warehouse — provavelmente só as tabelas **Gold** (schema estável, curado; Bronze/Silver são detalhe de implementação que o LLM não deveria ver) |
| **Memory** | Documentos, contexto histórico, decisões | Qdrant (docs de política sintéticos) | `docs/ARCHITECTURE.md`, `docs/adrs/*.md`, `docs/*-spec.md`, Working Papers (`articles/`) — a documentação que já existe e já é publicada |
| **Brain** | Relacionamentos, dependências, impacto | Neo4j (grafo extraído por LLM de texto narrativo) | **Lineage nativo do Unity Catalog** (`system.access.table_lineage`, `system.access.column_lineage`) + dependências declaradas em `pipelines/databricks.yml` (Asset Bundle) — estrutura real, não inferida por LLM |

A diferença chave em relação ao workshop: lá, o Brain foi populado escrevendo texto narrativo pra um LLM extrair ("X depende de Y") porque não existia outra fonte. Aqui **já existe lineage real** no Unity Catalog e dependência real declarada no Asset Bundle — é melhor puxar isso direto via API do que reconstruir com LLM. Mesmo princípio do porquê usar o grafo de issue-links do Jira em vez de LLM, se algum dia entrar uma vertical com Jira.

## O que já existe no repo que ajuda

- **`conselho_mcp/`** já é um MCP server rodando vector search simples (embeddings + chunks) sobre os Working Papers, pro conselho de revisores. É o mesmo padrão de exposição MCP que o novo Knowledge Hub usaria — reaproveitar a estrutura, não reinventar.
- **`docs/adrs/`** já é o formato certo pra registrar as decisões técnicas que essa proposta vai gerar (ex.: "por que Unity Catalog lineage em vez de LLM extraction pro Brain" é candidato a virar `ADR-007`).
- **Disciplina de FinOps** já é parte da cultura do projeto (US$70 lifetime, ~US$0,40/job run) — qualquer ingestão que rode LLM (ex.: se algum dia precisar de extração via LLM em cima de algo sem lineage nativo) precisa entrar nesse mesmo orçamento/instrumentação, não é gratuita como foi no workshop com modelo local de embedding.

## Lições do workshop que valem aqui também

Detalhadas na memória `rag-three-domain-architecture` (sessão do workshop), resumo do que mais importa pro Mirante:

1. **A descrição de cada tool do router é o contrato de roteamento.** Se o Memory ganhar um novo tipo de documento, a descrição da tool precisa mencionar isso explicitamente, ou o router nunca manda pergunta pra lá. Bug real que isso causou no workshop.
2. **Isolar as etapas de ingestão.** Ledger/Memory/Brain devem atualizar independentemente — uma falha no Unity Catalog não pode travar a atualização da documentação no Memory.
3. **Modelo pequeno/gratuito de LLM (se usado pro router) precisa de prompt reforçado** pra não "vazar" texto depois do JSON de decomposição — achado real no workshop, quebrava o parser com erro de "trailing data".
4. **Rate limit de LLM hospedado parece bug de roteamento, mas é infra.** Se o router usar um LLM hospedado (Groq, etc.), checar `x-ratelimit-remaining-tokens` antes de suspeitar de lógica.
5. **Pra número crítico, validar direto na fonte em paralelo ao RAG** — NL-to-SQL pode variar levemente entre chamadas.

## Próximos passos (pra sessão de implementação, dentro deste repo)

1. Confirmar quais tabelas Gold entram no Ledger (schema estável o suficiente pro NL-to-SQL).
2. Testar uma query no lineage do Unity Catalog (`system.access.table_lineage`) pra validar que dá pra construir o grafo do Brain sem LLM.
3. Decidir o vector store do Memory — reaproveitar o approach simples do `conselho_mcp` (embeddings + chunks locais) ou subir algo tipo Qdrant, dependendo de quanto conteúdo vai entrar.
4. Depois de validado, registrar a decisão de arquitetura como ADR novo em `docs/adrs/`.

# Unity Catalog (Databricks)

> Fonte: https://docs.databricks.com/en/data-governance/unity-catalog/index.html

## Modelo de três níveis

Namespacing hierárquico `catalog.schema.object`. Tabelas, views, volumes, funções, modelos e serviços seguem esse padrão de três níveis. No Mirante: `mirante_prd.{bronze,silver,gold}.<tabela>`.

## Governança de metadados

Camada de governança unificada para dados e IA, operando automaticamente em toda interação:
- Controle de acesso automático em consultas e modelos
- Aplicação de permissões via objetos "secureables"
- Políticas baseadas em atributos e filtros de linha/coluna

## Lineage automático

Rastreia automaticamente a linhagem conforme dados e assets de IA são usados — de fontes iniciais até modelos, serviços e dashboards. Exposto via `system.access.table_lineage` / `system.access.column_lineage`.

## Auditoria

Mantém registro completo de todo acesso a dados e atividade do sistema via audit log system table — essencial para conformidade e investigação.

## Tabelas gerenciadas vs. externas

- **Gerenciadas:** ciclo de vida completo controlado pelo Unity Catalog.
- **Externas:** apenas governança, dados residem fora do controle direto do UC.

## information_schema

`system.information_schema.tables` e `system.information_schema.columns` expõem comentários (`COMMENT ON TABLE`/`COMMENT ON COLUMN`) e metadados estruturais via SQL — é a fonte usada por `bolsa_familia_hub/uc_metadata.py` para popular o Memory deste Knowledge Hub com a documentação real das tabelas Bronze/Silver/Gold do PBF.

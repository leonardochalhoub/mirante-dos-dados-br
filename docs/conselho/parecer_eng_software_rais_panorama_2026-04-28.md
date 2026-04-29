# Parecer — Eng. Software & Plataforma de Dados
## Avaliação do estado técnico RAIS no Mirante — pós-WHY decidido

**Versão avaliada:** bronze `mirante_prd.bronze.rais_vinculos` v6 (commit 2158d65, post per-year reader fix) · silver `rais_uf_ano` · gold `rais_estados_ano` · export · DAB `databricks.yml`
**Score atribuído:** B (2,0 pts) — MINOR REVISION (sobe de C+/1,5 pós-fix do separador)
**Histórico:** C+/1,5 (parecer de bronze, 2026-04-28, commit do mesmo dia) → **B/2,0** (este parecer, com WHY decidido e fixes dos Issues A/B/C aplicados)
**Régua:** mestrado stricto sensu · A=3, B+=2,5, B=2, C=1, D=0 · aprovação ≥ 2,0

---

## Veredicto geral

O pipeline está no limiar mínimo de aprovação. A bronze saiu do buraco do Issues A/B/C — dual reader funcionando, DQ gate pós-bronze implementado, UC metadata aplicado. O que segura o score em B (não B+) é a combinação de quatro lacunas que, juntas, impossibilitam publicação peer-reviewed com reproducibility auditável: (1) silver cobre só 27 UFs × N anos em agregado grosseiro, não os 40 anos de séries brutas necessários para qualquer das 6 questões causais do §9 do panorama; (2) zero testes pytest para RAIS (conftest.py tem fixture `rais_gold` mas nenhum `test_rais_*.py` existe); (3) ausência de ADRs formais sobre as 4 decisões de arquitetura críticas que precisam estar documentadas em artigo ou no repositório para que um revisor externo valide a cadeia metodológica; (4) reproducibility de end-to-end — não há snapshot Delta versionado com `VERSION AS OF` citável, nem Zenodo DOI, nem hash de commit em qualquer artefato publicado da vertical RAIS.

O dataset é genuinamente rico e a infraestrutura de bronze está agora defensavelmente sólida. O passo seguinte exige trabalho de silver real — não é cosmético.

---

## 1. Avaliação do estado técnico da bronze pós-fix

### O que agora está correto (diferencial vs parecer anterior)

**Dual reader txt/COMT implementado** (`_read_batch_per_year` + dois checkpoints Auto Loader): a decisão de ler por ano (`_read_batch_per_year`) resolve o problema de header drift cross-ano — o CSV reader de cada ano pega o header do arquivo daquele ano, não do primeiro arquivo de um glob multi-ano. Isso é arquiteturalmente correto para um dataset com schema drift tão profundo (24 colunas em 1985 → 60 colunas em 2023+). A implementação de `unionByName(allowMissingColumns=True)` para reunir os anos sem perder colunas é a abordagem certa.

**DQ gate pós-bronze** (Step 3, linha ~1400): o gate calcula `avg_filled_cols` por `(ano, _source_file)` e falha com `raise RuntimeError` se `< 3.0`. Isso é o que faltava no parecer anterior. É simples, barato (Photon) e detecta silenciosamente o problema do separador errado que passou por duas runs anteriores. A lógica de filtrar `F.col("ano") >= 2018` é razoável — pré-1991 arquivos UF com cabeçalhos esparsos genuínos teriam falso-positivo.

**UC metadata** (Step 4): TAGs de plataforma aplicadas (`layer`, `domain`, `source`, `pii`, `grain`, `format_drift`, `estab_excluded`) + 50+ column COMMENTs verbosos. Idempotente. Esse era o item mais simples de resolver e foi resolvido.

**UniForm Iceberg** (Step 5): habilitado na canônica Delta via `IcebergCompatV2`. Correto para interop sem custo de storage. A sequência de ALTER TABLE em transações separadas (column mapping, DV, UniForm) está na ordem certa — é o `minWriterVersion=5` que habilita column mapping antes de Iceberg.

**ESTAB isolation** (`_filter_vinc` + `pathGlobFilter` + ESTAB_RX): grain agora está garantido por contrato. O filtro duplo (no step 1 via `_is_vinculo_filename` e no step 2 via regex `_source_file`) é redundância defensável — falha-seguro.

### O que ainda é preocupante na bronze

**Issue D fica aberto sem caveat publicado.** SP 1986 em quarentena permanente (`_bad/SP1986_1986.7z`) está documentado no código mas não em nenhum artefato versionável citável por um revisor externo. O panorama menciona ~7-13M linhas ausentes. Para qualquer análise que inclua 1986 — especificamente §9.5 (Plano Cruzado) — o fenômeno que o panorama chama de "queda de 28,6% nos vínculos ativos em 1986" pode ter componente de subregistro SP. Um Working Paper sobre o Cruzado que não mencione explicitamente "SP 1986 ausente por corrupção de arquivo FTP PDET, ~10% do estoque nacional estimado" está exposto a crítica metodológica básica.

**Silver.rais_uf_ano depende da bronze nova mas nunca foi re-executada** em 40 anos inteiros com o dual reader. O panorama cita dados de série que presumivelmente vieram de queries SQL diretas na bronze — não da silver. A silver atual (`pipelines/notebooks/silver/rais_uf_ano.py`) resolve `vl_dez` e `vl_med` via COALESCE de aliases cross-era, mas as medidas de remuneração em SM (salários-mínimos) de 1985-1993 (era1a) não têm equivalente nominal — `vl_remun_dezembro_sm` não existe deflacionado, e o gold deflaciona apenas `vl_remun_dezembro_nom` que só existe em 1994+. Resultado: para os 9 anos do Sarney/Cruzado, a coluna `massa_salarial_2021` na gold é NULL. Isso não está documentado em nenhum COMMENT.

**`_dupN` proliferação não está mapeada na silver.** A silver usa `_coalesce_logical` com listas fixas de aliases. Se `_read_batch_per_year` gerou um `municipio_dup3` (terceira variação de header de município) que não está na lista `LOGICAL_COLS["mun_trab"]` da silver, ele fica silenciosamente descartado. Não há mecanismo que detecte "nova variação de alias não coberta pela lista". Esse é um risco latente de silent data loss pós schema evolution.

---

## 2. Infraestrutura técnica que falta para o Working Paper

### 2.1 Silver: o gap de 1996-2022 e o que a silver atual entrega

A silver atual (`silver.rais_uf_ano`) entrega: `(uf, Ano, n_vinculos_total, n_vinculos_ativos, massa_salarial_dezembro, remun_media_mes, n_estabelecimentos_proxy, share_simples)`. Granularidade UF × Ano. Isso é suficiente para o panorama descritivo (§1-§7) e para análise de trajetória regional (§3).

**Não é suficiente para nenhuma das 6 questões causais do §9** porque todas requerem variáveis adicionais:

| Questão (§9) | Variáveis mínimas para identificação | Na silver atual? |
|---|---|---|
| 9.1 Reforma 2017 | tipo_admissao, tipo_vinculo, motivo_desligamento, ind_trabalho_intermitente | Não |
| 9.2 BEm COVID | vinculo_ativo_31_12 × mes × setor, motivo_desligamento × mes | Não |
| 9.3 BF formalização | sexo_trabalhador × municipio × ano | Não |
| 9.4 Intermitente | ind_trabalho_intermitente × qtd_hora_contr × tempo_emprego | Não |
| 9.5 Cruzado 1986 | cnae × uf × ano (grain fino, não agregado) | Não |
| 9.6 Bartik commodity | cnae × municipio × ano (instrumento shift-share) | Não |

**Isso não é crítica à decisão de começar simples na silver** — é aviso sobre o escopo do que precisa ser construído antes de qualquer das questões causais virar Working Paper. A silver atual serve uma vertical descritiva; não serve econometria.

**Há um bug na silver que precisa de correção antes de publicar qualquer dado:** `n_estabelecimentos_proxy` usa `countDistinct(concat_ws("_", mun_trab, cnae_classe))` como proxy. Isso é conceptualmente errado para grain de vínculo: um município pode ter 10.000 vínculos CNAE 5611 (restaurantes) — `countDistinct(mun+cnae)` conta 1, não 10.000. O nome `n_estabelecimentos_proxy` está documentado no COMMENT como "countDistinct mun_trab+cnae_classe", que é honesto, mas o campo na gold se chama `n_estabelecimentos_proxy` sem qualificação — e o frontend pode interpretar como "número de estabelecimentos", o que é ordens de magnitude errado. Ou remove o campo, ou adiciona sufixo `_mun_cnae_pair` e documenta o que significa de fato.

**Também há um bug semântico no gold:** `vinculos_per_capita` e `taxa_formalizacao_proxy` calculam `n_vinculos_ativos / populacao`. São o mesmo cálculo, dois nomes diferentes, mesma coluna duplicada no gold. É cargo cult de renaming sem valor computacional.

### 2.2 Silver que faz sentido construir agora (dada a decisão de WHY)

Para Working Paper com identificação causal, a silver mínima viável adicional é uma de duas:

**Opção A — Silver temática por questão de pesquisa:** um notebook silver por análise (ex.: `silver_rais_reforma_trabalhista.py` que agrega `tipo_vinculo + tipo_admissao + motivo_desligamento` por `(uf, setor, ano, mes_admissao)`). Mais rápido de implementar, menos reutilizável. Apropriado para Working Paper único com foco em uma questão.

**Opção B — Silver ampla `rais_uf_setor_ano`:** grain `(uf, cnae2dig, ano)` com todas as variáveis de identidade causal (sexo, faixa_etaria, tipo_vinculo, tipo_admissao, motivo_desligamento, grau_instrucao, ind_intermitente). Maior custo de build (scan de 2B linhas), mas serve todos os 6 §9. Para 40 anos + 27 UFs + 87 CNAEs 2-dig = ~94K linhas por medida. Manejável.

**Recomendação:** Opção A para o primeiro Working Paper (escolha a questão causal principal, construa silver temática, publique). Opção B como roadmap de plataforma para os subsequentes. Não tente construir Opção B antes de ter a questão causal escolhida — é over-engineering sem evidência de uso.

### 2.3 Notebook reproducible (Quarto + DABs)

Para Working Paper peer-reviewed, o notebook de análise (onde rodam os modelos causais, as figuras, as tabelas) deve ser Quarto. Justificativa:

- Quarto compila `.qmd` → PDF (LaTeX) com referências cruzadas, figuras numeradas, equações — adequado para artigo acadêmico
- Versionável em git (texto puro, não JSON de notebook Jupyter)
- Databricks Free Edition não tem Quarto nativo, mas o workflow de CI pode executar as queries SQL (via DABs job), exportar os artefatos de dados para `data/gold/`, e o Quarto roda localmente ou em GitHub Actions sobre esses artefatos — mesmo padrão das outras verticais

**Estrutura recomendada para o WP de RAIS:**

```
articles/
  rais-<tema>.tex          # LaTeX para PDF (ABNT++)
  build-figures-rais.py    # gera figuras via mirante_style + mirante_charts
  data/                    # artefatos snapshot exportados do gold
    rais_sample_<ano>.parquet  # DVC-tracked (não commitar raw 2B linhas)
```

**Quarto não é obrigatório** se o padrão do projeto é `.tex` (que é o padrão das outras verticais). O que é obrigatório é que as figuras sejam geradas por código (`build-figures-rais.py`) não por screenshot, e que o código rode em CI.

### 2.4 Data product público (parquet em CDN vs Iceberg REST)

**Não vale o esforço no momento.** Razões:

1. A bronze com 2B linhas tem ~100-200 GB comprimida em Delta. Servir isso via CDN requer ou (a) subsetting agressivo ou (b) custo de egress não-trivial.
2. UniForm Iceberg já está habilitado na bronze. Qualquer cliente com credenciais UC pode ler via REST. Para jornalistas e academia, o endpoint UC é suficiente — quem precisa de API REST não precisa de CDN, precisa de credenciais.
3. O gold exportado como JSON (~UF × Ano, ~1.000 linhas) já está em `data/gold/gold_rais_estados_ano.json` versionado no git — disponível publicamente via GitHub raw URL. Isso serve o objetivo (c) de plataforma de descoberta para o nível de granularidade que o frontend expõe.

**Se o objetivo (c) evoluir para permitir queries ad hoc do público** (jornalistas explorando por setor ou município), aí o investimento faz sentido — mas exige decisão de produto antes de decisão de infraestrutura. Não inverta a ordem.

### 2.5 Reproducibility tests (pytest CI)

**O que existe:** `tests/conftest.py` tem a fixture `rais_gold` que abre `data/gold/gold_rais_estados_ano.json` — mas nenhum `test_rais_*.py` existe. O conftest entrega um `[]` silencioso se o arquivo não existir (linha `return json.load(open(p)) if p.exists() else []`), o que significa que CI passaria mesmo sem dado nenhum.

**O mínimo para Working Paper:**

```python
# tests/test_rais_gold.py

def test_rais_gold_not_empty(rais_gold):
    assert len(rais_gold) > 0, "gold RAIS vazio — pipeline falhou ou JSON não exportado"

def test_rais_gold_40_anos(rais_gold):
    anos = {r["Ano"] for r in rais_gold}
    assert min(anos) <= 1985, f"série não começa em 1985: mín={min(anos)}"
    assert max(anos) >= 2024, f"série não chega em 2024: máx={max(anos)}"

def test_rais_gold_27_ufs_por_ano(rais_gold, ufs_canonical):
    from collections import Counter
    ufs_por_ano = {}
    for r in rais_gold:
        ufs_por_ano.setdefault(r["Ano"], set()).add(r["uf"])
    anos_incompletos = [(ano, sorted(set(ufs_canonical) - ufs)) 
                        for ano, ufs in ufs_por_ano.items()
                        if len(ufs) < 27]
    # SP 1986 ausente é conhecido — permitir DF gap pré-1987
    anos_inesperados = [(a, falt) for a, falt in anos_incompletos
                        if not (a == 1986 and falt == ["SP"])]
    assert not anos_inesperados, f"UFs faltantes por ano: {anos_inesperados}"

def test_rais_gold_vinculos_ativos_monotonic_recovery(rais_gold):
    """Pós-2020 deve ter crescimento — invariante de sanidade básica."""
    br = sorted([r for r in rais_gold if r["uf"] == "SP"], key=lambda r: r["Ano"])
    v2020 = next((r["n_vinculos_ativos"] for r in br if r["Ano"] == 2020), None)
    v2024 = next((r["n_vinculos_ativos"] for r in br if r["Ano"] == 2024), None)
    if v2020 and v2024:
        assert v2024 > v2020, f"SP: vínculos 2024 ({v2024}) <= 2020 ({v2020}) — anomalia"

def test_rais_gold_no_null_n_vinculos_ativos(rais_gold):
    nulls = [r for r in rais_gold if r.get("n_vinculos_ativos") is None]
    assert not nulls, f"{len(nulls)} linhas com n_vinculos_ativos=NULL — pipeline incompleto"
```

Cinco testes, ~50 linhas, CI passa em segundos (sem Spark). Esses testes não garantem que os dados estão certos — garantem que o pipeline não regrediu silenciosamente. É o piso mínimo.

### 2.6 ADRs necessários antes de publicação

Cinco ADRs que precisam existir — dois dos quais já estão documentados no código como comentários, mas precisam ser formalizados em arquivo:

**ADR-001: Dual reader txt-semicolon / COMT-comma** (formalize o que já existe em `rais_vinculos.py` linhas 1046-1067). Contexto: PDET mudou silenciosamente em 2023. Decisão: dois readers separados com `unionByName`. Consequência: schema evolution funciona mas `_dupN` pode proliferar se PDET mudar header novamente.

**ADR-002: Grain bronze = vínculo empregatício-ano (VINC-only, sem ESTAB)** (formalize `_is_vinculo_filename` + `_filter_vinc`). Crítico para Working Paper: COUNT(*) na bronze não é "número de trabalhadores" — um trabalhador com 2 empregos em 2010 aparece 2 vezes. Qualquer afirmação sobre "número de trabalhadores" no artigo exige caveats explícitos.

**ADR-003: Ausência de CPF — análises de mobilidade individual não são possíveis** (decisão do PDET, não do pipeline). Qualquer afirmação sobre "trajetória do trabalhador" ou "job-to-job mobility" com esses dados é pseudo-painel, não painel real. Precisa estar declarado.

**ADR-004: CBO94 (1985-2002) ≠ CBO2002 (2003+) — mapeamento não implementado na silver atual.** Comparações de ocupação cross-era precisam desta tabela de equivalência DIEESE. Sem ela, qualquer afirmação sobre "evolução da ocupação X entre 1990 e 2010" está errada.

**ADR-005: Grau de instrução — taxonomia dupla não harmonizada.** Era1+era2 usam PDET 1985 (10 categorias), era3 usa pós-2005 (codebook diferente). A silver não harmoniza — usa COALESCE bruto. A afirmação do panorama "mestre+doutor triplicou (7,4% → 24,4%)" é suspeita exatamente por isso: o codebook de 2024 pode incluir especialização lato sensu como grau 9, inflando a comparação.

---

## 3. Crítica do panorama da ótica de eng dados

### O que está fraco

**§6 (escolaridade):** o próprio panorama admite "A análise é parcial porque PDET trocou taxonomia em 2006". Isso deveria ser uma **limitação metodológica de seção**, não um parágrafo lateral. A frase "exigir auditoria do dicionário" está no documento — mas não é ação suficiente para um Working Paper. A auditoria precisa estar feita antes de publicar os números.

**§7 (massa salarial):** "A análise direta de mediana/p90 cross-era... requer deflacionar tudo pelo INPC ou pelo IPCA-15 primeiro. Sem deflação, comparação é vazia." Correto — mas o panorama apresenta a tabela §2.1 com os anos e não mostra salários deflacionados. O deflator do gold está ligado a `vl_remun_dezembro_nom` (1994+). Para 1985-1993, a silver tem apenas `vl_remun_dezembro_sm` (em salários-mínimos). A deflação por SM não é equivalente a deflação por IPCA — SM sofreu política (congelamentos do Cruzado, reajustes heterodoxos). Publicar comparação de remuneração 1985-2024 sem discutir esse problema metodológico é afirmação sem evidência reproduzível.

**§8.3 (gaps na fonte):** "SP1986: corrupção persistente do FTP, em quarentena (~7-13M linhas)". O panorama subestima o impacto: se SP tinha ~35% do emprego formal em 1985, e a queda de 28,6% nos vínculos ativos de 1986 é o "choque mais dramático da série", a pergunta imediata de qualquer revisor é: "quanto da queda de 1986 é SP ausente por corrupção de arquivo?" Isso precisa de análise de sensibilidade explícita antes de qualquer publicação sobre o Cruzado.

### O que está faltando

**Nenhuma análise de `COUNT(DISTINCT trabalhador)`** — o panorama apresenta vínculos como proxy de trabalhadores sem qualificar. A nota na §1 ("COUNT(*) não é número de trabalhadores") está lá, mas os números da tabela §2.1 são contagem de vínculos. Se SP tem 25M+ vínculos em 2024, isso inclui pluriemprego, desligamentos e readmissões no mesmo ano. A "formalização recorde" de Lula III (§1) pode ser parcialmente artefato de rotatividade alta, não de novos trabalhadores entrando no formal.

**Nenhuma validação externa cruzada** com CAGED, PME/PNAD ou IBGE. Para publicação, precisamos de pelo menos uma comparação de "estoque de vínculos ativos 31/12 RAIS vs estoque de empregos formais CAGED acumulado" para validar que a série RAIS está correta antes de usar como ground truth. Não é difícil de fazer — CAGED é público — mas não está feito.

---

## 4. Padrão de reproducibility mínimo para Working Paper citando RAIS

O mínimo aceitável para peer review em econometria aplicada com microdados de 40 anos:

**Obrigatório (não-negociável para submissão):**

1. **Commit hash fixado no artigo:** "Dados gerados a partir do pipeline commit `XXXXXXX` (YYYY-MM-DD)" no rodapé ou apêndice metodológico. O hash identifica exatamente qual versão do código gerou os resultados.

2. **Delta table VERSION AS OF para gold:** `SELECT * FROM mirante_prd.gold.rais_estados_ano VERSION AS OF N` onde N é o version number da tabela no momento da publicação. Isso permite que qualquer pessoa com acesso UC reproduza exatamente os dados usados. Documentar o version number no apêndice do artigo.

3. **pytest CI verde no commit do artigo:** o CI do repositório precisa passar `pytest tests/test_rais_gold.py` com o JSON de gold que foi usado para gerar as figuras. Isso garante que os artefatos são consistentes com o código.

4. **`build-figures-rais.py` commitado e rodável:** qualquer figura do artigo deve ser gerada por este script, não por captura de tela ou notebook ad hoc. O script deve ter `argparse` para receber o path do data/gold como input, e deve ser chamado no CI.

**Desejável (eleva de B para B+ na avaliação de eng dados):**

5. **DVC tracking do JSON de gold:** `dvc add data/gold/gold_rais_estados_ano.json` com remote configurado (pode ser o próprio repo git com LFS, ou um bucket S3 Free). Isso dá SHA256 verificável do artefato de dados, independente do código.

6. **Zenodo deposit do snapshot de gold + código:** DOI citable como `Chalhoub, L. (2026). RAIS 40 anos — gold panel UF × Ano. Zenodo. doi:10.5281/zenodo.XXXXXXX`. Para dados de 40 anos de microdados públicos, depositar o gold (não a bronze de 2B linhas) é suficiente para reproducibility do artigo.

7. **Docker image do ambiente de análise:** `FROM python:3.11-slim` com dependências fixadas (`requirements.txt` com hashes SHA256). Permite rodar `build-figures-rais.py` em qualquer máquina sem instalar Spark. As figuras dependem apenas do JSON de gold, não da bronze.

**O que NÃO é necessário (over-engineering para este projeto):**

- Publicar a bronze de 2B linhas via CDN ou Iceberg REST para uso público — a fonte PDET é pública e qualquer pessoa pode replicar o ingest. O pipeline de ingest está no repositório.
- MLflow para rastrear parâmetros do modelo causal — a questão causal usa econometria (DiD, RDD), não ML, e os parâmetros estão nos próprios scripts Python/R. MLflow é para modelos que treinam com hiperparâmetros.
- Kubernetes para rodar o pipeline — isso roda no Databricks Free Edition. Ponto.

---

## 5. Nota global — régua mestrado stricto sensu

| Dimensão | Nota | Justificativa |
|---|---|---|
| Bronze — correção do output | B | Dual reader resolveu Issues A/B/C. Issue D (SP 1986) documentado mas sem análise de sensibilidade publicada |
| Bronze — arquitetura e idempotência | B+ | Per-year reader, DQ gate, ESTAB isolation, UniForm, checkpoint dual: sólido |
| Bronze — UC metadata | B+ | TAGs + 50+ COMMENTs verbosos: padrão da plataforma cumprido |
| Silver — cobertura de variáveis | C | Serve panorama descritivo, não serve nenhuma das 6 questões causais |
| Silver — bugs conhecidos | C+ | n_estabelecimentos_proxy semanticamente errado; vinculos_per_capita ≡ taxa_formalizacao_proxy; remuneração 1985-93 NULL sem documentação |
| Testes automatizados | C | conftest tem fixture, zero test_rais_*.py existem |
| Reproducibility | C+ | Commit hash existe; sem DVC, sem Zenodo, sem VERSION AS OF documentado |
| ADRs | C | Decisões críticas documentadas como comentários no código, não como ADRs formais linkados no repo |
| DAB / CI/CD | B | Pipeline orquestrado, job RAIS no databricks.yml com dependências corretas |
| Observabilidade | B | DQ gate + logs estruturados no bronze; silver/gold sem métricas de DQ próprias |

**Nota global: B (2,0 pts) — no limiar de aprovação**

O que impediu B+: a silver não suporta as questões causais que o autor quer responder, e não há testes. Esses dois itens são os de maior impacto em peer review real — revisores de econometria vão pedir o código da análise, e revisores de eng dados vão pedir o pipeline de dados. Se o código da análise não roda em CI e a silver não tem as variáveis, o artigo não passa de B no parecer de eng.

---

## 6. Três ações prioritárias

**Ação 1 — Silver temática para a questão causal escolhida (1-2 semanas, depende da escolha do autor)**

O autor precisa escolher UMA das questões do §9 para o Working Paper. Depois disso, implementar `silver_rais_<tema>.py` com as variáveis específicas daquela questão (ver tabela na seção 2.1). Por exemplo, para §9.1 (Reforma Trabalhista 2017):

```python
# pipelines/notebooks/silver/rais_reforma_2017.py
# grain: (uf, cnae2dig, tipo_vinculo, tipo_admissao, ano, mes_admissao)
# foco: 2015-2022 (janela de event study)
# variáveis: n_vinculos, n_admitidos, n_desligados, media_tempo_emprego
#            n_intermitentes (2018+), share_sem_justa_causa
```

Custo computacional: scan parcial da bronze (7 anos × 2B/40 linhas = ~350M linhas). Estimativa: 20-40 min no serverless Free Edition.

Dependência: nenhuma — a bronze já está correta.

**Ação 2 — pytest RAIS mínimo + CI verde (2-3 dias, independente da Ação 1)**

Criar `tests/test_rais_gold.py` com os 5 testes listados na seção 2.5. Exportar o JSON de gold atual para `data/gold/gold_rais_estados_ano.json` (o pipeline de export já existe — rodar o job `refresh RAIS`). Confirmar que `pytest tests/test_rais_gold.py` passa em GitHub Actions. Isso não exige Spark — os testes rodam sobre o JSON estático.

Dependência: precisar de `gold_rais_estados_ano.json` exportado. Se a silver atual (agregado grosseiro) for suficiente para os testes de sanidade, rode o pipeline agora. Se quiser esperar a silver temática da Ação 1, aguardar. Mas não deixe mais de 1 semana sem esse arquivo testado.

**Ação 3 — 5 ADRs formais em `docs/adrs/` + analysis de sensibilidade SP 1986 (1 semana)**

Formalizar os 5 ADRs listados na seção 2.6 como arquivos Markdown em `docs/adrs/`. Formato mínimo: contexto / decisão / consequências / alternativas rejeitadas. Não precisa ser longo — 1-2 páginas por ADR é suficiente.

Em paralelo, rodar a query de sensibilidade:

```sql
-- Qual seria a queda de 1986 sem SP? (para isolar artefato de arquivo ausente)
SELECT
  ano,
  SUM(CASE WHEN uf != 'SP' THEN n_vinculos_ativos ELSE 0 END) AS ativos_sem_sp,
  SUM(n_vinculos_ativos) AS ativos_total
FROM mirante_prd.silver.rais_uf_ano
WHERE ano IN (1985, 1986, 1987)
GROUP BY ano ORDER BY ano;
```

Se a queda de 1986 desaparece sem SP, o "choque do Cruzado" é em parte artefato de arquivo ausente. Se persiste, o choque é real. Esse número precisa estar no apêndice metodológico de qualquer publicação sobre 1986.

Dependência: Ações 1 e 2 podem ser paralelas com a Ação 3. A análise de sensibilidade de SP 1986 precisa da silver atual (que já tem `rais_uf_ano` com dados de 1985-2022 via COALESCE).

---

*Parecer emitido por: Conselheiro de Eng. Software & Plataforma de Dados*
*Data: 2026-04-28*
*Versão auditada: bronze v6 (commit 2158d65), silver rais_uf_ano, gold rais_estados_ano, DAB databricks.yml*

# Bolema — checklist de conformidade 100% (submissão de "O Cálculo Ausente")

> **Alvo:** *Bolema: Boletim de Educação Matemática* (UNESP Rio Claro) — Qualis
> **A1** em Ensino/Educação Matemática. Open Access CC-BY, **sem taxas** de
> submissão ou publicação. Fluxo contínuo desde 2024.
> **Plataforma:** ScholarOne — <https://mc04.manuscriptcentral.com/bolema-scielo>
> **Manuscrito-fonte:** [`calculo-ensino-medio-internacional.tex`](calculo-ensino-medio-internacional.tex)
> (versão completa) → precisa virar **pacote Bolema em Word, anonimizado**.
> Fontes oficiais: SciELO/Bolema *About* + *Instructions to Authors*
> (lido em 2026-07-03).

---

## 0. Snapshot da revista

| Item | Bolema |
|---|---|
| ISSN | 0103-636X (impresso) · 1980-4415 (online) |
| Escopo | Ensino/aprendizagem de Matemática **e/ou o papel da Matemática e da Educação Matemática na sociedade** |
| Tipos aceitos | **Somente artigos originais** (baseados em dados de pesquisa e/ou teorias). **Relatos e resenhas: excluídos** |
| Idiomas | Português, Espanhol ou Inglês |
| Licença | Creative Commons **CC-BY** |
| Taxas | **Nenhuma** (opção de publicação bilíngue tem custo à parte) |
| Revisão | **Duplo-cega**, ≥2 pareceristas; 3 fases (triagem → editor associado → pares) |
| Similaridade | **Turnitin**; acima de **25%** (incl. autocitação) vai à análise dos Editores-chefes |
| Editores-chefes | Danyal Farsani (NTNU) · Marcus V. Maltempi (Unesp) · Roger Miarka (Unesp) |

**Aderência de escopo:** ✅ artigo é revisão documental comparada de currículos
de Matemática + marco pedagógico → cai no núcleo "papel da Educação Matemática
na sociedade". Enquadrar como **artigo original** (não como ensaio/relato).

---

## STATUS (2026-07-05): DESK-REJECT (BOLEMA-2026-0250) → reconstruído no template oficial

A 1ª submissão foi **reprovada na triagem** (não foi para avaliação). Motivo
literal da secretaria: *"Cover Letter e artigo fora do template exigido pela
revista."*

**Causa-raiz (mea culpa):** o `.docx` submetido fora **gerado por conversão
LaTeX→Word (pandoc)** — acertava as *specs* visuais mas por dentro usava estilos
do pandoc (`Body Text`, `Heading 1`…), não os do `TEMPLATE_BOLEMA_PT-2025.docx`
(`Texto Comum`, `Texto ABNT`, `local`, `Caption`…). Tínhamos o template no repo
e nunca digitamos dentro dele. A linha "Layout conferido contra TEMPLATE" abaixo
era **conferência de aparência, não uso do template** — enganosa.

**Correção (novos artefatos, fonte da verdade):**
- [`calculo-bolema-TEMPLATE.docx`](calculo-bolema-TEMPLATE.docx) — manuscrito
  **dentro** do template oficial (100% estilos Bolema; verificado), **PT+EN**
  (sem ES — a revista pede 1 idioma secundário), Quadro 1 como **tabela nativa
  editável** com matemática recuperada do `.tex`, 3 figuras com legenda+**Fonte**,
  seções finais do template (Agradecimentos / Contribuições / Disponibilidade),
  **anonimizado** (0 vazamentos de autor; propriedades limpas).
  ⚠️ **Gotcha corrigido:** o docx-fonte (pandoc) havia descartado TODO `\ref`
  (Figura/Quadro/Seção) e TODA matemática inline — recuperados do `.tex` (12 refs
  + estatísticas da Seção 4.3 + Gaokao/ENEM). Recuo de 1ª linha do estilo `Normal`
  zerado em títulos/cabeçalhos/figuras (senão centralização sai deslocada à
  direita). Centralização das 3 figuras confirmada por bbox no PDF (Word). 19 pp.
- [`calculo-bolema-carta-TEMPLATE.docx`](calculo-bolema-carta-TEMPLATE.docx) —
  cover letter no **template OFICIAL** do Bolema (`bolema-template-CL.docx`, baixado
  das instruções). NÃO é carta livre: é o **questionário obrigatório** (Seções A/B/C;
  faixas 400-500/400-500/500-600; respostas = 1.262 palavras ≤ 1.500), em PT
  (idioma primário), tipo de contribuição assinalado, blocos EN/ES removidos.
- Builds: [`scripts/build_docx_bolema_template.py`](scripts/build_docx_bolema_template.py),
  [`scripts/build_carta_bolema.py`](scripts/build_carta_bolema.py).

**LIMITE DE 20 PÁGINAS = conforme, com margem.** Medido na **paginação real do
MS Word** (Office16 via COM, `ComputeStatistics(wdStatisticPages)`):
`calculo-bolema-TEMPLATE.docx` = **19 páginas** (7.332 palavras) → **≤ 20, com
~1 página de folga**. Margem obtida por layout (figuras a 10 cm — alta resolução,
legíveis — e espaçamento do cabeçalho), **sem cortar nenhum texto científico**.
As 25 páginas do proof do ScholarOne eram o formato de revisão (duplo-espaço +
numeração de linha), NÃO o template; páginas de artigos *publicados* (19–34) são
diagramação do SciELO e não servem de referência.

**Pré-envio (externo, do autor):** (1) rodar **Turnitin < 25%**; (2) como foi
*Reject*, a resubmissão gera **novo Manuscript ID**. (Modelo oficial de cover
letter já resolvido — questionário A/B/C preenchido.)

---

### STATUS anterior (2026-07-03, histórico — contém as afirmações corrigidas acima)

**Revisão para "irresistível" concluída** (todas as recomendações das 4
cadeiras): reenquadramento denúncia→construção (Quadro didático CPA de Bruner
+ novo título), Spearman ρ=0,06 reportado com honestidade (Brasil = outlier
−3,5σ), literatura do Bolema citada (Pires 2014; Gonçalves 2018; Araújo &
Avelar 2022), figuras refeitas (heatmap legível + anotação direta), e
**auditabilidade 100%** (11/11 currículos oficiais verificados; `--strict`
exit 0). Mantido em **20 páginas**. Novos artefatos: `build_figures_calculo_bolema.py`,
`scripts/audit_curricula_keywords.py` (v2 + HWP), `sources_calculo_curricula.json`
(v2.0 c/ sha256), `calculo-bolema-PLANO-REVISAO.md`, `calculo-bolema-BRIEF-CONSELHO*.md`.
Layout conferido contra `TEMPLATE_BOLEMA_PT-2025.docx` (margens 3/2/3/2, TNR
12, título 16/14pt, keywords com ponto). Turnitin (#3 antigo) segue pendente
de conta externa; DOI de dados = placeholder até depósito OSF/Zenodo.

---

### STATUS anterior (histórico): 6/7 bloqueadores

**Pacote Bolema gerado** (base: versão REMat anonimizada):

| Arquivo | O que é |
|---|---|
| [`calculo-bolema-submissao.tex`](calculo-bolema-submissao.tex) | Manuscrito anonimizado, formatação Bolema, **20 páginas** |
| [`calculo-bolema-submissao.pdf`](calculo-bolema-submissao.pdf) | PDF de conferência (compilado com tectonic) |
| [`calculo-bolema-submissao.docx`](calculo-bolema-submissao.docx) | **Arquivo de submissão** (Word); propriedades anonimizadas; 718 KiB |
| [`calculo-bolema-CARTA-APRESENTACAO.md`](calculo-bolema-CARTA-APRESENTACAO.md) | Carta de apresentação (não-cega, Passo 6) |
| [`calculo-bolema-DECLARACOES.md`](calculo-bolema-DECLARACOES.md) | Conflito de interesse, ética, contribuição, IA, originalidade |
| [`scripts/build_docx_bolema.py`](scripts/build_docx_bolema.py) | Build reproduzível LaTeX→Word + anonimização de propriedades |

## 1. Requisitos que BLOQUEIAM aceitação

| # | Requisito Bolema | Regra exata | Estado | Evidência |
|---|---|---|---|---|
| 1 | **Limite de páginas** | **máx. 20 páginas** | ✅ **20 pág.** | cortes: exemplos de exame 4→2 caixas; removido Quadro "16 anos" (redundante); refs em TNR 11 |
| 2 | **Anonimização** | corpo + **propriedades do arquivo** sem autores; nome do arquivo idem | ✅ | `.docx` sem `dc:creator`/`lastModifiedBy`/`Company`; varredura de nomes/afiliações no corpo = 0 |
| 3 | **Similaridade Turnitin < 25%** | inclui autocitação | ⏳ **pendente** | exige conta Turnitin (não disponível aqui); texto é autoral e inédito — **rodar antes de enviar** |
| 4 | **Divulgação de uso de IA** | declarar em resumo/métodos; ocultar = falha ética | ✅ | Claude Opus 4.8 declarado na **Metodologia** e nas **Declarações** |
| 5 | **Carta de apresentação** | **obrigatória** (Passo 6 ScholarOne) | ✅ | `calculo-bolema-CARTA-APRESENTACAO.md` |
| 6 | **Conflito de interesse** | declaração obrigatória | ✅ | `calculo-bolema-DECLARACOES.md` §1 |
| 7 | **Tipo de documento** | só artigo original; sem resenha/relato | ✅ | enquadrar como "Artigo" no Passo 1 (revisão documental original) |

---

## 2. Formatação (Word) — especificação exata

> Submissão **em Word (.doc/.docx)**, A4. Fonte-base **Times New Roman**.
> (Nosso `.tex` usa `newtxtext`/`newtxmath` = Times; a conversão para Word deve
> reproduzir a fonte fielmente.)

| Elemento | Regra Bolema | Ação |
|---|---|---|
| Papel/margens | A4; **3 cm** (sup./esq.), **2 cm** (inf./dir.) | ⚠️ ajustar (nosso tex: top 3 / bottom 2 / left 3 / right 2 → **OK**) |
| Corpo do texto | Times New Roman **12**, espaçamento **1,5**, recuo 1ª linha **1,25 cm** | ✅ equivalente ao tex |
| Citações/excertos | TNR **11**, itálico, **espaço simples**, recuo 1,25 cm | ⚠️ conferir na conversão |
| Título principal (PT) | TNR **16**, negrito, 1,5, centralizado; iniciais maiúsc. (exceto prep./conj.) | ⚠️ formatar |
| Título secundário (EN/ES) | TNR **14**, negrito, 1,5, centralizado | ⚠️ formatar |
| Seções | numeração 1, 1.1 … até 2.1.1.1.1; TNR **12** negrito, à esquerda | ✅ conferir |
| Figuras | id. **embaixo**, centralizado: **"Figura 1 – Título"**; fonte interna TNR 10; **citar fonte** | ⚠️ 3 figuras — reposicionar legenda + fonte |
| Tabelas/Quadros | id. **em cima**, negrito: **"Tabela 1 – Título"**; **editáveis (não imagem)** | ⚠️ 5 quadros — garantir que sejam **tabelas nativas**, não PNG |
| Referências | **ABNT NBR 10520:2023** (autor-data); lista TNR **11**, espaço simples | ✅ já em ABNT — reconferir |
| Tamanho de arquivo | (limite prático da plataforma: manter enxuto; figuras vetoriais) | ⚠️ conferir |

---

## 3. Estrutura obrigatória do artigo (ordem exata)

1. Título (Português)
2. Nomes dos autores com notas em sobrescrito → **remover na versão anônima**
3. Resumo (PT)
4. Palavras-chave (PT)
5. Título (EN/ES)
6. Abstract/Resumen (EN/ES)
7. Keywords/Palabras clave
8. Corpo com seções numeradas
9. Agradecimentos (opcional, sem numeração) → **fora da versão anônima**
10. Referências

**Resumo:** **100–250 palavras**, TNR 10, espaço simples, justificado; deve
conter **problema, metodologia, resultados e conclusões**.
→ ⚠️ **conferir contagem** do nosso resumo (o resumo REMat é longo; pode passar
de 250 palavras — encurtar).

**Palavras-chave:** **até 5**, iniciais maiúsculas, separadas por ponto.
→ ✅ temos 5 (Cálculo Diferencial e Integral; Currículo de Matemática; Ensino
Médio; Educação Matemática Comparada; BNCC) — **conferir separador = ponto**.

---

## 4. Fluxo de submissão (ScholarOne — 7 passos)

1. Tipo, Título, Resumo
2. Upload do arquivo (**versão anônima**)
3. Atributos (palavras-chave)
4. Autores e instituições
5. Detalhes e comentários
6. **Upload da carta de apresentação** (obrigatória)
7. Revisar e submeter

**Pós-submissão / revisão:** triagem pelos Editores-chefes (escopo +
similaridade) → avaliação preliminar do Editor Associado (via cover letter) →
**duplo-cega** com ≥2 pareceristas. Decisões: aprovado / aprovado com
correções menores / reformulação (correções maiores) / recusado.

---

## 5. Itens já OK (não requerem ação)

- ✅ Sem taxas → nenhum pagamento a providenciar (a menos que queiram bilíngue).
- ✅ Idioma: Português aceito.
- ✅ Escopo: encaixa como artigo original de Educação Matemática.
- ✅ Referências já em normas ABNT (só reconferir NBR 10520:2023).
- ✅ 5 palavras-chave definidas.
- ✅ Figuras vetoriais já geradas (3) + 5 quadros.

---

## 6. Diferenças frente ao pacote REMat (o que reaproveitar / o que refazer)

| Aspecto | REMat (já feito) | Bolema (refazer) |
|---|---|---|
| Nº de autores | máx. 3 (Chalhoub, Korte, Rolim) | **sem limite explícito** — decidir composição |
| ORCID | obrigatório | **não exigido** (mas recomendável) |
| Título | 3 idiomas | PT + **um** secundário (EN ou ES) |
| Anonimização | já feita (`calculo-remat-submissao`) | **reaproveitar**, mas limpar Propriedades do Word |
| Limite | 15–25 pág. | **máx. 20** → cortar |
| Formato | LaTeX/PDF/DOCX | **Word obrigatório**, template Bolema |
| Carta de apresentação | — | **nova (obrigatória)** |
| Declaração de IA | — | **nova (obrigatória)** |

---

## 7. Checklist final antes de clicar "Submit"

- [ ] Manuscrito **≤ 20 páginas**
- [ ] Arquivo **.docx anônimo**; **Propriedades do Word limpas**; nome do arquivo sem autores
- [ ] Fonte Times New Roman em todo o corpo; margens 3/3/2/2 cm; recuo 1,25 cm
- [ ] Título PT (16 bold) + título secundário EN/ES (14 bold)
- [ ] Resumo **100–250 palavras** com problema/método/resultados/conclusão
- [ ] Até 5 palavras-chave separadas por ponto (PT + EN/ES)
- [ ] Figuras: legenda **embaixo** "Figura N – …" + **fonte**; Tabelas: título **em cima**, **editáveis**
- [ ] Referências ABNT NBR 10520:2023 (autor-data), TNR 11
- [ ] **Similaridade Turnitin < 25%** (verificado)
- [ ] **Declaração de uso de IA** no resumo/métodos
- [ ] **Carta de apresentação** (template Bolema) pronta
- [ ] **Formulário de conflito de interesse** preenchido
- [ ] Enquadrado como **Artigo original** (não ensaio/relato)
- [ ] Agradecimentos e identificação **fora** da versão anônima

---

### Fontes
- Bolema — Sobre: <https://www.scielo.br/journal/bolema/about/#about>
- Bolema — Corpo Editorial: <https://www.scielo.br/journal/bolema/about/#editors>
- Bolema — Instruções aos Autores: <https://www.scielo.br/journal/bolema/about/#instructions>

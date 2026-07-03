# Declarações — submissão ao Bolema

> Conteúdo dos formulários de declaração exigidos pelo *Bolema* (conflito
> de interesse, ética, contribuição, IA). Preencher/assinar no formato
> oficial da revista quando solicitado; o texto abaixo é a fonte única de
> verdade. **Documento não-cego** — não integra o manuscrito anonimizado.

**Título:** O cálculo ausente: duzentos anos de currículo e uma
comparação internacional no ensino médio.

---

## 1. Conflito de interesse

Os autores declaram **não haver conflito de interesse** de natureza
pessoal, comercial, política, acadêmica ou financeira relacionado a este
manuscrito.

## 2. Financiamento

A pesquisa **não recebeu financiamento** externo.

## 3. Ética em pesquisa

O estudo é uma **revisão documental** de fontes curriculares e de
avaliação **públicas e oficiais**; não envolve seres humanos, dados
pessoais ou experimentação, **não requerendo** apreciação por Comitê de
Ética em Pesquisa. A observância das boas práticas de pesquisa é de
responsabilidade dos autores.

## 4. Contribuição dos autores (CRediT)

Todos os autores contribuíram para a **concepção e o desenho do estudo**,
a **curadoria e verificação das fontes curriculares oficiais**, a
**redação** e a **revisão crítica**, tendo **aprovado a versão
submetida** e por ela se responsabilizando publicamente.

## 5. Uso de inteligência artificial

Declara-se o uso do assistente de IA **Claude, modelo Opus 4.8 (Anthropic)**,
como ferramenta de apoio em **todas as etapas** de elaboração do trabalho:
organização e revisão das fontes curriculares, redação e edição do texto e
geração do código das figuras. **Nenhum conteúdo foi incorporado sem
revisão e verificação humanas**; os autores assumem integral
responsabilidade pública pelo texto. Esta declaração consta também do
manuscrito (Seção de Metodologia e Declarações), em conformidade com a
política de transparência do *Bolema*.

## 5b. Disponibilidade de dados e código (URL para a versão final / camera-ready)

Repositório público (Mirante dos Dados):
**https://github.com/leonardochalhoub/mirante-dos-dados-br**

Artefatos que reproduzem os achados (sob `articles/`):
- `scripts/sources_calculo_curricula.json` — manifesto das 11 fontes curriculares
  oficiais (URL, órgão, SHA-256, data de captura).
- `scripts/audit_curricula_keywords.py` — auditoria do achado curricular
  (`--strict` → 11/11 OK; Brasil = 0 ocorrências de cálculo).
- `scripts/compute_pisa_correlations.py` — correlações status×PISA (ρ, bootstrap).
- `scripts/build_figures_calculo_bolema.py` — geração das figuras.
- `requirements-audit.txt` — dependências fixadas.

> **Atenção (duplo-cego):** a URL acima contém o nome do autor correspondente
> e **não** deve entrar na versão anonimizada do manuscrito. Inseri-la apenas
> no camera-ready (após o aceite). Para dar rastreabilidade ao revisor durante
> a revisão cega, opção recomendada: publicar um espelho anonimizado (ex.:
> `anonymous.4open.science`) e citar esse link temporário.

## 6. Originalidade e ineditismo

O manuscrito é **original e inédito**, **não** tendo sido publicado nem
submetido simultaneamente a outro periódico.

## 7. Similaridade (Turnitin) — a verificar

O *Bolema* submete os artigos ao **Turnitin**; manuscritos com
similaridade **acima de 25%** (incluindo autocitação) são analisados
pelos Editores-chefes. Providência pendente do autor correspondente:
**rodar verificação de similaridade** antes do envio e reduzir citações
diretas longas, se necessário. O texto é de autoria própria e não
reaproveita publicações anteriores dos autores.

---

**Autor correspondente:** Leonardo Chalhoub — leonardochalhoub@gmail.com

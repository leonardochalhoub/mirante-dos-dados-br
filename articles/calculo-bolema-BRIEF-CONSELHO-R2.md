# Brief do Conselho — Rodada 2 (re-avaliação de "O Cálculo Ausente")

Implementamos **todas** as recomendações da Rodada 1. Pedimos re-avaliação:
o artigo ficou irresistível para o Bolema? O que ainda trava aprovação?

## Arquivos
- **Artigo revisado (20 pág., anonimizado):** `articles/calculo-bolema-submissao.tex` / `.pdf`
- **Submissão em Word:** `articles/calculo-bolema-submissao.docx`
- **Template oficial do Bolema:** `TEMPLATE_BOLEMA_PT-2025.docx` (raiz do repo)
- Auditoria: `articles/scripts/audit_curricula_keywords.py` + `sources_calculo_curricula.json`

## O que mudou desde a Rodada 1 (por parecer)
**Administração (WHY / construção):**
- Novo **Quadro 1** = sequência didática CPA de Bruner (enativo→icônico→simbólico)
  para introduzir a derivada — entrega o "roteiro pedagógico" do novo título.
- Argumento de **equidade** (IB particular × rede pública) puxado para a Introdução.
- **Título** reformulado: "…comparação internacional \emph{e um roteiro pedagógico
  para o ensino médio}".
- **Literatura do Bolema** agora citada (Pires \emph{et al.}, 2014; Gonçalves;
  Dias; Peralta, 2018; Araújo; Avelar, 2022); removidas as citações da REMat.

**Finanças (rigor / causalidade):**
- **Spearman calculado** e reportado com honestidade: $\rho = 0{,}06$ (n.s.) ---
  \emph{não} há gradiente dose-resposta; o robusto é o Brasil como outlier
  ($-3{,}5\sigma$; ponto-bisserial $r=0{,}68$, $p<0{,}01$).
- Caveat do PISA **movido para antes** da figura e para a legenda.
- **Nível 2** da discussão reescrito (outlier, não "correlação alta"); Nível 3
  rebaixado para robustez baixa.
- Benjamin Constant (1890–1901) enquadrado como **quase-experimento**.
- Contraponto internacional de reprovação (Bressoud, 2015) adicionado.

**Engenharia (reprodutibilidade):**
- **Auditabilidade 100%**: 11/11 fontes oficiais primárias verificadas
  mecanicamente (Brasil=0 → ausente; demais > 0), com sha256 + data de captura.
- Bugs do script corrigidos (`--strict` agora falha em lacuna); leitura de HWP
  coreano; keywords calculus-específicas (sem falso-positivo).
- Parágrafo de reprodutibilidade na Metodologia + seção **Disponibilidade de
  dados e código** nas Declarações.

**Design (forma):**
- **Fig. 1** (heatmap) legível: 17 países, largura maior, **anotação direta**
  "← única linha integralmente ausente" (funciona em P&B/daltônico).
- **Fig. 2**: N declarado na legenda. **Fig. 3**: restrita aos países tabulados
  (sem pontos-fantasma).
- Cortes: prosa país-a-país condensada; Tabela do PISA removida (redundante com
  Fig. 2); exemplos de exame de 4→1 caixa. Mantido em **20 páginas**.

## Pedido de parecer (objetivo, ~1 página cada)
1. As mudanças resolveram o risco que você apontou? Ficou algum resíduo?
2. Nota de recomendação: aceitar / aceitar com correções menores / reformular.
3. **Conselheira de Design (adicional):** compare o `calculo-bolema-submissao.docx`
   com o `TEMPLATE_BOLEMA_PT-2025.docx` (raiz) e diga se está **100% conforme**
   o template (margens, fontes, tamanhos, espaçamento, estrutura de resumo,
   palavras-chave, títulos, quadros/figuras). Liste qualquer divergência.

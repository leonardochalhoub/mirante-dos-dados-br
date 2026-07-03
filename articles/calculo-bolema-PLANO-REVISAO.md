# Plano de revisão — "O Cálculo Ausente" irresistível para o Bolema

Síntese dos 4 pareceres do Conselho (Opus 4.8) + prior-art + perfil de forma.
Prioridade por **impacto × esforço**. Alvo: teto de 20 páginas mantido.

## Tese transversal dos 4 pareceres
Todos convergem no mesmo diagnóstico: **o artigo declara, mas não demonstra.**
- Administração: teoria (Bruner/Rezende) fica decorativa, não vira lente.
- Finanças: "correlação robusta" é retórica — nunca é número.
- Engenharia: auditabilidade existe como script de bastidor, não como ativo no texto.
- Design: a força "Brasil é a única linha ausente" depende de cor e de legenda, não é anotada no gráfico.

**Meta-movimento:** elevar de *policy report / infográfico de jornal* para
**artigo de Educação Matemática** — operacionalizar o que hoje é declarado, e
dialogar com a conversa do próprio Bolema. É isso que trava o risco nº 1 de
recusa ("fora de escopo: isto não é Educação Matemática").

---

## BACKLOG PRIORIZADO

### Tier 1 — alto impacto, baixo esforço (fazer primeiro)
1. **[A2] Citar a conversa do Bolema sobre currículo.** Inserir Pires, Godoy,
   Silva & Santos (2014, edição temática de currículo do Bolema), Gonçalves,
   Dias & Peralta (2018, comparativo Brasil–EUA) e Araújo & Avelar (2022,
   pensamento integral) na Introdução e na Discussão, posicionando/diferenciando.
   *Gesto de pertencimento — o parecerista se vê citado.*
2. **[F1] Calcular a correlação que já afirmamos.** Spearman ρ (ou point-biserial)
   entre status curricular ordinal e PISA 2022 no `quad:comparativo` (n=16), IC
   95% por bootstrap/randomization inference; rotular como **associação**, não
   efeito. Nota metodológica de 3–4 linhas após a Síntese quantitativa.
3. **[D1/D4] Fig. 1 legível + anotação direta.** `width` 0,74→0,95; reduzir de
   28 p/ ~16–18 linhas (Brasil + comparadores-chave; resto p/ suplementar); e
   anotar sobre o gráfico: **"← única linha integralmente ausente"** (funciona em
   P&B e para daltônicos). Rodar simulador de daltonismo.
4. **[F2/F5] Reordenar caveat→evidência no PISA.** Mover o aviso de "proxy
   invertido" para ANTES da Tabela 1/Fig. 2 e para a legenda; alinhar resumo
   trilíngue ("consequências mensuráveis" → "indicadores contextuais associados").
5. **[F4] Benjamin Constant (1890–1901) como quase-causal.** Uma frase religando
   a remoção exógena (pós-morte, realinhamento político) à moldura de robustez —
   é a peça de identificação mais forte do artigo, hoje solta na história.

### Tier 2 — alto impacto, esforço médio
6. **[A1/A4] Reenquadrar denúncia→construção — a mudança de maior impacto.**
   (a) Adicionar **um Quadro didático**: sequência CPA de Bruner para "taxa de
   variação" (enativo: queda de um corpo → icônico: gráfico posição-tempo →
   simbólico: derivada via limite), ancorada no 2º/3º ano do EM brasileiro.
   (b) Puxar o argumento de **equidade** (IB na escola particular × rede pública
   sem cálculo — hoje na l.875) para o 2º/3º parágrafo da Introdução.
7. **[A3] Fazer a teoria trabalhar.** Usar os 5 eixos epistemológicos de Rezende
   (discreto/contínuo, finito/infinito, local/global etc.) para **classificar**
   como 2–3 países-chave (Singapura, Alemanha, Brasil) tratam o cálculo.
8. **[E1–E5] Auditabilidade como ativo.** (a) Rodar o script de verdade e gerar
   `audit_report.csv`; (b) **corrigir bugs** (SKIP não conta como falha em
   `--strict`; Coreia e Rússia apontam para portal HTML, não PDF primário;
   adicionar `sha256`+`downloaded_at`); (c) publicar manifest+script+report em
   **Zenodo/OSF com DOI** (precisa de conta); (d) parágrafo metodológico + seção
   **"Disponibilidade de dados e código"** nas Declarações; (e) "Nota de
   reprodutibilidade" em caixa.

### Tier 3 — refino de forma
9. **[D3] Cortar o Quadro `quad:comparativo` (display)** — redundante com Fig.1 +
   Tabela 1 + Fig.2. **Reconciliação com [F1]:** manter os DADOS (nota de rodapé
   / suplementar) para computar o ρ; cortar só a tabela visível. Coluna "exame"
   migra para rodapé da Fig. 1.
10. **[D3/D5] Fig. 3:** rotular todos os pontos do cluster de alto IDH (0,91–0,96)
    ou restringir aos 11 países tabulados. **Fig. 2:** rotular todas as linhas ou
    declarar N na legenda.
11. **[F3] Contraponto internacional de reprovação** em cálculo universitário
    (D/F/W nos EUA etc.), com honestidade — reforça credibilidade A1.

### Cortes que financiam as adições (estamos no teto de 20 pág.)
- **[A/all] Seção 4.1** país-a-país (l.389–456) → 2–3 frases por continente
  (redundante com heatmap + Quadro 2). ~1–1,5 pág.
- **[F3] `\fbox` de exemplos** (Gaokao/ENEM) → 1 exemplo ou inline. ~0,5 pág.
  (já reduzidos de 4→2; agora reduzir mais).
- **[D3] Quadro `quad:comparativo`** (display) → rodapé. ~0,5–0,75 pág.
- **[E] Prosa "fonte primária/documentável"** repetida em 3 lugares (l.219,
  368–369, 686) → deduplicar.

---

## Conflito reconciliado
- **Design quer cortar `quad:comparativo`** × **Finanças usa seus dados p/ o ρ.**
  → Cortar a TABELA VISÍVEL; preservar os dados (rodapé/suplementar) e computar a
  correlação a partir deles. Sem perda de evidência.

## Decisões que dependem de você (escopo/forks)
1. **Título:** manter atual ou adotar o subtítulo construtivo sugerido
   (…"e um roteiro pedagógico para sua reintrodução…")?
2. **Quadro didático (item 6a):** adicioná-lo muda o caráter do artigo (mais
   "how-to"). Aprovar?
3. **DOI de dados/código (item 8c):** publicar em Zenodo/OSF exige sua conta —
   fazer agora ou deixar stub ("disponível mediante solicitação")?
4. **Autoria:** Bolema não limita nº de autores nem exige ORCID — confirmar
   composição (Chalhoub/Korte/Rolim?).

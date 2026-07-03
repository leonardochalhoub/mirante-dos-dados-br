# Brief do Conselho — Rodada 3 (avaliação final + probabilidade de aprovação)

Todas as recomendações da R2 foram implementadas. Pedimos: (1) veredito final;
(2) **estimativa da probabilidade de aprovação e publicação no Bolema**, com
raciocínio, ancorada no que a revista de fato publica (corpus dos 2 últimos
volumes analisado por nós).

## Arquivos
- Artigo final: `articles/calculo-bolema-submissao.tex` / `.pdf` (20 pág.) / `.docx`
- Template oficial: `TEMPLATE_BOLEMA_PT-2025.docx` (raiz)
- Corpus publicado (n=77, 2 últimos volumes): `articles/bolema-corpus/` +
  `form_profile.csv` + `priorart_scan.csv`
- Reprodutibilidade: repo público + espelho anônimo
  `https://anonymous.4open.science/r/calculo-ausente-repro/`

## O que mudou desde a R2 (todas as suas recomendações)
- **Admin:** Quadro CPA estendido à integral (área→Riemann→integral definida→TFC),
  fechando a assimetria com o título "roteiro pedagógico".
- **Finanças:** `compute_pisa_correlations.py` público; ρ recodificado = −0,08 (n.s.);
  terminologia obrigatório/eletivo corrigida; ressalva do r_pb (Brasil n=1).
- **Engenharia:** auditabilidade 100% (11/11 fontes oficiais, SHA-256, `--strict`
  exit 0, Brasil=0); `requirements-audit.txt`; manifest v2.1 (input imutável);
  repo público + espelho anônimo 4open para verificação durante a revisão cega.
- **Design:** figuras (contraste WCAG da Fig.1, México reclassificado); **docx
  reconstruído conforme o template** (TNR, A4, recuo 1,25, keywords, legendas
  "Quadro/Figura N –", seções numeradas). Verificado sem vazamento de identidade.
- **Prior-art:** nenhum artigo do Bolema ocupa a tese (verificado no corpus + arquivo).

## Pedido de parecer (≤1 página cada)
1. Restou **algum** motivo de recusa na sua lente? Se sim, qual e quão grave.
2. **Veredito final** (aceitar / aceitar c/ correções menores / reformular / recusar).
3. **Probabilidade estimada de aprovação e publicação no Bolema (0–100%)**, com
   o raciocínio: compare com o padrão do corpus publicado (forma, rigor, tema,
   profundidade teórica) e considere que o Bolema é A1 e competitivo. Seja
   honesto — não infle. Dê um intervalo se preferir.

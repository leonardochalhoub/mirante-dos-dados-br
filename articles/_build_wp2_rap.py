# -*- coding: utf-8 -*-
"""Transforma bolsa-familia.tex (Working Paper) -> wp2-rap.tex (formato RAP).
Mudanças: margens RAP, cabeçalho de manuscrito com 4 autores, resumo/abstract/
resumen trilíngue (<=250 palavras, sem citações), 3-5 palavras-chave por idioma,
conversão ABNT-numerado -> APA 7 (in-text autor-data + lista de referências),
remoção de capa/sumário/listas. Saída compilada com tectonic.
"""
import re

SRC = "bolsa-familia.tex"
OUT = "wp2-rap.tex"

t = open(SRC, encoding="utf-8").read()

# ---------------------------------------------------------------- 1. geometria
t = t.replace(
    r"\usepackage[a4paper,top=3cm,bottom=2cm,left=3cm,right=2cm]{geometry}",
    r"\usepackage[a4paper,top=2.5cm,bottom=2.5cm,left=3cm,right=3cm]{geometry}",
)

# ----------------------------------------------------- 2. capa -> cabeçalho RAP
header = r"""\begin{center}{\LARGE\bfseries Três regimes, um programa: documentação, identificação causal e equidade do Bolsa Família\par}\end{center}

\begin{center}{\large\itshape Three regimes, one program: documentation, causal identification, and equity of Bolsa Família\par}\end{center}

\begin{center}{\large\itshape Tres regímenes, un programa: documentación, identificación causal y equidad de Bolsa Família\par}\end{center}

\begin{center}{\large Leonardo Chalhoub\textsuperscript{1,*},~Jefferson Korte Junior\textsuperscript{2},~Alexandre Maciel Rolim\textsuperscript{3},~Luis Fernando Kranz\textsuperscript{4}\par}\end{center}

\begin{center}{\footnotesize\textsuperscript{1} Pesquisador independente, Porto Alegre, RS, Brasil. ORCID: 0000-0003-0484-158X. E-mail: leonardochalhoub@gmail.com\par}\end{center}

\begin{center}{\footnotesize\textsuperscript{2} Universidade Tecnológica Federal do Paraná (UTFPR), PR, Brasil. ORCID: 0009-0006-9466-9830. E-mail: jefferson.2024@alunos.utfpr.br\par}\end{center}

\begin{center}{\footnotesize\textsuperscript{3} Pesquisador independente, Florianópolis, SC, Brasil. ORCID: 0000-0001-9919-122X. E-mail: alexandremrolim@gmail.com\par}\end{center}

\begin{center}{\footnotesize\textsuperscript{4} Universidade Federal do Rio Grande do Sul (UFRGS), Porto Alegre, RS, Brasil. ORCID: [a inserir]. E-mail: [a inserir]\par}\end{center}

\begin{center}{\footnotesize\textsuperscript{*} Autor correspondente.\par}\end{center}

\vspace{6pt}
"""
t = re.sub(r"\\begin\{titlepage\}.*?\\end\{titlepage\}", lambda m: header, t, flags=re.S)

# ------------------------------------------- 3. front-matter trilíngue (resumo)
pt = ("Este trabalho analisa o Bolsa Família entre 2013 e 2025, integrando três "
"dimensões usualmente tratadas em separado: documentação reproduzível dos "
"microdados, identificação causal das transições institucionais e equidade "
"distributiva. Consolidam-se microdados mensais do Portal da Transparência "
"(mais de 2,2 bilhões de registros) em painel estado$\\times$ano, via "
"arquitetura \\textit{medallion}, com deflação pelo IPCA (base dezembro de "
"2021). A identificação causal articula diferenças-em-diferenças e efeitos "
"fixos de dois sentidos sobre a Medida Provisória 1.061/2021 e a Lei "
"14.601/2023, com inferência robusta por \\textit{wild-cluster bootstrap}, "
"testes de tendências paralelas, placebo e \\textit{leave-one-out}. A equidade "
"é medida pelo índice de Kakwani, ordenado pelo IDH municipal, e por um índice "
"de necessidade. Um \\textit{benchmark} internacional compara o programa a "
"quatro transferências condicionadas latino-americanas em dólares PPC. Em "
"termos reais, o gasto cresceu 283\\,\\% entre 2018 e 2024 e o valor por "
"beneficiário, 181\\,\\%. O efeito causal é grande sob erros HC3, mas "
"indistinguível de zero sob \\textit{bootstrap} robusto, e o teste de "
"tendências paralelas é rejeitado --- ilustrando o ônus identificacional com "
"poucos \\textit{clusters}. O índice de Kakwani confirma a progressividade do "
"programa, porém decrescente entre regimes; o índice de necessidade revela que "
"estados líderes em valor per capita estão subatendidos frente à intensidade "
"local da pobreza. O artigo publica o \\textit{pipeline}, os dados e os testes "
"automatizados, viabilizando reprodução integral.")

en = ("This paper analyzes Brazil's Bolsa Família program between 2013 and 2025, "
"integrating three dimensions usually treated separately: reproducible "
"microdata documentation, causal identification of the institutional "
"transitions, and distributive equity. Monthly microdata from the federal "
"Transparency Portal (over 2.2 billion records) are consolidated into a "
"state-by-year panel through a \\textit{medallion} architecture, deflated by "
"the IPCA index (December 2021 base). Causal identification combines "
"difference-in-differences and two-way fixed-effects estimators on Provisional "
"Measure 1.061/2021 and Law 14.601/2023, with robust inference via "
"\\textit{wild-cluster bootstrap}, parallel-trends tests, placebo, and "
"\\textit{leave-one-out} checks. Equity is measured with the Kakwani index "
"ranked by the municipal Human Development Index and with a need index. An "
"international benchmark compares the program with four Latin American "
"conditional cash transfers in PPP dollars. In real terms, spending grew "
"283\\,\\% between 2018 and 2024 and the per-beneficiary value grew 181\\,\\%. "
"The causal effect is large under HC3 errors but indistinguishable from zero "
"under robust \\textit{bootstrap}, and the parallel-trends test is rejected "
"--- illustrating the identification burden with few \\textit{clusters}. The "
"Kakwani index confirms the program's progressivity, although it declines "
"across regimes; the need index reveals that states leading in per-capita "
"value are underprovisioned relative to local poverty intensity. The paper "
"releases the pipeline, dataset, and automated tests, enabling full "
"reproduction.")

es = ("Este trabajo analiza el programa Bolsa Família entre 2013 y 2025 integrando "
"tres dimensiones habitualmente tratadas por separado: documentación "
"reproducible de los microdatos, identificación causal de las transiciones "
"institucionales y equidad distributiva. Se consolidan microdatos mensuales "
"del Portal de la Transparencia (más de 2,2 mil millones de registros) en un "
"panel estado$\\times$año, mediante una arquitectura \\textit{medallion}, con "
"deflación por el IPCA (base diciembre de 2021). La identificación causal "
"combina diferencias-en-diferencias y efectos fijos de dos vías sobre la "
"Medida Provisional 1.061/2021 y la Ley 14.601/2023, con inferencia robusta "
"por \\textit{wild-cluster bootstrap}, pruebas de tendencias paralelas, "
"placebo y \\textit{leave-one-out}. La equidad se mide con el índice de "
"Kakwani, ordenado por el IDH municipal, y con un índice de necesidad. Un "
"\\textit{benchmark} internacional compara el programa con cuatro "
"transferencias monetarias condicionadas latinoamericanas en dólares PPA. En "
"términos reales, el gasto creció 283\\,\\% entre 2018 y 2024 y el valor por "
"beneficiario, 181\\,\\%. El efecto causal es grande con errores HC3, pero "
"indistinguible de cero bajo \\textit{bootstrap} robusto, y la prueba de "
"tendencias paralelas se rechaza, ilustrando la carga de identificación con "
"pocos \\textit{clusters}. El índice de Kakwani confirma la progresividad del "
"programa, aunque decreciente entre regímenes; el índice de necesidad revela "
"que los estados líderes en valor per cápita están subatendidos frente a la "
"intensidad local de la pobreza. El artículo publica el \\textit{pipeline}, "
"los datos y las pruebas automatizadas, permitiendo su reproducción integral.")

front = (
r"\section*{Resumo}" "\n"
r"\begin{singlespace}\small\noindent" "\n" + pt + "\n\n"
r"\vspace{6pt}\noindent\textbf{Palavras-chave:} Bolsa Família; transferência condicionada de renda; avaliação de políticas públicas; equidade distributiva; reprodutibilidade." "\n"
r"\end{singlespace}" "\n\n"
r"\vspace{6pt}" "\n"
r"\section*{Abstract}" "\n"
r"\begin{singlespace}\small\noindent" "\n" + en + "\n\n"
r"\vspace{6pt}\noindent\textbf{Keywords:} Bolsa Família; conditional cash transfers; public policy evaluation; distributive equity; reproducibility." "\n"
r"\end{singlespace}" "\n\n"
r"\vspace{6pt}" "\n"
r"\section*{Resumen}" "\n"
r"\begin{singlespace}\small\noindent" "\n" + es + "\n\n"
r"\vspace{6pt}\noindent\textbf{Palabras clave:} Bolsa Família; transferencias monetarias condicionadas; evaluación de políticas públicas; equidad distributiva; reproducibilidad." "\n"
r"\end{singlespace}" "\n\n"
r"\clearpage" "\n\n"
)
t = re.sub(r"\\section\*\{Resumo\}.*?(?=\\section\{Introdu)", lambda m: front, t, flags=re.S)

# ----------------------------------------------------- 4. citações APA (in-text)
amp = "\\&"
apa = {
 "armbrust": "Armbrust et al., 2021",
 "atlas-brasil": "PNUD et al., 2013",
 "bcb-sgs": "Banco Central do Brasil, 2024",
 "breiman": "Breiman, 2001",
 "cameron": "Cameron et al., 2008",
 "hastie": "Hastie et al., 2009",
 "hoffmann": "Hoffmann, 2006",
 "pedregosa": "Pedregosa et al., 2011",
 "rasella": "Rasella et al., 2013",
 "rocha": "Rocha, 2008",
 "campello": "Campello " + amp + " Neri, 2013",
 "cepal": "CEPAL, 2024",
 "cgu": "CGU, 2025",
 "fiszbein": "Fiszbein " + amp + " Schady, 2009",
 "ibge-pnad": "IBGE, 2019",
 "ibge-sidra": "IBGE, 2024",
 "kakwani": "Kakwani, 1977",
 "kukreja": "Kukreja, 2021",
 "paes-sousa": "Paes-Sousa et al., 2011",
 "roth": "Roth, 2022",
 "soares": "Soares, 2010",
 "wb-aspire": "World Bank, 2024a",
 "wb-icp": "World Bank, 2024b",
 "wilkinson": "Wilkinson et al., 2016",
 "zaharia": "Zaharia et al., 2016",
}

# caso especial: "Kakwani (1977)" já é autor-data -> evita duplicação
t = t.replace(r"\textbf{Kakwani (1977)}\,[\ref{ref:kakwani}]",
              r"\textbf{Índice de Kakwani} (Kakwani, 1977)")

def repl(m):
    keys = re.findall(r"ref:([a-z0-9\-]+)", m.group(0))
    cites = "; ".join(apa[k] for k in keys)
    return " (" + cites + ")"

t = re.sub(r"\\,?\s*\[\s*\\ref\{ref:[a-z0-9\-]+\}(?:\s*,\s*\\ref\{ref:[a-z0-9\-]+\})*\s*\]",
           repl, t)

# ------------------------------------------------------ 5. referências APA 7
refs = r"""\section*{Referências}
\begin{singlespace}\small
\newcommand{\refitem}{\par\smallskip\noindent\hangindent=1.25cm\hangafter=1\relax}

\refitem Armbrust, M., Ghodsi, A., Xin, R., \& Zaharia, M. (2021). Lakehouse: A new generation of open platforms that unify data warehousing and advanced analytics. In \textit{11th Annual Conference on Innovative Data Systems Research (CIDR)}.

\refitem Banco Central do Brasil. (2024). \textit{Sistema Gerenciador de Séries Temporais --- série 433 (IPCA)} [Conjunto de dados]. \url{https://api.bcb.gov.br/dados/serie/bcdata.sgs.433/dados}

\refitem Breiman, L. (2001). Random forests. \textit{Machine Learning, 45}(1), 5--32.

\refitem Cameron, A. C., Gelbach, J. B., \& Miller, D. L. (2008). Bootstrap-based improvements for inference with clustered errors. \textit{The Review of Economics and Statistics, 90}(3), 414--427.

\refitem Campello, T., \& Neri, M. C. (Orgs.). (2013). \textit{Programa Bolsa Família: uma década de inclusão e cidadania}. IPEA.

\refitem CEPAL --- Comisión Económica para América Latina y el Caribe. (2024). \textit{Panorama social de América Latina y el Caribe 2024}. CEPAL. \url{https://www.cepal.org/es/publicaciones/panoramasocial}

\refitem CGU --- Controladoria-Geral da União. (2025). \textit{Portal da Transparência: microdados de pagamentos do Bolsa Família, Auxílio Brasil e Novo Bolsa Família} [Conjunto de dados]. \url{https://portaldatransparencia.gov.br/download-de-dados/bolsa-familia-pagamentos}

\refitem Fiszbein, A., \& Schady, N. (2009). \textit{Conditional cash transfers: Reducing present and future poverty}. World Bank.

\refitem Hastie, T., Tibshirani, R., \& Friedman, J. (2009). \textit{The elements of statistical learning} (2nd ed.). Springer.

\refitem Hoffmann, R. (2006). Transferências de renda e a redução da desigualdade no Brasil e cinco regiões entre 1997 e 2004. \textit{Econômica, 8}(1), 55--81.

\refitem IBGE --- Instituto Brasileiro de Geografia e Estatística. (2019). \textit{Pesquisa Nacional por Amostra de Domicílios Contínua (PNAD-C) --- Tabela 6688} [Conjunto de dados]. \url{https://sidra.ibge.gov.br/tabela/6688}

\refitem IBGE --- Instituto Brasileiro de Geografia e Estatística. (2024). \textit{SIDRA --- Tabela 6579: população residente estimada} [Conjunto de dados]. \url{https://sidra.ibge.gov.br/tabela/6579}

\refitem Kakwani, N. C. (1977). Measurement of tax progressivity: An international comparison. \textit{The Economic Journal, 87}(345), 71--80.

\refitem Kukreja, M. (2021). \textit{Data engineering with Apache Spark, Delta Lake, and Lakehouse}. Packt Publishing.

\refitem Paes-Sousa, R., Santos, L. M. P., \& Quaresma, J. M. (Orgs.). (2011). \textit{Bolsa Família: avaliação de impacto e o desafio da intersetorialidade}. Ministério do Desenvolvimento Social.

\refitem Pedregosa, F., Varoquaux, G., Gramfort, A., Michel, V., Thirion, B., Grisel, O., \ldots Duchesnay, É. (2011). Scikit-learn: Machine learning in Python. \textit{Journal of Machine Learning Research, 12}, 2825--2830.

\refitem PNUD, IPEA, \& Fundação João Pinheiro. (2013). \textit{Atlas do desenvolvimento humano no Brasil}. \url{http://atlasbrasil.org.br/}

\refitem Rasella, D., Aquino, R., Santos, C. A. T., Paes-Sousa, R., \& Barreto, M. L. (2013). Effect of a conditional cash transfer programme on childhood mortality: A nationwide analysis of Brazilian municipalities. \textit{The Lancet, 382}(9886), 57--64.

\refitem Rocha, S. (2008). Transferências de renda federais: focalização e impactos sobre pobreza e desigualdade. \textit{Revista de Economia Contemporânea, 12}(1), 67--96.

\refitem Roth, J. (2022). Pretest with caution: Event-study estimates after testing for parallel trends. \textit{American Economic Review: Insights, 4}(3), 305--322.

\refitem Soares, F. V. (2010). \textit{Bolsa Família, its design, its impacts and possibilities for the future} (Working Paper No. 137). International Policy Centre for Inclusive Growth.

\refitem Wilkinson, M. D., Dumontier, M., Aalbersberg, I. J., Appleton, G., Axton, M., Baak, A., \ldots Mons, B. (2016). The FAIR Guiding Principles for scientific data management and stewardship. \textit{Scientific Data, 3}, 160018. \url{https://doi.org/10.1038/sdata.2016.18}

\refitem World Bank. (2024a). \textit{ASPIRE: Atlas of Social Protection Indicators of Resilience and Equity} [Conjunto de dados]. \url{https://www.worldbank.org/en/data/datatopics/aspire}

\refitem World Bank. (2024b). \textit{International Comparison Program (ICP) 2021} [Conjunto de dados]. \url{https://www.worldbank.org/en/programs/icp}

\refitem Zaharia, M., Xin, R., Wendell, P., Das, T., Armbrust, M., Dave, A., \ldots Stoica, I. (2016). Apache Spark: A unified engine for big data processing. \textit{Communications of the ACM, 59}(11), 56--65.
\end{singlespace}
"""
t = re.sub(r"\\section\*\{Referências\}.*?\\end\{singlespace\}", lambda m: refs, t, flags=re.S)

open(OUT, "w", encoding="utf-8").write(t)

# checagem: nenhuma citação ABNT remanescente
left = re.findall(r"\\ref\{ref:[a-z0-9\-]+\}", t)
print("REF-numeradas remanescentes:", len(left), left[:5])
print("OK ->", OUT)

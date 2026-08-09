"""Gera o reference.docx usado pelo pandoc para estilizar o .docx da submissão PPP/IPEA.
Padrões PPP: A4, Times New Roman 12, espaço simples, margens sup/esq 3 cm, inf/dir 2 cm, justificado.
Uso: python articles/build-ppp-reference-docx.py
Saída: articles/ppp-reference.docx
"""
from docx import Document
from docx.shared import Pt, Cm, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_LINE_SPACING
from docx.enum.section import WD_SECTION
from docx.oxml.ns import qn

OUT = "articles/ppp-reference.docx"

doc = Document()

# ---- Página A4 e margens (sup/esq 3 cm; inf/dir 2 cm) ----
for section in doc.sections:
    section.page_height = Cm(29.7)
    section.page_width = Cm(21.0)
    section.top_margin = Cm(3)
    section.left_margin = Cm(3)
    section.bottom_margin = Cm(2)
    section.right_margin = Cm(2)

# ---- Estilo Normal: Times New Roman 12, espaço simples, justificado ----
normal = doc.styles["Normal"]
normal.font.name = "Times New Roman"
normal.font.size = Pt(12)
# garante a fonte também para caracteres complexos/leste-asiático
rpr = normal.element.get_or_add_rPr()
rfonts = rpr.get_or_add_rFonts()
for attr in ("w:ascii", "w:hAnsi", "w:cs"):
    rfonts.set(qn(attr), "Times New Roman")
pf = normal.paragraph_format
pf.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
pf.line_spacing_rule = WD_LINE_SPACING.SINGLE
pf.space_before = Pt(0)
pf.space_after = Pt(6)

# ---- Títulos: Times New Roman, tamanhos sóbrios, alinhados à esquerda ----
heading_sizes = {"Heading 1": 13, "Heading 2": 12, "Heading 3": 12, "Title": 16}
for name, size in heading_sizes.items():
    try:
        st = doc.styles[name]
    except KeyError:
        continue
    st.font.name = "Times New Roman"
    st.font.size = Pt(size)
    st.font.bold = True
    st.font.color.rgb = RGBColor(0, 0, 0)
    hrpr = st.element.get_or_add_rPr()
    hrfonts = hrpr.get_or_add_rFonts()
    for attr in ("w:ascii", "w:hAnsi", "w:cs"):
        hrfonts.set(qn(attr), "Times New Roman")
    st.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.LEFT
    st.paragraph_format.line_spacing_rule = WD_LINE_SPACING.SINGLE

doc.save(OUT)
print(f"✔ {OUT} — A4, Times New Roman 12, espaço simples, margens 3/3/2/2, justificado")

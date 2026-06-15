"""Build the REMat .docx from calculo-remat-submissao.tex (reproducible).

Pipeline: preprocess LaTeX -> pandoc -> patch styles (TNR12/1.5/headings)
-> title 14pt -> official REMat header/footer (page number).

Requires: pandoc (~/.local/bin), python-docx. Run:
    cd articles && python3 scripts/build_docx_remat.py
"""
from __future__ import annotations
import os, re, shutil, subprocess, zipfile
from pathlib import Path

ART = Path(__file__).resolve().parents[1]
TEX = ART / "calculo-remat-submissao.tex"
OUT = ART / "calculo-remat-submissao.docx"
PANDOC = os.path.expanduser("~/.local/bin/pandoc")
TITLE = ("O cálculo ausente: duzentos anos de currículo e uma comparação "
         "internacional no ensino médio")
# NB: sem cabeçalho/rodapé no arquivo da submissão (versão cega). O banner
# oficial da REMat (com nomes) só entra na versão final, após o aceite.


# ---------- 1. preprocess .tex for pandoc -------------------------------
def find_balanced(s, i):
    depth = 0
    while i < len(s):
        if s[i] == '{':
            depth += 1
        elif s[i] == '}':
            depth -= 1
            if depth == 0:
                return i
        i += 1
    return -1


def replace_cmd(s, cmd, fmt):
    out, i, tok = [], 0, "\\" + cmd + "{"
    while True:
        j = s.find(tok, i)
        if j < 0:
            out.append(s[i:]); break
        out.append(s[i:j])
        b = j + len(tok) - 1
        e = find_balanced(s, b)
        out.append(fmt(s[b + 1:e]))
        i = e + 1
    return "".join(out)


def unbox(s):
    out, i, tok = [], 0, "\\fbox{\\parbox{"
    while True:
        j = s.find(tok, i)
        if j < 0:
            out.append(s[i:]); break
        out.append(s[i:j])
        w = j + len("\\fbox{\\parbox")
        we = find_balanced(s, w)
        c = s.find("{", we)
        ce = find_balanced(s, c)
        inner = re.sub(r"^\\small\s*", "", s[c + 1:ce].strip())
        after = ce + 1
        if after < len(s) and s[after] == '}':
            after += 1
        out.append("\n\n" + inner + "\n\n")
        i = after
    return "".join(out)


def preprocess():
    s = TEX.read_text(encoding="utf-8")
    s = re.sub(r"\\newcommand\{\\fonte\}\[1\]\{[^\n]*\}\n", "", s)
    s = re.sub(r"\\newcommand\{\\refitem\}\[1\]\{[^\n]*\}\n", "", s)
    s = replace_cmd(s, "refitem", lambda x: "\n\n" + x.strip() + "\n\n")
    s = replace_cmd(s, "fonte", lambda x: "\n\n\\textit{Fonte: " + x.strip() + "}\n\n")
    s = unbox(s)
    s = re.sub(r"\\includegraphics(\[[^\]]*\])?\{(fig\d+[^}]*)\.pdf\}",
               r"\\includegraphics\1{figures-calculo/\2.png}", s)
    p = Path("/tmp/calculo_docx_src.tex")
    p.write_text(s, encoding="utf-8")
    return p


# ---------- 2. pandoc -> docx -------------------------------------------
def run_pandoc(src):
    subprocess.run([PANDOC, str(src), "-f", "latex", "-t", "docx",
                    "--resource-path", f"{ART}:{ART}/figures-calculo",
                    "-o", str(OUT)], check=True, cwd=ART)


# ---------- 3. patch styles.xml ----------------------------------------
def rpr(bold=True, caps=False):
    b = "<w:b /><w:bCs />" if bold else ""
    c = "<w:caps />" if caps else ""
    return ('<w:rPr><w:rFonts w:ascii="Times New Roman" w:hAnsi="Times New Roman" '
            'w:cs="Times New Roman" />' + b + c +
            '<w:color w:val="000000" /><w:sz w:val="24" /><w:szCs w:val="24" /></w:rPr>')


def patch_styles():
    z = zipfile.ZipFile(OUT)
    x = z.read("word/styles.xml").decode("utf-8")
    x = x.replace(
        '<w:rFonts w:asciiTheme="minorHAnsi" w:cstheme="minorBidi" w:eastAsiaTheme="minorHAnsi" w:hAnsiTheme="minorHAnsi" />',
        '<w:rFonts w:ascii="Times New Roman" w:hAnsi="Times New Roman" w:cs="Times New Roman" />')
    x = x.replace(
        '<w:pPrDefault>\n      <w:pPr>\n        <w:spacing w:after="200" />\n      </w:pPr>\n    </w:pPrDefault>',
        '<w:pPrDefault>\n      <w:pPr>\n        <w:spacing w:after="0" w:line="360" w:lineRule="auto" />\n        <w:jc w:val="both" />\n      </w:pPr>\n    </w:pPrDefault>')

    def ph(x, sid, bold, caps):
        pat = re.compile(r'(<w:style w:styleId="' + sid + r'" w:type="paragraph">.*?)<w:rPr>.*?</w:rPr>(\s*</w:style>)', re.S)
        return pat.sub(lambda m: m.group(1) + rpr(bold, caps) + m.group(2), x)

    x = ph(x, "Heading1", True, True)
    x = ph(x, "Heading2", True, False)
    x = ph(x, "Heading3", False, False)
    for n in (4, 5, 6, 7, 8, 9):
        x = ph(x, f"Heading{n}", True, False)

    tmp = Path("/tmp/_docx_work")
    shutil.rmtree(tmp, ignore_errors=True)
    z.extractall(tmp)
    (tmp / "word" / "styles.xml").write_text(x, encoding="utf-8")
    OUT.unlink()
    zo = zipfile.ZipFile(OUT, "w", zipfile.ZIP_DEFLATED)
    for root, _, files in os.walk(tmp):
        for fn in files:
            full = Path(root) / fn
            zo.write(full, full.relative_to(tmp))
    zo.close()


# ---------- 4. title 14pt + header/footer (python-docx) ----------------
def finish():
    import docx
    from docx.shared import Pt
    from docx.enum.text import WD_ALIGN_PARAGRAPH
    from docx.oxml.ns import qn
    from docx.oxml import OxmlElement

    d = docx.Document(str(OUT))

    def set_run(r, size, italic=False, bold=False):
        r.font.name = "Times New Roman"; r.font.size = Pt(size)
        r.font.italic = italic; r.font.bold = bold
        rprx = r._element.get_or_add_rPr()
        rf = rprx.find(qn('w:rFonts'))
        if rf is None:
            rf = OxmlElement('w:rFonts'); rprx.append(rf)
        for a in ('w:ascii', 'w:hAnsi', 'w:cs'):
            rf.set(qn(a), "Times New Roman")

    # title 14 (no header/footer in the blind submission file)
    for p in d.paragraphs:
        if "cálculo ausente" in p.text.lower() and "duzentos anos" in p.text.lower():
            for r in p.runs:
                set_run(r, 14, bold=True)
            break

    d.save(str(OUT))


if __name__ == "__main__":
    src = preprocess()
    run_pandoc(src)
    patch_styles()
    finish()
    print("built", OUT)

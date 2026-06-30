"""Corpus do Conselho do Mirante — manifesto (KB) + carregamento + chunking.

Fonte única de verdade sobre QUAIS documentos compõem a base de conhecimento
(KB) que os conselheiros consultam via RAG, e como cada arquivo é limpo e
quebrado em trechos (chunks) antes de ser indexado.

Usado tanto por build_index.py (construção do índice) quanto por server.py
(get_document / re-chunk para citação).
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

# Raiz do repositório (este arquivo vive em <repo>/conselho_mcp/corpus.py)
REPO_ROOT = Path(__file__).resolve().parent.parent

# ─── Manifesto do KB ────────────────────────────────────────────────────────
# Globs (relativos à raiz do repo) do corpus canônico. Tudo aqui é texto-fonte
# (.tex/.md), nunca PDF (PDFs são compilações redundantes dos .tex).
CORPUS_GLOBS: list[str] = [
    "articles/*.tex",          # Working Papers
    "docs/*.md",               # ARCHITECTURE, SUBMISSION_PLAN, design-system
    "docs/adrs/*.md",          # Architecture Decision Records
    "docs/conselho/*.md",      # pareceres e briefings do Conselho
]

# Arquivos a ignorar mesmo que casem com os globs (ruído/boilerplate).
EXCLUDE_NAMES = {"compile-stamp.tex", "README.md"}


def discover_paths() -> list[Path]:
    """Retorna os caminhos absolutos do corpus canônico, ordenados."""
    seen: dict[Path, None] = {}
    for pattern in CORPUS_GLOBS:
        for p in sorted(REPO_ROOT.glob(pattern)):
            if p.name in EXCLUDE_NAMES:
                continue
            seen.setdefault(p.resolve(), None)
    return list(seen.keys())


# ─── Limpeza de texto ───────────────────────────────────────────────────────
_TEX_PREAMBLE_RE = re.compile(r"\\begin\{document\}", re.IGNORECASE)
_TEX_COMMENT_RE = re.compile(r"(?<!\\)%.*$", re.MULTILINE)
_TEX_CMD_SIMPLE_RE = re.compile(r"\\(section|subsection|subsubsection|paragraph)\*?\{([^}]*)\}")
_TEX_STRIP_CMDS_RE = re.compile(r"\\[a-zA-Z@]+\*?(\[[^\]]*\])?(\{[^{}]*\})?")
_MULTISPACE_RE = re.compile(r"[ \t]+")
_MULTINEWLINE_RE = re.compile(r"\n{3,}")


def _clean_tex(text: str) -> str:
    """Remove preâmbulo e macros LaTeX, preservando títulos de seção como '## '."""
    m = _TEX_PREAMBLE_RE.search(text)
    if m:
        text = text[m.end():]
    text = _TEX_COMMENT_RE.sub("", text)
    # Promove títulos de seção a marcadores markdown-like para o chunker pegar
    text = _TEX_CMD_SIMPLE_RE.sub(lambda mm: f"\n## {mm.group(2)}\n", text)
    # Remove comandos restantes (\textbf{...}, \cite{...}, \usepackage, etc.)
    prev = None
    while prev != text:
        prev = text
        text = _TEX_STRIP_CMDS_RE.sub(r"\2", text)
    text = text.replace("{", "").replace("}", "")
    text = _MULTISPACE_RE.sub(" ", text)
    text = _MULTINEWLINE_RE.sub("\n\n", text)
    return text.strip()


def load_text(path: Path) -> str:
    """Carrega e limpa um arquivo do corpus (latin1-tolerante para .tex antigos)."""
    raw = path.read_text(encoding="utf-8", errors="replace")
    if path.suffix.lower() == ".tex":
        return _clean_tex(raw)
    return raw.strip()


# ─── Chunking ───────────────────────────────────────────────────────────────
@dataclass
class Chunk:
    doc_id: str        # caminho relativo ao repo (ex.: "docs/adrs/ADR-001-...md")
    section: str       # título da seção/heading mais próximo
    text: str
    ordinal: int       # índice do chunk dentro do documento

# Heading markdown (#..######) ou os '## ' que injetamos a partir do LaTeX.
_HEADING_RE = re.compile(r"^#{1,6}\s+(.*)$", re.MULTILINE)


def chunk_text(text: str, doc_id: str, target_words: int = 220, overlap_words: int = 40) -> list[Chunk]:
    """Quebra por seção (headings) e depois em janelas de ~target_words palavras.

    Mantém o título da seção corrente para citação ('arquivo · seção').
    """
    # Particiona em (titulo_secao, corpo) usando as posições dos headings.
    sections: list[tuple[str, str]] = []
    last_end = 0
    current_title = "(introdução)"
    for m in _HEADING_RE.finditer(text):
        body = text[last_end:m.start()].strip()
        if body:
            sections.append((current_title, body))
        current_title = m.group(1).strip() or current_title
        last_end = m.end()
    tail = text[last_end:].strip()
    if tail:
        sections.append((current_title, tail))
    if not sections:
        sections = [("(documento)", text.strip())]

    chunks: list[Chunk] = []
    ordinal = 0
    for title, body in sections:
        words = body.split()
        if not words:
            continue
        step = max(1, target_words - overlap_words)
        for start in range(0, len(words), step):
            window = words[start:start + target_words]
            if not window:
                continue
            chunks.append(Chunk(doc_id=doc_id, section=title, text=" ".join(window), ordinal=ordinal))
            ordinal += 1
            if start + target_words >= len(words):
                break
    return chunks


def rel_id(path: Path) -> str:
    """Caminho relativo à raiz do repo, usado como doc_id estável."""
    return str(path.resolve().relative_to(REPO_ROOT))

"""Corpus do Bolsa Família Knowledge Hub — manifesto (KB) + carregamento + chunking.

Mesmo padrão de `conselho_mcp/corpus.py` (limpeza de .tex, chunking por seção),
mas com um manifesto próprio: o artigo que estamos tentando publicar (WP2 PPP),
ADRs de arquitetura, a documentação externa curada (Databricks/Delta/Spark/
CGU/IBGE) e os metadados extraídos do Unity Catalog (uc_metadata.py).

Usado tanto por build_index.py (indexação no Qdrant) quanto por server.py
(get_document / re-chunk para citação).
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
HUB_ROOT = Path(__file__).resolve().parent

# ─── Manifesto do KB ────────────────────────────────────────────────────────
# Globs relativos à raiz do repo. O artigo (wp2-ppp) é o "nosso" texto — o que
# estamos tentando publicar; ADRs/pipelines README documentam as decisões de
# engenharia; docs_sources/ é a documentação externa curada (Databricks, Delta,
# Spark, CGU, IBGE) + os comentários extraídos do Unity Catalog.
CORPUS_GLOBS: list[str] = [
    "articles/wp2-ppp.tex",                    # Working Paper — texto completo
    "articles/wp2-ppp.frontmatter.md",         # título/resumo/autores/keywords
    "articles/wp2-ppp.references-abnt.md",     # referências citadas
    "docs/ARCHITECTURE.md",                    # arquitetura geral do Mirante
    "docs/adrs/*.md",                          # Architecture Decision Records
    "pipelines/README.md",                     # visão geral do Asset Bundle
    "bolsa_familia_hub/docs_sources/**/*.md",  # docs externas curadas + UC metadata
]

EXCLUDE_NAMES = {"compile-stamp.tex", "README.md"}
# README.md é excluído globalmente (índice, sem conteúdo substantivo), exceto
# pipelines/README.md que é explicitamente listado acima.
_ALWAYS_INCLUDE = {"pipelines/README.md"}


def discover_paths() -> list[Path]:
    """Retorna os caminhos absolutos do corpus canônico, ordenados."""
    seen: dict[Path, None] = {}
    for pattern in CORPUS_GLOBS:
        for p in sorted(REPO_ROOT.glob(pattern)):
            rel = str(p.resolve().relative_to(REPO_ROOT))
            if p.name in EXCLUDE_NAMES and rel not in _ALWAYS_INCLUDE:
                continue
            seen.setdefault(p.resolve(), None)
    return list(seen.keys())


# ─── Limpeza de texto (idêntico ao conselho_mcp, .tex precisa do mesmo tratamento) ──
_TEX_PREAMBLE_RE = re.compile(r"\\begin\{document\}", re.IGNORECASE)
_TEX_COMMENT_RE = re.compile(r"(?<!\\)%.*$", re.MULTILINE)
_TEX_CMD_SIMPLE_RE = re.compile(r"\\(section|subsection|subsubsection|paragraph)\*?\{([^}]*)\}")
_TEX_STRIP_CMDS_RE = re.compile(r"\\[a-zA-Z@]+\*?(\[[^\]]*\])?(\{[^{}]*\})?")
_MULTISPACE_RE = re.compile(r"[ \t]+")
_MULTINEWLINE_RE = re.compile(r"\n{3,}")


def _clean_tex(text: str) -> str:
    m = _TEX_PREAMBLE_RE.search(text)
    if m:
        text = text[m.end():]
    text = _TEX_COMMENT_RE.sub("", text)
    text = _TEX_CMD_SIMPLE_RE.sub(lambda mm: f"\n## {mm.group(2)}\n", text)
    prev = None
    while prev != text:
        prev = text
        text = _TEX_STRIP_CMDS_RE.sub(r"\2", text)
    text = text.replace("{", "").replace("}", "")
    text = _MULTISPACE_RE.sub(" ", text)
    text = _MULTINEWLINE_RE.sub("\n\n", text)
    return text.strip()


def load_text(path: Path) -> str:
    raw = path.read_text(encoding="utf-8", errors="replace")
    if path.suffix.lower() == ".tex":
        return _clean_tex(raw)
    return raw.strip()


# ─── Chunking ───────────────────────────────────────────────────────────────
@dataclass
class Chunk:
    doc_id: str
    section: str
    text: str
    ordinal: int


_HEADING_RE = re.compile(r"^#{1,6}\s+(.*)$", re.MULTILINE)


def chunk_text(text: str, doc_id: str, target_words: int = 220, overlap_words: int = 40) -> list[Chunk]:
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
    return str(path.resolve().relative_to(REPO_ROOT))

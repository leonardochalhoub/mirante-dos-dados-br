"""Constrói o índice vetorial RAG do corpus do Conselho (embeddings locais).

Uso:
    conda activate dev-env
    python conselho_mcp/build_index.py

Gera em conselho_mcp/index/:
    embeddings.npy   matriz float32 (n_chunks, dim), L2-normalizada
    chunks.jsonl     metadata por chunk (doc_id, section, text, ordinal)
    meta.json        modelo usado, dim, contagens, prefixo de embedding

Modelo: intfloat/multilingual-e5-small (384-d, forte em PT, ~118 MB).
e5 exige prefixos "query: " / "passage: " — passagens usam "passage: ".
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from corpus import Chunk, chunk_text, discover_paths, load_text, rel_id

MODEL_NAME = "intfloat/multilingual-e5-small"
INDEX_DIR = Path(__file__).resolve().parent / "index"


def build() -> None:
    paths = discover_paths()
    if not paths:
        raise SystemExit("Nenhum documento encontrado — confira CORPUS_GLOBS em corpus.py")

    all_chunks: list[Chunk] = []
    for p in paths:
        text = load_text(p)
        if not text.strip():
            continue
        all_chunks.extend(chunk_text(text, doc_id=rel_id(p)))

    print(f"{len(paths)} documentos → {len(all_chunks)} chunks")

    # Import tardio: só precisa do torch/ST na construção, não no import do módulo.
    from sentence_transformers import SentenceTransformer

    model = SentenceTransformer(MODEL_NAME)
    passages = [f"passage: {c.text}" for c in all_chunks]
    emb = model.encode(
        passages,
        batch_size=32,
        normalize_embeddings=True,
        show_progress_bar=True,
        convert_to_numpy=True,
    ).astype(np.float32)

    INDEX_DIR.mkdir(parents=True, exist_ok=True)
    np.save(INDEX_DIR / "embeddings.npy", emb)
    with (INDEX_DIR / "chunks.jsonl").open("w", encoding="utf-8") as fh:
        for c in all_chunks:
            fh.write(json.dumps(c.__dict__, ensure_ascii=False) + "\n")
    (INDEX_DIR / "meta.json").write_text(
        json.dumps(
            {
                "model": MODEL_NAME,
                "dim": int(emb.shape[1]),
                "n_chunks": len(all_chunks),
                "n_docs": len(paths),
                "query_prefix": "query: ",
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    print(f"Índice salvo em {INDEX_DIR} (dim={emb.shape[1]})")


if __name__ == "__main__":
    build()

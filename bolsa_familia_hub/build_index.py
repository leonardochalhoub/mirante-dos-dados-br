"""Constrói o índice Memory (RAG) do Bolsa Família Knowledge Hub — Qdrant.

Uso:
    conda activate dev-env
    docker compose -f bolsa_familia_hub/docker-compose.yml up -d qdrant
    python bolsa_familia_hub/build_index.py

Mesmo modelo de embedding do conselho_mcp: intfloat/multilingual-e5-small
(384-d, forte em PT). e5 exige prefixos "query: " / "passage: " — passagens
usam "passage: ", consultas usam "query: " (ver server.py::search_memory).

Roda de novo sempre que o corpus mudar (artigo, ADRs, docs_sources/, ou após
uc_metadata.py atualizar os comentários do Unity Catalog).
"""
from __future__ import annotations

import config
from corpus import Chunk, chunk_text, discover_paths, load_text, rel_id

MODEL_NAME = config.EMBEDDING_MODEL


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

    print(f"{len(paths)} documentos -> {len(all_chunks)} chunks")

    from sentence_transformers import SentenceTransformer
    from qdrant_client import QdrantClient
    from qdrant_client.models import Distance, PointStruct, VectorParams

    model = SentenceTransformer(MODEL_NAME)
    passages = [f"passage: {c.text}" for c in all_chunks]
    emb = model.encode(
        passages,
        batch_size=32,
        normalize_embeddings=True,
        show_progress_bar=True,
        convert_to_numpy=True,
    )

    client = QdrantClient(host=config.QDRANT_HOST, port=config.QDRANT_PORT)
    if client.collection_exists(config.QDRANT_COLLECTION):
        client.delete_collection(config.QDRANT_COLLECTION)
    client.create_collection(
        collection_name=config.QDRANT_COLLECTION,
        vectors_config=VectorParams(size=emb.shape[1], distance=Distance.COSINE),
    )

    points = [
        PointStruct(
            id=i,
            vector=emb[i].tolist(),
            payload={
                "doc_id": c.doc_id,
                "section": c.section,
                "text": c.text,
                "ordinal": c.ordinal,
            },
        )
        for i, c in enumerate(all_chunks)
    ]
    client.upsert(collection_name=config.QDRANT_COLLECTION, points=points)

    print(
        f"Coleção '{config.QDRANT_COLLECTION}' indexada em "
        f"{config.QDRANT_HOST}:{config.QDRANT_PORT} (dim={emb.shape[1]}, {len(points)} pontos)"
    )


if __name__ == "__main__":
    build()

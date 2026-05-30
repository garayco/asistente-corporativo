import json
import logging
import uuid

import requests
from qdrant_client import QdrantClient
from qdrant_client.http.models import Distance, PointStruct, VectorParams

from config import (
    DATASET_CHUNKED_PATH, EMBEDDING_BATCH_SIZE, EMBEDDING_DIM,
    EMBEDDING_MODEL, LOCALAI_API_KEY, LOCALAI_BASE_URL,
    QDRANT_API_KEY, QDRANT_COLLECTION, QDRANT_URL,
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s", datefmt="%H:%M:%S")
log = logging.getLogger(__name__)


def load_chunks(path=None):
    file_path = path or str(DATASET_CHUNKED_PATH)
    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    log.info("📄 %d chunks cargados desde %s", len(data), file_path)
    return data


def get_embeddings(texts):
    headers = {"Content-Type": "application/json"}
    if LOCALAI_API_KEY:
        headers["Authorization"] = f"Bearer {LOCALAI_API_KEY}"

    resp = requests.post(
        f"{LOCALAI_BASE_URL}/embeddings",
        json={"model": EMBEDDING_MODEL, "input": texts},
        headers=headers, timeout=120,
    )
    resp.raise_for_status()
    items = sorted(resp.json()["data"], key=lambda x: x["index"])
    return [item["embedding"] for item in items]


def main():
    chunks = load_chunks()

    # Generar embeddings en batches
    vectors = []
    total = len(chunks)
    for i in range(0, total, EMBEDDING_BATCH_SIZE):
        batch = [c["contenido"] for c in chunks[i:i + EMBEDDING_BATCH_SIZE]]
        vectors.extend(get_embeddings(batch))
        log.info("🔢 Embeddings: %d/%d", len(vectors), total)

    # Crear colección y subir puntos a Qdrant
    client = QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY)

    if client.collection_exists(QDRANT_COLLECTION):
        client.delete_collection(QDRANT_COLLECTION)

    client.create_collection(
        collection_name=QDRANT_COLLECTION,
        vectors_config=VectorParams(size=EMBEDDING_DIM, distance=Distance.COSINE),
    )

    points = [
        PointStruct(
            id=str(uuid.uuid5(uuid.NAMESPACE_URL, f"{c['source_url']}#{i}")),
            vector=v,
            payload={"contenido": c["contenido"], "source_url": c["source_url"], "topic": c["topic"]},
        )
        for i, (c, v) in enumerate(zip(chunks, vectors))
    ]

    client.upsert(collection_name=QDRANT_COLLECTION, points=points)
    log.info("✅ %d puntos indexados en '%s'", len(points), QDRANT_COLLECTION)


if __name__ == "__main__":
    main()

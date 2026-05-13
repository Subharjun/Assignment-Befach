import chromadb
from chromadb.config import Settings as ChromaSettings
from app.core.config import get_settings


class Vector:
    client: chromadb.api.ClientAPI | None = None
    collection = None


def init_chroma() -> None:
    s = get_settings()
    Vector.client = chromadb.PersistentClient(
        path=s.CHROMA_PERSIST_DIR,
        settings=ChromaSettings(anonymized_telemetry=False),
    )
    Vector.collection = Vector.client.get_or_create_collection(
        name=s.CHROMA_COLLECTION,
        metadata={"hnsw:space": "cosine"},
    )


def get_collection():
    assert Vector.collection is not None, "Chroma not initialised"
    return Vector.collection

"""
Owns the single ChromaDB collection the whole app reads and writes.

Both the ingestion script and the Flask app import get_vectorstore() and get
back the same kind of object pointed at the same on-disk collection
(config.CHROMA_PATH). The Flask app only ever reads from it; only
ingestion/ingest.py adds or deletes vectors.
"""
from langchain_chroma import Chroma

import config
from rag.embeddings import get_embedding_model

_vectorstore = None


def get_vectorstore():
    global _vectorstore
    if _vectorstore is None:
        _vectorstore = Chroma(
            collection_name=config.COLLECTION_NAME,
            embedding_function=get_embedding_model(),
            persist_directory=config.CHROMA_PATH,
            # Cosine distance makes the similarity math in rag/retriever.py
            # simple: similarity = 1 - distance. This only takes effect the
            # first time the collection is created.
            collection_metadata={"hnsw:space": "cosine"},
        )
    return _vectorstore

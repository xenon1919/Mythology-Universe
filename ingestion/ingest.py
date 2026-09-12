"""
Builds the ChromaDB knowledge base from the documents in data/.

Run this once, and again any time you add or change files in data/:

    uv run python -m ingestion.ingest

The Flask app (app.py) never writes to ChromaDB - it only reads the
collection this script creates. That split is intentional: embedding
documents is slow and should happen offline, not on every user request or
every server restart.
"""
import config
from ingestion.loader import load_documents
from ingestion.splitter import split_documents
from rag.vectorstore import get_vectorstore


def main():
    print(f"Loading documents from {config.DATA_DIR} ...")
    documents = load_documents()
    print(f"Loaded {len(documents)} source documents.")

    if not documents:
        print("No documents found. Add .txt files under data/<category>/ and try again.")
        return

    chunks = split_documents(documents)
    print(f"Split into {len(chunks)} chunks (chunk_size={config.CHUNK_SIZE}, overlap={config.CHUNK_OVERLAP}).")

    print("Generating embeddings and writing to ChromaDB (first run downloads the embedding model)...")
    vectorstore = get_vectorstore()

    existing = vectorstore.get()
    if existing["ids"]:
        print(f"Clearing {len(existing['ids'])} previously indexed chunks before re-ingesting ...")
        vectorstore.delete(ids=existing["ids"])

    ids = [f"chunk-{i}" for i in range(len(chunks))]
    vectorstore.add_documents(chunks, ids=ids)

    print(f"Done. {len(chunks)} chunks stored in collection '{config.COLLECTION_NAME}' at {config.CHROMA_PATH}")


if __name__ == "__main__":
    main()

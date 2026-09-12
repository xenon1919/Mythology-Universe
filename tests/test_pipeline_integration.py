"""
An end-to-end check of the non-LLM half of the RAG pipeline: load a document,
chunk it, embed it into a throwaway ChromaDB collection, and confirm semantic
search actually finds it. This never calls Groq, so it needs no API key -
it's only verifying that ingestion and retrieval agree with each other.
"""
import config
import rag.vectorstore as vectorstore_module
from ingestion.loader import load_documents
from ingestion.splitter import split_documents
from rag.retriever import retrieve

SAMPLE_TEXT = (
    "---\n"
    "source: Mahabharata\n"
    "section: Adi Parva\n"
    "characters: Karna, Surya, Kunti\n"
    "---\n"
    "Karna was the son of Kunti and the sun god Surya. He was raised by a "
    "charioteer named Adhiratha after Kunti set him afloat on a river.\n"
)


def test_ingest_then_retrieve_finds_the_right_chunk(tmp_path, monkeypatch):
    data_dir = tmp_path / "data" / "mahabharata"
    data_dir.mkdir(parents=True)
    (data_dir / "karna.txt").write_text(SAMPLE_TEXT, encoding="utf-8")

    # Point the vectorstore at a throwaway collection so this test never
    # touches the developer's real chroma_db/ directory.
    monkeypatch.setattr(config, "CHROMA_PATH", str(tmp_path / "chroma_db"))
    monkeypatch.setattr(config, "COLLECTION_NAME", "test_collection")
    monkeypatch.setattr(vectorstore_module, "_vectorstore", None)

    documents = load_documents(data_dir=str(tmp_path / "data"))
    chunks = split_documents(documents)
    store = vectorstore_module.get_vectorstore()
    store.add_documents(chunks, ids=[f"chunk-{i}" for i in range(len(chunks))])

    results = retrieve("Who was Karna's father?", top_k=3)

    assert len(results) > 0
    assert results[0]["similarity"] >= config.RELEVANCE_THRESHOLD
    assert "Surya" in results[0]["text"]
    assert results[0]["metadata"]["source"] == "Mahabharata"

from langchain_core.documents import Document

from ingestion.splitter import split_documents


def test_split_documents_preserves_metadata_and_adds_chunk_index():
    # Long enough to be split into more than one chunk at the default
    # chunk_size (see config.CHUNK_SIZE).
    paragraph = "Karna was a great warrior. " * 60
    doc = Document(page_content=paragraph, metadata={"source": "Mahabharata", "section": "Adi Parva"})

    chunks = split_documents([doc])

    assert len(chunks) > 1
    for i, chunk in enumerate(chunks):
        assert chunk.metadata["source"] == "Mahabharata"
        assert chunk.metadata["section"] == "Adi Parva"
        assert chunk.metadata["chunk_index"] == i


def test_split_documents_keeps_short_text_as_one_chunk():
    doc = Document(page_content="A short sentence.", metadata={"source": "General"})
    chunks = split_documents([doc])
    assert len(chunks) == 1
    assert chunks[0].page_content == "A short sentence."

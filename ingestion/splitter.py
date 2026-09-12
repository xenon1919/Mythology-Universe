"""
Splits loaded documents into chunks small enough to embed well, but large
enough to keep a scene or explanation in one piece.

RecursiveCharacterTextSplitter tries paragraph breaks first, then sentence
breaks, then words - only falling back to a hard character cut if it has to.
That's what "avoid breaking important paragraphs unnecessarily" means here.
Overlap repeats a little text between consecutive chunks so a sentence that
falls right on a chunk boundary still has surrounding context in at least
one of the chunks.
"""
from langchain_text_splitters import RecursiveCharacterTextSplitter

import config


def split_documents(documents):
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=config.CHUNK_SIZE,
        chunk_overlap=config.CHUNK_OVERLAP,
        separators=["\n\n", "\n", ". ", " ", ""],
    )
    chunks = splitter.split_documents(documents)

    for i, chunk in enumerate(chunks):
        chunk.metadata["chunk_index"] = i

    return chunks

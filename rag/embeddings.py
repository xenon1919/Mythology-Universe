"""
Wraps the embedding model used to turn text into vectors.

We use a small local Hugging Face sentence-transformer model. It runs on the
CPU, needs no API key, and is downloaded once then cached by Hugging Face -
this is what "local embeddings" means in the project requirements, as opposed
to calling a paid embedding API.
"""
from langchain_huggingface import HuggingFaceEmbeddings

import config

_embeddings = None


def get_embedding_model():
    """Return a shared, lazily-created embedding model instance.

    Both ingestion (writing vectors) and the Flask app (reading vectors) call
    this, so they must use the exact same model - otherwise similarity search
    would compare vectors from two different embedding spaces.
    """
    global _embeddings
    if _embeddings is None:
        _embeddings = HuggingFaceEmbeddings(model_name=config.EMBEDDING_MODEL)
    return _embeddings

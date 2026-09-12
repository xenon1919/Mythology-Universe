"""
Semantic search over the ChromaDB collection.

Every function here returns plain dicts (not LangChain Document objects) so
the rest of the app doesn't need to know anything about LangChain's types.
"""
import config
from rag.vectorstore import get_vectorstore


def retrieve(query, source=None, top_k=None):
    """Return the top_k most similar chunks to `query`.

    Each result is {"text", "metadata", "similarity"}, where similarity is a
    0-1 cosine similarity score (higher = more relevant). If `source` is
    given (e.g. "Mahabharata"), only chunks from that source are searched -
    this is the metadata filtering the project spec asks for, used when a
    question names a specific text.
    """
    top_k = top_k or config.TOP_K
    vectorstore = get_vectorstore()
    where = {"source": source} if source else None

    docs_with_scores = vectorstore.similarity_search_with_score(query, k=top_k, filter=where)

    results = []
    for doc, distance in docs_with_scores:
        similarity = 1 - distance
        results.append({
            "text": doc.page_content,
            "metadata": doc.metadata,
            "similarity": round(similarity, 4),
        })
    return results


def retrieve_for_character(name, top_k=None):
    """Search focused on a single character.

    We cast a wider semantic net, then move chunks whose "characters"
    metadata explicitly names them to the front. This favours chunks that
    are actually about the character over ones that merely resemble the
    question, without needing a brittle exact-match database filter.
    """
    top_k = top_k or config.TOP_K
    query = f"Who is {name}? Their origin, family, allies, enemies, teachers and major events."
    candidates = retrieve(query, top_k=top_k * 3)

    def mentions_name(result):
        characters = result["metadata"].get("characters", "")
        return name.lower() in characters.lower()

    exact = [r for r in candidates if mentions_name(r)]
    other = [r for r in candidates if not mentions_name(r)]
    return (exact + other)[:top_k]


def related_characters(results, exclude):
    """Characters that co-occur with `exclude` in the retrieved chunks,
    ranked by how often they appear together. This is the only source of
    "relationship" data we show - it comes from real document metadata, not
    from asking the LLM to guess a family tree.
    """
    counts = {}
    for result in results:
        names = [n.strip() for n in result["metadata"].get("characters", "").split(",")]
        for name in names:
            if name and name.lower() != exclude.lower():
                counts[name] = counts.get(name, 0) + 1
    return sorted(counts, key=counts.get, reverse=True)

"""
Read-only summaries of what's actually sitting in ChromaDB right now.

These power the Characters, Stories, and Sources pages. Everything here is
derived by scanning the real metadata of indexed chunks - nothing is
hardcoded, so these pages can never show a character or source that isn't
actually in the knowledge base.
"""
import content
from rag.vectorstore import get_vectorstore


def _all_metadata():
    store = get_vectorstore()
    data = store.get(include=["metadatas"])
    return data["metadatas"] or []


def total_chunks():
    return len(_all_metadata())


def list_characters():
    names = set()
    for meta in _all_metadata():
        for name in meta.get("characters", "").split(","):
            name = name.strip()
            if name:
                names.add(name)
    return sorted(names)


def source_stats():
    """Per-source counts of chunks, plus the distinct sections, characters,
    and topics found in that source's chunks."""
    stats = {}
    for meta in _all_metadata():
        source = meta.get("source", "Unknown")
        entry = stats.setdefault(source, {"chunks": 0, "sections": set(), "characters": set(), "topics": set()})
        entry["chunks"] += 1
        if meta.get("section"):
            entry["sections"].add(meta["section"])
        if meta.get("topic"):
            entry["topics"].add(meta["topic"])
        for name in meta.get("characters", "").split(","):
            name = name.strip()
            if name:
                entry["characters"].add(name)

    return {
        source: {
            "chunks": v["chunks"],
            "sections": sorted(v["sections"]),
            "characters": sorted(v["characters"]),
            "topics": sorted(v["topics"]),
        }
        for source, v in stats.items()
    }


def story_overview():
    """Combine the hand-written blurbs in content.py with real indexed stats,
    so each story card shows both a short description and what's actually
    searchable about it."""
    stats = source_stats()
    overview = []
    for source, description in content.STORY_INFO.items():
        stat = stats.get(source, {"chunks": 0, "sections": [], "characters": [], "topics": []})
        overview.append({
            "source": source,
            "description": description,
            "chunks_indexed": stat["chunks"],
            "sections": stat["sections"],
            "characters": stat["characters"],
            "topics": stat["topics"],
        })
    return overview

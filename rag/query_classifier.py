"""
Lightweight, keyword-based query understanding.

This deliberately does NOT call the LLM - classification is just used to
label the query type for the UI and to spot when a user names a specific
source (e.g. "Mahabharata") so retrieval can filter to it. A regex/keyword
check is fast, free, and predictable, and the spec explicitly asks to keep
this step simple rather than building a second AI agent for it.
"""
_SOURCE_KEYWORDS = {
    "Ramayana": ["ramayana"],
    "Mahabharata": ["mahabharata", "mahabharat"],
    "Bhagavad Gita": ["bhagavad gita", "bhagwad gita", "geeta", "gita"],
    "Puranas": ["purana", "puranas"],
}

_TYPE_KEYWORDS = [
    ("relationship", ["related to", "relation", "connected", "married", "father of",
                       "mother of", "son of", "daughter of", "wife of", "husband of",
                       "brother", "sister", "parents of"]),
    ("timeline", ["when did", "what order", "sequence of", "timeline", "before or after"]),
    ("event", ["what happened", "why did", "battle of", "war", "abduct"]),
    ("source_specific", ["according to", "in the ramayana", "in the mahabharata",
                          "in the gita", "in the puranas"]),
    ("story", ["story of", "tale of", "narrate", "tell me about the story"]),
    ("character", ["who was", "who is", "who were"]),
]


def detect_source_filter(text):
    """Return a canonical source name if the question clearly names one of
    the known texts (e.g. "According to the Mahabharata, ..."), else None."""
    lowered = text.lower()
    for source, keywords in _SOURCE_KEYWORDS.items():
        if any(keyword in lowered for keyword in keywords):
            return source
    return None


def classify_query(text):
    """Return a short label describing the kind of question asked."""
    lowered = text.lower()
    for label, keywords in _TYPE_KEYWORDS:
        if any(keyword in lowered for keyword in keywords):
            return label
    return "general"

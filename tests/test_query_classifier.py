from rag.query_classifier import classify_query, detect_source_filter


def test_detect_source_filter_finds_named_source():
    assert detect_source_filter("According to the Mahabharata, who was Karna's father?") == "Mahabharata"
    assert detect_source_filter("What happens in the Ramayana?") == "Ramayana"
    assert detect_source_filter("What does the Gita say about duty?") == "Bhagavad Gita"


def test_detect_source_filter_returns_none_when_no_source_named():
    assert detect_source_filter("Who was Karna?") is None


def test_classify_query_labels_relationship_questions():
    assert classify_query("How is Karna related to Arjuna?") == "relationship"


def test_classify_query_labels_character_questions():
    assert classify_query("Who was Karna?") == "character"


def test_classify_query_falls_back_to_general():
    assert classify_query("Tell me something interesting.") == "general"

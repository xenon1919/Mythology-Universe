from ingestion.loader import clean_text, load_documents, parse_frontmatter


def test_parse_frontmatter_extracts_metadata_and_body():
    raw = (
        "---\n"
        "source: Mahabharata\n"
        "characters: Karna, Kunti\n"
        "---\n"
        "Karna was born to Kunti.\n"
    )
    metadata, body = parse_frontmatter(raw)
    assert metadata == {"source": "Mahabharata", "characters": "Karna, Kunti"}
    assert body.strip() == "Karna was born to Kunti."


def test_parse_frontmatter_handles_missing_header():
    raw = "Just plain text, no header.\n"
    metadata, body = parse_frontmatter(raw)
    assert metadata == {}
    assert body == raw


def test_clean_text_collapses_extra_whitespace():
    messy = "Line one.\n\n\n\nLine two.   With   extra   spaces.\r\n"
    cleaned = clean_text(messy)
    assert "\n\n\n" not in cleaned
    assert "   " not in cleaned


def test_load_documents_reads_files_and_fills_defaults(tmp_path):
    ramayana_dir = tmp_path / "ramayana"
    ramayana_dir.mkdir()
    (ramayana_dir / "sample.txt").write_text(
        "---\nsection: Bala Kanda\ncharacters: Rama\n---\nRama was born in Ayodhya.\n",
        encoding="utf-8",
    )

    docs = load_documents(data_dir=str(tmp_path))

    assert len(docs) == 1
    doc = docs[0]
    assert doc.page_content == "Rama was born in Ayodhya."
    # source isn't in the frontmatter, so it should default to the folder name
    assert doc.metadata["source"] == "Ramayana"
    assert doc.metadata["section"] == "Bala Kanda"
    assert doc.metadata["file"] == "sample.txt"


def test_load_documents_skips_unsupported_files(tmp_path):
    general_dir = tmp_path / "general"
    general_dir.mkdir()
    (general_dir / "notes.pdf").write_bytes(b"not a real pdf")
    (general_dir / "notes.txt").write_text("Some text.", encoding="utf-8")

    docs = load_documents(data_dir=str(tmp_path))

    assert len(docs) == 1
    assert docs[0].metadata["file"] == "notes.txt"

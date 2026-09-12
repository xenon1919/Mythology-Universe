"""
Loads raw text files from data/ into LangChain Document objects.

Each source file may start with a small "front matter" metadata header,
delimited by --- lines, e.g.:

    ---
    source: Mahabharata
    category: character
    section: Adi Parva
    characters: Karna, Kunti, Surya
    topic: birth
    ---
    Karna was born to Kunti ...

Anything not covered by the header is filled in with sensible defaults (the
source name is guessed from the folder if not given), so plain .txt files
with no header at all still work.
"""
import os
import re

from langchain_core.documents import Document

import config

SUPPORTED_EXTENSIONS = {".txt", ".md"}


def clean_text(text):
    """Normalise line endings and collapse extra whitespace, without
    touching the actual wording of the story."""
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def parse_frontmatter(raw_text):
    """Split a file's optional --- metadata header from its body text.

    Returns (metadata_dict, body_text). If there's no header, metadata is {}
    and body_text is the whole file.
    """
    if not raw_text.startswith("---"):
        return {}, raw_text

    parts = raw_text.split("---", 2)
    if len(parts) < 3:
        return {}, raw_text

    header, body = parts[1], parts[2]
    metadata = {}
    for line in header.strip().splitlines():
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        metadata[key.strip().lower()] = value.strip()
    return metadata, body


def load_documents(data_dir=None):
    """Walk data/<category>/ recursively and return one Document per file."""
    data_dir = data_dir or config.DATA_DIR
    documents = []

    for root, _, files in os.walk(data_dir):
        for filename in sorted(files):
            ext = os.path.splitext(filename)[1].lower()
            if ext not in SUPPORTED_EXTENSIONS:
                continue

            path = os.path.join(root, filename)
            with open(path, "r", encoding="utf-8") as f:
                raw_text = f.read()

            metadata, body = parse_frontmatter(raw_text)
            body = clean_text(body)
            if not body:
                continue

            folder_name = os.path.basename(root)
            metadata.setdefault("source", folder_name.replace("_", " ").title())
            metadata.setdefault("category", "general")
            metadata.setdefault("language", "English")
            metadata["file"] = filename

            documents.append(Document(page_content=body, metadata=metadata))

    return documents

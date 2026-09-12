# Mythology Universe

An AI-powered Indian mythology exploration app built around Retrieval-Augmented
Generation (RAG). Every answer it gives is grounded in a local, private knowledge
base of mythology documents - the LLM is never allowed to answer from its own
training data alone.

## Problem statement

General-purpose LLMs will happily answer mythology questions from memory, but
they also confidently invent relationships, events, and "facts" that don't
exist in any actual text. For a mythology reference tool, that's a serious
problem: a wrong answer that sounds authoritative is worse than no answer.

Mythology Universe solves this by retrieving real passages from an indexed
knowledge base *before* generating an answer, checking that those passages are
actually relevant, and refusing to answer confidently if they aren't - instead
of ever letting the model "wing it."

## Technology stack

| Layer          | Choice                                              |
|----------------|------------------------------------------------------|
| Backend        | Python + Flask                                       |
| Frontend       | Plain HTML, CSS, vanilla JavaScript (no frameworks)   |
| RAG            | LangChain                                             |
| Vector DB      | ChromaDB (persistent, local)                          |
| LLM            | Groq API                                              |
| Embeddings     | Local Hugging Face sentence-transformer model         |
| Env / packages | [uv](https://docs.astral.sh/uv/)                      |

## Architecture

```
                         USER
                          |
                     Flask routes (app.py)
                          |
              -------------------------------
              |                             |
        page routes                    /api/* routes
     (render templates)             (JSON, used by JS)
                                          |
                                   rag/chain.py
                                          |
        classify query + detect source filter (rag/query_classifier.py)
                                          |
             condense follow-up question using chat history (LLM)
                                          |
                    rag/retriever.py  ->  ChromaDB (rag/vectorstore.py)
                                          |
                         similarity scores computed (cosine)
                                          |
                score >= RELEVANCE_THRESHOLD for at least one chunk?
                     |                                   |
                    NO                                  YES
                     |                                   |
        "not enough evidence" reply         build context block (rag/prompts.py)
          (no LLM call at all)                           |
                                              Groq LLM generates answer
                                           + related questions (one call)
                                                          |
                                    answer + sources + related questions
                                                          |
                                                  JSON response
                                                          |
                                        static/js/*.js renders it in the UI
```

This is the "retrieve first, verify, generate second" principle from the
project spec: the LLM is only ever invoked once there is evidence strong
enough to answer from, and the evidence retrieved is exactly what gets shown
back to the user as sources.

## RAG workflow, step by step

1. **Classify the question** (`rag/query_classifier.py`) - a fast, keyword-based
   check (no LLM call) that labels the question (character / relationship /
   event / timeline / general) and detects whether it names a specific text
   (e.g. "According to the Mahabharata...").
2. **Condense follow-up questions** - if there's chat history, a small LLM call
   rewrites something like "what about his mother?" into a standalone question
   ("What about Karna's mother?"), so retrieval can find the right documents.
3. **Retrieve** (`rag/retriever.py`) - semantic search against ChromaDB, filtered
   to a specific source if one was detected in step 1.
4. **Verify** - every retrieved chunk has a similarity score; if the *best*
   chunk still scores below `RELEVANCE_THRESHOLD`, the app returns "I couldn't
   find enough information..." without calling the LLM at all. This is the
   main hallucination-prevention mechanism.
5. **Generate** - the surviving chunks are formatted into a numbered, tagged
   context block and handed to Groq along with a strict system prompt
   (`rag/prompts.py`) that forbids using outside knowledge.
6. **Return** - the answer, deduplicated source metadata, and a few
   LLM-suggested follow-up questions (grounded in the same context) go back to
   the frontend as JSON.

## Prompting strategy

The system prompt (`rag/prompts.py`) is the single place that encodes the
grounding rules:

- Answer only from the CONTEXT given in the message, never from general
  knowledge.
- Never invent characters, relationships, events, or citations.
- Say plainly when the context isn't enough - don't guess.
- Attribute claims to their source ("According to the retrieved Mahabharata
  material...").
- Point out disagreements between sources instead of silently picking one.

## Hallucination prevention

Three independent layers work together:

1. **Retrieval threshold** - weak matches never reach the LLM (see step 4 above).
2. **Prompt constraints** - the LLM is explicitly told not to use outside
   knowledge and to say so when context is thin.
3. **Source transparency** - every answer shows exactly which indexed passages
   it came from, so a claim can always be checked against the original text.

## Project structure

```
mythology-universe/
├── app.py                 Flask routes only - no business logic
├── config.py               All settings, read from .env
├── content.py               Small curated data: story blurbs + timeline order
├── requirements.txt
├── .env.example
│
├── data/                    Source documents (see "Adding your own documents")
│   ├── ramayana/
│   ├── mahabharata/
│   ├── bhagavad_gita/
│   ├── puranas/
│   └── general/
│
├── ingestion/               Run separately from the Flask app
│   ├── loader.py            Reads files, parses metadata, cleans text
│   ├── splitter.py          Chunks documents
│   └── ingest.py            Orchestrates: load -> split -> embed -> store
│
├── rag/
│   ├── embeddings.py        The local HF embedding model
│   ├── vectorstore.py       The one shared ChromaDB collection
│   ├── retriever.py         Semantic search + character/related-character logic
│   ├── prompts.py           System prompt + prompt builders
│   ├── chain.py             Orchestrates retrieve -> verify -> generate
│   ├── memory.py            Session-based conversation history
│   ├── query_classifier.py  Lightweight keyword-based query typing
│   └── catalog.py           Aggregates real indexed metadata for the UI
│
├── templates/               Jinja2 page shells (data is fetched client-side)
└── static/
    ├── css/style.css
    └── js/{app,chat,explorer}.js
```

## Installation (using uv)

```bash
# 1. Create the virtual environment
uv venv

# 2. Install dependencies into it
uv pip install -r requirements.txt

# 3. Copy the env template and add your Groq API key
cp .env.example .env
# then edit .env and set GROQ_API_KEY=...
```

Get a free Groq API key at https://console.groq.com/keys.

## Environment variables

See `.env.example` for the full list with defaults. The important ones:

| Variable              | Purpose                                            |
|-----------------------|-----------------------------------------------------|
| `GROQ_API_KEY`         | Required. The app returns a clear error without it. |
| `GROQ_MODEL`           | Which Groq-hosted model to use.                      |
| `EMBEDDING_MODEL`      | Local Hugging Face embedding model name.             |
| `CHROMA_PATH`          | Where ChromaDB stores its data on disk.              |
| `CHUNK_SIZE` / `CHUNK_OVERLAP` | Ingestion chunking behaviour.                |
| `TOP_K`                | How many chunks to retrieve per question.            |
| `RELEVANCE_THRESHOLD`  | Minimum cosine similarity to trust a chunk.          |
| `MAX_HISTORY_TURNS`    | How many past Q&A turns to keep in memory.           |

## How to ingest documents

The Flask app never writes to ChromaDB - ingestion is a separate, explicit step:

```bash
uv run python -m ingestion.ingest
```

Run this once, and again any time you add or edit files under `data/`. It
clears the existing collection and rebuilds it from whatever is currently in
`data/`.

### Adding your own documents

Place `.txt` (or `.md`) files under the matching folder in `data/`. Optionally
start a file with a `---`-delimited metadata header:

```
---
source: Mahabharata
category: character
section: Adi Parva
characters: Karna, Kunti, Surya
topic: birth
---
Karna was born to Kunti ...
```

If you skip the header, the app still works - `source` defaults to the folder
name and everything else is left blank. The sample files shipped in `data/`
are short, original-wording summaries of widely known public-domain stories
(not excerpts from any copyrighted translation) - replace or add to them with
your own legally obtained material as needed.

## How to run Flask

```bash
uv run python app.py
```

Then open http://127.0.0.1:5000. If the knowledge base is empty or the Groq
key is missing, the console prints a warning and the UI shows a friendly error
instead of failing silently.

## Example questions

- Who was Karna?
- How were Krishna and Arjuna connected?
- Why did Ravana abduct Sita?
- Who were the parents of Ganesha?
- Why did the Kurukshetra war happen?
- What happened to Abhimanyu?
- How was Hanuman connected to Rama?

## API endpoints

| Method | Path                     | Purpose                                    |
|--------|--------------------------|---------------------------------------------|
| GET    | `/`                      | Homepage                                     |
| GET    | `/chat`                  | Chat UI                                      |
| GET    | `/characters`            | Character explorer                           |
| GET    | `/characters/<name>`     | Character detail page                        |
| GET    | `/stories`               | Story explorer                               |
| GET    | `/timeline`              | Timeline view                                |
| GET    | `/sources`               | Knowledge base transparency view             |
| POST   | `/api/ask`               | `{question}` -> `{answer, sources, related_questions, query_type}` |
| POST   | `/api/reset`             | Clears conversation memory for the session   |
| GET    | `/api/character/<name>`  | Grounded profile + related characters        |
| GET    | `/api/characters`        | All character names found in the metadata    |
| GET    | `/api/stories`           | Story blurbs + real indexed stats            |
| GET    | `/api/timeline`          | Curated event sequences                      |
| GET    | `/api/sources`           | Per-source chunk/section/character counts    |
| GET    | `/api/search?q=...`      | Raw retrieval results (debugging/transparency) |

## Design notes worth knowing about

- **Conversation memory** lives in the signed Flask session cookie, not a
  database - it's per-browser-session and disappears when the session ends.
- **Character relationships** are never invented by the LLM. `/api/character/<name>`
  shows "related characters" derived purely from which names co-occur in the
  same indexed chunks (`rag/retriever.py::related_characters`).
- **The Stories and Timeline pages** mix two kinds of data on purpose: short
  hand-written blurbs/orderings (`content.py`, so those pages render instantly
  and never invent a sequence of events) combined with real counts of what's
  actually indexed (`rag/catalog.py`).
- **Cosine similarity math**: the ChromaDB collection is created with
  `hnsw:space: cosine`, so `similarity = 1 - distance` directly - no dependency
  on LangChain's internal relevance-score normalization.

## Future improvements

- Re-rank retrieved chunks with a cross-encoder before generation.
- Support PDF/DOCX ingestion in addition to plain text/Markdown.
- Persist conversation memory per logged-in user instead of per-session.
- Add an admin view to re-run ingestion from the browser instead of the CLI.

"""
Central configuration for Mythology Universe.

Every tunable value in the app (chunk size, top-k, thresholds, model names, paths)
lives here and is read from environment variables (see .env.example). No other
module should read os.environ directly - this keeps every setting in one place.
"""
import os
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")

# --- Groq LLM -----------------------------------------------------------
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
# Check https://console.groq.com/docs/models (or GET /openai/v1/models with
# your key) for currently supported model names - Groq retires/renames models
# fairly often, so this is deliberately overridable via .env.
GROQ_MODEL = os.getenv("GROQ_MODEL", "openai/gpt-oss-20b")

# --- Embeddings (local Hugging Face model, no external API calls) -------
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")

# --- ChromaDB -------------------------------------------------------------
CHROMA_PATH = os.getenv("CHROMA_PATH", os.path.join(BASE_DIR, "chroma_db"))
COLLECTION_NAME = os.getenv("COLLECTION_NAME", "mythology_universe")

# --- Chunking (used only by the ingestion pipeline) ----------------------
CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", 800))
CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", 150))

# --- Retrieval -------------------------------------------------------------
TOP_K = int(os.getenv("TOP_K", 5))
# Cosine similarity (0-1, higher = more relevant) a retrieved chunk must reach
# before it's allowed to be used as evidence. Below this, we refuse to answer
# rather than let the LLM guess. Tune this if answers feel too strict/loose.
RELEVANCE_THRESHOLD = float(os.getenv("RELEVANCE_THRESHOLD", 0.25))

# --- Conversation memory ---------------------------------------------------
MAX_HISTORY_TURNS = int(os.getenv("MAX_HISTORY_TURNS", 4))

# --- Flask -------------------------------------------------------------
FLASK_SECRET_KEY = os.getenv("FLASK_SECRET_KEY", "dev-secret-change-me")

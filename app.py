"""
Flask entry point for Mythology Universe.

This file only wires together routes. The actual RAG logic lives in rag/,
and document ingestion (which must be run separately, see ingestion/ingest.py)
lives in ingestion/.
"""
from flask import Flask, jsonify, render_template, request, session

import config
import content
from rag import catalog, chain
from rag.memory import add_turn, clear_history, get_history
from rag.retriever import related_characters, retrieve, retrieve_for_character

app = Flask(__name__)
app.secret_key = config.FLASK_SECRET_KEY


# ---------------------------------------------------------------------------
# Pages - each template fetches its own data client-side from the JSON API
# below, keeping the server side simple.
# ---------------------------------------------------------------------------

@app.get("/")
def home():
    return render_template("index.html")


@app.get("/chat")
def chat_page():
    return render_template("chat.html")


@app.get("/characters")
def characters_page():
    return render_template("characters.html")


@app.get("/characters/<name>")
def character_detail_page(name):
    return render_template("character.html", name=name)


@app.get("/stories")
def stories_page():
    return render_template("stories.html")


@app.get("/timeline")
def timeline_page():
    return render_template("timeline.html")


@app.get("/sources")
def sources_page():
    return render_template("sources.html")


# ---------------------------------------------------------------------------
# JSON API
# ---------------------------------------------------------------------------

@app.post("/api/ask")
def api_ask():
    data = request.get_json(silent=True) or {}
    question = (data.get("question") or "").strip()

    if not question:
        return jsonify({"error": "Please enter a question."}), 400

    if catalog.total_chunks() == 0:
        return jsonify({
            "error": "The knowledge base is empty. Run 'uv run python -m ingestion.ingest' "
                     "before asking questions."
        }), 503

    try:
        history = get_history(session)
        result = chain.answer_question(question, history)
        add_turn(session, question, result["answer"])
        return jsonify(result)
    except RuntimeError as exc:
        return jsonify({"error": str(exc)}), 503
    except Exception:
        app.logger.exception("Unexpected error while answering a question")
        return jsonify({"error": "Something went wrong while generating the answer."}), 500


@app.post("/api/reset")
def api_reset():
    clear_history(session)
    return jsonify({"status": "ok"})


@app.get("/api/character/<name>")
def api_character(name):
    if catalog.total_chunks() == 0:
        return jsonify({"error": "The knowledge base is empty. Run the ingestion script first."}), 503

    try:
        results = retrieve_for_character(name)
        best_score = max((r["similarity"] for r in results), default=0)
        if best_score < config.RELEVANCE_THRESHOLD:
            return jsonify({"error": f"No indexed information found for '{name}'."}), 404

        profile = chain.answer_character(name, results)
        profile["related_characters"] = related_characters(results, exclude=name)
        return jsonify(profile)
    except RuntimeError as exc:
        return jsonify({"error": str(exc)}), 503
    except Exception:
        app.logger.exception("Unexpected error while building a character profile")
        return jsonify({"error": "Something went wrong while looking up this character."}), 500


@app.get("/api/characters")
def api_characters():
    return jsonify({"characters": catalog.list_characters()})


@app.get("/api/stories")
def api_stories():
    return jsonify({"stories": catalog.story_overview()})


@app.get("/api/timeline")
def api_timeline():
    return jsonify(content.TIMELINE)


@app.get("/api/sources")
def api_sources():
    return jsonify({"sources": catalog.source_stats()})


@app.get("/api/search")
def api_search():
    query = (request.args.get("q") or "").strip()
    source = request.args.get("source") or None

    if not query:
        return jsonify({"error": "Please provide a 'q' query parameter."}), 400

    try:
        results = retrieve(query, source=source)
        return jsonify({"results": results})
    except Exception:
        app.logger.exception("Search failed")
        return jsonify({"error": "Search failed. Has the knowledge base been built?"}), 500


# ---------------------------------------------------------------------------
# Error handlers - keep stack traces out of user-facing responses.
# ---------------------------------------------------------------------------

@app.errorhandler(404)
def not_found(_):
    return jsonify({"error": "Not found."}), 404


@app.errorhandler(500)
def server_error(_):
    return jsonify({"error": "Internal server error."}), 500


if __name__ == "__main__":
    if not config.GROQ_API_KEY:
        print("WARNING: GROQ_API_KEY is not set. Copy .env.example to .env and add your key.")
    if catalog.total_chunks() == 0:
        print("WARNING: ChromaDB has no indexed chunks yet. Run: uv run python -m ingestion.ingest")

    # use_reloader=False: the auto-reloader restarts the whole process (including
    # a several-second embedding-model reload) on every file change, and on some
    # Windows setups it can misfire into a restart loop that makes the server
    # briefly unreachable. Restart manually after changing code instead.
    app.run(debug=True, use_reloader=False)

"""
Conversation memory, kept per-browser-session using Flask's signed session
cookie. Nothing is written to a database - history disappears when the
session ends, and is never shared between users. Each entry is just the
question text and the final answer text, nothing more sensitive.
"""
import config


def get_history(session):
    return session.get("history", [])


def add_turn(session, question, answer):
    history = session.get("history", [])
    history.append({"question": question, "answer": answer})
    session["history"] = history[-config.MAX_HISTORY_TURNS:]
    session.modified = True


def clear_history(session):
    session.pop("history", None)

"""
The RAG pipeline itself: retrieve first, verify the evidence is strong
enough, only then ask the LLM to write an answer from it.

    question -> classify + detect source -> retrieve -> threshold check
        -> (LLM: standalone-question rewrite, if there's history)
        -> (LLM: generate answer + related questions from retrieved context)
"""
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_groq import ChatGroq

import config
from rag.prompts import (
    RELATED_DELIM,
    SYSTEM_PROMPT,
    build_character_prompt,
    build_context_block,
    build_user_prompt,
)
from rag.query_classifier import classify_query, detect_source_filter
from rag.retriever import retrieve

NO_EVIDENCE_MESSAGE = (
    "I couldn't find enough information in the available mythology sources to answer "
    "this reliably. Try rephrasing your question, or check the Sources page to see what "
    "is currently indexed."
)

_llm = None


def get_llm():
    """Create the Groq chat model on first use. Raising early with a clear
    message here is what turns a missing API key into a friendly error
    instead of a stack trace reaching the user."""
    global _llm
    if _llm is None:
        if not config.GROQ_API_KEY:
            raise RuntimeError(
                "GROQ_API_KEY is not set. Copy .env.example to .env and add your key."
            )
        _llm = ChatGroq(model=config.GROQ_MODEL, temperature=0.2)
    return _llm


def answer_question(question, history):
    """Answer one question, given prior turns as [{"question", "answer"}, ...].

    Returns {"answer", "sources", "related_questions", "query_type"}.
    """
    question = question.strip()
    if not question:
        raise ValueError("Question cannot be empty.")

    query_type = classify_query(question)
    source_filter = detect_source_filter(question)
    search_query = _condense_question(question, history) if history else question

    results = retrieve(search_query, source=source_filter)
    strong_results = [r for r in results if r["similarity"] >= config.RELEVANCE_THRESHOLD]

    if not strong_results:
        return {
            "answer": NO_EVIDENCE_MESSAGE,
            "sources": [],
            "related_questions": [],
            "query_type": query_type,
        }

    context_block = build_context_block(strong_results)
    messages = [SystemMessage(content=SYSTEM_PROMPT)]
    for turn in history:
        messages.append(HumanMessage(content=turn["question"]))
        messages.append(AIMessage(content=turn["answer"]))
    messages.append(HumanMessage(content=build_user_prompt(context_block, question)))

    llm = get_llm()  # raises RuntimeError with a clear message if the API key is missing
    try:
        response = llm.invoke(messages)
    except Exception as exc:
        raise RuntimeError("The Groq API request failed. Please try again shortly.") from exc

    answer_text, related_questions = _split_related_questions(response.content)

    return {
        "answer": answer_text,
        "sources": _dedupe_sources(strong_results),
        "related_questions": related_questions,
        "query_type": query_type,
    }


def answer_character(name, results):
    """Build a structured Origin/Family/Allies/... profile for one character
    from already-retrieved chunks. Used by the character explorer."""
    context_block = build_context_block(results)
    messages = [
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(content=build_character_prompt(context_block, name)),
    ]

    llm = get_llm()  # raises RuntimeError with a clear message if the API key is missing
    try:
        response = llm.invoke(messages)
    except Exception as exc:
        raise RuntimeError("The Groq API request failed. Please try again shortly.") from exc

    return {
        "name": name,
        "profile": response.content.strip(),
        "sources": _dedupe_sources(results),
    }


def _condense_question(question, history):
    """Rewrite a follow-up question ("what about his mother?") into a
    standalone one, using only the last couple of turns, so retrieval can
    resolve pronouns before searching. Falls back to the original question
    on any failure (e.g. missing API key) rather than blocking the request.
    """
    recent = history[-2:]
    history_text = "\n".join(f"Q: {t['question']}\nA: {t['answer']}" for t in recent)
    prompt = (
        "Rewrite the follow-up question so it can be understood on its own, without "
        "changing its meaning. Use the conversation only to resolve pronouns or implicit "
        "references. Reply with just the rewritten question, nothing else.\n\n"
        f"Conversation so far:\n{history_text}\n\nFollow-up question: {question}\n"
        "Standalone question:"
    )
    try:
        response = get_llm().invoke([HumanMessage(content=prompt)])
        rewritten = response.content.strip().strip('"')
        return rewritten or question
    except Exception:
        return question


def _split_related_questions(raw_text):
    if RELATED_DELIM in raw_text:
        answer_text, related_block = raw_text.split(RELATED_DELIM, 1)
    else:
        answer_text, related_block = raw_text, ""

    related_questions = [
        line.strip("-* \t")
        for line in related_block.strip().splitlines()
        if line.strip() and line.strip().lower() != "none"
    ]
    return answer_text.strip(), related_questions[:3]


def _dedupe_sources(results):
    seen = set()
    sources = []
    for result in results:
        meta = result["metadata"]
        key = (meta.get("source"), meta.get("section"), meta.get("file"))
        if key in seen:
            continue
        seen.add(key)
        sources.append({
            "source": meta.get("source", "Unknown"),
            "section": meta.get("section", ""),
            "metadata": meta,
        })
    return sources

"""
All prompt text lives here so the "rules of the game" for the LLM are in one
place, separate from the plumbing code in chain.py.
"""

# Marks the boundary between the main answer and the follow-up questions in
# the LLM's raw response, so chain.py can split the two apart reliably.
RELATED_DELIM = "###RELATED_QUESTIONS###"

SYSTEM_PROMPT = """You are the assistant for "Mythology Universe", a research tool for exploring \
Indian mythology (the Ramayana, the Mahabharata, the Bhagavad Gita, and the Puranas).

Follow these rules strictly:
1. Answer ONLY using the information given to you in the CONTEXT section of the user's message. \
Do not use any other knowledge of mythology you may already have, even if you believe it is correct.
2. Never invent characters, relationships, events, chapter names, or citations that are not present \
in the CONTEXT.
3. If the CONTEXT does not contain enough information to answer, say so plainly instead of guessing.
4. When you do answer, mention which source it came from, e.g. "According to the retrieved \
Mahabharata material, ...".
5. If different passages in the CONTEXT disagree with each other, point out the disagreement \
instead of silently picking one.
6. Keep your answer well organised: short paragraphs, and "-" bullet points for lists such as \
parents, allies, or events.
7. Never present an assumption or inference as a confirmed fact - say when you are inferring.
"""


def build_context_block(results):
    """Turn retrieved chunks into a numbered, source-tagged block of text
    that gets pasted into the prompt as CONTEXT."""
    blocks = []
    for i, result in enumerate(results, start=1):
        meta = result["metadata"]
        tag = meta.get("source", "Unknown source")
        if meta.get("section"):
            tag += f" - {meta['section']}"
        blocks.append(f"[{i}] ({tag})\n{result['text']}")
    return "\n\n".join(blocks)


def build_user_prompt(context_block, question):
    return f"""CONTEXT:
{context_block}

QUESTION:
{question}

Answer the question using only the CONTEXT above, following the rules you were given.
After your answer, add a line with exactly:
{RELATED_DELIM}
then up to 3 short follow-up questions (no numbering, one per line) that a curious reader \
could ask next, grounded only in the CONTEXT above. Write "None" if you cannot think of any.
"""


def build_character_prompt(context_block, name):
    return f"""CONTEXT:
{context_block}

Using ONLY the CONTEXT above, describe the mythological character "{name}" under these \
headings, each written as a markdown heading on its own line like "### Origin" (omit a \
heading entirely if the CONTEXT has nothing for it):

### Origin
### Family
### Allies
### Enemies
### Teachers
### Major Events

Use short "-" bullet points under each heading. Do not invent any detail that is not in the \
CONTEXT. If the CONTEXT does not actually mention {name}, say clearly that there is not enough \
indexed information about them instead of guessing.
"""

from rag.prompts import RELATED_DELIM, build_character_prompt, build_context_block, build_user_prompt


def _sample_results():
    return [
        {
            "text": "Karna was born to Kunti and the sun god Surya.",
            "metadata": {"source": "Mahabharata", "section": "Adi Parva"},
        },
        {
            "text": "Karna was raised by the charioteer Adhiratha.",
            "metadata": {"source": "Mahabharata", "section": "Adi Parva"},
        },
    ]


def test_build_context_block_tags_each_chunk_with_its_source():
    block = build_context_block(_sample_results())
    assert "Mahabharata - Adi Parva" in block
    assert "Karna was born to Kunti" in block
    assert "[1]" in block and "[2]" in block


def test_build_user_prompt_includes_question_context_and_delimiter():
    block = build_context_block(_sample_results())
    prompt = build_user_prompt(block, "Who was Karna's father?")
    assert "Who was Karna's father?" in prompt
    assert RELATED_DELIM in prompt
    assert block in prompt


def test_build_character_prompt_includes_name_and_headings():
    block = build_context_block(_sample_results())
    prompt = build_character_prompt(block, "Karna")
    assert "Karna" in prompt
    assert "### Origin" in prompt
    assert "### Family" in prompt

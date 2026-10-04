"""Sentence segmentation of streamed LLM text."""

from app.llm.sentence_chunker import SentenceChunker


def feed_all(chunker: SentenceChunker, tokens: list[str]) -> list[str]:
    out: list[str] = []
    for t in tokens:
        out.extend(chunker.feed(t))
    return out


def test_emits_first_sentence_before_stream_ends() -> None:
    c = SentenceChunker()
    out = feed_all(c, ["Sure, ", "I ", "can ", "help ", "with ", "that. ", "Your ", "order"])
    assert out == ["Sure, I can help with that."]
    assert c.flush() == "Your order"


def test_does_not_split_decimal_numbers() -> None:
    c = SentenceChunker()
    out = feed_all(c, ["The total is 3", ".", "5 euros today. ", "Thanks"])
    assert out == ["The total is 3.5 euros today."]


def test_does_not_split_after_abbreviation() -> None:
    c = SentenceChunker()
    out = feed_all(c, ["Please ask Dr. ", "Smith about it. ", "Bye"])
    assert out == ["Please ask Dr. Smith about it."]


def test_waits_when_punctuation_is_last_character() -> None:
    c = SentenceChunker()
    assert c.feed("This sentence is finished.") == []  # next token might be "5" or a space
    assert c.feed(" Next") == ["This sentence is finished."]


def test_very_short_sentence_is_joined_to_the_next() -> None:
    c = SentenceChunker(min_chars=12)
    out = feed_all(c, ["Hi. ", "How can I help you today? ", "x"])
    assert out == ["Hi. How can I help you today?"]


def test_long_clause_is_cut_at_a_comma() -> None:
    c = SentenceChunker(soft_limit_chars=40)
    out = feed_all(c, ["First we check the account status, ", "then we look at the latest invoice and so on"])
    assert out and out[0] == "First we check the account status,"


def test_flush_returns_none_when_empty() -> None:
    assert SentenceChunker().flush() is None

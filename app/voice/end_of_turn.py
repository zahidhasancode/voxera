"""Decides whether a finished transcript sounds like the end of the caller's turn.

The recogniser ends a turn after a fixed silence (300 ms with Deepgram). People
pause mid-sentence ("I want to book a table for... um... four people"), and a
fixed silence wait answers them too early. This check reads the words: a
transcript that ends on a joining word, a filler or a trailing comma sounds
unfinished, so the session waits a little longer before replying. A transcript
that sounds complete is answered at once, so normal turns get no slower.

It is a text rule, not a model: it knows English only and cannot hear intonation.
"""

from __future__ import annotations

import re

# Words an English sentence almost never ends on: conjunctions, articles,
# possessives and prepositions that need an object. Words that often do end a
# sentence ("so", "then", "it", "you", "do", "in", "on", "that") are left out on
# purpose: holding a finished turn costs the caller time on every such reply.
CONTINUATION_WORDS = frozenset(
    """
    and but or because although unless whereas if than
    which whose
    the a an my your our their every
    to of for with from into onto between without
    """.split()
)
FILLERS = frozenset({"um", "uh", "erm", "er", "hmm", "mm"})

_LAST_WORD = re.compile(r"([a-z']+)\W*$")


def sounds_unfinished(text: str) -> bool:
    """True when `text` probably stops in the middle of a sentence."""
    stripped = text.strip().lower()
    if not stripped:
        return False
    if stripped.endswith((",", "...", "…", "-", "—", ":")):
        return True
    if stripped.endswith(("?", "!")):
        return False  # a question or exclamation is a complete turn
    match = _LAST_WORD.search(stripped)
    if match is None:
        return False
    word = match.group(1)
    if word in FILLERS:
        return True  # "um." is unfinished even with a full stop after it
    return word in CONTINUATION_WORDS

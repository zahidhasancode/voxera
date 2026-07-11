"""Prompt injection sanitizer."""

import re


class PromptInjectionSanitizer:
    """
    Strips common prompt-injection patterns from knowledge excerpts.

    Defense-in-depth — not a substitute for validation and structured prompts.
    """

    _INJECTION_PATTERNS = [
        re.compile(r"(?i)ignore (all )?(previous|prior|above) instructions"),
        re.compile(r"(?i)you are now (?:a|an) "),
        re.compile(r"(?i)system\s*:\s*"),
        re.compile(r"(?i)\[INST\]|\[/INST\]|<\|im_start\|>|<\|im_end\|>"),
        re.compile(r"(?i)do not follow (?:your|the) (?:rules|guidelines|instructions)"),
    ]

    def sanitize(self, text: str) -> str:
        cleaned = text
        for pattern in self._INJECTION_PATTERNS:
            cleaned = pattern.sub("[filtered]", cleaned)
        return cleaned.strip()

    def contains_injection(self, text: str) -> bool:
        return any(p.search(text) for p in self._INJECTION_PATTERNS)

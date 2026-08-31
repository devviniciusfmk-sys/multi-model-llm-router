"""Heuristic task-tier classification for incoming prompts."""
from __future__ import annotations

import re

CODE_HINTS = re.compile(
    r"\b(function|class|def |import |sql|select |refactor|bug|stack ?trace|"
    r"typescript|python|docker|regex|api endpoint|exception)\b",
    re.IGNORECASE,
)
REASONING_HINTS = re.compile(
    r"\b(why|explain|analyz|analyz|compare|trade-?off|strategy|plan|architect|"
    r"design|root cause|step by step|reason)\b",
    re.IGNORECASE,
)
BULK_HINTS = re.compile(
    r"\b(summariz|translate|classify|label|extract|shorten|list|tag|categor)\w*\b",
    re.IGNORECASE,
)


def classify(prompt: str) -> str:
    """Return one of: reasoning, code, writing, bulk.

    Ordered by specificity: code and bulk signals beat generic reasoning
    words; a prompt that says nothing specific lands on writing.
    """
    if not prompt or not prompt.strip():
        return "writing"
    if CODE_HINTS.search(prompt):
        return "code"
    if BULK_HINTS.search(prompt):
        return "bulk"
    if REASONING_HINTS.search(prompt):
        return "reasoning"
    return "writing"

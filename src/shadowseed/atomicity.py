"""Admit possible inquiry without claiming content quality or authority.

Question admission is deliberately permissive. A seed is born at weight zero
and without evidence. The intake is not a grammatical parser, fact checker,
source verifier, or relevance judge. Overly clever comma, item-count, length,
and verb heuristics silently discard valid investigation paths.

Only visibly separate questions and sentences are blocked structurally.
A composite or semantically broad single question is stored as a weightless
possibility; later recurrence, expiry, evidence and the Gate remain separate.
"""

from __future__ import annotations

import re

_SEPARATE_SENTENCE = re.compile(r"[.!?]\s+[A-ZÀ-Ý]")


def is_single_question(text: str) -> bool | None:
    """Check structural question shape, not semantic atomicity or usefulness.

    None delegates nonquestion fragments to the legacy declarative intake.
    A valid shape does not authorize its contents to influence the host model,
    nor does it upgrade a hypothesis into external evidence.
    """
    stripped = text.strip()
    if not stripped.endswith("?"):
        return None
    if stripped.count("?") != 1:
        return False
    return not bool(_SEPARATE_SENTENCE.search(stripped))

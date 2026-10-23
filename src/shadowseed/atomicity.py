"""Structural check for one investigable question, not a quality verdict.

This intentionally does not classify a question as grounded, new, true or useful.
It avoids treating every comma/conjunction as another question while rejecting
obvious stacked sentences and short category checklists. Borderline cases still
need an independent, blind human review before detector claims can be made.
"""

from __future__ import annotations

import re

_SHORT_ITEM_WORDS = 4

# Leading words that normally make a comma segment a dependent clause, not
# an independently enumerated short category.
_DEPENDENT_LEADS = {
    "met", "van", "bij", "in", "op", "voor", "door", "naar", "uit", "aan",
    "tussen", "onder", "zonder", "waardoor", "waarbij", "wat", "die",
    "dat", "als", "wanneer", "terwijl", "omdat", "zodat", "maar",
    "with", "of", "for", "by", "on", "at", "from", "which", "that",
    "when", "while", "because", "so", "and", "en", "or",
}
_CONJUNCTIONS = {"en", "of", "and", "or"}

# A second request after a conjunction is not a single question.
# Deliberately do not reject "..., wat zou wijzen op ..." or binary
# alternatives of the form "..., of volgt het de thermometer?".
_SECOND_WH_CLAUSE = re.compile(
    r"\b(?:en|and)\s+"
    r"(?:hoe|wat|waarom|welke|welk|wie|wanneer|waardoor|"
    r"how|what|why|which|who|when|where)\b",
    re.IGNORECASE,
)
# After a comma, an inverted auxiliary is strong evidence of another
# question. Without punctuation, restrict rejection to auxiliaries that
# unambiguously begin a separate clause. "and is the same size" may be a
# coordinated predicate of the same subject and must not be rejected.
_YES_NO_PREFIX = (
    r"(?:de|het|een|er|dat|die|dit|deze|the|a|an|this|that|"
    r"it|there|we|ze|zij|they)\b"
)
_SECOND_YES_NO_CLAUSE = re.compile(
    r"[,;]\s*(?:(?:en|and)\s+)?"
    r"(?:is|zijn|kan|kunnen|blijft|blijven|hangt|verandert|verschilt|"
    r"heeft|hebben|geldt|ligt|wordt|werkt|lukt|does|do|did|are|was|were|"
    r"has|have|had|can|could|should|will|would)\s+"
    + _YES_NO_PREFIX,
    re.IGNORECASE,
)
_UNPUNCTUATED_SECOND_YES_NO = re.compile(
    r"\b(?:en|and)\s+"
    r"(?:does|do|did|has|have|had|can|could|should|will|would|"
    r"lukt|werkt|kan|kunnen|heeft|hebben)\s+"
    + _YES_NO_PREFIX,
    re.IGNORECASE,
)
_MULTIPLE_SENTENCES = re.compile(r"[.!?]\s+[A-ZÀ-Ý]")
_WORD = re.compile(r"[\w-]+")
# A list of levels introduced by one preposition is still one possible
# investigation. No word/character cap or allowed-predicate vocabulary is
# needed: the exception applies only to the detected list's own first item.
_MEASUREMENT_LEVELS = re.compile(
    r"\b(?:across|among|at|by|per|under|over|between|"
    r"op|bij|tussen|onder|langs)\s+[^,;?!]+,",
    re.IGNORECASE,
)
# These words begin a new aside about a different checklist; they are not
# values in the measurement enumeration that precedes them.
_LIST_SCOPE_BOUNDARIES = {
    "considering", "including", "regarding", "looking", "taking",
    "discussing", "checking", "exploring", "given", "besides",
    "such", "because", "since", "about", "gezien", "waarbij",
    "bijvoorbeeld", "zoals",
}


def has_multiple_sentences(text: str) -> bool:
    """Detect obvious multiple utterances; abbreviations remain a limitation."""
    return bool(_MULTIPLE_SENTENCES.search(text)) or text.count("?") > 1


def _short_item(tokens: list[str], limit: int = _SHORT_ITEM_WORDS) -> bool:
    return (
        1 <= len(tokens) <= limit
        and tokens[0] not in _DEPENDENT_LEADS
        and not any(token in _CONJUNCTIONS for token in tokens)
    )


def _is_measured_list(text: str, segments: list[str], item_index: int) -> bool:
    """Allow enumerated values only when tied to the list's own measurement.

    A prior phrase such as 'at night,' cannot exempt a later unrelated
    checklist introduced by 'considering security, privacy, and scalability'.
    """
    index = item_index - 1
    while index > 0:
        tokens = _WORD.findall(segments[index].lower())
        if not _short_item(tokens) or _LIST_SCOPE_BOUNDARIES.intersection(tokens):
            break
        index -= 1
    anchor_tokens = _WORD.findall(segments[index].lower())
    if _LIST_SCOPE_BOUNDARIES.intersection(anchor_tokens):
        return False
    return bool(_MEASUREMENT_LEVELS.search(segments[index].strip() + ","))


def looks_like_short_category_list(text: str) -> bool:
    """Reject short category stacks, but admit lists of measured values.

    The exception is tied to the actual list's first comma-separated item,
    not to an unrelated comparative phrase elsewhere in the candidate.
    """
    without_decimal_commas = re.sub(r"(?<=\d),(?=\d)", ".", text)
    segments = without_decimal_commas.split(",")
    chunks = [_WORD.findall(part.lower()) for part in segments]
    if len(chunks) < 2:
        return False

    if len(chunks) >= 3 and _short_item(chunks[-2]):
        last = chunks[-1]
        if _short_item(last) or (
            last[:1] in (["en"], ["and"])
            and _short_item(last[1:])
        ):
            return not _is_measured_list(text, segments, len(chunks) - 2)

    for chunk_index, chunk in enumerate(chunks[1:], start=1):
        for index, token in enumerate(chunk):
            if token in _CONJUNCTIONS and (
                _short_item(chunk[:index], limit=3)
                and _short_item(chunk[index + 1 :], limit=3)
            ):
                return not _is_measured_list(text, segments, chunk_index)

    return False


def is_single_question(text: str) -> bool | None:
    """Return None for nonquestions; otherwise check obvious question structure.

    A positive result means structurally admissible, not that the question
    is scientifically useful, safe to treat as an instruction or distinct
    from existing seeds.
    """
    stripped = text.strip()
    if not stripped.endswith("?"):
        return None
    if ";" in stripped or has_multiple_sentences(stripped):
        return False
    # A short noun-phrase inventory has no single relation to investigate.
    # Example shape: "Which A and B?". Longer relational questions remain free.
    if re.fullmatch(
        r"(?:welke|welk|which|what)\s+[\w-]+(?:\s+[\w-]+){0,2}"
        r"\s+(?:en|of|and|or)\s+[\w-]+\?",
        stripped,
        flags=re.IGNORECASE,
    ):
        return False
    if (
        _SECOND_WH_CLAUSE.search(stripped)
        or _SECOND_YES_NO_CLAUSE.search(stripped)
        or _UNPUNCTUATED_SECOND_YES_NO.search(stripped)
    ):
        return False
    return not looks_like_short_category_list(stripped)

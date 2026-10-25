"""Helpers for turning broad detection output into reviewable seed candidates.

The normalization step stays explicit and conservative: it splits broad lists
into smaller candidates, but it does not pretend to prove that every fragment
is already a valid atomic seed. The manager still decides what is accepted or
rejected.

Language note: the token lists and the generated " ontbreekt." suffix
("ontbreekt" is Dutch for "is missing") are retained, documented input-language
aliases for the historical Dutch research corpus. They are matched or appended
as literal tokens, and translating them would change the generated seed text and
the behavior of the existing corpus and its tests. English prose (comments,
docstrings, messages) is the canonical language of this module; the Dutch tokens
are data, not user-facing text.
"""

from __future__ import annotations

import re

# Dutch broad-intro prefixes stripped before splitting. Glosses: "voeg ... toe
# met aandacht voor" = "add ... with attention to"; "ontbrekende context/
# onderdelen" = "missing context/parts"; "let op:" = "note:".
BROAD_PREFIXES = (
    "voeg een volledig analysekader toe met aandacht voor",
    "voeg een analysekader toe met aandacht voor",
    "ontbrekende context:",
    "ontbrekende onderdelen:",
    "let op:",
)

SEPARATOR_PATTERN = re.compile(r"\s*(?:,|;)\s*", re.IGNORECASE)
CONJUNCTION_PATTERN = re.compile(r"\s*(?:\ben\b|\bof\b)\s*", re.IGNORECASE)


def clean_candidate_text(text: str) -> str:
    text = re.sub(r"^[-*\d.)\s]+", "", text.strip())
    text = re.sub(r"\s+", " ", text)
    return text.strip(" .")


def strip_broad_prefix(text: str) -> str:
    lowered = text.lower()
    for prefix in BROAD_PREFIXES:
        if lowered.startswith(prefix):
            return text[len(prefix) :].strip(" :.-")
    return text


def maybe_expand_fragment(fragment: str, expand_short_fragments: bool = True) -> str:
    """Normalize a fragment into a seed-shaped sentence.

    When ``expand_short_fragments`` is True (the default and the historical
    behavior) short fragments get " ontbreekt." appended, so that broad
    human-written categories like "kolonialisme" become "kolonialisme
    ontbreekt." When it is False — appropriate for output coming from a
    real language-model detector — short fragments are returned as-is, because
    a language model is expected to deliver whole-sentence gaps. Appending
    "ontbreekt" to a model-emitted fragment usually disguises garbage as a
    well-formed seed.
    """
    fragment = clean_candidate_text(fragment)
    if not fragment:
        return ""
    # An atomic question is already a complete candidate; its punctuation
    # must not become "?.", nor should it be rewritten as "ontbreekt".
    if fragment.endswith(("?", "!")):
        return fragment
    lowered = fragment.lower()
    if lowered.endswith(" ontbreken"):
        stem = fragment[: -len(" ontbreken")].strip()
        return f"{stem} ontbreekt."
    if lowered.endswith(" ontbreekt"):
        return fragment + "."
    if len(fragment.split()) <= 4:
        if not expand_short_fragments:
            return fragment + "."
        return f"{fragment} ontbreekt."
    return fragment + "."


def looks_like_short_category_stack(text: str) -> bool:
    cleaned = clean_candidate_text(text)
    lowered = cleaned.lower()
    if not (lowered.endswith(" ontbreekt") or lowered.endswith(" ontbreken")):
        return False
    if "," in lowered or ";" in lowered:
        return False
    return len(lowered.split()) <= 6 and (" en " in lowered or " of " in lowered)


def looks_like_short_category_fragment(text: str) -> bool:
    cleaned = clean_candidate_text(text)
    lowered = cleaned.lower()
    if "," in lowered or ";" in lowered:
        return False
    return len(lowered.split()) <= 4 and (" en " in lowered or " of " in lowered)


def split_broad_seed_text(text: str, expand_short_fragments: bool = True) -> list[str]:
    normalized = strip_broad_prefix(clean_candidate_text(text))
    if not normalized:
        return []

    if "," in normalized or ";" in normalized:
        raw_fragments = [clean_candidate_text(part) for part in SEPARATOR_PATTERN.split(normalized)]
        expanded: list[str] = []
        for raw_fragment in raw_fragments:
            if not raw_fragment:
                continue
            if looks_like_short_category_stack(raw_fragment) or looks_like_short_category_fragment(raw_fragment):
                expanded.extend(
                    maybe_expand_fragment(part, expand_short_fragments=expand_short_fragments)
                    for part in CONJUNCTION_PATTERN.split(clean_candidate_text(raw_fragment))
                )
            else:
                expanded.append(maybe_expand_fragment(raw_fragment, expand_short_fragments=expand_short_fragments))
        return [fragment for fragment in expanded if fragment]

    if looks_like_short_category_stack(normalized):
        fragments = [
            maybe_expand_fragment(part, expand_short_fragments=expand_short_fragments)
            for part in CONJUNCTION_PATTERN.split(normalized)
        ]
        return [fragment for fragment in fragments if fragment]

    return [maybe_expand_fragment(normalized, expand_short_fragments=expand_short_fragments)]


def normalize_detection_candidates_with_sources(
    candidates: list[str] | tuple[str, ...],
    expand_short_fragments: bool = True,
    split_broad: bool = True,
) -> list[tuple[int, str]]:
    """Use the ONE canonical normalizer while preserving each raw input index.

    A broad item can split into several normalized items, all with the same
    source index. Repeated raw text keeps separate indices. The mapping is
    about string transformations, NOT semantic correctness or model origin.
    """
    normalized: list[tuple[int, str]] = []
    for raw_index, candidate in enumerate(candidates):
        cleaned = clean_candidate_text(candidate)
        if not cleaned:
            continue
        if not split_broad:
            candidate_text = maybe_expand_fragment(
                cleaned, expand_short_fragments=expand_short_fragments
            )
            if candidate_text:
                normalized.append((raw_index, candidate_text))
            continue
        normalized.extend(
            (raw_index, text)
            for text in split_broad_seed_text(
                cleaned, expand_short_fragments=expand_short_fragments
            )
        )
    return normalized


def normalize_detection_candidates(
    candidates: list[str] | tuple[str, ...],
    expand_short_fragments: bool = True,
    split_broad: bool = True,
) -> list[str]:
    """Normalize raw detection output with the canonical shared rules.

    This historical API remains list[str]. Provenance-aware callers may use
    normalize_detection_candidates_with_sources; no second set of splitting
    or punctuation rules exists.
    """
    return [
        item
        for _raw_index, item in normalize_detection_candidates_with_sources(
            candidates,
            expand_short_fragments=expand_short_fragments,
            split_broad=split_broad,
        )
    ]

"""Helpers for turning broad detection output into reviewable seed candidates.

SSL 4.5 requires a normalization step before storage. This module keeps that
step explicit and conservative: it splits broad lists into smaller candidates,
but it does not pretend to prove that every fragment is already a valid atomic
seed. The manager still decides what is accepted or rejected.
"""

from __future__ import annotations

import re

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


def normalize_detection_candidates(
    candidates: list[str] | tuple[str, ...],
    expand_short_fragments: bool = True,
    split_broad: bool = True,
) -> list[str]:
    """Normalize raw detection output into seed-shaped candidates.

    Set ``expand_short_fragments=False`` for output produced by a real
    taalmodel detector. The historical default keeps the auto-"ontbreekt"
    expansion which is appropriate for broad human-written categories
    but disguises garbage as a well-formed seed when applied to model
    output.

    Set ``split_broad=False`` for real taalmodel output. The comma /
    semicolon / "en" / "of" splitting exists to break up broad
    human-written category stacks ("Security, privacy en schaalbaarheid
    ontbreken."). A language model already emits one gap per line, and
    natural sentences contain commas, so splitting them only shreds whole
    sentences into fragments ("De #36." / "wordt niet aangegeven.").
    """
    normalized: list[str] = []
    for candidate in candidates:
        cleaned = clean_candidate_text(candidate)
        if not cleaned:
            continue
        if not split_broad:
            normalized.append(maybe_expand_fragment(cleaned, expand_short_fragments=expand_short_fragments))
            continue
        parts = split_broad_seed_text(cleaned, expand_short_fragments=expand_short_fragments)
        if len(parts) <= 1:
            normalized.append(maybe_expand_fragment(cleaned, expand_short_fragments=expand_short_fragments))
            continue
        normalized.extend(parts)
    return normalized

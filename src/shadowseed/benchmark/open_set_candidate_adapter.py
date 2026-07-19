"""Open-set candidate adapter — templated baseline, not a 4.6 detector.

This module fills the open-set candidate slot with a small set of English
template sentences chosen by a regex over the input text. It is not a
language model and it does not satisfy the SSL 4.6 one-sentence claim, which
requires that a language model perform the detection step
(see `docs/00_shadow_seed_learning_4_6.md`).

Its role is therefore:

- infrastructural baseline for the open-set pipeline (item -> packets -> review)
- regression fixture for the packet generator and review summary code
- not an open-set seed-quality evidence source (Layer C in `00_`)

The generated candidates are meta-categories such as evidence for a central
claim or an affected party outside the main actor. that
`docs/02_atomic_seeds.md` lists as forbidden seed shapes. Reviewers should
reject them. A real detector belongs in a separate module that calls a
language model (for example via the existing hf-transformers backend used by
the model-benefit suite).

The SSLManager still performs normalization, atomicity checks, deduplication
and storage with weight starting at 0.0 around whatever candidates land here.
"""

from __future__ import annotations

import re
from typing import Any


OPEN_SET_CANDIDATE_ADAPTER_ID = "ssl45_open_set_candidate_adapter_v0.1"
EXPLICIT_CANDIDATE_SOURCE = "explicit_candidate_seeds"
OPEN_SET_ADAPTER_SOURCE = "open_set_candidate_adapter"

_COMMON_SENTENCE_INITIALS = frozenset(
    {
        "the",
        "a",
        "an",
        "this",
        "that",
        "these",
        "those",
        "it",
        "they",
        "we",
        "you",
        "he",
        "she",
        "i",
        "company",
        "companies",
        "people",
        "person",
        "someone",
        "everyone",
        "everybody",
        "anyone",
        "anybody",
        "de",
        "het",
        "een",
        "deze",
        "die",
        "dat",
        "dit",
        "ze",
        "zij",
        "hij",
        "wij",
        "jullie",
        "men",
        "bedrijf",
        "bedrijven",
        "iemand",
        "iedereen",
        "niemand",
        "today",
        "yesterday",
        "tomorrow",
        "here",
        "there",
        "vandaag",
        "gisteren",
        "morgen",
        "hier",
        "daar",
        "ag",
        "news",
        "business",
        "sci",
        "tech",
        "world",
        "sports",
    }
)

_CLAIM_TERMS = (
    "says",
    "said",
    "claim",
    "claims",
    "announced",
    "reported",
    "report",
    "according",
)
_TIME_TERMS = (
    "after",
    "before",
    "during",
    "deadline",
    "today",
    "yesterday",
    "monday",
    "tuesday",
    "wednesday",
    "thursday",
    "friday",
    "saturday",
    "sunday",
)
_AFFECTED_GROUP_TERMS = (
    "workers",
    "customers",
    "users",
    "patients",
    "investors",
    "students",
    "residents",
    "teams",
    "unions",
)
_DECISION_TERMS = (
    "wins",
    "won",
    "sets",
    "agrees",
    "rejects",
    "approves",
    "plans",
    "launches",
    "cuts",
    "raises",
)

_NUMBER_PATTERN = re.compile(
    r"(?:[$#€£]\s?\d|\d+(?:\.\d+)?\s?(?:million|billion|percent|%))",
    re.IGNORECASE,
)
_ENTITY_PATTERN = re.compile(r"\b[A-ZÀ-Þ][a-zA-ZÀ-ÿ0-9]{2,}\b")
_GENERATED_AG_NEWS_TITLE = re.compile(r"^AG News (?:Business|Sci/Tech|World|Sports) #\d+$")


def compact_text(value: Any) -> str:
    return " ".join(str(value or "").split())


def item_text(item: dict[str, Any]) -> str:
    return compact_text(item.get("text") or item.get("input") or "")


def _semantic_title(title: str) -> str:
    """Remove generated source labels that are not source content."""
    if _GENERATED_AG_NEWS_TITLE.match(title):
        return ""
    return title


def _contains_any(text: str, terms: tuple[str, ...]) -> bool:
    lowered = text.lower()
    return any(term in lowered for term in terms)


def _extract_first_entity(text: str) -> str | None:
    """Return the first proper-noun-like token in text."""
    if not text:
        return None
    for token in _ENTITY_PATTERN.findall(text):
        if token.lower() in _COMMON_SENTENCE_INITIALS:
            continue
        return token
    return None


def _append_unique(candidates: list[str], candidate: str, max_seeds: int) -> None:
    clean = compact_text(candidate)
    if clean and clean not in candidates and len(candidates) < max_seeds:
        candidates.append(clean)


def detect_open_set_candidates(item: dict[str, Any], max_seeds: int = 5) -> list[str]:
    """Create reviewable candidate seeds for an unknown open-set item.

    The candidates follow the 4.5 detection-pass shape: small, concrete and
    testable missing relations. They are hypotheses for review, not labels.
    """
    title = _semantic_title(compact_text(item.get("title", "")))
    text = item_text(item)
    if not (title or text):
        return []

    combined = compact_text(f"{title} {text}")
    entity = _extract_first_entity(combined)
    candidates: list[str] = []

    if entity:
        _append_unique(candidates, f"Role of {entity} in the event.", max_seeds)
    else:
        _append_unique(candidates, "Main actor in the described event.", max_seeds)

    if _contains_any(combined, _CLAIM_TERMS):
        _append_unique(candidates, "Source of the central claim.", max_seeds)
    else:
        _append_unique(candidates, "Evidence supporting the central claim.", max_seeds)

    if _contains_any(combined, _TIME_TERMS):
        _append_unique(candidates, "Timeline of the described event.", max_seeds)
    else:
        _append_unique(candidates, "Timing of the described event.", max_seeds)

    if _contains_any(combined, _AFFECTED_GROUP_TERMS):
        _append_unique(candidates, "Group directly affected in the item.", max_seeds)
    else:
        _append_unique(candidates, "Involved party outside the main actor.", max_seeds)

    if _NUMBER_PATTERN.search(combined):
        _append_unique(candidates, "Source of the reported figures.", max_seeds)
    elif _contains_any(combined, _DECISION_TERMS):
        _append_unique(candidates, "Reason for the described decision.", max_seeds)
    else:
        _append_unique(candidates, "Uncertainty surrounding the central claim.", max_seeds)

    return candidates[:max_seeds]


SUPPORTED_DETECTORS: tuple[str, ...] = ("adapter_v1", "adapter_v2", "model")


def raw_open_set_candidates(
    item: dict[str, Any],
    detector: str = "adapter_v1",
    model_backend: Any = None,
) -> tuple[list[str], str]:
    """Return explicit sample candidates or generated open-set candidates.

    `detector` selects the candidate generator when no explicit candidates
    are present on the item:

    - ``adapter_v1`` (default, backwards compatible): the v0.1 regex-template
      baseline in this module.
    - ``adapter_v2``: the v0.2 text-grounded baseline in
      ``open_set_candidate_adapter_v2``.
    - ``model``: the v0.3 language-model detector in ``open_set_model_detector``.
      Requires ``model_backend`` to be an instantiated ``DetectorBackend``
      (caller constructs it once and reuses it across items so models are
      not reloaded per call).

    Explicit ``candidate_seeds`` on the item always win, regardless of the
    selected detector.
    """
    explicit = item.get("candidate_seeds")
    if isinstance(explicit, list) and explicit:
        candidates = [str(seed).strip() for seed in explicit if str(seed).strip()]
        return candidates, EXPLICIT_CANDIDATE_SOURCE

    if detector == "adapter_v2":
        from .open_set_candidate_adapter_v2 import (
            OPEN_SET_ADAPTER_V2_SOURCE,
            detect_open_set_candidates_v2,
        )

        return detect_open_set_candidates_v2(item), OPEN_SET_ADAPTER_V2_SOURCE

    if detector == "model":
        if model_backend is None:
            raise ValueError(
                "detector='model' requires a model_backend instance; "
                "use open_set_model_detector.make_detector_backend(...)"
            )
        from .open_set_model_detector import OPEN_SET_MODEL_DETECTOR_SOURCE

        return model_backend.detect_seeds(item), OPEN_SET_MODEL_DETECTOR_SOURCE

    if detector != "adapter_v1":
        raise ValueError(
            f"Unknown detector {detector!r}. Allowed: {SUPPORTED_DETECTORS}."
        )

    return detect_open_set_candidates(item), OPEN_SET_ADAPTER_SOURCE

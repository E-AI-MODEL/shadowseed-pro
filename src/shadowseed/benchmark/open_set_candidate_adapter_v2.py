"""Open-set candidate adapter v0.2 — text-grounded baseline, still not a 4.6 detector.

This is a strict improvement on `open_set_candidate_adapter` (v0.1) on one
specific failure mode: v0.1 produces generic meta-categories that fit almost
any item. v0.2 instead extracts concrete tokens from the input
text and slots them into seed templates, so each generated seed contains
at least one word that ties it to the actual item.

What v0.2 fixes versus v0.1:

- every seed contains a token taken from the input text
- two different items produce two different seed sets (no more 10-of-12
  template reuse)

What v0.2 still does not do (and should not be claimed to do):

- it is not a language model — it does not satisfy the SSL 4.6 one-sentence
  claim, which requires a language model for the detection step
- it can pick the wrong token or the wrong relation; reviewers will still
  reject many candidates, just on different grounds (`not_relevant`,
  `style_not_gap`) instead of `too_vague`

Its role is therefore:

- stronger baseline than v0.1 for the open-set pipeline
- regression fixture once a real language-model detector (v0.3) lands, so the
  two can be compared side-by-side on the same batches
- not Layer C (open-set seed-quality) evidence on its own

See `docs/00_shadow_seed_learning_4_6.md` for the canonical seed contract
and `docs/02_atomic_seeds.md` for the seed criteria.
"""

from __future__ import annotations

import re
from typing import Any

from .open_set_candidate_adapter import (
    _COMMON_SENTENCE_INITIALS,
    _GENERATED_AG_NEWS_TITLE,
    compact_text,
    item_text,
)


OPEN_SET_ADAPTER_V2_ID = "ssl46_open_set_candidate_adapter_v0.2"
OPEN_SET_ADAPTER_V2_SOURCE = "open_set_candidate_adapter_v0_2"


_ENTITY_PATTERN = re.compile(r"\b[A-ZÀ-Þ][a-zA-ZÀ-ÿ0-9'\-]{2,}\b")
_CONTENT_WORD_PATTERN = re.compile(r"\b[a-zà-ÿ][a-zà-ÿ'\-]{5,}\b")

_SEED_TEMPLATES: tuple[str, ...] = (
    "Evidence supporting the statement about {token}.",
    "Causal relation between {token} and the outcome in this item.",
    "Timeline surrounding {token}.",
    "Party affected by {token}.",
    "Conditions or mechanism behind {token}.",
)


def _semantic_title(title: str) -> str:
    if _GENERATED_AG_NEWS_TITLE.match(title):
        return ""
    return title


def _extract_salient_tokens(combined: str, limit: int) -> list[str]:
    """Pick distinct text-grounded tokens, entities first then content words."""
    seen: set[str] = set()
    ordered: list[str] = []

    for token in _ENTITY_PATTERN.findall(combined):
        key = token.lower()
        if key in _COMMON_SENTENCE_INITIALS or key in seen:
            continue
        seen.add(key)
        ordered.append(token)
        if len(ordered) >= limit:
            return ordered

    for token in _CONTENT_WORD_PATTERN.findall(combined):
        key = token.lower()
        if key in _COMMON_SENTENCE_INITIALS or key in seen:
            continue
        seen.add(key)
        ordered.append(token)
        if len(ordered) >= limit:
            return ordered

    return ordered


def detect_open_set_candidates_v2(item: dict[str, Any], max_seeds: int = 5) -> list[str]:
    """Build text-grounded candidate seeds for an unknown open-set item.

    Returns at most `max_seeds` seeds. Each seed contains a token extracted
    from the input text, so two different items produce two different seed
    sets. The seeds are hypotheses for human review, not labels.
    """
    title = _semantic_title(compact_text(item.get("title", "")))
    text = item_text(item)
    if not (title or text):
        return []

    combined = compact_text(f"{title} {text}")
    tokens = _extract_salient_tokens(combined, max_seeds)

    if not tokens:
        return []

    candidates: list[str] = []
    seen: set[str] = set()
    for idx, token in enumerate(tokens):
        template = _SEED_TEMPLATES[idx % len(_SEED_TEMPLATES)]
        seed = template.format(token=token)
        if seed in seen:
            continue
        seen.add(seed)
        candidates.append(seed)
        if len(candidates) >= max_seeds:
            break

    return candidates

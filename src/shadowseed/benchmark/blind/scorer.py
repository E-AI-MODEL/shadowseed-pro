"""Scoring helpers for the blind benchmark."""

from __future__ import annotations

import re

from shadowseed.benchmark.blind.schemas import BlindScore, HiddenLabel


STOPWORDS = {
    "de", "het", "een", "en", "of", "van", "in", "op", "te", "is", "zijn", "was",
    "met", "als", "voor", "bij", "door", "naar", "uit", "aan", "dat", "dit", "die",
    "this", "that", "the", "and", "or", "of", "in", "on", "to", "a", "an", "are",
    "were", "with", "for", "by", "as", "at", "from",
}


def tokenize(text: str) -> set[str]:
    words = re.findall(r"[A-Za-zÀ-ÿ0-9_]+", text.lower())
    return {word for word in words if word not in STOPWORDS and len(word) > 2}


def jaccard(a: str, b: str) -> float:
    a_tokens = tokenize(a)
    b_tokens = tokenize(b)
    if not a_tokens or not b_tokens:
        return 0.0
    return len(a_tokens & b_tokens) / len(a_tokens | b_tokens)


def matched_items(candidates: list[str], targets: list[str], threshold: float) -> list[str]:
    matches = []
    for target in targets:
        if any(jaccard(candidate, target) >= threshold for candidate in candidates):
            matches.append(target)
    return matches


def coverage(candidates: list[str], expected_gaps: list[str], threshold: float = 0.45) -> tuple[float, list[str]]:
    if not expected_gaps:
        return 0.0, []
    matches = matched_items(candidates, expected_gaps, threshold)
    return len(matches) / len(expected_gaps), matches


def unsupported_matches(candidates: list[str], must_not_add: list[str], threshold: float = 0.45) -> list[str]:
    return matched_items(candidates, must_not_add, threshold)


def score_blind_result(
    baseline_candidates: list[str],
    ssl_candidates: list[str],
    label: HiddenLabel,
    unsupported_penalty: float = 0.25,
) -> BlindScore:
    """Score baseline and SSL candidates against private labels."""
    baseline_coverage, _baseline_matches = coverage(baseline_candidates, label.expected_gaps)
    ssl_coverage, ssl_matches = coverage(ssl_candidates, label.expected_gaps)
    unsupported = unsupported_matches(ssl_candidates, label.must_not_add)

    false_positive_count = max(0, len(ssl_candidates) - len(ssl_matches) - len(unsupported))
    coverage_delta = ssl_coverage - baseline_coverage
    net_benefit = coverage_delta - (unsupported_penalty * len(unsupported))

    return BlindScore(
        baseline_gap_coverage=baseline_coverage,
        ssl_gap_coverage=ssl_coverage,
        coverage_delta=coverage_delta,
        unsupported_additions=len(unsupported),
        false_positive_count=false_positive_count,
        net_benefit=net_benefit,
        matched_expected_gaps=ssl_matches,
        matched_unsupported_additions=unsupported,
    )

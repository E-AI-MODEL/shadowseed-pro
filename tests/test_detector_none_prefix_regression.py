"""Regression tests for legacy-prefixed NONE detector output."""

import pytest

from shadowseed.detection.model_detector import parse_numbered_seeds_with_diagnostics


@pytest.mark.parametrize(
    "raw",
    [
        "NONE\n1. What remains unmeasured?",
        "1. NONE\n1. What remains unmeasured?",
        "1. NONE\n2. What remains unmeasured?",
        "1. none\n1. A second candidate",
    ],
)
def test_none_prevents_mixed_candidates(raw):
    seeds, diagnostics = parse_numbered_seeds_with_diagnostics(raw)
    assert seeds == []
    assert diagnostics["explicit_none"] is True
    assert diagnostics["mixed_none_output"] is True
    assert diagnostics["accepted_candidates"] == 0


@pytest.mark.parametrize("raw", ["NONE", "1. NONE"])
def test_unmixed_none_is_not_malformed(raw):
    seeds, diagnostics = parse_numbered_seeds_with_diagnostics(raw)
    assert seeds == []
    assert diagnostics["explicit_none"] is True
    assert diagnostics["mixed_none_output"] is False


def test_legacy_numbering_still_accepts_a_real_candidate():
    seeds, diagnostics = parse_numbered_seeds_with_diagnostics(
        "1. 1. The relation between observed values and measurement conditions."
    )
    assert seeds == ["The relation between observed values and measurement conditions."]
    assert diagnostics["nested_numbering_prefixes_removed"] == 1

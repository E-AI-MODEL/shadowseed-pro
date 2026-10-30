"""Regression: a leading NONE never births candidates from explanations.

Genuine HF Qwen2.5-0.5B calibration run 40831589642 exposed the pattern:
the raw detector began with NONE, then added numbered explanatory examples.
The parser previously accepted those examples even though the output had
explicitly said there were no candidate gaps. These tests use reduced synthetic
reproductions; the original model-output artifact remains unchanged.
"""

import pytest

from shadowseed.detection.model_detector import (
    parse_numbered_seeds_with_diagnostics,
)


@pytest.mark.parametrize(
    "raw",
    [
        "NONE\\n\\nExplanation: no distinct gap.\\n1. What remains unmeasured?\\n2. Is a prior question unanswered?",
        "  **NONE**\\n\\nThere are two hypothetical gaps.\\n1. What remains unmeasured?",
        "NONE: no distinct candidates\\n1. What remains unmeasured?",
        "NONE The draft already covers the subject.\\n1. What remains unmeasured?",
    ],
)
def test_leading_none_mixed_with_numbered_explanation_fails_closed(raw: str) -> None:
    # The detector format is either a standalone NONE or a numbered list.
    # A contradictory mixture cannot become an apparent seed discovery.
    candidates, diagnostics = parse_numbered_seeds_with_diagnostics(raw)
    assert candidates == []
    assert diagnostics["explicit_none"] is True
    assert diagnostics["mixed_none_output"] is True
    assert diagnostics["accepted_candidates"] == 0


def test_standalone_none_still_reports_clean_empty_output() -> None:
    candidates, diagnostics = parse_numbered_seeds_with_diagnostics(" NONE ")
    assert candidates == []
    assert diagnostics["explicit_none"] is True
    assert diagnostics["mixed_none_output"] is False


def test_numbered_candidate_without_none_remains_parseable() -> None:
    candidate = "Could transit patterns explain the untested weekend anomaly?"
    candidates, diagnostics = parse_numbered_seeds_with_diagnostics(f"1. {candidate}")
    assert candidates == [candidate]
    assert diagnostics["explicit_none"] is False
    assert diagnostics["mixed_none_output"] is False

"""Predeclared MIT recurrence pair controls, using the existing parser."""
from research.experiments.mit_shadow_memory_20261103.run_identity_pilot import (
    CLUSTER_PAIRS, EXACT_POSITIVE_CONTROLS, build_source_rows
)
from shadowseed.recurrence_recognition import parse_answer, Verdict
import pytest

def test_recurrence_format_and_fail_closed_range():
    assert parse_answer("a: 1", 1, 1)[0] == Verdict(open_question=1)
    assert parse_answer("a: NONE", 1, 1)[0] == Verdict()
    assert parse_answer("a: 2", 1, 1)[0] == Verdict()
    assert parse_answer("malformed response", 1, 1) is None

def test_pair_set_frozen_with_negative_and_positive_controls():
    assert len(CLUSTER_PAIRS) == 12
    assert len(EXACT_POSITIVE_CONTROLS) == 2
    all_pairs = CLUSTER_PAIRS + EXACT_POSITIVE_CONTROLS
    assert len({(earlier, later) for earlier,later,_,_ in all_pairs}) == 14
    assert all(earlier < later for earlier,later,_,_ in all_pairs)
    assert {label for _,_,label,_ in CLUSTER_PAIRS} == {"same","different","related"}
    assert all(label == "same" for _,_,label,_ in EXACT_POSITIVE_CONTROLS)

def test_partial_source_trajectory_rejected():
    with pytest.raises(ValueError):
        build_source_rows("## t001\n### astra\n# Hypothesis: A hypothesis")

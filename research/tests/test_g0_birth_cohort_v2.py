"""Offline checks for real, late and missing seed birth cohorts."""
from __future__ import annotations
from types import SimpleNamespace
from unittest.mock import patch
import pytest

from shadowseed_research.benchmark.g0_birth_cohort_v2 import (
    BirthDecision, cohort_census, select_first_eligible_birth,
)
from shadowseed_research.benchmark.g0_next_inquiry_readiness import (
    prepare_inquiry_pair,
)
from test_g0_next_inquiry_readiness import study_inputs, SEED


class Engine:
    def __init__(self, born):
        self.born = born
    def export_state(self):
        return {"born_turn": self.born}


def test_T1_real_birth_retains_T2_T3_followups():
    engine = Engine({"ss_001": 1})
    report = {"turn": 1, "seeds_born_weightless": ["ss_001"]}
    with patch(
        "shadowseed_research.benchmark.g0_birth_cohort_v2.freeze_canonical_weightless_birth",
        return_value={"snapshot_sha256": "real_engine_checkpoint"},
    ) as frozen:
        decision = select_first_eligible_birth(
            engine, report, turn=1, total_turns=4
        )
    assert decision.status == "selected_real_weightless_birth"
    assert (decision.birth_turn, decision.first_inquiry_turn,
            decision.second_inquiry_turn) == (1, 2, 3)
    assert decision.seed_id == "ss_001"
    assert decision.checkpoint["snapshot_sha256"] == "real_engine_checkpoint"
    frozen.assert_called_once_with(engine, report, "ss_001")


def test_never_promote_late_birth_or_repeated_candidate():
    result = select_first_eligible_birth(
        Engine({"ss_late": 2}),
        {"turn": 2, "seeds_born_weightless": ["ss_late"]},
        turn=2, total_turns=4,
    )
    assert result.status == "real_birth_too_late_for_two_followups"
    assert result.seed_id is None
    repeated = select_first_eligible_birth(
        Engine({"ss_old": 0}),
        {"turn": 1, "seeds_born_weightless": ["ss_old"]},
        turn=1, total_turns=4,
    )
    assert repeated.status == "no_canonical_birth_this_turn"


def test_no_birth_not_equal_to_zero_effect_and_no_cherrypicking():
    absent = select_first_eligible_birth(
        Engine({}), {"turn": 0, "seeds_born_weightless": []},
        turn=0, total_turns=4
    )
    assert absent.status == "no_canonical_birth_this_turn"
    census = cohort_census([
        BirthDecision("selected_real_weightless_birth", 1, 2, 3, "ss", {}),
        BirthDecision("real_birth_too_late_for_two_followups", 2, None, None, None, None),
        BirthDecision("no_birth_observed_by_end", None, None, None, None, None),
        BirthDecision("failed_or_incomplete", None, None, None, None, None),
    ], 4)
    assert sum(census["outcomes"].values()) == 4
    assert census["outcomes"]["failed_or_incomplete"] == 1
    assert not census["q2_proven"]


def test_new_first_inquiry_after_T1_birth_has_no_prior_questions():
    case, prior, note = study_inputs(turn=2)
    pair = prepare_inquiry_pair(
        case, prior, note, SEED, 2, {"A": None, "B": None},
        first_inquiry_turn=2,
    )
    assert pair["first_inquiry_turn"] == 2
    assert pair["prompts"]["A"]["own_prior_questions_only"] is False
    assert "EIGEN EERDERE ONDERZOEKSVRAGEN" not in pair["prompts"]["A"]["prompt"]
    assert SEED not in pair["prompts"]["A"]["prompt"]
    assert SEED in pair["prompts"]["B"]["prompt"]


def test_second_inquiry_uses_only_its_own_prior_track():
    case, prior, note = study_inputs(turn=3)
    pair = prepare_inquiry_pair(
        case, prior, note, SEED, 3,
        {"A": {"tag": "ARM_A_QUESTION"}, "B": {"tag": "ARM_B_QUESTION"}},
        first_inquiry_turn=2,
    )
    pa = pair["prompts"]["A"]["prompt"]
    pb = pair["prompts"]["B"]["prompt"]
    assert "ARM_A_QUESTION" in pa and "ARM_B_QUESTION" not in pa
    assert "ARM_B_QUESTION" in pb and "ARM_A_QUESTION" not in pb


@pytest.mark.parametrize("bad_turn,first", [(1,2),(0,1),(4,2)])
def test_wrong_birth_and_inquiry_order_rejected(bad_turn,first):
    case, prior, note = study_inputs(turn=3)
    with pytest.raises(ValueError):
        prepare_inquiry_pair(
            case, prior[:bad_turn + 1], note, SEED, bad_turn,
            {"A": None, "B": None}, first_inquiry_turn=first
        )


def test_census_rejects_missing_cases():
    with pytest.raises(ValueError):
        cohort_census([], 4)

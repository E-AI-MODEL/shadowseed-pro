"""No-network regression for NEXT study readiness, never real model evidence."""
from __future__ import annotations

from copy import deepcopy

import pytest

from shadowseed_research.benchmark.g0_multicase_real_ab import (
    _parse_research, research_prompt,
)
from shadowseed_research.benchmark.g0_next_inquiry_readiness import (
    INQUIRY_INSTRUCTIONS_V2, MAX_CHARS, check_output_contract,
    prepare_inquiry_pair, safe_checkpoint_failure,
)
from shadowseed_research.benchmark.real_seed_rf_inquiry import _user_input

SEED = "Onbewezen relatie X tussen de volgorde en het onafhankelijke resultaat"


def study_inputs(turn: int = 2):
    """Synthetic long case; fake text is NOT a scientific observation."""
    case = {
        "id": "TEST_FICTION",
        "context": "K" * 2100,
        "turns": [
            {"question": "Vraag " + "Q" * 475, "new_observation": ""},
            {"question": "Vraag " + "R" * 475,
             "new_observation": "V" * 1180},
            {"question": "Vraag " + "S" * 475,
             "new_observation": "W" * 1180},
            {"question": "Vraag " + "T" * 475,
             "new_observation": "Z" * 1180},
        ],
    }
    prior = [
        (_user_input(case, t), "antwoord-%d:" % i + "H" * 1520)
        for i, t in enumerate(case["turns"][:turn + 1])
    ]
    return case, prior, "neutrale notitie " + "N" * 125


def test_fixed_template_matches_existing_strict_parser_and_no_none_pressure():
    check_output_contract()
    assert "maximaal twee" in INQUIRY_INSTRUCTIONS_V2
    assert "maximaal drie" in INQUIRY_INSTRUCTIONS_V2
    assert "geen experiment uit" in INQUIRY_INSTRUCTIONS_V2
    assert _parse_research(
        '{"status":"none","proposals":[],"unresolved_alternatives":[]}'
    )["status"] == "valid_none"


def test_T1_only_seed_slot_differs_and_future_observation_not_available():
    case, prior, note = study_inputs(turn=1)
    snapshot = deepcopy(prior)
    pair = prepare_inquiry_pair(
        case, prior, note, SEED, 1, {"A": None, "B": None}
    )
    a, b = (pair["prompts"][key]["prompt"] for key in ("A", "B"))
    assert "DEZELFDE GEWONE T0-NOTITIE" in a
    assert SEED not in a and SEED in b
    assert a.replace(
        "ONBEWEZEN KANDIDAAT (GEEN BEWIJS, GEEN PRODUCTPROMPT):\nNONE",
        "ONBEWEZEN KANDIDAAT (GEEN BEWIJS, GEEN PRODUCTPROMPT):\n" + SEED,
    ) == b
    assert "W" * 1180 not in a
    assert prior == snapshot  # the actual normal Engine history is unchanged
    assert pair["G0"] == "NOT_PASSED"
    assert not pair["study_is_confirmatory"]


def test_T2_eliminates_repeated_case_context_without_dropping_answers():
    case, prior, note = study_inputs(turn=2)
    earlier = {
        "status": "valid_questions",
        "proposals": [{
            "question": "Welke tweede proef kan de alternatieven scheiden?",
            "test": "Meet onafhankelijk onder beide condities.",
            "depends_on": "De externe tweede meting ontbreekt nog.",
        }],
        "unresolved_alternatives": [],
    }
    # The old v1 sidecar duplicated the same canonical case in every
    # ordinary user input. This test models the observed prompt-cap failure.
    old = research_prompt(case, prior, note, SEED, 2, earlier)
    assert len(old) > MAX_CHARS
    pair = prepare_inquiry_pair(
        case, prior, note, SEED, 2,
        {"A": earlier, "B": earlier}
    )
    for x in pair["prompts"].values():
        assert x["prompt_chars"] <= MAX_CHARS
        assert x["prompt"].count(case["context"]) == 1
        assert all(answer in x["prompt"] for _, answer in prior)
        assert all(turn["question"] in x["prompt"]
                   for turn in case["turns"][:3])
        assert case["turns"][1]["new_observation"] in x["prompt"]
        assert case["turns"][2]["new_observation"] in x["prompt"]
        assert x["external_action_executed"] is False
    assert pair["ordinary_context_sha256"]


def test_T2_keeps_each_arms_prior_questions_separate():
    case, prior, note = study_inputs(turn=2)
    a1 = {"status": "valid_questions", "proposals": [],
          "tag": "ONLY_A_PREVIOUS_INQUIRY"}
    b1 = {"status": "valid_none", "proposals": [],
          "tag": "ONLY_B_PREVIOUS_INQUIRY"}
    pair = prepare_inquiry_pair(
        case, prior, note, SEED, 2, {"A": a1, "B": b1}
    )
    pa = pair["prompts"]["A"]["prompt"]
    pb = pair["prompts"]["B"]["prompt"]
    assert "ONLY_A_PREVIOUS_INQUIRY" in pa
    assert "ONLY_B_PREVIOUS_INQUIRY" in pb
    assert "ONLY_B_PREVIOUS_INQUIRY" not in pa
    assert "ONLY_A_PREVIOUS_INQUIRY" not in pb
    assert SEED not in pa and SEED in pb


@pytest.mark.parametrize("problem", [
    "wrong_question", "existing_seed", "oversize", "wrong_tracks",
    "future_on_T1",
])
def test_fail_closed_before_provider_request(problem):
    case, prior, note = study_inputs(turn=1)
    earlier = {"A": None, "B": None}
    if problem == "wrong_question":
        prior[0] = ("noncanonical question", prior[0][1])
    elif problem == "existing_seed":
        note = note + " " + SEED
    elif problem == "oversize":
        prior[0] = (prior[0][0], "oversized " + "O" * 15000)
    elif problem == "wrong_tracks":
        earlier = {"A": None}
    elif problem == "future_on_T1":
        earlier = {"A": {"unavailable": True}, "B": None}
    with pytest.raises(ValueError):
        prepare_inquiry_pair(case, prior, note, SEED, 1, earlier)


def test_known_checkpoint_code_preserves_only_hashes_and_counts():
    state = {
        "turn": 3,
        "turn_reports": [{"turn": 0}, {"turn": 1}, {"turn": 2}],
        "manager": {
            "event_log": [{"event_type": "created"}],
            "gate_events": [],
        }
    }
    result = safe_checkpoint_failure(
        ValueError("previous checkpoint is not the preceding history"),
        state, case_id="TEST", turn=2,
        birth={"snapshot_sha256": "birth"},
        previous={"snapshot_sha256": "prior"},
    )
    assert result["error_code"] == "prior_history"
    assert result["history_count"] == 3
    assert result["event_log_count"] == 1
    assert result["birth_snapshot_sha256"] == "birth"
    assert result["prior_checkpoint_sha256"] == "prior"
    assert result["not_a_measured_zero_effect"]


def test_unknown_checkpoint_error_does_not_leak_raw_text():
    secret_text = "sensitive raw exception with example-credential-12345"
    result = safe_checkpoint_failure(
        ValueError(secret_text), {}, case_id="TEST", turn=2,
        birth=None, previous=None,
    )
    assert result["error_code"] == "unknown_checkpoint_error"
    assert len(result["error_message_sha256"]) == 64
    assert secret_text not in str(result)
    assert "example-credential" not in str(result)
    assert result["no_bypass_or_repair"]

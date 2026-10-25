"""No-network checks for prospective RF inquiry after a canonical first birth.

Uses real ShadowseedEngine, OpenAIDetectorBackend, parser, manager, Gate
and weightless longitudinal checkpoints. Only HTTP Responses/Embeddings
are faked. This is not evidence of model creativity or G0 approval.
"""
from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path

import numpy as np
import pytest

from shadowseed_research.benchmark.real_model_stage1_exploratory import (
    BoundedProvider,
    DETECTOR_INSTRUCTIONS,
    HOST_INSTRUCTIONS,
)
from shadowseed_research.benchmark.real_seed_rf_inquiry import (
    ARMS, MAX_CALLS, MAX_EMBEDDINGS, MAX_TOKENS, OUTPUT_CAP,
    INQUIRY_INSTRUCTIONS, NOTES_INSTRUCTIONS, OUTPUT_SCHEMA,
    _parse_inquiry, _inquiry_prompt, _user_input, run, validate,
)

FIXTURE = (
    Path(__file__).resolve().parents[1]
    / "fixtures" / "real_seed_rf_inquiry_v1.json"
)


def fixture() -> dict:
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


class FakeHttpProvider(BoundedProvider):
    def __init__(self, *, seed: bool = True, fail_at: int | None = None):
        super().__init__(
            "TEST_ONLY_NO_API_KEY", model_call_cap=MAX_CALLS,
            embedding_call_cap=MAX_EMBEDDINGS,
            all_token_cap=MAX_TOKENS, output_token_cap=OUTPUT_CAP,
        )
        self.detect_calls = 0
        self.call_count = 0
        self.seen_prompts: list[tuple[str, str]] = []
        self.seed = seed
        self.fail_at = fail_at

    def _post(self, endpoint: str, payload: dict) -> dict:
        if endpoint == "embeddings":
            assert payload["model"] == "text-embedding-3-small"
            x = np.zeros(1536)
            x[0] = 1
            return {
                "data": [{"index": 0, "embedding": x.tolist()}],
                "usage": {"total_tokens": 19},
            }
        if endpoint != "responses":
            raise AssertionError("unapproved network request")
        self.call_count += 1
        self.seen_prompts.append((payload["instructions"], payload["input"]))
        assert payload["store"] is False
        assert payload["model"] == "gpt-5"
        assert payload["max_output_tokens"] == OUTPUT_CAP
        if self.fail_at == self.call_count:
            return {
                "id": "fake-incomplete",
                "model": "gpt-5",
                "status": "incomplete",
                "incomplete_details": {"reason": "max_output_tokens"},
                "usage": {"input_tokens": 70, "output_tokens": 120},
                "output": [],
            }
        if payload["instructions"] == DETECTOR_INSTRUCTIONS:
            self.detect_calls += 1
            if self.seed and self.detect_calls == 1:
                text = (
                    "1. Onbekend of er verschillen zijn in mechanische "
                    "montage/omgeving van de sensoren (trilling, thermische "
                    "gradiënt, nabijheid van storingsbronnen) die kanaal 1 "
                    "selectief beïnvloeden."
                )
            else:
                text = "NONE"
        elif payload["instructions"] == HOST_INSTRUCTIONS:
            text = (
                "De verschillen tussen de sensormetingen zijn nog "
                "niet onafhankelijk geverifieerd."
            )
        elif payload["instructions"] == NOTES_INSTRUCTIONS:
            text = "Twee kanalen en een regelkast. Oorzaak niet bevestigd."
        elif payload["instructions"] == INQUIRY_INSTRUCTIONS:
            text = json.dumps({
                "question": "Welke onafhankelijke controle kan het verschil verklaren?",
                "test": "Vergelijk afzonderlijk vastgelegde waarnemingen.",
                "uncertainty": "Nog geen onafhankelijke resultaten.",
            })
        else:
            raise AssertionError("unexpected host instruction")
        return {
            "id": f"fake-{self.call_count}",
            "model": "gpt-5",
            "status": "completed",
            "usage": {"input_tokens": 70, "output_tokens": 120},
            "output": [{"content": [{"type": "output_text", "text": text}]}],
        }


def test_one_case_no_future_leakage_and_strict_json() -> None:
    data = fixture()
    c = validate(data)
    assert len(c["turns"]) == 3
    assert c["turns"][0]["new_observation"] == ""
    assert c["turns"][1]["new_observation"]
    first = _user_input(c, c["turns"][0])
    assert c["context"] in first
    assert c["turns"][1]["new_observation"] not in first
    assert c["turns"][2]["new_observation"] not in first
    assert _parse_inquiry("NONE") is None
    assert _parse_inquiry("not json") is None
    assert _parse_inquiry('{"question":"x","test":"x","uncertainty":"x"}') is None
    assert _parse_inquiry(
        '{"question":"Wat ontbreekt?","test":"Doe een nieuwe test.",'
        '"uncertainty":"Nog onbekend."}'
    ) is not None


def test_actual_engine_uses_true_birth_in_five_separate_research_arms() -> None:
    p = FakeHttpProvider()
    checkpoints: list[dict] = []
    result = run(fixture(), p, checkpoint=lambda r: checkpoints.append(deepcopy(r)))
    assert result["schema"] == OUTPUT_SCHEMA
    assert result["status"] == "completed_exploratory_real_seed_and_arm_questions"
    assert result["G0"] == "NOT_PASSED"
    assert result["q1_internal_absence_established"] is False
    assert result["q2_causal_novel_inquiry_established"] is False
    assert result["no_closed_loop_feedback"] is True
    assert len(result["ordinary_t0_samples"]) == 2
    assert result["first_seed"] is not None
    assert result["first_seed"]["weight"] == 0
    assert result["first_seed"]["evidence_count"] == 0
    assert len(result["turns"]) == 3
    assert result["turns"][0]["birth"]["raw_detector_item_to_seed_mapping_verified"]
    assert result["turns"][0]["followup"] is None
    assert result["turns"][1]["followup"]["turn"] == 1
    assert result["turns"][2]["followup"]["turn"] == 2
    for i in (1, 2):
        item = result["turns"][i]
        assert set(item["arms"]) == set(ARMS)
        assert all(a["parse_status"] == "valid_json" for a in item["arms"].values())
        assert all(a["independent_test_result"] is None for a in item["arms"].values())
        assert item["followup"]["seed_state_after_turn"]["weight"] == 0
        assert item["followup"]["seed_state_after_turn"]["evidence_count"] == 0
        assert item["followup"]["product_answer_seed_influence_observed"] is False
    assert all(t["none_control_answer_identical"] for t in result["turns"])
    assert p.model_calls == 19
    assert 0 < p.embedding_calls <= MAX_EMBEDDINGS
    assert result["provider_audit"]["recorded_tokens"] < MAX_TOKENS
    assert result["human_review_handoff"]["independent_review_complete"] is False
    assert len(result["human_review_handoff"]["episodes"]) == 5
    assert checkpoints and checkpoints[-1]["status"] == result["status"]
    assert not any(
        result["first_seed"]["text"] in prompt
        for instructions, prompt in p.seen_prompts
        if instructions == HOST_INSTRUCTIONS
    )


def test_real_absence_does_not_get_replaced_with_fake_birth() -> None:
    p = FakeHttpProvider(seed=False)
    o = run(fixture(), p)
    assert o["first_seed"] is None
    assert o["status"] == "completed_no_seed_no_q2_opportunity"
    assert all(not t["arms"] for t in o["turns"])
    assert p.model_calls == 9  # 2 ordinary, 3 host, 3 detector, 1 note
    assert o["q2_causal_novel_inquiry_established"] is False


def test_incomplete_model_is_not_treated_as_none() -> None:
    p = FakeHttpProvider(fail_at=3)
    with pytest.raises(RuntimeError, match="model returned no complete"):
        run(fixture(), p)
    assert p.model_calls == 3
    assert p.events[-1]["status"] == "incomplete"


@pytest.mark.parametrize("mutation", ["future_t0", "model", "regime", "extra", "missing"])
def test_invalid_scripted_prompts_cannot_be_used(mutation: str) -> None:
    d = deepcopy(fixture())
    if mutation == "future_t0":
        d["case"]["turns"][0]["new_observation"] = "future leaked"
    elif mutation == "model":
        d["model"] = "small"
    elif mutation == "regime":
        d["feedback_regime"] = "RI"
    elif mutation == "extra":
        d["case"]["turns"][1]["answer_key"] = "not allowed"
    else:
        d["case"]["turns"].pop()
    with pytest.raises(ValueError):
        validate(d)


def test_inquiry_only_sees_own_prior_question_not_other_arms() -> None:
    c = fixture()["case"]
    prompt = _inquiry_prompt(
        c, [("Vraag eerder", "Zichtbaar antwoord")],
        c["turns"][1]["new_observation"],
        c["turns"][1]["question"],
        arm="D", note="Testseed", earlier_question="Mijn eerdere vraag",
    )
    assert "Mijn eerdere vraag" in prompt
    assert "Testseed" in prompt
    assert c["turns"][2]["new_observation"] not in prompt
    assert "resultaat van die vraag" in prompt


def test_checkpoint_fail_closed_preserves_specific_invariant_and_no_t2_inquiries(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import shadowseed_research.benchmark.real_seed_rf_inquiry as module

    provider = FakeHttpProvider()
    original = module.freeze_weightless_followup
    checkpoints: list[dict] = []

    def fail_on_second_later_turn(engine, birth, *, previous=None):
        if previous is not None:
            raise ValueError("previous event ledger prefix was modified")
        return original(engine, birth, previous=previous)

    monkeypatch.setattr(module, "freeze_weightless_followup", fail_on_second_later_turn)
    with pytest.raises(ValueError, match="previous event ledger prefix was modified"):
        run(fixture(), provider, checkpoint=lambda x: checkpoints.append(deepcopy(x)))

    assert checkpoints
    last = checkpoints[-1]
    assert len(last["turns"]) == 3
    assert len(last["turns"][1]["arms"]) == 5
    assert last["turns"][2]["arms"] == {}
    diagnostics = last["turns"][2]["checkpoint_diagnostics"]
    assert diagnostics["error_code"] == "previous event ledger prefix was modified"
    assert diagnostics["no_automatic_repair"] is True
    assert diagnostics["expected_prior_history_sha256"] == diagnostics["actual_prior_history_sha256"]
    assert diagnostics["original_seed_weight"] == 0
    assert provider.model_calls == 14

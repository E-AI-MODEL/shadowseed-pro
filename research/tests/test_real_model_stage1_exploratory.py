"""No-network regressions for opt-in G0-PENDING real-model stage-1 adapter.

Run with the real canonical product Engine and real current-pair
OpenAIDetectorBackend. Replace ONLY the network HTTP transport. Never
treat the fake transcript here as model evidence or a scientific success.
"""
from __future__ import annotations

from copy import deepcopy
from pathlib import Path
import json

import numpy as np
import pytest

from shadowseed_research.benchmark.real_model_stage1_exploratory import (
    BoundedProvider,
    DETECTOR_INSTRUCTIONS,
    EMBEDDING_MODEL,
    HOST_INSTRUCTIONS,
    MAX_ALL_TOKENS,
    MAX_EMBEDDING_CALLS,
    MAX_MODEL_CALLS,
    MAX_OUTPUT_TOKENS,
    MODEL,
    OUTPUT_SCHEMA,
    SCHEMA,
    _host_prompt,
    run,
    validate_fixture,
)


FIXTURE = (
    Path(__file__).resolve().parents[1]
    / "fixtures" / "real_model_stage1_exploratory_v1.json"
)


class NoNetworkProvider(BoundedProvider):
    """Deterministic transport fixture, NOT a model or semantic scorer."""

    def __init__(self):
        super().__init__("TEST_ONLY_NOT_REAL_KEY")
        self._responses = 0

    def _post(self, endpoint: str, payload: dict) -> dict:
        if endpoint == "responses":
            self._responses += 1
            prompt = payload["input"]
            instructions = payload["instructions"]
            if instructions == DETECTOR_INSTRUCTIONS:
                if "testdozen" in prompt.lower():
                    text = "NONE"
                else:
                    text = (
                        "1. Of de tijdregistratie van beide meetkanalen "
                        "werkelijk gesynchroniseerd is?"
                    )
            elif instructions == HOST_INSTRUCTIONS:
                if "testdozen" in prompt.lower():
                    text = (
                        "De twintig testdozen en de voorraadlijst spreken "
                        "elkaar niet tegen. Er is geen verdere meting gevraagd."
                    )
                else:
                    text = (
                        "De waargenomen verschillen bewijzen nog geen oorzaak. "
                        "De meetsystemen zijn niet onafhankelijk geijkt."
                    )
            else:
                raise AssertionError("unsupported research model role")
            assert payload["model"] == MODEL
            assert payload["store"] is False
            assert payload["max_output_tokens"] == MAX_OUTPUT_TOKENS
            return {
                "id": f"fake-resp-{self._responses}",
                "model": MODEL,
                "status": "completed",
                "usage": {"input_tokens": 90, "output_tokens": 50},
                "output": [
                    {"content": [{"type": "output_text", "text": text}]}
                ],
            }
        if endpoint == "embeddings":
            assert payload["model"] == EMBEDDING_MODEL
            assert len(payload["input"]) == 1
            vector = np.zeros(1536, dtype=float)
            vector[0] = 1
            return {
                "data": [{"index": 0, "embedding": vector.tolist()}],
                "usage": {"total_tokens": 15},
            }
        raise AssertionError(f"unexpected endpoint {endpoint}")


def fixture() -> dict:
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


def test_frozen_case_count_future_information_and_no_answer_key() -> None:
    data = fixture()
    cases = validate_fixture(data)
    assert len(cases) == 2
    assert [c["id"] for c in cases] == ["MEASUREMENT", "STERILE"]
    first = cases[0]
    before = _host_prompt(
        first, [], first["turns"][0]["question"], first["turns"][0]["new_observation"]
    )
    for later in first["turns"][1:]:
        assert later["new_observation"] not in before
    assert "EERDERE VRAAG" not in before
    for case in cases:
        assert len(case["turns"]) == 4
        assert all("target_terms" not in turn for turn in case["turns"])
    assert MODEL == "gpt-5" and MAX_MODEL_CALLS == 24
    assert MAX_EMBEDDING_CALLS == 48 and MAX_ALL_TOKENS == 85000


@pytest.mark.parametrize("mutation", [
    "wrong_model", "missing_case", "duplicate_case",
    "future_at_birth", "too_few_turns", "answer_key",
])
def test_fixture_fails_closed_on_contaminated_or_invalid_design(mutation: str) -> None:
    data = deepcopy(fixture())
    if mutation == "wrong_model":
        data["model"] = "small-fixture-model"
    elif mutation == "missing_case":
        data["cases"].pop()
    elif mutation == "duplicate_case":
        data["cases"][1]["id"] = data["cases"][0]["id"]
    elif mutation == "future_at_birth":
        data["cases"][0]["turns"][0]["new_observation"] = "Future event"
    elif mutation == "too_few_turns":
        data["cases"][0]["turns"].pop()
    elif mutation == "answer_key":
        data["cases"][0]["target_terms"] = ["preferred answer"]
    else:
        raise AssertionError(mutation)
    with pytest.raises(ValueError):
        validate_fixture(data)


def test_live_product_pipeline_mock_transport_retains_weightless_seed_across_turns() -> None:
    p = NoNetworkProvider()
    data = run(fixture(), p)
    assert data["schema"] == OUTPUT_SCHEMA
    assert data["G0"] == "NOT_PASSED"
    assert data["independent_human_review_completed"] is False
    assert data["q1_probability_or_internal_absence_proven"] is False
    assert data["q2_later_investigability_proven"] is False
    assert data["confirmatory_trial"] is False
    assert len(data["cases"]) == 2
    assert p.model_calls == 20
    assert 0 < p.embedding_calls <= MAX_EMBEDDING_CALLS
    assert p.total_tokens < MAX_ALL_TOKENS

    positive, sterile = data["cases"]
    assert positive["selected_first_seed_id"] is not None
    assert positive["selected_first_seed_birth_turn"] == 0
    assert len(positive["ordinary_t0_samples_before_detection"]) == 2
    assert len(positive["turns"]) == 4
    assert positive["turns"][0]["first_seed_checkpoint"] is not None
    assert positive["turns"][0]["first_seed_checkpoint"][
        "raw_detector_item_to_seed_mapping_verified"
    ] is True
    for i in (1, 2, 3):
        c = positive["turns"][i]["followup_checkpoint"]
        assert c["turn"] == i
        assert c["seed_id"] == positive["selected_first_seed_id"]
        assert c["seed_state_after_turn"]["weight"] == 0
        assert c["seed_state_after_turn"]["evidence_count"] == 0
        assert c["product_answer_seed_influence_observed"] is False
        assert c["semantic_growth_assessed"] is False
    assert positive["turns"][0]["followup_checkpoint"] is None
    assert all(t["none_control_answer_identical"] for t in positive["turns"])
    assert sterile["selected_first_seed_id"] is None
    assert sterile["none_control_seed_count"] == 0
    assert all(t["none_control_answer_identical"] for t in sterile["turns"])
    assert "TEST_ONLY_NOT_REAL_KEY" not in json.dumps(data, ensure_ascii=False)
    assert len(data["provider_audit"]["events"]) >= 20


def test_provider_cap_and_token_validation_prevent_hidden_retries() -> None:
    p = NoNetworkProvider()
    p.model_calls = MAX_MODEL_CALLS
    with pytest.raises(RuntimeError, match="hard model-call cap"):
        p.generate(
            stage="test", case_id="MEASUREMENT",
            prompt="Testvraag met voldoende tekst", instructions=HOST_INSTRUCTIONS,
        )
    assert p._responses == 0

    q = NoNetworkProvider()
    q._consume(5)
    with pytest.raises(RuntimeError, match="token usage"):
        q._consume("missing")
    assert q.total_tokens == 5

    q._consume(MAX_ALL_TOKENS - 6)
    with pytest.raises(RuntimeError, match="hard combined"):
        q._consume(10)


def test_detector_parser_and_embedding_are_called_without_second_pipeline() -> None:
    p = NoNetworkProvider()
    first = fixture()["cases"][0]
    data = run({"schema": SCHEMA, "model": MODEL,
                "embedding_model": EMBEDDING_MODEL,
                "cases": [first, fixture()["cases"][1]]}, p)
    turn0 = data["cases"][0]["turns"][0]
    report = turn0["canonical_turn_report"]
    assert report["runtime_mode"] == "live"
    assert report["turn"] == 0
    assert report["detector_context_policy"] == "recent_clean_turns_v1"
    assert report["detector_audit"]["prompt_contract"]["prompt_id"] == "detector_current_pair"
    assert report["intake_diagnostics"]["lineage_schema"] == "candidate-intake-lineage-v1"
    assert turn0["detector_raw_output"].startswith("1.")
    assert turn0["first_seed_checkpoint"]["authority_at_birth"]["weight"] == 0
    assert data["provider_audit"]["model_calls"] == 20

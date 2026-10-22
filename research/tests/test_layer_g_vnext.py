"""Layer G vNext P1 mechanical checks. No neural/model-quality claims."""

from __future__ import annotations

from dataclasses import replace
import json
from pathlib import Path

import numpy as np
import pytest

from shadowseed_research.benchmark.layer_g_vnext import (
    Case, CaptureRequest, HFAnswerReplayReader, SyntheticReader,
    answer_token_positions, load_frozen_fixture, original_capture_request,
    run_synthetic_preflight, sha256_text, validate_activation_vectors,
    validate_cases, write_preflight,
)


FIXTURE = Path("research/fixtures/layer_g_vnext_synthetic.json")


def _cases() -> list[Case]:
    cases, _ = load_frozen_fixture(FIXTURE)
    return cases


def test_synthetic_preflight_keeps_claim_none_and_records_hashes(tmp_path: Path):
    report = write_preflight(FIXTURE, tmp_path / "preflight.json")
    assert report["status"] == "synthetic_preflight_only"
    assert report["research_claim"] == "none"
    assert report["capture_mode"] == "synthetic_hash_not_real_activations"
    assert len(report["cases"]) == len(_cases())
    assert all("label" not in c and "candidate" not in c for c in report["cases"])
    assert json.loads((tmp_path / "preflight.json").read_text()) == report


def test_candidate_and_label_changes_do_not_change_model_input_or_fake_vectors():
    case = _cases()[0]
    changed = replace(
        case, candidate_text="A totally different possible thought?",
        label="unsupported_alternative",
    )
    a = original_capture_request(case)
    b = original_capture_request(changed)
    assert a == b
    reader = SyntheticReader()
    assert np.array_equal(
        reader.capture(a)["synthetic.mlp.0"], reader.capture(b)["synthetic.mlp.0"]
    )


def test_unspoken_candidate_verbatim_in_original_material_rejected():
    original = _cases()[0]
    with pytest.raises(ValueError, match="appears verbatim"):
        original_capture_request(replace(
            original, original_answer=original.original_answer + " " + original.candidate_text
        ))


@pytest.mark.parametrize("marker", ["EVAL_CANDIDATE:", "GOLD_LABEL:", "<CANDIDATE_TEXT>"])
def test_injected_evaluation_metadata_is_rejected(marker: str):
    original = _cases()[1]
    with pytest.raises(ValueError, match="marker"):
        original_capture_request(replace(original, original_prompt=original.original_prompt + marker))


def test_capture_request_detects_mutated_stimulus_digest():
    request = original_capture_request(_cases()[0])
    with pytest.raises(ValueError, match="digest"):
        CaptureRequest(request.stimulus + " injected", request.answer_start,
                       request.answer_end, request.stimulus_sha256)


def test_duplicate_same_stimulus_cannot_create_contradictory_target():
    original = _cases()[0]
    with pytest.raises(ValueError, match="identical original context"):
        validate_cases([original, replace(original, case_id="new", label="already_expressed")]
                       + _cases()[1:])


@pytest.mark.parametrize("field", ["source_id", "topic_id"])
def test_no_shared_source_or_topic_across_folds(field: str):
    cases = _cases()
    changed = replace(cases[3], **{field: getattr(cases[0], field)})
    with pytest.raises(ValueError, match="leaks across splits"):
        validate_cases(cases[:3] + [changed] + cases[4:])


def test_split_and_label_schema_is_closed_and_nonempty():
    case = _cases()[0]
    for field, value in (("split", "random"), ("label", "proven_true"), ("language", "xx")):
        with pytest.raises(ValueError):
            Case.from_dict({**case.__dict__, field: value})
    with pytest.raises(ValueError, match="missing/extra"):
        Case.from_dict({**case.__dict__, "latent_truth": "yes"})


def test_original_answer_token_offsets_fail_closed_when_truncated():
    assert answer_token_positions([(0, 1), (1, 5), (5, 7)], 1, 7) == [1, 2]
    with pytest.raises(ValueError, match="fully cover"):
        answer_token_positions([(0, 1), (1, 3), (3, 5)], 1, 8)
    with pytest.raises(ValueError, match="absent"):
        answer_token_positions([(0, 2)], 4, 7)
    with pytest.raises(ValueError, match="bad answer"):
        answer_token_positions([(0, 1)], 2, 2)


def test_activation_shape_nan_and_layer_drift_fail_closed():
    expected = validate_activation_vectors({"model.layers.0.mlp.down_proj": np.ones(4)})
    with pytest.raises(ValueError, match="nonfinite"):
        validate_activation_vectors({"layer": np.array([0., np.nan])})
    with pytest.raises(ValueError, match="shapes changed"):
        validate_activation_vectors({"layer": np.ones(4)}, expected_shapes=expected)
    with pytest.raises(ValueError, match="feature shape"):
        validate_activation_vectors({"layer": np.ones((1, 4))})


def test_reader_rejects_unpinned_read_locations_and_slow_tokenizers():
    class Tokenizer:
        is_fast = False

    with pytest.raises(ValueError, match="tokenizer"):
        HFAnswerReplayReader(object(), Tokenizer(), layers=("model.layers.0.mlp.down_proj",))
    Tokenizer.is_fast = True
    with pytest.raises(ValueError, match="down-projection"):
        HFAnswerReplayReader(object(), Tokenizer(), layers=("model.layers.0.mlp",))


def test_fake_reader_records_no_seed_state_and_changes_with_input():
    case = _cases()[0]
    changed = replace(case, original_answer=case.original_answer + " independent update")
    reader = SyntheticReader()
    a = reader.capture(original_capture_request(case))
    b = reader.capture(original_capture_request(changed))
    assert not np.array_equal(a["synthetic.mlp.0"], b["synthetic.mlp.0"])
    assert all(isinstance(v, np.ndarray) for v in a.values())


def test_all_evaluation_cases_remain_independently_grouped():
    cases = _cases()
    assert {c.split for c in cases} == {"discovery", "validation", "test"}
    assert len({c.source_id for c in cases}) == len(cases)
    assert len({c.topic_id for c in cases}) == len(cases)
    output = run_synthetic_preflight(cases, sha256_text("fixture"))
    assert output["checks"]["source_and_topic_holdout_disjoint"]

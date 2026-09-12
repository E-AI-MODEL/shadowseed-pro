"""Public contract tests for the model-independent Shadowseed engine."""

from __future__ import annotations

import numpy as np
import pytest

from shadowseed import ENGINE_API_VERSION, PreparedTurn, ShadowseedEngine
from shadowseed.gate.signals import SignalDirection, SignalKind, ValidationSignal
from shadowseed.surfacing import CANDIDATE_CLOSE, CANDIDATE_OPEN


class StaticDetector:
    name = "static-detector"
    prompt_variant = "test"

    def __init__(self, candidate: str | None) -> None:
        self.candidate = candidate

    def detect_seeds(self, item, max_seeds=5):
        return [] if self.candidate is None else [self.candidate]


def _embedding(text: str) -> np.ndarray:
    low = text.lower()
    if "privacy" in low or "data" in low:
        return np.array([1.0, 0.0])
    return np.array([0.0, 1.0])


def _engine(candidate: str | None = None) -> ShadowseedEngine:
    return ShadowseedEngine(
        embedding_fn=_embedding,
        detector_backend=StaticDetector(candidate),
        recurrence_mode="pairwise",
    )


def test_real_detector_requires_semantic_embedding_or_explicit_override():
    with pytest.raises(ValueError, match="semantic embedding backend"):
        ShadowseedEngine(detector_backend=StaticDetector(None))

    engine = ShadowseedEngine(
        detector_backend=StaticDetector(None),
        allow_toy_embedder=True,
    )
    prepared = engine.prepare_turn("Fixture-only experiment")
    engine.observe_turn(prepared, "Visible answer")


def _verified_support(source_ref: str) -> ValidationSignal:
    return ValidationSignal(
        kind=SignalKind.HUMAN_FEEDBACK,
        direction=SignalDirection.SUPPORT,
        verified=True,
        independent=True,
        source_ref=source_ref,
        reason="checked outside the model output",
    )


def test_engine_splits_host_generation_from_ssl_observation():
    candidate = "Privacy as a missing decision boundary."
    engine = _engine(candidate)

    prepared = engine.prepare_turn("What should this data process consider?")
    assert isinstance(prepared, PreparedTurn)
    assert prepared.turn == 0
    assert prepared.surfaced_seeds == ()
    assert prepared.model_context == ""
    assert engine.has_pending_turn is True

    report = engine.observe_turn(prepared, "The host model's visible answer.")
    assert report["answer"] == "The host model's visible answer."
    assert report["prepared_turn_id"] == prepared.turn_id
    assert report["seeds_born_weightless"]
    assert engine.turn == 1
    assert engine.has_pending_turn is False

    seed = engine.inspect()["seeds"][0]
    assert seed["text"] == candidate
    assert seed["trace"] > 0
    assert seed["weight"] == 0.0
    assert seed["status"] != "PROMOTED"


def test_verified_seed_surfaces_as_bounded_model_context():
    candidate = "Privacy as a missing decision boundary."
    engine = _engine(candidate)
    first = engine.prepare_turn("What should this data process consider?")
    first_report = engine.observe_turn(first, "A first visible answer.")
    seed_id = first_report["seeds_born_weightless"][0]

    decisions = [
        engine.submit_evidence(seed_id, _verified_support(f"reviewer:{index}"))[
            "decision"
        ]
        for index in range(3)
    ]
    assert decisions == ["validated", "validated", "promoted"]

    prepared = engine.prepare_turn("Which privacy boundary applies to this data?")
    assert prepared.surfaced_seed_ids == (seed_id,)
    assert prepared.surfaced_seeds == (candidate,)
    assert CANDIDATE_OPEN in prepared.model_context
    assert CANDIDATE_CLOSE in prepared.model_context
    assert "untrusted quoted data" in prepared.model_context
    assert prepared.influence_decisions[0]["allowed"] is True

    report = engine.observe_turn(prepared, "A later visible answer.")
    assert report["surfaced_seed_ids"] == [seed_id]
    assert report["suppressed_self_attributed_candidates"] == [candidate]
    assert engine.audit() == 1


def test_prepared_turn_is_single_use_and_bound_to_one_engine():
    first_engine = _engine()
    second_engine = _engine()
    first = first_engine.prepare_turn("First question")
    second = second_engine.prepare_turn("Second question")

    with pytest.raises(RuntimeError, match="already awaiting"):
        first_engine.prepare_turn("Another question")
    with pytest.raises(RuntimeError, match="cannot export"):
        first_engine.export_state()
    with pytest.raises(ValueError, match="does not match"):
        first_engine.observe_turn(second, "Wrong engine answer")
    with pytest.raises(TypeError, match="answer must be a string"):
        first_engine.observe_turn(first, None)  # type: ignore[arg-type]

    first_engine.observe_turn(first, "Visible answer")
    with pytest.raises(RuntimeError, match="no prepared turn"):
        first_engine.observe_turn(first, "Replay")


def test_authority_cannot_change_during_a_pending_turn():
    engine = _engine("Privacy as a missing decision boundary.")
    first = engine.prepare_turn("What should this data process consider?")
    report = engine.observe_turn(first, "A visible answer.")
    seed_id = report["seeds_born_weightless"][0]
    pending = engine.prepare_turn("A follow-up question")

    with pytest.raises(RuntimeError, match="cannot change authority"):
        engine.submit_evidence(seed_id, _verified_support("reviewer:1"))
    with pytest.raises(RuntimeError, match="cannot change authority"):
        engine.submit_contradiction(
            seed_id,
            reason="The premise is false",
            source_ref="reviewer:2",
        )

    engine.observe_turn(pending, "A follow-up answer.")


def test_contradiction_is_attributable_and_blocks_later_influence():
    candidate = "Privacy as a missing decision boundary."
    engine = _engine(candidate)
    first = engine.prepare_turn("What should this data process consider?")
    seed_id = engine.observe_turn(first, "A visible answer.")[
        "seeds_born_weightless"
    ][0]
    for index in range(3):
        engine.submit_evidence(seed_id, _verified_support(f"reviewer:{index}"))

    result = engine.submit_contradiction(
        seed_id,
        reason="The cited policy was withdrawn",
        source_ref="policy-register:withdrawal-7",
    )
    assert result["decision"] == "contradicted"
    assert result["blocked_from_influence"] is True
    assert result["gate_event"]["signals"][0]["source_ref"] == (
        "policy-register:withdrawal-7"
    )

    prepared = engine.prepare_turn("Which privacy boundary applies to this data?")
    assert prepared.surfaced_seed_ids == ()
    engine.observe_turn(prepared, "Another visible answer.")


def test_engine_state_round_trip_keeps_shadow_but_not_a_model_provider():
    detector = StaticDetector("Privacy as a missing decision boundary.")
    engine = ShadowseedEngine(
        embedding_fn=_embedding,
        detector_backend=detector,
        recurrence_mode="pairwise",
    )
    prepared = engine.prepare_turn("What should this data process consider?")
    engine.observe_turn(prepared, "A visible answer.")
    state = engine.export_state()

    restored = ShadowseedEngine.from_state(
        state,
        embedding_fn=_embedding,
        detector_backend=StaticDetector(None),
    )
    assert restored.api_version == ENGINE_API_VERSION
    assert restored.turn == 1
    assert restored.inspect()["seeds"] == engine.inspect()["seeds"]

    next_turn = restored.prepare_turn("Continue")
    restored.observe_turn(next_turn, "A restored visible answer.")
    assert restored.turn == 2


@pytest.mark.parametrize("field", ["reason", "source_ref"])
def test_contradiction_requires_auditable_fields(field):
    engine = _engine("Privacy as a missing decision boundary.")
    prepared = engine.prepare_turn("Question")
    seed_id = engine.observe_turn(prepared, "Answer")["seeds_born_weightless"][0]
    values = {"reason": "Checked contradiction", "source_ref": "reviewer:1"}
    values[field] = " "

    with pytest.raises(ValueError, match=field):
        engine.submit_contradiction(seed_id, **values)

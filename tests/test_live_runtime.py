from __future__ import annotations

from dataclasses import replace

import numpy as np
import pytest

import shadowseed.chat as chatmod
from shadowseed.chat import ShadowChatSession
from shadowseed.gate.signals import (
    SignalDirection,
    SignalKind,
    ValidationSignal,
    recurrence_signal,
)
from shadowseed.manager import SeedStatus


class RecordingModel:
    name = "recording"

    def __init__(self, answer: str = "Visible answer.") -> None:
        self.answer = answer
        self.calls = []

    def generate(self, prompt, scenario, mode, seeds):
        self.calls.append((prompt, mode, list(seeds)))
        return self.answer


class ModeRecordingModel(RecordingModel):
    def generate(self, prompt, scenario, mode, seeds):
        self.calls.append((prompt, mode, list(seeds)))
        return "Baseline answer." if mode == "baseline" else "SSL answer."


class StaticDetector:
    name = "static"

    def __init__(self, seed: str | None) -> None:
        self.seed = seed

    def detect_seeds(self, item, max_seeds=5):
        return [] if self.seed is None else [self.seed]


def _emb_factory(backend, model_id=None, **kwargs):
    def embed(text: str) -> np.ndarray:
        low = text.lower()
        if "privacy" in low or "data" in low:
            return np.array([1.0, 0.0])
        return np.array([0.0, 1.0])
    return embed, 2


def _session(monkeypatch, *, detector_seed=None, answer="Visible answer.", **kwargs):
    model = RecordingModel(answer)
    monkeypatch.setattr(chatmod, "make_backend", lambda **kw: model)
    monkeypatch.setattr(chatmod, "make_detector_backend", lambda *a, **kw: StaticDetector(detector_seed))
    monkeypatch.setattr(chatmod, "make_embedding_fn", _emb_factory)
    session = ShadowChatSession(
        backend="openai",
        embedding_backend="openai",
        runtime_mode="live",
        recurrence_mode="pairwise",
        **kwargs,
    )
    return session, model


def test_live_turn_uses_one_generation_and_stores_visible_answer(monkeypatch):
    session, model = _session(monkeypatch, detector_seed=None, answer="What the user read.")
    report = session.turn("Question?")
    assert len(model.calls) == 1
    assert report["runtime_mode"] == "live"
    assert report["answer"] == "What the user read."
    assert report["baseline_answer"] is None
    assert session.history == [("Question?", "What the user read.")]


def test_session_api_defaults_to_live_runtime(monkeypatch):
    model = RecordingModel()
    monkeypatch.setattr(chatmod, "make_backend", lambda **kw: model)
    monkeypatch.setattr(chatmod, "make_detector_backend", lambda *a, **kw: StaticDetector(None))
    monkeypatch.setattr(chatmod, "make_embedding_fn", _emb_factory)
    session = ShadowChatSession(
        backend="openai",
        embedding_backend="openai",
        recurrence_mode="pairwise",
    )
    assert session.runtime_mode == "live"
    assert session.gate_policy_id == "evidence_backed"


def test_live_recurrence_alone_never_grants_authority(monkeypatch):
    session, _model = _session(
        monkeypatch,
        detector_seed="Privacy as a missing decision boundary.",
        answer="Answer about data.",
    )
    for index in range(6):
        session.turn(f"Question about data {index}?")
    seed = next(iter(session.manager.seeds.values()))
    assert seed.occurrence_count >= session.manager.config.min_occurrences_for_gate
    assert seed.weight == 0.0
    assert seed.status is not SeedStatus.PROMOTED
    assert session.gate_policy_id == "evidence_backed"
    assert session.manager.gate_events
    assert all(event.decision.value == "blocked" for event in session.manager.gate_events)


def test_live_uses_configured_recurrence_threshold(monkeypatch):
    session, _model = _session(
        monkeypatch,
        detector_seed="Privacy as a missing decision boundary.",
        answer="Answer about data.",
    )
    session.manager.config = replace(
        session.manager.config,
        min_occurrences_for_gate=5,
    )

    for index in range(4):
        session.turn(f"Question about data {index}?")
    assert session.manager.gate_events == []

    session.turn("Question about data 4?")
    assert len(session.manager.gate_events) == 1
    assert "threshold=5" in session.manager.gate_events[0].signals[0].reason


def test_live_submits_gate_event_only_for_changed_recurrence(monkeypatch):
    session, _model = _session(
        monkeypatch,
        detector_seed="Privacy as a missing decision boundary.",
        answer="Answer about data.",
    )
    for index in range(session.manager.config.min_occurrences_for_gate):
        session.turn(f"Question about data {index}?")
    before = len(session.manager.gate_events)
    assert before == 1

    session.detector.seed = None
    session.turn("A turn without a detected candidate.")
    assert len(session.manager.gate_events) == before


def test_live_suppresses_self_attributed_recurrence(monkeypatch):
    seed_text = "Privacy as a missing decision boundary."
    session, _model = _session(
        monkeypatch,
        detector_seed=seed_text,
        answer="Privacy remains important for this data decision.",
    )
    seed_id = session.manager.add_or_update_seed(seed_text)
    session.born_turn[seed_id] = -1
    for index in range(3):
        session.manager.submit_signals(
            seed_id,
            [ValidationSignal(kind=SignalKind.SSOT, verified=True, source_ref=f"source:{index}")],
            policy_id="evidence_backed",
        )
    seed = session.manager.seeds[seed_id]
    assert seed.status is SeedStatus.PROMOTED
    before = seed.occurrence_count
    report = session.turn("What about privacy and data?")
    assert seed_id in report["surfaced_seed_ids"]
    assert report["suppressed_self_attributed_candidates"] == [seed_text]
    assert session.manager.seeds[seed_id].occurrence_count == before


def test_live_suppresses_semantically_distinct_candidate_after_ssl_influence(monkeypatch):
    seed_text = "Privacy as a missing decision boundary."
    derived_text = "A downstream fairness implication."
    session, _model = _session(
        monkeypatch,
        detector_seed=derived_text,
        answer="The surfaced privacy concern implies a separate fairness risk.",
    )
    seed_id = session.manager.add_or_update_seed(seed_text)
    derived_id = session.manager.add_or_update_seed(derived_text)
    session.born_turn[seed_id] = -1
    for index in range(3):
        session.submit_evidence(
            seed_id,
            ValidationSignal(
                kind=SignalKind.SSOT,
                verified=True,
                source_ref=f"source:{index}",
            ),
        )

    before = session.manager.seeds[derived_id].occurrence_count
    report = session.turn("What about privacy and data?")
    assert seed_id in report["surfaced_seed_ids"]
    assert report["suppressed_self_attributed_candidates"] == [derived_text]
    assert session.manager.seeds[derived_id].occurrence_count == before


def test_live_explicit_evidence_route_promotes_and_enables_later_use(monkeypatch):
    session, _model = _session(monkeypatch, detector_seed=None, answer="Visible answer.")
    seed_id = session.manager.add_or_update_seed("Privacy as a missing decision boundary.")
    session.born_turn[seed_id] = -1

    decisions = []
    for index in range(3):
        result = session.submit_evidence(
            seed_id,
            ValidationSignal(
                kind=SignalKind.HUMAN_FEEDBACK,
                direction=SignalDirection.SUPPORT,
                verified=True,
                independent=True,
                source_ref=f"reviewer:{index}",
                reason="verified operator support",
            ),
        )
        decisions.append(result["decision"])

    seed = session.manager.seeds[seed_id]
    assert decisions == ["validated", "validated", "promoted"]
    assert seed.evidence_count == 3
    assert seed.status is SeedStatus.PROMOTED
    report = session.turn("What about privacy and data?")
    assert seed_id in report["surfaced_seed_ids"]
    assert any(record.allowed for record in session.influence_records)


@pytest.mark.parametrize(
    "signal, message",
    [
        (recurrence_signal(4, threshold=3), "external evidence"),
        (
            ValidationSignal(kind=SignalKind.SSOT, verified=False, source_ref="ssot:1"),
            "explicitly verified",
        ),
        (
            ValidationSignal(kind=SignalKind.SSOT, verified=True),
            "source_ref",
        ),
        (
            ValidationSignal(
                kind=SignalKind.SSOT,
                direction=SignalDirection.OPPOSE,
                verified=True,
                source_ref="ssot:2",
            ),
            "supporting signal",
        ),
        (
            ValidationSignal(
                kind=SignalKind.PROBE,
                verified=True,
                source_ref="probe:1",
            ),
            "external evidence",
        ),
    ],
)
def test_live_evidence_route_rejects_untrusted_inputs(monkeypatch, signal, message):
    session, _model = _session(monkeypatch, detector_seed=None)
    seed_id = session.manager.add_or_update_seed("Privacy as a missing decision boundary.")
    with pytest.raises(ValueError, match=message):
        session.submit_evidence(seed_id, signal)
    assert session.manager.seeds[seed_id].weight == 0.0
    assert session.manager.gate_events == []


def test_live_evidence_route_rejects_unknown_seed(monkeypatch):
    session, _model = _session(monkeypatch, detector_seed=None)
    signal = ValidationSignal(
        kind=SignalKind.SSOT,
        verified=True,
        source_ref="ssot:unknown",
    )

    with pytest.raises(KeyError, match="Unknown seed id"):
        session.submit_evidence("missing-seed", signal)

    assert session.manager.gate_events == []


def test_live_evidence_route_deduplicates_same_source(monkeypatch):
    session, _model = _session(monkeypatch, detector_seed=None)
    seed_id = session.manager.add_or_update_seed("Privacy as a missing decision boundary.")
    signal = ValidationSignal(
        kind=SignalKind.SSOT,
        verified=True,
        source_ref="ssot:stable-source",
    )

    first = session.submit_evidence(seed_id, signal)
    second = session.submit_evidence(seed_id, signal)

    assert first["decision"] == "validated"
    assert second["decision"] == "blocked"
    assert session.manager.seeds[seed_id].weight == pytest.approx(0.2)
    assert session.manager.seeds[seed_id].evidence_count == 1


def test_live_non_fixture_rejects_lexical_embedder(monkeypatch):
    monkeypatch.setattr(chatmod, "make_backend", lambda **kw: RecordingModel())
    monkeypatch.setattr(chatmod, "make_detector_backend", lambda *a, **kw: StaticDetector(None))
    with pytest.raises(ValueError, match="requires a semantic embedding backend"):
        ShadowChatSession(backend="openai", embedding_backend="lexical", runtime_mode="live")


def test_evaluation_mode_keeps_baseline_history_isolation(monkeypatch):
    model = ModeRecordingModel()
    monkeypatch.setattr(chatmod, "make_backend", lambda **kw: model)
    monkeypatch.setattr(chatmod, "make_detector_backend", lambda *a, **kw: StaticDetector(None))
    monkeypatch.setattr(chatmod, "make_embedding_fn", _emb_factory)
    session = ShadowChatSession(
        backend="openai",
        embedding_backend="openai",
        runtime_mode="evaluation",
        recurrence_mode="pairwise",
    )
    seed_id = session.manager.add_or_update_seed("Privacy as a missing decision boundary.")
    session.born_turn[seed_id] = -1
    for index in range(3):
        session.manager.submit_signals(
            seed_id,
            [ValidationSignal(kind=SignalKind.SSOT, verified=True, source_ref=f"source:{index}")],
            policy_id="evidence_backed",
        )

    report = session.turn("What about privacy and data?")
    assert report["runtime_mode"] == "evaluation"
    assert [mode for _prompt, mode, _seeds in model.calls] == ["baseline", "ssl"]
    assert report["answer"] == "SSL answer."
    assert report["baseline_answer"] == "Baseline answer."
    assert session.history == [("What about privacy and data?", "Baseline answer.")]


def test_evaluation_mode_applies_selected_gate_policy(monkeypatch):
    session, _model = _session(
        monkeypatch,
        detector_seed="Privacy as a missing decision boundary.",
        answer="Answer about data.",
    )
    session.runtime_mode = "evaluation"
    session.gate_policy_id = "evidence_backed"

    for index in range(5):
        session.turn(f"Question about data {index}?")

    seed = next(iter(session.manager.seeds.values()))
    assert seed.weight == 0.0
    assert seed.status is not SeedStatus.PROMOTED
    assert session.manager.gate_events
    assert all(event.policy_id == "evidence_backed" for event in session.manager.gate_events)


def test_live_state_roundtrip_preserves_mode_policy_and_visible_history(monkeypatch):
    session, _model = _session(
        monkeypatch,
        detector_seed=None,
        answer="First visible answer.",
    )
    session.turn("First question?")

    restored = ShadowChatSession.from_state(session.to_state())
    assert restored.runtime_mode == "live"
    assert restored.gate_policy_id == "evidence_backed"
    assert restored.history == [("First question?", "First visible answer.")]

    restored.model.answer = "Second visible answer."
    restored.turn("Second question?")
    assert restored.history[-1] == ("Second question?", "Second visible answer.")


def test_legacy_version_one_state_preserves_evaluation_and_decay(monkeypatch):
    session, _model = _session(monkeypatch, detector_seed=None)
    state = session.to_state()
    state["schema_version"] = 1
    state["session_config"]["embedding_backend"] = "lexical"
    state["session_config"].pop("runtime_mode")
    state["session_config"].pop("gate_policy_id")
    state["session_config"].pop("allow_toy_embedder")
    state["manager"]["config"]["half_life_turns"] = 3.0

    restored = ShadowChatSession.from_state(state)

    assert restored.runtime_mode == "evaluation"
    assert restored.gate_policy_id == "exploratory"
    assert restored.manager.half_life_turns == pytest.approx(3.0 * np.log(2.0))
    seed_id = restored.manager.add_or_update_seed("Privacy as a lifecycle test case.")
    restored.manager.decay_traces(turns_passed=1)
    assert restored.manager.seeds[seed_id].trace == pytest.approx(2.0 * np.exp(-1.0 / 3.0))


def test_later_version_one_state_keeps_true_half_life_and_runtime(monkeypatch):
    session, _model = _session(monkeypatch, detector_seed=None)
    state = session.to_state()
    state["schema_version"] = 1
    state["manager"]["config"]["half_life_turns"] = 3.0

    restored = ShadowChatSession.from_state(state)

    assert restored.runtime_mode == "live"
    assert restored.gate_policy_id == "evidence_backed"
    assert restored.manager.half_life_turns == pytest.approx(3.0)
    seed_id = restored.manager.add_or_update_seed("Privacy as a lifecycle test case.")
    restored.manager.decay_traces(turns_passed=3)
    assert restored.manager.seeds[seed_id].trace == pytest.approx(1.0)


def test_half_life_turns_is_a_real_half_life(monkeypatch):
    session, _model = _session(monkeypatch, detector_seed=None)
    seed_id = session.manager.add_or_update_seed("Privacy as a lifecycle test case.")
    start = session.manager.seeds[seed_id].trace
    session.manager.decay_traces(turns_passed=session.manager.half_life_turns)
    assert session.manager.seeds[seed_id].trace == pytest.approx(start / 2.0)

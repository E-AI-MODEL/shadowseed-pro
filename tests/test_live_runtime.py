from __future__ import annotations

import numpy as np
import pytest

import shadowseed.chat as chatmod
from shadowseed.chat import ShadowChatSession
from shadowseed.gate.signals import SignalKind, ValidationSignal
from shadowseed.manager import SeedStatus


class RecordingModel:
    name = "recording"

    def __init__(self, answer: str = "Visible answer.") -> None:
        self.answer = answer
        self.calls = []

    def generate(self, prompt, scenario, mode, seeds):
        self.calls.append((prompt, mode, list(seeds)))
        return self.answer


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


def test_live_non_fixture_rejects_lexical_embedder(monkeypatch):
    monkeypatch.setattr(chatmod, "make_backend", lambda **kw: RecordingModel())
    monkeypatch.setattr(chatmod, "make_detector_backend", lambda *a, **kw: StaticDetector(None))
    with pytest.raises(ValueError, match="requires a semantic embedding backend"):
        ShadowChatSession(backend="openai", embedding_backend="lexical", runtime_mode="live")


def test_evaluation_mode_remains_available(monkeypatch):
    session, model = _session(monkeypatch, detector_seed=None)
    session.runtime_mode = "evaluation"
    session.gate_policy_id = "exploratory"
    report = session.turn("Question?")
    assert report["runtime_mode"] == "evaluation"
    assert len(model.calls) == 1


def test_half_life_turns_is_a_real_half_life(monkeypatch):
    session, _model = _session(monkeypatch, detector_seed=None)
    seed_id = session.manager.add_or_update_seed("Privacy as a lifecycle test case.")
    start = session.manager.seeds[seed_id].trace
    session.manager.decay_traces(turns_passed=session.manager.half_life_turns)
    assert session.manager.seeds[seed_id].trace == pytest.approx(start / 2.0)

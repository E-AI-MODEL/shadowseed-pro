from __future__ import annotations

import numpy as np

import shadowseed.chat as chatmod
from shadowseed.chat import ShadowChatSession
from shadowseed.gate.signals import SignalKind, ValidationSignal
from shadowseed.manager import SeedStatus


class RecordingModel:
    name = "recording"

    def __init__(self, answer: str = "Visible answer.") -> None:
        self.answer = answer

    def generate(self, prompt, scenario, mode, seeds):
        return self.answer


class StaticDetector:
    name = "static"
    prompt_variant = "generative"

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


def _session(monkeypatch, *, detector_seed: str | None, answer: str) -> ShadowChatSession:
    model = RecordingModel(answer)
    detector = StaticDetector(detector_seed)
    monkeypatch.setattr(chatmod, "make_backend", lambda **kw: model)
    monkeypatch.setattr(chatmod, "make_detector_backend", lambda *a, **kw: detector)
    monkeypatch.setattr(chatmod, "make_embedding_fn", _emb_factory)
    return ShadowChatSession(
        backend="openai",
        embedding_backend="openai",
        runtime_mode="live",
        recurrence_mode="pairwise",
    )


def _promote(session: ShadowChatSession, seed_id: str) -> None:
    for index in range(3):
        session.submit_evidence(
            seed_id,
            ValidationSignal(
                kind=SignalKind.SSOT,
                verified=True,
                source_ref=f"source:{index}",
            ),
        )
    assert session.manager.seeds[seed_id].status is SeedStatus.PROMOTED


def test_live_contaminated_candidate_is_first_class_observation_without_recurrence(monkeypatch):
    candidate = "A downstream fairness implication."
    session = _session(
        monkeypatch,
        detector_seed=candidate,
        answer="The surfaced privacy concern implies a separate fairness risk.",
    )
    seed_id = session.manager.add_or_update_seed("Privacy as a missing decision boundary.")
    session.born_turn[seed_id] = -1
    _promote(session, seed_id)

    before_seed_state = session.manager.seeds[seed_id].to_dict()
    report = session.turn("What about privacy and data?")

    assert report["suppressed_self_attributed_candidates"] == [candidate]
    assert len(report["candidate_observations"]) == 1
    observation = report["candidate_observations"][0]
    assert observation["raw_text"] == candidate
    assert observation["ssl_exposed"] is True
    assert observation["recurrence_eligible"] is False
    assert observation["surfaced_seed_ids"] == [seed_id]
    assert session.manager.seeds[seed_id].occurrence_count == before_seed_state["occurrence_count"]
    assert session.manager.seeds[seed_id].weight == before_seed_state["weight"]
    assert session.manager.seeds[seed_id].evidence_count == before_seed_state["evidence_count"]


def test_live_later_clean_match_links_without_mutating_contaminated_record(monkeypatch):
    candidate = "Privacy needs a retention boundary."
    session = _session(
        monkeypatch,
        detector_seed=candidate,
        answer="Visible privacy answer.",
    )
    seed_id = session.manager.add_or_update_seed("Privacy as a missing decision boundary.")
    session.born_turn[seed_id] = -1
    _promote(session, seed_id)

    contaminated_report = session.turn("What about privacy and data?")
    contaminated = dict(contaminated_report["candidate_observations"][0])

    session.manager.falsify_seed(seed_id, reason="test removal of later surfacing")
    clean_report = session.turn("A later independent question?")

    assert clean_report["candidate_observations"][0]["recurrence_eligible"] is True
    assert session.observation_ledger.observations[0].to_dict() == contaminated
    assert len(session.observation_ledger.links) == 1
    assert session.observation_ledger.links[0].contaminated_observation_id == contaminated["observation_id"]


def test_observation_ledger_roundtrips_with_session_state(monkeypatch):
    session = _session(
        monkeypatch,
        detector_seed="A clean candidate.",
        answer="Visible answer.",
    )
    session.turn("Question?")
    state = session.to_state()

    restored = ShadowChatSession.from_state(state)

    assert restored.observation_ledger.to_dict() == session.observation_ledger.to_dict()


def test_older_state_projects_suppressed_candidates_without_rewriting_turn_reports(monkeypatch):
    session = _session(monkeypatch, detector_seed=None, answer="Visible answer.")
    state = session.to_state()
    state.pop("candidate_observation_ledger", None)
    state["turn_reports"] = [
        {
            "turn": 3,
            "surfaced_seed_ids": ["legacy-seed"],
            "suppressed_self_attributed_candidates": ["Legacy deferred candidate."],
        }
    ]
    original_reports = [dict(item) for item in state["turn_reports"]]

    restored = ShadowChatSession.from_state(state)

    assert state["turn_reports"] == original_reports
    assert len(restored.observation_ledger.observations) == 1
    observation = restored.observation_ledger.observations[0]
    assert observation.legacy_projection is True
    assert observation.recurrence_eligible is False

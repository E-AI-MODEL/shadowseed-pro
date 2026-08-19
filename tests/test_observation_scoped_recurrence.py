from __future__ import annotations

import math
from dataclasses import replace

import numpy as np

from shadowseed.chat import ShadowChatSession
from shadowseed.core_config import SSLCoreConfig
from shadowseed.recurrence_clustering import RecurrenceClusterer


def test_cluster_membership_and_recurrence_are_separate_with_observation_refs() -> None:
    clusterer = RecurrenceClusterer(threshold=0.6)
    a = np.asarray([1.0, 0.0, 0.0])
    b = np.asarray([0.9, 0.1, 0.0])
    c = np.asarray([0.85, 0.15, 0.0])

    cluster_id = clusterer.add("A", a, observation_ref="turn:0")
    assert clusterer.add("B", b, observation_ref="turn:0") == cluster_id
    assert clusterer.add("C", c, observation_ref="turn:0") == cluster_id

    assert clusterer.centroid_counts[cluster_id] == 3
    assert len(clusterer.members[cluster_id]) == 3
    assert clusterer.recurrence(cluster_id) == 1
    assert clusterer.seen_observation_refs[cluster_id] == {"turn:0"}

    # A deduped member from the same detector observation cannot self-recur.
    assert clusterer.bump(cluster_id, observation_ref="turn:0") == 1

    # A later independent observation contributes exactly one new credit even
    # when several paraphrases are observed in that later detector call.
    assert clusterer.add("D", a, observation_ref="turn:1") == cluster_id
    assert clusterer.add("E", b, observation_ref="turn:1") == cluster_id
    assert clusterer.bump(cluster_id, observation_ref="turn:1") == 2
    assert clusterer.recurrence(cluster_id) == 2
    assert clusterer.seen_observation_refs[cluster_id] == {"turn:0", "turn:1"}


def test_legacy_cluster_calls_without_observation_ref_keep_member_count_semantics() -> None:
    clusterer = RecurrenceClusterer(threshold=0.6)
    cluster_id = clusterer.add("A", np.asarray([1.0, 0.0]))
    assert clusterer.add("B", np.asarray([0.9, 0.1])) == cluster_id
    assert clusterer.bump(cluster_id) == 3

    assert clusterer.recurrence(cluster_id) == 3
    assert clusterer.seen_observation_refs[cluster_id] == set()


def test_empty_observation_ref_is_rejected() -> None:
    clusterer = RecurrenceClusterer()
    try:
        clusterer.add("A", np.asarray([1.0, 0.0]), observation_ref="  ")
    except ValueError as exc:
        assert "observation_ref" in str(exc)
    else:  # pragma: no cover - assertion guard
        raise AssertionError("empty observation_ref should fail")


class _Model:
    name = "observation-test-model"

    def generate(self, prompt, scenario, mode, ssl_seeds):
        return "A stable answer used for recurrence testing."


class _Detector:
    name = "observation-test-detector"

    batches = (
        (
            "Privacy as a constraint on personalization.",
            "Consent as a constraint on personalization.",
            "Transparency as a constraint on personalization.",
        ),
        (
            "Agency as a constraint on personalization.",
            "Fairness as a constraint on personalization.",
            "Security as a constraint on personalization.",
        ),
    )

    def __init__(self) -> None:
        self.index = 0

    def detect_seeds(self, item, max_seeds=5):
        batch = self.batches[min(self.index, len(self.batches) - 1)]
        self.index += 1
        return list(batch[:max_seeds])


def _embedding(text: str) -> np.ndarray:
    keywords = ("privacy", "consent", "transparency", "agency", "fairness", "security")
    a, b = math.sqrt(7.0), math.sqrt(3.0)
    vector = np.zeros(len(keywords) + 2, dtype=float)
    lowered = text.lower()
    for index, keyword in enumerate(keywords):
        if keyword in lowered:
            vector[0] = a
            vector[index + 1] = b
            return vector / np.linalg.norm(vector)
    vector[-1] = 1.0
    return vector


def _session(*, runtime_mode: str = "live") -> ShadowChatSession:
    return ShadowChatSession(
        backend="fixture",
        runtime_mode=runtime_mode,
        recurrence_mode="cluster",
        cluster_threshold=0.6,
        model_backend=_Model(),
        detector_backend=_Detector(),
        embedding_fn=_embedding,
        core_config=replace(
            SSLCoreConfig(),
            min_occurrences_for_gate=2,
            promotion_threshold=0.2,
        ),
    )


def _representative(session: ShadowChatSession):
    assert session.cluster_rep
    representative_id = session.cluster_rep[min(session.cluster_rep)]
    return session.manager.seeds[representative_id]


def test_canonical_chat_counts_one_semantic_recurrence_per_turn() -> None:
    session = _session(runtime_mode="evaluation")

    first = session.turn("First observation")
    representative = _representative(session)
    assert len(session.manager.seeds) == 3
    assert representative.occurrence_count == 1
    assert first["promoted_this_turn"] == []

    second = session.turn("Second independent observation")
    representative = _representative(session)
    assert len(session.manager.seeds) == 6
    assert representative.occurrence_count == 2
    assert representative.id in second["promoted_this_turn"]


def test_cluster_observation_refs_survive_session_save_restore() -> None:
    session = _session(runtime_mode="live")
    session.turn("First observation")
    session.turn("Second independent observation")

    state = session.to_state()
    cluster_state = state["cluster_state"]
    assert cluster_state is not None
    assert cluster_state["seen_observation_refs"] == [["turn:0", "turn:1"]]

    restored = ShadowChatSession.from_state(state)
    assert restored.clusterer is not None
    assert restored.clusterer.seen_observation_refs == [{"turn:0", "turn:1"}]
    assert restored.clusterer.recurrence(0) == 2

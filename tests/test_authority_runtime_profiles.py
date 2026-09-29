from __future__ import annotations

import numpy as np

from shadowseed.chat import ShadowChatSession
from shadowseed.manager import SeedStatus


def _feed_recurrence(session: ShadowChatSession, *, count: int = 6) -> list[dict]:
    reports = []
    for index in range(count):
        reports.append(
            session.observe_source_text(
                "Alpha provides a recurring explanatory perspective.",
                context_ref=f"source:authority-test:instance:{index:05d}:chunk:00000",
            )
        )
    return reports


def _alpha_seed(session: ShadowChatSession):
    return next(seed for seed in session.manager.seeds.values() if "Alpha" in seed.text)


def test_controlled_runtime_preserves_evidence_backed_authority() -> None:
    session = ShadowChatSession(
        backend="fixture",
        runtime_mode="live",
        embedding_backend="lexical",
        authority_profile_id="strict",
    )

    reports = _feed_recurrence(session)
    seed = _alpha_seed(session)

    assert session.gate_policy_id == "evidence_backed"
    assert seed.weight == 0.0
    assert seed.status is not SeedStatus.PROMOTED
    assert seed.evidence_count == 0
    assert all(report["authority_review_seed_ids"] == [] for report in reports)
    assert any(
        event.policy_id == "evidence_backed" and event.decision.value == "blocked"
        for event in session.manager.gate_events
        if event.seed_id == seed.id
    )


def test_assisted_runtime_flags_mature_recurrence_for_human_review() -> None:
    session = ShadowChatSession(
        backend="fixture",
        runtime_mode="live",
        embedding_backend="lexical",
        authority_profile_id="assisted",
    )

    reports = _feed_recurrence(session)
    seed = _alpha_seed(session)

    assert session.gate_policy_id == "evidence_backed"
    assert seed.weight == 0.0
    assert seed.status is not SeedStatus.PROMOTED
    assert any(seed.id in report["authority_review_seed_ids"] for report in reports)


def test_autonomous_runtime_promotes_recurrence_through_existing_gate() -> None:
    session = ShadowChatSession(
        backend="fixture",
        runtime_mode="live",
        embedding_backend="lexical",
        authority_profile_id="autonomous",
        surface_threshold=0.0,
        early_turn_margin=0.0,
    )

    reports = _feed_recurrence(session)
    seed = _alpha_seed(session)

    assert session.gate_policy_id == "exploratory"
    assert seed.status is SeedStatus.PROMOTED
    assert seed.weight >= session.manager.promotion_threshold
    assert seed.evidence_count == 0
    assert any(seed.id in report["promoted_this_observation"] for report in reports)
    assert any(
        event.policy_id == "exploratory" and event.decision.value == "promoted"
        for event in session.manager.gate_events
        if event.seed_id == seed.id
    )

    prepared = session.prepare_turn("Alpha perspective")
    try:
        assert seed.id in prepared.surfaced_seed_ids
    finally:
        session.abort_turn(prepared)


def test_autonomous_explicit_evidence_backed_override_stays_strict() -> None:
    session = ShadowChatSession(
        backend="fixture",
        runtime_mode="live",
        embedding_backend="lexical",
        authority_profile_id="autonomous",
        gate_policy_id="evidence_backed",
    )

    _feed_recurrence(session)
    seed = _alpha_seed(session)

    assert session.gate_policy_id == "evidence_backed"
    assert seed.weight == 0.0
    assert seed.status is not SeedStatus.PROMOTED


def test_open_runtime_exposes_unreviewed_system_evidence_capability_without_faking_it() -> None:
    session = ShadowChatSession(
        backend="fixture",
        runtime_mode="live",
        embedding_backend="lexical",
        authority_profile_id="open",
    )

    assert session.authority_runtime.allow_unreviewed_system_evidence is True
    assert session.gate_policy_id == "exploratory"

    _feed_recurrence(session)
    seed = _alpha_seed(session)
    assert seed.status is SeedStatus.PROMOTED
    assert seed.evidence_count == 0



class _NearDuplicateDetector:
    name = "near-duplicate-test"
    prompt_variant = "test"

    def detect_seeds(self, _payload, *, max_seeds=5):
        return [
            "Alpha identifies a missing explanatory boundary.",
            "Alpha identifies an absent explanatory boundary.",
            "Alpha identifies an omitted explanatory boundary.",
        ][:max_seeds]


def test_one_observation_cannot_self_promote_via_near_duplicate_candidates() -> None:
    session = ShadowChatSession(
        backend="fixture",
        runtime_mode="live",
        authority_profile_id="autonomous",
        embedding_backend="lexical",
        detector_backend=_NearDuplicateDetector(),
        embedding_fn=lambda _text: np.asarray([1.0, 0.0], dtype=float),
    )

    first = session.observe_source_text(
        "One source observation.",
        context_ref="source:test:instance:first:chunk:00000",
    )
    seed = next(iter(session.manager.seeds.values()))

    assert seed.occurrence_count == 1
    assert seed.status is not SeedStatus.PROMOTED
    assert first["promoted_this_observation"] == []

    session.observe_source_text(
        "Second independent observation.",
        context_ref="source:test:instance:second:chunk:00000",
    )
    assert seed.occurrence_count == 2
    assert seed.status is not SeedStatus.PROMOTED

    third = session.observe_source_text(
        "Third independent observation.",
        context_ref="source:test:instance:third:chunk:00000",
    )
    assert seed.occurrence_count == 3
    assert seed.status is SeedStatus.ACTIVE
    assert seed.weight == 0.2
    assert third["promoted_this_observation"] == []

    fourth = session.observe_source_text(
        "Fourth independent observation.",
        context_ref="source:test:instance:fourth:chunk:00000",
    )
    assert seed.occurrence_count == 4
    assert seed.status is SeedStatus.ACTIVE
    assert seed.weight == 0.4
    assert fourth["promoted_this_observation"] == []

    fifth = session.observe_source_text(
        "Fifth independent observation.",
        context_ref="source:test:instance:fifth:chunk:00000",
    )
    assert seed.occurrence_count == 5
    assert seed.status is SeedStatus.PROMOTED
    assert seed.id in fifth["promoted_this_observation"]



def test_source_chunk_overlap_counts_once_per_source_instance() -> None:
    session = ShadowChatSession(
        backend="fixture",
        runtime_mode="live",
        authority_profile_id="autonomous",
        embedding_backend="lexical",
        detector_backend=_NearDuplicateDetector(),
        embedding_fn=lambda _text: np.asarray([1.0, 0.0], dtype=float),
    )

    session.observe_source_text(
        "Boundary occurrence at the end of a chunk.",
        context_ref="source:overlap.md:instance:one:chunk:00000",
    )
    representative = next(iter(session.manager.seeds.values()))
    assert representative.occurrence_count == 1

    session.observe_source_text(
        "The same physical boundary occurrence repeated by overlap.",
        context_ref="source:overlap.md:instance:one:chunk:00001",
    )
    assert representative.occurrence_count == 1
    assert representative.status is not SeedStatus.PROMOTED

    session.observe_source_text(
        "An independent source occurrence.",
        context_ref="source:overlap.md:instance:two:chunk:00000",
    )
    assert representative.occurrence_count == 2


class _ClusterPairDetector:
    name = "cluster-pair-test"
    prompt_variant = "test"

    def detect_seeds(self, _payload, *, max_seeds=5):
        return [
            "Alpha primary boundary matters.",
            "Beta related boundary matters.",
        ][:max_seeds]


def _cluster_pair_embedding(text: str) -> np.ndarray:
    if text.startswith("Alpha"):
        return np.asarray([1.0, 0.0], dtype=float)
    return np.asarray([0.7, 0.714142842854285], dtype=float)


def test_assisted_review_excludes_cluster_nonrepresentatives() -> None:
    session = ShadowChatSession(
        backend="fixture",
        runtime_mode="live",
        authority_profile_id="assisted",
        embedding_backend="lexical",
        detector_backend=_ClusterPairDetector(),
        embedding_fn=_cluster_pair_embedding,
    )

    for index in range(3):
        session.observe_source_text(
            "Independent source observation.",
            context_ref=f"source:cluster-test:instance:{index}:chunk:00000",
        )

    assert len(session.manager.seeds) == 2
    representative_id = next(iter(session.cluster_rep.values()))
    nonrepresentative_id = next(
        seed_id for seed_id in session.manager.seeds if seed_id != representative_id
    )
    assert session.manager.seeds[nonrepresentative_id].occurrence_count >= 3
    assert session._seed_review_required(representative_id) is True
    assert session._seed_review_required(nonrepresentative_id) is False

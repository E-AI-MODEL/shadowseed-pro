from __future__ import annotations

import numpy as np

from shadowseed.chat import ShadowChatSession
from shadowseed.core_config import SSLCoreConfig
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



def test_near_duplicate_batch_writes_only_real_recurrence_audit_events() -> None:
    session = ShadowChatSession(
        backend="fixture",
        runtime_mode="live",
        authority_profile_id="autonomous",
        embedding_backend="lexical",
        detector_backend=_NearDuplicateDetector(),
        embedding_fn=lambda _text: np.asarray([1.0, 0.0], dtype=float),
    )

    session.observe_source_text(
        "First independent observation.",
        context_ref="source:audit-test:instance:first:chunk:00000",
    )
    seed = next(iter(session.manager.seeds.values()))
    assert seed.occurrence_count == 1
    assert [
        event
        for event in session.manager.event_log
        if event.seed_id == seed.id and event.event_type == "deduplicated"
    ] == []

    session.observe_source_text(
        "Second independent observation.",
        context_ref="source:audit-test:instance:second:chunk:00000",
    )
    recurrence_events = [
        event
        for event in session.manager.event_log
        if event.seed_id == seed.id and event.event_type == "deduplicated"
    ]

    assert seed.occurrence_count == 2
    assert len(recurrence_events) == 1
    assert recurrence_events[0].detail["occurrence_count"] == 2


def test_expired_cluster_representative_is_replaced_by_live_redetection() -> None:
    session = ShadowChatSession(
        backend="fixture",
        runtime_mode="live",
        authority_profile_id="autonomous",
        embedding_backend="lexical",
        detector_backend=_NearDuplicateDetector(),
        embedding_fn=lambda _text: np.asarray([1.0, 0.0], dtype=float),
    )

    session.observe_source_text(
        "Initial observation.",
        context_ref="source:expiry-test:instance:first:chunk:00000",
    )
    expired_id = next(iter(session.cluster_rep.values()))
    expired_seed = session.manager.seeds[expired_id]
    session.manager._set_authority(
        expired_seed,
        status=SeedStatus.EXPIRED,
        weight=0.0,
    )

    second = session.observe_source_text(
        "Independent observation after expiry.",
        context_ref="source:expiry-test:instance:second:chunk:00000",
    )
    replacement_id = next(iter(session.cluster_rep.values()))

    assert replacement_id != expired_id
    assert session.manager.seeds[replacement_id].status is not SeedStatus.EXPIRED
    assert session.manager.seeds[replacement_id].occurrence_count == 2
    assert any(
        event.event_type == "cluster_representative_replaced"
        and event.seed_id == replacement_id
        and event.detail["previous_seed_id"] == expired_id
        for event in session.manager.event_log
    )
    assert second["promoted_this_observation"] == []

    promoted = None
    for index in range(3, 7):
        report = session.observe_source_text(
            f"Independent recurrence {index}.",
            context_ref=(
                f"source:expiry-test:instance:independent-{index}:chunk:00000"
            ),
        )
        if replacement_id in report["promoted_this_observation"]:
            promoted = report
            break

    assert promoted is not None
    assert session.manager.seeds[replacement_id].status is SeedStatus.PROMOTED



def test_self_reinforcement_toggle_controls_ssl_attributed_recurrence() -> None:
    def make(enabled: bool) -> ShadowChatSession:
        return ShadowChatSession(
            backend="fixture",
            runtime_mode="live",
            authority_profile_id="autonomous",
            embedding_backend="lexical",
            detector_backend=_NearDuplicateDetector(),
            embedding_fn=lambda _text: np.asarray([1.0, 0.0], dtype=float),
            core_config=SSLCoreConfig(
                min_occurrences_for_gate=1,
                promotion_threshold=0.2,
            ),
            surface_threshold=0.0,
            early_turn_margin=0.0,
            allow_self_reinforcement=enabled,
        )

    guarded = make(False)
    open_loop = make(True)

    for session in (guarded, open_loop):
        first = session.observe_source_text(
            "Initial independent observation.",
            context_ref="source:self-loop:instance:first:chunk:00000",
        )
        assert first["promoted_this_observation"]
        seed = next(iter(session.manager.seeds.values()))
        assert seed.status is SeedStatus.PROMOTED

        prepared = session.prepare_turn("Alpha explanatory boundary")
        assert prepared.surfaced_seed_ids
        report = session.observe_turn(
            prepared,
            "Alpha identifies a missing explanatory boundary.",
        )
        assert report["surfaced_seed_ids"]

    guarded_seed = next(iter(guarded.manager.seeds.values()))
    open_seed = next(iter(open_loop.manager.seeds.values()))

    assert guarded_seed.occurrence_count == 1
    assert open_seed.occurrence_count == 2
    assert guarded.turn_reports[-1]["suppressed_self_attributed_candidates"]
    assert guarded.turn_reports[-1]["self_reinforcement_enabled"] is False
    assert open_loop.turn_reports[-1]["suppressed_self_attributed_candidates"] == []
    assert open_loop.turn_reports[-1]["self_reinforcement_enabled"] is True

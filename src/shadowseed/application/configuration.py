"""Canonical ownership and statefulness metadata for runtime settings.

The metadata is descriptive. It does not apply settings or grant authority.
Workbench and audit surfaces can use it to explain which component owns a
setting and whether changing it can safely take effect against existing state.
"""

from __future__ import annotations

from typing import Any

from shadowseed.application.models import SessionConfig
from shadowseed.core_config import SSLCoreConfig


IMMEDIATE = "immediate"
STATEFUL = "stateful"
REBUILD_REQUIRED = "rebuild_required"

_VALID_APPLY_MODES = {IMMEDIATE, STATEFUL, REBUILD_REQUIRED}


def _meta(component: str, apply_mode: str, reason: str) -> dict[str, str]:
    if apply_mode not in _VALID_APPLY_MODES:
        raise ValueError(f"unknown setting apply mode: {apply_mode}")
    return {
        "component": component,
        "apply_mode": apply_mode,
        "reason": reason,
    }


SETTING_METADATA: dict[str, dict[str, str]] = {
    # Generation/model transport.
    "backend": _meta(
        "answer_generation",
        STATEFUL,
        "A provider change affects future model calls but does not reinterpret stored seed state.",
    ),
    "model_id": _meta(
        "answer_generation",
        STATEFUL,
        "A model change affects future model calls but does not rewrite prior turns.",
    ),
    "max_new_tokens": _meta(
        "answer_generation",
        IMMEDIATE,
        "The generation limit is consumed on the next model call and has no persisted semantic state.",
    ),
    # Semantic representation.
    "embedding_backend": _meta(
        "semantic_representation",
        REBUILD_REQUIRED,
        "Existing seed vectors belong to the embedding space that created them.",
    ),
    "embedding_model": _meta(
        "semantic_representation",
        REBUILD_REQUIRED,
        "Existing seed vectors cannot be reinterpreted under another embedding model.",
    ),
    "allow_toy_embedder": _meta(
        "semantic_representation",
        REBUILD_REQUIRED,
        "Changing embedding capability may change the representation implementation used by existing memory.",
    ),
    # Relevance/surfacing.
    "surface_threshold": _meta(
        "relevance_surfacing",
        IMMEDIATE,
        "The threshold is evaluated at point of surfacing and does not rewrite authority.",
    ),
    "surface_top_k": _meta(
        "relevance_surfacing",
        IMMEDIATE,
        "The cap is evaluated at point of surfacing and does not rewrite authority.",
    ),
    "early_turn_margin": _meta(
        "relevance_surfacing",
        IMMEDIATE,
        "The margin affects future relevance selection only.",
    ),
    "early_turn_history": _meta(
        "relevance_surfacing",
        STATEFUL,
        "The rule reads conversation age/history and changes future selection against accumulated session history.",
    ),
    "resurface_margin": _meta(
        "relevance_surfacing",
        IMMEDIATE,
        "The margin affects future resurfacing decisions only.",
    ),
    # Detection/intake.
    "max_seeds_per_turn": _meta(
        "detection",
        IMMEDIATE,
        "The cap bounds future detector output only.",
    ),
    "max_seed_words": _meta(
        "detection_intake",
        IMMEDIATE,
        "The limit constrains future detector/intake candidates and leaves accepted historical seeds unchanged.",
    ),
    "dedup_threshold": _meta(
        "intake_deduplication",
        STATEFUL,
        "Changing semantic identity thresholds can change how future observations attach to existing seeds.",
    ),
    # Recurrence.
    "recurrence_mode": _meta(
        "recurrence",
        REBUILD_REQUIRED,
        "Pairwise and cluster recurrence use different persisted structural state.",
    ),
    "cluster_threshold": _meta(
        "recurrence",
        REBUILD_REQUIRED,
        "Existing cluster membership was built under the active threshold.",
    ),
    # Probe/retrieval side channel.
    "probe_corpus": _meta(
        "side_channels",
        STATEFUL,
        "The corpus changes future probe results without changing historical Gate events.",
    ),
    "probe_top_k": _meta(
        "side_channels",
        IMMEDIATE,
        "The cap affects future probe reads only.",
    ),
    # Runtime regime and authority.
    "runtime_mode": _meta(
        "runtime_orchestration",
        REBUILD_REQUIRED,
        "Live and evaluation sessions have different runtime semantics and should not reinterpret one persisted session.",
    ),
    "gate_policy_id": _meta(
        "validation_gate",
        STATEFUL,
        "A policy change changes current authorization and future Gate decisions; historical Gate events remain immutable.",
    ),
    "authority_profile_id": _meta(
        "human_ssl_orchestration",
        STATEFUL,
        "The profile changes who may act automatically and therefore changes future orchestration.",
    ),
    "revalidate_current_gate": _meta(
        "point_of_use_authorization",
        STATEFUL,
        "The flag changes whether historical promotion is rechecked against current Gate semantics.",
    ),
    "allow_same_turn_revision": _meta(
        "same_turn_revision",
        STATEFUL,
        "The switch controls whether a newly authorized seed may revise the current draft once.",
    ),
    "self_derived_signal_policy": _meta(
        "observation_provenance",
        STATEFUL,
        "The policy controls how future model-derived observations are retained without changing historical provenance.",
    ),
    "allow_self_reinforcement": _meta(
        "observation_provenance",
        STATEFUL,
        "Legacy compatibility field; 0.11 maps it to same-turn revision without reopening self-derived authority.",
    ),
    # Product aliases. They are persisted explanation/control values.
    "ssl_intensity": _meta(
        "relevance_surfacing",
        IMMEDIATE,
        "This product control maps onto concrete surfacing settings.",
    ),
    "gate_strictness": _meta(
        "validation_gate",
        STATEFUL,
        "This product control maps onto authority profile, Gate policy and Gate thresholds.",
    ),
    # Gate thresholds / authority trajectory.
    "min_occurrences_for_gate": _meta(
        "validation_gate",
        STATEFUL,
        "The threshold changes future qualifying recurrence and current authorization checks.",
    ),
    "min_evidence_for_gate": _meta(
        "validation_gate",
        STATEFUL,
        "The threshold is retained for compatibility policies and changes future/current Gate interpretation there.",
    ),
    "min_trace_for_gate": _meta(
        "validation_gate",
        STATEFUL,
        "The threshold is retained for compatibility policies and changes future/current Gate interpretation there.",
    ),
    "promotion_threshold": _meta(
        "validation_gate",
        STATEFUL,
        "The threshold changes current point-of-use eligibility and future promotion outcomes.",
    ),
    "validation_increment": _meta(
        "validation_gate",
        STATEFUL,
        "The increment changes future authority growth without rewriting historical Gate events.",
    ),
    # Lifecycle/core state.
    "trace_start": _meta(
        "lifecycle",
        STATEFUL,
        "The value changes initial trace for future seed creation only.",
    ),
    "half_life_turns": _meta(
        "lifecycle",
        STATEFUL,
        "The value changes future decay against already accumulated trace state.",
    ),
    "dormant_threshold": _meta(
        "lifecycle",
        STATEFUL,
        "The threshold changes future dormancy transitions against existing trace state.",
    ),
    "dormant_ttl_turns": _meta(
        "lifecycle",
        STATEFUL,
        "The value changes future terminal-expiry timing against accumulated dormancy state.",
    ),
    "max_trace": _meta(
        "lifecycle",
        STATEFUL,
        "The cap changes future trace updates without rewriting historical trace events.",
    ),
    "reactivation_increment": _meta(
        "lifecycle",
        STATEFUL,
        "The increment changes future reactivation behavior.",
    ),
    # Contradiction / outcome feedback.
    "contradiction_penalty": _meta(
        "validation_gate",
        STATEFUL,
        "The penalty changes future contradiction authority transitions.",
    ),
    "contradiction_trace_penalty": _meta(
        "lifecycle",
        STATEFUL,
        "The penalty changes future trace degradation after contradiction.",
    ),
    "reward_step": _meta(
        "task_outcome_feedback",
        STATEFUL,
        "The step changes future task-outcome updates only.",
    ),
    "penalty_step": _meta(
        "task_outcome_feedback",
        STATEFUL,
        "The step changes future task-outcome updates only.",
    ),
}


def setting_metadata() -> dict[str, dict[str, str]]:
    """Return a copy safe for read-only Workbench/audit projection."""

    return {key: dict(value) for key, value in SETTING_METADATA.items()}


def validate_setting_metadata_complete() -> None:
    """Fail if a persisted/runtime field has no explicit owner and apply mode."""

    expected = set(SessionConfig.__dataclass_fields__) | set(SSLCoreConfig.__dataclass_fields__)
    actual = set(SETTING_METADATA)
    missing = sorted(expected - actual)
    if missing:
        raise ValueError(
            "missing setting metadata for: " + ", ".join(missing)
        )


validate_setting_metadata_complete()


__all__ = [
    "IMMEDIATE",
    "STATEFUL",
    "REBUILD_REQUIRED",
    "SETTING_METADATA",
    "setting_metadata",
    "validate_setting_metadata_complete",
]

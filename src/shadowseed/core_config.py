"""Central SSL 4.5 core configuration.

This module keeps the canonical default thresholds in one place so the core
manager, benchmark runners and future evaluators can stay aligned.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True)
class SSLCoreConfig:
    """Canonical defaults for the SSL 4.5 core lifecycle."""

    trace_start: float = 2.0
    half_life_turns: float = 3.0
    dedup_threshold: float = 0.85
    promotion_threshold: float = 0.5
    dormant_threshold: float = 0.05
    validation_increment: float = 0.2
    contradiction_penalty: float = 0.3
    reward_step: float = 0.1
    penalty_step: float = 0.2
    max_trace: float = 3.0
    reactivation_increment: float = 2.0
    min_occurrences_for_gate: int = 3
    min_evidence_for_gate: int = 2
    min_trace_for_gate: float = 0.5
    max_seed_words: int = 18
    # TTL to disappearance (4.5 §10/§12.2): a seed that stays DORMANT without a
    # re-recognising trigger for this many decay turns becomes EXPIRED — the
    # doctrine's 'dormant too long without a trigger -> removed from shadow memory'.
    dormant_ttl_turns: int = 5
    # Falsification lowers weight (→ NEW) AND nudges trace down, so a degraded
    # seed starts running out its TTL toward disappearance instead of getting a
    # full new life. 0.0 keeps the legacy behaviour (weight-only).
    contradiction_trace_penalty: float = 0.5

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

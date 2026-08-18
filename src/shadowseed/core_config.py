"""Central SSL 4.5 core configuration.

This module keeps the canonical default thresholds in one place so the core
manager, benchmark runners and future evaluators can stay aligned.
"""

from __future__ import annotations

import math
from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True)
class SSLCoreConfig:
    """Canonical defaults for the SSL 4.5 core lifecycle."""

    trace_start: float = 2.0
    # The old exp(-t/3) default had an actual half-life of 3*ln(2). Keep that
    # calibrated decay curve while giving explicit values true half-life
    # semantics under exp(-ln(2)*t/h).
    half_life_turns: float = 3.0 * math.log(2.0)
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

    def __post_init__(self) -> None:
        numeric_fields = (
            "trace_start",
            "half_life_turns",
            "dedup_threshold",
            "promotion_threshold",
            "dormant_threshold",
            "validation_increment",
            "contradiction_penalty",
            "reward_step",
            "penalty_step",
            "max_trace",
            "reactivation_increment",
            "min_trace_for_gate",
            "contradiction_trace_penalty",
        )
        for name in numeric_fields:
            value = getattr(self, name)
            if isinstance(value, bool) or not isinstance(value, (int, float)):
                raise ValueError(f"{name} must be a finite number")
            if not math.isfinite(float(value)):
                raise ValueError(f"{name} must be finite")

        integer_fields = (
            "min_occurrences_for_gate",
            "min_evidence_for_gate",
            "max_seed_words",
            "dormant_ttl_turns",
        )
        for name in integer_fields:
            value = getattr(self, name)
            if isinstance(value, bool) or not isinstance(value, int):
                raise ValueError(f"{name} must be an integer")

        if self.trace_start <= 0.0:
            raise ValueError("trace_start must be > 0")
        if self.half_life_turns <= 0.0:
            raise ValueError("half_life_turns must be > 0")
        if not -1.0 <= self.dedup_threshold <= 1.0:
            raise ValueError("dedup_threshold must be between -1 and 1")
        if not 0.0 < self.promotion_threshold <= 1.0:
            raise ValueError("promotion_threshold must be in (0, 1]")
        if self.dormant_threshold < 0.0:
            raise ValueError("dormant_threshold must be >= 0")
        for name in (
            "validation_increment",
            "contradiction_penalty",
            "reward_step",
            "penalty_step",
        ):
            value = float(getattr(self, name))
            if not 0.0 <= value <= 1.0:
                raise ValueError(f"{name} must be between 0 and 1")
        if self.max_trace <= 0.0:
            raise ValueError("max_trace must be > 0")
        if self.max_trace < self.trace_start:
            raise ValueError("max_trace must be >= trace_start")
        if self.reactivation_increment < 0.0:
            raise ValueError("reactivation_increment must be >= 0")
        if self.min_occurrences_for_gate < 1:
            raise ValueError("min_occurrences_for_gate must be >= 1")
        if self.min_evidence_for_gate < 0:
            raise ValueError("min_evidence_for_gate must be >= 0")
        if self.min_trace_for_gate < 0.0:
            raise ValueError("min_trace_for_gate must be >= 0")
        if self.max_seed_words < 1:
            raise ValueError("max_seed_words must be >= 1")
        if self.dormant_ttl_turns < 0:
            raise ValueError("dormant_ttl_turns must be >= 0")
        if self.contradiction_trace_penalty < 0.0:
            raise ValueError("contradiction_trace_penalty must be >= 0")

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

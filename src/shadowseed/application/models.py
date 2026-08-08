"""Stable application-level data contracts for tester-facing workflows."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(frozen=True)
class SessionConfig:
    """Configuration required to construct one :class:`ShadowChatSession`.

    Secrets are intentionally absent. Hosted backend credentials remain in the
    process environment or an operating-system keyring and are never persisted
    in a workspace record.
    """

    backend: str = "fixture"
    model_id: str | None = None
    max_new_tokens: int = 700
    embedding_backend: str = "lexical"
    embedding_model: str | None = None
    surface_threshold: float = 0.30
    surface_top_k: int = 2
    early_turn_margin: float = 0.10
    early_turn_history: int = 5
    resurface_margin: float = 0.15
    recurrence_mode: str = "cluster"
    cluster_threshold: float | None = None
    probe_corpus: str | None = None
    probe_top_k: int = 3

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "SessionConfig":
        allowed = cls.__dataclass_fields__
        return cls(**{key: value for key, value in data.items() if key in allowed})


@dataclass(frozen=True)
class SessionSummary:
    session_id: str
    title: str
    profile_id: str
    backend: str
    model_id: str | None
    turn_count: int
    seed_count: int
    created_at: str
    updated_at: str


@dataclass(frozen=True)
class TesterFeedback:
    session_id: str
    turn_index: int
    overall: str = "neutral"
    seed_effect: str = "no_visible_effect"
    note: str = ""
    action: str = "record_only"
    seed_id: str | None = None
    created_at: str | None = None
    feedback_id: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class HealthCheck:
    name: str
    status: str
    detail: str
    repair: str | None = None

    @property
    def ok(self) -> bool:
        return self.status == "ok"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class DoctorReport:
    checks: tuple[HealthCheck, ...] = field(default_factory=tuple)

    @property
    def ready(self) -> bool:
        return all(check.status != "error" for check in self.checks)

    def to_dict(self) -> dict[str, Any]:
        return {
            "ready": self.ready,
            "checks": [check.to_dict() for check in self.checks],
        }

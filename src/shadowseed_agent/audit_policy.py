"""Audit helpers for agent decisions driven by SSL seeds."""

from __future__ import annotations

from dataclasses import dataclass


class WeightlessInfluenceError(AssertionError):
    """Raised when audit replay finds allowed influence from a weightless seed."""


@dataclass(frozen=True)
class AgentInfluenceRecord:
    """Replayable record of one seed-driven agent decision."""

    seed_id: str
    action: str
    seed_weight: float
    seed_status: str
    allowed: bool
    reason: str
    gate_event_ref: str | None = None


def assert_no_weightless_influence(records: list[AgentInfluenceRecord]) -> None:
    """Fail audit replay if any allowed action came from a weightless seed."""

    violations = [record for record in records if record.allowed and record.seed_weight <= 0.0]
    if not violations:
        return

    first = violations[0]
    raise WeightlessInfluenceError(
        "weightless seed influenced agent action: "
        f"seed_id={first.seed_id!r} action={first.action!r} reason={first.reason!r}"
    )

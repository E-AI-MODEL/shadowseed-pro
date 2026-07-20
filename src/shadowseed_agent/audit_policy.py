"""Audit helpers for agent decisions driven by SSL seeds."""

from __future__ import annotations

from dataclasses import dataclass


class WeightlessInfluenceError(AssertionError):
    """Raised when audit replay finds allowed influence from a weightless seed."""


class InfluenceReplayError(AssertionError):
    """Raised when strict replay finds an allowed influence that violates an
    invariant beyond positive weight (not promoted, contradicted, missing or
    stale Gate-event link)."""


@dataclass(frozen=True)
class AgentInfluenceRecord:
    """Replayable record of one seed-driven agent decision.

    The first fields are the original, backward-compatible shape. The trailing
    fields (added in #14) link the decision to the Gate event that authorized it
    and snapshot the authority version so a stale authorization can be detected
    on replay.
    """

    seed_id: str
    action: str
    seed_weight: float
    seed_status: str
    allowed: bool
    reason: str
    gate_event_ref: str | None = None
    authority_version: int | None = None
    contradiction_blocking: bool = False
    policy_id: str | None = None
    context_ref: str | None = None
    decided_at: str | None = None


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


def assert_influence_records_valid(
    records: list[AgentInfluenceRecord],
    gate_events: list | None = None,
) -> None:
    """Strict replay of every allowed influence decision.

    Beyond positive weight, each allowed record must be PROMOTED, free of a
    blocking contradiction, and linked to a Gate event that exists (when a
    ``gate_events`` ledger is supplied), belongs to the same seed, and left the
    seed PROMOTED. Raises on the first violation.
    """

    assert_no_weightless_influence(records)

    index: dict[str, object] = {}
    if gate_events is not None:
        for event in gate_events:
            event_id = getattr(event, "event_id", None)
            if event_id is not None:
                index[event_id] = event

    for record in records:
        if not record.allowed:
            continue
        if record.seed_status != "PROMOTED":
            raise InfluenceReplayError(
                f"allowed influence from non-promoted seed {record.seed_id!r} "
                f"(status={record.seed_status!r})"
            )
        if record.contradiction_blocking:
            raise InfluenceReplayError(
                f"allowed influence from contradicted seed {record.seed_id!r}"
            )
        if record.gate_event_ref is None:
            raise InfluenceReplayError(
                f"allowed influence with no Gate-event reference for seed {record.seed_id!r}"
            )
        if record.authority_version is None:
            raise InfluenceReplayError(
                f"allowed influence with no authority version for seed {record.seed_id!r}"
            )
        if gate_events is not None:
            event = index.get(record.gate_event_ref)
            if event is None:
                raise InfluenceReplayError(
                    f"allowed influence references unknown Gate event "
                    f"{record.gate_event_ref!r} for seed {record.seed_id!r}"
                )
            if getattr(event, "seed_id", None) != record.seed_id:
                raise InfluenceReplayError(
                    f"Gate-event {record.gate_event_ref!r} belongs to a different seed"
                )
            if getattr(event, "status_after", None) != "PROMOTED":
                raise InfluenceReplayError(
                    f"Gate-event {record.gate_event_ref!r} did not leave seed "
                    f"{record.seed_id!r} promoted"
                )
            if getattr(event, "authority_version", None) != record.authority_version:
                raise InfluenceReplayError(
                    f"stale authority version for seed {record.seed_id!r}: "
                    f"record={record.authority_version} event="
                    f"{getattr(event, 'authority_version', None)}"
                )
            if record.policy_id is not None and getattr(event, "policy_id", None) != record.policy_id:
                raise InfluenceReplayError(
                    f"policy mismatch for seed {record.seed_id!r}: "
                    f"record={record.policy_id!r} event={getattr(event, 'policy_id', None)!r}"
                )

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


#: Gate decisions that may authorize influence (mirror of the contract's set).
_AUTHORITY_CONFIRMING_DECISIONS = frozenset({"promoted", "validated"})


def assert_influence_records_valid(
    records: list[AgentInfluenceRecord],
    gate_events: list,
) -> None:
    """Strict replay of every allowed influence decision.

    ``gate_events`` (the manager's Gate ledger) is required: strict replay must
    be able to independently reconstruct each authorization. Each allowed record
    must be PROMOTED, free of a blocking contradiction (checked both on the
    record and on the linked event), carry a policy id and an authority version,
    and link to a Gate event that exists, belongs to the same seed, carries an
    authority-confirming decision, left the seed promoted, matches the recorded
    authority version, and matches the recorded policy. Raises on the first
    violation.
    """

    assert_no_weightless_influence(records)

    index: dict[str, object] = {}
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
        if record.policy_id is None:
            raise InfluenceReplayError(
                f"allowed influence with no policy id for seed {record.seed_id!r}"
            )
        if not record.decided_at:
            raise InfluenceReplayError(
                f"allowed influence with no timestamp for seed {record.seed_id!r}"
            )
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
        decision = getattr(event, "decision", None)
        decision_value = str(getattr(decision, "value", decision))
        if decision_value not in _AUTHORITY_CONFIRMING_DECISIONS:
            raise InfluenceReplayError(
                f"Gate-event {record.gate_event_ref!r} is not an authority-confirming "
                f"decision (decision={decision_value!r})"
            )
        if getattr(event, "status_after", None) != "PROMOTED":
            raise InfluenceReplayError(
                f"Gate-event {record.gate_event_ref!r} did not leave seed "
                f"{record.seed_id!r} promoted"
            )
        contradiction_after = getattr(event, "contradiction_after", None)
        if contradiction_after is not None and getattr(contradiction_after, "blocking", False):
            raise InfluenceReplayError(
                f"Gate-event {record.gate_event_ref!r} records a blocking contradiction "
                f"for seed {record.seed_id!r}"
            )
        if getattr(event, "authority_version", None) != record.authority_version:
            raise InfluenceReplayError(
                f"stale authority version for seed {record.seed_id!r}: "
                f"record={record.authority_version} event="
                f"{getattr(event, 'authority_version', None)}"
            )
        if getattr(event, "policy_id", None) != record.policy_id:
            raise InfluenceReplayError(
                f"policy mismatch for seed {record.seed_id!r}: "
                f"record={record.policy_id!r} event={getattr(event, 'policy_id', None)!r}"
            )

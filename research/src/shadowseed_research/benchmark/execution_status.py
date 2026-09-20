"""Execution-status logic for SSL benchmark lanes."""

from __future__ import annotations

from dataclasses import dataclass, field

from .run_types import ExecutionStatus, HostStatus, RunType, RunnerStatus


@dataclass
class ExecutionDecision:
    run_type: str
    execution_status: str
    execution_gap: bool
    notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "run_type": self.run_type,
            "execution_status": self.execution_status,
            "execution_gap": self.execution_gap,
            "notes": self.notes,
        }


def resolve_execution_status(
    requested_run_type: str,
    host_status: str,
    runner_status: str,
    execution_gap: bool,
) -> ExecutionDecision:
    notes: list[str] = []

    if host_status == HostStatus.OUTDATED.value or runner_status == RunnerStatus.OUTDATED.value:
        notes.append("An outdated host or repository blocks a live benchmark run.")
        return ExecutionDecision(
            run_type=RunType.PREPARATION.value,
            execution_status=ExecutionStatus.EXECUTION_GAP.value,
            execution_gap=True,
            notes=notes,
        )

    if runner_status == RunnerStatus.BLOCKED.value:
        notes.append("The runner is explicitly blocked.")
        return ExecutionDecision(
            run_type=RunType.PREPARATION.value,
            execution_status=ExecutionStatus.EXECUTION_GAP.value,
            execution_gap=True,
            notes=notes,
        )

    if requested_run_type == RunType.LIVE.value:
        if (
            host_status == HostStatus.VERIFIED.value
            and runner_status == RunnerStatus.VERIFIED.value
            and not execution_gap
        ):
            notes.append("The host and runner are verified for live execution.")
            return ExecutionDecision(
                run_type=RunType.LIVE.value,
                execution_status=ExecutionStatus.LIVE.value,
                execution_gap=False,
                notes=notes,
            )

        notes.append("Live execution was requested, but the route is not fully verified.")
        return ExecutionDecision(
            run_type=RunType.PREPARATION.value,
            execution_status=ExecutionStatus.EXECUTION_GAP.value,
            execution_gap=True,
            notes=notes,
        )

    if requested_run_type == RunType.SCAN.value:
        notes.append("A benchmark scan is allowed while the live route remains unverified.")
        return ExecutionDecision(
            run_type=RunType.SCAN.value,
            execution_status=ExecutionStatus.SCAN.value,
            execution_gap=execution_gap,
            notes=notes,
        )

    notes.append("Benchmark preparation remains the default status.")
    if execution_gap:
        notes.append("An execution gap remains open.")
    return ExecutionDecision(
        run_type=RunType.PREPARATION.value,
        execution_status=(
            ExecutionStatus.EXECUTION_GAP.value
            if execution_gap
            else ExecutionStatus.PREPARATION.value
        ),
        execution_gap=execution_gap,
        notes=notes,
    )

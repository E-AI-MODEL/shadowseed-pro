"""Host and runner verification helpers for benchmark execution lanes."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone

from .execution_status import resolve_execution_status
from .run_types import HostStatus, RunType, RunnerStatus


@dataclass
class HostVerification:
    benchmark_name: str
    host_platform: str
    runner_source: str
    runner_status: str
    host_status: str
    execution_status: str
    verification_notes: list[str]
    execution_gap: bool
    outdated_repo: bool = False
    verified_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> dict:
        return asdict(self)


def build_host_verification(
    benchmark_name: str,
    host_platform: str,
    runner_source: str,
    dataset_present: bool,
    paper_present: bool,
    repo_present: bool,
    runner_entrypoints_present: bool,
    outdated_repo: bool,
    requested_run_type: str = RunType.PREPARATION.value,
) -> HostVerification:
    notes: list[str] = []

    if dataset_present and paper_present and repo_present:
        host_status = HostStatus.PRESENT.value
        notes.append("The dataset, paper, and runner source are publicly present.")
    else:
        host_status = HostStatus.UNVERIFIED.value
        notes.append("Not all source layers have been publicly confirmed.")

    if outdated_repo:
        runner_status = RunnerStatus.OUTDATED.value
        notes.append("The repository route is invalid as a runner because it is outdated.")
    elif repo_present and runner_entrypoints_present:
        runner_status = RunnerStatus.STRUCTURE_PRESENT.value
        notes.append("Runner structure is present but has not been verified live.")
    elif repo_present:
        runner_status = RunnerStatus.UNVERIFIED.value
        notes.append("The repository exists, but its entry points are not established.")
    else:
        runner_status = RunnerStatus.BLOCKED.value
        notes.append("The runner source is missing or unreachable.")

    execution_gap = not (
        host_status == HostStatus.VERIFIED.value
        and runner_status == RunnerStatus.VERIFIED.value
    )

    decision = resolve_execution_status(
        requested_run_type=requested_run_type,
        host_status=host_status,
        runner_status=runner_status,
        execution_gap=execution_gap,
    )
    notes.extend(decision.notes)

    return HostVerification(
        benchmark_name=benchmark_name,
        host_platform=host_platform,
        runner_source=runner_source,
        runner_status=runner_status,
        host_status=host_status,
        execution_status=decision.execution_status,
        verification_notes=notes,
        execution_gap=decision.execution_gap,
        outdated_repo=outdated_repo,
    )

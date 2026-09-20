"""Generic benchmark runner lane for Shadow Seed Learning."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field

from .execution_status import ExecutionDecision, resolve_execution_status
from .host_verification import HostVerification
from .result_writer import ResultWriter
from .schemas import BenchmarkResult


@dataclass
class BenchmarkPlan:
    benchmark_name: str
    requested_run_type: str
    ssl_input_basis: list[str] = field(default_factory=list)
    host_platform: str = ""
    runner_source: str = ""
    score_type: str = "unverified"

    def to_dict(self) -> dict:
        return asdict(self)


class BenchmarkRunner:
    def __init__(self, writer: ResultWriter | None = None):
        self.writer = writer or ResultWriter()

    def evaluate_readiness(
        self,
        plan: BenchmarkPlan,
        verification: HostVerification,
        limitations: list[str],
    ) -> tuple[ExecutionDecision, BenchmarkResult]:
        decision = resolve_execution_status(
            requested_run_type=plan.requested_run_type,
            host_status=verification.host_status,
            runner_status=verification.runner_status,
            execution_gap=verification.execution_gap,
        )
        result = BenchmarkResult(
            benchmark_name=plan.benchmark_name,
            run_type=decision.run_type,
            execution_status=decision.execution_status,
            ssl_input_basis=plan.ssl_input_basis,
            host_platform=plan.host_platform,
            dataset_status=verification.host_status,
            runner_status=verification.runner_status,
            score=None,
            score_type=plan.score_type,
            interpretation=(
                "Readiness result without a live benchmark score. The repository "
                "supports the route but does not fabricate a run while verification is incomplete."
            ),
            limitations=limitations + verification.verification_notes,
            execution_gap=decision.execution_gap,
        )
        return decision, result

"""AbsenceBench-specific execution lane for Shadow Seed Learning."""

from __future__ import annotations

from dataclasses import asdict, dataclass

from .absencebench import build_preparation_record, build_run_card
from .host_verification import HostVerification, build_host_verification
from .runner import BenchmarkPlan, BenchmarkRunner
from .run_types import RunType


@dataclass
class AbsenceBenchExecutionBundle:
    preparation: dict
    run_card: dict
    verification: dict
    decision: dict
    result: dict

    def to_dict(self) -> dict:
        return asdict(self)


class AbsenceBenchRunner:
    def __init__(self, runner: BenchmarkRunner | None = None):
        self.runner = runner or BenchmarkRunner()

    def verify(
        self,
        requested_run_type: str = RunType.PREPARATION.value,
        dataset_present: bool = True,
        paper_present: bool = True,
        repo_present: bool = True,
        runner_entrypoints_present: bool = True,
        outdated_repo: bool = False,
    ) -> HostVerification:
        return build_host_verification(
            benchmark_name="AbsenceBench",
            host_platform="Hugging Face dataset + GitHub repo",
            runner_source="harveyfin/AbsenceBench + harvey-fin/absence-bench",
            dataset_present=dataset_present,
            paper_present=paper_present,
            repo_present=repo_present,
            runner_entrypoints_present=runner_entrypoints_present,
            outdated_repo=outdated_repo,
            requested_run_type=requested_run_type,
        )

    def build_execution_bundle(
        self,
        requested_run_type: str = RunType.PREPARATION.value,
        dataset_present: bool = True,
        paper_present: bool = True,
        repo_present: bool = True,
        runner_entrypoints_present: bool = True,
        outdated_repo: bool = False,
    ) -> AbsenceBenchExecutionBundle:
        preparation = build_preparation_record()
        run_card = build_run_card().to_dict()
        verification = self.verify(
            requested_run_type=requested_run_type,
            dataset_present=dataset_present,
            paper_present=paper_present,
            repo_present=repo_present,
            runner_entrypoints_present=runner_entrypoints_present,
            outdated_repo=outdated_repo,
        )
        plan = BenchmarkPlan(
            benchmark_name="AbsenceBench",
            requested_run_type=requested_run_type,
            ssl_input_basis=preparation["ssl_sources"],
            host_platform=run_card["host_platform"],
            runner_source="harvey-fin/absence-bench",
            score_type=preparation["score_type"],
        )
        decision, result = self.runner.evaluate_readiness(
            plan=plan,
            verification=verification,
            limitations=preparation["missing_components"],
        )
        return AbsenceBenchExecutionBundle(
            preparation=preparation,
            run_card=run_card,
            verification=verification.to_dict(),
            decision=decision.to_dict(),
            result=result.to_dict(),
        )

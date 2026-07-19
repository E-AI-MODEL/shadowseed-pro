from pathlib import Path
import sys

sys.path.insert(0, str(Path("src").resolve()))

from shadowseed.benchmark.host_verification import build_host_verification
from shadowseed.benchmark.run_types import RunType



def test_host_verification_marks_structure_present():
    verification = build_host_verification(
        benchmark_name="AbsenceBench",
        host_platform="Hugging Face dataset + GitHub repo",
        runner_source="harvey-fin/absence-bench",
        dataset_present=True,
        paper_present=True,
        repo_present=True,
        runner_entrypoints_present=True,
        outdated_repo=False,
        requested_run_type=RunType.PREPARATION.value,
    )
    assert verification.host_status == "present"
    assert verification.runner_status == "structure_present"
    assert verification.execution_gap is True



def test_outdated_repo_is_never_treated_as_valid_runner():
    verification = build_host_verification(
        benchmark_name="AbsenceBench",
        host_platform="Hugging Face dataset + GitHub repo",
        runner_source="harvey-fin/absence-bench",
        dataset_present=True,
        paper_present=True,
        repo_present=True,
        runner_entrypoints_present=True,
        outdated_repo=True,
        requested_run_type=RunType.LIVE.value,
    )
    assert verification.runner_status == "outdated"
    assert verification.execution_status == "execution_gap"

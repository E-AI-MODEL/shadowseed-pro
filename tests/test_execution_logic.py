from pathlib import Path
import sys

sys.path.insert(0, str(Path("src").resolve()))

from shadowseed.benchmark.execution_status import resolve_execution_status
from shadowseed.benchmark.run_types import HostStatus, RunType, RunnerStatus



def test_live_request_with_gap_falls_back_to_gap_status():
    decision = resolve_execution_status(
        requested_run_type=RunType.LIVE.value,
        host_status=HostStatus.PRESENT.value,
        runner_status=RunnerStatus.STRUCTURE_PRESENT.value,
        execution_gap=True,
    )
    assert decision.run_type == RunType.PREPARATION.value
    assert decision.execution_status == "execution_gap"
    assert decision.execution_gap is True



def test_outdated_runner_blocks_execution():
    decision = resolve_execution_status(
        requested_run_type=RunType.LIVE.value,
        host_status=HostStatus.PRESENT.value,
        runner_status=RunnerStatus.OUTDATED.value,
        execution_gap=True,
    )
    assert decision.execution_status == "execution_gap"
    assert decision.execution_gap is True

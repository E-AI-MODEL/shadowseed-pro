import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path("src").resolve()))

from shadowseed.benchmark.absencebench_runner import AbsenceBenchRunner
from shadowseed.benchmark.result_writer import ResultWriter
from shadowseed.benchmark.run_types import RunType



def test_absencebench_runner_smoke_bundle():
    bundle = AbsenceBenchRunner().build_execution_bundle(
        requested_run_type=RunType.SCAN.value
    ).to_dict()
    assert bundle["verification"]["host_status"] == "present"
    assert bundle["result"]["run_type"] == "benchmark_scan"



def test_report_writer_can_store_bundle_result(tmp_path: Path):
    bundle = AbsenceBenchRunner().build_execution_bundle(
        requested_run_type=RunType.PREPARATION.value
    ).to_dict()
    writer = ResultWriter(root=tmp_path)
    output = writer.write_payload(bundle["result"], "absencebench/readiness.json")
    payload = json.loads(output.read_text(encoding="utf-8"))
    assert payload["execution_gap"] is True

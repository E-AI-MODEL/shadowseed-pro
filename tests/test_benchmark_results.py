import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path("src").resolve()))

from shadowseed.benchmark.absencebench import build_run_card, load_gap_test_suite
from shadowseed.benchmark.result_writer import ResultWriter
from shadowseed.benchmark.run_types import ExecutionStatus, RunType
from shadowseed.benchmark.schemas import BenchmarkResult



def test_gap_test_suite_loads_expected_scenarios():
    suite = load_gap_test_suite()
    assert suite["version"] == "4.5"
    assert len(suite["scenarios"]) == 3



def test_result_writer_writes_required_schema(tmp_path: Path):
    writer = ResultWriter(root=tmp_path)
    result = BenchmarkResult(
        benchmark_name="AbsenceBench",
        run_type=RunType.PREPARATION.value,
        execution_status=ExecutionStatus.PREPARATION.value,
        ssl_input_basis=[
            "shadow_seed_learning_4_5_clean.md",
            "ssl_4_5_public_release/",
            "benchmark_bibliotheek/",
        ],
        host_platform="Hugging Face dataset + runner te verifiëren",
        dataset_status="bibliografisch vastgelegd",
        runner_status="te verifiëren",
        score=None,
        score_type="nog te verifiëren",
        interpretation="Voorbereidingsrecord zonder live benchmarkscore.",
        limitations=["runnerroute nog niet hard geverifieerd"],
        execution_gap=True,
    )

    output = writer.write_result(result, "absencebench/preparation_result.json")
    payload = json.loads(output.read_text(encoding="utf-8"))

    assert payload["benchmark_name"] == "AbsenceBench"
    assert payload["execution_gap"] is True
    assert "timestamp" in payload



def test_run_card_smoke():
    run_card = build_run_card()
    payload = run_card.to_dict()

    assert payload["benchmark_name"] == "AbsenceBench"
    assert payload["execution_status"] == "benchmark_preparation"
    assert payload["execution_gap"] is True
    assert payload["scenarios_loaded"] == 3
    assert "evaluate.py" in payload["start_command_template"]

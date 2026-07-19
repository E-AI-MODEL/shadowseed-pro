"""Verify AbsenceBench host and runner readiness for Shadow Seed Learning."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPO_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from shadowseed.benchmark.absencebench_runner import AbsenceBenchRunner
from shadowseed.benchmark.result_writer import ResultWriter
from shadowseed.benchmark.run_types import RunType



def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Verify AbsenceBench host and runner readiness."
    )
    parser.add_argument(
        "--run-type",
        default=RunType.SCAN.value,
        choices=[item.value for item in RunType],
        help="Requested benchmark mode.",
    )
    parser.add_argument(
        "--output",
        default="runs/absencebench/verification.json",
        help="Path for the verification summary.",
    )
    parser.add_argument(
        "--result-output",
        default="absencebench/example_scan.json",
        help="Relative path inside benchmarks/results for the scan or readiness result.",
    )
    parser.add_argument(
        "--outdated-repo",
        action="store_true",
        help="Force the outdated-repository block for verification tests.",
    )
    return parser.parse_args()



def main() -> None:
    args = parse_args()
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    runner = AbsenceBenchRunner()
    bundle = runner.build_execution_bundle(
        requested_run_type=args.run_type,
        outdated_repo=args.outdated_repo,
    ).to_dict()

    output_path.write_text(
        json.dumps(bundle, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    writer = ResultWriter(root=REPO_ROOT / "benchmarks" / "results")
    result_path = writer.write_payload(bundle["result"], args.result_output)

    print(f"AbsenceBench verification written to: {output_path}")
    print(f"Readiness result written to: {result_path}")
    print("Execution status:", bundle["decision"]["execution_status"])
    print("Execution gap:", "yes" if bundle["decision"]["execution_gap"] else "no")


if __name__ == "__main__":
    main()

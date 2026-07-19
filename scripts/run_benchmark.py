"""Dispatch benchmark scans, readiness checks, and future live runs."""

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
from shadowseed.benchmark.run_types import RunType



def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run a benchmark scan or readiness check for Shadow Seed Learning."
    )
    parser.add_argument(
        "--benchmark",
        default="absencebench",
        choices=["absencebench"],
        help="Benchmark to use.",
    )
    parser.add_argument(
        "--run-type",
        default=RunType.PREPARATION.value,
        choices=[item.value for item in RunType],
        help="Requested benchmark mode.",
    )
    parser.add_argument(
        "--output",
        default="runs/benchmark/latest.json",
        help="Path for the bundled benchmark output.",
    )
    return parser.parse_args()



def main() -> None:
    args = parse_args()
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    if args.benchmark != "absencebench":
        raise ValueError("Only AbsenceBench currently has an operational benchmark lane.")

    bundle = AbsenceBenchRunner().build_execution_bundle(
        requested_run_type=args.run_type
    ).to_dict()

    output_path.write_text(
        json.dumps(bundle, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(f"Benchmark output written to: {output_path}")
    print("Execution status:", bundle["decision"]["execution_status"])
    print("Run type:", bundle["decision"]["run_type"])


if __name__ == "__main__":
    main()

"""Run full SSL vs baseline experiment."""

from __future__ import annotations

import json
from pathlib import Path

from shadowseed.benchmark.absencebench_ssl_true import run_benchmark
from shadowseed.benchmark.absencebench_hf import fetch_absencebench_sample

OUTPUT_DIR = Path("results")


def main() -> None:
    OUTPUT_DIR.mkdir(exist_ok=True)

    dataset_path = "data/absencebench_sample.json"

    print("Fetching dataset...")
    fetch_absencebench_sample(dataset_path, limit=100)

    print("Running benchmark...")
    result = run_benchmark(dataset_path, OUTPUT_DIR / "ssl_results.json")

    print("Done. Results:")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()

"""Run full SSL vs baseline experiment."""

from __future__ import annotations

import json
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPO_ROOT / "src"
RESEARCH_SRC = REPO_ROOT / "research" / "src"
for source_root in (SRC_ROOT, RESEARCH_SRC):
    if str(source_root) not in sys.path:
        sys.path.insert(0, str(source_root))

from shadowseed_research.benchmark.absencebench_hf import fetch_absencebench_sample
from shadowseed_research.benchmark.absencebench_local import run_local_absencebench

OUTPUT_DIR = Path("results")


def main() -> None:
    OUTPUT_DIR.mkdir(exist_ok=True)

    dataset_path = "data/absencebench_sample.json"

    print("Fetching dataset...")
    fetch_absencebench_sample(dataset_path, limit=100)

    print("Running benchmark...")
    result_path = run_local_absencebench(dataset_path, str(OUTPUT_DIR / "ssl_results.json"))
    result = json.loads(result_path.read_text(encoding="utf-8"))

    print("Done. Results:")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()

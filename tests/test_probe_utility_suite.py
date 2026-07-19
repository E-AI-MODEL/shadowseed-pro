from __future__ import annotations

import json
from pathlib import Path

from shadowseed.benchmark.ssl45_probe_utility_suite import run_ssl45_probe_utility_suite


DATA = "src/shadowseed/data/ssl45_probe_utility_suite.json"


def test_probe_utility_suite_prefers_seed_guided_probes(tmp_path: Path) -> None:
    output = tmp_path / "probe_utility.json"
    run_ssl45_probe_utility_suite(DATA, str(output))

    payload = json.loads(output.read_text(encoding="utf-8"))
    summary = payload["summary"]

    assert summary["scenario_count"] == 3
    assert summary["mean_follow_up_delta"] > 0
    assert summary["mean_retrieval_delta"] > 0
    assert summary["mean_dialectic_delta"] > 0
    assert summary["overall_probe_utility_delta"] > 0
    assert summary["passed"] is True

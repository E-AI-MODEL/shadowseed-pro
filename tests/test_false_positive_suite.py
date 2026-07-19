from __future__ import annotations

import json
from pathlib import Path

from shadowseed.benchmark.ssl45_false_positive_suite import run_ssl45_false_positive_suite


DATA = "src/shadowseed/data/gap_test_suite_false_positive_4_5.json"


def test_false_positive_suite_blocks_adversarial_lures(tmp_path: Path) -> None:
    output = tmp_path / "false_positive.json"
    run_ssl45_false_positive_suite(DATA, str(output))

    payload = json.loads(output.read_text(encoding="utf-8"))
    summary = payload["summary"]

    assert summary["candidate_false_positives"] == 0
    assert summary["promoted_false_positives"] == 0
    assert summary["gate_promoted_false_positives"] == 0
    assert summary["baseline_trace_only_promotions"] > 0
    assert summary["gate_vs_trace_only_delta"] > 0
    assert summary["gate_block_rate_on_adversarial_candidates"] == 1.0
    assert summary["passed"] is True

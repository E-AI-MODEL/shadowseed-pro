from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


def test_recurrence_calibration_replays_candidates(tmp_path: Path) -> None:
    data = {
        "schema": "ssl-seed-calibration-input-v1",
        "arms": [
            {
                "model": "fixture",
                "conversations": [
                    {
                        "conversation_id": "C1",
                        "domain": "test",
                        "turns": [
                            {"turn": 0, "question": "q0", "answer": "a0",
                             "candidates": [{"text": "Whether staff can be recruited downtown."}]},
                            {"turn": 1, "question": "q1", "answer": "a1",
                             "candidates": [{"text": "Whether staff can be recruited downtown."}]},
                        ],
                    }
                ],
            }
        ],
    }
    source = tmp_path / "input.json"
    source.write_text(json.dumps(data), encoding="utf-8")
    out = tmp_path / "out"
    subprocess.run(
        [sys.executable, "scripts/recurrence_calibration.py", "--input", str(source),
         "--output-dir", str(out)],
        check=True,
        capture_output=True,
    )
    sweep = json.loads((out / "recurrence_sweep.json").read_text(encoding="utf-8"))
    default = next(row for row in sweep["sweep"] if row["is_product_default"])
    assert default["totals"] == {"clusters": 1, "recurring_2plus": 1, "recurring_3plus": 0}
    pairs = json.loads((out / "pair_sample.json").read_text(encoding="utf-8"))["pairs"]
    assert len(pairs) == 1 and pairs[0]["similarity"] > 0.99

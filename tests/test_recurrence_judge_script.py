from __future__ import annotations

import importlib.util
from pathlib import Path

_spec = importlib.util.spec_from_file_location("recurrence_judge", Path("scripts/recurrence_judge.py"))
judge_module = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(judge_module)


def test_verdict_parsing_and_scoring() -> None:
    assert judge_module.parse_verdict(" same.") == "same"
    assert judge_module.parse_verdict("DIFFERENT") == "different"
    assert judge_module.parse_verdict("Maybe") == "unparsed"
    pairs = [
        {"pair_id": "p1", "text_a": "a", "text_b": "a"},
        {"pair_id": "p2", "text_a": "a", "text_b": "b"},
    ]
    verdicts = judge_module.judge(pairs, lambda prompt: "SAME" if "Note A: a\nNote B: a" in prompt else "DIFFERENT")
    predictions = {k: v["verdict"] for k, v in verdicts.items()}
    scored = judge_module._confusion(predictions, {"p1": "same", "p2": "different"})
    assert scored == {"same_recognized": "1/1", "different_wrongly_merged": "0/1", "unparsed": 0, "accuracy": 1.0}

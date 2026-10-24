from __future__ import annotations

import importlib.util
from pathlib import Path

from shadowseed.chat import ShadowChatSession

_spec = importlib.util.spec_from_file_location(
    "detector_calibration", Path("scripts/detector_calibration.py")
)
calibration = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(calibration)


class _Client:
    def __init__(self) -> None:
        self.prompts: list[str] = []

    def generate(self, prompt: str, max_new_tokens: int = 400) -> str:
        self.prompts.append(prompt)
        return (
            "1. Whether the deadline already includes the review period.\n"
            "2. Which cloud provider stores the backups.\n"
            "3. Backup Location"
        )


def test_paired_run_keeps_candidate_out_of_the_session() -> None:
    session = ShadowChatSession(backend="fixture")
    session.detector.client = _Client()
    conversation = {
        "id": "C1",
        "turns": [{"question": "How should we back up Office files?"}],
    }

    result = calibration.run_conversation(conversation, session, max_new_tokens=50)

    turn = result["turns"][0]
    assert "How should we back up Office files?" in session.detector.client.prompts[0]
    assert turn["candidate"]["admitted"] == ["Which cloud provider stores the backups."]
    assert turn["candidate"]["example_leaks"] == [
        "Whether the deadline already includes the review period."
    ]
    # Seeds in the session come from the product detector only.
    assert all(
        "cloud provider" not in seed.text for seed in session.manager.seeds.values()
    )

    items, key = calibration.review_sample([result], cap=60, seed=1)
    assert {key[item["id"]] for item in items} <= {"product", "candidate"}
    assert all(
        set(item)
        == {"id", "conversation_id", "turn", "question", "answer", "candidate"}
        for item in items
    )
    summary = calibration.summarize([result])
    assert summary["candidate"]["admitted"] == 1
    assert summary["candidate"]["example_leaks"] == 1


def _turn(arm_seeds: dict[str, list[str]]) -> dict:
    return {
        "turn": 0,
        "question": "q",
        "answer": "a",
        **{arm: {"admitted": seeds} for arm, seeds in arm_seeds.items()},
    }


def test_sample_caps_each_prompt_separately() -> None:
    conversation = {
        "conversation_id": "C1",
        "turns": [
            _turn({"product": [f"p{i}"], "candidate": [f"c{i}a", f"c{i}b"]})
            for i in range(40)
        ],
    }
    for index, turn in enumerate(conversation["turns"]):
        turn["turn"] = index
    items, key = calibration.review_sample([conversation], cap=60, seed=7)
    arms = [key[item["id"]] for item in items]
    assert arms.count("product") == 40
    assert arms.count("candidate") == 60
    again, _ = calibration.review_sample([conversation], cap=60, seed=7)
    assert [item["id"] for item in again] == [item["id"] for item in items]

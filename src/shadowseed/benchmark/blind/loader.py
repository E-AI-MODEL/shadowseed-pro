"""Load public blind scenarios and private evaluator labels."""

from __future__ import annotations

import json
from pathlib import Path

from shadowseed.benchmark.blind.schemas import BlindScenario, HiddenLabel


class BlindBenchmarkInputError(ValueError):
    """Raised when a blind benchmark input file is malformed."""


def load_public_suite(path: str | Path) -> tuple[str | None, list[BlindScenario]]:
    """Load the public benchmark suite.

    The public suite contains only scenario text and optional baseline answers.
    It must not contain evaluator labels such as expected_gaps.
    """
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    scenarios = payload.get("scenarios")
    if not isinstance(scenarios, list):
        raise BlindBenchmarkInputError("Public blind suite must contain a scenarios list.")

    forbidden_keys = {"expected_gaps", "must_not_add", "labels", "ground_truth_seeds"}
    for scenario in scenarios:
        overlap = forbidden_keys & set(scenario)
        if overlap:
            raise BlindBenchmarkInputError(
                f"Public scenario {scenario.get('id', '<unknown>')} contains private keys: {sorted(overlap)}"
            )

    return payload.get("version"), [BlindScenario.from_dict(item) for item in scenarios]


def load_hidden_labels(path: str | Path) -> tuple[str | None, dict[str, HiddenLabel]]:
    """Load hidden labels for scoring.

    The detector and runner should only pass this data into the scorer phase.
    """
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    labels = payload.get("labels")
    if not isinstance(labels, list):
        raise BlindBenchmarkInputError("Hidden label file must contain a labels list.")

    label_by_id = {}
    for item in labels:
        label = HiddenLabel.from_dict(item)
        if not label.expected_gaps:
            raise BlindBenchmarkInputError(f"Hidden label {label.scenario_id} has no expected_gaps.")
        label_by_id[label.scenario_id] = label
    return payload.get("version"), label_by_id

"""Result schemas for benchmark reporting."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone


REQUIRED_RESULT_FIELDS = [
    "benchmark_name",
    "run_type",
    "execution_status",
    "ssl_input_basis",
    "host_platform",
    "dataset_status",
    "runner_status",
    "score",
    "score_type",
    "interpretation",
    "limitations",
    "execution_gap",
    "timestamp",
]


@dataclass
class BenchmarkResult:
    benchmark_name: str
    run_type: str
    execution_status: str
    ssl_input_basis: list[str]
    host_platform: str
    dataset_status: str
    runner_status: str
    score: float | int | None
    score_type: str
    interpretation: str
    limitations: list[str]
    execution_gap: bool
    timestamp: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )

    def to_dict(self) -> dict:
        payload = asdict(self)
        missing = [
            field_name
            for field_name in REQUIRED_RESULT_FIELDS
            if field_name not in payload
        ]
        if missing:
            raise ValueError(f"Result payload is missing required fields: {missing}")
        return payload

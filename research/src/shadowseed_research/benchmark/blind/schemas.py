"""Schemas for blind benchmark inputs and outputs."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field


@dataclass(frozen=True)
class BlindScenario:
    """Public scenario data. This is the only scenario content the detector may read."""

    id: str
    domain: str
    input: str
    baseline_answer: str | None = None
    metadata: dict = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: dict) -> "BlindScenario":
        return cls(
            id=data["id"],
            domain=data["domain"],
            input=data["input"],
            baseline_answer=data.get("baseline_answer"),
            metadata=data.get("metadata", {}),
        )


@dataclass(frozen=True)
class HiddenLabel:
    """Private evaluator labels. These may only be loaded by the scorer."""

    scenario_id: str
    expected_gaps: list[str]
    must_not_add: list[str] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: dict) -> "HiddenLabel":
        return cls(
            scenario_id=data["id"],
            expected_gaps=list(data.get("expected_gaps", [])),
            must_not_add=list(data.get("must_not_add", [])),
        )


@dataclass(frozen=True)
class BlindScore:
    baseline_gap_coverage: float
    ssl_gap_coverage: float
    coverage_delta: float
    unsupported_additions: int
    false_positive_count: int
    net_benefit: float
    matched_expected_gaps: list[str]
    matched_unsupported_additions: list[str]

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass(frozen=True)
class BlindScenarioResult:
    scenario_id: str
    domain: str
    detected_by_turn: list[list[str]]
    candidate_seed_count: int
    promoted_seed_count: int
    score: BlindScore
    ssl_state: dict

    def to_dict(self) -> dict:
        data = asdict(self)
        data["score"] = self.score.to_dict()
        return data

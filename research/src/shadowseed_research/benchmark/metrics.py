"""Reusable benchmark metrics."""

from __future__ import annotations

from dataclasses import asdict, dataclass


@dataclass
class Metrics:
    true_positive: int = 0
    false_positive: int = 0
    true_negative: int = 0
    false_negative: int = 0

    def update(self, prediction: bool, expected: bool) -> None:
        if prediction and expected:
            self.true_positive += 1
        elif prediction and not expected:
            self.false_positive += 1
        elif not prediction and expected:
            self.false_negative += 1
        else:
            self.true_negative += 1

    @property
    def precision(self) -> float:
        denom = self.true_positive + self.false_positive
        return self.true_positive / denom if denom else 0.0

    @property
    def recall(self) -> float:
        denom = self.true_positive + self.false_negative
        return self.true_positive / denom if denom else 0.0

    @property
    def f1(self) -> float:
        denom = self.precision + self.recall
        return (2 * self.precision * self.recall / denom) if denom else 0.0

    @property
    def accuracy(self) -> float:
        total = self.true_positive + self.false_positive + self.true_negative + self.false_negative
        return (self.true_positive + self.true_negative) / total if total else 0.0

    def to_dict(self) -> dict:
        data = asdict(self)
        data.update(
            {
                "precision": self.precision,
                "recall": self.recall,
                "f1": self.f1,
                "accuracy": self.accuracy,
            }
        )
        return data

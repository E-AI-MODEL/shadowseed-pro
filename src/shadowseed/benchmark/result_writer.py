"""Writers for benchmark preparation and result files."""

from __future__ import annotations

import json
from pathlib import Path

from .schemas import BenchmarkResult, REQUIRED_RESULT_FIELDS


class ResultWriter:
    def __init__(self, root: str | Path = "benchmarks/results"):
        self.root = Path(root)

    def write_result(self, result: BenchmarkResult, relative_path: str) -> Path:
        payload = result.to_dict()
        self._validate_payload(payload)
        destination = self.root / relative_path
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(
            json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        return destination

    def write_payload(self, payload: dict, relative_path: str) -> Path:
        self._validate_payload(payload)
        destination = self.root / relative_path
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(
            json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        return destination

    def _validate_payload(self, payload: dict) -> None:
        missing = [
            field_name
            for field_name in REQUIRED_RESULT_FIELDS
            if field_name not in payload
        ]
        if missing:
            raise ValueError(f"Result payload is missing required fields: {missing}")

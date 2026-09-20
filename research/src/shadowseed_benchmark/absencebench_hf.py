"""Small Hugging Face adapter for AbsenceBench.

This module avoids heavyweight dependencies. It uses the public Hugging Face
Datasets Server rows endpoint and writes a compact local JSON file that the
existing local runner can score.
"""

from __future__ import annotations

import json
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import urlopen

DATASET = "harveyfin/AbsenceBench"
DEFAULT_CONFIG = "github_prs"
DEFAULT_SPLIT = "validation"
ROWS_ENDPOINT = "https://datasets-server.huggingface.co/rows"


def fetch_absencebench_sample(
    output_path: str,
    config: str = DEFAULT_CONFIG,
    split: str = DEFAULT_SPLIT,
    limit: int = 10,
    offset: int = 0,
) -> Path:
    if limit < 1:
        raise ValueError("limit must be at least 1")
    if limit > 100:
        raise ValueError("limit must be at most 100 for a lightweight sample")

    query = urlencode(
        {
            "dataset": DATASET,
            "config": config,
            "split": split,
            "offset": offset,
            "length": limit,
        }
    )
    url = f"{ROWS_ENDPOINT}?{query}"

    with urlopen(url, timeout=30) as response:
        payload = json.loads(response.read().decode("utf-8"))

    rows = payload.get("rows", [])
    scenarios = []
    for item in rows:
        row = item.get("row", {})
        omitted = row.get("omitted_context") or []
        scenarios.append(
            {
                "id": str(row.get("id", item.get("row_idx", len(scenarios)))),
                "original_context": row.get("original_context", ""),
                "modified_context": row.get("modified_context", ""),
                "omitted_context": omitted,
                "omitted_index": row.get("omitted_index", []),
                "metadata": row.get("metadata", {}),
                "detected": bool(omitted),
            }
        )

    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(
            {
                "source": DATASET,
                "config": config,
                "split": split,
                "offset": offset,
                "limit": limit,
                "scenarios": scenarios,
            },
            indent=2,
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )
    return output

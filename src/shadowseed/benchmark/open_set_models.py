"""Curated registry of free Hugging Face instruct models for SSL test routes.

The registry (`src/shadowseed/data/open_set_models.json`) is the single source
of truth for which models the model-detector and SLM-benefit routes are known
to work with, plus their size, license and whether they fit a standard CPU
runner. The workflows expose the ungated cpu_runner_ok ids as a dropdown and
accept any other id as a custom override; this module backs the
`list-open-set-models` CLI command and a light validation helper.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


DEFAULT_REGISTRY = "src/shadowseed/data/open_set_models.json"


def load_models(registry_path: str = DEFAULT_REGISTRY) -> list[dict[str, Any]]:
    data = json.loads(Path(registry_path).read_text(encoding="utf-8"))
    return list(data.get("models", []))


def find_model(model_id: str, registry_path: str = DEFAULT_REGISTRY) -> dict[str, Any] | None:
    target = (model_id or "").strip()
    for model in load_models(registry_path):
        if model.get("id") == target:
            return model
    return None


def dropdown_ids(registry_path: str = DEFAULT_REGISTRY) -> list[str]:
    """Ids safe to offer as a no-token dropdown: ungated and CPU-runner-ok."""
    return [
        m["id"]
        for m in load_models(registry_path)
        if not m.get("gated", False) and m.get("cpu_runner_ok", False)
    ]


def format_table(registry_path: str = DEFAULT_REGISTRY) -> str:
    models = sorted(load_models(registry_path), key=lambda m: m.get("params_b", 0.0))
    lines = [
        f"{'model_id':45} {'B':>5} {'RAM':>5} {'gated':>5} {'cpu':>4}  license",
        "-" * 100,
    ]
    for m in models:
        lines.append(
            f"{m['id']:45} {m.get('params_b', 0):>5} {m.get('approx_ram_gb', 0):>5} "
            f"{('yes' if m.get('gated') else 'no'):>5} "
            f"{('ok' if m.get('cpu_runner_ok') else 'no'):>4}  {m.get('license', '?')}"
        )
    lines.append("")
    lines.append("Dropdown (ungated + cpu_runner_ok): " + ", ".join(dropdown_ids(registry_path)))
    return "\n".join(lines)


def run_list_open_set_models(
    output_path: str | None = None,
    registry_path: str = DEFAULT_REGISTRY,
) -> str:
    table = format_table(registry_path)
    if output_path:
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        Path(output_path).write_text(table + "\n", encoding="utf-8")
        return output_path
    return table

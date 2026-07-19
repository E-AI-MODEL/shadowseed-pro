"""Tests for the curated open-set model registry and its workflow wiring."""

from __future__ import annotations

from pathlib import Path

from shadowseed.benchmark.open_set_models import (
    dropdown_ids,
    find_model,
    format_table,
    load_models,
)


def test_registry_loads_and_has_required_fields():
    models = load_models()
    assert models
    for m in models:
        assert m["id"]
        for key in ("params_b", "approx_ram_gb", "license", "gated", "cpu_runner_ok"):
            assert key in m, f"{m['id']} missing {key}"


def test_find_model_strips_whitespace():
    # the trailing-space crash class: lookup must tolerate stray whitespace
    assert find_model("Qwen/Qwen2.5-1.5B-Instruct ") is not None
    assert find_model("  Qwen/Qwen2.5-1.5B-Instruct") is not None
    assert find_model("nope/does-not-exist") is None


def test_dropdown_ids_are_ungated_and_cpu_ok():
    ids = dropdown_ids()
    assert ids
    by_id = {m["id"]: m for m in load_models()}
    for mid in ids:
        assert by_id[mid]["gated"] is False
        assert by_id[mid]["cpu_runner_ok"] is True


def test_format_table_renders():
    table = format_table()
    assert "model_id" in table
    assert "Dropdown" in table
    assert "Qwen/Qwen2.5-1.5B-Instruct" in table


def _workflow_model_choices(path: str) -> list[str]:
    """Extract the model_id input's dropdown options without a YAML dependency.

    Walks the workflow file line by line: after the `model_id:` input is seen,
    collect the bullet items under its `options:` block until the block ends.
    Earlier inputs (detector, model_backend) and the following model_id_custom
    input are ignored because collection only starts at model_id's options.
    """
    seen_model_id = False
    in_options = False
    opts: list[str] = []
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if stripped.startswith("model_id:"):
            seen_model_id = True
            in_options = False
            continue
        if seen_model_id and stripped == "options:":
            in_options = True
            continue
        if in_options:
            if stripped.startswith("- "):
                opts.append(stripped[2:].strip())
            else:
                break
    return opts


def test_open_set_workflow_dropdown_is_subset_of_registry():
    """Drift guard: every model offered in the open-set workflow dropdown must
    exist in the registry and be ungated + cpu_runner_ok."""
    choices = _workflow_model_choices(".github/workflows/open-set-hf-review.yml")
    assert choices
    by_id = {m["id"]: m for m in load_models()}
    for mid in choices:
        assert mid in by_id, f"{mid} not in registry"
        assert by_id[mid]["gated"] is False
        assert by_id[mid]["cpu_runner_ok"] is True


def test_slm_workflow_dropdown_is_subset_of_registry():
    choices = _workflow_model_choices(".github/workflows/slm-model-benefit.yml")
    assert choices
    by_id = {m["id"]: m for m in load_models()}
    for mid in choices:
        assert mid in by_id, f"{mid} not in registry"
        assert by_id[mid]["gated"] is False
        assert by_id[mid]["cpu_runner_ok"] is True

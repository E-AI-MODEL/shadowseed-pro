from __future__ import annotations

import ast
from pathlib import Path

import pytest

from shadowseed.workbench.app import _seed_story_markdown, launch_workbench
from shadowseed.workbench.controller import WorkbenchController


REQUIRED_PRODUCT_FILES = (
    "src/shadowseed/workbench/app.py",
    "src/shadowseed/workbench/controller.py",
    "src/shadowseed/application/inspection.py",
    "src/shadowseed/application/feedback.py",
    "src/shadowseed/application/scenarios.py",
    "src/shadowseed/application/comparison.py",
)


def test_workbench_product_files_are_normal_source_files() -> None:
    for path in REQUIRED_PRODUCT_FILES:
        file = Path(path)
        assert file.is_file(), path
        assert file.stat().st_size > 100, path


def test_workbench_ui_does_not_import_runtime_authority_modules() -> None:
    forbidden = {
        "shadowseed.manager",
        "shadowseed.gate",
        "shadowseed.gate.runtime_adapter",
        "shadowseed.lifecycle",
    }
    for path in Path("src/shadowseed/workbench").glob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        imports: set[str] = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imports.update(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imports.add(node.module)
        assert not any(
            imported == denied or imported.startswith(f"{denied}.")
            for imported in imports
            for denied in forbidden
        ), f"{path} crosses Workbench authority boundary: {sorted(imports & forbidden)}"


def test_remote_binding_requires_explicit_opt_in(tmp_path) -> None:
    with pytest.raises(ValueError, match="remote Workbench binding is disabled"):
        launch_workbench(
            tmp_path / "workspace",
            host="0.0.0.0",
            allow_remote=False,
            inbrowser=False,
        )


def test_gradio_app_builds_when_optional_dependency_is_installed(tmp_path) -> None:
    pytest.importorskip("gradio")
    from shadowseed.workbench.app import build_app

    app = build_app(tmp_path / "workspace")
    assert app is not None


def test_gradio_evidence_submission_resets_operator_attestation(tmp_path) -> None:
    pytest.importorskip("gradio")
    from shadowseed.workbench.app import build_app

    controller = WorkbenchController(tmp_path / "workspace")
    session_id = controller.create_session(
        title="Evidence reset",
        profile_id="demo",
        backend="fixture",
        runtime_mode="live",
    )
    result = controller.send_turn(session_id, "What is missing from this privacy plan?")
    seed_id = result["session"]["seeds"][0]["id"]
    app = build_app(controller=controller)
    callback = next(
        dependency.fn
        for dependency in app.fns.values()
        if getattr(dependency.fn, "__name__", "") == "submit_verified_evidence"
    )

    outputs = callback(
        session_id,
        seed_id,
        "reviewer:one",
        "Checked against an independent source.",
        True,
    )

    assert outputs[-2:] == ("", False)


def test_seed_story_explains_promoted_without_forcing_action() -> None:
    story = _seed_story_markdown(
        {
            "id": "ss_001",
            "text": "A missing long-term perspective.",
            "status": "PROMOTED",
            "evidence_count": 3,
            "occurrence_count": 2,
            "weight": 0.6,
            "trace": 1.2,
            "blocking": False,
            "last_gate_event": {"decision": "promoted"},
            "plain_explanation": "Promoted by the Validation Gate.",
            "timeline": [],
        }
    )

    assert "PROMOTED" in story
    assert "A missing long-term perspective." in story
    assert "Evidence 3" in story
    assert "Nothing required right now." in story
    assert "Raw" not in story


def test_seed_story_surfaces_blocking_contradiction_as_next_action() -> None:
    story = _seed_story_markdown(
        {
            "text": "Candidate perspective",
            "status": "CONTRADICTED",
            "blocking": True,
            "plain_explanation": "Contradicted and blocked.",
            "timeline": [],
        }
    )

    assert "Needs attention" in story
    assert "contradiction" in story.lower()

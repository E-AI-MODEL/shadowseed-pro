from __future__ import annotations

import ast
from pathlib import Path

import pytest

from shadowseed.workbench.app import (
    _authority_profile_markdown,
    _control_overview_markdown,
    _ingest_summary_markdown,
    _seed_story_markdown,
    _shadow_overview_markdown,
    _status_markdown,
    launch_workbench,
)
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


def test_authority_profile_explainer_makes_control_model_visible() -> None:
    profiles = [
        {
            "id": "strict",
            "label": "Controlled",
            "description": "User-controlled validation.",
            "validate_mode": "manual",
            "promote_mode": "gate_after_manual_validation",
            "contradiction_mode": "block_and_manual_resolution",
        },
        {
            "id": "autonomous",
            "label": "Autonomous",
            "description": "Automatic lifecycle where policy allows.",
            "validate_mode": "auto",
            "promote_mode": "gate",
            "contradiction_mode": "block_and_auto_check",
        },
    ]

    strict = _authority_profile_markdown("strict", profiles)
    autonomous = _authority_profile_markdown("autonomous", profiles)

    assert "Controlled" in strict
    assert "Validate: **manual**" in strict
    assert "gate after manual validation" in strict
    assert "Autonomous" in autonomous
    assert "Validate: **auto**" in autonomous
    assert "Promote: **gate**" in autonomous



def test_ingest_summary_explains_corpus_result() -> None:
    empty = _ingest_summary_markdown(None)
    assert "Feed the shadow memory" in empty

    error = _ingest_summary_markdown({"error": "bad upload"})
    assert "Could not process sources" in error

    summary = _ingest_summary_markdown(
        {
            "sources": 2,
            "chunks": 7,
            "characters": 12345,
            "seeds_before": 3,
            "seeds_after": 11,
            "new_seed_count": 8,
            "source_names": ["a.md", "b.csv"],
        }
    )
    assert "2** source(s)" in summary
    assert "7** chunks" in summary
    assert "3 → 11" in summary
    assert "a.md, b.csv" in summary
    assert "not trusted evidence" in summary


def test_shadow_overview_summarizes_lifecycle_and_usage() -> None:
    text = _shadow_overview_markdown(
        {
            "authority_profile_id": "autonomous",
            "seeds": [
                {"id": "ss_1", "status": "PROMOTED", "blocking": False},
                {"id": "ss_2", "status": "ACTIVE", "blocking": True},
            ],
            "turn_reports": [
                {"surfaced_seed_ids": ["ss_1"]},
                {"surfaced_seed_ids": ["ss_1"]},
            ],
        }
    )
    assert "autonomous" in text
    assert "Seeds:** 2" in text
    assert "Promoted:** 1" in text
    assert "Used:** 1" in text
    assert "Blocked:** 1" in text

    assert "Select a run" in _shadow_overview_markdown(None)



def test_control_overview_explains_effective_runtime_policy() -> None:
    profiles = [
        {
            "id": "assisted",
            "label": "Assisted",
            "description": "Review mature recurrence.",
            "auto_validate_recurrence": True,
            "allow_unreviewed_system_evidence": False,
        },
        {
            "id": "autonomous",
            "label": "Autonomous",
            "description": "Automatic recurrence authority.",
            "auto_validate_recurrence": True,
            "allow_unreviewed_system_evidence": False,
        },
    ]

    assisted = _control_overview_markdown(
        {
            "authority_profile_id": "assisted",
            "effective_gate_policy_id": "evidence_backed",
            "authority_review_seed_ids": ["ss_1", "ss_2"],
        },
        profiles,
    )
    autonomous = _control_overview_markdown(
        {
            "authority_profile_id": "autonomous",
            "effective_gate_policy_id": "exploratory",
            "authority_review_seed_ids": [],
        },
        profiles,
    )

    assert "Assisted" in assisted
    assert "evidence_backed" in assisted
    assert "cannot raise authority by itself" in assisted
    assert "2" in assisted
    assert "Autonomous" in autonomous
    assert "exploratory" in autonomous
    assert "automatic authority path" in autonomous
    assert "Profile changes are run-level decisions" in autonomous



def test_status_markdown_shows_effective_gate_and_review_count() -> None:
    assert "Create or open" in _status_markdown(None)

    status = _status_markdown(
        {
            "runtime_mode": "live",
            "backend": "fixture",
            "authority_profile_id": "assisted",
            "effective_gate_policy_id": "evidence_backed",
            "authority_review_seed_ids": ["ss_1", "ss_2"],
            "turn": 4,
            "seeds": [
                {"status": "PROMOTED"},
                {"status": "ACTIVE"},
            ],
        }
    )

    assert "Live SSL" in status
    assert "assisted" in status
    assert "evidence_backed" in status
    assert "4 turns" in status
    assert "2 shadow seeds" in status
    assert "1 promoted" in status
    assert "2 need review" in status

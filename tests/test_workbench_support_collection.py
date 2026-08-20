from __future__ import annotations

import json
import zipfile
from pathlib import Path

import pytest

from shadowseed.application.exports import ExportService
from shadowseed.application.sessions import service_for_workspace
from shadowseed.support_collection import (
    SUPPORT_DATASET_SCHEMA,
    SupportCollectionError,
    collect_support_bundles,
    write_support_dataset,
)


def _bundle(tmp_path: Path, name: str) -> Path:
    workspace = tmp_path / f"workspace-{name}"
    sessions = service_for_workspace(workspace)
    session_id = sessions.create_session(
        title=f"private {name}",
        profile_id="demo",
        backend="fixture",
    )
    sessions.run_turn(session_id, f"private question {name}")
    return ExportService(sessions, workspace_root=workspace).export_support_bundle(
        session_id,
        tmp_path / f"{name}.zip",
    )


def test_collects_verified_support_bundles_without_free_text(tmp_path) -> None:
    first = _bundle(tmp_path, "a")
    second = _bundle(tmp_path, "b")

    payload = collect_support_bundles(
        [second, first],
        collection_id="pilot-2026-08",
    )

    assert payload["schema"] == SUPPORT_DATASET_SCHEMA
    assert payload["collection_id"] == "pilot-2026-08"
    assert payload["bundle_count"] == 2
    assert len(payload["records"]) == 2
    assert payload["records"] == sorted(
        payload["records"], key=lambda item: item["support_session_id"]
    )
    serialized = json.dumps(payload)
    assert "private question" not in serialized
    assert "private a" not in serialized
    assert "private b" not in serialized
    assert all(len(record["bundle_sha256"]) == 64 for record in payload["records"])


def test_duplicate_support_session_is_rejected(tmp_path) -> None:
    bundle = _bundle(tmp_path, "duplicate")

    with pytest.raises(SupportCollectionError, match="duplicate support session"):
        collect_support_bundles(
            [bundle, bundle],
            collection_id="duplicate-check",
        )


def test_full_report_is_not_accepted_as_collection_input(tmp_path) -> None:
    workspace = tmp_path / "workspace-report"
    sessions = service_for_workspace(workspace)
    session_id = sessions.create_session(
        title="private report",
        profile_id="demo",
        backend="fixture",
    )
    sessions.run_turn(session_id, "private report question")
    report = ExportService(sessions, workspace_root=workspace).export_report(
        session_id,
        tmp_path / "report.zip",
    )

    with pytest.raises(SupportCollectionError, match="not a support bundle"):
        collect_support_bundles([report], collection_id="report-reject")


def test_tampered_support_bundle_is_rejected(tmp_path) -> None:
    bundle = _bundle(tmp_path, "tampered")
    with zipfile.ZipFile(bundle, "r") as archive:
        files = {name: archive.read(name) for name in archive.namelist()}
    files["support.json"] = b'{"support_session_id":"support::tampered"}\n'
    with zipfile.ZipFile(bundle, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for name, content in files.items():
            archive.writestr(name, content)

    with pytest.raises(Exception, match="mismatch"):
        collect_support_bundles([bundle], collection_id="tamper-reject")


def test_dataset_write_is_json_and_contains_collection_identity(tmp_path) -> None:
    bundle = _bundle(tmp_path, "write")
    output = write_support_dataset(
        [bundle],
        collection_id="study-01",
        output=tmp_path / "dataset.json",
    )

    payload = json.loads(output.read_text(encoding="utf-8"))
    assert payload["schema"] == SUPPORT_DATASET_SCHEMA
    assert payload["collection_id"] == "study-01"
    assert payload["bundle_count"] == 1

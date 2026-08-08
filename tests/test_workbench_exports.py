from __future__ import annotations

import json
import stat
import zipfile
from pathlib import Path

import pytest

from shadowseed.application.exports import (
    ExportService,
    ExportVerificationError,
    redact_private_data,
    verify_workbench_export,
)
from shadowseed.application.feedback import FeedbackService
from shadowseed.application.sessions import service_for_workspace


def _session(tmp_path: Path) -> tuple[ExportService, str, Path]:
    workspace = tmp_path / "workspace"
    sessions = service_for_workspace(workspace)
    session_id = sessions.create_session(
        title="Private tester title",
        profile_id="demo",
        backend="fixture",
    )
    sessions.run_turn(session_id, "Private question with https://example.test as text")
    FeedbackService(sessions).record(
        session_id=session_id,
        turn_index=0,
        overall="better",
        seed_effect="no_visible_effect",
        note="Private tester note",
    )
    return ExportService(sessions, workspace_root=workspace), session_id, workspace


def _read_zip(path: Path) -> dict[str, bytes]:
    with zipfile.ZipFile(path) as archive:
        return {name: archive.read(name) for name in archive.namelist()}


def _rewrite_zip(path: Path, files: dict[str, bytes]) -> None:
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for name, payload in files.items():
            archive.writestr(name, payload)


def test_full_report_is_self_contained_and_verifiable(tmp_path) -> None:
    exports, session_id, _workspace = _session(tmp_path)
    target = exports.export_report(session_id, tmp_path / "report.zip")

    result = verify_workbench_export(target)
    files = _read_zip(target)

    assert result["valid"] is True
    assert result["kind"] == "report"
    assert {
        "manifest.json",
        "report.html",
        "environment.json",
        "config.json",
        "session.json",
        "messages.json",
        "seeds.json",
        "gate-events.json",
        "influence-events.json",
        "tester-feedback.csv",
    } == set(files)
    html = files["report.html"].decode("utf-8")
    assert "Private tester title" in html
    assert "https://example.test" in html
    assert '<script src="http' not in html.lower()


def test_support_bundle_omits_free_text_and_direct_session_identity(tmp_path) -> None:
    exports, session_id, _workspace = _session(tmp_path)
    target = exports.export_support_bundle(session_id, tmp_path / "support.zip")

    result = verify_workbench_export(target)
    files = _read_zip(target)
    combined = b"\n".join(files.values()).decode("utf-8", errors="replace")

    assert result["kind"] == "support"
    assert set(files) == {"manifest.json", "environment.json", "config.json", "support.json"}
    assert session_id not in combined
    assert "Private tester title" not in combined
    assert "Private question" not in combined
    assert "Private tester note" not in combined
    assert "support::" in combined


def test_recursive_redaction_removes_secrets_and_local_paths(tmp_path) -> None:
    workspace = tmp_path / "private" / "workspace"
    data = {
        "api_key": "sk-example",
        "nested": {
            "password": "secret-value",
            "cache_path": str(workspace / "cache"),
            "message": f"loaded from {workspace}/models/model.bin",
        },
        "windows_path": r"C:\\Users\\Tester\\secret.txt",
    }

    redacted = redact_private_data(data, workspace_root=workspace)
    serialized = json.dumps(redacted)

    assert "sk-example" not in serialized
    assert "secret-value" not in serialized
    assert str(workspace) not in serialized
    assert r"C:\\Users\\Tester" not in serialized
    assert "<redacted-secret>" in serialized
    assert "<local-path>" in serialized


def test_verifier_rejects_tampered_hash(tmp_path) -> None:
    exports, session_id, _workspace = _session(tmp_path)
    target = exports.export_report(session_id, tmp_path / "report.zip")
    files = _read_zip(target)
    files["session.json"] = b'{"tampered":true}\n'
    _rewrite_zip(target, files)

    with pytest.raises(ExportVerificationError, match="mismatch"):
        verify_workbench_export(target)


def test_verifier_rejects_extra_and_traversal_files(tmp_path) -> None:
    exports, session_id, _workspace = _session(tmp_path)
    target = exports.export_report(session_id, tmp_path / "report.zip")
    files = _read_zip(target)
    files["extra.txt"] = b"unexpected"
    _rewrite_zip(target, files)
    with pytest.raises(ExportVerificationError, match="do not match"):
        verify_workbench_export(target)

    traversal = tmp_path / "traversal.zip"
    with zipfile.ZipFile(traversal, "w") as archive:
        archive.writestr("../escape.txt", "bad")
        archive.writestr("manifest.json", "{}")
    with pytest.raises(ExportVerificationError, match="unsafe filename"):
        verify_workbench_export(traversal)

    windows = tmp_path / "windows-traversal.zip"
    with zipfile.ZipFile(windows, "w") as archive:
        archive.writestr(r"..\\escape.txt", "bad")
        archive.writestr("manifest.json", "{}")
    with pytest.raises(ExportVerificationError, match="unsafe filename"):
        verify_workbench_export(windows)


def test_verifier_rejects_duplicate_and_symlink_entries(tmp_path) -> None:
    duplicate = tmp_path / "duplicate.zip"
    with zipfile.ZipFile(duplicate, "w") as archive:
        archive.writestr("manifest.json", "{}")
        archive.writestr("manifest.json", "{}")
    with pytest.raises(ExportVerificationError, match="duplicate"):
        verify_workbench_export(duplicate)

    symlink = tmp_path / "symlink.zip"
    link = zipfile.ZipInfo("link")
    link.create_system = 3
    link.external_attr = (stat.S_IFLNK | 0o777) << 16
    with zipfile.ZipFile(symlink, "w") as archive:
        archive.writestr(link, "target")
        archive.writestr("manifest.json", "{}")
    with pytest.raises(ExportVerificationError, match="symlink"):
        verify_workbench_export(symlink)


def test_verifier_rejects_external_html_resources(tmp_path) -> None:
    exports, session_id, _workspace = _session(tmp_path)
    target = exports.export_report(session_id, tmp_path / "report.zip")
    files = _read_zip(target)
    files["report.html"] = b'<img src="https://tracker.example/image.png">'
    manifest = json.loads(files["manifest.json"])
    for entry in manifest["files"]:
        if entry["name"] == "report.html":
            import hashlib

            entry["size"] = len(files["report.html"])
            entry["sha256"] = hashlib.sha256(files["report.html"]).hexdigest()
    files["manifest.json"] = (json.dumps(manifest) + "\n").encode()
    _rewrite_zip(target, files)

    with pytest.raises(ExportVerificationError, match="external or embedded resource"):
        verify_workbench_export(target)


def test_export_replacement_is_atomic_when_verification_fails(tmp_path, monkeypatch) -> None:
    exports, session_id, _workspace = _session(tmp_path)
    target = tmp_path / "report.zip"
    target.write_bytes(b"existing-valid-placeholder")

    def fail(_path: Path) -> dict[str, object]:
        raise ExportVerificationError("forced verification failure")

    monkeypatch.setattr("shadowseed.application.exports.verify_workbench_export", fail)
    with pytest.raises(ExportVerificationError, match="forced"):
        exports.export_report(session_id, target)

    assert target.read_bytes() == b"existing-valid-placeholder"
    assert not list(tmp_path.glob(".report.zip.*.tmp"))

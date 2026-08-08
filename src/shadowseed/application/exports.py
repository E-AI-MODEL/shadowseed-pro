"""Verifiable Workbench report and privacy-minimized support exports."""

from __future__ import annotations

import csv
import hashlib
import html
import io
import json
import os
import platform
import re
import stat
import tempfile
import zipfile
from collections import Counter
from datetime import datetime, timezone
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path, PurePosixPath, PureWindowsPath
from typing import Any
from uuid import uuid4

from shadowseed.application.sessions import SessionService


EXPORT_FORMAT_VERSION = 1
MAX_BUNDLE_FILES = 64
MAX_FILE_BYTES = 10 * 1024 * 1024
MAX_TOTAL_BYTES = 50 * 1024 * 1024
MAX_COMPRESSION_RATIO = 200
_SECRET_FRAGMENTS = (
    "api_key",
    "apikey",
    "access_token",
    "auth_token",
    "secret",
    "password",
    "credential",
)
_EXTERNAL_RESOURCE_RE = re.compile(
    r"(?:src|href)\s*=\s*[\"']\s*(?:https?:)?//", re.IGNORECASE
)
_FORBIDDEN_HTML_TAG_RE = re.compile(
    r"<(?:base|iframe|object|embed)\b", re.IGNORECASE
)


class ExportVerificationError(RuntimeError):
    """Raised when a Workbench export is malformed, unsafe, or tampered with."""


def _json_bytes(value: Any) -> bytes:
    return (
        json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n"
    ).encode("utf-8")


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _package_version() -> str:
    try:
        return version("shadowseed")
    except PackageNotFoundError:  # pragma: no cover - editable source fallback
        return "0+unknown"


def _is_absolute_path(value: str) -> bool:
    if not value:
        return False
    try:
        if PurePosixPath(value).is_absolute() or PureWindowsPath(value).is_absolute():
            return True
    except (TypeError, ValueError):
        return False
    return False


def redact_private_data(
    value: Any,
    *,
    workspace_root: str | Path | None = None,
    key_name: str = "",
) -> Any:
    """Recursively redact secret-like values and local absolute paths."""

    lowered = key_name.lower()
    if any(fragment in lowered for fragment in _SECRET_FRAGMENTS):
        return "<redacted-secret>" if value not in (None, "") else value
    if isinstance(value, dict):
        return {
            str(key): redact_private_data(
                item,
                workspace_root=workspace_root,
                key_name=str(key),
            )
            for key, item in value.items()
        }
    if isinstance(value, (list, tuple)):
        return [
            redact_private_data(item, workspace_root=workspace_root)
            for item in value
        ]
    if not isinstance(value, str):
        return value

    root = str(Path(workspace_root).expanduser().resolve()) if workspace_root else ""
    home = str(Path.home().expanduser().resolve())
    result = value
    for private_prefix in (root, home):
        if private_prefix and private_prefix in result:
            result = result.replace(private_prefix, "<local-path>")
    if _is_absolute_path(result):
        return "<local-path>"
    return result


def _environment_payload() -> dict[str, Any]:
    return {
        "shadowseed_version": _package_version(),
        "python_version": platform.python_version(),
        "python_implementation": platform.python_implementation(),
        "system": platform.system(),
        "system_release": platform.release(),
        "machine": platform.machine(),
    }


def _messages_payload(state: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        {
            "turn": int(report.get("turn", index)),
            "question": str(report.get("question", "")),
            "answer": str(report.get("answer", "")),
            "baseline_answer": str(report.get("baseline_answer", "")),
            "ssl_answer": str(report.get("ssl_answer", "")),
            "surfaced_seed_ids": list(report.get("surfaced_seed_ids", [])),
        }
        for index, report in enumerate(state.get("turn_reports", []))
    ]


def _feedback_csv(feedback: list[Any]) -> bytes:
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(
        stream,
        fieldnames=[
            "feedback_id",
            "turn_index",
            "seed_id",
            "overall",
            "seed_effect",
            "note",
            "action",
            "created_at",
        ],
    )
    writer.writeheader()
    for item in feedback:
        data = item.to_dict()
        writer.writerow({key: data.get(key, "") for key in writer.fieldnames})
    return stream.getvalue().encode("utf-8")


def _report_html(
    *,
    session: dict[str, Any],
    state: dict[str, Any],
    feedback_count: int,
) -> bytes:
    manager = state.get("manager", {})
    rows: list[str] = []
    for index, report in enumerate(state.get("turn_reports", [])):
        turn = int(report.get("turn", index))
        question = html.escape(str(report.get("question", "")))
        answer = html.escape(str(report.get("answer", "")))
        rows.append(
            "<article><h3>Turn "
            f"{turn}</h3><p><strong>Question</strong></p><pre>{question}</pre>"
            f"<p><strong>Answer</strong></p><pre>{answer}</pre></article>"
        )
    body = "".join(rows) or "<p>No turns recorded.</p>"
    document = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Shadowseed Workbench report</title>
<style>
body{{font-family:system-ui,sans-serif;max-width:960px;margin:2rem auto;padding:0 1rem;line-height:1.5}}
pre{{white-space:pre-wrap;background:#f5f5f5;padding:1rem;border-radius:.5rem}}
article{{border-top:1px solid #ddd;padding:1rem 0}}
.meta{{display:grid;grid-template-columns:max-content 1fr;gap:.3rem 1rem}}
</style>
</head>
<body>
<h1>Shadowseed Workbench report</h1>
<p>This export is an auditable tester artifact, not a scientific result or production certification.</p>
<div class="meta">
<strong>Title</strong><span>{html.escape(str(session['title']))}</span>
<strong>Session</strong><span>{html.escape(str(session['session_id']))}</span>
<strong>Profile</strong><span>{html.escape(str(session['profile_id']))}</span>
<strong>Backend</strong><span>{html.escape(str(session['backend']))}</span>
<strong>Turns</strong><span>{len(state.get('turn_reports', []))}</span>
<strong>Seeds</strong><span>{len(manager.get('seeds', []))}</span>
<strong>Tester feedback</strong><span>{feedback_count}</span>
</div>
<h2>Conversation</h2>
{body}
</body>
</html>
"""
    return document.encode("utf-8")


def _safe_member_name(name: str) -> bool:
    if not name or "\x00" in name:
        return False
    posix = PurePosixPath(name)
    windows = PureWindowsPath(name)
    if posix.is_absolute() or windows.is_absolute() or windows.drive:
        return False
    if ".." in posix.parts or ".." in windows.parts:
        return False
    if name != posix.name or name != windows.name:
        return False
    return True


def verify_workbench_export(path: str | Path) -> dict[str, Any]:
    """Verify structure, integrity, resource locality, and size limits of a ZIP export."""

    bundle = Path(path).expanduser().resolve()
    if not bundle.is_file():
        raise ExportVerificationError(f"export does not exist: {bundle}")
    try:
        archive = zipfile.ZipFile(bundle, "r")
    except (OSError, zipfile.BadZipFile) as exc:
        raise ExportVerificationError("export is not a valid ZIP archive") from exc

    with archive:
        infos = archive.infolist()
        if len(infos) > MAX_BUNDLE_FILES:
            raise ExportVerificationError("export contains too many files")
        names = [info.filename for info in infos]
        if len(names) != len(set(names)):
            raise ExportVerificationError("export contains duplicate filenames")
        if any(not _safe_member_name(name) for name in names):
            raise ExportVerificationError("export contains an unsafe filename")
        total_size = 0
        for info in infos:
            if info.is_dir():
                raise ExportVerificationError("export may not contain directory entries")
            mode = (info.external_attr >> 16) & 0o170000
            if mode == stat.S_IFLNK:
                raise ExportVerificationError("export may not contain symlinks")
            if info.file_size > MAX_FILE_BYTES:
                raise ExportVerificationError(f"export file is too large: {info.filename}")
            total_size += info.file_size
            if total_size > MAX_TOTAL_BYTES:
                raise ExportVerificationError("export is too large")
            if info.file_size and info.compress_size == 0:
                raise ExportVerificationError("export contains an invalid compressed file")
            if info.compress_size and info.file_size / info.compress_size > MAX_COMPRESSION_RATIO:
                raise ExportVerificationError("export contains an unsafe compression ratio")

        if names.count("manifest.json") != 1:
            raise ExportVerificationError("export must contain exactly one manifest.json")
        try:
            manifest = json.loads(archive.read("manifest.json"))
        except (KeyError, UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise ExportVerificationError("manifest.json is invalid") from exc
        if manifest.get("format_version") != EXPORT_FORMAT_VERSION:
            raise ExportVerificationError("unsupported export format version")
        if manifest.get("kind") not in {"report", "support"}:
            raise ExportVerificationError("unsupported export kind")
        entries = manifest.get("files")
        if not isinstance(entries, list):
            raise ExportVerificationError("manifest files list is invalid")
        expected: dict[str, dict[str, Any]] = {}
        for entry in entries:
            if not isinstance(entry, dict) or not isinstance(entry.get("name"), str):
                raise ExportVerificationError("manifest file entry is invalid")
            name = entry["name"]
            if name == "manifest.json" or name in expected or not _safe_member_name(name):
                raise ExportVerificationError("manifest contains an invalid or duplicate filename")
            expected[name] = entry
        if set(names) != {"manifest.json", *expected.keys()}:
            raise ExportVerificationError("archive files do not match the manifest")
        for name, entry in expected.items():
            payload = archive.read(name)
            if entry.get("size") != len(payload):
                raise ExportVerificationError(f"size mismatch for {name}")
            if entry.get("sha256") != _sha256(payload):
                raise ExportVerificationError(f"hash mismatch for {name}")
        if "report.html" in expected:
            try:
                report_html = archive.read("report.html").decode("utf-8")
            except UnicodeDecodeError as exc:
                raise ExportVerificationError("report.html is not UTF-8") from exc
            if _EXTERNAL_RESOURCE_RE.search(report_html) or _FORBIDDEN_HTML_TAG_RE.search(report_html):
                raise ExportVerificationError("report.html contains an external or embedded resource")

    return {
        "valid": True,
        "kind": manifest["kind"],
        "format_version": manifest["format_version"],
        "file_count": len(names),
        "total_uncompressed_bytes": total_size,
    }


class ExportService:
    """Create atomic, self-verifying session and support bundles."""

    def __init__(
        self,
        sessions: SessionService,
        *,
        workspace_root: str | Path | None = None,
    ) -> None:
        self.sessions = sessions
        self.workspace_root = Path(workspace_root).expanduser().resolve() if workspace_root else None

    def export_report(self, session_id: str, destination: str | Path) -> Path:
        stored = self.sessions.load(session_id)
        state = dict(stored["state"])
        manager = dict(state.get("manager", {}))
        feedback = self.sessions.list_feedback(session_id)
        session_meta = {
            key: stored.get(key)
            for key in (
                "session_id",
                "title",
                "profile_id",
                "backend",
                "model_id",
                "created_at",
                "updated_at",
            )
        }
        files = {
            "report.html": _report_html(
                session=stored,
                state=state,
                feedback_count=len(feedback),
            ),
            "environment.json": _json_bytes(_environment_payload()),
            "config.json": _json_bytes(
                redact_private_data(
                    stored.get("config", {}),
                    workspace_root=self.workspace_root,
                )
            ),
            "session.json": _json_bytes(session_meta),
            "messages.json": _json_bytes(_messages_payload(state)),
            "seeds.json": _json_bytes(manager.get("seeds", [])),
            "gate-events.json": _json_bytes(manager.get("gate_events", [])),
            "influence-events.json": _json_bytes(state.get("influence_records", [])),
            "tester-feedback.csv": _feedback_csv(feedback),
        }
        return self._write_bundle(
            kind="report",
            session_reference=session_id,
            files=files,
            destination=destination,
        )

    def export_support_bundle(self, session_id: str, destination: str | Path) -> Path:
        stored = self.sessions.load(session_id)
        state = dict(stored["state"])
        manager = dict(state.get("manager", {}))
        seeds = list(manager.get("seeds", []))
        feedback = self.sessions.list_feedback(session_id)
        status_counts = Counter(str(seed.get("status", "unknown")) for seed in seeds)
        support_id = "support::" + _sha256(session_id.encode("utf-8"))[:20]
        rating_counts = Counter(item.overall for item in feedback)
        seed_effect_counts = Counter(item.seed_effect for item in feedback)
        support = {
            "support_session_id": support_id,
            "profile_id": stored.get("profile_id"),
            "backend": stored.get("backend"),
            "model_id": stored.get("model_id"),
            "turn_count": len(state.get("turn_reports", [])),
            "seed_count": len(seeds),
            "seed_status_counts": dict(sorted(status_counts.items())),
            "gate_event_count": len(manager.get("gate_events", [])),
            "contradiction_count": len(manager.get("contradiction_records", [])),
            "influence_event_count": len(state.get("influence_records", [])),
            "feedback_count": len(feedback),
            "feedback_overall_counts": dict(sorted(rating_counts.items())),
            "feedback_seed_effect_counts": dict(sorted(seed_effect_counts.items())),
        }
        files = {
            "environment.json": _json_bytes(_environment_payload()),
            "config.json": _json_bytes(
                redact_private_data(
                    stored.get("config", {}),
                    workspace_root=self.workspace_root,
                )
            ),
            "support.json": _json_bytes(support),
        }
        return self._write_bundle(
            kind="support",
            session_reference=support_id,
            files=files,
            destination=destination,
        )

    def _write_bundle(
        self,
        *,
        kind: str,
        session_reference: str,
        files: dict[str, bytes],
        destination: str | Path,
    ) -> Path:
        target = Path(destination).expanduser().resolve()
        target.parent.mkdir(parents=True, exist_ok=True)
        manifest = {
            "format_version": EXPORT_FORMAT_VERSION,
            "kind": kind,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "session_reference": session_reference,
            "files": [
                {"name": name, "size": len(payload), "sha256": _sha256(payload)}
                for name, payload in sorted(files.items())
            ],
        }
        temporary = target.with_name(f".{target.name}.{uuid4().hex}.tmp")
        try:
            with zipfile.ZipFile(
                temporary,
                "w",
                compression=zipfile.ZIP_DEFLATED,
                compresslevel=6,
            ) as archive:
                for name, payload in sorted(files.items()):
                    archive.writestr(name, payload)
                archive.writestr("manifest.json", _json_bytes(manifest))
            verify_workbench_export(temporary)
            os.replace(temporary, target)
        except Exception:
            try:
                temporary.unlink(missing_ok=True)
            finally:
                raise
        return target


def service_for_workspace(workspace: str | Path | None = None) -> ExportService:
    from shadowseed.application.sessions import service_for_workspace as session_service
    from shadowseed.application.workspace import WorkspaceService

    workspace_service = WorkspaceService(workspace)
    workspace_service.initialize()
    return ExportService(
        session_service(workspace_service.paths.root),
        workspace_root=workspace_service.paths.root,
    )

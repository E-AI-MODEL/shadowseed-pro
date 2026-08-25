from __future__ import annotations

import json
import os
import stat
from pathlib import Path

import pytest

import shadowseed.application.operations as operations
from shadowseed.application.operations import OperationalEventLog, OperationalLoggingError


def test_operational_log_allows_only_minimized_metadata(tmp_path: Path) -> None:
    log = OperationalEventLog(tmp_path / "logs")
    path = log.emit(
        "session.turn.completed",
        workspace_id="workspace::abc",
        session_id="session::abc",
        backend="fixture",
        runtime_mode="live",
        status="ok",
        duration_ms=12,
    )

    payload = json.loads(path.read_text(encoding="utf-8"))
    assert payload["event"] == "session.turn.completed"
    assert payload["workspace_id"] == "workspace::abc"
    assert payload["duration_ms"] == 12


def test_operational_log_rejects_content_and_secret_fields(tmp_path: Path) -> None:
    log = OperationalEventLog(tmp_path / "logs")
    sentinel = "DO-NOT-LOG-RAW-PROMPT"

    with pytest.raises(OperationalLoggingError, match="not allowed"):
        log.emit("bad", prompt=sentinel)
    with pytest.raises(OperationalLoggingError, match="not allowed"):
        log.emit("bad", evidence_note=sentinel)
    with pytest.raises(OperationalLoggingError, match="not allowed"):
        log.emit("bad", api_key=sentinel)

    assert not log.path.exists()


def test_operational_log_rotates_at_bound_without_copying_content(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(operations, "MAX_OPERATION_LOG_BYTES", 1)
    log = OperationalEventLog(tmp_path / "logs")
    log.emit("first", status="ok")
    log.emit("second", status="ok")

    rotated = log.path.with_name("operations.jsonl.1")
    assert rotated.is_file()
    assert '"event":"first"' in rotated.read_text(encoding="utf-8")
    assert '"event":"second"' in log.path.read_text(encoding="utf-8")


@pytest.mark.skipif(os.name == "nt", reason="POSIX permission contract")
def test_operational_log_is_restricted_before_first_write(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    observed_modes: list[int] = []
    original_fdopen = operations.os.fdopen

    def checked_fdopen(fd: int, *args, **kwargs):
        observed_modes.append(stat.S_IMODE(os.fstat(fd).st_mode))
        return original_fdopen(fd, *args, **kwargs)

    monkeypatch.setattr(operations.os, "fdopen", checked_fdopen)
    log = OperationalEventLog(tmp_path / "logs")
    log.emit("permission-check", status="ok")

    assert observed_modes == [0o600]
    assert stat.S_IMODE(log.path.stat().st_mode) == 0o600

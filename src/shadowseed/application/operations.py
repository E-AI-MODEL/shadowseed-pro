"""Content-minimized operational logging for the production-local profile.

Operational events deliberately use a small allow-list of metadata keys. User
content, prompts, answers, seed text, evidence references/notes, credentials and
arbitrary exception payloads are not accepted as structured fields.
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping


MAX_OPERATION_LOG_BYTES = 1 * 1024 * 1024
OPERATION_LOG_GENERATIONS = 5

_ALLOWED_FIELDS = frozenset(
    {
        "request_id",
        "workspace_id",
        "session_id",
        "seed_id",
        "backend",
        "runtime_mode",
        "operation",
        "status",
        "error_type",
        "gate_policy_id",
        "gate_decision",
        "integrity_status",
        "schema_version",
        "count",
        "duration_ms",
    }
)

_FORBIDDEN_NAME_FRAGMENTS = (
    "prompt",
    "answer",
    "message",
    "question",
    "seed_text",
    "source_ref",
    "evidence_note",
    "note",
    "secret",
    "password",
    "token",
    "api_key",
    "credential",
)


class OperationalLoggingError(ValueError):
    """Raised when a caller attempts to put user content into operations logs."""


def _safe_fields(fields: Mapping[str, Any]) -> dict[str, Any]:
    safe: dict[str, Any] = {}
    for raw_key, value in fields.items():
        key = str(raw_key)
        lowered = key.casefold()
        if key not in _ALLOWED_FIELDS or any(fragment in lowered for fragment in _FORBIDDEN_NAME_FRAGMENTS):
            raise OperationalLoggingError(f"operational log field is not allowed: {key}")
        if value is None or isinstance(value, (bool, int, float)):
            safe[key] = value
            continue
        if isinstance(value, str):
            if len(value) > 512:
                raise OperationalLoggingError(f"operational log field is too long: {key}")
            safe[key] = value
            continue
        raise OperationalLoggingError(f"operational log field has unsupported type: {key}")
    return safe


class OperationalEventLog:
    """Small rotating JSONL log with restrictive file permissions where possible."""

    def __init__(self, logs_dir: str | Path) -> None:
        self.logs_dir = Path(logs_dir).expanduser().resolve()
        self.path = self.logs_dir / "operations.jsonl"

    @staticmethod
    def _restrict(path: Path, mode: int) -> None:
        if os.name == "nt" or not path.exists():
            return
        try:
            path.chmod(mode)
        except OSError:
            return

    def _rotate_if_needed(self) -> None:
        if not self.path.exists() or self.path.stat().st_size < MAX_OPERATION_LOG_BYTES:
            return
        oldest = self.path.with_name(f"{self.path.name}.{OPERATION_LOG_GENERATIONS}")
        oldest.unlink(missing_ok=True)
        for index in range(OPERATION_LOG_GENERATIONS - 1, 0, -1):
            source = self.path.with_name(f"{self.path.name}.{index}")
            target = self.path.with_name(f"{self.path.name}.{index + 1}")
            if source.exists():
                os.replace(source, target)
        os.replace(self.path, self.path.with_name(f"{self.path.name}.1"))

    def _append_line(self, line: str) -> None:
        if os.name == "nt":
            with self.path.open("a", encoding="utf-8", newline="\n") as handle:
                handle.write(line)
            return

        flags = os.O_WRONLY | os.O_CREAT | os.O_APPEND
        fd = os.open(self.path, flags, 0o600)
        try:
            os.fchmod(fd, 0o600)
            handle = os.fdopen(fd, "a", encoding="utf-8", newline="\n")
            fd = -1
            with handle:
                handle.write(line)
        finally:
            if fd >= 0:
                os.close(fd)

    def emit(self, event: str, **fields: Any) -> Path:
        event_name = str(event).strip()
        if not event_name or len(event_name) > 128:
            raise OperationalLoggingError("operational event name is invalid")
        payload = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "event": event_name,
            **_safe_fields(fields),
        }
        self.logs_dir.mkdir(parents=True, exist_ok=True)
        self._restrict(self.logs_dir, 0o700)
        self._rotate_if_needed()
        line = json.dumps(payload, sort_keys=True, separators=(",", ":")) + "\n"
        self._append_line(line)
        return self.path

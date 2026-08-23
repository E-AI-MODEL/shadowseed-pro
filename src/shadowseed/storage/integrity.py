"""Content-minimized production ledger hashing and protected local anchor helpers."""

from __future__ import annotations

import hashlib
import hmac
import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Mapping

GENESIS_HASH = "0" * 64
EVENT_FORMAT_VERSION = 1
ANCHOR_FORMAT_VERSION = 1


def canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def event_digest(event: Mapping[str, Any]) -> str:
    return sha256_text(canonical_json(dict(event)))


def authority_projection(state: Mapping[str, Any]) -> list[dict[str, Any]]:
    """Return the minimal authority-bearing seed projection, excluding seed content."""

    manager = state.get("manager", {})
    if not isinstance(manager, Mapping):
        return []
    projected: list[dict[str, Any]] = []
    seeds = manager.get("seeds", [])
    if not isinstance(seeds, list):
        return []
    for seed in seeds:
        if not isinstance(seed, Mapping):
            continue
        projected.append(
            {
                "seed_id": str(seed.get("id", "")),
                "status": seed.get("status"),
                "weight": seed.get("weight"),
                "trace": seed.get("trace"),
                "authority_version": seed.get("authority_version"),
                "evidence_count": seed.get("evidence_count"),
            }
        )
    return sorted(projected, key=lambda item: item["seed_id"])


def authority_digest(state: Mapping[str, Any]) -> str:
    return sha256_text(canonical_json(authority_projection(state)))


def minimal_runtime_commit(state: Mapping[str, Any]) -> dict[str, Any]:
    """Commit to authority/Gate/use records without storing prompts, answers or seed text."""

    manager = state.get("manager", {})
    if not isinstance(manager, Mapping):
        manager = {}

    def event_commitments(items: Any, key_name: str) -> list[dict[str, str]]:
        if not isinstance(items, list):
            return []
        result: list[dict[str, str]] = []
        for index, item in enumerate(items):
            if not isinstance(item, Mapping):
                continue
            key = str(item.get(key_name) or f"event::{index:06d}")
            result.append({"id": key, "digest": sha256_text(canonical_json(dict(item)))})
        return result

    return {
        "authority_digest": authority_digest(state),
        "gate_events": event_commitments(manager.get("gate_events", []), "event_id"),
        "contradictions": event_commitments(
            manager.get("contradiction_records", []), "contradiction_id"
        ),
        "influence_events": event_commitments(state.get("influence_records", []), "event_id"),
    }


@dataclass(frozen=True)
class AnchorState:
    workspace_id: str
    audit_epoch: str
    sequence_no: int
    head_hash: str
    key_id: str

    def unsigned(self) -> dict[str, Any]:
        return {
            "format_version": ANCHOR_FORMAT_VERSION,
            "workspace_id": self.workspace_id,
            "audit_epoch": self.audit_epoch,
            "sequence_no": self.sequence_no,
            "head_hash": self.head_hash,
            "key_id": self.key_id,
        }


def key_id(key: bytes) -> str:
    return f"local-hmac-sha256::{hashlib.sha256(key).hexdigest()[:24]}"


def _require_private_posix_file(path: Path, *, label: str) -> None:
    """Reject group/other access for protected material on POSIX hosts."""

    if os.name == "nt":
        return
    try:
        mode = path.stat().st_mode & 0o777
    except OSError as exc:
        raise ValueError(f"{label} is unavailable") from exc
    if mode & 0o077:
        raise ValueError(
            f"{label} permissions are too broad ({mode:o}); owner-only access is required"
        )


def create_integrity_key(path: Path) -> bytes:
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        path.parent.chmod(0o700)
    except OSError:
        pass
    if path.exists():
        return load_integrity_key(path)
    key = os.urandom(32)
    temporary = path.with_suffix(path.suffix + ".tmp")
    with temporary.open("wb") as handle:
        handle.write(key)
        handle.flush()
        os.fsync(handle.fileno())
    try:
        temporary.chmod(0o600)
    except OSError:
        pass
    os.replace(temporary, path)
    _require_private_posix_file(path, label="protected integrity key")
    return key


def load_integrity_key(path: Path) -> bytes:
    _require_private_posix_file(path, label="protected integrity key")
    try:
        key = path.read_bytes()
    except OSError as exc:
        raise ValueError("protected integrity key is unavailable") from exc
    if len(key) != 32:
        raise ValueError("protected integrity key is malformed")
    return key


def write_anchor(path: Path, state: AnchorState, key: bytes) -> None:
    unsigned = state.unsigned()
    signature = hmac.new(
        key, canonical_json(unsigned).encode("utf-8"), hashlib.sha256
    ).hexdigest()
    payload = {**unsigned, "hmac_sha256": signature}
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        path.parent.chmod(0o700)
    except OSError:
        pass
    temporary = path.with_suffix(path.suffix + ".tmp")
    with temporary.open("w", encoding="utf-8") as handle:
        handle.write(canonical_json(payload) + "\n")
        handle.flush()
        os.fsync(handle.fileno())
    try:
        temporary.chmod(0o600)
    except OSError:
        pass
    os.replace(temporary, path)
    _require_private_posix_file(path, label="protected integrity anchor")


def read_anchor(path: Path, key: bytes) -> AnchorState:
    _require_private_posix_file(path, label="protected integrity anchor")
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError("protected integrity anchor is unavailable or malformed") from exc
    if payload.get("format_version") != ANCHOR_FORMAT_VERSION:
        raise ValueError("protected integrity anchor format is unsupported")
    signature = payload.pop("hmac_sha256", None)
    expected = hmac.new(
        key, canonical_json(payload).encode("utf-8"), hashlib.sha256
    ).hexdigest()
    if not isinstance(signature, str) or not hmac.compare_digest(signature, expected):
        raise ValueError("protected integrity anchor authentication failed")
    return AnchorState(
        workspace_id=str(payload["workspace_id"]),
        audit_epoch=str(payload["audit_epoch"]),
        sequence_no=int(payload["sequence_no"]),
        head_hash=str(payload["head_hash"]),
        key_id=str(payload["key_id"]),
    )


def verify_chain_rows(rows: Iterable[Mapping[str, Any]]) -> dict[str, Any]:
    previous_hash = GENESIS_HASH
    expected_sequence = 1
    workspace_id: str | None = None
    audit_epoch: str | None = None
    head_hash = GENESIS_HASH
    count = 0
    for raw_row in rows:
        row = dict(raw_row)
        sequence_no = int(row["sequence_no"])
        if sequence_no != expected_sequence:
            raise ValueError(f"ledger sequence discontinuity at {sequence_no}")
        if row["previous_hash"] != previous_hash:
            raise ValueError(f"ledger previous-hash mismatch at {sequence_no}")
        current_workspace = str(row["workspace_id"])
        current_epoch = str(row["audit_epoch"])
        if workspace_id is None:
            workspace_id = current_workspace
        elif current_workspace != workspace_id:
            raise ValueError(f"ledger workspace changed at {sequence_no}")
        if audit_epoch is None:
            audit_epoch = current_epoch
        elif current_epoch != audit_epoch:
            audit_epoch = current_epoch
        stored_hash = str(row.pop("event_hash"))
        computed_hash = event_digest(row)
        if not hmac.compare_digest(stored_hash, computed_hash):
            raise ValueError(f"ledger event hash mismatch at {sequence_no}")
        previous_hash = stored_hash
        head_hash = stored_hash
        expected_sequence += 1
        count += 1
    return {
        "event_count": count,
        "workspace_id": workspace_id,
        "audit_epoch": audit_epoch,
        "sequence_no": count,
        "head_hash": head_hash,
    }

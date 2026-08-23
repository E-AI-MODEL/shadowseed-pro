"""Authorized production-local contradiction resolution boundary."""

from __future__ import annotations

import hashlib
from datetime import datetime
from typing import Any

from shadowseed.application.auth import (
    CONTRADICTION_RESOLVE,
    ActorContext,
    require_capability,
)
from shadowseed.application.limits import validate_contradiction_resolution
from shadowseed.chat import ShadowChatSession
from shadowseed.storage.sqlite import SQLiteWorkspaceRepository, WorkspaceStorageError


def _request_fingerprint(
    session_id: str,
    seed_id: str,
    basis: str,
    contradiction_id: str | None,
) -> str:
    material = "\x1f".join(
        (
            CONTRADICTION_RESOLVE,
            session_id,
            seed_id,
            contradiction_id or "",
            basis,
        )
    )
    return hashlib.sha256(material.encode("utf-8")).hexdigest()


def _validated_replay(
    replay: dict[str, Any],
    *,
    expected_fingerprint: str,
) -> dict[str, Any]:
    stored_fingerprint = replay.pop("_request_fingerprint", None)
    if stored_fingerprint != expected_fingerprint:
        raise WorkspaceStorageError(
            "request_id was replayed with different contradiction-resolution input"
        )
    return replay


def resolve_authorized_contradiction(
    repository: SQLiteWorkspaceRepository,
    session_id: str,
    seed_id: str,
    *,
    basis: str,
    actor: ActorContext,
    scope_id: str,
    contradiction_id: str | None = None,
) -> dict[str, Any]:
    """Resolve blocking contradiction records through auth, Gate, ledger, and anchor.

    Authorization and bounded-input validation happen before runtime mutation. The
    core Gate owns the actual contradiction-resolution decision; this application
    boundary only establishes who may invoke it and persists the result atomically.
    Raw resolution rationale remains in session-owned state and is not copied into
    the content-minimized production ledger.
    """

    authorization = require_capability(
        actor,
        scope_id=scope_id,
        capability=CONTRADICTION_RESOLVE,
    )
    normalized_basis, normalized_id = validate_contradiction_resolution(
        basis,
        contradiction_id,
    )
    fingerprint = _request_fingerprint(
        session_id,
        seed_id,
        normalized_basis,
        normalized_id,
    )

    replay = repository.authorized_request_result(
        actor.request_id,
        event_type=CONTRADICTION_RESOLVE,
        session_id=session_id,
        seed_id=seed_id,
    )
    if replay is not None:
        return {
            **_validated_replay(replay, expected_fingerprint=fingerprint),
            "authorization": authorization,
        }

    stored = repository.load_session(session_id)
    session = ShadowChatSession.from_state(stored["state"])
    seed = session.manager.get_seed(seed_id)
    authority_version_before = seed.authority_version
    selected = session.manager.open_contradictions(seed_id)
    if normalized_id is not None:
        selected = [
            record for record in selected if record.contradiction_id == normalized_id
        ]
    resolved_ids = [record.contradiction_id for record in selected]

    event = session.manager.resolve_contradiction(
        seed_id,
        basis=normalized_basis,
        contradiction_id=normalized_id,
        resolver=actor.actor_id,
    )
    result = {
        "gate_event_id": event.event_id,
        "decision": event.decision.value,
        "policy_id": event.policy_id,
        "authority_version_before": authority_version_before,
        "authority_version_after": event.authority_version,
        "blocking_after": event.contradiction_after.blocking,
        "resolved_contradiction_ids": resolved_ids,
        "_request_fingerprint": fingerprint,
    }
    persisted = repository.save_authorized_session(
        session_id,
        session.to_state(),
        updated_at=datetime.now().isoformat(),
        authorization=authorization,
        event_type=CONTRADICTION_RESOLVE,
        seed_id=seed_id,
        operation_result=result,
        event_metadata={
            "action": "contradiction_resolution",
            "basis_sha256": hashlib.sha256(normalized_basis.encode("utf-8")).hexdigest(),
            "contradiction_ids": resolved_ids,
        },
    )
    persisted = _validated_replay(
        persisted,
        expected_fingerprint=fingerprint,
    )
    return {**persisted, "authorization": authorization}

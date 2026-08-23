"""Atomic production-local session deletion with attributable authorization."""

from __future__ import annotations

import json
from typing import Any, Mapping

from shadowseed.application.auth import SESSION_MANAGE
from shadowseed.storage.integrity import authority_digest
from shadowseed.storage.production import ProductionSQLiteWorkspaceRepository
from shadowseed.storage.sqlite import WorkspaceStorageError

_SESSION_DELETE_EVENT = "session.delete"
_SESSION_OWNED_TABLES = ("turns", "seeds", "audit_events", "tester_feedback")


def _authorization_fields(authorization: Mapping[str, Any]) -> dict[str, str]:
    values = {
        "request_id": str(authorization.get("request_id") or "").strip(),
        "actor_id": str(authorization.get("actor_id") or "").strip(),
        "scope_id": str(authorization.get("scope_id") or "").strip(),
        "capability": str(authorization.get("capability") or "").strip(),
        "auth_method": str(authorization.get("auth_method") or "").strip(),
        "policy_version": str(authorization.get("policy_version") or "").strip(),
    }
    if not all(values.values()):
        raise WorkspaceStorageError("authorization metadata is incomplete")
    if values["capability"] != SESSION_MANAGE:
        raise WorkspaceStorageError("session deletion requires session.manage capability")
    return values


def _replay_result(row: Mapping[str, Any], *, session_id: str) -> dict[str, Any]:
    if row["event_type"] != _SESSION_DELETE_EVENT or row["session_id"] != session_id:
        raise WorkspaceStorageError(
            "request_id was already used for a different authority operation"
        )
    payload = json.loads(str(row["payload_json"]))
    result = payload.get("operation_result")
    if not isinstance(result, dict):
        raise WorkspaceStorageError("stored session deletion result is invalid")
    return {**result, "idempotent_replay": True, "ledger_event_id": row["event_id"]}


def delete_authorized_session(
    repository: ProductionSQLiteWorkspaceRepository,
    session_id: str,
    *,
    authorization: Mapping[str, Any],
) -> dict[str, Any]:
    """Delete one production session atomically and retain only a minimized tombstone."""

    repository.initialize()
    workspace_id = repository._workspace_id
    if workspace_id is None:
        raise WorkspaceStorageError("production session deletion requires a bound workspace")

    authz = _authorization_fields(authorization)
    if authz["scope_id"] != workspace_id:
        raise WorkspaceStorageError("authorization scope does not match workspace")

    with repository._connect() as connection:
        previous = connection.execute(
            "SELECT * FROM production_ledger WHERE request_id = ?",
            (authz["request_id"],),
        ).fetchone()
    if previous is not None:
        return _replay_result(previous, session_id=session_id)

    with repository._connect() as connection:
        try:
            connection.execute("BEGIN IMMEDIATE")
            duplicate = connection.execute(
                "SELECT * FROM production_ledger WHERE request_id = ?",
                (authz["request_id"],),
            ).fetchone()
            if duplicate is not None:
                connection.rollback()
                return _replay_result(duplicate, session_id=session_id)

            stored = connection.execute(
                "SELECT state_json FROM sessions WHERE session_id = ?",
                (session_id,),
            ).fetchone()
            if stored is None:
                raise KeyError(f"unknown session id: {session_id}")
            try:
                state = json.loads(str(stored["state_json"]))
            except json.JSONDecodeError as exc:
                raise WorkspaceStorageError("session state is invalid JSON") from exc

            operation_result = {"session_id": session_id, "deleted": True}
            ledger = repository._append_ledger_event(
                connection,
                workspace_id=workspace_id,
                audit_epoch=repository._current_epoch(connection),
                session_id=session_id,
                event_type=_SESSION_DELETE_EVENT,
                request_id=authz["request_id"],
                actor_id=authz["actor_id"],
                actor_scope_id=authz["scope_id"],
                capability=authz["capability"],
                auth_method=authz["auth_method"],
                policy_version=authz["policy_version"],
                payload={
                    "authority_digest_before_delete": authority_digest(state),
                    "content_removed": True,
                    "operation_result": operation_result,
                },
            )
            cursor = connection.execute(
                "DELETE FROM sessions WHERE session_id = ?",
                (session_id,),
            )
            if cursor.rowcount != 1:
                raise KeyError(f"unknown session id: {session_id}")

            for table in _SESSION_OWNED_TABLES:
                remaining = connection.execute(
                    f"SELECT COUNT(*) FROM {table} WHERE session_id = ?",
                    (session_id,),
                ).fetchone()
                if remaining is None or int(remaining[0]) != 0:
                    raise WorkspaceStorageError(
                        f"session deletion left orphaned content in {table}"
                    )
            connection.commit()
        except Exception:
            connection.rollback()
            raise

    repository._advance_anchor()
    return {
        **operation_result,
        "idempotent_replay": False,
        "ledger_event_id": ledger["event_id"],
        "ledger_sequence_no": ledger["sequence_no"],
        "ledger_event_hash": ledger["event_hash"],
    }

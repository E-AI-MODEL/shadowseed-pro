"""Production-local session deletion acceptance tests."""

from __future__ import annotations

import json
from dataclasses import replace

import pytest

from shadowseed.application.auth import SESSION_MANAGE, AuthorizationError
from shadowseed.workbench.production_controller import ProductionLocalWorkbenchController


def _content_session(controller: ProductionLocalWorkbenchController) -> tuple[str, str]:
    session_id = controller.create_session(
        title="Deletion target",
        profile_id="demo",
        backend="fixture",
        runtime_mode="live",
    )
    result = controller.send_turn(
        session_id,
        "DELETION_QUESTION_SENTINEL What is missing from this privacy plan?",
    )
    seed_id = str(result["session"]["seeds"][0]["id"])
    controller.submit_verified_evidence(
        session_id,
        seed_id,
        source_ref="DELETION_SOURCE_SENTINEL",
        note="DELETION_NOTE_SENTINEL",
        operator_verified=True,
    )
    controller.record_feedback(
        session_id=session_id,
        turn_index=0,
        overall="better",
        seed_effect="helpful",
        note="DELETION_FEEDBACK_SENTINEL",
        seed_id=seed_id,
    )
    return session_id, seed_id


def test_production_session_delete_is_authorized_atomic_and_content_minimized(
    tmp_path,
) -> None:
    controller = ProductionLocalWorkbenchController(tmp_path / "workspace")
    session_id, _seed_id = _content_session(controller)

    result = controller.delete_session(session_id)

    assert result["deleted"] is True
    assert result["authorization"]["capability"] == SESSION_MANAGE
    assert result["authorization"]["scope_id"] == controller.workspace.workspace_id
    with pytest.raises(KeyError):
        controller.workspace.repository.load_session(session_id)

    with controller.workspace.repository._connect() as connection:
        for table in ("turns", "seeds", "audit_events", "tester_feedback"):
            assert connection.execute(
                f"SELECT COUNT(*) FROM {table} WHERE session_id = ?",
                (session_id,),
            ).fetchone()[0] == 0
        tombstone = connection.execute(
            "SELECT * FROM production_ledger "
            "WHERE session_id = ? AND event_type = 'session.delete' "
            "ORDER BY sequence_no DESC LIMIT 1",
            (session_id,),
        ).fetchone()
        assert tombstone is not None
        assert tombstone["actor_id"] == result["authorization"]["actor_id"]
        assert tombstone["actor_scope_id"] == controller.workspace.workspace_id
        assert tombstone["capability"] == SESSION_MANAGE
        assert tombstone["request_id"] == result["authorization"]["request_id"]
        payload = json.loads(tombstone["payload_json"])

    serialized = json.dumps(payload)
    assert payload["content_removed"] is True
    assert "DELETION_QUESTION_SENTINEL" not in serialized
    assert "DELETION_SOURCE_SENTINEL" not in serialized
    assert "DELETION_NOTE_SENTINEL" not in serialized
    assert "DELETION_FEEDBACK_SENTINEL" not in serialized
    assert controller.workspace.repository.verify_production_integrity()[
        "authority_snapshot_verified"
    ] is True


def test_production_session_delete_rejects_missing_capability_before_mutation(
    tmp_path,
    monkeypatch,
) -> None:
    controller = ProductionLocalWorkbenchController(tmp_path / "workspace")
    session_id, _seed_id = _content_session(controller)
    before = controller.workspace.repository.verify_production_integrity()
    valid = controller.workspace.local_actor_context(request_id="request::no-session-manage")
    denied = replace(valid, capabilities=valid.capabilities - {SESSION_MANAGE})
    monkeypatch.setattr(controller.workspace, "local_actor_context", lambda: denied)

    with pytest.raises(AuthorizationError, match="session.manage"):
        controller.delete_session(session_id)

    assert controller.workspace.repository.load_session(session_id)["session_id"] == session_id
    after = controller.workspace.repository.verify_production_integrity()
    assert after["sequence_no"] == before["sequence_no"]
    assert after["head_hash"] == before["head_hash"]

"""Final production-local contradiction-resolution acceptance tests."""

from __future__ import annotations

import hashlib
import json
from dataclasses import replace

import pytest

from shadowseed.application.auth import CONTRADICTION_RESOLVE, AuthorizationError
from shadowseed.application.contradiction_resolution import resolve_authorized_contradiction
from shadowseed.application.limits import (
    MAX_CONTRADICTION_RESOLUTION_BASIS_CHARS,
    ResourceLimitError,
)
from shadowseed.storage.sqlite import WorkspaceStorageError
from shadowseed.workbench.production_controller import ProductionLocalWorkbenchController


def _contradicted_seed(
    controller: ProductionLocalWorkbenchController,
) -> tuple[str, str]:
    session_id = controller.create_session(
        title="Resolution target",
        profile_id="demo",
        backend="fixture",
        runtime_mode="live",
    )
    turn = controller.send_turn(session_id, "What assumption should be checked?")
    seed_id = str(turn["session"]["seeds"][0]["id"])
    controller.falsify_seed(session_id, seed_id)
    assert controller.seed_view(session_id, seed_id)["blocking"] is True
    return session_id, seed_id


def test_production_resolution_requires_distinct_capability_and_persists_gate_link(
    tmp_path,
) -> None:
    controller = ProductionLocalWorkbenchController(tmp_path / "workspace")
    session_id, seed_id = _contradicted_seed(controller)
    before_seed = controller.seed_view(session_id, seed_id)
    before_integrity = controller.workspace.repository.verify_production_integrity()
    basis = "RESOLUTION_BASIS_SENTINEL independently rechecked the contradiction"

    result = controller.resolve_contradiction(
        session_id,
        seed_id,
        basis=basis,
    )

    after_seed = controller.seed_view(session_id, seed_id)
    after_integrity = controller.workspace.repository.verify_production_integrity()
    assert result["decision"] == "contradiction_resolved"
    assert result["policy_id"] == "contradiction_resolution"
    assert result["blocking_after"] is False
    assert result["authorization"]["capability"] == CONTRADICTION_RESOLVE
    assert result["authorization"]["scope_id"] == controller.workspace.workspace_id
    assert after_seed["blocking"] is False
    assert after_seed["weight"] == before_seed["weight"]
    assert after_integrity["sequence_no"] == before_integrity["sequence_no"] + 1
    assert after_integrity["head_hash"] != before_integrity["head_hash"]

    with controller.workspace.repository._connect() as connection:
        row = connection.execute(
            "SELECT * FROM production_ledger "
            "WHERE session_id = ? AND seed_id = ? AND event_type = 'contradiction.resolve' "
            "ORDER BY sequence_no DESC LIMIT 1",
            (session_id, seed_id),
        ).fetchone()
        assert row is not None
        payload = json.loads(row["payload_json"])

    assert row["capability"] == CONTRADICTION_RESOLVE
    assert row["actor_id"] == result["authorization"]["actor_id"]
    assert row["actor_scope_id"] == controller.workspace.workspace_id
    assert row["request_id"] == result["authorization"]["request_id"]
    assert payload["operation_result"]["gate_event_id"] == result["gate_event_id"]
    assert payload["metadata"]["action"] == "contradiction_resolution"
    assert payload["metadata"]["basis_sha256"] == hashlib.sha256(
        basis.encode("utf-8")
    ).hexdigest()
    assert "RESOLUTION_BASIS_SENTINEL" not in json.dumps(payload)


def test_resolution_missing_capability_fails_before_mutation(tmp_path) -> None:
    controller = ProductionLocalWorkbenchController(tmp_path / "workspace")
    session_id, seed_id = _contradicted_seed(controller)
    before_state = controller.workspace.repository.load_session(session_id)["state"]
    before_integrity = controller.workspace.repository.verify_production_integrity()
    actor = controller.workspace.local_actor_context(request_id="request::deny-resolution")
    denied = replace(actor, capabilities=actor.capabilities - {CONTRADICTION_RESOLVE})

    with pytest.raises(AuthorizationError, match="contradiction.resolve"):
        resolve_authorized_contradiction(
            controller.workspace.repository,
            session_id,
            seed_id,
            basis="rechecked",
            actor=denied,
            scope_id=controller.workspace.workspace_id,
        )

    assert controller.workspace.repository.load_session(session_id)["state"] == before_state
    after_integrity = controller.workspace.repository.verify_production_integrity()
    assert after_integrity["sequence_no"] == before_integrity["sequence_no"]
    assert after_integrity["head_hash"] == before_integrity["head_hash"]


def test_resolution_basis_limit_fails_before_mutation(tmp_path) -> None:
    controller = ProductionLocalWorkbenchController(tmp_path / "workspace")
    session_id, seed_id = _contradicted_seed(controller)
    before_state = controller.workspace.repository.load_session(session_id)["state"]
    before_integrity = controller.workspace.repository.verify_production_integrity()
    actor = controller.workspace.local_actor_context(request_id="request::oversized-resolution")

    with pytest.raises(ResourceLimitError, match="resolution basis exceeds"):
        resolve_authorized_contradiction(
            controller.workspace.repository,
            session_id,
            seed_id,
            basis="x" * (MAX_CONTRADICTION_RESOLUTION_BASIS_CHARS + 1),
            actor=actor,
            scope_id=controller.workspace.workspace_id,
        )

    assert controller.workspace.repository.load_session(session_id)["state"] == before_state
    after_integrity = controller.workspace.repository.verify_production_integrity()
    assert after_integrity["sequence_no"] == before_integrity["sequence_no"]
    assert after_integrity["head_hash"] == before_integrity["head_hash"]


def test_resolution_request_id_is_idempotent_and_rejects_changed_basis(tmp_path) -> None:
    controller = ProductionLocalWorkbenchController(tmp_path / "workspace")
    session_id, seed_id = _contradicted_seed(controller)
    actor = controller.workspace.local_actor_context(request_id="request::resolution-replay")
    kwargs = {
        "repository": controller.workspace.repository,
        "session_id": session_id,
        "seed_id": seed_id,
        "basis": "same checked basis",
        "actor": actor,
        "scope_id": controller.workspace.workspace_id,
    }

    first = resolve_authorized_contradiction(**kwargs)
    after_first = controller.workspace.repository.verify_production_integrity()
    second = resolve_authorized_contradiction(**kwargs)
    after_second = controller.workspace.repository.verify_production_integrity()

    assert first["idempotent_replay"] is False
    assert second["idempotent_replay"] is True
    assert second["ledger_event_id"] == first["ledger_event_id"]
    assert after_second["sequence_no"] == after_first["sequence_no"]
    assert after_second["head_hash"] == after_first["head_hash"]

    with pytest.raises(WorkspaceStorageError, match="different contradiction-resolution input"):
        resolve_authorized_contradiction(
            controller.workspace.repository,
            session_id,
            seed_id,
            basis="different basis",
            actor=actor,
            scope_id=controller.workspace.workspace_id,
        )

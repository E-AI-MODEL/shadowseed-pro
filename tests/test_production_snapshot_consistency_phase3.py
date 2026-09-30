from __future__ import annotations

import json
import sqlite3
from pathlib import Path

import pytest

from shadowseed.application.workspace import WorkspaceService
from shadowseed.storage.sqlite import WorkspaceStorageError
from shadowseed.workbench.controller import WorkbenchController


def test_mutable_authority_snapshot_cannot_silently_diverge_from_ledger(
    tmp_path: Path,
) -> None:
    controller = WorkbenchController(tmp_path / "workspace")
    session_id = controller.create_session(
        title="Authority snapshot",
        profile_id="demo",
        backend="fixture",
        runtime_mode="live",
    )
    result = controller.send_turn(session_id, "What should this plan verify?")
    seed_id = result["session"]["seeds"][0]["id"]

    with sqlite3.connect(controller.workspace.paths.database) as connection:
        raw = connection.execute(
            "SELECT state_json FROM sessions WHERE session_id = ?", (session_id,)
        ).fetchone()
        assert raw is not None
        state = json.loads(raw[0])
        seed = next(item for item in state["manager"]["seeds"] if item["id"] == seed_id)
        seed["weight"] = 999.0
        connection.execute(
            "UPDATE sessions SET state_json = ? WHERE session_id = ?",
            (json.dumps(state, sort_keys=True), session_id),
        )

    with pytest.raises(WorkspaceStorageError, match="snapshot diverges"):
        controller.workspace.repository.verify_production_integrity()


def test_production_checkpoint_is_content_minimized_and_verified(tmp_path: Path) -> None:
    workspace = WorkspaceService(tmp_path / "workspace")
    workspace.initialize()

    report = workspace.repository.verify_production_integrity()
    assert report["authority_snapshot_verified"] is True

    with sqlite3.connect(workspace.paths.database) as connection:
        row = connection.execute(
            "SELECT payload_json FROM production_ledger "
            "WHERE event_type='production.authority_checkpoint'"
        ).fetchone()
    assert row is not None
    payload = json.loads(row[0])
    assert payload == {"authority_snapshot": []}



def test_gate_reconfiguration_is_committed_and_tamper_detected(tmp_path: Path) -> None:
    controller = WorkbenchController(tmp_path / "workspace")
    session_id = controller.create_session(
        title="Protected Gate config",
        profile_id="demo",
        backend="fixture",
        runtime_mode="live",
        ssl_intensity=100,
        gate_strictness=0,
    )

    controller.update_session_controls(
        session_id,
        ssl_intensity=100,
        gate_strictness=60,
        allow_self_reinforcement=False,
    )

    with sqlite3.connect(controller.workspace.paths.database) as connection:
        row = connection.execute(
            "SELECT payload_json FROM production_ledger "
            "WHERE session_id = ? AND event_type = 'runtime.session_reconfigure' "
            "ORDER BY sequence_no DESC LIMIT 1",
            (session_id,),
        ).fetchone()
        assert row is not None
        payload = json.loads(row[0])

        assert len(payload["authority_config_digest"]) == 64
        assert payload["authority_config"]["session_config"]["gate_policy_id"] == (
            "evidence_backed"
        )
        assert payload["authority_config"]["session_config"][
            "revalidate_current_gate"
        ] is True
        assert payload["authority_config"]["manager_config"][
            "min_occurrences_for_gate"
        ] == 3
        assert payload["runtime_commit"]["authority_config"] == payload[
            "authority_config"
        ]
        assert payload["runtime_commit"]["authority_config_digest"] == payload[
            "authority_config_digest"
        ]

        stored = connection.execute(
            "SELECT state_json FROM sessions WHERE session_id = ?",
            (session_id,),
        ).fetchone()
        assert stored is not None
        state = json.loads(stored[0])
        state["session_config"]["gate_policy_id"] = "exploratory"
        state["session_config"]["revalidate_current_gate"] = False
        state["manager"]["config"]["min_occurrences_for_gate"] = 1
        connection.execute(
            "UPDATE sessions SET state_json = ? WHERE session_id = ?",
            (json.dumps(state, sort_keys=True), session_id),
        )
        connection.commit()

    with pytest.raises(
        WorkspaceStorageError,
        match="authority configuration diverges",
    ):
        controller.workspace.repository.verify_production_integrity()

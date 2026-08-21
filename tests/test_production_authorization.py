from __future__ import annotations

from dataclasses import replace

import pytest

from shadowseed.application.auth import (
    CONTRADICTION_SUBMIT,
    EVIDENCE_VERIFY,
    ActorContext,
    AuthorizationError,
    require_capability,
)
from shadowseed.application.workspace import WorkspaceService
from shadowseed.workbench.controller import WorkbenchController


def test_local_workspace_identity_is_stable_and_not_path_derived(tmp_path) -> None:
    workspace = WorkspaceService(tmp_path / "workspace")
    first = workspace.workspace_id
    second = WorkspaceService(tmp_path / "workspace").workspace_id

    assert first == second
    assert first.startswith("workspace::")
    assert str(tmp_path) not in first
    assert workspace.paths.identity.read_text(encoding="utf-8").strip() == first


def test_local_actor_context_is_product_derived_and_attributable(tmp_path) -> None:
    workspace = WorkspaceService(tmp_path / "workspace")
    actor = workspace.local_actor_context(request_id="request::test")

    assert actor.scope_id == workspace.workspace_id
    assert actor.actor_id.startswith("local-owner::")
    assert actor.auth_method == "local-install"
    assert actor.request_id == "request::test"
    assert EVIDENCE_VERIFY in actor.capabilities


def test_authorization_rejects_wrong_scope_and_missing_capability() -> None:
    actor = ActorContext(
        actor_id="actor::1",
        scope_id="workspace::1",
        capabilities=frozenset({EVIDENCE_VERIFY}),
        auth_method="local-install",
        request_id="request::1",
    )

    with pytest.raises(AuthorizationError, match="scope"):
        require_capability(
            actor,
            scope_id="workspace::2",
            capability=EVIDENCE_VERIFY,
        )

    without_capability = replace(actor, capabilities=frozenset())
    with pytest.raises(AuthorizationError, match="evidence.verify"):
        require_capability(
            without_capability,
            scope_id="workspace::1",
            capability=EVIDENCE_VERIFY,
        )


def test_authorization_record_contains_no_secret_material() -> None:
    actor = ActorContext(
        actor_id="actor::1",
        scope_id="workspace::1",
        capabilities=frozenset({EVIDENCE_VERIFY}),
        auth_method="local-install",
        assurance={"profile": "single-user-local"},
        request_id="request::1",
    )

    record = require_capability(
        actor,
        scope_id="workspace::1",
        capability=EVIDENCE_VERIFY,
    )

    assert record == {
        "actor_id": "actor::1",
        "scope_id": "workspace::1",
        "capability": EVIDENCE_VERIFY,
        "auth_method": "local-install",
        "assurance": {"profile": "single-user-local"},
        "request_id": "request::1",
        "policy_version": "production-authz-v1",
        "authorized": True,
    }


def _live_seed(controller: WorkbenchController) -> tuple[str, str]:
    session_id = controller.create_session(
        title="Authorization target",
        profile_id="demo",
        backend="fixture",
        runtime_mode="live",
    )
    result = controller.send_turn(session_id, "What is missing from this privacy plan?")
    return session_id, str(result["session"]["seeds"][0]["id"])


def test_workbench_verified_evidence_uses_trusted_actor_context(tmp_path) -> None:
    controller = WorkbenchController(tmp_path / "workspace")
    session_id, seed_id = _live_seed(controller)

    result = controller.submit_verified_evidence(
        session_id,
        seed_id,
        source_ref="reviewer:one",
        note="Independently checked.",
        operator_verified=True,
    )

    authz = result["authorization"]
    assert authz["authorized"] is True
    assert authz["scope_id"] == controller.workspace.workspace_id
    assert authz["capability"] == EVIDENCE_VERIFY
    assert str(authz["actor_id"]).startswith("local-owner::")
    assert str(authz["request_id"]).startswith("request::")


def test_workbench_wrong_scope_fails_before_evidence_mutation(tmp_path, monkeypatch) -> None:
    controller = WorkbenchController(tmp_path / "workspace")
    session_id, seed_id = _live_seed(controller)
    before = controller.sessions.load(session_id)["state"]
    valid = controller.workspace.local_actor_context(request_id="request::wrong-scope")
    wrong_scope = replace(valid, scope_id="workspace::other")
    monkeypatch.setattr(controller.workspace, "local_actor_context", lambda: wrong_scope)

    with pytest.raises(AuthorizationError, match="scope"):
        controller.submit_verified_evidence(
            session_id,
            seed_id,
            source_ref="reviewer:wrong-scope",
            operator_verified=True,
        )

    after = controller.sessions.load(session_id)["state"]
    assert after == before


def test_workbench_missing_evidence_capability_fails_before_mutation(
    tmp_path, monkeypatch
) -> None:
    controller = WorkbenchController(tmp_path / "workspace")
    session_id, seed_id = _live_seed(controller)
    before = controller.sessions.load(session_id)["state"]
    valid = controller.workspace.local_actor_context(request_id="request::no-evidence")
    without_evidence = replace(
        valid,
        capabilities=valid.capabilities - {EVIDENCE_VERIFY},
    )
    monkeypatch.setattr(controller.workspace, "local_actor_context", lambda: without_evidence)

    with pytest.raises(AuthorizationError, match="evidence.verify"):
        controller.submit_verified_evidence(
            session_id,
            seed_id,
            source_ref="reviewer:no-capability",
            operator_verified=True,
        )

    after = controller.sessions.load(session_id)["state"]
    assert after == before


def test_workbench_contradiction_requires_capability_before_mutation(
    tmp_path, monkeypatch
) -> None:
    controller = WorkbenchController(tmp_path / "workspace")
    session_id, seed_id = _live_seed(controller)
    before = controller.sessions.load(session_id)["state"]
    valid = controller.workspace.local_actor_context(request_id="request::no-contradiction")
    without_contradiction = replace(
        valid,
        capabilities=valid.capabilities - {CONTRADICTION_SUBMIT},
    )
    monkeypatch.setattr(
        controller.workspace,
        "local_actor_context",
        lambda: without_contradiction,
    )

    with pytest.raises(AuthorizationError, match="contradiction.submit"):
        controller.falsify_seed(session_id, seed_id)

    after = controller.sessions.load(session_id)["state"]
    assert after == before


def test_workbench_contradiction_is_attributable(tmp_path) -> None:
    controller = WorkbenchController(tmp_path / "workspace")
    session_id, seed_id = _live_seed(controller)

    result = controller.falsify_seed(session_id, seed_id)

    authz = result["authorization"]
    assert authz["authorized"] is True
    assert authz["scope_id"] == controller.workspace.workspace_id
    assert authz["capability"] == CONTRADICTION_SUBMIT

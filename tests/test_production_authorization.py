from __future__ import annotations

from dataclasses import replace

import pytest

from shadowseed.application.auth import (
    EVIDENCE_VERIFY,
    ActorContext,
    AuthorizationError,
    require_capability,
)
from shadowseed.application.workspace import WorkspaceService


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

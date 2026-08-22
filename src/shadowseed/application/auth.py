"""Production application authorization primitives.

The Validation Gate remains the only authority decision engine. This module only
answers whether a trusted product actor may invoke an authority-bearing command.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Mapping


SESSION_MANAGE = "session.manage"
EVIDENCE_VERIFY = "evidence.verify"
CONTRADICTION_SUBMIT = "contradiction.submit"
CONTRADICTION_RESOLVE = "contradiction.resolve"
WORKSPACE_BACKUP_RESTORE = "workspace.backup_restore"
WORKSPACE_INTEGRITY_RECOVER = "workspace.integrity_recover"

LOCAL_PRODUCTION_CAPABILITIES = frozenset(
    {
        "chat.use",
        SESSION_MANAGE,
        "feedback.record",
        EVIDENCE_VERIFY,
        CONTRADICTION_SUBMIT,
        CONTRADICTION_RESOLVE,
        "export.create",
        WORKSPACE_BACKUP_RESTORE,
        WORKSPACE_INTEGRITY_RECOVER,
    }
)


class AuthorizationError(PermissionError):
    """Raised before an unauthorized authority-bearing mutation reaches runtime."""


@dataclass(frozen=True)
class ActorContext:
    """Trusted actor metadata created by the product boundary, never form input."""

    actor_id: str
    scope_id: str
    capabilities: frozenset[str]
    auth_method: str
    assurance: Mapping[str, str] = field(default_factory=dict)
    request_id: str = ""
    policy_version: str = "production-authz-v1"

    def __post_init__(self) -> None:
        for name in ("actor_id", "scope_id", "auth_method", "request_id", "policy_version"):
            value = getattr(self, name)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{name} must be a non-empty string")
        object.__setattr__(self, "actor_id", self.actor_id.strip())
        object.__setattr__(self, "scope_id", self.scope_id.strip())
        object.__setattr__(self, "auth_method", self.auth_method.strip())
        object.__setattr__(self, "request_id", self.request_id.strip())
        object.__setattr__(self, "policy_version", self.policy_version.strip())
        object.__setattr__(
            self,
            "capabilities",
            frozenset(item.strip() for item in self.capabilities if item.strip()),
        )
        object.__setattr__(
            self,
            "assurance",
            MappingProxyType({str(k): str(v) for k, v in self.assurance.items()}),
        )

    def authorization_record(self, capability: str) -> dict[str, object]:
        return {
            "actor_id": self.actor_id,
            "scope_id": self.scope_id,
            "capability": capability,
            "auth_method": self.auth_method,
            "assurance": dict(self.assurance),
            "request_id": self.request_id,
            "policy_version": self.policy_version,
            "authorized": True,
        }


def require_capability(
    actor: ActorContext,
    *,
    scope_id: str,
    capability: str,
) -> dict[str, object]:
    """Fail closed on wrong scope or missing capability before runtime mutation."""

    if not isinstance(actor, ActorContext):
        raise AuthorizationError("trusted ActorContext is required")
    if actor.scope_id != scope_id:
        raise AuthorizationError("actor scope does not match target workspace")
    if capability not in actor.capabilities:
        raise AuthorizationError(f"missing required capability: {capability}")
    return actor.authorization_record(capability)

"""Authority profiles for Shadowseed runtime behavior.

Profiles do not bypass the Validation Gate. They describe how much of the
existing lifecycle may run automatically. The strict profile intentionally
matches the current production-local behavior so introducing profiles is
backwards-compatible.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any


class AuthorityProfileId(str, Enum):
    STRICT = "strict"
    ASSISTED = "assisted"
    AUTONOMOUS = "autonomous"
    OPEN = "open"


@dataclass(frozen=True)
class AuthorityProfile:
    id: AuthorityProfileId
    label: str
    description: str
    detect_mode: str
    validate_mode: str
    promote_mode: str
    surface_mode: str
    contradiction_mode: str
    require_operator_verified_evidence: bool
    auto_validate_recurrence: bool
    auto_validate_system_evidence: bool
    auto_promote_when_gate_allows: bool
    auto_surface_when_relevant: bool
    allow_unreviewed_system_evidence: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id.value,
            "label": self.label,
            "description": self.description,
            "detect_mode": self.detect_mode,
            "validate_mode": self.validate_mode,
            "promote_mode": self.promote_mode,
            "surface_mode": self.surface_mode,
            "contradiction_mode": self.contradiction_mode,
            "require_operator_verified_evidence": self.require_operator_verified_evidence,
            "auto_validate_recurrence": self.auto_validate_recurrence,
            "auto_validate_system_evidence": self.auto_validate_system_evidence,
            "auto_promote_when_gate_allows": self.auto_promote_when_gate_allows,
            "auto_surface_when_relevant": self.auto_surface_when_relevant,
            "allow_unreviewed_system_evidence": self.allow_unreviewed_system_evidence,
        }


STRICT_PROFILE = AuthorityProfile(
    id=AuthorityProfileId.STRICT,
    label="Controlled",
    description=(
        "Shadowseed detects and learns automatically, but authority-bearing "
        "validation remains user-controlled before a seed may influence chat."
    ),
    detect_mode="auto",
    validate_mode="manual",
    promote_mode="gate_after_manual_validation",
    surface_mode="gate_and_relevance",
    contradiction_mode="block_and_manual_resolution",
    require_operator_verified_evidence=True,
    auto_validate_recurrence=False,
    auto_validate_system_evidence=False,
    auto_promote_when_gate_allows=True,
    auto_surface_when_relevant=True,
)

ASSISTED_PROFILE = AuthorityProfile(
    id=AuthorityProfileId.ASSISTED,
    label="Assisted",
    description=(
        "Shadowseed automates low-risk lifecycle steps and asks the user only "
        "for authority-bearing checks that still need human confirmation."
    ),
    detect_mode="auto",
    validate_mode="mixed",
    promote_mode="gate",
    surface_mode="gate_and_relevance",
    contradiction_mode="block_and_assist",
    require_operator_verified_evidence=True,
    auto_validate_recurrence=True,
    auto_validate_system_evidence=True,
    auto_promote_when_gate_allows=True,
    auto_surface_when_relevant=True,
)

AUTONOMOUS_PROFILE = AuthorityProfile(
    id=AuthorityProfileId.AUTONOMOUS,
    label="Autonomous",
    description=(
        "Shadowseed may validate, activate, promote and surface seeds "
        "automatically when the configured Gate and point-of-use checks allow it."
    ),
    detect_mode="auto",
    validate_mode="auto",
    promote_mode="gate",
    surface_mode="gate_and_relevance",
    contradiction_mode="block_and_auto_check",
    require_operator_verified_evidence=False,
    auto_validate_recurrence=True,
    auto_validate_system_evidence=True,
    auto_promote_when_gate_allows=True,
    auto_surface_when_relevant=True,
)

OPEN_PROFILE = AuthorityProfile(
    id=AuthorityProfileId.OPEN,
    label="Open research",
    description=(
        "Maximum autonomy for exploratory runs. Gate and audit events remain "
        "active, but the runtime may accept unreviewed system evidence when the "
        "selected policy permits it."
    ),
    detect_mode="auto",
    validate_mode="auto",
    promote_mode="gate",
    surface_mode="gate_and_relevance",
    contradiction_mode="block_and_auto_check",
    require_operator_verified_evidence=False,
    auto_validate_recurrence=True,
    auto_validate_system_evidence=True,
    auto_promote_when_gate_allows=True,
    auto_surface_when_relevant=True,
    allow_unreviewed_system_evidence=True,
)


AUTHORITY_PROFILES: dict[AuthorityProfileId, AuthorityProfile] = {
    profile.id: profile
    for profile in (
        STRICT_PROFILE,
        ASSISTED_PROFILE,
        AUTONOMOUS_PROFILE,
        OPEN_PROFILE,
    )
}


def get_authority_profile(profile_id: str | AuthorityProfileId | None) -> AuthorityProfile:
    if profile_id is None:
        return STRICT_PROFILE
    try:
        key = AuthorityProfileId(str(profile_id))
    except ValueError as exc:
        raise ValueError(f"unknown authority profile: {profile_id}") from exc
    return AUTHORITY_PROFILES[key]

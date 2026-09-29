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
class AuthorityRuntimePolicy:
    """Resolved runtime behavior for one persisted authority profile.

    This object selects existing Gate policy semantics; it never implements a
    second authority decision path. An explicitly configured Gate policy always
    wins so research/compatibility callers remain deterministic.
    """

    profile_id: AuthorityProfileId
    gate_policy_id: str
    proactive_review: bool
    auto_surface_when_relevant: bool
    allow_unreviewed_system_evidence: bool

    def to_dict(self) -> dict[str, Any]:
        return {
            "profile_id": self.profile_id.value,
            "gate_policy_id": self.gate_policy_id,
            "proactive_review": self.proactive_review,
            "auto_surface_when_relevant": self.auto_surface_when_relevant,
            "allow_unreviewed_system_evidence": self.allow_unreviewed_system_evidence,
        }


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
        "Shadowseed tracks mature recurrence automatically and brings the user "
        "in when verified authority-bearing support is still required."
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
        "Shadowseed may let recurring seeds earn authority automatically through "
        "the exploratory Gate, then surface them only when point-of-use checks allow."
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
        "Maximum autonomy for exploratory runs. Recurrence may earn authority "
        "automatically; unreviewed system evidence is permitted only when an "
        "explicit producer and Gate policy support it."
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
        key = profile_id if isinstance(profile_id, AuthorityProfileId) else AuthorityProfileId(str(profile_id))
    except ValueError as exc:
        raise ValueError(f"unknown authority profile: {profile_id}") from exc
    return AUTHORITY_PROFILES[key]



def resolve_authority_runtime(
    profile_id: str | AuthorityProfileId | None,
    *,
    runtime_mode: str,
    configured_gate_policy_id: str | None = None,
) -> AuthorityRuntimePolicy:
    """Resolve profile intent onto the canonical Gate and surfacing machinery.

    Controlled remains exactly on the existing live evidence_backed policy.
    Assisted also keeps evidence-backed authority but can proactively surface
    review needs. Autonomous/Open opt into the existing exploratory Gate,
    where recurrence is a first-class support signal and can therefore raise
    authority without being mislabeled as external evidence.

    Evaluation sessions preserve their historical exploratory default. An
    explicit configured_gate_policy_id always wins.
    """

    if runtime_mode not in {"live", "evaluation"}:
        raise ValueError("runtime_mode must be 'live' or 'evaluation'")
    profile = get_authority_profile(profile_id)

    if configured_gate_policy_id:
        gate_policy_id = str(configured_gate_policy_id)
    elif runtime_mode == "evaluation":
        gate_policy_id = "exploratory"
    elif profile.id in {AuthorityProfileId.AUTONOMOUS, AuthorityProfileId.OPEN}:
        gate_policy_id = "exploratory"
    else:
        gate_policy_id = "evidence_backed"

    return AuthorityRuntimePolicy(
        profile_id=profile.id,
        gate_policy_id=gate_policy_id,
        proactive_review=(
            profile.id is AuthorityProfileId.ASSISTED
            and gate_policy_id == "evidence_backed"
        ),
        auto_surface_when_relevant=profile.auto_surface_when_relevant,
        allow_unreviewed_system_evidence=profile.allow_unreviewed_system_evidence,
    )

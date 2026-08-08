"""Simple tester profiles that configure surfacing without bypassing the Gate."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from shadowseed.application.models import SessionConfig


@dataclass(frozen=True)
class WorkbenchProfile:
    profile_id: str
    label: str
    description: str
    settings: dict[str, Any]

    def apply(self, base: SessionConfig | None = None, **overrides: Any) -> SessionConfig:
        values = (base or SessionConfig()).to_dict()
        values.update(self.settings)
        values.update({key: value for key, value in overrides.items() if value is not None})
        return SessionConfig.from_dict(values)


_PROFILES: dict[str, WorkbenchProfile] = {
    "demo": WorkbenchProfile(
        profile_id="demo",
        label="Demo",
        description="Deterministic fixture profile for onboarding and smoke checks.",
        settings={
            "backend": "fixture",
            "surface_threshold": 0.30,
            "surface_top_k": 2,
            "early_turn_margin": 0.10,
            "resurface_margin": 0.15,
            "recurrence_mode": "cluster",
        },
    ),
    "balanced": WorkbenchProfile(
        profile_id="balanced",
        label="Balanced",
        description="Default practical profile with bounded cross-turn influence.",
        settings={
            "surface_threshold": 0.30,
            "surface_top_k": 2,
            "early_turn_margin": 0.10,
            "resurface_margin": 0.15,
            "recurrence_mode": "cluster",
        },
    ),
    "conservative": WorkbenchProfile(
        profile_id="conservative",
        label="Conservative",
        description="Higher relevance bars and fewer surfaced seeds per turn.",
        settings={
            "surface_threshold": 0.55,
            "surface_top_k": 1,
            "early_turn_margin": 0.15,
            "resurface_margin": 0.20,
            "recurrence_mode": "cluster",
        },
    ),
    "exploratory": WorkbenchProfile(
        profile_id="exploratory",
        label="Exploratory",
        description="Shows more eligible perspectives while preserving Gate authority rules.",
        settings={
            "surface_threshold": 0.20,
            "surface_top_k": 3,
            "early_turn_margin": 0.05,
            "resurface_margin": 0.10,
            "recurrence_mode": "cluster",
        },
    ),
}


def get_profile(profile_id: str) -> WorkbenchProfile:
    try:
        return _PROFILES[profile_id]
    except KeyError as exc:
        raise ValueError(
            f"unknown Workbench profile {profile_id!r}; choose from {', '.join(_PROFILES)}"
        ) from exc


def list_profiles() -> tuple[WorkbenchProfile, ...]:
    return tuple(_PROFILES.values())

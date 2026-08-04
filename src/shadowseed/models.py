"""Stable Shadow Seed Learning domain models.

These enums, dataclasses, authority guards, snapshot validators, and serialized
contracts were extracted from :mod:`shadowseed.manager` without changing their
behavior. ``shadowseed.manager`` re-exports the public names for compatibility.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime
from enum import Enum
import math
from typing import Any, Mapping

import numpy as np


class SeedStatus(str, Enum):
    NEW = "NEW"
    ACTIVE = "ACTIVE"
    DECAYING = "DECAYING"
    DORMANT = "DORMANT"
    PROMOTED = "PROMOTED"
    EXPIRED = "EXPIRED"


class CandidateType(str, Enum):
    """Why a candidate absence was proposed.

    This is observability metadata only. It records what kind of gap the
    detector believed it found; it never affects trace, weight, evidence, or
    the Validation Gate. Closed vocabulary so audit logs stay legible.
    """

    MISSING_RELATION = "missing_relation"
    MISSING_BOUNDARY = "missing_boundary"
    UNSTATED_ASSUMPTION = "unstated_assumption"
    CONTRADICTION = "contradiction"
    ALTERNATIVE_HYPOTHESIS = "alternative_hypothesis"
    MISSING_DEPENDENCY = "missing_dependency"
    POSSIBLE_COMPLETION = "possible_completion"
    UNSPECIFIED = "unspecified"


@dataclass
class SeedOrigin:
    """Optional, audit-only record of *why* a seed was generated.

    Purely descriptive provenance. It makes the conceptual origin of a seed
    visible in the created-event and export, but carries no epistemic force:
    a convincing rationale here must still leave ``weight`` at ``0.0``. Weight
    can rise only through the Validation Gate, never from this metadata.
    """

    candidate_type: CandidateType = CandidateType.UNSPECIFIED
    detection_basis: str = ""
    context_ref: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "candidate_type": self.candidate_type.value,
            "detection_basis": self.detection_basis,
            "context_ref": self.context_ref,
        }


# Authority fields: only the Validation Gate transition path (SSLManager) may
# change these. They determine whether a seed can eventually influence behavior.
# trace, occurrence_count, and turns_dormant are observation/lifecycle-support
# fields and stay freely writable. authority_version is included so it cannot be
# assigned externally; it is managed automatically by _write_authority.
AUTHORITY_FIELDS: frozenset[str] = frozenset(
    {"weight", "status", "evidence_count", "contradiction_score", "authority_version"}
)

# The subset whose value actually changing marks an authority change (and bumps
# the version). Status is handled separately: only crossing the PROMOTED
# boundary counts, so ordinary lifecycle moves (ACTIVE/DORMANT/NEW) do not churn
# the authority version.
_VERSIONED_AUTHORITY_FIELDS: frozenset[str] = frozenset(
    {"weight", "contradiction_score", "evidence_count"}
)

# Authority range for a restored weight. Weight is clamped to [0.0, 1.0]
# everywhere it is written (every Gate/probe/decay path uses
# ``max(0.0, min(1.0, ...))``), so this is the invariant the current
# implementation and policies already enforce — restoration must not silently
# accept a snapshot claiming an out-of-range weight. Derived from that
# invariant, not an independent threshold.
WEIGHT_MIN: float = 0.0
WEIGHT_MAX: float = 1.0


def _is_int(value: Any) -> bool:
    """True for a genuine integer, rejecting ``bool``.

    ``bool`` is a subclass of ``int`` in Python, so ``isinstance(True, int)``
    is ``True``. Persisted counters must not silently accept ``True``/``False``.
    """

    return isinstance(value, int) and not isinstance(value, bool)


def _is_real_number(value: Any) -> bool:
    """True for a real (non-complex) number, rejecting ``bool``."""

    return isinstance(value, (int, float)) and not isinstance(value, bool)


def validate_seed_snapshot(data: Mapping[str, Any]) -> None:
    """Reject a malformed or internally inconsistent persisted seed snapshot.

    Defense-in-depth for the restoration boundary (deserialization/migration),
    *not* an authority decision: it never changes weight, never runs the Gate,
    never bumps the authority version, and never counts as evidence. It only
    confirms that ``data`` is a structurally valid, finite, self-consistent
    snapshot before ``from_dict`` reconstructs a seed from it.

    Raises a field-specific :class:`ValueError` or :class:`TypeError` on the
    first violation. Fields that ``from_dict`` supplies defaults for (counters,
    scores, status, ``authority_version``) are only checked when present, so
    legitimate legacy snapshots that omit them stay valid.
    """

    if not isinstance(data, Mapping):
        raise TypeError(f"seed snapshot must be a mapping, got {type(data).__name__}")

    # --- id: required, non-empty string ---
    if "id" not in data:
        raise ValueError("seed snapshot is missing required field 'id'")
    seed_id = data["id"]
    if not isinstance(seed_id, str):
        raise TypeError(f"seed 'id' must be a string, got {type(seed_id).__name__}")
    if not seed_id:
        raise ValueError("seed 'id' must be a non-empty string")

    # --- text: required, string ---
    if "text" not in data:
        raise ValueError("seed 'text' is missing")
    if not isinstance(data["text"], str):
        raise TypeError(f"seed 'text' must be a string, got {type(data['text']).__name__}")

    # --- embedding: numeric, non-empty, all finite ---
    if "embedding" not in data:
        raise ValueError("seed 'embedding' is missing")
    try:
        embedding = np.asarray(data["embedding"], dtype=float)
    except (TypeError, ValueError) as exc:
        raise TypeError(f"seed 'embedding' must be a numeric array: {exc}") from exc
    if embedding.size == 0:
        raise ValueError("seed 'embedding' must not be empty")
    if not np.all(np.isfinite(embedding)):
        raise ValueError("seed 'embedding' must contain only finite values (no NaN/inf)")

    # --- trace: finite, non-negative ---
    if "trace" in data:
        trace = data["trace"]
        if not _is_real_number(trace):
            raise TypeError(f"seed 'trace' must be a number, got {type(trace).__name__}")
        if not math.isfinite(trace):
            raise ValueError("seed 'trace' must be finite (no NaN/inf)")
        if trace < 0:
            raise ValueError(f"seed 'trace' must not be negative, got {trace}")

    # --- integer counters: integer (not bool), non-negative ---
    for name in ("occurrence_count", "turns_dormant", "evidence_count", "authority_version"):
        if name in data:
            value = data[name]
            if not _is_int(value):
                raise TypeError(
                    f"seed '{name}' must be an integer (bool is not accepted), "
                    f"got {type(value).__name__}"
                )
            if value < 0:
                raise ValueError(f"seed '{name}' must be non-negative, got {value}")

    # --- weight: finite, within the authority range ---
    if "weight" in data:
        weight = data["weight"]
        if not _is_real_number(weight):
            raise TypeError(f"seed 'weight' must be a number, got {type(weight).__name__}")
        if not math.isfinite(weight):
            raise ValueError("seed 'weight' must be finite (no NaN/inf)")
        if not (WEIGHT_MIN <= weight <= WEIGHT_MAX):
            raise ValueError(
                f"seed 'weight' must be within the authority range "
                f"[{WEIGHT_MIN}, {WEIGHT_MAX}], got {weight}"
            )

    # --- contradiction_score: finite, non-negative ---
    if "contradiction_score" in data:
        score = data["contradiction_score"]
        if not _is_real_number(score):
            raise TypeError(
                f"seed 'contradiction_score' must be a number, got {type(score).__name__}"
            )
        if not math.isfinite(score):
            raise ValueError("seed 'contradiction_score' must be finite (no NaN/inf)")
        if score < 0:
            raise ValueError(f"seed 'contradiction_score' must not be negative, got {score}")

    # --- status: a valid SeedStatus ---
    status_value = data.get("status", SeedStatus.NEW.value)
    if isinstance(status_value, SeedStatus):
        status = status_value
    else:
        try:
            status = SeedStatus(status_value)
        except ValueError as exc:
            raise ValueError(f"seed 'status' is not a valid SeedStatus: {status_value!r}") from exc

    # --- origin: when present, a mapping with a valid CandidateType ---
    origin_data = data.get("origin")
    if origin_data is not None:
        if not isinstance(origin_data, Mapping):
            raise TypeError(
                f"seed 'origin' must be a mapping when present, "
                f"got {type(origin_data).__name__}"
            )
        candidate_type = origin_data.get("candidate_type", CandidateType.UNSPECIFIED.value)
        if not isinstance(candidate_type, CandidateType):
            try:
                CandidateType(candidate_type)
            except ValueError as exc:
                raise ValueError(
                    f"seed 'origin.candidate_type' is not a valid CandidateType: "
                    f"{candidate_type!r}"
                ) from exc
        detection_basis = origin_data.get("detection_basis", "")
        if not isinstance(detection_basis, str):
            raise TypeError(
                f"seed 'origin.detection_basis' must be a string, "
                f"got {type(detection_basis).__name__}"
            )
        context_ref = origin_data.get("context_ref")
        if context_ref is not None and not isinstance(context_ref, str):
            raise TypeError(
                f"seed 'origin.context_ref' must be a string or None, "
                f"got {type(context_ref).__name__}"
            )

    # --- cross-field invariant: an EXPIRED seed is terminal with zero weight ---
    if status == SeedStatus.EXPIRED and "weight" in data and data["weight"] != 0:
        raise ValueError(
            f"an EXPIRED seed must have zero weight, got {data['weight']} "
            f"(EXPIRED is terminal; restoration must preserve that)"
        )


@dataclass
class ShadowSeed:
    id: str
    text: str
    embedding: np.ndarray
    trigger_keywords: list[str] = field(default_factory=list)
    trace: float = 2.0
    occurrence_count: int = 1
    turns_dormant: int = 0
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())
    origin: SeedOrigin | None = None
    # Authority fields are init=False: they cannot be set through the
    # constructor, closing the construction bypass. A seed is always born
    # weightless; authority is reached only through the Gate, and tests use
    # unsafe_set_authority(...).
    weight: float = field(default=0.0, init=False)
    evidence_count: int = field(default=0, init=False)
    contradiction_score: float = field(default=0.0, init=False)
    status: SeedStatus = field(default=SeedStatus.NEW, init=False)
    # Monotonic counter stamped whenever authority (weight, evidence,
    # contradiction, or promotion state) changes. A point-of-use decision
    # references it so a stale authorization can be detected on replay.
    authority_version: int = field(default=0, init=False)
    _authority_sealed: bool = field(default=False, repr=False, compare=False, init=False)

    def __post_init__(self) -> None:
        # Seal after construction so field defaults can be set during init, but
        # later direct assignments are guarded.
        object.__setattr__(self, "_authority_sealed", True)

    def __setattr__(self, name: str, value: Any) -> None:
        if name in AUTHORITY_FIELDS and getattr(self, "_authority_sealed", False):
            raise AttributeError(
                f"'{name}' is authority state and cannot be assigned directly. "
                "Authority changes only through the SSLManager Validation Gate "
                "transition path. In tests or benchmarks, use "
                "ShadowSeed.unsafe_set_authority(...)."
            )
        object.__setattr__(self, name, value)

    def _write_authority(self, changes: dict[str, Any]) -> None:
        """Apply an authority change and bump the version when it matters.

        This is the single low-level writer. It bypasses the ``__setattr__``
        guard on purpose; callers are the manager's transition path and the
        explicit unsafe test hook. The version bumps only when an
        authority-determining value actually changes (weight, evidence, or
        contradiction score) or when the PROMOTED boundary is crossed — not on
        an unchanged rewrite, and not on a pure lifecycle status move.
        """

        promoted_before = self.status == SeedStatus.PROMOTED
        value_changed = False
        for name, value in changes.items():
            if name == "authority_version":
                raise KeyError("authority_version is managed automatically")
            if name not in AUTHORITY_FIELDS:
                raise KeyError(f"'{name}' is not an authority field")
            if name in _VERSIONED_AUTHORITY_FIELDS and value != getattr(self, name):
                value_changed = True
            object.__setattr__(self, name, value)
        promoted_after = self.status == SeedStatus.PROMOTED
        if value_changed or promoted_before != promoted_after:
            object.__setattr__(self, "authority_version", self.authority_version + 1)

    def unsafe_set_authority(
        self,
        *,
        weight: float | None = None,
        status: "SeedStatus | None" = None,
        evidence_count: int | None = None,
        contradiction_score: float | None = None,
    ) -> None:
        """Explicitly unsafe, unsupported authority setter for tests/benchmarks.

        This is not a normal API and production code must never call it (a static
        test enforces that for this repository). It exists so tests can construct
        edge-case authority states without a full Gate run. It does not claim to
        make mutation *technically* impossible for third-party callers — it is an
        explicit, clearly-named escape hatch. It bumps the authority version like
        any other change; use :meth:`from_dict` to restore a persisted version.
        """

        changes: dict[str, Any] = {}
        if weight is not None:
            changes["weight"] = weight
        if status is not None:
            changes["status"] = status
        if evidence_count is not None:
            changes["evidence_count"] = evidence_count
        if contradiction_score is not None:
            changes["contradiction_score"] = contradiction_score
        self._write_authority(changes)

    def _restore_authority(
        self,
        *,
        weight: float,
        evidence_count: int,
        contradiction_score: float,
        status: "SeedStatus",
        authority_version: int,
    ) -> None:
        """Restore a persisted authority snapshot exactly, version included.

        Used only by :meth:`from_dict`. Unlike a Gate transition this does not
        recompute or increment the version — it reinstates the stored one — so a
        round-trip is lossless. It is deserialization, not an authority decision.
        """

        object.__setattr__(self, "weight", float(weight))
        object.__setattr__(self, "evidence_count", int(evidence_count))
        object.__setattr__(self, "contradiction_score", float(contradiction_score))
        object.__setattr__(self, "status", SeedStatus(status))
        object.__setattr__(self, "authority_version", int(authority_version))

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data.pop("_authority_sealed", None)
        data["embedding"] = self.embedding.tolist()
        data["status"] = self.status.value
        data["origin"] = self.origin.to_dict() if self.origin is not None else None
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ShadowSeed":
        """Reconstruct a seed from its serialized form (deserialization/migration).

        Restores the full authority snapshot — weight, evidence count,
        contradiction score, status, and the original ``authority_version`` —
        without treating the restoration as a new Gate transition. This is the
        documented migration path required now that authority fields are
        ``init=False``; ``ShadowSeed(**saved)`` intentionally no longer works.

        The snapshot is validated first (see :func:`validate_seed_snapshot`), so
        a malformed or internally inconsistent snapshot raises before any object
        is constructed. Validation is defense-in-depth for deserialization; it
        does not run the Gate, change authority, or bump the version.
        """

        validate_seed_snapshot(data)
        origin_data = data.get("origin")
        origin = (
            SeedOrigin(
                candidate_type=CandidateType(origin_data.get("candidate_type", "unspecified")),
                detection_basis=origin_data.get("detection_basis", ""),
                context_ref=origin_data.get("context_ref"),
            )
            if origin_data
            else None
        )
        seed = cls(
            id=data["id"],
            text=data["text"],
            embedding=np.asarray(data["embedding"], dtype=float),
            trigger_keywords=list(data.get("trigger_keywords", [])),
            trace=float(data.get("trace", 2.0)),
            occurrence_count=int(data.get("occurrence_count", 1)),
            turns_dormant=int(data.get("turns_dormant", 0)),
            created_at=data.get("created_at") or datetime.now().isoformat(),
            updated_at=data.get("updated_at") or datetime.now().isoformat(),
            origin=origin,
        )
        seed._restore_authority(
            weight=data.get("weight", 0.0),
            evidence_count=data.get("evidence_count", 0),
            contradiction_score=data.get("contradiction_score", 0.0),
            status=data.get("status", SeedStatus.NEW.value),
            authority_version=data.get("authority_version", 0),
        )
        return seed


@dataclass
class Constellation:
    members: list[str]
    centroid: list[float]
    combined_weight: float
    id: str = ""
    label: str = ""
    probe_type: str = "socratic"

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["member_ids"] = list(self.members)
        return data


@dataclass
class SeedEvent:
    event_type: str
    seed_id: str
    detail: dict[str, Any]
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class ValidationGateResult:
    seed_id: str
    status_before: str
    status_after: str
    weight_before: float
    weight_after: float
    occurrence_count: int
    evidence_count: int
    internal_recognition_passed: bool
    external_evidence_passed: bool
    contradiction_free: bool
    external_evidence_applied: bool
    contradiction_applied: bool
    promoted: bool
    verdict: str
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ValidationGateFlags:
    internal_recognition_passed: bool
    external_evidence_passed: bool
    contradiction_free: bool


class ProbeType(str, Enum):
    """Which probe instrument produced the outcome."""

    FOLLOW_UP = "follow_up"
    RETRIEVAL = "retrieval"
    DIALECTIC = "dialectic"
    GENERAL = "general"


class ProbeOutcome(str, Enum):
    """Outcome of a probe evaluation.

    Probe feedback is deliberately weaker than the Validation Gate. A probe may
    nudge a seed's weight up or down, but it cannot promote a seed on its own.
    It can demote a promoted seed back to ACTIVE when repeated poor outcomes
    drive the weight back below the promotion threshold.
    """

    REWARD = "reward"
    PENALTY = "penalty"
    NEUTRAL = "neutral"


@dataclass
class ProbeFeedbackResult:
    """Structured record of a single probe-feedback event."""

    seed_id: str
    probe_type: str
    outcome: str
    weight_before: float
    weight_after: float
    delta_applied: float
    status_before: str
    status_after: str
    demoted: bool
    skipped: bool
    skip_reason: str
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


__all__ = [
    "AUTHORITY_FIELDS",
    "CandidateType",
    "Constellation",
    "ProbeFeedbackResult",
    "ProbeOutcome",
    "ProbeType",
    "SeedEvent",
    "SeedOrigin",
    "SeedStatus",
    "ShadowSeed",
    "ValidationGateFlags",
    "ValidationGateResult",
    "WEIGHT_MAX",
    "WEIGHT_MIN",
    "validate_seed_snapshot",
]

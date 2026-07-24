"""Validation Gate contracts for Shadow Seed Learning.

Typed signals describe observations, named policies propose authority changes,
and immutable Gate events record what the Gate applied. The runtime compatibility
adapter routes the historical boolean API through the same signal-native engine.
"""

from __future__ import annotations

from shadowseed.gate.contradictions import (
    BLOCKING_STATUSES,
    ContradictionRecord,
    ContradictionStatus,
)
from shadowseed.gate.events import ContradictionState, GateDecision, GateEvent
from shadowseed.gate.policies import (
    DEFAULT_POLICY_ID,
    EXAMPLE_POLICY_IDS,
    EvidenceBackedPolicy,
    ExploratoryPolicy,
    GateDecisionProposal,
    GatePolicy,
    LegacyEvidenceRequiredPolicy,
    ProposedVerdict,
    default_policy,
    resolve_policy,
)
from shadowseed.gate.signals import (
    SignalDirection,
    SignalKind,
    ValidationSignal,
)

__all__ = [
    "SignalKind",
    "SignalDirection",
    "ValidationSignal",
    "GatePolicy",
    "GateDecisionProposal",
    "ProposedVerdict",
    "ExploratoryPolicy",
    "EvidenceBackedPolicy",
    "LegacyEvidenceRequiredPolicy",
    "default_policy",
    "resolve_policy",
    "DEFAULT_POLICY_ID",
    "EXAMPLE_POLICY_IDS",
    "GateEvent",
    "GateDecision",
    "ContradictionState",
    "ContradictionRecord",
    "ContradictionStatus",
    "BLOCKING_STATUSES",
]

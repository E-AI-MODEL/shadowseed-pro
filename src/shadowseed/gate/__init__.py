"""Validation Gate contracts for Shadow Seed Learning.

This package defines the canonical data contracts every authority decision uses,
before the existing mutation paths are migrated onto them (issue #10 of the
Validation Gate alignment; see ``docs/architecture/adr/ADR-001-validation-gate-authority.md``).

Three concepts live here:

- :mod:`shadowseed.gate.signals` — typed ``ValidationSignal`` inputs. A signal
  records *what was observed* (recurrence, SSOT, human feedback, retrieval,
  dialectic, probe, task outcome, contradiction, contradiction resolution). A
  signal never grants authority by itself.
- :mod:`shadowseed.gate.policies` — named ``GatePolicy`` objects. A policy reads
  a set of signals plus the current authority state and *proposes* a decision.
  Policies never mutate anything; only the Gate applies transitions.
- :mod:`shadowseed.gate.events` — the immutable ``GateEvent`` record. Every Gate
  invocation produces one, capturing the typed inputs, the policy, the
  before/after authority state, the contradiction state, and the reason.

Nothing in this package is wired into ``SSLManager`` yet. Wiring the runtime
onto these contracts is issues #11 and #12.
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

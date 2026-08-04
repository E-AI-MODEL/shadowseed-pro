"""Regression tests for the single executable Validation Gate path."""

from __future__ import annotations

import numpy as np
import pytest

from shadowseed.gate import (
    GateDecision,
    SignalDirection,
    SignalKind,
    ValidationSignal,
)
from shadowseed.gate.signals import recurrence_signal
from shadowseed.manager import SSLManager


def _manager(**kwargs) -> SSLManager:
    return SSLManager(
        embedding_fn=lambda _text: np.array([1.0, 0.0, 0.0]),
        **kwargs,
    )


def _recurrent_seed(manager: SSLManager) -> str:
    seed_id = manager.add_or_update_seed("A relevant boundary is missing.")
    manager.add_or_update_seed("A relevant boundary is missing.")
    manager.add_or_update_seed("A relevant boundary is missing.")
    return seed_id


def test_legacy_boolean_api_uses_one_real_policy_event_per_call():
    manager = _manager()
    seed_id = _recurrent_seed(manager)

    first = manager.run_validation_gate_detailed(seed_id, external_evidence=True)
    second = manager.run_validation_gate_detailed(seed_id, external_evidence=True)

    assert first.verdict == "blocked"
    assert second.verdict == "validated"
    assert len(manager.gate_events) == 2
    assert len(manager.validation_log) == 2
    assert all(
        event.policy_id == "legacy_evidence_required"
        for event in manager.gate_events
    )
    assert {signal.kind for signal in manager.gate_events[-1].signals} == {
        SignalKind.RECURRENCE,
        SignalKind.SSOT,
    }


def test_legacy_policy_preserves_manager_validation_increment():
    manager = _manager(validation_increment=0.35, promotion_threshold=0.3)
    seed_id = _recurrent_seed(manager)

    assert manager.run_validation_gate(seed_id, external_evidence=True) is None
    assert manager.run_validation_gate(seed_id, external_evidence=True) is True

    assert manager.get_seed(seed_id).weight == 0.35
    assert manager.gate_events[-1].policy_id == "legacy_evidence_required"


def test_named_policy_is_executed_not_only_written_to_event():
    manager = _manager()
    seed_id = manager.add_or_update_seed("A relevant boundary is missing.")

    result = manager.run_validation_gate_detailed(
        seed_id,
        signals=[recurrence_signal(3, threshold=2)],
        policy_id="exploratory",
    )

    assert result.verdict == "validated"
    assert manager.gate_events[-1].policy_id == "exploratory"
    assert manager.get_seed(seed_id).weight > 0.0


def test_private_legacy_core_is_redirected_to_signal_gate():
    manager = _manager()
    seed_id = _recurrent_seed(manager)

    first = manager._run_validation_gate_core(
        seed_id,
        external_evidence=True,
    )
    second = manager._run_validation_gate_core(
        seed_id,
        external_evidence=True,
    )

    assert first.verdict == "blocked"
    assert second.verdict == "validated"
    assert len(manager.gate_events) == 2
    assert all(
        event.policy_id == "legacy_evidence_required"
        for event in manager.gate_events
    )


def test_legacy_policy_blocks_unverified_external_signal():
    manager = _manager()
    seed_id = _recurrent_seed(manager)

    result = manager.run_validation_gate_detailed(
        seed_id,
        signals=[
            recurrence_signal(3, threshold=2),
            ValidationSignal(kind=SignalKind.SSOT, verified=False),
        ],
    )

    assert result.verdict == "blocked"
    assert result.external_evidence_passed is False
    assert result.external_evidence_applied is False
    assert manager.get_seed(seed_id).weight == 0.0
    assert manager.get_seed(seed_id).evidence_count == 0


def test_exploratory_policy_blocks_unverified_external_support_alone():
    manager = _manager()
    seed_id = manager.add_or_update_seed("A source boundary is missing.")
    signal = ValidationSignal(kind=SignalKind.RETRIEVAL, verified=False)

    event = manager.submit_signals(seed_id, [signal], policy_id="exploratory")

    assert event.decision is GateDecision.BLOCKED
    assert event.signals == (signal,)
    assert manager.get_seed(seed_id).weight == 0.0
    assert manager.get_seed(seed_id).evidence_count == 0
    result = manager.validation_log[-1]
    assert result.external_evidence_passed is False
    assert result.external_evidence_applied is False


def test_exploratory_policy_accepts_verified_external_support():
    manager = _manager()
    seed_id = manager.add_or_update_seed("A source boundary is missing.")

    event = manager.submit_signals(
        seed_id,
        [ValidationSignal(kind=SignalKind.RETRIEVAL, verified=True)],
        policy_id="exploratory",
    )

    assert event.decision is GateDecision.VALIDATED
    assert manager.get_seed(seed_id).weight > 0.0
    assert manager.get_seed(seed_id).evidence_count == 1
    result = manager.validation_log[-1]
    assert result.external_evidence_passed is True
    assert result.external_evidence_applied is True


def test_mixed_external_signals_count_only_verified_support():
    manager = _manager()
    seed_id = manager.add_or_update_seed("A source boundary is missing.")

    manager.submit_signals(
        seed_id,
        [
            ValidationSignal(kind=SignalKind.SSOT, verified=False),
            ValidationSignal(kind=SignalKind.RETRIEVAL, verified=True),
            ValidationSignal(kind=SignalKind.HUMAN_FEEDBACK, verified=False),
        ],
        policy_id="exploratory",
    )

    assert manager.get_seed(seed_id).evidence_count == 1


def test_recurrence_can_validate_without_promoting_unverified_signal_to_evidence():
    manager = _manager()
    seed_id = manager.add_or_update_seed("A recurring boundary is missing.")
    unverified = ValidationSignal(kind=SignalKind.SSOT, verified=False)

    event = manager.submit_signals(
        seed_id,
        [recurrence_signal(3, threshold=2), unverified],
        policy_id="exploratory",
    )

    assert event.decision is GateDecision.VALIDATED
    assert unverified in event.signals
    assert manager.get_seed(seed_id).evidence_count == 0
    result = manager.validation_log[-1]
    assert result.internal_recognition_passed is True
    assert result.external_evidence_passed is False
    assert result.external_evidence_applied is False


def test_contradiction_boolean_synthesizes_opposition_when_supplied_signal_is_not_opposing():
    manager = _manager()
    seed_id = _recurrent_seed(manager)
    non_opposing = ValidationSignal(
        kind=SignalKind.CONTRADICTION,
        direction=SignalDirection.SUPPORT,
        reason="caller supplied a non-opposing contradiction signal",
    )

    result = manager.run_validation_gate_detailed(
        seed_id,
        external_evidence=True,
        contradiction=True,
        signals=[non_opposing],
    )

    assert result.verdict == "contradicted"
    assert result.contradiction_applied is True
    assert any(
        signal.kind is SignalKind.CONTRADICTION
        and signal.direction is SignalDirection.OPPOSE
        for signal in manager.gate_events[-1].signals
    )


def test_legacy_policy_blocks_while_a_contradiction_record_remains_open():
    manager = _manager()
    seed_id = _recurrent_seed(manager)

    contradicted = manager.run_validation_gate_detailed(seed_id, contradiction=True)
    assert contradicted.verdict == "contradicted"

    manager.add_or_update_seed("A relevant boundary is missing.")
    manager.add_or_update_seed("A relevant boundary is missing.")
    first = manager.run_validation_gate_detailed(seed_id, external_evidence=True)
    second = manager.run_validation_gate_detailed(seed_id, external_evidence=True)

    assert first.verdict == "blocked"
    assert second.verdict == "blocked"
    assert first.contradiction_free is False
    assert second.contradiction_free is False
    assert manager.get_seed(seed_id).weight == 0.0
    assert manager._contradiction_state(manager.get_seed(seed_id)).blocking is True


# --------------------------------------------------------------------------- #
# P1: contradiction=True must synthesize an opposing contradiction regardless   #
# of a non-opposing CONTRADICTION signal supplied by the caller.                #
# --------------------------------------------------------------------------- #


def _opposing(signals) -> list[ValidationSignal]:
    return [
        signal
        for signal in signals
        if signal.kind is SignalKind.CONTRADICTION
        and signal.direction is SignalDirection.OPPOSE
    ]


@pytest.mark.parametrize(
    "supplied, label",
    [
        pytest.param(
            ValidationSignal(
                kind=SignalKind.CONTRADICTION,
                direction=SignalDirection.SUPPORT,
                reason="non-opposing SUPPORT contradiction",
            ),
            "support",
            id="direction_support",
        ),
        pytest.param(
            ValidationSignal(
                kind=SignalKind.CONTRADICTION,
                direction=SignalDirection.NEUTRAL,
                reason="non-opposing NEUTRAL contradiction",
            ),
            "neutral",
            id="direction_neutral",
        ),
        pytest.param(
            # ValidationSignal.direction defaults to SUPPORT, so a caller who
            # omits it supplies a non-opposing contradiction by accident.
            ValidationSignal(
                kind=SignalKind.CONTRADICTION,
                reason="contradiction signal with default direction",
            ),
            "default",
            id="direction_default",
        ),
    ],
)
def test_non_opposing_contradiction_signal_does_not_suppress_synthesis(supplied, label):
    """A supplied CONTRADICTION signal that does not oppose must not cancel the
    opposing contradiction required by ``contradiction=True``."""

    manager = _manager()
    seed_id = _recurrent_seed(manager)

    result = manager.run_validation_gate_detailed(
        seed_id,
        external_evidence=True,
        contradiction=True,
        signals=[supplied],
    )

    assert result.verdict == "contradicted", label
    assert result.contradiction_applied is True
    # The opposing contradiction was synthesized and recorded on the event...
    recorded = _opposing(manager.gate_events[-1].signals)
    assert len(recorded) == 1
    # ...the caller's non-opposing signal is preserved for audit...
    assert supplied in manager.gate_events[-1].signals
    # ...and the contradiction actually took effect on authority.
    assert manager.get_seed(seed_id).weight == 0.0
    assert manager._contradiction_state(manager.get_seed(seed_id)).blocking is True


def test_existing_opposing_contradiction_is_not_duplicated():
    """When the caller already supplies an opposing contradiction, no second one
    is synthesized."""

    manager = _manager()
    seed_id = _recurrent_seed(manager)
    supplied = ValidationSignal(
        kind=SignalKind.CONTRADICTION,
        direction=SignalDirection.OPPOSE,
        reason="caller supplied the opposing contradiction",
    )

    result = manager.run_validation_gate_detailed(
        seed_id,
        contradiction=True,
        signals=[supplied],
    )

    assert result.verdict == "contradicted"
    recorded = _opposing(manager.gate_events[-1].signals)
    assert len(recorded) == 1
    assert recorded[0] is supplied
    # Exactly one contradiction record was opened, not two.
    assert len(manager.contradictions_for(seed_id)) == 1


def test_authority_returns_only_through_the_resolution_route():
    """An open blocking contradiction cannot be walked around by recurrence or
    accumulated evidence; authority returns only after a recorded resolution."""

    manager = _manager()
    seed_id = _recurrent_seed(manager)
    assert manager.run_validation_gate_detailed(seed_id, contradiction=True).verdict == (
        "contradicted"
    )

    # Rebuild recurrence, and accumulate enough verified evidence that the only
    # remaining reason to refuse is the open contradiction itself. Both calls
    # must still be blocked.
    for _ in range(3):
        manager.add_or_update_seed("A relevant boundary is missing.")
    first = manager.run_validation_gate_detailed(seed_id, external_evidence=True)
    second = manager.run_validation_gate_detailed(seed_id, external_evidence=True)
    assert (first.verdict, second.verdict) == ("blocked", "blocked")
    # Evidence and recurrence thresholds are satisfied by now, so this is the
    # contradiction blocking — not a missing-evidence block.
    assert second.internal_recognition_passed is True
    assert second.external_evidence_passed is True
    assert second.contradiction_free is False
    assert manager.get_seed(seed_id).weight == 0.0

    # The intended route: a recorded resolution basis, then Gate revalidation.
    manager.resolve_contradiction(seed_id, basis="independent source confirmed the gap")
    assert manager._contradiction_state(manager.get_seed(seed_id)).blocking is False

    after = manager.run_validation_gate_detailed(seed_id, external_evidence=True)
    assert after.verdict in {"validated", "promoted"}
    assert manager.get_seed(seed_id).weight > 0.0


# --------------------------------------------------------------------------- #
# Structure: one visible Gate implementation, no import-time method swapping.   #
# --------------------------------------------------------------------------- #


GATE_METHODS = (
    "submit_signals",
    "run_validation_gate",
    "run_validation_gate_detailed",
    "_run_validation_gate_core",
    "_log_validation_from_signals",
)


@pytest.mark.parametrize("method_name", GATE_METHODS)
def test_gate_methods_are_defined_on_the_manager_not_installed(method_name):
    """The Gate methods must be real ``SSLManager`` methods declared in
    manager.py, not functions assigned onto the class at import time."""

    import inspect
    import pathlib

    method = getattr(SSLManager, method_name)
    assert method.__qualname__ == f"SSLManager.{method_name}", (
        f"{method_name} is not declared on SSLManager (qualname "
        f"{method.__qualname__!r}) — it looks installed rather than defined."
    )
    source_file = pathlib.Path(inspect.getsourcefile(method)).name
    assert source_file == "manager.py", (
        f"{method_name} resolves to {source_file}, not manager.py"
    )


def test_package_import_installs_nothing_onto_the_manager():
    """Importing the package must not rewrite SSLManager, and no installer
    helper may exist to do so."""

    import importlib

    import shadowseed
    from shadowseed.gate import runtime_adapter, verified_logging

    before = {name: getattr(SSLManager, name) for name in GATE_METHODS}
    importlib.reload(shadowseed)
    for name, original in before.items():
        assert getattr(SSLManager, name) is original, (
            f"importing shadowseed replaced SSLManager.{name}"
        )

    for module in (runtime_adapter, verified_logging):
        installers = [n for n in dir(module) if n.startswith("install_")]
        assert not installers, f"{module.__name__} still exposes {installers}"


# --------------------------------------------------------------------------- #
# Adversarial review findings (2026-08-04).                                     #
# --------------------------------------------------------------------------- #


def test_resolution_signal_alone_cannot_lift_an_open_contradiction():
    """A CONTRADICTION_RESOLUTION signal is not a resolution. Only
    ``resolve_contradiction`` closes records; until then the Gate blocks even
    with recurrence and verified evidence present."""

    manager = _manager()
    seed_id = _recurrent_seed(manager)
    manager.run_validation_gate_detailed(seed_id, contradiction=True)
    assert manager._contradiction_state(manager.get_seed(seed_id)).blocking is True

    event = manager.submit_signals(
        seed_id,
        [
            recurrence_signal(5, threshold=2),
            ValidationSignal(kind=SignalKind.CONTRADICTION_RESOLUTION, verified=True),
            ValidationSignal(kind=SignalKind.SSOT, verified=True),
        ],
        policy_id="exploratory",
    )

    assert event.decision is GateDecision.BLOCKED
    assert manager.get_seed(seed_id).weight == 0.0
    # The record is untouched: a signal never closes it.
    assert manager._contradiction_state(manager.get_seed(seed_id)).blocking is True
    assert len(manager.open_contradictions(seed_id)) == 1


def test_blocked_by_open_contradiction_is_not_logged_as_contradiction_free():
    """A generic-policy call blocked by an open record returns BLOCKED, not
    CONTRADICTED — the derived log must still report contradiction_free False."""

    manager = _manager()
    seed_id = _recurrent_seed(manager)
    manager.run_validation_gate_detailed(seed_id, contradiction=True)

    manager.submit_signals(
        seed_id,
        [recurrence_signal(5, threshold=2)],
        policy_id="exploratory",
    )

    result = manager.validation_log[-1]
    assert result.verdict == "blocked"
    assert result.contradiction_free is False


def test_adapter_must_follow_the_legacy_policy_proposal(monkeypatch):
    """The adapter may not re-derive the legacy verdict. With the thresholds
    demonstrably satisfied, a policy that proposes BLOCK must still block —
    which the old second decision implementation would not have done."""

    from shadowseed.gate.policies import (
        GateDecisionProposal,
        LegacyEvidenceRequiredPolicy,
        ProposedVerdict,
    )

    manager = _manager()
    seed_id = _recurrent_seed(manager)
    # Accumulate evidence so the historical thresholds are met on the next call;
    # without the sentinel this call validates (pinned by the tests above).
    manager.run_validation_gate_detailed(seed_id, external_evidence=True)

    def _sentinel_block(self, signals, authority):
        return GateDecisionProposal(
            self.policy_id,
            ProposedVerdict.BLOCK,
            reason="sentinel refusal",
        )

    monkeypatch.setattr(LegacyEvidenceRequiredPolicy, "propose", _sentinel_block)
    result = manager.run_validation_gate_detailed(seed_id, external_evidence=True)

    # The thresholds themselves are still satisfied (these come from the same
    # policy object, which is not patched) ...
    assert result.internal_recognition_passed is True
    assert result.external_evidence_passed is True
    # ... yet the Gate blocked, because the policy's proposal is what decides.
    assert result.verdict == "blocked"
    assert manager.get_seed(seed_id).weight == 0.0
    assert manager.gate_events[-1].policy_id == "legacy_evidence_required"


def test_expired_seed_with_open_contradiction_reports_it_in_the_fallback_result():
    """The fallback result (no validation_log entry) must not claim
    contradiction_free while a record is still open."""

    from shadowseed.manager import SeedStatus

    manager = _manager()
    seed_id = _recurrent_seed(manager)
    manager.run_validation_gate_detailed(seed_id, contradiction=True)
    assert manager._contradiction_state(manager.get_seed(seed_id)).blocking is True

    # An EXPIRED seed under an explicit public policy takes the fallback path.
    manager.get_seed(seed_id).unsafe_set_authority(status=SeedStatus.EXPIRED)
    logged_before = len(manager.validation_log)
    result = manager.run_validation_gate_detailed(
        seed_id,
        signals=[recurrence_signal(5, threshold=2)],
        policy_id="exploratory",
    )

    assert len(manager.validation_log) == logged_before  # fallback path taken
    assert result.verdict == "expired"
    assert result.contradiction_free is False
    assert manager.get_seed(seed_id).weight == 0.0


@pytest.mark.parametrize(
    "direction",
    [SignalDirection.NEUTRAL, SignalDirection.OPPOSE],
    ids=["neutral", "oppose"],
)
def test_external_evidence_boolean_survives_a_non_supporting_verified_signal(direction):
    """A verified but non-supporting external signal must not cancel the
    synthesized support that external_evidence=True asks for."""

    manager = _manager()
    seed_id = _recurrent_seed(manager)
    supplied = ValidationSignal(
        kind=SignalKind.SSOT,
        direction=direction,
        verified=True,
        reason="verified but not supporting",
    )

    manager.run_validation_gate_detailed(
        seed_id, external_evidence=True, signals=[supplied]
    )
    manager.run_validation_gate_detailed(seed_id, external_evidence=True)

    # The boolean still had effect: evidence accumulated and the seed validated.
    assert manager.get_seed(seed_id).evidence_count >= 2
    assert manager.get_seed(seed_id).weight > 0.0

"""Model-independent public API for the live Shadow Seed Learning pipeline.

The engine owns no language-model call.  A host application asks which already
authorized seeds may be considered, calls its own model, and returns the visible
answer for post-generation observation.  The existing ``ShadowChatSession``
remains the canonical orchestration implementation; this module exposes its
live pipeline as a small integration contract rather than duplicating Gate,
lifecycle, or point-of-use logic.
"""

from __future__ import annotations

from typing import Any

from shadowseed.adapters.embedding import EmbedFn
from shadowseed.chat import PreparedTurn, ShadowChatSession
from shadowseed.core_config import SSLCoreConfig
from shadowseed.detection.model_detector import DetectorBackend
from shadowseed.gate.signals import (
    SignalDirection,
    SignalKind,
    ValidationSignal,
)
from shadowseed_agent import AgentSafetyContract, InfluenceAction

ENGINE_API_VERSION = 1


class _DetachedModelBackend:
    """Fail loudly if detached engine wiring ever tries to generate text."""

    name = "detached"

    def generate(
        self,
        prompt: str,
        scenario: dict,
        mode: str,
        ssl_seeds: list[str],
    ) -> str:
        raise RuntimeError(
            "ShadowseedEngine never calls a language model; call prepare_turn, "
            "run the host model, then call observe_turn"
        )


class ShadowseedEngine:
    """Standalone, model-independent facade over the canonical live SSL runtime.

    One instance represents one ordered conversation or task stream.  The host
    owns message history, model selection, provider credentials, and generation.
    The engine owns shadow memory, lifecycle, evidence, Gate decisions,
    point-of-use authorization, candidate observation, and audit state.
    """

    api_version = ENGINE_API_VERSION

    def __init__(
        self,
        *,
        embedding_backend: str = "lexical",
        embedding_model: str | None = None,
        embedding_fn: EmbedFn | None = None,
        detector_backend: DetectorBackend | None = None,
        surface_threshold: float = 0.30,
        surface_top_k: int = 2,
        early_turn_margin: float = 0.10,
        early_turn_history: int = 5,
        resurface_margin: float = 0.15,
        max_seeds_per_turn: int = 5,
        recurrence_mode: str = "cluster",
        cluster_threshold: float | None = None,
        gate_policy_id: str = "evidence_backed",
        allow_toy_embedder: bool = False,
        contract: AgentSafetyContract | None = None,
        core_config: SSLCoreConfig | None = None,
    ) -> None:
        if (
            detector_backend is not None
            and embedding_fn is None
            and embedding_backend == "lexical"
            and not allow_toy_embedder
        ):
            raise ValueError(
                "a real detached detector requires a semantic embedding backend; "
                "provide embedding_fn, select sentence-transformers/openai, or pass "
                "allow_toy_embedder=True only for an explicit non-production experiment"
            )
        self._session = ShadowChatSession(
            backend="fixture",
            embedding_backend=embedding_backend,
            embedding_model=embedding_model,
            embedding_fn=embedding_fn,
            detector_backend=detector_backend,
            model_backend=_DetachedModelBackend(),
            surface_threshold=surface_threshold,
            surface_top_k=surface_top_k,
            early_turn_margin=early_turn_margin,
            early_turn_history=early_turn_history,
            resurface_margin=resurface_margin,
            max_seeds_per_turn=max_seeds_per_turn,
            recurrence_mode=recurrence_mode,
            cluster_threshold=cluster_threshold,
            runtime_mode="live",
            gate_policy_id=gate_policy_id,
            allow_toy_embedder=allow_toy_embedder,
            contract=contract,
            core_config=core_config,
        )

    @classmethod
    def _from_session(cls, session: ShadowChatSession) -> "ShadowseedEngine":
        if session.runtime_mode != "live":
            raise ValueError("ShadowseedEngine requires a live runtime state")
        engine = cls.__new__(cls)
        engine._session = session
        return engine

    @classmethod
    def from_state(
        cls,
        state: dict[str, Any],
        *,
        detector_backend: DetectorBackend | None = None,
        embedding_fn: EmbedFn | None = None,
    ) -> "ShadowseedEngine":
        """Restore an exported engine state with host-supplied runtime adapters."""

        session = ShadowChatSession.from_state(
            state,
            model_backend=_DetachedModelBackend(),
            detector_backend=detector_backend,
            embedding_fn=embedding_fn,
        )
        return cls._from_session(session)

    @property
    def turn(self) -> int:
        """Number of fully observed turns."""

        return self._session._turn

    @property
    def has_pending_turn(self) -> bool:
        return self._session._pending_live_turn is not None

    def prepare_turn(self, message: str) -> PreparedTurn:
        """Return authorized candidate context without generating an answer."""

        return self._session.prepare_turn(message)

    def observe_turn(
        self,
        prepared: PreparedTurn,
        answer: str,
    ) -> dict[str, Any]:
        """Observe the host's visible answer and advance shadow state once."""

        return self._session.observe_turn(prepared, answer)

    def submit_evidence(
        self,
        seed_id: str,
        signal: ValidationSignal,
    ) -> dict[str, Any]:
        """Offer verified external support through the canonical Gate."""

        if self.has_pending_turn:
            raise RuntimeError("cannot change authority while a prepared turn is pending")
        return self._session.submit_evidence(seed_id, signal)

    def submit_contradiction(
        self,
        seed_id: str,
        *,
        reason: str,
        source_ref: str,
        strength: float = 1.0,
    ) -> dict[str, Any]:
        """Submit an attributable contradiction through the canonical Gate."""

        if self.has_pending_turn:
            raise RuntimeError("cannot change authority while a prepared turn is pending")
        if seed_id not in self._session.manager.seeds:
            raise KeyError(f"Unknown seed id: {seed_id}")
        if not isinstance(reason, str) or not reason.strip():
            raise ValueError("contradiction reason must be non-empty")
        if not isinstance(source_ref, str) or not source_ref.strip():
            raise ValueError("contradiction source_ref must be non-empty")
        signal = ValidationSignal(
            kind=SignalKind.CONTRADICTION,
            direction=SignalDirection.OPPOSE,
            strength=strength,
            source_ref=source_ref.strip(),
            verified=True,
            independent=True,
            reason=reason.strip(),
        )
        event = self._session.manager.submit_signals(
            seed_id,
            [signal],
            policy_id=self._session.gate_policy_id,
        )
        seed = self._session.manager.seeds[seed_id]
        blocked = self._session.contract.inspect(
            seed,
            InfluenceAction.ANSWER_MODIFICATION,
            self._session.manager.gate_events,
            contradiction_blocking=self._session.manager.is_blocking_contradiction(
                seed_id
            ),
        ).is_blocked
        return {
            "seed_id": seed_id,
            "decision": event.decision.value,
            "policy_id": event.policy_id,
            "weight_after": seed.weight,
            "status_after": seed.status.value,
            "blocked_from_influence": blocked,
            "gate_event": event.to_dict(),
        }

    def inspect(self) -> dict[str, Any]:
        """Return the current shadow and influence record for UI or diagnostics."""

        report = self._session.shadow_report()
        return {"engine_api_version": self.api_version, **report}

    def audit(self) -> int:
        """Replay point-of-use invariants and return the record count."""

        return self._session.audit()

    def export_state(self) -> dict[str, Any]:
        """Return restorable state after a fully observed turn."""

        if self.has_pending_turn:
            raise RuntimeError("cannot export state while a prepared turn is pending")
        return self._session.to_state()


__all__ = ["ENGINE_API_VERSION", "PreparedTurn", "ShadowseedEngine"]

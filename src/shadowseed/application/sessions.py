"""Tester-facing session orchestration over the existing ShadowChat runtime."""

from __future__ import annotations

import hashlib
from datetime import datetime
from pathlib import Path
from typing import Any
from uuid import uuid4

from shadowseed.application.auth import (
    CONTRADICTION_RESOLVE,
    CONTRADICTION_SUBMIT,
    EVIDENCE_VERIFY,
    ActorContext,
    require_capability,
)
from shadowseed.application.limits import (
    validate_evidence,
    validate_feedback_note,
    validate_message,
    validate_model_id,
    validate_session_config,
    validate_session_title,
)
from shadowseed.application.models import SessionConfig, SessionSummary, TesterFeedback
from shadowseed.application.profiles import get_profile
from shadowseed.application.session_lock import session_mutation_lock
from shadowseed.chat import ShadowChatSession
from shadowseed.core_config import SSLCoreConfig
from shadowseed.gate.signals import SignalDirection, SignalKind, ValidationSignal
from shadowseed.manager import SeedStatus
from shadowseed.storage.sqlite import SQLiteWorkspaceRepository, WorkspaceStorageError
from shadowseed.surfacing import build_chat_prompt


class SessionService:
    def __init__(
        self,
        repository: SQLiteWorkspaceRepository,
        *,
        scope_id: str | None = None,
    ) -> None:
        self.repository = repository
        self.scope_id = scope_id
        self.repository.initialize()

    def _session_lock(self, session_id: str):
        """Return the repository-wide process-local lock for one session."""

        return session_mutation_lock(self.repository, session_id)

    def create_session(
        self,
        *,
        title: str = "Untitled session",
        profile_id: str = "balanced",
        config: SessionConfig | None = None,
        backend: str | None = None,
        model_id: str | None = None,
        config_overrides: dict[str, Any] | None = None,
    ) -> str:
        normalized_title = validate_session_title(title)
        normalized_model_id = validate_model_id(model_id)
        profile = get_profile(profile_id)
        resolved = profile.apply(
            config,
            backend=backend,
            model_id=normalized_model_id,
            **dict(config_overrides or {}),
        )
        validate_session_config(
            max_seeds_per_turn=resolved.max_seeds_per_turn,
            max_new_tokens=resolved.max_new_tokens,
        )
        runtime_config = resolved.to_dict()
        core_config = SSLCoreConfig(
            min_occurrences_for_gate=int(runtime_config.pop("min_occurrences_for_gate")),
            min_evidence_for_gate=int(runtime_config.pop("min_evidence_for_gate")),
            min_trace_for_gate=float(runtime_config.pop("min_trace_for_gate")),
            promotion_threshold=float(runtime_config.pop("promotion_threshold")),
            validation_increment=float(runtime_config.pop("validation_increment")),
        )
        # Product-facing slider values are persisted in the application config,
        # while the runtime consumes the concrete Gate and surfacing settings.
        runtime_config.pop("ssl_intensity", None)
        runtime_config.pop("gate_strictness", None)
        session = ShadowChatSession(**runtime_config, core_config=core_config)
        session_id = f"session::{uuid4()}"
        now = datetime.now().isoformat()
        self.repository.create_session(
            session_id=session_id,
            title=normalized_title or "Untitled session",
            profile_id=profile_id,
            config=resolved.to_dict(),
            state=session.to_state(),
            created_at=now,
        )
        return session_id

    def update_controls(
        self,
        session_id: str,
        *,
        config_updates: dict[str, Any],
        session_config_updates: dict[str, Any],
        core_config_updates: dict[str, Any],
    ) -> dict[str, Any]:
        """Apply product controls to an existing session without changing seed authority."""

        with self._session_lock(session_id):
            stored = self.repository.load_session(session_id)
            config = dict(stored.get("config", {}))
            config.update(config_updates)

            state = dict(stored["state"])
            state_session_config = dict(state.get("session_config", {}))
            state_session_config.update(session_config_updates)
            state["session_config"] = state_session_config

            manager_state = dict(state.get("manager", {}))
            manager_config = dict(manager_state.get("config", {}))
            manager_config.update(core_config_updates)
            manager_state["config"] = manager_config
            state["manager"] = manager_state

            # Regie updates are configuration-only. Do not rehydrate the
            # model backend here: moving a slider must never load a local model
            # or initialize a hosted provider. The controller supplies bounded,
            # canonical mappings for all updated fields.
            updated_at = datetime.now().isoformat()
            self.repository.save_session_configuration(
                session_id,
                config=config,
                state=state,
                updated_at=updated_at,
            )
            return self.repository.load_session(session_id)

    @staticmethod
    def _generate_live_no_ssl_control(
        session: ShadowChatSession,
        question: str,
    ) -> str:
        """Generate a same-history, non-mutating control for one live turn.

        This deliberately uses the same visible pre-turn history and the same
        prompt/generation path as the live SSL answer, with only the surfaced
        Shadow Seed context removed. The control never enters detection,
        recurrence, Gate state, or later conversation history.
        """

        fixture_answer = f"Fixture echo answer to: {question}"
        return session.model.generate(
            build_chat_prompt(
                session.history,
                question,
                [],
                response_language="the same language as the user's current question",
            ),
            {
                "question": question,
                "turn": session._turn,
                "baseline_answer": fixture_answer,
            },
            "baseline",
            [],
        )

    @staticmethod
    def _experimental_shadow_pressure(
        session: ShadowChatSession,
        question: str,
        *,
        limit: int = 3,
    ) -> list[dict[str, Any]]:
        """Rank non-promoted seeds for read-only pre-authority comparison.

        This never changes authority or surfacing state. It exists only for the
        Workbench's experimental A/B lab so researchers can inspect whether
        growing shadow memory would steer a model before formal promotion.
        """

        if limit <= 0 or not session.manager.seeds:
            return []
        question_embedding = session.manager.get_embedding(question)
        min_occurrences = max(1, int(session.manager.config.min_occurrences_for_gate))
        min_evidence = max(1, int(session.manager.config.min_evidence_for_gate))
        max_trace = max(0.001, float(session.manager.config.max_trace))

        ranked: list[dict[str, Any]] = []
        for seed_id, seed in session.manager.seeds.items():
            if seed.status in {SeedStatus.PROMOTED, SeedStatus.EXPIRED, SeedStatus.DORMANT}:
                continue
            if session.manager.is_blocking_contradiction(seed_id):
                continue
            if session.clusterer is not None:
                cluster_id = session.seed_to_cluster.get(seed_id)
                if cluster_id is not None and session.cluster_rep.get(cluster_id) != seed_id:
                    continue

            similarity = float(question_embedding @ seed.embedding)
            if similarity < 0.10:
                continue
            occurrence = min(1.0, float(seed.occurrence_count) / min_occurrences)
            evidence = min(1.0, float(seed.evidence_count) / min_evidence)
            weight = max(0.0, min(1.0, float(seed.weight)))
            trace = max(0.0, min(1.0, float(seed.trace) / max_trace))
            maturity = (
                (0.45 * occurrence)
                + (0.25 * evidence)
                + (0.20 * weight)
                + (0.10 * trace)
            )
            score = max(0.0, similarity) * maturity
            if maturity < 0.15 or score <= 0.0:
                continue
            ranked.append(
                {
                    "seed_id": seed_id,
                    "text": seed.text,
                    "similarity": round(similarity, 4),
                    "maturity": round(maturity, 4),
                    "score": round(score, 4),
                    "status": seed.status.value,
                    "weight": round(float(seed.weight), 4),
                    "occurrence_count": int(seed.occurrence_count),
                    "evidence_count": int(seed.evidence_count),
                }
            )

        ranked.sort(key=lambda item: float(item["score"]), reverse=True)
        return ranked[:limit]

    @classmethod
    def _generate_live_shadow_pressure_control(
        cls,
        session: ShadowChatSession,
        question: str,
        *,
        baseline_answer: str,
    ) -> tuple[str, list[dict[str, Any]]]:
        """Generate a read-only experimental pre-promotion treatment arm."""

        candidates = cls._experimental_shadow_pressure(session, question)
        if not candidates:
            return baseline_answer, []
        shadow_context = [
            (
                f"Experimental pre-authority perspective; maturity "
                f"{float(item['maturity']):.2f}; NOT Validation-Gate authorized: "
                f"{item['text']}"
            )
            for item in candidates
        ]
        answer = session.model.generate(
            build_chat_prompt(
                session.history,
                question,
                shadow_context,
                response_language="the same language as the user's current question",
            ),
            {
                "question": question,
                "turn": session._turn,
                "baseline_answer": baseline_answer,
                "shadow_pressure": True,
            },
            "ssl",
            shadow_context,
        )
        return answer, candidates

    def run_turn(
        self,
        session_id: str,
        question: str,
        *,
        compare_without_ssl: bool = False,
        comparison_mode: str = "authorized",
    ) -> dict[str, Any]:
        # Validate before loading runtime state or calling a provider so a rejected
        # message cannot partially mutate the session or consume an expensive call.
        normalized_question = validate_message(question)
        with self._session_lock(session_id):
            stored = self.repository.load_session(session_id)
            session = ShadowChatSession.from_state(stored["state"])

            if comparison_mode not in {"authorized", "shadow_pressure", "longitudinal"}:
                raise ValueError(
                    "comparison_mode must be 'authorized', 'shadow_pressure' or 'longitudinal'"
                )
            if (
                compare_without_ssl
                and comparison_mode == "shadow_pressure"
                and session.runtime_mode != "live"
            ):
                raise ValueError(
                    "shadow_pressure comparison is available only for live sessions"
                )

            control_answer: str | None = None
            control_metadata: dict[str, Any] = {}
            shadow_pressure_answer: str | None = None
            shadow_pressure_candidates: list[dict[str, Any]] = []
            prior_ssl_seed_ids = (
                sorted(
                    {
                        str(seed_id)
                        for prior_report in session.turn_reports
                        for seed_id in prior_report.get("surfaced_seed_ids", [])
                    }
                )
                if session.runtime_mode == "live"
                else []
            )
            if compare_without_ssl and session.runtime_mode == "live":
                if comparison_mode == "longitudinal":
                    control_metadata = session.generate_vanilla_control(
                        normalized_question
                    )
                    control_answer = str(control_metadata["answer"])
                else:
                    control_answer = self._generate_live_no_ssl_control(
                        session,
                        normalized_question,
                    )
                    control_metadata = {
                        "transport": "same_prompt_path",
                        "replayed_turns": 0,
                        "history_turns_before": len(session.history),
                    }
                if comparison_mode == "shadow_pressure":
                    shadow_pressure_answer, shadow_pressure_candidates = (
                        self._generate_live_shadow_pressure_control(
                            session,
                            normalized_question,
                            baseline_answer=control_answer,
                        )
                    )

            report = session.turn(normalized_question)

            if compare_without_ssl:
                if session.runtime_mode == "evaluation":
                    baseline = report.get("baseline_answer")
                    if baseline is None:
                        raise RuntimeError(
                            "evaluation comparison requested but the turn has no baseline answer"
                        )
                    control_answer = str(baseline)
                if control_answer is None:
                    raise RuntimeError("comparison requested but no no-SSL control was generated")
                if comparison_mode == "shadow_pressure" and session.runtime_mode == "live":
                    treatment_answer = (
                        shadow_pressure_answer
                        if shadow_pressure_answer is not None
                        else control_answer
                    )
                    comparison_kind = "same_history_no_ssl_vs_shadow_pressure"
                    comparison_seed_ids = [
                        str(item["seed_id"]) for item in shadow_pressure_candidates
                    ]
                    comparison_interpretation = (
                        "Both arms use the same visible pre-turn history and the same "
                        "generation path. The control receives no Shadow Seed context. "
                        "The treatment receives read-only, non-promoted shadow-memory "
                        "perspectives for this turn only. This is a pre-authority research "
                        "experiment, not evidence of authorized SSL influence."
                    )
                elif comparison_mode == "longitudinal" and session.runtime_mode == "live":
                    treatment_answer = str(report.get("answer", ""))
                    comparison_kind = "independent_vanilla_vs_ssl_path"
                    comparison_seed_ids = list(report.get("surfaced_seed_ids", []))
                    comparison_interpretation = (
                        "The control is an independent vanilla conversation built only "
                        "from the same user questions and its own vanilla answers. The "
                        "treatment follows the normal Shadowseed conversation, including "
                        "any earlier SSL-influenced answers. A difference therefore "
                        "measures cumulative Shadowseed-path divergence from vanilla; "
                        "current-turn seed influence is reported separately."
                    )
                else:
                    treatment_answer = str(report.get("answer", ""))
                    comparison_kind = (
                        "same_history_no_ssl_vs_ssl"
                        if session.runtime_mode == "live"
                        else "evaluation_control"
                    )
                    comparison_seed_ids = list(report.get("surfaced_seed_ids", []))
                    comparison_interpretation = (
                        (
                            "Both arms use the same model configuration, the same visible "
                            "pre-turn history and the same current user message. The control "
                            "uses the same generation path but receives no surfaced Shadow "
                            "Seeds. Only the real SSL turn changes session state. Earlier SSL "
                            "influence in visible history is shared by both arms, so this "
                            "comparison isolates current-turn SSL context rather than the "
                            "full long-term conversation path."
                        )
                        if session.runtime_mode == "live"
                        else (
                            "The evaluation runtime keeps baseline history isolated and "
                            "compares it with the SSL sidecar answer for the same turn."
                        )
                    )
                current_ssl_influence = bool(comparison_seed_ids)
                prior_ssl_influence = bool(prior_ssl_seed_ids)
                comparison_fields = {
                    "comparison_requested": True,
                    "comparison_mode": comparison_mode,
                    "comparison_kind": comparison_kind,
                    "comparison_control_answer": control_answer,
                    "comparison_ssl_answer": treatment_answer,
                    "comparison_seed_ids": comparison_seed_ids,
                    "comparison_shadow_pressure_candidates": shadow_pressure_candidates,
                    "comparison_control_history_isolated": (
                        session.runtime_mode == "live" and comparison_mode == "longitudinal"
                    ),
                    "comparison_control_state_isolated": True,
                    "comparison_control_transport": control_metadata.get("transport"),
                    "comparison_control_replayed_turns": int(
                        control_metadata.get("replayed_turns", 0)
                    ),
                    "comparison_control_history_turns_before": int(
                        control_metadata.get("history_turns_before", 0)
                    ),
                    "comparison_prior_ssl_seed_ids": prior_ssl_seed_ids,
                    "comparison_current_ssl_influence_observed": current_ssl_influence,
                    "comparison_prior_ssl_influence_observed": prior_ssl_influence,
                    "comparison_ssl_influence_observed": (
                        current_ssl_influence
                        or (
                            prior_ssl_influence
                            if comparison_mode == "longitudinal"
                            else False
                        )
                    ),
                    "comparison_interpretation": comparison_interpretation,
                }
                report.update(comparison_fields)
                if session.turn_reports:
                    session.turn_reports[-1].update(comparison_fields)

            self.repository.save_session(
                session_id,
                session.to_state(),
                updated_at=datetime.now().isoformat(),
            )
            return report

    def ingest_source_chunks(
        self,
        session_id: str,
        chunks: list[dict[str, str]],
    ) -> dict[str, Any]:
        """Observe source chunks without generating chat answers."""

        with self._session_lock(session_id):
            if not chunks:
                raise ValueError("at least one source chunk is required")
            stored = self.repository.load_session(session_id)
            session = ShadowChatSession.from_state(stored["state"])

            reports: list[dict[str, Any]] = []
            source_names: set[str] = set()
            source_instances: set[str] = set()
            characters = 0
            seeds_before = len(session.manager.seeds)
            promoted_ids: set[str] = set()
            review_ids: set[str] = set()
            authority_runtime: dict[str, Any] | None = None
            for item in chunks:
                text = str(item.get("text", "")).strip()
                context_ref = str(item.get("context_ref", "")).strip()
                source_name = str(item.get("source_name", "source")).strip() or "source"
                source_instance_id = str(item.get("source_instance_id", "")).strip()
                if not text or not context_ref:
                    raise ValueError("source chunks require non-empty text and context_ref")
                report = session.observe_source_text(text, context_ref=context_ref)
                reports.append(report)
                source_names.add(source_name)
                if source_instance_id:
                    source_instances.add(source_instance_id)
                elif ":chunk:" in context_ref:
                    # Backward-compatible fallback for older callers that only
                    # provide a context reference. All chunks from the same source
                    # prefix count as one source instance.
                    source_instances.add(context_ref.rsplit(":chunk:", 1)[0])
                else:
                    source_instances.add(context_ref)
                characters += len(text)
                promoted_ids.update(report.get("promoted_this_observation", []))
                review_ids.update(report.get("authority_review_seed_ids", []))
                if isinstance(report.get("authority_runtime"), dict):
                    authority_runtime = dict(report["authority_runtime"])

            # Report the complete post-ingest review state, not only review
            # requests created by this batch. Review remains outstanding through
            # partial verified validation until the seed is actually promoted.
            review_ids = {
                seed_id
                for seed_id in session.manager.seeds
                if session._seed_review_required(seed_id)
            }

            self.repository.save_session(
                session_id,
                session.to_state(),
                updated_at=datetime.now().isoformat(),
            )
            return {
                "session_id": session_id,
                "sources": len(source_instances),
                "source_names": sorted(source_names),
                "source_instance_count": len(source_instances),
                "chunks": len(reports),
                "characters": characters,
                "seeds_before": seeds_before,
                "seeds_after": len(session.manager.seeds),
                "new_seed_count": max(0, len(session.manager.seeds) - seeds_before),
                "promoted_seed_ids": sorted(promoted_ids),
                "authority_review_seed_ids": sorted(review_ids),
                "authority_runtime": authority_runtime,
                "reports": reports,
            }

    def falsify(self, session_id: str, seed_id: str) -> dict[str, Any]:
        """Research compatibility path; not production authorization."""

        with self._session_lock(session_id):
            stored = self.repository.load_session(session_id)
            session = ShadowChatSession.from_state(stored["state"])
            result = session.falsify(seed_id)
            self.repository.save_session(
                session_id,
                session.to_state(),
                updated_at=datetime.now().isoformat(),
            )
            return result

    def falsify_authorized(
        self,
        session_id: str,
        seed_id: str,
        *,
        actor: ActorContext,
    ) -> dict[str, Any]:
        """Production contradiction submission guarded before runtime mutation."""

        authz = self._authorize(actor, CONTRADICTION_SUBMIT)
        with self._session_lock(session_id):
            replay = self.repository.authorized_request_result(
                actor.request_id,
                event_type=CONTRADICTION_SUBMIT,
                session_id=session_id,
                seed_id=seed_id,
            )
            if replay is not None:
                return {**replay, "authorization": authz}

            stored = self.repository.load_session(session_id)
            session = ShadowChatSession.from_state(stored["state"])
            result = session.falsify(seed_id)
            persisted = self.repository.save_authorized_session(
                session_id,
                session.to_state(),
                updated_at=datetime.now().isoformat(),
                authorization=authz,
                event_type=CONTRADICTION_SUBMIT,
                seed_id=seed_id,
                operation_result=result,
                event_metadata={"action": "operator_falsification"},
            )
            return {**persisted, "authorization": authz}

    def resolve_contradiction_authorized(
        self,
        session_id: str,
        seed_id: str,
        *,
        basis: str,
        actor: ActorContext,
    ) -> dict[str, Any]:
        """Resolve an open contradiction through the canonical Gate boundary."""

        normalized_basis = str(basis or "").strip()
        if not normalized_basis:
            raise ValueError("contradiction resolution requires a non-empty basis")
        authz = self._authorize(actor, CONTRADICTION_RESOLVE)
        with self._session_lock(session_id):
            replay = self.repository.authorized_request_result(
                actor.request_id,
                event_type=CONTRADICTION_RESOLVE,
                session_id=session_id,
                seed_id=seed_id,
            )
            if replay is not None:
                return {**replay, "authorization": authz}

            stored = self.repository.load_session(session_id)
            session = ShadowChatSession.from_state(stored["state"])
            event = session.manager.resolve_contradiction(
                seed_id,
                basis=normalized_basis,
                resolver=str(authz["actor_id"]),
            )
            result = event.to_dict()
            persisted = self.repository.save_authorized_session(
                session_id,
                session.to_state(),
                updated_at=datetime.now().isoformat(),
                authorization=authz,
                event_type=CONTRADICTION_RESOLVE,
                seed_id=seed_id,
                operation_result=result,
                event_metadata={"action": "operator_contradiction_resolution"},
            )
            return {**persisted, **result, "authorization": authz}

    def submit_verified_evidence(
        self,
        session_id: str,
        seed_id: str,
        *,
        source_ref: str,
        note: str = "",
        operator_verified: bool = False,
    ) -> dict[str, Any]:
        """Research compatibility path; a bare boolean is not production authorization."""

        if not operator_verified:
            raise ValueError("operator verification must be explicitly confirmed")
        normalized_source, normalized_note = validate_evidence(source_ref, note)
        return self._submit_verified_evidence(
            session_id,
            seed_id,
            source_ref=normalized_source,
            note=normalized_note,
        )

    @staticmethod
    def _evidence_request_fingerprint(
        session_id: str,
        seed_id: str,
        source_ref: str,
        note: str,
    ) -> str:
        material = "\x1f".join(
            (
                EVIDENCE_VERIFY,
                session_id,
                seed_id,
                source_ref,
                note,
            )
        )
        return hashlib.sha256(material.encode("utf-8")).hexdigest()

    @staticmethod
    def _validated_replay(
        replay: dict[str, Any],
        *,
        expected_fingerprint: str,
    ) -> dict[str, Any]:
        stored_fingerprint = replay.pop("_request_fingerprint", None)
        if stored_fingerprint != expected_fingerprint:
            raise WorkspaceStorageError(
                "request_id was replayed with different authority-operation input"
            )
        return replay

    @staticmethod
    def _minimal_evidence_result(
        result: dict[str, Any],
        *,
        request_fingerprint: str,
    ) -> dict[str, Any]:
        """Keep idempotency data useful without copying raw evidence into the ledger."""

        keys = (
            "seed_id",
            "decision",
            "policy_id",
            "weight_after",
            "status_after",
            "evidence_count",
        )
        return {
            **{key: result[key] for key in keys if key in result},
            "_request_fingerprint": request_fingerprint,
        }

    def submit_verified_evidence_authorized(
        self,
        session_id: str,
        seed_id: str,
        *,
        source_ref: str,
        note: str = "",
        actor: ActorContext,
    ) -> dict[str, Any]:
        """Production evidence submission requiring trusted attributable authorization."""

        # Actor authorization and resource validation both happen before runtime
        # mutation. Neither check substitutes for the Gate's evidence decision.
        authz = self._authorize(actor, EVIDENCE_VERIFY)
        normalized_source, normalized_note = validate_evidence(source_ref, note)
        request_fingerprint = self._evidence_request_fingerprint(
            session_id,
            seed_id,
            normalized_source,
            normalized_note,
        )
        with self._session_lock(session_id):
            replay = self.repository.authorized_request_result(
                actor.request_id,
                event_type=EVIDENCE_VERIFY,
                session_id=session_id,
                seed_id=seed_id,
            )
            if replay is not None:
                replay = self._validated_replay(
                    replay, expected_fingerprint=request_fingerprint
                )
                return {**replay, "authorization": authz}

            stored = self.repository.load_session(session_id)
            session = ShadowChatSession.from_state(stored["state"])
            if session.runtime_mode != "live":
                raise ValueError("verified evidence entry is available only for live sessions")
            result = session.submit_evidence(
                seed_id,
                ValidationSignal(
                    kind=SignalKind.HUMAN_FEEDBACK,
                    direction=SignalDirection.SUPPORT,
                    verified=True,
                    independent=True,
                    source_ref=normalized_source,
                    reason=normalized_note or "verified Workbench operator support",
                ),
            )
            persisted = self.repository.save_authorized_session(
                session_id,
                session.to_state(),
                updated_at=datetime.now().isoformat(),
                authorization=authz,
                event_type=EVIDENCE_VERIFY,
                seed_id=seed_id,
                operation_result=self._minimal_evidence_result(
                    result,
                    request_fingerprint=request_fingerprint,
                ),
                event_metadata={
                    "source_ref_sha256": hashlib.sha256(
                        normalized_source.encode("utf-8")
                    ).hexdigest(),
                    "note_sha256": hashlib.sha256(normalized_note.encode("utf-8")).hexdigest(),
                    "verified": True,
                    "independent": True,
                },
            )
            persisted = self._validated_replay(
                persisted, expected_fingerprint=request_fingerprint
            )
            ledger_fields = {
                key: persisted[key]
                for key in (
                    "idempotent_replay",
                    "ledger_event_id",
                    "ledger_sequence_no",
                    "ledger_event_hash",
                )
                if key in persisted
            }
            return {**result, **ledger_fields, "authorization": authz}

    @staticmethod
    def _normalize_source_ref(source_ref: str) -> str:
        normalized_source, _ = validate_evidence(source_ref, "")
        return normalized_source

    def _submit_verified_evidence(
        self,
        session_id: str,
        seed_id: str,
        *,
        source_ref: str,
        note: str,
    ) -> dict[str, Any]:
        with self._session_lock(session_id):
            normalized_source, normalized_note = validate_evidence(source_ref, note)
            stored = self.repository.load_session(session_id)
            session = ShadowChatSession.from_state(stored["state"])
            if session.runtime_mode != "live":
                raise ValueError("verified evidence entry is available only for live sessions")
            result = session.submit_evidence(
                seed_id,
                ValidationSignal(
                    kind=SignalKind.HUMAN_FEEDBACK,
                    direction=SignalDirection.SUPPORT,
                    verified=True,
                    independent=True,
                    source_ref=normalized_source,
                    reason=normalized_note or "verified Workbench operator support",
                ),
            )
            self.repository.save_session(
                session_id,
                session.to_state(),
                updated_at=datetime.now().isoformat(),
            )
            return result

    def _authorize(self, actor: ActorContext, capability: str) -> dict[str, object]:
        if not self.scope_id:
            raise RuntimeError("production authorization requires a stable workspace scope")
        return require_capability(actor, scope_id=self.scope_id, capability=capability)

    def load(self, session_id: str) -> dict[str, Any]:
        return self.repository.load_session(session_id)

    def list_sessions(self) -> list[SessionSummary]:
        return self.repository.list_sessions()

    def inspect_seed(self, session_id: str, seed_id: str) -> dict[str, Any]:
        stored = self.repository.load_session(session_id)
        session = ShadowChatSession.from_state(stored["state"])
        seed = session.manager.get_seed(seed_id)
        open_contradictions = [
            record.to_dict() for record in session.manager.open_contradictions(seed_id)
        ]
        gate_event = next(
            (event for event in reversed(session.manager.gate_events) if event.seed_id == seed_id),
            None,
        )
        return {
            **seed.to_dict(),
            "born_turn": session.born_turn.get(seed_id),
            "last_surfaced_turn": session.last_surfaced.get(seed_id),
            "open_contradictions": open_contradictions,
            "last_gate_event": gate_event.to_dict() if gate_event else None,
            "blocking": session.manager.is_blocking_contradiction(seed_id),
        }

    def record_feedback(self, feedback: TesterFeedback) -> TesterFeedback:
        if feedback.action != "record_only":
            raise ValueError(
                "foundation release supports record_only feedback; authority-changing "
                "feedback remains an explicit later workflow"
            )
        normalized_note = validate_feedback_note(feedback.note)
        self.repository.load_session(feedback.session_id)
        normalized = TesterFeedback(
            session_id=feedback.session_id,
            turn_index=feedback.turn_index,
            overall=feedback.overall,
            seed_effect=feedback.seed_effect,
            note=normalized_note,
            action=feedback.action,
            seed_id=feedback.seed_id,
            created_at=feedback.created_at,
            feedback_id=feedback.feedback_id,
        )
        return self.repository.add_feedback(normalized)

    def list_feedback(self, session_id: str) -> list[TesterFeedback]:
        return self.repository.list_feedback(session_id)

    def delete_session(self, session_id: str) -> None:
        with self._session_lock(session_id):
            self.repository.delete_session(session_id)


def service_for_workspace(workspace: str | Path | None = None) -> SessionService:
    from shadowseed.application.workspace import WorkspaceService

    workspace_service = WorkspaceService(workspace)
    workspace_service.initialize()
    return SessionService(
        workspace_service.repository,
        scope_id=workspace_service.workspace_id,
    )

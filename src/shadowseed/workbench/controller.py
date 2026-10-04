"""Thin Workbench controller over tester-facing application services.

No Validation Gate, manager, or lifecycle implementation is imported here. The
controller translates UI actions into application-service calls and adds only
product concerns such as external-provider consent and presentation shaping.
"""

from __future__ import annotations

from dataclasses import asdict
from importlib.util import find_spec
from pathlib import Path
from typing import Any

from shadowseed.adapters.embedding import SUPPORTED_EMBEDDING_BACKENDS
from shadowseed.authority_profiles import AUTHORITY_PROFILES, get_authority_profile
from shadowseed.core_config import SSLCoreConfig
from shadowseed.application.ingest import prepare_sources
from shadowseed.application.comparison import ComparisonService
from shadowseed.application.contradiction_resolution import resolve_authorized_contradiction
from shadowseed.application.exports import ExportService, verify_workbench_export
from shadowseed.application.feedback import FeedbackService
from shadowseed.application.inspection import InspectionService
from shadowseed.application.models import SessionConfig
from shadowseed.application.profiles import list_profiles
from shadowseed.application.scenarios import ScenarioService, ScenarioSpec
from shadowseed.application.sessions import SessionService
from shadowseed.application.workspace import WorkspaceService


BACKENDS = ("fixture", "hf-transformers", "ollama", "openai")
EMBEDDING_BACKENDS = SUPPORTED_EMBEDDING_BACKENDS
RUNTIME_MODES = ("evaluation", "live")
_EXTERNAL_PROMPT_BACKENDS = {"openai"}

_BACKEND_NOTES = {
    "fixture": (
        "Offline deterministic demo backend. Useful for onboarding and regression checks, "
        "not a high-end model."
    ),
    "hf-transformers": (
        "Runs the selected Transformers model locally after it is available. Initial model "
        "download may contact Hugging Face; prompts are evaluated locally by this backend."
    ),
    "ollama": "Uses a model served by your local Ollama instance.",
    "openai": (
        "Hosted provider. Prompts and generated context are sent to the OpenAI API; "
        "the API key remains in the process environment and is not stored by the Workbench."
    ),
}


class WorkbenchController:
    """Product-level orchestration for the local tester Workbench."""

    def __init__(self, workspace: str | Path | None = None) -> None:
        self.workspace = WorkspaceService(workspace)
        self.workspace.initialize()
        self.sessions = SessionService(
            self.workspace.repository,
            scope_id=self.workspace.workspace_id,
        )
        self.inspection = InspectionService(self.sessions)
        self.feedback = FeedbackService(self.sessions)
        self.scenarios = ScenarioService(self.sessions)
        self.comparison = ComparisonService(self.sessions)
        self.exports = ExportService(
            self.sessions,
            workspace_root=self.workspace.paths.root,
        )

    @property
    def workspace_root(self) -> str:
        return str(self.workspace.paths.root)

    def profiles(self) -> list[dict[str, Any]]:
        return [
            {
                "profile_id": profile.profile_id,
                "label": profile.label,
                "description": profile.description,
            }
            for profile in list_profiles()
        ]

    @staticmethod
    def authority_profiles() -> list[dict[str, Any]]:
        return [profile.to_dict() for profile in AUTHORITY_PROFILES.values()]

    @staticmethod
    def backend_available(backend: str) -> bool:
        """Return whether the optional runtime for a product backend is installed."""

        if backend in {"fixture", "ollama"}:
            return True
        if backend == "openai":
            return find_spec("openai") is not None
        if backend == "hf-transformers":
            return all(
                find_spec(module) is not None
                for module in ("sentence_transformers", "transformers", "torch")
            )
        return False

    def backends(self) -> list[dict[str, str]]:
        return [
            {"backend": backend, "note": _BACKEND_NOTES[backend]}
            for backend in BACKENDS
            if self.backend_available(backend)
        ]

    @staticmethod
    def embedding_backend_available(backend: str) -> bool:
        """Return whether an embedding runtime is usable in this installation."""

        if backend in {"lexical", "ollama"}:
            return True
        if backend == "openai":
            return find_spec("openai") is not None
        if backend == "sentence-transformers":
            return find_spec("sentence_transformers") is not None
        return False

    @staticmethod
    def embedding_backends() -> tuple[str, ...]:
        """Return the canonical supported embedding-backend registry."""

        return EMBEDDING_BACKENDS

    @staticmethod
    def available_embedding_backends() -> tuple[str, ...]:
        """Return embedding backends usable in the current installation."""

        return tuple(
            backend
            for backend in EMBEDDING_BACKENDS
            if WorkbenchController.embedding_backend_available(backend)
        )

    @staticmethod
    def runtime_modes() -> tuple[str, ...]:
        return RUNTIME_MODES

    @staticmethod
    def default_embedding_backend(backend: str) -> str:
        """Return the safe product default for a model backend."""

        if backend == "fixture":
            return "lexical"
        if backend == "ollama":
            return "ollama"
        if backend == "openai":
            return "openai"
        return "sentence-transformers"

    @staticmethod
    def default_embedding_model(embedding_backend: str) -> str | None:
        """Return the explicit product default model for an embedding backend."""

        if embedding_backend == "ollama":
            from shadowseed.adapters.ollama_client import DEFAULT_OLLAMA_EMBEDDING_MODEL

            return DEFAULT_OLLAMA_EMBEDDING_MODEL
        return None

    @staticmethod
    def validate_ollama_embedding_model(model_id: str | None) -> None:
        """Fail early with an actionable setup message when the embedding model is absent."""

        from shadowseed.adapters.ollama_client import (
            DEFAULT_OLLAMA_EMBEDDING_MODEL,
            list_ollama_models,
        )

        requested = str(model_id or DEFAULT_OLLAMA_EMBEDDING_MODEL).strip()
        try:
            installed = list_ollama_models()
        except RuntimeError as exc:
            raise ValueError(
                "Ollama is not reachable at the configured local endpoint. "
                "Start Ollama and try again."
            ) from exc

        requested_key = requested.casefold()
        available = {
            str(name).strip().casefold()
            for name in installed
            if str(name).strip()
        }
        exact_match = requested_key in available
        latest_match = (
            ":" not in requested_key
            and f"{requested_key}:latest" in available
        )
        if not exact_match and not latest_match:
            raise ValueError(
                f"Ollama embedding model {requested!r} is not installed. "
                f"Run `ollama pull {requested}` in Terminal, then create the chat again."
            )

    @staticmethod
    def ssl_intensity_settings(percent: int | float) -> dict[str, float | int]:
        """Map 0-100% SSL influence to surfacing settings without weakening authority."""

        value = max(0.0, min(100.0, float(percent)))
        if value == 0.0:
            return {
                "ssl_intensity": 0,
                "surface_threshold": 1.0,
                "surface_top_k": 0,
                "early_turn_margin": 0.0,
                "resurface_margin": 0.0,
            }
        ratio = value / 100.0
        return {
            "ssl_intensity": int(round(value)),
            "surface_threshold": round(0.65 - (0.45 * ratio), 3),
            "surface_top_k": 1 if value <= 40.0 else (2 if value <= 80.0 else 3),
            "early_turn_margin": round(0.20 - (0.15 * ratio), 3),
            "resurface_margin": round(0.25 - (0.15 * ratio), 3),
        }

    @staticmethod
    def gate_strictness_settings(percent: int | float) -> dict[str, Any]:
        """Map 0-100% Gate strictness onto the canonical Validation Gate."""

        value = max(0.0, min(100.0, float(percent)))
        common: dict[str, Any] = {"gate_strictness": int(round(value))}

        if value <= 10.0:
            return {
                **common,
                "authority_profile_id": "autonomous",
                "gate_policy_id": "exploratory",
                "min_occurrences_for_gate": 1,
                "min_evidence_for_gate": 0,
                "min_trace_for_gate": 0.0,
                "promotion_threshold": 0.2,
                "validation_increment": 0.2,
            }
        if value <= 30.0:
            return {
                **common,
                "authority_profile_id": "autonomous",
                "gate_policy_id": "exploratory",
                "min_occurrences_for_gate": 2,
                "min_evidence_for_gate": 0,
                "min_trace_for_gate": 0.0,
                "promotion_threshold": 0.2,
                "validation_increment": 0.2,
            }
        if value <= 50.0:
            return {
                **common,
                "authority_profile_id": "autonomous",
                "gate_policy_id": "exploratory",
                "min_occurrences_for_gate": 3,
                "min_evidence_for_gate": 0,
                "min_trace_for_gate": 0.0,
                "promotion_threshold": 0.4,
                "validation_increment": 0.2,
            }
        if value <= 70.0:
            return {
                **common,
                "authority_profile_id": "assisted",
                "gate_policy_id": "evidence_backed",
                "min_occurrences_for_gate": 3,
                "min_evidence_for_gate": 1,
                "min_trace_for_gate": 0.0,
                "promotion_threshold": 0.2,
                "validation_increment": 0.2,
            }
        if value < 100.0:
            return {
                **common,
                "authority_profile_id": "assisted",
                "gate_policy_id": "evidence_backed",
                "min_occurrences_for_gate": 3,
                "min_evidence_for_gate": 2 if value <= 85.0 else 3,
                "min_trace_for_gate": 0.0,
                "promotion_threshold": 0.4 if value <= 85.0 else 0.6,
                "validation_increment": 0.2,
            }
        return {
            **common,
            "authority_profile_id": "strict",
            "gate_policy_id": "evidence_backed",
            "min_occurrences_for_gate": 4,
            "min_evidence_for_gate": 3,
            "min_trace_for_gate": 0.5,
            "promotion_threshold": 0.6,
            "validation_increment": 0.2,
        }

    @staticmethod
    def discover_models(backend: str) -> list[str]:
        """Discover locally available models without changing provider state."""

        if backend == "ollama":
            from shadowseed.adapters.ollama_client import list_ollama_chat_models

            return list_ollama_chat_models()
        # Hosted providers and arbitrary HF repositories keep a custom-value
        # field. Fixture needs no model id.
        return []

    def list_sessions(self) -> list[dict[str, Any]]:
        return [asdict(item) for item in self.sessions.list_sessions()]

    def create_session(
        self,
        *,
        title: str,
        profile_id: str,
        backend: str,
        model_id: str | None = None,
        revision_backend: str | None = None,
        revision_model_id: str | None = None,
        detection_backend: str | None = None,
        detection_model_id: str | None = None,
        detection_max_new_tokens: int | None = None,
        runtime_mode: str = "live",
        authority_profile_id: str = "strict",
        embedding_backend: str | None = None,
        embedding_model: str | None = None,
        allow_toy_embedder: bool = False,
        external_confirmed: bool = False,
        ssl_intensity: int | float | None = None,
        gate_strictness: int | float | None = None,
        allow_same_turn_revision: bool | None = None,
        allow_self_reinforcement: bool = False,
    ) -> str:
        resolved_embedding = embedding_backend or self.default_embedding_backend(backend)
        resolved_embedding_model = (
            embedding_model
            if embedding_model is not None
            else self.default_embedding_model(resolved_embedding)
        )
        gate_settings = (
            self.gate_strictness_settings(gate_strictness)
            if gate_strictness is not None
            else {}
        )
        if "authority_profile_id" in gate_settings:
            authority_profile_id = str(gate_settings.pop("authority_profile_id"))
        authority_profile = get_authority_profile(authority_profile_id)
        self._validate_backend(
            backend,
            model_id=model_id,
            revision_backend=revision_backend,
            revision_model_id=revision_model_id,
            detection_backend=detection_backend,
            detection_model_id=detection_model_id,
            runtime_mode=runtime_mode,
            embedding_backend=resolved_embedding,
            allow_toy_embedder=allow_toy_embedder,
            external_confirmed=external_confirmed,
        )
        effective_same_turn_revision = (
            bool(allow_self_reinforcement)
            if allow_same_turn_revision is None
            else bool(allow_same_turn_revision)
        )
        config_overrides: dict[str, Any] = {}
        if ssl_intensity is not None:
            config_overrides.update(self.ssl_intensity_settings(ssl_intensity))
        config_overrides.update(gate_settings)
        return self.sessions.create_session(
            title=title,
            profile_id=profile_id,
            config=SessionConfig(
                runtime_mode=runtime_mode,
                revision_backend=revision_backend,
                revision_model_id=revision_model_id,
                detection_backend=detection_backend,
                detection_model_id=detection_model_id,
                detection_max_new_tokens=detection_max_new_tokens,
                authority_profile_id=authority_profile.id.value,
                embedding_backend=resolved_embedding,
                embedding_model=resolved_embedding_model,
                allow_toy_embedder=allow_toy_embedder,
                revalidate_current_gate=gate_strictness is not None,
                allow_same_turn_revision=effective_same_turn_revision,
                self_derived_signal_policy="fail_closed",
                allow_self_reinforcement=bool(allow_self_reinforcement),
            ),
            backend=backend,
            model_id=model_id or None,
            config_overrides=config_overrides or None,
        )

    def update_session_controls(
        self,
        session_id: str,
        *,
        ssl_intensity: int | float,
        gate_strictness: int | float,
        allow_self_reinforcement: bool,
    ) -> dict[str, Any]:
        """Apply the Regie controls to the currently selected persisted chat."""

        ssl_settings = self.ssl_intensity_settings(ssl_intensity)
        gate_settings = self.gate_strictness_settings(gate_strictness)
        authority_profile_id = str(gate_settings["authority_profile_id"])
        gate_policy_id = str(gate_settings["gate_policy_id"])

        core_keys = {
            "min_occurrences_for_gate",
            "min_evidence_for_gate",
            "min_trace_for_gate",
            "promotion_threshold",
            "validation_increment",
        }
        core_updates = {
            key: gate_settings[key]
            for key in core_keys
            if key in gate_settings
        }
        session_config_updates = {
            "surface_threshold": ssl_settings["surface_threshold"],
            "surface_top_k": ssl_settings["surface_top_k"],
            "early_turn_margin": ssl_settings["early_turn_margin"],
            "resurface_margin": ssl_settings["resurface_margin"],
            "gate_policy_id": gate_policy_id,
            "authority_profile_id": authority_profile_id,
            "revalidate_current_gate": True,
            "allow_same_turn_revision": bool(allow_self_reinforcement),
            "self_derived_signal_policy": "fail_closed",
            "allow_self_reinforcement": bool(allow_self_reinforcement),
        }
        config_updates = {
            **ssl_settings,
            **gate_settings,
            "authority_profile_id": authority_profile_id,
            "revalidate_current_gate": True,
            "allow_same_turn_revision": bool(allow_self_reinforcement),
            "self_derived_signal_policy": "fail_closed",
            "allow_self_reinforcement": bool(allow_self_reinforcement),
        }
        self.sessions.update_controls(
            session_id,
            config_updates=config_updates,
            session_config_updates=session_config_updates,
            core_config_updates=core_updates,
        )
        return self.inspection.session_view(session_id)

    def update_session_advanced(
        self,
        session_id: str,
        *,
        settings: dict[str, Any],
        external_confirmed: bool = False,
        force: bool = False,
    ) -> dict[str, Any]:
        """Persist direct Workbench controls onto the canonical runtime config.

        This is the expert/God-mode boundary used by the local Workbench. It does
        not create a parallel settings model: values are written to the persisted
        SessionConfig, ShadowChatSession session_config, and SSLCoreConfig snapshot
        consumed by the next runtime turn.

        Structural semantic-memory settings are blocked once seeds exist.
        Embedding backend/model, recurrence mode, and cluster threshold determine
        how persisted seed state is interpreted and therefore require a new
        session or an explicit rebuild/migration path. God-mode force does not
        reinterpret existing vectors or recurrence state.
        """

        if not isinstance(settings, dict):
            raise TypeError("settings must be a dictionary")

        view = self.inspection.session_view(session_id)
        persisted = dict(view.get("persisted_config", {}))

        session_fields = set(SessionConfig.__dataclass_fields__)
        core_fields = set(SSLCoreConfig.__dataclass_fields__)
        known = session_fields | core_fields
        unknown = sorted(set(settings) - known)
        if unknown:
            raise ValueError(f"unknown Shadowseed setting(s): {', '.join(unknown)}")

        desired = {**persisted, **settings}
        desired_backend = str(desired.get("backend", view.get("backend") or "fixture"))
        desired_model = desired.get("model_id")
        desired_revision_backend = desired.get("revision_backend")
        desired_revision_model = desired.get("revision_model_id")
        desired_detection_backend = desired.get("detection_backend")
        desired_detection_model = desired.get("detection_model_id")
        desired_runtime = str(desired.get("runtime_mode", view.get("runtime_mode") or "live"))
        desired_embedding = str(
            desired.get("embedding_backend", view.get("embedding_backend") or "lexical")
        )
        desired_toy = bool(desired.get("allow_toy_embedder", False))

        structural_keys = (
            "embedding_backend",
            "embedding_model",
            "recurrence_mode",
            "cluster_threshold",
        )
        structural_changes = [
            key
            for key in structural_keys
            if key in settings and settings.get(key) != persisted.get(key)
        ]
        if structural_changes and view.get("seeds"):
            forced = (
                " God mode force cannot bypass this boundary."
                if force
                else ""
            )
            raise ValueError(
                "structural setting(s) "
                + ", ".join(structural_changes)
                + " cannot be changed after seeds exist; start a new session "
                "or use a future explicit rebuild/migration path."
                + forced
            )

        self._validate_backend(
            desired_backend,
            model_id=desired_model,
            revision_backend=(
                None
                if desired_revision_backend is None
                else str(desired_revision_backend)
            ),
            revision_model_id=(
                None
                if desired_revision_model is None
                else str(desired_revision_model)
            ),
            detection_backend=(
                None
                if desired_detection_backend is None
                else str(desired_detection_backend)
            ),
            detection_model_id=(
                None
                if desired_detection_model is None
                else str(desired_detection_model)
            ),
            runtime_mode=desired_runtime,
            embedding_backend=desired_embedding,
            allow_toy_embedder=desired_toy,
            external_confirmed=external_confirmed,
        )

        config_updates = dict(settings)
        # The pre-0.11 expert flag is a compatibility alias for revision only.
        # It never opens self-derived recurrence.
        if "allow_self_reinforcement" in settings:
            compatibility_revision = bool(settings["allow_self_reinforcement"])
            config_updates["allow_same_turn_revision"] = compatibility_revision
            config_updates["self_derived_signal_policy"] = "fail_closed"
            settings = {
                **settings,
                "allow_same_turn_revision": compatibility_revision,
                "self_derived_signal_policy": "fail_closed",
            }
        product_only_fields = {"ssl_intensity", "gate_strictness"}
        state_updates = {
            key: value
            for key, value in settings.items()
            if (
                key in session_fields
                and key not in core_fields
                and key not in product_only_fields
            )
        }
        core_updates = {
            key: value for key, value in settings.items() if key in core_fields
        }

        if any(
            key in settings
            for key in (
                "gate_policy_id",
                "authority_profile_id",
                "min_occurrences_for_gate",
                "min_evidence_for_gate",
                "min_trace_for_gate",
                "promotion_threshold",
                "validation_increment",
            )
        ):
            config_updates["revalidate_current_gate"] = True
            state_updates["revalidate_current_gate"] = True

        if "ssl_intensity" not in settings and any(
            key in settings
            for key in (
                "surface_threshold",
                "surface_top_k",
                "early_turn_margin",
                "early_turn_history",
                "resurface_margin",
            )
        ):
            config_updates["ssl_intensity"] = None
        if "gate_strictness" not in settings and any(
            key in settings
            for key in (
                "gate_policy_id",
                "authority_profile_id",
                "min_occurrences_for_gate",
                "min_evidence_for_gate",
                "min_trace_for_gate",
                "promotion_threshold",
                "validation_increment",
            )
        ):
            config_updates["gate_strictness"] = None

        self.sessions.update_controls(
            session_id,
            config_updates=config_updates,
            session_config_updates=state_updates,
            core_config_updates=core_updates,
        )
        return self.inspection.session_view(session_id)
    def update_session_self_reinforcement(
        self,
        session_id: str,
        *,
        allow_self_reinforcement: bool,
    ) -> dict[str, Any]:
        """Compatibility toggle for bounded same-turn revision only.

        The historical control name is retained for older callers. In 0.11 it
        never enables self-derived recurrence; that policy remains fail-closed.
        """

        loop = bool(allow_self_reinforcement)
        updates = {
            "allow_self_reinforcement": loop,
            "allow_same_turn_revision": loop,
            "self_derived_signal_policy": "fail_closed",
        }
        self.sessions.update_controls(
            session_id,
            config_updates=updates,
            session_config_updates=updates,
            core_config_updates={},
        )
        return self.inspection.session_view(session_id)

    def send_turn(
        self,
        session_id: str,
        question: str,
        *,
        compare_without_ssl: bool = False,
        comparison_mode: str = "authorized",
        external_confirmed: bool = False,
        request_id: str | None = None,
    ) -> dict[str, Any]:
        stored = self.sessions.load(session_id)
        config = dict(stored.get("config", {}))
        self._validate_backend(
            str(stored["backend"]),
            model_id=stored.get("model_id"),
            revision_backend=(
                None
                if config.get("revision_backend") is None
                else str(config.get("revision_backend"))
            ),
            revision_model_id=(
                None
                if config.get("revision_model_id") is None
                else str(config.get("revision_model_id"))
            ),
            detection_backend=(
                None
                if config.get("detection_backend") is None
                else str(config.get("detection_backend"))
            ),
            detection_model_id=(
                None
                if config.get("detection_model_id") is None
                else str(config.get("detection_model_id"))
            ),
            runtime_mode=str(config.get("runtime_mode", "evaluation")),
            embedding_backend=str(config.get("embedding_backend", "lexical")),
            allow_toy_embedder=bool(config.get("allow_toy_embedder", False)),
            external_confirmed=external_confirmed,
        )
        actor = (
            self.workspace.local_actor_context(request_id=request_id)
            if request_id is not None
            else None
        )
        report = self.sessions.run_turn(
            session_id,
            question,
            compare_without_ssl=compare_without_ssl,
            comparison_mode=comparison_mode,
            actor=actor,
        )
        comparison = None
        if compare_without_ssl:
            comparison = self.comparison.compare_turn(
                session_id,
                int(report["turn"]),
                blinded=False,
                reveal=True,
            )
        return {
            "report": report,
            "comparison": comparison,
            "session": self.inspection.session_view(session_id),
        }

    def ingest_sources(
        self,
        session_id: str,
        *,
        pasted_text: str = "",
        file_paths: list[str] | None = None,
        external_confirmed: bool = False,
    ) -> dict[str, Any]:
        stored = self.sessions.load(session_id)
        config = dict(stored.get("config", {}))
        self._validate_backend(
            str(stored["backend"]),
            model_id=stored.get("model_id"),
            revision_backend=(
                None
                if config.get("revision_backend") is None
                else str(config.get("revision_backend"))
            ),
            revision_model_id=(
                None
                if config.get("revision_model_id") is None
                else str(config.get("revision_model_id"))
            ),
            detection_backend=(
                None
                if config.get("detection_backend") is None
                else str(config.get("detection_backend"))
            ),
            detection_model_id=(
                None
                if config.get("detection_model_id") is None
                else str(config.get("detection_model_id"))
            ),
            runtime_mode=str(config.get("runtime_mode", "evaluation")),
            embedding_backend=str(config.get("embedding_backend", "lexical")),
            allow_toy_embedder=bool(config.get("allow_toy_embedder", False)),
            external_confirmed=external_confirmed,
        )
        chunks = prepare_sources(
            pasted_text=pasted_text or "",
            file_paths=file_paths or [],
        )
        payload = [
            {
                "source_name": chunk.source_name,
                "source_instance_id": chunk.source_instance_id,
                "context_ref": chunk.context_ref,
                "text": chunk.text,
            }
            for chunk in chunks
        ]
        result = self.sessions.ingest_source_chunks(session_id, payload)
        result["session"] = self.inspection.session_view(session_id)
        return result

    def session_view(self, session_id: str) -> dict[str, Any]:
        return self.inspection.session_view(session_id)

    def falsify_seed(
        self,
        session_id: str,
        seed_id: str,
        *,
        request_id: str | None = None,
    ) -> dict[str, Any]:
        """Submit an attributed local-owner contradiction through authorization."""

        actor = (
            self.workspace.local_actor_context()
            if request_id is None
            else self.workspace.local_actor_context(request_id=request_id)
        )
        return self.sessions.falsify_authorized(
            session_id,
            seed_id,
            actor=actor,
        )

    def resolve_contradiction(
        self,
        session_id: str,
        seed_id: str,
        *,
        basis: str,
        contradiction_id: str | None = None,
        request_id: str | None = None,
    ) -> dict[str, Any]:
        """Resolve a blocking contradiction through the existing production flow."""

        actor = (
            self.workspace.local_actor_context()
            if request_id is None
            else self.workspace.local_actor_context(request_id=request_id)
        )
        return resolve_authorized_contradiction(
            self.workspace.repository,
            session_id,
            seed_id,
            basis=basis,
            contradiction_id=contradiction_id,
            actor=actor,
            scope_id=self.workspace.workspace_id,
        )

    def submit_verified_evidence(
        self,
        session_id: str,
        seed_id: str,
        *,
        source_ref: str,
        note: str = "",
        operator_verified: bool = False,
        request_id: str | None = None,
    ) -> dict[str, Any]:
        """Submit verified support with UI attestation plus trusted local authorization.

        ``operator_verified`` is only the explicit evidence-verification attestation from
        the local user. It is not authorization. The trusted ActorContext is created here
        at the product boundary and is required separately before runtime mutation.
        """

        if not operator_verified:
            raise ValueError("operator verification must be explicitly confirmed")
        actor = (
            self.workspace.local_actor_context()
            if request_id is None
            else self.workspace.local_actor_context(request_id=request_id)
        )
        return self.sessions.submit_verified_evidence_authorized(
            session_id,
            seed_id,
            source_ref=source_ref,
            note=note,
            actor=actor,
        )

    def seed_view(self, session_id: str, seed_id: str) -> dict[str, Any]:
        return self.inspection.seed_view(session_id, seed_id)

    def record_feedback(
        self,
        *,
        session_id: str,
        turn_index: int,
        overall: str,
        seed_effect: str,
        note: str = "",
        seed_id: str | None = None,
    ) -> dict[str, Any]:
        return self.feedback.record(
            session_id=session_id,
            turn_index=int(turn_index),
            overall=overall,
            seed_effect=seed_effect,
            note=note,
            seed_id=seed_id or None,
        ).to_dict()

    def compare_turn(
        self,
        session_id: str,
        turn_index: int,
        *,
        blinded: bool = True,
        reveal: bool = False,
    ) -> dict[str, Any]:
        return self.comparison.compare_turn(
            session_id,
            int(turn_index),
            blinded=blinded,
            reveal=reveal,
        )

    def parse_scenario(self, scenario_json: str) -> dict[str, Any]:
        return self.scenarios.parse(scenario_json).to_dict()

    def run_scenario(
        self,
        scenario_json: str,
        *,
        external_confirmed: bool = False,
    ) -> dict[str, Any]:
        scenario: ScenarioSpec = self.scenarios.parse(scenario_json)
        self._validate_backend(
            scenario.backend,
            model_id=scenario.model_id,
            runtime_mode=scenario.runtime_mode,
            embedding_backend=scenario.embedding_backend,
            allow_toy_embedder=scenario.allow_toy_embedder,
            external_confirmed=external_confirmed,
        )
        result = self.scenarios.run(scenario)
        result["session"] = self.inspection.session_view(result["session_id"])
        return result

    def resume_scenario(
        self,
        scenario_json: str,
        session_id: str,
        *,
        start_at: int | None = None,
        external_confirmed: bool = False,
    ) -> dict[str, Any]:
        scenario = self.scenarios.parse(scenario_json)
        stored = self.sessions.load(session_id)
        if scenario.profile_id != stored["profile_id"]:
            raise ValueError("scenario profile does not match the persisted session")
        if scenario.backend != stored["backend"]:
            raise ValueError("scenario backend does not match the persisted session")
        if (scenario.model_id or None) != (stored.get("model_id") or None):
            raise ValueError("scenario model does not match the persisted session")
        config = dict(stored.get("config", {}))
        expected_config = {
            "runtime_mode": scenario.runtime_mode,
            "embedding_backend": scenario.embedding_backend,
            "embedding_model": scenario.embedding_model,
            "allow_toy_embedder": scenario.allow_toy_embedder,
        }
        legacy_defaults = {
            "runtime_mode": "evaluation",
            "embedding_backend": "lexical",
            "embedding_model": None,
            "allow_toy_embedder": False,
        }
        for key, expected in expected_config.items():
            if config.get(key, legacy_defaults[key]) != expected:
                raise ValueError(f"scenario {key} does not match the persisted session")
        self._validate_backend(
            str(stored["backend"]),
            model_id=stored.get("model_id"),
            runtime_mode=scenario.runtime_mode,
            embedding_backend=scenario.embedding_backend,
            allow_toy_embedder=scenario.allow_toy_embedder,
            external_confirmed=external_confirmed,
        )
        result = self.scenarios.resume(scenario, session_id, start_at=start_at)
        result["session"] = self.inspection.session_view(session_id)
        return result

    def export_report(self, session_id: str, destination: str | Path) -> str:
        return str(self.exports.export_report(session_id, destination))

    def export_support_bundle(self, session_id: str, destination: str | Path) -> str:
        return str(self.exports.export_support_bundle(session_id, destination))

    @staticmethod
    def verify_export(path: str | Path) -> dict[str, Any]:
        return verify_workbench_export(path)

    @staticmethod
    def chat_messages(session_view: dict[str, Any]) -> list[dict[str, str]]:
        messages: list[dict[str, str]] = []
        for report in session_view.get("turn_reports", []):
            messages.append({"role": "user", "content": str(report.get("question", ""))})
            messages.append({"role": "assistant", "content": str(report.get("answer", ""))})
        return messages

    @staticmethod
    def session_choices(summaries: list[dict[str, Any]]) -> list[tuple[str, str]]:
        choices: list[tuple[str, str]] = []
        for item in summaries:
            runtime_mode = item.get("runtime_mode", "evaluation")
            experience = "SSL chat" if runtime_mode == "live" else "Research comparison"
            choices.append(
                (
                    f"{item['title']} · {experience} · {item['backend']} · "
                    f"{item['turn_count']} turns",
                    str(item["session_id"]),
                )
            )
        return choices

    @staticmethod
    def seed_choices(session_view: dict[str, Any]) -> list[tuple[str, str]]:
        choices: list[tuple[str, str]] = []
        for seed in session_view.get("seeds", []):
            seed_id = str(seed.get("id", ""))
            text = str(seed.get("text", "")).replace("\n", " ")
            status = str(seed.get("status", "unknown"))
            choices.append((f"{status} · {text[:72]}", seed_id))
        return choices

    @staticmethod
    def _validate_backend(
        backend: str,
        *,
        model_id: str | None,
        revision_backend: str | None = None,
        revision_model_id: str | None = None,
        detection_backend: str | None = None,
        detection_model_id: str | None = None,
        runtime_mode: str = "live",
        embedding_backend: str = "lexical",
        allow_toy_embedder: bool = False,
        external_confirmed: bool,
    ) -> None:
        if backend not in BACKENDS:
            raise ValueError(f"unsupported Workbench backend: {backend}")
        if runtime_mode not in RUNTIME_MODES:
            raise ValueError(f"unsupported Workbench runtime mode: {runtime_mode}")
        if embedding_backend not in EMBEDDING_BACKENDS:
            raise ValueError(f"unsupported Workbench embedding backend: {embedding_backend}")
        if backend != "fixture" and not str(model_id or "").strip():
            raise ValueError(f"backend {backend!r} requires a model id")
        effective_revision_backend = revision_backend or backend
        effective_revision_model_id = (
            revision_model_id
            if revision_model_id is not None
            else (model_id if effective_revision_backend == backend else None)
        )
        if effective_revision_backend not in BACKENDS:
            raise ValueError(
                f"unsupported Workbench revision backend: {effective_revision_backend}"
            )
        if (
            effective_revision_backend != "fixture"
            and not str(effective_revision_model_id or "").strip()
        ):
            raise ValueError(
                f"revision backend {effective_revision_backend!r} requires a model id"
            )
        effective_detection_backend = detection_backend or backend
        effective_detection_model_id = (
            detection_model_id
            if detection_model_id is not None
            else (model_id if effective_detection_backend == backend else None)
        )
        if effective_detection_backend not in BACKENDS:
            raise ValueError(
                f"unsupported Workbench detection backend: {effective_detection_backend}"
            )
        if (
            effective_detection_backend != "fixture"
            and not str(effective_detection_model_id or "").strip()
        ):
            raise ValueError(
                f"detection backend {effective_detection_backend!r} requires a model id"
            )
        if (
            runtime_mode == "live"
            and backend != "fixture"
            and embedding_backend == "lexical"
            and not allow_toy_embedder
        ):
            raise ValueError(
                "live non-fixture sessions require a semantic embedding backend "
                "(sentence-transformers, ollama or openai); enable the toy override only for an explicit test"
            )
        uses_external_provider = (
            backend in _EXTERNAL_PROMPT_BACKENDS
            or effective_revision_backend in _EXTERNAL_PROMPT_BACKENDS
            or effective_detection_backend in _EXTERNAL_PROMPT_BACKENDS
            or embedding_backend == "openai"
        )
        if uses_external_provider and not external_confirmed:
            raise ValueError(
                "this runtime sends content to an external provider; check the explicit "
                "external-provider confirmation before continuing"
            )

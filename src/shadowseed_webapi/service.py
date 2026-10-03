"""Framework-free application adapter for the Shadowseed web client."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from shadowseed.application.provider_policy import (
    ProviderPolicyError,
    validate_production_local_backend,
)
from shadowseed.storage.sqlite import WorkspaceStorageError
from shadowseed.workbench.controller import WorkbenchController
from shadowseed.workbench.production_controller import ProductionLocalWorkbenchController


_AUTHORITY_MODE_TO_PROFILE = {
    "controlled": "strict",
    "assisted": "assisted",
    "exploratory": "autonomous",
}
_MISSING = object()
_WEB_V1_BACKENDS = frozenset({"fixture", "ollama"})
_WEB_V1_EMBEDDING_BACKENDS = frozenset({"lexical", "ollama"})


def _optional_json_bool(
    payload: dict[str, Any],
    key: str,
    *,
    default: bool = False,
) -> bool:
    """Return a JSON boolean without accepting truthy strings or numbers."""

    value = payload.get(key, default)
    if not isinstance(value, bool):
        raise ValueError(f"{key} must be a JSON boolean")
    return value


def _json_string(
    payload: dict[str, Any],
    key: str,
    *,
    default: str | object = _MISSING,
    required: bool = False,
    allow_null: bool = False,
) -> str | None:
    """Validate a JSON string while keeping missing and explicit null distinct."""

    if key not in payload:
        if default is not _MISSING:
            return str(default)
        if required:
            raise ValueError(f"{key} is required")
        return None

    value = payload[key]
    if value is None:
        if allow_null:
            return None
        raise ValueError(f"{key} must be a JSON string")
    if not isinstance(value, str):
        raise ValueError(f"{key} must be a JSON string")

    normalized = value.strip()
    if required and not normalized:
        raise ValueError(f"{key} is required")
    return normalized


def _defaulted_json_string(
    payload: dict[str, Any],
    key: str,
    default: str,
) -> str:
    value = _json_string(payload, key, default=default)
    if value is None:  # Defensive; explicit null is rejected by _json_string.
        raise ValueError(f"{key} must be a JSON string")
    return value


def _required_json_string(payload: dict[str, Any], key: str) -> str:
    value = _json_string(payload, key, required=True)
    if value is None:  # Defensive; missing/null already raise above.
        raise ValueError(f"{key} is required")
    return value


def _request_id(payload: dict[str, Any]) -> str:
    value = _required_json_string(payload, "request_id")
    allowed = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_.:")
    if len(value) > 128 or any(character not in allowed for character in value):
        raise ValueError(
            "request_id must be 1-128 characters using letters, numbers, '-', '_', '.', or ':'"
        )
    return value


def _raise_idempotency_conflict(exc: WorkspaceStorageError) -> None:
    message = str(exc)
    if (
        "request_id was already used" in message
        or "request_id was replayed" in message
    ):
        raise ValueError(message) from exc
    raise exc


class WebApiService:
    """Expose product-shaped operations without reimplementing SSL semantics."""

    def __init__(
        self,
        workspace: str | Path | None = None,
        *,
        controller: WorkbenchController | None = None,
    ) -> None:
        self.controller = controller or ProductionLocalWorkbenchController(workspace)

    def health(self) -> dict[str, Any]:
        return {"ok": True, "api_version": "v1"}

    def list_sessions(self) -> dict[str, Any]:
        sessions = []
        for item in self.controller.list_sessions():
            try:
                view = self.controller.session_view(str(item["session_id"]))
            except KeyError:
                continue
            if self._session_provider_supported(view):
                sessions.append(item)
        return {"sessions": sessions}

    def get_session(self, session_id: str) -> dict[str, Any]:
        return self._session_payload(self._supported_session_view(session_id))

    def get_seed(self, session_id: str, seed_id: str) -> dict[str, Any]:
        self._supported_session_view(session_id)
        return self.controller.seed_view(session_id, seed_id)

    def create_session(self, payload: dict[str, Any]) -> dict[str, Any]:
        title = _defaulted_json_string(payload, "title", "Nieuw gesprek")
        title = title or "Nieuw gesprek"
        backend = _defaulted_json_string(payload, "backend", "fixture")
        authority_mode = _defaulted_json_string(
            payload,
            "authority_mode",
            "assisted",
        )
        model_id = _json_string(payload, "model_id", allow_null=True)
        if model_id == "":
            model_id = None

        try:
            authority_profile_id = _AUTHORITY_MODE_TO_PROFILE[authority_mode]
        except KeyError as exc:
            allowed = ", ".join(sorted(_AUTHORITY_MODE_TO_PROFILE))
            raise ValueError(f"authority_mode must be one of: {allowed}") from exc

        if backend not in {"fixture", "ollama"}:
            raise ValueError("web client v1 supports only fixture and Ollama")
        if backend == "fixture":
            model_id = None
        elif not model_id:
            raise ValueError("Ollama requires a model_id")

        embedding_backend = self.controller.default_embedding_backend(backend)
        validate_production_local_backend(backend, embedding_backend)

        session_id = self.controller.create_session(
            title=title,
            profile_id="balanced",
            backend=backend,
            model_id=model_id,
            runtime_mode="live",
            authority_profile_id=authority_profile_id,
            embedding_backend=embedding_backend,
            allow_same_turn_revision=_optional_json_bool(
                payload,
                "allow_same_turn_revision",
            ),
            allow_self_reinforcement=False,
            external_confirmed=False,
        )
        return self.get_session(session_id)

    def run_turn(self, session_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        self._supported_session_view(session_id)
        question = _required_json_string(payload, "question")
        request_id = _request_id(payload)

        try:
            result = self.controller.send_turn(
                session_id,
                question,
                compare_without_ssl=_optional_json_bool(
                    payload,
                    "compare_without_ssl",
                ),
                comparison_mode="authorized",
                external_confirmed=False,
                request_id=request_id,
            )
        except WorkspaceStorageError as exc:
            _raise_idempotency_conflict(exc)
        return {
            "report": result["report"],
            "comparison": result["comparison"],
            "session": self._session_payload(dict(result["session"])),
        }

    def submit_evidence(
        self,
        session_id: str,
        seed_id: str,
        payload: dict[str, Any],
    ) -> dict[str, Any]:
        source_ref = _required_json_string(payload, "source_ref")
        note = _defaulted_json_string(payload, "note", "")

        operator_verified = payload.get("operator_verified")
        if operator_verified is not True:
            raise ValueError(
                "operator_verified must be the literal JSON boolean true"
            )
        request_id = _request_id(payload)

        self._supported_session_view(session_id)
        try:
            self.controller.submit_verified_evidence(
                session_id,
                seed_id,
                source_ref=source_ref,
                note=note,
                operator_verified=True,
                request_id=request_id,
            )
        except WorkspaceStorageError as exc:
            _raise_idempotency_conflict(exc)
        return self.get_session(session_id)

    def contradict_seed(
        self,
        session_id: str,
        seed_id: str,
        payload: dict[str, Any],
    ) -> dict[str, Any]:
        request_id = _request_id(payload)
        self._supported_session_view(session_id)
        try:
            self.controller.falsify_seed(
                session_id,
                seed_id,
                request_id=request_id,
            )
        except WorkspaceStorageError as exc:
            _raise_idempotency_conflict(exc)
        return self.get_session(session_id)

    def resolve_contradiction(
        self,
        session_id: str,
        seed_id: str,
        payload: dict[str, Any],
    ) -> dict[str, Any]:
        basis = _required_json_string(payload, "basis")
        request_id = _request_id(payload)
        contradiction_id = _json_string(
            payload,
            "contradiction_id",
            allow_null=True,
        )
        if contradiction_id == "":
            contradiction_id = None

        self._supported_session_view(session_id)
        try:
            self.controller.resolve_contradiction(
                session_id,
                seed_id,
                basis=basis,
                contradiction_id=contradiction_id,
                request_id=request_id,
            )
        except WorkspaceStorageError as exc:
            _raise_idempotency_conflict(exc)
        return self.get_session(session_id)

    @staticmethod
    def _session_provider_supported(view: dict[str, Any]) -> bool:
        backend = str(view.get("backend") or "").strip()
        revision_backend = str(
            view.get("revision_backend") or backend
        ).strip()
        embedding_backend = str(
            view.get("embedding_backend") or "lexical"
        ).strip()
        if not (
            backend in _WEB_V1_BACKENDS
            and revision_backend in _WEB_V1_BACKENDS
            and embedding_backend in _WEB_V1_EMBEDDING_BACKENDS
        ):
            return False
        try:
            validate_production_local_backend(backend, embedding_backend)
            validate_production_local_backend(revision_backend, embedding_backend)
        except ProviderPolicyError:
            return False
        return True

    def _supported_session_view(self, session_id: str) -> dict[str, Any]:
        view = self.controller.session_view(session_id)
        if not self._session_provider_supported(view):
            raise ValueError(
                "web client v1 does not support this session provider configuration"
            )
        return view

    def _session_payload(self, view: dict[str, Any]) -> dict[str, Any]:
        return {**view, "messages": self.controller.chat_messages(view)}

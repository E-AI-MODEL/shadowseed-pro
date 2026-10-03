"""Framework-free application adapter for the Shadowseed web client."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from shadowseed.workbench.controller import WorkbenchController


_AUTHORITY_MODE_TO_PROFILE = {
    "controlled": "strict",
    "assisted": "assisted",
    "exploratory": "autonomous",
}
_MISSING = object()
_WEB_V1_BACKENDS = frozenset({"fixture", "ollama"})


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


class WebApiService:
    """Expose product-shaped operations without reimplementing SSL semantics."""

    def __init__(
        self,
        workspace: str | Path | None = None,
        *,
        controller: WorkbenchController | None = None,
    ) -> None:
        self.controller = controller or WorkbenchController(workspace)

    def health(self) -> dict[str, Any]:
        return {"ok": True, "api_version": "v1"}

    def list_sessions(self) -> dict[str, Any]:
        sessions = [
            item
            for item in self.controller.list_sessions()
            if item.get("backend") in _WEB_V1_BACKENDS
        ]
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

        session_id = self.controller.create_session(
            title=title,
            profile_id="balanced",
            backend=backend,
            model_id=model_id,
            runtime_mode="live",
            authority_profile_id=authority_profile_id,
            embedding_backend=self.controller.default_embedding_backend(backend),
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

        result = self.controller.send_turn(
            session_id,
            question,
            compare_without_ssl=_optional_json_bool(
                payload,
                "compare_without_ssl",
            ),
            comparison_mode="authorized",
            external_confirmed=False,
        )
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

        self._supported_session_view(session_id)
        self.controller.submit_verified_evidence(
            session_id,
            seed_id,
            source_ref=source_ref,
            note=note,
            operator_verified=True,
        )
        return self.get_session(session_id)

    def contradict_seed(
        self,
        session_id: str,
        seed_id: str,
    ) -> dict[str, Any]:
        self._supported_session_view(session_id)
        self.controller.falsify_seed(session_id, seed_id)
        return self.get_session(session_id)

    def _supported_session_view(self, session_id: str) -> dict[str, Any]:
        view = self.controller.session_view(session_id)
        backend = str(view.get("backend") or "").strip()
        if backend not in _WEB_V1_BACKENDS:
            raise ValueError(
                "web client v1 supports only fixture and Ollama sessions"
            )
        return view

    def _session_payload(self, view: dict[str, Any]) -> dict[str, Any]:
        return {**view, "messages": self.controller.chat_messages(view)}

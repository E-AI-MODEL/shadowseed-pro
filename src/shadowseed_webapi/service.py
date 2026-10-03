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
        return {"sessions": self.controller.list_sessions()}

    def get_session(self, session_id: str) -> dict[str, Any]:
        return self._session_payload(self.controller.session_view(session_id))

    def get_seed(self, session_id: str, seed_id: str) -> dict[str, Any]:
        return self.controller.seed_view(session_id, seed_id)

    def create_session(self, payload: dict[str, Any]) -> dict[str, Any]:
        title = str(payload.get("title") or "Nieuw gesprek").strip() or "Nieuw gesprek"
        backend = str(payload.get("backend") or "fixture").strip()
        model_id_raw = payload.get("model_id")
        model_id = None if model_id_raw in (None, "") else str(model_id_raw).strip()

        authority_mode = str(payload.get("authority_mode") or "assisted").strip()
        try:
            authority_profile_id = _AUTHORITY_MODE_TO_PROFILE[authority_mode]
        except KeyError as exc:
            allowed = ", ".join(sorted(_AUTHORITY_MODE_TO_PROFILE))
            raise ValueError(f"authority_mode must be one of: {allowed}") from exc

        if backend not in {"fixture", "ollama"}:
            raise ValueError("web client v1 supports only fixture and Ollama")
        if backend == "ollama" and not model_id:
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
        question = str(payload.get("question") or "").strip()
        if not question:
            raise ValueError("question is required")

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
        source_ref = str(payload.get("source_ref") or "").strip()
        if not source_ref:
            raise ValueError("source_ref is required")

        operator_verified = payload.get("operator_verified")
        if operator_verified is not True:
            raise ValueError(
                "operator_verified must be the literal JSON boolean true"
            )

        self.controller.submit_verified_evidence(
            session_id,
            seed_id,
            source_ref=source_ref,
            note=str(payload.get("note") or ""),
            operator_verified=True,
        )
        return self.get_session(session_id)

    def contradict_seed(
        self,
        session_id: str,
        seed_id: str,
    ) -> dict[str, Any]:
        self.controller.falsify_seed(session_id, seed_id)
        return self.get_session(session_id)

    def _session_payload(self, view: dict[str, Any]) -> dict[str, Any]:
        return {**view, "messages": self.controller.chat_messages(view)}

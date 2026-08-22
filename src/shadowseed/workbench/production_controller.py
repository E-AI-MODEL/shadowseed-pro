"""Production-local product controller boundary.

This wraps the generic Workbench controller with deployment-only controls. It
never changes Validation Gate semantics or grants seed authority itself.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from shadowseed.application.operations import OperationalEventLog
from shadowseed.application.provider_policy import validate_production_local_backend
from shadowseed.workbench.controller import WorkbenchController


class ProductionLocalWorkbenchController(WorkbenchController):
    """Single-user local controller with endpoint policy and minimized telemetry."""

    def __init__(self, workspace: str | Path | None = None) -> None:
        super().__init__(workspace)
        self.operations = OperationalEventLog(self.workspace.paths.logs)
        self.operations.emit(
            "workspace.ready",
            workspace_id=self.workspace.workspace_id,
            status="ok",
            integrity_status="verified",
            schema_version=self.workspace.repository.schema_version(),
        )

    @staticmethod
    def _validate_backend(
        backend: str,
        *,
        model_id: str | None,
        runtime_mode: str = "live",
        embedding_backend: str = "lexical",
        allow_toy_embedder: bool = False,
        external_confirmed: bool,
    ) -> None:
        validate_production_local_backend(backend, embedding_backend)
        WorkbenchController._validate_backend(
            backend,
            model_id=model_id,
            runtime_mode=runtime_mode,
            embedding_backend=embedding_backend,
            allow_toy_embedder=allow_toy_embedder,
            external_confirmed=external_confirmed,
        )

    @staticmethod
    def discover_models(backend: str) -> list[str]:
        if backend == "ollama":
            validate_production_local_backend("ollama", "lexical")
        return WorkbenchController.discover_models(backend)

    def _emit_failure(self, event: str, exc: BaseException, **fields: Any) -> None:
        self.operations.emit(
            event,
            status="error",
            error_type=type(exc).__name__,
            **fields,
        )

    def create_session(self, **kwargs: Any) -> str:
        try:
            session_id = super().create_session(**kwargs)
        except BaseException as exc:
            self._emit_failure("session.create", exc)
            raise
        self.operations.emit(
            "session.create",
            session_id=session_id,
            backend=str(kwargs.get("backend") or ""),
            runtime_mode=str(kwargs.get("runtime_mode") or "live"),
            status="ok",
        )
        return session_id

    def send_turn(
        self,
        session_id: str,
        question: str,
        *,
        compare_without_ssl: bool = False,
        external_confirmed: bool = False,
    ) -> dict[str, Any]:
        try:
            result = super().send_turn(
                session_id,
                question,
                compare_without_ssl=compare_without_ssl,
                external_confirmed=external_confirmed,
            )
        except BaseException as exc:
            self._emit_failure("session.turn", exc, session_id=session_id)
            raise
        self.operations.emit(
            "session.turn",
            session_id=session_id,
            status="ok",
        )
        return result

    def falsify_seed(self, session_id: str, seed_id: str) -> dict[str, Any]:
        try:
            result = super().falsify_seed(session_id, seed_id)
        except BaseException as exc:
            self._emit_failure(
                "contradiction.submit",
                exc,
                session_id=session_id,
                seed_id=seed_id,
            )
            raise
        self.operations.emit(
            "contradiction.submit",
            session_id=session_id,
            seed_id=seed_id,
            status="ok",
        )
        return result

    def submit_verified_evidence(
        self,
        session_id: str,
        seed_id: str,
        *,
        source_ref: str,
        note: str = "",
        operator_verified: bool = False,
    ) -> dict[str, Any]:
        try:
            result = super().submit_verified_evidence(
                session_id,
                seed_id,
                source_ref=source_ref,
                note=note,
                operator_verified=operator_verified,
            )
        except BaseException as exc:
            self._emit_failure(
                "evidence.verify",
                exc,
                session_id=session_id,
                seed_id=seed_id,
            )
            raise
        self.operations.emit(
            "evidence.verify",
            session_id=session_id,
            seed_id=seed_id,
            status="ok",
            gate_decision=str(result.get("decision") or "unknown"),
            gate_policy_id=str(result.get("policy_id") or "unknown"),
        )
        return result

    def export_report(self, session_id: str, destination: str | Path) -> str:
        try:
            result = super().export_report(session_id, destination)
        except BaseException as exc:
            self._emit_failure("export.report", exc, session_id=session_id)
            raise
        self.operations.emit("export.report", session_id=session_id, status="ok")
        return result

    def export_support_bundle(self, session_id: str, destination: str | Path) -> str:
        try:
            result = super().export_support_bundle(session_id, destination)
        except BaseException as exc:
            self._emit_failure("export.support", exc, session_id=session_id)
            raise
        self.operations.emit("export.support", session_id=session_id, status="ok")
        return result

"""Web product controller with local hardening plus explicit hosted-provider consent."""

from __future__ import annotations

from shadowseed.application.provider_policy import validate_production_local_backend
from shadowseed.workbench.controller import WorkbenchController
from shadowseed.workbench.production_controller import ProductionLocalWorkbenchController


class WebWorkbenchController(ProductionLocalWorkbenchController):
    """Preserve production-local controls while allowing explicit OpenAI egress.

    The web adapter constrains supported provider combinations. This controller
    adds defense in depth: every Ollama route remains loopback-only, while
    OpenAI still passes through the canonical Workbench external-consent check.
    """

    @staticmethod
    def _validate_backend(
        backend: str,
        *,
        model_id: str | None,
        revision_backend: str | None = None,
        revision_model_id: str | None = None,
        runtime_mode: str = "live",
        embedding_backend: str = "lexical",
        allow_toy_embedder: bool = False,
        external_confirmed: bool,
    ) -> None:
        effective_revision_backend = revision_backend or backend
        uses_openai = (
            backend == "openai"
            or effective_revision_backend == "openai"
            or embedding_backend == "openai"
        )

        if not uses_openai:
            ProductionLocalWorkbenchController._validate_backend(
                backend,
                model_id=model_id,
                revision_backend=revision_backend,
                revision_model_id=revision_model_id,
                runtime_mode=runtime_mode,
                embedding_backend=embedding_backend,
                allow_toy_embedder=allow_toy_embedder,
                external_confirmed=external_confirmed,
            )
            return

        # Hosted-provider support must never weaken local Ollama endpoint policy.
        if backend == "ollama":
            validate_production_local_backend("ollama", "lexical")
        if effective_revision_backend == "ollama":
            validate_production_local_backend("ollama", "lexical")
        if embedding_backend == "ollama":
            validate_production_local_backend("fixture", "ollama")

        WorkbenchController._validate_backend(
            backend,
            model_id=model_id,
            revision_backend=revision_backend,
            revision_model_id=revision_model_id,
            runtime_mode=runtime_mode,
            embedding_backend=embedding_backend,
            allow_toy_embedder=allow_toy_embedder,
            external_confirmed=external_confirmed,
        )

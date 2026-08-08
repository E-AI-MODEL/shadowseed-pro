"""Installation and workspace diagnostics used by ``shadowseed doctor``."""

from __future__ import annotations

import importlib.util
import json
import os
import platform
import shutil
from pathlib import Path
from urllib.error import URLError
from urllib.request import Request, urlopen

from shadowseed.adapters.models import make_backend
from shadowseed.application.models import DoctorReport, HealthCheck
from shadowseed.application.workspace import WorkspaceService


def _ollama_check() -> HealthCheck:
    request = Request("http://127.0.0.1:11434/api/tags", headers={"Accept": "application/json"})
    try:
        with urlopen(request, timeout=0.5) as response:  # noqa: S310 - fixed localhost URL
            payload = json.loads(response.read().decode("utf-8"))
        models = [item.get("name", "") for item in payload.get("models", [])]
        detail = f"available ({len(models)} local model{'s' if len(models) != 1 else ''})"
        return HealthCheck("ollama", "ok", detail)
    except (OSError, URLError, json.JSONDecodeError):
        return HealthCheck(
            "ollama",
            "warning",
            "not detected at http://127.0.0.1:11434",
            "Start `ollama serve`, pull a model, and rerun `shadowseed doctor`.",
        )


def run_doctor(workspace: str | Path | None = None) -> DoctorReport:
    checks: list[HealthCheck] = []
    major, minor = platform.python_version_tuple()[:2]
    supported = (int(major), int(minor)) >= (3, 10)
    checks.append(
        HealthCheck(
            "python",
            "ok" if supported else "error",
            platform.python_version(),
            None if supported else "Install Python 3.10 or newer.",
        )
    )

    service = WorkspaceService(workspace)
    try:
        paths = service.initialize()
        checks.append(HealthCheck("workspace", "ok", str(paths.root)))
        checks.append(
            HealthCheck("sqlite_schema", "ok", str(service.repository.schema_version()))
        )
        writable = os.access(paths.root, os.W_OK) and os.access(paths.exports, os.W_OK)
        checks.append(
            HealthCheck(
                "workspace_write_access",
                "ok" if writable else "error",
                "writable" if writable else "not writable",
                None if writable else "Choose a writable --workspace directory.",
            )
        )
        free = shutil.disk_usage(paths.root).free
        checks.append(
            HealthCheck(
                "disk_space",
                "ok" if free >= 100 * 1024 * 1024 else "warning",
                f"{free // (1024 * 1024)} MiB free",
                None if free >= 100 * 1024 * 1024 else "Free at least 100 MiB.",
            )
        )
    except Exception as exc:
        checks.append(HealthCheck("workspace", "error", str(exc)))

    try:
        make_backend("fixture", None, 20)
        checks.append(HealthCheck("fixture_backend", "ok", "available"))
    except Exception as exc:
        checks.append(HealthCheck("fixture_backend", "error", str(exc)))

    checks.append(_ollama_check())
    checks.append(
        HealthCheck(
            "openai",
            "ok" if bool(os.getenv("OPENAI_API_KEY")) else "warning",
            "configured" if os.getenv("OPENAI_API_KEY") else "OPENAI_API_KEY is not set",
            None
            if os.getenv("OPENAI_API_KEY")
            else "Set OPENAI_API_KEY only for sessions that use the OpenAI backend.",
        )
    )
    hf_ready = all(importlib.util.find_spec(name) is not None for name in ("torch", "transformers"))
    checks.append(
        HealthCheck(
            "hugging_face",
            "ok" if hf_ready else "warning",
            "optional dependencies installed" if hf_ready else "optional dependencies missing",
            None if hf_ready else "Install `shadowseed[models]` to use local HF models.",
        )
    )
    return DoctorReport(tuple(checks))

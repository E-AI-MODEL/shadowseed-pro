"""Production-local Workbench launcher with a non-configurable loopback boundary."""

from __future__ import annotations

from pathlib import Path
from typing import Any


PRODUCTION_LOCAL_HOST = "127.0.0.1"


def launch_production_local_workbench(
    workspace: str | Path | None = None,
    *,
    port: int = 7860,
    inbrowser: bool = True,
) -> Any:
    """Launch the supported single-user local profile on IPv4 loopback only.

    This API intentionally has no host or remote-allow parameter. Trusted remote
    preview/development use remains a separate generic Workbench surface and is
    never upgraded into the production-local deployment contract.
    """

    from shadowseed.workbench.app import launch_workbench

    return launch_workbench(
        workspace,
        host=PRODUCTION_LOCAL_HOST,
        port=int(port),
        allow_remote=False,
        inbrowser=bool(inbrowser),
    )

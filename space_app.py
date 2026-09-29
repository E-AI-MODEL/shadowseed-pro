"""Hugging Face Spaces launcher for Shadowseed functional testing.

This is intentionally separate from the supported production-local launcher.
It exposes the same Workbench/controller/Gate stack on the container interface
required by Hugging Face Spaces. It does not change SSL authority semantics.
"""

from __future__ import annotations

import os
from pathlib import Path

from shadowseed.workbench.production_controller import ProductionLocalWorkbenchController
from shadowseed.workbench.production_local import build_production_local_app


DEFAULT_WORKSPACE = "/tmp/shadowseed-workspace"
DEFAULT_PORT = 7860


def workspace_path() -> Path:
    """Return the Space workspace path.

    Set SHADOWSEED_WORKSPACE=/data/shadowseed when persistent Space storage is
    attached. The default /tmp path is intentionally ephemeral.
    """

    return Path(os.environ.get("SHADOWSEED_WORKSPACE", DEFAULT_WORKSPACE)).expanduser()


def main() -> None:
    os.environ.setdefault("GRADIO_ANALYTICS_ENABLED", "False")
    os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")

    controller = ProductionLocalWorkbenchController(workspace_path())
    app = build_production_local_app(controller=controller)
    app.launch(
        server_name="0.0.0.0",
        server_port=int(os.environ.get("PORT", str(DEFAULT_PORT))),
        inbrowser=False,
        share=False,
    )


if __name__ == "__main__":
    main()

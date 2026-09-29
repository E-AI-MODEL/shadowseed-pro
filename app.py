"""Hugging Face Gradio Space launcher for Shadowseed functional testing.

This hosted test surface reuses the shipped Workbench, production controller,
semantic embedding path, Validation Gate, evidence submission, and point-of-use
logic. It is not the supported production-local deployment boundary.
"""

from __future__ import annotations

import os
from pathlib import Path

from shadowseed.workbench.production_controller import ProductionLocalWorkbenchController
from shadowseed.workbench.production_local import build_production_local_app


WORKSPACE = Path(
    os.environ.get("SHADOWSEED_WORKSPACE", "/tmp/shadowseed-workspace")
).expanduser()

os.environ.setdefault("GRADIO_ANALYTICS_ENABLED", "False")
os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")

controller = ProductionLocalWorkbenchController(WORKSPACE)
demo = build_production_local_app(controller=controller)

if __name__ == "__main__":
    demo.launch(
        server_name="0.0.0.0",
        server_port=int(os.environ.get("PORT", "7860")),
        inbrowser=False,
        share=False,
    )

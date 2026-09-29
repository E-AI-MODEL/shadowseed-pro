"""Hugging Face Gradio/ZeroGPU launcher for Shadowseed functional testing.

This hosted test surface reuses the shipped Workbench. ZeroGPU requires at
least one module-level @spaces.GPU function during startup. The small probe
below only registers that capability; Shadowseed's normal CPU path does not
consume GPU quota merely by starting the Space.
"""

from __future__ import annotations

import os
from pathlib import Path

try:
    import spaces

    @spaces.GPU(duration=5)
    def _zerogpu_probe() -> str:
        import torch
        return f"cuda available: {torch.cuda.is_available()}"

except ImportError:
    def _zerogpu_probe() -> str:
        return "ZeroGPU runtime unavailable"

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
        server_port=7860,
        inbrowser=False,
        share=False,
        ssr_mode=False,
    )

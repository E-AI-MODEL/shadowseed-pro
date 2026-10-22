"""ZeroGPU Space packaging and safety checks, without model/GPU downloads."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[2]
APP = ROOT / "research/spaces/layer-g-zerogpu/app.py"
CARD = ROOT / "research/spaces/layer-g-zerogpu/README.md"
REQUIREMENTS = ROOT / "research/spaces/layer-g-zerogpu/requirements.txt"
BUILD = ROOT / "research/scripts/build_layer_g_zerogpu_space.py"
DEPLOY = ROOT / "research/scripts/deploy_layer_g_zerogpu_space.py"
WORKFLOW = ROOT / ".github/workflows/deploy-layer-g-zerogpu.yml"


def _script(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, str(path))
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


def test_source_app_has_direct_gpu_event_and_no_user_input():
    source = APP.read_text(encoding="utf-8")
    compile(source, str(APP), "exec")
    assert source.index("import spaces") < source.index("import torch")
    assert "@spaces.GPU(duration=90)" in source
    assert "start.click(fn=run_pilot, inputs=[], outputs=[result, artifact])" in source
    assert "device_map=\"cuda\"" in source
    assert "Qwen/Qwen2.5-14B-Instruct" in source
    assert "load_in_4bit=True" in source
    assert "bnb_4bit_quant_type=\"nf4\"" in source
    assert "model_revision = model_info(MODEL_ID).sha" in source
    assert "GenerationRequest.from_original_prompt(original)" in source
    assert "write_generation_observation(" in source
    assert "research_claim" in source
    assert "unknown_neurons_proven" not in source
    for unwanted in ("OpenAI(", "api_key=", "hf_jobs(", "request_space_hardware("):
        assert unwanted not in source


def test_space_metadata_limits_and_supported_model_versions():
    card = CARD.read_text(encoding="utf-8")
    deps = REQUIREMENTS.read_text(encoding="utf-8")
    assert card.startswith("---\n")
    assert "sdk: gradio" in card
    assert "suggested_hardware: zero-a10g" in card
    assert "python_version: 3.12" in card
    assert "torch==2.9.1" in deps
    assert "bitsandbytes==0.48.2" in deps
    assert "gradio==5.49.1" in deps
    assert "Qwen2.5-7B" not in card


def test_space_builder_copies_canonical_code_exactly(tmp_path: Path):
    build = _script(BUILD, "layer_g_free_builder")
    sha = "a" * 40
    output = tmp_path / "bundle"
    manifest = build.build_space(output, source_sha=sha)
    assert manifest["research_claim"] == "none"
    assert manifest["source_git_sha"] == sha
    assert manifest["status"] == "unexecuted_zero_gpu_space_bundle"
    assert "hf_token" not in json.dumps(manifest).lower()
    assert set(path.name for path in output.iterdir()) == {
        "README.md", "requirements.txt", "app.py", "LICENSE",
        "layer_g_capture", "source_manifest.json",
    }
    for name in build.COPY_MODULES:
        actual = output / "layer_g_capture" / name
        expected = build.CANONICAL / name
        assert actual.read_bytes() == expected.read_bytes()
        compile(actual.read_text(encoding="utf-8"), str(actual), "exec")
    compile((output / "app.py").read_text(encoding="utf-8"), "app.py", "exec")
    with pytest.raises(FileExistsError):
        build.build_space(output, source_sha=sha)


def test_deployer_rejects_missing_token_and_nonzero_hardware():
    deploy = _script(DEPLOY, "layer_g_free_deployer")
    assert deploy.FREE_HARDWARE == "zero-a10g"
    assert deploy.TARGET == "EAImodelserie5/shadowseed-layerg-zero"
    with pytest.raises(RuntimeError, match="HF_TOKEN missing"):
        deploy.publish_space(token="", source_sha="a" * 40)
    source = DEPLOY.read_text(encoding="utf-8")
    assert "space_hardware=FREE_HARDWARE" in source
    assert "hardware != FREE_HARDWARE" in source
    assert "Token owner does not match" in source
    assert "api.upload_folder(" in source
    assert "api.add_space_secret" not in source
    assert "api.request_space_hardware" not in source
    assert "paid" in source.lower()


def test_deployment_is_secret_gated_and_actions_pinned():
    action = WORKFLOW.read_text(encoding="utf-8")
    assert "secrets.HF_TOKEN" in action
    assert 'if [ -z "$HF_TOKEN" ]; then' in action
    assert "NOT_DEPLOYED" in action
    assert "hf_jobs" not in action.lower()
    assert "deploy_layer_g_zerogpu_space.py" in action
    assert "workflow_dispatch:" in action
    for line in action.splitlines():
        if "uses:" in line:
            assert line.split("@")[-1].split()[0].strip().isalnum()
            assert len(line.split("@")[-1].split()[0]) == 40

"""Static regression guards for the zero-payment Layer G 14B notebook.

GPU execution cannot be asserted by GitHub Actions; a pass is not neural evidence.
"""
from __future__ import annotations

import json
from pathlib import Path


NOTEBOOK = Path("research/notebooks/layer_g_14b_free_gpu.ipynb")


def test_free_gpu_notebook_has_valid_structure_and_compilable_python():
    notebook = json.loads(NOTEBOOK.read_text(encoding="utf-8"))
    assert notebook["nbformat"] == 4
    assert notebook["nbformat_minor"] >= 5
    codes = [cell["source"] for cell in notebook["cells"] if cell["cell_type"] == "code"]
    assert len(codes) == 4
    for index, code in enumerate(codes):
        assert isinstance(code, str)
        compile(code, f"free14b-cell-{index}", "exec")


def test_no_paid_gpu_no_smaller_model_or_fabricated_result():
    notebook = json.loads(NOTEBOOK.read_text(encoding="utf-8"))
    codes = "\n".join(cell["source"] for cell in notebook["cells"] if cell["cell_type"] == "code")
    assert codes.index("torch.cuda.is_available()") < codes.index("pip\", \"install")
    assert codes.index("gpu.total_memory") < codes.index("AutoModelForCausalLM.from_pretrained")
    assert codes.index("len(model_sha) == 40") < codes.index("AutoModelForCausalLM.from_pretrained")
    assert "Qwen/Qwen2.5-14B-Instruct" in codes
    assert "load_in_4bit=True" in codes and "bnb_4bit_quant_type='nf4'" in codes
    assert "device_map={'':0}" in codes
    assert "HFOriginalGenerationReader" in codes
    assert "research_claim':'none'" in codes
    assert "free_gpu_only; no billing calls" in codes
    assert "CUDA_VISIBLE_DEVICES" in codes
    assert "huggingface_hub" in codes
    for unwanted in ("Qwen2.5-7B-Instruct", "0.5b-instruct", "hf_jobs", "runpod", "openai.ChatCompletion"):
        assert unwanted not in codes

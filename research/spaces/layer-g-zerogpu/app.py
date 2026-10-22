"""Mobile Gradio ZeroGPU UI for a *synthetic* Layer G 14B capture pilot.

ZeroGPU GPU memory is only assigned inside the decorated event handler. No
user input, hosted inference keys, SSL authority, or generated candidate labels.
"""
from __future__ import annotations

# Import before torch: ZeroGPU installs CUDA emulation at module scope.
import os
os.environ.setdefault("GRADIO_ANALYTICS_ENABLED", "False")
import spaces

import hashlib
import importlib.metadata
import json
from datetime import datetime, timezone
from pathlib import Path
import re
import tempfile
import zipfile

import gradio as gr
import torch
from huggingface_hub import model_info
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig
from layer_g_capture.layer_g_live_generation import (
    GenerationRequest, HFOriginalGenerationReader, write_generation_observation,
)

MODEL_ID = "Qwen/Qwen2.5-14B-Instruct"
LAYERS = ("model.layers.12.mlp.down_proj", "model.layers.36.mlp.down_proj")
TOKEN_LIMIT = 16
QUESTION = (
    "A fictional laboratory report observed a small temperature difference "
    "between two sealed boxes in separate rooms, but contains no sensor "
    "calibration data or measurements of airflow. Summarize what the fictional "
    "report establishes and what remains unresolved. Do not invent evidence."
)
QUANTIZATION = "NF4 4-bit, double quant, bfloat16 compute"
SOURCE = json.loads(
    (Path(__file__).parent / "source_manifest.json").read_text(encoding="utf-8")
)
assert SOURCE["research_claim"] == "none"
assert SOURCE["capture_path"] == "original-generation-before-seed"

model = None
tokenizer = None
model_revision = None
loading_error = None

# Required at module level for ZeroGPU's packing step.
try:
    model_revision = model_info(MODEL_ID).sha
    if not re.fullmatch(r"[0-9a-f]{40}", model_revision or ""):
        raise RuntimeError("No immutable model revision from Hub")
    tokenizer = AutoTokenizer.from_pretrained(
        MODEL_ID, revision=model_revision, trust_remote_code=False
    )
    bnb = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_use_double_quant=True,
        bnb_4bit_compute_dtype=torch.bfloat16,
    )
    model = AutoModelForCausalLM.from_pretrained(
        MODEL_ID,
        revision=model_revision,
        quantization_config=bnb,
        device_map="cuda",
        dtype=torch.bfloat16,
        low_cpu_mem_usage=True,
        trust_remote_code=False,
    ).eval()
    if not getattr(model, "is_loaded_in_4bit", False):
        raise RuntimeError("Model was not loaded in NF4")
except Exception as error:
    # Keep the mobile UI usable and show the actual start error, not a success.
    loading_error = f"{type(error).__name__}: {str(error)[:280]}"
    model = None


def versions() -> dict[str, str]:
    values = {}
    for name in ("torch", "transformers", "bitsandbytes", "accelerate",
                 "gradio", "spaces", "numpy", "huggingface_hub"):
        try:
            values[name] = importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError:
            values[name] = "unavailable"
    values["source_git_sha"] = SOURCE["source_git_sha"]
    values["quantization"] = QUANTIZATION
    values["free_gpu_size"] = "large"
    return values


@spaces.GPU(duration=90)
def run_pilot() -> tuple[str, str | None]:
    """Gradio binds directly to this decorated function."""
    if loading_error or model is None or tokenizer is None or not model_revision:
        return ("**Geen meting.** Laden van 14B is mislukt: "
                + (loading_error or "model unavailable"), None)
    try:
        if not torch.cuda.is_available():
            raise RuntimeError("ZeroGPU has not allocated a GPU")
        original = tokenizer.apply_chat_template(
            [{"role": "user", "content": QUESTION}],
            tokenize=False,
            add_generation_prompt=True,
        )
        reader = HFOriginalGenerationReader(
            model, tokenizer,
            model_id=MODEL_ID, model_revision=model_revision,
            layers=LAYERS, max_input_tokens=1024, max_new_tokens=TOKEN_LIMIT,
        )
        observation = reader.capture(
            GenerationRequest.from_original_prompt(original)
        )
        temporary = Path(tempfile.mkdtemp(prefix="shadowseed_zerogpu_"))
        directory = temporary / "capture"
        manifest = write_generation_observation(
            observation, directory, runtime=versions()
        )
        additional = {
            "model_revision": model_revision,
            "source_sha": SOURCE["source_git_sha"],
            "quantization": QUANTIZATION,
            "research_claim": "none",
            "independent_label_count": 0,
            "utc": datetime.now(timezone.utc).isoformat(),
            "caveat": "Next-token decision-prefix activation; NOT hidden truth",
        }
        (directory / "space_provenance.json").write_text(
            json.dumps(additional, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        zip_file = temporary / "shadowseed-layerg-14b.zip"
        with zipfile.ZipFile(zip_file, "w", zipfile.ZIP_DEFLATED) as archive:
            for path in sorted(directory.iterdir()):
                archive.write(path, path.name)
        digest = hashlib.sha256(zip_file.read_bytes()).hexdigest()
        if len(manifest["forward_token_counts"]) != len(observation.token_ids):
            raise RuntimeError("Decision/token count mismatch")
        return (
            "### Activaties technisch vastgelegd\n\n"
            + "**Model:** Qwen2.5-14B-Instruct (NF4)\n\n"
            + "**Modelrevisie:** " + model_revision[:12] + "\n\n"
            + "**Gegenereerde tokens:** " + str(len(observation.token_ids)) + "\n\n"
            + "**Meetlagen:** " + ", ".join(LAYERS) + "\n\n"
            + "**ZIP SHA-256:** " + digest + "\n\n"
            + "**Bewijsstatus:** alleen technische proef. Geen bewezen "
            + "interne kennisrepresentatie of SSL-voordeel.",
            str(zip_file),
        )
    except Exception as error:
        return (
            "**Geen geldige meting.** "
            + type(error).__name__ + ": " + str(error)[:280]
            + ". Hieruit volgt geen conclusie over SSL.",
            None,
        )


with gr.Blocks(title="Shadowseed | Layer G | ZeroGPU") as demo:
    gr.Markdown(
        "# Shadowseed: 14B-activatiemeting\n\n"
        "Eén fictieve proef met een open model. Activaties worden geregistreerd "
        "tijdens het oorspronkelijke antwoord, zonder kandidaat of label in "
        "de modelinvoer.\n\n"
        "**Gratis ZeroGPU** met een dagquotum. Geen OpenAI-key of betaalde GPU."
    )
    start = gr.Button("Start de 14B-proef", variant="primary", size="lg")
    result = gr.Markdown("Nog geen echte meting uitgevoerd.")
    artifact = gr.File(label="Controleerbaar ZIP-bestand (fictieve data)")
    gr.Markdown(
        "Dit meet next-token-beslissingsactivaties, niet wat het model "
        "wel of niet weet. NF4 4-bit is geen full-precision replicatie.\n\n"
        "[Onderzoek en broncode](https://github.com/E-AI-MODEL/shadowseed-pro/issues/203)"
    )
    start.click(fn=run_pilot, inputs=[], outputs=[result, artifact])

demo.queue(default_concurrency_limit=1)

if __name__ == "__main__":
    demo.launch(ssr_mode=False)

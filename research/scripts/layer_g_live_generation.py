#!/usr/bin/env python3
"""Opt-in Layer G P2 generation-time capture; NEVER an efficacy experiment.

Example on an explicitly provisioned >=40GB GPU:
  python research/scripts/layer_g_live_generation.py \
    --model-id Qwen/Qwen2.5-14B-Instruct \
    --model-revision <exact-40-char-hf-commit> \
    --prompt-file /path/to/public-synthetic-prompt.txt \
    --read-layers model.layers.12.mlp.down_proj,model.layers.36.mlp.down_proj \
    --output-dir /private/results/case-001 --max-new-tokens 80

Reproducibility: pin torch/transformers versions in the external environment.
"""

from __future__ import annotations

import argparse
import importlib.metadata
import json
from pathlib import Path
import re
import sys

from shadowseed_research.benchmark.layer_g_live_generation import (
    GenerationRequest, HFOriginalGenerationReader,
    write_generation_observation,
)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model-id", required=True)
    parser.add_argument("--model-revision", required=True)
    parser.add_argument("--prompt-file", required=True, type=Path)
    parser.add_argument("--read-layers", required=True)
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument("--max-new-tokens", type=int, default=80)
    parser.add_argument("--min-gpu-gb", type=float, default=40.0)
    args = parser.parse_args()
    if not re.fullmatch(r"[a-f0-9]{40}", args.model_revision):
        parser.error("--model-revision requires a pinned 40-character commit SHA")
    if not 1 <= args.max_new_tokens <= 128:
        parser.error("--max-new-tokens must be between 1 and 128")
    if args.min_gpu_gb < 40:
        parser.error("P2 trial requires at least 40 GB GPU memory by design")
    if args.output_dir.exists():
        parser.error("output directory exists; never overwrite prior evidence")
    original = args.prompt_file.read_text(encoding="utf-8")
    if len(original) > 12_000:
        parser.error("original source text too long for a bounded pilot")
    if "synthetic" not in args.prompt_file.name.lower():
        parser.error("P2 pilot only accepts an explicitly named synthetic prompt file")
    # Refuse expensive model downloads without a suitable visible GPU.
    import torch

    if not torch.cuda.is_available():
        parser.error("No CUDA GPU. Never substitute a small CPU model as SSL evidence.")
    gpu = torch.cuda.get_device_properties(0)
    gb = gpu.total_memory / (1024 ** 3)
    if gb < args.min_gpu_gb:
        parser.error(f"GPU has {gb:.1f} GiB; need >= {args.min_gpu_gb:.1f} GiB")
    if torch.cuda.device_count() != 1:
        parser.error("single-device GPU capture only; sharding is not yet validated")

    from transformers import AutoModelForCausalLM, AutoTokenizer

    tokenizer = AutoTokenizer.from_pretrained(
        args.model_id, revision=args.model_revision, trust_remote_code=False,
    )
    prompt = tokenizer.apply_chat_template(
        [{"role": "user", "content": original}], tokenize=False,
        add_generation_prompt=True,
    )
    request = GenerationRequest.from_original_prompt(prompt)
    model = AutoModelForCausalLM.from_pretrained(
        args.model_id, revision=args.model_revision,
        torch_dtype=torch.bfloat16, trust_remote_code=False,
    ).to("cuda").eval()
    reader = HFOriginalGenerationReader(
        model, tokenizer, model_id=args.model_id,
        model_revision=args.model_revision,
        layers=tuple(x.strip() for x in args.read_layers.split(",")),
        max_new_tokens=args.max_new_tokens,
    )
    record = reader.capture(request)
    manifest = write_generation_observation(
        record, args.output_dir,
        runtime={
            "torch": torch.__version__,
            "transformers": importlib.metadata.version("transformers"),
            "tokenizers": importlib.metadata.version("tokenizers"),
            "numpy": importlib.metadata.version("numpy"),
            "python": sys.version.split()[0],
            "cuda_gpu": gpu.name,
            "gpu_memory_gib": f"{gb:.2f}",
        },
    )
    print(json.dumps({
        "status": manifest["status"],
        "research_claim": manifest["research_claim"],
        "capture_mode": manifest["capture_mode"],
        "model_id": manifest["model_id"],
        "model_revision": manifest["model_revision"],
        "generated_tokens": manifest["generated_token_count"],
        "output_dir": str(args.output_dir),
    }, indent=2))


if __name__ == "__main__":
    main()

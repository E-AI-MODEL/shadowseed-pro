"""P2 original-generation observation: model decision activations, not seed truth.

The original prompt is the only epistemic input. The reader captures the input
to selected MLP down-projections at the decision positions while a causal LM
actually generates its first answer. It never consumes proposed candidates,
human labels, SSL state, recurrence, or Gate verdicts.

Generation-time **decision context** is not the final generated token's
activation: for token y[t], the captured forward activation comes from the
preceding prefix ending at t-1. Treating this as y[t]'s own activation would
silently shift the measurement. This is an instrument, not a decoder of
"what an LLM doesn't know".
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
import re
from typing import Any

import numpy as np

from .layer_g_vnext import sha256_text

_LAYER_PATTERN = re.compile(r"^model\.layers\.(\d+)\.mlp\.down_proj$")
_UNTRUSTED_REVIEW_MARKERS = (
    "EVAL_CANDIDATE:", "GOLD_LABEL:", "SHADOWSEED_TARGET:",
    "PROBE_CLASS:", "<CANDIDATE_TEXT>", "<LABEL_FOR_PROBE>",
)
_REVISION = re.compile(r"^[a-f0-9]{40}$")


@dataclass(frozen=True)
class GenerationRequest:
    original_prompt: str
    prompt_sha256: str

    @classmethod
    def from_original_prompt(cls, original_prompt: str) -> "GenerationRequest":
        return cls(original_prompt, sha256_text(original_prompt))

    def __post_init__(self) -> None:
        if not self.original_prompt.strip():
            raise ValueError("original-generation prompt cannot be empty")
        if sha256_text(self.original_prompt) != self.prompt_sha256:
            raise ValueError("original-generation prompt hash mismatch")
        if any(
            marker.casefold() in self.original_prompt.casefold()
            for marker in _UNTRUSTED_REVIEW_MARKERS
        ):
            raise ValueError("candidate or reviewer-label marker in original prompt")


def sorted_read_layers(layers: tuple[str, ...]) -> tuple[str, ...]:
    if not layers or len(set(layers)) != len(layers):
        raise ValueError("select distinct down-projection read layers")
    matched = [_LAYER_PATTERN.fullmatch(layer) for layer in layers]
    if any(match is None for match in matched):
        raise ValueError("unsupported read layer: expected model.layers.N.mlp.down_proj")
    return tuple(sorted(layers, key=lambda name: int(_LAYER_PATTERN.fullmatch(name)[1])))


class DecisionCaptureLedger:
    """Fail-closed verifier for ordered per-forward features during generation.

    The first forward pass covers the prompt; each later cached decode
    forward sees one input token. Each pass must invoke every selected layer
    exactly once, in the model's forward order. No raw candidate is attached.
    """

    def __init__(self, layers: tuple[str, ...]) -> None:
        self.layers = sorted_read_layers(layers)
        self.values: dict[str, list[np.ndarray]] = {name: [] for name in self.layers}
        self.input_lengths: list[int] = []
        self._events = 0
        self._widths: dict[str, int] = {}

    def record(self, layer: str, features: np.ndarray, input_length: int) -> None:
        expected = self.layers[self._events % len(self.layers)]
        if layer != expected:
            raise ValueError(f"generation hook order/duplicate mismatch: {layer} != {expected}")
        if input_length < 1:
            raise ValueError("empty generation forward input")
        value = np.asarray(features, dtype=np.float32)
        if value.ndim != 1 or value.size == 0 or not np.isfinite(value).all():
            raise ValueError("nonfinite or non-vector model activations")
        if layer in self._widths and self._widths[layer] != value.size:
            raise ValueError("MLP feature width changed during generation")
        self._widths[layer] = int(value.size)
        if self._events % len(self.layers) == 0:
            self.input_lengths.append(int(input_length))
        elif self.input_lengths[-1] != input_length:
            raise ValueError("selected layers saw different forward-token counts")
        self.values[layer].append(value.copy())
        self._events += 1

    def finish(
        self, *, input_token_count: int, generated_token_ids: list[int],
    ) -> tuple[dict[str, np.ndarray], list[int]]:
        generated_len = len(generated_token_ids)
        if not (generated_len and self._events == generated_len * len(self.layers)):
            raise ValueError(
                "generation-step/MLP-hook count mismatch; cannot align decision positions"
            )
        if self.input_lengths != [input_token_count] + [1] * (generated_len - 1):
            raise ValueError(
                "non-cached/irregular forward sequence; decision positions not aligned"
            )
        features = {
            layer: np.stack(self.values[layer]).astype(np.float32)
            for layer in self.layers
        }
        for layer, matrix in features.items():
            if matrix.ndim != 2 or matrix.shape[0] != generated_len:
                raise ValueError(f"invalid aligned matrix: {layer}")
        return features, list(self.input_lengths)


@dataclass
class GenerationObservation:
    """Answer and aligned decision-position arrays before candidate generation."""

    generated_answer: str
    token_ids: list[int]
    layer_features: dict[str, np.ndarray]
    forward_lengths: list[int]
    prompt_sha256: str
    prompt_tokens: int
    model_revision: str
    model_id: str
    read_layers: tuple[str, ...]
    decoding: dict[str, Any]


class HFOriginalGenerationReader:
    """Capture real generation, NOT a teacher-forced replay.

    Externally loaded, pinned Hugging Face model/tokenizer required. This
    class is intentionally independent of the SSL engine and never calls a
    detector. The prompt must already contain the chosen chat template.
    """

    def __init__(
        self, model: Any, tokenizer: Any, *,
        model_id: str, model_revision: str, layers: tuple[str, ...],
        max_input_tokens: int = 2048, max_new_tokens: int = 96,
    ) -> None:
        if not model_id.strip() or not _REVISION.fullmatch(model_revision):
            raise ValueError("model ID and immutable 40-hex model revision required")
        if not (8 <= max_input_tokens <= 4096):
            raise ValueError("max_input_tokens must be 8..4096")
        if not (1 <= max_new_tokens <= 128):
            raise ValueError("max_new_tokens must be 1..128")
        if getattr(model, "training", True):
            raise ValueError("model must be in eval mode")
        if getattr(getattr(model, "config", None), "is_encoder_decoder", True):
            raise ValueError("only causal decoder-only models supported")
        self.model = model
        self.tokenizer = tokenizer
        self.model_id = model_id
        self.model_revision = model_revision
        self.layers = sorted_read_layers(layers)
        self.max_input_tokens = max_input_tokens
        self.max_new_tokens = max_new_tokens

    def capture(self, request: GenerationRequest) -> GenerationObservation:
        import torch  # optional; not imported in normal research-package CI

        encoded = self.tokenizer(
            request.original_prompt, return_tensors="pt",
            truncation=False, add_special_tokens=False,
        )
        input_ids = encoded["input_ids"]
        if len(input_ids.shape) != 2 or input_ids.shape[0] != 1:
            raise ValueError("generation capture supports exactly one prompt")
        n_input = int(input_ids.shape[1])
        if n_input < 1 or n_input > self.max_input_tokens:
            raise ValueError("input token limit exceeded (no silent truncation)")
        masks = encoded.get("attention_mask")
        if masks is not None and (masks.shape != input_ids.shape or not bool(masks.all())):
            raise ValueError("padding/masked input not supported for aligned capture")

        modules = dict(self.model.named_modules())
        if any(name not in modules for name in self.layers):
            raise ValueError("selected down-projection module missing")
        if getattr(self.model, "training", True):
            raise ValueError("model must remain in eval mode")
        device = self.model.device
        inputs = {
            name: value.to(device) if hasattr(value, "to") else value
            for name, value in encoded.items()
        }
        ledger = DecisionCaptureLedger(self.layers)
        handles: list[Any] = []

        def make_hook(name: str):
            def observe(_module: Any, args: tuple[Any, ...]) -> None:
                value = args[0]
                if value.ndim != 3 or int(value.shape[0]) != 1:
                    raise ValueError("unexpected MLP tensor rank or batch size")
                # Last INPUT token's activation predicts the NEXT OUTPUT token.
                vector = value[:, -1, :].detach().to(torch.float32).cpu().numpy()[0]
                ledger.record(name, vector, int(value.shape[1]))
            return observe

        pad_id = getattr(self.tokenizer, "pad_token_id", None)
        if pad_id is None:
            pad_id = getattr(self.tokenizer, "eos_token_id", None)
        if pad_id is None:
            raise ValueError("tokenizer needs a known pad/eos id")
        try:
            for name in self.layers:
                handles.append(modules[name].register_forward_pre_hook(make_hook(name)))
            with torch.inference_mode():
                output = self.model.generate(
                    **inputs,
                    max_new_tokens=self.max_new_tokens,
                    do_sample=False,
                    num_beams=1,
                    num_return_sequences=1,
                    use_cache=True,
                    return_dict_in_generate=True,
                    output_scores=False,
                    pad_token_id=int(pad_id),
                )
        finally:
            for handle in handles:
                handle.remove()

        sequences = output.sequences
        if len(sequences.shape) != 2 or sequences.shape[0] != 1:
            raise ValueError("generation produced an unexpected number of sequences")
        produced = [int(token) for token in sequences[0, n_input:].tolist()]
        if not 1 <= len(produced) <= self.max_new_tokens:
            raise ValueError("generated token count outside configured bounds")
        if [int(token) for token in sequences[0, :n_input].tolist()] != [
            int(token) for token in input_ids[0].tolist()
        ]:
            raise ValueError("generated sequence does not preserve original input")
        features, forward_lengths = ledger.finish(
            input_token_count=n_input, generated_token_ids=produced,
        )
        answer = self.tokenizer.decode(
            produced, skip_special_tokens=True, clean_up_tokenization_spaces=False,
        )
        return GenerationObservation(
            generated_answer=answer, token_ids=produced,
            layer_features=features, forward_lengths=forward_lengths,
            prompt_sha256=request.prompt_sha256, prompt_tokens=n_input,
            model_revision=self.model_revision, model_id=self.model_id,
            read_layers=self.layers,
            decoding={
                "mode": "greedy", "do_sample": False,
                "num_beams": 1, "use_cache": True,
                "max_new_tokens": self.max_new_tokens,
            },
        )


def write_generation_observation(
    observation: GenerationObservation, output_dir: Path,
    *, runtime: dict[str, str],
) -> dict[str, Any]:
    """Persist raw per-step activations separately from original prompt text.

    The output directory must not already exist, preventing silent overwrites.
    Even though only hashes of original inputs are written, the generated
    answer may contain sensitive content: do not upload real-user runs.
    """
    if not runtime.get("torch") or not runtime.get("transformers"):
        raise ValueError("runtime package version provenance required")
    if len(observation.token_ids) != len(observation.forward_lengths):
        raise ValueError("observation token/forward mismatch")
    for layer in observation.read_layers:
        arr = observation.layer_features.get(layer)
        if (
            arr is None or arr.ndim != 2
            or arr.shape[0] != len(observation.token_ids)
            or not np.isfinite(arr).all()
        ):
            raise ValueError(f"invalid serialized feature matrix for {layer}")
    output_dir.mkdir(parents=True, exist_ok=False)
    array_path = output_dir / "decision_activations.npz"
    np.savez_compressed(
        array_path,
        **{name: observation.layer_features[name] for name in observation.read_layers},
    )
    answer_path = output_dir / "original_answer.json"
    answer = {
        "generated_answer": observation.generated_answer,
        "generated_token_ids": observation.token_ids,
    }
    answer_path.write_text(
        json.dumps(answer, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )
    sha = lambda path: hashlib.sha256(path.read_bytes()).hexdigest()
    manifest = {
        "artifact": "layer_g_vnext_generation_capture",
        "status": "unlabelled_mechanistic_pilot",
        "research_claim": "none",
        "read_location": "mlp_down_proj_input_at_next_token_decision",
        "capture_mode": "synchronous_original_generation",
        "original_prompt_sha256": observation.prompt_sha256,
        "original_prompt_token_count": observation.prompt_tokens,
        "original_prompt_stored": False,
        "generated_token_count": len(observation.token_ids),
        "answer_sha256": sha(answer_path),
        "features_sha256": sha(array_path),
        "forward_token_counts": observation.forward_lengths,
        "layers": {
            layer: {
                "shape": list(observation.layer_features[layer].shape),
                "dtype": str(observation.layer_features[layer].dtype),
                "sha256": hashlib.sha256(
                    observation.layer_features[layer].tobytes(order="C")
                ).hexdigest(),
            }
            for layer in observation.read_layers
        },
        "model_id": observation.model_id,
        "model_revision": observation.model_revision,
        "decoding": observation.decoding,
        "runtime": dict(runtime),
        "warning": (
            "Features observe decoder decision-prefix activations, not latent "
            "truth, missing knowledge or generated-token self-activations. "
            "No candidates or independent quality labels were measured."
        ),
    }
    (output_dir / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )
    return manifest

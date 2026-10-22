"""Layer G vNext P1: leakage-aware, synthetic-only activation preflight.

This is NOT an H-Neurons replication or an estimator of hidden ignorance.
The original answer stimulus is separated from independently annotated
candidate metadata. Actual model activations require a separate, pinned
open-weight pilot and preregistration.

Never import or mutate SSL seed, trace, weight, recurrence or Gate state.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
import re
from typing import Any, Protocol

import numpy as np

CASE_LABELS = frozenset({
    "unspoken_coherent", "already_expressed", "unsupported_alternative",
    "undetermined",
})
SPLITS = frozenset({"discovery", "validation", "test"})
_ANSWER_MARKER = "\n\n<ORIGINAL_ANSWER>\n"
_LEAK_MARKERS = (
    "SHADOWSEED_TARGET:", "EVAL_CANDIDATE:", "PROBE_CLASS:",
    "GOLD_LABEL:", "<CANDIDATE_TEXT>", "<LABEL_FOR_PROBE>",
)


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _normalized(value: str) -> str:
    return " ".join(re.findall(r"[^\W_]+", value.casefold(), flags=re.UNICODE))


@dataclass(frozen=True)
class Case:
    case_id: str
    source_id: str
    topic_id: str
    split: str
    language: str
    original_prompt: str
    original_answer: str
    candidate_text: str
    label: str

    @classmethod
    def from_dict(cls, value: dict[str, Any]) -> "Case":
        expected = set(cls.__dataclass_fields__)
        if set(value) != expected:
            raise ValueError(
                "case fields must match frozen P1 schema; missing/extra fields: "
                + repr(sorted(set(value) ^ expected))
            )
        if any(not isinstance(v, str) or not v.strip() for v in value.values()):
            raise ValueError("all case fields must be nonempty strings")
        case = cls(**value)
        if case.split not in SPLITS:
            raise ValueError(f"unknown split for {case.case_id}")
        if case.label not in CASE_LABELS:
            raise ValueError(f"unknown label for {case.case_id}")
        if case.language not in ("nl", "en"):
            raise ValueError(f"unsupported language for {case.case_id}")
        return case


@dataclass(frozen=True)
class CaptureRequest:
    """Only original generated material may cross the capture boundary."""

    stimulus: str
    answer_start: int
    answer_end: int
    stimulus_sha256: str

    def __post_init__(self) -> None:
        if not (0 <= self.answer_start < self.answer_end <= len(self.stimulus)):
            raise ValueError("invalid original-answer span")
        if sha256_text(self.stimulus) != self.stimulus_sha256:
            raise ValueError("stimulus digest mismatch")


def original_capture_request(case: Case) -> CaptureRequest:
    """Deliberately never references case.candidate_text or case.label."""
    stimulus = case.original_prompt + _ANSWER_MARKER + case.original_answer
    if any(marker.casefold() in stimulus.casefold() for marker in _LEAK_MARKERS):
        raise ValueError("explicit evaluation/candidate marker in original stimulus")
    if case.label == "unspoken_coherent":
        possible = _normalized(case.candidate_text)
        if len(possible) >= 20 and possible in _normalized(stimulus):
            raise ValueError(
                "positive unspoken candidate appears verbatim in original stimulus; "
                "semantic paraphrase checks still require independent review"
            )
    start = len(case.original_prompt) + len(_ANSWER_MARKER)
    return CaptureRequest(stimulus, start, len(stimulus), sha256_text(stimulus))


def validate_cases(cases: list[Case]) -> None:
    if not cases:
        raise ValueError("empty case set")
    ids: set[str] = set()
    stimuli: set[str] = set()
    by_source: dict[str, str] = {}
    by_topic: dict[str, str] = {}
    for case in cases:
        if case.case_id in ids:
            raise ValueError("duplicate case_id")
        ids.add(case.case_id)
        request = original_capture_request(case)
        if request.stimulus_sha256 in stimuli:
            raise ValueError(
                "identical original context assigned to multiple candidates; "
                "candidate-specific hidden signals cannot be distinguished"
            )
        stimuli.add(request.stimulus_sha256)
        for kind, group, registry in (
            ("source", case.source_id, by_source),
            ("topic", case.topic_id, by_topic),
        ):
            if group in registry and registry[group] != case.split:
                raise ValueError(f"{kind} leaks across splits: {group}")
            registry[group] = case.split
    if not {"discovery", "validation", "test"} <= {c.split for c in cases}:
        raise ValueError("discovery, validation and test must be distinct")
    # Not a statistical minimum or proof of a suitable sampling frame.
    if len({c.source_id for c in cases}) < 3:
        raise ValueError("too few independent source groups even for a preflight")


def load_frozen_fixture(path: Path) -> tuple[list[Case], str]:
    raw = path.read_bytes()
    document = json.loads(raw)
    if document.get("version") != "layer-g-vnext-p1-v1":
        raise ValueError("unknown fixture version")
    if document.get("status") != "synthetic_preflight_only":
        raise ValueError("this runner cannot use real annotated data")
    cases = [Case.from_dict(obj) for obj in document["cases"]]
    validate_cases(cases)
    return cases, hashlib.sha256(raw).hexdigest()


class ActivationReader(Protocol):
    """The backend sees only the original stimulus; never a candidate/label."""

    def capture(self, request: CaptureRequest) -> dict[str, np.ndarray]: ...


class SyntheticReader:
    """Label-blind hash-based vectors for mechanical CI, not neural evidence."""

    def __init__(self, dim: int = 16) -> None:
        if dim < 2:
            raise ValueError("dim must be >=2")
        self.dim = dim

    def capture(self, request: CaptureRequest) -> dict[str, np.ndarray]:
        seed = int(request.stimulus_sha256[:16], 16)
        rng = np.random.default_rng(seed)
        return {"synthetic.mlp.0": rng.normal(size=self.dim)}


def validate_activation_vectors(
    vectors: dict[str, np.ndarray], *, expected_shapes: dict[str, tuple[int, ...]] | None = None,
) -> dict[str, tuple[int, ...]]:
    if not vectors:
        raise ValueError("no activation layers captured")
    shapes: dict[str, tuple[int, ...]] = {}
    for name, raw in vectors.items():
        if not isinstance(name, str) or not name.strip():
            raise ValueError("invalid activation layer name")
        arr = np.asarray(raw)
        if arr.ndim != 1 or arr.size == 0 or not np.issubdtype(arr.dtype, np.number):
            raise ValueError(f"invalid feature shape at {name}")
        if not np.isfinite(arr).all():
            raise ValueError(f"nonfinite features at {name}")
        shapes[name] = tuple(arr.shape)
    if expected_shapes is not None and shapes != expected_shapes:
        raise ValueError("layer names/activation shapes changed across cases")
    return shapes


def answer_token_positions(
    offsets: list[tuple[int, int]], start: int, end: int,
) -> list[int]:
    """Fail closed if original-answer tokens were omitted or truncated."""
    if not (0 <= start < end):
        raise ValueError("bad answer span")
    indices = [i for i, (s, e) in enumerate(offsets) if e > s and s < end and e > start]
    if not indices:
        raise ValueError("answer span absent from tokenized input")
    covered_start = min(offsets[i][0] for i in indices)
    covered_end = max(offsets[i][1] for i in indices)
    if covered_start > start or covered_end < end:
        raise ValueError("tokenization/truncation did not fully cover original answer")
    return indices


class HFAnswerReplayReader:
    """Opt-in teacher-forced answer replay; *not* original-generation capture.

    Requires an externally pinned, loaded torch model and fast tokenizer.
    P1 exercises token-span logic without downloading model weights. A future
    P2 pilot must report revision, dtype, device, torch/transformers versions,
    and distinguish replay from synchronous generation-time observation.
    """

    def __init__(
        self, model: Any, tokenizer: Any, *,
        layers: tuple[str, ...], max_tokens: int = 1024,
    ) -> None:
        if not layers or len(set(layers)) != len(layers):
            raise ValueError("one or more unique MLP down-projection layers required")
        if not all(name.endswith(".mlp.down_proj") for name in layers):
            raise ValueError("read location must be Qwen/Llama MLP down-projection input")
        if not getattr(tokenizer, "is_fast", False):
            raise ValueError("tokenizer must provide reliable offset mapping")
        if max_tokens < 1:
            raise ValueError("invalid maximum token count")
        self.model, self.tokenizer, self.layers, self.max_tokens = (
            model, tokenizer, layers, max_tokens,
        )

    def capture(self, request: CaptureRequest) -> dict[str, np.ndarray]:
        import torch  # optional model extra; no torch import on synthetic CI

        encoded = self.tokenizer(
            request.stimulus, return_tensors="pt",
            return_offsets_mapping=True, truncation=False,
        )
        offsets = [tuple(map(int, pair)) for pair in encoded.pop("offset_mapping")[0].tolist()]
        if len(offsets) > self.max_tokens:
            raise ValueError("original stimulus exceeds max_tokens; no silent truncation")
        positions = answer_token_positions(
            offsets, request.answer_start, request.answer_end,
        )
        modules = dict(self.model.named_modules())
        if any(name not in modules for name in self.layers):
            raise ValueError("specified MLP layer absent in pinned model")
        if self.model.training:
            raise ValueError("model must be in eval() mode for activation capture")
        captured: dict[str, np.ndarray] = {}
        handles = []

        def capture_hook(name: str):
            def hook(_module: Any, args: tuple[Any, ...]) -> None:
                tensor = args[0]
                if tensor.ndim != 3 or tensor.shape[0] != 1 or tensor.shape[1] != len(offsets):
                    raise ValueError("activation tensor/token alignment mismatch")
                pooled = tensor[:, positions, :].detach().to(torch.float32)
                captured[name] = pooled.mean(dim=(0, 1)).cpu().numpy().copy()
            return hook

        try:
            for name in self.layers:
                handles.append(modules[name].register_forward_pre_hook(capture_hook(name)))
            with torch.no_grad():
                self.model(**encoded)
        finally:
            for handle in handles:
                handle.remove()
        validate_activation_vectors(captured)
        return captured


def run_synthetic_preflight(cases: list[Case], fixture_sha256: str) -> dict[str, Any]:
    validate_cases(cases)
    reader = SyntheticReader()
    expected_shapes = None
    captures: list[dict[str, Any]] = []
    for case in cases:
        request = original_capture_request(case)
        vectors = reader.capture(request)
        shapes = validate_activation_vectors(vectors, expected_shapes=expected_shapes)
        if expected_shapes is None:
            expected_shapes = shapes
        captures.append({
            "case_id": case.case_id,
            "split": case.split,
            "stimulus_sha256": request.stimulus_sha256,
            "answer_char_span": [request.answer_start, request.answer_end],
            "layer_shapes": {name: list(shape) for name, shape in shapes.items()},
            # No raw candidate, label or source-specific reviewer metadata.
        })
    return {
        "artifact": "layer_g_vnext_preflight",
        "status": "synthetic_preflight_only",
        "research_claim": "none",
        "fixture_sha256": fixture_sha256,
        "checks": {
            "capture_input_excludes_candidate_and_label_fields": True,
            "explicit_marker_guard": True,
            "source_and_topic_holdout_disjoint": True,
            "duplicate_stimuli_rejected": True,
            "activation_shapes_and_finite_values": True,
            "answer_span_validation": "unit_tested_without_real_model",
        },
        "capture_mode": "synthetic_hash_not_real_activations",
        "cases": captures,
        "limitations": (
            "No model weights loaded, no actual learned representation measured; "
            "labels and generated candidates are not ground truth for hidden knowledge."
        ),
    }


def write_preflight(fixture: Path, output: Path) -> dict[str, Any]:
    cases, digest = load_frozen_fixture(fixture)
    report = run_synthetic_preflight(cases, digest)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(report, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )
    return report

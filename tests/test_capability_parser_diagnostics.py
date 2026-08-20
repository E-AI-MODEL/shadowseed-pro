from __future__ import annotations

import sys
import types

from shadowseed.adapters.models import make_backend
from shadowseed.benchmark.capability_scaling import _parser_diagnostics_summary
from shadowseed.detection.model_detector import (
    make_detector_backend,
    parse_numbered_seeds,
    parse_numbered_seeds_with_diagnostics,
)


def test_nested_numbering_prefill_artifact_is_removed_and_counted() -> None:
    raw = "1. 1. Social mobility as an explanatory frame for industrial change."
    seeds, diagnostics = parse_numbered_seeds_with_diagnostics(raw)
    assert seeds == ["Social mobility as an explanatory frame for industrial change."]
    assert diagnostics["nested_numbering_prefixes_removed"] == 1
    assert parse_numbered_seeds(raw) == seeds


def test_fewshot_leakage_is_rejected_but_measured() -> None:
    raw = """1. Colonial capital as an explanatory frame alongside technological innovation.
2. Supply-chain concentration as a risk to the announced expansion.
"""
    seeds, diagnostics = parse_numbered_seeds_with_diagnostics(raw)
    assert seeds == ["Supply-chain concentration as a risk to the announced expansion."]
    assert diagnostics["numbered_lines"] == 2
    assert diagnostics["dropped_fewshot_leak"] == 1
    summary = _parser_diagnostics_summary(diagnostics)
    assert summary["fewshot_leakage_rate"] == 0.5
    assert summary["parser_rejection_rate"] == 0.5


def _install_fake_model_modules(monkeypatch):
    calls: list[tuple[str, str, dict]] = []
    torch = types.ModuleType("torch")
    torch.float16 = object()

    class Cuda:
        @staticmethod
        def is_available() -> bool:
            return False

    torch.cuda = Cuda()
    transformers = types.ModuleType("transformers")

    class AutoTokenizer:
        @classmethod
        def from_pretrained(cls, model_id: str, **kwargs):
            calls.append(("tokenizer", model_id, dict(kwargs)))
            return object()

    class AutoModelForCausalLM:
        @classmethod
        def from_pretrained(cls, model_id: str, **kwargs):
            calls.append(("model", model_id, dict(kwargs)))
            return object()

    def pipeline(*_args, **_kwargs):
        def generate(*_call_args, **_call_kwargs):
            return [{"generated_text": "A generated answer."}]

        return generate

    transformers.AutoTokenizer = AutoTokenizer
    transformers.AutoModelForCausalLM = AutoModelForCausalLM
    transformers.pipeline = pipeline
    monkeypatch.setitem(sys.modules, "torch", torch)
    monkeypatch.setitem(sys.modules, "transformers", transformers)
    return calls


def test_hf_runtime_revision_is_applied_to_model_and_detector(monkeypatch) -> None:
    calls = _install_fake_model_modules(monkeypatch)
    make_backend(
        "hf-transformers",
        "example/model",
        32,
        model_revision="deadbeef",
    )
    make_detector_backend(
        "hf-transformers",
        model_id="example/model",
        max_new_tokens=32,
        prompt_variant="generative",
        model_revision="deadbeef",
    )
    tokenizer_calls = [entry for entry in calls if entry[0] == "tokenizer"]
    model_calls = [entry for entry in calls if entry[0] == "model"]
    assert len(tokenizer_calls) == 2
    assert len(model_calls) == 2
    assert all(entry[2]["revision"] == "deadbeef" for entry in tokenizer_calls)
    assert all(entry[2]["revision"] == "deadbeef" for entry in model_calls)

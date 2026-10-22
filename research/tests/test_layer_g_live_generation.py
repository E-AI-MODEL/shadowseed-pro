"""P2 generation-time instrumentation tests. Fake models != neural findings."""

from __future__ import annotations

from contextlib import nullcontext
import json
from pathlib import Path
import sys
from types import SimpleNamespace

import numpy as np
import pytest

from shadowseed_research.benchmark.layer_g_live_generation import (
    DecisionCaptureLedger,
    GenerationRequest,
    HFOriginalGenerationReader,
    sorted_read_layers,
    write_generation_observation,
)


L0 = "model.layers.0.mlp.down_proj"
L2 = "model.layers.2.mlp.down_proj"
REVISION = "c" * 40


def test_request_rejects_review_labels_and_forged_hashes():
    req = GenerationRequest.from_original_prompt("What is the unknown alternative?")
    assert req.prompt_sha256
    with pytest.raises(ValueError, match="hash mismatch"):
        GenerationRequest("modified", req.prompt_sha256)
    with pytest.raises(ValueError, match="marker"):
        GenerationRequest.from_original_prompt("Given text. GOLD_LABEL: coherent")
    assert set(req.__dict__) == {"original_prompt", "prompt_sha256"}


def test_layer_names_are_sorted_and_unique():
    assert sorted_read_layers((L2, L0)) == (L0, L2)
    with pytest.raises(ValueError, match="distinct"):
        sorted_read_layers((L0, L0))
    with pytest.raises(ValueError, match="unsupported"):
        sorted_read_layers(("model.layers.0.mlp",))


def test_ledger_distinguishes_prefill_from_cached_decisions():
    ledger = DecisionCaptureLedger((L2, L0))
    for n in (6, 1, 1):
        ledger.record(L0, np.ones(4), n)
        ledger.record(L2, np.ones(7), n)
    arrays, lengths = ledger.finish(
        input_token_count=6, generated_token_ids=[15, 16, 17],
    )
    assert lengths == [6, 1, 1]
    assert arrays[L0].shape == (3, 4)
    assert arrays[L2].shape == (3, 7)


def test_ledger_rejects_hook_loss_duplicate_and_non_cached_alignment():
    ledger = DecisionCaptureLedger((L0, L2))
    ledger.record(L0, np.ones(4), 6)
    with pytest.raises(ValueError, match="order/duplicate"):
        ledger.record(L0, np.ones(4), 6)
    ledger.record(L2, np.ones(4), 6)
    ledger.record(L0, np.ones(4), 7)
    ledger.record(L2, np.ones(4), 7)
    with pytest.raises(ValueError, match="non-cached"):
        ledger.finish(input_token_count=6, generated_token_ids=[1, 2])
    with pytest.raises(ValueError, match="step/MLP-hook"):
        DecisionCaptureLedger((L0,)).finish(
            input_token_count=6, generated_token_ids=[1],
        )


def test_ledger_rejects_nonfinite_vectors_and_width_drift():
    ledger = DecisionCaptureLedger((L0,))
    with pytest.raises(ValueError, match="nonfinite"):
        ledger.record(L0, np.array([1., np.nan]), 2)
    ledger.record(L0, np.ones(3), 2)
    with pytest.raises(ValueError, match="width changed"):
        ledger.record(L0, np.ones(4), 1)


class FakeActivation:
    def __init__(self, array):
        self.array = np.asarray(array, dtype=np.float32)
        self.ndim = self.array.ndim
        self.shape = self.array.shape

    def detach(self):
        return self

    def to(self, _dtype):
        return self

    def cpu(self):
        return self

    def numpy(self):
        return self.array

    def __getitem__(self, key):
        return FakeActivation(self.array[key])


class FakeModule:
    def __init__(self):
        self.hook = None
        self.removed = False

    def register_forward_pre_hook(self, hook):
        self.hook = hook
        handle = self
        return handle

    def remove(self):
        self.removed = True
        self.hook = None


class FakeTokenizer:
    pad_token_id = None
    eos_token_id = 1

    def __call__(self, text, **_kwargs):
        return {"input_ids": np.array([[4, 5, 6, 7]]),
                "attention_mask": np.ones((1, 4), dtype=np.int64)}

    def decode(self, ids, **_kwargs):
        return "model answer " + ",".join(map(str, ids))


class FakeModel:
    training = False
    device = "cpu"
    config = SimpleNamespace(is_encoder_decoder=False)

    def __init__(self, bad_step=False):
        self.modules = {L0: FakeModule(), L2: FakeModule()}
        self.bad_step = bad_step

    def named_modules(self):
        return list(self.modules.items())

    def generate(self, **kwargs):
        input_ids = kwargs["input_ids"][0].tolist()
        assert kwargs["do_sample"] is False
        assert kwargs["use_cache"] is True
        assert kwargs["num_beams"] == 1
        for index in range(3):
            forward_len = 4 if index == 0 else 1
            if self.bad_step and index == 2:
                forward_len = 4
            for name, width in ((L0, 4), (L2, 6)):
                activation = FakeActivation(np.ones((1, forward_len, width)) * (index + 1))
                self.modules[name].hook(self.modules[name], (activation,))
        return SimpleNamespace(sequences=np.array([input_ids + [8, 9, 10]]))


def test_full_generation_hook_path_and_artifact_without_real_torch(monkeypatch, tmp_path):
    fake_torch = SimpleNamespace(inference_mode=nullcontext, float32="float32")
    monkeypatch.setitem(sys.modules, "torch", fake_torch)
    model = FakeModel()
    reader = HFOriginalGenerationReader(
        model, FakeTokenizer(), model_id="synthetic/Fake", model_revision=REVISION,
        layers=(L2, L0), max_new_tokens=3,
    )
    request = GenerationRequest.from_original_prompt("An ordinary unlabelled prompt")
    record = reader.capture(request)
    assert record.forward_lengths == [4, 1, 1]
    assert record.read_layers == (L0, L2)
    assert record.token_ids == [8, 9, 10]
    assert record.layer_features[L2].shape == (3, 6)
    assert all(module.removed for module in model.modules.values())
    manifest = write_generation_observation(
        record, tmp_path / "run1",
        runtime={"torch": "fake-only", "transformers": "fake-only"},
    )
    assert manifest["capture_mode"] == "synchronous_original_generation"
    assert manifest["research_claim"] == "none"
    assert manifest["model_revision"] == REVISION
    assert manifest["forward_token_counts"] == [4, 1, 1]
    assert "original_prompt" not in json.dumps(manifest)
    assert (tmp_path / "run1" / "decision_activations.npz").is_file()
    with np.load(tmp_path / "run1" / "decision_activations.npz") as features:
        assert features[L0].shape == (3, 4)
    with pytest.raises(FileExistsError):
        write_generation_observation(
            record, tmp_path / "run1",
            runtime={"torch": "fake-only", "transformers": "fake-only"},
        )


def test_missing_or_irregular_forward_fails_and_hooks_always_removed(monkeypatch):
    monkeypatch.setitem(
        sys.modules, "torch",
        SimpleNamespace(inference_mode=nullcontext, float32="float32"),
    )
    model = FakeModel(bad_step=True)
    reader = HFOriginalGenerationReader(
        model, FakeTokenizer(), model_id="synthetic/Fake", model_revision=REVISION,
        layers=(L0, L2), max_new_tokens=4,
    )
    with pytest.raises(ValueError, match="non-cached"):
        reader.capture(GenerationRequest.from_original_prompt("Original prompt"))
    assert all(module.removed for module in model.modules.values())


def test_live_reader_requires_immutable_sha_and_eval():
    model = FakeModel()
    with pytest.raises(ValueError, match="immutable"):
        HFOriginalGenerationReader(
            model, FakeTokenizer(), model_id="model", model_revision="main",
            layers=(L0,),
        )
    model.training = True
    with pytest.raises(ValueError, match="eval"):
        HFOriginalGenerationReader(
            model, FakeTokenizer(), model_id="model", model_revision=REVISION,
            layers=(L0,),
        )

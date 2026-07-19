"""Layer G activation probe for dialectical verdict signals.

The probe records MLP activations while processing dialectical cases and tests
whether activation vectors separate the legacy verdict classes ``WEERLEGD`` and
``HOUDT_STAND``. It includes centroid separation, exact or Monte Carlo label
permutations, and a sparse L1 logistic classifier with leave-one-out validation.

The probe never reads or changes seed state. It produces a research signal, not
a gate verdict or promotion decision. The deterministic fake backend verifies
only harness mechanics; real-model probing is optional.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import numpy as np

from shadowseed.benchmark.dialectic_falsification import (
    VERDICT_HOUDT_STAND,
    VERDICT_WEERLEGD,
    FixtureDialecticBackend,
    build_dialectic_prompt,
    parse_dialectic_verdict,
)

# -- analysekern (model-vrij, deterministisch) --------------------------------


def find_focus_span(prompt: str, focus: str) -> tuple[int, int] | None:
    """Return the focus span, anchored after the claim marker when possible.

    A quoted claim may also appear in the source text. Anchoring prevents the
    probe from pooling the earlier source copy instead of the claim itself.
    """
    if not focus:
        return None
    anchor = prompt.find("CLAIM:")
    if anchor < 0:
        anchor = prompt.find("STELLING:")  # legacy prompt compatibility
    if anchor >= 0:
        start = prompt.find(focus, anchor)
        if start >= 0:
            return start, start + len(focus)
    start = prompt.find(focus)
    if start >= 0:
        return start, start + len(focus)
    return None


def select_focus_positions(
    offsets: list[tuple[int, int]], span_start: int, span_end: int
) -> list[int]:
    """Return token positions whose character offsets overlap the focus span."""
    return [
        i
        for i, (s, e) in enumerate(offsets)
        if e > span_start and s < span_end and e > s
    ]


def class_separation(
    activations: dict[str, list[np.ndarray]],
) -> dict[str, Any]:
    """Measure per-layer separation between two class centroids.

    Candidate dimensions are ranked by absolute mean difference. They are
    candidate features, not established neurons.
    """
    labels = sorted(activations)
    if len(labels) != 2 or any(len(v) == 0 for v in activations.values()):
        return {"separable": False, "reason": "two non-empty classes required"}
    a, b = (np.mean(np.stack(activations[label]), axis=0) for label in labels)
    denom = float(np.linalg.norm(a) * np.linalg.norm(b))
    cosine = float(np.dot(a, b) / denom) if denom else 1.0
    diff = np.abs(a - b)
    top = np.argsort(diff)[::-1][:5]
    return {
        "separable": True,
        "classes": labels,
        "cosine_between_class_means": cosine,
        "cosine_distance": 1.0 - cosine,
        "candidate_dimensions": [
            {"dim": int(i), "abs_mean_diff": float(diff[i])} for i in top
        ],
        "n_per_class": {label: len(activations[label]) for label in labels},
    }


def _class_mean_distance(vectors: list[np.ndarray], labels: list[str]) -> float:
    classes = sorted(set(labels))
    a = np.mean([v for v, l in zip(vectors, labels) if l == classes[0]], axis=0)
    b = np.mean([v for v, l in zip(vectors, labels) if l == classes[1]], axis=0)
    denom = float(np.linalg.norm(a) * np.linalg.norm(b))
    return 1.0 - (float(np.dot(a, b) / denom) if denom else 1.0)


def permutation_control(
    vectors: list[np.ndarray],
    labels: list[str],
    n_permutations: int = 500,
    rng_seed: int = 45,
) -> dict[str, Any]:
    """Run a label-shuffle control for observed class separation.

    Small samples enumerate all assignments exactly. Larger samples use a
    deterministic Monte Carlo permutation test.
    """
    from itertools import combinations
    from math import comb

    classes = sorted(set(labels))
    if len(classes) != 2:
        return {"valid": False, "reason": "two classes required"}
    observed = _class_mean_distance(vectors, labels)
    n = len(labels)
    k = labels.count(classes[0])
    total = comb(n, k)
    null: list[float] = []
    if total <= 2000:
        for combo in combinations(range(n), k):
            perm = [classes[0] if i in combo else classes[1] for i in range(n)]
            null.append(_class_mean_distance(vectors, perm))
        exact = True
        p = sum(1 for d in null if d >= observed - 1e-12) / total
        # Label-swap symmetry: with balanced classes the complementary assignment
        # always ties the observed assignment, so the attainable floor is 2/total.
        # With unbalanced classes, 1/total remains attainable.
        floor = (2 if 2 * k == n else 1) / total
    else:
        rng = np.random.default_rng(rng_seed)
        shuffled = list(labels)
        for _ in range(n_permutations):
            rng.shuffle(shuffled)
            null.append(_class_mean_distance(vectors, shuffled))
        exact = False
        p = (1 + sum(1 for d in null if d >= observed - 1e-12)) / (1 + n_permutations)
        floor = 1.0 / (1 + n_permutations)
    return {
        "valid": True,
        "exact": exact,
        "observed_cosine_distance": observed,
        "p_value": float(p),
        "n_assignments": total if exact else n_permutations,
        "min_possible_p": float(floor),
        "null_mean": float(np.mean(null)),
        "null_max": float(np.max(null)),
    }


def _sigmoid(z: np.ndarray) -> np.ndarray:
    return 1.0 / (1.0 + np.exp(-np.clip(z, -30.0, 30.0)))


def _fit_l1_logistic_batch(
    X: np.ndarray, Y: np.ndarray, lam: np.ndarray, n_iter: int = 200
) -> tuple[np.ndarray, np.ndarray]:
    """Fit batched L1 logistic regressions with deterministic ISTA/FISTA.

    The implementation is NumPy-only and uses an unpenalized intercept. It is a
    detector for controlled experiments, not a high-precision optimizer.
    """
    n, d = X.shape
    X = np.ascontiguousarray(X, dtype=np.float32)
    Y = np.ascontiguousarray(Y, dtype=np.float32)
    lam32 = lam.astype(np.float32)
    gram = X @ X.T
    # Use a deterministic non-constant start vector. After column centering,
    # an all-ones vector lies in the Gram matrix null space and would make
    # power iteration collapse immediately.
    v = np.random.default_rng(7).standard_normal(n).astype(np.float32)
    v /= max(float(np.linalg.norm(v)), 1e-12)
    for _ in range(30):
        nxt = gram @ v
        norm = float(np.linalg.norm(nxt))
        if norm == 0.0:
            break
        v = nxt / norm
    sigma2 = float(v @ gram @ v)
    if sigma2 <= 0.0:
        # For a positive semidefinite matrix, trace is at least sigma_max squared.
        # This fallback is conservative but stable.
        sigma2 = float(np.trace(gram))
    step = np.float32(1.0 / max(sigma2 / (4.0 * n), 1e-12))
    W = np.zeros((d, Y.shape[1]), dtype=np.float32)
    b = np.zeros(Y.shape[1], dtype=np.float32)
    Z = W  # FISTA-extrapolatiepunt
    t_acc = 1.0
    for _ in range(n_iter):
        resid = (_sigmoid(X @ Z + b) - Y) / np.float32(n)
        W_next = Z - step * (X.T @ resid)
        W_next = np.sign(W_next) * np.maximum(np.abs(W_next) - step * lam32, 0.0)
        b = b - step * resid.sum(axis=0)
        t_next = (1.0 + np.sqrt(1.0 + 4.0 * t_acc * t_acc)) / 2.0
        Z = W_next + np.float32((t_acc - 1.0) / t_next) * (W_next - W)
        W, t_acc = W_next, t_next
    return W.astype(np.float64), b.astype(np.float64)


def sparse_probe(
    vectors: list[np.ndarray],
    labels: list[str],
    n_permutations: int = 500,
    rng_seed: int = 45,
    lam_frac: float = 0.1,
    n_iter: int = 200,
) -> dict[str, Any]:
    """Run an H-Neurons-style sparse classifier with leave-one-out CV.

    The permutation control tests whether high-dimensional sparse separation is
    stronger than chance under the same small-sample conditions.
    """
    classes = sorted(set(labels))
    if len(classes) != 2:
        return {"valid": False, "reason": "two classes required"}
    counts = {c: labels.count(c) for c in classes}
    if min(counts.values()) < 2:
        return {
            "valid": False,
            "reason": "at least two examples per class are required for leave-one-out CV",
            "n_per_class": counts,
        }
    X = np.stack(vectors).astype(np.float64)
    y = np.array([1.0 if lbl == classes[1] else 0.0 for lbl in labels])
    n, d = X.shape
    rng = np.random.default_rng(rng_seed)
    Y = np.empty((n, 1 + n_permutations))
    Y[:, 0] = y
    for j in range(n_permutations):
        Y[:, j + 1] = rng.permutation(y)

    probs = np.empty((n, Y.shape[1]))
    for i in range(n):
        mask = np.ones(n, dtype=bool)
        mask[i] = False
        x_tr = X[mask]
        mu = x_tr.mean(axis=0)
        sd = x_tr.std(axis=0)
        sd[sd == 0.0] = 1.0
        x_std = (x_tr - mu) / sd
        y_tr = Y[mask]
        # Scale lambda relative to lambda_max, where the L1 solution becomes zero,
        # independently for each label column.
        lam = lam_frac * np.max(np.abs(x_std.T @ (0.5 - y_tr)), axis=0) / (n - 1)
        W, b = _fit_l1_logistic_batch(x_std, y_tr, lam, n_iter=n_iter)
        probs[i] = _sigmoid(((X[i] - mu) / sd) @ W + b)

    hard = probs >= 0.5
    pos = Y == 1.0
    tpr = (hard & pos).sum(axis=0) / pos.sum(axis=0)
    tnr = (~hard & ~pos).sum(axis=0) / (~pos).sum(axis=0)
    baccs = (tpr + tnr) / 2.0
    observed = float(baccs[0])
    p_value = (
        float((1 + int((baccs[1:] >= observed - 1e-12).sum())) / (1 + n_permutations))
        if n_permutations
        else None
    )

    # Fit all data only to inspect sparsity and candidate dimensions.
    # Generalization evidence comes exclusively from LOOCV and permutation.
    mu = X.mean(axis=0)
    sd = X.std(axis=0)
    sd[sd == 0.0] = 1.0
    x_std = (X - mu) / sd
    y_col = y.reshape(-1, 1)
    lam_full = lam_frac * np.max(np.abs(x_std.T @ (0.5 - y_col)), axis=0) / n
    W_full, _ = _fit_l1_logistic_batch(x_std, y_col, lam_full, n_iter=n_iter)
    w = W_full[:, 0]
    nonzero = np.flatnonzero(w)
    top = nonzero[np.argsort(np.abs(w[nonzero]))[::-1][:5]]
    return {
        "valid": True,
        "method": (
            "sparse L1 logistic classifier (ISTA, NumPy) + "
            "leave-one-out CV + label-shuffle permutation control; "
            "H-Neurons-style detector"
        ),
        "classes": classes,
        "n_per_class": counts,
        "loocv_balanced_accuracy": observed,
        "p_value": p_value,
        "n_permutations": n_permutations,
        "min_possible_p": (1.0 / (1 + n_permutations)) if n_permutations else None,
        "n_dims": int(d),
        "n_nonzero_full_fit": int(nonzero.size),
        "sparsity_fraction": float(nonzero.size / d) if d else 0.0,
        "candidate_neurons": [
            {"dim": int(i), "weight": float(w[i])} for i in top
        ],
    }


def probe_report(
    per_layer: dict[str, dict[str, list[np.ndarray]]],
    sparse_permutations: int = 500,
) -> dict[str, Any]:
    """Build per-layer separation, permutation, and sparse-probe reports."""
    layers: dict[str, dict[str, Any]] = {}
    for name, acts in per_layer.items():
        rep = class_separation(acts)
        if rep.get("separable"):
            vectors = [v for label in sorted(acts) for v in acts[label]]
            labels = [label for label in sorted(acts) for _ in acts[label]]
            rep["permutation"] = permutation_control(vectors, labels)
            rep["sparse_probe"] = sparse_probe(
                vectors, labels, n_permutations=sparse_permutations
            )
        layers[name] = rep
    scored = {
        name: rep["cosine_distance"]
        for name, rep in layers.items()
        if rep.get("separable")
    }
    best = max(scored, key=scored.get) if scored else None
    sparse_scored = {
        name: rep["sparse_probe"]["loocv_balanced_accuracy"]
        for name, rep in layers.items()
        if rep.get("sparse_probe", {}).get("valid")
    }
    sparse_best = max(sparse_scored, key=sparse_scored.get) if sparse_scored else None
    return {
        "layers": layers,
        "strongest_layer": best,
        "strongest_cosine_distance": scored.get(best) if best else None,
        "strongest_permutation_p": (
            layers[best]["permutation"]["p_value"] if best else None
        ),
        "strongest_sparse_layer": sparse_best,
        "strongest_sparse_balanced_accuracy": (
            sparse_scored.get(sparse_best) if sparse_best else None
        ),
        "strongest_sparse_p": (
            layers[sparse_best]["sparse_probe"]["p_value"] if sparse_best else None
        ),
    }


# -- activatie-backends --------------------------------------------------------


class FakeActivationModel:
    """Deterministic CI backend that derives activations from a text hash.

    It validates hooks-to-vectors-to-analysis mechanics and encodes no class
    information. It provides no evidence about real model internals.
    """

    name = "fake"
    layer_names = ("mlp.0", "mlp.1")

    def __init__(self, dim: int = 16) -> None:
        self.dim = dim

    def activations_for(self, prompt: str, focus: str | None = None) -> dict[str, np.ndarray]:
        # With token-scoped pooling, the vector depends only on the focus span.
        basis = focus if focus and focus in prompt else prompt
        out: dict[str, np.ndarray] = {}
        for layer in self.layer_names:
            digest = hashlib.sha256(f"{layer}::{basis}".encode()).digest()
            rng = np.random.default_rng(int.from_bytes(digest[:8], "big"))
            out[layer] = rng.normal(size=self.dim)
        return out


class HFActivationModel:  # pragma: no cover - vereist torch/transformers (opt-in)
    """Capture activations from MLP modules in a Hugging Face model.

    ``mlp_out`` reads MLP block output. ``neuron`` reads the input of the down
    projection, after the nonlinearity and before projection to the residual
    stream.
    """

    def __init__(
        self,
        model_id: str,
        device: str = "cpu",
        read_location: str = "mlp_out",
        revision: str | None = None,
        dtype: str | None = None,
    ) -> None:
        import torch  # noqa: F401
        from transformers import AutoModelForCausalLM, AutoTokenizer

        if read_location not in ("mlp_out", "neuron"):
            raise ValueError(f"Unknown read_location: {read_location!r}")
        # Pin a model revision for reproducibility. Without a fixed snapshot, the
        # Hub may serve a different model version between runs.
        self.name = f"hf:{model_id}" + (f"@{revision}" if revision else "")
        self.read_location = read_location
        self.revision = revision
        # Larger models may not fit in fp32 on a CPU runner. bf16 or fp16 roughly
        # halves memory. The default remains fp32 for historical small-model runs.
        self.dtype = dtype
        torch_dtype = {
            None: None,
            "float32": torch.float32,
            "float16": torch.float16,
            "bfloat16": torch.bfloat16,
        }.get(dtype)
        if dtype is not None and torch_dtype is None:
            raise ValueError(f"Unknown dtype: {dtype!r}")
        self.tokenizer = AutoTokenizer.from_pretrained(model_id, revision=revision)
        self.model = AutoModelForCausalLM.from_pretrained(
            model_id, revision=revision, torch_dtype=torch_dtype
        )
        self.model.eval()
        self.device = device
        self.model.to(device)

    def activations_for(self, prompt: str, focus: str | None = None) -> dict[str, np.ndarray]:
        """Return per-layer activations, optionally pooled over focus tokens."""
        import torch

        positions: list[int] | None = None
        span = find_focus_span(prompt, focus) if focus else None
        if span is not None:
            encoded = self.tokenizer(
                prompt,
                return_offsets_mapping=True,
                truncation=True,
                max_length=512,
            )
            positions = select_focus_positions(
                encoded["offset_mapping"], span[0], span[1]
            ) or None

        captured: dict[str, np.ndarray] = {}

        def _pool(tensor, _name):
            tensor = tensor.detach().float()
            if positions is not None and tensor.dim() == 3:
                tensor = tensor[:, positions, :]
            captured[_name] = tensor.mean(dim=(0, 1)).cpu().numpy()

        handles = []
        for name, module in self.model.named_modules():
            if self.read_location == "neuron":
                # H-Neurons-style read point: input to the down projection, representing
                # per-neuron activations in the intermediate dimension.
                if name.endswith(".mlp.c_proj") or name.endswith(".mlp.down_proj"):
                    def _pre_hook(mod, inputs, _name=name):
                        _pool(inputs[0], _name)
                    handles.append(module.register_forward_pre_hook(_pre_hook))
            else:
                # Cover common GPT-2 and Llama-style MLP module names.
                if name.endswith(".mlp") or name.endswith(".mlp.c_proj"):
                    def _hook(mod, inputs, output, _name=name):
                        tensor = output[0] if isinstance(output, tuple) else output
                        _pool(tensor, _name)
                    handles.append(module.register_forward_hook(_hook))
        try:
            tokens = self.tokenizer(
                prompt, return_tensors="pt", truncation=True, max_length=512
            ).to(self.device)
            with torch.no_grad():
                self.model(**tokens)
        finally:
            for h in handles:
                h.remove()
        return captured


# -- probe run -------------------------------------------------------------------


def load_verdict_labels(verdicts_path: str) -> dict[str, str]:
    """Load externally judged labels from a dialectic-falsification artifact.

    Undecided and skipped records are excluded.
    """
    payload = json.loads(Path(verdicts_path).read_text(encoding="utf-8"))
    records = payload.get("records", payload if isinstance(payload, list) else [])
    labels: dict[str, str] = {}
    for rec in records:
        verdict = rec.get("verdict")
        text = rec.get("seed_text")
        if text and verdict in (VERDICT_WEERLEGD, VERDICT_HOUDT_STAND):
            labels[text] = verdict
    return labels


def run_activation_probe(
    input_path: str,
    output_path: str = "results/activation_probe.json",
    backend: str = "fake",
    model_id: str | None = None,
    pooling: str = "statement",
    verdicts_path: str | None = None,
    read_location: str = "mlp_out",
    sparse_permutations: int = 500,
    model_revision: str | None = None,
    require_verdict_coverage: bool = False,
    dtype: str | None = None,
) -> dict[str, Any]:
    """Probe dialectical cases by verdict class and model layer.

    Verdicts come from the deterministic fixture unless an external
    dialectic-falsification artifact is supplied. No manager or seed state is
    accessed.
    """
    data = json.loads(Path(input_path).read_text(encoding="utf-8"))
    source_text = data["source_text"]
    if backend == "fake":
        model: Any = FakeActivationModel()
    elif backend == "hf":
        if not model_id:
            raise ValueError("--model-id is required for backend 'hf'")
        model = HFActivationModel(
            model_id,
            read_location=read_location,
            revision=model_revision,
            dtype=dtype,
        )
    else:
        raise ValueError(f"Unknown activation-probe backend: {backend!r}")

    external_labels = load_verdict_labels(verdicts_path) if verdicts_path else None
    verdict_source = "external" if external_labels is not None else "fixture"
    # Coverage guard: a verdict file from another case set, or an incomplete
    # artifact, must not silently produce a plausible-looking subset run.
    verdict_coverage: dict[str, Any] | None = None
    if external_labels is not None:
        input_texts = {case["seed_text"] for case in data["cases"]}
        foreign = sorted(set(external_labels) - input_texts)
        if foreign:
            raise ValueError(
                f"verdict file contains {len(foreign)} claims that are not in "
                f"the input case set: {foreign[:3]}"
            )
        labeled = input_texts & set(external_labels)
        missing = sorted(input_texts - set(external_labels))
        if not labeled:
            raise ValueError(
                "no input case has an external verdict label; the verdict file "
                "does not match this input"
            )
        if require_verdict_coverage and missing:
            raise ValueError(
                f"strict coverage is required, but {len(missing)} of "
                f"{len(input_texts)} cases lack an external label: {missing[:3]}"
            )
        verdict_coverage = {
            "n_input_cases": len(input_texts),
            "n_labeled": len(labeled),
            "n_missing": len(missing),
            "strict": require_verdict_coverage,
        }
    verdict_backend = FixtureDialecticBackend() if external_labels is None else None
    per_layer: dict[str, dict[str, list[np.ndarray]]] = {}
    cases_out: list[dict[str, Any]] = []
    for case in data["cases"]:
        seed_text = case["seed_text"]
        prompt = build_dialectic_prompt(seed_text, source_text)
        if external_labels is not None:
            verdict = external_labels.get(seed_text)
            if verdict is None:
                continue  # no external verdict for this claim
        else:
            raw = verdict_backend.generate(
                prompt, {"seed_text": seed_text, "source_text": source_text}, "dialectic", []
            )
            verdict = parse_dialectic_verdict(raw)["verdict"]
        if verdict not in (VERDICT_WEERLEGD, VERDICT_HOUDT_STAND):
            continue  # ONBESLIST does not provide a class signal.
        focus = seed_text if pooling in ("statement", "stelling") else None
        acts = model.activations_for(prompt, focus=focus)
        for layer, vec in acts.items():
            per_layer.setdefault(layer, {}).setdefault(verdict, []).append(vec)
        cases_out.append({"seed_text": seed_text, "verdict": verdict, "layers": sorted(acts)})

    result = {
        "artifact": "activation_probe",
        "evidence_layer": "G",
        "backend": getattr(model, "name", backend),
        "pooling": pooling,
        "read_location": read_location,
        "model_revision": model_revision,
        "dtype": dtype,
        "verdict_source": verdict_source,
        "verdict_coverage": verdict_coverage,
        "doctrine": (
            "Layer G signal: activation separation between dialectical verdict "
            "classes. Signal != verdict; no seed state is touched and no "
            "promotion is triggered. The fake backend proves harness mechanics only."
        ),
        "cases": cases_out,
        "report": probe_report(per_layer, sparse_permutations=sparse_permutations),
    }
    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return result

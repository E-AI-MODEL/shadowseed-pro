from __future__ import annotations

from pathlib import Path


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"{label}: expected exactly one match, found {count}")
    return text.replace(old, new, 1)


def patch_model_adapter() -> None:
    path = Path("src/shadowseed/adapters/models.py")
    text = path.read_text(encoding="utf-8")
    text = replace_once(
        text,
        '    def __init__(self, model_id: str, max_new_tokens: int = 220) -> None:\n',
        '    def __init__(\n        self,\n        model_id: str,\n        max_new_tokens: int = 220,\n        revision: str | None = None,\n    ) -> None:\n',
        "HF model constructor",
    )
    text = replace_once(
        text,
        '        self.max_new_tokens = max_new_tokens\n        self.tokenizer = AutoTokenizer.from_pretrained(model_id)\n',
        '        self.max_new_tokens = max_new_tokens\n        self.revision = revision\n        tokenizer_kwargs = {"revision": revision} if revision is not None else {}\n        self.tokenizer = AutoTokenizer.from_pretrained(model_id, **tokenizer_kwargs)\n',
        "HF model tokenizer revision",
    )
    text = replace_once(
        text,
        '        model = AutoModelForCausalLM.from_pretrained(model_id, **model_kwargs)\n',
        '        if revision is not None:\n            model_kwargs["revision"] = revision\n        model = AutoModelForCausalLM.from_pretrained(model_id, **model_kwargs)\n',
        "HF model weights revision",
    )
    text = replace_once(
        text,
        'def make_backend(backend: str, model_id: str | None, max_new_tokens: int) -> ModelBackend:\n',
        'def make_backend(\n    backend: str,\n    model_id: str | None,\n    max_new_tokens: int,\n    model_revision: str | None = None,\n) -> ModelBackend:\n',
        "model backend factory signature",
    )
    text = replace_once(
        text,
        '        return HFTransformersBackend(model_id=model_id, max_new_tokens=max_new_tokens)\n',
        '        return HFTransformersBackend(\n            model_id=model_id,\n            max_new_tokens=max_new_tokens,\n            revision=model_revision,\n        )\n',
        "model backend revision forwarding",
    )
    path.write_text(text, encoding="utf-8")


def patch_detector() -> None:
    path = Path("src/shadowseed/detection/model_detector.py")
    text = path.read_text(encoding="utf-8")

    start = text.index("def parse_numbered_seeds(")
    end = text.index("\n\n# Prompt variant", start)
    replacement = '''def parse_numbered_seeds_with_diagnostics(
    raw_output: str,
    max_seeds: int = 5,
    source_text: str = "",
) -> tuple[list[str], dict[str, int | bool]]:
    """Parse detector output and retain non-authority parser diagnostics.

    The diagnostics make malformed output and few-shot leakage observable to
    research harnesses without changing Gate semantics. A duplicated numbering
    prefix (``1. 1. candidate``) can be introduced when a backend reconstructs
    the prompt's prefilled ``1.`` line. Removing only that syntactic prefix is
    counted explicitly and never changes the candidate's semantic content.
    """

    seeds: list[str] = []
    seen: set[str] = set()
    diagnostics: dict[str, int | bool] = {
        "nonblank_lines": 0,
        "numbered_lines": 0,
        "unnumbered_nonblank_lines": 0,
        "nested_numbering_prefixes_removed": 0,
        "dropped_blank_or_placeholder": 0,
        "dropped_citation_or_stub": 0,
        "dropped_fewshot_leak": 0,
        "dropped_duplicate": 0,
        "accepted_candidates": 0,
        "truncated_after_max_seeds": False,
    }
    for line in raw_output.splitlines():
        if line.strip():
            diagnostics["nonblank_lines"] = int(diagnostics["nonblank_lines"]) + 1
        match = _NUMBERED_LINE.match(line)
        if not match:
            if line.strip():
                diagnostics["unnumbered_nonblank_lines"] = (
                    int(diagnostics["unnumbered_nonblank_lines"]) + 1
                )
            continue
        diagnostics["numbered_lines"] = int(diagnostics["numbered_lines"]) + 1
        seed = match.group(1).strip().strip("-•").strip()
        while seed:
            nested = _NUMBERED_LINE.match(seed)
            if nested is None:
                break
            seed = nested.group(1).strip().strip("-•").strip()
            diagnostics["nested_numbering_prefixes_removed"] = (
                int(diagnostics["nested_numbering_prefixes_removed"]) + 1
            )
        if not seed or seed.lower() == "[seed]":
            diagnostics["dropped_blank_or_placeholder"] = (
                int(diagnostics["dropped_blank_or_placeholder"]) + 1
            )
            continue
        if _looks_like_citation_fragment(seed, source_text):
            diagnostics["dropped_citation_or_stub"] = (
                int(diagnostics["dropped_citation_or_stub"]) + 1
            )
            continue
        if _looks_like_fewshot_leak(seed):
            diagnostics["dropped_fewshot_leak"] = int(diagnostics["dropped_fewshot_leak"]) + 1
            continue
        if seed in seen:
            diagnostics["dropped_duplicate"] = int(diagnostics["dropped_duplicate"]) + 1
            continue
        seen.add(seed)
        seeds.append(seed)
        if len(seeds) >= max_seeds:
            diagnostics["truncated_after_max_seeds"] = True
            break
    diagnostics["accepted_candidates"] = len(seeds)
    return seeds, diagnostics


def parse_numbered_seeds(
    raw_output: str,
    max_seeds: int = 5,
    source_text: str = "",
) -> list[str]:
    """Parse ``1. seed`` style lines while preserving the legacy list API."""

    seeds, _diagnostics = parse_numbered_seeds_with_diagnostics(
        raw_output,
        max_seeds=max_seeds,
        source_text=source_text,
    )
    return seeds
'''
    text = text[:start] + replacement + text[end:]

    text = replace_once(
        text,
        '    def __init__(self, model_id: str, max_new_tokens: int = 400, prompt_variant: str = "absence") -> None:\n',
        '    def __init__(\n        self,\n        model_id: str,\n        max_new_tokens: int = 400,\n        prompt_variant: str = "absence",\n        revision: str | None = None,\n    ) -> None:\n',
        "HF detector constructor",
    )
    text = replace_once(
        text,
        '        self.model_id = model_id\n        self.max_new_tokens = max_new_tokens\n        self.tokenizer = AutoTokenizer.from_pretrained(model_id)\n',
        '        self.model_id = model_id\n        self.max_new_tokens = max_new_tokens\n        self.revision = revision\n        self.last_raw_output: str | None = None\n        self.last_parse_diagnostics: dict[str, int | bool] | None = None\n        tokenizer_kwargs = {"revision": revision} if revision is not None else {}\n        self.tokenizer = AutoTokenizer.from_pretrained(model_id, **tokenizer_kwargs)\n',
        "HF detector revision and diagnostics",
    )
    text = replace_once(
        text,
        '        model = AutoModelForCausalLM.from_pretrained(model_id, **model_kwargs)\n',
        '        if revision is not None:\n            model_kwargs["revision"] = revision\n        model = AutoModelForCausalLM.from_pretrained(model_id, **model_kwargs)\n',
        "HF detector weights revision",
    )

    # Ollama and OpenAI detector constructors each have this exact state block.
    state = '        self.model_id = model_id\n        self.max_new_tokens = max_new_tokens\n        self.client = '
    if text.count(state) != 2:
        raise RuntimeError(f"real client detector state: expected 2 matches, found {text.count(state)}")
    text = text.replace(
        state,
        '        self.model_id = model_id\n        self.max_new_tokens = max_new_tokens\n        self.last_raw_output: str | None = None\n        self.last_parse_diagnostics: dict[str, int | bool] | None = None\n        self.client = ',
    )

    old_return = '''        # the prompt ends with "1.\\n" — re-prepend so the parser sees the first item
        return parse_numbered_seeds(
            "1. " + raw, max_seeds=max_seeds, source_text=text
        )
'''
    new_return = '''        # The prompt ends with a prefilled ``1.``. Reconstruct it for parsing,
        # but retain raw output and diagnostics so research runs can measure
        # formatting artifacts and rejected leakage rather than hiding them.
        seeds, diagnostics = parse_numbered_seeds_with_diagnostics(
            "1. " + raw, max_seeds=max_seeds, source_text=text
        )
        self.last_raw_output = raw
        self.last_parse_diagnostics = diagnostics
        return seeds
'''
    if text.count(old_return) != 3:
        raise RuntimeError(f"detector parse return: expected 3 matches, found {text.count(old_return)}")
    text = text.replace(old_return, new_return)

    old_factory = '''def make_detector_backend(
    backend: str,
    model_id: str | None = None,
    max_new_tokens: int = 400,
    prompt_variant: str = "absence",
) -> DetectorBackend:
'''
    new_factory = '''def make_detector_backend(
    backend: str,
    model_id: str | None = None,
    max_new_tokens: int = 400,
    prompt_variant: str = "absence",
    model_revision: str | None = None,
) -> DetectorBackend:
'''
    text = replace_once(text, old_factory, new_factory, "detector factory signature")
    text = replace_once(
        text,
        '            model_id=model_id, max_new_tokens=max_new_tokens, prompt_variant=prompt_variant\n',
        '            model_id=model_id,\n            max_new_tokens=max_new_tokens,\n            prompt_variant=prompt_variant,\n            revision=model_revision,\n',
        "detector revision forwarding",
    )
    path.write_text(text, encoding="utf-8")


def patch_capability_harness() -> None:
    path = Path("src/shadowseed/benchmark/capability_scaling.py")
    text = path.read_text(encoding="utf-8")
    text = replace_once(
        text,
        'from shadowseed.detection.model_detector import make_detector_backend\n',
        'from shadowseed.detection.model_detector import (\n    OPEN_SET_GENERATIVE_DETECTOR_ID,\n    OPEN_SET_GENERATIVE_PROMPT,\n    make_detector_backend,\n)\n',
        "capability detector imports",
    )

    gate_anchor = 'def _assert_live_authority_invariants(events: list[dict[str, Any]]) -> None:\n'
    helper = '''def _parser_diagnostics_summary(counts: Counter[str] | dict[str, int]) -> dict[str, Any]:
    numbered = int(counts.get("numbered_lines", 0))
    dropped_blank = int(counts.get("dropped_blank_or_placeholder", 0))
    dropped_citation = int(counts.get("dropped_citation_or_stub", 0))
    dropped_fewshot = int(counts.get("dropped_fewshot_leak", 0))
    dropped_duplicate = int(counts.get("dropped_duplicate", 0))
    rejected = dropped_blank + dropped_citation + dropped_fewshot + dropped_duplicate
    return {
        "nonblank_lines": int(counts.get("nonblank_lines", 0)),
        "numbered_lines": numbered,
        "unnumbered_nonblank_lines": int(counts.get("unnumbered_nonblank_lines", 0)),
        "accepted_candidates": int(counts.get("accepted_candidates", 0)),
        "nested_numbering_prefixes_removed": int(
            counts.get("nested_numbering_prefixes_removed", 0)
        ),
        "dropped_blank_or_placeholder": dropped_blank,
        "dropped_citation_or_stub": dropped_citation,
        "dropped_fewshot_leak": dropped_fewshot,
        "dropped_duplicate": dropped_duplicate,
        "parser_rejection_rate": round(rejected / numbered, 6) if numbered else None,
        "fewshot_leakage_rate": round(dropped_fewshot / numbered, 6) if numbered else None,
        "dropped_citation_or_stub_rate": round(dropped_citation / numbered, 6)
        if numbered
        else None,
    }


'''
    if gate_anchor not in text:
        raise RuntimeError("capability parser summary anchor not found")
    text = text.replace(gate_anchor, helper + gate_anchor, 1)

    text = replace_once(
        text,
        '    total_answer_calls = 0\n\n    for conversation in selected:\n',
        '    total_answer_calls = 0\n    parser_diag_totals: Counter[str] = Counter()\n\n    for conversation in selected:\n',
        "parser diagnostic counter",
    )
    text = replace_once(
        text,
        '            report = session.turn(turn["question"])\n            turn_reports.append(report)\n',
        '            report = session.turn(turn["question"])\n            if mode == "live":\n                parse_diagnostics = getattr(detector_backend, "last_parse_diagnostics", None)\n                raw_detector_output = getattr(detector_backend, "last_raw_output", None)\n                if isinstance(parse_diagnostics, dict):\n                    report["detector_parse_diagnostics"] = dict(parse_diagnostics)\n                    for key, value in parse_diagnostics.items():\n                        if isinstance(value, int) and not isinstance(value, bool):\n                            parser_diag_totals[key] += value\n                if isinstance(raw_detector_output, str):\n                    report["detector_raw_output"] = raw_detector_output\n            turn_reports.append(report)\n',
        "capture detector diagnostics",
    )
    text = replace_once(
        text,
        '        "candidate_metrics": duplicate_metrics,\n        "gate": gate_summary,\n',
        '        "candidate_metrics": duplicate_metrics,\n        "detector_parser": _parser_diagnostics_summary(parser_diag_totals),\n        "gate": gate_summary,\n',
        "suite parser summary",
    )

    text = replace_once(
        text,
        '    suppressed = sum(item["suppressed_self_attributed_occurrences"] for item in live)\n    return {\n',
        '    suppressed = sum(item["suppressed_self_attributed_occurrences"] for item in live)\n    parser_counts: Counter[str] = Counter()\n    for item in live:\n        for key in (\n            "nonblank_lines",\n            "numbered_lines",\n            "unnumbered_nonblank_lines",\n            "accepted_candidates",\n            "nested_numbering_prefixes_removed",\n            "dropped_blank_or_placeholder",\n            "dropped_citation_or_stub",\n            "dropped_fewshot_leak",\n            "dropped_duplicate",\n        ):\n            parser_counts[key] += int(item.get("detector_parser", {}).get(key, 0))\n    parser_summary = _parser_diagnostics_summary(parser_counts)\n    return {\n',
        "aggregate parser counts",
    )
    text = replace_once(
        text,
        '            "semantic_duplicate_rate": round(live_semantic_dupes / live_admissible, 6)\n            if live_admissible\n            else None,\n',
        '            "semantic_duplicate_rate": round(live_semantic_dupes / live_admissible, 6)\n            if live_admissible\n            else None,\n            "detector_parser": parser_summary,\n',
        "aggregate parser summary",
    )
    text = replace_once(
        text,
        '        f"- Live candidate occurrences: {live[\'candidate_occurrences\']}",\n        f"- Malformed/non-atomic prescreen rate: {live[\'malformed_or_non_atomic_rate\']}",\n',
        '        f"- Live candidate occurrences: {live[\'candidate_occurrences\']}",\n        f"- Detector parser rejection rate: {live[\'detector_parser\'][\'parser_rejection_rate\']}",\n        f"- Detector few-shot leakage rate: {live[\'detector_parser\'][\'fewshot_leakage_rate\']}",\n        f"- Nested numbering prefixes removed: {live[\'detector_parser\'][\'nested_numbering_prefixes_removed\']}",\n        f"- Malformed/non-atomic prescreen rate after parsing: {live[\'malformed_or_non_atomic_rate\']}",\n',
        "report parser metrics",
    )

    text = replace_once(
        text,
        '    model = make_backend(backend=backend, model_id=model_id, max_new_tokens=max_new_tokens)\n    detector = make_detector_backend(\n        backend,\n        model_id=model_id,\n        max_new_tokens=max_new_tokens,\n        prompt_variant="generative",\n    )\n',
        '    model = make_backend(\n        backend=backend,\n        model_id=model_id,\n        max_new_tokens=max_new_tokens,\n        model_revision=model_revision,\n    )\n    detector = make_detector_backend(\n        backend,\n        model_id=model_id,\n        max_new_tokens=max_new_tokens,\n        prompt_variant="generative",\n        model_revision=model_revision,\n    )\n',
        "apply model revision",
    )
    text = replace_once(
        text,
        '            "detector_prompt_variant": "generative",\n            "authority_effect_of_model_identity": "none",\n',
        '            "detector_prompt_variant": "generative",\n            "detector_id": OPEN_SET_GENERATIVE_DETECTOR_ID,\n            "detector_prompt_template_sha256": _sha256_bytes(\n                OPEN_SET_GENERATIVE_PROMPT.encode("utf-8")\n            ),\n            "authority_effect_of_model_identity": "none",\n',
        "manifest detector identity",
    )
    path.write_text(text, encoding="utf-8")


def write_tests() -> None:
    path = Path("tests/test_capability_parser_diagnostics.py")
    path.write_text(
        '''from __future__ import annotations

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
    raw = """\
1. Colonial capital as an explanatory frame alongside technological innovation.
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
''',
        encoding="utf-8",
    )


def main() -> None:
    patch_model_adapter()
    patch_detector()
    patch_capability_harness()
    write_tests()


if __name__ == "__main__":
    main()

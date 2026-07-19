"""Open-set language-model detector for the SSL 4.6 research claim.

The open-set detection step is model-backed rather than a regex or template
baseline. Given an input item, this module builds a constrained prompt and
parses numbered model output into weightless candidate seeds.

Supported backends:

- ``fixture``: deterministic and offline. It prefixes all output with
  ``[FIXTURE]`` so it cannot be confused with model evidence.
- ``hf-transformers``: a local Hugging Face causal language model.
- ``ollama``: a model served by a local Ollama server.
- ``openai``: a hosted OpenAI chat model.

Detector output remains hypothetical. Candidates still pass through seed
normalization, zero-weight storage, evidence review, and the Validation Gate
before they can influence an answer or action.
"""

from __future__ import annotations

import re
from typing import Any, Protocol


OPEN_SET_MODEL_DETECTOR_ID = "ssl46_open_set_model_detector_v0.3"
OPEN_SET_MODEL_DETECTOR_SOURCE = "open_set_model_detector"


# Few-shot examples deliberately come from domains that are NOT the open-set
# news corpus (history, software, law, medicine). When the model leaks an
# example verbatim into a news item it is then obviously off-topic and is also
# caught by the verbatim leakage filter below. Using news-domain entities here
# (the v0.3b mistake) let the model blend "Sven Jaschan" / "Apple" into
# unrelated news items because they pattern-matched the input.
_FEWSHOT_BAD = (
    "Evidence for the central claim.",
    "Timeline of the event.",
    "Security, privacy, and scalability.",
    "&lt;tag&gt;",
)
_FEWSHOT_GOOD = (
    "Colonial capital as a funding source for British factory investment.",
    "GDPR compliance when processing medical heart-rate data.",
    "Jurisdiction in a cross-border consumer dispute.",
)

# Generative ("kunnen staan") few-shot: not an omission to fill but an
# explanatory FRAME / lens / dimension that could lift the answer beyond what is
# literally retrievable. Still bare noun phrases (the canonical form), still
# foreign-domain (form only), but bigger in scope than the absence examples.
_FEWSHOT_GOOD_GENERATIVE = (
    "Colonial capital as an explanatory frame alongside technological innovation.",
    "Privacy by design as a principle affecting the entire architecture.",
    "Private international law as a framing dimension for this consumer case.",
)


def _numbered(lines: tuple[str, ...]) -> str:
    return "\n".join(f"{i}. {line}" for i, line in enumerate(lines, start=1))


# Prompt iteration v0.3g: resolves the scaffold contradiction that round 006
# exposed. v0.3e required complete absence sentences.
# while its few-shot EXAMPLES showed bare noun phrases — the canonical 4.5
# seed form as a short noun phrase. Qwen followed
# the rule; Phi followed the examples (and form compliance proved
# domain-dependent: 0/60 scaffolded on news, 18/60 on science). v0.3g aligns
# the rule with the examples: the gap-label noun phrase is canonical, the
# absence sentence stays allowed, and asserting a fact stays forbidden. A
# noun phrase cannot assert a fact (no main-clause verb), so the
# claim-vs-gap failure mode this rule exists for is structurally excluded.
#
# Note (02_atomic_seeds §2): generation enforces only "one gap per seed", "no
# fabricated facts", and "tie the gap to THIS text". Value judgments —
# triviality, specificity, relevance, redundancy — are review/Gate/normalization
# concerns, NOT generation blockades, because pre-judging value at birth breaks
# the weightless-seed principle. Redundant near-duplicates are deduplicated
# downstream (normalization, 4.5 §12.4) and surfaced by the prescreen, not
# suppressed here.
OPEN_SET_DETECTION_PROMPT = """
You are an epistemic analyst.

You receive a short input text. Do not summarize, quote, or paraphrase it.
Identify small structural absences: which concepts, relations, assumptions, or
constraints are missing even though they would be needed for a fuller
understanding of this specific subject?

Rules:
- Return at most {max_seeds} candidate gaps.
- Each candidate names exactly one missing element.
- Use the same language as the input text. Keep technical terms and proper
  names in their original form when translation would be uncertain.
- The output is detector material for later review. Do not assign a seed,
  evidence, validation, promotion, or status label.
- Name the MISSING element itself as a short, concrete noun phrase like the
  good examples below. A complete absence sentence is also allowed.
  Do not write a new factual claim.
  * Wrong claim: "The regulator did not investigate the incident."
  * Good gap label: "The outcome of the regulator's investigation."
  * Also good: "Whether the regulator investigated the incident is not stated."
- Only name something as missing when it is genuinely absent from the text.
  A name, amount, date, or relation already present is not a gap.
- Tie every candidate to the subject of THIS input text.
- Do not invent facts, names, numbers, quotations, or sources.
- Do not copy sentences or long fragments from the input.
- Do not return isolated words, names, or acronyms without a relation.
- Do not combine multiple analytical frames or lists in one candidate.
- Do not use vague meta-categories without a concrete relation.

The examples below come from OTHER texts and domains. They demonstrate form
only. Do not copy their content. Write candidates about the input text below.

Bad form examples, do not copy:
{bad_examples}

Good form examples from other domains, do not copy:
{good_examples}

Input text:
{text}

Return at most {max_seeds} candidate gaps about this input text. Start directly
with "1.".

Output:
1.
""".strip()


class DetectorBackend(Protocol):
    name: str

    def detect_seeds(self, item: dict[str, Any], max_seeds: int = 5) -> list[str]:
        ...


_NUMBERED_LINE = re.compile(r"^\s*\d+[.)]\s*(.+?)\s*$")
# Catches both proper entities (&amp; &gt; &#36;) and the bare numeric remnant
# (#36;) that survives when the source already stripped the leading ampersand.
_HTML_ENTITY = re.compile(r"&(?:[a-zA-Z]+|#\d+);?|#\d+;")
_ACRONYM_ONLY = re.compile(r"^[A-Z][A-Z0-9.&;<>\-]{1,8}$")


def _normalize_for_match(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip(" .,:;-").lower()


def _token_set(text: str) -> set[str]:
    return {t for t in re.findall(r"[a-zà-ÿ0-9]+", text.lower()) if len(t) > 2}


_FEWSHOT_NORMALIZED = frozenset(
    _normalize_for_match(example) for example in (_FEWSHOT_GOOD + _FEWSHOT_BAD)
)
_FEWSHOT_TOKEN_SETS = tuple(_token_set(example) for example in (_FEWSHOT_GOOD + _FEWSHOT_BAD))


def _looks_like_fewshot_leak(seed: str, threshold: float = 0.7) -> bool:
    """Drop output that copies a few-shot example verbatim or near-verbatim.

    A small model sometimes echoes the prompt's example seeds. Foreign-domain
    examples make that obvious and rare, but this is the safety net. Mutated
    leakage (same template, swapped entity) is intentionally NOT caught here:
    that needs content-grounding against the input text, which is future work.
    """
    normalized = _normalize_for_match(seed)
    if normalized in _FEWSHOT_NORMALIZED:
        return True
    seed_tokens = _token_set(seed)
    if not seed_tokens:
        return False
    for example_tokens in _FEWSHOT_TOKEN_SETS:
        if not example_tokens:
            continue
        overlap = len(seed_tokens & example_tokens) / len(seed_tokens | example_tokens)
        if overlap >= threshold:
            return True
    return False


def _looks_like_citation_fragment(seed: str, source_text: str) -> bool:
    """Heuristic filter for clearly non-seed output from small models.

    Drops candidates that are too short, that are obvious HTML/garbage, that
    are bare acronyms, or that appear as a literal long substring of the
    source text. These all indicate the model copied from the input rather
    than naming a gap.
    """
    stripped = seed.strip()
    if not stripped:
        return True
    if _HTML_ENTITY.search(stripped):
        return True
    word_count = len(stripped.split())
    if word_count <= 2:
        return True
    if _ACRONYM_ONLY.match(stripped):
        return True
    # Long literal substring of input → almost certainly a citation
    if source_text and word_count <= 16:
        normalized_seed = re.sub(r"\s+", " ", stripped).strip(" .,:;-").lower()
        normalized_source = re.sub(r"\s+", " ", source_text).lower()
        if len(normalized_seed) >= 20 and normalized_seed in normalized_source:
            return True
    return False


def parse_numbered_seeds(
    raw_output: str,
    max_seeds: int = 5,
    source_text: str = "",
) -> list[str]:
    """Parse `1. seed` style lines out of a model response.

    Lines without a leading number are ignored. Blank seeds, the literal
    placeholder ``[seed]``, citation fragments (HTML entities, bare
    acronyms, very short stubs, long substrings of the source text) and
    duplicates are dropped. Returns at most ``max_seeds`` items in source
    order.

    `source_text` is the input text that was given to the model. When
    provided, candidates that appear as a long literal substring of it are
    dropped as citations.
    """
    seeds: list[str] = []
    seen: set[str] = set()
    for line in raw_output.splitlines():
        match = _NUMBERED_LINE.match(line)
        if not match:
            continue
        seed = match.group(1).strip().strip("-•").strip()
        if not seed or seed.lower() == "[seed]":
            continue
        if _looks_like_citation_fragment(seed, source_text):
            continue
        if _looks_like_fewshot_leak(seed):
            continue
        if seed in seen:
            continue
        seen.add(seed)
        seeds.append(seed)
        if len(seeds) >= max_seeds:
            break
    return seeds


# Prompt variant v0.4-gen ("kunnen staan"): the generative linchpin from
# docs/research/vision-generative-seeds.md (gap 1). Where the absence prompt asks
# the absence variant asks what is missing; this variant asks what could have
# appeared here: an untaken angle, frame, or relation that could lift the answer
# beyond what retrieval would surface. It is deliberately more generative, and
# is doctrine-safe precisely because of weightlessness: a candidate is born at
# weight 0, so a bold-but-wrong possibility costs nothing and is filtered
# downstream by the Gate (02_atomic_seeds §2). The one hard generation rule that
# stays: name a direction/frame to explore, never assert an invented fact.
OPEN_SET_GENERATIVE_PROMPT = """
You are an imaginative epistemic analyst.

You receive a short input text. Do not summarize, quote, or paraphrase it.
Identify what COULD have appeared here: an angle, explanatory frame, relation,
or dimension that might deepen understanding of this specific subject and
would not automatically emerge from a normal summary or retrieval query.

This is not a completeness checklist. It is the untaken direction.

Rules:
- Return at most {max_seeds} candidate directions.
- Each candidate contains exactly one angle, frame, relation, or dimension.
- Use the same language as the input text. Keep technical terms and proper
  names in their original form when translation would be uncertain.
- Name a DIRECTION to investigate, not a fact to accept as true.
  * Wrong claim: "Colonial trade financed the factories."
  * Good direction: "Colonial capital as an explanatory frame alongside
    technological innovation."
- Do NOT invent concrete facts, names, numbers, quotations, or sources. A new
  angle is allowed; an invented fact is not.
- Tie every candidate to the subject of THIS input text.
- The output is detector material for later review and starts with weight 0.
  Do not assign a seed, evidence, validation, promotion, or status label.
- Do not copy complete phrases from the input.
- Do not combine several frames or lists in one candidate.
- Do not return isolated words or acronyms without a relation.

The examples below come from OTHER texts and domains. They demonstrate form and
ambition only. Do not copy their content.

Bad form examples, do not copy:
{bad_examples}

Good form examples from other domains, do not copy:
{good_examples}

Input text:
{text}

Return at most {max_seeds} candidate directions about this input text. Start
directly with "1.".

Output:
1.
""".strip()


OPEN_SET_GENERATIVE_DETECTOR_ID = "ssl46_open_set_model_detector_v0.4-gen"
PROMPT_VARIANTS: tuple[str, ...] = ("absence", "generative")


def build_detection_prompt(text: str, max_seeds: int = 5, variant: str = "absence") -> str:
    """Build a constrained detector prompt for an absence or generative seed."""
    if variant not in PROMPT_VARIANTS:
        raise ValueError(f"Unknown prompt variant {variant!r}. Allowed: {PROMPT_VARIANTS}.")
    template = OPEN_SET_GENERATIVE_PROMPT if variant == "generative" else OPEN_SET_DETECTION_PROMPT
    good = _FEWSHOT_GOOD_GENERATIVE if variant == "generative" else _FEWSHOT_GOOD
    return template.format(
        text=text.strip(),
        max_seeds=max_seeds,
        bad_examples=_numbered(_FEWSHOT_BAD),
        good_examples=_numbered(good),
    )


class FixtureDetectorBackend:
    """Deterministic CI backend. Marks every seed with ``[FIXTURE]``."""

    name = "fixture"

    def __init__(self, prompt_variant: str = "absence") -> None:
        self.prompt_variant = prompt_variant

    def detect_seeds(self, item: dict[str, Any], max_seeds: int = 5) -> list[str]:
        text = str(item.get("text") or item.get("input") or "").strip()
        if not text:
            return []
        # take up to max_seeds distinct capitalized tokens from the text
        tokens: list[str] = []
        seen: set[str] = set()
        for token in re.findall(r"\b[A-ZÀ-Þ][a-zA-ZÀ-ÿ]{2,}\b", text):
            key = token.lower()
            if key in seen:
                continue
            seen.add(key)
            tokens.append(token)
            if len(tokens) >= max_seeds:
                break
        if self.prompt_variant == "generative":
            return [
                f"[FIXTURE] {token} as an explanatory frame for this text."
                for token in tokens
            ]
        return [
            f"[FIXTURE] Missing explanation of {token} in this text."
            for token in tokens
        ]


class HFTransformersDetectorBackend:
    """Local Hugging Face transformers backend for real language-model detection.

    Opt-in. Requires ``pip install -e '.[models]'`` and network access to
    download the model (or a pre-warmed HF cache). Default decoding is
    greedy and deterministic so the same input produces the same seeds.
    """

    def __init__(self, model_id: str, max_new_tokens: int = 400, prompt_variant: str = "absence") -> None:
        self.prompt_variant = prompt_variant
        try:
            import torch
            from transformers import AutoModelForCausalLM, AutoTokenizer, pipeline
        except ImportError as exc:  # pragma: no cover - optional dependency
            raise RuntimeError(
                "Install optional model dependencies first: "
                "pip install -e '.[models]' transformers torch"
            ) from exc

        self.name = f"hf-transformers:{model_id}"
        self.model_id = model_id
        self.max_new_tokens = max_new_tokens
        self.tokenizer = AutoTokenizer.from_pretrained(model_id)
        if torch.cuda.is_available():
            model_kwargs: dict[str, Any] = {"torch_dtype": torch.float16, "device_map": "auto"}
        else:
            # CPU: load the checkpoint's native (half) precision instead of
            # upcasting to float32. Halves memory — a 3.8B model loads in
            # ~8 GB instead of ~15 GB, which is what makes Phi-3.5-mini and
            # Qwen3-4B fit on the public-repo ubuntu-latest runner (16 GB).
            model_kwargs = {"torch_dtype": "auto"}
        model = AutoModelForCausalLM.from_pretrained(model_id, **model_kwargs)
        self.generator = pipeline(
            "text-generation",
            model=model,
            tokenizer=self.tokenizer,
            device=0 if torch.cuda.is_available() else -1,
        )

    def detect_seeds(self, item: dict[str, Any], max_seeds: int = 5) -> list[str]:
        text = str(item.get("text") or item.get("input") or "").strip()
        if not text:
            return []
        prompt = build_detection_prompt(text, max_seeds=max_seeds, variant=self.prompt_variant)
        output = self.generator(
            prompt,
            max_new_tokens=self.max_new_tokens,
            do_sample=False,
            return_full_text=False,
        )
        raw = output[0]["generated_text"]
        # the prompt ends with "1.\n" — re-prepend so the parser sees the first item
        return parse_numbered_seeds(
            "1. " + raw, max_seeds=max_seeds, source_text=text
        )


class OllamaDetectorBackend:
    """Detector backend backed by a local Ollama server over HTTP.

    Opt-in. Needs no Python model dependencies (stdlib only): install Ollama,
    run ``ollama pull <model_id>``, then point the run at it. Decoding is greedy
    (temperature 0, fixed seed) so the same input produces the same seeds.
    """

    def __init__(
        self,
        model_id: str,
        max_new_tokens: int = 400,
        host: str | None = None,
        prompt_variant: str = "absence",
    ) -> None:
        from shadowseed.adapters.ollama_client import OllamaClient

        self.prompt_variant = prompt_variant
        self.name = f"ollama:{model_id}"
        self.model_id = model_id
        self.max_new_tokens = max_new_tokens
        self.client = OllamaClient(model=model_id, host=host)

    def detect_seeds(self, item: dict[str, Any], max_seeds: int = 5) -> list[str]:
        text = str(item.get("text") or item.get("input") or "").strip()
        if not text:
            return []
        prompt = build_detection_prompt(text, max_seeds=max_seeds, variant=self.prompt_variant)
        raw = self.client.generate(prompt, max_new_tokens=self.max_new_tokens)
        # the prompt ends with "1.\n" — re-prepend so the parser sees the first item
        return parse_numbered_seeds(
            "1. " + raw, max_seeds=max_seeds, source_text=text
        )


class OpenAIDetectorBackend:
    """Detector backend backed by a hosted OpenAI chat model.

    Opt-in (needs the ``openai`` extra). The API key is read from
    ``OPENAI_API_KEY``. Decoding is greedy (temperature 0, fixed seed) so the
    same input produces the same seeds as far as the API allows.
    """

    def __init__(
        self,
        model_id: str,
        max_new_tokens: int = 400,
        prompt_variant: str = "absence",
    ) -> None:
        from shadowseed.adapters.openai_client import OpenAIClient

        self.prompt_variant = prompt_variant
        self.name = f"openai:{model_id}"
        self.model_id = model_id
        self.max_new_tokens = max_new_tokens
        self.client = OpenAIClient(model=model_id)

    def detect_seeds(self, item: dict[str, Any], max_seeds: int = 5) -> list[str]:
        text = str(item.get("text") or item.get("input") or "").strip()
        if not text:
            return []
        prompt = build_detection_prompt(text, max_seeds=max_seeds, variant=self.prompt_variant)
        raw = self.client.generate(prompt, max_new_tokens=self.max_new_tokens)
        # the prompt ends with "1.\n" — re-prepend so the parser sees the first item
        return parse_numbered_seeds(
            "1. " + raw, max_seeds=max_seeds, source_text=text
        )


SUPPORTED_MODEL_BACKENDS: tuple[str, ...] = ("fixture", "hf-transformers", "ollama", "openai")


def make_detector_backend(
    backend: str,
    model_id: str | None = None,
    max_new_tokens: int = 400,
    prompt_variant: str = "absence",
) -> DetectorBackend:
    if prompt_variant not in PROMPT_VARIANTS:
        raise ValueError(f"Unknown prompt variant {prompt_variant!r}. Allowed: {PROMPT_VARIANTS}.")
    if backend == "fixture":
        return FixtureDetectorBackend(prompt_variant=prompt_variant)
    if backend == "hf-transformers":
        if not model_id:
            raise ValueError(
                "--model-id is required for --model-backend hf-transformers"
            )
        return HFTransformersDetectorBackend(
            model_id=model_id, max_new_tokens=max_new_tokens, prompt_variant=prompt_variant
        )
    if backend == "ollama":
        if not model_id:
            raise ValueError(
                "--model-id is required for --model-backend ollama"
            )
        return OllamaDetectorBackend(
            model_id=model_id, max_new_tokens=max_new_tokens, prompt_variant=prompt_variant
        )
    if backend == "openai":
        if not model_id:
            raise ValueError(
                "--model-id is required for --model-backend openai"
            )
        return OpenAIDetectorBackend(
            model_id=model_id, max_new_tokens=max_new_tokens, prompt_variant=prompt_variant
        )
    raise ValueError(
        f"Unknown model backend {backend!r}. "
        f"Allowed: {SUPPORTED_MODEL_BACKENDS}."
    )

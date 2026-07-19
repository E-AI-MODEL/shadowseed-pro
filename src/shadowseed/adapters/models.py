"""Runtime text-generation backends used by chat and benchmarks."""

from __future__ import annotations

from typing import Protocol

class ModelBackend(Protocol):
    name: str

    def generate(self, prompt: str, scenario: dict, mode: str, ssl_seeds: list[str]) -> str:
        ...


class FixtureBackend:
    """Deterministic CI backend.

    It simulates a weak baseline and a model that follows SSL-guided revision
    instructions. This checks the harness mechanics without downloading a model.
    """

    name = "fixture"

    def generate(self, prompt: str, scenario: dict, mode: str, ssl_seeds: list[str]) -> str:
        if mode == "baseline":
            return scenario.get("baseline_answer", "")
        additions = " ".join(ssl_seeds)
        return f"{scenario.get('baseline_answer', '')}\n\nSSL-guided revision: {additions}".strip()


class HFTransformersBackend:
    """Local Hugging Face transformers backend.

    This is opt-in because model downloads can be slow and are not suitable for
    default CI. Recommended small model examples include TinyLlama-style instruct
    models or any local text-generation model available in the HF cache.
    """

    def __init__(self, model_id: str, max_new_tokens: int = 220) -> None:
        try:
            import torch
            from transformers import AutoModelForCausalLM, AutoTokenizer, pipeline
        except ImportError as exc:  # pragma: no cover - optional dependency
            raise RuntimeError(
                "Install optional model dependencies first: pip install -e '.[models]' transformers torch"
            ) from exc

        self.name = f"hf-transformers:{model_id}"
        self.model_id = model_id
        self.max_new_tokens = max_new_tokens
        self.tokenizer = AutoTokenizer.from_pretrained(model_id)
        if torch.cuda.is_available():
            model_kwargs = {"torch_dtype": torch.float16, "device_map": "auto"}
        else:
            # CPU: keep the checkpoint's native (half) precision instead of
            # upcasting to float32 — halves memory on CPU-only runners.
            model_kwargs = {"torch_dtype": "auto"}
        model = AutoModelForCausalLM.from_pretrained(model_id, **model_kwargs)
        self.generator = pipeline(
            "text-generation",
            model=model,
            tokenizer=self.tokenizer,
            device=0 if torch.cuda.is_available() else -1,
        )

    def generate(self, prompt: str, scenario: dict, mode: str, ssl_seeds: list[str]) -> str:
        output = self.generator(
            prompt,
            max_new_tokens=self.max_new_tokens,
            do_sample=False,
            return_full_text=False,
        )
        return output[0]["generated_text"].strip()


class OllamaBackend:
    """Local Ollama backend.

    Talks to a running Ollama server over HTTP instead of loading weights in
    process. This keeps real small-model runs lightweight enough for a standard
    CI runner: install Ollama, ``ollama pull`` a quantized model, then point the
    run at it. Decoding is greedy (temperature 0, fixed seed) for reproducibility.
    """

    def __init__(self, model_id: str, max_new_tokens: int = 220, host: str | None = None) -> None:
        from shadowseed.adapters.ollama_client import OllamaClient

        self.name = f"ollama:{model_id}"
        self.model_id = model_id
        self.max_new_tokens = max_new_tokens
        self.client = OllamaClient(model=model_id, host=host)

    def generate(self, prompt: str, scenario: dict, mode: str, ssl_seeds: list[str]) -> str:
        return self.client.generate(prompt, max_new_tokens=self.max_new_tokens)


class OpenAIBackend:
    """Hosted OpenAI backend.

    Calls a strong hosted chat model so the SSL-guided revision step is not
    bottlenecked on a weak local SLM. The API key is read from
    ``OPENAI_API_KEY`` (never passed as an argument). Decoding is greedy
    (temperature 0, fixed seed) for reproducibility. Opt-in: needs the
    ``openai`` extra.
    """

    def __init__(self, model_id: str, max_new_tokens: int = 220) -> None:
        from shadowseed.adapters.openai_client import OpenAIClient

        self.name = f"openai:{model_id}"
        self.model_id = model_id
        self.max_new_tokens = max_new_tokens
        self.client = OpenAIClient(model=model_id)

    def generate(self, prompt: str, scenario: dict, mode: str, ssl_seeds: list[str]) -> str:
        return self.client.generate(prompt, max_new_tokens=self.max_new_tokens)


def make_backend(backend: str, model_id: str | None, max_new_tokens: int) -> ModelBackend:
    if backend == "fixture":
        return FixtureBackend()
    if backend == "hf-transformers":
        if not model_id:
            raise ValueError("--model-id is required for backend hf-transformers")
        return HFTransformersBackend(model_id=model_id, max_new_tokens=max_new_tokens)
    if backend == "ollama":
        if not model_id:
            raise ValueError("--model-id is required for backend ollama")
        return OllamaBackend(model_id=model_id, max_new_tokens=max_new_tokens)
    if backend == "openai":
        if not model_id:
            raise ValueError("--model-id is required for backend openai")
        return OpenAIBackend(model_id=model_id, max_new_tokens=max_new_tokens)
    raise ValueError(f"Unknown backend: {backend}")


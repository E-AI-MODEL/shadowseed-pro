"""Runtime text-generation backends used by chat and benchmarks."""

from __future__ import annotations

from typing import Protocol


def chat_messages(
    history: list[tuple[str, str]],
    question: str,
) -> list[dict[str, str]]:
    """Build provider-native chat turns for a vanilla conversation."""

    messages: list[dict[str, str]] = []
    for user_text, assistant_text in history:
        messages.append({"role": "user", "content": str(user_text)})
        messages.append({"role": "assistant", "content": str(assistant_text)})
    messages.append({"role": "user", "content": str(question)})
    return messages


class ModelBackend(Protocol):
    name: str

    def generate(self, prompt: str, scenario: dict, mode: str, ssl_seeds: list[str]) -> str:
        ...

    def generate_chat(
        self,
        history: list[tuple[str, str]],
        question: str,
    ) -> str:
        """Generate one vanilla turn from role-structured conversation history."""
        ...

    def generate_messages(self, messages: list[dict[str, str]]) -> str:
        """Generate from an already prepared role-structured message sequence."""
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

    def generate_chat(
        self,
        history: list[tuple[str, str]],
        question: str,
    ) -> str:
        return f"Fixture echo answer to: {question}"

    def generate_messages(self, messages: list[dict[str, str]]) -> str:
        user_messages = [
            str(message.get("content", ""))
            for message in messages
            if message.get("role") == "user"
        ]
        current = user_messages[-1] if user_messages else ""
        open_marker = "<<<CANDIDATE_PERSPECTIVES data=untrusted>>>"
        close_marker = "<<<END_CANDIDATE_PERSPECTIVES>>>"
        question = current.split("\n\n" + open_marker, 1)[0]
        baseline = f"Fixture echo answer to: {question}"
        if open_marker not in current or close_marker not in current:
            return baseline
        candidate_block = current.split(open_marker, 1)[1].split(close_marker, 1)[0]
        candidates = []
        for line in candidate_block.splitlines():
            text = line.strip()
            if not text:
                continue
            if text.startswith("[") and "]" in text:
                text = text.split("]", 1)[1].strip()
            if text:
                candidates.append(text)
        if not candidates:
            return baseline
        return f"{baseline}\n\nSSL-guided revision: {' '.join(candidates)}"


class HFTransformersBackend:
    """Local Hugging Face transformers backend.

    This is opt-in because model downloads can be slow and are not suitable for
    default CI. Recommended small model examples include TinyLlama-style instruct
    models or any local text-generation model available in the HF cache.
    """

    def __init__(
        self,
        model_id: str,
        max_new_tokens: int = 220,
        revision: str | None = None,
    ) -> None:
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
        self.revision = revision
        tokenizer_kwargs = {"revision": revision} if revision is not None else {}
        self.tokenizer = AutoTokenizer.from_pretrained(model_id, **tokenizer_kwargs)
        if torch.cuda.is_available():
            model_kwargs = {"torch_dtype": torch.float16, "device_map": "auto"}
        else:
            # CPU: keep the checkpoint's native (half) precision instead of
            # upcasting to float32 — halves memory on CPU-only runners.
            model_kwargs = {"torch_dtype": "auto"}
        if revision is not None:
            model_kwargs["revision"] = revision
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

    @staticmethod
    def _fold_system_for_chat_template(
        messages: list[dict[str, str]],
    ) -> list[dict[str, str]]:
        """Fold system guidance into the first user turn for strict templates.

        Some supported Hugging Face instruct templates accept only user and
        assistant roles. Preserve the product contract without flattening the
        entire conversation when such a template rejects an explicit system role.
        """

        if not messages or messages[0].get("role") != "system":
            return [dict(message) for message in messages]

        system_content = str(messages[0].get("content", "")).strip()
        folded = [dict(message) for message in messages[1:]]
        if not folded:
            return [{"role": "user", "content": system_content}]
        if folded[0].get("role") == "user":
            user_content = str(folded[0].get("content", ""))
            folded[0] = {
                **folded[0],
                "content": (
                    f"{system_content}\n\nUSER MESSAGE:\n{user_content}"
                    if system_content
                    else user_content
                ),
            }
            return folded
        return [
            {"role": "user", "content": system_content},
            *folded,
        ]

    def generate_messages(self, messages: list[dict[str, str]]) -> str:
        chat_template = getattr(self.tokenizer, "apply_chat_template", None)
        if callable(chat_template):
            try:
                prompt = chat_template(
                    messages,
                    tokenize=False,
                    add_generation_prompt=True,
                )
            except Exception:
                prompt = chat_template(
                    self._fold_system_for_chat_template(messages),
                    tokenize=False,
                    add_generation_prompt=True,
                )
        else:
            prompt = "\n".join(
                f"{message['role'].capitalize()}: {message['content']}"
                for message in messages
            ) + "\nAssistant:"
        output = self.generator(
            prompt,
            max_new_tokens=self.max_new_tokens,
            do_sample=False,
            return_full_text=False,
        )
        return output[0]["generated_text"].strip()

    def generate_chat(
        self,
        history: list[tuple[str, str]],
        question: str,
    ) -> str:
        return self.generate_messages(chat_messages(history, question))


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

    def generate_messages(self, messages: list[dict[str, str]]) -> str:
        return self.client.generate_chat(
            messages,
            max_new_tokens=self.max_new_tokens,
        )

    def generate_chat(
        self,
        history: list[tuple[str, str]],
        question: str,
    ) -> str:
        return self.generate_messages(chat_messages(history, question))


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

    def generate_messages(self, messages: list[dict[str, str]]) -> str:
        return self.client.generate_chat(
            messages,
            max_new_tokens=self.max_new_tokens,
        )

    def generate_chat(
        self,
        history: list[tuple[str, str]],
        question: str,
    ) -> str:
        return self.generate_messages(chat_messages(history, question))


def make_backend(
    backend: str,
    model_id: str | None,
    max_new_tokens: int,
    model_revision: str | None = None,
) -> ModelBackend:
    if backend == "fixture":
        return FixtureBackend()
    if backend == "hf-transformers":
        if not model_id:
            raise ValueError("--model-id is required for backend hf-transformers")
        return HFTransformersBackend(
            model_id=model_id,
            max_new_tokens=max_new_tokens,
            revision=model_revision,
        )
    if backend == "ollama":
        if not model_id:
            raise ValueError("--model-id is required for backend ollama")
        return OllamaBackend(model_id=model_id, max_new_tokens=max_new_tokens)
    if backend == "openai":
        if not model_id:
            raise ValueError("--model-id is required for backend openai")
        return OpenAIBackend(model_id=model_id, max_new_tokens=max_new_tokens)
    raise ValueError(f"Unknown backend: {backend}")


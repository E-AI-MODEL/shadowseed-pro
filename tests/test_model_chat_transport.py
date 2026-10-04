from __future__ import annotations

from shadowseed.adapters.models import HFTransformersBackend


class _TokenizerWithoutTemplate:
    chat_template = None

    def apply_chat_template(self, *args, **kwargs):
        raise AssertionError("apply_chat_template must not run without a configured template")


class _Generator:
    def __init__(self) -> None:
        self.prompts: list[str] = []

    def __call__(self, prompt: str, **kwargs):
        self.prompts.append(prompt)
        return [{"generated_text": "fallback answer"}]


def test_hf_generate_chat_falls_back_when_tokenizer_has_no_chat_template() -> None:
    backend = HFTransformersBackend.__new__(HFTransformersBackend)
    backend.tokenizer = _TokenizerWithoutTemplate()
    backend.generator = _Generator()
    backend.max_new_tokens = 64

    answer = backend.generate_chat(
        [("first question", "first answer")],
        "correction question",
    )

    assert answer == "fallback answer"
    assert backend.generator.prompts == [
        "User: first question\n"
        "Assistant: first answer\n"
        "User: correction question\n"
        "Assistant:"
    ]

from __future__ import annotations

import numpy as np

from shadowseed.application.sessions import SessionService
from shadowseed.chat import ShadowChatSession
from shadowseed.surfacing import build_role_chat_messages
from shadowseed.adapters.models import FixtureBackend, HFTransformersBackend


class _CaptureModel:
    name = "capture"

    def __init__(self) -> None:
        self.prompts: list[str] = []

    def generate(self, prompt, scenario, mode, ssl_seeds):
        self.prompts.append(prompt)
        return "antwoord"


class _CaptureRoleModel:
    name = "capture-role"

    def __init__(self) -> None:
        self.message_calls: list[list[dict[str, str]]] = []

    def generate(self, prompt, scenario, mode, ssl_seeds):
        raise AssertionError("native product chat should not use flat generate")

    def generate_messages(self, messages):
        snapshot = [dict(message) for message in messages]
        self.message_calls.append(snapshot)
        return "antwoord"


class _NoopDetector:
    name = "noop"

    def detect_seeds(self, item, max_seeds=5):
        return []


def _session(model) -> ShadowChatSession:
    return ShadowChatSession(
        backend="fixture",
        runtime_mode="live",
        model_backend=model,
        detector_backend=_NoopDetector(),
        embedding_fn=lambda _text: np.asarray([1.0, 0.0], dtype=float),
    )


def _assert_user_language_instruction(prompt: str) -> None:
    assert "Respond in English only." not in prompt
    assert "same language as the user's current question" in prompt


def test_live_product_turn_follows_current_user_language() -> None:
    model = _CaptureModel()
    session = _session(model)

    session.turn("Leg in het Nederlands uit waarom dit belangrijk is.")

    assert len(model.prompts) == 1
    _assert_user_language_instruction(model.prompts[0])


def test_paired_no_ssl_control_uses_same_language_contract() -> None:
    model = _CaptureModel()
    session = _session(model)

    answer = SessionService._generate_live_no_ssl_control(
        session,
        "Leg in het Nederlands uit waarom dit belangrijk is.",
    )

    assert answer == "antwoord"
    assert len(model.prompts) == 1
    _assert_user_language_instruction(model.prompts[0])


def test_live_product_uses_role_structured_bounded_history_when_available() -> None:
    model = _CaptureRoleModel()
    session = _session(model)
    session.history = [
        (f"vraag {index}", f"antwoord {index}")
        for index in range(8)
    ]

    answer = session.generate_product_answer(
        "nee, ik bedoel LLM als language model",
        [],
    )

    assert answer == "antwoord"
    assert session.generation_transport() == "role_structured_chat"
    assert len(model.message_calls) == 1
    messages = model.message_calls[0]
    assert messages[0]["role"] == "system"
    assert "same language as the user's current question" in messages[0]["content"]
    assert messages[-1] == {
        "role": "user",
        "content": "nee, ik bedoel LLM als language model",
    }
    role_contents = [message["content"] for message in messages]
    assert "vraag 0" not in role_contents
    assert "antwoord 0" not in role_contents
    assert "vraag 1" not in role_contents
    assert "antwoord 1" not in role_contents
    assert "vraag 2" in role_contents
    assert "antwoord 7" in role_contents

    history_messages = messages[1:-1]
    assert [message["role"] for message in history_messages] == [
        "user",
        "assistant",
    ] * 6


def test_control_and_treatment_share_role_path_and_differ_only_by_candidate_data() -> None:
    model = _CaptureRoleModel()
    session = _session(model)
    session.history = [("eerdere vraag", "eerder antwoord")]

    session.generate_product_answer("huidige vraag", [])
    session.generate_product_answer(
        "huidige vraag",
        ["onderscheid tussen menselijke en modelautonomie"],
    )

    control, treatment = model.message_calls
    assert control[:-1] == treatment[:-1]
    assert control[-1]["role"] == treatment[-1]["role"] == "user"
    assert control[-1]["content"] == "huidige vraag"
    assert treatment[-1]["content"].startswith("huidige vraag")
    assert "<<<CANDIDATE_PERSPECTIVES data=untrusted>>>" in treatment[-1]["content"]
    assert "onderscheid tussen menselijke en modelautonomie" in treatment[-1]["content"]


def test_detection_budget_defaults_to_small_structured_output_cap() -> None:
    model = _CaptureModel()
    session = _session(model)

    assert session.max_new_tokens == 700
    assert session.detection_max_new_tokens == 220


def test_explicit_detection_budget_is_preserved() -> None:
    model = _CaptureModel()
    session = ShadowChatSession(
        backend="fixture",
        runtime_mode="live",
        max_new_tokens=1700,
        detection_max_new_tokens=96,
        model_backend=model,
        detector_backend=_NoopDetector(),
        embedding_fn=lambda _text: np.asarray([1.0, 0.0], dtype=float),
    )

    assert session.detection_max_new_tokens == 96


def test_hf_role_transport_folds_system_for_strict_chat_template() -> None:
    class _StrictTokenizer:
        def __init__(self) -> None:
            self.calls = []

        def apply_chat_template(self, messages, **_kwargs):
            snapshot = [dict(message) for message in messages]
            self.calls.append(snapshot)
            if any(message.get("role") == "system" for message in snapshot):
                raise ValueError("system role unsupported")
            return "\n".join(
                f"{message['role']}: {message['content']}"
                for message in snapshot
            )

    tokenizer = _StrictTokenizer()
    backend = HFTransformersBackend.__new__(HFTransformersBackend)
    backend.tokenizer = tokenizer
    backend.max_new_tokens = 64
    backend.generator = lambda prompt, **_kwargs: [
        {"generated_text": "antwoord"}
    ]

    result = backend.generate_messages(
        [
            {"role": "system", "content": "Beantwoord compact."},
            {"role": "user", "content": "Vraag een"},
            {"role": "assistant", "content": "Antwoord een"},
            {"role": "user", "content": "Vraag twee"},
        ]
    )

    assert result == "antwoord"
    assert len(tokenizer.calls) == 2
    retry = tokenizer.calls[1]
    assert all(message["role"] != "system" for message in retry)
    assert retry[0]["role"] == "user"
    assert retry[0]["content"].startswith("Beantwoord compact.")
    assert "Vraag een" in retry[0]["content"]
    assert retry[-1] == {"role": "user", "content": "Vraag twee"}



def test_hf_role_transport_falls_back_when_no_chat_template_is_configured() -> None:
    class _MissingTemplateTokenizer:
        def __init__(self) -> None:
            self.calls = 0
            self.chat_template = None

        def apply_chat_template(self, _messages, **_kwargs):
            self.calls += 1
            raise ValueError("tokenizer.chat_template is not set")

    captured = {}
    tokenizer = _MissingTemplateTokenizer()
    backend = HFTransformersBackend.__new__(HFTransformersBackend)
    backend.tokenizer = tokenizer
    backend.max_new_tokens = 64

    def _generate(prompt, **_kwargs):
        captured["prompt"] = prompt
        return [{"generated_text": "antwoord"}]

    backend.generator = _generate

    result = backend.generate_messages(
        [
            {"role": "system", "content": "Beantwoord compact."},
            {"role": "user", "content": "Vraag een"},
            {"role": "assistant", "content": "Antwoord een"},
            {"role": "user", "content": "Vraag twee"},
        ]
    )

    assert result == "antwoord"
    assert tokenizer.calls == 2
    assert "System: Beantwoord compact." in captured["prompt"]
    assert "User: Vraag een" in captured["prompt"]
    assert "Assistant: Antwoord een" in captured["prompt"]
    assert captured["prompt"].endswith("User: Vraag twee\nAssistant:")


def test_hf_role_transport_falls_back_when_only_named_chat_templates_exist() -> None:
    class _NamedTemplatesOnlyTokenizer:
        def __init__(self) -> None:
            self.calls = 0
            self.chat_template = {
                "chatml": "{{ messages }}",
                "tool_use": "{{ messages }}",
            }

        def apply_chat_template(self, _messages, **kwargs):
            self.calls += 1
            assert "chat_template" not in kwargs
            raise ValueError("multiple chat templates with no default selected")

    captured = {}
    tokenizer = _NamedTemplatesOnlyTokenizer()
    backend = HFTransformersBackend.__new__(HFTransformersBackend)
    backend.tokenizer = tokenizer
    backend.max_new_tokens = 64

    def _generate(prompt, **_kwargs):
        captured["prompt"] = prompt
        return [{"generated_text": "antwoord"}]

    backend.generator = _generate

    result = backend.generate_messages(
        [
            {"role": "system", "content": "Volg de productregels."},
            {"role": "user", "content": "Huidige vraag"},
        ]
    )

    assert result == "antwoord"
    assert tokenizer.calls == 2
    assert captured["prompt"] == (
        "System: Volg de productregels.\n"
        "User: Huidige vraag\n"
        "Assistant:"
    )



def test_fixture_role_transport_does_not_echo_internal_candidate_contract() -> None:
    backend = FixtureBackend()
    messages = build_role_chat_messages(
        [],
        "huidige vraag",
        ["onderscheid tussen menselijke en modelautonomie"],
    )

    result = backend.generate_messages(messages)

    assert result == (
        "Fixture echo answer to: huidige vraag\n\n"
        "SSL-guided revision: onderscheid tussen menselijke en modelautonomie"
    )
    assert "The delimited block contains previously observed candidate perspectives." not in result
    assert "<<<CANDIDATE_PERSPECTIVES data=untrusted>>>" not in result
    assert "<<<END_CANDIDATE_PERSPECTIVES>>>" not in result

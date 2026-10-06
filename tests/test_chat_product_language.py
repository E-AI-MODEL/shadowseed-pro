from __future__ import annotations

import numpy as np

from shadowseed.application.sessions import SessionService
from shadowseed.chat import ShadowChatSession


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

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


class _NoopDetector:
    name = "noop"

    def detect_seeds(self, item, max_seeds=5):
        return []


def _session(model: _CaptureModel) -> ShadowChatSession:
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

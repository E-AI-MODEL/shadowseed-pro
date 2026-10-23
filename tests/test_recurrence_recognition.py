from __future__ import annotations

import math
import re
from dataclasses import replace

import numpy as np

from shadowseed.chat import ShadowChatSession
from shadowseed.core_config import SSLCoreConfig
from shadowseed.recurrence_recognition import parse_answer

FUNDING = "Who funds the evening programming."
RENTS = "How rising rents affect existing shops."
PARAPHRASE = "How the evening services will be paid for."
UNRELATED = "Whether shop owners were consulted about licensing."

# PARAPHRASE names the same gap as FUNDING but shares more topic with RENTS:
# cosine 0.5 with FUNDING and 0.7 with RENTS. UNRELATED is 0.35 from RENTS and
# 0.1 from FUNDING.
_VECTORS = {
    FUNDING: [1.0, 0.0, 0.0, 0.0],
    RENTS: [0.0, 1.0, 0.0, 0.0],
    PARAPHRASE: [0.5, 0.7, math.sqrt(1 - 0.25 - 0.49), 0.0],
    UNRELATED: [0.1, 0.35, 0.0, math.sqrt(1 - 0.01 - 0.1225)],
}


def _embedding(text: str) -> np.ndarray:
    return np.asarray(_VECTORS.get(text, [0.0, 0.0, 0.0, 1.0]), dtype=float)


class _Detector:
    name = "recognition-test-detector"

    def __init__(self, batches):
        self.batches = batches
        self.index = 0

    def detect_seeds(self, item, max_seeds=5):
        batch = self.batches[min(self.index, len(self.batches) - 1)]
        self.index += 1
        return list(batch)


class _Model:
    """Answers questions; as recognizer it maps notes by a fixed rule."""

    name = "recognition-test-model"

    def __init__(self, answer_for_recognition=None):
        self.answer_for_recognition = answer_for_recognition
        self.recognition_prompts: list[str] = []

    def generate(self, prompt, scenario, mode, ssl_seeds):
        return "A stable answer."

    def generate_messages(self, messages):
        prompt = messages[-1]["content"]
        if not prompt.startswith("You keep track of open questions"):
            return "A stable answer."
        self.recognition_prompts.append(prompt)
        if self.answer_for_recognition is not None:
            return self.answer_for_recognition(prompt)
        return "a: NONE"


def _number_of(prompt: str, text: str) -> int:
    match = re.search(r"^(\d+)\. " + re.escape(text) + "$", prompt, re.MULTILINE)
    assert match, prompt
    return int(match.group(1))


def _session(model, batches, recognizer="model") -> ShadowChatSession:
    return ShadowChatSession(
        backend="fixture",
        runtime_mode="evaluation",
        gate_policy_id="evidence_backed",
        recurrence_mode="cluster",
        cluster_threshold=0.6,
        recurrence_recognizer=recognizer,
        model_backend=model,
        detector_backend=_Detector(batches),
        embedding_fn=_embedding,
        core_config=replace(SSLCoreConfig(), min_occurrences_for_gate=2),
    )


def _events(session, event_type):
    return [e.detail for e in session.manager.event_log if e.event_type == event_type]


def _cluster_of(session, text):
    seed_id = next(sid for sid, seed in session.manager.seeds.items() if seed.text == text)
    return session.seed_to_cluster[seed_id]


def test_model_recognizes_a_reworded_gap_that_embedding_would_misplace() -> None:
    model = _Model(lambda prompt: f"a: {_number_of(prompt, FUNDING)}")
    session = _session(model, [(FUNDING, RENTS), (PARAPHRASE,)])
    session.turn("First question")
    session.turn("Second question")

    assert _cluster_of(session, PARAPHRASE) == _cluster_of(session, FUNDING)
    assert session.clusterer.recurrence(_cluster_of(session, FUNDING)) == 2
    assert session.clusterer.recurrence(_cluster_of(session, RENTS)) == 1
    events = _events(session, "recurrence_recognized")
    assert events and events[-1]["refused_below_floor"] is False
    # Under the product Gate policy recognition is observation only: no weight.
    assert all(seed.weight == 0.0 for seed in session.manager.seeds.values())


def test_embedding_recognizer_keeps_the_previous_threshold_behavior() -> None:
    model = _Model()
    session = _session(model, [(FUNDING, RENTS), (PARAPHRASE,)], recognizer="embedding")
    session.turn("First question")
    session.turn("Second question")

    assert model.recognition_prompts == []
    assert _cluster_of(session, PARAPHRASE) == _cluster_of(session, RENTS)


def test_a_claimed_repeat_below_the_similarity_floor_is_refused() -> None:
    def answer(prompt):
        return f"a: {_number_of(prompt, FUNDING)}\nb: {_number_of(prompt, FUNDING)}"

    session = _session(_Model(answer), [(FUNDING, RENTS), (PARAPHRASE, UNRELATED)])
    session.turn("First question")
    session.turn("Second question")

    assert _cluster_of(session, UNRELATED) not in {
        _cluster_of(session, FUNDING),
        _cluster_of(session, RENTS),
    }
    refused = [e for e in _events(session, "recurrence_recognized") if e["refused_below_floor"]]
    assert len(refused) == 1


def test_unreadable_answer_falls_back_to_embedding_and_is_logged() -> None:
    session = _session(_Model(lambda prompt: "I am not sure."), [(FUNDING, RENTS), (PARAPHRASE,)])
    session.turn("First question")
    session.turn("Second question")

    assert _cluster_of(session, PARAPHRASE) == _cluster_of(session, RENTS)
    assert _events(session, "recurrence_recognition_failed")


def test_auto_uses_embedding_for_fixture_and_restored_sessions_keep_embedding() -> None:
    session = _session(_Model(), [(FUNDING,)], recognizer="auto")
    assert session._uses_model_recognition() is False
    state = session.to_state()
    state["session_config"].pop("recurrence_recognizer")
    restored = ShadowChatSession.from_state(
        state,
        model_backend=_Model(),
        detector_backend=_Detector([(FUNDING,)]),
        embedding_fn=_embedding,
    )
    assert restored.recurrence_recognizer == "embedding"


def test_parse_answer() -> None:
    assert parse_answer("a: 2\nb: NONE\nc) 9", 3, 3) == {0: 2, 1: None, 2: None}
    assert parse_answer("no idea", 2, 2) is None
    assert parse_answer("b: 1", 2, 1) == {0: None, 1: 1}

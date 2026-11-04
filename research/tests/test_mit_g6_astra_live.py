"""Strictly offline contract tests for the one-shot Astra research pilot."""
import importlib.util
import json
import sys
from pathlib import Path

import pytest

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))
spec = importlib.util.spec_from_file_location("mit_g6_astra_live", SCRIPTS / "mit_g6_astra_live.py")
pilot = importlib.util.module_from_spec(spec)
spec.loader.exec_module(pilot)


class FakeProvider:
    def __init__(self):
        self.calls = 0
        self.embeds = 0
        self.tokens = 0
        self.events = []
        self.messages = []

    def complete(self, stage, messages, **kwargs):
        self.calls += 1
        self.messages.append((stage, messages))
        return json.dumps({
            "question": "What changes under time alignment?",
            "experiment": "Compare predeclared timestamp alignment conditions.",
            "expected_result": "One explanation predicts a specific difference.",
        })


def test_model_and_hard_limits_are_pinned():
    assert pilot.MODEL == "gpt-6-astra"
    assert pilot.MAX_CALLS == 12
    assert pilot.MAX_EMBEDS <= 8
    assert pilot.MAX_TOKENS <= 52000


def test_five_arm_run_separates_seed_and_sham(monkeypatch):
    monkeypatch.setattr(pilot, "first_birth", lambda p: (
        "First answer", "Do sensors sample different locations?", {"status": "canonical_birth"}
    ))
    fake = FakeProvider()
    result = pilot.run(fake)
    assert result["status"] == "completed"
    assert set(result["arms"]) == set("ABCDE")
    assert fake.calls == 10
    assert all(len(results) == 2 for results in result["arms"].values())
    by_stage = {stage: json.dumps(messages) for stage, messages in fake.messages}
    assert "Do sensors sample different locations?" in by_stage["D_T1"]
    assert all("Do sensors sample different locations?" not in by_stage[a + "_T1"]
               for a in "ABCE")
    assert "A neutral note" in by_stage["E_T1"]
    assert "A neutral note" not in by_stage["D_T1"]
    assert result["G0"] == "NOT_PASSED"
    assert result["confirmatory"] is False


def test_no_canonical_birth_refuses_treatment(monkeypatch):
    monkeypatch.setattr(pilot, "first_birth", lambda p: ("answer", None, {"status": "no_seed"}))
    result = pilot.run(FakeProvider())
    assert result["status"] == "no_seed"
    assert result["arms"] == {}


def test_bad_reply_is_not_a_success(monkeypatch):
    monkeypatch.setattr(pilot, "first_birth", lambda p: (
        "answer", "uncertain candidate", {"status": "canonical_birth"}
    ))
    class Bad(FakeProvider):
        def complete(self, stage, messages, **kwargs):
            self.calls += 1
            return "NONE"
    result = pilot.run(Bad())
    assert result["status"] == "incomplete"
    assert all(len(rows) == 1 for rows in result["arms"].values())


def test_mismatched_provider_identity_fails_without_retry(monkeypatch):
    class Transport:
        def __call__(self):
            return None

    p = pilot.Provider("test-key")
    def bogus(endpoint, payload):
        return {"model": "gpt-5", "usage": {"input_tokens": 4, "output_tokens": 6},
                "status": "completed", "output": []}
    monkeypatch.setattr(p, "send", bogus)
    with pytest.raises(RuntimeError, match="Model identity"):
        p.complete("test", [{"role": "user", "content": "hello"}])
    assert p.calls == 1


def test_capped_calls_do_not_invoke_provider(monkeypatch):
    p = pilot.Provider("test-key")
    p.calls = pilot.MAX_CALLS
    def forbidden(*args):
        raise AssertionError("unexpected provider access")
    monkeypatch.setattr(p, "send", forbidden)
    with pytest.raises(RuntimeError, match="limit reached"):
        p.complete("test", [{"role": "user", "content": "hello"}])

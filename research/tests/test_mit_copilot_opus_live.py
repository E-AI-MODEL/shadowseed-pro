"""Offline contract tests for the bounded Copilot Opus five-arm study."""
import json
import sys
from pathlib import Path
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import mit_copilot_opus_live as pilot


def fake_birth(provider):
    return "Host records uncertainty.", (
        "Whether asymmetric sampling positions explain intermittent sensor spikes."
    ), {"checkpoint": {"schema": "test-only"}}


def fake_answer(prompt):
    return json.dumps({
        "question": "Can channel swapping distinguish timing errors from sensor faults?",
        "experiment": "Swap sensors and compare separately logged readings.",
        "expected_result": "A pattern follows a physical sensor or a controller channel.",
    })


def test_fixed_strong_model_and_bounded_calls():
    assert pilot.MODEL == "claude-opus-5.5"
    assert pilot.MAX_REQUESTS == 12
    p = pilot.Provider(complete_fn=fake_answer)
    p.attempts = pilot.MAX_REQUESTS
    with pytest.raises(RuntimeError, match="call cap"):
        p.ask(stage="test", prompt="a")


def test_word_unit_sham_is_distinct_not_semantically_certified():
    for text in ("One important question.", "Whether independent timing offsets matter here."):
        fake = pilot.matched_sham(text)
        assert fake != text
        assert len(fake.split()) == len(text.split())


def test_two_real_arm_stages_with_shared_feedback(monkeypatch):
    monkeypatch.setattr(pilot, "canonical_birth", fake_birth)
    p = pilot.Provider(complete_fn=fake_answer)
    result = pilot.run_study(p)
    assert result["status"] == "completed_exploratory"
    assert p.attempts == 10
    assert result["G0"] == "NOT_PASSED"
    assert result["scientific_effect_established"] is False
    assert result["embedding_mode"] == "lexical_TOY_research_only"
    assert set(result["arm_results"]) == set("ABCDE")
    for arm in "ABCDE":
        events = result["arm_results"][arm]
        assert [e["stage"] for e in events] == ["T1", "T3"]
        assert all(e["status"] == "parsed" for e in events)
        assert pilot.SCENARIO["feedback"] not in events[0]["request_text"]
        assert pilot.SCENARIO["feedback"] in events[1]["request_text"]
    assert result["candidate_text"] in result["arm_results"]["D"][0]["request_text"]
    assert result["candidate_text"] not in result["arm_results"]["E"][0]["request_text"]
    assert result["sham_text"] in result["arm_results"]["E"][0]["request_text"]
    for arm in "ABC":
        assert result["candidate_text"] not in result["arm_results"][arm][0]["request_text"]


def test_no_seed_stops_without_arm_inference(monkeypatch):
    monkeypatch.setattr(pilot, "canonical_birth", lambda p: (
        "Host response", None, {"status": "no_seed"}
    ))
    p = pilot.Provider(complete_fn=fake_answer)
    result = pilot.run_study(p)
    assert result["status"] == "no_canonical_birth"
    assert result["arm_results"] == {}
    assert p.attempts == 0


def test_invalid_model_format_is_not_a_negative_shadowseed_result(monkeypatch):
    monkeypatch.setattr(pilot, "canonical_birth", fake_birth)
    p = pilot.Provider(complete_fn=lambda prompt: "NONE")
    result = pilot.run_study(p)
    assert result["status"] == "incomplete_unscorable"
    assert p.attempts == 5
    assert all(row[0]["status"] == "unscorable_format"
               for row in result["arm_results"].values())


def test_failed_provider_is_explicitly_recorded(monkeypatch):
    monkeypatch.setattr(pilot, "canonical_birth", fake_birth)
    def no_auth(_):
        raise RuntimeError("simulated denial")
    p = pilot.Provider(complete_fn=no_auth)
    result = pilot.run_study(p)
    assert result["status"] == "incomplete_unscorable"
    assert len(p.events) == 5
    assert all(e["status"] == "failed" for e in p.events)
    assert all(e[0]["status"] == "provider_error" for e in result["arm_results"].values())

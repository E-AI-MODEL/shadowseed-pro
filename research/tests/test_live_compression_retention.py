"""No-network checks for the gated GPT-5 research feasibility job.

These tests check code mechanics, stage separation and authority boundaries.
They DO NOT validate a scientific effect or replace independent human review.
"""

from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path

import numpy as np
import pytest

from shadowseed_research.benchmark.live_compression_retention import (
    ARMS, MAX_MODEL_CALLS, Provider, _json, _memory_list, _initial_prompt,
    _later_prompt, _preupdate_prompt, run, validate_cases,
)


FIXTURE = Path("research/fixtures/live_compression_exploratory_v0.json")


def cases():
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


def test_t0_prompts_do_not_disclose_later_evidence_or_oracle_labels():
    document = cases()
    assert len(validate_cases(document)) == 3
    for case in document["items"]:
        prompts = [_initial_prompt(case)] + [
            _preupdate_prompt(case, "Temporary answer", stage)
            for stage in ("candidates", "notes", "summary")
        ]
        for prompt in prompts:
            assert case["late_event"] not in prompt
            assert case["followup_question"] not in prompt
            assert '"target_terms"' not in prompt
        assert case["late_event"] in _later_prompt(
            case, {"summary": "An earlier answer.", "draft": "Earlier answer"},
            "compressed_only", [],
        )


def test_strict_json_and_memory_contract():
    assert _json('{"summary":"yes"}') == {"summary": "yes"}
    assert _json('garbage {"summary":"yes"}') == {}
    assert _json('["x"]') == {}
    assert _memory_list({"notes": ["first note here", "second note here"]}, "notes") == [
        "first note here", "second note here",
    ]
    assert _memory_list({"notes": ["one"]}, "notes") == []
    assert _memory_list({"notes": ["one", 0]}, "notes") == []


def test_fixture_validation_catches_leak_prone_mistakes():
    data = cases()
    bad = copy.deepcopy(data)
    bad["items"][1]["id"] = bad["items"][0]["id"]
    with pytest.raises(ValueError, match="unique"):
        validate_cases(bad)
    bad = copy.deepcopy(data)
    bad["items"][2]["target_terms"] = ["customs"]
    with pytest.raises(ValueError, match="negative"):
        validate_cases(bad)
    bad = copy.deepcopy(data)
    bad["items"][0]["late_event"] = "x"
    with pytest.raises(ValueError, match="late_event"):
        validate_cases(bad)


class FakeProvider:
    """Inject known output without secrets, network, hosted embeddings or tokens."""

    def __init__(self, *, bad_compression_case: str | None = None):
        self.model_calls = 0
        self.embedding_calls = 0
        self.token_count = 0
        self.events: list[dict] = []
        self.prompts: list[tuple[str, str, str]] = []
        self.bad_compression_case = bad_compression_case

    def generate(self, stage: str, case_id: str, prompt: str) -> dict:
        self.model_calls += 1
        self.prompts.append((case_id, stage, prompt))
        if stage == "T0_draft":
            value = {"answer": "The familiar explanation is still provisional."}
        elif stage == "T0_candidates":
            value = {"candidates": [
                "A shared electrical power supply might distort these measurements.",
                "Hidden operational timing constraints may alter the observations.",
            ]}
        elif stage == "T0_notes":
            value = {"notes": [
                "Review the agreed reporting procedure and latest logs.",
                "Compare current observations with the previous schedule.",
            ]}
        elif stage == "T0_compression":
            if case_id == self.bad_compression_case:
                text = '{"bad":"missing required summary"}'
            else:
                value = {"summary": "A preliminary explanation remains unverified."}
                text = json.dumps(value)
        else:
            assert stage.startswith("T2_")
            value = {
                "answer": "Further independent evidence is needed.",
                "next_question": "Which intervention would distinguish the explanations?",
                "uncertainty": "The available observations are limited.",
            }
        if stage != "T0_compression" or case_id != self.bad_compression_case:
            text = json.dumps(value)
        self.token_count += 20
        event = {
            "stage": stage, "case": case_id, "model": "fake-offline",
            "status": "completed", "usage": {"input_tokens": 12, "output_tokens": 8},
            "text": text, "parsed_json": bool(_json(text)),
        }
        self.events.append(event)
        return event

    def embed(self, case_id: str, texts: list[str]) -> dict[str, np.ndarray]:
        self.embedding_calls += 1
        vectors = {}
        for text in texts:
            digest = hashlib.sha256(text.encode("utf-8")).digest()
            vec = np.array([float(x) + 1.0 for x in digest], dtype=float)
            vectors[text] = vec / np.linalg.norm(vec)
        return vectors


def test_offline_simulation_runs_all_three_cases_without_authority(tmp_path: Path):
    fake = FakeProvider()
    report = run(cases(), provider=fake, out_dir=tmp_path, fixture_sha="local-test")
    assert report["status"] == "completed_exploratory_not_efficacy"
    assert report["usage"]["model_calls"] == 30
    assert report["usage"]["embedding_calls"] == 3
    assert len(report["t0"]) == len(report["t2"]) == 3
    assert (tmp_path / "frozen-t0.json").is_file()
    assert (tmp_path / "result.json").is_file()
    for case, frozen in zip(cases()["items"], report["t0"]):
        assert frozen["candidate_valid"] is True
        assert frozen["notes_valid"] is True
        assert frozen["compression_valid"] is True
        assert len(frozen["candidate_sha256"]) == 64
        for cid, stage, prompt in fake.prompts:
            if cid == case["id"] and stage.startswith("T0"):
                assert case["late_event"] not in prompt
    for case in report["t2"]:
        assert set(case["arms"]) == set(ARMS)
        assert case["gate_events"] == 0
        assert case["candidate_weightless"] is True
        assert len(case["canonical_seed_ids"]) == 2
        assert len(case["arms"]) == 6
        assert all(v["parsed_json"] for v in case["arms"].values())
    assert report["t2"][2]["no_opportunity"] is True
    assert report["t2"][2]["arms"]["compressed_only"]["exploratory_surface_metric"] == {
        "negative_context_intrusions": [],
    }


def test_invalid_compression_does_not_become_a_fake_compressed_arm(tmp_path: Path):
    provider = FakeProvider(bad_compression_case="ATTENDANCE")
    report = run(cases(), provider=provider, out_dir=tmp_path,
                 fixture_sha="deliberately-bad")
    assert report["status"] == "partial_invalid_compression"
    assert report["t2"][1]["status"] == "skipped_invalid_compression"
    assert report["t0"][1]["compression_valid"] is False
    assert report["usage"]["model_calls"] == 24
    assert report["usage"]["embedding_calls"] == 2


def test_provider_fails_closed_before_paid_call_at_hard_limit():
    provider = Provider("dummy-never-send")
    provider.model_calls = MAX_MODEL_CALLS
    with pytest.raises(RuntimeError, match="model call cap reached"):
        provider.generate("test", "MOCK", "some prompt")
    assert provider.events == []

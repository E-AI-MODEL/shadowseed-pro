"""Contract tests for measuring the actual live chat runtime."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pytest

from shadowseed.benchmark import live_session_measurement as live_measurement
from shadowseed.benchmark.ssl_session_suite import run_ssl_session
from shadowseed.chat import ShadowChatSession
from shadowseed.cli import build_parser


class _Model:
    name = "fake-real-model"

    def __init__(self) -> None:
        self.calls = 0

    def generate(self, prompt, scenario, mode, seeds):
        self.calls += 1
        return "A visible answer whose gap detector runs after generation."


class _Detector:
    name = "fake-real-detector"

    def __init__(self) -> None:
        self.calls = 0

    def detect_seeds(self, item, max_seeds=5):
        self.calls += 1
        return ["Recurring causal mechanism omitted from the answer."]


def _semantic_embedder(backend, model_id=None, **kwargs):
    seed_vector = np.array([1.0, 0.0])
    question_vector = np.array([0.35, np.sqrt(1.0 - 0.35**2)])

    def embed(text: str) -> np.ndarray:
        if "Recurring causal mechanism" in text:
            return seed_vector.copy()
        return question_vector.copy()

    return embed, 2


def _suite(tmp_path: Path, *, turns: int = 9) -> Path:
    path = tmp_path / "suite.json"
    path.write_text(
        json.dumps(
            {
                "version": "test",
                "conversations": [
                    {
                        "id": "live-conversation",
                        "domain": "test",
                        "turns": [
                            {"question": f"Does the mechanism apply in case {index}?"}
                            for index in range(turns)
                        ],
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    return path


def test_live_measurement_runs_real_session_arms_and_scores_deferral(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    model = _Model()
    detector = _Detector()
    monkeypatch.setattr(live_measurement, "make_backend", lambda **kwargs: model)
    monkeypatch.setattr(
        live_measurement,
        "make_detector_backend",
        lambda *args, **kwargs: detector,
    )
    monkeypatch.setattr(live_measurement, "make_embedding_fn", _semantic_embedder)

    output = tmp_path / "live.json"
    run_ssl_session(
        str(_suite(tmp_path)),
        str(output),
        backend="openai",
        model_id="fake",
        embedding_backend="sentence-transformers",
        runtime_mode="live",
        live_arms="both",
    )
    payload = json.loads(output.read_text(encoding="utf-8"))
    arms = {arm["arm_id"]: arm for arm in payload["arms"]}

    assert payload["summary"]["artifact"] == "ssl_live_session_measurement"
    assert payload["summary"]["runtime_mode"] == "live"
    assert payload["summary"]["model_id"] == "fake"
    assert (
        payload["summary"]["embedding_model"]
        == "sentence-transformers/all-MiniLM-L6-v2"
    )
    assert payload["summary"]["detector_prompt_variant"] == "generative"
    assert len(payload["summary"]["input_sha256"]) == 64
    assert payload["summary"]["source_revision"]
    assert "elapsed_seconds" not in payload["summary"]
    assert set(payload["summary"]["timing"]) == {
        "adapter_setup_elapsed_seconds",
        "live_turn_elapsed_seconds",
        "deferral_scoring_elapsed_seconds",
        "measurement_wall_elapsed_seconds",
    }
    assert payload["summary"]["answer_generation_calls"] == 18
    assert payload["summary"]["detector_calls"] == 18
    assert model.calls == 18
    assert detector.calls == 18

    evidence = arms["evidence-backed"]
    assert evidence["production_policy"] is True
    assert evidence["external_evidence_injected"] is False
    assert evidence["promoted_seed_count"] == 0
    assert evidence["influence_record_count"] == 0
    assert "elapsed_seconds" not in evidence
    assert evidence["timing"]["live_turn_elapsed_seconds"] >= 0
    assert evidence["timing"]["deferral_scoring_elapsed_seconds"] >= 0

    counterfactual = arms["counterfactual"]
    assert counterfactual["production_policy"] is False
    assert counterfactual["promoted_seed_count"] == 1
    assert counterfactual["influence_record_count"] >= 1
    costs = counterfactual["deferral_metrics"]
    assert costs["suppressed_candidate_occurrences"] >= 1
    assert costs["normalization_admissible_occurrences"] >= 1
    assert costs["later_recovered_occurrences"] >= 1
    assert costs["later_recovery_rate"] > 0
    assert "truth or usefulness" in costs["interpretation"]

    conversation = counterfactual["conversations"][0]
    assert all(turn["runtime_mode"] == "live" for turn in conversation["turns"])
    assert conversation["audit_records_verified"] == counterfactual["influence_record_count"]
    assert any(
        turn["suppressed_self_attributed_candidates"]
        for turn in conversation["turns"]
    )
    assert conversation["timing"]["live_turn_elapsed_seconds"] >= 0
    assert conversation["timing"]["deferral_scoring_elapsed_seconds"] >= 0


def test_live_measurement_reuses_expensive_adapters_across_conversations(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    data = json.loads(_suite(tmp_path, turns=1).read_text(encoding="utf-8"))
    data["conversations"].append(
        {"id": "second", "turns": [{"question": "A separate conversation?"}]}
    )
    suite = tmp_path / "two.json"
    suite.write_text(json.dumps(data), encoding="utf-8")
    calls = {"model": 0, "detector": 0, "embedding": 0}

    def model_factory(**kwargs):
        calls["model"] += 1
        return _Model()

    def detector_factory(*args, **kwargs):
        calls["detector"] += 1
        return _Detector()

    def embedding_factory(*args, **kwargs):
        calls["embedding"] += 1
        return _semantic_embedder(*args, **kwargs)

    monkeypatch.setattr(live_measurement, "make_backend", model_factory)
    monkeypatch.setattr(live_measurement, "make_detector_backend", detector_factory)
    monkeypatch.setattr(live_measurement, "make_embedding_fn", embedding_factory)

    run_ssl_session(
        str(suite),
        str(tmp_path / "out.json"),
        backend="openai",
        model_id="fake",
        embedding_backend="sentence-transformers",
        runtime_mode="live",
        live_arms="both",
    )

    assert calls == {"model": 1, "detector": 1, "embedding": 1}


def test_live_session_preserves_explicit_zero_cluster_threshold() -> None:
    embed, _dimension = _semantic_embedder("sentence-transformers")
    session = ShadowChatSession(
        backend="fixture",
        embedding_backend="sentence-transformers",
        runtime_mode="live",
        recurrence_mode="cluster",
        cluster_threshold=0.0,
        model_backend=_Model(),
        detector_backend=_Detector(),
        embedding_fn=embed,
    )

    assert session.clusterer is not None
    assert session.clusterer.threshold == 0.0


def test_live_measurement_rejects_fixture_and_toy_embeddings(tmp_path: Path) -> None:
    suite = _suite(tmp_path, turns=1)
    with pytest.raises(ValueError, match="requires a real model backend"):
        run_ssl_session(
            str(suite),
            str(tmp_path / "fixture.json"),
            backend="fixture",
            runtime_mode="live",
        )
    with pytest.raises(ValueError, match="requires sentence-transformers or openai"):
        run_ssl_session(
            str(suite),
            str(tmp_path / "lexical.json"),
            backend="openai",
            model_id="fake",
            runtime_mode="live",
        )


def test_live_measurement_cli_exposes_runtime_arms_and_semantic_embedder() -> None:
    args = build_parser().parse_args(
        [
            "run-ssl-session",
            "--runtime-mode",
            "live",
            "--live-arms",
            "counterfactual",
            "--embedding-backend",
            "sentence-transformers",
        ]
    )

    assert args.runtime_mode == "live"
    assert args.live_arms == "counterfactual"
    assert args.embedding_backend == "sentence-transformers"
    assert args.recurrence_mode is None


@pytest.mark.parametrize(
    "payload, match",
    [
        ({"conversations": []}, "at least one conversation"),
        ({"conversations": [{"id": "empty", "turns": []}]}, "at least one turn"),
        (
            {"conversations": [{"id": "bad", "turns": [{"question": ""}]}]},
            "non-empty question",
        ),
    ],
)
def test_live_measurement_rejects_behaviorally_empty_suites(
    tmp_path: Path,
    payload: dict,
    match: str,
) -> None:
    suite = tmp_path / "empty.json"
    suite.write_text(json.dumps(payload), encoding="utf-8")

    with pytest.raises(ValueError, match=match):
        run_ssl_session(
            str(suite),
            str(tmp_path / "out.json"),
            backend="openai",
            model_id="fake",
            embedding_backend="sentence-transformers",
            runtime_mode="live",
        )

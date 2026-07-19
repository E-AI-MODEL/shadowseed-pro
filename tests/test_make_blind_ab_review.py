"""Tests for the SSL session blind A/B review pack generator."""
from __future__ import annotations

import hashlib
import importlib.util
import json

import pytest

_spec = importlib.util.spec_from_file_location("blind_ab", "scripts/make_blind_ab_review.py")
assert _spec and _spec.loader
blind_ab = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(blind_ab)


def _payload(count: int):
    return {
        "summary": {"cross_turn_payoff_events": count},
        "conversations": [
            {
                "conversation_id": "C",
                "domain": "test",
                "turns": [
                    {
                        "turn": i,
                        "is_cross_turn_payoff": True,
                        "question": f"Q{i}?",
                        "baseline_answer": f"baseline {i}.",
                        "ssl_answer": f"ssl {i}.",
                        "surfaced_cross_turn_seeds": [f"seed {i}"],
                    }
                    for i in range(count)
                ],
            }
        ],
    }


def test_seed_45_assignment_is_balanced_for_small_odd_pack():
    _, answer_key = blind_ab.build_review_pack(_payload(9), seed=45)
    ssl_as_a = sum(1 for key in answer_key if key["ssl_answer_key"] == "A")
    ssl_as_b = sum(1 for key in answer_key if key["ssl_answer_key"] == "B")

    assert len(answer_key) == 9
    assert abs(ssl_as_a - ssl_as_b) == 1
    assert {key["ssl_answer_key"] for key in answer_key} == {"A", "B"}


def test_even_pack_splits_ssl_answers_equally():
    _, answer_key = blind_ab.build_review_pack(_payload(10), seed=45)
    ssl_as_a = sum(1 for key in answer_key if key["ssl_answer_key"] == "A")
    ssl_as_b = sum(1 for key in answer_key if key["ssl_answer_key"] == "B")

    assert ssl_as_a == 5
    assert ssl_as_b == 5


def test_review_pack_carries_answer_hashes_and_truncation_diagnostics():
    review_items, answer_key = blind_ab.build_review_pack(_payload(2), seed=45)

    assert review_items[0]["schema_version"] == blind_ab.SCHEMA_VERSION
    assert "answer_diagnostics" in review_items[0]
    assert "answer_A_sha256" in answer_key[0]
    assert "answer_B_sha256" in answer_key[0]
    assert review_items[0]["answer_diagnostics"]["A"]["likely_truncated"] is False


def test_summary_hashes_written_artifact_bytes(tmp_path):
    payload = _payload(2)
    input_path = tmp_path / "ssl_session_suite.json"
    input_path.write_text(json.dumps(payload), encoding="utf-8")
    review_items, answer_key = blind_ab.build_review_pack(payload, seed=45)
    review_items_path = tmp_path / "ssl_session_blind_ab_review_items.json"
    answer_key_path = tmp_path / "ssl_session_blind_ab_answer_key.json"
    summary_path = tmp_path / "ssl_session_blind_ab_summary.json"

    blind_ab.write_json(review_items_path, review_items)
    blind_ab.write_json(answer_key_path, answer_key)
    blind_ab.write_summary(
        summary_path,
        payload,
        review_items,
        answer_key,
        input_path=input_path,
        review_items_path=review_items_path,
        answer_key_path=answer_key_path,
        seed=45,
        prefix="ssl_session_blind_ab",
    )

    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    review_items_sha = hashlib.sha256(review_items_path.read_bytes()).hexdigest()
    answer_key_sha = hashlib.sha256(answer_key_path.read_bytes()).hexdigest()

    assert summary["schema_version"] == blind_ab.SCHEMA_VERSION
    assert summary["shuffle_seed"] == 45
    assert summary["integrity"]["answer_key_is_canonical"] is True
    assert summary["integrity"]["hash_basis"] == "actual UTF-8 artifact bytes as written to disk"
    assert summary["integrity"]["review_items_sha256"] == review_items_sha
    assert summary["integrity"]["answer_key_sha256"] == answer_key_sha


@pytest.mark.parametrize("bad_prefix", ["round_024/ssl_session", "../ssl_session", "/tmp/ssl_session", "..", ".hidden"])
def test_prefix_rejects_paths_and_hidden_relative_names(bad_prefix):
    with pytest.raises(ValueError):
        blind_ab._safe_prefix(bad_prefix)


def test_prefix_accepts_plain_filename_prefix():
    assert blind_ab._safe_prefix("round024_ssl_session") == "round024_ssl_session"

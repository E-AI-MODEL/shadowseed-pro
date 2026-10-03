from __future__ import annotations

import pytest

from shadowseed_webapi.service import WebApiService


def test_web_api_vertical_slice_uses_canonical_session_runtime(tmp_path) -> None:
    api = WebApiService(tmp_path / "workspace")
    created = api.create_session(
        {
            "title": "Web vertical slice",
            "backend": "fixture",
            "authority_mode": "assisted",
        }
    )

    session_id = created["session_id"]
    assert created["authority_profile_id"] == "assisted"
    assert created["effective_gate_policy_id"] == "evidence_backed"
    assert created["messages"] == []

    result = api.run_turn(
        session_id,
        {"question": "Which boundary might be missing here?"},
    )
    messages = result["session"]["messages"]

    assert [item["role"] for item in messages] == ["user", "assistant"]
    assert messages[0]["content"] == "Which boundary might be missing here?"
    assert result["session"]["effective_gate_policy_id"] == "evidence_backed"


def test_web_api_exploratory_mode_selects_autonomous_profile(tmp_path) -> None:
    api = WebApiService(tmp_path / "workspace")
    created = api.create_session(
        {"title": "Explore", "backend": "fixture", "authority_mode": "exploratory"}
    )

    assert created["authority_profile_id"] == "autonomous"
    assert created["effective_gate_policy_id"] == "exploratory"


def test_web_api_does_not_expose_legacy_self_reinforcement_switch(tmp_path) -> None:
    api = WebApiService(tmp_path / "workspace")
    created = api.create_session(
        {
            "title": "No loop",
            "backend": "fixture",
            "authority_mode": "assisted",
            "allow_same_turn_revision": True,
            "allow_self_reinforcement": True,
        }
    )

    assert created["allow_same_turn_revision"] is True
    assert created["self_derived_signal_policy"] == "fail_closed"
    assert created["allow_self_reinforcement"] is False


def test_web_api_rejects_unknown_authority_mode(tmp_path) -> None:
    api = WebApiService(tmp_path / "workspace")
    with pytest.raises(ValueError, match="authority_mode"):
        api.create_session(
            {"title": "Nope", "backend": "fixture", "authority_mode": "mystery"}
        )


def test_web_api_rejects_string_false_evidence_attestation(tmp_path) -> None:
    api = WebApiService(tmp_path / "workspace")

    with pytest.raises(ValueError, match="literal JSON boolean true"):
        api.submit_evidence(
            "session::does-not-matter",
            "seed::does-not-matter",
            {
                "source_ref": "source:test",
                "operator_verified": "false",
            },
        )


def test_web_api_rejects_boolean_false_evidence_attestation(tmp_path) -> None:
    api = WebApiService(tmp_path / "workspace")

    with pytest.raises(ValueError, match="literal JSON boolean true"):
        api.submit_evidence(
            "session::does-not-matter",
            "seed::does-not-matter",
            {
                "source_ref": "source:test",
                "operator_verified": False,
            },
        )


def test_web_api_rejects_truthy_string_for_product_boolean(tmp_path) -> None:
    api = WebApiService(tmp_path / "workspace")

    with pytest.raises(ValueError, match="allow_same_turn_revision must be a JSON boolean"):
        api.create_session(
            {
                "title": "Strict JSON types",
                "backend": "fixture",
                "authority_mode": "assisted",
                "allow_same_turn_revision": "false",
            }
        )

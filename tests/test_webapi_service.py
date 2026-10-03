from __future__ import annotations

import pytest

from shadowseed.application.provider_policy import ProviderPolicyError
from shadowseed.workbench.controller import WorkbenchController
from shadowseed.workbench.production_controller import ProductionLocalWorkbenchController
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
        {
            "question": "Which boundary might be missing here?",
            "request_id": "web-turn:test-vertical-slice",
        },
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


@pytest.mark.parametrize("bad_question", [{"x": 1}, ["x"], 42, True])
def test_web_api_rejects_non_string_questions_without_persisting_turn(
    tmp_path,
    bad_question,
) -> None:
    api = WebApiService(tmp_path / "workspace")
    created = api.create_session(
        {
            "title": "Strict question types",
            "backend": "fixture",
            "authority_mode": "assisted",
        }
    )

    with pytest.raises(ValueError, match="question must be a JSON string"):
        api.run_turn(created["session_id"], {"question": bad_question})

    after = api.get_session(created["session_id"])
    assert after["messages"] == []
    assert after["turn"] == 0


@pytest.mark.parametrize("bad_source_ref", [{"url": "x"}, ["x"], 42, True])
def test_web_api_rejects_non_string_evidence_reference_before_mutation(
    tmp_path,
    bad_source_ref,
) -> None:
    api = WebApiService(tmp_path / "workspace")

    with pytest.raises(ValueError, match="source_ref must be a JSON string"):
        api.submit_evidence(
            "session::does-not-matter",
            "seed::does-not-matter",
            {
                "source_ref": bad_source_ref,
                "operator_verified": True,
            },
        )


def test_web_api_rejects_non_string_evidence_note_before_mutation(tmp_path) -> None:
    api = WebApiService(tmp_path / "workspace")

    with pytest.raises(ValueError, match="note must be a JSON string"):
        api.submit_evidence(
            "session::does-not-matter",
            "seed::does-not-matter",
            {
                "source_ref": "source:test",
                "note": {"unexpected": "object"},
                "operator_verified": True,
            },
        )


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("title", None),
        ("backend", None),
        ("authority_mode", None),
    ],
)
def test_web_api_rejects_explicit_null_for_defaulted_string_fields(
    tmp_path,
    field,
    value,
) -> None:
    api = WebApiService(tmp_path / "workspace")
    payload = {
        "title": "Null contract",
        "backend": "fixture",
        "authority_mode": "assisted",
    }
    payload[field] = value

    with pytest.raises(ValueError, match=rf"{field} must be a JSON string"):
        api.create_session(payload)


def test_web_api_allows_explicit_null_model_id_for_fixture(tmp_path) -> None:
    api = WebApiService(tmp_path / "workspace")
    created = api.create_session(
        {
            "title": "Optional model",
            "backend": "fixture",
            "authority_mode": "assisted",
            "model_id": None,
        }
    )

    assert created["model_id"] is None


def test_web_api_rejects_explicit_null_evidence_note_before_mutation(tmp_path) -> None:
    api = WebApiService(tmp_path / "workspace")

    with pytest.raises(ValueError, match="note must be a JSON string"):
        api.submit_evidence(
            "session::does-not-matter",
            "seed::does-not-matter",
            {
                "source_ref": "source:test",
                "note": None,
                "operator_verified": True,
            },
        )


def test_web_api_clears_stale_model_id_for_fixture(tmp_path) -> None:
    api = WebApiService(tmp_path / "workspace")
    created = api.create_session(
        {
            "title": "Fixture provenance",
            "backend": "fixture",
            "authority_mode": "assisted",
            "model_id": "qwen2.5:7b",
        }
    )

    assert created["backend"] == "fixture"
    assert created["model_id"] is None


def test_web_api_hides_and_rejects_existing_unsupported_provider_sessions(
    tmp_path,
) -> None:
    api = WebApiService(tmp_path / "workspace")
    supported = api.create_session(
        {
            "title": "Supported",
            "backend": "fixture",
            "authority_mode": "assisted",
        }
    )
    unsupported_id = api.controller.create_session(
        title="Existing hosted session",
        profile_id="balanced",
        backend="openai",
        model_id="gpt-4o-mini",
        runtime_mode="live",
        authority_profile_id="assisted",
        embedding_backend="openai",
        external_confirmed=True,
    )

    listed_ids = {
        item["session_id"]
        for item in api.list_sessions()["sessions"]
    }
    assert supported["session_id"] in listed_ids
    assert unsupported_id not in listed_ids

    with pytest.raises(
        ValueError,
        match="web client v1 does not support this session provider configuration",
    ):
        api.get_session(unsupported_id)

    with pytest.raises(
        ValueError,
        match="web client v1 does not support this session provider configuration",
    ):
        api.run_turn(unsupported_id, {"question": "Do not call the provider"})



@pytest.mark.parametrize(
    ("revision_backend", "revision_model_id", "embedding_backend"),
    [
        ("openai", "gpt-4o-mini", "lexical"),
        (None, None, "openai"),
    ],
)
def test_web_api_hides_sessions_with_unsupported_secondary_providers(
    tmp_path,
    revision_backend,
    revision_model_id,
    embedding_backend,
) -> None:
    api = WebApiService(tmp_path / "workspace")
    session_id = api.controller.create_session(
        title="Unsupported secondary provider",
        profile_id="balanced",
        backend="fixture",
        model_id=None,
        revision_backend=revision_backend,
        revision_model_id=revision_model_id,
        runtime_mode="live",
        authority_profile_id="assisted",
        embedding_backend=embedding_backend,
        external_confirmed=True,
    )

    listed_ids = {
        item["session_id"]
        for item in api.list_sessions()["sessions"]
    }
    assert session_id not in listed_ids

    with pytest.raises(
        ValueError,
        match="web client v1 does not support this session provider configuration",
    ):
        api.get_session(session_id)

    with pytest.raises(
        ValueError,
        match="web client v1 does not support this session provider configuration",
    ):
        api.run_turn(session_id, {"question": "Do not call the provider"})



def test_web_api_uses_production_local_controller_by_default(tmp_path) -> None:
    api = WebApiService(tmp_path / "workspace")

    assert isinstance(api.controller, ProductionLocalWorkbenchController)


def test_web_api_rejects_remote_ollama_before_creation_even_with_generic_controller(
    monkeypatch,
    tmp_path,
) -> None:
    monkeypatch.setenv("OLLAMA_HOST", "http://192.0.2.25:11434")
    controller = WorkbenchController(tmp_path / "workspace")
    api = WebApiService(controller=controller)
    before = controller.workspace.repository.counts()["sessions"]

    with pytest.raises(ProviderPolicyError, match="loopback endpoint"):
        api.create_session(
            {
                "title": "Remote Ollama",
                "backend": "ollama",
                "model_id": "example",
                "authority_mode": "assisted",
            }
        )

    assert controller.workspace.repository.counts()["sessions"] == before


@pytest.mark.parametrize(
    ("backend", "model_id", "revision_backend", "revision_model_id", "embedding_backend"),
    [
        ("ollama", "example", None, None, "ollama"),
        ("fixture", None, "ollama", "example", "lexical"),
        ("fixture", None, None, None, "ollama"),
    ],
)
def test_web_api_hides_existing_sessions_when_ollama_ceases_to_be_local(
    monkeypatch,
    tmp_path,
    backend,
    model_id,
    revision_backend,
    revision_model_id,
    embedding_backend,
) -> None:
    monkeypatch.setenv("OLLAMA_HOST", "http://127.0.0.1:11434")
    workspace = tmp_path / "workspace"
    controller = WorkbenchController(workspace)
    session_id = controller.create_session(
        title="Local provider becomes remote",
        profile_id="balanced",
        backend="fixture",
        model_id=None,
        runtime_mode="live",
        authority_profile_id="assisted",
        embedding_backend="lexical",
        external_confirmed=False,
    )
    provider_config = {
        "backend": backend,
        "model_id": model_id,
        "revision_backend": revision_backend,
        "revision_model_id": revision_model_id,
        "embedding_backend": embedding_backend,
    }
    controller.sessions.update_controls(
        session_id,
        config_updates=provider_config,
        session_config_updates=provider_config,
        core_config_updates={},
    )

    monkeypatch.setenv("OLLAMA_HOST", "http://192.0.2.25:11434")
    api = WebApiService(workspace)

    listed_ids = {
        item["session_id"]
        for item in api.list_sessions()["sessions"]
    }
    assert session_id not in listed_ids

    with pytest.raises(
        ValueError,
        match="web client v1 does not support this session provider configuration",
    ):
        api.get_session(session_id)

    with pytest.raises(
        ValueError,
        match="web client v1 does not support this session provider configuration",
    ):
        api.run_turn(session_id, {"question": "Do not call the remote provider"})



def test_web_api_turn_retry_is_idempotent_across_service_restart(tmp_path) -> None:
    workspace = tmp_path / "workspace"
    api = WebApiService(workspace)
    created = api.create_session(
        {
            "title": "Idempotent retry",
            "backend": "fixture",
            "authority_mode": "assisted",
        }
    )
    payload = {
        "question": "Persist this turn once.",
        "request_id": "web-turn:retry-once",
    }

    first = api.run_turn(created["session_id"], payload)
    restarted = WebApiService(workspace)
    replay = restarted.run_turn(created["session_id"], payload)

    assert replay["report"]["turn"] == first["report"]["turn"]
    assert replay["report"]["answer"] == first["report"]["answer"]
    assert replay["session"]["turn"] == first["session"]["turn"]
    assert [item["role"] for item in replay["session"]["messages"]] == [
        "user",
        "assistant",
    ]
    integrity = restarted.controller.workspace.repository.verify_production_integrity()
    assert integrity["sequence_no"] == integrity["anchor_sequence_no"]


def test_web_api_rejects_reusing_turn_request_id_with_different_question(
    tmp_path,
) -> None:
    api = WebApiService(tmp_path / "workspace")
    created = api.create_session(
        {
            "title": "Idempotency conflict",
            "backend": "fixture",
            "authority_mode": "assisted",
        }
    )
    request_id = "web-turn:conflict"

    api.run_turn(
        created["session_id"],
        {
            "question": "Original question",
            "request_id": request_id,
        },
    )

    with pytest.raises(ValueError, match="different chat input"):
        api.run_turn(
            created["session_id"],
            {
                "question": "Changed question",
                "request_id": request_id,
            },
        )

    after = api.get_session(created["session_id"])
    assert after["turn"] == 1
    assert len(after["messages"]) == 2


def test_web_api_requires_turn_request_id(tmp_path) -> None:
    api = WebApiService(tmp_path / "workspace")
    created = api.create_session(
        {
            "title": "Request id required",
            "backend": "fixture",
            "authority_mode": "assisted",
        }
    )

    with pytest.raises(ValueError, match="request_id is required"):
        api.run_turn(
            created["session_id"],
            {"question": "Do not persist without an idempotency key"},
        )

    assert api.get_session(created["session_id"])["turn"] == 0



def test_web_api_rejects_reusing_turn_request_id_across_sessions(tmp_path) -> None:
    api = WebApiService(tmp_path / "workspace")
    first = api.create_session(
        {
            "title": "First request scope",
            "backend": "fixture",
            "authority_mode": "assisted",
        }
    )
    second = api.create_session(
        {
            "title": "Second request scope",
            "backend": "fixture",
            "authority_mode": "assisted",
        }
    )
    request_id = "web-turn:cross-session-conflict"

    api.run_turn(
        first["session_id"],
        {
            "question": "First session only",
            "request_id": request_id,
        },
    )

    with pytest.raises(ValueError, match="request_id was already used"):
        api.run_turn(
            second["session_id"],
            {
                "question": "Do not reuse this id",
                "request_id": request_id,
            },
        )

    assert api.get_session(second["session_id"])["turn"] == 0

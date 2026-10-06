from __future__ import annotations

import pytest

from shadowseed.adapters.openai_client import (
    clear_process_openai_api_key,
    configure_process_openai_api_key,
)
from shadowseed.application.provider_policy import ProviderPolicyError
from shadowseed.workbench.controller import WorkbenchController
from shadowseed.workbench.production_controller import ProductionLocalWorkbenchController
from shadowseed_webapi.service import WebApiService


@pytest.fixture(autouse=True)
def _clear_web_openai_process_key(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    clear_process_openai_api_key()
    yield
    clear_process_openai_api_key()


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


def test_web_api_lists_hosted_session_read_only_when_provider_not_ready(
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
    hosted_id = api.controller.create_session(
        title="Existing hosted session",
        profile_id="balanced",
        backend="openai",
        model_id="gpt-4o-mini",
        runtime_mode="live",
        authority_profile_id="assisted",
        embedding_backend="openai",
        external_confirmed=True,
    )

    listed = {
        item["session_id"]: item
        for item in api.list_sessions()["sessions"]
    }
    assert listed[supported["session_id"]]["provider_ready"] is True
    assert listed[hosted_id]["provider_ready"] is False

    hosted = api.get_session(hosted_id)
    assert hosted["backend"] == "openai"
    assert hosted["provider_ready"] is False



@pytest.mark.parametrize(
    (
        "revision_backend",
        "revision_model_id",
        "detection_backend",
        "detection_model_id",
        "embedding_backend",
    ),
    [
        ("openai", "gpt-4o-mini", None, None, "lexical"),
        (None, None, "openai", "gpt-4o-mini", "lexical"),
        (None, None, None, None, "openai"),
    ],
)
def test_web_api_hides_sessions_with_unsupported_secondary_providers(
    tmp_path,
    revision_backend,
    revision_model_id,
    detection_backend,
    detection_model_id,
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
        detection_backend=detection_backend,
        detection_model_id=detection_model_id,
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


def _capture_web_session_creation(monkeypatch, api: WebApiService) -> dict:
    captured: dict = {}

    def fake_create_session(**kwargs):
        captured.update(kwargs)
        return "session::captured"

    monkeypatch.setattr(api.controller, "create_session", fake_create_session)
    monkeypatch.setattr(
        api,
        "get_session",
        lambda session_id: {"session_id": session_id},
    )
    monkeypatch.setattr(
        "shadowseed_webapi.service.validate_production_local_backend",
        lambda backend, embedding_backend: None,
    )
    return captured


def test_web_api_does_not_route_local_roles_by_model_family_name(
    monkeypatch,
    tmp_path,
) -> None:
    api = WebApiService(tmp_path / "workspace")
    captured = _capture_web_session_creation(monkeypatch, api)
    monkeypatch.setattr(
        api.controller,
        "discover_models",
        lambda backend: ["deepseek-r1:latest", "gemma2:latest", "llama3.1:latest"]
        if backend == "ollama"
        else [],
    )

    api.create_session(
        {
            "title": "No name-based local routing",
            "backend": "ollama",
            "model_id": "deepseek-r1:latest",
            "authority_mode": "assisted",
        }
    )

    assert captured["model_id"] == "deepseek-r1:latest"
    assert captured["revision_backend"] is None
    assert captured["revision_model_id"] is None
    assert captured["detection_backend"] is None
    assert captured["detection_model_id"] is None
    assert captured["detection_max_new_tokens"] is None


def test_web_api_routes_only_roles_with_explicit_capability_evidence(
    monkeypatch,
    tmp_path,
) -> None:
    api = WebApiService(tmp_path / "workspace")
    captured = _capture_web_session_creation(monkeypatch, api)
    monkeypatch.setattr(
        "shadowseed_webapi.service._LOCAL_ROLE_CAPABILITIES",
        {"gemma2:latest": frozenset({"revision", "detection"})},
    )
    monkeypatch.setattr(
        api.controller,
        "discover_models",
        lambda backend: ["deepseek-r1:latest", "gemma2:latest"]
        if backend == "ollama"
        else [],
    )

    api.create_session(
        {
            "title": "Evidence-backed local roles",
            "backend": "ollama",
            "model_id": "deepseek-r1:latest",
            "authority_mode": "assisted",
        }
    )

    assert captured["revision_backend"] == "ollama"
    assert captured["revision_model_id"] == "gemma2:latest"
    assert captured["detection_backend"] == "ollama"
    assert captured["detection_model_id"] == "gemma2:latest"
    assert captured["detection_max_new_tokens"] == 220


def test_web_api_role_capability_is_specific_to_exact_model_id(
    monkeypatch,
    tmp_path,
) -> None:
    api = WebApiService(tmp_path / "workspace")
    captured = _capture_web_session_creation(monkeypatch, api)
    monkeypatch.setattr(
        "shadowseed_webapi.service._LOCAL_ROLE_CAPABILITIES",
        {"gemma2:9b": frozenset({"revision", "detection"})},
    )
    monkeypatch.setattr(
        api.controller,
        "discover_models",
        lambda backend: ["deepseek-r1:latest", "gemma2:latest"]
        if backend == "ollama"
        else [],
    )

    api.create_session(
        {
            "title": "Exact model evidence only",
            "backend": "ollama",
            "model_id": "deepseek-r1:latest",
            "authority_mode": "assisted",
        }
    )

    assert captured["revision_backend"] is None
    assert captured["revision_model_id"] is None
    assert captured["detection_backend"] is None
    assert captured["detection_model_id"] is None
    assert captured["detection_max_new_tokens"] is None


def test_web_api_capability_evidence_is_role_specific(
    monkeypatch,
    tmp_path,
) -> None:
    api = WebApiService(tmp_path / "workspace")
    captured = _capture_web_session_creation(monkeypatch, api)
    monkeypatch.setattr(
        "shadowseed_webapi.service._LOCAL_ROLE_CAPABILITIES",
        {"gemma2:latest": frozenset({"detection"})},
    )
    monkeypatch.setattr(
        api.controller,
        "discover_models",
        lambda backend: ["llama3.1:latest", "gemma2:latest"]
        if backend == "ollama"
        else [],
    )

    api.create_session(
        {
            "title": "Role-specific local evidence",
            "backend": "ollama",
            "model_id": "llama3.1:latest",
            "authority_mode": "assisted",
        }
    )

    assert captured["revision_backend"] is None
    assert captured["revision_model_id"] is None
    assert captured["detection_backend"] == "ollama"
    assert captured["detection_model_id"] == "gemma2:latest"
    assert captured["detection_max_new_tokens"] == 220


def test_web_session_payload_exposes_effective_model_roles(tmp_path) -> None:
    api = WebApiService(tmp_path / "workspace")
    view = {
        "backend": "ollama",
        "model_id": "deepseek-r1:latest",
        "revision_backend": "ollama",
        "revision_model_id": "gemma2:latest",
        "detection_backend": "ollama",
        "detection_model_id": "gemma2:latest",
        "detection_max_new_tokens": 220,
    }
    api._provider_ready_for_view = lambda current: True  # type: ignore[method-assign]
    api.controller.chat_messages = lambda current: []  # type: ignore[method-assign]

    payload = api._session_payload(view)

    assert payload["model_roles"] == {
        "generation": {
            "backend": "ollama",
            "model_id": "deepseek-r1:latest",
        },
        "revision": {
            "backend": "ollama",
            "model_id": "gemma2:latest",
        },
        "detection": {
            "backend": "ollama",
            "model_id": "gemma2:latest",
            "max_new_tokens": 220,
        },
    }


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



def _web_seed_fixture(api: WebApiService) -> tuple[str, str]:
    created = api.create_session(
        {
            "title": "Seed actions",
            "backend": "fixture",
            "authority_mode": "assisted",
        }
    )
    session_id = created["session_id"]
    turn = api.run_turn(
        session_id,
        {
            "question": "What is missing from this privacy plan?",
            "request_id": "web-turn:seed-action-fixture",
        },
    )
    return session_id, turn["session"]["seeds"][0]["id"]


def test_web_api_seed_detail_exposes_canonical_timeline(tmp_path) -> None:
    api = WebApiService(tmp_path / "workspace")
    session_id, seed_id = _web_seed_fixture(api)

    detail = api.get_seed(session_id, seed_id)

    assert detail["id"] == seed_id
    assert detail["plain_explanation"]
    assert detail["effective_gate_policy_id"] == "evidence_backed"
    assert isinstance(detail["timeline"], list)
    assert detail["timeline"]
    assert all("type" in item and "payload" in item for item in detail["timeline"])


def test_web_api_evidence_retry_is_idempotent(tmp_path) -> None:
    api = WebApiService(tmp_path / "workspace")
    session_id, seed_id = _web_seed_fixture(api)
    payload = {
        "source_ref": "reviewer:web-evidence",
        "note": "Checked independently.",
        "operator_verified": True,
        "request_id": "web-evidence:retry-once",
    }

    first = api.submit_evidence(session_id, seed_id, payload)
    after_first = api.controller.workspace.repository.verify_production_integrity()
    second = api.submit_evidence(session_id, seed_id, payload)
    after_second = api.controller.workspace.repository.verify_production_integrity()

    first_seed = next(item for item in first["seeds"] if item["id"] == seed_id)
    second_seed = next(item for item in second["seeds"] if item["id"] == seed_id)
    assert first_seed["evidence_count"] == 1
    assert second_seed["evidence_count"] == 1
    assert after_second["sequence_no"] == after_first["sequence_no"]
    assert after_second["head_hash"] == after_first["head_hash"]


def test_web_api_contradiction_retry_is_idempotent(tmp_path) -> None:
    api = WebApiService(tmp_path / "workspace")
    session_id, seed_id = _web_seed_fixture(api)
    payload = {"request_id": "web-contradiction:retry-once"}

    first = api.contradict_seed(session_id, seed_id, payload)
    after_first = api.controller.workspace.repository.verify_production_integrity()
    second = api.contradict_seed(session_id, seed_id, payload)
    after_second = api.controller.workspace.repository.verify_production_integrity()

    first_seed = next(item for item in first["seeds"] if item["id"] == seed_id)
    second_seed = next(item for item in second["seeds"] if item["id"] == seed_id)
    assert first_seed["blocking"] is True
    assert second_seed["blocking"] is True
    assert after_second["sequence_no"] == after_first["sequence_no"]
    assert after_second["head_hash"] == after_first["head_hash"]


def test_web_api_contradiction_resolution_retry_is_idempotent(tmp_path) -> None:
    api = WebApiService(tmp_path / "workspace")
    session_id, seed_id = _web_seed_fixture(api)
    api.contradict_seed(
        session_id,
        seed_id,
        {"request_id": "web-contradiction:before-resolution"},
    )
    payload = {
        "basis": "Independent review resolved the conflict.",
        "request_id": "web-contradiction-resolve:retry-once",
    }

    first = api.resolve_contradiction(session_id, seed_id, payload)
    after_first = api.controller.workspace.repository.verify_production_integrity()
    second = api.resolve_contradiction(session_id, seed_id, payload)
    after_second = api.controller.workspace.repository.verify_production_integrity()

    first_seed = next(item for item in first["seeds"] if item["id"] == seed_id)
    second_seed = next(item for item in second["seeds"] if item["id"] == seed_id)
    assert first_seed["blocking"] is False
    assert second_seed["blocking"] is False
    assert after_second["sequence_no"] == after_first["sequence_no"]
    assert after_second["head_hash"] == after_first["head_hash"]


def test_web_api_rejects_changed_resolution_for_same_request_id(tmp_path) -> None:
    api = WebApiService(tmp_path / "workspace")
    session_id, seed_id = _web_seed_fixture(api)
    api.contradict_seed(
        session_id,
        seed_id,
        {"request_id": "web-contradiction:resolution-conflict"},
    )
    request_id = "web-contradiction-resolve:conflict"
    api.resolve_contradiction(
        session_id,
        seed_id,
        {
            "basis": "First checked basis.",
            "request_id": request_id,
        },
    )

    with pytest.raises(ValueError, match="different contradiction-resolution input"):
        api.resolve_contradiction(
            session_id,
            seed_id,
            {
                "basis": "Different basis.",
                "request_id": request_id,
            },
        )


@pytest.mark.parametrize(
    ("method", "payload"),
    [
        (
            "evidence",
            {
                "source_ref": "reviewer:missing-id",
                "operator_verified": True,
            },
        ),
        ("contradict", {}),
        ("resolve", {"basis": "Checked basis"}),
    ],
)
def test_web_api_seed_mutations_require_request_id(
    tmp_path,
    method,
    payload,
) -> None:
    api = WebApiService(tmp_path / "workspace")
    session_id, seed_id = _web_seed_fixture(api)

    with pytest.raises(ValueError, match="request_id is required"):
        if method == "evidence":
            api.submit_evidence(session_id, seed_id, payload)
        elif method == "contradict":
            api.contradict_seed(session_id, seed_id, payload)
        else:
            api.resolve_contradiction(session_id, seed_id, payload)



def test_web_api_provider_status_never_returns_or_persists_openai_key(
    monkeypatch,
    tmp_path,
) -> None:
    workspace = tmp_path / "workspace"
    api = WebApiService(workspace)
    monkeypatch.setattr(
        api.controller,
        "backend_available",
        lambda backend: backend == "openai",
    )
    secret = "sk-provider-secret-marker"

    before = api.provider_status()
    assert next(
        item for item in before["providers"] if item["provider"] == "openai"
    )["configured"] is False

    configured = api.configure_openai({"api_key": secret})
    openai = next(
        item for item in configured["providers"] if item["provider"] == "openai"
    )
    assert openai["configured"] is True
    assert openai["ready"] is True
    assert secret not in repr(configured)

    for path in workspace.rglob("*"):
        if path.is_file():
            assert secret.encode("utf-8") not in path.read_bytes()

    cleared = api.clear_openai()
    openai = next(
        item for item in cleared["providers"] if item["provider"] == "openai"
    )
    assert openai["configured"] is False
    assert openai["ready"] is False


def test_web_api_openai_creation_requires_configured_provider(
    monkeypatch,
    tmp_path,
) -> None:
    api = WebApiService(tmp_path / "workspace")
    monkeypatch.setattr(
        api.controller,
        "backend_available",
        lambda backend: backend == "openai",
    )

    with pytest.raises(ValueError, match="OpenAI is not configured"):
        api.create_session(
            {
                "title": "Hosted",
                "backend": "openai",
                "model_id": "gpt-4o-mini",
                "authority_mode": "assisted",
                "external_confirmed": True,
            }
        )


def test_web_api_openai_creation_requires_explicit_external_consent(
    monkeypatch,
    tmp_path,
) -> None:
    api = WebApiService(tmp_path / "workspace")
    monkeypatch.setattr(
        api.controller,
        "backend_available",
        lambda backend: backend == "openai",
    )
    configure_process_openai_api_key("sk-test")

    with pytest.raises(ValueError, match="confirm external processing"):
        api.create_session(
            {
                "title": "Hosted",
                "backend": "openai",
                "model_id": "gpt-4o-mini",
                "authority_mode": "assisted",
            }
        )


def test_web_api_openai_session_is_visible_and_ready_when_configured(
    monkeypatch,
    tmp_path,
) -> None:
    api = WebApiService(tmp_path / "workspace")
    monkeypatch.setattr(
        api.controller,
        "backend_available",
        lambda backend: backend == "openai",
    )
    configure_process_openai_api_key("sk-test")

    created = api.create_session(
        {
            "title": "Hosted",
            "backend": "openai",
            "model_id": "gpt-4o-mini",
            "authority_mode": "assisted",
            "external_confirmed": True,
        }
    )

    assert created["backend"] == "openai"
    assert created["provider_ready"] is True
    assert created["embedding_backend"] == "openai"
    listed = {
        item["session_id"]: item
        for item in api.list_sessions()["sessions"]
    }
    assert listed[created["session_id"]]["provider_ready"] is True


def test_web_api_openai_turn_requires_fresh_external_consent(
    monkeypatch,
    tmp_path,
) -> None:
    api = WebApiService(tmp_path / "workspace")
    monkeypatch.setattr(
        api.controller,
        "backend_available",
        lambda backend: backend == "openai",
    )
    configure_process_openai_api_key("sk-test")
    created = api.create_session(
        {
            "title": "Hosted",
            "backend": "openai",
            "model_id": "gpt-4o-mini",
            "authority_mode": "assisted",
            "external_confirmed": True,
        }
    )

    with pytest.raises(ValueError, match="confirm external processing"):
        api.run_turn(
            created["session_id"],
            {
                "question": "Do not send this without consent.",
                "request_id": "web-turn:openai-consent",
            },
        )

    assert api.get_session(created["session_id"])["turn"] == 0


def test_web_api_openai_status_distinguishes_key_from_missing_runtime(
    monkeypatch,
    tmp_path,
) -> None:
    api = WebApiService(tmp_path / "workspace")
    monkeypatch.setattr(api.controller, "backend_available", lambda backend: False)
    configure_process_openai_api_key("sk-test")

    status = next(
        item
        for item in api.provider_status()["providers"]
        if item["provider"] == "openai"
    )

    assert status["configured"] is True
    assert status["available"] is False
    assert status["ready"] is False

from __future__ import annotations

import http.client
import json
import threading
from pathlib import Path

import pytest
from http.server import ThreadingHTTPServer
from typing import Any

from shadowseed.adapters.openai_client import clear_process_openai_api_key
from shadowseed_webapi.server import make_handler, serve
from shadowseed_webapi.service import WebApiService


class _FakeService:
    def __init__(self) -> None:
        self.created: list[dict[str, Any]] = []

    def health(self) -> dict[str, Any]:
        return {"ok": True}

    def list_sessions(self) -> dict[str, Any]:
        return {"sessions": []}

    def create_session(self, payload: dict[str, Any]) -> dict[str, Any]:
        self.created.append(dict(payload))
        return {"session_id": "session::fake"}


def _request(
    service: Any,
    *,
    method: str,
    path: str,
    body: str = "",
    headers: dict[str, str] | None = None,
) -> tuple[int, dict[str, Any]]:
    server = ThreadingHTTPServer(
        ("127.0.0.1", 0),
        make_handler(service),
    )
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        connection = http.client.HTTPConnection(
            "127.0.0.1",
            server.server_address[1],
            timeout=3,
        )
        connection.request(method, path, body=body, headers=headers or {})
        response = connection.getresponse()
        raw = response.read()
        payload = json.loads(raw.decode("utf-8")) if raw else {}
        connection.close()
        return response.status, payload
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=3)


def test_unapproved_browser_origin_is_rejected_before_mutation() -> None:
    service = _FakeService()
    status, payload = _request(
        service,
        method="POST",
        path="/api/v1/sessions",
        body='{"title":"attack"}',
        headers={
            "Origin": "https://attacker.example",
            "Content-Type": "text/plain",
        },
    )

    assert status == 403
    assert payload == {"error": "origin_not_allowed"}
    assert service.created == []


def test_allowed_origin_with_json_can_reach_service() -> None:
    service = _FakeService()
    status, payload = _request(
        service,
        method="POST",
        path="/api/v1/sessions",
        body='{"title":"ok"}',
        headers={
            "Origin": "http://127.0.0.1:3000",
            "Content-Type": "application/json",
        },
    )

    assert status == 201
    assert payload == {"session_id": "session::fake"}
    assert service.created == [{"title": "ok"}]


def test_text_plain_post_is_rejected_even_without_origin() -> None:
    service = _FakeService()
    status, payload = _request(
        service,
        method="POST",
        path="/api/v1/sessions",
        body='{"title":"no-cors"}',
        headers={"Content-Type": "text/plain"},
    )

    assert status == 400
    assert "application/json" in payload["error"]
    assert service.created == []


def test_ipv6_loopback_is_rejected_before_server_construction(tmp_path) -> None:
    with pytest.raises(ValueError, match="IPv6 loopback binding is not supported"):
        serve(
            workspace=tmp_path / "workspace",
            host="::1",
            port=0,
        )


def test_explicit_null_string_field_returns_400_not_500(tmp_path) -> None:
    service = WebApiService(tmp_path / "workspace")
    status, payload = _request(
        service,
        method="POST",
        path="/api/v1/sessions",
        body='{"backend":null}',
        headers={"Content-Type": "application/json"},
    )

    assert status == 400
    assert "backend must be a JSON string" in payload["error"]



class _ConcurrentMutationService(_FakeService):
    def __init__(self) -> None:
        super().__init__()
        self._guard = threading.Lock()
        self.active = 0
        self.max_active = 0

    def create_session(self, payload: dict[str, Any]) -> dict[str, Any]:
        with self._guard:
            self.active += 1
            self.max_active = max(self.max_active, self.active)
        try:
            threading.Event().wait(0.1)
            return {"session_id": f"session::{payload.get('title', 'fake')}"}
        finally:
            with self._guard:
                self.active -= 1


def test_threaded_server_serializes_workspace_mutations() -> None:
    service = _ConcurrentMutationService()
    server = ThreadingHTTPServer(
        ("127.0.0.1", 0),
        make_handler(service),
    )
    server_thread = threading.Thread(target=server.serve_forever, daemon=True)
    server_thread.start()
    statuses: list[int] = []
    statuses_lock = threading.Lock()

    def post(title: str) -> None:
        connection = http.client.HTTPConnection(
            "127.0.0.1",
            server.server_address[1],
            timeout=3,
        )
        connection.request(
            "POST",
            "/api/v1/sessions",
            body=json.dumps({"title": title}),
            headers={"Content-Type": "application/json"},
        )
        response = connection.getresponse()
        response.read()
        connection.close()
        with statuses_lock:
            statuses.append(response.status)

    clients = [
        threading.Thread(target=post, args=(f"chat-{index}",))
        for index in range(4)
    ]
    try:
        for client in clients:
            client.start()
        for client in clients:
            client.join(timeout=3)

        assert sorted(statuses) == [201, 201, 201, 201]
        assert service.max_active == 1
    finally:
        server.shutdown()
        server.server_close()
        server_thread.join(timeout=3)


def test_missing_session_returns_404(tmp_path) -> None:
    service = WebApiService(tmp_path / "workspace")
    status, payload = _request(
        service,
        method="GET",
        path="/api/v1/sessions/session::missing",
    )

    assert status == 404
    assert payload == {"error": "not_found"}


def test_missing_seed_returns_404(tmp_path) -> None:
    service = WebApiService(tmp_path / "workspace")
    created = service.create_session(
        {
            "title": "Seed lookup",
            "backend": "fixture",
            "authority_mode": "assisted",
        }
    )
    status, payload = _request(
        service,
        method="GET",
        path=f"/api/v1/sessions/{created['session_id']}/seeds/seed::missing",
    )

    assert status == 404
    assert payload == {"error": "not_found"}



def test_remote_binding_is_rejected_without_escape_hatch(tmp_path) -> None:
    with pytest.raises(ValueError, match="loopback-only"):
        serve(
            workspace=tmp_path / "workspace",
            host="0.0.0.0",
            port=0,
        )



def test_seed_authority_routes_reach_canonical_service(tmp_path) -> None:
    service = WebApiService(tmp_path / "workspace")
    created = service.create_session(
        {
            "title": "Seed HTTP routes",
            "backend": "fixture",
            "authority_mode": "assisted",
        }
    )
    session_id = created["session_id"]
    turn = service.run_turn(
        session_id,
        {
            "question": "What is missing from this plan?",
            "request_id": "web-turn:http-seed-routes",
        },
    )
    seed_id = turn["session"]["seeds"][0]["id"]
    seed_path = (
        f"/api/v1/sessions/{session_id}/seeds/{seed_id}"
    )

    detail_status, detail = _request(
        service,
        method="GET",
        path=seed_path,
    )
    assert detail_status == 200
    assert detail["id"] == seed_id
    assert isinstance(detail["timeline"], list)

    contradiction_status, contradicted = _request(
        service,
        method="POST",
        path=seed_path + "/contradictions",
        body=json.dumps(
            {"request_id": "web-contradiction:http-seed-routes"}
        ),
        headers={"Content-Type": "application/json"},
    )
    assert contradiction_status == 200
    contradicted_seed = next(
        item for item in contradicted["seeds"] if item["id"] == seed_id
    )
    assert contradicted_seed["blocking"] is True

    resolve_status, resolved = _request(
        service,
        method="POST",
        path=seed_path + "/contradictions/resolve",
        body=json.dumps(
            {
                "basis": "Independent review resolved the conflict.",
                "request_id": "web-contradiction-resolve:http-seed-routes",
            }
        ),
        headers={"Content-Type": "application/json"},
    )
    assert resolve_status == 200
    resolved_seed = next(
        item for item in resolved["seeds"] if item["id"] == seed_id
    )
    assert resolved_seed["blocking"] is False

    evidence_status, supported = _request(
        service,
        method="POST",
        path=seed_path + "/evidence",
        body=json.dumps(
            {
                "source_ref": "reviewer:http-seed-routes",
                "note": "Checked independently.",
                "operator_verified": True,
                "request_id": "web-evidence:http-seed-routes",
            }
        ),
        headers={"Content-Type": "application/json"},
    )
    assert evidence_status == 200
    supported_seed = next(
        item for item in supported["seeds"] if item["id"] == seed_id
    )
    assert supported_seed["evidence_count"] == 1



def test_provider_http_routes_never_echo_openai_key(tmp_path) -> None:
    clear_process_openai_api_key()
    service = WebApiService(tmp_path / "workspace")
    secret = "sk-http-secret-marker"
    try:
        status, payload = _request(
            service,
            method="POST",
            path="/api/v1/providers/openai/credential",
            body=json.dumps({"api_key": secret}),
            headers={"Content-Type": "application/json"},
        )

        assert status == 200
        assert secret not in json.dumps(payload)
        openai = next(
            item for item in payload["providers"] if item["provider"] == "openai"
        )
        assert openai["configured"] is True

        status, payload = _request(
            service,
            method="GET",
            path="/api/v1/providers",
        )
        assert status == 200
        assert secret not in json.dumps(payload)

        status, payload = _request(
            service,
            method="POST",
            path="/api/v1/providers/openai/credential/clear",
            body="{}",
            headers={"Content-Type": "application/json"},
        )
        assert status == 200
        openai = next(
            item for item in payload["providers"] if item["provider"] == "openai"
        )
        assert openai["configured"] is False
    finally:
        clear_process_openai_api_key()



def _raw_request(
    service: Any,
    *,
    method: str,
    path: str,
    static_root: Path,
    headers: dict[str, str] | None = None,
) -> tuple[int, bytes, dict[str, str]]:
    server = ThreadingHTTPServer(
        ("127.0.0.1", 0),
        make_handler(service, static_root=static_root),
    )
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        connection = http.client.HTTPConnection(
            "127.0.0.1",
            server.server_address[1],
            timeout=3,
        )
        connection.request(method, path, headers=headers or {})
        response = connection.getresponse()
        raw = response.read()
        response_headers = {key.lower(): value for key, value in response.getheaders()}
        status = response.status
        connection.close()
        return status, raw, response_headers
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=3)


def test_static_client_is_served_without_node_runtime(tmp_path) -> None:
    static_root = tmp_path / "static"
    asset = static_root / "_next" / "static" / "chunks" / "app.js"
    asset.parent.mkdir(parents=True)
    (static_root / "index.html").write_text(
        "<!doctype html><html><body>Shadowseed Web</body></html>",
        encoding="utf-8",
    )
    asset.write_text("console.log('shadowseed')", encoding="utf-8")

    service = _FakeService()
    status, raw, headers = _raw_request(
        service,
        method="GET",
        path="/",
        static_root=static_root,
    )
    assert status == 200
    assert b"Shadowseed Web" in raw
    assert headers["cache-control"] == "no-store"

    status, raw, headers = _raw_request(
        service,
        method="GET",
        path="/_next/static/chunks/app.js",
        static_root=static_root,
    )
    assert status == 200
    assert b"shadowseed" in raw
    assert headers["cache-control"] == "public, max-age=31536000, immutable"


def test_static_client_rejects_path_traversal(tmp_path) -> None:
    static_root = tmp_path / "static"
    static_root.mkdir()
    (static_root / "index.html").write_text("ok", encoding="utf-8")
    outside = tmp_path / "secret.txt"
    outside.write_text("PRIVATE", encoding="utf-8")

    status, raw, _headers = _raw_request(
        _FakeService(),
        method="GET",
        path="/%2e%2e/secret.txt",
        static_root=static_root,
    )

    assert status == 404
    assert b"PRIVATE" not in raw


def test_same_origin_packaged_client_can_mutate_api() -> None:
    service = _FakeService()
    server = ThreadingHTTPServer(
        ("127.0.0.1", 0),
        make_handler(service),
    )
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        port = int(server.server_address[1])
        connection = http.client.HTTPConnection("127.0.0.1", port, timeout=3)
        connection.request(
            "POST",
            "/api/v1/sessions",
            body='{"title":"same-origin"}',
            headers={
                "Origin": f"http://127.0.0.1:{port}",
                "Content-Type": "application/json",
            },
        )
        response = connection.getresponse()
        payload = json.loads(response.read().decode("utf-8"))
        connection.close()
        assert response.status == 201
        assert payload == {"session_id": "session::fake"}
        assert service.created == [{"title": "same-origin"}]
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=3)

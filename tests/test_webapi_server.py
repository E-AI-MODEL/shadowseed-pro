from __future__ import annotations

import http.client
import json
import threading

import pytest
from http.server import ThreadingHTTPServer
from typing import Any

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

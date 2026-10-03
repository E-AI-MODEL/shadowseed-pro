from __future__ import annotations

import http.client
import json
import threading
from http.server import ThreadingHTTPServer
from typing import Any

from shadowseed_webapi.server import make_handler


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
    service: _FakeService,
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

"""Loopback-only JSON HTTP server for the Shadowseed web product client."""

from __future__ import annotations

import argparse
import ipaddress
import json
import mimetypes
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from threading import RLock
from typing import Any
from urllib.parse import unquote, urlsplit

from shadowseed.application.error_safety import sanitized_exception_line
from shadowseed_webapi.service import WebApiService


DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 8765
DEFAULT_WEB_ORIGINS = frozenset(
    {"http://127.0.0.1:3000", "http://localhost:3000"}
)
_MAX_BODY_BYTES = 1_000_000


def _is_loopback(host: str) -> bool:
    """Return whether host is a loopback supported by the IPv4 HTTP server."""

    normalized = str(host).strip().lower()
    if normalized == "localhost":
        return True
    try:
        address = ipaddress.ip_address(normalized)
    except ValueError:
        return False
    return address.version == 4 and address.is_loopback


def _is_ipv6_loopback(host: str) -> bool:
    try:
        address = ipaddress.ip_address(str(host).strip().lower())
    except ValueError:
        return False
    return address.version == 6 and address.is_loopback


def _parts(path: str) -> list[str]:
    return [
        unquote(part)
        for part in urlsplit(path).path.strip("/").split("/")
        if part
    ]


def _origin_is_allowed(
    origin: str | None,
    allowed_origins: frozenset[str],
) -> bool:
    """Allow non-browser callers and explicitly trusted browser origins only."""

    return origin is None or origin in allowed_origins


def _is_json_content_type(content_type: str | None) -> bool:
    if content_type is None:
        return False
    media_type = content_type.split(";", 1)[0].strip().lower()
    return media_type == "application/json"


def _static_candidate(static_root: Path, request_path: str) -> Path | None:
    """Resolve one static request without allowing traversal outside the export."""

    root = static_root.resolve()
    relative = unquote(urlsplit(request_path).path).lstrip("/") or "index.html"
    candidate = (root / relative).resolve()
    if candidate != root and root not in candidate.parents:
        return None
    if candidate.is_dir():
        candidate = candidate / "index.html"
    return candidate if candidate.is_file() else None


def make_handler(
    service: WebApiService,
    *,
    allowed_origins: frozenset[str] = DEFAULT_WEB_ORIGINS,
    static_root: str | Path | None = None,
):
    mutation_lock = RLock()
    resolved_static_root = Path(static_root).resolve() if static_root else None

    class Handler(BaseHTTPRequestHandler):
        server_version = "ShadowseedWebApi/1"

        def _origin_allowed(self) -> bool:
            origin = self.headers.get("Origin")
            if _origin_is_allowed(origin, allowed_origins):
                return True
            if not origin:
                return True
            host = self.headers.get("Host", "").strip()
            return bool(host and origin == f"http://{host}")

        def _cors_origin(self) -> str | None:
            origin = self.headers.get("Origin")
            return origin if origin and self._origin_allowed() else None

        def _reject_unapproved_origin(self) -> bool:
            if self._origin_allowed():
                return False
            self._write_json(
                HTTPStatus.FORBIDDEN,
                {"error": "origin_not_allowed"},
            )
            return True

        def _write_json(self, status: int, payload: Any) -> None:
            data = json.dumps(
                payload, ensure_ascii=False, separators=(",", ":")
            ).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(data)))
            self.send_header("Cache-Control", "no-store")
            origin = self._cors_origin()
            if origin:
                self.send_header("Access-Control-Allow-Origin", origin)
                self.send_header("Vary", "Origin")
            self.end_headers()
            self.wfile.write(data)

        def _write_file(
            self,
            path: Path,
            *,
            status: int = HTTPStatus.OK,
            head_only: bool = False,
        ) -> None:
            data = path.read_bytes()
            content_type, _encoding = mimetypes.guess_type(path.name)
            self.send_response(status)
            self.send_header(
                "Content-Type",
                (content_type or "application/octet-stream")
                + ("; charset=utf-8" if content_type and content_type.startswith("text/") else ""),
            )
            self.send_header("Content-Length", str(len(data)))
            cache_control = (
                "public, max-age=31536000, immutable"
                if "/_next/static/" in path.as_posix()
                else "no-store"
            )
            self.send_header("Cache-Control", cache_control)
            self.end_headers()
            if not head_only:
                self.wfile.write(data)

        def _serve_static(self, *, head_only: bool = False) -> None:
            if resolved_static_root is None:
                return self._write_json(
                    HTTPStatus.NOT_FOUND,
                    {"error": "not_found"},
                )
            candidate = _static_candidate(resolved_static_root, self.path)
            if candidate is not None:
                return self._write_file(candidate, head_only=head_only)
            fallback = resolved_static_root / "404.html"
            if fallback.is_file():
                return self._write_file(
                    fallback,
                    status=HTTPStatus.NOT_FOUND,
                    head_only=head_only,
                )
            self._write_json(HTTPStatus.NOT_FOUND, {"error": "not_found"})

        def _read_json(self) -> dict[str, Any]:
            if not _is_json_content_type(self.headers.get("Content-Type")):
                raise ValueError("Content-Type must be application/json")
            try:
                length = int(self.headers.get("Content-Length", "0"))
            except ValueError as exc:
                raise ValueError("invalid Content-Length") from exc
            if length < 0 or length > _MAX_BODY_BYTES:
                raise ValueError("request body is too large")
            raw = self.rfile.read(length) if length else b"{}"
            try:
                payload = json.loads(raw.decode("utf-8"))
            except (UnicodeDecodeError, json.JSONDecodeError) as exc:
                raise ValueError("request body must be valid UTF-8 JSON") from exc
            if not isinstance(payload, dict):
                raise ValueError("request body must be a JSON object")
            return payload

        def do_OPTIONS(self) -> None:  # noqa: N802
            if self._reject_unapproved_origin():
                return
            origin = self._cors_origin()
            self.send_response(HTTPStatus.NO_CONTENT)
            if origin:
                self.send_header("Access-Control-Allow-Origin", origin)
                self.send_header("Vary", "Origin")
            self.send_header("Access-Control-Allow-Methods", "GET,POST,OPTIONS")
            self.send_header("Access-Control-Allow-Headers", "Content-Type")
            self.send_header("Access-Control-Max-Age", "600")
            self.end_headers()

        def do_GET(self) -> None:  # noqa: N802
            if self._reject_unapproved_origin():
                return
            try:
                parts = _parts(self.path)
                if parts == ["api", "v1", "health"]:
                    return self._write_json(HTTPStatus.OK, service.health())
                if parts == ["api", "v1", "providers"]:
                    return self._write_json(HTTPStatus.OK, service.provider_status())
                if parts == ["api", "v1", "sessions"]:
                    return self._write_json(HTTPStatus.OK, service.list_sessions())
                if len(parts) == 4 and parts[:3] == ["api", "v1", "sessions"]:
                    return self._write_json(
                        HTTPStatus.OK, service.get_session(parts[3])
                    )
                if (
                    len(parts) == 6
                    and parts[:3] == ["api", "v1", "sessions"]
                    and parts[4] == "seeds"
                ):
                    return self._write_json(
                        HTTPStatus.OK, service.get_seed(parts[3], parts[5])
                    )
                if parts[:2] == ["api", "v1"]:
                    return self._write_json(
                        HTTPStatus.NOT_FOUND,
                        {"error": "not_found"},
                    )
                self._serve_static()
            except KeyError:
                self._write_json(
                    HTTPStatus.NOT_FOUND,
                    {"error": "not_found"},
                )
            except ValueError as exc:
                self._write_json(
                    HTTPStatus.BAD_REQUEST,
                    {"error": sanitized_exception_line(exc)},
                )
            except Exception as exc:  # pragma: no cover
                self._write_json(
                    HTTPStatus.INTERNAL_SERVER_ERROR,
                    {"error": sanitized_exception_line(exc)},
                )

        def do_POST(self) -> None:  # noqa: N802
            if self._reject_unapproved_origin():
                return
            try:
                parts = _parts(self.path)
                payload = self._read_json()
                with mutation_lock:
                    if parts == ["api", "v1", "providers", "openai", "credential"]:
                        return self._write_json(
                            HTTPStatus.OK,
                            service.configure_openai(payload),
                        )
                    if parts == [
                        "api",
                        "v1",
                        "providers",
                        "openai",
                        "credential",
                        "clear",
                    ]:
                        return self._write_json(
                            HTTPStatus.OK,
                            service.clear_openai(),
                        )
                    if parts == ["api", "v1", "sessions"]:
                        return self._write_json(
                            HTTPStatus.CREATED, service.create_session(payload)
                        )
                    if (
                        len(parts) == 5
                        and parts[:3] == ["api", "v1", "sessions"]
                        and parts[4] == "turns"
                    ):
                        return self._write_json(
                            HTTPStatus.OK, service.run_turn(parts[3], payload)
                        )
                    if (
                        len(parts) == 7
                        and parts[:3] == ["api", "v1", "sessions"]
                        and parts[4] == "seeds"
                        and parts[6] == "evidence"
                    ):
                        return self._write_json(
                            HTTPStatus.OK,
                            service.submit_evidence(parts[3], parts[5], payload),
                        )
                    if (
                        len(parts) == 7
                        and parts[:3] == ["api", "v1", "sessions"]
                        and parts[4] == "seeds"
                        and parts[6] == "contradictions"
                    ):
                        return self._write_json(
                            HTTPStatus.OK,
                            service.contradict_seed(parts[3], parts[5], payload),
                        )
                    if (
                        len(parts) == 8
                        and parts[:3] == ["api", "v1", "sessions"]
                        and parts[4] == "seeds"
                        and parts[6] == "contradictions"
                        and parts[7] == "resolve"
                    ):
                        return self._write_json(
                            HTTPStatus.OK,
                            service.resolve_contradiction(
                                parts[3],
                                parts[5],
                                payload,
                            ),
                        )
                    self._write_json(HTTPStatus.NOT_FOUND, {"error": "not_found"})
            except KeyError:
                self._write_json(
                    HTTPStatus.NOT_FOUND,
                    {"error": "not_found"},
                )
            except ValueError as exc:
                self._write_json(
                    HTTPStatus.BAD_REQUEST,
                    {"error": sanitized_exception_line(exc)},
                )
            except Exception as exc:  # pragma: no cover
                self._write_json(
                    HTTPStatus.INTERNAL_SERVER_ERROR,
                    {"error": sanitized_exception_line(exc)},
                )

        def do_HEAD(self) -> None:  # noqa: N802
            if self._reject_unapproved_origin():
                return
            parts = _parts(self.path)
            if parts[:2] == ["api", "v1"]:
                self.send_response(HTTPStatus.METHOD_NOT_ALLOWED)
                self.send_header("Allow", "GET,POST,OPTIONS")
                self.end_headers()
                return
            self._serve_static(head_only=True)

        def log_message(self, format: str, *args: Any) -> None:
            return None

    return Handler


def create_server(
    *,
    workspace: str | Path | None = None,
    host: str = DEFAULT_HOST,
    port: int = DEFAULT_PORT,
    static_root: str | Path | None = None,
) -> ThreadingHTTPServer:
    if _is_ipv6_loopback(host):
        raise ValueError(
            "IPv6 loopback binding is not supported by the local web API; "
            "use 127.0.0.1 or localhost"
        )
    if not _is_loopback(host):
        raise ValueError(
            "the Shadowseed web API is loopback-only; use 127.0.0.1 or localhost"
        )
    service = WebApiService(workspace)
    return ThreadingHTTPServer(
        (host, int(port)),
        make_handler(service, static_root=static_root),
    )


def serve(
    *,
    workspace: str | Path | None = None,
    host: str = DEFAULT_HOST,
    port: int = DEFAULT_PORT,
    static_root: str | Path | None = None,
) -> None:
    server = create_server(
        workspace=workspace,
        host=host,
        port=port,
        static_root=static_root,
    )
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run the local Shadowseed web API")
    parser.add_argument("--workspace", default=None)
    parser.add_argument("--host", default=DEFAULT_HOST)
    parser.add_argument("--port", type=int, default=DEFAULT_PORT)
    args = parser.parse_args(argv)
    serve(
        workspace=args.workspace,
        host=args.host,
        port=args.port,
    )
    return 0

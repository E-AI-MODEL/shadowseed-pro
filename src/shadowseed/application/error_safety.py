"""Content-minimized error rendering for production-local surfaces."""

from __future__ import annotations

import os
import re


_SECRET_ENV_FRAGMENTS = (
    "API_KEY",
    "TOKEN",
    "SECRET",
    "PASSWORD",
    "CREDENTIAL",
)
_SECRET_ASSIGNMENT_RE = re.compile(
    r"(?i)\b(api[_-]?key|access[_-]?token|auth[_-]?token|token|secret|password|credential)"
    r"\s*[:=]\s*([^\s,;]+)"
)
_AUTH_HEADER_RE = re.compile(r"(?i)(authorization\s*:\s*(?:bearer|basic)\s+)([^\s,;]+)")
_OPENAI_KEY_RE = re.compile(r"\bsk-[A-Za-z0-9_-]{8,}\b")


def _known_environment_secrets() -> tuple[str, ...]:
    values: set[str] = set()
    for name, value in os.environ.items():
        upper = name.upper()
        if not any(fragment in upper for fragment in _SECRET_ENV_FRAGMENTS):
            continue
        normalized = value.strip()
        if len(normalized) >= 4:
            values.add(normalized)
    return tuple(sorted(values, key=len, reverse=True))


def sanitize_error_text(value: object) -> str:
    """Remove credential material while retaining a useful error description."""

    text = str(value)
    for secret in _known_environment_secrets():
        text = text.replace(secret, "<redacted-secret>")
    text = _AUTH_HEADER_RE.sub(r"\1<redacted-secret>", text)
    text = _SECRET_ASSIGNMENT_RE.sub(r"\1=<redacted-secret>", text)
    text = _OPENAI_KEY_RE.sub("<redacted-secret>", text)
    return text


def sanitized_exception_line(exc: BaseException) -> str:
    """Return an exception type plus sanitized message, without traceback locals."""

    message = sanitize_error_text(exc)
    return f"{type(exc).__name__}: {message}" if message else type(exc).__name__

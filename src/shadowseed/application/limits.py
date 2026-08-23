"""Bounded input/resource policy for the single-user production-local profile.

These limits protect expensive or integrity-sensitive product paths. They are
application constraints, not Validation Gate policy. A rejected input must fail
before the corresponding runtime or persistence mutation begins.
"""

from __future__ import annotations

from pathlib import Path


MAX_MESSAGE_CHARS = 32_000
MAX_EVIDENCE_SOURCE_REF_CHARS = 4_096
MAX_EVIDENCE_NOTE_CHARS = 16_000
MAX_FEEDBACK_NOTE_CHARS = 16_000
MAX_SESSION_TITLE_CHARS = 512
MAX_MODEL_ID_CHARS = 512
MAX_BACKUP_BYTES = 512 * 1024 * 1024
MAX_PRODUCTION_SEEDS_PER_TURN = 20
MAX_NEW_TOKENS = 4_096


class ResourceLimitError(ValueError):
    """Raised before mutation when a production-local resource bound is exceeded."""


def bounded_text(value: str, *, field: str, max_chars: int, allow_empty: bool = False) -> str:
    if not isinstance(value, str):
        raise ResourceLimitError(f"{field} must be a string")
    normalized = value.strip()
    if not allow_empty and not normalized:
        raise ResourceLimitError(f"{field} must not be empty")
    if len(normalized) > max_chars:
        raise ResourceLimitError(f"{field} exceeds the production-local limit of {max_chars} characters")
    return normalized


def validate_message(value: str) -> str:
    return bounded_text(value, field="message", max_chars=MAX_MESSAGE_CHARS)


def validate_session_title(value: str) -> str:
    return bounded_text(
        value,
        field="session title",
        max_chars=MAX_SESSION_TITLE_CHARS,
        allow_empty=True,
    )


def validate_model_id(value: str | None) -> str | None:
    if value is None:
        return None
    return bounded_text(value, field="model id", max_chars=MAX_MODEL_ID_CHARS)


def validate_evidence(source_ref: str, note: str) -> tuple[str, str]:
    source = bounded_text(
        source_ref,
        field="evidence source_ref",
        max_chars=MAX_EVIDENCE_SOURCE_REF_CHARS,
    )
    rationale = bounded_text(
        note,
        field="evidence note",
        max_chars=MAX_EVIDENCE_NOTE_CHARS,
        allow_empty=True,
    )
    return source, rationale


def validate_feedback_note(note: str) -> str:
    return bounded_text(
        note,
        field="feedback note",
        max_chars=MAX_FEEDBACK_NOTE_CHARS,
        allow_empty=True,
    )


def validate_session_config(*, max_seeds_per_turn: int, max_new_tokens: int) -> None:
    if not 1 <= int(max_seeds_per_turn) <= MAX_PRODUCTION_SEEDS_PER_TURN:
        raise ResourceLimitError(
            "max_seeds_per_turn exceeds the production-local bound "
            f"of {MAX_PRODUCTION_SEEDS_PER_TURN}"
        )
    if not 1 <= int(max_new_tokens) <= MAX_NEW_TOKENS:
        raise ResourceLimitError(
            f"max_new_tokens exceeds the production-local bound of {MAX_NEW_TOKENS}"
        )


def validate_backup_file(path: str | Path) -> Path:
    source = Path(path).expanduser().resolve()
    if not source.is_file():
        raise ResourceLimitError(f"backup does not exist: {source}")
    size = source.stat().st_size
    if size > MAX_BACKUP_BYTES:
        raise ResourceLimitError(
            f"backup exceeds the production-local limit of {MAX_BACKUP_BYTES} bytes"
        )
    return source

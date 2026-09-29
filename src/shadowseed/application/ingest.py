"""Safe text/file ingestion helpers for the Shadowseed Workbench."""

from __future__ import annotations

import csv
import hashlib
import json
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


SUPPORTED_TEXT_SUFFIXES = {".txt", ".md", ".markdown", ".json", ".csv"}
DEFAULT_CHUNK_CHARS = 4000
DEFAULT_CHUNK_OVERLAP = 300
MAX_UPLOAD_BYTES = 25 * 1024 * 1024
MAX_SOURCE_BATCH_BYTES = 25 * 1024 * 1024
MAX_SOURCE_BATCH_CHUNKS = 256

# csv.field_size_limit is process-global. Configure it once instead of
# mutating/restoring it per request, which is racy when Gradio ingests CSV
# sources concurrently. Preserve a larger host-process setting if one exists.
if csv.field_size_limit() < MAX_UPLOAD_BYTES:
    csv.field_size_limit(MAX_UPLOAD_BYTES)


@dataclass(frozen=True)
class IngestChunk:
    source_name: str
    source_instance_id: str
    chunk_index: int
    text: str

    @property
    def context_ref(self) -> str:
        return (
            f"source:{self.source_name}:instance:{self.source_instance_id}:"
            f"chunk:{self.chunk_index:05d}"
        )


def _json_strings(value: object, prefix: str = "") -> list[str]:
    items: list[str] = []
    if isinstance(value, str):
        text = value.strip()
        if text:
            items.append(f"{prefix}: {text}" if prefix else text)
    elif isinstance(value, list):
        for index, item in enumerate(value):
            items.extend(_json_strings(item, f"{prefix}[{index}]" if prefix else f"[{index}]"))
    elif isinstance(value, dict):
        for key, item in value.items():
            label = f"{prefix}.{key}" if prefix else str(key)
            items.extend(_json_strings(item, label))
    return items


def read_source_file(path: str | Path) -> tuple[str, str]:
    source = Path(path)
    suffix = source.suffix.lower()
    if suffix not in SUPPORTED_TEXT_SUFFIXES:
        raise ValueError(
            f"unsupported upload type {suffix or '(none)'}; supported: "
            + ", ".join(sorted(SUPPORTED_TEXT_SUFFIXES))
        )
    if not source.is_file():
        raise ValueError(f"upload does not exist: {source.name}")
    if source.stat().st_size > MAX_UPLOAD_BYTES:
        raise ValueError(f"upload exceeds {MAX_UPLOAD_BYTES // (1024 * 1024)} MB: {source.name}")

    if suffix in {".txt", ".md", ".markdown"}:
        text = source.read_text(encoding="utf-8")
    elif suffix == ".json":
        data = json.loads(source.read_text(encoding="utf-8"))
        text = "\n".join(_json_strings(data))
    else:
        rows: list[str] = []
        with source.open("r", encoding="utf-8-sig", newline="") as handle:
            reader = csv.reader(handle)
            for row in reader:
                values = [value.strip() for value in row if value.strip()]
                if values:
                    rows.append(" | ".join(values))
        text = "\n".join(rows)

    normalized = text.strip()
    if not normalized:
        raise ValueError(f"upload contains no usable text: {source.name}")
    return source.name, normalized


def chunk_text(
    text: str,
    *,
    source_name: str,
    source_instance_id: str | None = None,
    max_chars: int = DEFAULT_CHUNK_CHARS,
    overlap_chars: int = DEFAULT_CHUNK_OVERLAP,
) -> list[IngestChunk]:
    normalized = "\n".join(line.rstrip() for line in text.replace("\r\n", "\n").split("\n")).strip()
    if not normalized:
        return []
    if max_chars < 500:
        raise ValueError("max_chars must be at least 500")
    overlap = max(0, min(int(overlap_chars), max_chars // 3))
    instance_id = source_instance_id or hashlib.sha256(
        normalized.encode("utf-8")
    ).hexdigest()[:16]

    chunks: list[IngestChunk] = []
    start = 0
    index = 0
    length = len(normalized)
    while start < length:
        hard_end = min(length, start + max_chars)
        end = hard_end
        if hard_end < length:
            window = normalized[start:hard_end]
            candidates = [
                window.rfind("\n\n"),
                window.rfind("\n"),
                window.rfind(". "),
                window.rfind("! "),
                window.rfind("? "),
            ]
            split_at = max(candidates)
            if split_at >= max_chars // 2:
                end = start + split_at + 1
        chunk = normalized[start:end].strip()
        if chunk:
            chunks.append(
                IngestChunk(
                    source_name=source_name,
                    source_instance_id=instance_id,
                    chunk_index=index,
                    text=chunk,
                )
            )
            index += 1
        if end >= length:
            break
        next_start = max(start + 1, end - overlap)
        start = next_start
    return chunks


def prepare_sources(
    *,
    pasted_text: str = "",
    file_paths: Iterable[str | Path] = (),
) -> list[IngestChunk]:
    paths = [Path(path) for path in file_paths]
    pasted_bytes = len(pasted_text.encode("utf-8"))
    file_bytes = 0
    for source in paths:
        if source.exists() and source.is_file():
            file_bytes += source.stat().st_size
    total_input_bytes = pasted_bytes + file_bytes
    if total_input_bytes > MAX_SOURCE_BATCH_BYTES:
        raise ValueError(
            "source batch exceeds "
            f"{MAX_SOURCE_BATCH_BYTES // (1024 * 1024)} MB total input limit"
        )

    chunks: list[IngestChunk] = []
    ingest_id = uuid.uuid4().hex[:12]
    source_ordinal = 0

    def source_instance_id(source_name: str, text: str) -> str:
        nonlocal source_ordinal
        source_ordinal += 1
        digest = hashlib.sha256(text.encode("utf-8")).hexdigest()[:12]
        return f"{digest}-{ingest_id}-{source_ordinal:03d}"

    if pasted_text.strip():
        normalized_paste = pasted_text.strip()
        chunks.extend(
            chunk_text(
                normalized_paste,
                source_name="pasted-text",
                source_instance_id=source_instance_id("pasted-text", normalized_paste),
            )
        )

    for path in paths:
        source_name, text = read_source_file(path)
        chunks.extend(
            chunk_text(
                text,
                source_name=source_name,
                source_instance_id=source_instance_id(source_name, text),
            )
        )
    if not chunks:
        raise ValueError("paste text or upload at least one supported file")
    if len(chunks) > MAX_SOURCE_BATCH_CHUNKS:
        raise ValueError(
            "source batch would create "
            f"{len(chunks)} chunks; maximum is {MAX_SOURCE_BATCH_CHUNKS} per ingest"
        )
    return chunks

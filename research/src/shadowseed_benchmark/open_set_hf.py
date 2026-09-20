"""Lightweight Hugging Face dataset intake for open-set seed review."""

from __future__ import annotations

import json
import os
from pathlib import Path
import re
from typing import Any
from urllib.parse import urlencode
from urllib.request import Request, urlopen


ROWS_ENDPOINT = "https://datasets-server.huggingface.co/rows"
DEFAULT_SOURCE_REGISTRY = "src/shadowseed/data/open_set_hf_sources.json"
HF_TOKEN_ENV_VARS = ("HUGGINGFACE_TOKEN", "HF_TOKEN")


def _clean_text(value: Any) -> str:
    text = str(value or "")
    return re.sub(r"\s+", " ", text).strip()


def _fallback_title(text: str) -> str:
    if not text:
        return "Untitled"
    head = re.split(r"(?<=[.!?])\s+", text, maxsplit=1)[0].strip()
    if len(head) <= 96:
        return head
    return head[:93].rstrip() + "..."


def _load_source(registry_path: str, source_id: str) -> dict[str, Any]:
    registry = json.loads(Path(registry_path).read_text(encoding="utf-8"))
    sources = registry.get("sources", [])
    for source in sources:
        if source.get("id") == source_id:
            return source
    raise ValueError(f"Unknown open-set HF source: {source_id}")


def _label_name(row: dict[str, Any], source: dict[str, Any]) -> str:
    label_text_field = source.get("label_text_field")
    if label_text_field:
        label_text = _clean_text(row.get(label_text_field))
        if label_text:
            return label_text

    label_field = source.get("label_field")
    if label_field:
        label = row.get(label_field)
        label_names = source.get("label_names", {})
        if label is not None:
            mapped = label_names.get(str(label))
            if mapped:
                return _clean_text(mapped)
            return _clean_text(label)

    return _clean_text(source.get("default_domain")) or "unknown"


def _row_to_item(source_id: str, source: dict[str, Any], row_idx: int, row: dict[str, Any]) -> dict[str, Any] | None:
    text = _clean_text(row.get(source.get("text_field", "text")))
    min_text_length = int(source.get("min_text_length", 0) or 0)
    if not text or len(text) < min_text_length:
        return None

    label_name = _label_name(row, source)
    title_field = source.get("title_field")
    title = _clean_text(row.get(title_field)) if title_field else ""
    if not title:
        title_template = source.get("title_template")
        if title_template:
            title = _clean_text(
                title_template.format(
                    label_name=label_name,
                    row_idx=row_idx,
                )
            )
    if not title:
        title = _fallback_title(text)

    domain_template = source.get("domain_template")
    if domain_template:
        domain = _clean_text(domain_template.format(label_name=label_name, row_idx=row_idx))
    else:
        domain = label_name or _clean_text(source.get("default_domain")) or "unknown"

    return {
        "id": f"{source_id.upper()}_{row_idx}",
        "title": title,
        "domain": domain,
        "text": text,
        "source_metadata": {
            "dataset": source.get("dataset"),
            "config": source.get("config"),
            "split": source.get("split"),
            "revision": source.get("revision"),
            "license": source.get("license"),
            "row_idx": row_idx,
            "label_name": label_name,
        },
    }


def _hf_headers() -> dict[str, str]:
    headers = {"User-Agent": "shadowseed-open-set-intake/0.2"}
    for env_var in HF_TOKEN_ENV_VARS:
        token = (os.getenv(env_var) or "").strip()
        if token:
            headers["Authorization"] = f"Bearer {token}"
            break
    return headers


def fetch_open_set_hf_batch(
    output_path: str,
    *,
    source_id: str = "ag_news_test",
    registry_path: str = DEFAULT_SOURCE_REGISTRY,
    limit: int = 12,
    offset: int = 0,
) -> Path:
    if limit < 1:
        raise ValueError("limit must be at least 1")
    if limit > 100:
        raise ValueError("limit must be at most 100 for a lightweight review batch")
    if offset < 0:
        raise ValueError("offset must not be negative")

    source = _load_source(registry_path, source_id)
    items: list[dict[str, Any]] = []
    cursor = offset
    seen_ids: set[int] = set()
    headers = _hf_headers()

    while len(items) < limit:
        batch_size = min(max((limit - len(items)) * 2, 10), 100)
        query = urlencode(
            {
                "dataset": source["dataset"],
                "config": source.get("config", "default"),
                "split": source.get("split", "train"),
                "offset": cursor,
                "length": batch_size,
            }
        )
        request = Request(f"{ROWS_ENDPOINT}?{query}", headers=headers)
        with urlopen(request, timeout=30) as response:
            payload = json.loads(response.read().decode("utf-8"))

        rows = payload.get("rows", [])
        if not rows:
            break

        for item in rows:
            row_idx = int(item.get("row_idx", cursor))
            if row_idx in seen_ids:
                continue
            seen_ids.add(row_idx)
            normalized = _row_to_item(source_id, source, row_idx, item.get("row", {}))
            if normalized:
                items.append(normalized)
                if len(items) >= limit:
                    break

        cursor += len(rows)
        if len(rows) < batch_size:
            break

    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(
            {
                "version": "hf-open-set-batch-0.1",
                "source": {
                    "id": source_id,
                    "dataset": source.get("dataset"),
                    "config": source.get("config", "default"),
                    "split": source.get("split", "train"),
                    "revision": source.get("revision", "main"),
                    "license": source.get("license", "unknown"),
                    "registry_path": registry_path,
                    "requested_limit": limit,
                    "requested_offset": offset,
                    "returned_count": len(items),
                    "authenticated": "Authorization" in headers,
                },
                "items": items,
            },
            indent=2,
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )
    return output

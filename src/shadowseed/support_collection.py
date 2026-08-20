"""Aggregate verified privacy-minimized Workbench support bundles for research."""

from __future__ import annotations

import hashlib
import json
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

from shadowseed.application.exports import verify_workbench_export


SUPPORT_DATASET_SCHEMA = "shadowseed-support-dataset-v1"


class SupportCollectionError(ValueError):
    """Raised when support bundles cannot form one valid collection."""


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _read_json(archive: zipfile.ZipFile, name: str) -> dict[str, Any]:
    try:
        value = json.loads(archive.read(name))
    except (KeyError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise SupportCollectionError(f"invalid {name} in support bundle") from exc
    if not isinstance(value, dict):
        raise SupportCollectionError(f"{name} must contain a JSON object")
    return value


def collect_support_bundles(
    paths: Iterable[str | Path],
    *,
    collection_id: str,
) -> dict[str, Any]:
    """Verify and combine support bundles without adding conversation free text."""

    if not isinstance(collection_id, str) or not collection_id.strip():
        raise SupportCollectionError("collection_id must be a non-empty string")

    records: list[dict[str, Any]] = []
    seen_sessions: set[str] = set()
    for source in sorted((Path(path).expanduser().resolve() for path in paths), key=str):
        verification = verify_workbench_export(source)
        if verification["kind"] != "support":
            raise SupportCollectionError(f"not a support bundle: {source}")

        with zipfile.ZipFile(source, "r") as archive:
            manifest = _read_json(archive, "manifest.json")
            support = _read_json(archive, "support.json")
            environment = _read_json(archive, "environment.json")
            config = _read_json(archive, "config.json")

        support_session_id = support.get("support_session_id")
        if not isinstance(support_session_id, str) or not support_session_id.startswith(
            "support::"
        ):
            raise SupportCollectionError(f"invalid support session id: {source}")
        if support_session_id in seen_sessions:
            raise SupportCollectionError(
                f"duplicate support session id: {support_session_id}"
            )
        seen_sessions.add(support_session_id)

        records.append(
            {
                "support_session_id": support_session_id,
                "bundle_sha256": _sha256(source),
                "export_created_at": manifest.get("created_at"),
                "environment": environment,
                "config": config,
                "support": support,
            }
        )

    records.sort(key=lambda item: item["support_session_id"])
    return {
        "schema": SUPPORT_DATASET_SCHEMA,
        "collection_id": collection_id.strip(),
        "created_at": datetime.now(timezone.utc).isoformat(),
        "bundle_count": len(records),
        "shadowseed_versions": sorted(
            {
                str(record["environment"].get("shadowseed_version", "unknown"))
                for record in records
            }
        ),
        "records": records,
    }


def write_support_dataset(
    paths: Iterable[str | Path],
    *,
    collection_id: str,
    output: str | Path,
) -> Path:
    """Write one JSON dataset atomically after all input bundles verify."""

    payload = collect_support_bundles(paths, collection_id=collection_id)
    target = Path(output).expanduser().resolve()
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = target.with_suffix(target.suffix + ".tmp")
    temporary.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    temporary.replace(target)
    return target

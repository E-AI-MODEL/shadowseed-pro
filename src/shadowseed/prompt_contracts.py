"""Versioned metadata for live Shadowseed language contracts."""

from __future__ import annotations

import hashlib
from typing import Any


def prompt_contract_metadata(
    *,
    prompt_id: str,
    prompt_version: str,
    component: str,
    template: str,
) -> dict[str, Any]:
    """Return stable audit metadata for one prompt template.

    The hash covers the template contract, not user content. This lets a turn
    identify the exact language contract without storing another copy of the
    rendered prompt in audit metadata.
    """

    normalized = template.strip().replace("\r\n", "\n")
    return {
        "prompt_id": prompt_id,
        "prompt_version": prompt_version,
        "component": component,
        "template_sha256": hashlib.sha256(normalized.encode("utf-8")).hexdigest(),
    }

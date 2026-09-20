"""Stable identifiers shared by the product CLI and research tooling.

This module intentionally contains metadata only. Product/runtime imports may
depend on it without importing the research/evaluation implementation.
"""

from __future__ import annotations

SUPPORTED_DETECTORS: tuple[str, ...] = ("adapter_v1", "adapter_v2", "model")

__all__ = ["SUPPORTED_DETECTORS"]

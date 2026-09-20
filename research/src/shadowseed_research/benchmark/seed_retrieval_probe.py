"""Compatibility import path for a historical module.

Authority: COMPATIBILITY_ONLY
Canonical module: shadowseed.retrieval_probe

This module contains no implementation.
Do not add new behavior here. New internal code must import from the
canonical module above.
"""
from shadowseed.retrieval_probe import (
    EmbedFn,
    centroid_of,
    retrieval_probe_vs_question,
    run_seed_retrieval_probe,
)

__all__ = [
    "EmbedFn",
    "centroid_of",
    "retrieval_probe_vs_question",
    "run_seed_retrieval_probe",
]

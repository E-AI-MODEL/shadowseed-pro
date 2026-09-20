"""Compatibility import path for a historical module.

Authority: COMPATIBILITY_ONLY
Canonical module: shadowseed.recurrence_clustering

This module contains no implementation.
Do not add new behavior here. New internal code must import from the
canonical module above.
"""
from shadowseed.recurrence_clustering import (
    DEFAULT_CLUSTER_THRESHOLD,
    RecurrenceClusterer,
    auto_calibrated_min_occurrences,
)

__all__ = [
    "DEFAULT_CLUSTER_THRESHOLD",
    "RecurrenceClusterer",
    "auto_calibrated_min_occurrences",
]

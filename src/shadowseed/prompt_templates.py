"""Compatibility import path for a historical module.

Authority: COMPATIBILITY_ONLY
Canonical module: shadowseed.prompts

This module contains no implementation.
Do not add new behavior here. New internal code must import from the
canonical module above.
"""
from shadowseed.prompts import (
    DETECTION_PASS,
    DIALECTICAL_PROBE,
    SEED_NORMALIZATION,
    SOCRATIC_PROBE,
)

__all__ = [
    "DETECTION_PASS",
    "DIALECTICAL_PROBE",
    "SEED_NORMALIZATION",
    "SOCRATIC_PROBE",
]

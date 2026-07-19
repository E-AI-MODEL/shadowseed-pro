"""Compatibility import path for a historical module.

Authority: COMPATIBILITY_ONLY
Canonical module: shadowseed.detection.model_detector

This module contains no implementation.
Do not add new behavior here. New internal code must import from the
canonical module above.
"""
from shadowseed.detection.model_detector import (
    OPEN_SET_DETECTION_PROMPT,
    OPEN_SET_GENERATIVE_DETECTOR_ID,
    OPEN_SET_GENERATIVE_PROMPT,
    OPEN_SET_MODEL_DETECTOR_ID,
    OPEN_SET_MODEL_DETECTOR_SOURCE,
    PROMPT_VARIANTS,
    SUPPORTED_MODEL_BACKENDS,
    DetectorBackend,
    FixtureDetectorBackend,
    HFTransformersDetectorBackend,
    OllamaDetectorBackend,
    OpenAIDetectorBackend,
    build_detection_prompt,
    make_detector_backend,
    parse_numbered_seeds,
)

__all__ = [
    "OPEN_SET_DETECTION_PROMPT",
    "OPEN_SET_GENERATIVE_DETECTOR_ID",
    "OPEN_SET_GENERATIVE_PROMPT",
    "OPEN_SET_MODEL_DETECTOR_ID",
    "OPEN_SET_MODEL_DETECTOR_SOURCE",
    "PROMPT_VARIANTS",
    "SUPPORTED_MODEL_BACKENDS",
    "DetectorBackend",
    "FixtureDetectorBackend",
    "HFTransformersDetectorBackend",
    "OllamaDetectorBackend",
    "OpenAIDetectorBackend",
    "build_detection_prompt",
    "make_detector_backend",
    "parse_numbered_seeds",
]

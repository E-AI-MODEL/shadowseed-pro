"""Runtime seed-detection backends."""

from shadowseed.detection.model_detector import (
    DetectorBackend,
    FixtureDetectorBackend,
    HFTransformersDetectorBackend,
    OllamaDetectorBackend,
    OpenAIDetectorBackend,
    make_detector_backend,
)

__all__ = [
    "DetectorBackend",
    "FixtureDetectorBackend",
    "HFTransformersDetectorBackend",
    "OllamaDetectorBackend",
    "OpenAIDetectorBackend",
    "make_detector_backend",
]

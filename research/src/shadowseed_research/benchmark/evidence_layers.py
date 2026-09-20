"""Canonical evidence-layer labels for benchmark and review artifacts.

These constants keep artifact ownership explicit without introducing a parallel
pipeline. Existing SSL routes remain responsible for producing the artifacts.
"""

from __future__ import annotations


REGRESSION = "regression"
SMALL_BENCHMARK = "small_benchmark"
OPEN_SET_SEED_QUALITY = "open_set_seed_quality"
ADVERSARIAL_NOISE_CONTROL = "adversarial_noise_control"
PROBE_UTILITY = "probe_utility"
DOMAIN_TRANSFER = "domain_transfer"

VALID_LAYERS = frozenset(
    {
        REGRESSION,
        SMALL_BENCHMARK,
        OPEN_SET_SEED_QUALITY,
        ADVERSARIAL_NOISE_CONTROL,
        PROBE_UTILITY,
        DOMAIN_TRANSFER,
    }
)


def assert_valid_layer(layer: str) -> str:
    if layer not in VALID_LAYERS:
        raise ValueError(
            f"Unknown evidence_layer '{layer}'. Valid layers: {sorted(VALID_LAYERS)}"
        )
    return layer

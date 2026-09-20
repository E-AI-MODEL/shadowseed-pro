"""Compatibility bridge for historical shadowseed.benchmark imports.

Canonical research and evaluation code lives in the repository-only
shadowseed_benchmark package under research/. Product distributions retain
only this bridge and the documented runtime compatibility facades.
"""

from __future__ import annotations

try:
    import shadowseed_benchmark as _research
except ModuleNotFoundError:
    _research = None

if _research is not None:
    for _research_path in _research.__path__:
        if _research_path not in __path__:
            __path__.append(_research_path)

_LEGACY_EXPORTS = {
    "AbsenceBenchPreparation",
    "AbsenceBenchRunCard",
    "AbsenceBenchRunner",
    "BenchmarkPlan",
    "BenchmarkResult",
    "BenchmarkRunner",
    "ExecutionDecision",
    "ExecutionStatus",
    "HostStatus",
    "HostVerification",
    "ResultWriter",
    "RunType",
    "RunnerStatus",
    "build_host_verification",
    "build_preparation_record",
    "build_run_card",
    "load_gap_test_suite",
    "resolve_execution_status",
}


def __getattr__(name: str):
    if name not in _LEGACY_EXPORTS or _research is None:
        raise AttributeError(name)
    return getattr(_research, name)


__all__ = sorted(_LEGACY_EXPORTS)

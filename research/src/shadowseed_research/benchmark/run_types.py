"""Shared benchmark enums for Shadow Seed Learning."""

from __future__ import annotations

from enum import Enum


class RunType(str, Enum):
    SCAN = "benchmark_scan"
    PREPARATION = "benchmark_preparation"
    LIVE = "live_benchmark"


class ExecutionStatus(str, Enum):
    SCAN = "benchmark_scan"
    PREPARATION = "benchmark_preparation"
    EXECUTION_GAP = "execution_gap"
    LIVE = "live_benchmark"


class HostStatus(str, Enum):
    UNVERIFIED = "unverified"
    PRESENT = "present"
    VERIFIED = "verified"
    OUTDATED = "outdated"


class RunnerStatus(str, Enum):
    UNVERIFIED = "unverified"
    STRUCTURE_PRESENT = "structure_present"
    VERIFIED = "verified"
    OUTDATED = "outdated"
    BLOCKED = "blocked"

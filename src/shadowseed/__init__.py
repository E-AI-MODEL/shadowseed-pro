"""Shadow Seed Learning 4.6 package."""

from .manager import (
    CandidateType,
    Constellation,
    SeedOrigin,
    SeedStatus,
    ShadowSeed,
    SSLManager,
)
from .gate.runtime_adapter import install_gate_runtime_adapter

install_gate_runtime_adapter()

__all__ = [
    "SSLManager",
    "ShadowSeed",
    "SeedStatus",
    "SeedOrigin",
    "CandidateType",
    "Constellation",
]

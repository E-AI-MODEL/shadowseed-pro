"""Stable hashing helpers for deterministic local embeddings.

Python's built-in ``hash()`` is process-randomized, which makes it unsuitable
for benchmark embeddings that should stay stable across subprocesses and CI
runs. These helpers provide fixed bucket assignment for lexical scaffold code.
"""

from __future__ import annotations

import hashlib


def stable_bucket_index(token: str, dimensions: int) -> int:
    if dimensions <= 0:
        raise ValueError("dimensions must be positive")
    digest = hashlib.blake2b(token.encode("utf-8"), digest_size=8).digest()
    return int.from_bytes(digest, "big") % dimensions

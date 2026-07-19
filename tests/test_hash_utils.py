from __future__ import annotations

import subprocess
import sys

from shadowseed.hash_utils import stable_bucket_index


def test_stable_bucket_index_is_repeatable() -> None:
    assert stable_bucket_index("koloniaal", 128) == stable_bucket_index("koloniaal", 128)


def test_stable_bucket_index_is_stable_across_processes() -> None:
    code = "from shadowseed.hash_utils import stable_bucket_index; print(stable_bucket_index('koloniaal', 128))"
    first = subprocess.check_output([sys.executable, "-c", code], text=True).strip()
    second = subprocess.check_output([sys.executable, "-c", code], text=True).strip()

    assert first == second


def test_stable_bucket_index_rejects_invalid_dimensions() -> None:
    try:
        stable_bucket_index("token", 0)
    except ValueError as exc:
        assert "dimensions must be positive" in str(exc)
    else:
        raise AssertionError("stable_bucket_index should reject non-positive dimensions")

"""Guard against the results/open_review artifact-set drift Codex found on #128.

The HF-review workflow commits only the summary set
(open_set_seed_review_summary.json + disagreements + report + README). The
per-item packets and raw seed output are transient: regenerated each run,
uploaded as Actions artifacts, and curated per round under
benchmarks/open_review/rounds/. Tracking them in results/open_review/ froze
them at the PR #76 state while the summary advanced, leaving an incoherent set.

These tests lock the fix: the two transient files are gitignored and not
tracked, so they cannot be re-committed stale.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

TRANSIENT = (
    "results/open_review/open_set_review_packets.json",
    "results/open_review/open_set_seed_output.json",
)


def test_transient_open_review_files_are_gitignored() -> None:
    ignore = Path(".gitignore").read_text(encoding="utf-8").splitlines()
    for path in TRANSIENT:
        assert path in ignore, f"{path} must stay gitignored to prevent stale drift"


def test_transient_open_review_files_are_not_tracked() -> None:
    result = subprocess.run(
        ["git", "ls-files", "results/open_review/"],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode == 0:
        tracked = result.stdout.split()
        for path in TRANSIENT:
            assert path not in tracked, (
                f"{path} is tracked again; it can drift stale because the workflow "
                "never commits it"
            )
        return

    # Source archives do not contain .git metadata. In that case the same
    # invariant is testable from the archive contents and .gitignore.
    for path in TRANSIENT:
        assert not Path(path).exists(), f"{path} must not be shipped in a source archive"

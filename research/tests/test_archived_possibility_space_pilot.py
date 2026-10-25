"""Keep the retired v0 possibility-space pilot's offline controls in CI.

Historical formal graph mechanics only. This test performs zero model calls and
cannot validate either clause of the current Shadowseed research thesis.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path


ARCHIVE = Path("experiments/possibility_space")


def test_retired_pilot_unittests_stay_green_without_provider_credentials():
    env = dict(os.environ)
    env.pop("OPENAI_API_KEY", None)
    env.pop("OPENAI_KEY", None)
    done = subprocess.run(
        [
            sys.executable, "-m", "unittest", "discover", "-s", str(ARCHIVE),
            "-p", "test_pilot.py", "-v",
        ],
        env=env, check=False, capture_output=True, text=True, timeout=90,
    )
    assert done.returncode == 0, done.stdout + "\n" + done.stderr


def test_retired_pilot_offline_oracle_has_no_model_calls(tmp_path: Path):
    output = tmp_path / "archived-offline.json"
    env = dict(os.environ)
    env.pop("OPENAI_API_KEY", None)
    env.pop("OPENAI_KEY", None)
    done = subprocess.run(
        [sys.executable, str(ARCHIVE / "pilot.py"), "selftest", "--output", str(output)],
        env=env, check=False, capture_output=True, text=True, timeout=90,
    )
    assert done.returncode == 0, done.stdout + "\n" + done.stderr
    result = json.loads(output.read_text(encoding="utf-8"))
    assert result["status"] == "passed"
    assert result["model_calls"] == 0
    assert result["this_is_not_model_evidence"] is True


def test_archive_actions_workflow_does_not_use_credentials_or_paid_run():
    workflow = Path(".github/workflows/possibility-space-pilot.yml").read_text(
        encoding="utf-8"
    )
    assert "workflow_dispatch:" in workflow
    assert "python pilot.py selftest" in workflow
    assert "python -m unittest" in workflow
    assert "OPENAI_API_KEY" not in workflow
    assert "OPENAI_KEY" not in workflow

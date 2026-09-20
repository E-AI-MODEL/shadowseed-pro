from __future__ import annotations

import os
from pathlib import Path
import sys

_REPO_ROOT = Path(__file__).resolve().parents[1]
_RESEARCH_SRC = _REPO_ROOT / "research" / "src"

if str(_RESEARCH_SRC) not in sys.path:
    sys.path.insert(0, str(_RESEARCH_SRC))

_existing = os.environ.get("PYTHONPATH")
os.environ["PYTHONPATH"] = (
    str(_RESEARCH_SRC)
    if not _existing
    else str(_RESEARCH_SRC) + os.pathsep + _existing
)

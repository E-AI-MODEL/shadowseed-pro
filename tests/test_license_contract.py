from __future__ import annotations

from pathlib import Path


def test_repository_ships_canonical_noncommercial_terms_and_notice() -> None:
    text = Path("LICENSE").read_text(encoding="utf-8")
    assert text.startswith("# PolyForm Noncommercial License 1.0.0\n")
    assert "https://polyformproject.org/licenses/noncommercial/1.0.0" in text
    assert "Required Notice: Copyright 2026 H. Visser / E-AI-MODEL." in text
    assert "## Noncommercial Purposes" in text
    assert "## Noncommercial Organizations" in text
    assert "## No Liability" in text
    assert "Historical artifacts distributed without this license" in text


def test_readme_does_not_claim_osi_open_source() -> None:
    readme = Path("README.md").read_text(encoding="utf-8")
    assert "PolyForm Noncommercial License 1.0.0" in readme
    assert "This is not an OSI open-source license" in readme
    assert "All rights are reserved. Public visibility is not permission for reuse." not in readme

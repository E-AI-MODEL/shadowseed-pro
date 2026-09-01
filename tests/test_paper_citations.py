"""Citation guards for the manuscript bibliography (issue #116).

A published claim of scientific grounding is only as good as the weakest entry
in its bibliography. These guards keep three things true:

1. every bibliography entry has a verification record;
2. every entry is actually cited in the manuscript;
3. every citation in the manuscript resolves to an entry.

They check bookkeeping, not correctness of the cited work. Whether a source
supports the sentence citing it remains a human review question.
"""

from __future__ import annotations

import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BIB = (ROOT / "paper/references.bib").read_text(encoding="utf-8")
MANUSCRIPT = (ROOT / "paper/main.tex").read_text(encoding="utf-8")
VERIFICATION = (ROOT / "paper/references-verification.md").read_text(encoding="utf-8")

_ENTRY = re.compile(r"^@[A-Za-z]+\{([^,\s]+)\s*,", re.M)
_CITE = re.compile(r"\\cite[a-zA-Z]*\*?(?:\[[^\]]*\])*\{([^}]+)\}")


def bibliography_keys() -> set[str]:
    return set(_ENTRY.findall(BIB))


def cited_keys() -> set[str]:
    keys: set[str] = set()
    for group in _CITE.findall(MANUSCRIPT):
        keys.update(key.strip() for key in group.split(",") if key.strip())
    return keys


def test_bibliography_is_not_empty() -> None:
    # Guards against a regex that silently matches nothing and makes every
    # other assertion in this module vacuously true.
    assert len(bibliography_keys()) >= 20
    assert len(cited_keys()) >= 20


def test_every_bibliography_entry_has_a_verification_record() -> None:
    missing = sorted(
        key for key in bibliography_keys() if f"`{key}`" not in VERIFICATION
    )

    assert not missing, (
        "bibliography entries without a record in paper/references-verification.md:\n"
        + "\n".join(missing)
    )


def test_every_bibliography_entry_is_cited() -> None:
    orphans = sorted(bibliography_keys() - cited_keys())

    assert not orphans, "bibliography entries never cited in main.tex:\n" + "\n".join(
        orphans
    )


def test_every_citation_resolves_to_an_entry() -> None:
    dangling = sorted(cited_keys() - bibliography_keys())

    assert not dangling, "citations with no bibliography entry:\n" + "\n".join(dangling)


def test_verification_record_states_its_own_limits() -> None:
    # The record must keep saying how it was produced. A verification artifact
    # that drops its method is an assertion, not evidence.
    assert "## Method and its limits" in VERIFICATION
    assert "venue-confirmed" in VERIFICATION
    assert "preprint-confirmed" in VERIFICATION

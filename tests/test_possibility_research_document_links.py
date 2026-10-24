"""Keep the active possibility-space research map navigable.

This checks repository-relative Markdown file references, not scientific validity,
external link reachability, or whether a human reviewer approved G0.
"""

from __future__ import annotations

import re
from pathlib import Path
from urllib.parse import unquote


ROOT = Path(__file__).resolve().parents[1]
RESEARCH = ROOT / "docs/research/possibility-space"
LINK = re.compile(r"(?<!!)\]\(([^)\n]+)\)")


def test_internal_possibility_space_markdown_links_exist() -> None:
    missing: list[str] = []
    docs = sorted(RESEARCH.rglob("*.md"))
    assert docs, "Expected a nonempty possibility-space research directory"

    for doc in docs:
        body = doc.read_text(encoding="utf-8")
        body = re.sub(r"```.*?```", "", body, flags=re.DOTALL)
        for raw in LINK.findall(body):
            target = raw.strip().split(" ", maxsplit=1)[0].strip("<>")
            if not target or target.startswith(("#", "http://", "https://", "mailto:")):
                continue
            target = unquote(target.split("#", maxsplit=1)[0])
            resolved = (doc.parent / target).resolve()
            if not resolved.is_file() or not resolved.is_relative_to(ROOT):
                missing.append(f"{doc.relative_to(ROOT)} -> {target}")

    assert not missing, "Broken local research links:\n" + "\n".join(missing)


def test_study_contract_and_unapproved_independent_review_are_explicit() -> None:
    thesis = (ROOT / "docs/research/possibility-space-thesis.md").read_text(
        encoding="utf-8"
    )
    rubric = (RESEARCH / "g0/dynamic-inquiry-independent-review.md").read_text(
        encoding="utf-8"
    )
    index = (RESEARCH / "README.md").read_text(encoding="utf-8")
    contract = (RESEARCH / "g0/adapter-evaluation-contract-2026-10-25.md").read_text(
        encoding="utf-8"
    )

    assert "En kunnen we onderzoeken hoe nieuwe mogelijkheden ontstaan" in thesis
    assert "UNFILLED" in rubric
    assert "G0" in index and "NOT PASSED" in index
    assert "A — ordinary" in contract
    assert "D — actual weightless store" in contract
    assert "E — matched ablation/sham" in contract

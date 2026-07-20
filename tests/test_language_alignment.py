"""Repository English-alignment check (issue #16).

Enforces English as the canonical language of the core runtime modules' prose
(comments, docstrings, messages), while explicitly allowing the documented
Dutch input-language tokens retained for the historical research corpus.

Scope is the core runtime, not benchmark suites or JSON data fixtures: those
carry historical research data whose Dutch content is preserved to avoid
altering benchmark meaning (see docs/migration/language-policy.md).
"""

from __future__ import annotations

import pathlib
import re

SRC = pathlib.Path(__file__).resolve().parents[1] / "src"

# Core runtime modules that must read as English prose.
CORE_MODULES = [
    "shadowseed/manager.py",
    "shadowseed/chat.py",
    "shadowseed/surfacing.py",
    "shadowseed/ssot.py",
    "shadowseed/recurrence.py",
    "shadowseed/retrieval_probe.py",
    "shadowseed/core_config.py",
    "shadowseed/seed_normalization.py",
    "shadowseed/gate/signals.py",
    "shadowseed/gate/policies.py",
    "shadowseed/gate/events.py",
    "shadowseed/gate/contradictions.py",
    "shadowseed_agent/agent_contract.py",
    "shadowseed_agent/audit_policy.py",
    "shadowseed_agent/retrieval_policy.py",
]

# Documented Dutch input-language tokens (data, not user-facing prose): the
# atomic-seed heuristics and the seed-normalization tokens. Permitted anywhere.
ALLOWED_DUTCH_TOKENS = {
    "en", "of", "zoals", "bijvoorbeeld", "analysekader", "oorzaken", "gevolgen",
    "contexten", "perspectieven", "meerdere", "schaalbaarheid", "kolonialisme",
    "ontbreekt", "ontbreken", "ontbrekende", "voeg", "toe", "aandacht", "let",
    "op", "onderdelen", "volledig", "een", "met", "voor",
}

# High-confidence Dutch prose words that should never appear in core prose.
# These are distinctive enough that a match reliably signals untranslated text.
DUTCH_PROSE_MARKERS = {
    "installeer", "gebruiken", "gebruikt", "zonder", "gewicht", "eigenaar",
    "medische", "niet", "koloniaal", "kapitaal", "deze", "wordt", "worden",
    "naar", "hierdoor", "daarom", "echter", "aangezien", "waardoor",
}

_WORD = re.compile(r"[A-Za-zÀ-ÿ]+")


def test_core_modules_are_english_prose():
    offenders: list[str] = []
    for rel in CORE_MODULES:
        path = SRC / rel
        for lineno, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
            for word in _WORD.findall(line):
                lowered = word.lower()
                if lowered in DUTCH_PROSE_MARKERS and lowered not in ALLOWED_DUTCH_TOKENS:
                    offenders.append(f"{rel}:{lineno} {word!r}")
    assert not offenders, "Dutch prose found in core runtime modules: " + ", ".join(offenders)


def test_allowlist_and_markers_are_disjoint():
    # A token cannot be both a forbidden marker and an allowed alias.
    assert not (DUTCH_PROSE_MARKERS & ALLOWED_DUTCH_TOKENS)

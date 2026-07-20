"""Repository English-alignment check (issue #16).

Enforces English as the canonical language of the core runtime by inspecting the
prose (comments and string literals) of every auto-discovered core module via
the ``tokenize`` module. It applies:

- exact forbidden-phrase checks for known regressions;
- a curated distinctive-Dutch vocabulary;
- path-specific allowed literals for documented Dutch input-language tokens.

Scope note: the automated strict scan covers the core runtime packages
(``shadowseed`` excluding ``benchmark/`` and ``data/``, plus ``shadowseed_agent``).
Benchmark suites and JSON fixtures retain documented Dutch content so benchmark
meaning and historical results are not altered — see
``docs/migration/language-policy.md``. This test therefore substantiates an
English-core claim, not a whole-repository one.
"""

from __future__ import annotations

import io
import pathlib
import re
import tokenize

SRC = pathlib.Path(__file__).resolve().parents[1] / "src"
CORE_ROOTS = [SRC / "shadowseed", SRC / "shadowseed_agent"]
EXCLUDE_DIR_PARTS = {"benchmark", "data", "__pycache__"}

# Exact phrases that must never reappear (regressions fixed under #16). Each is a
# compiled regex so word boundaries can be enforced where a bare substring would
# over-match (for example the old feedback prefix "OP:" must not flag "STOP:").
FORBIDDEN_PATTERNS = (
    re.compile(r"Cluster rond"),
    re.compile(r"Installeer sentence-transformers"),
    re.compile(r"te gebruiken"),
    re.compile(r"(?<![A-Za-z])OP:"),  # old feedback prefix, not "STOP:"
)

# Distinctive Dutch words (chosen to avoid English collisions such as "of"/"on").
DUTCH_VOCAB = {
    "installeer", "gebruiken", "gebruikt", "zonder", "gewicht", "eigenaar",
    "medische", "niet", "koloniaal", "kapitaal", "wordt", "worden", "hierdoor",
    "daarom", "echter", "aangezien", "waardoor", "rond", "ontbreekt", "ontbreken",
    "ontbrekende", "analysekader", "oorzaken", "gevolgen", "contexten",
    "perspectieven", "meerdere", "schaalbaarheid", "kolonialisme", "voeg",
    "aandacht", "onderdelen", "zoals", "bijvoorbeeld", "taalmodel", "houdt",
    "onbeslist", "weerlegd",
}

# Documented Dutch input-language tokens, permitted ONLY in their own files.
ALLOWED_LITERALS = {
    "shadowseed/manager.py": {
        "zoals", "bijvoorbeeld", "analysekader", "oorzaken", "gevolgen",
        "contexten", "perspectieven", "meerdere", "schaalbaarheid",
        "kolonialisme", "ontbreekt", "ontbreken",
    },
    "shadowseed/seed_normalization.py": {
        "ontbreekt", "ontbreken", "ontbrekende", "voeg", "aandacht",
        "onderdelen", "zoals", "bijvoorbeeld", "analysekader", "schaalbaarheid",
        "kolonialisme",
    },
}

_WORD = re.compile(r"[A-Za-zÀ-ÿ]+")


def _core_modules() -> list[pathlib.Path]:
    modules: list[pathlib.Path] = []
    for root in CORE_ROOTS:
        for path in root.rglob("*.py"):
            rel_parts = path.relative_to(SRC).parts
            if any(part in EXCLUDE_DIR_PARTS for part in rel_parts):
                continue
            modules.append(path)
    return modules


def _prose(path: pathlib.Path) -> str:
    """Return the concatenated comment and string-literal text of a module."""

    chunks: list[str] = []
    data = path.read_text(encoding="utf-8")
    for tok in tokenize.generate_tokens(io.StringIO(data).readline):
        if tok.type in (tokenize.COMMENT, tokenize.STRING):
            chunks.append(tok.string)
    return "\n".join(chunks)


def test_core_modules_have_no_forbidden_phrases():
    offenders: list[str] = []
    for path in _core_modules():
        prose = _prose(path)
        rel = path.relative_to(SRC).as_posix()
        for pattern in FORBIDDEN_PATTERNS:
            if pattern.search(prose):
                offenders.append(f"{rel}: {pattern.pattern!r}")
    assert not offenders, "forbidden Dutch phrase(s): " + ", ".join(offenders)


def test_core_modules_are_english_prose():
    offenders: list[str] = []
    for path in _core_modules():
        rel = path.relative_to(SRC).as_posix()
        allowed = ALLOWED_LITERALS.get(rel, set())
        for word in _WORD.findall(_prose(path)):
            lowered = word.lower()
            if lowered in DUTCH_VOCAB and lowered not in allowed:
                offenders.append(f"{rel} {word!r}")
    assert not offenders, "Dutch prose in core runtime: " + ", ".join(sorted(set(offenders)))


def test_auto_discovery_covers_known_core_modules():
    # Guards against silent under-coverage if discovery breaks.
    discovered = {p.relative_to(SRC).as_posix() for p in _core_modules()}
    for expected in (
        "shadowseed/manager.py",
        "shadowseed/chat.py",
        "shadowseed/surfacing.py",
        "shadowseed/gate/policies.py",
        "shadowseed_agent/agent_contract.py",
    ):
        assert expected in discovered
    # Benchmark/data are excluded from the strict scan.
    assert not any(part in EXCLUDE_DIR_PARTS for p in discovered for part in p.split("/"))


# -- self-tests of the checker (synthetic fixtures, not repository files) -----


def _scan_text(text: str, rel: str = "shadowseed/_fixture.py") -> list[str]:
    allowed = ALLOWED_LITERALS.get(rel, set())
    hits = []
    prose = "\n".join(
        tok.string
        for tok in tokenize.generate_tokens(io.StringIO(text).readline)
        if tok.type in (tokenize.COMMENT, tokenize.STRING)
    )
    for word in _WORD.findall(prose):
        if word.lower() in DUTCH_VOCAB and word.lower() not in allowed:
            hits.append(word)
    for pattern in FORBIDDEN_PATTERNS:
        if pattern.search(prose):
            hits.append(pattern.pattern)
    return hits


def test_checker_flags_cluster_rond_regression():
    assert _scan_text('x = "Cluster rond iets"\n')


def test_checker_flags_old_feedback_prefix():
    hits = _scan_text('x = "FEEDBACK: a OP: b"\n')
    assert any("OP:" in h for h in hits)


def test_checker_does_not_flag_stop_as_old_prefix():
    # "STOP:" contains "OP:" but must not trip the boundary-anchored pattern.
    assert _scan_text('x = "Please STOP: now"\n') == []


def test_checker_flags_arbitrary_dutch_sentence():
    assert _scan_text('# Dit wordt niet vertaald\n')


def test_checker_allows_dutch_tokens_only_in_their_files():
    snippet = '# analysekader\n'
    # Allowed inside manager.py, flagged elsewhere.
    assert not _scan_text(snippet, rel="shadowseed/manager.py")
    assert _scan_text(snippet, rel="shadowseed/chat.py")


def test_allowlist_tokens_are_in_vocabulary():
    # Every allowed literal must be a word the scan would otherwise catch,
    # otherwise the allowlist entry is dead.
    for tokens in ALLOWED_LITERALS.values():
        for token in tokens:
            assert token in DUTCH_VOCAB, token

from __future__ import annotations

from pathlib import Path


MANAGER_DOC_OLD = '''"""
Shadow Seed Learning 4.6 core manager.

This manager is the canonical Niveau-1 core for SSL. The mechanical kernel is
unchanged across 4.5 and 4.6 — see `docs/00_shadow_seed_learning_4_6.md` for
the current canonical source. It keeps four ideas explicit:

- a seed is atomic;
- trace measures presence;
- weight measures influence;
- promotion requires the Validation Gate.

The manager now also keeps explicit configuration, normalization results and
validation-event logs so benchmark runs can be reconstructed more honestly.
Stable data contracts live in :mod:`shadowseed.models` and are re-exported here
for backward compatibility.
"""
'''

MANAGER_DOC_NEW = '''"""Shadow Seed Learning 4.6 orchestration and compatibility facade.

``SSLManager`` owns runtime configuration, the seed registry, audit logs,
serialization, and the guarded authority-field mutation primitive. Focused
canonical modules own the executable concerns that were formerly embedded here:

- :mod:`shadowseed.models` owns stable data contracts;
- :mod:`shadowseed.intake` owns embedding, normalization, and deduplication;
- :mod:`shadowseed.lifecycle` owns TTL, dormancy, TrTL, and expiry;
- :mod:`shadowseed.contradictions` owns contradiction records and lifecycle;
- :mod:`shadowseed.vector_workflows` owns vector search and constellations;
- :mod:`shadowseed.gate.runtime_adapter` owns Gate-controlled decisions.

Historical methods and model imports remain available through this module and
delegate to those canonical implementations.
"""
'''

AUTHORITY_DOC_OLD = '''        """The single production authority-transition path.

        Every runtime authority change (validation, contradiction, probe
        feedback, decay/expiry, lifecycle status moves) goes through here. #12
        migrates the callers to feed this from typed signals and a named policy;
        #11 establishes that no runtime code writes authority fields directly.
        """
'''

AUTHORITY_DOC_NEW = '''        """Guarded mutation primitive for seed authority fields.

        Gate-controlled decisions are made in ``shadowseed.gate``. Explicit
        mechanical intake and lifecycle transitions are made in their canonical
        modules. Both categories apply the resulting field changes through this
        primitive, so no runtime path writes guarded fields directly.
        """
'''

AUTHORITY_ENTRIES = '''  - path: src/shadowseed/manager.py
    authority: RUNTIME_IMPLEMENTATION
    owner: core-orchestration
    runtime_import_allowed: true
    modifications_allowed: true
    notes: >
      SSLManager configuration/state registry, audit logs, serialization,
      guarded authority mutation primitive, and compatibility method facade.
      Focused domain logic belongs in the explicit canonical modules below.

  - path: src/shadowseed/models.py
    authority: RUNTIME_IMPLEMENTATION
    owner: data-contracts
    runtime_import_allowed: true
    modifications_allowed: true
    notes: Stable enums, dataclasses, serialization, and authority-field guards.

  - path: src/shadowseed/contradictions.py
    authority: RUNTIME_IMPLEMENTATION
    owner: contradiction-domain
    runtime_import_allowed: true
    modifications_allowed: true
    notes: Contradiction record collection, blocking state, resolution, and migration.

  - path: src/shadowseed/intake.py
    authority: RUNTIME_IMPLEMENTATION
    owner: intake
    runtime_import_allowed: true
    modifications_allowed: true
    notes: Embedding, atomicity heuristics, candidate normalization, deduplication, and creation.

  - path: src/shadowseed/lifecycle.py
    authority: RUNTIME_IMPLEMENTATION
    owner: lifecycle
    runtime_import_allowed: true
    modifications_allowed: true
    notes: TTL decay, dormancy, TrTL reactivation, and terminal expiry.

  - path: src/shadowseed/vector_workflows.py
    authority: RUNTIME_IMPLEMENTATION
    owner: vector-runtime
    runtime_import_allowed: true
    modifications_allowed: true
    notes: Uncertain-region search, external-feedback routing, and constellations.

  - path: src/shadowseed/gate/**
    authority: RUNTIME_IMPLEMENTATION
    owner: validation-gate
    runtime_import_allowed: true
    modifications_allowed: true
    notes: >
      Typed signals, policies, contradiction/event contracts, verified logging,
      and the single executable Gate-controlled authority-decision engine.

'''

STRUCTURE_LAYOUT_OLD = '''│   │   ├── *.py                    core runtime: chat, cli, manager, ssot,
│   │   │                           recurrence, retrieval_probe, prompts,
│   │   │                           seed_normalization, surfacing, …
│   │   ├── adapters/               model/service adapters (embedding, openai,
'''

STRUCTURE_LAYOUT_NEW = '''│   │   ├── manager.py              orchestration, registry, logs, serialization,
│   │   │                           authority mutation primitive, compatibility facade
│   │   ├── models.py               stable data contracts and authority guards
│   │   ├── contradictions.py       contradiction collection and lifecycle
│   │   ├── intake.py               embedding, normalization, dedup, seed creation
│   │   ├── lifecycle.py            TTL, dormancy, TrTL, terminal expiry
│   │   ├── vector_workflows.py     vector search, feedback routing, constellations
│   │   ├── gate/                   typed signals/policies/events + Gate engine
│   │   ├── *.py                    other core runtime: chat, cli, ssot,
│   │   │                           retrieval_probe, prompts, surfacing, …
│   │   ├── adapters/               model/service adapters (embedding, openai,
'''

RESPONSIBILITY_OLD = '''| `src/shadowseed/` top-level modules | Core SSL runtime, CLI, manager, SSOT | RUNTIME_IMPLEMENTATION |
| `src/shadowseed/adapters/` | Embedding + LLM service adapters | RUNTIME_IMPLEMENTATION |
'''

RESPONSIBILITY_NEW = '''| `src/shadowseed/manager.py` | Runtime orchestration, state registry, logs, serialization, compatibility facade | RUNTIME_IMPLEMENTATION |
| `src/shadowseed/models.py` | Stable data contracts and guarded authority fields | RUNTIME_IMPLEMENTATION |
| `src/shadowseed/contradictions.py` | Contradiction collection, blocking state, formal resolution | RUNTIME_IMPLEMENTATION |
| `src/shadowseed/intake.py` | Embedding, normalization, deduplication, seed creation/update | RUNTIME_IMPLEMENTATION |
| `src/shadowseed/lifecycle.py` | TTL, dormancy, TrTL, terminal expiry | RUNTIME_IMPLEMENTATION |
| `src/shadowseed/vector_workflows.py` | Vector search, feedback routing, constellation construction | RUNTIME_IMPLEMENTATION |
| `src/shadowseed/gate/` | Typed Gate contracts, policies, logging, executable decision engine | RUNTIME_IMPLEMENTATION |
| Other `src/shadowseed/*.py` modules | Chat, CLI, SSOT, surfacing, probes, prompts | RUNTIME_IMPLEMENTATION |
| `src/shadowseed/adapters/` | Embedding + LLM service adapters | RUNTIME_IMPLEMENTATION |
'''

OLD_MOVE_SECTION = '''## Why no files were physically moved

The v0.3.0 rebuild already places responsibilities under clear packages
(`adapters/`, `detection/`, `analysis/`, `vectorstore/`, `benchmark/`), and all
active runtime code already imports canonical paths — no active module imports a
compatibility facade. The remaining ambiguity was **authority legibility**, not
physical location: it was hard to tell canonical from legacy from archive.

Physical moves would have risked packaging (package-data, console entry points,
import identity) without improving that legibility. The chosen approach instead
makes authority **explicit and testable**:

- `repository-authority.yaml` — machine-readable classification of every area;
- explicit `COMPATIBILITY_ONLY` headers + `__all__` on all facades;
- visible historical banners on archive documentation;
- a canonical-first artifact-precedence guard.

Public APIs, CLI entry points, packaging, and benchmark semantics are unchanged.

## Packaging impact

None. `pyproject.toml` discovers packages from `src/` only, so `archive/`,
`benchmarks/`, `scripts/`, and `experiments/` are never packaged. Package-data
(`shadowseed/data/*.json`) is unchanged. Editable install, wheel build, and the
`shadowseed` console entry point all continue to work.
'''

NEW_MOVE_SECTION = '''## Manager modularization

The original `manager.py` combined data contracts, contradiction workflows,
Gate execution, intake, lifecycle, vector search, constellation construction,
and probe feedback. Those concerns were moved in bounded, behavior-preserving
steps while `SSLManager` kept its historical methods as explicit facades:

1. `shadowseed.models` — stable data contracts;
2. `shadowseed.contradictions` — contradiction state and record lifecycle;
3. `shadowseed.intake` — embedding, normalization, deduplication, creation;
4. `shadowseed.lifecycle` — TTL, dormancy, TrTL, expiry;
5. `shadowseed.vector_workflows` — vector search, feedback, constellations;
6. `shadowseed.gate.runtime_adapter` — Gate-controlled authority decisions.

`manager.py` now owns configuration, the live seed registry, audit collections,
serialization, the guarded authority mutation primitive, and compatibility
method routing. Contract tests pin delegation, import identity, authority
boundaries, and a size ceiling so the former monolith cannot silently return.

## Packaging impact

The new modules are ordinary `src/shadowseed/*.py` runtime modules and are
discovered automatically by the existing package configuration. Public manager
imports, CLI entry points, package data, editable installation, and wheel
installation remain unchanged. `archive/`, `benchmarks/`, `scripts/`, and
`experiments/` remain outside the installed package.
'''

FINAL_TEST = r'''"""Structural completion guards for manager modularization (#25)."""

from __future__ import annotations

import ast
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE_ROOT = ROOT / "src/shadowseed"
MANAGER = SOURCE_ROOT / "manager.py"


def test_manager_stays_a_bounded_orchestration_facade() -> None:
    source = MANAGER.read_text(encoding="utf-8")
    assert len(source.splitlines()) <= 800

    tree = ast.parse(source)
    imported_modules = {
        alias.asname or alias.name
        for node in tree.body
        if isinstance(node, ast.ImportFrom) and node.module == "shadowseed"
        for alias in node.names
    }
    assert {"intake_engine", "lifecycle_engine", "vector_workflows"} <= imported_modules

    forbidden_calls = {
        ("np", "dot"),
        ("np", "mean"),
        ("np", "linalg"),
        ("math", "exp"),
        ("re", "findall"),
    }
    seen_calls: set[tuple[str, str]] = set()
    for call in ast.walk(tree):
        if not isinstance(call, ast.Call) or not isinstance(call.func, ast.Attribute):
            continue
        if isinstance(call.func.value, ast.Name):
            seen_calls.add((call.func.value.id, call.func.attr))
    assert forbidden_calls.isdisjoint(seen_calls)


def test_modularized_runtime_has_explicit_authority_ownership() -> None:
    authority = (ROOT / "repository-authority.yaml").read_text(encoding="utf-8")
    for path in (
        "src/shadowseed/manager.py",
        "src/shadowseed/models.py",
        "src/shadowseed/contradictions.py",
        "src/shadowseed/intake.py",
        "src/shadowseed/lifecycle.py",
        "src/shadowseed/vector_workflows.py",
        "src/shadowseed/gate/**",
    ):
        assert f"- path: {path}" in authority


def test_active_ownership_docs_name_the_final_boundaries() -> None:
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    overview = (ROOT / "docs/architecture/overview.md").read_text(encoding="utf-8")
    structure = (ROOT / "docs/architecture/repository-structure.md").read_text(
        encoding="utf-8"
    )

    for module in (
        "shadowseed.models",
        "shadowseed.contradictions",
        "shadowseed.intake",
        "shadowseed.lifecycle",
        "shadowseed.vector_workflows",
        "shadowseed.gate",
    ):
        assert module in readme
        assert module in overview
        assert module in structure

    assert "orchestration" in readme
    assert "orchestration" in overview
    assert "Manager modularization" in structure
'''


def replace_once(path: Path, old: str, new: str) -> None:
    text = path.read_text(encoding="utf-8")
    if text.count(old) != 1:
        raise SystemExit(f"{path}: expected one anchor, got {text.count(old)}")
    path.write_text(text.replace(old, new, 1), encoding="utf-8")


def main() -> None:
    manager = Path("src/shadowseed/manager.py")
    replace_once(manager, MANAGER_DOC_OLD, MANAGER_DOC_NEW)
    replace_once(manager, AUTHORITY_DOC_OLD, AUTHORITY_DOC_NEW)

    authority = Path("repository-authority.yaml")
    replace_once(
        authority,
        "  # --- Canonical runtime implementation ----------------------------------\n"
        "  - path: src/shadowseed/*.py\n",
        "  # --- Canonical runtime implementation ----------------------------------\n"
        + AUTHORITY_ENTRIES
        + "  - path: src/shadowseed/*.py\n",
    )
    replace_once(
        authority,
        "      Canonical top-level runtime modules (chat, cli, manager, ssot,\n"
        "      recurrence, retrieval_probe, prompts, seed_normalization, etc.).\n",
        "      Remaining canonical top-level runtime modules (chat, cli, ssot,\n"
        "      retrieval_probe, prompts, seed_normalization, surfacing, etc.).\n"
        "      Explicit domain entries above take precedence for ownership.\n",
    )

    replace_once(
        Path("README.md"),
        "| [`shadowseed.manager`](src/shadowseed/manager.py) | `SSLManager` orchestration, authority-transition facade, lifecycle, TTL, TrTL, Validation Gate facade, and feedback logs |\n",
        "| [`shadowseed.manager`](src/shadowseed/manager.py) | `SSLManager` configuration/state registry, audit logs, serialization, guarded authority mutation primitive, and compatibility facades |\n",
    )
    replace_once(
        Path("docs/architecture/overview.md"),
        "| `shadowseed.manager` | `SSLManager` orchestration, authority-transition facade, lifecycle, TTL, TrTL, Validation Gate facade, probe feedback |\n",
        "| `shadowseed.manager` | `SSLManager` configuration/state registry, audit logs, serialization, guarded authority mutation primitive, and compatibility facades |\n",
    )

    structure = Path("docs/architecture/repository-structure.md")
    replace_once(structure, STRUCTURE_LAYOUT_OLD, STRUCTURE_LAYOUT_NEW)
    replace_once(structure, RESPONSIBILITY_OLD, RESPONSIBILITY_NEW)
    replace_once(structure, OLD_MOVE_SECTION, NEW_MOVE_SECTION)

    Path("tests/test_manager_modularization_complete.py").write_text(
        FINAL_TEST,
        encoding="utf-8",
    )

    Path(".github/workflows/finalize-manager-modularization.yml").unlink()
    Path(".github/scripts/finalize_manager_modularization.py").unlink()


if __name__ == "__main__":
    main()

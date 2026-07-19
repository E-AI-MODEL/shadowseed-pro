# Compatibility Policy

**Authority:** CANONICAL_SPEC
**Scope:** Legacy import paths in the `shadowseed` package

This document defines how historical import paths are supported. It is the
authoritative reference for the `COMPATIBILITY_ONLY` modules in this
repository.

## 1. Purpose

Some modules were moved to canonical locations as the package was
consolidated. To avoid breaking external code and historical references, the
original import paths are retained as thin compatibility modules that
re-export the canonical objects. These modules contain **no implementation**.

## 2. Supported legacy import paths

| Legacy import path | Canonical target |
|---|---|
| `shadowseed.benchmark.embedding_backends` | `shadowseed.adapters.embedding` |
| `shadowseed.benchmark.openai_client` | `shadowseed.adapters.openai_client` |
| `shadowseed.benchmark.ollama_client` | `shadowseed.adapters.ollama_client` |
| `shadowseed.benchmark.open_set_model_detector` | `shadowseed.detection.model_detector` |
| `shadowseed.benchmark.recurrence_clustering` | `shadowseed.recurrence_clustering` |
| `shadowseed.benchmark.seed_retrieval_probe` | `shadowseed.retrieval_probe` |
| `shadowseed.prompt_templates` | `shadowseed.prompts` |

## 3. Public compatibility boundary

Each compatibility module declares an explicit `__all__`. Only the names in
`__all__` are supported through the legacy path. For every supported name:

```text
legacy_object is canonical_object
```

The objects exposed by a compatibility module are the *same* objects as those
exposed by its canonical module — not copies, wrappers, or reimplementations.

## 4. Policy for private internals

Underscore-prefixed names are private to the canonical module. They are **not**
guaranteed through compatibility paths and must not be relied on by external
code. Incidental imports (typing constructs such as `Any`/`Callable`, standard
library modules such as `os`/`re`/`json`, and third-party modules such as
`numpy`) are not part of the compatibility surface even though a historical
`import *` may once have exposed them.

## 5. Ban on new implementation inside wrappers

A compatibility module must not contain branching, transformation, fallback,
validation, I/O, configuration, logging, or state logic. It must not normalize
or reinterpret SSL state, configuration, or lifecycle inputs. If new behavior
is required, it belongs in the canonical implementation and must be reviewed as
a separate functional change.

## 6. Rule for new internal code

New internal runtime code must import from the **canonical** module, never from
a compatibility path. Compatibility paths exist only for backward
compatibility. This rule is enforced by an active import-path scan in the
compatibility gate.

## 7. Deprecation requirements

- A legacy path may be marked deprecated in its module docstring and in this
  document before removal.
- Deprecation must name the canonical replacement.
- Deprecation must give consumers a clear migration target
  (`legacy_object is canonical_object`, so a find-and-replace of the import
  path is sufficient).

## 8. Removal criteria

A compatibility module may be removed only when **all** of the following hold:

1. No active runtime code imports the legacy path (verified by scan).
2. The path has been documented as deprecated for at least one release.
3. The canonical replacement is stable and documented.
4. Removal is an intentional, separately reviewed change.

## 9. Required tests before removal

Before removing a compatibility module, the compatibility contract test
(`tests/test_compatibility_contracts.py`) must be updated in the same change
that removes the path, and the full suite must pass. The contract test is the
guard that keeps `legacy is canonical` true for every supported name while the
path exists.

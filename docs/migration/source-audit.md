# Source audit

## Scope

The migration inspected every file in the supplied archive, not only the initially requested modules.

- 506 source files
- 6,724,785 source bytes
- 110 runtime or benchmark Python files
- 60 original test modules
- 366 test functions in the rebuilt repository
- 160 historical open-review files retained as regression fixtures
- 82 documentation files reviewed
- 22 workflows reviewed
- 33 historical result artifacts reviewed

The complete per-file decision log, including SHA-256 hashes and destinations, is in `file-manifest.csv`. No source file remains unmapped.

## Baseline

The untouched archive produced:

- 362 passing tests
- 9 failing tests
- 4 skipped tests

Eight failures came from subprocess tests launched outside the source tree without an installed package. One failure required Git metadata that a zip archive does not contain.

## Rebuilt repository

After installation, refactoring, translation, and test updates:

- 375 tests pass
- 4 optional-backend tests are skipped
- Python compilation passes
- Ruff's configured fatal-error checks pass
- the installed CLI runs from outside the repository
- the fixture chat exposes the new early-turn and resurface controls
- the default gap suite finds packaged data without relying on `src/` paths

## Main findings

- The session benchmark had newer surfacing behavior than live chat.
- Live application code imported model, embedding, clustering, retrieval, and similarity behavior from the benchmark namespace.
- Historical review rounds are active regression inputs, not disposable output.
- Test helper functions are fixtures or setup helpers; no remaining test module is the sole owner of runtime behavior.
- The original documents and workflows contain valuable history but mix active, superseded, and exploratory claims.
- The source archive has no license file.

## Migration rule

Reusable behavior moved to runtime-owned modules. Benchmarks and tests import those modules. Compatibility wrappers preserve older imports. Historical documents, workflows, result artifacts, templates, and the source PDF are retained under `archive/` rather than deleted.

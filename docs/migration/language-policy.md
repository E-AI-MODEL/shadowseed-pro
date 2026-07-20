# Language policy

The active package, CLI, error messages, documentation, templates, workflows, and test descriptions are English.

Some content remains in its source language for a technical reason:

- multilingual detector inputs and normalization patterns test language coverage;
- historical open-review rounds are immutable research artifacts and regression fixtures;
- legacy verdict tokens such as `WEERLEGD`, `HOUDT_STAND`, and `ONBESLIST` remain readable for artifact compatibility;
- archived source documentation and results are preserved without rewriting.

These exceptions are data compatibility, not the public language of the new repository. New code and documentation must be written in English.

## Enforcement

`tests/test_language_alignment.py` checks that the core runtime modules
(`manager`, `chat`, `surfacing`, `ssot`, `recurrence`, `retrieval_probe`,
`core_config`, `seed_normalization`, the `gate` package, and `shadowseed_agent`)
read as English prose. It flags a curated set of high-confidence Dutch prose
words and allows an explicit list of documented Dutch input-language tokens.

The allowed tokens are data, not user-facing prose:

- the atomic-seed heuristic tokens in `SSLManager.is_atomic_seed` and the
  seed-normalization tokens (for example `en`, `of`, `zoals`, `ontbreekt`,
  `analysekader`), which detect and shape Dutch-corpus candidates and are
  matched or appended as literal tokens;
- these are glossed in English in the code and would change detection behavior
  on the existing corpus if translated away.

The check is deliberately scoped to the core runtime. Benchmark suites and JSON
data fixtures are out of scope: their Dutch content (including the legacy
verdict tokens above and historical seed text) is preserved so benchmark meaning
and historical results are not altered.

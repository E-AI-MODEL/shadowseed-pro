# Language policy

English is the canonical language of the active repository. The core runtime
prose (comments, docstrings, exceptions, messages) is English and is enforced
automatically (see Enforcement below). New code and documentation must be
written in English.

Active runtime and session-measurement inputs are English. Some frozen or explicitly multilingual content remains in its source language for a technical reason:

- multilingual detector inputs and normalization patterns test language coverage;
- historical open-review rounds are immutable research artifacts and regression fixtures;
- legacy verdict tokens such as `WEERLEGD`, `HOUDT_STAND`, and `ONBESLIST` remain readable for artifact compatibility. Canonical English aliases `VERDICT_REFUTED`, `VERDICT_SURVIVES`, and `VERDICT_UNDECIDED` are provided in code; the serialized token *values* stay Dutch so existing artifacts and model-output parsing remain compatible;
- archived source documentation and results are preserved without rewriting.

These exceptions are data compatibility, not the public language of the new repository.

## Enforcement

`tests/test_language_alignment.py` inspects the prose (comments and string
literals, via the `tokenize` module) of every auto-discovered core runtime
module — `shadowseed` excluding `benchmark/` and `data/`, plus
`shadowseed_agent`. It applies exact forbidden-phrase checks, a curated
distinctive-Dutch vocabulary, and **path-specific** allowlists so a documented
Dutch input-language token (for example `ontbreekt` or `analysekader`) is
accepted only in the file that legitimately uses it, and flagged anywhere else.

### Scope and limits

The automated strict scan covers the **core runtime**. It substantiates an
English-core guarantee, not a whole-repository one. The following content is
outside that strict scan:

- benchmark suite Python prose (docstrings/comments), which references the
  legacy verdict tokens and historical Dutch scenario text;
- explicitly multilingual detector fixtures and frozen historical result artifacts;
- Markdown documentation, CLI help text, workflows, and templates.

The active top-level and `docs/` Markdown is English. Historical review rounds, multilingual fixtures, and compatibility tokens retain their
original language so artifact compatibility is not altered. The canonical SSL session
suites used for new live measurements are English and declare `language: en`; live
measurement fails closed on suites that do not declare that contract. Extending the
strict scanner beyond the core runtime is optional hardening, not part of the
current English-core guarantee.

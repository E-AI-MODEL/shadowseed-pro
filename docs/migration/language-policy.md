# Language policy

English is the canonical language of the active repository. The core runtime
prose (comments, docstrings, exceptions, messages) is English and is enforced
automatically (see Enforcement below). New code and documentation must be
written in English.

Some content remains in its source language for a technical reason:

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

### Scope and honest limits

The automated strict scan covers the **core runtime**. It substantiates an
English-core guarantee, not a whole-repository one. Explicitly **not** yet under
the automated strict scan:

- benchmark suite Python prose (docstrings/comments), which references the
  legacy verdict tokens and historical Dutch scenario text;
- JSON data fixtures and current result summaries;
- Markdown documentation, CLI help text, workflows, and templates.

These retain documented Dutch content so benchmark meaning and historical
results are not altered. Extending the scan to benchmark Python prose and
active Markdown is tracked as follow-up work.

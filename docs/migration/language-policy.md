# Language policy

English is the canonical language of the active repository. Core runtime prose (comments, docstrings, exceptions, messages) is English and is enforced automatically (see Enforcement below). New code and active repository documentation must be written in English.

That repository-language rule is separate from product-language behavior. Ordinary live chat follows the language of the current user question. Research and benchmark protocols may deliberately pin a language, and the canonical live session measurement suites currently declare English where their protocol requires it.

Some frozen or explicitly multilingual content remains in its source language for a technical reason:

- product chat accepts multilingual user input and requests an answer in the current question's language;
- multilingual detector inputs and normalization patterns test language coverage;
- historical open-review rounds are immutable research artifacts and regression fixtures;
- legacy verdict tokens such as `WEERLEGD`, `HOUDT_STAND`, and `ONBESLIST` remain readable for artifact compatibility. Canonical English aliases `VERDICT_REFUTED`, `VERDICT_SURVIVES`, and `VERDICT_UNDECIDED` are provided in code; the serialized token values stay Dutch so existing artifacts and model-output parsing remain compatible;
- archived source documentation and results are preserved without rewriting.

These exceptions do not change the canonical language of active repository prose.

## Enforcement

`tests/test_language_alignment.py` inspects the prose (comments and string literals, via the `tokenize` module) of every auto-discovered core runtime module: `shadowseed` excluding `benchmark/` and `data/`, plus `shadowseed_agent`. It applies exact forbidden-phrase checks, a curated distinctive-Dutch vocabulary, and path-specific allowlists so a documented Dutch input-language token (for example `ontbreekt` or `analysekader`) is accepted only in the file that legitimately uses it, and flagged anywhere else.

### Scope and limits

The automated strict scan covers the **core runtime**. It substantiates an English-core guarantee, not a whole-repository or English-only product guarantee. The following content is outside that strict scan:

- benchmark suite Python prose (docstrings/comments), which references legacy verdict tokens and historical Dutch scenario text;
- explicitly multilingual detector fixtures and frozen historical result artifacts;
- Markdown documentation, CLI help text, workflows, and templates.

Active top-level and `docs/` Markdown is maintained in English. Historical review rounds, multilingual fixtures, and compatibility tokens retain their original language so artifact compatibility is not altered.

Research inputs can be stricter than product input. For example, the canonical SSL session suites used for current live measurements declare `language: en`, and that measurement path fails closed on suites that do not declare the protocol. This benchmark restriction must not be generalized into a claim that ordinary product chat is English-only.

Extending the strict scanner beyond the core runtime is optional hardening, not part of the current English-core guarantee.

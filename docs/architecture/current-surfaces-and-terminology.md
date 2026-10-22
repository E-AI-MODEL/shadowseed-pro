# Current product surfaces and precise status language

**Authority:** explanatory canonical-spec companion. Refer to the accepted ADRs
for the actual SSL/Gate contracts, and to the installed code/tests for
executable behavior. Status checked on `main`
`f3ec86c124ab88247e0739a6cbe3c817a6508219` (22 October 2026).
A pending pull request is not a released runtime.

## The labels are not interchangeable

| Term to use | Meaning today | Implementation / evidence | Do **not** imply |
| --- | --- | --- | --- |
| **SSL engine / canonical runtime** | Model-independent state, lifecycle, candidate observation, Gate, provenance and point-of-use boundary | `src/shadowseed/`, `src/shadowseed_agent/`, `ShadowseedEngine` | A separately conscious model or an autonomous truth finder |
| **Local web app** / **Shadowseed Web** | **Primary user-facing product**: static Next.js frontend and loopback-only Python API, backed by the canonical engine | `apps/web/`, `src/shadowseed_webapi/`, `shadowseed-web` | Hosted website, Gradio, or independent Gate |
| **Gradio Workbench (optional)** | Still runnable Python/Gradio research/development UI; command `shadowseed-workbench`; extra `workbench` | `src/shadowseed/workbench/` | Current secure downloadable 0.12.3 web app; this optional extra retains [issue #200](https://github.com/E-AI-MODEL/shadowseed-pro/issues/200) |
| **Workbench** (historical umbrella) | Older name still visible in paths, CLI, test/workflow names and documentation roots | `docs/workbench/`, `standalone-workbench.yml` and existing command aliases | That every referenced component uses Gradio. In new prose, prefer the specific surface name above |
| **Compatibility facade / legacy import path** | Supported re-export alias for existing consumers; **not** redundant code to delete | `src/shadowseed/benchmark/`, `shadowseed.prompt_templates`; [compatibility policy](compatibility-policy.md) | Deprecated or removable without contract tests and a migration window |
| **Historical archive** | Frozen original designs, earlier research and former wiki; may use outdated claim or path names | `archive/`, [archive status](../../archive/README.md) | Current authority merely because an archived document calls itself 'canonical' |
| **Historical detector / absence-style baseline** | Older gap-oriented prompt and its results, needed for reproducibility | `src/shadowseed/prompts.py`, versioned detector contracts, old evaluation artifacts | Current inquiry-first quality or a deprecated live API without verification |
| **Inquiry-first v0.7 proposal** | Broader prompt/intake/UI work for specific open questions, doubt, curiosity and alternatives | Draft [PR #202](https://github.com/E-AI-MODEL/shadowseed-pro/pull/202) | Merged, validated against real-model v0.6, or officially released |
| **Research harness** | Actively maintained evaluation/benchmark code distributed separately from the product | `research/src/shadowseed_research/`, `research/tests/` | 'Legacy' merely because it is not part of the end-user app |
| **Research Preview candidate** | Current source state and automated test coverage, not an immutable public download | `pyproject.toml`, release notes, GitHub Actions | `production-ready/local`, efficacy, or published `v0.12.3` |
| **Published Research Preview** | Immutable tagged/downloadable release with exact evidence | GitHub [releases](https://github.com/E-AI-MODEL/shadowseed-pro/releases); latest verified on this date: `v0.12.2` | Current untagged source build |
| **Production-ready/local** | Stronger operational assurance with local Ollama use cycle, exact-SHA release assurance, soak and no unresolved high-severity findings | `docs/research/status.md`, `docs/operations/` | Already achieved by green fixture, packaging or CI |
| **Hosted / public service** | Distinct as-yet-unapproved deployment/security boundary | ADR-007 | `https://eaimodel.nl` is an SSL server or that loopback HTTP is a public API |

## Vocabulary for a seed

A seed is **one bounded, context-connected, independently investigable line
of inquiry**. Possible forms include an open question, doubt, uncertainty,
relevant what-if, tentative explanatory frame, possible missing distinction,
or an omission. It is **not necessarily a detected deficiency**.

- **Detection / observation** means that a model or rule proposed a candidate.
  It does not establish correctness or truth. The model does not *feel*
  curiosity or doubt; these words describe the kind of question being recorded.
- **Remembered / trace** means a candidate is present in the shadow memory.
- **Verified external evidence** is separate from source content, generated
  prose, semantic similarity or recurrence.
- **Weight / authority** is policy-controlled eligibility, not a measure of
  truth or of how much of the answer was caused by a seed.
- **Gate authorized** does not guarantee point-of-use eligibility; **offered
  to an answer** is not automatically a causal effect or a quality improvement.
- **Question** is not truth-apt on its own. Evidence may support a bounded,
  evaluable claim linked to a question; it does not 'prove the question'.
- `NONE` is allowed where no specific grounded line of inquiry is worth
  preserving. More candidates or model confidence do not confer authority.

## What to preserve and what to clean

**Preserve exactly for provenance:** historical paper/PDF and datasets, old
benchmarks, archived 4.5/4.6 prose, versioned prompts and public API names.
The June 2026 generative-vision document already contrasts *what could have
been there* with *what should have been there*; it must not be edited
retroactively to pretend that every earlier code path was inquiry-first.

**Clarify in current material:** source vs published version, default web
client vs optional Gradio, research-only controls vs live product, versioned
absence-style detector vs draft v0.7, and genuine release/quality claims.
Fix misleading install instructions, obsolete future-tense design documents
and ambiguous 'legacy' labels where their actual category is known.

**Remove only with proof:** duplicate or dead live files, unreferenced
obsolete instructions, or unsupported aliases after consumer/CI checks and a
reviewed migration. Do not remove working compatibility facades, historical
experiment artifacts or a still-used Workbench interface just to simplify
the tree.

## Current sources to check before revising this page

- [ADR-001 authority](adr/ADR-001-validation-gate-authority.md)
  and [ADR-002 seed contract](adr/ADR-002-epistemic-seed-contract.md).
- [ADR-003 contaminated observations](adr/ADR-003-contaminated-observation-boundary.md)
  and [ADR-005 chat-first surface](adr/ADR-005-chat-first-product-surface.md).
- [ADR-008 UI terminology](adr/ADR-008-workbench-ui-reset.md).
- [repository structure](repository-structure.md),
  [compatibility policy](compatibility-policy.md),
  [current research status](../research/status.md),
  [web/optional Gradio guide](../workbench/README.md),
  [2026-10-22 plan](../plans/pva-shadowseed-history-noise-inquiry-2026-10-22.md).

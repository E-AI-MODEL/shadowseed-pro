# Possibility-space research — sources, conversation, and course elimination

> **Status:** open research program; neither a proven capability nor an accepted architecture decision.
> **Date:** 2026-10-24.
> **Source of authority for the question:** [Foundational research thesis (verbatim, Dutch)](../possibility-space-thesis.md). Never reduce its two clauses to only "better answers," "more ideas," or "novel knowledge from existing knowledge."

## Read in this order

1. **[Original question and scope](../possibility-space-thesis.md)** — exact research question and explicit boundary between possibility, knowledge, and evidence.
2. **[Conversation record and user corrections](conversation-record-2026-10-24.md)** — chronological detailed reconstruction, including repeated reminders not to narrow the question, the anti-embedding metaphor, model capability concerns, why over-strict exploration may fail, and the correction concerning FunSearch. This is **not** a byte-for-byte ChatGPT export.
3. **[Annotated, source-checked literature map](literature-map-2026-10-24.md)** — links to original studies and their fit and non-conclusions. No reproduced paper PDFs.
4. **[Course-elimination and two-clause audit](course-elimination-2026-10-24.md)** — discarded approaches, rejected comparisons, experimental controls, proposed coupled research design, and conditions for abandoning the preferred route.
5. **[Original first experimental proposal](first-discriminating-experiment.md)** — preserved as the 2026-10-24 draft. Its implementation attempt became an inadequately aligned fixed-edge-gap assay; **do not treat it as the current protocol**.
6. **[Revised Q1/Q2 protocol (2026-10-25)](revised-q1-q2-experiment-2026-10-25.md)** — the current research direction after inspecting the 24-call GPT-5 feasibility attempt: repeated ordinary-generation measurements, *new relation kinds/constraints*, withheld downstream tests, an actual weightless cross-turn candidate arm, candidate ablations, cost-matched controls, and G0-G4 stop conditions. **Proposed, not implemented, preregistered, or proven**.
7. **[First live pilot, failure analysis (separate research PR #220)](https://github.com/E-AI-MODEL/shadowseed-pro/blob/research/possibility-pilot-20261024/docs/research/possibility-space/first-live-pilot-result-2026-10-24.md)** — 24 GPT-5 calls, 16 parseable results, eight incomplete, and a crucial construct-validity failure. Raw outcomes preserved; this is historical feasibility evidence, not thesis validation.

## Decisions and open work

- **Preserved:** the full, unshortened question.
- **Corrected:** FunSearch is not a direct comparator for the Shadowseed research aim.
- **Not proven:** either that model-internal unselected relations can be measured from output, or that a fixed LLM's conceptual space is expanded by current Shadowseed.
- **Not yet decided:** architecture, data structures, prompt changes, TTL/Gate adjustments, model family or size. The earlier GPT-5 API plumbing worked; its fixed-graph tasks did not satisfy the protected research question.
- **Immediate next evidence need:** pass **G0 construct validity** of the [revised experiment](revised-q1-q2-experiment-2026-10-25.md), using independently checkable changes in **relation kinds or constraints**, not merely missing paths in a fixed graph. Then separately measure ordinary-generation selection (Q1) and causally enabled new downstream relation classes (Q2), and only then their coupled effect against strong cost-matched controls.
- **Safeguard:** retain zero authority for mere suggestions and the existing Gate/point-of-use boundary until a separately justified architectural decision is accepted.

Related [original June 2026 vision](https://github.com/E-AI-MODEL/shadowseed/blob/main/docs/research/vision-generative-seeds.md) and [Pro ADR-002](../../architecture/adr/ADR-002-epistemic-seed-contract.md). The original archived sources are historical material; accepted Pro ADRs remain authoritative for the existing runtime.

**Scope:** This folder is a research continuity package for future investigators. It is not an instruction to implement an experimental suggestion as production behavior.

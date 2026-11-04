# Shadowseed Pro — raw-to-intake source-fate check and the next experiment

**Date:** 28 October 2026. **Status:** inspected original source output, not a general parser-quality claim, independent evaluation, Q1/Q2 proof or product acceptance.

## Source and exact scope

Original nested GitHub Actions artifact `12754935105` stored as `actions/original-github-action-zips/github-actions-artifact-12754935105.zip` in the author's 27 October archive. The original file `observed.json` has SHA-256 `0a5094e38ab2fdcf8c68dc8d6a3c75d29eeffd49e1f6c8e138589ed73ca36bbf`.

Grain: **48 detector turns**, belonging to 6 fictional scenarios × 2 models × 4 turns. These are **not 48 independent investigations**. Counts below are *candidate occurrences*, not unique concepts or independently valuable discoveries.

| Stage | Occurrences or turns |
| --- | ---: |
| Detector turns with archived raw output and diagnostics | 48 |
| `NONE` turns | 4 |
| Raw numbered candidate lines in the stored detector text | 94 |
| Parsed candidate occurrences | 94 |
| Normalized candidate occurrences | 94 |
| Item-level intake-lineage occurrences | 94 |
| `accepted` under historical intake | 48 |
| `rejected/not_atomic` under historical intake | 46 |
| Actual parser diagnostics: dropped stub, few-shot, duplicate, malformed/placeholder | 0 each |
| Turns with `truncated_after_max_seeds=True` | 24 |
| Turns where raw contains more numbered candidate lines than appeared in parsed output | 0 |

In this bounded source, there is **no observed loss of generated numbered lines between detector raw text, parser, normalization and intake**. There is demonstrable historical **operational seed-birth exclusion at atomicity** for 46 items. Every normalized output had the same substantive text as its parsed source (punctuation aside). A parser-limit flag is **not proof that extra candidate text was generated and discarded**: its implementation sets `truncated_after_max_seeds=True` as soon as the maximum *accepted number* is reached, even when no more raw lines follow. Here GPT-5 produced 72 parsed candidates across 24 turns, and GPT-6 Luna 22 across 24 turns; these are observations under different model-generation conditions, not a capability ranking.

The detector prompt itself requests **at most the configured `max_seeds`** and a single atomic candidate per line. Consequently a complete raw-to-parser match **cannot establish** what the model might have proposed under less prescriptive prompts, longer output, different decoding, or unrestricted questioning. It rules out only one particular kind of software loss *in the stored output*.

## End-to-end present-day boundary

[PR #262](https://github.com/E-AI-MODEL/shadowseed-pro/pull/262) proposes retaining non-atomic-form detector items as actual, original-text, weight-zero `unresolved` seeds in the Pro lifecycle. A local deterministic source replay previously found 46/46 such items could be born without Gate authority. Its main source and all four associated workflows have passed at the final recorded commit, but this **changes accepted ADR-002 semantics** and must be independently reviewed before merge.

A `weightless` possibility is neither evidence nor authorization. An archived accepted/rejected decision is not a judgement of truth or intellectual worth. **Do not** treat successful seeding or persistence as measured expansion of the model's possibility space.

## Immediate next experiment: longitudinal Pro replay without fresh model calls

1. **Reconstruct chronological original contexts per model/case,** including all 48 original host turns, all recorded raw candidate observations and the original detector model/prompt provenance.
2. **Run the actual proposed Pro intake + one persistent `ShadowseedEngine` per independent model/case**, with the archived detector output as an exact replay and the host answer unchanged. Do not transform an unparsed candidate into a supposedly original detector idea.
3. **Trace every candidate's fate, not just accepted ones:** original observation -> real `created_bounded` or `created_unresolved` -> same-ID persistence -> recurrence/dedup/TTL/DORMANT/TrTL/EXPIRED -> optional new candidate connections. Document naturally occurring none, nonmatch and expiry cases.
4. **Keep the unchosen candidate genuinely hidden from the ordinary host prompt** until existing Gate + point-of-use approve influence. The replay should confirm that preserving a weightless item is not secretly a hint injection. Include detector-NONE and source-preserving controls.
5. **Research question:** identify whether subsequent *model-originated* observed relations can be linked to earlier retained possibilities without counting a researcher's later prompt or inspection as spontaneous growth. If all later answers are unaffected, that is a correct null for answer influence and not a failure of weightless memory.
6. **Only after that**, design a separate model-originated side inquiry and the matched normal-generation/ordinary-memory/candidate-ablation comparison. Q2 concerns what becomes investigable later, not number of accepted seeds or “good answers” at birth.

### Measurable outputs, not a synthetic success score

- Candidate fate ledger keyed by original observation and seed ID, never by inferred text similarity alone.
- Preservation/loss at each software boundary (raw, parse, normalization, intake, memory persistence), including negative cases.
- Identity preservation and `weight=0` invariants.
- Later contextual matches with source, actor, timestamps and explicit differentiation of new detection versus TrTL reactivation.
- Distinguish a genuinely new subsequent relation from candidate repetition or paraphrase **after** the raw events are frozen. Any human/AI interpretation stays separate and provenance-tagged.

No new paid model calls are necessary for this immediate replay. No production Gate, trace/weight policy, TTL/TrTL or authority semantics should be modified to produce a positive finding.

**Alignment:** Current Shadowseed Pro code and accepted ADRs govern runtime behavior; full two-clause philosophical possibility-space thesis governs the research question. Historical Shadow Seed Learning material is provenance. The scope of a candidate is not its worth. The weightless shadow is an existence/persistence permission; answer influence remains separately gated.

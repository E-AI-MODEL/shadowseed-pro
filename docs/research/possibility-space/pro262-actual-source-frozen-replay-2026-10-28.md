# Actual Shadowseed Pro weightless multi-turn replay — source-frozen result

**28 October 2026 | Local mechanical result, not Q1/Q2 causal evidence.**  
**Runtime:** branch `feature/pro-weightless-unresolved-birth-20261028` / [draft PR #262](https://github.com/E-AI-MODEL/shadowseed-pro/pull/262). The five altered Pro runtime files were reconstructed from a 27 October clean main-source tar and patched locally; **Git blob SHA-1 matched each exact file of PR #262**. No modified production environment, no new model calls, no new evidence input.

## What actually ran

The **actual** `ShadowseedEngine.prepare_turn/observe_turn` runtime was executed in 12 isolated Pro sessions (six fictional cases × two recorded host models), using all four successive recorded user inputs and host answers per session. Detector output was not regenerated: each turn received the **original, exact archived list of already parsed detector candidates** through a fixed, local detector adapter. The original model text and observations were not published.

Original source: `repositories/shadowseed-pro/shadowseed-pro-main-source.tar` together with `actions/original-github-action-zips/github-actions-artifact-12754935105.zip/observed.json` inside the author's 27 October private archive. `observed.json` SHA-256 **`0a5094e38ab2fdcf8c68dc8d6a3c75d29eeffd49e1f6c8e138589ed73ca36bbf`**. The parent commit and exact PR #262 runtime blob identities were checked separately.

**Important limitation:** lexical, deterministic 128-dimensional sign-hash embeddings were used to keep the replay offline and free of model calls. They are **not semantically calibrated** and do not test whether a larger model would independently re-recognize a relation. The experiment freezes the host's words; it cannot demonstrate that remembering seeds changes generation.

## Measured outcomes

| Original / counterfactual route | Event counts |
| --- | ---: |
| Original candidate occurrences | 94 |
| Chronological observed turns | 48 (12 sessions × four turns) |
| Originally born bounded seeds | 48 |
| Historically rejected solely as `not_atomic` | 46 |
| In real PR #262 runtime: new `unresolved` seeds | **46** |
| In real PR #262 runtime: new bounded seeds | **48** |
| New distinct seed IDs total, all 12 sessions | **94** |
| Candidates still rejected under Pro's new intake | **0** |
| Unresolved exact reobservations in these frozen turns | **0** |
| TrTL reactivations | 0 |
| Positive authority / Gate promotions / normal-answer surfacing | **0 / 0 / 0** |
| Persisted seeds after turn 4 | **94 (48 bounded + 46 unresolved)** |
| Session snapshot restore checks | **12 / 12 passed** |
| New LLM calls | **0** |
| Independent assessments of newly formed relational possibilities | **0** |

The actual engine's public `inspect` state retained the seed IDs and original text. An exported/restored state preserved each record's identity, text, `scope_status` and zero weight; the recorded 12 sessions generated zero Gate events. The replay's `prepare_turn` produced no candidate context and no surfaced seed IDs in any of the 48 turns.

Of the 46 previously rejected candidate occurrences, **78 candidate-turn observation windows** existed later in their respective four-turn histories (15 rejected at turn 0 ×3, 10 at turn 1 ×2 and 13 at turn 2 ×1; eight at turn 3 ×0). This is a **bookkeeping measure of opportunities** the historical operational memory lacked. It is not 78 demonstrated model discoveries, reactivations, lost causal effects or unique relationships.

The original host outputs and current replay both show no repetition of the same unresolved candidate text and no observed TrTL activity. This can mean no later relevant match within the four turns or the absence of a qualifying lifecycle state; do not infer impossibility or absence of internal model capability.

## What is supported

The original form rule suppressed operational seed birth for 46 archived detector candidates. PR #262 allows each to be recorded as its own **real, weight-zero Pro seed** without editing source meaning or bypassing the Gate, while preserving the 48 previously bounded births. The original source replay demonstrates that this retention works **over actual multi-turn engine state** with source-identity and restoration checks.

## What is NOT supported

1. That all 46 represent a single, useful, true or independently new epistemic relationship.
2. That the host model has newly learned or internally formed a relation.
3. That two seeds autonomously combined into a different possibility.
4. That Q2's `possibility space` has expanded; the host outputs are frozen and cannot respond to changed memory.
5. That a toy embedding adequately tests semantic recurrence, TrTL or conceptual changes.
6. That PR #262 is ready to ship. **Accepted ADR-002 presently says seeds are atomic**; this proposed unresolved-scope extension still needs an explicit architecture, safety and compatibility decision despite green CI.

## Immediate scientific next step

The *engineering* retention failure is now reproducible and fixed on a **draft branch**. Do not repeat a larger paid prompt experiment until the following scientific object is defined:

> What independently observable relation transition or interplay appears **after** a possibility is retained, compared with a matched branch that did not retain it, when the candidate is never reinserted as a host hint?

Use the actual Pro session, source-origin attribution and multi-turn persistence, a capable matched model (not a toy embedding as sole semantic detector), and equal compute/context budgets. Freeze original raw candidate identity before interpreting emergent links. No extra Gate power is granted for speculative birth or inspection.

**Merge boundary:** PR #262 remains draft, independently review ADR-002 extension and cross-module authorization/security first. The previous open-set measurements remain historical, not overwritten by the new candidate-count denominator.

## Source / provenance

- [Pro source and proposal — PR #262](https://github.com/E-AI-MODEL/shadowseed-pro/pull/262)
- [Source-fate audit — PR #261](https://github.com/E-AI-MODEL/shadowseed-pro/pull/261)
- [Full possibility-space thesis](../possibility-space-thesis.md)
- Unpublished author-only runtime replay files: `run_actual_pro262_replay.py`, `Pro262_actual_48_turns_94_seeds_replay_20261028.json`, `PRIVATE_Pro262_frozen_replay_94_lineage.csv`.

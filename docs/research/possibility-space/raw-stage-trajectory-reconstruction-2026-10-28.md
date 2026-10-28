# Source-preserving stage trajectory reconstruction (28 October 2026)

**Status:** Read-only reconstruction of an existing, author-held **derived observation register**. Not a new experiment, independent review, reproduction of all original Actions artifacts, or an accepted change to Pro architecture.

## What was reconstructed

The existing 28 October private observation register contains 220 complete, recorded turn rows. Grouping only by the literal `(dataset, artifact_id, model, case_id)` keys produces **40 distinct recorded trajectories** with contiguous turn indices beginning at zero:

| Recorded length | Trajectories | Turns |
| ---: | ---: | ---: |
| 3 | 8 | 24 |
| 4 | 16 | 64 |
| 8 | 12 | 96 |
| 9 | 4 | 36 |
| **Total** | **40** | **220** |

Each owner-only trajectory export retains every original CSV row, including the serialized complete original turn object, question, answer, detector and recorded candidate fields. These 40 groups are **not** 40 independent scientific trials; some share questions, cases, research designs or model comparisons. No original turn was rewritten to resolve a disagreement.

The register also contains **1,224 recorded candidate occurrences**, each preserved in the owner-only candidate ledger. The script checks exact source keys before attributing an occurrence to a recorded stage:

| Mechanical source link | Candidate occurrences | Reading |
| --- | ---: | --- |
| Exact `(dataset, artifact, model, case, turn)` match | 368 | Literal stage join |
| Same dataset/artifact/case/turn, **different model label** | 96 | Not joined; Qwen source says `qwen-unspecified` where the turn register says `qwen2.5-7b` |
| No matching stage on those literal keys | 760 | Separate detector calibration, local gap resilience and inquiry-first candidate entries; **not** a proof of missing or lost turns |
| **All candidates retained** | **1,224** | No candidate selection or semantic interpretation |

The turn index is cross-checked against the `02_beurten_stage_220.csv` record. Duplicate source-turn identities, noncontiguous turn indices, broken original JSON and inconsistent stage-index keys cause a fail-closed error.

## What this does not establish

- The author-held ZIP is a **derived register**, not the 84 MB original 27 October archive. Its SHA-256 and the three input-member hashes bind this reconstruction to the submitted copy, but **do not independently verify all 62 original GitHub Actions archives**, old Git histories or their complete transcription.
- The 220 turn records do not cover all 1,224 candidate occurrences as complete dialogues. In particular, 760 candidate observations come from source groups that do not have corresponding rows in this stage register, and 96 others have a source-label mismatch.
- A literal answer difference is not an independent scientific insight. A candidate birth is not a downstream exposure. Source labels do not establish model-internal phenomena, autonomous relation formation, Q1, Q2 or causal seed effects.
- Original labels such as `accepted`, `rejected`, `born`, `surfaced` and `promoted` are preserved *as data*, not endorsed as semantic judgements.
- This does not change open draft PR #262, the accepted ADR-002 contract, Validation Gate, TrTL or G0. No paid calls, new model output, content-scoring or automatic semantic normalization were used.

## Local reproduction (no network)

```bash
python research/scripts/pro_archive_trajectory_reconstruction.py \
  /private/Shadowseed_Observatieregister_20261028.zip \
  --public-manifest /private/reconstruction-counts.json
```

By default the command emits **only a count-only manifest**. The source text stays inside the process. To export the original turns and all recorded candidate rows for private inspection, explicitly add `--owner-only-dir /private/new-trajectory-directory`. The directory must not yet exist. No source text, person identifiers or hidden allocation keys belong in a public commit, GitHub Action log, external comparison or publicly distributed result. The author must handle any private review allocation separately.

**Local execution against the owner's 28 October register:** 220/220 stage-key rows cross-check; 40 reconstructed trajectories; 1,224/1,224 candidate rows retained; 368 exact joins, 96 model-label mismatches, 760 source-only candidate rows. Offline synthetic regression suite: 6/6 passed. This is an internal technical check, not independent verification of the original primary archives.

## Next boundary

Return to the original 62 Action archives **without converting their differing schemas into assumed comparable turns**. Add a source-specific parser only after verifying its original bytes and schema, with a recorded `unparsed` state whenever a complete turn cannot be recovered. Do not turn a missing stage join into a new causal finding. Human G0 vetoes #234 and #235 remain outstanding before confirmatory Q1/Q2 experiments.

Related: [original thesis](../possibility-space-thesis.md), [27 October source-fate audit, draft PR #261](https://github.com/E-AI-MODEL/shadowseed-pro/pull/261), [28 October unresolved-seed replay, draft PR #262](https://github.com/E-AI-MODEL/shadowseed-pro/pull/262), [readiness issue #228](https://github.com/E-AI-MODEL/shadowseed-pro/issues/228).

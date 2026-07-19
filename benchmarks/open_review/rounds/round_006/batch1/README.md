# Round 006 — batch 1 (Phi-3.5-mini, substance replication, Layer C)

> **Status: AI review complete.** Detector run is real (Actions run
> [27256277709](https://github.com/E-AI-MODEL/shadowseed/actions/runs/27256277709),
> ~50 min on the public `ubuntu-latest` runner). Review is **delegated AI**
> (`reviewer_ai_claude`, single reviewer, maintainer-delegated) — labeled AI,
> not human, throughout. The clean comparison is against the round 005 **AI**
> pass (same reviewer), not the round 005 human batch.

## Run provenance

- **Model:** `hf-transformers:microsoft/Phi-3.5-mini-instruct` (MIT), v0.3e
  prompt **unchanged** (one lever per round), `max_new_tokens=512`, greedy.
- **Input:** `ag_news_test` offset 0, limit 12 — the same 12 source items as
  the round 005 offset-0 batch, so the model effect is isolated.
- **Artifacts:** `input/hf_batch.json` and `open_set_seed_output.json` are the
  **verbatim run artifacts** (maintainer-uploaded from the Actions artifact,
  sha256 c364874e…). The run produced **60 raw candidates**; the SSLManager
  atomicity gate rejected 2 before packet generation (both "of"-stacked /
  category-worded: "De mogelijke impact of gevolgen voor T N pension.",
  "De exacte percentages van andere veroorzakende factoren …"), leaving the
  **58 reviewed candidates**. `run_review_packets_pending.json` preserves the
  run's own untouched two-reviewer packets, so a human review pass remains
  possible later.

## Mechanical prescreen (triage, not evidence)

60 raw candidates over 12 items (yield 5.0); the prescreen's `not_atomic`
flags exactly the 2 candidates the manager gate also rejected — independent
confirmation of that gate. Versus round 005 (same items + offset 12,
Qwen2.5-3B):

| Code | Round 005 | Batch 1 (Phi) |
|---|---:|---:|
| `not_atomic` | 38 | **2** |
| `near_duplicate` | 13 | **0** |
| `parse_leak` | 10 | **0** |
| `truncated` | 9 | **0** |
| `claim_vs_gap` | 0 | **60** |

**The 60 `claim_vs_gap` flags are scaffold non-compliance, not claims.** Phi
ignores the v0.3e rule "formuleer als afwezigheid ('… wordt niet vermeld')"
and instead follows the few-shot examples — which are themselves bare noun
phrases in the canonical 4.5 seed form ("Koloniaal kapitaal als
financieringsbron…"). All 58 were manually read: none asserts a fact as true
(the Qwen failure mode this check was built for). The maintainer reviewed
this reading and ruled **GO** on the gate.

**Resolved after this round in prompt v0.3g:** the noun-phrase gap label (the
canonical 4.5 form, and what the few-shot examples already showed) is now the
rule as well; absence sentences stay allowed. The prescreen `claim_vs_gap`
check was redefined accordingly: it now detects actual assertions
(main-clause finite verb without an absence marker) instead of requiring a
marker. Under that contract this batch is claim-free (the committed prescreen
artifact reflects the current code; the 58-flag reading below is the
historical state at review time).

## AI review result (single reviewer, same bar as the round 005 AI pass)

- unique seeds **58** · accepted **29** · acceptance **0.50**
- criterion pass rates: atomicity **1.00**, relevance **0.86**,
  testability **0.69**, non_triviality **0.50**, follow_up_utility **0.50**
- reject codes: `too_vague` 11, `trivial` 4, `not_relevant` 4 (false gaps),
  `style_not_gap` 4, `duplicate` 3, `not_testable` 3

### The comparison that is valid (same reviewer, same items, same rubric)

| | Round 005 offset-0 (Qwen2.5-3B, AI review) | Batch 1 (Phi-3.5-mini, AI review) |
|---|---:|---:|
| acceptance | 0.185 | **0.50** |
| atomicity | 0.81 | **1.00** |
| testability | 0.30 | **0.69** |
| non_triviality | 0.19 | **0.50** |
| follow_up_utility | 0.19 | **0.50** |

**Reading:** model capability was the dominant lever, exactly as the round
006 design hypothesized. The substance problem (relevant-but-trivial) is
roughly halved, not solved: half the candidates still fail, dominated by
vague impact/detail questions (`too_vague` 11) and false gaps on numeric
facts that are present in the text (item TEST_9: arrests/savings/period all
stated, all "re-missed" by the model).

### What this does NOT claim

- This is not human review; acceptance 0.50 is an AI-judged number. The
  round 005 **human** anchor (0.29, offset-12, different items) is not
  directly comparable and is not superseded.
- The ≥ 0.60 Layer-C target is not met, and the judge is not human — do not
  quote 0.50 as Layer-C evidence; quote it as a delegated-AI signal that the
  model lever works.

## Remaining weaknesses (for batch 2 and the next prompt iteration)

1. **False gaps on present numerics** (TEST_9) — the "staat het er al, sla
   het over"-rule needs reinforcement or a grounding check.
2. **Vague impact/speculation questions** ("impact op de markt",
   "reacties achteraf") — the largest reject bucket.
3. **Scaffold non-compliance** — decide the canonical form (see above).
4. One full-English candidate slipped the `language_leak` heuristic
   (only one stopword hit).

## Artifacts

```text
input/hf_batch.json                  # the 12 source items (reconstructed subset, provenance noted)
open_set_seed_output.json            # reconstructed candidates + run provenance
mechanical_prescreen.json / .md      # deterministic triage (clean-rate 0.0 — see scaffold reading)
ai_review/open_set_review_packets.json       # 58 judged packets, reviewer_ai_claude
ai_review/open_set_seed_review_summary.json  # canonical summary route output
ai_review/open_set_review_report.md          # human-readable summary
ai_review/open_set_disagreements.json        # empty (single reviewer)
```

Next: batch 2 — same detector and prompt on a different domain (first Layer-F
signal), per the round plan in `../README.md`.

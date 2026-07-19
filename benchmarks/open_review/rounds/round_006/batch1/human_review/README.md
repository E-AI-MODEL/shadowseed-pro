# Round 006 batch 1 — human second pass (blind)

> **Status: packet ready, awaiting human judgments.** This is the real
> independent second reviewer that the AI-review arms could not provide. It
> re-reviews the same 58 news candidates (round 006 batch 1, ag_news offset 0)
> that `reviewer_ai_claude` judged at acceptance 0.50 — blind — so we get the
> first human-vs-AI agreement number since the round 005 human batch.

## Why this batch

Round 006 batch 1 carries the headline "the model lever works" (0.185 → 0.50).
A human anchor on it does two things at once: a real human acceptance number
for the batch, and a retroactive check on whether the delegated AI reviews can
be trusted at all (via agreement + Cohen's kappa on the same items).

## How to do it

1. Open `human_review_packets.json`. It has 58 rows, one per candidate, in a
   **blind shuffled order**. It contains **no AI verdicts** — do not open
   `../ai_review/` until you are done.
2. For each row fill:
   - the five `review_fields` booleans: `atomicity`, `relevance`,
     `testability`, `non_triviality`, `follow_up_utility`;
   - `review_status`: `accepted` or `rejected`;
   - `reject_reason` when rejected — one of `too_broad`, `too_vague`,
     `trivial`, `not_relevant`, `not_testable`, `duplicate`, `style_not_gap`.
   Rubric (same as the AI pass): accept a candidate that names a specific,
   concrete, testable, non-trivial gap genuinely useful for a follow-up about
   *this* item; a fact already stated in the text is not a gap.
3. Score it:
   ```bash
   python scripts/human_review_control.py score benchmarks/open_review/rounds/round_006/batch1
   ```
   This prints human acceptance, AI acceptance, raw agreement, Cohen's kappa,
   and the accept/reject confusion counts (both-accept, both-reject,
   human-only, ai-only). It reads `../ai_review/` only at scoring time.

A second human (`reviewer_human_2`) can repeat on a copy for inter-human
agreement too; the scorer compares whatever human packet is present against the
AI arm.

## What the result will mean

- **High agreement / kappa** → the delegated AI reviews are a usable proxy, and
  the round 006–007 numbers stand as AI-estimated signals with a measured
  reliability.
- **Low agreement / kappa** → the AI acceptance numbers are reviewer-specific
  and must be treated as one opinion, not a stable Layer-C estimate.

Either outcome is reportable and directly addresses the round 007 finding that
reviewer variance was an unseparated confound. This remains a **signal**, not
Layer-C validation: n = 58 candidates / 12 items, and the ≥ 0.60 target is
unchanged.

## Files

```text
human_review_packets.json   # 58 blind rows to fill (regenerate with: human_review_control.py build <batchdir>)
```
The AI arm being compared against is `../ai_review/open_set_review_packets.json`.

# Round 008 — the payoff test: does acting on validated seeds improve answers?

> **Status: two runs done.** `payoff_run_01/` free rewrite = SSL win 0.333 (1/3, derailed); `payoff_run_02/` no-harm append = SSL win 1.0 (3/3). The run-01 losses were the rewrite step, not the seeds (n=3; run-02 win is a superset-by-construction floor — see its caveats).** This is the strategic pivot (see
> `docs/research/milestone-open-set-2026-06.md`). Rounds 004–007 answered "can
> the system detect/validate gaps?" (yes, near-human on a capable model). Round
> 008 asks the question that actually decides SSL's worth: **does *using*
> validated seeds make the answer measurably better, end to end?**

## Why this and not another detector round

Form is solved (v0.3g) and detector precision is now a review/Gate function
(two mechanical precision levers — density, grounding — failed empirically).
More detector tuning has diminishing, semantic-bound returns. The unproven part
of the 4.6 vision is the *use* of seeds, not their supply.

## Design (extends `ssl45_model_benefit_suite`, no new metric pipeline)

The model-benefit suite already generates, per item, two answers with the same
model: `baseline` (answer directly) and `ssl_guided` (revise using promoted
seeds). It currently scores them on deterministic token coverage-delta. Round
008 adds the missing layer: **a blind reader judgment of which answer is
actually better.**

1. **Generate** baseline + ssl_guided answers on ~12 items
   (`run-model-benefit-suite --backend hf-transformers`,
   Phi-3.5-mini). Seeds come from the already-reviewed batches so the
   "validated seed" input is real, not synthetic.
2. **Blind pairwise judgment**: present the two answers per item with arm hidden
   and order shuffled (mirror `build_blind_control_packets.py`); the reader
   marks which is more complete/useful, or tie. Reader = the κ-0.63-validated
   AI judge (`reviewer_ai_claude`), with a human anchor on a subset.
3. **Metric**: SSL-guided **win rate** over baseline (wins / (wins+losses),
   ties reported separately). No total score; baseline-coverage-delta kept
   alongside as the deterministic cross-check.

## Success criteria (signal, not proof)

- SSL-guided win rate **> 0.5** by a margin beyond the per-item noise, under
  blind judgment, on real validated seeds;
- the win is not just "longer answer" — track added-word count and require the
  win to survive a length control (the suite already penalizes unsupported
  additions);
- a human anchor on ≥ 5 items agrees in direction (re-uses the round-006
  human-review tooling).

A **null or negative** result is the most important possible outcome: it would
mean the detect→validate machinery doesn't yet translate into better answers,
and would redirect SSL toward *why* (probe formulation, seed injection method)
rather than more detection. Report it straight.

## Claim boundary

End-to-end answer quality is the 4.6 payoff claim, so this is the highest-stakes
layer — keep it the most conservative. n ≈ 12 items, single AI judge + small
human anchor: a **first signal** on whether seeds help, never "SSL improves
answers" unqualified. Blind, order-randomized, length-controlled, or it does not
count.

## Dispatch (harness is built — ready to run)

The blind answer-pair scaffold already lives in `run-model-benefit-suite`
(`blind_review_items` + hidden `blind_answer_key`), and the win-rate scorer
(`scripts/answer_pair_winrate.py`) now closes the loop. Flow:

```bash
# 1. generate baseline + ssl_guided answers on a real model (~per-item cost)
shadowseed run-model-benefit-suite --backend hf-transformers \
  --model-id microsoft/Phi-3.5-mini-instruct \
  --output results/ssl45_model_benefit_suite.json

# 2. a blind reader fills scores_to_fill.better_answer (A/B/tie) in
#    blind_review_items — without reading blind_answer_key. Reader = the
#    kappa-0.63-validated AI judge, with a human anchor on a subset.

# 3. win-rate (unblinds via the key; length-controlled)
python scripts/answer_pair_winrate.py results/ssl45_model_benefit_suite.json
```

Output: `ssl_win_rate` (ssl_wins / decided) and `ssl_win_rate_length_neutral`
(restricted to pairs where the SSL answer was not longer) + tie/pending counts.

The only remaining input is a model dispatch; everything downstream is in place
and unit-tested.

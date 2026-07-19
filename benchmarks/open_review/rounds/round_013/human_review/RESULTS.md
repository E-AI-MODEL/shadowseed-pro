# Round 013 — human review results

> **Status: human-anchored payoff result.** Four reviewers scored the 10 blind
> gpt-4.1 answer pairs and were **unanimous**, and their verdicts **matched the
> assistant's blind verdicts on every item** (as reported by the maintainer,
> 2026-06-19).

## Outcome

| measure | value |
|---|---:|
| reviewers | 4 |
| items | 10 (9 gap scenarios + 1 do-no-harm control) |
| inter-reviewer agreement | unanimous (1.0) |
| **human SSL win-rate (gap scenarios)** | **9 / 9** |
| DNH_UNITS control | tie (as designed) |
| **human-vs-AI raw agreement** | **10 / 10 (1.0)** |

Because the four reviewers agreed with each other and with `ai_better_answer` on
all ten items, the human SSL win-rate equals the AI win-rate (9/9 gap scenarios
SSL-better, DNH a tie), and human-vs-AI agreement is 1.0 (κ is degenerate at
perfect agreement; the headline is the raw match across 4 independent reviewers).

## What this establishes

1. **The payoff is human-anchored on this fixture.** Acting on validated
   gap-seeds produced answers that humans — not just the AI judge — consistently
   rated better, with zero harm and zero unsupported additions (rounds 011–013).
2. **The AI judge is a faithful proxy here.** 4/4 reviewers matching the
   assistant's blind verdicts on 10/10 items retroactively strengthens the
   AI-judged rounds 010–012 (and is a stronger agreement signal than round 006's
   single-reviewer κ 0.63).
3. **The semantic metric agrees too** (round 013 part 1: +0.575), so three
   independent signals — human, AI reader, semantic coverage — now line up.

## Honest bounds (unchanged by this result)

- **Author-designed scenarios + ground-truth gaps.** This validates: *when a
  valid gap-seed exists, acting on it yields an answer humans judge better, and
  the AI judge tracks the humans.* It does **not** validate that SSL discovers
  non-obvious gaps in the wild — that is the open-set detection track (rounds
  004–007, human κ 0.63).
- **n = 10, one model (gpt-4.1), one fixture, one review session.** A strong,
  human-anchored signal — not a broad claim. As-reported by the maintainer; the
  four reviewers were sourced and scored outside this repo.
- Unanimity with the AI judge is encouraging but also a reminder to keep future
  packs genuinely blind and to include harder/adversarial items where humans and
  the AI might legitimately diverge.

## Next steps

1. **Adversarial payoff items**: pairs where the promoted "gap" is wrong,
   irrelevant, or already covered, so a faithful reviewer (and the AI) should
   sometimes pick the baseline. This tests discrimination, not just agreement.
2. **Close the wild-detection loop**: feed open-set-detected seeds (not
   author-designed) through the same payoff + human-review pipeline.
3. Record the reviewers/protocol if a citable provenance is wanted.

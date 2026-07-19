# Round 005 — delegated AI review (offset-0 single-arm + blind control)

> **Status: completed under explicit maintainer delegation.**
> This is **AI review** (`reviewer_ai_claude`), not human review. The maintainer
> delegated it after the offset-12 human batch was already landed. It closes the
> two parts of round 005 that were still open: the offset-0 batch and the blind
> model-vs-baseline control. It is labeled AI everywhere on purpose.

## What human review remains the authority for

The offset-12 human batch (`../reviewed_offset12/`) stays the **authoritative
Layer-C evidence** and the authoritative reject-code source. This AI pass does
**not** overwrite or relabel it. Per issue #62 ("do not fabricate review
data"), nothing here is presented as human judgment.

## Method

- **One reviewer, one rubric.** A single AI reviewer applied the same bar to
  every candidate: accept only a candidate that names a *specific, concrete,
  testable, non-trivial* absence in *this* text that is genuinely useful for a
  follow-up — well-formed, not a meta-category, not truncated, not a
  near-duplicate of an earlier-accepted candidate in the same item.
- **Blind for the control.** The blind packets were judged without consulting
  `blind_key.json` (the arm mapping). The key is not committed; it is
  regenerated deterministically from the two arm files only at un-blind time.
- **Single-reviewer caveat.** Agreement / unanimity metrics are meaningless
  with one reviewer and must be ignored. The value here is the per-arm accept
  delta (control) and a first labeled read of offset-0.

## Calibration against the human batch

On the 41 offset-12 model seeds the humans already judged, this AI reviewer
agrees on **40/41 (0.98)**. The single disagreement is principled: the AI
rejects *"Of Apple Computer Inc. een Amerikaanse firma is, wordt niet vermeld."*
as `trivial` (world knowledge); the humans accepted it. High agreement is a
credibility signal, not a claim of equivalence to human review.

## Results — blind model-vs-baseline control (secondary robustness)

`blind_control_summary.json`:

| Arm | Judged | Accepted | Accept rate | Atomicity of accepted |
|---|---:|---:|---:|---:|
| model (v0.3e) | 114 | 25 | **0.219** | 1.00 |
| baseline (`adapter_v1`) | 115 | 0 | **0.000** | — |

**Accept-rate delta (model − baseline): +0.219.** The model arm clearly beats
the template baseline under blind review. The baseline produces only the
meta-categories `02_atomic_seeds` §3 forbids ("Rol van X in de gebeurtenis.",
"Onderbouwing van de centrale bewering.") and is rejected wholesale.

**Honest limitation (already noted in the round README):** `adapter_v1` is a
template baseline, so its lines are stylistically recognisable. The interleave
controls for rubric/order effects and rubber-stamping, **not** for arm
recognition. A harder baseline (`adapter_v2` or a weak model) is future work.
The delta therefore confirms "the model is not rubber-stamped and beats a weak
baseline", not "the model produces good seeds" — that is what the absolute
acceptance rate (below, and the human batch) is for, and it is low.

## Results — offset-0 single-arm (first labeled read of items 0–11)

`offset0_seed_review_summary.json` (model candidates, items index < 12):

- unique seeds **54** · accepted **10** · acceptance **0.185**
- criterion pass rates: atomicity 0.81, relevance 0.91, **testability 0.30,
  non_triviality 0.19, follow_up_utility 0.19**
- reject reasons (heuristic-assisted, see caveat): `too_vague` 25,
  `too_broad` 10, `not_relevant` 5, `not_testable` 3, `duplicate` 1

This reproduces the offset-12 human finding on a fresh batch: **the absences
are on-topic but mostly trivial or untestable.** The weakness is substance,
not form — exactly what round 006 is designed to attack.

**Reject-code caveat:** the offset-0 reject *codes* are assigned with mechanical
help (prescreen + rules), not pure reading, so treat the code distribution as
indicative. The criterion booleans and accept/reject decisions are the
reviewer's own judgment.

## Combined round-005 reading (no total score)

- **Primary (Layer C, human, offset-12):** acceptance 0.29 — quality warning.
- **Primary (Layer C, AI, offset-0):** acceptance 0.185 — same pattern,
  consistent with the human batch.
- **Secondary (blind control):** model > baseline by +0.219 accept rate, model
  accepted-atomicity 1.0 — robustness check passes.

Round 005 is now closed on all three. The substance gap stands and hands off to
round 006.

## Artifacts

```text
blind_review_packets.json        # 229 interleaved candidates, AI judgment filled
blind_control_summary.json       # per-arm accept/atomic + delta (after un-blind)
offset0_review_packets.json      # 54 model offset-0 candidates, AI judgment
offset0_seed_review_summary.json # canonical summary route output (single-arm)
offset0_review_report.md         # human-readable summary
offset0_disagreements.json       # empty (single reviewer)
# blind_key.json is intentionally NOT committed; regenerate deterministically.
```

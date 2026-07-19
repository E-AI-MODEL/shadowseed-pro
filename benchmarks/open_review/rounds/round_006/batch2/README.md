# Round 006 — batch 2 (Phi-3.5-mini on arXiv abstracts, first Layer-F signal)

> **Status: AI review complete.** Detector run is real (Actions run
> [27350504602](https://github.com/E-AI-MODEL/shadowseed/actions/runs/27350504602),
> 93 min). Review is **delegated AI** (`reviewer_ai_claude`, single reviewer) —
> labeled AI, not human. This is the first non-news open-set batch in the
> repo's history and therefore the first Layer-F (domain transfer) data point.
> Exploratory: batch 1 is the anchored comparison.

## Run provenance

- **Model:** `hf-transformers:microsoft/Phi-3.5-mini-instruct`, v0.3e prompt
  **unchanged**, `max_new_tokens=512`, greedy — identical settings to batch 1;
  only the input domain differs (one lever per comparison).
- **Input:** `arxiv_abstracts` (`gfissore/arxiv-abstracts-2021`, CC0), offset
  0, 12 abstracts (337–1713 chars; 3 short rows skipped by the
  `min_text_length` filter). Source validated live first via a smoke dispatch
  (run 27350416887).
- **Artifacts are verbatim** (maintainer-uploaded Actions artifact). Runtime
  note: 93 min vs 50 min for batch 1 — abstracts are 3–5× longer than news
  items; budget accordingly in future rounds.

## Mechanical prescreen (triage, not evidence)

60 raw candidates (yield 5.0); the SSLManager atomicity gate rejected **12**
before packet generation (vs 2 on news — almost all "X of Y"-stacked phrases,
which technical prose invites), leaving **48 reviewed candidates**. The
prescreen's `not_atomic` flags exactly those same 12 — the second independent
confirmation of the gate, on a new domain.

| Code (raw 60) | News batch 1 | arXiv batch 2 |
|---|---:|---:|
| `not_atomic` (= manager gate) | 2 | **12** |
| `truncated` | 0 | **2** (heuristic; ~5 visible in item 11) |
| `near_duplicate` | 0 | 1 |
| `parse_leak` | 0 | 0 |
| `claim_vs_gap` (scaffold non-compliance) | 60 | 42 |

Notable: 18 of the 60 raw candidates DID use the absence scaffold ("… wordt
niet vermeld") versus 0 on news — form compliance turns out to be
domain-dependent. The truncations cluster in the one heavily LaTeX-loaded
item (ARXIV_11).

## AI review result (single reviewer, same bar as batch 1)

- unique seeds **48** · accepted **22** · acceptance **0.458**
- criterion pass rates: atomicity 0.96, relevance 0.79, testability 0.73,
  non_triviality **0.46**, follow_up_utility **0.46**
- reject codes: `not_relevant` 5 (false gaps), `style_not_gap` 5, `trivial` 4,
  `too_vague` 4, `not_testable` 4 (the item-11 truncations), `duplicate` 2,
  `too_broad` 2

### Genre note (documented rubric reading)

Abstracts omit detail *by design*, so the bar applied here is: **accept a
candidate that names a claimed-but-unstated specific** of this abstract (the
selection criteria, the algorithm, the congruences, the phase-space region);
**reject** generic detail/implication asks, background-knowledge questions
and restatements of stated findings. This is the same rubric, read for the
genre — flagged here so a future human reviewer can calibrate against it.

## The first Layer-F comparison (same reviewer, model, prompt, settings)

| | News (batch 1) | Science (batch 2) |
|---|---:|---:|
| acceptance | 0.50 | **0.458** |
| non_triviality | 0.50 | **0.46** |
| testability | 0.69 | **0.73** |
| atomicity | 1.00 | 0.96 |
| accepted seeds | 29/58 | 22/48 |

**Reading: the quality transfers.** The drop is −0.04 acceptance — within
single-batch noise, and excluding the one LaTeX-mangled item (ARXIV_11, 0/5)
the science batch scores 22/43 = 0.51, indistinguishable from news. The
accepted seeds are genuinely domain-native ("De exacte methode voor het
isoleren van bona fide YSO's uit de achtergrondcontaminatie", "De specifieke
punten waar de congruenties van $L$-functies worden verkregen") — no news
templates leaked across.

**What shifts is the failure profile, not the quality:**

1. "of"-stacking explodes upstream (manager gate 2 → 12) — technical prose
   invites coordinated noun phrases; the gate absorbs it correctly;
2. truncation returns on dense LaTeX input (item 11) — a length/decoding
   issue, not a domain issue;
3. occasional garbled Dutch technical vocabulary ("interactiviteitstransformatie",
   "Precisiesnede") — translation strain on jargon.

### What this does NOT claim

- One exploratory 12-item batch, AI-judged: this is a **first Layer-F signal**,
  not Layer-F validation. No total score; news and science numbers stay
  side-by-side.
- The ≥ 0.60 Layer-C target is still not met on either domain.

## Artifacts

```text
input/hf_batch.json                  # verbatim run input (12 abstracts)
open_set_seed_output.json            # verbatim run output (60 raw candidates)
run_review_packets_pending.json      # the run's untouched two-reviewer packets (human pass stays possible)
mechanical_prescreen.json / .md      # deterministic triage on the raw 60
ai_review/open_set_review_packets.json       # 48 judged packets, reviewer_ai_claude
ai_review/open_set_seed_review_summary.json  # canonical summary route output
ai_review/open_set_review_report.md          # human-readable summary
ai_review/open_set_disagreements.json        # empty (single reviewer)
```

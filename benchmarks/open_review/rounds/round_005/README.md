# Open-set round 005 — first v0.3e Layer-C round, with blind model-vs-baseline control

> **Status: closed on all three arms.**
> 1. **offset-12 — human** (`reviewed_offset12/`): authoritative Layer-C
>    evidence, 41 seeds, acceptance 0.29.
> 2. **offset-0 — delegated AI** (`ai_review/`): 54 seeds, acceptance 0.185 —
>    same relevant-but-trivial pattern, consistent with the human batch.
> 3. **blind model-vs-baseline control — delegated AI** (`ai_review/`): model
>    0.219 vs baseline 0.0, delta +0.219, model accepted-atomicity 1.0.
>
> The offset-0 and blind-control arms were completed by a single AI reviewer
> under explicit maintainer delegation (98% accept-agreement with the human
> batch on the overlapping seeds). They are labeled AI, not human; see
> `ai_review/README.md`. The substance gap (low non-triviality) stands and
> hands off to round 006.

## Why this round

Round 005 is the first open-set seed-quality round (Layer C) on the v0.3e
detector prompt (merge #109) run on a *capable* model. Its **primary** purpose
is what the SSL 4.6 evaluation matrix (§3) asks of Layer C: can the detector
produce small, relevant, testable, non-trivial seeds on unseen text **without a
ground-truth seed list** — measured by acceptance rate, atomicity ratio,
relevance ratio, reviewer agreement, trivial %, and reject-code counts.

It additionally carries a **secondary** blind model-vs-baseline robustness check
against the `adapter_v1` template baseline. That comparison is adversarial-style
framing (model beats a weaker baseline; 4.5 §20/H1/H8, and the forking-paths
discipline of Gelman & Loken 2013). It is borrowed here only as a robustness
control against rubber-stamping — it is **not** the definition of Layer-C
evidence, and it does not replace the absolute open-set metrics above.

Executed under SSL 4.6 evidence discipline: open text, no ground truth, blind
human review, no total score, no fixture-as-evidence.

## Evidence sources (do not duplicate the existing route)

- **Primary Layer-C metrics** come from the existing canonical route,
  `summarize-open-set-seed-review` on the model-arm packets — it already emits
  acceptance, criterion pass rates (atomicity / relevance / testability /
  non_triviality / follow_up_utility), reviewer agreement, disagreements,
  per-domain counts and reject-code counts. The blind control does **not**
  recompute these (work-categories: no parallel metric pipeline).
- **Secondary robustness** comes from the blind control's per-arm accept/atomic
  comparison (`build_blind_control_packets.py unblind`).

## Go / no-go gate (before any human review)

Run the mechanical prescreen on the model run first:

```bash
python scripts/prescreen_open_set_output.py results/open_review/open_set_seed_output.json \
  --input benchmarks/open_review/rounds/round_005/input/hf_batch.json \
  --round round_005 \
  --output benchmarks/open_review/rounds/round_005/mechanical_prescreen.json
```

- **Reference baselines:** round 004 (Qwen-3B, v0.3d) scored clean-rate **0.45**
  with `claim_vs_gap` dominant; SmolLM2-1.7B was a capability floor (yield
  0.17/item).
- **Proceed to human review only if** the model run clearly beats those:
  yield ≥ ~3 candidates/item and clean-rate well above 0.45. If it is still
  `claim_vs_gap`-dominant, fix the prompt before spending reviewer time.

The prescreen is a deterministic triage aid — **not** human review and **not**
Layer C evidence.

## Blind control design

To keep the seed-quality claim from being a forking-paths artefact (Gelman &
Loken 2013; cf. Tang et al. 2024 on band-exemplar vs distributional prompts),
reviewers judge model and baseline candidates **blind and interleaved**:

```bash
# 1. produce both arms on the SAME input batch
shadowseed run-open-set-seed-review --input <batch> --detector model \
  --model-backend <hf-transformers|ollama> --model-id <id> \
  --output results/open_review/model_seed_output.json
shadowseed run-open-set-seed-review --input <batch> --detector adapter_v1 \
  --output results/open_review/baseline_seed_output.json

# 2. build a single blind packet (arm hidden, order shuffled per item)
python scripts/build_blind_control_packets.py build \
  --model results/open_review/model_seed_output.json \
  --baseline results/open_review/baseline_seed_output.json \
  --input <batch> \
  --packets benchmarks/open_review/rounds/round_005/blind_review_packets.json \
  --key benchmarks/open_review/rounds/round_005/blind_key.json

# 3. reviewers fill `judgment` on the packets (they never see blind_key.json)

# NB: blind_key.json is not committed. Regenerate it deterministically from the
#     two arm files with the same `build` command before un-blinding.

# 4. un-blind and read per-arm accept / atomic rates and the model-vs-baseline delta
python scripts/build_blind_control_packets.py unblind \
  --packets <filled blind_review_packets.json> \
  --key benchmarks/open_review/rounds/round_005/blind_key.json \
  --output benchmarks/open_review/rounds/round_005/blind_control_summary.json
```

## Review unit and fields (per candidate gap)

| Field | Question |
|---|---|
| `atomic` | Bevat de kandidaat precies één gap? |
| `relevant` | Gaat het echt over een betekenisvol gemis in deze tekst? |
| `testable` | Is de gap in principe verifieerbaar of falsifieerbaar? |
| `non_trivial` | Is het meer dan een vage of banale uitbreiding? |
| `useful_for_followup` | Helpt het een goede vervolgstap maken? |
| `accept` | `true`/`false` — eindoordeel van deze reviewer |
| `reject_reason` | code (zie hieronder) als `accept=false` |

Reject codes: `too_broad`, `too_vague`, `trivial`, `not_relevant`,
`not_testable`, `duplicate`, `style_not_gap`.

## Round size and reviewers

- 12–20 source items, two reviewers (`reviewer_a`, `reviewer_b`);
- both reviewers judge every blinded candidate where possible;
- a small complete round beats a large partial one.

## Success criteria

### Primary — Layer-C seed quality (evaluation-matrix §3)

Measured on the model arm via `summarize-open-set-seed-review`:

- acceptance rate ≥ 60% (model candidates not directly rejected);
- atomicity ratio ≥ 70% of accepted candidates;
- relevance ratio and trivial % reported and read separately (no total score);
- reviewer agreement reported with the disagreement log;
- reject-code counts return real learning signal.

### Secondary — baseline robustness (4.5 "boven baseline")

- model arm ≥ `adapter_v1` baseline arm on accept and atomic rate, blind.

This is a robustness control, not the Layer-C definition. These are acceptance
criteria for a first usable open-set evaluation layer, not paper-level claims.

## Artifact contract

```text
input/hf_batch.json                 # the open-set source items (from the run)
model_seed_output.json              # detector=model (v0.3e) raw + normalized
baseline_seed_output.json           # detector=adapter_v1 raw + normalized
mechanical_prescreen.json / .md     # deterministic gate (triage, not evidence)
blind_review_packets.json           # blinded interleaved packets for review
blind_key.json                      # hidden arm mapping (reviewers must not see)
blind_control_summary.json          # per-arm accept/atomic rates + delta (after un-blinding)
```

---

## Run notes (this round, extended 2026-06-02 with the offset-12 batch)

- **Model arm** (`model_seed_output.json`): real Actions artifacts,
  `hf-transformers:Qwen/Qwen2.5-3B-Instruct`, v0.3e, source `ag_news_test`,
  **two batches merged** — offset 0 + offset 12 (limit 12 each). Item
  `AG_NEWS_TEST_12` overlapped both batches with identical candidates and was
  deduplicated. Result: **114 candidates over 23 items** (TEST 0–7, 9–20,
  23–25).
- **Baseline arm** (`baseline_seed_output.json`): `adapter_v1` on the same
  23-item input, 115 candidates.
- **Prescreen gate (combined, regenerated 2026-06-09): yield 5.0/item,
  clean-rate 0.553** (`truncated` 9, `parse_leak` 10, `not_atomic` 38,
  `near_duplicate` 13). The offset-0 batch was mechanically cleaner than the
  offset-12 batch (0.483 alone); all 9 truncations come from offset-12.
  **Diagnosis correction:** the nine candidates previously counted as
  `claim_vs_gap` are in fact unfinished "Of ..."-clauses that never reach
  their absence scaffold — a decoding/parse truncation artifact, not a
  prompt claim-form regression. v0.3e therefore removed the dominant
  round-004 failure mode *completely* (round 004: 30 claim_vs_gap at
  clean-rate 0.45; round 005: 0). The remaining mechanical work is
  truncation (decoding budget / line parser), not absence-phrasing.
- **Blind packets**: 229 blinded candidates (114 model + 115 baseline), 458
  rows (2 reviewers).
- **Key is intentionally NOT committed.** The shuffle is deterministic, so
  `build_blind_control_packets.py build` regenerates the identical key from the
  two arm files at un-blind time. This keeps the blind intact in the repo.

### Mechanical per-arm preview (NOT evidence)

- Prescreen clean-rate: model **0.588** vs baseline **0.0** (every adapter_v1
  candidate lacks the absence form).
- Manager auto-accept is inverted and misleading: it passes ~all short template
  baseline lines but flags longer model sentences — exactly why the manager
  accept rate is not a quality signal and human review is the arbiter.

### Honest limitation of this baseline

`adapter_v1` is a template baseline, so its candidates ("Rol van X.", "Tijdlijn
van Y.") are stylistically recognisable next to the model's fluent absence
sentences. The interleaving therefore controls for **rubric and order effects
and rubber-stamping**, not for arm recognition. A future round can swap in
`adapter_v2` or a weaker model for a harder-to-distinguish baseline.

### Reviewer-aandachtspunten (uit de prescreen + eyeballing)

- **Atomiciteit** — 38/114 model-kandidaten mechanisch `not_atomic` (o.a. TEST_9
  "… 171 of het bedrag …" stapelt met " of "). Kandidaat `too_broad`/`not_atomic`.
- **Truncatie** — 9 kandidaten (offset-12 batch) zijn afgekapte
  "Of ..."-bijzinnen zonder afgemaakt scaffold; de reviewers wezen alle 9 af
  als `not_testable`. (Eerder onterecht als claim-vs-gap geteld.)
- **Parse-leak** — 10 kandidaten met ingebedde nummering of afgekapte zinnen.
- **Over-generatie / near-duplicates** within an item (TEST_1: 5× "Of de tweede
  team een *X* heeft genoemd"; logische ontkenningen) → `duplicate`/`trivial`.
- "tweede team" reads like an awkward translation → reviewer attention.

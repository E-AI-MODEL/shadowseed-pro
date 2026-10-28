# Completed two-moment 48-call inquiry experiment — source-led run record

> **Observed:** 28 October 2026. **Status:** exploratory real-model execution complete; semantic value and Q1/Q2 causation **not independently established**.
> This file is deliberately publication-safe: no raw model transcripts, reviewer mappings, owner keys, credentials or unpublished source archives are included.

## Reproduction anchors

- Original fictitious case: DM26-C02 in observed.json, artifact [12754935105](https://github.com/E-AI-MODEL/shadowseed-pro/actions/runs/40542431712), SHA-256 `0a5094e38ab2fdcf8c68dc8d6a3c75d29eeffd49e1f6c8e138589ed73ca36bbf`.
- **First original attempt**: [40615769463](https://github.com/E-AI-MODEL/shadowseed-pro/actions/runs/40615769463), failed artifact-retrieval preflight, 0 model calls.
- **Free recovery check**: [40615932910](https://github.com/E-AI-MODEL/shadowseed-pro/actions/runs/40615932910), passed original SHA and mock-provider tests.
- **First paid technical attempt**: [40616060572](https://github.com/E-AI-MODEL/shadowseed-pro/actions/runs/40616060572), 1 incomplete/no-visible-answer GPT-5 attempt under 1,900 output-token cap, **0 completed answers**. Failure is neither a negative nor a positive treatment observation.
- **Corrected completed run**: [40616375653](https://github.com/E-AI-MODEL/shadowseed-pro/actions/runs/40616375653), after 4,096 output-token limit adjustment. **48/48 distinct successful model responses**, **24/24 complete two-turn tracks**, **187,255** provider-reported input+output tokens, 0 human completed reviews.
- **Lifetime attempts** in this small study: at most 49, consisting of 1 incomplete technical attempt plus 48 complete calls in the corrected run. Do not report this as 49 experimental responses.
- Corrected run owner-only encrypted artifact: `q1q2-48-encrypted-owner-40616375653` (artifact 12786191379). Its expiry is **4 November 2026**. The private decryption key is outside the public repository and must be kept with the author.

## Actual matrix

| Single fictional case | Model at checkpoint | Research arms | Repetitions per arm | Followup questions | Completed calls |
|---|---|---|---:|---:|---:|
| DM26-C02 after T2, horizon question | GPT-5 | ordinary / deliberate search / weight-zero original candidate / unrelated placebo | 3 | 2 | 24 |
| DM26-C02 after T3, battery question | GPT-6 Luna | same four arms | 3 | 2 | 24 |

**There is only one fictional case, with two different model checkpoints.** The models and their ordinary histories differ between checkpoints. Do not pool them into a single generic effect. The candidate note is a research-context intervention, not promotion via the production Validation Gate. No original candidate was given new answer-steering authority in the product engine.

## Confirmed mechanical results (from decrypted owner data)

| Checkpoint | Arm | Complete pairs | Calls | Input+output tokens |
|---|---|---:|---:|---:|
| Battery | Ordinary | 3 | 6 | 13,875 |
| Battery | Deliberate search | 3 | 6 | 15,381 |
| Battery | Weight-zero candidate | 3 | 6 | 14,253 |
| Battery | Unrelated placebo | 3 | 6 | 14,195 |
| Horizon | Ordinary | 3 | 6 | 31,219 |
| Horizon | Deliberate search | 3 | 6 | 36,837 |
| Horizon | Weight-zero candidate | 3 | 6 | 31,294 |
| Horizon | Unrelated placebo | 3 | 6 | 30,201 |
| **Total** | | **24** | **48** | **187,255** |

Checks: all 48 provider response IDs are distinct, each visible answer matches its stored SHA-256, each recorded model identity matches the requested ID, the predeclared randomized call order matches the stored trajectories, each of the eight model/moment/arm groups contains exactly three two-turn tracks. **Zero** canonical product-Gate-exposure events by experimental design. Zero completed independent human quality ratings.

## Nonblind descriptive observations, not hypothesis verdicts

- **Horizon:** at least two of three ordinary GPT-5 tracks themselves articulate the possible insufficiency of fixed visual references by the second research answer. The candidate must not be claimed to be inaccessible to ordinary generation. The deliberate-search and placebo arms also formulate alternative testable hypotheses.
- **Battery:** the three candidate-exposed GPT-6 tracks focus on possible battery-voltage interactions with motion sensing and timestamping, and their second research answers develop different possible conditional tests involving load, sensor behaviour and observed boundary estimates. Ordinary and deliberately searching GPT-6 tracks also produce testable alternatives (lighting, camera settings, external temperature/load, reverse cause). This is *directional prompt conditioning* until independent semantic comparisons rule out repetition and alternatives.
- **Placebo:** some tracks correctly reject the unrelated wear-measurement candidate instead of forcing a connection to the buoy data. Rejection of an invalid research direction is potentially useful and must not count as an automatic failure of question generation.
- **No scientific discoveries are validated:** the fictional case has no measured battery-electrical design, no recorded horizon visibility, and no actual ocean/boating observations. An effect on later text does not verify an environmental mechanism or grant truth to a model-generated relation.

## What remains before an efficacy claim

Two human reviewers must separately assess whether a second-turn track contains a **genuinely different falsifiable relation**, mere echo, already accessible baseline content or an unjustified invented assumption. Keep owner allocation secret until both are submitted; the prepared blind packets are outside GitHub. Then report per-checkpoint paired outcomes and disagreements, with no generic statistical significance from two dependent checkpoints. A stronger prospective replication with more independent cases may be necessary for generalization, but is **not** a reason to rewrite this recorded null/partial evidence as a success.

## Archive and safety

The exact executed one-shot workflow is retained as inert [text](archived-once-workflow.yml.txt). The four active one-shot workflow files were removed from `.github/workflows` after the completed run to prevent accidental repeated paid execution; Git history preserves prior attempts. The source-runner, offline tests, research protocol and public encryption key remain available for inspection.

The author-side private result bundle must never be copied into this public repository. For reproducibility, owner-only receipts and exact raw answers are retained offline, not in GitHub issue discussions or model-judge prompts.

# Live runtime real-model measurements

This directory preserves the first intentional real-model pipeline run of the
one-generation live runtime. Treat it as diagnostic evidence, not an efficacy result.
It exposed model-language drift, a generative few-shot leakage bug, and a recovery
metric that was not identifiable under sustained surfacing. The raw JSON artifacts
are preserved unchanged as historical evidence of that run.

## Environment and provenance

| Field | Value |
|---|---|
| Date | 2026-08-16 UTC |
| Source revision | `78c67caca664f82e20bf5f60661827efd1ebfc5a` |
| Source worktree | clean |
| Input | `src/shadowseed/data/ssl_session_suite.json` (`ssl-session-0.2`, 3 conversations, 22 turns) |
| Input SHA-256 | `3041467fff0ee398726782173190c3a13ce6c919d235bc9952b0c3889df05f0f` |
| Model and detector | `Qwen/Qwen2.5-0.5B-Instruct` |
| Embeddings | `sentence-transformers/all-MiniLM-L6-v2` |
| Decoding | greedy, 96 maximum new tokens |
| Python | 3.11.15 |
| Model packages | PyTorch 2.13.0, Transformers 5.15.0, Sentence Transformers 5.7.0 |
| Runner | GitHub Actions `ubuntu-24.04` |
| Workflow run | [31928321119](https://github.com/E-AI-MODEL/shadowseed-pro/actions/runs/31928321119) |

The JSON artifacts pin the Shadowseed revision, input digest, model identifiers,
package version, call counts, thresholds, and dirty-worktree state. The Hugging
Face model revisions and the complete dependency set were not pinned in the
command, so the run is traceable but not guaranteed to be bit-for-bit
reproducible after upstream model or package changes.

## Diagnostic status

`Qwen/Qwen2.5-0.5B-Instruct` did not follow the Dutch input language reliably, so
answer and detector language drift contaminated the run. The generative detector also
echoed prompt examples because `_FEWSHOT_GOOD_GENERATIVE` was missing from the
few-shot leak blocklist. The stress run influenced 19 of 22 turns, leaving no later
uninfluenced observation window for most suppressed candidates. Its recorded
`later_recovery_rate = 0.0` is therefore not evidence of permanent loss.

The follow-up runtime fixes all three measurement problems. New live measurements use
an English suite, request English responses explicitly, block all prompt few-shots, and
report recovery as `null` when no later uninfluenced observation window exists. An
evidence-quality rerun should use a materially stronger instruction model; the 0.5B
artifact remains useful only as a pipeline/regression diagnostic.

Do not compare the historical `later_recovery_rate` numerically with a new artifact
without accounting for the changed denominator: new runs include only suppressed
candidates that have a later uninfluenced observation window.

## Results

| Arm | Product policy | Answer calls | Detector calls | Detected candidates | Promotions | Influence records | Influenced turns | Suppressed occurrences | Admissible suppressed | Later recovered |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Default `evidence-backed` | yes | 22 | 22 | 85 | 0 | 0 | 0 | 0 | 0 | 0 |
| Default `counterfactual` | no | 22 | 22 | 85 | 0 | 0 | 0 | 0 | 0 | 0 |
| Deferral stress `counterfactual` | no | 22 | 22 | 82 | 7 | 27 | 19 | 69 | 58 | 0 |

The default artifact confirms that the shipped evidence-backed policy did not
grant authority from model recurrence alone. The ordinary recurrence-only
counterfactual also produced no promotion with this model, suite, and default
thresholds. Its zero suppression count therefore means that deferral was not
observed, not that deferral had zero cost.

The separate stress artifact deliberately sets `min_occurrences=1`,
`promotion_threshold=0.2`, `surface_threshold=0`, `early_turn_margin=0`, and
`resurface_margin=0`. This forces non-production surfacing opportunities. On
those turns, the fail-closed rule deferred all 69 detected candidate
occurrences. Fifty-eight passed the normalization/atomicity proxy and none was
semantically recovered on a later qualifying unsuppressed turn.

That result exposes a possible opportunity cost under sustained influence. It
does not show that the candidates were true, relevant, or useful. The stress
setup also leaves few later unsuppressed turns, so zero observed recovery is not
evidence of permanent loss under normal product settings.

## Timing

| Artifact | Adapter setup | Live turn loop | Deferral scoring | Wall time |
|---|---:|---:|---:|
| Default, two arms | 13.623 s | 2199.652 s | 0.000 s | 2213.276 s |
| Stress, one arm | 6.387 s | 1208.287 s | 0.003 s | 1214.679 s |

Each live turn contains one visible answer generation and one separate
model-backed detector call. The timing describes this CPU-bound Hugging Face
run; it is not an Ollama or production latency claim.

## Artifacts

- [`ssl_live_session_qwen2.5_0.5b_default.json`](ssl_live_session_qwen2.5_0.5b_default.json), SHA-256 `8fa2776669bca01d98ad6d144bfdad1dfe1fe13351aad9d570f73f79ff2e2e0c`
- [`ssl_live_session_qwen2.5_0.5b_deferral_stress.json`](ssl_live_session_qwen2.5_0.5b_deferral_stress.json), SHA-256 `945267dcc2bd9d3648168f9202ee5b46386a03aa616b57f7d04c17cbee3e2c22`

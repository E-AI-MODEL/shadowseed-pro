# Shadowseed possibility-space feasibility pilot (2026-10-24)

**Research prototype only.** This is not the shipping Shadowseed runtime, does not create actual Shadow Seeds, does not modify the Validation Gate, and has **not** proven the fundamental possibility-space thesis.

The authoritative two-clause research question and related literature are stored in `docs/research/possibility-space/` (PR #219). This pilot is a *first assay and instrumentation test*, not a preregistered confirmatory evaluation.

## One independent world, two observed quantities

Three synthetic typed networks (ARCHIVE, LOGISTICS, NEGATIVE) describe which components can connect. The independent deterministic oracle permits a candidate directed edge only when its types and zones match and it creates no cycle. It measures newly reachable **source-to-sink pairs** after adding one valid bridge. Removing that bridge returns the network to its original state.

- **Q1 proxy:** Which candidate links does one ordinary-model prompt select, and which links are proposed under equally budgeted deliberate search, persistent-note prompts, or speculative shadow prompts? B/C/D see the same baseline-A output; no arm sees hidden fixture answers. A link not proposed by A is only *unselected in that observation*, not proof it lies outside the model's latent or probabilistic support.
- **Q2 proxy:** Did a proposed bridge cause additional terminal pairs to become reachable under the declared graph rules, and can the model predict them? The independent oracle checks each claim and edge-ablation. This is **not** a demonstration of new semantic concept types, transformation of an abstract conceptual space, or real-world scientific novelty.
- **Coupled proxy:** Are some downstream paths caused by D's novel-to-A candidate and absent in the other arms? If all arms find them, the control succeeds and Shadowseed has shown *no incremental benefit*.

The fixtures include one known helpful bridge per positive world **and multiple admissible non-helpful choices**, plus a negative world where no new source-to-sink chain is possible. Fixture truth is never in live prompts. The task might be easy for a capable model; that is a legitimate negative result.

## Four paired model arms (A/B/C/D)

Each arm receives one candidate-generation call and one downstream-prediction call on **the same model**. The ordinary A output is supplied to B/C/D as their shared reference. Only the prompting strategy differs. This is an **exploratory prompting comparison**, not an implemented SSL memory pipeline; arm D is merely a *shadow-inspired research candidate*. A stronger follow-up needs genuinely persistent weightless seeds and repeated ordinary-generation samples.

Model suggestions never validate themselves. The script separately reports valid and invalid bridges, independently verified downstream paths, stage-two correct/incorrect predictions, and zero-opportunity cases. The oracle is objective only **inside the formal fictional environment**; there are no independent human judgments of conceptual novelty.

## Offline tests, independent of any API

```bash
cd experiments/possibility_space
python -m unittest -v test_pilot
python pilot.py selftest --output /tmp/possibility-oracle.json
```

The self-test result is explicitly marked `model_calls=0` and `this_is_not_model_evidence=true`. It tests evaluator mechanics and negative controls, **not** the Q1/Q2 claims.

## Bounded live test (only when credentials already exist)

```bash
python experiments/possibility_space/pilot.py run \
  --case-ids ARCHIVE LOGISTICS NEGATIVE \
  --model gpt-5 --reasoning-effort low \
  --max-output-tokens 900 --max-calls 24 \
  --output /tmp/possibility-model-pilot.json
```

The local command requires an `OPENAI_API_KEY` environment variable. **Never paste, print or commit it.** The opt-in GitHub workflow `.github/workflows/possibility-space-pilot.yml` checks the **existing repository-level** `OPENAI_API_KEY` secret when present; otherwise the result is `blocked_no_api_key`. No credentials are set or restored by this code, no conversations are uploaded, and no production authority changes. The action uploads only the synthetic evidence bundle. Maximum 24 calls and 900 generated tokens per call, including reasoning. Actual model and token usage are recorded in raw output.

## Major limits and next research gate

1. Two positive synthetic worlds and a negative case are **not** representative research evidence; this mainly tests instrumentation, parsing, nontrivial candidate selection, and whether a capable baseline already saturates the task.
2. A generated valid bridge represents graph-rule feasibility only. It does not show that the LLM knows a previously nonexistent relation.
3. Q1 has no token-logit distribution, model-internal intervention, or repeated sampling. No `anti-embedding` conclusion follows.
4. Q2 demonstrates only path reachability from adding an edge, not transformation of conceptual constraints or previously unthinkable relation **types**.
5. Baseline A is observed first, so B/C/D have additional visible baseline context (the same shared context for all three). A future matched design must control this.
6. A "shadow" prompt is not a deployed Shadowseed system. No answer-quality superiority or actual system efficacy can be attributed to SSL from this pilot.
7. Error, blocked, incomplete, null and negative results must be recorded transparently, not concealed as missing opportunities.

**Exit condition:** Move to a preregistered, held-out relational-transformational study only if this harness can reject invalid and zero-utility proposals and can reliably capture parseable strong-model results. The first study must use causal candidate ablation, equal context exposure, stronger controls, model capacity tiers and independent evaluations. If ordinary generation already solves these examples, that is evidence against *incremental value on these examples* and a reason to avoid celebrating a trivial benchmark.

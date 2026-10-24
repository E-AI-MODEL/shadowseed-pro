# Archived Shadowseed fixed-edge feasibility pilot v0 (2026-10-24)

**Research prototype only.** This is not the shipping Shadowseed runtime, does not create actual Shadow Seeds, does not modify the Validation Gate, and has **not** proven the fundamental possibility-space thesis.

> **RETIRED AS A TEST OF THE TWO-CLAUSE THESIS (2026-10-25):** The 24-call GPT-5 run [#40136015917](https://github.com/E-AI-MODEL/shadowseed-pro/actions/runs/40136015917) was completed with 8/24 unparseable outputs; the missing-edge task did not measure new *relation kinds* or representational possibility transformation. This directory is retained for independent reproduction of the **offline** oracle and historical failure analysis, not a current Q1/Q2 experimental arm. See the [revised research protocol](../../docs/research/possibility-space/revised-q1-q2-experiment-2026-10-25.md) on the documentation base branch (PR #219) and [the full run report](../../docs/research/possibility-space/first-live-pilot-result-2026-10-24.md).

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

## Historical GPT-5 run — do not repeat as the new test

The originally bounded GPT-5 fixed-edge test used the GitHub Environment `OpenAI key` and its secret `OPENAI_KEY`, injected as the Python environment variable `OPENAI_API_KEY`. The real run made 24 calls; 16 responses were parseable, and 8 were incomplete. No credential value was exposed.

**The associated GitHub Actions workflow is now manual/offline-only**, and no longer reads the API secret or makes paid model calls. Historical behavior can be inspected from the original Git revision and immutable run artifacts; repeat model calls only as a separately approved **plumbing reproduction**, not as evidence of the revised research thesis. The current protocol does not authorize repeating this run merely by increasing token budgets.

## Major limits and next research gate

1. Two positive synthetic worlds and a negative case are **not** representative research evidence; this mainly tests instrumentation, parsing, nontrivial candidate selection, and whether a capable baseline already saturates the task.
2. A generated valid bridge represents graph-rule feasibility only. It does not show that the LLM knows a previously nonexistent relation.
3. Q1 has no token-logit distribution, model-internal intervention, or repeated sampling. No `anti-embedding` conclusion follows.
4. Q2 demonstrates only path reachability from adding an edge, not transformation of conceptual constraints or previously unthinkable relation **types**.
5. Baseline A is observed first, so B/C/D have additional visible baseline context (the same shared context for all three). A future matched design must control this.
6. A "shadow" prompt is not a deployed Shadowseed system. No answer-quality superiority or actual system efficacy can be attributed to SSL from this pilot.
7. Error, blocked, incomplete, null and negative results must be recorded transparently, not concealed as missing opportunities.

**Historical finding:** The v0 fixed-edge oracle passed its controls, but the live measurement failed both response-completeness and **construct-validity** checks against the protected question. The next study requires Q1 probability-conditioned selection, Q2 genuinely changed **relation types/constraints**, same-model/cost-matched baselines, a cross-turn **weightless** candidate arm, prospective independent verification, and candidate ablation. This repository directory should **not** be extended into that study without completing its G0 construct-validity gate.

# Post-alignment capability scaling

This protocol measures Shadow Seed Learning after the doctrine-alignment merge in PR #62. It is designed to scale from the GitHub-hosted Qwen 7B reference tier to stronger local, dedicated-runner, or hosted models without changing the SSL trust model.

## Canonical protocol and amendment history

The canonical preregistration for definitive post-alignment model measurements is:

`src/shadowseed/data/capability_scaling_preregistration_v2.json`

Version 1 is intentionally retained as an immutable protocol-history artifact. Before accepting or interpreting a post-alignment Qwen 7B result as the definitive reference, the first execution attempt exposed two measurement blind spots:

1. the v1 harness observed detector candidates only after parser filtering, so parser-rejected malformed output and few-shot leakage were not measurable;
2. a declared Hugging Face model revision was written into provenance but was not yet passed to the underlying tokenizer/model loaders.

Version 2 was registered before the definitive reference result was accepted. It adds raw detector/parser diagnostics and requires declared Hugging Face revisions to be applied to `from_pretrained`, not merely recorded. The earlier execution remains diagnostic and is not the v2 baseline.

## What is held fixed

Model capability is an experimental variable. It is never an authority variable.

Every run keeps these invariants:

- detector output is candidate material, not evidence;
- one accepted seed represents one atomic epistemic direction;
- every seed starts with `weight = 0`;
- trace and recurrence remain separate from authority;
- recurrence is never external evidence;
- the live arm uses `evidence_backed` and injects no external evidence;
- the evaluation arm is explicitly non-production and uses `exploratory` only to create cross-turn A/B opportunities;
- influence is still subject to the normal point-of-use safety contract;
- SSL-exposed same-turn candidates are deferred rather than counted as independent recurrence;
- parser diagnostics never change seed weight, evidence, Gate policy, or point-of-use authorization.

## Why there are two arms

### Live evidence-backed arm

The live arm answers once per turn with the same runtime used by the product-oriented path. It measures:

- raw detector/parser behavior;
- numbered and unnumbered detector output;
- parser rejection and few-shot leakage;
- duplicated numbering caused by prompt-prefill reconstruction;
- accepted candidate output;
- malformed or non-atomic prescreen failures after parsing;
- exact and semantic duplicate rates;
- same-turn SSL contamination/deferral;
- Gate events;
- influence records;
- latency and call counts.

No external evidence is supplied. Therefore a positive weight event, `VALIDATED`, or `PROMOTED` decision in this arm is treated as a harness failure, not as an interesting result.

A zero promotion count is expected trust-model behaviour. It is not evidence that SSL has no value.

### Evaluation exploratory arm

The evaluation arm keeps the baseline history isolated from the SSL answer. Recurrence may promote under the explicit research-only `exploratory` policy. A blind A/B pair is created only when a previously promoted seed actually passes point-of-use checks and surfaces on a later turn.

This arm asks whether a carried-over epistemic direction adds value under a controlled research counterfactual. It is not production authority and is never merged into the live metrics.

## Detector/parser observability

The detector retains raw model output and non-authority parser diagnostics for research runs. The parser reports at least:

- nonblank output lines;
- numbered lines;
- unnumbered nonblank lines;
- accepted candidates;
- parser-rejected blank/placeholders;
- citation/stub rejections;
- few-shot leakage rejections;
- duplicate rejections;
- nested numbering prefixes removed.

A duplicated prefix such as `1. 1. candidate` can arise when a backend reconstructs the prompt's prefilled `1.`. Removing only that syntactic prefix is allowed and counted explicitly. It does not add, split, merge, or reinterpret candidate semantics.

Few-shot leakage is reported as detector behavior before seed candidacy. A rejected few-shot echo is not a seed, evidence item, contradiction, or Gate decision.

## Candidate review

Automatic atomicity screening is a filter, not semantic proof. The runner emits a blind candidate packet for independent reviewers.

Reviewers score:

- atomic;
- relevant;
- specific;
- investigable;
- nontrivial;
- grounded to the supplied context;
- factual assertion masquerading as uncertainty;
- duplicate of a prior candidate;
- useful to investigate;
- epistemic role: `gap`, `doubt`, `what_if`, `other`, or `unclear`.

The review packet does not contain model identity, promotion state, or hidden runtime keys. Raw parser diagnostics remain in the research artifact rather than the blind packet. A separate key file preserves provenance for later analysis.

## Answer review

Answer reviewers receive option A and option B without knowing which is baseline and which is SSL. They choose `A`, `B`, or `tie` and may add notes. The answer key is separate.

No A/B item is created on a turn where no seed surfaced. This prevents the denominator from being inflated with turns where SSL could not have affected the answer.

## Provenance and reproducibility

A bundle contains:

```text
manifest.json
summary.json
REPORT.md
environment.txt
inputs/
  preregistration.json
  suite_<id>.json
raw/
  live_<id>.json
  evaluation_<id>.json
review/
  candidate_review_packet.json
  candidate_review_key.json
  answer_review_packet.json
  answer_review_key.json
```

`manifest.json` records and hashes:

- source Git revision and dirty state;
- package version;
- model backend and runtime id;
- public model reference;
- model revision or digest;
- quantization where applicable;
- detector id and generative prompt-template hash;
- embedding backend, reference, revision, and dimension;
- runtime thresholds;
- preregistration;
- exact input suites;
- Python/platform/pip environment;
- every generated artifact.

For Hugging Face runs, `--model-revision` is mandatory and is applied to both tokenizer and model loading. For Ollama runs, `--model-digest` is mandatory. Sentence-transformer runs require `--embedding-revision`; reference workflows materialize the embedding model from that exact snapshot. A hosted OpenAI run must supply an explicit model snapshot/revision identifier rather than relying on an unversioned alias.

A GitHub reference bundle additionally records the external runner layer, including the Ollama version, Ollama binary SHA256, actual pulled model digest, GitHub runner metadata, and the resolved embedding revision. This metadata is added to the same artifact hash chain before final verification.

The runner can verify a moved bundle without access to the original working directory:

```bash
python -m shadowseed.benchmark.capability_scaling verify results/capability-scaling/<run>
```

Any changed or missing hashed artifact fails verification.

## Running the harness

A runner can use any supported real model backend. Example with a locally served model:

```bash
python -m shadowseed.benchmark.capability_scaling run \
  --backend ollama \
  --model-id qwen2.5:7b-instruct-q4_K_M \
  --model-reference qwen2.5:7b-instruct-q4_K_M \
  --model-digest <ollama-digest> \
  --quantization q4_K_M \
  --embedding-backend sentence-transformers \
  --embedding-model <pinned-local-embedding-path> \
  --embedding-reference sentence-transformers/all-MiniLM-L6-v2 \
  --embedding-revision <hf-commit-sha> \
  --suite primary=src/shadowseed/data/ssl_session_suite.json \
  --suite transfer=src/shadowseed/data/ssl_session_transfer_suite.json \
  --evaluation-conversation CONV_STARTUP \
  --evaluation-conversation CONV_EDU \
  --preregistration src/shadowseed/data/capability_scaling_preregistration_v2.json \
  --output-dir results/capability-scaling/qwen7b-post-alignment-v2
```

The evaluation subset is fixed before results are inspected. For the GitHub Qwen 7B reference, `CONV_STARTUP` supplies a primary-domain conversation and `CONV_EDU` supplies a transfer-domain conversation. The live arm still runs every conversation in both suites.

## High-end/frontier execution

GitHub-hosted compute is a reference tier, not the SSL design ceiling. Stronger models should run on an appropriate external environment while producing the same bundle schema.

The minimum comparison contract across model tiers is:

- the same canonical v2 preregistration or an explicitly versioned amendment made before results are interpreted;
- identical suite versions and hashes;
- identical detector id and prompt-template hash;
- identical live/evaluation policy split;
- comparable semantic embedding setup;
- pinned model identity or provider snapshot;
- same parser diagnostic definitions;
- same human-review dimensions;
- no interpretation before the bundle passes hash verification.

Provider price, latency, GPU memory, and wall time belong in resource reporting. They do not modify Gate rules.

## Review summary

After independent reviewers fill the generated packets:

```bash
python -m shadowseed.benchmark.capability_scaling summarize-reviews \
  --candidate-packet review/candidate_review_packet.json \
  --candidate-key review/candidate_review_key.json \
  --answer-packet review/answer_review_packet.json \
  --answer-key review/answer_review_key.json \
  --output review_summary.json
```

The summarizer reports per-field rates, epistemic-role counts, raw agreement, Cohen's kappa where two reviewer values are available, and unblinded SSL/baseline answer wins. Reviewer disagreement is retained as a result.

The runner creates review packets but does not invent independent human judgments. Until independent review is completed, subjective candidate quality and answer-benefit claims remain pending even when the automatic bundle is complete.

## Claim discipline

A completed automatic bundle may support a bounded statement such as:

> Under this pinned model, detector prompt, parser, suite, embedding setup, and runtime revision, the system produced the following detector/parser, candidate, duplication, contamination, Gate, and evaluation-opportunity measurements.

After independent blind review, the same bundle may additionally support bounded candidate-quality and answer-preference statements for that exact configuration.

It does not support:

- "the seeds are true";
- "SSL always improves answers";
- "larger models should receive more weight";
- "recurrence is evidence";
- "parser acceptance proves atomicity";
- "the system is production-ready".

Historical Qwen 7B artifacts from PR #61 remain pre-alignment reference data and must not be overwritten or relabeled as post-alignment evidence.

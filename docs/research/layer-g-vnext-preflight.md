# Layer G vNext: frozen-design preflight and preregistration draft

**Status:** P0/P1 implementation candidate for issue #203. No model study
started. No neural or SSL-benefit result can be claimed from this document.

## Why the old probe cannot be rerun as an SSL test

Round 033 used externally generated binary **dialectical verdicts** for
statements that the model was explicitly shown. It failed preregistered
replication at <=0.5B. That bounded null result stands. It does not measure
an internally available but **unexpressed** relation.

The older activation hooks, sparse regression, permutations and controls
can be reused as infrastructure. Their task/labels and timing cannot be
silently recycled. See the original results in
[round 033](../../benchmarks/open_review/rounds/round_033/RESULTS.md).

The SSL research construct is a possible, still-unexpressed epistemic
relation. A generated candidate is not a fact and absence from output does
not establish what is represented internally. H-Neurons is inspiration for
instrument design, not evidence that an SSL neural correlate exists.

## What P1 now protects

- The input crossing the capture boundary is **only original_prompt +
  original_answer**. Candidate text and labels are separate review metadata.
- The input and its SHA-256 digest are locked together at capture. An
  optional detector is not permitted to assemble a prompt from its own
  candidate text and feed it to the model under test.
- An explicitly injected candidate, class, or gold-label marker is rejected.
  Verbatim candidate appearance is rejected for the positive "unspoken"
  label. Semantic paraphrases still require independent human judgement.
- The same original stimulus cannot be duplicated as two differently labeled
  candidate examples. This is crucial: one vector cannot identify which of
  two unseen candidates an externally assigned label refers to.
- Source and topic are disjoint across discovery/validation/test.
- Token-offset selection must cover the *entire* original-answer span.
  Truncation and inconsistent layer tensor shapes fail closed.
- The synthetic adapter tests the instrument only. It cannot produce
  model-quality, sparse-neuron or latent-knowledge evidence.

## Construct and label plan (not yet preregistered)

The target is a **candidate-independent signal in original-answer
activations** that predicts a later, separately reviewed class:
"coherent and unspoken" versus matched controls ("already expressed",
"unsupported", and unresolved). This is an operational starting point,
not yet proof of reading a particular candidate from the hidden state.

Critical unresolved validity question: without showing the candidate,
activations may reflect general answer uncertainty, length, topic or
answer style instead of the semantic representation of a particular
unspoken relation. Therefore a positive classifier alone is insufficient.

### Independence and chronology

P1 works with **frozen original-answer text**. The optional HF adapter
performs teacher-forced **offline replay** of that text through the
original model; it is not a synchronous capture taken when the answer
was originally generated. A later P2 study should instrument original
generation directly, record the model response and activations at that
time, then generate and review candidate directions in a *separate*
stage. Do not conflate these two capture modes.

Labels must be assigned with blind independent review, including
uncertainty and disagreements. "Coherent" is a scope-limited external
judgement, not confirmation of a latent model state.

### Necessary controls and future statistical design

For P2/P3 pre-register *before* test inspection:

1. capable open-weight model, revision hash, tokenizer revision, dtype,
   exact hooks/read locations, hardware/library digests, languages and
   source inclusion rules;
2. generation of original answer first, activations synchronously captured,
   candidate direction generated only **after** capture and independently
   judged; full provenance chronology and admission/decline log;
3. matched already-expressed, semantically nearby unsupported and
   lexically altered controls; review noise and "undetermined" cases;
4. grouped holdout across **source and topic**, avoid split leakage
   through paraphrases or common documents;
5. preselected primary statistic, effect size, confidence interval,
   test-set independence, permutation null, corrections over tested
   layers/neurons and robustness to correlated feature alternatives;
6. a frozen null-verdict when evidence is absent; only a replicated
   independent signal can motivate causal intervention with random
   and non-target neuron controls, including collateral response behavior.

There is no arbitrary 12-case criterion. The final sample size must
follow an explicit power/precision design after a separate pilot, and
the pilot cases must be excluded from the final held-out measurement.

## How to run the P1 mechanical preflight

From the repository root after installing product and research packages:

    python research/scripts/layer_g_vnext_preflight.py \
      --fixture research/fixtures/layer_g_vnext_synthetic.json \
      --output /tmp/layer_g_vnext_p1.json

Expected output identifies **synthetic_preflight_only** and
**research_claim: none**. CI can test the pipeline without a model
download. Re-running this fixture is not a new H-Neurons experiment.

## Separation of authority

L2 capture cannot read or mutate weight, trace, TTL, TrTL, seed state,
Validation Gate or the point-of-use authorization boundary. Any future
model-internal signal is an **observation**, not promotion or independent
evidence. This research route cannot silently change Level 1 product
defaults. PR #202 can be independently assessed for Level 1 safety.

## Status and next gate

- P0: protocol draft with source and known null-result traceability.
- P1: synthetic leakage/preflight code and tests, pending CI.
- P2: not performed; selection of a suitable model and a live-generation
  capture method is required first.
- P3: not preregistered; not performed.
- P4: not performed.

**Read this correctly:** a green CI means the instrument and its
negative controls behave as specified. It is not model-internal evidence.

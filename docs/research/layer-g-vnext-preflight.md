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


## P2: synchronous original-generation decision-feature capture (code ready)

[Implementation](../../research/src/shadowseed_research/benchmark/layer_g_live_generation.py),
[CLI](../../research/scripts/layer_g_live_generation.py) and
[mechanical tests](../../research/tests/test_layer_g_live_generation.py) add
a distinct generation-time reader.

- It hooks chosen **down_proj inputs while the original model.generate() call
  is running**. The first vector comes from the final prompt input token,
  which predicts the first generated token. Cached forwards then use the
  preceding generated token to predict the next. These are **prefix-decision
  features**, not activations of the generated token itself. The number and
  ordering of hook calls must match generated token IDs exactly.
- Only a frozen original prompt, its digest, an immutable 40-character model
  revision, explicitly chosen layers and bounded greedy decoding enter
  capture. Candidate text and evaluation labels have no route into the
  reader. Synthetic tests deliberately fake PyTorch/model.forward hooks,
  without downloading weights or claiming neuroscience.
- Raw token-aligned arrays are saved into an isolated new directory as
  compressed NPZ, with artifact SHA-256s, model/runtime provenance and a
  manifest marked **unlabelled_mechanistic_pilot / research_claim: none**.
  Original prompt text is not copied into the artifact; generated responses
  and activations still require careful privacy and access controls.
- The GPU runner refuses absent CUDA, GPU memory below the configured 40 GiB
  floor, multiple visible GPUs, mutable revisions, reused output directories
  and inputs not explicitly identified as synthetic. It never silently falls
  back to 0.5B CPU as if that answered the SSL hypothesis.

The proposed first *engineering* pilot uses a capable open-weight model such
as **Qwen/Qwen2.5-14B-Instruct** on a dedicated >=40-GiB CUDA GPU. Obtain its
exact revision from the model Hub and pin torch/transformers/tokenizer
libraries before capture. The test-only input is
[synthetic prompt](../../research/fixtures/layer_g_vnext_synthetic_prompt.txt).
Example:

    python research/scripts/layer_g_live_generation.py \
      --model-id Qwen/Qwen2.5-14B-Instruct \
      --model-revision <resolved-40-hex-model-sha> \
      --prompt-file research/fixtures/layer_g_vnext_synthetic_prompt.txt \
      --read-layers model.layers.12.mlp.down_proj,model.layers.36.mlp.down_proj \
      --max-new-tokens 80 \
      --output-dir /private/layer-g/first-pilot

**Not yet shown by passing unit tests:** that a real Qwen release has precisely
the assumed hook order, that its cached decoding takes a single input token
per step under pinned packages, or that any recovered activation feature
encodes an unexpressed relation. A live-model pilot must establish the first
two *before* anything is called neural SSL evidence.

P2 is successful as an **instrument** only if the real generation completes,
the captured vector count matches output token count, arrays are finite and
reproducible under a pinned revision/environment, and no candidate or label
entered capture. A model-specific hook mismatch is a failed preflight, not a
negative finding about internal possibility representation.

## P2: no-payment 14B route (quantized instrument pilot)

The freely downloadable **Qwen/Qwen2.5-14B-Instruct** weights can be
run on a free NVIDIA T4 or P100 with 14+ GiB of available VRAM via
[the Colab/Kaggle notebook](../../research/notebooks/layer_g_14b_free_gpu.ipynb).
Use the one-click
[Open in Colab](https://colab.research.google.com/github/E-AI-MODEL/shadowseed-pro/blob/feat/layer-g-vnext-preflight/research/notebooks/layer_g_14b_free_gpu.ipynb)
link (select a free GPU first), or import the notebook into a Kaggle GPU
notebook. Both platforms have availability/quota limits; **no paid cloud
jobs or billing tokens are used**.

This route loads the 14B model in bitsandbytes NF4 **4-bit**, double quant,
float16 arithmetic. It *changes the actual representation* compared to
the unquantized 14B source and the original H-Neurons setup. Therefore its
activations are evidence about the quantized model/instrument ONLY.
Do not pool NF4 feature measurements with BF16/FP16 or make
full-precision-neuron identity claims.

The notebook uses the existing generation-time hook reader from this PR;
real model weights are downloaded only **after** CUDA and disk preflight.
It refuses a smaller-model fallback or use of hosted paid APIs. Model Hub
revision, Git source commit, GPU and package versions are recorded, and
the zip output is limited to fictional synthetic input. The notebook
intentionally does not have unattended GitHub access to publish results.

**Execution status:** notebook syntax and boundary tests run in CI.
No free-GPU model execution has yet been verified through this notebook,
and passing these tests is NOT evidence that 14B features have been captured.

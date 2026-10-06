# ADR-010: Capability-based model role routing

Status: proposed

## Context

Shadowseed historically used the primary session model for both answer generation
and candidate-gap detection. Same-turn revision already had a separate optional
model role.

That coupling is convenient for a single-model demo but it is a poor fit for a
local multi-model setup. The tasks have different output contracts:

- answer generation is broad and user-facing;
- detection must produce a small structured set of atomic candidate gaps or
  `NONE`;
- revision is conditional and only rewrites an answer after authorized context
  is available.

A small model can be useful for one of these tasks without being suitable for
all of them. Parameter count alone is not a sufficient capability test: model
family, training, quantization, reasoning behaviour, prompt compliance and
output discipline all matter.

## Decision

Shadowseed treats generation, revision and detection as explicit model roles.

The persisted session configuration supports:

- `backend` / `model_id` / `max_new_tokens` for answer generation;
- `revision_backend` / `revision_model_id` for same-turn revision;
- `detection_backend` / `detection_model_id` /
  `detection_max_new_tokens` for candidate-gap detection.

When no detection role is configured, detection inherits the primary generation
backend, model and generation budget. Existing sessions therefore retain their
previous behaviour.

Role changes are behaviour changes, not authority changes. They are included in
the behaviour fingerprint and audit projection but do not alter the authority
configuration digest.

## Eligibility policy

Shadowseed does **not** impose a rule such as "models below X billion parameters
are forbidden".

Instead, model eligibility is task-specific and evidence-based:

1. define the exact role and output contract;
2. evaluate the model on a role-specific benchmark with positive and negative
   controls;
3. record parser loss separately from genuine model abstention;
4. measure quality and latency independently;
5. recommend a model for a role only when it meets that role's acceptance
   criteria.

Parameter count and quantization may be recorded as capacity/cost metadata, but
they are not substitutes for the benchmark.

A model that fails broad detection may still be tested for a narrower microtask.
That microtask must remain outside Validation Gate authority unless an existing
canonical authority path explicitly permits its output.

## Local multi-model implication

A practical local setup may therefore use a stronger instruction-following
model for structured detection while reserving a smaller reasoning model for a
narrower or conditional role. The exact assignment is configuration, not a
hard-coded product assumption.

This allows small models to earn a useful role without forcing them through
every complex Shadowseed operation, and avoids spending large-model compute on
tasks a smaller model can already perform reliably.

## Consequences

Positive:

- different tasks can use different local models;
- detection gets an independent token budget;
- model-role choices are reproducible in the behaviour audit;
- existing single-model sessions remain compatible;
- future role-specific routing can be added without changing Gate authority.

Costs:

- a multi-model session may require more than one local model to be loaded;
- users and benchmarks must distinguish model quality from parser behaviour;
- automatic routing needs explicit capability evidence before it can become a
  default.

## Non-decisions

This ADR does not:

- select DeepSeek R1, Gemma2, Llama or any other model as a universal default;
- define a minimum parameter count;
- grant an LLM authority over Gate promotion or evidence;
- introduce automatic model switching based only on model name or size;
- make benchmark results a product-quality score.



## Local web routing policy

The local web client must not infer role capability from a model family name,
parameter count, or the mere presence of another installed model.

Automatic assignment of a secondary local model is allowed only when the exact
model identifier has explicit role-specific capability evidence recorded by the
product. Evidence for one role does not imply eligibility for another role.

If no such evidence exists, the web client preserves single-model behaviour:
generation, detection and revision inherit the user-selected model through the
existing fallback rules.

This keeps automatic routing subordinate to the eligibility policy above.
Adding an entry to the capability registry is therefore a behaviour change that
must be justified by a committed role-specific benchmark result and reviewed as
such.

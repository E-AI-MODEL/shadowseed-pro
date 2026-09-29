# What is Shadow Seed Learning?

Shadow Seed Learning (SSL) is a model-independent learning layer that runs
alongside a language model. It does not retrain the model weights. Instead, it
builds an external, persistent and inspectable memory of candidate perspectives
that may become useful later.

## Core idea

A normal LLM answers from its model weights, current prompt and available
context. SSL adds a separate shadow process:

**observe -> seed -> recur / gather evidence -> validate -> promote -> relevance
check -> point-of-use influence**

A shadow seed is a hypothesis or candidate perspective. It is not automatically
true and it does not automatically influence the model.

## Authority

Seeds gain authority only through the configured lifecycle and Validation Gate.
Contradictions can block them. Even a promoted seed must still pass relevance
and point-of-use checks before it may affect a later answer.

## Why this can become distinctive

Because the shadow memory persists, two Shadowseed installations using the same
base LLM can diverge over time if they process different conversations,
documents or corpora. That resembles experience accumulation more than classic
fine-tuning.

The important distinction is that SSL experience remains external to the model
weights. It can be inspected, attributed, contradicted, decayed and removed.

## More data is not automatically better

Large-scale text ingestion is useful only when SSL also performs memory hygiene:
semantic deduplication, clustering, recurrence tracking, provenance, validation,
contradiction handling, decay and selective surfacing.

The design goal is therefore:

**observe broadly, grant authority selectively, retrieve narrowly.**

## User control

The product exposes four authority profiles:

- **Controlled**: authority-bearing validation remains user-controlled.
- **Assisted**: low-risk lifecycle work is automated and the user is asked when
  an authority decision still needs confirmation.
- **Autonomous**: SSL may validate, promote and surface automatically when policy,
  provenance, Gate and point-of-use checks allow.
- **Open research**: maximum experimental autonomy while preserving audit and
  Gate records.

## How to verify SSL

A user should not have to infer influence from answer differences. The product
therefore exposes:

- **Shadow** for seed lifecycle and status;
- **Verify** for stored SSL-on / SSL-off comparisons and attribution;
- **Technical inspection** for raw JSON, Gate events, trace, relevance and
  influence records.

A textual difference between two generations is not evidence of SSL influence
unless an authorized seed actually surfaced on that turn.

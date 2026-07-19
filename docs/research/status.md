# Research Status

## Defensible status

The repository is **research-ready**. Core mechanics, benchmark harnesses, and a broad regression suite are present and executable as an installed package.

## Supported claims

- Trace and weight are implemented as separate concepts.
- New seeds begin weightless.
- TTL decay and TrTL reactivation are implemented and tested.
- The Validation Gate controls promotion and records decisions.
- The agent contract blocks unapproved point-of-use influence.
- Live chat and session benchmarks share the same surfacing rules.
- Fixture runs demonstrate harness behavior, not real-model quality.

## Claims not supported yet

- General answer-quality improvement across open-ended tasks.
- Production readiness.
- Safety against all prompt-injection or seed-spam attacks.
- Reliable benefit from every promoted seed.
- A general internal neural signal for missing context.

## Remaining production work

- durable seed, evidence, and event storage;
- schema migrations and deterministic replay across versions;
- operational monitoring and alert thresholds;
- privacy, retention, deletion, and access-control policies;
- rollback for promoted influence;
- rate limits and adversarial seed-spam controls;
- operator approval for high-impact actions;
- real-world evaluations with independent review.

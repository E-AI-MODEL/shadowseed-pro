# Research Status

## Defensible status

The repository is **research-ready, locally mass-testable, and able to produce structured privacy-minimized tester datasets**. Core mechanics, benchmark harnesses, a broad regression suite, a chat-first local Workbench, standalone build contracts, verifiable exports, and support-bundle aggregation are present. This status does not imply production readiness or general answer-quality benefit.

Version 0.5.1 is the current source/release candidate. A public release should be described as published only after the corresponding immutable `v0.5.1` tag and verified release assets are actually present.

## Supported claims

- Trace and weight are implemented as separate concepts; new seeds begin weightless.
- TTL decay and TrTL reactivation are implemented and tested.
- Semantic recurrence is scoped to eligible observation contexts and remains observation, not evidence.
- Gate authority is policy-dependent. The ordinary live product uses `evidence_backed`; research/evaluation may use explicitly different policies such as `exploratory`.
- The Validation Gate records authority decisions and verified external support remains provenance-bound to underlying source identity.
- The point-of-use agent contract blocks unapproved or stale influence.
- A tester may request a same-message SSL-off control without authoring a baseline; that control does not mutate SSL or later conversation state.
- Full report and privacy-minimized support exports are integrity-checked.
- Verified support bundles can be aggregated into schema `shadowseed-support-dataset-v1`; duplicate support-session identities and non-support/tampered inputs are rejected.
- Standalone packaging has frozen self-test, provenance, and checksum contracts.

## What collected tester data means

Support datasets are structured observational artifacts. They preserve pseudonymous support-session identity, software/environment identity, sanitized configuration, model/backend identity, and structural outcome/feedback counts while omitting conversation and seed free text by design.

This makes multi-tester collection practical, but collection is not inference. A support dataset does not automatically establish candidate quality, causal SSL benefit, factual correctness, or safety. Those claims require an explicit study protocol, inclusion rules, controls, analysis plan, and appropriate review. Full reports may be used for deeper qualitative research only under a separate privacy/data-handling decision because they contain conversation content.

## Claims not supported yet

- General answer-quality improvement across open-ended tasks.
- Universal or reliably complete missing-information detection.
- Reliable benefit from every promoted or surfaced seed.
- Calibration between seed weight and factual correctness.
- Cross-domain, cross-model, or cross-lingual generalization of candidate quality.
- A general internal neural signal for missing context.
- Safety against all prompt-injection, evidence-poisoning, or seed-spam attacks.
- Hostile-network or high-impact production readiness.

## Remaining production and evidence work

- durable append-only or tamper-evident audit persistence;
- deterministic replay assurance and migration guarantees across future versions;
- hostile-network authentication, tenancy, TLS/CSRF controls, rate limits, and backend isolation;
- managed secrets plus explicit privacy, retention, deletion, and access-control operations;
- operational monitoring, rollback, and incident handling;
- platform vendor signing/notarization and a decision on Intel macOS support;
- broad high-end-model efficacy studies with frozen protocols and independent review;
- real-world usability and safety evaluation.

Issue-level research follow-up, including independent candidate-quality review of existing Qwen evidence, remains research work rather than a prerequisite for publishing the local mass-tester software artifact unless a future release explicitly declares otherwise.

## Appropriate use today

Appropriate uses include local tester studies, mechanism inspection, controlled experiments, benchmark development, structured support-data collection, and research discussion. Do not treat Shadowseed Pro as a certified safety layer for healthcare, finance, employment, law, public administration, education decisions, or autonomous high-impact action.

# Research Status

## Defensible status

The repository is **research-ready, locally mass-testable, able to produce structured privacy-minimized tester datasets, and equipped for preregistered evidence-backed paired efficacy studies**. Core mechanics, benchmark harnesses, a broad regression suite, a chat-first local Workbench, standalone build contracts, verifiable exports, support-bundle aggregation, candidate review packets, and influence-opportunity accounting are present. This status does not by itself imply `production-ready/local` or general answer-quality benefit.

Source version 0.7.1 is the current production-local assurance candidate. Version identity, production status, and public release availability remain separate facts: describe `v0.7.1` as published only after the fresh immutable tag and verified release assets actually exist, and describe it as `production-ready/local` only after the exact-SHA acceptance and unchanged-candidate soak requirements are complete. The existing `v0.7.0` release and older tags remain immutable historical software references and are not rewritten by this upgrade.

## Research access

Repository states and software releases that include the root `LICENSE` file are available under PolyForm Noncommercial License 1.0.0. The license permits the noncommercial purposes stated in its terms, including qualifying research, experiment, testing, modification, and distribution. Commercial use requires separate permission. This is source-available licensing rather than an OSI open-source claim.

The new license is not retroactive. Historical repository states and artifacts retain the rights terms distributed with those versions. Third-party dependencies, model weights, datasets, the manuscript, and separately identified material retain their own applicable terms.

The release pipeline treats license delivery as a distribution contract: standalone manifests record the license hash, Python wheel/sdist builds are checked for exact license inclusion, and a public release includes `LICENSE` as a checksum-covered asset.

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
- Standalone packaging has frozen self-test, provenance, checksum, and license-delivery contracts.
- The capability-scaling harness produces blinded candidate and answer-review packets for pinned model/runtime configurations.
- The evidence-efficacy runner can submit predeclared operator-attested external support only through the canonical `ShadowChatSession.submit_evidence` boundary while keeping the `evidence_backed` Gate policy.
- Evidence-efficacy A/B items are created only on later turns where an authorized seed actually surfaces.
- `opportunity_audit.json` separates candidate observation, evidence submission, Gate authority, selection, point-of-use authorization, surfacing, and A/B generation instead of treating every no-A/B path as one undifferentiated failure.
- Production-local hardening now includes actor-attributable authorization, durable tamper-evident authority audit state, migrations/recovery controls, loopback-local deployment boundaries, lifecycle/deletion operations, and release/supply-chain assurance paths. These controls are necessary for, but do not by themselves complete, the `production-ready/local` claim.

## Existing post-alignment evidence

The checked-in Qwen2.5 7B q4_K_M post-alignment capability bundle contains 43 live candidate occurrences. Its automatic measurements report zero parser rejections, zero few-shot leakage, one malformed/non-atomic prescreen failure, no exact duplicates, a small semantic-duplicate rate, and zero unexplained positive-weight live Gate events. It also contains 43 candidate-review items that still require independent human review.

Its exploratory evaluation subset produced zero surfaced turns and therefore zero legitimate blinded answer A/B items. That is a sequencing/opportunity result. It is not evidence that recurrence is missing external evidence, not proof that SSL has no effect, and not a reason to weaken the ordinary product Gate.

## What collected tester data means

Support datasets are structured observational artifacts. They preserve pseudonymous support-session identity, software/environment identity, sanitized configuration, model/backend identity, and structural outcome/feedback counts while omitting conversation and seed free text by design.

This makes multi-tester collection practical, but collection is not inference. A support dataset does not automatically establish candidate quality, causal SSL benefit, factual correctness, or safety. Those claims require an explicit study protocol, inclusion rules, controls, analysis plan, and appropriate review. Full reports may be used for deeper qualitative research only under a separate privacy/data-handling decision because they contain conversation content.

## Evidence-backed efficacy boundary

The efficacy protocol introduced in v0.6.0 adds a third research view next to the live no-evidence negative control and the exploratory recurrence counterfactual.

The efficacy runner uses baseline-isolated evaluation mechanics so a baseline answer and SSL answer can be compared without changing later baseline history, but it explicitly selects the shipped `evidence_backed` Gate policy. External support is submitted through `ShadowChatSession.submit_evidence` with an external signal kind, supporting direction, explicit verification attestation, and stable `source_ref`.

The runner cannot establish source truth. The researcher/operator remains the trust anchor behind the assertion that a source actually supports the selected candidate. Generated model output, recurrence, similarity, probes, and the harness itself are never silently upgraded to verified evidence.

A failed predeclared selector, blocked Gate decision, point-of-use denial, or absence of a later relevant turn remains visible in the opportunity audit. The harness does not change policy or fabricate a candidate to force an A/B denominator.

## Claims not supported yet

- General answer-quality improvement across open-ended tasks.
- Universal or reliably complete missing-information detection.
- Reliable benefit from every promoted or surfaced seed.
- Calibration between seed weight and factual correctness.
- Cross-domain, cross-model, or cross-lingual generalization of candidate quality.
- A general internal neural signal for missing context.
- Safety against all prompt-injection, evidence-poisoning, or seed-spam attacks.
- Hostile-network or high-impact production readiness.
- General efficacy from the existence of the runner alone; real-model results and independent review are still required.

## Next evidence work

The highest-value follow-up is empirical rather than architectural:

1. complete independent review of the existing 43 Qwen candidate items;
2. preregister evidence-efficacy suites with genuine externally reviewable support and later relevance opportunities;
3. execute the same frozen protocol across at least two meaningful model tiers while pinning model and embedding provenance;
4. blind-review only surfaced A/B pairs and report null/unmatched/blocked opportunities alongside positive comparisons;
5. decide whether candidate generation, prompts, thresholds, or product direction need changes only after those results are available.

Issue #63 remains the natural home for high-end capability/evidence follow-up. Candidate-quality review is research work, not a hidden prerequisite for the production-local release-assurance sequence.

## Remaining production work

The first production target is `production-ready/local`. Its remaining work is release evidence rather than a new SSL authority architecture:

- land the 0.7.1 release-candidate preparation on protected `main` from the exact macOS sealing fix;
- obtain successful exact-head required CI plus Linux/macOS/Windows production-local and standalone evidence;
- create a fresh immutable `v0.7.1` tag on the exact protected-main candidate SHA;
- publish and verify checksums, provenance, SBOM, lockfile, wheel/sdist, standalone artifacts, license delivery, and trusted pre-publication attestations;
- pass the read-only Production Release Assurance workflow against that exact tag;
- complete the required unchanged-candidate soak of at least 24 hours with normal local Workbench use and `shadowseed doctor` evidence;
- keep the candidate free of unresolved P0/P1 production findings through promotion.

Protected-main quality gates are active. Hosted production remains a separate target and still requires its own authentication, tenancy, hostile-network, abuse-control, managed-secret, and service-operation controls. Native Apple notarization/Developer ID signing, Windows Authenticode signing, and broader real-world usability/safety evaluation also remain outside the current local production claim.

## Appropriate use today

Appropriate uses include local tester studies, mechanism inspection, controlled experiments, benchmark development, structured support-data collection, candidate-quality review, and preregistered evidence-backed paired studies. Source version 0.7.1 is a production-local assurance candidate, not yet a completed `production-ready/local` release. Do not treat Shadowseed Pro as a certified safety layer for healthcare, finance, employment, law, public administration, education decisions, or autonomous high-impact action.

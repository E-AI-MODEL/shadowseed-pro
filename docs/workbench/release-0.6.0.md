# Shadowseed Workbench 0.6.0 Research Preview

Version 0.6.0 is the research-access and evidence-measurement upgrade. It preserves the shipped live `evidence_backed` authority model while making noncommercial research/testing explicitly licensed and adding a preregistered path for measuring answer-level effects only when verified support actually reaches later authorized surfacing.

Public release availability is a separate publication fact. Treat `v0.6.0` as published only after the immutable tag and verified release assets exist.

## What changed

### Noncommercial research access

Repository states and releases that include `LICENSE` are distributed under PolyForm Noncommercial License 1.0.0 with the required copyright notice for H. Visser / E-AI-MODEL.

The license supports the noncommercial purposes defined by its terms, including qualifying research, experiment, testing, modification, and distribution. Commercial use requires separate permission. This is source-available licensing, not an OSI open-source claim.

The change is not retroactive: historical releases and repository states keep the rights terms distributed with those versions.

### License delivery is release-tested

The release path now fails closed when license delivery is incomplete:

- wheel and source distribution must contain the exact repository `LICENSE` bytes;
- each frozen standalone archive contains `SHADOWSEED_LICENSE.txt`;
- standalone manifests record `license_identifier` and `license_sha256`;
- release provenance records the same license identity/hash;
- the public release includes `LICENSE` as a top-level checksum-covered asset.

### Evidence-backed paired efficacy research

A new runner is available at:

```text
python -m shadowseed.benchmark.evidence_efficacy
```

It uses the canonical `ShadowChatSession` and its existing `submit_evidence` boundary. The runner does not define its own Gate or change live product policy.

The research session uses baseline-isolated evaluation mechanics with `gate_policy_id = evidence_backed`. This allows a baseline and SSL answer to be compared without feeding the SSL answer into later baseline history, while authority is still granted only by the normal evidence-backed policy.

The bundled preregistration is:

```text
src/shadowseed/data/evidence_efficacy_preregistration_v1.json
```

Evidence plans may use only external evidence kinds (`ssot`, `human_feedback`, `retrieval`), a stable `source_ref`, supporting direction, and explicit operator/researcher verification attestation. Generated model output, recurrence, similarity, probe output, and the harness itself never become evidence.

### Opportunity audit

Each planned evidence event emits an explicit stage trace:

```text
candidate observed
-> evidence submitted
-> Gate authority granted
-> later selection
-> point-of-use authorization
-> surfaced
-> blinded A/B generated
```

Unmatched selectors, Gate blocks, point-of-use denials, and lack of later relevance are retained as results rather than collapsed into `0 A/B` or repaired by weakening policy.

### Blind review remains human

A blinded answer packet/key is produced only on surfaced turns. Reviewer fields remain blank. The software does not invent independent human judgments.

Existing Qwen post-alignment candidate packets remain pending independent review; v0.6.0 does not rewrite those historical artifacts or claim that the new runner proves benefit.

## What did not change

- New candidates start with positive trace and zero steering weight.
- Recurrence is observation, never external evidence.
- Ordinary new Workbench sessions use `runtime_mode = live` and `evidence_backed`.
- Authority changes remain Validation Gate owned.
- Contradictions remain blocking.
- Point-of-use authorization remains mandatory.
- Same-message SSL-off controls do not mutate candidate detection, recurrence, Gate, SSL state, or later history.
- Ordinary tester feedback remains record-only unless an explicit external-evidence action is used.
- The reviewed manuscript remains pinned to its own source 0.5.0 implementation anchor; this software release does not silently rewrite the paper/PDF.

## Scientific boundary

Version 0.6.0 is research instrumentation, not an efficacy result. It enables stronger tests of whether and when authorized uncertain memory helps, but the answer still depends on real-model execution, valid external support, frozen protocols, and independent review.

Do not claim from this release alone:

- general answer-quality improvement;
- reliable benefit from every seed;
- universal missing-information detection;
- semantic truth;
- protection against all evidence poisoning or prompt injection;
- production readiness.

## Publication requirements

A published v0.6.0 prerelease must contain:

- three platform standalone archives and manifests;
- exact bundled license hash in every standalone manifest;
- `PROVENANCE.json` tied to the exact source SHA and license hash;
- one Python wheel and one source distribution with exact license inclusion;
- top-level `LICENSE`;
- `SHA256SUMS` covering the published files.

Publication remains fail-closed on exact `main` SHA before and after release creation.

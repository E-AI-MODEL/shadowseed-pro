# Workbench 0.7.1 limitations

Shadowseed Workbench 0.7.1 remains a local research preview and production-local assurance candidate for single-user use. It is not yet a completed `production-ready/local` release, a hostile-network service, a multi-user authorization boundary, or a scientific evidence generator by itself. The noncommercial research access and efficacy instrumentation introduced in 0.6.0 remain available; neither feature upgrades the assurance claim automatically.

## Security and deployment

- Native and standalone servers bind to loopback by default.
- There is no built-in login, tenant separation, hostile-network TLS/CSRF boundary, abuse protection or multi-user access-control layer.
- Remote binding is only for controlled environments that provide their own network/access controls.
- The Docker image listens on `0.0.0.0` internally; the documented mapping publishes host loopback only.
- Platform-vendor signing/notarization is separate from checksum/provenance verification and is not implied by the standalone build contract.
- macOS standalone builds now re-seal the final application after bundle mutations and verify the exact archive after extraction, but native Apple Developer ID signing and notarization are still not claimed unless a release explicitly provides that evidence.

## Data handling

- Prompts, answers, seeds and audit data are stored locally in the tester workspace.
- Full reports are content-bearing and should be treated as sensitive unless inspected.
- Support bundles are content-minimized but can still reveal pseudonymous session identity, backend/model choice, platform/environment metadata, sanitized configuration and structural counts.
- The support-dataset collector combines only verified support bundles, rejects duplicates and records input bundle hashes. This is structured pseudonymous collection, not formal anonymization.
- Evidence-efficacy bundles can contain full questions, baseline/SSL answers, candidate-selection metadata, source references, and research audit data. Treat them as research data, not privacy-minimized support bundles.
- Study owners remain responsible for consent where applicable, minimization, retention/deletion, access control, ethics/legal requirements and analysis protocol.
- Hosted inference/embeddings send relevant content to the selected provider after explicit confirmation/configuration.
- SSL-off comparison adds one model generation; with a hosted model this means an additional hosted request.

## Runtime authority

- New ordinary sessions use canonical `live` runtime with the `evidence_backed` Gate policy.
- The Workbench has no direct weight/status/promotion editor.
- Tester feedback is `record_only` by default.
- Verified support is a separate operator-attested input to the existing Validation Gate; the UI cannot select the Gate outcome or weight.
- The operator/host remains the trust anchor for evidence attestation. Field/provenance validation is not source-truth verification.
- Reusing one underlying external `source_ref` through another signal channel does not create extra authority credit.
- Promotion means eligibility for consideration, not mandatory influence. Point-of-use checks remain current and separate.
- The evidence-efficacy runner does not define a benchmark-only Gate. It submits external support through `ShadowChatSession.submit_evidence` and keeps `gate_policy_id = evidence_backed`.

## Comparison and scientific limits

- The same-message SSL-off control does not enter detection, recurrence, the Gate, seed state or later history.
- The actual live turn is the only state-changing turn.
- Textual difference is not automatically an SSL effect; when no authorized seed surfaced, ordinary generation variance remains possible.
- Historical evaluation sessions, authored baselines, scenario JSON and blind benchmark flows remain research tools.
- The evidence-efficacy loop is also research-only: it uses baseline-isolated evaluation mechanics to create paired comparisons while the authority policy remains evidence-backed.
- A preregistered selector that does not match remains an unmatched opportunity. The runner does not substitute another candidate after inspecting results.
- A blind A/B item is generated only when an authorized seed actually surfaces on a later turn.
- Fixture runs are deterministic product/research smokes, not model-effect evidence.
- Workbench exports and aggregated support datasets do not by themselves establish statistical significance, candidate quality, causal benefit or generalization.
- A complete efficacy bundle still requires valid external support, appropriate experimental design and independent human review before answer-preference claims are defensible.
- `benchmarks/results/**` remains a separately governed evidence area.

## Licensing and distribution

- Repository states/releases containing `LICENSE` are subject to PolyForm Noncommercial License 1.0.0. Commercial use is not granted by that license.
- The software license is source-available, not an OSI open-source claim.
- Historical artifacts retain the rights terms distributed with those versions; the 0.6.0 license change is not retroactive.
- Third-party dependencies, model weights, datasets, the manuscript and separately identified material can have different rights terms.
- Python wheel/sdist builds are checked for the exact repository license.
- Frozen standalone bundles include the license and record its SHA-256 in their manifest.

## Compatibility

- Python 3.10 and 3.12 are covered by repository CI for the package.
- Windows, macOS and Linux receive standalone build/self-test coverage.
- The standalone contract targets Windows amd64, Linux x86_64 and macOS Apple Silicon arm64. Intel/universal macOS support is not implied.
- Frozen bundles must pass their packaged self-test before upload.
- macOS bundles must also pass strict code-signature verification before archiving and after the exact ZIP is re-extracted.
- Model weights are not bundled. Model acquisition, provider availability and credentials remain separate dependencies.
- The browser UI uses Gradio 6 through the `[workbench]` extra.
- Workspace schema migration remains conservative; back up valuable prerelease workspaces before upgrades.

# Workbench 0.5.1 limitations

Shadowseed Workbench 0.5.1 is a local mass-tester research preview for single-user use. It is not a production service, a multi-user authorization boundary, or a scientific evidence generator by itself.

## Security and deployment

- Native and standalone servers bind to loopback by default.
- There is no built-in login, tenant separation, hostile-network TLS/CSRF boundary, abuse protection or multi-user access-control layer.
- Remote binding is only for controlled environments that provide their own network/access controls.
- The Docker image listens on `0.0.0.0` internally; the documented mapping publishes host loopback only.
- Platform-vendor signing/notarization is separate from checksum/provenance verification and is not implied by the standalone build contract.

## Data handling

- Prompts, answers, seeds and audit data are stored locally in the tester workspace.
- Full reports are content-bearing and should be treated as sensitive unless inspected.
- Support bundles are content-minimized but can still reveal pseudonymous session identity, backend/model choice, platform/environment metadata, sanitized configuration and structural counts.
- The v0.5.1 support-dataset collector combines only verified support bundles, rejects duplicates and records input bundle hashes. This is structured pseudonymous collection, not formal anonymization.
- Study owners remain responsible for consent where applicable, minimization, retention/deletion, access control, ethics/legal requirements and analysis protocol.
- Hosted inference/embeddings send relevant content to the selected provider after explicit confirmation.
- SSL-off comparison adds one model generation; with a hosted model this means an additional hosted request.

## Runtime authority

- New ordinary sessions use canonical `live` runtime with the `evidence_backed` Gate policy.
- The Workbench has no direct weight/status/promotion editor.
- Tester feedback is `record_only` by default.
- Verified support is a separate operator-attested input to the existing Validation Gate; the UI cannot select the Gate outcome or weight.
- The operator/host remains the trust anchor for evidence attestation. Field/provenance validation is not source-truth verification.
- Reusing one underlying external `source_ref` through another signal channel does not create extra authority credit.
- Promotion means eligibility for consideration, not mandatory influence. Point-of-use checks remain current and separate.

## Comparison and scientific limits

- The same-message SSL-off control does not enter detection, recurrence, the Gate, seed state or later history.
- The actual live turn is the only state-changing turn.
- Textual difference is not automatically an SSL effect; when no authorized seed surfaced, ordinary generation variance remains possible.
- Historical evaluation sessions, authored baselines, scenario JSON and blind benchmark flows remain research tools.
- Fixture runs are deterministic product smokes, not model-effect evidence.
- Workbench exports and aggregated support datasets do not by themselves establish statistical significance, candidate quality, causal benefit or generalization.
- `benchmarks/results/**` remains a separately governed evidence area.

## Compatibility and distribution

- Python 3.10 and 3.12 are covered by repository CI for the package.
- Windows, macOS and Linux receive standalone build/self-test coverage.
- The 0.5.1 standalone contract targets Windows amd64, Linux x86_64 and macOS Apple Silicon arm64. Intel/universal macOS support is not implied.
- Frozen bundles must pass their packaged self-test before upload.
- Model weights are not bundled. Model acquisition, provider availability and credentials remain separate dependencies.
- The browser UI uses Gradio 6 through the `[workbench]` extra.
- Workspace schema migration remains conservative; back up valuable prerelease workspaces before upgrades.

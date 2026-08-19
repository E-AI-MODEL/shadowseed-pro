# Workbench 0.5 limitations

Shadowseed Workbench 0.5.0 is a local mass-tester product preview for single-user use. It is not a production service, an authorization boundary for multiple users, or a scientific evidence generator by itself.

## Security and deployment

- The supported native and standalone server binds to loopback by default.
- There is no built-in login, tenant separation, hostile-network TLS/CSRF boundary, abuse protection, or multi-user access-control layer.
- Any remote-binding option is for explicitly controlled environments that provide their own network and access controls. Do not expose this preview directly to an untrusted network.
- The Docker image listens on `0.0.0.0` inside the container so it can be reached through a port mapping. The documented mapping publishes the port on host loopback only.
- Platform-vendor signing/notarization is separate from checksum/provenance verification and is not implied by the standalone build contract.

## Data handling

- Session prompts, answers, seeds and audit data are stored locally in the tester workspace.
- Full reports are content-bearing exports and must be treated accordingly.
- Support bundles are intentionally content-minimized but may still reveal backend/model choice, platform metadata and structural session counts.
- Redaction is defense in depth, not permission to paste credentials into a conversation. Testers should avoid unnecessary secrets and personal data.
- Hosted inference or embeddings send the relevant content to the selected external provider after the Workbench's explicit provider confirmation.
- Requesting **Compare this message with SSL off** causes an additional model generation. With a hosted model this means an additional hosted request using the same user message and pre-turn visible history, but without surfaced SSL seeds.

## Runtime authority

- New ordinary sessions use the canonical `live` runtime with the `evidence_backed` Gate policy.
- The Workbench has no direct weight, status, promotion or contradiction-state editor.
- Tester feedback is `record_only` by default.
- Live sessions provide a separate verified-support action. It submits an operator-attested, provenance-bearing signal to the existing Validation Gate; it cannot directly choose a Gate decision or final weight.
- The operator or host application is the trust anchor for that attestation. The Workbench validates required fields and provenance shape, not source truth.
- Reusing the same underlying external `source_ref` through another signal channel does not create additional authority credit.
- Seed authority remains governed by the existing Validation Gate and point-of-use checks.
- A promoted seed is only eligible for consideration; promotion does not force influence.

## Comparison and evaluation limits

- A live tester may request a same-message SSL-off control. The control is generated automatically from the same model configuration and pre-turn visible history and does not enter candidate detection, recurrence, the Gate, seed state, or later conversation history.
- The actual live turn is the only state-changing turn.
- A textual difference is not automatically evidence of an SSL effect. Attribute a difference to SSL only when an authorized seed actually surfaced on the live turn; ordinary model-generation variance remains a possible explanation otherwise.
- Historical `evaluation` sessions, authored baseline fixtures, scenario JSON and blind benchmark flows remain Advanced/research tools.
- The Workbench does not infer statistical significance or scientific validity from an individual comparison.
- Fixture runs are deterministic product smokes, not model-effect evidence.
- Workbench tests and exports must not be represented as new benchmark evidence.
- `benchmarks/results/**` remains a separately governed evidence area.

## Compatibility and distribution

- Python 3.10 and 3.12 are covered by the repository CI for the Python package preview.
- Windows, macOS and Linux receive clean-install Workbench portability checks.
- The 0.5.0 standalone build contract targets Windows amd64, Linux x86_64 and macOS Apple Silicon arm64. Intel/universal macOS support is not implied.
- Frozen standalone bundles must pass their packaged self-test before upload.
- Model weights are not bundled. Model acquisition, provider availability and provider credentials remain separate dependencies.
- The browser UI uses the Gradio 6 API family through the `[workbench]` extra.
- Workspace schema migration support remains deliberately conservative; create a backup before using a newer prerelease against valuable tester data.

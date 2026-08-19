# Workbench privacy guidance

Shadowseed Workbench 0.5.0 is local-first, but local-first does not mean that all data is automatically non-sensitive. Testers remain responsible for the content they enter and for exports they choose to share.

## Local workspace

The Workbench stores sessions and audit data in the local SQLite workspace. That can include prompts, generated answers, automatically generated comparison controls, seed text, model/backend metadata, Gate and influence records, verified-support source references and notes, and tester feedback.

- Do not paste passwords, API keys, access tokens, private keys, or other credentials into a tester conversation.
- Do not place credentials or unnecessary personal data in evidence source references or verification notes.
- Do not use real personal or confidential data when synthetic or redacted test material is sufficient.
- Protect workspace backups like the source workspace; a backup is not a privacy-minimized support artifact.
- Use `shadowseed workspace delete --yes` only when you intentionally want to remove the complete local workspace.

## Backend transmission

The fixture backend is deterministic and local. Ollama is intended for a local Ollama service. Hugging Face Transformers inference is local after model files are available, although obtaining a model can contact Hugging Face. Sentence Transformers may likewise obtain its embedding model before local use.

The OpenAI model and embedding backends are hosted. Prompts, generated context, seed text, or query text are sent to that provider only after the Workbench requires explicit hosted-provider confirmation. Provider-side handling is outside the local SQLite boundary and must be evaluated under the provider/account terms used by the tester.

### Paired SSL-off comparison

**Compare this message with SSL off** performs an additional model generation from the same current user message and pre-turn visible conversation history. The control contains no surfaced SSL seeds and does not mutate SSL or later conversation state, but it is still a real model request.

- With fixture, Ollama, or local Transformers inference, that extra generation stays on the configured local inference path.
- With a hosted model, enabling comparison causes an additional hosted request carrying the same user message and pre-turn visible history.
- Comparison can therefore affect provider usage, latency and any provider-side data handling even though it is isolated from Shadowseed state.

Do not enable comparison for content you would not otherwise send to the configured model provider.

HTTPX honors standard proxy environment variables. The Workbench extra includes HTTPX's optional SOCKS transport so an existing `ALL_PROXY`, `HTTP_PROXY`, or `HTTPS_PROXY` configuration can be used rather than silently disabled. The Workbench does not create or select a proxy itself.

Credentials must be supplied through supported environment or local credential mechanisms. The Workbench does not accept backend credentials as persisted workspace configuration.

## Full reports

A full Workbench report is an intentional content-bearing export. It can contain session identity, prompts, visible answers, stored comparison controls, seed snapshots, Gate/influence records and free-text tester feedback.

Treat a full report as sensitive unless you have inspected the session and know that its contents are safe to share.

## Support bundles

A support bundle is intentionally minimized for troubleshooting. It omits:

- the free session title;
- the direct session identifier;
- prompts and generated answers;
- comparison answer text;
- seed text;
- free-text tester notes.

It can still contain backend/model choice, profile, platform/environment metadata, sanitized configuration and structural counts. The pseudonymous support identifier is stable for a given session identifier; it is useful for correlating repeated support bundles but must not be described as formal anonymization.

## Redaction and verification

Exported configuration is recursively checked for secret-like field names and local absolute paths. This is defense in depth, not a promise that arbitrary free text is safe. Full reports deliberately preserve session content.

Every Workbench export includes a manifest with SHA-256 hashes and declared sizes. `shadowseed verify-workbench-export` checks integrity and defensive ZIP constraints before an export should be trusted as a Workbench-generated bundle.

## Sharing checklist

Before sharing an artifact:

1. Prefer a support bundle for troubleshooting.
2. Use a full report only when conversation/seed/comparison content is actually needed.
3. Verify the ZIP with `shadowseed verify-workbench-export`.
4. Inspect the intended artifact when the data is sensitive.
5. Share through an appropriate channel for the data classification involved.

The 0.5.0 preview has no automatic cloud workspace upload. Hosted inference and embeddings remain explicit provider interactions rather than workspace synchronization.

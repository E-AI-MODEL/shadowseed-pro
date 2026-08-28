# Workbench privacy guidance

Shadowseed Workbench 0.7.0 is local-first, but local-first does not make all entered or exported data non-sensitive. Version 0.7.0 is the current production-local assurance candidate, not yet a completed `production-ready/local` release. Testers and study owners remain responsible for the content they enter and for artifacts they choose to share.

## Local workspace

The local SQLite workspace can contain prompts, generated answers, SSL-off comparison controls, seed text, model/backend metadata, Gate and influence records, verified-support references and notes, and tester feedback.

- Do not paste passwords, API keys, access tokens, private keys or other credentials into conversations.
- Do not put credentials or unnecessary personal data in evidence references or notes.
- Prefer synthetic or redacted material when real personal/confidential data is unnecessary.
- Treat workspace backups like the source workspace; they are not privacy-minimized artifacts.
- `shadowseed workspace delete --yes` intentionally removes the complete local workspace.

## Backend transmission

The fixture backend is deterministic and local. Ollama is intended for a local Ollama service. Hugging Face Transformers and Sentence Transformers run locally after model material is available, although acquiring that material can contact Hugging Face.

OpenAI model/embedding backends are hosted and require explicit provider confirmation/configuration. Provider-side handling is outside the local SQLite boundary and must be evaluated under the account/provider terms used by the tester.

**Compare this message with SSL off** performs an additional generation from the same current message and pre-turn visible history. With a hosted model this is an additional hosted request. The control does not mutate Shadowseed state, but that isolation does not remove provider-side data handling or usage.

## Full reports

A full Workbench report is intentionally content-bearing. It can include session identity, prompts, visible answers, stored controls, seed snapshots, Gate/influence records and free-text tester feedback. Treat it as sensitive unless the session has been inspected and is safe to share.

## Privacy-minimized support bundles

A support bundle omits:

- the free session title and direct session identifier;
- prompts and generated answers;
- comparison answer text;
- seed text;
- free-text tester notes.

It can still contain backend/model choice, profile, platform/environment metadata, sanitized configuration and structural counts. Its `support::...` identifier is a stable pseudonym derived from the local session identifier. It is useful for duplicate/correlation checks but is **not formal anonymization**.

## Multi-tester support collection

Researchers can aggregate verified support bundles with:

```bash
python scripts/aggregate_support_bundles.py \
  tester-a.zip tester-b.zip \
  --collection-id study-01 \
  --output results/study-01-support-dataset.json
```

The collector:

- runs the canonical export verifier on every input;
- accepts privacy-minimized support bundles only, not full reports;
- rejects duplicate pseudonymous support-session identities;
- records each input bundle SHA-256;
- keeps only the already-minimized `environment.json`, `config.json` and `support.json` payloads plus collection metadata.

The resulting dataset is therefore suitable for **structured collection**, not automatically anonymous or scientifically conclusive. A study owner remains responsible for consent where applicable, data minimization, lawful/ethical handling, retention and deletion policy, access control, protocol design, and interpretation.

## Evidence-efficacy bundles

Evidence-efficacy bundles, introduced with the 0.6.0 research harness and retained in 0.7.0, are **not privacy-minimized support bundles**. They are research artifacts and can contain:

- full study questions;
- baseline and SSL answers;
- selected/surfaced seed identities and research metadata;
- Gate and point-of-use records;
- evidence source references and reasons;
- model/environment/provenance details;
- blinded review packets containing answer text.

Do not aggregate or publish these bundles under the support-bundle privacy assumptions. Use synthetic/public study material where possible, define access/retention rules before collecting sensitive data, and inspect every bundle before publication.

A `source_ref` should be stable enough for evidence identity and deduplication but should not contain credentials, unnecessary personal identifiers, secret URLs or confidential free text. Prefer study-local identifiers such as `study://source/001` with separately governed source documentation.

The efficacy runner validates evidence signal shape and source identity. It does not verify that the external source is factually true. The human/operator attestation behind `verified=True` remains an explicit research trust decision and should be documented outside the bundle when needed.

## Redaction and verification

Exported Workbench configuration is recursively checked for secret-like field names and local absolute paths. This is defense in depth, not a guarantee that arbitrary user-supplied strings are harmless. Full reports and evidence-efficacy bundles deliberately preserve research content.

Every Workbench export includes a SHA-256 manifest. `shadowseed verify-workbench-export` checks integrity and defensive ZIP constraints before an artifact should be trusted as Workbench-generated data. Support aggregation verifies again before collection.

Evidence-efficacy bundles use their own hash manifest and can be verified after moving them:

```bash
python -m shadowseed.benchmark.evidence_efficacy verify <bundle-directory>
```

Integrity verification proves the recorded files match the manifest. It does not make the content anonymous, truthful or scientifically valid.

## Sharing checklist

1. Prefer a support bundle when conversation content is unnecessary.
2. Use a full report only when content-bearing analysis is needed and appropriate.
3. Treat evidence-efficacy bundles as content-bearing research data, not support bundles.
4. Verify the relevant artifact before sharing or aggregating it.
5. Inspect sensitive artifacts manually.
6. Give a multi-tester collection or efficacy study a declared identifier and protocol.
7. Do not describe pseudonymous support data as anonymous unless a separate privacy assessment justifies that claim.
8. Keep evidence source references free of credentials and unnecessary personal/confidential data.

Version 0.7.0 has no automatic cloud workspace upload. Hosted model/embedding calls remain explicit provider interactions rather than workspace synchronization.

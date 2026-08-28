# Workbench tester guidelines

Shadowseed Workbench 0.7.0 is a local research preview and production-local assurance candidate for using Shadow Seed Learning in an ordinary chat. It is not yet a completed `production-ready/local` release. A normal tester should not need to understand the research harness, author a baseline answer, prepare benchmark JSON, install Git, or install a system Python runtime when a verified standalone release is available.

Repository states/releases containing `LICENSE` are available under PolyForm Noncommercial License 1.0.0. Read the terms before copying, modifying or redistributing the software. Commercial use requires separate permission.

## What to test

Useful tester questions include:

- Can a new tester download, open and start the Workbench without Python setup?
- Is it clear which provider and model are active?
- Can local Ollama models be discovered and selected without copying model IDs by hand?
- Can a chat be closed and resumed without losing visible turns or audit state?
- Does the product behave like a normal chatbot before exposing seed internals?
- Is **Compare this message with SSL off** understandable without implying one answer is automatically better?
- Is it clear when a comparison difference can actually be attributed to SSL?
- Are seed status and plain-language explanations understandable in the Shadow view?
- Is record-only feedback easy to enter and clearly non-authorizing?
- Are errors actionable when a backend, model, credential, workspace or export is unavailable?
- Can a privacy-minimized support bundle be produced without conversation content?

## Start with the fixture

Use the deterministic fixture first for installation, UI, export and workflow testing. A fixture run proves product mechanics only. It is not evidence that Shadowseed improves a real model.

Move to Ollama, Hugging Face Transformers or OpenAI only when a test requires a real backend. The export records model/backend configuration automatically; still describe the intended test protocol when contributing data.

## Normal chat and paired comparison

New ordinary chats use the canonical `live` runtime with the `evidence_backed` Gate policy. The visible answer is the answer stored in conversation history.

When **Compare this message with SSL off** is enabled, the Workbench generates a same-model no-SSL control from the same pre-turn visible history. The control is comparison data only. It does not enter candidate detection, recurrence, the Validation Gate or later conversation history. The real live turn remains the only state-changing turn.

A textual difference is not automatically an SSL effect. Attribute a difference to SSL only when an authorized seed actually surfaced on the real live turn. When no seed surfaced, normal generation variance remains a possible explanation.

Historical `evaluation` sessions, authored baseline fixtures, scenario JSON and blind benchmark workflows remain research/regression tools rather than prerequisites for ordinary product testing.

## Feedback and authority discipline

Workbench feedback is `record_only` by default. A tester rating or note is an observation, not evidence for a seed and not permission to change seed weight, status or promotion.

The live verified-support action is separate from ordinary feedback. Use it only for independently checked support, give the source a stable reference, and do not treat model output or recurrence as verification. The operator attestation is part of the trust boundary and is recorded in the Gate ledger.

The Workbench is not an authority editor. Testers cannot directly set seed weight, promotion status, contradiction state or Gate decisions. Unexpected UI behavior that appears to bypass those boundaries is a high-priority defect.

## Contributing tester data

For routine multi-tester collection, prefer the privacy-minimized support bundle. It omits conversation/seed free text but preserves pseudonymous session identity, model/backend/configuration metadata and structural counts.

A study coordinator can combine submitted support ZIPs with:

```bash
python scripts/aggregate_support_bundles.py \
  tester-a.zip tester-b.zip \
  --collection-id study-01 \
  --output results/study-01-support-dataset.json
```

The collection command re-verifies every ZIP, rejects content-bearing full reports, rejects duplicate pseudonymous session identities and records source-bundle hashes. Testers should not manually edit support ZIPs before submission because integrity verification will fail.

When contributing to an actual study, use the collection/study identifier and instructions provided by the study owner. The repository supplies technical collection tooling; consent, inclusion criteria, study protocol, retention, access control and interpretation remain study-level responsibilities.

## Evidence-efficacy studies are not routine tester exports

The evidence-efficacy runner, introduced in 0.6.0 and retained in 0.7.0, is a research harness, not an automatic mode for ordinary tester sessions. Its bundles can contain questions, baseline/SSL answers, seed metadata, Gate decisions and external source references. Do not submit them through the privacy-minimized support-bundle collection path.

A valid evidence-efficacy study must be preregistered before interpreting results. A human/researcher must attest external support independently of model output. A blind A/B item is created only when that support passes the normal `evidence_backed` Gate and the authorized seed later surfaces.

If a candidate selector does not match, the Gate blocks, the point-of-use check denies influence, or no later question makes the seed relevant, that is a study result. Do not alter the candidate or Gate after seeing the outcome merely to obtain an A/B pair.

## Reporting an issue

Include:

- what you were trying to do;
- provider/model and relevant Workbench settings;
- the smallest reproducible sequence of actions;
- expected versus observed behavior;
- whether an SSL-off control was requested and whether a seed actually surfaced;
- a verified support bundle when structural context is enough;
- a full report only when conversation or seed contents are necessary and safe to share.

## Data hygiene

- Do not enter credentials into prompts or notes.
- Prefer synthetic or redacted data for ordinary testing.
- Read `privacy.md` before sharing or collecting exports.
- Prefer support bundles for routine troubleshooting and observational collection.
- Treat evidence-efficacy bundles as content-bearing research data.
- Keep valuable workspaces backed up before prerelease upgrades.

## Evidence discipline

Ordinary Workbench sessions, UI tests, paired controls, support datasets and CI smokes are not automatically benchmark evidence. Do not copy incidental tester output into `benchmarks/results/**`. Evidence snapshots should be updated only through an intentional benchmark/evaluation run or a declared study protocol with provenance and review.

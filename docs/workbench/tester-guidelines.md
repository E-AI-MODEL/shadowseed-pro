# Workbench tester guidelines

Shadowseed Workbench 0.5.0 is a local mass-tester preview for using Shadow Seed Learning in an ordinary chat. A normal tester should not need to understand the research harness, author a baseline answer, prepare benchmark JSON, install Git, or install a system Python runtime.

## What to test

Useful tester questions include:

- Can a new tester download, open, and start the Workbench without Python setup?
- Is it clear which provider and model are active?
- Can local Ollama models be discovered and selected without copying model IDs by hand?
- Can a chat be closed and resumed without losing visible turns or audit state?
- Does the product behave like a normal chatbot before exposing seed internals?
- Is **Compare this message with SSL off** understandable without implying that one answer is automatically better?
- Is it clear when a comparison difference can actually be attributed to SSL?
- Are seed status and plain-language explanations understandable when the tester opens the Shadow view?
- Is record-only feedback easy to enter and clearly non-authorizing?
- Are errors actionable when a backend, model, credential, workspace, or export is unavailable?
- Can a support bundle be produced without exposing conversation content?

## Start with the fixture

Use the deterministic fixture first for installation, UI, export, and workflow testing. A fixture run proves product mechanics only. It is not evidence that Shadowseed improves a real model.

Move to Ollama, Hugging Face Transformers, or OpenAI only when the test requires a real backend. Record the backend and model used when reporting behavior.

## Normal chat and paired comparison

New ordinary chats use the canonical `live` runtime with the `evidence_backed` Gate policy. The visible answer is the answer stored in conversation history.

When **Compare this message with SSL off** is enabled, the Workbench automatically generates a same-model no-SSL control from the same pre-turn visible history. The control is comparison data only. It must not enter candidate detection, recurrence, the Validation Gate, or later conversation history. The real live turn remains the only state-changing turn.

A textual difference is not automatically an SSL effect. Attribute a difference to SSL only when an authorized seed actually surfaced on the real live turn. When no seed surfaced, normal generation variance remains a possible explanation.

Historical `evaluation` sessions, authored baseline fixtures, scenario JSON, and blind benchmark workflows remain under **Advanced / research**. They are research and regression tools, not prerequisites for ordinary product testing.

## Feedback discipline

Workbench feedback is `record_only` by default. A tester rating or note is an observation, not evidence for a seed and not permission to change seed weight, status, or promotion.

The live verified-support action is separate from ordinary feedback. Use it only for independently checked support, give the source a stable reference, and do not treat model output or recurrence as verification. The operator attestation is part of the trust boundary and is recorded in the Gate ledger.

When reporting an issue, include:

- what you were trying to do;
- provider/model and relevant Workbench settings;
- the smallest reproducible sequence of actions;
- expected versus observed behavior;
- whether a paired SSL-off control was requested and whether a seed actually surfaced;
- a verified support bundle when it contains enough context;
- a full report only when conversation or seed contents are necessary and safe to share.

## Data hygiene

- Do not enter credentials into prompts or notes.
- Prefer synthetic or redacted data for ordinary testing.
- Read `privacy.md` before sharing full reports.
- Prefer support bundles for routine troubleshooting.
- Keep valuable workspaces backed up before prerelease upgrades.

## Authority boundary

The Workbench is not an authority editor. Testers cannot directly set seed weight, promotion status, contradiction state, or Gate decisions. Verified support is an input to the Gate, not a direct state edit. Unexpected UI behavior that appears to bypass those runtime boundaries is a high-priority defect.

## Evidence discipline

Ordinary Workbench sessions, UI tests, paired controls, support bundles, and CI smokes are not new benchmark evidence. Do not copy incidental tester output into `benchmarks/results/**`. Evidence snapshots should only be updated through an intentional benchmark or evaluation run with its own provenance and review.

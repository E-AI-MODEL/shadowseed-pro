# Workbench tester guidelines

Shadowseed Workbench 0.4.0 is intended to make the runtime practical to test
without requiring testers to understand or modify the research internals.

## What to test

Useful tester questions include:

- Can a new tester install and start the Workbench without Python coding?
- Is it clear which backend/profile is active?
- Can a session be closed and resumed without losing turns or audit state?
- Are seed status and plain-language explanations understandable?
- Does the baseline-vs-Shadowseed comparison make sense without implying an
  automatic winner?
- Is record-only feedback easy to enter and clearly non-authorizing?
- Are errors actionable when a backend, model, credential, workspace, or export
  is unavailable?
- Can a support bundle be produced without exposing conversation content?

## Start with the fixture

Use the deterministic fixture first for installation, UI and workflow testing.
A fixture run proves product mechanics only. It is not evidence that Shadowseed
improves a real model.

Move to Ollama, Hugging Face Transformers or OpenAI only when the test requires
a real backend. Record the backend and model used when reporting behavior.

## Feedback discipline

Workbench feedback is `record_only` by default. A tester rating or note is an
observation, not new evidence for a seed and not permission to change seed
weight/status.

When reporting an issue, include:

- what you were trying to do;
- backend/model and Workbench profile;
- the smallest reproducible sequence of actions;
- expected versus observed behavior;
- a verified support bundle when it contains enough context;
- a full report only when the conversation or seed contents are necessary and
  safe to share.

## Blind comparison

Blind A/B mode hides which candidate is the clean baseline and which is the
Shadowseed-visible answer until reveal. Judge the content before revealing the
mapping when possible.

Do not interpret one preference as a scientific result. Repeated tester
preferences can motivate a later controlled evaluation, but the Workbench does
not calculate statistical significance or convert preferences into benchmark
evidence.

## Data hygiene

- Do not enter credentials into prompts or notes.
- Prefer synthetic or redacted data for ordinary testing.
- Read `privacy.md` before sharing full reports.
- Prefer support bundles for routine troubleshooting.
- Keep valuable workspaces backed up before prerelease upgrades.

## Authority boundary

The Workbench is not an authority editor. Testers should never need to directly
set seed weight, promotion status, contradiction state, or Gate decisions.
Unexpected UI behavior that appears to bypass those existing runtime boundaries
should be treated as a high-priority defect.

## Evidence discipline

Ordinary Workbench sessions, UI tests, support bundles, and CI smokes are not
new benchmark evidence. Do not copy incidental test output into
`benchmarks/results/**`. Evidence snapshots should only be updated through an
intentional benchmark/evaluation run with its own provenance and review.

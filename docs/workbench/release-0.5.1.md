# Shadowseed Workbench 0.5.1 Mass Tester Preview

Version 0.5.1 is the release candidate that consolidates Shadowseed Pro as a scientifically bounded, low-friction local tester with a structured privacy-minimized data-collection path. Public release availability is a separate publication fact: treat `v0.5.1` as published only when the immutable tag and verified release assets are actually present.

## What this release is for

The repository has three explicit goals:

1. **Scientific inspection.** The runtime, tests, manuscript, benchmark evidence and claim boundaries remain separately auditable and provenance-aware.
2. **Low-friction testing.** Verified standalone archives let ordinary testers open a local chat application without Git, system Python, `pip`, benchmark JSON or an authored baseline answer.
3. **Structured data collection.** Privacy-minimized support bundles can be verified and combined into schema `shadowseed-support-dataset-v1` without importing conversation or seed free text.

## Tester path

```text
download -> extract/open -> choose model -> create chat -> chat with SSL -> optionally compare one message with SSL off
```

The ordinary product uses the canonical `live` runtime and the `evidence_backed` Gate policy. Candidates start weightless. Recurrence remains observation rather than external evidence under this product policy. Gate authority and point-of-use authorization remain runtime-owned, contradictions remain blocking, and ordinary tester feedback remains record-only.

`Compare this message with SSL off` creates a same-model control from the same pre-turn visible history. The control does not enter detection, recurrence, the Validation Gate or later conversation history. A textual difference is not labelled an SSL effect unless an authorized seed actually surfaced on the live turn.

## Data collection

The Workbench continues to export:

- a full content-bearing auditable report;
- a privacy-minimized support bundle that omits direct session identity, prompts, answers, comparison text, seed text and free-text tester notes.

Version 0.5.1 adds the verified collection command:

```bash
python scripts/aggregate_support_bundles.py \
  tester-a.zip tester-b.zip tester-c.zip \
  --collection-id pilot-2026-08 \
  --output results/pilot-2026-08-support-dataset.json
```

The collector verifies every input bundle using the canonical Workbench export verifier, accepts support bundles only, rejects duplicate support-session identities, records input bundle SHA-256 values, and emits one versioned JSON dataset. This is research instrumentation, not automatic evidence of model benefit. Study claims still require a declared protocol, controls, analysis plan and review.

## Code cleanup

The unused legacy `src/shadowseed/paper_pipeline.py` paper-ingest path was removed. It had no supported product or CLI entrypoint and duplicated obsolete claim/SSOT semantics inside the shipping runtime. The now-unused PyMuPDF `[paper]` package extra was removed as well. Historical benchmark evidence, compatibility facades and archived provenance were intentionally retained because they support replay and scientific traceability rather than constituting duplicate canonical runtime implementations.

## Paper boundary

The checked-in paper remains a reviewed methods/systems snapshot with its own explicit source version and implementation commit. Version 0.5.1 does not silently rewrite the LaTeX/PDF pair merely to match a software badge. The paper and repository remain aligned on the authority model and claim boundary; a future manuscript revision must rebuild and review source and PDF together.

## Standalone verification

Every platform build is produced by the same `Standalone Workbench` workflow from one exact commit. Before upload, the frozen application must prove it can initialize an isolated workspace, build the chat-first UI, execute a live fixture turn, generate the SSL-off control, export and verify both report types, and import packaged runtime dependencies.

A published 0.5.1 prerelease is required to contain:

- three platform standalone archives and their manifests;
- `PROVENANCE.json` tying those bundles to the exact source SHA and workflow run;
- one Python wheel and one source distribution;
- `SHA256SUMS` covering the published files.

The release workflow checks `main == RELEASE_SHA` at preflight, immediately before publication, and immediately after release creation. If `main` moves during publication, the workflow deletes the stale release and tag and fails closed.

## Scientific and production boundary

0.5.1 is a **mass-tester research preview**, not a production certification. It does not establish general answer-quality improvement, reliable benefit from every seed, universal missing-information detection, semantic truth, hostile-network multi-user security, managed tenancy/secrets, complete retention/deletion operations, or high-impact deployment readiness.

Independent review of existing Qwen candidate-quality research and repository branch-protection administration remain separate follow-up work; they are not hidden prerequisites for the local tester release contract.

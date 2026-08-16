# Shadowseed Tester Workbench

The Workbench is a local-first tester interface for the existing Shadowseed
runtime. It is designed for practical testing and review, not as a scientific
statistics platform or a production multi-user service.

The implementation plan is maintained in
[`docs/plans/tester-workbench-0.4.md`](../plans/tester-workbench-0.4.md).
Before external testing, also read the
[privacy guidance](privacy.md), [tester guidelines](tester-guidelines.md), and
[preview limitations](limitations.md).

## Install and start

For the 0.4 tester preview:

```bash
python -m pip install "shadowseed[workbench]"
shadowseed doctor
shadowseed init
shadowseed workbench
```

The supported server binds to `127.0.0.1` by default. The preview has no
multi-user authentication layer. Do not expose it to an untrusted network.

The Workbench extra includes HTTPX's optional SOCKS transport. Environments
that already set `ALL_PROXY`, `HTTP_PROXY`, or `HTTPS_PROXY` can therefore
start Gradio without disabling those settings. Shadowseed does not configure a
proxy itself.

## Tester workflow

1. Run `shadowseed doctor` and resolve reported setup errors.
2. Run `shadowseed init` to create the local SQLite workspace.
3. Start `shadowseed workbench`.
4. Create or resume a session and choose a runtime mode, profile, model backend,
   and embedding backend.
5. In a live session, submit verified support only after checking an independent
   source and assigning it a stable source reference.
6. Inspect seed snapshots and their audit timeline when useful.
7. Record tester feedback. The default Workbench feedback action is
   `record_only`; it does not change seed authority.
8. Use Compare for side-by-side or blinded baseline-vs-Shadowseed review in an
   evaluation session.
9. Export a full report for deliberate session sharing, or a minimized support
   bundle for troubleshooting.
10. Back up the workspace with `shadowseed workspace backup`.

## Runtime modes and evidence

`evaluation` remains the Workbench form default. It preserves the isolated
baseline and optional SSL-assisted answer used by the Compare tab.

`live` performs one visible generation and stores that answer in conversation
history. For non-fixture live sessions, choose Sentence Transformers or OpenAI
embeddings. Lexical hash embeddings are available only behind the explicit toy
override. Fixture live sessions may use lexical embeddings for deterministic UI
and persistence tests.

Live recurrence alone does not grant steering authority. The verified-support
action creates a provenance-bearing human-feedback signal and submits it to the
existing `evidence_backed` Validation Gate. The tester must confirm that the
support was checked outside the model output. The Workbench validates the
attestation and source-reference shape, not whether the source is true. Reusing
the same source reference is audited but does not add authority again.

Runtime mode and profile are separate settings. Profiles tune surfacing; they do
not switch the conversation loop.

Imported scenarios accept `runtime_mode`, `embedding_backend`,
`embedding_model`, and `allow_toy_embedder` alongside the existing session
fields. Missing fields retain the backward-compatible evaluation, lexical, and
no-override defaults. Resume rejects a scenario whose runtime configuration no
longer matches its persisted session.

## Backends and privacy

- **fixture**: deterministic local onboarding and smoke-test backend.
- **Ollama**: prompt execution through the configured local Ollama server.
- **Hugging Face Transformers**: local inference after model material is
  available; an initial model download may contact Hugging Face.
- **OpenAI**: hosted inference. Prompts and generated context are transmitted to
  the provider only after the Workbench's explicit hosted-provider confirmation.

Embedding choices are lexical, Sentence Transformers, and OpenAI. OpenAI
embeddings also send seed and query text to the hosted provider and require the
same explicit confirmation. Sentence Transformers runs locally after model
material is available; obtaining that material may contact Hugging Face.

Credentials are not accepted as persistent Workbench configuration. Use the
backend's supported environment-variable or local credential mechanism.

Session messages are stored locally, so testers should not paste credentials or
unnecessary sensitive data into conversations. See [privacy.md](privacy.md) for
the full sharing and data-handling guidance.

## Exports

A full report is intentionally content-bearing and may include the session
name, prompts, answers, seed snapshots, Gate events, influence events and tester
feedback. Treat it as sensitive tester material.

```bash
shadowseed export-workbench-report SESSION_ID --output report.zip
shadowseed verify-workbench-export report.zip
```

A support bundle is content-minimized. It omits the free session title, direct
session id, prompts, answers, seed text and tester notes. It contains structural
counts, backend/profile metadata, sanitized configuration and environment
metadata.

```bash
shadowseed export-support-bundle SESSION_ID --output support.zip
shadowseed verify-workbench-export support.zip
```

Every export contains a manifest with SHA-256 hashes and sizes. The verifier
also rejects missing or extra files, duplicate filenames, path traversal,
symlink entries, oversized content, unsafe compression ratios, and external or
embedded resources in the standalone HTML report.

## Workspace backup and restore

```bash
shadowseed workspace info
shadowseed workspace backup --output shadowseed-workspace.sqlite
shadowseed workspace restore shadowseed-workspace.sqlite
```

Restore replaces the local workspace database after schema validation. Keep a
separate backup before experimenting with migration or prerelease builds.

## Docker

The repository includes `Dockerfile.workbench` as an optional tester packaging
path. Build it from the repository root:

```bash
docker build -f Dockerfile.workbench -t shadowseed-workbench:0.4.1 .
docker run --rm \
  -p 127.0.0.1:7860:7860 \
  -v shadowseed-data:/data \
  shadowseed-workbench:0.4.1
```

The container listens on `0.0.0.0` internally so the host can reach it, but the
recommended port mapping publishes it only on host loopback. Do not change that
mapping on an untrusted network.

## What the preview does not claim

- no production-readiness claim;
- no multi-tenant or account isolation;
- no automatic scientific-validity claim for tester observations;
- no direct weight, status or promotion editor;
- no UI-owned Gate or lifecycle policy;
- no telemetry or automatic cloud workspace upload.

Scientific and authority constraints remain in the existing runtime. The
Workbench presents, persists and compares behavior; it is not a second policy
engine.

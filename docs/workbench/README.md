# Shadowseed Tester Workbench

The Workbench is the local-first chat surface for testing Shadow Seed Learning in an ordinary LLM conversation. A normal tester does not prepare a benchmark suite, write JSON, author a baseline answer, install Git, or install a system Python runtime when a verified standalone release is available.

The ordinary product path is:

```text
download -> extract/open -> choose model -> create chat -> chat with SSL -> optionally compare one message with SSL off
```

Research scenarios, historical evaluation mode, raw diagnostics and benchmark-oriented tools remain under **Advanced / research**. They are not prerequisites for ordinary testing.

The Workbench remains a local single-user product preview. It is not a hostile-network multi-user service. Before sharing tester data, read the [privacy guidance](privacy.md), [tester guidelines](tester-guidelines.md), and [preview limitations](limitations.md).

## Fastest start: standalone tester

Source version 0.5.0 contains the fail-closed build and release automation for self-contained Workbench archives for Windows, macOS and Linux. Treat the standalone download route as available only when a verified `v0.5.0` GitHub release and its assets are actually present. Source version and public release availability are separate facts.

When the verified release is present:

1. Download the archive matching your operating system and architecture.
2. Download `SHA256SUMS` from the same release and verify the archive hash when practical.
3. Extract the archive.
4. Open **Shadowseed** (`Shadowseed.exe` on Windows, `Shadowseed.app` on macOS, or the `Shadowseed` executable inside the Linux folder).
5. The app creates or opens the local `~/.shadowseed` workspace and opens the chat UI in your browser on loopback only.
6. Choose a model, create a chat and start talking.

No Git checkout, `pip install`, system Python, fixture file or authored baseline is required for the verified standalone route. If no verified release is present yet, use the developer/source installation route below rather than assuming unpublished assets exist.

### What the standalone bundle does not bundle

Model weights are intentionally separate from the application. This avoids silently shipping third-party model material and keeps model provenance explicit.

- **fixture** works offline immediately and demonstrates mechanics only.
- **Ollama** discovers models already installed in the local Ollama server. If none exist, install/pull a model through Ollama first.
- **Hugging Face Transformers** may download the selected model on first use.
- **Sentence Transformers** may download its semantic embedding model on first use.
- **OpenAI** requires an explicitly configured provider credential and user confirmation before hosted content is sent.

Model acquisition time is therefore measured separately from Shadowseed setup time.

### Release integrity and provenance

A valid 0.5.0 standalone prerelease is required to contain:

- one standalone archive per build platform;
- one machine-readable manifest per standalone archive;
- `PROVENANCE.json` tying those manifests to the exact source commit and standalone workflow run;
- `SHA256SUMS` covering all downloadable release files;
- the Python wheel and source distribution for developers.

Each frozen bundle executes its own packaged self-test before it is uploaded. That self-test proves the embedded runtime can build the chat UI, run a live fixture turn, automatically generate the paired SSL-off control, and create/verify both report and support exports.

The 0.5.0 release contract uses checksums and build provenance. Platform vendor signing/notarization is a separate hardening step when signing credentials are available; do not describe an asset as notarized or Authenticode-signed unless the published asset actually carries that signature.

## Normal tester workflow

1. Open Shadowseed.
2. In **Chat**, choose a provider and model. Local Ollama models can be detected automatically.
3. Create a chat. New ordinary chats use the canonical `live` runtime and its `evidence_backed` Gate policy.
4. Chat normally. The visible answer is the answer stored in conversation history.
5. When useful, enable **Compare this message with SSL off** before sending one message.
6. Review the paired outputs. A difference is an SSL effect only when an authorized Shadow Seed actually surfaced on that turn.
7. Open **Shadow** only when you want to inspect seed state, contradictions or independently verified evidence.
8. Record feedback or export a report when useful.

No authored baseline is required. No benchmark suite is required. There is no direct seed-weight or promotion editor.

## Chat with SSL

A new ordinary session defaults to:

```text
runtime_mode = live
Gate policy = evidence_backed
```

The detector may propose atomic epistemic candidates after a visible answer. New candidates start weightless. Recurrence is observable but does not become external evidence and cannot raise authority by itself under the live default policy.

Only a seed with current Gate authority that passes the point-of-use contract may influence a later answer. Contradictions remain blocking according to the canonical runtime contract. The Workbench presents this runtime; it does not implement a second Gate.

### Model and embedding defaults

- **fixture** uses lexical embeddings for deterministic offline mechanics testing. It is not a high-end model.
- **Ollama**, **Hugging Face Transformers**, and **OpenAI** default to Sentence Transformers for semantic seed matching in the product form.
- lexical hashing with a real model is available only behind the explicit research/toy override.
- OpenAI inference or OpenAI embeddings require explicit external-provider confirmation in the UI.

Product live prompts ask the model to answer in the language of the current user question. Research benchmarks may pin a language as part of their protocol.

## Compare one message with SSL off

The comparison checkbox is a product control, not an authored baseline workflow.

For a live session the Workbench:

1. restores the current pre-turn visible conversation history;
2. asks the same model for a control answer with no surfaced Shadow Seeds;
3. keeps that control out of candidate detection, recurrence, the Gate and later conversation history;
4. runs the actual live SSL turn normally;
5. stores the control beside the real turn as comparison data.

The actual live turn is the only state-changing turn. Requesting a comparison must not create extra seeds, recurrence, trace, weight or Gate authority.

When no authorized seed surfaced, the comparison UI warns that textual differences may be ordinary generation variance and must not be attributed to SSL.

## Shadow inspection, evidence and feedback

The **Shadow** tab is secondary to the conversation. It exposes read-only seed state and audit history plus explicit contradiction and independently verified-support actions.

Verified support is available only in live sessions. The tester must confirm support was checked outside model output and provide a stable source reference. Reusing the same underlying source does not create extra authority by changing channel labels or repeating it.

Ordinary tester feedback remains `record_only`. It may describe perceived answer quality or visible SSL effect, but it does not change weight, promotion or Gate authority.

## Advanced / research

The **Advanced / research** tab contains scenario JSON, historical `evaluation` runtime controls, stored blind comparisons and benchmark-oriented diagnostics.

Historical scenarios or persisted sessions without runtime metadata retain their evaluation-compatible interpretation so old data is not silently reclassified. Historical baseline fixtures and result artifacts remain useful for regression and reproducibility. They are not product inputs.

## Backends and privacy

- **fixture**: deterministic offline mechanics backend.
- **Ollama**: inference through the configured local Ollama server; model discovery uses read-only `/api/tags` and sends no chat content.
- **Hugging Face Transformers**: local inference after model material is available; initial acquisition may contact Hugging Face.
- **OpenAI**: hosted inference after explicit confirmation. Prompts and generated context are transmitted to that provider.

OpenAI embeddings also send relevant text to the hosted provider. Sentence Transformers runs locally after its model material is available.

Session messages, answers, seeds and full report exports are content-bearing data. Do not paste credentials or unnecessary sensitive material into conversations.

## Exports and workspace safety

The UI provides full reports and privacy-minimized support bundles. Every export contains a manifest with SHA-256 hashes and sizes. The verifier rejects missing/extra files, duplicates, path traversal, symlink entries, oversized content, unsafe compression ratios and external/embedded resources in standalone HTML reports.

The workspace defaults to `~/.shadowseed`. Backup/restore remains available from the developer CLI and restore validates a candidate database before replacing the active workspace.

## Developer install

Developers and research users can install the Python package directly:

```bash
python -m pip install "shadowseed[workbench]"
shadowseed doctor
shadowseed workbench
```

The dedicated installed launcher is also available:

```bash
shadowseed-workbench
```

This is the development and research route, and it is also the source fallback while no verified standalone release is available. It is not the intended zero-setup mass-tester path once verified standalone assets are published.

## Docker

The repository still includes `Dockerfile.workbench` as an optional deployment/test packaging route:

```bash
docker build -f Dockerfile.workbench -t shadowseed-workbench:0.5.0 .
docker run --rm \
  -p 127.0.0.1:7860:7860 \
  -v shadowseed-data:/data \
  shadowseed-workbench:0.5.0
```

The container listens on `0.0.0.0` internally so the host can reach it, while the recommended port mapping publishes it only on host loopback. Do not expose this preview directly to an untrusted network.

## Claim boundary

The 0.5.0 chat-first standalone build contracts make Shadowseed packageable for local mass testing. A public downloadable release is a separate publication fact. Neither packaging nor publication by itself establishes full production readiness or general answer-quality benefit.

Still separate are hostile-network authentication/tenancy, TLS/CSRF controls, abuse/rate limits, managed secret storage, formal retention/deletion operations, platform vendor signing/notarization, operational monitoring, high-end-model efficacy studies and independent real-world review.

Scientific and authority constraints remain in the canonical runtime. Packaging does not grant seeds authority and does not turn research artifacts into product truth.

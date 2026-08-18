# Shadowseed Tester Workbench

The Workbench is the local-first chat surface for testing Shadow Seed Learning with an ordinary LLM conversation. The normal tester does not need to prepare a benchmark suite, write JSON, or author a baseline answer.

The intended product path is:

```text
open Workbench -> choose model -> create chat -> chat with SSL -> optionally compare one message with SSL off
```

Research scenarios, historical evaluation mode, raw diagnostics and benchmark-oriented tools remain available under **Advanced / research**. They are not prerequisites for ordinary testing.

The Workbench is still a local single-user preview. It is not a hostile-network multi-user production service. Before external testing, read the [privacy guidance](privacy.md), [tester guidelines](tester-guidelines.md), and [preview limitations](limitations.md).

## Install and start

For the current tester preview:

```bash
python -m pip install "shadowseed[workbench]"
shadowseed doctor
shadowseed init
shadowseed workbench
```

The `workbench` extra includes Gradio, the supported semantic/model stack and the OpenAI client. Provider credentials are still supplied through the provider's environment or local credential mechanism and are never persisted in the workspace.

The supported server binds to `127.0.0.1` by default. The preview has no multi-user authentication layer. Do not expose it to an untrusted network.

## Normal tester workflow

1. Start the Workbench.
2. In **Chat**, choose the model provider and exact model id.
3. Create a chat. New ordinary chats use the canonical `live` runtime and its `evidence_backed` Gate policy.
4. Chat normally. The visible answer is the answer stored in conversation history.
5. When useful, enable **Compare this message with SSL off** before sending one message.
6. Review the paired outputs. A difference is an SSL effect only when an authorized Shadow Seed actually surfaced on that turn.
7. Open **Shadow** only when you want to inspect seed state, contradictions or verified evidence.
8. Record feedback or export a report when useful.

No authored baseline is required. No benchmark suite is required. No seed or weight editing is required.

## Chat with SSL

A new ordinary session defaults to:

```text
runtime_mode = live
Gate policy = evidence_backed
```

The detector may propose atomic epistemic candidates after a visible answer. New candidates start weightless. Recurrence is observable but does not become external evidence and cannot raise authority by itself under the live default policy.

Only a seed that has current Gate authority and passes the point-of-use contract may influence a later answer. Contradictions remain blocking according to the existing runtime contract.

The Workbench does not own this authority logic. It presents the existing canonical runtime.

### Model and embedding defaults

- **fixture** uses lexical embeddings for deterministic offline mechanics testing. It is not a high-end model.
- **Ollama**, **Hugging Face Transformers**, and **OpenAI** default to Sentence Transformers for semantic seed matching in the product form.
- lexical hashing with a real model is available only behind the explicit research/toy override.
- OpenAI inference or OpenAI embeddings require explicit external-provider confirmation in the UI.

Product live prompts tell the model to answer in the language of the current user question. Research benchmarks may pin a language as part of their own protocol.

## Compare one message with SSL off

The comparison checkbox is a product control, not an authored baseline workflow.

For a live session the Workbench does this before the real turn:

1. restore the current pre-turn visible conversation history;
2. ask the same model for a control answer with no surfaced Shadow Seeds;
3. keep that control out of candidate detection, recurrence, the Gate and later conversation history;
4. run the actual live SSL turn normally;
5. store the control beside the real turn as comparison data.

The actual live turn is the only state-changing turn.

This means requesting a comparison must not create extra seeds, recurrence, trace, weight or Gate authority. Regression tests compare paired-control sessions against otherwise identical live sessions to enforce that boundary.

When no authorized seed surfaced, the comparison UI explicitly warns that any textual difference may be ordinary model-generation variance and must not be attributed to SSL.

## Shadow inspection and evidence

The **Shadow** tab is secondary to the conversation. It exposes read-only seed state and the audit timeline, plus two explicit authority-related actions:

- mark a seed contradicted;
- submit independently verified support.

Verified support is available only in live sessions. The tester must confirm that support was checked outside model output and provide a stable source reference. The Workbench validates the attestation and source-reference shape, not whether the source is true. The host/operator remains the trust anchor.

Reusing the same underlying evidence source is audited but does not create extra authority by changing evidence channel or repeating the same source.

There is no direct weight, status or promotion editor.

## Feedback

Ordinary tester feedback remains `record_only`.

Feedback can describe whether an answer or visible SSL effect seemed helpful, harmful, neutral or unclear, but recording feedback does not alter seed authority. Authority-bearing human evidence uses the separate verified-support action instead.

## Advanced / research

The **Advanced / research** tab contains tools that exist for reproducibility and experiments rather than normal product use:

- scenario JSON;
- the historical `evaluation` runtime;
- stored blinded or side-by-side comparisons;
- benchmark-oriented controls and diagnostics.

`evaluation` preserves the older isolated baseline/SSL research loop. Historical scenarios that omit `runtime_mode` keep the backward-compatible `evaluation` default. Existing persisted sessions without a recorded runtime mode are also interpreted as evaluation so old data is not silently reclassified.

Those compatibility rules do not change the default for a newly created ordinary chat, which is live.

Historical baseline fixtures and result artifacts remain useful for regression, replay and research. They are not the product's no-SSL input format.

## Backends and privacy

- **fixture**: deterministic offline demo and regression backend.
- **Ollama**: inference through the configured local Ollama server.
- **Hugging Face Transformers**: local inference after model material is available; initial model acquisition may contact Hugging Face.
- **OpenAI**: hosted inference. Prompts and generated context are transmitted to the provider only after explicit confirmation.

OpenAI embeddings also send relevant text to the hosted provider. Sentence Transformers runs locally after its model material is available.

Session messages, answers, seeds and full report exports are content-bearing data. Do not paste credentials or unnecessary sensitive information into conversations. See [privacy.md](privacy.md) for the full handling guidance.

## Exports

A full report may include the session name, prompts, answers, paired comparison data, seed snapshots, Gate events, influence events and tester feedback. Treat it as sensitive tester material.

```bash
shadowseed export-workbench-report SESSION_ID --output report.zip
shadowseed verify-workbench-export report.zip
```

A support bundle is content-minimized. It omits the free session title, direct session id, prompts, answers, seed text and tester notes. It contains structural counts, backend/profile metadata, sanitized configuration and environment metadata.

```bash
shadowseed export-support-bundle SESSION_ID --output support.zip
shadowseed verify-workbench-export support.zip
```

Every export contains a manifest with SHA-256 hashes and sizes. The verifier also rejects missing or extra files, duplicate filenames, path traversal, symlink entries, oversized content, unsafe compression ratios, and external or embedded resources in the standalone HTML report.

## Workspace backup and restore

```bash
shadowseed workspace info
shadowseed workspace backup --output shadowseed-workspace.sqlite
shadowseed workspace restore shadowseed-workspace.sqlite
```

Restore validates the candidate database before replacing the active workspace. Keep a separate backup before migration or prerelease experiments.

## Docker

The repository includes `Dockerfile.workbench` as an optional tester packaging path:

```bash
docker build -f Dockerfile.workbench -t shadowseed-workbench:0.4.2 .
docker run --rm \
  -p 127.0.0.1:7860:7860 \
  -v shadowseed-data:/data \
  shadowseed-workbench:0.4.2
```

The container listens on `0.0.0.0` internally so the host can reach it, while the recommended port mapping publishes it only on host loopback. Do not expose this preview to an untrusted network.

## What this product slice does not claim

The chat-first Workbench makes SSL usable as a normal local chatbot experience. It does **not** by itself establish full production readiness.

Still required for a hostile-network or mass-deployed product are, among other things:

- authentication and account/tenant isolation;
- TLS and CSRF/network controls;
- abuse controls and rate limits;
- managed secret storage;
- retention/deletion policy and operational monitoring;
- signed/no-Python standalone distribution;
- real-world high-end-model evaluation and independent review.

Scientific and authority constraints remain in the canonical runtime. The Workbench is a product surface over that runtime, not a second policy engine.

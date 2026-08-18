# Shadowseed Workbench 0.5.0 Mass Tester Preview

Shadowseed 0.5.0 changes the tester contract from a Python-installed research preview to a downloadable local chat application.

## Download/open product path

The release publishes self-contained Workbench archives for Windows, macOS and Linux. The ordinary tester no longer needs Git, a repository checkout, a system Python installation, `pip`, benchmark JSON or an authored baseline answer.

The intended flow is:

```text
download -> extract/open -> choose model -> create chat -> chat with SSL -> optionally compare one message with SSL off
```

Each standalone bundle contains its own Python runtime and Workbench dependencies. Model weights remain separate and explicit. Local Ollama models are detected through the read-only local tags endpoint; Hugging Face/Sentence Transformer model material may be acquired on first use; hosted OpenAI use remains explicit and credential-dependent.

## Chat-first SSL behavior

The ordinary product continues to use the canonical live/evidence-backed runtime introduced before this release:

- candidates start weightless;
- recurrence is not external evidence;
- Gate authority and point-of-use authorization remain runtime-owned;
- contradictions remain blocking under the current contract;
- ordinary tester feedback remains record-only;
- `Compare this message with SSL off` generates a same-model control without adding detection, recurrence, Gate or conversation-history state;
- a comparison difference is not labelled an SSL effect when no authorized seed actually surfaced.

Packaging does not create a second SSL implementation or change seed authority.

## Standalone release verification

Every platform build is produced by the same `Standalone Workbench` workflow from one exact Git commit.

Before upload, the frozen application runs its own self-test and must prove that it can:

1. initialize an isolated workspace;
2. build the chat-first UI;
3. execute a live fixture turn;
4. generate the paired SSL-off control;
5. export and verify a full report;
6. export and verify the privacy-minimized support bundle;
7. import the packaged Gradio, Sentence Transformers, Transformers, Torch and OpenAI runtime dependencies.

The release contains per-platform manifests, consolidated `PROVENANCE.json`, and `SHA256SUMS` for all published assets. The release workflow also publishes the Python wheel and source distribution for developers.

## Platform signing boundary

The 0.5.0 prerelease provides release checksums and build provenance. Platform-vendor signing/notarization is not claimed unless the published binary is actually signed with configured release credentials. macOS Gatekeeper or Windows reputation warnings can therefore still occur for this prerelease.

## Scientific and production boundary

0.5.0 is a **mass-tester product preview**, not a full production-readiness claim.

It does not establish general answer-quality improvement, reliable benefit from every valid seed, hostile-network multi-user security, managed tenancy/secrets, complete retention/deletion operations, broad high-end-model efficacy or independent real-world validation.

Historical benchmark baselines remain research/regression material. They are not inputs required by the standalone tester.

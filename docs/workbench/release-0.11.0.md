# Shadowseed Workbench 0.11.0

Shadowseed Workbench 0.11.0 is the 0.11 architecture and local-distribution alignment release. It keeps the ordinary product on one canonical authority path, makes runtime behavior easier to audit, and makes the normal local Workbench substantially thinner by moving heavy optional provider stacks out of the default standalone.

## Canonical runtime and audit alignment

0.11 tightens the relationship between persisted configuration, runtime behavior and audit output.

- structural settings that can reinterpret existing semantic state are guarded rather than silently reapplied;
- current Validation Gate revalidation follows the canonical configured policy;
- lifecycle expiry routes through the canonical Gate path;
- legacy Gate behavior is excluded from normal product controls;
- same-turn answer revision is separated from self-derived observation/authority semantics;
- generation and revision model roles are reported explicitly;
- prompt-contract and detector plumbing are auditable;
- human/SSL orchestration is surfaced as read-only derived state rather than reimplemented in the UI;
- behavior configuration now carries a versioned projection, digest and epoch so turn reports retain the exact behavior contract that produced them.

These changes do not create a second authority path. Gate decisions, contradiction handling, verified support and point-of-use authorization remain canonical runtime concerns.

## Workbench cleanup

The active Workbench is now the vNext chat-first interface only.

- the retired pre-vNext UI and its legacy tests were removed;
- the public Workbench entrypoint is thin and routes directly to the current interface;
- displayed version information comes from installed package metadata instead of a hardcoded label;
- current UI help distinguishes same-turn revision from self-derived authority;
- orchestration, Gate/profile relation and rebuild-required settings are visible without moving authority decisions into presentation code.

## Ollama-first semantic embeddings

Ollama is now a first-class semantic embedding backend.

- local embeddings use Ollama `POST /api/embed`;
- new Ollama Workbench sessions default to `embeddinggemma` and persist that model identity in provenance;
- chat-model discovery filters models that Ollama explicitly identifies as embedding-only;
- production-local loopback policy applies when either chat generation or embeddings use Ollama;
- Sentence Transformers uses the current embedding-dimension API with a backward-compatible fallback for older installations.

For the normal local path, pull an Ollama chat model and the embedding model once:

```bash
ollama pull <chat-model>
ollama pull embeddinggemma
```

## Thin normal Workbench and standalone

The normal `[workbench]` installation and frozen standalone no longer include the heavy Hugging Face/Sentence Transformers/Torch stack or the hosted OpenAI SDK.

The default local product therefore supports:

- fixture mode for deterministic mechanics testing;
- local Ollama chat plus local Ollama semantic embeddings.

Optional providers remain available for Python installations:

```bash
python -m pip install "shadowseed[workbench,models]"  # Hugging Face / Sentence Transformers / Torch
python -m pip install "shadowseed[workbench,openai]"  # hosted OpenAI
```

The provider selector shows optional providers only when their runtime is installed. Frozen Windows, Linux and macOS builds explicitly prove that the optional provider stacks are absent from the normal standalone.

## Standalone and CI hardening

0.11 also hardens the standalone bootstrap and release path.

- frozen startup calls `multiprocessing.freeze_support()` before entering the launcher;
- the packaged self-test exercises multiprocessing spawn in the real frozen artifact;
- ordinary merge protection remains on the required CI checks;
- heavy Workbench, portability, research-package and standalone assurance no longer rerun after every merge to `main`;
- the release workflow dispatches those heavy workflows explicitly for the exact release-candidate SHA and aborts if `main` advances;
- wheel, SBOM and production dependency audits now enforce the thin default distribution boundary.

## Upgrading from 0.10.1

Existing workspaces remain outside the application bundle and are not replaced by an application update.

A 0.10.1 standalone can use **Menu → Updates** to check for a verified 0.11.0 release and download the matching bundle. Replacement remains an explicit user action.

Python users who previously relied on Hugging Face or OpenAI being pulled indirectly by `[workbench]` must now install the corresponding provider extra explicitly.

## Claim boundary

0.11.0 remains a Research Preview. Stronger configuration/audit contracts, a thinner distribution, successful packaging checks and local semantic embeddings do not establish general answer-quality benefit, semantic truth, hostile-network security, hosted/multi-user readiness or a completed `production-ready/local` claim.

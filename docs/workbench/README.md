# Shadowseed Web and legacy Workbench

The 0.12.4 Research Preview candidate packages the existing browser client
with its local, loopback-only Python backend. It uses the canonical Shadow Seed
runtime. The old Gradio Workbench stays in the repository for opt-in
development/research, but **is not part of the audited 0.12.4 download**
because the legacy Gradio dependency pins a vulnerable Pillow version.
See [release notes](release-0.12.4.md) and
[security issue #200](https://github.com/E-AI-MODEL/shadowseed-pro/issues/200).
Until an exact-SHA release completes, v0.12.3 remains the latest published
download. No claim of production-ready/local follows from a successful
Research Preview build.

The normal tester flow is:

```text
download -> extract/open -> browser opens local Shadowseed -> choose model -> create chat -> talk with SSL -> optionally compare SSL off
```

Research scenarios, baseline-isolated experiments and evidence-efficacy work
remain separate from ordinary testing.

## Standalone web tester

A published release provides Windows, macOS and Linux archives. They contain
their own Python runtime and verified static web assets. Testers do not need
Git, pip or a system Python.

1. Download the appropriate archive and check `SHA256SUMS` when practical.
2. Extract and start **Shadowseed**. On macOS, the included first-launch
   helper can address browser quarantine for the ad-hoc signed application.
3. Shadowseed opens the interface in a browser on your own computer only.
4. Create a fixture conversation to inspect the mechanism without Ollama.
5. For real local chat, install and start Ollama and your chosen chat model,
   and pull `embeddinggemma`. EmbeddingGemma requires Ollama v0.11.10 or later.

Provider model weights are not bundled. Hugging Face and OpenAI runtimes are
optional separate extras, not part of the downloadable application. A bundled
self-test proves packaging and deterministic fixture behavior; it does not
prove live-model quality or a complete Ollama conversation.

The exact-SHA release gate verifies source SHA, three platform manifests,
audited web-only requirements, SBOM, frozen asset checks, checksums, wheel
installation, macOS sealing and archive round trip, and provenance. It
explicitly rejects Gradio/Pillow in the shipped dependency closure.

## Research access

Repository states/releases containing the root `LICENSE` are available under PolyForm Noncommercial License 1.0.0. Read those terms before copying, modifying or redistributing the software. Commercial use requires separate permission. This is source-available licensing, not an OSI open-source claim.

Historical releases keep the rights terms distributed with those versions. The 0.6.0 licensing change is not retroactive.

## Normal product contract

New ordinary chats use:

```text
runtime_mode = live
Gate policy = evidence_backed
```

New candidates start weightless. Recurrence is observable but does not become external evidence or raise authority on its own under this product policy. Contradictions remain blocking. Only current Gate-authorized seeds that pass the point-of-use contract may influence a later answer.

The Workbench presents the canonical runtime; it does not implement a second Gate or expose direct weight/promotion editing.

## Compare the current answer with SSL off

The normal Workbench comparison is a **same-turn control**. Both arms use the same model configuration, the same visible pre-turn conversation history and the same current user message. The control receives no surfaced Shadow Seed context. Only the real SSL turn changes session state.

This comparison adds at most one extra current-turn model generation. It never reconstructs older turns synchronously and it does not create a second ordinary chat history.

A textual difference is not automatically an SSL effect. When no authorized seed surfaced on the real turn, ordinary generation variance remains a possible explanation.

### Longitudinal vanilla is research-only

The **Research** tab contains a different experiment: an independent vanilla conversation trajectory that receives the same user questions but only its own earlier vanilla answers.

That experiment asks a different question: how a full vanilla conversation path diverges over time from the Shadowseed path. Starting it late can require historical user turns to be replayed into the vanilla trajectory, so it can be substantially slower. The UI reports how many earlier turns were rebuilt.

The longitudinal control remains isolated from candidate detection, recurrence, the Validation Gate and the Shadowseed conversation history. Do not describe it as a same-turn causal comparison.

## Feedback and independently verified support

Ordinary tester feedback is `record_only`: it does not alter seed authority.

Verified support is a separate live action. The tester/operator must attest that support was checked outside model output and provide a stable source reference. Reusing the same underlying source cannot manufacture extra authority by relabeling or resubmitting it.

## Exports

### Full report

A full report is self-contained and auditable but content-bearing. It can include prompts, answers, controls, seeds, Gate/influence records and free-text tester feedback. Treat it as sensitive unless inspected and intentionally shared.

### Privacy-minimized support bundle

A support bundle omits direct session identity, session title, prompts, answers, control text, seed text and free-text tester notes. It retains a stable pseudonymous `support::...` identifier, model/backend/configuration metadata, environment metadata and structural counts. This is minimization, not formal anonymization.

Both export types contain SHA-256 manifests and are checked by `shadowseed verify-workbench-export`.

## Collect data across testers

The support collector combines verified privacy-minimized bundles:

```bash
python scripts/aggregate_support_bundles.py \
  tester-a.zip tester-b.zip tester-c.zip \
  --collection-id pilot-2026-08 \
  --output results/pilot-2026-08-support-dataset.json
```

The collector:

- verifies every ZIP through the canonical Workbench verifier;
- accepts support bundles only;
- rejects duplicate pseudonymous session identities;
- records each source bundle SHA-256;
- emits schema `shadowseed-support-dataset-v1` with collection identity, software/environment/configuration metadata and minimized structural observations.

This makes mass-test data technically collectable and auditable. It does not create a scientific conclusion by itself. A real study still needs protocol, inclusion rules, controls, analysis plan, privacy/ethics decisions and review.

## Evidence-efficacy studies are separate

Version 0.6.0 introduced a preregistered evidence-efficacy research path for answer-level effects after verified external support has passed through the canonical `evidence_backed` Gate. In the current repository that harness lives in the separate `shadowseed-research` distribution and runs as `python -m shadowseed_research.benchmark.evidence_efficacy`.

This is not a Workbench support-data feature. Evidence-efficacy bundles contain content-bearing research data and use baseline-isolated evaluation mechanics. They must not be treated as privacy-minimized support bundles.

A valid paired item is created only when:

```text
predeclared candidate observed
-> verified external support submitted
-> evidence_backed Gate grants authority
-> later point-of-use check allows it
-> seed surfaces
-> blind baseline/SSL A/B packet generated
```

If any step does not happen, the reason remains in `opportunity_audit.json`. The harness never weakens the product Gate merely to create an A/B pair.

See [evidence efficacy](../research/evidence-efficacy.md), [privacy guidance](privacy.md) and [tester guidelines](tester-guidelines.md).

## Developer install

The normal web product needs only the core Python runtime plus generated
static assets. The command is `shadowseed-web`. To run from source, build
`apps/web` and synchronize assets with `scripts/sync_web_assets.py`.

The previous Gradio interface remains explicitly opt-in and **not approved
as a secure downloadable 0.12.4 bundle** while issue #200 is unresolved.

```bash
python -m pip install "shadowseed[workbench]"
shadowseed-workbench --legacy-gradio

# Optional local model providers:
python -m pip install "shadowseed[workbench,models]"
```

## Docker

The optional container route remains available for development/testing:

```bash
docker build -f Dockerfile.workbench -t shadowseed-workbench:0.12.4 .
docker run --rm \
  -p 127.0.0.1:7860:7860 \
  -v shadowseed-data:/data \
  shadowseed-workbench:0.12.4
```

Do not expose this preview directly to an untrusted network.

## Claim boundary

Version 0.12.4 is the current Research Preview release candidate and production-local assurance candidate; published `v0.12.1` is not eligible for production-local promotion. Packaging, licensing, tester observations, support-dataset aggregation, release hardening and the existence of an efficacy runner do not establish general answer-quality benefit, semantic truth, hostile-network production security or high-impact deployment readiness. The `production-ready/local` claim remains gated on exact protected-main release evidence and the recorded use cycle on the published release defined by the production acceptance contract.

The scientific/authority constraints remain in the canonical runtime. Historical evaluation sessions, benchmark artifacts and compatibility surfaces remain research/provenance material rather than product prerequisites.

# Shadowseed Tester Workbench

The Workbench is the local-first chat surface for testing Shadow Seed Learning in an ordinary LLM conversation. Version 0.7.1 carries forward the low-friction mass-tester path, noncommercial research access, and evidence-measurement tooling while serving as the current production-local assurance candidate. It is not `production-ready/local` until the exact-SHA release-assurance and unchanged-candidate soak requirements are complete.

```text
download -> extract/open -> choose model -> create chat -> chat with SSL -> optionally compare one message with SSL off
```

Research scenarios, baseline-isolated evaluation mode, evidence-efficacy studies, raw diagnostics and benchmark tools remain separate. They are not prerequisites for ordinary testing.

## Standalone tester

Use the download/open route only when a verified GitHub release for the version you want to test and its assets are present. A normal tester then does not need Git, `pip`, system Python, benchmark JSON or an authored baseline.

1. Download the archive for the operating system/architecture.
2. Verify it against `SHA256SUMS` when practical.
3. Extract/open **Shadowseed**.
4. The app creates/opens the local `~/.shadowseed` workspace and binds the UI to loopback.
5. Choose a model, create a chat and start talking.

Model weights are intentionally separate. Fixture works offline for mechanics. Ollama uses local installed models. Hugging Face/Sentence Transformers may acquire model material on first use. Hosted OpenAI is explicit and credential-dependent.

A valid 0.7.1 prerelease contains three standalone archives and manifests, `PROVENANCE.json`, `SHA256SUMS`, a Python wheel, source distribution, and `LICENSE`. Frozen bundles must pass their packaged product self-test and carry the exact repository license hash before upload. The macOS archive must additionally preserve a valid final application seal after every bundle mutation, survive archive extraction, and pass the frozen self-test from the round-tripped app before release.

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

## Compare one message with SSL off

When **Compare this message with SSL off** is enabled, the Workbench first generates a same-model control from the same pre-turn visible history without surfaced SSL seeds. The control is stored as comparison data only. It does not enter candidate detection, recurrence, the Validation Gate or later conversation history. The actual live turn remains the only state-changing turn.

A textual difference is not automatically an SSL effect. When no authorized seed surfaced, ordinary generation variance remains a possible explanation.

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

Version 0.6.0 introduced `python -m shadowseed.benchmark.evidence_efficacy` for preregistered research on answer-level effects after verified external support has passed through the canonical `evidence_backed` Gate. That research harness remains available in 0.7.1.

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

```bash
python -m pip install "shadowseed[workbench]"
shadowseed doctor
shadowseed workbench
```

or:

```bash
shadowseed-workbench
```

## Docker

The optional container route remains available for development/testing:

```bash
docker build -f Dockerfile.workbench -t shadowseed-workbench:0.7.1 .
docker run --rm \
  -p 127.0.0.1:7860:7860 \
  -v shadowseed-data:/data \
  shadowseed-workbench:0.7.1
```

Do not expose this preview directly to an untrusted network.

## Claim boundary

Version 0.7.1 is the current production-local assurance candidate. Packaging, licensing, tester observations, support-dataset aggregation, release hardening and the existence of an efficacy runner do not establish general answer-quality benefit, semantic truth, hostile-network production security or high-impact deployment readiness. The `production-ready/local` claim remains gated on the exact protected-main release evidence and unchanged-candidate soak defined by the production acceptance contract.

The scientific/authority constraints remain in the canonical runtime. Historical evaluation sessions, benchmark artifacts and compatibility surfaces remain research/provenance material rather than product prerequisites.

# Shadowseed Workbench 0.10.0

Shadowseed Workbench 0.10.0 is a major Workbench reset around the actual
Shadow Seed Learning lifecycle. The release keeps the canonical SSL runtime,
Validation Gate, persistence and point-of-use authority model, but replaces
the 0.9.x product surface and corrects the normal comparison contract.

## New Workbench interface

The normal application is now organized around one active conversation:

- conversations on the left;
- ordinary chat in the center;
- a compact Shadow summary and recent memory points on the right;
- dedicated drawers for New chat, Source input, Shadow detail, Research,
  Technical audit and contextual Help.

The ordinary UI no longer exposes a single "SSL influence" percentage, a
single Gate percentage or self-reinforcement as if those were simple product
controls. Independent mechanisms remain separate and research-oriented controls
live under Research.

Every visible normal-product function has contextual help that explains:

- the function in simple language;
- what it maps to in the runtime;
- what it does not do;
- how it interacts with other SSL mechanisms;
- what the current combination means for the active session or seed.

The help text preserves the distinctions that define SSL: remembered is not
believed, recurrence is not evidence, relevant is not authorized, authorized
is not necessarily surfaced, and surfaced context is not proof of causal
influence.

## Normal A/B is same-turn again

The ordinary action to compare a response without SSL is a same-turn control.

Both arms use:

- the same model configuration;
- the same visible pre-turn conversation history;
- the same current user message;
- the same generation path.

The intended difference is the availability of authorized Shadow Seed context.
The control is non-mutating and does not enter detection, recurrence, Gate
state or later conversation history.

This path adds at most one extra current-turn model generation and never
replays older turns synchronously.

## Longitudinal vanilla stays research-only

The independent vanilla-history experiment introduced in 0.9.2 remains
available under Research for a different question: cumulative trajectory
divergence over time.

It is explicitly separated from the normal same-turn comparison. Starting that
experiment late may require historical user turns to be replayed and can
therefore be substantially slower.

## Shadow and source semantics

The Workbench now presents the SSL lifecycle directly:

```text
noticed -> seen again -> supported/contradicted -> authorized
        -> relevant -> offered at point of use
```

The UI keeps these concepts distinct:

- **remembered** means a persistent seed exists;
- **authorized** means the current Gate permits influence;
- **offered** means the seed passed the current relevance/point-of-use path;
- **contradiction** blocks point-of-use until formally resolved;
- **verified support** is independently checked evidence routed through the
  existing evidence/Gate path;
- **source input** is observation material and is not automatically trusted
  evidence.

## Release process

0.10.0 also changes the release publication flow.

Feature and release pull requests continue to run the normal CI, Workbench,
portability, research-package and standalone checks. Publishing is no longer an
automatic side effect of every successful main push.

A release is now started explicitly through the **Release Workbench** workflow.
The workflow:

1. binds to the current protected `main` SHA;
2. verifies successful exact-SHA CI, Workbench CI, Workbench Portability,
   Research Package CI and Standalone Workbench runs;
3. reuses the exact standalone artifacts from that SHA;
4. verifies lock, license, manifests, provenance and checksums;
5. builds and smoke-tests the wheel/sdist;
6. produces the CycloneDX SBOM and GitHub artifact attestations;
7. publishes an exact-source prerelease tag;
8. re-downloads and verifies the published assets;
9. fails closed if `main` advances during publication.

## Compatibility

The 0.10.0 Workbench reset does not intentionally replace the SSL engine or
reinterpret seed authority. Existing persisted sessions retain their runtime
metadata and audit history.

The legacy 0.9.2 independent `vanilla_history` remains readable for research
and provenance even though it is no longer the normal interactive comparison.

## Claim boundary

0.10.0 is a **Research Preview**. It does not establish general answer-quality
improvement, semantic truth, universal missing-information detection,
production-ready hosted/multi-user operation, or suitability for high-impact
decisions.

A textual difference between two model generations is not by itself evidence
that SSL improved or caused the answer. Interpretation depends on the recorded
Gate, surfacing and comparison provenance.

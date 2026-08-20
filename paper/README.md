# Shadowseed paper LaTeX source

**Title:** *Shadowseed: Remembering Without Trusting*  
**Subtitle:** *A Validation-Gated Memory Architecture for Language Model Systems*

**Author:** H. Visser, E-AI-MODEL

[Read the compiled paper (PDF)](shadowseed-paper.pdf)

This `paper/` directory is the canonical manuscript location. The manuscript is a reviewed research artifact, not a moving release brochure and not an authority source over the runtime, accepted ADRs, or current architecture documentation.

## Files

- `main.tex` - manuscript source
- `references.bib` - bibliography
- `shadowseed-paper.pdf` - compiled manuscript generated from that source revision

`main.tex`, `references.bib`, and `shadowseed-paper.pdf` must change together when the manuscript itself is revised. Do not edit only the visible PDF version/commit text to make it match a newer software badge.

## Relationship to software v0.6.0

The current software upgrade candidate is **0.6.0**. The checked-in manuscript remains intentionally pinned to the reviewed software source version **0.5.0** and implementation commit printed inside `main.tex` and the compiled PDF.

Software 0.6.0 adds noncommercial research access, license-delivery release checks, and evidence-backed paired efficacy instrumentation. It does **not** redefine the paper's core trace/weight, Validation Gate, evidence identity, contradiction, lifecycle, or point-of-use authority model. The new efficacy runner deliberately reuses the existing `evidence_backed` Gate and `ShadowChatSession.submit_evidence` boundary rather than creating a manuscript-only or benchmark-only authority path.

This separation is deliberate scientific provenance:

1. **Current software version** tells you which package/release you are running.
2. **Reviewed implementation commit in the paper** tells you which code snapshot the manuscript's implementation claims were checked against.
3. **Paper-source revision** identifies the exact manuscript/PDF pair.
4. **Research-result bundles** identify the exact later software/model/protocol configuration used for empirical measurements.

A later paper revision may advance those anchors, but only when the LaTeX source, bibliography as needed, and compiled PDF are rebuilt and reviewed together.

## Claim alignment

The repository and manuscript agree on the important claim boundary:

- a remembered candidate is not automatically trusted;
- trace and steering weight are separate;
- authority changes are policy-controlled and auditable;
- validation policy is explicit rather than universalized across research and product modes;
- recurrence is not external evidence;
- current point-of-use authorization remains separate from prior promotion;
- tests and artifacts support bounded implementation claims, not general answer-quality improvement or production certification.

The v0.5.1 support-dataset collector remains research instrumentation. It makes privacy-minimized multi-tester observations easier to combine, but collected data becomes scientific evidence only under an explicit protocol, controls, analysis plan, and review.

The v0.6.0 evidence-efficacy runner is also research instrumentation. It can create a valid blind A/B opportunity only when predeclared external support passes through the normal evidence-backed Gate and the authorized seed later surfaces. The existence of that runner is not itself an efficacy result. Real-model execution, valid external support, and independent review remain necessary.

## Licensing and manuscript rights

The root software repository now contains PolyForm Noncommercial License 1.0.0 for repository states and software releases that include that license. Do not infer from that software license that every paper, dataset, model weight, citation source, or separately identified third-party artifact has been relicensed. The applicable notice distributed with each artifact remains authoritative for that artifact.

## Release identity is separate

A source version is not proof that a corresponding public release exists. Treat `v0.6.0` as published only when the immutable tag and verified release assets are present. Release provenance, license delivery, and checksums are governed by the repository's release workflow, not by this manuscript.

## Authorship and LLM disclosure

The manuscript lists the accountable human author. LLM systems are acknowledged in the paper's `LLM usage disclosure` section rather than listed as authors. The human author remains responsible for claims, citations, source verification, and the published artifact.

## Build

With a TeX distribution containing `latexmk`, `biber`, and the packages imported by `main.tex`:

```bash
latexmk -pdf -interaction=nonstopmode -halt-on-error main.tex
mv main.pdf shadowseed-paper.pdf
```

Before committing a rebuilt PDF, render and inspect every page for broken references, clipping, missing glyphs, or layout regressions.

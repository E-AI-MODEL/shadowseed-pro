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

## Relationship to current software v0.7.1

The current software version is **0.7.1**. The checked-in manuscript remains intentionally pinned to the reviewed software source version **0.5.0** and implementation commit printed inside `main.tex` and the compiled PDF.

Software releases after 0.5.0 extend the product, research instrumentation, persistence, operational safety, and release-assurance layers around the reviewed SSL core. They do **not** redefine the paper's core trace/weight separation, Validation Gate, evidence identity, contradiction, lifecycle, or point-of-use authority model.

In particular:

- **0.5.1** adds support-dataset collection for research use;
- **0.6.0** adds noncommercial research access, license-delivery checks, and evidence-backed paired efficacy instrumentation;
- **0.7.x** adds production-local persistence, recovery, authorization, operational limits, candidate-observation provenance, and release-assurance hardening;
- **0.7.1** repairs the macOS standalone sealing and archive round-trip verification path while leaving the SSL authority model unchanged.

The later efficacy and production-assurance paths deliberately reuse the existing runtime authority boundaries rather than creating manuscript-only, benchmark-only, or product-only Gate semantics.

This separation is deliberate scientific provenance:

1. **Current software version** tells you which package/release you are running.
2. **Reviewed implementation commit in the paper** tells you which code snapshot the manuscript's implementation claims were checked against.
3. **Paper-source revision** identifies the exact manuscript/PDF pair.
4. **Research-result bundles** identify the exact later software/model/protocol configuration used for empirical measurements.

A later paper revision may advance those anchors, but only when the LaTeX source, bibliography as needed, and compiled PDF are rebuilt and reviewed together.

## Directory boundary: `paper/` versus `data/papers/`

These directories intentionally serve different roles:

- `paper/` contains the Shadowseed manuscript source, bibliography, and compiled publication artifact;
- `data/papers/` contains external research papers and other source-reference material used during research and review.

External source PDFs therefore belong under `data/papers/`, not under `paper/data/`. Keeping them separate preserves the repository authority boundary between the publication artifact and its supporting source material.

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

The v0.7.x production-local assurance work adds operational controls and stronger persistence/release guarantees around the same SSL authority model. Those additions do not retroactively expand the manuscript's evidence claims and do not turn the reviewed paper into a production certification.

## Licensing and manuscript rights

The root software repository contains PolyForm Noncommercial License 1.0.0 for repository states and software releases that include that license. Do not infer from that software license that every paper, dataset, model weight, citation source, or separately identified third-party artifact has been relicensed. The applicable notice distributed with each artifact remains authoritative for that artifact.

## Release identity is separate

A source version is not proof that a corresponding public release exists. Release publication, provenance, license delivery, checksums, attestations, and prerelease/production status are governed by the repository's release workflow and release records, not by this manuscript.

The 0.7.1 research preview is a production-local assurance candidate. Its existence does not by itself complete a `production-ready/local` claim; that status remains governed by the repository production-acceptance contract.

## Authorship and LLM disclosure

The manuscript lists the accountable human author. LLM systems are acknowledged in the paper's `LLM usage disclosure` section rather than listed as authors. The human author remains responsible for claims, citations, source verification, and the published artifact.

## Build

With a TeX distribution containing `latexmk`, `biber`, and the packages imported by `main.tex`:

```bash
latexmk -pdf -interaction=nonstopmode -halt-on-error main.tex
mv main.pdf shadowseed-paper.pdf
```

Before committing a rebuilt PDF, render and inspect every page for broken references, clipping, missing glyphs, or layout regressions.

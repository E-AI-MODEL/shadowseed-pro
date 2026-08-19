# Shadowseed paper LaTeX source

**Title:** *Shadowseed: Remembering Without Trusting*  
**Subtitle:** *A Validation-Gated Memory Architecture for Language Model Systems*

**Author:** H. Visser, E-AI-MODEL

[Read the compiled paper (PDF)](shadowseed-paper.pdf)

This `paper/` directory is the canonical repository location for the manuscript source. The paper is a research/publication artifact. It does not override the runtime, accepted ADRs, or current architecture documentation.

## Files

- `main.tex` - manuscript source
- `references.bib` - bibliography
- `shadowseed-paper.pdf` - compiled manuscript generated from the source above

`main.tex`, `references.bib`, and `shadowseed-paper.pdf` must change together when the manuscript is revised.

## Version anchors

The manuscript separates three identities that should not be conflated:

1. **Software source version:** the package/repository source version described by the paper.
2. **Reviewed implementation commit:** the exact code commit against which implementation claims were checked.
3. **Paper-source revision:** the Git commit containing the manuscript source and compiled PDF.

A source version is not evidence that a matching public release tag or binary asset exists. Release availability must be verified independently before documentation calls it published.

## Claim boundary

The manuscript is a methods/systems paper. Tests and CI support bounded implementation-contract claims. They do not establish general answer-quality improvement, semantic correctness of generated candidates, universal security, or production readiness.

## Authorship and LLM disclosure

The manuscript lists the accountable human author. LLM systems are acknowledged in the paper's `LLM usage disclosure` section rather than listed as authors. The human author remains responsible for claims, citations, source verification, and the published artifact.

## Build

From this directory, with a TeX distribution that includes `latexmk`, `biber`, and the packages imported by `main.tex`:

```bash
latexmk -pdf -interaction=nonstopmode -halt-on-error main.tex
mv main.pdf shadowseed-paper.pdf
```

Before committing a rebuilt PDF, render it and inspect every page for broken references, clipping, missing glyphs, or layout regressions.

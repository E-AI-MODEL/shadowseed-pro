# Shadowseed paper LaTeX source

**Title:** *Shadowseed: Remembering Without Trusting*  
**Subtitle:** *A Validation-Gated Memory Architecture for Language Model Systems*

**Authors:** H. Visser, ChatGPT, Claude, Kimi, GLM

## Files

- `main.tex` — complete manuscript draft
- `references.bib` — bibliography based on primary paper/proceedings sources plus the frozen Shadowseed 0.4.2 software artifact

The manuscript is written as a methods/systems paper. Its evidential scope is deliberately narrow: the current tests and CI establish executable implementation contracts. General answer-quality improvement, universal security, and production readiness remain open empirical or operational questions.

Implementation under test:

- Shadowseed Pro 0.4.2
- commit `18039196549e68936d1976b74eb8e6aac3eac98e`

## Compilation

The source uses `biblatex` with the `biber` backend. A typical build is:

```bash
latexmk -pdf -interaction=nonstopmode -halt-on-error main.tex
```

Manual equivalent:

```bash
pdflatex main.tex
biber main
pdflatex main.tex
pdflatex main.tex
```

The current draft compiles successfully with TeX Live, `biber` 2.20, and `latexmk` 4.86.

## Editorial note

The prose received a separate style pass aimed at reducing formulaic LLM-like cadence. In particular, the manuscript contains no `not X, but Y` / `not only X but Y` negative-parallelism constructions, no em dashes, and no repeated stock transitions such as `However`, `Moreover`, or `Furthermore`. These are editorial choices, not an AI-authorship test.

Before venue submission, replace the generic article layout with the venue template and check that venue's current authorship, AI-contribution, disclosure, affiliation, and double-blind-review policies. The author block in this draft intentionally lists H. Visser, ChatGPT, Claude, Kimi, and GLM as requested for the project record.

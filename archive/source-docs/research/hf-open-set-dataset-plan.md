# HF Open-Set Dataset Integration Plan

> Status: historical
> Date: 2026-05-22
> Evidence layer: HF intake plan, mostly implemented; see workflow + #81
> Current source: no


## Why this exists

The report and publish pipeline now carries automatic benchmark layers cleanly, but the next evidence step is still missing: a reproducible open-set dataset intake route.

This PR is intentionally a scope PR, not a data-import PR.

## Goal

Add a reproducible Hugging Face dataset intake path for open-set seed review without turning the repository into a large raw-data mirror.

## Principles

- Keep standard regression CI small and stable.
- Keep human-reviewed open-set evidence separate from automatic smoke layers.
- Pin upstream dataset source and revision.
- Commit only small curated review batches to the repository.
- Keep large raw downloads out of `main`.

## Proposed deliverables for the implementation PR

1. A dataset source registry with dataset name, split, revision, license note, and selection rationale.
2. A fetch script that downloads a pinned subset from Hugging Face.
3. A prepare script that normalizes examples into the repo's open-set review input schema.
4. A small checked-in sample batch for reproducible manual review.
5. Documentation for where raw data lives versus what is safe to commit.

## Non-goals

- No large raw dataset dump into the repository.
- No automatic claim that open-set review belongs in standard CI.
- No silent mixing of human-reviewed outputs with fixture-smoke metrics.

## Suggested execution order

1. Choose one or two Hugging Face datasets that fit the repo domains.
2. Define the normalized schema and filtering rules.
3. Implement fetch and prepare scripts.
4. Commit a tiny curated sample batch.
5. Run open-set review on that batch and document the review protocol.

## Review question for the implementation PR

Should the first HF-backed batch optimize for domain realism, review speed, or legal/licensing simplicity?

# SLM Open Evaluation Prompts

Status: experimental
Related issue: #56

## Purpose

This directory contains rotating prompt sets for SLM open evaluation.

The goal is to test whether SSL improves a small language model on unfamiliar prompts. These prompt sets are not fixed fixture suites and should not contain expected gaps or prefilled seeds.

## What this is for

Use these prompt sets to compare:

- the same SLM;
- the same prompt;
- baseline answer without SSL;
- SSL-assisted answer;
- saved raw outputs and later review.

## What this is not for

Do not use these files as standard regression fixtures.

Do not treat one small prompt set as broad proof of SSL quality.

Do not add hidden expected gaps, answer keys, or pre-written seeds to the prompt file.

## Prompt file contract

Each prompt file should be JSON with this shape:

```json
{
  "version": "slm-open-eval-0.1",
  "prompt_set_id": "2026-05-10-smoke",
  "source": "human_curated_rotating",
  "status": "experimental",
  "items": [
    {
      "id": "SLM_OPEN_001",
      "domain": "legal_reasoning",
      "prompt": "...",
      "source_note": "...",
      "hidden_review_notes": null
    }
  ]
}
```

Required fields per item:

| Field | Meaning |
|---|---|
| `id` | Stable prompt ID inside this prompt set. |
| `domain` | Broad topic label for grouping later review. |
| `prompt` | The prompt shown to both baseline and SSL routes. |
| `source_note` | Short human note about origin or intent. |
| `hidden_review_notes` | Must be `null` before generation. |

## Rules

- no `expected_gaps` field;
- no `expected_seeds` field;
- no answer key;
- no prefilled SSL seeds;
- no scenario labels that reveal a target gap;
- prompt set ID must be visible in raw output later;
- old prompt sets should not be reused as the main evidence source unless explicitly marked as regression.

## Review boundary

The prompt file is only the input.

A later review step may create separate review packets with fields such as:

- preferred answer: `baseline`, `ssl`, or `tie`;
- whether SSL added useful detail;
- whether SSL added unsupported claims;
- answer length delta;
- reviewer notes.

That review data must live in a separate output file, not in the prompt file.

## First implementation path

1. Add prompt contract and first prompt set.
2. Add a raw generation route that writes `results/slm_open_eval_raw.json`.
3. Add review packets and summary generation.
4. Add a manual workflow only after the command path is stable.
5. Keep any publication experimental and opt-in.

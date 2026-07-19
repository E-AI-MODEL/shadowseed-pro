# SLM Open Evaluation Plan

> Status: partly current
> Date: 2026-05-22
> Evidence layer: Earlier plan; design contract is `slm-open-evaluation.md` (#56 / PR #83)
> Current source: partial


Status: proposed
Date: 2026-05-10
Base commit: `52c8fdf4fe422b43bd116f7c1e06e2f361c87330`
Related issue: #56

## Purpose

Use an SLM to measure whether SSL improves answers on unfamiliar prompts.

This plan changes the SLM direction from fixture validation to open evaluation. Fixed scenario suites can stay as smoke and regression support, but they should not be the main evidence for SLM/SSL effectiveness.

## Current problem

The current SLM route runs a real HF-backed model benefit suite, but it also generates companion outputs from fixed benchmark suites before analysis:

- gap suite
- false-positive suite
- benefit suite

Those fixed suites are useful because they are stable and repeatable. They are not enough to measure whether SSL works on unfamiliar inputs. If the repo keeps testing the same known gaps and seeds, the result becomes a regression check rather than a meaningful effectiveness evaluation.

## Target question

The SLM route should answer this question:

> Given the same small language model and the same unfamiliar prompt, does SSL produce a better answer than the baseline route without SSL?

The main comparison should be:

| Dimension | Requirement |
|---|---|
| Model | Same SLM for baseline and SSL-assisted answer. |
| Prompt | Same prompt for both routes. |
| Prompt source | Fresh, rotating, external, or human-curated. |
| Main evidence | Open or blind prompts, not fixed known fixture gaps. |
| Output | Raw baseline answer, raw SSL answer, SSL seeds/probes, and review or judge summary. |
| Claim | Experimental SLM open-evaluation, not standard CI regression. |

## Non-goal

This does not remove the fixed suites.

The fixed suites should stay available as:

- regression checks;
- smoke checks;
- route sanity checks;
- analyzer compatibility checks.

They should not be described as the main SLM effectiveness proof.

## Proposed evaluation modes

Start with one small mode. Do not build all modes at once.

### Mode A: rotating prompt file

A prompt file is committed for a short evaluation window.

Example path:

```text
benchmarks/slm_open_eval/prompts/YYYY-MM-DD.json
```

Pros:

- easy to review;
- easy to reproduce;
- no external dependency during the run.

Cons:

- prompts can become stale;
- needs discipline to rotate.

### Mode B: HF/open-set sample with pinned IDs

The workflow samples from a known external dataset or open-set registry, then pins selected IDs in the artifact.

Pros:

- less hand-authored;
- better open-set signal.

Cons:

- external dependency;
- dataset drift must be controlled.

### Mode C: generated prompt batch saved before evaluation

The workflow creates or fetches prompts and saves the batch as an artifact before running baseline/SSL.

Pros:

- can rotate often;
- avoids silently reusing the same set.

Cons:

- harder to review;
- generated prompts can be low quality.

### Mode D: human-curated blind batch

Humans curate prompts and hide review labels until after answer generation.

Pros:

- strongest for claim discipline;
- avoids hardcoded expected gaps during generation.

Cons:

- manual;
- slower.

## Recommended first implementation

Start with Mode A.

Why:

- simplest implementation;
- easy to inspect in PR review;
- no external dataset dependency;
- enough to stop relying on the same fixed scenario suites;
- can later move to Mode B or D.

## Suggested data contract

### Prompt file

```json
{
  "version": "slm-open-eval-0.1",
  "prompt_set_id": "2026-05-10-smoke",
  "source": "human_curated_rotating",
  "items": [
    {
      "id": "SLM_OPEN_001",
      "domain": "legal_reasoning",
      "prompt": "...",
      "source_note": "short human note",
      "hidden_review_notes": null
    }
  ]
}
```

Rules:

- no expected gaps in the prompt file;
- no pre-filled seeds;
- no answer-specific labels before generation;
- prompt IDs must be stable within a run;
- prompt set ID must be visible in output.

### Raw output file

Suggested path:

```text
results/slm_open_eval_raw.json
```

Should include:

- model ID;
- prompt set ID;
- prompt ID;
- baseline answer;
- SSL-assisted answer;
- SSL seeds promoted during the run;
- probe feedback if present;
- answer lengths;
- runtime settings.

### Review or judge summary

Suggested path:

```text
results/slm_open_eval_summary.json
```

Should include:

- item count;
- evaluator type: `human`, `llm_judge`, or `mixed`;
- preference rate for SSL answer;
- tie rate;
- baseline preference rate;
- unsupported addition flags;
- answer length deltas;
- review status.

### Report

Suggested path:

```text
results/slm_open_eval_report.md
```

Must label the result as:

```text
experimental_open_eval
```

## Evaluation options

The first version can use manual review instead of automatic scoring.

Recommended review fields:

| Field | Meaning |
|---|---|
| `preferred_answer` | `baseline`, `ssl`, or `tie`. |
| `ssl_added_useful_detail` | Whether SSL added useful missing detail. |
| `ssl_added_unsupported_claim` | Whether SSL added unsupported or risky content. |
| `baseline_missed_obvious_point` | Whether baseline missed a major point. |
| `ssl_answer_too_long` | Whether SSL only wins by being longer or verbose. |
| `reviewer_notes` | Short explanation. |

This keeps the first SLM open-eval honest without inventing a fake ground truth.

## Length control

Length must be measured.

The output should include:

- baseline token or word count;
- SSL token or word count;
- answer length delta;
- preference result with length visible;
- optional normalized score when implemented.

Reason:

Longer SSL answers may look better because they mention more things. That is not automatically proof of better SSL behavior.

## Workflow direction

Create a new manual workflow later:

```text
.github/workflows/slm-open-evaluation.yml
```

Suggested inputs:

| Input | Default | Meaning |
|---|---|---|
| `model_id` | `TinyLlama/TinyLlama-1.1B-Chat-v1.0` | HF model ID. |
| `prompt_file` | latest rotating prompt file | Prompt file to evaluate. |
| `turns` | `3` | SSL detection turns. |
| `max_new_tokens` | `220` | Generation limit. |
| `publish` | `false` | Whether to publish report to Wiki. |
| `review_mode` | `manual_pending` | First implementation should not fake a full judge. |

The workflow should:

1. install model dependencies;
2. load the rotating prompt file;
3. generate baseline and SSL answers;
4. save raw answer artifacts;
5. create review packets or pending summary;
6. optionally publish an experimental report.

## Publication rule

Do not publish SLM open-eval as a standard proof route on the first implementation.

If published, page title should make status clear:

```text
SLM Open Evaluation Experimental
```

The report should state:

- prompt set ID;
- model ID;
- sample size;
- review status;
- whether review is pending, human-reviewed, or judge-reviewed;
- that fixed fixture suites were not the main evidence source.

## Relation to existing SLM workflows

Existing workflows:

- `slm-model-benefit.yml`
- `publish-existing-slm-conclusion.yml`

Do not merge or delete them yet.

The next implementation should add the new open-evaluation route beside them. After it works, decide whether:

- `slm-model-benefit.yml` becomes a smoke/regression workflow;
- `publish-existing-slm-conclusion.yml` is retired;
- SLM Wiki publication is moved to the new open-eval route.

## Migration plan

### PR A: planning

- add this document;
- reframe issue #56;
- do not change YAML.

### PR B: prompt contract and sample prompt file

- add `benchmarks/slm_open_eval/README.md`;
- add first small rotating prompt file;
- add schema expectations in docs or tests.

### PR C: raw generation command or script

- add a CLI route or benchmark module that produces `slm_open_eval_raw.json`;
- generate baseline and SSL answers for same prompts;
- no publication yet.

### PR D: review packets and summary

- add review packet generation;
- add manual review summary route;
- include length and unsupported-addition fields.

### PR E: manual workflow

- add `slm-open-evaluation.yml`;
- upload raw output, review packets, summary and report artifacts;
- keep publishing off by default.

### PR F: publication, if results are useful

- add experimental Wiki publication;
- keep it separate from standard CI publication;
- label claim boundaries clearly.

## Done criteria for first useful version

A first useful SLM open-evaluation version is done when:

- the prompt set is not one of the fixed fixture suites;
- baseline and SSL answers are generated for the same prompts;
- raw answers are saved;
- review packets exist;
- summary reports sample size, SSL preference, ties, unsupported additions and length deltas;
- report labels the result as experimental;
- fixed fixture results are not used as the main claim.

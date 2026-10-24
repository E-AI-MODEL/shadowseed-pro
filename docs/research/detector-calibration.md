# Detector calibration for small local models (2026-10-24)

## Why

In the live recurrence probe (Qwen 2.5 7B Q4_K_M, the 12 conversations of the study-1 suite, 96 turns), the product detector `current_pair` v0.6 returned NONE in 63 of 96 turns. The raw output shows three patterns:

- bare `NONE`, and malformed variants such as `3\nNONE` and `1. NONE`. The model echoes the `0 to {max_seeds}` range or numbers the NONE;
- title-case labels without content ("Backup Location"), which the parser drops as stubs;
- multi-sentence explanations ("... This gap could be a candidate for further clarification."), which the intake rejects as more than one sentence.

GPT-5 gives about five usable candidates per turn on the same prompt, so the prompt is not wrong in general. It is too abstract for a 7B model.

## Design (fixed before the run)

`scripts/detector_calibration.py` runs each conversation through a live session with the product detector. At every detection call the same item (question, draft answer, bounded context) also goes to one candidate prompt, `detector_current_pair_candidate_v0.7`. The candidate's output never enters the session, so both prompts see identical turns.

The candidate prompt asks for "open points the answer depends on but does not settle", lists five concrete kinds (assumption, uncovered case, unspecified number or choice, missing user information, blurred distinction), asks for one short sentence per numbered line, and gives two format examples from an unrelated topic. Output that copies an example is dropped and counted.

Measured per prompt: detections with no admitted candidate, explicit NONE, parsed and admitted candidates, example leaks.

Usefulness: the admitted candidates of both prompts are mixed into one blind sample with the prompt hidden. Each candidate is rated against its question and draft answer as "useful gap", "not useful" or "unclear", with the same definition as the seed calibration (docs/research/seed-calibration.md). If one prompt has more than 60 admitted candidates, a seeded random 60 of them are rated.

## Decision rule (fixed before the run)

The candidate replaces v0.6 as the product detector only if all three hold:

1. it has at least one admitted candidate in at least half of the detections;
2. more than half of its rated candidates are useful;
3. its useful share is not more than 15 percentage points below v0.6's, when v0.6 has at least 10 rated candidates.

If 1 holds but 2 or 3 fails, the prompt is revised and measured again on the same suite. If 1 fails, the prompt is not the lever for 7B models and the next step is the model size (the release notes then say that local 7B models produce few seeds).

The rule is about the detector only. No candidate gets weight from this run: the session uses the product Gate and no evidence is submitted.

## Results

Pending.

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

Usefulness: the admitted candidates of both prompts are mixed into one blind sample with the prompt hidden. Each candidate is rated against its question and draft answer as "useful gap", "not useful" or "unclear", with the same definition as the seed calibration (docs/research/seed-calibration.md). After all shards finish, `sample` merges them and draws per prompt a seeded random sample of at most 60 admitted candidates (seed 20261024). The mixed sample and the id-to-prompt key are written to separate files; the key is decoded only after all labels are recorded. Only recurrence uses the embedder in this run, so the session uses the lexical embedder.

## Decision rule (fixed before the run)

The candidate replaces v0.6 as the product detector only if all three hold:

1. it has at least one admitted candidate in at least half of the detections;
2. more than half of its rated candidates are useful;
3. its useful share is not more than 15 percentage points below v0.6's, when v0.6 has at least 10 rated candidates.

If 1 holds but 2 or 3 fails, the prompt is revised and measured again on the same suite. If 1 fails, the prompt is not the lever for 7B models and the next step is the model size (the release notes then say that local 7B models produce few seeds).

The rule is about the detector only. No candidate gets weight from this run: the session uses the product Gate and no evidence is submitted.

## Results, run 1: candidate v0.7 (2026-10-24)

Qwen 2.5 7B Q4_K_M, 12 conversations, 96 detections, same detection cap (220 tokens) for both prompts. Run: https://github.com/E-AI-MODEL/shadowseed-pro/actions/runs/40071579894. Data: `benchmarks/detector_calibration/run1_candidate_v0.7/`.

| | v0.6 (product) | candidate v0.7 |
|---|---|---|
| detections with no admitted candidate | 84 of 96 | 0 of 96 |
| explicit NONE | 57 | 0 |
| admitted candidates | 35 | 478 |
| rated | 35 (all) | 60 (seeded sample) |
| useful / unclear / not useful | 8 / 5 / 22 | 14 / 11 / 35 |
| useful share | 23% | 23% |

The 95 labels were recorded and hashed (`e4f9cacb…`) before the key was decoded. One limitation weakens the blinding: some v0.6 output has a recognisable form ("Label: The draft … does not …").

Decision rule: 1 holds, 2 fails (23% is not more than half), 3 holds (0.4 points apart). Outcome: the prompt is revised and measured again.

What the labels show:

- Both prompts reach the same useful share on this model. With GPT-5 the v0.6 prompt reached 85% (seed calibration). On a 7B model the bottleneck is not only the prompt.
- The candidate almost always returns exactly five points. Most of the not-useful ones are generic requests for the user's situation ("the user's current portfolio", "the desired colour of the chili") that would not change the answer.
- Truncated candidates ("Thermal Performance:", "User Notification: The draft does not") come from both prompts.
- The useful ones name a concrete assumption or open number in the answer: whether the 24-hour reset-token lifetime fits, whether the 30% Dutch tax rate holds, the per-tree sequestration figure, hot holding of chili at a party.
- In absolute terms the candidate yields about 14 times more seeds at the same share, so roughly 110 useful and 370 not useful or unclear over 96 turns, against 8 and 27 for v0.6.

## Revision: candidate v0.8 (fixed before run 2)

Changes against v0.7, each aimed at a pattern in the run-1 labels:

- each point must be something that, once settled, could change what the answer recommends or concludes, and should name a specific assumption, number, case or distinction in the answer;
- general background about the user is excluded unless the recommendation clearly depends on it;
- at most three points instead of five (parsed with the same cap), and NONE is stated as an ordinary outcome instead of "answer NONE only when…";
- the format examples are tied to a claim in an answer; the run-1 example "Which budget limit the user is working within" invited the generic requests.

The design and the decision rule stay the same, including the cap of 60 rated candidates per prompt. Run 2 uses the same suite and the same rater as run 1, so a pass is weaker evidence than it would be on fresh conversations. If v0.8 passes, the product change is checked once more on conversations outside this suite before release.

## Results, run 2: candidate v0.8 (2026-10-24)

Same model, suite and cap. All eight shards of both runs used Ollama model digest `845dbda0ea48ed749caafd9e6037047aa19acfcfd82e704d7ca97d631a0b697e` (read from each job's `/api/tags` output; the Ollama version was not logged). Run: https://github.com/E-AI-MODEL/shadowseed-pro/actions/runs/40081609202. Data: `benchmarks/detector_calibration/run2_candidate_v0.8/`. Labels hashed before the key was decoded (`9b53cece…`).

| | v0.6 (product) | candidate v0.8 |
|---|---|---|
| detections with no admitted candidate | 82 of 96 | 10 of 96 |
| explicit NONE | 57 | 10 |
| admitted candidates | 42 | 258 (2.7 per detection) |
| rated | 42 (all) | 60 (seeded sample) |
| useful / unclear / not useful | 11 / 4 / 27 | 20 / 8 / 32 |
| useful share | 26% | 33% |

Decision rule: 1 holds, 2 fails (33%), 3 holds. v0.8 is not adopted.

Observations:

- v0.8 is better than v0.7 (33% against 23%) and NONE now occurs, but two thirds of its points are still not useful. The useful ones again check a number or assumption in the answer: whether 1,250 euros a month is realistic after an income loss, whether the 7% index return is an average, the rate-limit values, whether the 30-day retention covers the data-change pattern.
- Three candidates in the sample copy the template of a format example ("the 5% failure rate … older machines"). The exact-copy filter does not catch this mutated leak.
- v0.6 gave 23% in run 1 and 26% in run 2. On this model no prompt tried so far gets above a third.

## Conclusion after two runs

On Qwen 2.5 7B the detector prompt is a lever for how many seeds appear, not for how good they are: a third useful at best, against 85% for v0.6 on GPT-5. Further prompt rounds on the same suite and rater risk fitting the prompt to these labels. The product prompt stays v0.6. The next lever is the model: the same paired design on a larger local model (for example a 14B model). The limitation is recorded in the Unreleased section of `CHANGELOG.md`, so the next release notes carry it.

The workflow is now dispatch-only, so later pull requests do not start a 2.5-hour run.

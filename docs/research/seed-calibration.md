# Seed usefulness and recurrence calibration (2026-10-23)

Input: the 196 candidates from the fixed22 SSL arms (GPT-5 and GPT-6.1-sol, `current_pair` v0.6 detector), stored in `benchmarks/seed_calibration/fixed22_candidates.json`. Results are in `benchmarks/seed_calibration/results/`.

The reference labels were made by Claude, blind to model, intake verdict and similarity. They are a model's judgment, not human review, and are recorded as such.

## A. Are the seeds useful?

A seeded random sample of 60 candidates (30 per model) was rated "useful gap", "not useful" or "unclear" against the question that produced it.

- 51 useful, 6 not useful, 3 unclear. GPT-5: 29 of 30 useful. GPT-6.1-sol: 22 of 30 useful. The not-useful ones were mostly questions about the question, such as "Ambiguity of 'this kind of app'".
- The intake's lexical separator guard did not separate useful from not useful. Of the 24 candidates it rejected, 22 were useful. Example: "Possible endogeneity: whether high wages and cheap energy were antecedent causes or partly outcomes of early industrialization."

Change: English declarative candidates are admitted unless they are a bare category stack of eight words or fewer ("Security, privacy and scalability are missing."). The broader guard remains for the historical Dutch corpus. Admission on the 196 candidates goes from 99 to 189. In the sample, useful candidates rejected by the intake drop from 22 to 4.

Decision rule from #63: more than half of the candidates are useful, so the detector does not need to change before an efficacy run.

## B. Is the same gap recognized when it returns?

The admitted candidates were replayed through the product `RecurrenceClusterer` with `all-MiniLM-L6-v2` (revision `1110a243fdf4706b3f48f1d95db1a4f5529b4d41`) across thresholds (`recurrence_sweep.json`). Then 53 cross-turn pairs, stratified by similarity, were labelled "same gap" or "different" (`pair_sample.json`, `claude_pair_labels.json`).

| Threshold | Same gap recognized | Different gaps wrongly merged |
|---|---:|---:|
| 0.50 | 6 of 8 | 20 of 40 |
| 0.60 (default) | 5 of 8 | 10 of 40 |
| 0.70 | 2 of 8 | 3 of 40 |

Same-gap pairs range from 0.42 to 0.74 similarity. Different-gap pairs reach 0.72. No threshold separates them: embedding similarity measures topic overlap, not whether two candidates are the same open question. The sample is small (8 same-gap pairs) but the overlap is unambiguous.

Next: `scripts/recurrence_judge.py` asks a model the same question on the same pairs (`seed-calibration.yml`, Qwen 2.5 7B). If a model clearly beats the embedding threshold, recurrence recognition moves into the detector: it receives the open seeds of the conversation and reports "new" or "recurs: <seed id>", with similarity kept only as a floor. Recurrence stays an observation and never becomes evidence or weight.

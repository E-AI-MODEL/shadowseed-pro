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

All results below use the intake as changed in this PR (189 admitted candidates). The admitted candidates were replayed through the product `RecurrenceClusterer` with `all-MiniLM-L6-v2` (revision `1110a243fdf4706b3f48f1d95db1a4f5529b4d41`) across thresholds (`recurrence_sweep.json`). Then 56 cross-turn pairs, stratified by similarity, were labelled "same gap", "different" or "unclear" (`pair_sample.json`, `claude_pair_labels.json`). Thirteen pairs also occurred in an earlier sample drawn before the intake change and keep that label.

| Threshold | Recurring clusters (2+ turns) | Same gap recognized | Different gaps wrongly merged |
|---|---:|---:|---:|
| 0.50 | 25 | 8 of 8 | 20 of 44 |
| 0.55 | 22 | 8 of 8 | 12 of 44 |
| 0.60 (default) | 12 | 7 of 8 | 10 of 44 |
| 0.65 | 9 | 6 of 8 | 7 of 44 |
| 0.70 | 6 | 4 of 8 | 4 of 44 |

Same-gap pairs score 0.59 to 0.75. Different-gap pairs reach 0.72. At the default threshold about one in four different-gap pairs is merged. Raising the threshold removes wrong merges only by losing real recurrences. Embedding similarity measures topic overlap, not whether two candidates are the same open question. The sample is small (8 same-gap pairs), but the overlap is clear.

## Model judge

`scripts/recurrence_judge.py` asks a model "do A and B point at the same open question?" on the labelled pairs (`seed-calibration.yml`).

| Recognizer (current sample) | Same gap recognized | Different gaps wrongly merged |
|---|---:|---:|
| Embedding similarity at 0.60 | 7 of 8 | 10 of 44 |
| Qwen 2.5 7B q4_K_M (digest `845dbda0…`) | 7 of 8 | 1 of 44 |

Result file: `recurrence_judge_qwen2.5_7b.json`. Even a small local model finds the same recurrences as the embedding threshold and removes nine of its ten wrong merges. On the earlier pre-change sample, Qwen recognized 4 of 8 with 1 of 40 wrong merges. The same script runs with `--backend openai` for GPT-5 and GPT-6.1-sol, the models that produced the candidates.

Decision: ADR-012. The session model recognizes a returning gap; embedding similarity is kept as a floor and fallback. Earlier plan text follows for reference. If a model clearly beats the embedding threshold, recurrence recognition moves into the detector. The detector then receives the open seeds of the conversation and reports "new" or "recurs: <seed id>", and similarity is kept only as a floor. Recurrence stays an observation and never becomes evidence or weight.

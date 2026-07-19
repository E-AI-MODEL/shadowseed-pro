# Experiment Design

## Research Question

Does Shadow Seed Learning (SSL 4.5) improve absence detection compared to a baseline?

## Setup

Dataset:
- AbsenceBench (sample via Hugging Face)

Comparison:
- baseline (single-pass detection)
- SSL (multi-turn + validation gate)

## SSL Mechanics

Each seed:
- trace initialized at 2.0
- weight starts at 0.0
- evolves across turns

Validation Gate:
- occurrence_count ≥ 3
- evidence_count ≥ 2
- no contradiction

## Evaluation

Metrics:
- precision
- recall
- F1

Primary metric:
- ΔF1 (SSL - baseline)

## Notes

- no ground truth used during detection
- ground truth only used for validation and scoring
- no paid APIs or external models

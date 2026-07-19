# Open-set Seed Review Report

Evidence layer: `open_set_seed_quality`
Status: `review_complete`

## Overview

- packets: 56
- completed packets: 56
- invalid packets: 0
- unique seeds: 56
- fully reviewed seeds: 56
- accepted seeds: 15
- rejected seeds: 41
- mixed seeds: 0
- pending seeds: 0
- invalid seeds: 0

## Core Rates

- packet acceptance rate: 0.27
- seed acceptance rate: 0.27
- seed rejection rate: 0.73
- unanimous verdict rate: 0.00
- pairwise decision agreement rate: 0.00

## Criterion Pass Rates

- `atomicity`: 1.00
- `relevance`: 0.36
- `testability`: 0.43
- `non_triviality`: 0.27
- `follow_up_utility`: 0.27

## Reject Reasons

- `not_relevant`: 8
- `style_not_gap`: 28
- `too_vague`: 4
- `trivial`: 1

## Domain Coverage

- `wetenschap - arXiv abstract`: 56

## Follow-up

- disagreements artifact: `benchmarks/open_review/rounds/round_007/batchB/ai_review/open_set_disagreements.json`
- invalid packet rows must be fixed before this layer is treated as completed evidence
- partial reviewer completion does not count as a seed-level acceptance or rejection
- do not collapse this layer into the standard regression score

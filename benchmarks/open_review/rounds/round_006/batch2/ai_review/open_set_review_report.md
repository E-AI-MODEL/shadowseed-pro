# Open-set Seed Review Report

Evidence layer: `open_set_seed_quality`
Status: `review_complete`

## Overview

- packets: 48
- completed packets: 48
- invalid packets: 0
- unique seeds: 48
- fully reviewed seeds: 48
- accepted seeds: 22
- rejected seeds: 26
- mixed seeds: 0
- pending seeds: 0
- invalid seeds: 0

## Core Rates

- packet acceptance rate: 0.46
- seed acceptance rate: 0.46
- seed rejection rate: 0.54
- unanimous verdict rate: 0.00
- pairwise decision agreement rate: 0.00

## Criterion Pass Rates

- `atomicity`: 0.96
- `relevance`: 0.79
- `testability`: 0.73
- `non_triviality`: 0.46
- `follow_up_utility`: 0.46

## Reject Reasons

- `duplicate`: 2
- `not_relevant`: 5
- `not_testable`: 4
- `style_not_gap`: 5
- `too_broad`: 2
- `too_vague`: 4
- `trivial`: 4

## Domain Coverage

- `wetenschap - arXiv abstract`: 48

## Follow-up

- disagreements artifact: `benchmarks/open_review/rounds/round_006/batch2/ai_review/open_set_disagreements.json`
- invalid packet rows must be fixed before this layer is treated as completed evidence
- partial reviewer completion does not count as a seed-level acceptance or rejection
- do not collapse this layer into the standard regression score

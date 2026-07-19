# Open-set Seed Review Report

Evidence layer: `open_set_seed_quality`
Status: `review_complete`

## Overview

- packets: 54
- completed packets: 54
- invalid packets: 0
- unique seeds: 54
- fully reviewed seeds: 54
- accepted seeds: 18
- rejected seeds: 36
- mixed seeds: 0
- pending seeds: 0
- invalid seeds: 0

## Core Rates

- packet acceptance rate: 0.33
- seed acceptance rate: 0.33
- seed rejection rate: 0.67
- unanimous verdict rate: 0.00
- pairwise decision agreement rate: 0.00

## Criterion Pass Rates

- `atomicity`: 1.00
- `relevance`: 0.74
- `testability`: 0.59
- `non_triviality`: 0.33
- `follow_up_utility`: 0.33

## Reject Reasons

- `not_relevant`: 11
- `style_not_gap`: 3
- `too_vague`: 19
- `trivial`: 3

## Domain Coverage

- `nieuws - Business`: 5
- `nieuws - Sports`: 12
- `nieuws - World`: 37

## Follow-up

- disagreements artifact: `benchmarks/open_review/rounds/round_007/batchA/ai_review/open_set_disagreements.json`
- invalid packet rows must be fixed before this layer is treated as completed evidence
- partial reviewer completion does not count as a seed-level acceptance or rejection
- do not collapse this layer into the standard regression score

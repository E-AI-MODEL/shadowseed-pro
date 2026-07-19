# Open-set Seed Review Report

Evidence layer: `open_set_seed_quality`
Status: `review_complete`

## Overview

- packets: 58
- completed packets: 58
- invalid packets: 0
- unique seeds: 58
- fully reviewed seeds: 58
- accepted seeds: 29
- rejected seeds: 29
- mixed seeds: 0
- pending seeds: 0
- invalid seeds: 0

## Core Rates

- packet acceptance rate: 0.50
- seed acceptance rate: 0.50
- seed rejection rate: 0.50
- unanimous verdict rate: 0.00
- pairwise decision agreement rate: 0.00

## Criterion Pass Rates

- `atomicity`: 1.00
- `relevance`: 0.86
- `testability`: 0.69
- `non_triviality`: 0.50
- `follow_up_utility`: 0.50

## Reject Reasons

- `duplicate`: 3
- `not_relevant`: 4
- `not_testable`: 3
- `style_not_gap`: 4
- `too_vague`: 11
- `trivial`: 4

## Domain Coverage

- `nieuws - Business`: 4
- `nieuws - Sci/Tech`: 54

## Follow-up

- disagreements artifact: `benchmarks/open_review/rounds/round_006/batch1/ai_review/open_set_disagreements.json`
- invalid packet rows must be fixed before this layer is treated as completed evidence
- partial reviewer completion does not count as a seed-level acceptance or rejection
- do not collapse this layer into the standard regression score

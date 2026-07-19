# Open-set Seed Review Report

Evidence layer: `open_set_seed_quality`
Status: `review_complete`

## Overview

- packets: 54
- completed packets: 54
- invalid packets: 0
- unique seeds: 54
- fully reviewed seeds: 54
- accepted seeds: 10
- rejected seeds: 44
- mixed seeds: 0
- pending seeds: 0
- invalid seeds: 0

## Core Rates

- packet acceptance rate: 0.19
- seed acceptance rate: 0.19
- seed rejection rate: 0.81
- unanimous verdict rate: 0.00
- pairwise decision agreement rate: 0.00

## Criterion Pass Rates

- `atomicity`: 0.81
- `relevance`: 0.91
- `testability`: 0.30
- `non_triviality`: 0.19
- `follow_up_utility`: 0.19

## Reject Reasons

- `duplicate`: 1
- `not_relevant`: 5
- `not_testable`: 3
- `too_broad`: 10
- `too_vague`: 25

## Domain Coverage

- `nieuws - Business`: 5
- `nieuws - Sci/Tech`: 49

## Follow-up

- disagreements artifact: `benchmarks/open_review/rounds/round_005/ai_review/offset0_disagreements.json`
- invalid packet rows must be fixed before this layer is treated as completed evidence
- partial reviewer completion does not count as a seed-level acceptance or rejection
- do not collapse this layer into the standard regression score

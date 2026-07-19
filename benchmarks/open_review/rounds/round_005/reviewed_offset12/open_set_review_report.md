# Open-set Seed Review Report

Evidence layer: `open_set_seed_quality`
Status: `review_completed`

## Overview

- packets: 82
- completed packets: 82
- invalid packets: 0
- unique seeds: 41
- fully reviewed seeds: 41
- accepted seeds: 12
- rejected seeds: 29
- mixed seeds: 0
- pending seeds: 0
- invalid seeds: 0

## Core Rates

- packet acceptance rate: 0.29
- seed acceptance rate: 0.29
- seed rejection rate: 0.71
- unanimous verdict rate: 1.00
- pairwise decision agreement rate: 1.00

## Criterion Pass Rates

- `atomicity`: 0.66
- `relevance`: 0.98
- `testability`: 0.66
- `non_triviality`: 0.29
- `follow_up_utility`: 0.29

## Reject Reasons

- `duplicate`: 6
- `not_relevant`: 2
- `not_testable`: 18
- `style_not_gap`: 20
- `too_vague`: 10
- `trivial`: 2

## Domain Coverage

- `nieuws - Sci/Tech`: 41

## Follow-up

- disagreements artifact: `results/open_review/open_set_disagreements.json`
- human review is complete for reviewer_a and reviewer_b
- reviewer agreement is unanimous for this batch; no mixed seeds require adjudication
- this batch has a materially lower acceptance rate than offset 0 and should be treated as a quality warning for the model detector
- do not collapse this layer into the standard regression score

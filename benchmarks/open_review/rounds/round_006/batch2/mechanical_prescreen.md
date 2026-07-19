# Mechanische prescreen — round_006_batch2 (GEEN menselijke review)

> **Status: deterministisch hulpmiddel, geen evidence.** Deterministische prescreen, GEEN menselijke review. Telt NIET als reviewer_a/reviewer_b en niet als open_set_seed_quality (Laag C) evidence, en geeft GEEN accept/reject-verdict. Bedoeld om aandacht te richten en de v0.3e-prompt te toetsen aan haar eigen regels.

Detector: `model` · backend: `hf-transformers:microsoft/Phi-3.5-mini-instruct`

## Yield (levert het model kandidaten op?)

- items: **12** · met kandidaten: **12** · leeg: **0** (empty-rate **0.0**)
- gemiddeld kandidaten per item: **5.0**

## Kwaliteit van geleverde kandidaten (60 kandidaat-lacunes)

- clean (geen mechanische vlag): **45**
- geflagd: **15**
- clean-rate: **0.75**
- near-duplicate-rate: **0.017**

## Mechanische faalcodes

- `not_atomic`: 12
- `truncated`: 2
- `near_duplicate`: 1
- `citation_fragment`: 0
- `claim_vs_gap`: 0
- `entity_bleed`: 0
- `fewshot_leak`: 0
- `language_leak`: 0
- `parse_leak`: 0

## Niet mechanisch te checken (vraagt een lezer)

- `false_gap`, `mistranslation`, `grammar`


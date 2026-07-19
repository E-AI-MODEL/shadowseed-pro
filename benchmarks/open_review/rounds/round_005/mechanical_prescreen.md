# Mechanische prescreen — round_005 (GEEN menselijke review)

> **Status: deterministisch hulpmiddel, geen evidence.** Deterministische prescreen, GEEN menselijke review. Telt NIET als reviewer_a/reviewer_b en niet als open_set_seed_quality (Laag C) evidence, en geeft GEEN accept/reject-verdict. Bedoeld om aandacht te richten en de v0.3e-prompt te toetsen aan haar eigen regels.

Detector: `model` · backend: `hf-transformers:Qwen/Qwen2.5-3B-Instruct`

## Yield (levert het model kandidaten op?)

- items: **23** · met kandidaten: **23** · leeg: **0** (empty-rate **0.0**)
- gemiddeld kandidaten per item: **4.957**

## Kwaliteit van geleverde kandidaten (114 kandidaat-lacunes)

- clean (geen mechanische vlag): **63**
- geflagd: **51**
- clean-rate: **0.553**
- near-duplicate-rate: **0.114**

## Mechanische faalcodes

- `not_atomic`: 38
- `near_duplicate`: 13
- `parse_leak`: 10
- `truncated`: 9
- `citation_fragment`: 0
- `claim_vs_gap`: 0
- `entity_bleed`: 0
- `fewshot_leak`: 0
- `language_leak`: 0

## Niet mechanisch te checken (vraagt een lezer)

- `false_gap`, `mistranslation`, `grammar`


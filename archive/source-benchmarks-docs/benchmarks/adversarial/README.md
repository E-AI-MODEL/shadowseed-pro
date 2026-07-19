# Adversarial Workspace

Deze map is bedoeld voor de eerstvolgende harde Gate-stresstest.

## Doel

Niet alleen laten zien dat SSL weinig onzin promoot, maar dat de huidige Validation Gate beter presteert dan eenvoudiger promotieregels.

## Minimale baselinevergelijkingen

- `current_gate`
- `trace_only`
- `trace_no_contradiction_check`

## Verwachte inputvorm

- bijna-complete antwoorden
- lokkende maar irrelevante uitbreidingskansen
- stijlzwakke maar niet-gap teksten
- optioneel conflictteksten met tegenstrijdige evidencesignalen

## Verwachte artifacts

- `adversarial_candidates.json`
- `adversarial_gate_comparison.json`
- `adversarial_false_positive_log.json`
- `adversarial_casebook.md`
- `adversarial_summary.json`

## Grens

Deze laag moet de Gate echt belasten.

Dus niet:

- by construction op nul false positives uitkomen

Maar wel:

- laten zien waar de huidige Gate beter blokkeert dan simpele baselines

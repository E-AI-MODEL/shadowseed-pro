# Documentatie

Deze map houdt documentrollen bewust uit elkaar.

## 1. Huidige canonieke bron

Begin voor theorie en doelbeeld hier:

1. [Canonieke bron: SSL 4.6](00_shadow_seed_learning_4_6.md)

Dit document is leidend voor:

- de inhoudelijke definitie van SSL;
- de gewenste evaluatiekoers;
- de richting waarin de repo zich moet ontwikkelen.

Praktische regel:

> als afgeleide docs inhoudelijk botsen met `00_shadow_seed_learning_4_6.md`, dan gaat `00_` voor op theorie en doelbeeld.

## 2. Historische bron

De eerdere 4.5-specificatie blijft beschikbaar als historische referentie:

1. [Historische technische bron: SSL 4.5](legacy/00_shadow_seed_learning_4_5.md)

Gebruik die bron om de eerdere mechanische formulering terug te lezen, niet als primaire bron voor huidige repo-alignment.

## 3. Huidige research-stack

Deze documenten zijn nu de belangrijkste actuele research- en alignmentdocs.

1. [Huidige status](research/current-status.md)
2. [SWOT naar werkcategorieen](research/work-categories.md)
3. [Roadmap stabilisatie en evidence-hardening](research/roadmap-shadowseed-stabilization.md)
4. [Evaluatiematrix](research/evaluation-matrix.md)
5. [Artifact contracts](research/artifact-contracts.md)
6. [Workflow map](research/workflow-map.md)

Praktische regel:

> de research-docs vertellen wat vandaag al staat, welke bewijslagen nog gebouwd moeten worden, en hoe die lagen zichtbaar moeten blijven in code, workflows en publicatie.

## 4. Ondersteunende en oudere research-docs

Deze documenten kunnen nog nuttig zijn, maar horen niet meer tot de kleinste huidige bronstack.

1. [Scenario-onafhankelijk roadmap](research/scenario-independence-roadmap.md)
2. [Volgende implementatiefase](research/next-phase-implementation.md)
3. [Open-set en adversarial plan](research/open-set-adversarial-plan.md)
4. [Evaluation layer target architecture](research/evaluation-layer-target-architecture.md)
5. [Workflow evidence taxonomy](research/workflow-evidence-taxonomy.md)

Gebruik deze documenten als verdieping, niet als eerste bron wanneer current status, roadmap of claimgrenzen onduidelijk zijn.

## 5. Afgeleide werkdocumenten

Deze documenten helpen bij uitleg, benchmarkgebruik en dagelijkse oriëntatie.

1. [Framework](01_framework.md)
2. [Atomische seeds](02_atomic_seeds.md)
3. [Gap-Test Suite](03_gap_test_suite.md)
4. [Testplan fase 0-4](04_testplan_fase_0_4.md)
5. [Handleiding voor beoordelaars](06_handleiding_beoordelaars.md)
6. [Reproduceerbaarheid](07_reproduceerbaarheid.md)
7. [Referenties](08_referenties.md)
8. [CLI command map](CLI_COMMAND_MAP.md)
9. [Repo-overzicht](ARCHITECTURE_MAP.md)
10. [Resultaten](results.md)

## Aanbevolen leesroutes

### Route A — Huidige bronstack

Lees in deze volgorde:

1. [Canonieke bron: SSL 4.6](00_shadow_seed_learning_4_6.md)
2. [Huidige status](research/current-status.md)
3. [SWOT naar werkcategorieen](research/work-categories.md)
4. [Roadmap stabilisatie en evidence-hardening](research/roadmap-shadowseed-stabilization.md)
5. [Evaluatiematrix](research/evaluation-matrix.md)
6. [Artifact contracts](research/artifact-contracts.md)
7. [Workflow map](research/workflow-map.md)

Gebruik deze route als je wilt begrijpen:

- wat SSL inhoudelijk claimt;
- wat de repo vandaag werkelijk aantoont;
- welke issues nu preservation-, reduction-, opportunity- of risk-werk zijn;
- hoe artifacts en workflows zich tot de claimgrens verhouden.

### Route B — Dagelijks repo-gebruik

Lees in deze volgorde:

1. [Repo-overzicht](ARCHITECTURE_MAP.md)
2. [CLI command map](CLI_COMMAND_MAP.md)
3. [Benchmarks in de Wiki](wiki/Benchmarks.md)
4. [Blind Benchmark](wiki/Blind-Benchmark.md)
5. [Resultaten](results.md)

Gebruik deze route als je vooral wilt draaien, vergelijken, publiceren of benchmarkoutput interpreteren.

## Leeswijzer voor waarheidstype

| Vraag | Leidende bron |
|---|---|
| Wat is SSL inhoudelijk en waar moet het heen? | `00_shadow_seed_learning_4_6.md` |
| Waar staat de oudere 4.5-specificatie? | `legacy/00_shadow_seed_learning_4_5.md` |
| Wat bewijst de repo vandaag echt? | `research/current-status.md` |
| Hoe worden open issues en workstreams geordend? | `research/work-categories.md` |
| Wat is de huidige uitvoervolgorde van het werk? | `research/roadmap-shadowseed-stabilization.md` |
| Welke evaluatielagen moeten de hoofdclaim gaan dragen? | `research/evaluation-matrix.md` |
| Hoe worden artifacts en analyzer-inputs benoemd? | `research/artifact-contracts.md` |
| Hoe lopen workflows en publicatieroutes? | `research/workflow-map.md` |
| Welke onderdelen heeft de repo nu? | `ARCHITECTURE_MAP.md` |
| Welke commands en workflows horen bij welke laag? | `CLI_COMMAND_MAP.md` en `.github/workflows/` |

## Kernregels

> Een seed bevat precies één gap.

> Wat mechanisch werkt is nog niet automatisch wetenschappelijk bewezen.

> Regressie, kleine benchmarkvalidatie en hoofdclaim mogen niet door elkaar lopen.

## Praktisch

- Publieke benchmarkdata staat in `src/shadowseed/data/`.
- Private blinde labels horen in `benchmarks/private/` en worden niet gecommit.
- De benchmarkrunners staan in `src/shadowseed/benchmark/`.
- De CLI staat in `src/shadowseed/cli.py`.
- De standaard CI bewaakt vooral regressie en meetketenstabiliteit.
- De volgende inhoudelijke winst moet vooral komen uit open-set review, adversarial Gate-evaluatie, probe utility en domeintransfer.

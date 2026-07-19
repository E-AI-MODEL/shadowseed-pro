# Repo-overzicht

Deze pagina is de kaart van de repo.

Gebruik haar voor drie vragen:

- wat doet de repo technisch?
- welke resultaten zijn standaard?
- welke resultaten zijn aanvullend bewijs?

## Vijf banen

| Baan | Doel | Belangrijkste plekken | Status |
|---|---|---|---|
| Core SSL | seeds opslaan, laten uitdoven, valideren en eventueel promoten | `src/shadowseed/manager.py`, `src/shadowseed/vectorstore/`, `src/shadowseed/ssot.py` | prototype, getest |
| Standaard meetketen | regressie, smoke en kleine benchmarks draaien | `src/shadowseed/benchmark/`, `tests/`, `.github/workflows/tests.yml` | standaard |
| Aanvullende evidencelagen | open-set, adversarial, probe utility en later transfer zichtbaar maken | `src/shadowseed/evaluation/`, `benchmarks/open_review/`, `benchmarks/adversarial/`, `benchmarks/transfer/` | deels operationeel |
| Rapportage | artifacts samenvatten tot een begrijpelijk rapport | `src/shadowseed/analysis/ssl45_result_analyzer.py` | automatisch |
| Publicatie | verhaal en resultaten delen | `verhaal.html` (standalone), wiki-resultaten via `publish-test-results.yml` (zonder Pages) en `publish-wiki.yml` | automatisch |

## Evaluatielagen

De map `src/shadowseed/evaluation/` is de eerste ordeningsstap richting de 4.6-laagindeling.

Ze bevat nu deze laagmappen:

- `regression/`
- `open_review/`
- `adversarial/`
- `behavioral/`
- `transfer/`

Belangrijk: deze mappen veranderen nog geen gedrag. De bestaande uitvoerende code leeft voorlopig grotendeels in `src/shadowseed/benchmark/`. De laagmappen leggen vast welke bewijssoort eigenaar is van bestaande en toekomstige evaluatielogica.

## De hoofdroute

```text
push naar main
  -> Checks en benchmark-resultaten
  -> artifacts uploaden
  -> Publiceer testresultaten naar Wiki en Pages
  -> results/latest + results/artifacts als workflow-snapshot
  -> Wiki + Pages + workflow-artifact
```

De publicatieroute is bedoeld voor buitenstaanders.
Daarom moet ze niet alleen artifacts tonen, maar ook uitleggen wat die artifacts zijn.

## Welke standaardruns staan in de hoofdroute?

| Run | Vraag | Bewijssoort |
|---|---|---|
| 01 Codecheck | werkt de Python-code? | regressie |
| 02 Gap Finder | vindt SSL bekende ontbrekende punten? | kleine benchmark |
| 03 Rustig blijven | voegt SSL geen onzin toe? | regressie / beperkte ruiscontrole |
| 04 Antwoordwinst | wordt een antwoord completer door SSL? | kleine benchmark |
| 05 Model smoke | werkt de modelroute technisch? | technische smoke |
| 06 Blind test | blijven labels verborgen tot scoring? | methodologische smoke |
| 06b Adversarial Gate | blokkeert de Gate misleidende lure-seeds? | aanvullende evidencelaag |
| 06c Probe utility | helpen promoted seeds bij scherpere vervolgacties? | aanvullende evidencelaag |
| 07 Rapport | hoe ziet de samenvatting eruit? | rapportage |
| 08 AbsenceBench rooktest | werkt de lokale dataset-run? | technische smoke |
| 09 Herhalingstest | wat gebeurt er bij meer rondes? | gevoeligheid / regressie |

## Wat is standaard en wat niet?

### Standaardpublicatie

Dit hoort vandaag bij de standaardpublicatie:

- regressieruns;
- smoke-runs;
- kleine benchmarkruns;
- aanvullende evidencelagen voor adversarial Gate en probe utility.

### Handmatige of optionele routes

Deze routes zijn nuttig, maar horen niet automatisch bij elke standaardpublicatie:

- open-set review via Hugging Face intake;
- retrieval- en vectorstoreruns;
- complete vector + SSOT runs.

## Bevestigde handmatige workflows

De actuele repo bevat in elk geval deze handmatige workflows:

- `Open-set HF review batch`
- `Vectorstore Smoke Run`
- `Complete Vector + SSOT Run`
- `Publiceer testresultaten naar Wiki en Pages` via `workflow_dispatch`

## Waarom deze scheiding belangrijk is

De repo probeert twee fouten tegelijk te vermijden:

- alles opblazen tot een te grote claim;
- extra bewijs verstoppen alsof alleen regressie telt.

Daarom gebruikt de repo nu bewust drie lagen in de publieke presentatie:

1. basis werkt nog
2. kleine benchmark geeft richting
3. aanvullende evidencelaag laat extra inhoudelijk gedrag zien

## Waar bezoekers meestal moeten beginnen

- `README.md`
- `docs/wiki/Home.md`
- `Latest-Test-Results` in de wiki
- `SSL-45-Analysis` in de wiki
- `site/` voor GitHub Pages

## Korte samenvatting

De repo is vandaag het best te begrijpen als een werkende SSL-harness met een publieke standaardpublicatie die mechanische stabiliteit, kleine benchmarksignalen en eerste aanvullende evidencelagen naast elkaar laat zien zonder ze als hetzelfde bewijs te presenteren.

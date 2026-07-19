# Shadow Seed Learning

[![checks](https://github.com/E-AI-MODEL/shadowseed/actions/workflows/tests.yml/badge.svg)](https://github.com/E-AI-MODEL/shadowseed/actions/workflows/tests.yml)
![Python](https://img.shields.io/badge/python-3.10%2B-blue)
![Status](https://img.shields.io/badge/status-research%20prototype-orange)

Shadow Seed Learning (SSL) is in de kern een **afdwingbare, auditeerbare geheugendiscipline**: een waargenomen ontbrekend punt (een *shadow seed*) begint gewichtloos, en invloed moet **verdiend en verantwoord** worden — via de Validation Gate, en in de agent-laag (`shadowseed chat`, `shadowseed_agent`) op het gebruiksmoment herbevestigd door het contract, met een replaybare audit-trail en falsificatie als eersteklas operatie. Gevonden is nooit automatisch waar of sturend. De benchmark-routes toetsen de Gate-discipline; de contract-check op het gebruiksmoment is de agent-laag.

Daarbovenop stelt de research-harness een simpele maar strenge vraag:

> kan een model beter verder werken als het niet alleen kijkt naar wat er staat, maar ook naar wat structureel ontbreekt?

Zie `docs/research/positioning-synthese.md` voor waarom de discipline — en niet antwoordwinst — de voorgrond is.

## In 30 seconden

- **Wat:** SSL laat een model opsporen wat structureel *ontbreekt* of onderbelicht blijft (gevonden seeds zijn relevant, maar kunnen triviaal of weinig toetsbaar zijn — laag C), bewaart dat als een gewichtloze shadow seed, en laat alleen Gate-gevalideerde seeds meesturen in vervolgactie of antwoordruimte — in de agent-laag bovendien contract-gecheckt op het gebruiksmoment.
- **Hoe:** elke seed heeft twee velden — `trace` (aanwezigheid, vervalt via TTL en leeft op via TrTL) en `weight` (invloed, start op `0.0` en stijgt alléén via de Validation Gate). Gewichtloos tot bewezen.
- **Status:** werkende research-harness. De kern (het cross-turn mechanisme: een gevalideerde seed verrijkt een later antwoord) is bevestigd op veilige instellingen en blind getoetst over vier rondes en twee modellen. De uitkomst leest op twee assen: head-to-head ongeveer gelijkspel tegen hetzelfde model op z'n best, en in ~69% van alle blinde oordelen (57/83, rounds 022–031) hielp de seed het antwoord vooruit — het sterkst bij sterke fit; de discipline-hertest (round 031) legde herhaald duwen van matig passende seeds bloot als open vraag (zie `docs/research/ssl-integrale-evaluatie.md`). De brede claim blijft bewust begrensd.

> Kernregel: één seed = één klein, toetsbaar ontbrekend punt.

## Canonieke en historische bron

Gebruik deze regel voor documentatie:

- `docs/00_shadow_seed_learning_4_6.md` is de huidige canonieke bron voor theorie, evaluatiekoers en repo-alignment.
- `docs/legacy/00_shadow_seed_learning_4_5.md` blijft beschikbaar als historische technische referentie voor de eerdere 4.5-specificatie.

Dat betekent:

- 4.6 vertelt waar de repo inhoudelijk heen moet;
- 4.5 blijft leesbaar, maar is niet meer de primaire bron voor huidige alignment-beslissingen.

## Wat de repo vandaag bewijst (lagen A–G)

SSL hanteert één laag-taal voor bewijs, gelijk aan `docs/00_shadow_seed_learning_4_6.md` en `src/shadowseed/benchmark/evidence_layers.py`. De lagen worden bewust gescheiden gehouden — er is géén totaalscore.

| Laag | Vraag | Status vandaag |
|---|---|---|
| **A** Regressie | Blijft de kernmechaniek werken? | **Sterk** — snelle CI-ruggengraat |
| **B** Kleine benchmark | Werkt SSL op vaste, controleerbare casussen? | **Bruikbaar** — bewust smal |
| **C** Open-set seedkwaliteit | Goede seeds op onbekende tekst, zonder ground truth? | **Eerste evidence, gemengd** — relevantie hoog, trivialiteit/testability blijft risico |
| **D** Adversarial Gate | Weert de Gate misleidende gaps? | **Eerste echte evidence** — kleine maar duidelijke stresstest |
| **E** Probe utility / payoff | Leveren promoted seeds betere vervolgstappen of antwoordruimte op? | **Cross-turn mechanisme vuurt; use-time discipline gedraaid en blind getoetst (round 023: overeenstemming ~0.67, ruis vrijwel weg; seed-effect 20/30 "helpt", winnaar-as ≤0.5)** |
| **F** Domein- en taaktransfer | Werkt dezelfde doctrine buiten de bekende domeinen? | **Voorzichtig positief (round 025, 2 blinde reviewers): consensus-SSL 4/7 (alle valkuilvragen), seed-effect 14/14 "helpt", ruis 0. Replicatie op gpt-4o (round 029, voorlopige consensus van 2 reviewers; alleen r1-sheet gecommit): winnaar-as 0.50, seed-effect 6/9 "helpt" — begrensd op de winnaar-as, voorlopig over twee modellen bevestigd op de seed-effect-as** |
| **G** Modelintern | Steun in interne activaties? | **Zes iteraties doorlopen (rounds 026–030): dialectische falsificatie + activatie-sonde met gpt-4.1-oordeel → drie schone nulls, incl. NL-getraind model met 24 cases en vloer 0.002 (round 030); geen interne steun aangetoond op kleine modellen (≤124M)** |

De standaard workflow (`Checks en benchmark-resultaten`) publiceert de regressie- en kleine-benchmarklagen plus aanvullende evidencelagen. Manual OpenAI-runs via `Research · SSL Benefit (OpenAI)` kunnen zwaardere payoff- en `ssl-session` artifacts maken, inclusief blind A/B-reviewpack voor cross-turn sessies.

## Het cross-turn mechanisme (de kern, in gewone taal)

Het hart van SSL is dat een seed uit een eerdere gespreksbeurt een later antwoord mag verrijken — maar pas nadat hij door de Gate is gevalideerd en op het gebruiksmoment opnieuw is gecontroleerd. Dat mechanisme is bevestigd op veilige instellingen. (In oudere documenten heet dit werkpakket "W9f"; die code betekent verder niets.)

De kernclaim is bewust smal. Niet: SSL maakt elk antwoord beter of verslaat een frontier-model. Wel:

> SSL kan een opgemerkt gemis gewichtloos vasthouden, later valideren, en daardoor antwoordruimte openen die er anders niet was.

De blinde A/B-reviews zijn de kwaliteitscontrole daarop. De uitkomst leest op twee assen (zie de lagen-tabel hierboven en `docs/research/ssl-integrale-evaluatie.md`): head-to-head is het ongeveer gelijkspel tegen hetzelfde model op z'n best, maar in ~69% van alle blinde oordelen (rounds 022–031) zeggen reviewers dat de seed het antwoord vooruit hielp. De leercurve is zichtbaar én eerlijk: gespleten start (022), discipline bracht overeenstemming en nul ruis (023, 025), replicatie op een tweede model (029), en de hertest (031) legde een nieuwe, gelokaliseerde zwakte bloot: een matig passende seed die op late beurten herhaald blijft duwen.

Verdieping: `docs/research/w9f-evaluatieconclusie.md` (historische naamgeving) en `benchmarks/open_review/rounds/`.

## Wat de resultaten wel en niet betekenen

Wat je voorzichtig wel mag zeggen:

- SSL heeft een reproduceerbare mechanische kern.
- De repo bewaakt `trace`, `weight`, TTL, TrTL, status lifecycle en Gate-gedrag.
- De repo kan meten of bekende gaps gevonden worden.
- De Gate heeft eerste echte adversarial evidence.
- Probe-feedback heeft eerste behavioral evidence.
- Het cross-turn mechanisme toont dat eerder opgemerkte, gevalideerde seeds bruikbare extra antwoordruimte kunnen openen.

Wat je nog niet breed moet zeggen:

- dat SSL algemeen bewezen beter presteert op open-ended modeltaken;
- dat SSL elk antwoord verbetert;
- dat elke promoted seed waardevol is;
- dat fixture-smokes gelijk staan aan echte modelvalidatie;
- dat de huidige lagen samen al volledige scenario-onafhankelijke eindvalidatie vormen.

## Snelstart

```bash
pip install -e ".[test]"
pytest
shadowseed run-gap-suite
shadowseed run-false-positive-suite
shadowseed run-benefit-suite
shadowseed run-blind-benchmark --labels benchmarks/private/blind_suite_labels.json
shadowseed run-adversarial-gate-benchmark
shadowseed run-probe-utility-benchmark
shadowseed analyze-results
```

## Live schaduwlaag: `shadowseed chat`

De levende schaduw-geheugenlaag (visie-item 5) heeft nu een operationele demo:

```bash
shadowseed chat --backend fixture
```

Een seed wordt gewichtloos geboren, reist mee in de schaduw, promoveert via de
Validation Gate en mag pas daarna een later antwoord sturen — met het
`shadowseed_agent`-contract live op de invloedgrens en een replaybare
audit-trail (`/shadow`, `/audit`, `/falsify <id>`). Dit is een applicatiedemo
op de gevalideerde mechaniek, geen nieuwe bewijslaag; zie
`docs/research/shadow-chat-demo.md`.

## Hugging Face token

Voor publieke HF dataset-intake is niet altijd een token nodig.
Voor gated of strengere HF-routes gebruikt de repo nu een optioneel secretpatroon via environment variables.

Lokaal:

1. kopieer `.env.example` naar `.env`
2. zet daar je echte token in
3. exporteer `HUGGINGFACE_TOKEN` in je shell of laad `.env` lokaal

In GitHub Actions:

- gebruik de repository secret `HUGGINGFACE_TOKEN`
- start daarna handmatig de workflow `Open-set HF review batch` voor intake en review-packets

Belangrijk:

- commit nooit een echte token;
- zet geen tokens in JSON-bestanden of code;
- gebruik in GitHub Actions een repository secret met de naam `HUGGINGFACE_TOKEN`.

## Belangrijkste documenten

Huidige bron- en researchstack:

- `docs/ssl-het-verhaal.md` — het hele verhaal voor een breed publiek: herkomst, filosofie, bewijs en pad vooruit
- `docs/00_shadow_seed_learning_4_6.md`
- `docs/research/current-status.md`
- `docs/research/ssl-integrale-evaluatie.md`
- `docs/research/w9f-evaluatieconclusie.md`
- `docs/research/w9f-review-artifacts.md`
- `docs/research/positioning-synthese.md`
- `docs/research/scenario-independence-roadmap.md`
- `docs/research/evaluation-matrix.md`
- `docs/research/work-categories.md`
- `docs/research/roadmap-shadowseed-stabilization.md`
- `docs/research/artifact-contracts.md`
- `docs/research/workflow-map.md`

Technische repo-oriëntatie:

- `docs/ARCHITECTURE_MAP.md`
- `docs/CLI_COMMAND_MAP.md`
- `docs/README.md`

Historische referentie:

- `docs/legacy/00_shadow_seed_learning_4_5.md`

## Meer lezen

- `docs/ssl-het-verhaal.md` — het hele verhaal: herkomst, filosofie, wetenschap, bewijs en pad vooruit
- [`verhaal.html`](verhaal.html) — hetzelfde verhaal als losse, interactieve pagina: download het bestand en open het in je browser (werkt offline, alles zit erin)
- [GitHub Wiki Home](https://github.com/E-AI-MODEL/shadowseed/wiki) — uitgebreide uitleg en achtergrond
- [Latest Test Results](https://github.com/E-AI-MODEL/shadowseed/wiki/Latest-Test-Results)
- [SSL 4.5 Analysis](https://github.com/E-AI-MODEL/shadowseed/wiki/SSL-45-Analysis)

## Kernregel

> Een seed bevat precies een klein, toetsbaar ontbrekend punt.

Dat is de reden dat SSL complex kan worden zonder vaag te worden: het systeem probeert niet "meer context" toe te voegen, maar een heel specifiek gemis veilig vast te leggen, te toetsen en pas daarna mee te laten wegen.

# Huidige Status van SSL-validatie

> Status: current
> Date: 2026-06-30
> Evidence layer: status snapshot across layers A-G
> Source: 4.6 evidence model in `docs/00_shadow_seed_learning_4_6.md`
>
> **Update 2026-07-04 (sindsdien gelanceerd, zie de gelinkte docs):** use-time
> discipline blind getoetst (round 023: overeenstemming ~0.67, ruis vrijwel
> weg, win-rate ≤0.5); **W10 doctrine-transfer heeft een eerste voorzichtig
> positief blind verdict** (round 025: consensus-SSL 4/7 incl. alle
> valkuilvragen, ruis 0; n=7, één model); positioneringsbesluit doorgevoerd
> (`positioning-synthese.md`, issue #46 gesloten); levende schaduwlaag +
> SSL→RAG-brug operationeel (`shadow-chat-demo.md`); **Laag G doorlopen tot een
> eerste inhoudelijke meting** (dialectische falsificatie + activatie-sonde;
> gpt-4.1 als oordeelbron gaf een schoon nulresultaat, rounds 026–028,
> `laag-g-scoping.md`). De snapshot hieronder beschrijft de stand per
> 2026-06-30.
>
> **Update 2026-07-07:** W10-replicatie op gpt-4o gedraaid en blind gereviewd
> — inmiddels een **voorlopig consensus-verdict** (2 onafhankelijke blinde
> reviewers; onder provenance-voorbehoud omdat alleen r1's sheet als CSV is
> gecommit, zie `round_029/human_review/r2_concurrence.md`) — en alle
> payoff-conclusies herwogen op **twee assen**: de
> winnaar-as (A/B head-to-head, win-rate ≤0.5 — een artefact van het
> reviewformaat, nooit hoofdmetriek) naast de **seed-effect-as** ("helpt de
> seed naar een beter antwoord?"): ~75% "helpt" over alle gecommitte
> beoordelingen (52/69, rounds 022–029); de zeldzame ruis zit vóór de
> use-time discipline (022) en in vroege-beurt off-topic-sturing die de
> huidige cap niet uitsluit (029, t04). Zie `ssl-integrale-evaluatie.md`,
> sectie "Twee assen". **Laag G iteratie 6 (round 030) is gedraaid:** de
> activatie-sonde op het NL-getrainde GroNLP/gpt2-small-dutch met 24 cases
> (gpt-4.1-oordeel: 6 HOUDT_STAND / 17 WEERLEGD; vloer 0.002) gaf de derde
> schone null (sterkste laag p 0.2056) — geen lineair leesbaar
> houdbaarheidsoordeel in kleine modellen, ook niet NL-getraind. **De
> vroege-beurt-discipline is gebouwd én blind hertest** (round 031, 2
> reviewers, beide sheets gecommit): de vooraf vastgelegde leesregel werd
> NIET gehaald — vroege ruis weg, maar dezelfde matig passende seed bleef op
> late beurten duwen (seed-effect 5/14 helpt, overeenstemming 0.43). De
> teltabel staat nu op 57/83 (~69%) "helpt" over rounds 022–031; de open
> disciplinevraag is seed-herhaling over beurten (cooldown-kandidaat).

## Doel van dit document

Dit document maakt expliciet wat de repository vandaag werkelijk aantoont, wat gedeeltelijk is afgedekt, en wat nog onderzoekswerk is.

De kernregel blijft:

> wat mechanisch werkt is nog niet automatisch een brede algemene claim.

Maar de status is sinds de eerdere 2026-05/06-snapshots verschoven. Vooral W9f heeft de cross-turn SSL-levenscyclus uit de sfeer van alleen belofte gehaald en als technische baseline vastgezet.

## Korte samenvatting

De repo staat sterk voor:

- de mechanische SSL-kern (`trace`, `weight`, TTL, TrTL, status lifecycle, Validation Gate);
- regressie en kleine benchmarkvalidatie;
- adversarial Gate-evaluatie als eerste echte ruiscontrole;
- probe-feedback lifecycle als eerste behavioral bewijs;
- cross-turn context-discovery en memory-surfacing via W9f.

De repo staat nog niet sterk genoeg voor:

- een brede claim dat SSL elk antwoord verbetert;
- algemene domein-onafhankelijkheid;
- volledige productmatige betrouwbaarheid van automatisch seed-gebruik;
- modelinterne validatie.

De belangrijkste statuswijziging:

> Het W9f cross-turn *mechanisme* is bevestigd op veilige drempels (recurrence → Gate → surfacing vuurt reproduceerbaar). De *payoff-kwaliteit* is echter een baseline-kandidaat, niet afgesloten: de eerste blinde review op veilige drempels kwam gespleten terug (round 022). De volgende stap is daarom tweeledig — use-time seed-discipline (potentieel-vs-must) én doctrine-transfer (W10) — niet nog meer bewijs dat het mechanisme bestaat.

Zie ook `docs/research/w9f-evaluatieconclusie.md` en `benchmarks/open_review/rounds/round_022/human_review/`.

## Statusoverzicht per laag

| Laag | Vraag | Status per 2026-06-30 | Korte duiding |
|---|---|---|---|
| A — Regressie | Blijft de kernmechaniek werken? | **Sterk** | CI, manager-tests, lifecycle-tests en benchmark-smokes bewaken de kern. |
| B — Kleine benchmarkvalidatie | Werkt SSL op vaste, controleerbare casussen? | **Bruikbaar** | Geschikt als regressie en beperkte benchmark, niet als eindclaim. |
| C — Open-set seedkwaliteit | Maakt SSL goede seeds zonder vaste ground truth? | **Eerste echte evidence, gemengd** | Menselijke en gedelegeerde reviews tonen relevantie, maar ook trivialiteit/testability-risico. |
| D — Adversarial ruiscontrole | Weert de Gate misleidende gaps? | **Eerste echte evidence** | Gate presteert sterk op kleine adversarial set; bredere stress blijft wenselijk. |
| E — Probe utility / payoff | Leveren promoted seeds nuttige vervolgstappen of antwoorden op? | **Positief voor W9f cross-turn; deels open voor productgebruik** | W9f toont cross-turn payoff; seed-vernauwing blijft foutklasse. |
| F — Domeintransfer | Werkt dezelfde doctrine buiten bekende scenario's? | **Volgende stap** | W10 moet transfer van de levenscyclus meten, niet opnieuw W9f bewijzen. |
| G — Modelintern | Is er interne modelsteun voor extern gemeten afwezigheid? | **Onderzoekslaag** | Niet nodig voor de huidige engineering-baseline. |

## Mechanische kern

De minimale SSL-definitie is technisch aanwezig en wordt bewaakt:

- een seed moet atomisch zijn;
- brede of samengestelde seeds kunnen worden geweigerd of gesplitst;
- `trace` en `weight` zijn formeel gescheiden;
- `trace` bewaart aanwezigheid;
- `weight` start op `0.0` en meet pas na promotie invloed;
- TTL laat onherkende seeds vervallen;
- TrTL houdt seeds levend wanneer nieuwe context ze herkent;
- EXPIRED is terminaal;
- promotie loopt via de Validation Gate.

Dit is het verschil tussen een los benchmarkidee en een reproduceerbare kernarchitectuur.

## Open-set seedkwaliteit

De open-set lijn heeft echte signalen opgeleverd, maar blijft inhoudelijk gemengd.

Belangrijke stand:

- round 005 offset-12 gaf de eerste mensgereviewde Laag-C evidence: relevantie hoog, maar acceptance laag door trivialiteit, vaagheid en toetsbaarheidsproblemen;
- latere gedelegeerde AI-review en modelruns bevestigden dat sterkere modelpaden de vorm kunnen verbeteren, maar niet automatisch de volledige substantieclaim dragen;
- human-vs-AI agreement was bruikbaar genoeg om gedelegeerde reviews als proxy te gebruiken, mits duidelijk gelabeld.

Conclusie:

> Open-set detectie is niet leeg, maar ook niet definitief opgelost. De waarschuwing is niet dat SSL niets vindt, maar dat gevonden seeds vaak relevant maar te triviaal of te weinig toetsbaar kunnen zijn.

## Adversarial Gate en veiligheid

De adversarial Gate-lijn toont dat veiligheid vóór antwoordgeneratie moet zitten.

Belangrijke stand:

- de Gate is sterker dan trace-only-achtige baselines op de huidige adversarial fixture;
- slechte of irrelevante seeds kunnen een sterk model nog steeds richting ruis sturen wanneer ze de revisie halen;
- een capabel model is een redelijke backstop tegen valse feiten, maar niet tegen irrelevante seed-injectie;
- daarom blijft `weight = 0` tot Gate-promotie een kernonderdeel van de doctrine.

Conclusie:

> De Gate/weightless-filtering is geen formaliteit, maar de veiligheidslaag die antwoordruis moet voorkomen.

## Probe utility en payoff

De payoff-lijn heeft drie belangrijke lessen opgeleverd:

1. handelen op geldige seeds kan antwoorden verbeteren;
2. kleine of zwakke modellen kunnen derailen in de revisiestap;
3. capabele modellen kunnen seeds vloeiend gebruiken zonder unsupported additions, mits de prompt en do-no-harm-regel goed staan.

De semantische coverage- en human-review-lijnen tonen dat lexicale coverage te grof was: goed geïntegreerde seeds worden vaak geparafraseerd en moeten semantisch of menselijk beoordeeld worden.

## W9f cross-turn baseline

W9f is de belangrijkste recente statuswijziging.

De eerdere W1/W5 single-shot resultaten lieten zien dat een frontiermodel vaak zelf veel frames of gaps kan noemen. Dat zette SSL als externe single-shot detector onder druk.

W9f verschuift de claim terug naar SSL's eigen sterke mechanisme:

> wat nu nog geen antwoord is, kan later in de sessie antwoordruimte worden.

W9f operationaliseert dit via:

- echte `SSLManager`-lifecycle;
- weightless seeds;
- recurrence;
- Gate-promotie;
- TTL/TrTL;
- cluster-based recurrence voor parafrastische herhaling;
- representative-based promotie in plaats van clusterbrede overpromotie;
- blind A/B-review-pack als kwaliteitscontrole.

### W9f-follow-up baseline

De follow-up baseline na PR #148 corrigeerde twee belangrijke punten:

- centroid-weging en recurrence-telling zijn gescheiden;
- representatives blijven levend wanneer recurrence via non-representative members binnenkomt.

De release `w9f-follow-up-baseline` bevriest deze stand.

De laatste review-artifact met blind A/B-pack bevatte 8 cross-turn payoff items, met gebalanceerde A/B-toewijzing:

- `CONV_STARTUP`: 4 review-items;
- `CONV_CITY`: 4 review-items;
- `CONV_IR_SHORT`: 0 review-items;
- SSL als A: 4;
- SSL als B: 4.

### Interpretatie van de blind review

De blind review moet niet worden gelezen als klassieke model-vs-model benchmark.

Zonder SSL zouden de SSL-gestuurde antwoordvarianten niet als optie hebben bestaan. De review beoordeelt dus of door SSL geopende antwoordruimte bruikbaar is, niet of GPT-4.1 in abstracto wordt verslagen.

De review (round 022, 8 cross-turn items, twee reviewers, veilige drempels) liet zien:

- **geen consensus**: de twee reviewers kozen op 7/8 items een andere winnaar (overeenstemming 1/8);
- de SSL/seed-variant werd door Reviewer A 1/8 en door Reviewer B 8/8 geprefereerd — vrijwel perfecte inversie;
- `CONV_CITY` was het meest gepolariseerd (Reviewer A seed 0/4, Reviewer B 4/4), niet het sterkste positieve signaal;
- het enige consensus-item was het meest concrete (operationaliserende seed); waar de seed breedte toevoegde, splitste het oordeel;
- de gemarkeerde ruis zat in *gevalideerde, promoted* seeds — een use-time-discipline-vraag, geen bewijs dat de levenscyclus niet werkt.

Zie `benchmarks/open_review/rounds/round_022/human_review/`.

### W9f-besluit

Het W9f cross-turn *mechanisme* is bevestigd op veilige drempels; de *payoff-kwaliteit* is een baseline-kandidaat, niet afgesloten (round 022 kwam gespleten terug).

Er komt geen nieuwe recurrence/promotion-tuning om te bewijzen dat het mechanisme bestaat — dat vuurt. De openstaande stap is use-time seed-discipline: wanneer mag een promoted seed het antwoord sturen?

## Wat de repo vandaag hard aantoont

De repo toont vandaag overtuigend aan dat:

1. de SSL-levenscyclus technisch aanwezig is;
2. `trace` en `weight` gescheiden blijven;
3. TTL/TrTL reactivatie en verval operationeel maken;
4. de Gate sterker is dan zwakkere promotieregels op de huidige adversarial set;
5. probe-feedback lifecycle-effecten heeft;
6. handelen op geldige seeds bij capabele modellen antwoordruimte kan verbeteren;
7. cross-turn surfaced seeds in W9f extra antwoordruimte openen die de history-baseline niet zelf opwerpt (de *kwaliteit* daarvan is reviewer-afhankelijk — round 022).

## Wat de repo niet moet claimen

Niet claimen:

- SSL maakt elk antwoord beter;
- SSL verslaat GPT-4.1 algemeen;
- elke promoted seed is waardevol;
- open-set seedkwaliteit is volledig opgelost;
- scenario-onafhankelijkheid is al hard bewezen;
- modelinterne validatie is operationeel.

## Praktische betekenis voor repo-beslissingen

De repo moet vanaf hier drie dingen doen:

1. de regressie- en lifecyclelaag behouden;
2. het W9f-*mechanisme* niet opnieuw bewijzen (dat vuurt), maar de payoff-*discipline* aanpakken: wanneer mag een promoted seed sturen;
3. de volgende onderzoeksstap richten op use-time seed-discipline én transfer van de doctrine.

Dat betekent concreet:

- scenario-suites blijven nuttig als regressie;
- blind A/B blijft nuttig als kwaliteitscontrole op antwoordruimte;
- seed-vernauwing en seed-ruis moeten expliciet als foutklasse blijven staan;
- W10 moet meten of dezelfde lifecycle buiten de huidige scenario's werkt.

## Aanbevolen volgende documenten

Leidend na deze update:

- `docs/00_shadow_seed_learning_4_6.md` — canonieke theorie;
- `docs/research/w9f-evaluatieconclusie.md` — W9f-besluit;
- `docs/research/evaluation-matrix.md` — laagstatus;
- `docs/research/scenario-independence-roadmap.md` — overgang naar transfer.

## Korte eindkwalificatie

De repo is vandaag:

> een sterke SSL-researchharness met bewezen lifecycle-mechaniek, eerste echte open-set en adversarial evidence, en een bevestigd W9f cross-turn *mechanisme* op veilige drempels. De W9f-*payoff* is een baseline-kandidaat — de eerste blinde review op veilige drempels kwam gespleten terug (round 022). De brede claim blijft begrensd: de volgende stap is use-time seed-discipline (potentieel-vs-must) én doctrine-transfer (W10), niet nog meer bewijs dat het mechanisme bestaat.

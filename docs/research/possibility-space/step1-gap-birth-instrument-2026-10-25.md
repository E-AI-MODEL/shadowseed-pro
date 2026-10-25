# Stap 1: meetinstrument rond de bestaande Shadowseed-pijplijn

> **25 oktober 2026. Status: offline instrumentatie, géén modelonderzoek.**
> Sluit aan op [de uitgebreide stap-1-bronnenanalyse](step1-model-signals-gap-origin-2026-10-25.md), [het bewijsregister](step1-evidence-register-2026-10-25.md) en [de H-Neurons-methodestudie](step1-h-neurons-method-crosswalk-2026-10-25.md). De [oorspronkelijke Q1/Q2-these](../possibility-space-thesis.md) blijft ongewijzigd.
>
> Geen betaalde calls, geen H-neuronenmeting, geen gekalibreerde detectorvergelijking. Synthetische tekst is geen modelgedrag.

## Wat is gebouwd?

De [offline meetmodule](../../../research/src/shadowseed_research/benchmark/step1_gap_birth_instrument.py) gebruikt een echte **ShadowChatSession**, in live modus met blijvende SSLManager, maar zonder toegang tot een extern model. Het eerste antwoord en de detectoruitvoer komen uit de [duidelijk synthetische fixture](../../../research/fixtures/step1_gap_birth_recorded_v0.json).

Er is geen nieuwe detector geschreven. De recorder gebruikt rechtstreeks de productmethode **OpenAIDetectorBackend.detect_seeds**, maar injecteert een lokaal, vooraf vastgelegd transport, zonder het OpenAI-clientobject of HTTP op te starten. Zo worden dezelfde originele promptopbouw, nummerparser, parserdiagnostiek en de bijzondere generative-v0.4-nummerprefill gebruikt.

De sessie doorloopt de echte productmethoden: **prepare_turn → vastgelegd hostantwoord → observe_turn → kandidaatobservaties → normalisatie → atomiciteit → deduplicatie → gewichtloze seedgeboorte**. Ook de standaard **clustergebaseerde recurrence** blijft actief. De generatieve modelbeoordelaar voor recurrence wordt in deze fixture niet gebruikt, omdat er geen echt model wordt aangeroepen.

Twee gescheiden sessies gebruiken exact dezelfde fictieve antwoorden, maar verschillende vooraf geschreven detectoruitvoer. Dit is GEEN meting van welk model of welke detector beter is:
- **current_pair v0.6** onderzoekt vraag, eerste antwoord en maximaal vier begrensde, schone eerdere turns. Expliciet NONE betekent geen kandidaat.
- **generative v0.4** onderzoekt niet-gekozen verklaringsrichtingen. Een lege continuatie is niet automatisch een expliciete abstentie, en de historische vooringevulde nummering wordt behouden.

## Meetpunten

| Stap | Wat wordt gelogd | Wat niet is aangetoond |
| --- | --- | --- |
| Eerste generatie | Vastgelegde vraag en antwoord met expliciete onderzoeksherkomst | Geen echte modelgeneratie of representatieonderzoek |
| Detectie-input | Originele productprompt, SHA-256 en werkelijk begrensde schone context | Geen bewijs van intern verborgen relaties |
| Ruwe detectie | Exacte uitvoer, afzonderlijke ruwe regels en volledige parsercounters | Niet elke regel heeft een afzonderlijk parserafwijslabel |
| Parser | Parsed candidates; onderscheid tussen expliciet NONE, leeg en niet parsebaar | Geen onafhankelijke kandidaatvaliditeit |
| Intake | Genormaliseerde kandidaten, toegelaten en afgewezen kandidaten met redenen | Toegelaten is niet automatisch relevant, nieuw of waar |
| Geboorte | Originele seed-ID, status, trace, weight, evidence_count, occurrence_count en herkomst; met snapshots vóór voorbereiding, na het TTL-/TrTL-voorbereidingspad en na observe_turn | Nul gewicht is geen wetenschappelijk resultaat; terugkeer hoeft het totale traceverval niet te overtreffen |
| Tijdsverloop | Dezelfde manager over vier turns, eventlog en seedstatus vóór/na | Nog geen getoetste meerturnswaarde of groei |

De ruwe parseroutput blijft inspecteerbaar. De huidige parser geeft niet voor iedere individuele weggefilterde regel een afzonderlijke inhoudelijke reden. Het instrument verzint die informatie niet.

## Vaste mechanische controles

De vier fictieve turns toetsen:
- Twee onderzoekbare kandidaten en een gekopieerd few-shot-voorbeeld, dat de originele parser moet wegfilteren.
- Een ongerelateerde kantinevraag met expliciet NONE in current_pair, tegenover lege oudere generative-uitvoer. Die uitkomsten mogen niet gelijk worden behandeld.
- De terugkeer van dezelfde kandidaat in een latere beurt, zodat de bestaande manager een herhaling kan verwerken zonder automatisch gewicht of evidentie toe te kennen.
- Een niet-genummerde detectoruitvoer die een parserfout/ongebruikte output zichtbaar moet maken, geen bewuste NONE.

De ingebouwde lexicale embedding is uitsluitend offline testgereedschap. Echte semantische kwaliteit moet later met een geschikt model en onafhankelijke beoordeling worden vastgesteld.

## Offline uitvoeren

Na de bestaande ontwikkelinstallatie, in de hoofdmap van de repo:

    uv sync --locked --extra test
    uv pip install --python .venv/bin/python --no-deps -e ./research
    uv run --no-sync python -m pytest -q research/tests/test_step1_gap_birth_instrument.py
    uv run --no-sync python -m shadowseed_research.benchmark.step1_gap_birth_instrument --fixture research/fixtures/step1_gap_birth_recorded_v0.json --output /tmp/step1-gap-birth-audit.json

Het JSON-resultaat bevat de fixture-hash, twee sessies, vier turns per sessie, nul modelcalls, nul externe embeddingcalls, prompt- en contexthashes, ruwe kandidaten, parser- en intakebesluiten en alle gewichtloze seedstatussen. Het claimveld is nadrukkelijk FALSE.

De Research Package CI en reguliere productcontroles moeten groen worden. CI groen bewijst slechts dat het instrument technisch werkt.

## Wat pas in de volgende echte modelstudie mag worden getoetst

De volgende stap moet nieuwe, geblindeerde en onafhankelijk beoordeelde gevallen gebruiken. Uitkomsten voor één sterk, gepind model moeten worden vergeleken met herhaald gewoon genereren, current_pair, generative, doelbewust alternatieven zoeken, semantische variatie en detectie zonder het oorspronkelijke antwoord. Kosten, bronnen, tooltoegang, sampling, context en fouten worden per arm gelogd.

Zelfs zo'n vergelijking bewijst geen interne modelrepresentaties. Een H-Neurons-achtige test vereist een aparte open-weight activatiestudie. De vraag of één seed later werkelijk andere onderzoekbaarheid mogelijk maakt, blijft een aparte Q2-studie met blijvende seedstaat en onafhankelijke controlegebeurtenissen.

**Besluit:** een inspecteerbaar instrument voor het begin van de bestaande pijplijn. Geen vervangende architectuur, geen andere Gate, geen TTL-/TrTL-/weight-aanpassing en geen nieuw modelresultaat.

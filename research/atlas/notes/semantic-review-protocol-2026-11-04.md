# Beoordeel de negen historische woordovereenkomsten op betekenis

**Werkprotocol, 4 november 2026. Status: voorbereid, niet beoordeeld.** Dit document is geen bewijs dat ShadowSeed latere onderzoeksvragen verandert. Er zijn in deze opdracht geen nieuwe modelantwoorden gegenereerd.

## Aanleiding en grenzen

[De bestaande 94-kandidatenanalyse in PR #283](https://github.com/E-AI-MODEL/shadowseed-pro/pull/283) volgt 94 detectorwaarnemingen (48 geaccepteerd, 46 als `not_atomic` afgewezen) door 140 latere beurtvensters. De strenge automatische screening vond negen vensters uit acht kandidaatvoorkomens met een zeldzaam aangrenzend woordstampaar. De negen vensters zijn **zoekresultaten**, geen negen inhoudelijke bevestigingen. De 48 oorspronkelijke hostbeurten ontvingen geen opgeslagen seed-context, hadden geen Gate-promoties en geen invloedbesluiten. Een latere woordovereenkomst in deze data kan dus geen aangetoond effect van het aanbieden van een opgeslagen kandidaat zijn.

De originele bron met SHA-256 `0a5094e38ab2fdcf8c68dc8d6a3c75d29eeffd49e1f6c8e138589ed73ca36bbf` staat onder `research/datasets/2026-10-28-q1q2-48/`. Het eerdere auteursdossier met de negen exacte reviewregels en alle 140 vensters is **niet in deze PR opgenomen**. Het label AUTHOR-ONLY op de afzonderlijke oude reviewbijlage is geen feitelijke toegangsbeveiliging: de oorspronkelijke detector- en hostteksten zijn al in openbare Git-geschiedenis opgeslagen. Verander die situatie niet door de teksten opnieuw te publiceren. De eerdere blindingsindeling van het 48-call-archief is openbaar; voor deze nieuwe beoordeling is een nieuwe toewijzing nodig.

## Wat de inhoudelijke toets precies uitzoekt

Bekijk steeds een kandidaat op het moment waarop hij ontstond en het oorspronkelijke, latere modelantwoord. Onderscheid vier vragen:

1. **Tekst:** zijn dezelfde woorden aanwezig, of is de woordoverlap toevallig, generiek of door het filter ontstaan?
2. **Betekenis:** verwijzen de passages daadwerkelijk naar dezelfde hypothese, een inhoudelijk verwante maar andere hypothese, of naar iets anders?
3. **Onderzoekshandeling:** bevat het latere antwoord een uitvoerbare andere toets, met een benoemde observatie en een uitkomst die de hypothese kan weerleggen? Is die toets nieuw ten opzichte van wat al in de bekende context stond?
4. **Herkomst:** was die toets al in de oorspronkelijke gebruikersvraag, het hostantwoord bij de kandidaatvorming of de latere prompt aanwezig? Noem een latere herhaling niet `nieuw` omdat zij lexicaal afwijkt.

Een oordeel over **betekenis** is geen oordeel over **causale invloed**. In de historische run werd geen kandidaat teruggegeven aan de host. De afzonderlijke vraag naar een *effect van het aanbieden of bewaren* van een kandidaat vereist een nieuwe gecontroleerde proef.

## Beoordelingsset, vooraf op te bouwen

- Neem alle **negen** vensters die de strenge woordpaarregel raken, inclusief de twee vensters die bij hetzelfde kandidaatvoorkomen horen. Bewaar `candidate_observation_id`, `session_id`, oorspronkelijke beurt, latere beurt, en hashes uitsluitend in een afgescheiden sleutelbestand.
- Kies voor ieder treffervenster **één controlevenster zonder treffend woordpaar**, bij voorkeur uit dezelfde modelsessie en met zo klein mogelijk verschil in latere beurt. Documenteer vooraf wanneer zo'n match niet bestaat. Kies controles niet op aantrekkelijke inhoudelijke uitkomst.
- Voeg **minstens twee generieke-woordoverlap-negatieven** toe uit de brede 24 treffervensters die niet door de strenge regel komen, als die aan de bronselectie voldoen. Leg de selectie reproduceerbaar vast. Gebruik geen nieuwe, verzonnen modelantwoorden.
- Houd gekoppelde vensters uit één kandidaatgeboorte bij de analyse bij elkaar. Negen vensters zijn niet negen onafhankelijke kandidaten. De 12 sessies en zes casussen zijn evenmin onafhankelijke experimenten.
- Toon de beoordelaar alle context die nodig is om `nieuw` te kunnen bepalen, maar **niet** het screeninglabel, `accepted`/`not_atomic`, het modeltype, de arm of het gewenste onderzoeksresultaat. Randomiseer de volgorde van records. Door dezelfde publieke bron kan volledige blindering niet worden gegarandeerd; laat de beoordelaar vooraf aangeven of de dataset bekend is.
- Leg vóór de eerste beoordeling de definitieve selectie, loting, uitsluitingen en de bijbehorende hashes vast. Houd de mapping gescheiden van de scorebladen. Publiceer geen persoonlijke gegevens, providergeheimen of vertrouwelijke testinformatie.

## Invulvelden voor iedere review

Gebruik één regel per venster en per beoordelaar met deze velden:

| Veld | Toegestane waarde |
| --- | --- |
| `blind_id` | Nieuwe willekeurige referentie; geen herleidbare arm-/modelnaam |
| `reviewer_id` | Afgesproken pseudoniem |
| `relation` | `SAME_CLAIM`, `RELATED_DISTINCT`, `LEXICAL_ONLY`, `NO_CLEAR_LINK`, `UNCERTAIN` |
| `new_test` | `YES`, `NO`, `UNCERTAIN` |
| `test_question` | Letterlijke onderzoeksvraag, of leeg bij `NO` |
| `observable` | Welke nieuwe waarneming zou de vraag toetsen? |
| `falsifier` | Welke mogelijke uitkomst zou de vraag verzwakken of weerleggen? |
| `already_in_context` | `YES`, `NO`, `UNCERTAIN` |
| `reason` | Korte reden met verwijzing naar de getoonde passages |
| `confidence` | `LOW`, `MEDIUM`, `HIGH` |

De beoordelaar mag `UNCERTAIN` kiezen. Dwing geen inhoudelijk verband of nieuwe proef af. Een interessant voorstel van de beoordelaar is geen oorspronkelijk modelresultaat; sla het op als afzonderlijk **reviewer-voorstel**, nooit als later ontstaan modelantwoord.

## Oordelen en controles

Laat bij voorkeur twee inhoudelijk deskundige mensen de set afzonderlijk beoordelen, zonder de labels van de ander te zien. Anonimiteit mag behouden blijven; noteer wel afzonderlijk datum, relevante expertise, mogelijke voorkennis en precies welke materialen zij ontvingen. Eén eigen beoordeling kan alvast een verkennende lezing zijn, **niet** de vereiste onafhankelijke replicatie.

Ontgrendel de selectie pas na ontvangst van de ingevulde bladen. Rapporteer de volledige verwarringsmatrix en verschillen tussen beoordelaars; zet `UNCERTAIN` niet stilzwijgend om naar `NO`. Rapporteer alle negen treffervensters en alle controles, ook lege en negatieve uitkomsten. Vergelijk de verdeling van inhoudelijke overeenkomsten tussen gevonden treffers en controles, **zonder causale effectclaim** of onnauwkeurige p-waarden op deze kleine, afhankelijke set.

Controleer na ontblinding afzonderlijk hoeveel kandidaten onder de oude `not_atomic`-filter zijn verdwenen. Dat kan aanwijzingen geven over verloren opslagkansen; het toont op zichzelf geen gemiste onderzoekswinst.

## Beslissing na deze ronde

- **Alleen letterlijke of generieke overlap:** documenteer de negatieve bevinding en verbeter zo nodig het automatische screeningsinstrument. Geen geheugenvoordeel claimen.
- **Werkelijke inhoudelijke relaties zonder nieuwe toets:** bewaar deze als beschrijvende observaties; test eventuele suggesties in een afzonderlijke proef.
- **Eén of meer inhoudelijk andere en toetsbare vragen:** gebruik die als kandidaat-casussen voor een vooraf vastgelegde A/B-proef met het *zelfde model en dezelfde begininformatie*, gewone historie/notities, gerichte zoekarm, kandidaatarm, en specifieke kandidaatablatie. Beoordeel ook afleiding en vernauwing zoals in ronde 031.
- **Verschillende beoordelaars of ontbrekende context:** rapporteer `onbeslist`, herzie de beoordelingsvraag en behoud alle bronrecords.

Voor een nieuwe betaalde modelrun geldt afzonderlijke toestemming met kostenplafond, handmatige start en gegevenscontrole. De G0-beperking geldt voor bevestigende Q1/Q2-claims en studies, niet als algemene stop op dit verkennende werk. Geen productie-Gate- of ADR-wijziging op grond van dit protocol.

## Werkelijke status

**In dit document uitgevoerd:** onderzoeksopzet en beoordelingsvelden vastgelegd op een aparte onderzoeksbranch. **Niet uitgevoerd:** selectie en vastpinnen van de exacte negen ruwe reviewregels in deze PR, nieuwe willekeurige toewijzing, menselijke beoordeling, vergelijkende modelproef, onafhankelijke Q1/Q2-confirmatie. De bestaande Atlas-, PR- en bronbestanden blijven ongewijzigd.



## Herhaalbare woordcontrole in dezelfde onderzoeksbranch

Het bestand [`inspect_lexical_windows.py`](../scripts/inspect_lexical_windows.py) berekent een **aparte** letterlijke screening op de oorspronkelijke JSON. Het gebruikt een expliciete stopwoordenlijst en maakt zesletterwoordstammen. Het vergelijkt kandidaatteksten met latere modelantwoorden, sluit woordparen uit die al in de eerdere vraag of het eerdere antwoord staan, en sluit ook woordparen uit die de latere gebruiker zelf aanlevert.

Deze methode is niet aantoonbaar byte-voor-byte gelijk aan de oorspronkelijke privé-analyse van PR #283. Een eerste afzonderlijke doorlezing van de bron met vergelijkbare regels vond **10** vensters uit **8** kandidaatwaarnemingen (7 oorspronkelijk geaccepteerd, 3 afgewezen), tegenover **9** vensters uit **8** kandidaten (7/2) in PR #283. De afwijking kan door tokenisatie, stopwoorden of een ander selectiedetail komen. **Nog geen correctie van de historische telling:** reconstrueer eerst de exacte oorspronkelijke zoekregel en controleer het verschil op observation-ID en beurt. Tot dat moment zijn beide uitkomsten methodegebonden.

Voor een lokale controle vanuit de repository:

```bash
python research/atlas/scripts/inspect_lexical_windows.py research/datasets/2026-10-28-q1q2-48/original-author-kit/SOURCE/original-observed_sha256_0a5094e3.json
python -m pytest -q tests/test_research_atlas_lexical_window_screen.py
```

Het script controleert vóór verwerking de volledige SHA-256 van de originele bron en geeft **geen kandidaat-, gebruikers-, hostteksten of woordstamparen** uit, maar uitsluitend technische bron-ID's, beurtnummers, de gecontroleerde bestandshash en aantallen. Een andere lokale bron wordt geweigerd. De output is nog geen beoordelingsset: `intake_outcome` staat in het technische overzicht en hoort **niet** bij de geblindeerde beoordelaar terecht te komen. De kleine scriptproeven zijn lokaal uitgevoerd tijdens de eerdere ontwikkelstap. Nu zijn ook exact tien vensters, acht kandidaat-ID's, de verwachte acceptatieverdeling en een foutgeval met veranderde bron in tests vastgelegd. Deze nieuw toegevoegde regressies moeten nog door GitHub-CI op de huidige commit worden uitgevoerd. Deze paragraaf is een eigen technische controle, geen onafhankelijke menselijke beoordeling.

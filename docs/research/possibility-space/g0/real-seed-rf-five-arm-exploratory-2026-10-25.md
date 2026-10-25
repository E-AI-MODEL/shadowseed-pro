# Verkennende Q1/Q2-proef: echte seed en vijf onderzoekscondities

> **25 oktober 2026. Status: onderzoeksopzet, nog GEEN uitvoeringsresultaat. G0 NOT PASSED.** De oorspronkelijke [tweedelige onderzoeksvraag](../../possibility-space-thesis.md) blijft ongewijzigd. Deze proef is een **RF-fixed-feedback verkenning**, geen bevestigende Q1/Q2-proef en geen RI-proef met een uitvoerende wereld.

## Wat deze proef wel toevoegt

We testen nu niet opnieuw of er technisch een seed kan blijven bestaan. Dat is al in [PR #249](https://github.com/E-AI-MODEL/shadowseed-pro/pull/249) gecontroleerd. Nieuw is dat een **werkelijk in de canonieke Engine geboren, eerst geaccepteerde seed** in een **aparte onderzoeksvraagtaak** aan een krachtig model wordt aangeboden. De gewone host ziet die seed nooit en blijft beschermd door de bestaande Gate en point-of-use.

De onderzoeksvraag: formuleert het model later aantoonbaar **andere onderzoeksvragen** met zo'n specifieke, eerder niet-gekozen kandidaat dan zonder die kandidaat, met gewone notities, of met bewuste alternatievenzoektocht? Een verschil alleen is geen bewezen oorzaak of wetenschappelijke meerwaarde.

## Chronologie, niet één grote prompt

- **T0 vooraf:** twee gewone GPT-5-antwoorden op een vooraf geschreven fictieve meetcasus, vóór detector of seed. Slechts twee samples: geen betrouwbare schatting van een onderliggende kansverdeling.
- **T0 gewone host:** de echte GPT-5 genereert een gewoon derde antwoord. De host krijgt de oorspronkelijke casus. De bestaande `current_pair` detector krijgt via `ShadowseedEngine.prepare_turn` dezelfde oorspronkelijke feiten plus dat antwoord. De bestaande parser, intake, eventledger en `freeze_canonical_weightless_birth` bepalen of een nieuwe seed werkelijk is ontstaan. Selectie **vooraf vastgelegd: de eerste canoniek geaccepteerde nieuwe seed**, nooit de mooiste achteraf. Bij `NONE` of alleen afwijzingen: géén vervangende nepseed.
- **T0 gewone notities:** een aparte GPT-5-aanroep vat alleen bestaande feiten samen. Die notitie is de gewone geheugenkandidaat voor conditie C. Hij krijgt de bewaarde seed niet.
- **T1:** pas nu komt de eerste vooraf geschreven externe waarneming beschikbaar. Het hostmodel antwoordt gewoon, de echte detector draait opnieuw en de bestaande seed krijgt een controleerbare checkpoint. Daarna ontstaat vijfmaal een *apart modelantwoord* met één door het model geformuleerde onderzoeksvraag.
- **T2:** een tweede, onafhankelijke vooraf geschreven externe waarneming. We herhalen gewone host, bestaande detector, echte shadow-checkpoint en vijf **nieuwe modelaanroepen**. Iedere conditie mag alleen zijn eigen T1-onderzoeksvraag meenemen. Er is geen onafhankelijk resultaat van die vraag beschikbaar en geen ingreep uitgevoerd.

Host en detector krijgen steeds dezelfde actuele broncasus. Het eerdere v1-contextverschil wordt niet herhaald. Alle ruwe teksten, NONE, parsefouten, providerstatus, complete en onvoltooide modelaanroepen en kandidaatbesluiten blijven behouden.

## Vijf vergelijkingscondities

| Conditie | Extra onderzoeksinvoer bij T1/T2 | Wat dit kan ontkrachten |
| --- | --- | --- |
| **A** gewoon | Geen bewaarde notitie | Gewone generatie vindt dezelfde vragen |
| **B** bewust verkennen | Geen seed, maar expliciete alternatieven-/tegenvoorbeeldenzoektocht | Doelbewuste gewone modelredenering volstaat |
| **C** gewone notities | Los van Shadowseed bij T0 gemaakte feitennotitie | Gewoon extern geheugen volstaat |
| **D** werkelijke shadow-seed | Exacte eerste T0-seed, behoud via één echte Engine over turns, weight/evidence 0 | De specifieke bewaarde mogelijkheid beïnvloedt onderzoeksvragen |
| **E** kandidaatablatie met sham | Zelfde route als D, maar een vooraf vastgelegde irrelevante administratieve notitie | Extra invoer of een willekeurige notitie verklaart D |

Dit zijn **onderzoeksvraagcondities**, niet vijf nieuwe productimplementaties. D/E gebruiken geen nieuwe Gate. Sham, C en D zijn inhoudelijk niet exact even lang of even informatief. Ook verschillen de contextkosten, omdat de detector voor D extra modelcalls nodig heeft. Daarom is **geen zuivere kosten-gelijke effectschatting** mogelijk. Alle feitelijke model-/tokenkosten worden apart gelogd. Een volgende proef moet de ongelijkheden oplossen.

## Wat RF werkelijk meet

De latere waarnemingen zijn voor alle armen gelijk, **niet** door een van de armen uitgelokt. De modelvragen zijn echte afzonderlijke Responses-aanroepen, maar het experiment voert die vragen **niet** uit. Een algemene onafhankelijke evaluator of geblindeerde menselijke beoordelaar is nog niet aan het werk. De reviewuitvoer heeft de expliciete status **niet beoordeeld**. Alleen de T1/T2-vragen worden vastgelegd, zonder automatische semantische score.

Een eventueel verschil tussen D en E wijst hoogstens op een *kandidaatafhankelijk gedragseffect* onder deze promptinstellingen. Het bewijst niet dat de vraag relevant is, dat zij nieuw is, dat de seed intern als latente gedachte bestond of dat een nieuwe onderzoekbare mogelijkheid is ontstaan.

## Grenzen, uitval en kosten

- **API-model:** `gpt-5` via Responses, `text-embedding-3-small` voor echte engine-embeddings. Maximaal **24 modelaanroepen**, **48 embeddings**, **110.000 providergerapporteerde tokens**, en **4.096 uitvoertokens per modelcall**. Gepland: 19 modelaanroepen met één MEASUREMENT-casus. Geen automatische retries. Geen gegarandeerde eurogrens, wel begrensde aanvragen en tokens.
- Uitval bij `incomplete` wordt expliciet als uitval opgeslagen; dat is niet hetzelfde als `NONE`. Tussentijds opgeslagen ruwe observaties blijven behouden, zodat een onvoltooide uitvoering niet als nulresultaat verschijnt.
- Eén apart vrijgegeven research-Action, geheim uit de bestaande `OpenAI key` GitHub-omgeving; geen sleutel in code of logs.
- Geen productiecode- of Gatewijzigingen, geen positieve weight, SSOT-aanpassingen, nieuwe TTL/TrTL-parameter, tweede onderzoeksmemory of ongeautoriseerde gewone antwoordinvloed.
- Hergebruikte, publiek bekende meetcasus: **geen verborgen holdout**. Het ongeteste steriele geval blijft een wezenlijke tekortkoming van deze beperkte eerste verkenning.
- De aparte lijn over interne H-Neuron-achtige activaties is hier **niet** uitgevoerd. Deze proef zegt niets over de modelinterne oorsprong van de kandidaat.

## Beslisregels voor de eerstvolgende stap

**Technisch bruikbaar** alleen wanneer een echte seedgeboorte mét exacte lineage op T0 is vastgelegd, iedere volgende turn een geldige checkpoint heeft, de gewone antwoorden niet door seeds worden beïnvloed en de vijf feitelijke afzonderlijke onderzoeksvraagresponses bij T1 én T2 zijn opgeslagen.

**Stop als inhoudelijke Q2-claim:** geen onafhankelijke test van de vragen, geen causaal onderscheid boven een sterke kostengelijke baseline, promptverschillen, mislukte output, alleen parafrases, of een model dat gewoon een bij T0 al zichtbare optie herhaalt. Een goede technische run mag desondanks worden opgeslagen voor verder methodisch werk.

Dit is een **voorbereidende verkenning**. Voor een bevestigende proef blijven de openstaande onafhankelijke G0-v3-review, onafhankelijke evaluator, nieuwe holdouts, echte RI-test en kosten-gelijke A/B/C/D/E-vergelijking vereist.

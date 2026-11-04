# Welke ShadowSeed-kandidaten kwamen later terug?

**Onderzoeksnotitie, 4 november 2026.** Dit is een historische, brongebonden herlezing. Er zijn geen nieuwe modelaanroepen of onafhankelijke inhoudelijke beoordelingen uitgevoerd.

De oorspronkelijke 12 gesprekken, met elk vier beurten, bevatten **94 detectorwaarnemingen**. De oude intake liet er 48 toe en wees 46 af als `not_atomic`. Alle 94 zijn aan hun oorspronkelijke observatie, beurt en teksthash gekoppeld; de 46 afwijzingen zijn bovendien vergeleken met de afzonderlijke auteur-audit.

Die oorspronkelijke gegevens geven samen **140 latere beurtvensters**. Voor 16 kandidaten van de laatste beurt bestaat geen vervolg in de bron, wat geen mislukte herinnering is. De sessies gebruiken zes fictieve casussen met twee verschillende modellen en zijn niet onafhankelijk.

## Wat we daadwerkelijk terugvonden

| Letterlijke zoekregel | Toegelaten kandidaten: 62 latere vensters | Afgewezen kandidaten: 78 latere vensters |
| --- | ---: | ---: |
| Volledige kandidaattekst herhaald in een later hostantwoord | 0 | 0 |
| Dezelfde kandidaattekst later opnieuw gedetecteerd | 0 | 0 |
| Minstens één inhoudswoordstam, afwezig bij de geboorte en in de latere gebruikersprompt | 27 | 42 |
| Twee weinig voorkomende woordstammen in één later antwoord onder die voorwaarden | 11 | 13 |
| Een weinig voorkomend, opeenvolgend woordpaar onder die voorwaarden | **7** | **2** |

De brede regel met twee losse woordstammen vond 24 vensters. Een striktere regel met een opeenvolgend woordpaar vond er **9**, afkomstig van **8 kandidaatvoorkomens**. Die strengere regel is niet automatisch inhoudelijk betrouwbaar: bij een deel van de treffers gaat het om algemene formuleringen en niet om een bijzondere onderzoeksvraag. Geen van deze gevallen is onafhankelijk beoordeeld op betekenis of bruikbaarheid.

De oorspronkelijke hostantwoorden kregen **nul** van de kandidaten terug als seed-context. De opgeslagen uitvoer bevat ook **nul invloedbesluiten en nul Gate-promoties**. In alle 48 beurten bleef het gewone hostantwoord gelijk aan het vastgelegde antwoord. De gevonden woordovereenkomsten kunnen in deze bronrun dus niet zijn veroorzaakt door een opnieuw aangeboden ShadowSeed-kandidaat.

Dat is de interessante waarneming: een inhoudelijk onderwerp kan in een later antwoord terugkomen **zonder enige blootstelling aan het opgeslagen seed-record**. De studie meet niet of de opslag later ook iets toevoegt.

## Hoe is gezocht?

De originele bron is op SHA-256 gecontroleerd: `0a5094e38ab2fdcf8c68dc8d6a3c75d29eeffd49e1f6c8e138589ed73ca36bbf`. De aparte auteur-audit met 46 afgewezen teksten is eveneens op de oorspronkelijke bestanden gecontroleerd: `b2eb0b64a981612ee3ea3f1d5e2723d834c46eecf9eab73b697229a80a03f051`.

Voor de tekstscreening zijn woorden genormaliseerd en teruggebracht tot zesletterstammen. Woorden uit de huidige gebruikersprompt en het hostantwoord bij kandidaatvorming tellen niet als nieuwe vondst. Voor een 'niet expliciet opnieuw genoemde' overeenkomst mag het woord of woordpaar ook niet in de latere gebruikersprompt staan. Een zeldzaam woordpaar verschijnt in maximaal drie van de 94 kandidaatteksten. Het exacte woordenfilter en alle 140 controles staan in het afzonderlijke auteur-dossier.

**Dit is een letterlijke screening, geen semantische toets.** Het wegfilteren van stopwoorden kan twee woorden zelfs kunstmatig naast elkaar plaatsen. De 24 en 9 treffers zijn daarom controlepunten voor menselijke herlezing, geen geverifieerde nieuwe mogelijkheden. De 48 aangenomen en 46 afgewezen teksten zijn ook niet willekeurig verdeeld. Een percentageverschil zegt niets over een effect van intake of geheugen.

De modellen leverden verschillende aantallen kandidaten: GPT-5 leverde 72 waarnemingen en 108 latere vensters; GPT-6 Luna 22 waarnemingen en 32 vensters. Ook dit is geen gecontroleerde modelvergelijking.

## Waar zijn de oorspronkelijke teksten?

In de [28-oktoberbronverzameling](../../datasets/2026-10-28-q1q2-48/README.md) en de [replay van PR #262](https://github.com/E-AI-MODEL/shadowseed-pro/blob/feature/pro-weightless-unresolved-birth-20261028/docs/research/possibility-space/pro262-actual-source-frozen-replay-2026-10-28.md) staan de historische context en herkomst. De oorspronkelijke 46-kandidaten-bijlage heeft de aanduiding **AUTHOR-ONLY, do not publish**.

De brongetrouwe beoordeling per kandidaat is daarom apart aan de auteur geleverd en **niet** in deze openbare PR opgenomen. Dat dossier bevat de 94 exacte kandidaatteksten, alle 140 latere antwoordvensters, bronhashes, het offline analysescript en negen oningevulde beoordelingsformulieren. De publiek leesbare [aggregaten](../data/seed_recurrence_94_aggregate_2026-11-04.json) zijn gebaseerd op die private bron; zonder toegang tot die bron kan een externe lezer de telling niet zelfstandig volledig reproduceren.

## Voorgestelde volgende proef, nog niet uitgevoerd

Een nieuwe, geautoriseerde proef moet hetzelfde model, dezelfde begininformatie en hetzelfde toegestane budget aanhouden, met geblindeerde beoordeling van afzonderlijke onderzoeksvoorstellen. Vergelijk minimaal: geen aangeboden kandidaat; één keer dezelfde kandidaat; dezelfde kandidaat herhaald; gewone blijvende aantekening; en een even lange irrelevante aantekening. Kijk niet alleen naar 'nieuwe woorden' of welke arm wint, maar ook naar **een uitvoerbare andere toets, geen toevoeging en hinder door afleiding of vernauwing**.

Een prompt met een kandidaat is nog geen bewijs van geheugenwerking. Voor een mechanistische ShadowSeed-vraag moeten ook de werkelijke `prepare_turn`/`observe_turn`-toestanden, de toegestane contextoverdracht en de identiteit van de getoonde kandidaat worden vastgelegd. De eerdere [negatieve hertest uit ronde 031](https://github.com/E-AI-MODEL/shadowseed-pro/blob/main/benchmarks/open_review/rounds/round_031/human_review/RESULTS.md) is een reden om herhaald aanbieden nadrukkelijk op mogelijke hinder te beoordelen.

Er zijn geen nieuwe providerkosten gemaakt. Voor een nieuwe betaalde verkenning zijn afzonderlijke toestemming, een kostenplafond en veilige gegevensverwerking nodig. G0 blijft niet aangenomen voor bevestigende Q1/Q2-claims; voor bevestigend onderzoek blijven onafhankelijke G0-beoordelingen vereist.

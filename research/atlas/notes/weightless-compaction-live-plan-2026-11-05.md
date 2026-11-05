# ShadowSeed: gewichtloos geheugen bij echte contextcompressie

5 november 2026, **voor de live-run vastgelegd**. Verkennend: twee fictieve casussen, geen personen, geen geheime gegevens.

## De precieze vraag
Worden oude, door de echte ShadowSeed-engine als onbewezen bewaarde mogelijkheden bij een echte contextovergang opnieuw onderzoekbaar, zonder dat we ze als feiten of instructies in het gewone modelantwoord laten meedoen?

## Gelijke uitgangssituatie en scheiding
Voor ieder van twee casussen maakt GPT-6.1 Sol drie opeenvolgende zichtbare antwoorden. De oorspronkelijke gebruikersvraag en elk antwoord worden in exact dezelfde volgorde aan de echte `ShadowseedEngine.prepare_turn` / `observe_turn` doorgegeven. De canonieke `current_pair`-detector gebruikt GPT-4.1 en OpenAI text-embedding-3-small; de canonieke parser en seed-intake blijven ongewijzigd. `gate_policy_id=evidence_backed` voorkomt dat modelherhaling op eigen kracht bevoegdheid geeft.

Alle seeds beginnen en blijven gewicht 0, bewijs 0. We controleren vóór iedere hostbeurt dat geen seed is meegestuurd. Het onderzoekstraject bewaart na de derde beurt dezelfde oorspronkelijke hostgeschiedenis voor alle vervolgroutes. Een enkele echte `client.responses.compact`-aanroep van die geschiedenis levert een servergegenereerde, grotendeels onleesbare compaction-toestand. Diezelfde toestand wordt in alle gecomprimeerde varianten gebruikt. Niets wordt door ons in het compaction-item gewijzigd.

## Zes voorwaarden per casus
We leggen dezelfde nieuwe vraag voor in twee contextvormen: `full` en `provider_compacted`. Onder iedere contextvorm voeren we drie onafhankelijke stateless vervolgaanroepen uit: `regular`, `reflect` en `weightless_review`. De laatste variant krijgt uitsluitend voor een **afzonderlijke, fictieve onderzoekstaak** de door de engine bewaarde gewichtloze seeds te zien. Geen seed mag hierdoor automatisch productbevoegdheid krijgen. Reflectie krijgt een extra zoekopdracht zonder seeds.

De volgorde van de zes vervolgvarianten is deterministisch gehusseld. Iedere call heeft dezelfde hostmodelversie, dezelfde oorspronkelijke geschiedenis in zijn contextgroep, dezelfde systeeminstructie en dezelfde nieuwe gebruikersinformatie. Er is geen onderlinge gespreksstate, maar condities verschillen bewust in promptlengte en kandidaatinhoud.

## Wat zou onze hypothese verzwakken?
- De normale gecomprimeerde conditie vindt dezelfde specifieke bruikbare mogelijkheden als de weightless-conditie.
- De reflectiecontrole komt op vergelijkbare mogelijkheden.
- Weightless-herbeoordeling levert vooral generieke of irrelevante suggesties op.
- De echte compressie produceert geen compactieobject of is anders niet op gelijke wijze terug te spelen. In dat geval is de proef technisch mislukt en mogen we geen effectclaim formuleren.

## Exact meetbaar
Originele prompts en antwoorden, provider-ID, gebruikstokens, kostenraming, ruwe door de detector gevonden kandidaten, na iedere beurt seedstatus, Gate-autoriteit 0, gebruikte compaction-output met hash, en twaalf vervolgaanroepen. Compaction is technisch waarneembaar als object maar inhoudelijk niet ontleedbaar; we kunnen dus niet beweren wat de provider heeft weggegooid.

**Belangrijke grenzen:** twee casussen zonder onafhankelijke menselijke beoordeling; geen gemeten verandering van getrainde modelgewichten; geen interne verborgen redeneringen of volledige tokenwaarschijnlijkheidsverdeling. Dit is een proef met afzonderlijke, openbare onderzoeksoutput. Productieve invloed op het normale modelantwoord blijft uitgeschakeld.

**Uitvoering:** bestaande GitHub Environment `OpenAI key` met `secrets.OPENAI_KEY`. Eénmalige run; maximaal geraamd $0,50 (softwarestop vóór volgende aanvraag, geen retries). Geen productiecodewijziging en geen push naar `main`. Eerdere experimenten behouden.

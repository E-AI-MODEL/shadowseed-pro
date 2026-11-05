# Matched memory vs. weightless: onderzoeksopzet van 5 november 2026

**Vastgelegd vóór de eerste betaalde aanroep.**

We willen vaststellen of de status van een zelfstandig ontstane, onbewezen mogelijkheid op het moment van contextcompressie leidt tot andere vervolgen. Het oude experiment verschilde op meerdere punten in het aantal tokens en de informatie die het model kreeg. Nu krijgt het model in twee vergelijkingsarmen **precies dezelfde drie door ShadowSeed gevonden kandidaatteksten**.

## Onafhankelijke gevallen en gezamenlijke uitgangspositie

Vier nieuwe fictieve gesprekken met verschillende onderwerpen (koeltransport, museumcampagne, regenwaterbassins, leesclub), telkens drie hostbeurten. Elk geval heeft een afzonderlijke hostgesprekshistorie, een eigen `ShadowseedEngine`, een eigen detector en eigen providercompactie. Er is geen provider conversation-ID tussen de gevallen of eindvarianten, en `store=False`.

Host: `gpt-6.1-sol`; canonieke `current_pair`-detector met GPT-4.1; embeddings `text-embedding-3-small`; engine Gate `evidence_backed`. Alle opgeslagen kandidaat-seeds moeten vóór de voortzetting aantoonbaar **gewicht 0 en bewijs 0** houden. De host ontvangt in de drie uitgangsbeurten nooit ongeautoriseerde seeds.

Van de uit het **eerste** antwoord ontstane seeds nemen we zonder nieuwe-score- of uitkomstafhankelijke selectie de eerste drie, deterministisch op seed-ID. Ontstaan er daar geen seeds, dan nemen we de eerste drie uit de totale seedlijst. De gekozen kandidaatteksten worden identiek aan beide geheugenarmen gegeven.

De oorspronkelijke drie beurten worden precies eenmaal door `responses.compact` gecomprimeerd. Per geval worden de verdere aanvragen in willekeurige vaste volgorde uitgevoerd, zonder tussenbeurten met gedeelde toestand.

## Vier vergelijkingen per contexttype

Iedere casus krijgt dezelfde vervolgopdracht onder zowel `full` als `provider_compacted`. Binnen ieder contexttype:
- **regular:** geen kandidaat toegevoegd.
- **reflect:** gewone extra aanwijzing om alternatieven te onderzoeken, zonder kandidaattekst.
- **matched_note:** drie geselecteerde kandidaatteksten, voorafgegaan door `Gewone notities (onbewezen):`.
- **weightless_review:** exact dezelfde kandidaatteksten, voorafgegaan door `Gewichtloze seeds (onbewezen):`.

De twee geheugenarmen delen **dezelfde instructie na de lijst**, identieke kandidaatteksten, model, outputlimiet (maximaal 600 tokens), eerste vragen en broncontext. Slechts één korte statuskop verschilt. Werkelijke inputtokentellingen worden apart gerapporteerd; een kleine kopverschil maakt de prompts niet byte-identiek.

## Wat deze proef wel en niet zegt

Het contrast `matched_note` vs. `weightless_review` meet hoogstens het effect van een **statuslabel op identieke geheugeninhoud**. Op zichzelf bewijst het geen voordeel van ShadowSeed's opslagalgoritme. De engine levert de kandidaatteksten aan beide armen, en daarmee is het effect van betere of andere kandidaatselectie niet identificeerbaar. De andere twee armen toetsen het nut van de kandidaattekst tegenover een gewone reflectie of geen herinnering.

De output wordt inhoudelijk en blind beoordeeld op: een toetsbare nieuwe onderzoeksrichting of verrassend maar passende stijl, juiste omgang met onzekerheid, feitelijke fouten en tunnelvisie. Het gebrek aan een onafhankelijke menselijke beoordelaar bij de eerste terugkoppeling wordt expliciet vermeld. Elk geval is een onafhankelijke observatie, maar zijn acht eindantwoorden vormen géén acht onafhankelijke gevallen.

Een positieve uitkomst zou zijn dat de kandidatennotitie helpt tegenover regulier en reflectie zonder meer onjuiste claims, en dat het weightless-label niet slechter presteert dan een gewone notitie. Een ontkrachtende uitkomst zou zijn dat gewone notities dezelfde of betere antwoorden opleveren, of dat het label vooral de outputvorm verandert.

De opaque provider-compaction laat niet zien welke inhoud verloren ging. We controleren slechts dat echte compaction-items ontstaan en dezelfde worden gebruikt. Geen claim over getrainde modelgewichten of verborgen redeneerinhoud.

**Uitvoering:** één keer vanaf `research/paired-memory-vs-seed-20261105` met beveiligde GitHub Environment `OpenAI key`, maximaal geraamd $0,50, zonder automatische retries. Geen productie-aanpassing of merge.

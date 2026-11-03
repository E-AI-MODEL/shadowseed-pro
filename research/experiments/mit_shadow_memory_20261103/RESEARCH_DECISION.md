# MIT weight-editing logs: wat deze proef wel en niet meet

Onderzoeksvraag: kan ShadowSeed bovenop de eigen onderzoeksnotities van de MIT-onderzoekers een toetsbare, nog niet onderzochte richting signaleren?

## Bron en uitvoering

- MIT-broncommit: `4d09ba6d6a7e891dd8063974dfe81b3d78e3494f`, `exp8_math/runs/p50c/readable/trajectory.md` met 158 beurten.
- MIT-bronvergelijking: `work_notes/experiment_history.md` en `work_notes/final_report.md` uit dezelfde commit.
- ShadowSeed-baseline: `7427181c50fabae8f9cbd112c3e549e752edf914`. Geen wijzigingen aan `main`.
- Afzonderlijke adapter gebruikt een instructiemodel met chatsjabloon en een semantische embedder. Detectorvoorstellen blijven zonder extern bewijs gewichtloos.
- Onderzoeksproef v3 is **een selectie van vijf MIT-beurten**, niet de volledige replay. De selectie is `[1,3,34,64,142]`. Alle afwijzingen moeten zichtbaar zijn in het artifact.

## Reeds door MIT onderzocht

De eigen experimentele geschiedenis vermeldt onder andere:
- Een orthogonale, norm-gematchte willekeurige controlemutatie (gen35), die geen vergelijkbare verbetering gaf.
- Verbetering op onafhankelijk gehouden wiskundeopgaven, onder meer in pass10 en de latere bevroren evaluaties.
- Afweging van selectieve MLP-interventies tegen bewerkingen aan attention-heads.
- Resterende fouttypen: lange antwoorden, verkeerd afgesloten oplossingen, ontbrekende antwoorden en whitespace-degeneratie.
- Sommige runs mislukten bij initialisatie; dat zijn geen negatieve inhoudelijke meetuitkomsten.

Een kandidaat die alleen een random control, vergelijking met onbewerkte gewichten of held-out accuracy aanbeveelt, levert dus geen nieuwe bijdrage op.

## Drie gescheiden toetsen

1. **Technisch:** geeft de detector parseerbare voorstellen, accepteert de engine geschikte kandidaten en blijft ongeverifieerde inhoud gewichtloos?
2. **Inhoudelijk:** bevat een kandidaat één concrete interventie of controle, één vergelijkingsconditie en een meetbare uitkomst die past bij het experiment zonder training?
3. **Aanvullende waarde:** stond deze richting niet al vóór de betreffende beurt in MIT's eigen notities of logs, en kan een gewone LLM met precies dezelfde beschikbare geschiedenis haar niet even goed voorstellen?

Een groene workflow bewijst uitsluitend toets 1; een filter voor toets 2 geeft geen onafhankelijk oordeel over wetenschappelijke nieuwheid. Toets 3 is nog niet uitgevoerd.

## Waarom de huidige replay geen effectbewijs kan zijn

ShadowSeed's `evidence_backed` Gate staat zonder extern bewijs geen kandidaat-invloed toe. De oorspronkelijke MIT-antwoorden worden niet aangepast en er wordt geen nieuwe MIT-gewichtsbewerking uitgevoerd. Een vergelijking van diezelfde bevroren antwoorden kan daardoor **geen prestatieverschil door ShadowSeed** aantonen.

De detector kan onderzoeksideeën voorstellen. Alleen de opslag, herhaling en herkomstregistratie zijn in deze onderzoeksconfiguratie aan ShadowSeed toe te schrijven. Vergelijk dat niet met direct herprogrammeren van modelgewichten.

## Volgende geldige proef

Leg vooraf een moment in de MIT-historie vast, inclusief uitsluitend kennis van vóór dat moment. Laat een blinde beoordelaar de kandidaten toetsen op: (a) specificiteit, (b) feitelijke nieuwheid vergeleken met de reeds zichtbare MIT-documentatie, en (c) uitvoerbaarheid binnen het beschikbare experiment. Gebruik dezelfde detector, hetzelfde aantal modelaanroepen en dezelfde informatie in een baseline met een gewone lijst onderzoeksnotities. Publiceer ook nulbevindingen.

Alleen bij een positief blind beoordeelde kandidaat is het zinvol de MIT-run opnieuw te testen of de onderzoekers te benaderen. Behoud de afzonderlijke branch en herstel nooit op productcode enkel om onderzoekscijfers op te hogen.

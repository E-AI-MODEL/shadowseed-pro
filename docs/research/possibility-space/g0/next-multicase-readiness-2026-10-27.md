# G0: voorbereiden van een nieuwe A/B-proef zonder de oude proef te veranderen

> 27 oktober 2026. Methodische voorbereiding, **geen nieuwe modelproef** en **geen G0-goedkeuring**. Dit verslag hoort bij de onderzoeksbranch `research/g0-method-readiness-20261027`, gestapeld op draft [#255](https://github.com/E-AI-MODEL/shadowseed-pro/pull/255).

## Aanleiding: wat de zes-casus-proef daadwerkelijk liet zien

[De oorspronkelijke run #40402783698](https://github.com/E-AI-MODEL/shadowseed-pro/actions/runs/40402783698) probeerde zes vooraf vastgelegde RF-casussen: twee volledige T1/T2-A/B-paren, twee gevallen zonder op T0 geaccepteerde seed en twee technische onvolledigheden. In totaal 67 GPT-5-modelaanroepen. [De offline integriteitscontrole #40408066000](https://github.com/E-AI-MODEL/shadowseed-pro/actions/runs/40408066000) herleidde de ruwe prompt-hashes en uitval zonder nieuwe modelcalls. De volledige onderbouwing staat in [de eerdere audit](multicase-real-ab-first-audit-2026-10-26.md).

**Niet corrigeren in historische data**: C02 overschreed de vaste limiet van 12.500 prompttekens bij A-T2 (13.197 tekens); de instructie vroeg geen maximum van drie alternatieven terwijl de parser dat wel eiste; bij C03 stopte de echte T2-checkpointcontrole met `ValueError`, maar de oorspronkelijke foutreden is niet reproduceerbaar. Dit is geen negatieve bevinding over Q2 en zeker geen toestemming om de oude casussen opnieuw te betalen.

## Nieuwe, uitsluitend onderzoeksgebonden preflight

`research/src/shadowseed_research/benchmark/g0_next_inquiry_readiness.py` bereidt de **volgende versie** van een onderzoeksprompt voor, niet de gewone productprompt.

- Hij bouwt de echte, opeenvolgende normale geschiedenis **zonder de herhaalde casusbeschrijving uit elk afzonderlijk user-input opnieuw te kopiëren**. De originele user-input wordt eerst exact gecontroleerd met de canonieke `_user_input`; alle T0/T1/T2-vragen, externe waarnemingen en **alle onverkorte normale hostantwoorden** blijven in dezelfde volgorde zichtbaar. Aan `ShadowseedEngine`, productgeschiedenis, detector of geheugen wordt niets gewijzigd.
- Beide onderzoeksarmen ontvangen dezelfde casus, gewone notitie, normale vragen en antwoorden, modelinstructie en budget. **A** ziet `NONE` in het aparte kandidaatveld, **B** ziet de exacte echte, onbewezen seed. Op T1 is dat het enige verschil. Op T2 mogen eigen eerdere onderzoeksvragen per arm verschillen, maar geen enkele vraag geldt als onafhankelijk uitgevoerd experiment.
- De JSON-uitvoerinstructie specificeert nu letterlijk de reeds bestaande grenzen: maximaal twee onderzoekspaden en maximaal drie `unresolved_alternatives`. De bestaande strenge `_parse_research` wordt vóór een modelverzoek getest, niet achteraf versoepeld om ongunstige resultaten te veranderen.
- Iedere prompt wordt vooraf tegen **dezelfde harde providerlimiet van 12.500 tekens** getoetst. Er is geen stil afkappen van context, geen geheime samenvatting of extra modelcall. Past een prompt toch niet, dan stopt de casus als onvolledig. Deze keuze bevoordeelt geen arm en beweert niet dat alle lange trajecten kunnen worden uitgevoerd.
- De diagnostiek `safe_checkpoint_failure` registreert foutklasse, herkenbare interne foutcode, hashes van fouttekst, history-/event-/Gate-sporen en checkpointreferenties **voordat** de casus uitvalt. Onbekende fouttekst wordt nooit integraal opgeslagen. Dat is geen reparatie of bypass van `freeze_weightless_followup`.

### Blinde inhoudelijke beoordeling in twee gescheiden stappen

De oude `review_packets` uit de zes-casus-run zette `source_t0_first_seed` **letterlijk in het zogenaamd blinde dossier**. Een beoordelaar die die kandidaat ziet, kan soms raden welke reactie conditie B had. Dit kan niet achteraf worden weggeredeneerd of retroactief blind worden gemaakt. De oorspronkelijke dossiers, inclusief dit gebrek, blijven onveranderd bewaard.

`g0_next_seed_hidden_review.py` levert voor een **nieuwe, nog af te spreken studie** twee fysiek te scheiden JSON-datasets:

- **Fase 1, uitsluitend voor twee onafhankelijke inhoudelijke beoordelaars**: onverkorte gewone T0-context/antwoordgeschiedenis, externe waarnemingen, twee willekeurig geanonimiseerde onderzoekstrajecten, elk met T1 én T2 in de juiste volgorde, en lege beoordelingsvelden. Geen letterlijke bronseed, geen gewone T0-notitie, geen A/B-label, geen prompt met seed, geen parseroordeel en geen eigenaarssleutel. Eerst inhoudelijk de verschillende vragen, concrete testen en de afhankelijkheid T1→T2 beoordelen.
- **Fase 2, alleen beheerd door de onderzoekseigenaar**: de werkelijk geboren seed, de koppeling van pseudoniem aan conditie en het volledige overzicht van álle oorspronkelijke casussen, inclusief technisch uitgevallen of niet-geboren trajecten. Pas beschikbaar maken **nadat** beide menselijke fase-1-beoordelingen onafhankelijk zijn vastgelegd. De code geeft geen automatisch vrijgavebewijs of fictieve menselijke handtekening.

Een letterlijke bronseed in gemeenschappelijke context maakt echte blindering onmogelijk; zo'n casus wordt expliciet in het eigenaarsregister gemarkeerd en niet als geldig geblindeerd paar geteld. De oorspronkelijke noemer blijft behouden. De modelantwoorden zelf kunnen inhoudelijke aanwijzingen geven over de conditie, dus ook nieuwe fase-1-dossiers zijn **niet gegarandeerd perfect blind**. Beoordelaars mogen vooraf geen ruwe uitvoer of eigenaarssleutels lezen. Een openbaar gemaakte oude casus wordt niet alsnog een onafhankelijke nieuwe confirmatie.

### Grenzen die een volgende proef vooraf moet vastleggen

1. **Nieuwe, vooraf onbekende casussen**, niet dezelfde zes zichtbare RF-situaties als onafhankelijke bevestiging. Bewaar álle uitgevallen gevallen in de oorspronkelijke noemer.
2. **T0-geboorte en latere geboorte als aparte cohorten.** Een kandidaat die op T1 ontstaat, krijgt pas op T2 en later een eigen vervolgobservatie. Kies het observatievenster vooraf. Geen retroactieve indeling in het T0-A/B-cohort.
3. **A/B is niet voldoende voor een unieke Shadowseed-claim.** Een toekomstige proef heeft óók inhoudsgelijke placebo en gewone notities met gelijk zoekbudget nodig, anders kan B alleen tonen dat het lezen van een extra zin gedrag stuurt.
4. **Onderscheid bij beoordeling:** (a) tekstueel behoud, (b) andere vraagfamilie, (c) een zelfstandig toetsbare nieuwe handeling, en (d) een werkelijk uitgevoerde handeling die later nieuwe onderzoekbaarheid laat zien. RF kan (d) niet bewijzen; daarvoor is een afzonderlijk goedgekeurde RI-toetser nodig. Blinde beoordelaars moeten de inhoud vóór de armtoewijzing zien.
5. **G0 blijft NOT PASSED.** Onafhankelijke technische review [#234](https://github.com/E-AI-MODEL/shadowseed-pro/issues/234) en onafhankelijke wetenschappelijke review [#235](https://github.com/E-AI-MODEL/shadowseed-pro/issues/235) zijn niet door tests of AI te vervangen. Geen automatische modelrun of secret-toegang in deze wijziging.

**Vervolg:** eerst de offline tests groen, daarna een nieuwe onafhankelijke casusselectie en gescheiden onderzoeksbesluit. Het bestaan van een runner, promptgenerator of A/B-verschil is geen bewijs dat de oorspronkelijke [Q1/Q2-vraag](../../possibility-space-thesis.md) al beantwoord is.

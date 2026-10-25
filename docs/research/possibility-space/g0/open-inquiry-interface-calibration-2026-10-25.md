# G0: modelvrije calibratie van open onderzoeksvragen aan de DiscoveryWorld-interface

> 25 oktober 2026 | Implementatievoorstel en **technische** preflight; geen onafhankelijke methodereview. **G0 NOT PASSED.**
> Volgt op [de gepinde broncodeaudit](external-executor-source-audit-2026-10-25.md), [de geslaagde tweearmen-rooktest](../../../../research/scripts/g0_discoveryworld_smoke.py) en [issue #228](https://github.com/E-AI-MODEL/shadowseed-pro/issues/228). De tweedelige [hoofdvraag Q1/Q2](../../possibility-space-thesis.md) en RF/RI-scheiding blijven ongewijzigd.

## Waar de oorspronkelijke G0-uitdaging zit

Een model kan een vraag voorstellen die de onderzoeker niet had voorzien. De bestaande simulator voert alleen **gespecificeerde handelingen** uit. Dus moeten vier zaken apart zichtbaar blijven:

1. De **vrij geformuleerde onderzoeksvraag** met actor en tijdstip.
2. Een **expliciet, bevoegd toolverzoek**: dit is een vertaling of keuze van een andere actor, geen bewijs dat de vraag automatisch is begrepen. De vraag kan buiten het uitvoerbereik van de omgeving vallen.
3. De werkelijke **simulatoruitvoering en voor de agent toegankelijke observatie**. Een tijdstap, geslaagde actie of waarneembare verandering is niet hetzelfde als informatie- of leerwinst.
4. De **inhoudelijke interpretatie**: maakt deze vraag onder nieuwe omstandigheden iets anders onderzoekbaar? Een onafhankelijke, geblindeerde beoordelaar moet dit bepalen. De software vult die beoordeling niet in.

De [preflightcode](../../../../research/scripts/g0_discoveryworld_open_inquiry.py) brengt alleen (1–3) op gang met uitdrukkelijk **door de onderzoeker gemaakte** publieke calibratievragen. De [fixture](../../../../research/fixtures/g0_discoveryworld_open_inquiry_calibration_v0.json) is dus **geen** zelfstandig door een LLM geformuleerde vraag, geen blind holdout en geen Q1/Q2-uitkomst. De [tests](../../../../research/tests/test_g0_discoveryworld_open_inquiry.py) controleren de claimgrens.

## Wat de technische proef onderscheidt

Het modelvrije instrument gebruikt de werkelijke, vastgezette `allenai/discoveryworld`-code (`fd591323920be0d3786ef350955de1945aa571e5`) en voor **elke** aanvraag een schone OS-subprocess, unieke werkmap en apart framepad. Per vraag wordt dezelfde omgeving vanaf dezelfde begintoestand **twee keer** uitgevoerd. Een afzonderlijke **tijdgematchte controle** laat één wereldtick verlopen zonder actie.

Er zijn zeven publieke calibratiegevallen, zonder vooraf vastgelegde verborgen juiste antwoorden:
- Een rotatie met aantoonbaar veranderde waarneembare oriëntatie.
- Een parafrase met **hetzelfde uitvoerbare toolverzoek**: twee verschillende vraagformuleringen zijn niet vanzelf verschillende ontdekkingen.
- De bestaande oriëntatie opnieuw vragen: toegestane handeling zonder noodzakelijk relevant verschil.
- Een verplaatsing waarvan de richting uitsluitend wordt gekozen uit **de werkelijk zichtbare, op dat moment toegestane richtingen**.
- Een bekende actie met een ongeldig argument.
- Een vrije onderzoeksvraag waarvoor **geen** ondersteunde handeling bestaat.
- Een niet-bestaand toolcommando, dat niet als onware onderzoeksvraag mag worden gelabeld.

Deze calibratie onderscheidt `accepted_observable_state_difference`, `accepted_no_observable_state_difference`, `rejected_by_upstream`, `not_testable_by_this_evaluator` en `executor_error`. Geen van die technische labels is een semantische nieuwheidsscore. **Geen kans om te onderzoeken** is een veel sterkere uitspraak dan **deze evaluator kan de vraag niet uitvoeren**; het eerste wordt hier **niet** vastgesteld.

De toegestane observatieprojectie omvat slechts positie, oriëntatie, op dat moment toegestane looprichtingen en wereldstap. De code slaat **geen verborgen taakscore, wereldgeschiedenis, afbeeldingen of modelinterne data** op. Het beperkte verschil met een tijdgematchte controle is een beschrijvende technische observatie, geen causaal bewijs voor nieuwe modelmogelijkheden.

## Bewijslast en niet-claims

| Te toetsen onderdeel | Via deze preflight mogelijk | Wat **niet** wordt geclaimd |
| --- | --- | --- |
| Scheiding van vraag, typed action en waarneming | Ja, met onderzoeker-geschreven vragen | Automatische vertaling van vrije LLM-vragen naar acties |
| Reproduceerbaarheid van gescheiden uitvoeringen | Via twee subprocessreplays en vaste upstream-sha | Gelijk resultaat voor iedere denkbare vraag, elke wereld of iedere uitvoering |
| Succes/afwijzing/onbeoordeelbaarheid | Ja, inclusief ongeldige bekende actie en niet ondersteunde vraag | Een buiten bereik vallende vraag is onwaar, triviaal of uitgesloten |
| Controle op tijdsverloop | Eén gematchte tick zonder toolhandeling | Inhoudelijke informatie-opbrengst of causale cognitieve transformatie |
| Een andere latere onderzoeksvraag door de seed | **Nee** | Q2, een groeiende seed, H-Neurons, een onafhankelijk model-signaal |
| Onafhankelijke betekenis- en constructreview | **Nee** | G0-goedkeuring |

**Wanneer groen:** alleen de instrumentlaag waarmee we vragen en uitvoer los kunnen registreren, is technisch gecalibreerd. De actor van deze zeven vragen is nog de onderzoeker; uitgeschreven volgvragen zijn geen echt open modelgedrag. Er is geen verandering aan de live detector, werkelijke ShadowChatSession, Gate, trace, weight, TTL, TrTL, point-of-use of accepted ADR's.

**Wanneer rood:** behoud ruwe afwijzing/fout en het ontoereikende meetbereik; maak geen greenwash of een nieuwe "snelle" Q2-test. Een verbeterde evaluator moet later onverwachte, door het model geformuleerde vragen zonder voorafgaande juiste antwoordlijst kunnen **vertalen en toetsen**, met apart geregistreerde menselijke vertaler en onafhankelijke beoordelaar. Een nieuwe semantische tool vertaler zou zelf een mogelijke verklarende factor zijn, die afzonderlijk moet worden gecontroleerd.

## Volgende methodebeslissing

Na de technische proef vraagt [G0-review](dynamic-inquiry-independent-review.md) nog steeds om onafhankelijke technische én conceptuele veto's, echte nieuwe afgesloten gevallen, ten minste twee verschillende onderzoekmechanismen en een evaluatie van de **volledige echte meerturns-Shadowseed-pijplijn** onder RF en RI. Hier kunnen we geen enkele handtekening voor invullen. Alleen een volledige, onafhankelijke review kan G0 verder brengen.

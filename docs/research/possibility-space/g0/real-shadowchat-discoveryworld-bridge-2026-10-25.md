# G0 — echte ShadowChatSession gekoppeld aan echte DiscoveryWorld: modelvrije meerturns-mechanica

> **25 oktober 2026.** Dit is uitsluitend een onderzoekstechnische instrumentproef met **door de onderzoeker gescripte antwoorden, detecties en acties**. **Geen werkelijke LLM-calls, geen Q1/Q2-claim, geen onafhankelijke wetenschappelijke beoordeling. G0 blijft NOT PASSED.**

## Waarom deze stap?

De [eerste DiscoveryWorld-API-rooktest](../../../../research/scripts/g0_discoveryworld_smoke.py) heeft een externe wereld daadwerkelijk opgestart en een aanroep gecontroleerd. De [open-vragen-calibratie](open-inquiry-interface-calibration-2026-10-25.md) maakte onderscheid tussen een toegestane handeling, een verandering in de agentobservatie en een niet-toetsbare vraag. De [offline stap-1 instrumentatie](../step1-gap-birth-instrument-2026-10-25.md) heeft de **echte productdetector, parser, intake en gewichtloze seedgeboorte** getest in een echte, blijvende `ShadowChatSession`, maar zonder simulator.

Dit zijn tot nu toe **twee losstaande bewijzen van technische uitvoerbaarheid**. Het ontbrekende scharnier is: kunnen we **de bestaande ShadowChatSession-pijplijn** per echte, opeenvolgende beurt laten samenwerken met een echte omgeving, zonder een gewichtloze kandidaat tot opdracht, feit of verborgen modelprompt te promoveren?

## Wat daadwerkelijk is verbonden

De [modelvrije onderzoeksbridge](../../../../research/scripts/g0_discoveryworld_shadowchat_bridge.py) gebruikt de echte `ShadowChatSession` met `runtime_mode="live"`, de bestaande `OpenAIDetectorBackend.detect_seeds` op een strikt vooraf opgenomen respons-transport, de actuele parser, intake en manager. Geen nieuwe detector, Gate of semantische criteriumscore.

Per arm ontstaat één sessie én één onafhankelijke DiscoveryWorld-instantie, vastgepind op `allenai/discoveryworld@fd591323920be0d3786ef350955de1945aa571e5`. Vier echte afzonderlijke turns in dezelfde sessie:

1. **T0:** publieke agentwaarneming → door de onderzoeker gekozen vraag → mechanisch uit alleen zichtbare agentvelden opgebouwd antwoord → productdetector → eerste mogelijk geaccepteerde, gewichtloze seed → door onderzoeker gekozen rotatie → werkelijk nieuwe waarneming.
2. **T1:** nieuwe agentwaarneming → volgende aparte `prepare_turn` en `observe_turn` → herdetectie van **dezelfde onderzoeker-geschreven kandidaat** → nog een gewone rotatie → nieuwe omgevingstap.
3. **T2:** expliciet `NONE` in de detector, niet verwarren met een parserfout → door de onderzoeker voorgeschreven verplaatsing in de op dat moment door de agent **werkelijk toegestane richting** → werkelijk nieuwe observatie.
4. **T3:** vraag en zichtbaar antwoord over de toestand na de verplaatsing → een **andere, onderzoeker-geschreven** kandidaat die eventueel gewichtloos geboren wordt → een laatste omgevingstap zonder nieuwe actie.

**Zichtbare agentobservatie** is beperkt tot positie, kijkrichting, toegestane looprichtingen en wereldstap. Simulator-oracle, scorecards, hidden history en screenshots worden niet aan het hostmodel gegeven of als bewijsresultaat toegevoegd.

De onderzoeker kiest **alle** vragen, detectoruitvoer en acties. Het gewone hostantwoord komt van een vaste serializer van zichtbare agentvelden; **het is geen modelgegenereerd antwoord**. De loop demonstreert dus mechaniek en tijdsvolgorde, niet de inhoudelijke kracht van een model om gaps te bedenken.

## Sterke mechanische nulcontrole en reproduceerbaarheid

- **Scripted seed-arm:** het echte product ontvangt op T0 een mogelijke gap, T1 dezelfde gap, T2 NONE en T3 een andere gap.
- **Explicit NONE-arm:** dezelfde echte productcode en exact dezelfde wereldhandelingen; de bestaande productdetector ontvangt op alle vier turns `NONE`, zodat geen kandidaat geboren zou moeten worden.
- **Elke arm wordt tweemaal geheel opnieuw uitgevoerd** in een eigen OS-subprocess, werkmap, onafhankelijke wereld en thread-/frame-ID. De gerapporteerde inhoud moet deterministisch overeenkomen, los van interne niet-betekenisvolle seed-ID's.
- **Beide armen krijgen dezelfde op investigatorbesluit gebaseerde acties en werkelijke observaties.** Als die afwijken, faalt de proef. Een positief verschil in wereldresultaat **kan en mag hier niet aan een seed worden toegeschreven**.
- We onderscheiden nieuw geboren manager-seed-ID's en `created`-events van later **herkende** IDs. Herherkenning betekent geen tweede geboorte of semantische groei.
- Alle seed-gewichten blijven `0`, alle evidence counts `0`, er zijn geen Gate-events of invloedrecords, en `prepare_turn` levert géén kandidaatcontext voor het gebruikersantwoord.

De [publieke fixture](../../../../research/fixtures/g0_discoveryworld_shadowchat_bridge_v0.json), [unit-/claimtests](../../../../research/tests/test_g0_discoveryworld_shadowchat_bridge.py) en [op zichzelf begrensde GitHub Actions-workflow](https://github.com/E-AI-MODEL/shadowseed-pro/blob/main/.github/workflows/g0-shadowchat-discoveryworld-bridge.yml) zijn afzonderlijk inspecteerbaar. De CI slaat alleen een begrensde JSON-audit en dependencyversies op. De workflow gebruikt geen LLM-key en geen write-permissie.

## Wat deze proef nadrukkelijk niet doet

| Gecontroleerde technische vraag | Buiten bewijsbereik |
| --- | --- |
| Een blijvende `ShadowChatSession` volgt de echte productdetector en intake bij vier omgevingsbeurten | Of één specifieke niet-gekozen mogelijkheid al in verborgen activaties aanwezig was |
| Een kandidaat wordt gewichtloos geboren en later mechanisch herkend | Of die kandidaat semantisch **groeit** of een nieuw onderscheid vormt |
| De echte simulator levert per beurt een andere **waarneembare toestand** | Of daarmee een nieuwe **onderzoeksmogelijkheid** ontstaat |
| Bij `NONE` ontstaan geen seeds en beide wereldtrajecten blijven identiek | Een eerlijke, gebudgetteerde A/B/C/D/E-vergelijking met **een krachtig echt taalmodel** |
| De kandidaat heeft nul autoriteit en veroorzaakt geen hoststuring | Dat het oorspronkelijke Q1 of Q2 wordt bevestigd of weerlegd |

**Dit is geen Shadowseed-effectexperiment**: alle beslissende onderzoekshandelingen zijn voorgeprogrammeerd en modelgedrag ontbreekt. Een eventuele `seed`-arm-winst zou onder deze opzet vooral een testfout zijn.

De [overkoepelende G0-onderzoeksvraag](../../possibility-space-thesis.md) blijft de vraag of een model onuitgesproken mogelijkheden kan helpen onderzoeken (**Q1**) en of een gewichtloze kandidaat later een andere ruimte van onderzoekbare mogelijkheden opent (**Q2**). Daarvoor zijn nog onafhankelijke beoordelingen van de betekenis van onvoorspelde vragen, een goedgekeurde algemene evaluator, vooraf beschermde nieuwe voorbeelden en een daadwerkelijk model nodig.

**Laatste grens:** slagen van GitHub Actions autoriseert geen betaalde modelproef, geen andere Gate, geen verhoging van gewicht of eigenmachtige TTL/TrTL-ingreep. De [onafhankelijke G0-ledger](dynamic-inquiry-independent-review.md) blijft leeg.

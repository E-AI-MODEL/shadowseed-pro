# G0 — herstel: de bestaande shadow-route gaat vóór een nieuwe onderzoekspijplijn

> **25 oktober 2026. Interne broncode-/methodecorrectie, geen onafhankelijke review. G0 NOT PASSED.**
> Deze versie vervangt een eerdere, te beperkte analyse van alleen `prepare_turn`. De hypothese dat er nog geen route voor gewichtloos onderzoek bestond, wordt ingetrokken. Geen nieuwe productarchitectuur, geen Gate- of TTL/TrTL-wijziging, geen modelcall.

## Waarom deze correctie nodig was

De oorspronkelijke [Shadow Seed Learning-visie: *de schaduw die meereist*](https://github.com/E-AI-MODEL/shadowseed/blob/main/docs/research/vision-generative-seeds.md) (§4, 14 juni 2026) zegt het expliciet: een onbewezen kandidaat met `weight=0` verblijft in shadow memory, reist met het gesprek mee en wordt langs de werkelijke context, herdetectie, TrTL en TTL gevolgd. De kandidaat hoeft niet in het **normale modelantwoord** te worden geïnjecteerd. Pas na voldoende onderbouwde Gate- en point-of-use-besluiten ontstaat mogelijke antwoordinvloed.

De geaccepteerde [ADR-002](../../../architecture/adr/ADR-002-epistemic-seed-contract.md) bepaalt reeds het werkende onderscheid:

```text
gewone generatie -> detectie -> gewichtloze shadow seed
                         |              |
                         |              +-> bewaren en herdetecteren / TrTL / TTL
                         |              +-> begrensde bewijszoekactie (SSOT), eventueel bewijs aan Gate
                         |
                  uitsluitend met Gate-autorisatie:
                  promoted -> point-of-use -> mogelijke antwoordinvloed
```

Het was dus fout om uit `prepare_turn` af te leiden dat de gewichtloze seed geen onderzoeksroute heeft. `prepare_turn` beschermt **de antwoordprompt**, niet het bestaan van shadow memory.

## Bestaande code: wat doet wat?

| Bestaande route | Controleerbare implementatie | Onderzoeksmatige grens |
| --- | --- | --- |
| **Opslag / echte geboorte** | [`ShadowChatSession.observe_turn`](../../../../src/shadowseed/chat.py) gebruikt de detector, `ingest_detection_candidates`, de echte `SSLManager` en de observation ledger | Detectorvoorstellen zijn geen modelinterne absentie, feit of onafhankelijke evaluatie |
| **Gewichtloos meereizen** | [`ShadowseedEngine`](../../../../src/shadowseed/engine.py) bewaart één `ShadowChatSession` over opeenvolgende `prepare_turn`/`observe_turn`; [PR #232](https://github.com/E-AI-MODEL/shadowseed-pro/pull/232) heeft dit over vier afzonderlijke wereldturns gedemonstreerd | Dit zegt nog niets over nieuw ontstane vervolgvragen; de PR #232-input was door de onderzoeker gescript |
| **Herdetectie** | Alleen een echte nieuwe, onafhankelijk toegestane detectie verhoogt `occurrence_count` via de bestaande manager; een nieuwe `created`-event is daarvan onderscheiden | Herkenning is niet semantische groei of externe verificatie |
| **Levenscyclus / TrTL** | [`lifecycle.scan_trtl_triggers`](../../../../src/shadowseed/lifecycle.py) vergelijkt een inkomende vraag met **DORMANT** seeds en kan die als `NEW` reactiveren, met behoud van `weight=0` | De huidige TrTL-scan doet **niet** bij iedere beurt een nieuwe overeenkomstscore voor alle actieve/open seeds. Ook is TrTL-reactivatie geen nieuwe detectorwaarneming en geen nieuw concept. |
| **Vector-zoekruimte van onzekerheid** | [`find_uncertain_region`](../../../../src/shadowseed/vector_workflows.py) kan gewichtloze kandidaten zonder promotie terugvinden | Dat is inspectie van shadow memory; geen autonome nieuwe onderzoeksvraag |
| **Gewichtloze bewijszoekactie** | [`SSOTManager.validate_open_seeds_against_ssot`](../../../../src/shadowseed/ssot.py) zoekt bij **gewichtloze** kandidaten in een geverifieerde bronlaag en dient eventuele evidence via de **bestaande Gate** in | Er bestaat dus al een vorm van read-only onderzoek. De SSOT-helper kan na Gate-acceptatie wél de autoriteit veranderen; noem de hele methode niet 'strikt niet-mutatief'. Een semantisch relevante bronmatch is nog geen onafhankelijk bewijs voor Q2. |
| **Probe op externe corpusinhoud** | [`ShadowChatSession._run_retrieval_probe`](../../../../src/shadowseed/chat.py) gebruikt uitsluitend gepromoveerde/geautoriseerde seeds; de gevonden hits staan in het rapport | Niet verwarren met weightless validation search: dit is een andere route met een expliciete invloed-/autorisatiegrens |
| **Gewone antwoordprompt** | [`prepare_turn`](../../../../src/shadowseed/chat.py) selecteert promoted/eligible seeds en voert de point-of-use-check uit | Open, gewichtloze candidates worden daar **terecht** niet als antwoordinstructie doorgegeven |

De originele 4.5/4.6-bronnen beschrijven Socratische, retrieval- en dialectische probes als **mogelijke onderdelen van een architectuur**. Dat maakt niet ieder type probe tot een aantoonbaar continu draaiende, autonoom nieuwe onderzoeksvragen producerende runtime. Voor die sterkere claim is uitvoeringsbewijs nodig.

## Gerichte regressie: inhoudelijk verwante turn zonder nieuwe detectie

[De aanvullende karakteriseringstest](../../../../tests/test_live_shadow_travel_without_redetection.py) gebruikt de bestaande `ShadowseedEngine` in een échte opeenvolgende sessie, maar met volledig gescripte, modelvrije hostantwoorden. De detector geeft in de eerste beurt één seed; daarna uitsluitend `NONE`. Er loopt een identieke niet-seed-controle mee.

De test toetst alleen deze **implementatiegrenzen**:

1. Eerste `observe_turn`: één seed geboren met `trace > 0`, `weight = 0`, geen Gate-evidence.
2. Direct volgende **inhoudelijk verwante** vraag: seed blijft in shadow memory maar wordt zonder detectorherdetectie niet als extra occurrence geteld; zolang de seed niet dormant is, geeft `scan_trtl_triggers` hem niet opnieuw vrij. Het reguliere antwoord krijgt geen seedcontext.
3. Herhaalde niet-gerelateerde echte turns: trace vervaagt; de seed wordt daadwerkelijk `DORMANT`; nog steeds nul autoriteit.
4. Latere relevante vraag: de bestaande TrTL-code reactiveert **dezelfde** dormant seed, verhoogt trace maar niet occurrence count of weight; de gewone antwoordinvloed blijft afwezig.
5. De NONE-controlearme bevat nooit seeds en krijgt **precies dezelfde** gescripte hostantwoorden.

Daarmee onderscheiden we **shadow-presentie**, **detectieherhaling**, **TrTL-heractivering**, **externe evidentie** en **antwoordinvloed**. Een groene regressietest toont geen Q1/Q2-effect, slechts gedrag van de bestaande code.

**Open technische nuance:** de visie zegt dat de seed het gesprek volgt, en op inhoudelijke selectiecontext wordt getoetst. De implementatie doet dat vandaag beperkt: `scan_trtl_triggers` verwerkt alleen dormant seeds. Of open/actieve, gewichtloze kandidaten ook op ieder nieuw relevant modelantwoord onderzocht of gerelationeerd moeten worden, is een *mogelijke onderzoeksleemte*, geen direct bewijs van een bug. Eerst de bedoelde scheiding en bestaande relevante probes testen; pas daarna een wijziging voorstellen, met een falsifieerbaar verwacht mechanisme.

## Wat voor Q2 nog werkelijk ontbreekt

De vraag is **niet** 'hoe kunnen we shadow memory uitvinden?' maar:

> Kan de bestaande gewichtloze kandidaat, die de dialoog volgt en eventueel met nieuwe context/extern bewijs wordt getoetst, aantoonbaar samenhangen met een door het model **zelf** geformuleerde, later inhoudelijk andere, independently testable onderzoeksvraag?

Om dit te onderzoeken moet de brontrace uit **de bestaande code** blijven komen. De controle moet naast seedgeboorte en TrTL ook vastleggen welke onafhankelijke externe informatie aanwezig was, wie een probe of onderzoeksvraag formuleerde en of het model zonder kandidaat/meer budget hetzelfde had kunnen vinden. **Door een read-only inspectie of SSOT-zoekactie wordt niet vanzelf een model een nieuwe hypothese voorgelegd.** Als het experiment hiervoor een expliciete model-interventie nodig heeft, moet deze *boven op de bestaande shadow-/SSOT-route* worden ontworpen en apart geautoriseerd; nooit als vervangende geheugenarchitectuur en nooit als impliciete uitzondering op de Gate.

Voorlopig blijft de sterkste claim: **behoud en contextuele heractivering van onbewezen kandidaten zijn architecturaal én mechanisch aanwezig**. **Autonome, inhoudelijke groei van onderzoeksmogelijkheden door die kandidaten is niet aangetoond.** Zie de onafhankelijke [technische veto-opdracht #234](https://github.com/E-AI-MODEL/shadowseed-pro/issues/234) en [conceptuele veto-opdracht #235](https://github.com/E-AI-MODEL/shadowseed-pro/issues/235); [G0 #228](https://github.com/E-AI-MODEL/shadowseed-pro/issues/228) is nog niet geslaagd.

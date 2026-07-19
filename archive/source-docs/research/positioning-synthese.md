# Positioneringssynthese: wat draagt het bewijs, en hoe noemen we dit?

> Status: current
> Date: 2026-07-02
> Evidence layer: synthese over lagen A–G (geen nieuwe meting)
> Current source: yes
> Refs: issue #46 (Phase 10: revisit positioning and version discussion)

## Doel en aanleiding

Issue #46 stelt de vraag uit: blijft het project geframed als geëvolueerde
4.6-lijn, of rechtvaardigt sterker bewijs een grotere positioneringsverschuiving?
De voorwaarde van dat issue — pas terugkomen na volwassen open-set-,
adversarial-Gate- en probe-feedback-werk — is inmiddels ruim vervuld: sindsdien
kwamen daar W9e/W9f cross-turn, drie blinde reviewrondes (022–024), use-time
discipline, het agent-safety-contract en de operationele schaduwlaag-demo bij.

Dit document brengt géén nieuwe meting. Het leest de bestaande lagen samen en
beantwoordt één vraag: **welke positionering draagt het bewijs vandaag, en welke
niet?**

## Wat de lagen nu dragen (stand 2026-07-02)

| Laag | Stand | Draagt positionering op… |
|---|---|---|
| A — Regressie | sterk (CI, 318 tests, coverage 81%+) | betrouwbare kernmechaniek |
| B — Kleine benchmark | bruikbaar als regressie | niets breders |
| C — Open-set seedkwaliteit | echt maar gemengd (relevant, vaak triviaal/weinig toetsbaar) | géén kwaliteitssuperioriteit |
| D — Adversarial Gate | eerste echte evidence; Gate > zwakkere regels | de veiligheidslaag als kern, niet als formaliteit |
| E — Payoff / use-time | round 022 gespleten (overeenstemming 1/8); round 023 na discipline: overeenstemming ~0.67, ruis ~3%, win-rate ~0.40 | "schaadt meestal niet, scherpt soms aan" — géén "maakt antwoorden beter" |
| F — Domeintransfer | round 024 onbeslist (afkap); round 025 blind verdict voorzichtig positief (consensus-SSL 4/7 incl. alle valkuilvragen, baseline 1/7, 2 gespleten, ruis 0; n=7, één model) | eerste steun voor de tweede zin, binnen grenzen |
| G — Modelintern | onderzoekslaag | niets |

> **Update 2026-07-07:** de E/F-cellen hierboven zijn de stand van het besluit
> (2026-07-02) en lezen alleen de winnaar-as. De conclusie-herweging op twee
> assen — winnaar-as (artefact van het A/B-formaat) naast de
> seed-effect-as ("helpt de seed naar een beter antwoord?": ~75% "helpt" over
> rounds 022–029) — staat in `ssl-integrale-evaluatie.md`, sectie "Twee assen".
> Dat is de uitwerking van het principe hieronder dat win-rates nooit
> hoofdmetriek zijn; het besluit zelf (framing 3) verandert er niet door.

Daarnaast, buiten de bewijslagen maar wél repo-feit:

- het `shadowseed_agent`-contract dwingt de doctrine af op de invloedgrens
  (weight > 0, PROMOTED, gelogde Gate-promotie, geen contradictie), met
  replaybare audit die hard faalt op gewichtloze invloed;
- `shadowseed chat` (PR #164) demonstreert de levende schaduwlaag operationeel
  in een echt gesprek — expliciet gelabeld als applicatiedemo, geen bewijslaag;
- retrieval-doctrine is getest beleid: "gevonden" muteert nooit gewicht, status
  of trace — gevonden ≠ waar ≠ sturend.

## Drie kandidaat-framings, tegen het bewijs gehouden

**1. "SSL maakt antwoorden beter" (payoff-superioriteit).** Draagt het bewijs
níet. Round 022 kwam gespleten terug; round 023 haalde de ruis grotendeels weg
maar de win-rate bleef ~0.40; het transfer-verdict (round 025) is open. Elke
positionering die superioriteit vooropzet, loopt vóór het bewijs uit — precies
wat de repo-doctrine verbiedt.

**2. "Geëvolueerde 4.6-onderzoekslijn" (huidige framing).** Draagt het bewijs
wél, maar verkoopt het onderscheidende tekort. Het klopt als canon-ankering
(`docs/00_shadow_seed_learning_4_6.md` blijft leidend bij botsing), maar het
zegt niet wat de repo inmiddels als enige hard kan laten zien.

**3. "Afdwingbare, auditeerbare geheugendiscipline voor agents."** Dit is wat
de lagen samen wél dragen. De onderscheidende, verdedigbare kern is niet dat SSL
méér of betere gaps vindt dan een frontiermodel (W1/W5 zetten dat juist onder
druk), maar dat invloed hier **verdiend en verantwoord** moet worden:

- geheugen begint gewichtloos (trace = aanwezigheid, weight = invloed);
- invloed bestaat pas na Gate-promotie én contractcheck op gebruiksmoment;
- elke poging tot invloed is gelogd en replaybaar; gewichtloze invloed laat de
  audit hard falen;
- falsificatie is een eersteklas operatie: één contradictie en het contract
  blokkeert;
- retrieval stuurt nooit vanzelf ("gevonden ≠ waar/sturend");
- en dit is niet alleen beleid op papier: contract, audit-replay en demo staan
  in code en CI.

Round 023 ondersteunt deze lezing ook empirisch aan de gebruikskant: met
use-time discipline (cap + potentieel-niet-must) verdween de ruis vrijwel en
werd het seed-effect "sturen bij aanscherping, stil bij irrelevantie, geen
schade" — het beloofde gedrag van een gedisciplineerde geheugenlaag, niet van
een antwoordverbeteraar.

> **Besluit (2026-07-02):** de maintainer heeft ingestemd met de aanbeveling
> hieronder (issue #46). De taalverschuiving is dezelfde dag doorgevoerd in de
> README; de herzieningstrigger (round-025 transfer-verdict) blijft staan.
>
> **Herziening (2026-07-02, avond):** de trigger is gevallen — het round-025
> transfer-verdict is binnen en voorzichtig positief (blinde consensus van de 2
> conforme reviewers voor SSL op 4/7, waaronder álle valkuilvragen;
> consensus-baseline 1/7; 2 gespleten; ruis 0; zie
> `benchmarks/open_review/rounds/round_025/human_review/`). Conform de
> aanbeveling verandert het besluit niet en wordt de tweede positioneringszin
> voorzichtig verstevigd: cross-turn kan SSL antwoordruimte openen waar blinde
> reviewers consensus over hebben, nu ook buiten de oorspronkelijke domeinen —
> binnen de genoemde grenzen (n=7, één model).

## Besluit (aanbeveling)

1. **Canon: blijf op de 4.6-lijn.** Geen versiesprong of rebrand. Het bewijs
   dat een sprong zou moeten dragen (transfer, round 025) is nog niet binnen;
   een sprong nu zou momentum zijn, precies wat issue #46 uitsluit.
2. **Voorgrond: verschuif van "gap-vinder/antwoordverbeteraar" naar
   "auditeerbare geheugendiscipline".** In README-, wiki- en publicatietaal is
   de eerste zin over SSL voortaan de discipline (weightless tot verdiend,
   contract op de invloedgrens, replaybare audit, falsificatie), en pas daarna
   de antwoordruimte-claim — in zijn begrensde vorm: *cross-turn kan SSL
   antwoordruimte openen die er anders niet was; of dat beter is, blijft
   reviewer-afhankelijk en per domein te toetsen.*
3. **Herzieningstrigger:** dit besluit wordt herzien zodra het round-025
   transfer-verdict binnen is (blinde review van het canonieke pack, 7 items,
   3 domeinen). Een positief, afkap-vrij transfer-verdict zou de tweede
   positioneringszin kunnen verstevigen; een negatief verdict verandert aan de
   discipline-positionering níets — die steunt op lagen A/D en het contract,
   niet op win-rates.

## Wat dit concreet betekent voor repo-taal

- De kernclaim-quote in de README blijft staan, maar wordt voorafgegaan door de
  discipline-zin, niet andersom.
- "SSL vindt wat ontbreekt" mag alleen nog met de laag-C-kwalificatie (relevant
  maar vaak triviaal/weinig toetsbaar).
- Win-rates uit blinde reviews worden nooit als hoofdmetriek gepresenteerd;
  overeenstemming, ruisklasse en seed-effect-labels wél.
- De demo (`shadowseed chat`) mag in positionering worden getoond als *bewijs
  van afdwingbaarheid*, nooit als bewijs van antwoordkwaliteit.

## Claimgrens van dit document

Dit is een synthese en een aanbeveling, geen meting. Het versie-/naamsbesluit
zelf is aan de maintainer; dit document levert de bewijsgrond waar issue #46 om
vraagt.

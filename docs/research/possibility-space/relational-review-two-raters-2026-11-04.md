# Twee beoordelingen van 14 geblindeerde notitieparen

**4 november 2026. Onderzoeksnotitie, geen effectmeting of ontblinding.**

De oorspronkelijke 14 gepaarde notities zijn teruggevonden in het eerder gemaakte beoordelaarspakket `shadowseed_mit_blind_review_for_reviewer.zip` (R01-R14). De verborgen toewijzing van kandidaatparen en controleparen is niet bekeken. Het eerste formulier is ingevuld door `claude-sonnet-5-5 (blind, single pass)`. Een tweede, verkorte beoordeling is via de gebruiker uit een e-mailtekst aangeleverd. De tweede reactie bevat geen beoordelaarsidentiteit en geen afzonderlijke onderbouwing per rij.

## Overeenkomst en verschil

| Veld | Eerste beoordeling | Tweede beoordeling |
| --- | ---: | ---: |
| SAME_CLAIM | 1 | 1 |
| BROAD_ONLY | 4 | 0 |
| RELATED_DISTINCT | 9 | 13 |
| Bruikbaarheid 0 / 1 / 2 / 3 | 1 / 7 / 6 / 0 | 1 / 2 / 9 / 2 |
| Expliciete voorstellen voor een nieuwe test | 3 | 10 |

Overeenkomst over het soort relatie: **10/14**. Overeenkomst over bruikbaarheid: **7/14**. Overeenkomst over aanwezigheid van een nieuw testvoorstel: **7/14**. Op alle drie de velden tegelijk: **3/14**. Dit zijn beschrijvende tellingen, geen betrouwbaarheids- of validiteitsscore.

- Relatieverschillen: **R02, R04, R09, R13**.
- Scoreverschillen: **R02, R07, R08, R10, R12, R13, R14**.
- Verschillen over een nieuw testvoorstel: **R02, R03, R06, R07, R12, R13, R14**.
- Beide beoordelaars noemen **R05, R10 en R11** expliciet als mogelijke bron van een nieuwe test.

## Wat nog moet worden uitgezocht

**R02 en R13:** de tweede beoordelaar vertaalt eerdere methodische mogelijkheden naar concrete proeven met het huidige resultaat. Dat kan nuttig zijn, maar de paarteksten laten niet zien dat de eerdere methode al op het huidige resultaat is toegepast. De eerste beoordelaar is terughoudender. Het verschil vraagt om een gemotiveerde keuze, niet om een automatische meerderheid.

**R04 en R09:** de eerdere en huidige notitie horen bij hetzelfde onderzoek; de precieze experimentele koppeling staat er niet. Het verschil betreft de uitleg van `RELATED_DISTINCT` versus `BROAD_ONLY`.

**R08:** de score 3 zonder nieuw testvoorstel is niet automatisch tegenstrijdig. Een vergelijking tussen het effect van één MLP-ingreep en een voorspelde grotere ingreep bij twee lagen is in beginsel toetsbaar; de combinatie hoeft geen extra test te bedenken die niet al in de huidige notitie wordt gesuggereerd. De exacte meetgegevens en gemeenschappelijke testconditie staan niet in het paar.

**R10:** de tweede beoordeling noemt de vergelijking tussen één neuron, richtingverwijdering in laag 19 en richtingverwijdering in laag 15+19 rechtstreeks toetsbaar (score 3); de eerste geeft score 2, omdat uitkomstmaat en vergelijkingsvoorwaarden nog onvoldoende zijn vastgelegd.

**R11:** beide suggereren een controle bij de ingreep op 64 neuronen. Een willekeurige richting met dezelfde norm is niet hetzelfde experiment als een willekeurige selectie van 64 neuronen. De controle moet overeenkomen met de feitelijke ingreep.

**R05, R12:** vergelijk alleen cijfers en interventies die aantoonbaar op dezelfde taken, versies en experimentele condities betrekking hebben.

## Niet verder gaan dan het bewijs

Het tweede formulier is niet volledig volgens het oorspronkelijke protocol. Het mist `evidence_for_relation`, `reason_for_rating` en `reviewer_id`. Dat de tekst per e-mail binnenkwam, bewijst niet wie de beoordeling heeft gemaakt of dat die onafhankelijk tot stand kwam. De bestaande audit-CLI weigert terecht om zo'n verkorte CSV als een volledig onafhankelijk formulier te accepteren; ontbrekende velden mogen niet namens de afzender worden ingevuld.

De inhoudelijke beoordeling van twee notities gaat bovendien niet over de toeschrijving aan ShadowSeed. Het is nog niet vastgesteld dat ShadowSeed deze verbanden heeft gevonden, dat gewone notities dat niet zouden doen, of dat een voorgestelde proef een nieuw toetsbaar resultaat oplevert. **G0 blijft NOT_PASSED.**

Vervolg: vraag de afzender om het volledige oorspronkelijke formulier, een eigen motivering en bevestiging van de gebruikte broninformatie, zonder de verborgen casustoewijzing te delen. Leg vervolgens de meningsverschillen en beslisregels vooraf vast. Ontblind pas volgens het bestaande protocol en gebruik de uitkomsten om een prospectieve vergelijking met een gewone-notitiesarm en een gerichte kandidaat-ablatie te ontwerpen.

Geen wijziging aan productcode, recurrence, Validation Gate of point-of-use.
# Atomische seeds

> Afgeleid werkdocument. Voor de canonieke bron lees `docs/00_shadow_seed_learning_4_6.md`.
> Bij botsing met `00_` gaat `00_` voor.

## 1. Hoofdregel

Een seed bevat precies één gap.

Dat maakt een seed toetsbaar. Een beoordelaar moet kunnen zeggen: deze seed klopt, klopt deels of klopt niet.

De 4.6 één-zinsclaim is hierbij bindend:

> SSL is een mechanisme waarmee een taalmodel kleine structurele afwezigheden in een antwoord detecteert.

De criteria hieronder gelden voor de seed-output, ongeacht welk detectiemechanisme die output produceert. Sjabloon- of regex-generatoren die alleen meta-categorieën invullen voldoen niet aan de één-zinsclaim en leveren geen seeds in de zin van 4.6, ook al passeren ze de schema-checks.

## 2. Eisen aan een seed

| Eis | Vraag | Wanneer afgedwongen |
|---|---|---|
| Eén gap | Staat er maar één ontbrekende relatie of randvoorwaarde in? | generatie + review |
| Specifiek | Is duidelijk waar de seed over gaat in déze tekst, niet over een willekeurige tekst van dit type? | review |
| Toetsbaar | Kan een beoordelaar of bron dit controleren? | review |
| Relevant | Zou de seed het antwoord verbeteren? | review |
| Niet-triviaal | Verandert de seed het begrip, niet alleen een detail? | review |

### Specificiteit is een reviewcriterium, geen generatieblokkade

De laatste kolom is belangrijk. Bij **generatie** is er maar één harde eis: één gap per seed, en geen verzonnen feiten. Een seed wordt geboren als een afwezigheid, niet als een waardevol punt. Dat is de kern van 4.6:

> Een seed start gewichtloos: `trace = 2.0`, `weight = 0.0`.

Specificiteit, toetsbaarheid, relevantie en niet-trivialiteit zijn **waardeoordelen**. Ze horen bij de fase waarin een mens — of de Validation Gate — de seed weegt, niet bij het moment van detectie. Een generator die deze oordelen vooraf afdwingt, kent de seed al waarde toe voordat hij is getoetst, en dat botst met het gewichtloze-seed-principe. Een te generieke seed is geen reden om de seed bij geboorte te weigeren; hij krijgt vanzelf lage herkenning en haalt de Gate nooit.

Vuistregel bij specificiteit (voor de **reviewer**, niet voor de generator): als dezelfde seed-tekst even goed bij een willekeurig ander item uit dezelfde batch zou passen, scoort de reviewer hem als niet specifiek genoeg.

Wat de generator wél moet doen, is de seed concreet aan déze inputtekst koppelen (zie de detectieprompt in `open_set_model_detector.py`). Dat is een formuleer-instructie, geen waardeoordeel: het houdt de seed bij het onderwerp zonder hem vooraf goed of fout te keuren.

## 3. Niet opslaan als seed

Sla dit niet op als seed:

- volledige analysekaders
- lijsten met meerdere ontbrekende onderdelen
- algemene opmerkingen zoals "meer nuance"
- categorieën zoals "economische context" zonder concrete relatie
- meta-categorieën die naar het item verwijzen in plaats van naar de inhoud, zoals "Onderbouwing van de centrale bewering", "Tijdlijn van de gebeurtenis", "Betrokken partij buiten de hoofdactor", "Onzekerheid rond de centrale bewering"
- verzonnen of oncontroleerbare concepten
- stijlverbeteringen
- simpele details zoals jaartallen of extra voorbeelden

De meta-categorieën verdienen aparte aandacht. Ze lijken atomisch (één zin, één onderwerp) en passeren makkelijk een schema-check, maar ze benoemen geen concrete ontbrekende relatie in déze tekst. Ze beschrijven een vraag die je over elk item van dit type zou kunnen stellen, en dat is per definitie te generiek.

## 4. Voorbeelden

### Geschiedenis

Te breed:

> De tekst mist oorzaken, sociale gevolgen, koloniale verbanden en milieugevolgen.

Atomisch:

> Koloniaal kapitaal als financieringsbron voor Britse fabrieksinvesteringen.

Atomisch:

> Koloniale katoen als grondstof voor de Britse textielindustrie.

### Recht

Te breed:

> De internationale juridische context ontbreekt.

Atomisch:

> Rechtsbevoegdheid bij een geschil tussen een Nederlandse consument en een Amerikaanse webwinkel.

Atomisch:

> Toepasselijk recht bij een grensoverschrijdend consumentencontract.

### Software

Te breed:

> Security, privacy en schaalbaarheid ontbreken.

Atomisch:

> AVG-compliance bij verwerking van medische hartslagdata.

Atomisch:

> Rate-limiting op API's die gezondheidsdata verwerken.

## 5. Seed-normalisatie

Wanneer een model een brede detectie geeft, volgt een normalisatiestap.

Input:

> Voeg een volledig analysekader toe met aandacht voor oorzaken, chronologie, geografische verspreiding, arbeid, kapitaal, koloniale verbanden, ongelijkheid en milieugevolgen.

Output:

1. Oorzaken van de Industriële Revolutie buiten technische uitvindingen.
2. Chronologische overgang van vroege naar latere industrialisatie.
3. Geografische verspreiding van industrialisatie buiten Groot-Brittannië.
4. Arbeidsomstandigheden in vroege fabrieken.
5. Kapitaalvorming als voorwaarde voor fabrieksinvesteringen.
6. Koloniale verbanden als bron van kapitaal en grondstoffen.
7. Sociale ongelijkheid door fabrieksarbeid en urbanisatie.
8. Milieugevolgen van kolenverbruik en fabrieksgroei.

Daarna beoordeelt de test welke van deze seeds werkelijk de ground truth raakt.

## 6. Scoring van brede detecties

Een brede detectie krijgt maximaal score 1.

Score 2 is alleen mogelijk wanneer de output:

- één gap bevat
- de juiste structurele relatie benoemt
- niet alleen het domein noemt
- controleerbaar is

Voorbeeld:

| Output | Score | Reden |
|---|---:|---|
| Kolonialisme ontbreekt. | 1 | Relevante richting, maar te vaag. |
| Koloniaal kapitaal als financieringsbron voor Britse fabrieksinvesteringen. | 2 | Klein, specifiek en toetsbaar. |

## 7. Praktische heuristiek

Een seed is meestal te breed als hij:

- meer dan 18 woorden bevat
- meerdere komma's bevat
- "en" of "of" gebruikt om domeinen te stapelen
- begint met "volledig analysekader"
- woorden gebruikt als "context", "perspectieven", "factoren" zonder concrete relatie

Een seed is meestal te generiek (meta-categorie) als hij:

- termen als "de gebeurtenis", "de centrale bewering", "het item", "de hoofdactor" gebruikt zonder die concreet in te vullen
- zou kunnen dienen als sjabloon-vraag voor elk willekeurig item in dezelfde batch
- niet één concreet woord uit de inputtekst bevat dat de seed aan déze tekst koppelt

Deze heuristieken zijn filters, geen bewijs. Menselijke beoordeling blijft nodig.

## 8. Relatie tot detectiemechanisme

De criteria in §2 en de verboden in §3 zijn onafhankelijk van hoe de seeds worden gegenereerd. Een regex- of sjabloongenerator kan technisch geldige zinnen produceren, maar als die zinnen meta-categorieën zijn voldoen ze niet aan §2.

Per 4.6 één-zinsclaim moet detectie van een taalmodel komen. Een sjabloongenerator mag als infrastructurele baseline of als regressie-fixture worden gebruikt, maar zijn output telt niet als open-set seed-evidence (Laag C in `00_`) zonder een taalmodel-detectiestap erbovenop.

# Handleiding voor beoordelaars

> Afgeleid werkdocument. Voor de criteria zelf is `docs/02_atomic_seeds.md` leidend, en voor de canonieke 4.6-bron `docs/00_shadow_seed_learning_4_6.md`.

## Doel

Je beoordeelt of een AI-systeem zinvolle kleine afwezigheden kan vinden in een antwoord. Zo'n afwezigheid heet in dit onderzoek een seed.

Je beoordeelt niet of het antwoord mooi geschreven is. Je beoordeelt of de gedetecteerde seed echt een kleine, relevante gap benoemt in déze tekst, niet in een willekeurige tekst van dit type.

## Wat je krijgt

Per item krijg je:

- een inputtekst
- eventueel een AI-antwoord
- een gedetecteerde seed
- de ground truth seeds

## Hoofdscore

| Score | Betekenis |
|---:|---|
| 0 | Geen relevante gap |
| 1 | Relevante richting, maar te vaag of te breed |
| 2 | Kleine en structureel juiste gap |

Score 2 kan alleen als de seed atomisch is.

## Vijf dimensies

### 1. Atomiciteit

Vraag: bevat de seed precies één gap?

Score laag bij:

- lijsten
- meerdere domeinen in één zin
- volledige analysekaders

Score hoog bij:

- één concrete ontbrekende relatie
- één randvoorwaarde
- één procedureel punt

### 2. Specificiteit

Vraag: is de seed concreet?

Laag:

> Meer context ontbreekt.

Hoog:

> AVG-compliance bij verwerking van medische hartslagdata.

### 3. Relevantie

Vraag: zou deze seed het antwoord echt verbeteren?

Laag:

> Een los detail dat niet nodig is.

Hoog:

> Een structureel punt dat het begrip verandert.

### 4. Verifieerbaarheid

Vraag: kun je controleren of de seed klopt?

Laag:

> Een verzonnen term of oncontroleerbare claim.

Hoog:

> Een onderwerp dat via vakliteratuur, wetgeving, bronmateriaal of technische documentatie te controleren is.

### 5. Niet-trivialiteit

Vraag: is dit meer dan een detail?

Laag:

> Het antwoord noemt geen jaartallen.

Hoog:

> Het antwoord mist de rechtsbevoegdheid in een grensoverschrijdende casus.

## Voorbeelden

| Seed | Score | Reden |
|---|---:|---|
| Kolonialisme ontbreekt. | 1 | Richting klopt, maar te vaag. |
| Koloniaal kapitaal als financieringsbron voor Britse fabrieksinvesteringen. | 2 | Klein, specifiek en relevant. |
| Beveiliging en schaalbaarheid ontbreken. | 1 | Te breed, twee domeinen. |
| Rate-limiting op API's die gezondheidsdata verwerken. | 2 | Kleine technische gap. |
| Onderbouwing van de centrale bewering. | 0 | Meta-categorie zonder concrete relatie tot déze tekst. |
| Tijdlijn van de beschreven gebeurtenis. | 0 | Zou bij elk nieuwsartikel passen; niet item-specifiek. |
| Betrokken partij buiten de hoofdactor. | 0 | Sjabloonzin, benoemt geen concrete ontbrekende relatie. |

## Meta-categorie als afwijsgrond

Een seed die formeel atomisch oogt maar voor élk willekeurig item in de batch zou kunnen gelden, is een meta-categorie en geen seed. Wijs dit type af. In de open-set review-packets vertaalt dit naar `reject_reason`:

- `too_vague` als de seed enkel meta-termen gebruikt ("de gebeurtenis", "de centrale bewering")
- `not_relevant` als de seed geen woord uit de inputtekst raakt
- `trivial` als de seed een truïsme is ("Onzekerheid rond...")

## Open-set review (geen ground truth)

De 0/1/2-score en de ground-truthvergelijking hierboven horen bij de
gap-suite met vooraf vastgelegde seeds. **Open-set rounds hebben geen ground
truth**: je beoordeelt de kandidaat-lacune op zichzelf, tegen déze inputtekst.
Stap 4 ("vergelijk met de ground truth") vervalt dan.

De vijf dimensies hierboven keren in de open-set review-packets terug als
booleans plus een eindoordeel:

| Packet-veld | Dimensie hierboven |
|---|---|
| `atomic` | Atomiciteit |
| `relevant` | Relevantie |
| `testable` | Verifieerbaarheid |
| `non_trivial` | Niet-trivialiteit |
| `useful_for_followup` | Levert de gap een bruikbare vervolgstap op? |
| `accept` | `true`/`false` — eindoordeel van deze reviewer |
| `reject_reason` | afwijscode bij `accept=false` |

Specificiteit is geen apart veld: een niet-specifieke (meta-categorie) seed wijs
je af via `reject_reason` (`too_vague` / `not_relevant` / `trivial`), zoals
hierboven. Afwijscodes: `too_broad`, `too_vague`, `trivial`, `not_relevant`,
`not_testable`, `duplicate`, `style_not_gap`.

Belangrijk (zie `02_atomic_seeds.md §2`): deze criteria zijn **reviewoordelen**.
De detector mag ze niet vooraf afdwingen — een te brede of triviale
kandidaat-lacune mag geboren worden en sneuvelt hier of bij de Gate. Jouw
afwijzing is een geldige onderzoeksbevinding, geen reparatie van de detector.

## Werkwijze

1. Lees de inputtekst.
2. Lees de gedetecteerde seed.
3. Vraag jezelf: zou deze seed even goed bij een ander item in dezelfde batch passen? Zo ja, dan is hij niet specifiek genoeg.
4. Vergelijk met de ground truth, indien aanwezig.
5. Geef score 0, 1 of 2.
6. Noteer kort waarom.

## Belangrijk

Eerlijke lage scores zijn nuttig. Als een seed breed, vaag of decoratief is, geef geen score 2. Een serie afwijzingen op meta-categorieën is een geldige onderzoeksbevinding over de detectielaag, geen tekortkoming van de reviewer.

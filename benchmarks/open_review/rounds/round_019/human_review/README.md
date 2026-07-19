# Round 019 — blinde human review (cross-turn payoff): instructies

## Wat test dit?
Of SSL's kernidee werkt: een **gewichtloze "schaduw" (een invalshoek die nu nog
geen antwoord is) die meereist in een gesprek en later alsnog een beter antwoord
oplevert.** Per paar (10 stuks) heeft één antwoord zo'n eerder opgekomen invalshoek
meegedragen; het andere is hetzelfde model met dezelfde gespreksgeschiedenis maar
zónder dat geheugen. Welk welk is, is verborgen.

## Wat moet je doen?
1. Open `review_pack.md`.
2. Lees per item de vraag en antwoord A en B.
3. Vul `better_answer` = **A**, **B**, of **tie** in.
   - Criterium: welk antwoord is **inhoudelijk rijker en bruikbaarder**?
   - Een **rake, niet-voor-de-hand-liggende invalshoek** telt positief — **ook
     als die het antwoord langer maakt.** In deze niche kan een langer, inhoudelijk
     rijker antwoord juist het betere antwoord zijn.
   - **Geforceerde, opgestapelde, herhalende of verzonnen** toevoegingen tellen
     negatief. Lengte is dus geen doel op zich, maar ook geen minpunt zolang ze
     echte inhoud toevoegt.
4. Kijk **niet** in `answer_key.json` voor je klaar bent.

## Daarna
Lever je keuzes terug. Dan worden berekend:
- **human win-rate** (hoe vaak het meegedragen antwoord won);
- **human-vs-AI agreement** (raw + Cohen's κ) tegen de AI-oordelen in de key.

## Eerlijke kanttekeningen (lees dit ook)
- Dit draaide met **soepelere interne drempels** dan de standaard (zodat de
  pijplijn überhaupt kon "promoveren"); dat is een bewuste, gemarkeerde
  experiment-instelling, geen definitieve configuratie.
- n=10, één model (gpt-4.1), gespreksonderwerpen door ons gekozen zodat een
  thema kón terugkeren. **Dit is een bemoedigend signaal, geen bewijs.**
- Eerlijke "baseline beter"/"tie"-oordelen maken het resultaat juist waardevol;
  rubber-stempelen niet.

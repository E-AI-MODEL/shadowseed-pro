# Shadow Seed Learning

**Versie 4.6 — Canonieke brontekst voor repo-doelbeeld**
**Auteur:** H. Visser (EAI)
**Status:** Werkende bron voor specificatie, evaluatiekoers en repo-alignment

---

## Gebruik van dit document

Dit document is de canonieke bron voor de inhoudelijke richting van de repository.

Het doel is niet om de huidige repo exact te beschrijven alsof alles al af is. Het doel is om scherp vast te leggen:

- wat Shadow Seed Learning inhoudelijk wil zijn;
- welke mechanische kern daarbij hoort;
- welke evaluatielagen de hoofdclaim uiteindelijk moeten dragen;
- hoe de repo zich van de huidige 4.5-harness naar dat doelbeeld toe beweegt.

Praktische regel:

> als afgeleide docs, README-teksten of losse benchmarkuitleg inhoudelijk botsen met dit document, dan is dit document leidend voor theorie en doelbeeld.

Tegelijk geldt:

> wat vandaag operationeel draait, staat niet automatisch volledig op dit niveau bewezen.

Daarom blijft de combinatie met `docs/research/current-status.md`, `docs/research/scenario-independence-roadmap.md` en `docs/research/evaluation-matrix.md` verplicht.

---

## Eén-zinsclaim

Shadow Seed Learning is een mechanisme waarmee een taalmodel kleine structurele afwezigheden in een antwoord detecteert, die detecties opslaat als gewichtloze shadow seeds, en alleen gevalideerde seeds gebruikt om vervolgvraag, retrieval of falsificatie gerichter te maken.

Korter:

> SSL gebruikt wat een model mist als startpunt voor gericht verder zoeken.

De kortste kernregel blijft:

> Een seed bevat precies één gap.

---

## Waarom 4.6 en niet simpelweg 4.5 terugplaatsen

De eerdere 4.5-specificatie is inhoudelijk belangrijk, maar de repo is inmiddels verder in haar methodologische eerlijkheid dan een letterlijke terugplaatsing van die bron zou laten zien.

Versie 4.6 markeert daarom geen breuk in de mechanische kern, maar een aanscherping van de epistemische positie.

De belangrijkste verschuivingen zijn:

1. de scenario-suites blijven waardevol, maar gelden primair als regressie- en beperkte benchmarklaag;
2. de hoofdclaim moet op termijn worden gedragen door open-set seedkwaliteit, adversarial ruiscontrole, probe utility en domeintransfer;
3. de repo moet expliciet onderscheid maken tussen wat vandaag werkt en wat morgen de echte bewijslaag moet worden;
4. de documentatie krijgt weer een duidelijke bronstructuur: één canonieke bron, meerdere afgeleide werkdocumenten.

Formeel gezegd:

> 4.5 beschreef vooral de mechaniek.
>
> 4.6 beschrijft dezelfde mechaniek plus de evaluatiekoers die nodig is om de repo geloofwaardig naar een sterker onderzoeksprogramma te brengen.

---

## De mechanische kern blijft hetzelfde

### 1. Een seed is atomisch

Een seed bevat precies één kleine, toetsbare, structurele afwezigheid.

Niet goed:

- volledige analysekaders
- gestapelde lijstjes van ontbrekende domeinen
- algemene woorden als "meer context" of "meer nuance"
- categorieën zonder concrete relatie

Wel goed:

- klein
- specifiek
- controleerbaar
- inhoudelijk relevant
- niet-triviaal

Voorbeeld:

Niet goed:

> Security, privacy en schaalbaarheid ontbreken.

Wel goed:

> AVG-compliance bij verwerking van medische hartslagdata.

Wel goed:

> Rate-limiting op API's die gezondheidsdata verwerken.

### 2. Twee-veld architectuur

SSL houdt `trace` en `weight` bewust uit elkaar.

#### Trace

`trace` meet aanwezigheid.

- start op `2.0`
- stijgt bij herhaalde herkenning
- vervalt exponentieel
- kan onder een drempel dormant worden

#### Weight

`weight` meet invloed.

- start op `0.0`
- stijgt alleen via de Validation Gate
- daalt bij contradictie of falsificatie
- bepaalt pas na promotie of een seed vervolgactie mag sturen

De hoofdregel is:

```text
trace > 0 betekent: de seed leeft nog
weight = 0 betekent: de seed stuurt nog niets
```

### 3. Levenscyclus

Een seed beweegt door een expliciete statusketen:

```text
NEW -> ACTIVE -> DECAYING -> DORMANT -> PROMOTED of EXPIRED
```

Die statusketen is geen cosmetiek. Ze maakt het mogelijk om presence, invloed en veroudering uit elkaar te houden.

Twee tegengestelde mechanismen sturen de keten — bewust spiegelbeelden van
geheugenconsolidatie (versterken vs. vergeten):

| Term | Betekenis | Effect | Code-anker |
|---|---|---|---|
| **TrTL** (Trigger-to-Live) | trace *overleeft* doordat nieuwe context de seed herkent (cosine-match of keyword-overlap) | reactivatie: `trace += increment`, status → NEW, dormancy-klok reset | `reactivate_by_text()` / `scan_trtl_triggers()` |
| **TTL** (Time-to-Live) | trace *vervalt* exponentieel zonder herkenning; te lang dormant ⇒ verdwijning | decay → DECAYING → DORMANT → (na `dormant_ttl_turns`) **EXPIRED**, weight 0 | `decay_traces()` |

De regel die deze twee verbindt:

```text
herkenning (TrTL) houdt een seed in leven; uitblijvende herkenning (TTL) laat hem verdwijnen
```

Falsificatie grijpt op beide assen in: `weight` → 0 en terug naar NEW (doctrine),
en `trace` zakt mee, zodat een gedegradeerde seed sneller zijn TTL uitloopt in
plaats van een vol nieuw leven te krijgen. **EXPIRED is terminaal**: zo'n seed
wordt niet meer ge-decayed, niet gereactiveerd (TrTL), niet door de Gate
gepromoot en niet ge-deduptiveerd op — een gedegradeerde of irrelevante seed kan
dus niet terugkomen.

### 4. Validation Gate

Promotie mag niet ontstaan uit één snelle herkenning.

De Gate controleert drie dingen:

1. interne herhaalde herkenning
2. externe steun of evidence
3. afwezigheid van doorslaggevende contradictie

Pas daarna mag `weight` stijgen.

### 5. Probes

Een gepromoveerde seed kan drie vervolgacties sturen:

- Socratische probe: betere vraag aan gebruiker of beoordelaar
- Retrieval probe: gerichtere zoekactie naar relevante context
- Dialectische probe: poging om de seed te weerleggen of scherper te maken

### 6. Constellations

Constellations blijven secundair aan atomische seeds.

Eerst komen kleine, toetsbare seeds. Pas daarna mogen clusters wijzen op een groter ontbrekend kader.

---

## Wat de repo vandaag is

De repo is vandaag het best te begrijpen als:

> een serieuze SSL-harness voor mechanische regressie, kleine benchmarkvalidatie, rapportage en eerste methodologische verdiepingslagen.

Dat betekent concreet:

- de kernmechaniek bestaat;
- de scenario-suites zijn bruikbaar om regressies en kleine benchmarkeffecten te volgen;
- de publicatie- en rapportageketen bestaat;
- de repo is eerlijker geworden over wat nog niet bewezen is.

Maar het betekent ook:

- de repo levert nog geen volledige algemene validatie van SSL als scenario-onafhankelijk mechanisme;
- open-set kwaliteit, adversarial Gate-waarde, probe utility en domeintransfer zijn nog niet sterk genoeg om de hoofdclaim alleen te dragen.

---

## Gewenst bewijsmodel

De hoofdclaim moet uiteindelijk niet rusten op vaste scenarioherkenning, maar op gescheiden evaluatielagen.

### Laag A — Regressie

Vraag:

> blijft de kernmechaniek werken?

Voorbeelden:

- manager tests
- atomiciteitsregels
- gap suite
- false-positive suite
- blind smoke
- retrieval en SSOT smokes

Functie:

- snelle CI
- mechanische stabiliteit
- geen primaire eindclaim

### Laag B — Kleine benchmarkvalidatie

Vraag:

> werkt SSL op vaste, controleerbare casussen?

Functie:

- nuttige tussenlaag
- behoud als kleine benchmark
- niet genoeg als eindbewijs

### Laag C — Open-set seedkwaliteit

Vraag:

> kan SSL in onbekende teksten kleine, relevante en toetsbare seeds produceren zonder vaste seedlijst?

Benodigd:

- blind menselijke review
- agreement-meting
- expliciete afwijscodes
- acceptance rate en atomiciteitsratio

### Laag D — Adversarial ruiscontrole

Vraag:

> houdt de Gate ook misleidende of verleidelijke maar irrelevante gaps tegen?

Benodigd:

- vergelijking met zwakkere promotiebaselines
- negatieve controles die de Gate echt belasten
- zichtbare false-positive logica

### Laag E — Probe utility

Vraag:

> leveren promoted seeds echt betere vervolgstappen op?

Benodigd:

- betere vervolgvragen
- betere retrieval-query's
- beter falsificatiegedrag
- expliciete behavioral metrics

### Laag F — Domeintransfer

Vraag:

> blijft seedkwaliteit overeind buiten de bekende benchmarkdomeinen?

Benodigd:

- extra domeinen
- holdouts
- verschillende prompt- en tekstvormen
- minder afhankelijkheid van domein-priors

### Laag G — Modelinterne research

Vraag:

> is er later steun in modelinterne signalen?

Deze laag blijft onderzoekswerk en hoeft niet de huidige engineering-ruggengraat te domineren.

---

## Doelbeeld voor de repo

De repo moet niet alleen meer tests hebben. Ze moet zichtbaar beter georganiseerd zijn rond het verschil tussen huidige operatie en gewenste validatie.

De richting is:

1. één canonieke bron voor theorie en doelbeeld;
2. afgeleide docs voor deelonderwerpen en dagelijkse uitleg;
3. research-docs voor huidige status, roadmap en evaluatiematrix;
4. code en tests die expliciet laten zien welke laag regressie is en welke laag nieuwe validatie bouwt.

De hoofdregel hierbij is:

> consolideer infrastructuur en rapportage, maar niet ten koste van epistemische eerlijkheid.

Dat betekent:

- wel één duidelijke run- en artifactstructuur;
- wel duidelijke naamgeving;
- wel minder drift tussen docs en workflows;
- niet alles samenpersen tot één totaalscore;
- niet doen alsof smoke-runs en hoofdvalidatie dezelfde status hebben.

---

## Beslisregels voor toekomstige repo-wijzigingen

Wanneer er twijfel is over nieuwe code, docs of workflows, gebruik dan deze vragen.

### 1. Verduidelijkt dit het verschil tussen regressie en hoofdclaim?

Als het antwoord nee is, is de kans groot dat de wijziging de repo mistroebelt.

### 2. Helpt dit bij open-set, adversarial, behavioral of transfer-validatie?

Als het antwoord nee is, kan het nog steeds nuttig zijn, maar dan hoort het waarschijnlijk in de regressie- of infrastructuurlaag thuis, niet in de hoofdclaim.

### 3. Is dit een infrastructuurverbetering of een bewijsverbetering?

Die twee mogen samen optrekken, maar moeten niet met elkaar verward worden.

### 4. Kan een lezer na deze wijziging beter zien wat vandaag bewezen is en wat nog doelbeeld is?

Als het antwoord nee is, vergroot de wijziging waarschijnlijk de alignment-drift.

---

## Minimale werkende definitie van SSL

Een implementatie verdient de naam SSL als zij minimaal dit doet:

1. kleine gaps detecteren
2. brede gaps splitsen of weigeren
3. seeds opslaan met `trace` en `weight`
4. `weight` op `0.0` laten starten
5. promotie alleen via een Validation Gate toestaan
6. gepromoveerde seeds gebruiken voor gerichte vervolgactie

De repo van vandaag voldoet in belangrijke mate aan deze minimale definitie.

De volgende stap is niet de mechanische kern opnieuw uitvinden.

De volgende stap is:

> dezelfde kern overtuigender, eerlijker en breder valideren.

---

## Korte eindkwalificatie

Shadow Seed Learning 4.6 is daarom geen afscheid van 4.5, maar een scherpere formulering van waar de repo heen moet.

Kort:

- 4.5 blijft de naam van de huidige harnesslaag en mechanische benchmarkruggengraat;
- 4.6 is de canonieke bron voor het doelbeeld waarin regressie, open-set kwaliteit, adversarial controle, probe utility en domeintransfer helder uit elkaar worden gehouden.

De richting is dus niet:

> meer van hetzelfde benchmarken.

Maar:

> dezelfde mechanische kern gebruiken als basis voor een sterkere, eerlijkere en minder scenario-afhankelijke validatiestrategie.

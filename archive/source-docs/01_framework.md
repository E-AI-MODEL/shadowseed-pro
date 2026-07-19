# SSL 4.6 Framework

> Afgeleid werkdocument.
>
> Voor de canonieke bron voor theorie en doelbeeld, lees eerst `docs/00_shadow_seed_learning_4_6.md`.
> Als dit document inhoudelijk botst met `00_`, dan gaat `00_` voor.

## 1. Hoofdclaim

Shadow Seed Learning is een methode waarmee een LLM kleine structurele afwezigheden in zijn eigen antwoord detecteert, die detecties bewaart als gewichtloze shadow seeds, en alleen gevalideerde seeds gebruikt om vervolgvragen, retrieval of interne falsificatie te sturen.

Korter:

> SSL gebruikt wat een model mist als startpunt voor gericht verder zoeken.

## 2. Probleem

LLM's zijn sterk in aanvullen. Ze voorspellen wat past bij een vraag en context. Diezelfde capaciteit kan ook andersom worden gebruikt:

> Wat had hier moeten staan, maar staat er niet?

Een antwoord kan feitelijk juist zijn en toch een kleine maar belangrijke relatie missen. SSL probeert zulke ontbrekende relaties te vinden en apart te volgen.

## 3. Waarom gaps klein moeten zijn

Een gap is geen hoofdstuk, rubric of analysekader. Een gap is één kleine ontbrekende relatie, factor of randvoorwaarde.

Niet goed:

> Oorzaken, chronologie, arbeid, kapitaal, kolonialisme, politiek, ongelijkheid en milieu ontbreken.

Wel goed:

> Koloniaal kapitaal als financieringsbron voor Britse fabrieksinvesteringen.

De eerste zin is een analyseplan. De tweede zin is een seed.

## 4. Shadow seed

Een shadow seed is een kleine, gewichtloze plekhouder voor een mogelijke afwezigheid.

Een seed heeft deze eigenschappen:

- hij bevat precies één gap
- hij is toetsbaar
- hij begint zonder invloed
- hij kan opnieuw herkend worden
- hij kan vervallen
- hij kan worden gepromoveerd
- hij kan worden gefalsificeerd

## 5. Trace en weight

SSL 4.5 gebruikt twee velden.

### Trace

`trace` meet aanwezigheid.

- Startwaarde: `2.0`
- Valt exponentieel terug
- Stijgt bij herhaalde herkenning
- Onder `0.05` wordt een seed dormant

Formule:

```text
trace_t = trace_0 * exp(-t / half_life)
```

### Weight

`weight` meet invloed.

- Startwaarde: `0.0`
- Stijgt alleen via de Validation Gate
- Daalt alleen door falsificatie of tegenspraak
- Vanaf `0.5` is een seed gepromoveerd

Belangrijk onderscheid:

```text
trace > 0  betekent: de seed is aanwezig
weight = 0 betekent: de seed stuurt nog niets
```

## 6. Statussen

| Status | Betekenis | Gedrag |
|---|---|---|
| `NEW` | net gedetecteerd | opgeslagen zonder invloed |
| `ACTIVE` | opnieuw herkend | trace stijgt |
| `DECAYING` | minder recent | trace daalt |
| `DORMANT` | slapend | geen probing, wacht op trigger |
| `PROMOTED` | gevalideerd | mag actie sturen |
| `EXPIRED` | verdwenen | wordt niet meer gebruikt |

## 7. Validation Gate

Een seed krijgt pas invloed als drie checks slagen.

### Check 1: interne herkenning

Dezelfde seed wordt meerdere keren onafhankelijk gevonden.

```text
occurrence_count >= 3
trace > 0.5
```

### Check 2: externe bevestiging

De seed krijgt steun van de gebruiker, een retrieval-resultaat, een bron of een latere context.

```text
evidence_count >= 2
```

### Check 3: tegenspraak-test

Het systeem probeert de seed te weerleggen.

Vraag:

> Waarom zou deze gap in deze context niet relevant zijn?

Alleen als de seed die test overleeft, mag de `weight` stijgen.

## 8. Probes

Een gepromoveerde seed kan drie soorten acties sturen.

| Probe | Trigger | Actie |
|---|---|---|
| Socratisch | individuele promoted seed | stel één natuurlijke vraag aan de gebruiker |
| Retrieval | zware seed of constellation | zoek gericht in documenten of database |
| Dialectisch | Validation Gate | probeer de seed intern te weerleggen |

### Socratisch voorbeeld

Seed:

> Koloniaal kapitaal als financieringsbron voor Britse fabrieksinvesteringen.

Probe:

> We hebben de technische innovaties besproken, maar welke rol speelde koloniaal kapitaal volgens u in de financiering van deze fabrieken?

## 9. Constellations

Een constellation is een cluster van verwante seeds. Seeds zelf blijven klein. De bredere samenhang ontstaat pas na clustering.

Voorwaarde:

```text
minstens 3 seeds
cosine similarity > 0.70
```

Voorbeeld van drie seeds:

1. Koloniaal kapitaal als financieringsbron voor Britse fabrieksinvesteringen.
2. Winsten uit trans-Atlantische slavenhandel als investeringskapitaal.
3. Koloniale katoen als grondstof voor de Britse textielindustrie.

Mogelijke constellation:

> Koloniale economische voorwaarden van Britse industrialisatie.

## 10. Beurtcyclus

Elke beurt doorloopt zes stappen.

1. Trigger-check op dormant seeds.
2. Eerste antwoord genereren.
3. Detectie-pass uitvoeren.
4. Brede gaps splitsen naar atomische seeds.
5. State bijwerken en Validation Gate draaien.
6. Eindantwoord maken met eventuele probe.

## 11. Twee implementatieniveaus

### Niveau 1: externe vectorruimte

Dit is direct bouwbaar.

- Seeds worden als tekst opgeslagen.
- Een embedding-model maakt vectoren.
- Een vector-database zoekt verwante seeds terug.
- `weight` bepaalt of een seed invloed krijgt.

Voorbeelden van tools: FAISS, ChromaDB, Qdrant of een eenvoudige in-memory index.

### Niveau 2: modelinterne analyse

Dit is onderzoekswerk.

- Seeds worden gekoppeld aan patronen in de forward pass.
- Open-source modellen zijn nodig.
- Interventies kunnen worden getest met activation scaling.

Niveau 2 is niet nodig om Niveau 1 te gebruiken.

## 12. Grenzen

SSL is geen waarheidsmachine. Een seed is een hypothese over afwezigheid, geen feit.

SSL faalt wanneer:

- de detectie alleen vage thema's oplevert
- brede lijsten als seeds worden opgeslagen
- de Validation Gate te licht staat
- Socratische probes te vaak of te dwingend worden gebruikt
- de gebruiker geen probing wil

## 13. Minimale werkende definitie

Een SSL-systeem voldoet aan de minimale definitie als het:

1. kleine gaps detecteert
2. brede gaps splitst
3. seeds opslaat met `trace` en `weight`
4. `weight` op `0.0` laat starten
5. promotie via de Validation Gate laat lopen
6. gepromoveerde seeds gebruikt voor een gerichte actie

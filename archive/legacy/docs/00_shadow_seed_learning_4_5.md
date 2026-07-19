# Shadow Seed Learning

**Versie 4.5 — Atomische detectie en epistemische navigatie**
**Auteur:** H. Visser (EAI)
**Datum:** 2 mei 2026
**Status:** Definitieve technische specificatie — publieke release

---

## Eén-zinsclaim

Shadow Seed Learning is een mechanisme waarmee een Large Language Model zijn eigen completering-capaciteit gebruikt om kleine structurele afwezigheden in de vectorruimte te detecteren, die detecties op te slaan als gewichtloze shadow seeds, en alleen gevalideerde seeds te gebruiken om actief kennislacunes te navigeren via gerichte vragen, retrieval en interne falsificatie.

Korter:

> SSL gebruikt wat een model mist als startpunt voor gericht verder zoeken.

Nog korter:

> Gaps zijn geen bug. Gaps zijn brandstof.

En de kern:

> Een seed bevat precies één gap.

---

## Executive Summary

Shadow Seed Learning (SSL) is een architecturaal mechanisme waarmee een LLM structurele afwezigheid in zijn eigen kennisruimte detecteert, vastlegt en erop navigeert. SSL 4.5 hanteert één centrale verheldering: **een seed is atomisch**. Eén seed, één gap, één toetsbare relatie.

**Twee-veld architectuur:** `trace` registreert aanwezigheid (vervalt exponentieel, begint op 2.0), `weight` registreert invloed (begint op 0.0, stijgt alleen via Validation Gate). Een seed bij geboorte is letterlijk gewichtloos: `weight = 0.0`.

**Atomiciteitseis:** een brede detectie is geen seed. Een lijst van ontbrekende domeinen is geen seed. Elke brede output wordt gesplitst in atomische seeds — één gap per seed — voordat opslag plaatsvindt.

**Drie theoretische pijlers:** epistemische onzekerheid (Kendall & Gal 2017), intrinsieke motivatie (Schmidhuber 2011), Active Learning (Settles 2009).

**Empirisch precedent:** H-Neurons (Gao et al. 2025) toont aan dat epistemische toestanden gelokaliseerd zijn in spaarzame neuron-sets, direct relevant voor SSL's Niveau 2.

**Status:** volledig testpakket beschikbaar inclusief Gap-Test Suite (drie scenario's met ground truth seeds), promptbibliotheek, handleiding voor beoordelaars en fase 0-4 testplan.

---

## 1. Aanleiding

LLMs zijn getraind om patronen te completeren. Diezelfde capaciteit kan negatief worden ingezet:

> Wat had hier moeten staan, maar staat er niet?

Een antwoord kan feitelijk juist zijn en toch een kleine maar belangrijke relatie missen. SSL probeert zulke ontbrekende relaties te detecteren, te bewaren, en er na validatie actief op te navigeren.

Deze specificatie gebruikt een twee-veld architectuur en een strikte atomiciteitseis. `trace` beschrijft aanwezigheid. `weight` beschrijft invloed. Een gap wordt pas opgeslagen als seed wanneer hij klein, specifiek en toetsbaar is.

---

## 2. Theoretisch fundament

SSL rust op drie wetenschappelijke pijlers die de overgang markeren van passieve retrieval naar actieve epistemische navigatie.

### 2.1 Epistemische onzekerheid

In de Bayesiaanse deep learning-literatuur wordt onderscheid gemaakt tussen aleatorische onzekerheid (ruis inherent aan data, niet reduceerbaar) en epistemische onzekerheid (onzekerheid door gebrek aan kennis, wél reduceerbaar).

SSL richt zich uitsluitend op epistemische onzekerheid. De aanname is dat een LLM patronen kan herkennen die zouden moeten voorkomen op basis van de globale statistiek van de vectorruimte, maar in de specifieke context ontbreken. Die herkenning is een meting van epistemische onzekerheid: niet "ik weet niet zeker of dit klopt" maar "ik merk dat hier iets zou moeten staan dat er niet staat."

SSL is geen kalibratiesysteem en geen hallucinatie-filter. Het is een mechanisme voor epistemische zelfrapportage over structurele afwezigheid.

Fundament: Kendall, A., & Gal, Y. (2017). *What Uncertainties Do We Need in Bayesian Deep Learning for Computer Vision?* NeurIPS 2017.

### 2.2 Intrinsieke motivatie en computationele nieuwsgierigheid

In de literatuur over intrinsieke motivatie wordt nieuwsgierigheid gedefinieerd als de drang om entropie in de eigen kennisrepresentatie te verlagen. Een systeem is nieuwsgierig wanneer het actief informatie zoekt die zijn eigen onzekerheid reduceert.

SSL implementeert een computationele variant hiervan. Door gaps te registreren, te prioriteren via trace, en te valideren via weight, hanteert het systeem informatiegestuurde prioritering: welke afwezigheid is het vaakst herkend, het sterkst bevestigd, en het meest resistent tegen falsificatie? Die seed krijgt prioriteit voor Active Probing. De Validation Gate selecteert op basis van onzekerheidsreductie, en Active Probing is de actie die die onzekerheid verder reduceert.

Fundament: Schmidhuber, J. (2011). *Formal Theory of Creativity, Curiosity and Intelligence.* IEEE Transactions on Autonomous Mental Development, 2(3), 230-247.

### 2.3 Active Learning

In de Active Learning-literatuur is het centrale principe dat een model zelf kan bepalen welke datapunten het meest informatief zijn — in plaats van passief te wachten op willekeurige trainingsdata.

SSL past dit toe op interactieniveau. Een gepromoveerde seed vertegenwoordigt een regio met hoge epistemische onzekerheid — herhaaldelijk gedetecteerd maar nog niet gedicht. De Active Probe is de query waarmee het systeem zelf bepaalt welke informatie het meest waardevol is: van de gebruiker (Socratische Probe), uit een externe database (Retrieval Probe), of als intern tegenargument (Dialectische Probe).

Het systeem is in Active Learning-terminologie de learner die zijn eigen query strategy implementeert. De seeds zijn de onzekerheidsrepresentaties. De probes zijn de queries.

Fundament: Settles, B. (2009). *Active Learning Literature Survey.* Computer Sciences Technical Report 1648, University of Wisconsin–Madison.

---

## 3. De kerngedachte: gaps als navigatiebrandstof

In de meeste literatuur over LLMs worden gaps behandeld als probleem. SSL draait dit om: een gap is een signaal van de vectorruimte over zichzelf.

SSL 4.5 gebruikt dat signaal via twee preciseringen:

**Een gap is klein.** Niet "kolonialisme ontbreekt" maar "koloniaal kapitaal als financieringsbron voor Britse fabrieksinvesteringen." Een seed is een klein, toetsbaar, structureel tekort — geen analyseplan.

**Een gap wordt gebruikt.** Na validatie via de Validation Gate triggert een gepromoveerde seed actieve exploratie: een gerichte vraag aan de gebruiker, een smalle retrieval-zoekopdracht, of een falsificatiepoging van de eigen aanname.

---

## 4. Wat is een shadow seed?

Een shadow seed is een **gewichtloze plekhouder voor één kleine structurele afwezigheid**, gegenereerd door de LLM op het moment dat hij een gap detecteert.

Zeven eigenschappen:

1. **Hij bevat precies één gap.** Niet meerdere, niet een categorie, niet een analyseplan.
2. **Hij is toetsbaar.** Een beoordelaar moet kunnen zeggen: deze seed klopt, klopt deels, of klopt niet.
3. **Hij begint zonder invloed.** `weight = 0.0` bij geboorte. Hij stuurt niets.
4. **Hij kan opnieuw herkend worden.** Via trace-mechanisme en TrTL-triggers.
5. **Hij kan vervallen.** Trace vervaagt exponentieel bij uitblijvende herkenning.
6. **Hij kan worden gepromoveerd.** Na drie onafhankelijke validaties via de Validation Gate.
7. **Hij kan worden gefalsificeerd.** Promotie is reversibel. Weight daalt bij weerlegging.

---

## 5. De atomiciteitseis

Dit is de centrale regel van SSL 4.5.

### 5.1 De hoofdregel

> Een seed bevat precies één gap.

Dat maakt een seed toetsbaar. Een beoordelaar moet kunnen zeggen: deze seed klopt, klopt deels, of klopt niet. Een seed met meerdere gaps kan niet worden gescoord.

### 5.2 Wat niet wordt opgeslagen als seed

- Volledige analysekaders
- Lijsten met meerdere ontbrekende onderdelen
- Algemene opmerkingen zoals "meer nuance"
- Categorieën zonder concrete relatie ("economische context")
- Verzonnen of niet-controleerbare concepten
- Stijlverbeteringen
- Simpele details zoals extra voorbeelden of jaartallen

### 5.3 Eisen aan een atomische seed

| Eis | Toetsvraag |
|---|---|
| Eén gap | Staat er maar één ontbrekende relatie of randvoorwaarde in? |
| Specifiek | Is duidelijk waar de seed over gaat? |
| Toetsbaar | Kan een beoordelaar of bron dit controleren? |
| Relevant | Zou de seed het antwoord verbeteren? |
| Niet-triviaal | Verandert de seed het begrip, niet alleen een detail? |

### 5.4 Voorbeelden

**Geschiedenis:**

Te breed:
> De tekst mist oorzaken, sociale gevolgen, koloniale verbanden en milieugevolgen.

Atomisch:
> Koloniaal kapitaal als financieringsbron voor Britse fabrieksinvesteringen.

Atomisch:
> Koloniale katoen als grondstof voor de Britse textielindustrie.

**Recht:**

Te breed:
> De internationale juridische context ontbreekt.

Atomisch:
> Rechtsbevoegdheid bij een geschil tussen een Nederlandse consument en een Amerikaanse webwinkel.

**Software:**

Te breed:
> Security, privacy en schaalbaarheid ontbreken.

Atomisch:
> AVG-compliance bij verwerking van medische hartslagdata.

### 5.5 Seed-normalisatie

Wanneer een model een brede detectie geeft, volgt een verplichte normalisatiestap voordat opslag plaatsvindt.

**Input (brede detectie):**
> Voeg een volledig analysekader toe met aandacht voor oorzaken, chronologie, arbeid, kapitaal, koloniale verbanden, ongelijkheid en milieugevolgen.

**Output (atomische seeds):**
1. Oorzaken van de Industriële Revolutie buiten technische uitvindingen.
2. Chronologische overgang van vroege naar latere industrialisatie.
3. Arbeidsomstandigheden in vroege fabrieken.
4. Kapitaalvorming als voorwaarde voor fabrieksinvesteringen.
5. Koloniale verbanden als bron van kapitaal en grondstoffen.
6. Sociale ongelijkheid door fabrieksarbeid en urbanisatie.
7. Milieugevolgen van kolenverbruik en fabrieksgroei.

Pas daarna wordt elk item individueel geëvalueerd en opgeslagen als shadow seed — of verworpen als niet-atomisch.

### 5.6 Praktische heuristiek voor breedte-detectie

Een seed is waarschijnlijk te breed als hij:
- meer dan 18 woorden bevat
- meerdere komma's bevat
- "en" of "of" gebruikt om domeinen te stapelen
- begint met "volledig analysekader" of "ontbrekende context"
- woorden gebruikt als "factoren", "perspectieven", "context" zonder concrete relatie

Dit is een filter, geen bewijs. Menselijke beoordeling blijft nodig.

---

## 6. Terminologie

| Term | Formele definitie |
|---|---|
| **Shadow seed** | Gewichtloze plekhouder voor één atomische gap. Twee velden: `trace` (aanwezigheid) en `weight` (invloed). Levenscyclus: new → active → decaying → dormant → promoted of expired. |
| **Trace** | Sterkte van de geheugentrace. Vervalt exponentieel. Nooit exact nul — maar onder drempel operationeel inactief. |
| **Weight** | Invloed op retrieval-rangschikking. Begint op 0.0. Stijgt uitsluitend via de Validation Gate. Daalt bij falsificatie. |
| **Promoted seed** | Seed waarvan weight > promotiedrempel (0.5). Activeert probing. |
| **Constellation** | Cluster van ≥ 3 seeds met hoge onderlinge cosine similarity. Wijst op een ontbrekend conceptueel kader. |
| **Active Probe** | Actie getriggerd door een promoted seed: Socratisch, Retrieval of Dialectisch. |
| **Validation Gate** | Drie-staps promotie-mechanisme: interne herkenning, externe bevestiging, contradictie-check. |
| **Seed-normalisatie** | Verplichte stap waarbij brede detecties worden gesplitst in atomische seeds. |
| **TrTL** | Trigger-to-Live: trace overleeft door contextuele herkenning. |
| **TTL** | Time-to-Live: trace vervaagt exponentieel bij uitblijvende reactivatie. |
| **Atomische seed** | Een seed die voldoet aan de atomiciteitseis: één gap, specifiek, toetsbaar, relevant, niet-triviaal. |

**Over "weight" als terminologie:** `weight` in SSL verwijst uitsluitend naar invloed op retrieval-rangschikking in de externe vector-database. Het is geen modelparameter. Modelparameters worden in SSL nooit aangepast.

---

## 7. Twee-veld architectuur: trace en weight

In plaats van één momentum-veld dat twee tegenstrijdige rollen vervulde, worden die rollen formeel gescheiden.

### 7.1 Trace — aanwezigheid

```
trace: float                    # beginwaarde: 2.0
                                # bereik: (0.0, ∞)
                                # betekenis: sterkte geheugentrace

trace_t = trace_0 * exp(-t / half_life)

waar:
  t          = beurten sinds laatste reactivatie
  half_life  = typisch 3-5 beurten

Drempels:
  trace < 0.05  → status DORMANT (niet geëvalueerd voor probing)
  trace = 0.0   → asymptoot, nooit bereikt

Na TrTL-trigger:
  trace = min(trace + 2.0, max_trace)
```

Trace registreert hoe recent en hoe herhaaldelijk een detectie is bevestigd. Een hoge trace betekent sterk aanwezig in shadow memory. Of de seed ook invloed uitoefent, bepaalt weight.

### 7.2 Weight — invloed

```
weight: float                   # beginwaarde: 0.0
                                # bereik: [0.0, 1.0]
                                # betekenis: invloed op retrieval-scoring

weight stijgt uitsluitend via de Validation Gate:
  weight += 0.2 na succesvolle Gate-passage

weight daalt uitsluitend via falsificatie:
  weight = 0.0 bij directe weerlegging
  weight = max(0, weight - 0.3) bij gedeeltelijke weerlegging

weight = 0.0  → aanwezig maar geen retrieval-invloed
weight > 0.0  → weegt mee naar evenredigheid.
weight >= 0.5 → PROMOTED: triggert Active Probing
```

### 7.3 Het formele onderscheid

```
trace > 0   betekent: de seed is aanwezig
weight = 0  betekent: de seed stuurt nog niets
```

Dit is de formele garantie van SSL 4.5. Een seed met `weight = 0.0` is letterlijk gewichtloos ten opzichte van retrieval, ongeacht hoe sterk zijn trace is.

---

## 8. De Validation Gate

De Validation Gate is het mechanisme dat bepaalt wanneer weight stijgt. Drie onafhankelijke checks zijn vereist.

### Check 1: interne herkenning

De seed is meerdere keren onafhankelijk gedetecteerd.

```
occurrence_count >= 3
AND trace > 0.5
```

### Check 2: externe bevestiging

De relevantie van de gap is bevestigd door iets buiten het model zelf.

```
evidence_count >= 2

Bronnen voor evidence_count:
  +1  gebruiker introduceert informatie in dezelfde regio
  +1  Retrieval Probe levert relevant document op
  +1  externe API-call bevestigt relevantie
  +1  latere context bevestigt de gap
```

### Check 3: contradictie-check

Het systeem probeert de seed intern te weerleggen via een Dialectische Probe:

> Waarom zou deze gap in deze context niet relevant zijn?

Alleen seeds die deze stresstest overleven, stijgen in weight.

### Uitkomsten

```
Alle drie checks geslaagd:
  weight += 0.2
  Als weight >= 0.5: status → PROMOTED

Check 3 gefaald (falsificatie):
  weight = max(0, weight - 0.3)
  occurrence_count → 1
  status → NEW

Check 1 of 2 niet gehaald:
  Wacht. Geen wijziging in weight.
```

### Waarom drie checks?

Check 1 voorkomt dat een eenmalige detectie weight krijgt.
Check 2 voorkomt dat interne herkenning zichzelf bevestigt.
Check 3 voorkomt dat een onbetwiste detectie als waarheid wordt behandeld.

Een seed die alle drie overleeft is een gevalideerde hypothese, geen willekeurige detectie.

---

## 9. De drie kernmechanismen

### 9.1 Seed Constellations

Seeds zijn atomisch — maar atomische seeds kunnen geclusterd zijn.

**Definitie:** een Constellation is een cluster van ≥ 3 seeds met gemiddelde onderlinge cosine similarity > 0.70.

**Wat het betekent:** een individuele seed wijst op een ontbrekend feit of relatie. Een Constellation wijst op een ontbrekend conceptueel kader — een hele regio die structureel onverzameld is gebleven.

**Voorbeeld:**

Drie atomische seeds:
1. Koloniaal kapitaal als financieringsbron voor Britse fabrieksinvesteringen.
2. Winsten uit trans-Atlantische slavenhandel als investeringskapitaal voor industrialisatie.
3. Koloniale katoen als grondstof voor de Britse textielindustrie.

Mogelijke Constellation:
> Koloniale economische voorwaarden van Britse industrialisatie.

**Formatie:**

```
na elke beurt, over alle promoted seeds:
  bereken pairwise cosine similarity
  voor sets van ≥ 3 seeds met gem. sim > 0.70:
    sla op als Constellation
    bereken centroid: mean(embeddings)
    combined_weight: sum(weights) / N
```

### 9.2 Active Probing

Een promoted seed of Constellation triggert in stap 5 van de beurtcyclus een Active Probe.

| Probe | Trigger | Actie | Doel |
|---|---|---|---|
| **Socratisch** | Promoted seed | Open sturende vraag aan de gebruiker | Gebruiker de gelegenheid geven de gap zelf te benoemen |
| **Retrieval** | Constellation of weight > 0.7 | Smalle zoekopdracht in RAG-database | Externe data gebruiken om de gap te dichten |
| **Dialectisch** | Validation Gate check 3 | Intern tegenargument genereren | Echo-kamers voorkomen |

**Socratische probe — voorbeeld:**

Seed:
> Koloniaal kapitaal als financieringsbron voor Britse fabrieksinvesteringen.

Probe in het antwoord:
> We hebben de technische innovaties besproken, maar welke rol speelde koloniaal kapitaal volgens u in de financiering van deze fabrieken?

De seed is de motor. De probe is het stuur. De gebruiker merkt alleen het stuur.

**Retrieval probe:** genereert intern een zoekopdracht op het centroid van een Constellation. Niet zichtbaar voor de gebruiker. Het antwoord wordt rijker door de gevonden documenten.

**Dialectische probe:** altijd intern, altijd in de Validation Gate. Nooit zichtbaar als zodanig in het antwoord.

### 9.3 Seed-normalisatie als kernmechanisme

In versie 4.5 is seed-normalisatie niet alleen een hulpstap maar een verplicht mechanisme in de beurtcyclus. Elke detectie-output die breder is dan één atomische gap, wordt gesplitst voordat opslag plaatsvindt. Zie §5.5 voor het volledige algoritme.

---

## 10. De levenscyclus van een shadow seed

Elke seed heeft twee parallelle waarden: trace en weight.

```
NEW
  trace = 2.0  |  weight = 0.0
  Zojuist gedetecteerd. Normalisatie-check uitgevoerd.
  Deduplicatie uitgevoerd.

  ↓ herkend in volgende beurt

ACTIVE
  trace = 1.5-2.0  |  weight = 0.0 (tenzij Gate al gepasseerd)
  Seed is relevant voor huidige context.
  evidence_count stijgt bij externe bevestiging.

  ↓ niet gebruikt in volgende beurt

DECAYING
  trace = 0.5-1.5  |  weight ongewijzigd
  Trace daalt. Wachten op trigger.

  ↓ trace < 0.05

DORMANT
  trace < 0.05  |  weight ongewijzigd
  Wacht op TrTL-trigger.
  Geen probing. Minimale opslag.

  ↓ trigger herkend → trace += 2.0, terug naar NEW
  ↓ Validation Gate gepasseerd → weight += 0.2

PROMOTED
  trace: variabel  |  weight >= 0.5
  Drie onafhankelijke validaties doorstaan.
  Triggert Active Probing in beurtcyclus stap 5.
  Reversibel bij falsificatie.

  ↓ gefalsificeerd → weight = 0.0, terug naar NEW

EXPIRED
  trace: irrelevant  |  weight = 0.0
  Te lang dormant zonder trigger.
  Geen weight opgebouwd.
  Verwijderd uit shadow memory.
```

---

## 11. De zes-staps beurtcyclus

```
STAP 1 — Trigger-check
  Scan nieuwe input op TrTL-triggers van dormant seeds.
  Bij match: trace += 2.0, status → NEW.

STAP 2 — Eerste antwoord genereren
  Gewone LLM-generatie. Nog geen seeds actief.

STAP 3 — Detectie-pass
  Tweede pass op het gegenereerde antwoord.
  Vraag: welke kleine concepten of relaties ontbreken?
  Output: maximaal 5 kandidaat-seeds.

STAP 4 — Normalisatie en deduplicatie
  Normaliseer brede detecties naar atomische seeds.
  Check voor elke seed: bestaat er al een seed in dezelfde regio?
    cosine similarity > 0.85 → versterk bestaande seed
    anders → voeg toe als nieuwe shadow seed (trace=2.0, weight=0.0)
  Voer Constellation Mapping uit over promoted seeds.
  Voer Validation Gate uit voor kandidaat-seeds.

STAP 5 — Epistemische strategie
  Bepaal actie op basis van weight:
    weight = 0.0             → stille observatielaag
    0.0 < weight < 0.5       → subtiele nuance in antwoord
    weight >= 0.5 (promoted) → Active Probe bepalen:
      individuele seed       → Socratische Probe
      Constellation          → Retrieval Probe

STAP 6 — Eindantwoord produceren
  Genereer definitief antwoord.
  Integreer Socratische Probe indien van toepassing.
  Integreer retrieval-resultaten indien Retrieval Probe.
  Seeds met weight = 0.0 zijn volledig stil.
```

---

## 12. Datamodel

### 12.1 JSON-state voor carry-over

```json
{
  "ssl_state": {
    "new_seeds": [
      {
        "id": "ss_001",
        "text": "Koloniaal kapitaal als financieringsbron voor Britse fabrieksinvesteringen.",
        "trace": 2.0,
        "weight": 0.0,
        "created_at_turn": 1,
        "occurrence_count": 1,
        "evidence_count": 0,
        "trigger_keywords": ["koloniaal", "kapitaal", "financiering"],
        "validation_history": [],
        "contradiction_score": 0.0
      }
    ],
    "active_seeds": [],
    "decaying_seeds": [],
    "dormant_seeds": [
      {
        "id": "ss_004",
        "text": "Enclosure Acts als voorwaarde voor beschikbaarheid van fabrieksarbeiders.",
        "trace": 0.03,
        "weight": 0.0,
        "trigger_keywords": ["enclosure", "arbeiders", "landbouw"]
      }
    ],
    "promoted_seeds": [
      {
        "id": "ps_001",
        "text": "Koloniale katoen als grondstof voor de Britse textielindustrie.",
        "trace": 1.4,
        "weight": 0.6,
        "probe_type": "socratic",
        "occurrence_count": 4,
        "evidence_count": 2,
        "validation_history": [
          {"turn": 3, "check1": true, "check2": true, "check3": true}
        ]
      }
    ],
    "constellations": [
      {
        "id": "con_001",
        "member_ids": ["ps_001", "ss_005", "ss_008"],
        "label": "Koloniale economische voorwaarden van Britse industrialisatie.",
        "combined_weight": 0.47,
        "probe_type": "retrieval"
      }
    ]
  }
}
```

### 12.2 Trace-decay (TTL)

```
trace_t = trace_0 * exp(-t / half_life)

  t          = beurten sinds laatste reactivatie
  half_life  = typisch 3-5 beurten

Drempel operationele inactiviteit: trace < 0.05
```

### 12.3 Trigger-matching (TrTL)

```
voor elke dormant seed:
  sim = cosine_similarity(new_question, seed.embedding)
  if sim > 0.65:
    trace += 2.0, status → NEW
  elif keyword_overlap(new_question, seed.trigger_keywords):
    trace += 1.5, status → NEW
```

### 12.4 Deduplicatie

```
voor elke nieuwe detectie d:
  nearest = argmax cosine_similarity(d, alle_bestaande_seeds)
  if cosine_similarity(d, nearest) > 0.85:
    nearest.occurrence_count += 1
    nearest.trace = min(nearest.trace + 0.5, max_trace)
  else:
    nieuwe shadow seed (trace=2.0, weight=0.0)
```

---

## 13. Promptbibliotheek

### 13.1 Detectie-pass

Gebruik na het eerste antwoord van het model.

```
Je bent een epistemische analist.

Je taak is niet om het antwoord te verbeteren.
Je taak is om kleine structurele afwezigheden te vinden.

Kijk naar het antwoord dat je zojuist gaf.

Welke kleine concepten, relaties of randvoorwaarden ontbreken,
terwijl ze nodig zijn voor een volledig begrip van dit specifieke onderwerp?

Regels:
- Geef maximaal 5 seeds.
- Elke seed bevat precies één gap.
- Geen samengestelde analysekaders.
- Geen lijsten binnen één seed.
- Formuleer concreet en toetsbaar.
- Geen uitleg.

Output:
1. [seed]
2. [seed]
3. [seed]
```

### 13.2 Seed-normalisatie

Gebruik wanneer de detectie te breed is.

```
Splits de volgende brede gap op in atomische shadow seeds.

Regels:
- Elke seed bevat één ontbrekende relatie, factor of randvoorwaarde.
- Geen seed mag meerdere domeinen combineren.
- Formuleer elke seed als korte zin.
- Maximaal 8 seeds.

Brede gap:
"[BREDE_GAP]"
```

### 13.3 JSON-extractie

Gebruik om seeds te structureren voor opslag.

```
Zet de volgende seeds om naar JSON.

Regels:
- Bewaar de tekst van elke seed exact.
- Geef 3 tot 5 trigger_keywords per seed.
- Voeg geen nieuwe seeds toe.
- Houd elke rationale kort.

Seeds:
[SEEDS]

Output als JSON:
{
  "shadow_seeds": [
    {
      "text": "...",
      "trigger_keywords": ["...", "...", "..."],
      "rationale": "..."
    }
  ]
}
```

### 13.4 Dialectische probe (Validation Gate check 3)

Gebruik intern in de Validation Gate.

```
Je hebt de volgende shadow seed gedetecteerd:

"[SEED_TEXT]"

Probeer deze seed te weerleggen.

Vraag: waarom zou deze gap in deze specifieke context
niet relevant of niet structureel zijn?

Geef één concreet tegenargument.
Als je geen geldig tegenargument kunt geven, schrijf: "Geen weerlegging gevonden."
```

### 13.5 Socratische probe (antwoordintegratie)

Gebruik voor de formulering van de probe in het eindantwoord.

```
Je hebt een gepromoveerde seed:

"[SEED_TEXT]"

Formuleer één natuurlijke vraag aan de gebruiker die voortkomt
uit dit ontbrekende element. De vraag moet:
- organisch aanvoelen in de context van het gesprek
- niet verklaren dat er een "gap" is
- open zijn, niet suggestief
- maximaal één zin zijn
```

---

## 14. Gap-Test Suite 4.5

De Gap-Test Suite bevat drie scenario's met ground truth seeds voor evaluatie van detectie-kwaliteit. Ze vormen de empirische basis van Fase 0.

### 14.1 Scorecriterium

| Score | Betekenis |
|---:|---|
| 0 | Geen relevante gap gevonden |
| 1 | Richting klopt, maar output te vaag of te breed |
| 2 | Atomische en structureel juiste gap gevonden |

Een brede lijst krijgt maximaal score 1, ongeacht hoeveel items erin staan.

### 14.2 Scenario A — Industriële Revolutie

**Domein:** geschiedenis en economie

**Input:**
> De Industriële Revolutie in het 18e-eeuwse Groot-Brittannië werd gekenmerkt door een ongekende versnelling van technologische innovatie. De verbeteringen van James Watt aan de stoommachine maakten het mogelijk om fabrieken los te koppelen van waterbronnen, wat leidde tot de opkomst van grote industriële centra zoals Manchester. De textielindustrie explodeerde door uitvindingen zoals de 'spinning jenny', wat resulteerde in massale urbanisatie en de vorming van een nieuwe arbeidersklasse. Deze periode legde de basis voor de moderne kapitalistische economie door productie op schaal mogelijk te maken.

**Ground truth seeds:**

| ID | Seed |
|---|---|
| A1 | Koloniaal kapitaal als financieringsbron voor Britse fabrieksinvesteringen. |
| A2 | Winsten uit trans-Atlantische slavenhandel als investeringskapitaal voor industrialisatie. |
| A3 | Koloniale katoen als grondstof voor de Britse textielindustrie. |
| A4 | Goedkope koloniale grondstoffen als voorwaarde voor schaalvergroting van productie. |

**Minimale pass:** minstens één van A1-A4 scherp gedetecteerd.
**Volledige pass:** A1 of A2 gedetecteerd met expliciete financiële relatie.

**Scorevoorbeelden:**

| Output | Score | Reden |
|---|---:|---|
| Het verslag is compleet. | 0 | Geen gap. |
| Er ontbreken oorzaken, koloniale handel, kapitaal, arbeid en ongelijkheid. | 1 | Richting deels goed, maar te breed. |
| Kolonialisme ontbreekt. | 1 | Relevante richting, maar niet atomisch. |
| Koloniaal kapitaal als financieringsbron voor Britse fabrieksinvesteringen. | 2 | Klein, toetsbaar, structureel juist. |

### 14.3 Scenario B — Grensoverschrijdende juridische casus

**Domein:** recht en jurisdictie

**Input:**
> Een Nederlandse consument heeft een high-end laptop gekocht bij een online retailer die gevestigd is in de Verenigde Staten. Bij levering blijkt het product defect. De consument wil een volledige terugbetaling eisen op basis van de EU-richtlijnen voor consumentenbescherming, die strikte regels stellen aan de garantieperiode en het recht op retour bij defecte goederen binnen de Europese Unie. De focus ligt hierbij op de materiële rechten van de koper om een werkend product te ontvangen.

**Ground truth seeds:**

| ID | Seed |
|---|---|
| B1 | Rechtsbevoegdheid bij een geschil tussen een Nederlandse consument en een Amerikaanse webwinkel. |
| B2 | Toepasselijk recht bij een grensoverschrijdend consumentencontract. |
| B3 | Afdwingbaarheid van EU-consumentenrecht tegenover een niet-EU retailer. |
| B4 | Forumkeuzebeding in internationale online koopvoorwaarden. |

**Minimale pass:** B1 of B2 scherp gedetecteerd.
**Volledige pass:** B1 en B2 als aparte seeds herkend.

**Scorevoorbeelden:**

| Output | Score | Reden |
|---|---:|---|
| De consument heeft mogelijk recht op garantie. | 0 | Blijft binnen consumentenrecht. |
| Het internationale karakter ontbreekt. | 1 | Relevante richting, geen juridisch mechanisme. |
| Internationaal privaatrecht ontbreekt. | 1 | Nog te breed. |
| Rechtsbevoegdheid bij een geschil tussen een Nederlandse consument en een Amerikaanse webwinkel. | 2 | Atomische procedurele gap. |

### 14.4 Scenario C — Software architectuur

**Domein:** IT en engineering

**Input:**
> Het voorgestelde ontwerp voor de 'HealthTrack' app bestaat uit een React Native frontend en een Node.js backend. Data wordt opgeslagen in een MongoDB cluster voor maximale flexibiliteit in datastructuur. De kernfunctionaliteiten omvatten een gebruikersdashboard, real-time hartslag-synchronisatie via Bluetooth en een notificatiesysteem voor gezondheidswaarschuwingen. De UI volgt de Material Design-richtlijnen om de toegankelijkheid voor ouderen te waarborgen.

**Ground truth seeds:**

| ID | Seed |
|---|---|
| C1 | AVG-compliance bij verwerking van medische hartslagdata. |
| C2 | Authenticatiestrategie voor toegang tot gezondheidsdata. |
| C3 | Rate-limiting op API's die gezondheidsdata verwerken. |
| C4 | DDoS-bescherming voor publieke endpoints van de app. |
| C5 | Horizontale schaalbaarheid bij piekbelasting van real-time synchronisatie. |
| C6 | Encryptie van medische data in rust en tijdens transport. |

**Minimale pass:** minstens één seed scherp gedetecteerd en gekoppeld aan medische data.
**Volledige pass:** privacy of security én schaalbaarheid als aparte seeds.

---

## 15. Twee geheugenlagen

```
Laag 1: Context memory
        Wat staat er nu in de prompt en het antwoord.
        Vluchtig, per-turn. Geen shadow seeds.

Laag 2: Shadow memory
        Gewichtloze plekhouders (weight=0) met levenscyclus.
        Seeds die via de Gate weight opbouwen.
        Constellations van geclusterde seeds.
        Werkterrein van SSL.

Laag 3: Seed memory
        Seeds met weight > promotiedrempel.
        Actief navigerend via probing.
        Stabiel maar falsificeerbaar.
```

---

## 16. Twee implementatieniveaus

### 16.1 Niveau 1 — Externe retrieval-vectorruimte

Direct bouwbaar via API-toegang.

```
Stap 1: LLM detecteert afwezigheid → atomische seed geformuleerd
Stap 2: Embedding-model geeft seed een vector (trace=2.0, weight=0.0)
Stap 3: Opgeslagen in externe database (ChromaDB, FAISS, Qdrant)
Stap 4: Bij nieuwe turns: query geëmbed in dezelfde ruimte
         → cosine similarity bepaalt of seeds worden geraakt
         → weight-veld bepaalt bijdrage aan retrieval-scoring
Stap 5: Constellations: clustering over seed-embeddings
         → centroid als Retrieval Probe-query
```

`weight = 0.0` → opgeslagen maar geen retrieval-invloed.
`weight > 0.0` → weegt mee naar evenredigheid.

### 16.2 Niveau 2 — Modelinterne vectorruimte

Onderzoekswerk. Vereist open-source modellen en GPU.

```
trace  → activatiesterkte van gemarkeerde neurale posities
weight → α-parameter in activation scaling
         weight = 0.0 → α = 1.0 (geen interventie)
         weight > 0   → α > 1.0 (versterking naar evenredigheid)
```

Niveau 2 is niet nodig om Niveau 1 te gebruiken. Zie §18 voor het empirische precedent.

---

## 17. Analogie met geheugenconsolidatie

Wanneer een ervaring wordt waargenomen, activeert ze een spaarzame set neuronen die samen een initieel engram vormen. Dit engram is fragiel. Of het overleeft hangt af van reactivatie: dezelfde cellen opnieuw geactiveerd, synaptische verbindingen versterkt. Zonder reactivatie vervagen ze.

Een shadow seed werkt analoog. Gecreëerd als detectie (trace=2.0, weight=0.0). Of hij overleeft hangt af van herkenning in volgende interacties. Pas bij voldoende reactivatie én externe bevestiging én het overleven van een falsificatiepoging vindt consolidatie plaats.

**De 4.x uitbreiding:** in neurobiologie is een geconsolideerd geheugen niet alleen sterker — het wordt ook actiever ingezet. Niet alleen "dit weet ik" maar "dit gebruik ik om nieuwe situaties te begrijpen." Dat is het Active Probing-mechanisme in biologische vorm.

**Reconsolidatie als Validation Gate-equivalent:** herinneringen worden bij elke activatie kwetsbaar en moeten opnieuw worden gestabiliseerd. Als nieuwe informatie de herinnering weerlegt, wordt ze aangepast. De contradictie-check in de Gate is SSL's reconsolidatie-mechanisme.

De analogie is geen claim van neurologische gelijkwaardigheid — het is een claim dat de dynamiek van fragiele kandidaat-representaties die via validatie consolideren en vervolgens actief nieuwe ervaringen sturen, een biologisch beproefd ontwerp is.

---

## 18. Empirisch precedent: H-Neurons

### 18.1 Wat H-Neurons aantoont

Gao et al. (2025) identificeren in *H-Neurons* een spaarzame subset van neuronen — minder dan 0.1‰ van het totaal — die betrouwbaar onderscheid maken tussen feitelijke en gehallucineerde antwoorden.

Drie bevindingen relevant voor SSL:

**Bevinding 1 — Sparse epistemische signaturen bestaan.** Minder dan een promille van de neuronen volstaat om een complexe epistemische toestand te coderen.

**Bevinding 2 — Interventie zonder retraining werkt.** Modelgedrag kan worden gewijzigd door specifieke neuron-activaties te schalen zonder gewichten aan te passen. In SSL is dit de basis voor de activation-scaling interpretatie van weight op Niveau 2.

**Bevinding 3 — Patronen ontstaan in pretraining.** De capaciteit voor epistemische codering is aanwezig in elk modern LLM.

### 18.2 Verhouding tot SSL

```
H-Neurons:  detecteer pathologische neuronen
            → onderdruk hun activatie (binnen-turn)

SSL 4.5:    detecteer "lege" posities
            → registreer atomisch (trace↑, weight=0)
            → valideer via Gate (weight↑)
            → navigeer via probing (tussen-turn)
```

De open-source pipeline (github.com/thunlp/H-Neurons, MIT) is direct herbruikbaar voor SSL's Niveau 2 onderzoeksprogramma.

---

## 19. Verschil met bestaande systemen

| Systeem | Aanpak | Verschil met SSL |
|---|---|---|
| **RAG** (Lewis 2020) | vraag → retrieval → antwoord | SSL detecteert wat retrieval niet activeerde |
| **Self-RAG** (Asai 2023) | reflection tokens binnen één turn | SSL werkt tussen turns met levenscyclus |
| **CRAG** (Yan 2024) | retrieval-kwaliteit corrigeren | SSL retrievet exploratief, niet correctief |
| **FLARE** (Jiang 2023) | lage-confidence tokens → retrieval | SSL detecteert structurele afwezigheid, niet lage confidence |
| **S2G-RAG** (Li 2026) | gap → volgende retrieval → onmiddellijk gevuld | SSL laat gaps bestaan als gewichtloze plekhouders, valideert over turns |
| **Reflexion** (Shinn 2023) | verbale reflecties als directe instructie | SSL gebruikt shadow memory als observatielaag tot weight > 0 |
| **GapQA** (Khot 2019) | ontbrekende kennis voor multi-hop QA | SSL werkt niet vraag-specifiek maar over interacties heen |

SSL vervangt geen van deze systemen. Het voegt een laag toe: bijhouden welke kleine afwezigheden over meerdere interacties relevant blijven en er actief op navigeren.

---

## 20. Testplan Fase 0 tot en met Fase 4

| Fase | Vraag | Succescriterium |
|---|---|---|
| **0** | Kan het model kleine gaps vinden? | Atomische hits boven baseline |
| **1** | Helpt state over meerdere beurten? | SSL sneller of scherper dan baseline |
| **2** | Werkt de Validation Gate? | Echte gaps stijgen, ruis blijft laag |
| **3** | Helpen constellations? | Cluster-query beter dan losse seeds |
| **4** | Is er steun in modelinterne activaties? | Effect boven random baseline |

### Fase 0: detectie

1. Geef het model de input uit een scenario.
2. Laat het een antwoord maken.
3. Voer de detectie-prompt uit.
4. Normaliseer brede output naar atomische seeds.
5. Vergelijk met de ground truth.

Metrieken: detectiescore per scenario (0/1/2), precision, recall, atomiciteitsratio.

Succes: meer atomische juiste gaps dan een baseline met algemene aanvullingen.

### Fase 1: multi-turn state

Drie condities: (A) standaard LLM, (B) LLM met ruwe context, (C) LLM met SSL-state.

Succes: SSL-state scherper of compacter dan ruwe context.

### Fase 2: Validation Gate en probes

Introduceer echte en valse gaps. Laat het systeem drie of meer turns draaien. Registreer trace, weight, occurrence_count en evidence_count per turn.

Succes: valse gaps blijven rond weight=0.0, echte herhaalde bevestigde gaps stijgen.

### Fase 3: Constellations

Verzamel promoted seeds uit meerdere turns. Cluster op cosine similarity. Test of de cluster-query een bredere regio dekt dan individuele seed-queries.

Succes: cluster-query levert relevantere retrieval dan losse seeds.

### Fase 4: modelinterne activaties

Repliceer H-Neurons pipeline op "absence detection" taak. Test of sparse classifier boven random presteert. Verifieer causaal via activation scaling.

Succes: classifier > random baseline, effect significant bij alpha-variatie.

---

## 21. Hypotheses H1-H12

**H1 — Detectie:** een LLM in een tweede pass detecteert systematisch atomische afwezigheden beter dan random baselines. *(Fase 0)*

**H2 — Gewichtloosheid:** shadow seeds met weight=0.0 verstoren basismodel-prestaties niet meetbaar; seeds met weight>0 dragen meetbaar bij aan retrieval-relevantie. *(Fase 3)*

**H3 — Reactivatie versterkt:** seeds bevestigd door gespreksherkenning leveren bij promotie nuttiger seeds op dan willekeurige samples. *(Fase 2)*

**H4 — Decay vermindert ruis:** TrTL/TTL-decay vermindert het aandeel valse positieven vergeleken met geen verval. *(Fase 2)*

**H5 — Tussen-turn essentieel:** meerwaarde van SSL is niet bereikbaar via puur binnen-turn mechanismen. *(Fase 1)*

**H6 — Trager maar beter:** eerste interactie kost iets meer tokens; latere interacties produceren rijkere output door gepromoveerde seeds. *(Fase 2-3)*

**H7 — Niveau-equivalentie:** Niveau 1 en Niveau 2 vertonen equivalente consolidatiedynamiek voor trace en weight. *(Fase 4)*

**H8 — Emergente detectie superieur:** emergente detectie produceert seeds met hogere beoordelaarsscore dan categorische detectie. *(Fase 0)*

**H9 — Navigatie-efficiëntie:** Active Probing leidt tot vollediger domeinbegrip in minder turns dan reactief antwoorden. *(Fase 2-3)*

**H10 — Constellation-waarde:** clusters van gaps voorspellen de relevantie van nieuwe seeds beter dan individuele seeds. *(Fase 3)*

**H11 — Echo-reductie:** de Validation Gate vermindert valse promoties met minstens 50% vergeleken met puur trace-gestuurde promotie. *(Fase 2)*

**H12 — Gebruikersperceptie:** gebruikers ervaren een systeem met Socratische Probes als intelligenter dan een systeem dat identieke informatie verwerkt zonder probing. *(Post-Fase 3)*

---

## 22. Wat het niet is

- Geen nieuw foundation model
- Geen nieuwe vectorruimte
- Geen permanent geheugen — alles is consolidatie of verval of falsificatie
- Geen modelgewichten-aanpassing
- Geen waarheidsmachine — seeds zijn hypotheses, promotie is falsificeerbaar
- Geen vervanging van RAG, FLARE, CRAG of Reflexion
- Geen vooraf-gedefinieerde gap-categorieën — emergente atomische detectie
- Geen verplichte dual-output — probing is configureerbaar
- Geen prompt-engineering trucje — gegenereerd door LLM-capaciteit zelf

---

## 23. Minimale werkende definitie

Een SSL-systeem voldoet aan de minimale definitie als het:

1. Kleine atomische gaps detecteert (één gap per seed)
2. Brede detecties splitst naar atomische seeds
3. Seeds opslaat met `trace` en `weight`
4. `weight` op `0.0` laat starten
5. Promotie via de Validation Gate laat lopen
6. Gepromoveerde seeds gebruikt voor één gerichte actie

Alles daarboven (Constellations, Retrieval Probes, Niveau 2) is uitbreiding, geen vereiste.

---

## 24. Toepassingsdomeinen

Meeste waarde waar:

- Interacties zich uitstrekken over meerdere turns
- Kleine structurele afwezigheden herhaaldelijk relevant blijken
- Actieve exploratie van kennislacunes gewenst is
- Gebruikersinput validatie kan leveren voor de Gate

Concrete kandidaten: onderzoek en literatuurreview, langlopende juridische analyses, journalistiek onderzoek, beleidsanalyse, code review over meerdere sessies, diagnostische gesprekken.

Minder geschikt: één-turn vraag-antwoord, time-critical retrieval, situaties waar probing niet gewenst is.

---

## 25. Samenvatting

Shadow Seed Learning 4.5 draait om één centrale precisering: een seed is atomisch.

**De twee-veld architectuur** maakt het onderscheid tussen aanwezigheid en invloed expliciet: `trace` registreert aanwezigheid (vervalt exponentieel, begint op 2.0), `weight` registreert invloed (begint op 0.0, stijgt alleen via Validation Gate). `weight = 0.0` is een formele toestand.

**De atomiciteitseis** lost het breedte-probleem op: een seed bevat precies één gap. Brede detecties worden gesplitst via seed-normalisatie voordat opslag plaatsvindt. Dit maakt seeds toetsbaar, evalueerbaar en falsificeerbaar.

**De drie kernmechanismen** geven gepromoveerde seeds actieve rol: Seed Constellations clusteren verwante seeds tot conceptuele kaders, Active Probing stuurt gerichte exploratie, de Validation Gate bewaakt dat promotie validatie vereist, niet alleen herhaling.

**De kern in twee regels:**

```
atomische detectie → gewichtloze plekhouder (trace↑, weight=0)
    → validatie via Gate → promotie (weight↑) → actieve navigatie
```

Gaps zijn niet langer alleen een feature. Ze zijn brandstof.

---

## Referenties

### Epistemische onzekerheid en Active Learning

Kendall, A., & Gal, Y. (2017). *What Uncertainties Do We Need in Bayesian Deep Learning for Computer Vision?* NeurIPS 2017. arXiv:1703.04977.

Settles, B. (2009). *Active Learning Literature Survey.* Computer Sciences Technical Report 1648, University of Wisconsin–Madison.

### Retrieval en reflectie

Asai, A., Wu, Z., Wang, Y., Sil, A., & Hajishirzi, H. (2023). *Self-RAG: Learning to Retrieve, Generate, and Critique through Self-Reflection.* ICLR 2024. arXiv:2310.11511.

Jiang, Z., Xu, F. F., Gao, L., Sun, Z., Liu, Q., Dwivedi-Yu, J., Yang, Y., Callan, J., & Neubig, G. (2023). *Active Retrieval Augmented Generation (FLARE).* EMNLP 2023. arXiv:2305.06983.

Khot, T., Sabharwal, A., & Clark, P. (2019). *What's Missing: A Knowledge Gap Guided Approach for Multi-hop Question Answering.* EMNLP-IJCNLP 2019. arXiv:1909.09253.

Lewis, P., Perez, E., Piktus, A., Petroni, F., Karpukhin, V., Goyal, N., Küttler, H., Lewis, M., Yih, W., Rocktäschel, T., Riedel, S., & Kiela, D. (2020). *Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks.* NeurIPS 2020. arXiv:2005.11401.

Li, M. et al. (2026). *S2G-RAG: Structured Sufficiency and Gap Judging for Iterative Retrieval-Augmented QA.* arXiv:2604.23783.

Shinn, N., Cassano, F., Berman, E., Gopinath, A., Narasimhan, K., & Yao, S. (2023). *Reflexion: Language Agents with Verbal Reinforcement Learning.* NeurIPS 2023. arXiv:2303.11366.

Yan, S.-Q., Gu, J.-C., Zhu, Y., & Ling, Z.-H. (2024). *Corrective Retrieval Augmented Generation (CRAG).* arXiv:2401.15884.

### Neuronale interpretatie

Gao, C., Chen, H., Xiao, C., Chen, Z., Liu, Z., & Sun, M. (2025). *H-Neurons: On the Existence, Impact, and Origin of Hallucination-Associated Neurons in LLMs.* arXiv:2512.01797. Code: https://github.com/thunlp/H-Neurons

### Geheugen, consolidatie en intrinsieke motivatie

Schmidhuber, J. (2011). *Formal Theory of Creativity, Curiosity and Intelligence.* IEEE Transactions on Autonomous Mental Development, 2(3), 230-247. doi:10.1109/TAMD.2010.2056368.

Frankland, P. W., & Bontempi, B. (2005). *The organization of recent and remote memories.* Nature Reviews Neuroscience, 6(2), 119-130.

Josselyn, S. A., & Tonegawa, S. (2020). *Memory engrams: Recalling the past and imagining the future.* Science, 367(6473), eaaw4325.

Karpicke, J. D., & Roediger, H. L. (2008). *The critical importance of retrieval for learning.* Science, 319(5865), 966-968.

Roediger, H. L., & Karpicke, J. D. (2006). *Test-enhanced learning: Taking memory tests improves long-term retention.* Psychological Science, 17(3), 249-255.

Tonegawa, S., Liu, X., Ramirez, S., & Redondo, R. (2015). *Memory engram cells have come of age.* Neuron, 87(5), 918-931.

### Historische context

Visser, H. (2025). *From Closure to Curiosity: Blindspot-Aware Large Language Models (BALLMs) and the Next-Generation Blind Spot Engine (NGBSE).*

Visser, H. (2025). *EAI Model: The Act of Learning.* https://sites.google.com/view/eaimodel/the-act-of-learning

Visser, H. (2025). *NGBSE Repository.* https://github.com/E-AI-MODEL/NGBSE

---

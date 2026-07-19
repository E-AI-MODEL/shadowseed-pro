# Dashboard

Dit is de snelle statuspagina voor Shadow Seed Learning 4.5.

Gebruik deze pagina als je niet alle workflows wilt bekijken, maar alleen wilt weten:

```text
werkt de standaard publicatie?
werkt het systeem nog breder?
werkt het met een echt model?
blijft het veilig?
```

## Hoofdstatus

| Blok | Run of pagina | Betekenis | Waar kijk je? |
|---|---|---|---|
| 1 | Latest standard publish | Laatste standaardresultaten op `main` | [Latest Test Results](Latest-Test-Results) |
| 2 | Full Validation Sweep | Brede systeemcheck buiten de standaardroute | [Full Validation Sweep](Full-Validation-Sweep) |
| 3 | Model Reality Check | Test met een echt HF/SLM-model | [Retrieval Model HF](Retrieval-Model-HF) |
| 4 | Safety Check | Test of SSOT niet naïef bronnen accepteert | [SSOT Falsification](SSOT-Falsification) |

## 1. Latest standard publish

Dit is nu de belangrijkste snelle check.

Deze route vertelt of de normale `main`-keten nog klopt:

- standaard tests en benchmarks zijn geslaagd;
- de artifacts zijn opnieuw opgebouwd;
- analyse en manifest zijn gepubliceerd;
- Wiki en Pages zijn bijgewerkt.

Gebruik deze route om te beantwoorden:

> Werkt de gewone repo-publicatie nog zoals bedoeld?

Als deze route groen is en `Latest Test Results` er goed uitziet, is de dagelijkse meet- en publicatieketen gezond.

## 2. Full Validation Sweep

Dit is een bredere handmatige of incidentele systeemcheck.

Hij controleert onder meer:

- unit tests;
- SSL gap suites;
- false-positive gedrag;
- vectorstore smoke;
- SSOT smoke;
- retrieval benchmark;
- retrieval → model benchmark;
- memory, FAISS en Chroma.

Gebruik deze run om te beantwoorden:

> Werkt ook de bredere technische onderlaag nog?

Dit is waardevol voor diagnose, maar niet meer de hoofd-ingang voor de dagelijkse status.

## 3. Model Reality Check

Deze run gebruikt een echt HF/SLM-model.

Hij vergelijkt:

```text
antwoord zonder SSOT-context
vs
antwoord met opgehaalde SSOT-context
```

Gebruik deze run om te beantwoorden:

> Helpt retrieval + SSOT ook bij echte modeloutput?

Deze run is zwaarder en blijft daarom handmatig.

## 4. Safety Check

Deze run test of het systeem niet naïef is.

Hij controleert:

- fout of irrelevant document promoot geen seed;
- `llm_proposed` telt niet als bewijs;
- `rejected` chunks tellen nooit mee;
- alleen `verified` chunks mogen de Gate in.

Gebruik deze run om te beantwoorden:

> Slikt SSL niet zomaar elke bron?

## Simpele prioriteit

Als je weinig tijd hebt:

1. kijk naar **Latest Test Results**;
2. kijk naar **SSL 4.5 Analysis**;
3. kijk naar **Safety Check**;
4. kijk naar **Model Reality Check**;
5. kijk daarna pas naar **Full Validation Sweep**.

## Wat betekent groen?

Groen betekent:

```text
de implementatie werkt binnen de huidige tests
```

Groen betekent niet automatisch:

```text
wetenschappelijk definitief bewezen
```

Voor sterk bewijs blijven nodig:

- meer papers;
- meer scenario’s;
- meerdere echte modellen;
- herhaalde runs;
- blind review.

## Korte conclusie

De snelste combinatie is nu:

```text
Latest Test Results
+ SSL 4.5 Analysis
+ Safety Check
+ Model Reality Check
```

Als die combinatie gezond is, is SSL 4.5 technisch stabiel en klaar voor verdere validatie.

# Stap 1: evidence-register en beslisregels

> **Datum 2026-10-25 | Alleen reeds bestaande waarnemingen, gescheiden van nieuw te toetsen hypotheses.**
> Deze tabel hoort bij [het uitgebreide onderzoek](step1-model-signals-gap-origin-2026-10-25.md), niet bij een goedgekeurde nieuwe modelrun. De originele [Q1/Q2-these](../possibility-space-thesis.md) blijft de onderzoeksvraag.

## I. Wat is daadwerkelijk gemeten?

| Referentie | Onderzoekseenheid en waarneming | Onderbouwde uitspraak | Niet aangetoond |
| --- | --- | --- | --- |
| [Gao et al. H-Neurons 2025](https://arxiv.org/html/2512.01797) | Neuronbijdragen bij feitelijke antwoordtokens; sparse klassificatie; modelinterventies; meerdere modellen 4B–70B | Bepaalde activaties zijn voor deze modellen/taken informatief voor een hallucinatielabel en interventies beïnvloeden gedrag | Of een LLM zelf zijn verborgen mogelijkheden kan opsommen; een bijzondere gap-to-seed-route; Q2 |
| [Cavus et al. 2026](https://arxiv.org/html/2609.29781) | Twee Gemma 4B-familiemodellen, meerdere QA-datasets; correlatie, bootstraps, L1/L2, matched-neuroninterventies en transfer | Predictie en interventie kunnen bestaan zonder stabiele, uniek gelokaliseerde neuronset; preprint | Unieke neuronidentiteit, of een classifier een specifieke niet-uitgesproken relatie representeert |
| [Ji et al. 2024](https://aclanthology.org/2024.blackboxnlp-1.6/) | Interne modeltoestanden vóór of rond antwoordgeneratie bij hallucinatierisico | Er kan voor een bepaalde taak informatie in hidden states zitten die het zichtbare antwoord niet rechtstreeks toont | Spontane detectie van nieuwe relaties, contextvrije modelzelfkennis |
| [Farquhar et al. 2024](https://www.nature.com/articles/s41586-024-07421-0) | Meerdere generatie-uitkomsten, clustering van betekenissen, semantische onzekerheid | Variatie tussen betekenisfamilies kan onzekerheid over confabulatie voorspellen | 'Niet genoemd' staat gelijk aan 'was intern aanwezig', of nieuwe onderzoeksvragen zijn ontstaan |
| [Shadowseed round 032](../../../benchmarks/open_review/rounds/round_032/RESULTS.md) | Qwen2.5-0.5B, 24 gegeven stellingen, externe GPT-4.1-houdbaarheidsetiketten, down_proj, gecorrigeerde multiple tests | Geen significant signaal volgens eigen vooraf vastgelegde grens; ruwe p 0.014 en 0.018 voldeden niet | Nulresultaat over alle modelgroottes of onuitgesproken mogelijkheden |
| [Shadowseed round 033](../../../benchmarks/open_review/rounds/round_033/RESULTS.md) | Nieuwe brontekst, vier vooraf vastgezette toetsen, geverifieerde herhaalbaarheid | 0/4 boven de vereiste statistische drempel; vroeg signaal niet gerepliceerd voor deze taak en schaal | Universele afwezigheid van relationele modelrepresentaties |
| [Detectorcalibratie 2026-10-24](../detector-calibration.md) | Qwen2.5 7B Q4_K_M, 96 turns, product v0.6 versus v0.7 en v0.8, dezelfde suite | v0.7 478 versus product 35 toegelaten kandidaten in run 1, beide 23% bruikbaar volgens beoordelingssample; v0.8 258 kandidaten en 33% bruikbaar, niet aangenomen | Meer genereren betekent beter signaleren; onafhankelijke bevestiging van nuttige gaps |
| [Seedcalibratie 2026-10-23](../seed-calibration.md) | GPT-5 en GPT-6.1-sol; 60 kandidaatteksten extern door een ander model beoordeeld; intakefilter gecontroleerd | 51/60 werden door de modelbeoordelaar bruikbaar genoemd; een oude filter wees 22/24 volgens die labels bruikbare kandidaten af | Onafhankelijke menselijke beoordeling of bewezen latente modellering |
| [Recurrencecalibratie, ADR-012](../../architecture/adr/ADR-012-model-recurrence-recognition.md) | 8 same-gap en 44 different-gap paren, modelbeoordelaarslabels | Embedding bij 0.60: 7/8 en 10/44 fout merges; Qwen: 7/8 en 1/44 fout merges; semantische identiteit behoeft apart oordeel | Wetenschappelijk onafhankelijke effectschatting of bronbewijs voor een seed |
| [Live GPT-5-compressieproef](live-compression-retention-result-2026-10-25.md) | 30 echte modelcalls, 3 embeddings; T0/T2; geen productdetector of levende per-turn-seedstate | Alternatieven opslaan en terugvinden werkt als technische proef; normale samenvattingen hadden de goede interpretaties al | Een echte gap-birth-test, longitudinale levenscyclus, unique SSL effect of Q1/Q2 |

**Bronhiërarchie:** originele modelruns en hun ruwe outputs zijn observaties, onderzoekerstabellen zijn samenvattingen, labels van een ander LLM zijn beoordelingen, nieuwe hypothetische onderzoekstappen zijn **geen** observaties. Vergelijk geen percentages uit andere modelsnapshots, verschillende datasets en verschillende beoordelaars alsof het één gecontroleerde modelgrootteschaal is.

## II. Technische provenance: wat bestaat, wat is bewust geparkeerd?

| Bron | Status in main op 2026-10-25 | Consequentie voor onderzoek |
| --- | --- | --- |
| [Productdetector](../../../src/shadowseed/detection/model_detector.py) | Current-pair v0.6, generative v0.4 en historical absence-variant beschikbaar | Vastzetten per meetarm; wijzigingen niet in-place experimenteren |
| [Session/engine](../../../src/shadowseed/chat.py) | Werkelijke meerturnsloop aanwezig | Niet achteraf een nieuwe manager maken bij de late fase |
| [Canonical intake](../../../src/shadowseed/intake.py) en [observatielog](../../../src/shadowseed/observations.py) | Ruwe kandidaat → intake → status, inclusief rejected/suppressed | Elke kandidaatobservatie moet vóór en na normalisatie zichtbaar blijven |
| [ADR-012](../../architecture/adr/ADR-012-model-recurrence-recognition.md) | Accepted, recurrenceherkenning is een aparte modeltaak | Geldige herhaling ≠ evidentie/gewicht |
| [PR #205](https://github.com/E-AI-MODEL/shadowseed-pro/pull/205) | Gemerged | Structurele intake- en levenscyclusreparaties gebruiken, geen tweede implementatie |
| [PR #202](https://github.com/E-AI-MODEL/shadowseed-pro/pull/202) | **Gesloten, niet gemerged** | Detector v0.7 niet als huidige productie presenteren; eerst onafhankelijke review |
| [Issue #203](https://github.com/E-AI-MODEL/shadowseed-pro/issues/203) | Gesloten met parkeerbesluit | Mechanistisch spoor niet stilzwijgend reactiveren |
| [PR #204](https://github.com/E-AI-MODEL/shadowseed-pro/pull/204) | **Gesloten, niet gemerged**; synthetische hook-preflight in branch beschikbaar | Geen voltooid 14B-resultaat, geen gepubliceerd ZeroGPU-experiment; instrument is alleen mogelijke broncode |
| [Oorspronkelijke these](../possibility-space-thesis.md) | Verbatim en ongewijzigd | Beide delen blijven open; geen enkele small-scope test mag haar herdefiniëren |

## III. Minimaal inspecteerbare observatie-eenheid

De basis is **één afzonderlijke gespreksturn** met vastgelegde tijdsvolgorde. Geen samengevoegd cijfer over de hele conversatie kan herkomstschendingen goed genoeg verbergen.

1. **Vóór generatie:** casus-/gesprek-ID, chronologische turn-ID, bron- en topicgroep, werkelijk zichtbare historie, prompt/templatehash, model- en embeddingrevisie, sampling, totale costs.
2. **Gewone generatie:** onbewerkte eerste uitkomst en eventuele native fout/stop, voordat een kandidaatprompt wordt gebruikt. Bepaal welke betekenisfamilies bij herhaald normaal genereren aantoonbaar verschijnen.
3. **Afzonderlijke detectie:** detectorrol, exact detectie-input (ook beperking 4 schone turns), raw output, NONE-versus-parsefout, candidate-type alleen als auditmetadata, raw kandidaatreferentie.
4. **Geboorte:** parserdiagnose, normalisatie vóór/na, atomiciteitsbeoordeling, rejectreden, ID, hash, SeedOrigin, trace/weight/evidence_count en context.
5. **Volgende turns:** vragen, nieuw bewijs apart met bronref, zelf-toegevoegde versus externe context, herkenning, clustering, TTL/TrTL, eventlog, Gate, punt van gebruik, status na elke turn.
6. **Later extern oordeel:** zelfstandig onderzoekbare vervolgvraag, onafhankelijke beoordelaar en bron-toets; label na de gebeurtenis, niet vooraf verstopt in modelprompt.

De live productroute en de research-view zijn **twee weergaven van dezelfde echte gebeurtenis**. Het onderzoeksinstrument mag logs maken maar geen eigen, alternatieve autorisatieroute introduceren.

## IV. Goedkeuring voor de eerste echte meetfase

**Voordat een live proef zinvol is**, moeten een methodereviewer en een code-/veiligheidsreviewer antwoord geven op deze vragen:

- Welke van de vier verschillende fenomenen meten we: niet-uitgesproken, onder andere condities bereikbaar, contextgebonden onderzoekbare kandidaat, of later werkelijk andere onderzoekbaarheid?
- Is de nulhypothese het sterke model dat zelf anders zoekt of gewone notities gebruikt, met dezelfde compute en context? Welke uitkomst zou een unieke Shadowseed-bijdrage ontkrachten?
- Is een echte abstentie herkenbaar zonder die te verwarren met een outputfout, max-tokenlimiet of formatteringsruis?
- Ontvangt de detector alleen de vraag, eerste antwoord en expliciet toegestane context, en nooit al ingevulde toekomstinformatie of een autoriserend label?
- Is één kandidaat ook daadwerkelijk één open relatie, niet slechts één zin?
- Wordt een waardevolle kandidaat door normalisatie verwijderd of inhoudelijk veranderd? Wordt een inhoudelijk andere kandidaat ten onrechte als recurrence gemeld?
- Is de start van de seed echt vóór de latere gebeurtenis? Is dezelfde manager/engine gedurende alle turns actief?
- Gaan weightless kandidaturen alleen naar geïsoleerde observatie/read-only onderzoek, en niet naar antwoordinvloed zonder actuele Gate?
- Zijn de negatieve cases, splits, onafhankelijke labels, sampleomvang, geldigheidscontroles en stopcriteria vooraf vastgelegd, buiten de promptkalibratieset?
- Voor neural claims: originele generatietoken-activaties, modelrevisie, quantisatietype, held-out bron- en onderwerpgroepen en correlated-feature/sham-interventiecontrole vastgelegd?

Status op 25 oktober: deze antwoorden zijn nog **geen onafhankelijke getekende akkoordverklaring**. [De bestaande G0-reviewledger](g0/dynamic-inquiry-independent-review.md) is nog leeg. Geen nieuw betaalde LLM-proef en geen productie-aanpassing uit dit evidence-register.

## V. Besluit

**Vaststaand:** de repository heeft een echte gescheiden detectie-/intake-/levenscyclusroute en oude bruikbare mechanistische instrumenten. De resultaten tonen zowel modelcapaciteitsverschillen als meetfouten. De H-Neurons-literatuur rechtvaardigt de vraag of ongebruikelijke interne signalen bestaan, maar bewijst geen relatie tussen die signalen en Shadowseed.

**Onbeslist:** kan een krachtige detector buiten gewone generatie een betekenisvolle, nog niet gekozen relatie vinden? Kan die observatie correct door de bestaande seedgeboorte? Leeft die seed vervolgens op een inhoudelijk gerechtvaardigde manier mee of verdwijnt zij terecht? Kan zij latere onderzoekbaarheid aantoonbaar veranderen?

Die vier vragen mogen afzonderlijk een negatief antwoord krijgen. Dat is een geldige onderzoeksuitkomst, geen reden om de these zonder bewijs te herschrijven.

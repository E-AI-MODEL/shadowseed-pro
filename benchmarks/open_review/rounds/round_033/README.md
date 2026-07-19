# Round 033 — vooraf geregistreerde replicatie van het round-032-signaalkandidaat

> **Status: VERDICT — NIET gerepliceerd (zie `RESULTS.md`).** Op de vier
> vooraf vastgelegde toetsen (lagen 2 en 5 × beide detectoren, lat 0.0125)
> haalde 0 van de 4 de lat: laag 2 centroïde-p 0.0319 / sparse-p 0.597,
> laag 5 centroïde-p 0.0459 / sparse-p 0.565 (LOOCV 0.50 = toeval). Het
> round-032-kandidaat was ruis; spoor 2 sluit voor schaal ≤0.5B.
>
> **Oorspronkelijke preregistratie (run nog niet gedraaid).** Round 032 gaf op het
> H-Neurons-leespunt de eerste níet-vlakke null van het spoor (centroïde
> p 0.014 op laag 2, sparse L1 p 0.018 op laag 5) — boven de Bonferroni-lat
> over 24 lagen, dus geen signaal, maar wél het patroon dat óf toeval óf
> een eerste echt spoortje is. Deze round beslist dat op de enige zuivere
> manier: nieuwe data, vooraf vastgelegde hypothese, één kans. Dit dossier
> ís het "vooraf geregistreerde replicatieplan" dat de rust-afspraak van
> round 032 vereist; de maintainer heeft tot deze replicatie besloten.

## Wat er nieuw is en wat bewust identiek blijft

**Nieuw (de replicatie-eis):**

- Brontekst: drie níeuwe casussen (WONEN / ZORG / CULTUUR) in plaats van
  onderwijs/gezondheid/klimaat — `dialectic_falsification_transfer_v3.json`;
- 24 nieuwe cases, zelfde ontwerpmix als v2: 7 kandidaat-gaps, 5
  bron-parafrases, 2 strijdige stellingen, 5 domein-nabije stellingen, 5
  domein-verre distractors. Notes zijn ontwerp-intenties, geen labels.

**Identiek (anders is het geen replicatie):**

- gesondeerd model `Qwen/Qwen2.5-0.5B`, leespunt `neuron`
  (down_proj-input), pooling `stelling`, 500 permutaties;
- gpt-4.1 als ontkoppelde oordeelbron, zelfde workflow-keten.

## Leesregel (vooraf vastgelegd — dít is de preregistratie)

1. **Alleen deze vier toetsen tellen:** laag `model.layers.2.mlp.down_proj`
   en laag `model.layers.5.mlp.down_proj` (de twee sterkste lagen uit
   round 032), elk op beide detectoren (centroïde-permutatie en sparse-L1-
   permutatie). Bonferroni over 4 toetsen: **lat = 0.05/4 = 0.0125** per
   toets (permutatievloer 1/501 ≈ 0.002 — ruim haalbaar).
2. **Gerepliceerd** = minstens één van de vier vooraf benoemde toetsen
   onder 0.0125. Dan is er voor het eerst een signaal dat een claim op
   instrument-niveau draagt, en heropent het spoor richting Niveau 2
   (met als eerstvolgende vraag: is het effect stabiel over casesets en
   schaalt het mee met modelgrootte?).
3. **Niet gerepliceerd** = round 032 was ruis; het spoor sluit definitief
   voor deze schaal (≤0.5B), met een véél sterkere afsluiting dan round
   032 alleen. De schaalvraag (H-Neurons meet op 24B–70B) blijft benoemd
   toekomstwerk, geen belofte.
4. Alle andere lagen worden gewoon gerapporteerd maar tellen **niet** mee
   in het verdict — wat daar ook uitkomt. Geen post-hoc-promotie van een
   "verrassende" derde laag; die mag hoogstens een nieuwe preregistratie
   voeden.
5. Een eventueel signaal blijft een Laag G-*signaal*: het voedt geen
   promotie en verandert geen claims van lagen A–F (signaal ≠ verdict).

## Amendement vóór de run (codex-P2, 2026-07-14)

Twee cases bleken bij deterministische controle niet heelhuids door de
échte ingest-route te komen (`ingest_detection_candidates` met
broad-splitting, zoals de runner hem aanroept): de hittewerende-
maatregelen-case fragmenteerde op komma's/"zoals … en …" (alleen het
eerste fragment zou beoordeeld zijn) en de zorgtechnologie-case werd zelfs
volledig geweigerd (stil uit de set gevallen). Beide zijn vóór de run
geherformuleerd zonder splitter-triggers; een test bewaakt nu dat álle 24
cases exact één geaccepteerde, tekst-intacte seed opleveren. Dit is een
amendement op de caseset vóór dataverzameling — de leesregel (vier
toetsen, lat 0.0125) is ongewijzigd.

## Run-recept

```text
workflow: Research · Laag G sonde met echte verdictbron
probe_model_id: Qwen/Qwen2.5-0.5B
dialectic_model_id: gpt-4.1
input_path: src/shadowseed/data/dialectic_falsification_transfer_v3.json
read_location: neuron
sparse_permutations: 500
```

## Klaar wanneer

1. Run gedraaid, artifact + digest hier vastgelegd.
2. Verdict gelezen op uitsluitend de vier vooraf benoemde toetsen en
   gedocumenteerd in `RESULTS.md` — repliceert of repliceert niet, allebei
   een geldig en definitief antwoord voor deze schaal.
3. `laag-g-scoping.md` bijgewerkt met de uitkomst.

## Claimgrens

Exploratieve Laag G. Deze round kan hoogstens een instrument-niveau-signaal
opleveren, geen inhoudelijke SSL-claim; en een niet-replicatie is geen
falen maar het eerlijke einde van dit spoor op deze schaal.

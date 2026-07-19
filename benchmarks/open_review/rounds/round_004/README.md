# Open-set Review Round 004

> Status: **menselijke review afgerond (anchored, zie caveat)**
> Detector: `model` + `hf-transformers` (Qwen/Qwen2.5-3B-Instruct), v0.3c prompt
> Evidence layer: `open_set_seed_quality` (Laag C)
> Related: #41, #62, #81, ADR 0001

## Wat dit is

Round 004 herhaalt de open-set seed-generatie van round 003, maar met een
**groter model**: Qwen/Qwen2.5-3B-Instruct in plaats van de 1.5B uit round 003c.
Doel is te zien of een grotere model-tier de rommeligheid van de 1.5B-output
vermindert, met dezelfde 12 AG News test-items (offset 0) en dezelfde v0.3c
prompt (vreemd-domein few-shot + leak-filter).

- 12 items, 54 unieke seeds, 108 review-packets (54 seeds × reviewer_a + reviewer_b)
- review afgerond: **28 accepted / 26 rejected** (acceptance rate 51.9%)
- automatische acceptatie na normalisatie: 54/60 (0.90)
- batch is nog 12/12 nieuws/Sci-Tech (offset 0) — geen domein-spreiding

## Caveat: anchored review

Twee menselijke reviewers hebben elk onafhankelijk de seeds beoordeeld,
maar **vertrokken vanuit dezelfde AI-prescreen** als startpunt. Ze
hadden geen afwijkende bevindingen ten opzichte van de prescreen-verdicts.

Dit is echte menselijke review (mensen hebben geoordeeld), maar:

- de 100% inter-beoordelaars-overeenstemming is een artefact van gemeenschappelijk
  startpunt, niet van onafhankelijke convergentie
- de overeenstemming mag **niet** worden geïnterpreteerd als sterk
  inter-beoordelaars-signaal
- de accepted/rejected verdicts zijn wel geldig als conservatief Layer C-sample

Toegestane claim:

> Round 004 bevat een eerste door mensen bevestigde seed-quality sample
> (anchored review, 28/54 accepted).

Niet toegestaan:

> Twee onafhankelijke reviewers stemden voor 100% overeen.

Voor een werkelijk onafhankelijke ronde met blindmeting moet een
volgende round zonder AI-prescreen als startpunt worden uitgevoerd.

Round 003 (Qwen-1.5B) blijft ongemoeid; die review loopt apart. Dit is een
parallelle, sterkere-model batch, niet een vervanging.

## Eerlijke kwaliteitswaarschuwing

Qwen-3B is duidelijk netter dan 1.5B, maar nog niet schoon. Een statische scan
voor menselijke review liet zien:

- de meeste seeds zijn echte zin-vormige NL gap-observaties (duidelijk beter
  dan 1.5B)
- **4 seeds** bevatten een onvertaalde Engelse bronfrase (model echoot de
  brontaal), bijv. `... ligt bij de stricken parent firm Federal Mogul`
  (TEST_0), `high-speed wireless format` (TEST_10), `music retailers` (TEST_12)
- **1 seed** heeft een niet-gedecodeerde HTML-entity: `De #36;10 miljoen Ansari
  X Prize ...` (TEST_1), waar `#36;` voor `$` staat
- **2 seeds** in TEST_0 zijn als bewering geformuleerd (`De aansprakelijkheid
  ... ligt bij ...`) in plaats van als ontbrekend element — beoordeel of dat
  `style_not_gap` is

Dit is precies waarom menselijke review nodig is: de cijfers van het model
zeggen niets, jullie oordeel wel. Een hoog afwijspercentage is een geldige
uitkomst, geen mislukking. Let bij taalmenging op `style_not_gap` met een
notitie (zie reject codes).

## Hoe in te vullen

Elke reviewer bewerkt **alleen het eigen bestand**:

- `reviewer_a_packets.csv` (54 rijen)
- `reviewer_b_packets.csv` (54 rijen)

Per rij invullen:

- `review_status`: `accepted` of `rejected`
- vijf booleans (`atomicity`, `relevance`, `testability`, `non_triviality`,
  `follow_up_utility`): `true` of `false`
- `reject_reason`: één code uit de lijst hieronder als `rejected`, leeg als `accepted`
- `reviewer_notes`: korte tekst

De CSV is een werkkopie. De canonieke artefact is
`open_set_review_packets.json`; ingevulde rijen moeten daar via `packet_index`
terug naartoe voordat de summary draait.

### Reject codes

`too_broad`, `too_vague`, `trivial`, `not_relevant`, `not_testable`,
`duplicate`, `style_not_gap`

(En, gezien dit een modelrun is, let extra op: `not_dutch` / taalmenging mag je
als `style_not_gap` afwijzen met een notitie.)

## Na het invullen

Merge de ingevulde CSV-rijen terug in `open_set_review_packets.json` en draai:

```bash
shadowseed summarize-open-set-seed-review \
  --input benchmarks/open_review/rounds/round_004/open_set_review_packets.json \
  --output results/open_review/open_set_seed_review_summary.json \
  --disagreements-output results/open_review/open_set_disagreements.json \
  --report-output results/open_review/open_set_review_report.md
```

## Claim-grens

Toegestaan na een geldige ronde:

> Een open-set seed-quality sample met een grotere taalmodel-detector
> (Qwen-3B) is menselijk gereviewd.

Niet toegestaan:

> SSL is bewezen beter op open data.

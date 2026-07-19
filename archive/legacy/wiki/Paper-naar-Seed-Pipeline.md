# Paper naar Seed Pipeline

Deze pagina beschrijft de volgende stap voor SSL 4.5: wetenschappelijke papers gebruiken als input voor candidate seeds, SSOT-proposals en benchmarkscenario’s.

## Hoofdidee

Een PDF-paper wordt niet direct waarheid.

Een paper is input voor een pipeline:

```text
PDF
→ tekstextractie
→ claims
→ failure modes
→ candidate seeds
→ scenario’s
→ llm_proposed SSOT chunks
→ human verify
→ verified SSOT
→ Validation Gate
```

De pipeline bepaalt dus de seeds. De mens of een vertrouwde stap bepaalt pas later of de bijbehorende chunks verified worden.

## Waarom dit past bij SSL

Veel RAG-literatuur ziet retrievalruis, conflicten en irrelevante context als probleem.

SSL ziet zulke failure modes als mogelijk signaal:

| RAG-probleem | SSL-kandidaat |
|---|---|
| noisy retrieval | ontbrekend filtercriterium |
| conflicting context | bronconflict niet herkend |
| irrelevant context | ontbrekende grens tussen onderwerpen |
| hallucination trigger | ontbrekende verificatiestap |
| low-confidence answer | onzekerheidsgebied |
| missing evidence | candidate shadow seed |

De pipeline moet deze signalen niet blind geloven, maar omzetten naar toetsbare candidate seeds.

## Pipeline-stappen

### 1. PDF-inname

Input:

```text
data/papers/*.pdf
```

Output:

```text
results/paper_ingest/<paper_id>/text.txt
```

De eerste versie mag tekst-PDF’s ondersteunen. Scans en OCR kunnen later.

### 2. Tekstextractie

Doel:

```text
paper → paragrafen → secties
```

Metadata:

```json
{
  "paper_id": "paper_001",
  "title": "...",
  "source_path": "data/papers/paper_001.pdf",
  "extracted_at": "..."
}
```

### 3. Claim-extractie

De pipeline zoekt uitspraken die bruikbaar zijn voor SSL:

- definities;
- failure modes;
- beperkingen;
- benchmarkobservaties;
- claims over RAG-problemen;
- claims over uncertainty of factuality.

Elke claim wordt eerst voorstel:

```json
{
  "claim_id": "claim_001",
  "text": "Conflicting retrieved evidence can reduce answer faithfulness.",
  "status": "llm_proposed",
  "source": "paper_001",
  "section": "Failure Analysis"
}
```

### 4. Candidate seed generatie

Elke claim kan één of meer candidate seeds opleveren.

Regel:

> Een seed bevat precies één gap.

Voorbeeld:

```json
{
  "seed_text": "Bronconflict tussen opgehaalde documenten wordt niet herkend.",
  "source_claim_id": "claim_001",
  "status": "candidate",
  "atomic": true
}
```

Brede seeds worden afgewezen of gesplitst.

### 5. Scenario-generatie

Uit dezelfde claim kan een scenario ontstaan:

```json
{
  "scenario_id": "paper_001_scenario_001",
  "question": "Wat moet het model doen bij twee conflicterende bronnen?",
  "expected_additions": [
    "bronconflict herkennen",
    "geen willekeurige bron kiezen",
    "onzekerheid expliciet maken"
  ],
  "source_claim_ids": ["claim_001"]
}
```

Scenario’s worden gebruikt in benchmarks.

### 6. SSOT proposals

Paperchunks en claims komen eerst in SSOT als:

```text
trust_level = llm_proposed
status = proposed
```

Ze mogen dan nog geen seeds valideren.

### 7. Verificatie

Na menselijke controle:

```text
verify_chunk() → verified
```

Pas dan mogen chunks meetellen als externe evidence.

### 8. Validatie van open seeds

Daarna kan de bestaande functie draaien:

```text
validate_open_seeds_against_ssot()
```

De Validation Gate bepaalt of weight groeit.

## Eerste implementatie

Minimale versie:

```text
paper text fixture
→ claim extraction via regels
→ candidate seeds json
→ scenario json
→ SSOT llm_proposed
```

Daarna:

```text
PDF extractie
→ echte papers
→ verify workflow
```

## Belangrijke veiligheidsregel

Een paper is niet automatisch waarheid.

Zelfs peer-reviewed papers kunnen:

- beperkt zijn;
- elkaar tegenspreken;
- domeinspecifiek zijn;
- verkeerd worden geïnterpreteerd.

Daarom geldt:

```text
paper claim → llm_proposed
human verify → verified
verified → Validation Gate
```

## Wat dit oplevert

Deze pipeline maakt van RAG-failure-literatuur een bron voor SSL:

```text
failure mode → candidate seed → scenario → test → evidence
```

Zo wordt “rommel” uit retrieval niet weggegooid, maar gecontroleerd gebruikt als ingang voor leren.
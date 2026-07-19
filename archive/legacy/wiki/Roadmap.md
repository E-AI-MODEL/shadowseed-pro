# Roadmap

> Status: achtergrond en planning. Gebruik voor actuele resultaten eerst [Latest Test Results](Latest-Test-Results) en [SSL 4.5 Analysis](SSL-45-Analysis).

Deze roadmap houdt de claims van SSL 4.5 eerlijk en toetsbaar.

## Klaar

- SSLManager met trace, weight, decay, Validation Gate en promotie.
- Positieve Gap-Test Suite.
- False-positive controls.
- Benefit Suite fase 1.
- Model Benefit Suite met fixture en optionele `hf-transformers` backend.
- Blind benchmark smoke-route.
- Probe utility suite als handmatige gedragslaag.
- CI-artifacts voor de standaard suites.
- Centrale artifact snapshot helper met manifest en tests.
- Analyse-laag met Markdown, JSON en SVG.
- Publicatie naar Wiki en GitHub Pages via de standaard publish-route.

## Huidige standaardroute

De dagelijkse route is:

```text
Actions → Checks en benchmark-resultaten
Actions → Publiceer testresultaten naar Wiki en Pages
```

De actuele output staat daarna op:

- [Latest Test Results](Latest-Test-Results)
- [SSL 4.5 Analysis](SSL-45-Analysis)
- [Dashboard](Dashboard)
- `verhaal.html` in de repo-root (standalone; het Pages-dashboard is opgeheven)

## Eerstvolgende stappen

### 1. Reward/Penalty-validatie ontwerpen

De volgende inhoudelijke stap is SSL minder afhankelijk maken van vaste scenario-ground-truth.

Doel:

```text
seed → probe/tool/retrieval/user feedback → reward of penalty → weight update
```

Ground truth blijft nuttig als regressielaag, maar mag niet de primaire motor van SSL blijven.

### 2. Open-set review uitbreiden

Gebruik open inputs zonder hardcoded expected gaps.

Meet vooral:

- atomiciteit;
- relevantie;
- toetsbaarheid;
- probe utility;
- foutieve promoties;
- nuttige latere heractivatie.

### 3. Probe utility strenger maken

De probe utility suite moet testen of een promoted seed leidt tot een nuttige vervolgstap, niet alleen of een tekstmatch klopt.

### 4. Retrieval en tool evidence koppelen aan reward

Retrieval en toolcalling moeten niet automatisch valideren. Ze leveren signalen:

- steun;
- geen steun;
- contradictie;
- gedeeltelijke bruikbaarheid.

### 5. Meer negatieve controles

Test of SSL rustig blijft bij:

- volledige antwoorden;
- irrelevante signalen;
- tegengestelde evidence;
- brede vaagheden;
- stijlproblemen die geen echte gap zijn;
- herhaalde maar nutteloze seeds.

### 6. Meer modellen

Vergelijk meerdere SLM's, maar altijd binnen hetzelfde patroon:

```text
model X baseline
model X met SSL
```

Niet model X vergelijken met model Y als bewijs voor SSL.

## Claimniveau

### Nu toegestaan

> SSL 4.5 werkt intern op de huidige suite en produceert reproduceerbare benchmark-, analyse- en publicatie-output.

### Pas later toegestaan

> SSL verbetert antwoorden gemiddeld op meerdere domeinen zonder afhankelijk te zijn van vaste scenario-ground-truth.

Dat mag pas na open-set evaluatie, reward/penalty-validatie, bredere modelruns en blind review.

# Gap-Test Suite 4.5

## Doel

Deze testset meet of een model kleine structurele gaps kan vinden. Elk scenario bevat een incomplete inputtekst, atomische ground truth seeds en scorevoorbeelden.

## Algemene scoring

| Score | Betekenis |
|---:|---|
| 0 | Geen relevante gap gevonden |
| 1 | Richting klopt, maar output is te vaag of te breed |
| 2 | Atomische en structureel juiste gap gevonden |

Een brede lijst krijgt maximaal score 1.

---

## Scenario A: Industriële Revolutie

**Domein:** geschiedenis en economie

### Input

> De Industriële Revolutie in het 18e-eeuwse Groot-Brittannië werd gekenmerkt door een ongekende versnelling van technologische innovatie. De verbeteringen van James Watt aan de stoommachine maakten het mogelijk om fabrieken los te koppelen van waterbronnen, wat leidde tot de opkomst van grote industriële centra zoals Manchester. De textielindustrie explodeerde door uitvindingen zoals de 'spinning jenny', wat resulteerde in massale urbanisatie en de vorming van een nieuwe arbeidersklasse. Deze periode legde de basis voor de moderne kapitalistische economie door productie op schaal mogelijk te maken.

### Atomische ground truth seeds

| Seed ID | Seed |
|---|---|
| A1 | Koloniaal kapitaal als financieringsbron voor Britse fabrieksinvesteringen. |
| A2 | Winsten uit trans-Atlantische slavenhandel als investeringskapitaal voor industrialisatie. |
| A3 | Koloniale katoen als grondstof voor de Britse textielindustrie. |
| A4 | Goedkope koloniale grondstoffen als voorwaarde voor schaalvergroting van productie. |

### Minimale pass

Het model detecteert minstens één van A1-A4 scherp.

### Volledige pass

Het model detecteert A1 of A2 en maakt de financiële relatie expliciet.

### Scorevoorbeelden

| Output | Score | Reden |
|---|---:|---|
| Het verslag is compleet. | 0 | Geen gap. |
| Er ontbreken oorzaken, koloniale handel, kapitaal, arbeid en ongelijkheid. | 1 | Richting deels goed, maar te breed. |
| Kolonialisme ontbreekt. | 1 | Relevante richting, maar niet atomisch genoeg. |
| Koloniaal kapitaal als financieringsbron voor Britse fabrieksinvesteringen. | 2 | Kleine, toetsbare financiële gap. |

---

## Scenario B: Grensoverschrijdende juridische casus

**Domein:** recht en jurisdictie

### Input

> Een Nederlandse consument heeft een high-end laptop gekocht bij een online retailer die gevestigd is in de Verenigde Staten. Bij levering blijkt het product defect. De consument wil een volledige terugbetaling eisen op basis van de EU-richtlijnen voor consumentenbescherming, die strikte regels stellen aan de garantieperiode en het recht op retour bij defecte goederen binnen de Europese Unie. De focus ligt hierbij op de materiële rechten van de koper om een werkend product te ontvangen.

### Atomische ground truth seeds

| Seed ID | Seed |
|---|---|
| B1 | Rechtsbevoegdheid bij een geschil tussen een Nederlandse consument en een Amerikaanse webwinkel. |
| B2 | Toepasselijk recht bij een grensoverschrijdend consumentencontract. |
| B3 | Afdwingbaarheid van EU-consumentenrecht tegenover een niet-EU retailer. |
| B4 | Forumkeuzebeding in internationale online koopvoorwaarden. |

### Minimale pass

Het model detecteert B1 of B2 scherp.

### Volledige pass

Het model herkent rechtsbevoegdheid en toepasselijk recht als aparte seeds.

### Scorevoorbeelden

| Output | Score | Reden |
|---|---:|---|
| De consument heeft mogelijk recht op garantie. | 0 | Blijft binnen consumentenrecht. |
| Het internationale karakter ontbreekt. | 1 | Relevante richting, maar geen juridisch mechanisme. |
| Internationaal privaatrecht ontbreekt. | 1 | Relevante richting, maar nog breed. |
| Rechtsbevoegdheid bij een geschil tussen een Nederlandse consument en een Amerikaanse webwinkel. | 2 | Atomische procedurele gap. |

---

## Scenario C: Software Architectuur

**Domein:** IT en engineering

### Input

> Het voorgestelde ontwerp voor de 'HealthTrack' app bestaat uit een React Native frontend en een Node.js backend. Data wordt opgeslagen in een MongoDB cluster voor maximale flexibiliteit in datastructuur. De kernfunctionaliteiten omvatten een gebruikersdashboard, real-time hartslag-synchronisatie via Bluetooth en een notificatiesysteem voor gezondheidswaarschuwingen. De UI volgt de Material Design-richtlijnen om de toegankelijkheid voor ouderen te waarborgen.

### Atomische ground truth seeds

| Seed ID | Seed |
|---|---|
| C1 | AVG-compliance bij verwerking van medische hartslagdata. |
| C2 | Authenticatiestrategie voor toegang tot gezondheidsdata. |
| C3 | Rate-limiting op API's die gezondheidsdata verwerken. |
| C4 | DDoS-bescherming voor publieke endpoints van de app. |
| C5 | Horizontale schaalbaarheid bij piekbelasting van real-time synchronisatie. |
| C6 | Encryptie van medische data in rust en tijdens transport. |

### Minimale pass

Het model detecteert minstens één seed en koppelt die scherp aan medische data.

### Volledige pass

Het model detecteert privacy of security én schaalbaarheid als aparte seeds.

### Scorevoorbeelden

| Output | Score | Reden |
|---|---:|---|
| Het ontwerp lijkt technisch compleet. | 0 | Geen gap. |
| Beveiliging en schaalbaarheid ontbreken. | 1 | Relevant, maar te algemeen. |
| Privacy ontbreekt. | 1 | Te vaag. |
| AVG-compliance bij verwerking van medische hartslagdata. | 2 | Kleine, toetsbare compliance-gap. |
| Horizontale schaalbaarheid bij piekbelasting van real-time synchronisatie. | 2 | Kleine, toetsbare schaalbaarheids-gap. |

---

## Logboektabel

| Scenario | Gedetecteerde seed | Ground truth match | Score 0-2 | Toelichting |
|---|---|---|---:|---|
| A |  |  |  |  |
| B |  |  |  |  |
| C |  |  |  |  |

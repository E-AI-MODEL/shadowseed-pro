# Public-Facing Recovery Plan

## Doel

Dit plan beschrijft hoe `shadowseed` publiek begrijpelijk, inhoudelijk eerlijk en operationeel consistenter wordt voor repo- en wiki-bezoekers.

De kernvraag is niet alleen hoe goed SSL technisch werkt, maar ook:

- of een nieuwe bezoeker direct begrijpt wat SSL is;
- of een nieuwe bezoeker direct ziet naar welke resultaten hij kijkt;
- of de repo duidelijk maakt wat bewezen is en wat nog niet;
- of secrets en externe toegang veilig zijn ingericht.

## Wat een bezoeker direct moet kunnen begrijpen

Een bezoeker moet binnen de eerste minuut antwoord krijgen op deze vragen:

1. Wat is SSL?
2. Waarom is SSL inhoudelijk interessant?
3. Welke resultaten zijn standaard?
4. Welke resultaten zijn aanvullend bewijs?
5. Wat mag ik voorzichtig concluderen?
6. Wat is nog geen brede claim?

## Gewenste publieksboodschap

De gewenste standaardboodschap is:

> SSL probeert kleine, toetsbare afwezigheden in antwoorden zichtbaar te maken, veilig op te slaan en pas na validatie invloed te geven.

Daarna moet meteen volgen:

- de repo heeft een werkende mechanische kern;
- de standaard meetketen draait;
- de standaardpublicatie combineert regressie, smoke, kleine benchmarks en aanvullende evidencelagen;
- die extra lagen maken de repo inhoudelijk eerlijker, maar vormen nog geen volledige eindvalidatie.

## Herstelpunten

### 1. Publieke ingang vereenvoudigen

Benodigde plekken:

- `README.md`
- `docs/wiki/Home.md`
- `docs/wiki/Start-Hier.md`
- `site/index.html`

Hersteldoel:

- minder interne jargonblokken aan het begin;
- direct uitleggen wat SSL is;
- direct uitleggen waar bezoekers het best moeten beginnen.

### 2. Resultaten expliciet labelen

Elke publieke resultatenroute moet zichtbaar maken of iets is:

- regressie
- technische smoke
- methodologische smoke
- kleine benchmark
- aanvullende evidencelaag

Hersteldoel:

- geen impliciete vermenging van bewijssoorten;
- bezoekers hoeven niet zelf te reconstrueren hoe zwaar een resultaat weegt.

### 3. Standaardpublicatie en docs weer laten overeenkomen

De standaardworkflow publiceert nu meer dan alleen de oude kernsuites.
Daarom moeten docs, wiki en analyzer hetzelfde verhaal vertellen over:

- adversarial Gate
- probe utility
- open-set review

Hersteldoel:

- geen conflict meer tussen "handmatig" en "standaard zichtbaar";
- wel duidelijk blijven dat niet alles dezelfde bewijslast heeft.

### 4. Analysekop herschrijven

Het analyserapport mag niet vooral blijven klinken als:

- fixture smoke werkt

Het moet eerst uitleggen:

- wat de publicatie bevat;
- welke bewijslaag je bekijkt;
- hoe ver de claim reikt.

### 5. Secretpatroon formaliseren

Hugging Face toegang mag niet in code of datafiles terechtkomen.

Hersteldoel:

- lokale secrets via `.env`
- echte token nooit committen
- CI via repository secret `HUGGINGFACE_TOKEN`
- code mag optioneel auth gebruiken, maar moet waar mogelijk ook zonder token werken

## Rollout-volgorde

1. publieke ingang vereenvoudigen
2. bewijssoorten expliciet labelen
3. analyzer en publicatiepagina's herschrijven
4. secretpatroon vastleggen
5. daarna pas nieuwe evidencelagen verder uitbouwen

## Succescriteria

Het herstel is geslaagd als:

- een nieuwe bezoeker zonder voorkennis de eerste pagina begrijpt;
- wiki en repo dezelfde kernboodschap gebruiken;
- standaardresultaten niet meer gelezen worden als een te grote claim;
- aanvullende evidencelagen zichtbaar zijn zonder de regressiebasis te overschrijven;
- HF toegang veilig via secrets loopt in plaats van via code of committed bestanden.

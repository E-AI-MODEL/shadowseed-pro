# Plan naar scenario-onafhankelijke SSL-validatie

> Status: current
> Date: 2026-06-30
> Evidence layer: Direction note after W9f
> Current source: yes

## Doel van dit document

Dit document beschrijft hoe Shadow Seed Learning doorgroeit van scenario-gedreven validatie naar scenario-onafhankelijke validatie.

De stand is sinds de eerdere roadmap veranderd. Het W9f cross-turn *mechanisme* is bevestigd op veilige drempels; de *payoff-kwaliteit* is een baseline-kandidaat (de eerste blinde review op veilige drempels kwam gespleten terug, round 022). De openstaande vragen zijn daarom niet meer of het mechanisme bestaat, maar (1) onder welke use-time discipline een promoted seed mag sturen, en (2) of dezelfde doctrine overdraagt naar andere domeinen, taken en modellen.

## Korte samenvatting

De repo heeft inmiddels een sterkere kern dan alleen een kleine scenario-suite:

- `trace` en `weight` zijn formeel gescheiden;
- TTL/TrTL regelen verval en reactivatie;
- EXPIRED is terminaal;
- de Validation Gate bepaalt wanneer invloed mag ontstaan;
- cluster-recurrence kan parafrastische herhaling samenbrengen;
- W9f toont cross-turn payoff via echte sessiecontext;
- blind A/B-review is beschikbaar als kwaliteitscontrole op door SSL geopende antwoordruimte.

De volgende fase is daarom:

> W10: doctrine-transfer.

Niet groter binnen dezelfde A/B-opzet, maar breder toetsen of de bestaande SSL-levenscyclus overdraagt.

## 1. Wat scenario's nu nog doen

Scenario's blijven nuttig, maar hun rol verandert.

Ze zijn niet langer de primaire drager van de hoofdclaim. Ze zijn vooral:

- regressieanker;
- reproduceerbare smoke-laag;
- debugomgeving voor lifecyclewijzigingen;
- vaste vergelijking wanneer nieuwe code oude garanties kan breken.

De hoofdclaim moet verder opschuiven naar:

- open-set seedkwaliteit;
- adversarial ruiscontrole;
- probe utility;
- cross-turn payoff;
- transfer van de doctrine.

## 2. Waarom W9f de overgang markeert

Eerdere single-shot rondes lieten zien dat een frontiermodel veel korte of expliciet gevraagde frames zelf kan noemen. Dat zette SSL als externe single-shot gapdetector onder druk.

W9f verplaatst de claim naar SSL's eigen mechaniek:

```text
wat nu nog geen antwoord is, kan later in de sessie antwoordruimte worden
```

Daarvoor is scenario-overlap niet het juiste hoofdcriterium. De relevante vraag is of een seed:

1. gewichtloos kan ontstaan;
2. via trace kan blijven leven;
3. via TrTL opnieuw wordt herkend;
4. via TTL kan verdwijnen als hij niet terugkomt;
5. pas na Gate-promotie invloed krijgt;
6. later bruikbare antwoordruimte opent.

W9f heeft dit in de huidige setting voldoende laten zien om als baseline te gelden.

## 3. Wat scenario-onafhankelijkheid nu betekent

Scenario-onafhankelijkheid betekent niet dat alle scenario's verdwijnen.

Het betekent dat de hoofdvraag verschuift van:

> vindt de suite de vooraf bedachte gaps?

naar:

> blijft de SSL-levenscyclus betrouwbaar wanneer domein, taak, model en promptvorm veranderen?

Daarbij hoort een andere evaluatielogica.

## 4. W10: doctrine-transfer

### Doel

Toetsen of dezelfde SSL-doctrine buiten de huidige startup/city-testcontext blijft werken.

### Te transfereren doctrine

- atomische seeds;
- `trace` als aanwezigheid;
- `weight` als invloed;
- TTL en TrTL;
- Validation Gate;
- cluster-recurrence;
- representative-based promotie;
- blind A/B-review van surfaced antwoordruimte;
- expliciete labels voor seed-ruis en seed-vernauwing.

### Transferassen

#### 1. Domeintransfer

Nieuwe domeinen zonder de kernlogica te herschrijven:

- onderwijs;
- onderzoek;
- beleid;
- productontwerp;
- juridische of ethische analyse met voorzichtigheid rond claims.

#### 2. Taaktransfer

Niet alleen Q&A:

- planning;
- kritiek;
- samenvatting;
- besluitondersteuning;
- follow-up vraaggeneratie;
- retrieval-query generatie.

#### 3. Modeltransfer

Niet alleen `gpt-4.1`:

- kleiner OpenAI-model;
- frontiermodel;
- lokaal of kleiner model waar mogelijk;
- vergelijking tussen modelcapaciteit en seed-gebruik.

#### 4. Reviewtransfer

Eén reviewerprotocol dat onderscheid maakt tussen:

- SSL maakt antwoord duidelijk beter;
- SSL maakt antwoord anders maar niet beter;
- SSL helpt een beetje;
- SSL vernauwt het antwoord;
- SSL veroorzaakt ruis;
- baseline is beter.

## 5. Acceptatiecriteria voor W10

W10 slaagt niet pas wanneer SSL elk item wint.

Realistische acceptatiecriteria:

- surfaced seeds openen in meerdere domeinen bruikbare antwoordruimte;
- ruis en vernauwing worden expliciet gedetecteerd;
- er is geen systematische overpromotie per domein;
- `weight = 0` tot Gate-promotie blijft gehandhaafd;
- TrTL/TTL voorkomt dat irrelevante seeds eindeloos blijven rondzingen;
- reviewers kunnen verschil zien tussen inhoudelijke verrijking en alleen lengte.

## 6. Wat niet opnieuw moet gebeuren

Vermijd:

- W9f blijven herhalen als bewijs dat SSL bestaat;
- een klassieke model-vs-model A/B-test gebruiken als enige succescriterium;
- succes gelijkstellen aan meer promoted seeds;
- seed-ruis oplossen door alleen recurrence-parameters te tweaken;
- transfer verwarren met domein-priors toevoegen.

## 7. Wat wel moet gebeuren

Bouw W10 als kleine, expliciete transferlaag:

1. kies 2 of 3 nieuwe domeinen;
2. houd lifecycle- en Gate-instellingen verdedigbaar;
3. genereer cross-turn sessies;
4. maak automatisch blind review-packs;
5. laat reviewerlabels seed-effect en ruis expliciet scoren;
6. rapporteer per domein en per taak, niet als één totaalscore.

## 8. Repo-structuur

De aanbevolen structuur blijft:

```text
docs/
  research/
    current-status.md
    w9f-evaluatieconclusie.md
    scenario-independence-roadmap.md
    evaluation-matrix.md

benchmarks/
  open_review/
  transfer/

results/
  blind_ab_review/
```

Belangrijk blijft:

> consolideer infrastructuur en rapportage, maar niet ten koste van epistemische eerlijkheid.

## 9. Eindoordeel

Scenario-afhankelijkheid is niet meer het bewijsprobleem: het W9f cross-turn *mechanisme* staat op veilige drempels. Maar W9f is geen afgesloten payoff-bewijs — de eerste blinde review op veilige drempels kwam gespleten terug (round 022).

De volgende vragen zijn daarom:

> 1. onder welke use-time discipline mag een promoted seed het antwoord sturen (sturen bij aanscherping, dormant bij vernauwing)?
> 2. blijft de SSL-levenscyclus werken wanneer de context verandert?

Samen vormen die de juiste volgende stap naar scenario-onafhankelijke SSL-validatie.

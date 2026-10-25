# G0 — onafhankelijke, geblindeerde beoordeling van latere onderzoeksvragen

> **25 oktober 2026 | Werkinstrument, geen onderzoeksuitkomst. G0 NOT PASSED.**
> De bestaande [meerturns ShadowChatSession + DiscoveryWorld-test](real-shadowchat-discoveryworld-bridge-2026-10-25.md) heeft **alleen mechanische uitvoerbaarheid** bewezen, met vier door de onderzoeker vastgelegde vragen en handelingen. De huidige stap maakt een **latere onafhankelijke beoordeling** technisch mogelijk, niet het ontstaan van een nieuwe mogelijkheid.

## Waarom apart van detector, parser en simulator?

Een detector kan een kandidaat formuleren, een parser kan tekst accepteren en een simulator kan een handeling uitvoeren. Geen van die drie laat zien of een **nieuwe, later ontstane onderzoeksvraag** iets onderscheidt wat anders niet onderzocht zou worden. Ook een succesvolle actie of verschil in de fysieke wereld is niet automatisch een nieuw concept. Een vaste beoordelingssleutel met de "gewenste" vervolgvragen zou de proef opnieuw zelf voorspelbaar maken.

Daarom levert de [broncode voor onafhankelijke beoordelingspakketten](../../../../research/scripts/g0_blind_later_inquiry_review.py) **geen automatische semantische score**. Een assessor krijgt alleen de opeenvolgende zichtbare vragen, herkomst van de zichtbare antwoorden, uitgevoerde onderzoekshandelingen en waarnemingen. De kandidaat-ID, detectoruitvoer, armnaam, trace/weight en bronmapping blijven **bij de onderzoeksbeheerder**.

EAI Blindspot 0.5.4 levert hiervoor uitsluitend de **methodische discipline**: onderscheid observatie en interpretatie, wijs de werkelijke actor aan, behandel onbeslist niet als falen en rechtvaardig een claim alleen met passend bewijs. Dit is **geen toepassing van de onderwijsspecifieke EAI-klassificatierubric**, geen EAI-score en geen nieuw productfilter. EAI Blindspot Core 0.5.4 is bovendien zelf een ontwerp vóór empirische validatie.

## De twee strikt gescheiden fasen

**Fase A — onafhankelijke semantische beoordeling, vóór ontblinding**

Twee afzonderlijke **menselijke** beoordelaars krijgen dezelfde armgeblindeerde, in willekeurige volgorde gepresenteerde cases. Ze mogen de privékaart, armnamen, detectoroutput en onderlinge antwoorden niet zien totdat ieder afzonderlijk zijn beoordeling heeft vastgelegd.

Een reviewformulier vraagt **per case** naar:
- Is een **latere** vraag inhoudelijk anders dan eerdere vragen, of slechts een andere formulering/herhaling? **Onbeslist** is een geldig antwoord.
- Is de vraag via onafhankelijke, algemene regels **in principe toetsbaar**, of ontbreekt in deze evaluator een geschikte toets? **Onbeslist** blijft mogelijk.
- Is er een werkelijk **waargenomen, onafhankelijk controleerbaar later gevolg** dat een ander onderzoek opent, of is dit nog niet aangetoond? De publieke demo staat een positieve bevestiging niet toe.
- Welke **turn-ID's** dragen dit oordeel, waarom, en welke *gewone verklaring* (deliberate search, active learning, extra observaties, menselijke aanwijzing, planning) kan dezelfde stap opleveren?

Deze dimensies zijn **naast elkaar** te beschrijven, niet op te tellen tot een "creativiteitsscore". Twee inhoudelijk verschillende vragen kunnen allebei even goed onderzoekbaar zijn. Een goed klinkende vraag zonder toetsbaar gevolg blijft onbeslist/niet aangetoond. Een vraag buiten de huidige simulatorgrammatica is niet automatisch onzinnig.

**Fase B — gecontroleerde ontblinding, pas na twee onafhankelijke formulieren**

De onderzoekseigenaar vergelijkt de beoordelingen met de bij de bron bewaarde experimentele armen en eventuele specifieke kandidaats-ablatie. Verschillen tussen beoordelaars worden **niet automatisch gemiddeld of opgelost**. De eigen identiteit, de bronherkomst van de modeloutput en onafhankelijkheid van de menselijke beoordelaars moeten **buiten de software aantoonbaar worden bevestigd**.

De [reconcile-opdracht](../../../../research/scripts/g0_blind_later_inquiry_review.py) bewaart de oorspronkelijke twee oordelen, bewijsverwijzingen en openlijke onenigheid; rapporteert **altijd** dat de Q1-claim, causale Q2-toeschrijving en G0-goedkeuring niet automatisch vastgesteld zijn.

## De vier bestandstypen

| Bestand | Toegang | Inhoud |
| --- | --- | --- |
| Originele onderzoekstrace | Onderzoeksbeheerder | Ruwe herkomst, autorisatie, vraag-/antwoordstromen, experimentele arm, kandidaat en assessor-opname |
| **Geblindeerd pakket** | Beoordelaars | Willekeurige identiteiten, gemaskeerde groepsnummers, echte zichtbare turns en in neutrale termen gespecificeerde onderzoeksvragen |
| **Leeg beoordelingsformulier** | Ieder van twee onafhankelijke beoordelaars, apart in te vullen | Inhoudelijk verschil, toetsbaarheid, later gevolg, bewijs-turns, argument, sterkste gewone alternatieve verklaring |
| **Privé-ontblindingskaart** | Alleen onderzoeksbeheerder; **nooit** GitHub commit/artifact of mee met reviewers | Armnaam, bronidentiteit, kandidaatreferenties en de verbinding tussen private en geblindeerde ID's |

De publieke demo uit PR #232 is van oorsprong **al bekend** en is daarom **niet werkelijk blind of confirmatoir**, zelfs als we armnamen in een nieuw pakket maskeren. Het enige doel is controleren of de overdracht, het formulier, de privémapping en de latere ontblinding technisch betrouwbaar zijn. Voor een echte modelstudie is een onafhankelijk ontworpen en beschermd nieuw geval vereist.

## Praktisch uitvoeren met de bestaande echte PR #232-bron

Gebruik de **echte, door GitHub uitgevoerde en gecontroleerde** [brontrace uit run #40169010028](https://github.com/E-AI-MODEL/shadowseed-pro/actions/runs/40169010028), artifact `g0-real-shadowchat-world-bridge-40169010028` (het ZIP-bestand bevat `g0-real-shadowchat-world-bridge.json`). **SHA-256 van de JSON:** `059280cd9fd57c91243e416591bfd0f8b0d4861d10b1dfa362292e7e04a230a0`. Deze versie is geen sealed holdout.

Binnen een *privé* werkmap, met de trace reeds uitgepakt en met een privémap die niet naar de repo of de beoordelaars wordt geüpload:

```bash
install -d -m 700 "$HOME/shadowseed-private-g0"
python research/scripts/g0_blind_later_inquiry_review.py prepare \
  --bridge-json /secure/path/g0-real-shadowchat-world-bridge.json \
  --packet /tmp/g0-blind-review-packet.json \
  --blank-review /tmp/g0-blank-semantic-review.json \
  --owner-map "$HOME/shadowseed-private-g0/owner-pr232.json"
```

Geef twee **kopieën** van de lege template aan twee verschillende onafhankelijke reviewers. De bron wordt altijd aangemerkt als `investigator_scripted_calibration` en `MECHANICS_CALIBRATION`. De template begint **geheel oningevuld**; de eigenaar vult geen beoordeling namens een reviewer in. De reviewer levert onder eigen identificatie en tijdstempel een inhoudelijke beslissing per case met turn-verwijzingen.

Ontblind *uitsluitend* wanneer de twee beoordelaars elk zelfstandig hun formulier afgerond hebben:

```bash
python research/scripts/g0_blind_later_inquiry_review.py reconcile \
  --packet /tmp/g0-blind-review-packet.json \
  --owner-map "$HOME/shadowseed-private-g0/owner-pr232.json" \
  --review-one /secure/path/reviewer-one.json \
  --review-two /secure/path/reviewer-two.json \
  --output "$HOME/shadowseed-private-g0/compared-pr232.json"
```

Het commando weigert ontbrekende beoordelingen, twee keer dezelfde genoemde beoordelaar, ontbrekende evidence-turns, verkeerd getekende pakketidentiteit, ongeldige of ontbrekende beoordeling, automatisch ingevulde successcores, en iedere fictieve bevestiging van een latere ontdekkingsuitkomst bij uitsluitend gescripte input. De **werkelijke onafhankelijkheid en identiteit** worden niet met een formulier of JSON-veld bewezen.

Voor toekomstige onuitgegeven, modelgegenereerde traces bestaat `prepare --input <private-source.json>` met verplicht bron- en feedbackregimelabel. Dat pad is **geen toestemming voor een modelproef**. De afzonderlijke technische evaluator en conceptuele reviewer moeten eerst nog formeel hun veto/goedkeuring kunnen uitspreken. RF (gelijk vervolgbeeld) en RI (verschillende eigen interventiegevolgen) blijven gescheiden; dit meetinstrument maakt daar geen gemengde score van.

## Wat de software bewust niet kan

- De software mag **geen Q1-distributie**, modelinterne neuronrepresentatie of inhoudelijke Q2-groei afleiden uit PR #232.
- De software voert **geen LLM-oproep** uit en vraagt **geen** model om zijn eigen vraag te beoordelen.
- Er is **geen** automatisch G0-succes en geen verborgen benchmarkantwoord om "nieuwheid" te belonen.
- Het masker kan tijdens een adaptief RI-traject herkenbare externe observaties **niet magisch onherkenbaar maken**. Dat risico blijft zichtbaar voor een menselijk reviewer, inclusief een mogelijke blinderingsbreuk.
- Een tweede beoordelaar is geen wetenschappelijk onafhankelijk reviewer als diezelfde persoon de casus/vragen vooraf heeft geschreven. De software kan dat niet controleren.
- Het instrument dwingt geen nieuwe productstatus, seedscore, Gate/point-of-use, TTL/TrTL of wijziging van accepted ADR's af.

**Besluit:** dit is een overdrachts- en bewijsinstrument dat echte semantische beoordeling **later mogelijk maakt**, zonder een resultaat te verzinnen. De [ongevulde G0-reviewledger](dynamic-inquiry-independent-review.md) en [issue #228](https://github.com/E-AI-MODEL/shadowseed-pro/issues/228) blijven open en ongewijzigd.

# G0 v3: beoordelingsdossier voor onafhankelijke beslissing

**Opgesteld: 25 oktober 2026. Besluit: G0 NIET GOEDGEKEURD.**

Dit dossier organiseert de externe beoordeling en actualiseert de herkomst van de reeds uitgevoerde verkennende modelproeven. Het is geen eigen technische of wetenschappelijke goedkeuring. Een PR, een groen testsysteem, een LLM-oordeel of dit dossier kan de twee onafhankelijke mensen niet vervangen.

## Beoordelingsversie en bevroren bronnen

| Onderdeel | Exacte bron | Betekenis |
|---|---|---|
| Oorspronkelijke onderzoeksvraag | [letterlijke Q1/Q2-these](../../possibility-space-thesis.md) | Niet terugbrengen tot alleen memory, meer antwoorden of redeneren |
| Geldend product | `main` op `a5ec14ecc52adcacf85fa9503a22e3fe91527b06` | Echte `ShadowseedEngine` en gemergede [PR #249](https://github.com/E-AI-MODEL/shadowseed-pro/pull/249) voor per-turn gewichtloze checkpoints |
| G0 v3 ontwerp | [model-originated inquiry](dynamic-inquiry-protocol-candidate-2026-10-25.md) en [beoordelingsformulier](dynamic-inquiry-independent-review.md) | De algemene evaluator moet onvoorziene, zinvolle vragen kunnen beoordelen |
| Vergelijkingscontract | [A/B/C/D/E en RF/RI](adapter-evaluation-contract-2026-10-25.md) | Geen effectclaim zonder gelijke informatie-/middelenkansen en kandidaat-specifieke ablaties |
| GPT-5 verkenning 1 | [draft PR #250](https://github.com/E-AI-MODEL/shadowseed-pro/pull/250), head `abff8a02ea866313f33e6ec4f34724d5706e596b`, [run #40215854335](https://github.com/E-AI-MODEL/shadowseed-pro/actions/runs/40215854335) | 20 echte GPT-5-aanroepen; echte geboorten, 4 turns per fictieve case; T0-host/detector-context ongelijk |
| GPT-5 verkenning 2 | [draft PR #251](https://github.com/E-AI-MODEL/shadowseed-pro/pull/251), herleidbare resultaatsnapshot `53646efdad883c4b268ed92435c7d446fabe4699`, [run #40224494313](https://github.com/E-AI-MODEL/shadowseed-pro/actions/runs/40224494313) | 14 modelaanroepen, een echte seed; vijf modelbedachte T1-vragen; T2-checkpoint `ValueError` en gestopt. Geen Q2-toets |
| Negatieve/technische controles | [researchsuite #40225139146](https://github.com/E-AI-MODEL/shadowseed-pro/actions/runs/40225139146) | 432 tests geslaagd, 3 overgeslagen. Geen onafhankelijke inhoudelijke validatie |
| Open productveiligheid | [SSOT-support/contradictie #241](https://github.com/E-AI-MODEL/shadowseed-pro/issues/241) | Relevante bron ≠ daadwerkelijk SUPPORT. Voor G0 moet review bevestigen dat de Gate-route niet als semantische proef wordt misbruikt |

De proef in PR #251 begon nadat de oorspronkelijke G0-v3-instructie was geschreven. Sommige oudere documenten zeggen om die reden nog dat er **geen modelproeven** zijn uitgevoerd. Die historische tekst wordt niet als huidige status gelezen: er zijn wel verkennende proeven, maar **geen onafhankelijke G0-acceptatie, geen besloten holdout of bevestigd Q1/Q2-effect**. De hierboven gepinde commits identificeren *historisch bekeken* code; de review van een nieuwe evaluator en verborgen cases moet een eigen, nieuwe versiepin krijgen.

## Wat G0 formeel betekent

**Een beoordeling van de geschiktheid van het onderzoeksontwerp**, niet van de vraag of Shadowseed werkt. Per E1 (verborgen interactieve mechanismen) én E2 (veranderlijke observatie-/instrumentmogelijkheden) zijn twee zelfstandig geschreven en gedateerde oordelen vereist:

- **R1 technisch:** kan een onafhankelijke, algemeen toepasbare evaluator niet-voorgeschreven modelvragen beoordelen, met echte negatieve/no-opportunity-cases, gescheiden resets, veilige tooluitvoering, provenance, vergunningen en begrensde kosten?
- **R2 wetenschappelijk:** meet dit werkelijk later veranderde *onderzoekbaarheid*? Houdt het ontwerp afwijkende vragen, toetsbaarheid, werkelijk gevalideerd later gevolg en kandidaat-specifieke causaliteit gescheiden? Zijn een sterk gewoon model, uitgebreid zoeken, gewone notities en inhoud-gelijke ablaties serieuze mogelijke verklaringen?
- Beide beoordelaars moeten per E1 en E2 expliciet kiezen uit `ACCEPT FOR LIMITED FEASIBILITY`, `REJECT` of `INDETERMINATE` en hun redenen en veto's bewaren. Eén afwijzing of onbesliste noodzakelijke voorwaarde houdt G0 op **NOT PASSED**. 'Accept' betekent alleen ontwerpgeschiktheid voor een *latere* vooraf afgesproken haalbaarheidsstudie.

Zie [G0 hoofdissue #228](https://github.com/E-AI-MODEL/shadowseed-pro/issues/228), [R1-issue #234](https://github.com/E-AI-MODEL/shadowseed-pro/issues/234) en [R2-issue #235](https://github.com/E-AI-MODEL/shadowseed-pro/issues/235). Die issues bestaan al. Maak geen duplicaten en vervang geen persoon door een AI-review.

## Wat de beoordelaars nu werkelijk moeten falsifiëren

**R1:**
- Kan E1/E2 een vraag behandelen die de auteur niet vooraf kende, maar een model tijdens de proef bedacht? Bestaat er een algemene toelatings- en uitvoerregel, niet een lijst goede antwoorden?
- Worden 'zinvol maar hier niet toetsbaar', 'onmogelijk', 'technisch fout', 'nulresultaat' en 'geen vraag' afzonderlijk geregistreerd?
- Kunnen een nieuwe vraag en de daarop volgende actie een werkelijk ander observeerbaar gevolg produceren onder RI, met precies dezelfde aanvangstoestand en toolrechten?
- Wat kan niet veilig of vergund worden uitgevoerd? Een upstream codefragment met vrije Python `exec` mag niet zonder aparte isolatie draaien.

**R2:**
- Mag de uitkomst falen wanneer een sterk model zonder Shadowseed dezelfde nieuwe vraag vindt? **Ja, dat moet.**
- Is er aantoonbaar een tweede zelfstandig door het model geformuleerde vraag die op een getoetste T1-interventie voortbouwt, en niet op een door de onderzoeker geschreven T2-observatie?
- Worden behoud van een alternatieve verklaring, gewijzigde vraagrichting, verschil in testplan en nieuw onafhankelijke onderzoeksactie als verschillende uitkomsten beoordeeld?
- Wat is de geldige eenheid van analyse? De *casus/seedtrajecten*, niet losse modelcalls of drie zinnen die tot één semantische vraagfamilie behoren.

## Welke bestaande metingen al tellen, zonder overclaim

`prepare_turn → gewone generatie → observe_turn → raw detectoritem → intake → created-event → next-turn checkpoint` is **rechtstreeks herleidbare softwaregedragsregistratie**. De geopende vraag of het model via de aparte onderzoeksroute andere vragen maakt, is **voorlopige gedragsinformatie**. Bij de eerste RF-run wezen alle vijf T1-vragen naar hetzelfde schakel/tijdstip-probleem. In D stond de oorspronkelijke ruimtelijke-sensorhypothese nog in de beschrijving van onzekerheid. Dat kan op hypothesebehoud wijzen, maar een enkele niet-gerandomiseerde vraag bewijst geen causale invloed.

Het gedrag van de gewone host is bovendien **bewust nul beïnvloed** zolang de seed gewichtloos blijft. Dat is een geslaagde veiligheidsafbakening en mag niet worden verward met een uitblijvend effect in een speciaal, gecontroleerd onderzoeksdeel.

Zie [kandidaat-specifiek invloedsonderzoek](seed-influence-causal-measurement-2026-10-25.md).

## Beoordeling registreren: invuldiscipline

Elke reviewer levert apart en vóór overleg:
1. eigen naam, functie/kennisgebied en onafhankelijkheid van auteurs, code en dataset, inclusief belangen;
2. beoordeelde commit van dit dossier, exact E1/E2-upstream-commit, evaluatorversie en gebruikte openbare bewijsmiddelen;
3. eigen probegevallen en bewijsreferenties inclusief negatieve uitkomsten;
4. `ACCEPT FOR LIMITED FEASIBILITY` / `REJECT` / `INDETERMINATE` **per** mechanismefamilie, met onderbouwde veto's;
5. expliciete overweging van de genoemde modelruns als *verkennend* en hun methodische tekortkomingen.

Maak géén openbare GitHub-pagina met de inhoud van een toekomstige afgeschermde confirmatieset. De administratieve identiteit van de reviewer en de onafhankelijkheid worden door een menselijke onderzoeksbeheerder geverifieerd. Een geautomatiseerde volledigheidscheck kan geen onafhankelijkheid of wetenschappelijke geldigheid bevestigen.

## Huidige stopstatus

- **R1 onafhankelijk oordeel: ontbreekt.**
- **R2 onafhankelijk oordeel: ontbreekt.**
- **E1 algemene ongeplande-vraag-evaluator: nog niet voldoende onafhankelijk aangetoond.**
- **E2 afzonderlijk mechanisme en algemene evaluator: nog niet voldoende onafhankelijk aangetoond.**
- **T2-checkpointafwijking in de eerste echte RF-vraagproef: onverklaard, fail-closed bewaard.**
- **Nieuwe afgesloten toetscases: niet ingediend.**

**G0-v3 = NOT PASSED.** Het dossier is nu te beoordelen, niet goedgekeurd. Zodra beide menselijke reviewers werkelijk beschikbaar zijn, krijgen zij afzonderlijk dit dossier en hun eigen bestaande issue. Hun besluiten mogen de status veranderen, niet onze eigen code, AI-beoordeling of groene CI.

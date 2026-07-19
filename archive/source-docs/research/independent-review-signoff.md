# Onafhankelijke review & sign-off van de tussenstappen

> **Doel.** Twee onafhankelijke mensen moeten de tussenstappen van het
> SSL-onderzoek niet alleen kunnen *lezen*, maar ook *begrijpen* en *goedkeuren*.
> Dit document vat elke stap in gewone taal samen, met wat het wél en niet
> aantoont, en bevat onderaan een sign-off-tabel. Het is bewust kort en zonder
> jargon; details staan in de genoemde `round_*`-mappen.

## In één alinea
SSL plaatst bij elk antwoord kleine "schaduw-zaadjes": invalshoeken die nu nog
geen gewicht hebben (geen invloed op het antwoord), maar die in een gesprek
kunnen *meereizen* en, als ze steeds opnieuw relevant blijken, mogen "promoveren"
en een later antwoord rijker maken. De kernvraag van dit onderzoek: **levert dat
meetbaar betere antwoorden op, zonder schade?**

## De tussenstappen (gewone taal)

| stap | wat we deden | wat eruit kwam | wat het betekent |
|---|---|---|---|
| **R010** | Op een sterk model (gpt-4o-mini) een gevalideerd zaadje in het antwoord laten verwerken | 2 wins / 1 gelijk / 0 verlies; geen schade | Handelen op een góéd zaadje helpt en schaadt niet |
| **R011** | Hetzelfde, groter (n=10) | 8 wins / 2 gelijk / 0 verlies | Bevestiging op grotere schaal (door mij beoordeeld) |
| **R012** | Antwoorden netjes laten "weven" i.p.v. lijstjes plakken | Werkt; ontdekte dat onze automatische maat alleen letterlijke herhaling beloonde | We hadden een betere (betekenis-)maat nodig |
| **R013** | Betekenis-maat + **mensen** laten oordelen | **4 mensen, unaniem, eens met de AI op 10/10** | De AI-jury is een betrouwbare proxy; payoff mens-verankerd — op zélf-bedachte zaadjes |
| **R014** | Wat als een *slecht* zaadje toch wordt gebruikt? | Vals → model corrigeert; irrelevant → 2/3 schade | Veiligheid moet vóór het handelen zitten (de "Gate") |
| **lifecycle** | Gate + TTL: slechte/oude zaadjes verdwijnen onomkeerbaar | end-to-end aangetoond | Een slecht zaadje kan niet terugkomen |
| **R015** | Echte (zelf-gedetecteerde) zaadjes op makkelijke nieuwsteksten | Model vindt ~82% zelf | Op makkelijke tekst voegt detectie weinig toe |
| **R016** | Idem met "generatieve" invalshoeken, single-shot | Model vindt ~88% zelf | Single-shot is niet waar SSL z'n waarde heeft |
| **correctie** | Inzicht: R015/R016 testten *niet* de echte SSL-pijplijn (alleen losse strings) | gemarkeerd als NIET-PIJPLIJN | Eerlijk teruggedraaid; opnieuw, nu door de échte pijplijn |
| **R017–018** | Echte pijplijn, meerdere beurten | Promotie vuurde niet (zaadjes herhaalden te zelden) | Bottleneck gevonden: parafrasen "mergen" niet |
| **R019** | Bottleneck verzacht (per-run), echte pijplijn | **Promotie vuurt; 10 cross-turn events; antwoorden rijker** | **Eerste positieve signaal voor SSL's eigen mechanisme** |

## Wat R019 wél en niet zegt (de stap die nu ter goedkeuring ligt)
- **Wél:** door de echte pijplijn reist een vroeg-opgekomen invalshoek mee en
  maakt een later, ánder antwoord aantoonbaar rijker — precies de belofte
  "wat nu geen antwoord is, kan het later worden".
- **Niet (eerlijke grenzen):** het vuurde alleen met **soepelere interne drempels**
  dan standaard; door de **AI beoordeeld**; **n=10**; gespreksonderwerpen **door ons
  gekozen** zodat een thema kón terugkeren. Daarom: **bemoedigend signaal, geen
  bewijs.**
- **Over lengte:** de SSL-antwoorden zijn doorgaans wat langer. Dat is hier
  *niet automatisch* een vertekening: in deze niche is het doel juist een rijker,
  vollediger antwoord, dus extra lengte die echte relevante invalshoeken toevoegt
  is een verbetering, geen opvulling. De review let er daarom op of de extra
  inhoud *waardevol* is (niet of het antwoord langer is).

## Wat we aan de onafhankelijke reviewers vragen
1. Lees deze samenvatting en (steekproef) één `round_*/README.md`.
2. Doe de blinde review: `benchmarks/open_review/rounds/round_019/human_review/review_pack.md`
   (A/B/tie per item; niet in de answer_key kijken).
3. Teken hieronder af: begrijp je de stap, en keur je goed dat we zo doorgaan?

## Sign-off

| reviewer | datum | begrepen? | akkoord met aanpak? | opmerkingen |
|---|---|---|---|---|
| _(naam 1)_ |  | ☐ | ☐ |  |
| _(naam 2)_ |  | ☐ | ☐ |  |

> Onafhankelijk = niet de auteur van de code/zaadjes; bij voorkeur de blinde
> review ingevuld vóór het bekijken van de answer_key.

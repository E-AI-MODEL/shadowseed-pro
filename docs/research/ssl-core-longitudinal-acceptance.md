# Shadowseed kern: longitudinale acceptatietest (zonder Laag G)

Status: toetsbaar mechanisch protocol, **geen** modelkwaliteit- of effectiviteitsbewijs.

## Onderzoeksvraag

Kan een niet-uitgesproken, onderzoekbare mogelijkheid als gewichtloze
kandidaat ontstaan, terugkeren, door TTL en TrTL veranderen en uiteindelijk
verdwijnen, zonder dat herhaling zichzelf tot waarheid of bevoegdheid verheft?

Dit is de SSL Level 1-kern. Modelinterne activaties (H-Neurons/Laag G) zijn
**niet vereist** voor deze toets.

## Vooraf vastgelegde toetsvolgorde

1. **Geboorte:** behoud een concrete relationele vraag met vraagteken.
   Controleer `trace > 0`, `weight == 0`, geen evidence of Gate-event.
2. **Clean herhaling:** dezelfde hypothese wordt opnieuw herkend en trace
   neemt toe. Onder `evidence_backed` weigert de Gate autoriteit op basis
   van recurrence alléén.
3. **Verloop zonder herhaling:** laat trace per geldige beurt afnemen.
   Een niet-herstelde seed wordt DORMANT.
4. **TrTL binnen TTL:** een relevant vervolg activeert de dormant seed
   opnieuw, met behoud van `weight == 0`.
5. **TTL tot terminaliteit:** zonder nieuwe herkenning wordt de seed EXPIRED.
   Expiry blijft terminal, ook bij overeenkomende tekst; een later identiek
   kandidaatvoorstel start hoogstens een nieuwe gewichtloze seed.
6. **Beleidsscheiding:** expliciet `exploratory` kan recurrence toelaten
   als bevoegdheidssignaal, **niet** als externe verificatie of bewijs.
   De huidige live `evidence_backed`-standaard mag er niet door worden
   veranderd.
7. **Foutbestendigheid:** negatieve of niet-eindige tijdstappen mogen de
   tijd, trace, TTL en audit niet omkeren/vervuilen. Fractionele positieve
   tijd blijft mogelijk voor reproduceerbare half-life-calibratie;
   nul stappen is noop.

Deze acceptatie draait echte bestaande `SSLManager`, `lifecycle`,
`Gate` en normalisatiecode, maar gebruikt **vaste fictieve data** en een
deterministische embedding. Geen echt model, menselijke review of
geobserveerd SSL-voordeel wordt hiermee vastgesteld.

## Methode en run

```bash
uv run --no-sync python -m pytest -q tests/test_weightless_inquiry_lifecycle.py
```

**Controle zonder semantische voorselectie:** het toelaatbaar maken van
een relationele vraag is alleen structurele intake. De uitvoer zegt niet
of die vraag werkelijk nuttig, waar of origineel is. Relevantie,
betrouwbaarheid en nut worden apart en later onderzocht.

Na de AB5X-evaluatie is de toelating bewust ruimer: een vraag met één zichtbaar
vraagteken en zonder duidelijk afzonderlijke tweede zin kan als gewichtloze
kandidaat worden vastgelegd. Komma's, opsommingen, lengte en een tweede
bijzin zijn geen redenen om die mogelijkheid al vóór opslag weg te gooien.
Een samengestelde vraag is hiermee niet aantoonbaar één semantische hypothese.
Het opslaan ervan is geen goedkeuring, geen bewijs, geen systeeminstructie
en geen vrijbrief om de Gate te omzeilen.

## Release- en onderzoeksgrens

Deze wijziging bewaart detector v0.6 en zijn promphash op `main`.
De v0.7-detector uit [PR #202](https://github.com/E-AI-MODEL/shadowseed-pro/pull/202)
heeft nog geen representatieve onafhankelijk beoordeelde open-set-kwaliteit
en wordt daarom **niet stilzwijgend de productstandaard**.
De opname van vragen in de kern, TTL/TrTL/Gate-regels en tijdvalidatie
kunnen onafhankelijk van de nieuwe prompt worden geregressietest en
vrijgegeven. De nog niet goedgekeurde generatieproef blijft bewaard
als onderzoeksbron, niet als geclaimde vooruitgang.

De tests beantwoorden *of de kern haar mechanische contract bewaakt*,
niet *of SSL voor mensen merkbaar betere antwoorden veroorzaakt*.

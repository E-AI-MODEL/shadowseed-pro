# ShadowSeed tegenover MIT's gewichts-editexperiment

Datum: 3 november 2026. Dit is een afgebakend onderzoeksverslag, geen bewijs van wetenschappelijke meerwaarde.

## Vraag

Vindt ShadowSeed een concrete, nog niet onderzochte hypothese in de gepubliceerde MIT-gegevens die met een gerichte gewichts-editproef kan worden getoetst?

MIT-bron: [lm_understand-logs, exp8_math, p50c](https://github.com/RikiyaT/lm_understand-logs/tree/4d09ba6d6a7e891dd8063974dfe81b3d78e3494f/exp8_math/runs/p50c).
ShadowSeed-bron bij aanvang: commit `7427181c50fabae8f9cbd112c3e549e752edf914`. Alle wijzigingen staan op de afzonderlijke branch `research/mit-shadow-memory-replay-20261103`.

## Werkelijk uitgevoerd

| Proef | Invoer | Resultaat | Controleerbaar bewijs |
|---|---|---|---|
| v1 | Eerste 12 van 158 MIT-beurten; Qwen2.5-0.5B, huidige pair-detector | GitHub groen, 0 kandidaten opgeslagen. Detector gaf op alle 12 beurten tekst terug, maar geen geldige seeds. | [Run 41717970040](https://github.com/E-AI-MODEL/shadowseed-pro/actions/runs/41717970040) |
| v2 | Vijf expliciete MIT-hypotheses; Qwen2.5-1.5B in chat-formaat, MiniLM-embeddings, echte ShadowseedEngine | 4 regressietests geslaagd, 10 kandidaten geproduceerd en als gewichtloze seeds opgeslagen. Veel voorstellen pasten niet bij het onderzoek. | [Run 41725274953](https://github.com/E-AI-MODEL/shadowseed-pro/actions/runs/41725274953) |
| v3, laatste beoordeelde versie | MIT-beurten 1, 3, 34, 64, 142; Qwen2.5-1.5B, methodefilter en onaangetaste ShadowSeed-intake | 14 regressietests geslaagd. 8 voorstellen al in methodefilter afgewezen, 1 doorgelaten, maar door ShadowSeed terecht met `not_atomic` geweigerd. 0 seeds opgeslagen. De onderzoeksrun is rood. | [Run 41727811847](https://github.com/E-AI-MODEL/shadowseed-pro/actions/runs/41727811847), [ruwe uitvoer](https://github.com/E-AI-MODEL/shadowseed-pro/actions/runs/41727811847/artifacts/13274968123) |

De v3-uitvoer bevestigt dat `not_atomic` uit de bestaande `ingest_detection_candidates` komt, niet uit een transportfout. De kandidaat combineerde een baseline-beschrijving, een tokenwaarschijnlijkheidsmeting en een tweede vergelijking in één lange tekst. ShadowSeed bewaarde de afwijzing en haar herkomst.

Andere afgewezen Qwen-voorstellen gingen over training van een bevroren model, willekeurig geïnitialiseerde gewichten of zelfs 'students who fail the test'. Zulke voorstellen sluiten niet aan op MIT's specifieke experiment. Dit zijn uitvoerproblemen van de modeldetector en de onderzoeksspecifieke invoer. Het is geen bewijs dat het geheugenmechanisme van ShadowSeed niet werkt.

## Technische diagnose

- V1 gebruikte regelmatig Python-code en kunstmatige vragen als detectivekst; de taalmodel-uitvoer paste niet bij het parsercontract.
- V2 gebruikte echte hypothesezinnen en een chat-template. Het technisch intakepad werkte, maar de voorstellen waren methodisch vaak te breed of onjuist.
- V3 voegde een beperkte methodefilter en een brongebonden meetverslag toe. De originele parser bleef fail-closed bij `NONE` plus extra tekst. Meerregelige, expliciet gelabelde meetuitkomsten werden binnen de research-adapter verwerkt, zonder de productparser te veranderen.
- De actuele v3-regels zijn een grove voorselectie, geen semantische validatie. Een kandidaat die deze regels haalt, kan nog ongeschikt of niet-atomair zijn. De bestaande ShadowSeed-intake weigerde het enige geval dat door de voorselectie kwam.
- Tijdens deze replay zijn geen seeds met bewijs gepromoveerd en is geen historisch MIT-antwoord aangepast.

## Niet aangetoond

Er is **geen** nieuwe MIT-hypothese gevonden, geen verbetering tegenover gewone onderzoeksnotities gemeten en geen causale winst bij modelgewichten aangetoond. Slechts vijf geselecteerde MIT-observaties zijn in de laatste proef aan de detector aangeboden. De test dekt niet het volledige traject van 158 beurten. Er is ook geen blinde menselijke beoordeling van de kandidaten uitgevoerd.

## Verantwoord vervolg

Laat de onderzoeksbranch staan, wijzig `main` niet en forceer geen positieve kandidaat door telkens de parser te versoepelen. Gebruik eerst een vaste, vooraf beoordeelde testset met geldige en ongeldige voorbeelden. Vergelijk daarna minstens twee modeldetectoren op hetzelfde materiaal. Meet apart: (a) uitvoer volgens contract, (b) aansluiting op de bron, (c) atomaire opslag, (d) echt niet eerder onderzochte mogelijkheid volgens broncontrole, en (e) toegevoegde waarde boven MIT's eigen notities of een gewone AI-analyse. Een hoge overeenkomstscore of een groene workflow bewijst (d) en (e) niet.

**Besluit:** de technische onderzoeksadapter is beter controleerbaar geworden. De huidige detectorproef ondersteunt nog geen voorstel om MIT op basis van ShadowSeed te benaderen. Stop hier met het tunen van dezelfde vijf voorbeelden en ontwerp een nieuwe, vaste vergelijking voordat de dataset wordt uitgebreid.

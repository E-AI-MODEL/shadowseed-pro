# MIT / ShadowSeed: wat een inhoudelijke koppeling betekent

Onderzoeksdatum: 3 november 2026. Deze notitie beschrijft de **uitgevoerde** vergelijking op de onderzoeksbranch. Zij verandert geen productcode of onderzoek van MIT.

## Uitgevoerde controles

- GitHub Actions: [run 41731705475](https://github.com/E-AI-MODEL/shadowseed-pro/actions/runs/41731705475), **geslaagd** op commit `8598e12a553503fdba517741616857213fa7056b`.
- Regressies: **12 geslaagd**. De MIT-bron `exp8_math/runs/p50c/readable/trajectory.md` is opnieuw met Git-hash `caa2d040547e81677f98cccb1854769b1057f3b7` gecontroleerd.
- Er zijn **29** achteraf geselecteerde paren aan `Qwen/Qwen2.5-1.5B-Instruct` voorgelegd. Elk paar bestond uit twee originele MIT-hypotheseteksten. Dit was een gewone modelbeoordeling **zonder ShadowSeed**, geen extra modeltraining.
- Ruwe uitvoering: [artifact mit-shadowseed-relation-comparison](https://github.com/E-AI-MODEL/shadowseed-pro/actions/runs/41731705475/artifacts/13277831376). Bewaart `all_pair_results.json`, `summary.json` en `manifest.json`.

| Waarneming | Aantal |
| --- | ---: |
| Beoordeelde paren | 29 |
| Parseerbare modeloordelen | 29 |
| Qwen: dezelfde specifieke claim | 4 |
| Qwen: verwant maar verschillend | 25 |
| Qwen: geen duidelijk direct verband | **0** |
| Paren die in hetzelfde bestaande ShadowSeed-herhalingscluster zaten | 16 |
| Daarvan door Qwen 'dezelfde claim' genoemd | 3 |
| Daarvan door Qwen 'verwant maar verschillend' genoemd | 13 |
| Paren buiten hetzelfde herhalingscluster die Qwen toch verwant/gelijk noemde | 13 |

De 29 voorbeelden zijn geselecteerd nadat de MIT-inhoud en eerdere ShadowSeed-clusters al bekeken waren. Deze steekproef levert **geen onafhankelijke nauwkeurigheidsscore**.

## Drie concrete gevallen

**MLP en attention-heads: een zinvolle verbinding, geen identieke ingreep.** MIT-beurt 13 onderzoekt het verwijderen van een schrijf­richting uit het MLP van laag 19. Beurt 60 stelt dat twee attention-heads herhaling onafhankelijk van MLP-bewerkingen versterken. ShadowSeed bracht ze bijeen, Qwen koos `RELATED_DISTINCT`. Dat is geen bewezen fout: beide horen bij hetzelfde mechanistische onderzoek, maar blijven verschillende causale ingrepen.

**Experimentadministratie en attention-heads: te ruim verband.** Beurt 44 gaat over het veilig parsen van JSONL om een onafhankelijke validatieset te krijgen. Beurt 60 gaat over attention-heads. ShadowSeed plaatste ze niet in hetzelfde herhalingscluster. Qwen koos ook hier `RELATED_DISTINCT`. Op basis van deze twee teksten is een direct inhoudelijk verband niet goed onderbouwd. De gewone AI gebruikte de categorie 'geen duidelijk direct verband' nergens. Dit tast zijn onderscheidend vermogen als beoordelaar aan.

**Letterlijke herhaling hoeft geen tweede opgeslagen seed te worden.** Beurt 81 en 82 bevatten precies dezelfde hypothese over alpha2 versus alpha4. Qwen herkende `SAME_CLAIM`. ShadowSeed gaf geen twee leden in hetzelfde recurrente cluster terug, omdat de Engine letterlijke dubbelen bij de opslag kan samenvoegen. Dat mag niet worden gelezen als het missen van de herhaling; controleer daarvoor de observatie- en recurrence-registratie.

## Wat de meting niet bewijst

- `RELATED_DISTINCT` betekent dat Qwen een verband **beweert**. Dit is geen onafhankelijk oordeel dat de relatie inhoudelijk zinvol of door bewijs gesteund is.
- Qwen kreeg per vraag **twee** notities, niet op hetzelfde moment de gehele historie die het ShadowSeed-geheugen eerder kon verwerken. Dit is **geen eerlijke gelijkwaardige vergelijking van een normale AI met een geheugenagent**.
- De 16 herhalingsclusterverbindingen zijn semantische geheugenstructuur. Ze bewijzen geen nieuwe onderzoeksvraag, onafhankelijke bevestiging, betere beslissingen of verbetering van de MIT-modelgewichten.
- Er is geen onafhankelijke, blind samengestelde en beoordeelde set beschikbaar. De bestaande `causal_pair_reference.json` bevat voorlopige, achteraf gekozen duidingen en mag niet als gouden standaard dienen.
- De uitvoering levert **geen** prestatieverbetering of causale bijdrage aan MIT's experiment.

## Besluit en volgende proef

Behoud het huidige ShadowSeed-clustermechanisme. Het signaleert zowel samenhang als herhaling, en is niet op grond van deze proef defect. Voeg geen autorisatie of gewicht toe op basis van semantische nabijheid. Verander ook niet de bestaande code om alle uiteenlopende hypotheses gedwongen apart op te slaan.

Een volgende geldige proef vereist vooraf gekozen historische tijdstippen. Per tijdstip ontvangen ShadowSeed en een gewone AI **precies dezelfde al beschikbare MIT-notities**. Meet afzonderlijk:

1. relevante verbanden tussen verschillende hypothesen;
2. werkelijke herhaling van dezelfde claim of ingreep;
3. te ruime verbanden die slechts het algemene onderwerp delen;
4. of een gevonden verband leidt tot een **uitvoerbare, nog niet onderzochte vergelijking**.

Gebruik een vooraf vastgelegde beoordelingsrubriek, controleparen met echte verschillen binnen hetzelfde experiment en een beoordelaar die niet weet welke methode de koppeling voorstelde. Rapporteer afwijzingen en nulresultaten. Vergelijk daarnaast feitelijke kosten en aantallen modelaanroepen. Pas bij een positieve uitkomst kan een gerichte, onafhankelijke MIT-vervolgproef worden voorgesteld.

**Status:** technische pairwise proef uitgevoerd en gemeten; relatiekwaliteit slechts deels nagekeken; wetenschappelijke meerwaarde tegenover een gewone AI met volledige historie **niet vastgesteld**. Geen merge naar `main`.

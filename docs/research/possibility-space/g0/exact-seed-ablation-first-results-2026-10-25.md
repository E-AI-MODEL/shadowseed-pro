# Exacte seed-ablatie: eerste echte GPT-5-resultaat

> Uitgevoerd op 25 oktober 2026. **Post-hoc verkennende proef, één bevroren casus, één echte seed, zonder onafhankelijke inhoudelijke beoordeling.** Geen G0-goedkeuring, geen Q1-bewijs over interne modelrepresentaties en geen aangetoonde Q2-uitbreiding van onderzoekbare mogelijkheden.

## Ruwe bronnen

- [Voltooide GitHub Action #40232952059](https://github.com/E-AI-MODEL/shadowseed-pro/actions/runs/40232952059), zestien echte `gpt-5-2025-08-07` Responses-aanroepen met lage redeneerinspanning, `store:false`.
- Bron is de **niet gewijzigde** gedeeltelijke [RF-run #40224494313](https://github.com/E-AI-MODEL/shadowseed-pro/actions/runs/40224494313), oorspronkelijke `observed.json` SHA-256 `62f778fb53547f2c0532795ccb31f02f09381500a2eb67b7598bf86ae597820f`. De eerste seedgeboorte en T1-checkpoint waren vooraf geverifieerd.
- Werkelijk nieuwe raw `observed.json` SHA-256 **`d0f7db05ad5d53ae0ef9487d2d92e54a0de504563782b0e0614e9ecce0d95da9`**, in artifact **`exact-seed-ablation-owner-40232952059`**. Het afzonderlijke **`exact-seed-ablation-blind-40232952059`** bevat de 16 antwoorden onder verborgen conditielabels en nog lege menselijke beoordelingen.
- Methode, vaste oproepvolgorde, controlelengte en budget werden vóór deze nieuwe modelcalls vastgelegd in [het protocol](exact-seed-ablation-t1-protocol-2026-10-25.md). Dit protocol is echter opgesteld **nadat de eerdere T1-resultaten al bekend waren**. Ook een vooraf vastgelegde herhaalproef op hetzelfde voorbeeld wordt daardoor geen afgeschermde bevestigingsstudie.

## Technische uitvoering

| Waarneming | Uitkomst |
| --- | ---: |
| Modelaanroepen voltooid | **16/16** |
| Geldige JSON-onderzoeksvragen | **16/16** |
| Echte D-seed aanwezig in de aparte onderzoeksprompt | 4/4 |
| Modelaanroepen in X/P/N met letterlijke D-seed in hun prompt | 0 |
| Gebruikte embeddingaanroepen | 0 |
| Providergerapporteerde input- + outputtokens | **51.210** |
| Beoordelingen door onafhankelijke mensen | **0** |

Iedere conditie kreeg exact hetzelfde gewone T0/T1-gesprek, dezelfde externe T1-waarneming en dezelfde onderzoeksinstructie. Alleen het bestaande veld met een onbewezen notitie verschilde. De gewone product-host werd **niet** aangeroepen of beïnvloed. De vier oproepvolgordes waren vooraf verschoven: elke conditie stond één keer op iedere positie. Elke conditie kreeg vier afzonderlijke GPT-5-aanroepen; er werd geen gecontroleerde samplingseed gebruikt.

De echte D-seed en de neutrale placebo P waren beide **185 tekens**; hun modelinput bedroeg respectievelijk **2.531 en 2.532 tokens per aanroep**. De X-conditie met `NONE` gebruikte 2.493 inputtokens; de gewone notitie N 2.611. Token- en informatiebalans is daarmee niet perfect en mag niet als identiek worden voorgesteld.

## Eerste beschrijvende waarnemingen, géén automatische inhoudelijke score

Alle zestien voorgestelde **hoofdvragen** onderzochten de temporele relatie tussen de uitschieters in kanaal 1 en de schakelmomenten of activiteit van de regelkast. In de D-conditie ontstond in geen van de vier vragen een zichtbaar afzonderlijke **ruimtelijke-meetverschillenproef**.

In de tekst over wat onzeker blijft, werd de precieze uitdrukking **‘ruimtelijke offset’** wel herkend:

| Conditie | Vragen over schakelmomenten/actieve intervallen | Letterlijke uitdrukking ‘ruimtelijke offset’ in onzekerheidsveld |
| --- | ---: | ---: |
| **D**: oorspronkelijke echte gewichtloze seed | 4/4 | **2/4** |
| **X**: seed in exact dezelfde prompt verwijderd | 4/4 | 0/4 |
| **P**: even lange neutrale administratieve notitie | 4/4 | 0/4 |
| **N**: oorspronkelijke gewone gespreksnotitie | 4/4 | 0/4 |

Dit is een **achteraf uitgevoerde exacte woordtelling**, geen semantische score. Synoniemen, impliciete suggesties en bredere fysische verklaringen zijn daarmee niet betrouwbaar afgevangen. De bijbehorende vier P- en N-antwoorden kunnen eigen relevante alternatieven hebben genoemd zonder deze specifieke woorden. De onafhankelijke raters moeten dat uit de volledige teksten beoordelen.

De twee D-uitvoerfragmenten luidden:

- `ruimtelijke offset tussen sensoren blijven onbewezen` (onzekerheid in ronde 1)
- `ruimtelijke offset en filters blijven mogelijke verklaringen` (onzekerheid in ronde 3)

Het antwoord mét seed koos daarmee **niet aantoonbaar een andere hoofdonderzoeksvraag**, maar herhaalde in twee gevallen wel expliciet het bewaarde alternatieve idee als onbewezen mogelijkheid. Het woord dat wij zelf als seed aanboden, kan ook door gewone tekstconditionering zijn teruggekeerd. **Dat zou een effect van blootstelling aan de seedtekst zijn, niet automatisch van het bijzondere Shadowseed-geheugen of van een nieuw modelmechanisme.**

## Wat de proef wel toevoegt

We hebben nu een reproduceerbare, in broncode, modelreceipts en hashes te controleren **manipulatie van één specifieke, echt geboren kandidaattekst**. De eerdere vijf-armige proef gaf verschillende onderzoeksinstructies en notitielengtes; deze proef houdt de complete onderzoeksinstructie gelijk, verschuift de volgorde evenwichtig en varieert alleen de inhoud van het oude notitieveld. Dit maakt een beperkt gedragscontrast veel beter meetbaar.

De relevante vervolgvragen zijn nu concreet en niet cosmetisch: blijft de oude onbewezen hypothese aantoonbaar beschikbaar? Zet die hypothese het model ertoe aan een werkelijk **andere toets** te ontwerpen? Is die toets onafhankelijk uitvoerbaar? Het verschil tussen een vermelding in de onzekerheid en een nieuwe onderzoeksvraag staat centraal.

## Waar de wetenschap nog moet ingrijpen

- **Eén casus en één seed** leveren geen populatie-effect op. Vier afzonderlijke GPT-5-uitvoeren per variant zijn herhaalde sampling binnen hetzelfde scenario, geen vier nieuwe onderzoeksomgevingen. Geen betrouwbaar generaliseerbare effectgrootte of bewijs van unieke mogelijkheidsexpansie.
- Het gekozen T1-scenario en de seed waren al bekend uit een eerdere proef. We kunnen met deze uitkomst **geen nieuwe confirmatiestudie achteraf construeren**.
- De blind-bestanden zijn gemaakt, maar **geen menselijke onafhankelijke beoordeling is afgerond**. Uitvoerecho's en de beoordeling van alternatieve testplannen mogen niet als onafhankelijke data worden voorgesteld.
- De controlevariant P is lengte-gelijk in **tekens**, maar bevat irrelevante administratieve informatie; X heeft minder tokens; N een langere gewone notitie. De effecten van notitielengte, tekstdomein en modelstochastiek zijn niet verdwenen.
- **Q1**: een zichtbaar herhaalde hypothese bewijst niet dat een niet-uitgesproken relatie vooraf intern als zelfstandige representatie aanwezig was.
- **Q2**: geen van deze modelbedachte vragen is uitgevoerd. Er was geen nieuwe RI-feedback of aantoonbare verandering in wat een onafhankelijk onderzoeker werkelijk kon toetsen.
- **G0 = NOT PASSED**; twee onafhankelijke menselijke beoordelingen en de algemene evaluator blijven een apart besluit. De onverklaarde T2-checkpointfout van de eerdere run blijft open.

De volgende verdedigbare stap is **eerst de twee geblindeerde beoordelingen van deze echte outputs**, en daarna een nieuw, vooraf onbekend aantal onafhankelijke casussen en seeds met hetzelfde D/X/P/N-contract. In een latere RI-studie moet de onderzoeksvraag vervolgens werkelijk worden uitgevoerd en moet het model met een nieuw, onafhankelijk resultaat verder kunnen. De aard van een LLM zelf en mogelijke H-Neuron-activaties vallen onder een afzonderlijke Q1-proef.

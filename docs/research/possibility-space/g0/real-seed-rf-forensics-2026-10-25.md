# Forensische controle van de eerste echte RF-proef (25 oktober 2026)

> **Verkennend, onvolledig, niet door externe beoordelaars beoordeeld.** Dit document is gebaseerd op de ruwe GitHub-uitvoer en twee **achteraf** toegevoegde, modelvrije controles. Geen nieuwe GPT-5-aanroepen, geen productwijziging en geen G0-goedkeuring. De exacte T2-foutoorzaak is met het oorspronkelijke artifact niet vast te stellen.

## Vastgehouden bronnen

- Echte [Action #40224494313](https://github.com/E-AI-MODEL/shadowseed-pro/actions/runs/40224494313), broncommit `7677f8e145c4766ff3fea5451c95acea21edaacb`. Status **failure**, na 14 voltooide GPT-5-aanroepen, 10 embeddingaanroepen, 37.503 geregistreerde tokens.
- Oorspronkelijk researchartifact `g0-real-seed-rf-inquiry-40224494313`, bestand `observed.json`, SHA-256 **`62f778fb53547f2c0532795ccb31f02f09381500a2eb67b7598bf86ae597820f`**. De complete ongefilterde antwoorden blijven daar; deze pagina publiceert geen nieuwe verkorte of hernoemde vervangende dataset.
- [Action #40231042410](https://github.com/E-AI-MODEL/shadowseed-pro/actions/runs/40231042410): **10 modelvrije forensische tests geslaagd**; het artifact is met de oorspronkelijke SHA opnieuw opgehaald en gecontroleerd. Uitvoer `g0-rf-forensics-offline-40231042410`.
- [Action #40231215980](https://github.com/E-AI-MODEL/shadowseed-pro/actions/runs/40231215980): **8 tests geslaagd**; A/B/C/D/E-onderzoeksprompts voor T1 **volledig gereconstrueerd en met de oorspronkelijk gelogde SHA's vergeleken**. De oorspronkelijke promptfunctie en fixture bleken in de onderzochte codeversies gelijk. Uitvoer `g0-rf-t1-prompt-lineage-40231215980`.

## Wat rechtstreeks uit de ruwe records bevestigd is

1. Op **T0** werd de eerste, gewichtloze seed `ss_001` werkelijk via detectoritem → intake → eerste geboorte vastgelegd. De bevroren T0-geboortehash, kandidaattekst en intakegegevens sluiten op de opgeslagen bron aan.
2. Op **T1** is een geldige opvolgcheckpoint van precies die seed bewaard. De hash van de opgeslagen T0/T1-geschiedenis en het T1-rapport komt overeen met de hash die op T1 is vastgelegd. Het gewicht en het aantal bewijsstukken bleven nul.
3. De volledige gewone gespreksantwoorden in het archive rapporteren **geen geselecteerde of getoonde seeds**; het afzonderlijke NONE-controlepad kreeg diezelfde antwoorden. Dit controleert de geregistreerde softwaregrens; het bewijst niet welke concepten het hostmodel onbewust heeft verwerkt.
4. Vijf verschillende T1-onderzoeksarmen leverden ieder één geldige modelvraag. **Alle vijf** gingen over tijdelijke samenhang tussen sensorpieken en schakelmomenten van de regelkast. In D werd de oorspronkelijke ruimtelijke sensorhypothese wél in een onzekerheidsvoorbehoud genoemd. Dat is één mogelijke tekstuele echo, niet een onafhankelijk vastgestelde, causale werking.
5. De gewone T2-hostaanroep en de afzonderlijke T2-detectoraanroep zijn voltooid en gearchiveerd. Daarna ontbrak een geldige opvolgcheckpoint en werden **geen** T2-onderzoeksvragen opgeroepen. De bron bewaart `ValueError`, maar niet de fouttekst en evenmin de volledige T2-manager-/eventlog- en Gate-snapshot. **De precieze falende invariant blijft UNKNOWN.** Een onbekende fout is geen `NONE`-resultaat en geen bewijs dat de seed verdween.

## Werd de echte seed werkelijk alleen in D aangeboden?

De eerdere rapportage gaf alleen aan wat de runner volgens de code hoorde te doen. Dat was nog geen verificatie van iedere oorspronkelijke invoertekst. Met de ongewijzigde oorspronkelijke fixture en zichtbaar opgeslagen gewone geschiedenis zijn de vijf T1-onderzoeksprompts exact opnieuw opgebouwd. Alle vijf prompt-hashes, notitie-hashes en lengtes kwamen overeen met de **vóór de modelaanroep vastgelegde** records.

| Arm | Prompttekens | Extra notitietekens | Letterlijke T0-seed in onderzoeksprompt? |
| --- | ---: | ---: | --- |
| A: normaal | 9.879 | 4 (`NONE`) | Nee |
| B: doelgericht zoeken | 9.960 | 4 (`NONE`) | Nee |
| C: gewone notities | 10.320 | 445 | Nee |
| **D: echte Shadowseed** | **10.060** | **185** | **Ja** |
| E: ander echt T0-detectoritem | 9.995 | 120 | Nee |

**Wat nu sterker gecontroleerd is:** de behandeling D bestond in deze gereconstrueerde **aparte onderzoeksprompt** aantoonbaar uit de exacte kandidaattekst, zonder letterlijke overspraak naar A/B/C/E. Dit is een herleidbare invoerinterventie, geen aangetoonde verandering in het model.

**Beperking:** de prompts waren niet werkelijk gelijk in lengte, zoekinstructie of notitie-inhoud. D verschilt bijvoorbeeld 65 prompttekens van E; C bevat 260 meer tekens dan D. Verder is er maar **één onafhankelijke casus/seed/T1-moment**, niet vijf onafhankelijke effectmetingen. Een stilistisch of inhoudelijk afwijkend antwoord kan door sampling, context, instructie of gewone domeinkennis ontstaan. Ook een letterlijke echo kan spontaan in een baseline verschijnen. Een onafhankelijke beoordelaar moet het inhoudelijke onderscheid blind beoordelen.

## Welke T2-fout we na deze controles wel en niet hebben afgebakend

De T1-checkpoint is intern consistent met de *later opnieuw gedownloade* T0/T1-rapporten, inclusief historische volgorde. Een achteraf overschreven gewone T1-report of bewust verzonnen seedgeboorte zou de gecontroleerde hashes breken. De T2-rapporten zijn eveneens chronologisch, met een schone gewone antwoordroute.

**Niet beschikbaar in de oorspronkelijke run:** de T2-managertoestand en eventlog waarmee `freeze_weightless_followup` het eigenlijke `ValueError` bepaalde. Dat kan niet verantwoord worden gereconstrueerd uit alleen de zichtbare detector- en antwoordtekst. De nieuwe fail-closed foutcode-/hashlogging in PR #251 dient een volgende echte afwijking te lokaliseren. Er is **geen productfout bewezen en niets stilzwijgend gerepareerd**.

## Wetenschappelijke betekenis en volgende toets

De gecontroleerde metingen zijn: herkomst, exacte gewichtloze identiteit, meerturnsbehoud, gescheiden blootstelling en vijf **echte door GPT-5 geformuleerde** T1-vragen. Dit is een bruikbare reproduceerbare **methodische basis**; het toont nog geen onderscheidend effect van D, laat staan intern niet-gekozen activaties of een nieuw onderzoekbare tweede-orde mogelijkheid.

Een volgende, prospectief vastgelegde contrastproef moet de exacte seed enerzijds aanbieden en anderzijds **wegnemen zonder de rest te veranderen**, met een aparte lengte- en inhoudsvergelijkbare notitiecontrole, hetzelfde sterke model, gelijke oorspronkelijke informatie, meerdere onafhankelijke gevallen en geblindeerde semantische codering. Pas een onafhankelijk uitgevoerd nieuw experiment kan aantonen of de vraag een werkelijke nieuwe vervolgonderzoeksmogelijkheid opent. RF-voorspelde externe waarnemingen mogen niet als RI-reactie op een modelvraag worden voorgesteld.

G0 blijft **NOT PASSED** en vereist afzonderlijke externe beoordelingen onder [#234](https://github.com/E-AI-MODEL/shadowseed-pro/issues/234) en [#235](https://github.com/E-AI-MODEL/shadowseed-pro/issues/235). Deze na-analyse is geen preregistratie van de oude modelproef, geen onafhankelijke review en geen aanleiding voor verborgen herhaalde betaalde aanroepen.

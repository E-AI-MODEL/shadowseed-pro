# ShadowSeed x MIT: proefopzet met vijf gelijke onderzoeksarmen

**4 november 2026. Alleen technische voorbereiding; G0 blijft NOT PASSED.**

## Wat we hebben gemeten

De historische equal-history-replay bevat vijf checkpoints. De **oorspronkelijk opgeslagen parseruitkomst** was vijfmaal `invalid_format`, maar de afzonderlijke [historische heranalyse op de MIT-onderzoeksbranch](https://github.com/E-AI-MODEL/shadowseed-pro/blob/research/mit-shadow-memory-replay-20261103/research/experiments/mit_shadow_memory_20261103/EQUAL_HISTORY_REANALYSIS.md) had de fout al gevonden: het model gebruikte `t019` waar de parser het voorvoegsel `t` afwees. Met het bewaarde ruwe antwoord én de 85 originele bronnotities zijn nu **vier van de vijf antwoorden opnieuw als structureel geldig bevestigd**. Het vijfde, losse `NONE`, blijft een ongestructureerde onthouding. De oorspronkelijke uitkomst wordt niet overschreven, en de vier verwijzingen zijn niet automatisch inhoudelijk juist.

Het eerder uitgevoerde retrospectieve blindonderzoek blijft apart. Acht geselecteerde relaties werden verdeeld over vier ShadowSeed- en vier Qwen-vondsten. De anonieme beoordelaar vond beide routes bij alle vier bruikbaar. Dit is geen rechtstreekse toets van een unieke ShadowSeed-bijdrage.

## Nieuwe technische preflight

`research/scripts/mit_matched_preflight.py` gebruikt alleen Python-standaardbibliotheken en heeft twee commando's. `audit-history` telt de oorspronkelijke technische parserfouten en kan met de originele `source_hypotheses.json` bovendien een gecontroleerde, afzonderlijke herparse uitvoeren. Bij die herstelstap blijven de originele uitkomst en de gecorrigeerde uitkomst naast elkaar bestaan. `check-plan` controleert een **synthetische** onderzoeksopzet en stopt bij ongelijkheid. Geen taalmodelaanroep, geen gebruik van de oorspronkelijke privé-ontblindingssleutel en geen wijziging aan de product-Gate.

Het programma weigert een onvolledige set onderzoeksarmen, ongelijke modelidentiteit, decoding, geschiedenis, begincontext of call-/token-/tool-/retrievallimieten. De ShadowSeed-kandidaat in D moet vóór de blootstelling bestaan en gewichtloos blijven. In E moet precies die kandidaat ontbreken en een lengte-gematchte, anders gehashte schijnnotitie staan. De controle verifieert alleen **opgegeven metadata**: niet dat de echte modelpayloads deze hashes hebben of dat de neutraliteit van de schijnnotitie bewezen is.

## Vijf onderzoeksarmen

| Arm | Wat de methode ziet | Wat je meet |
| --- | --- | --- |
| A, gewoon model | Dezelfde geschiedenis en actuele gegevens | Welke vragen zonder speciale hulp ontstaan |
| B, bewust zoeken | Dezelfde gegevens, vooraf vastgelegde zoekopdracht | Of gewone gerichte verdieping voldoende is |
| C, gewone notities | Dezelfde gegevens en gewone bewaarde notities | Of alleen geheugen het verschil verklaart |
| D, gewichtloze ShadowSeed-kandidaat | Eén werkelijk eerder geboren kandidaat, uitsluitend in onderzoekssessie | Of die specifieke kandidaat de latere vraag beïnvloedt |
| E, kandidaat-ablatie | Dezelfde route als D, maar de kandidaat is vervangen door een schijnnotitie | Of het effect wegvalt zonder de kandidaat |

Voor de eigenlijke proef zijn **echt** dezelfde modelversie, eerste informatie, contextrechten en maximale kosten nodig. Het budget moet alle detector-, selectie-, model- en revisieaanroepen omvatten. De opgenomen testfixture heeft verzonnen hashes, een fictief model en is alleen bedoeld om de controles te beproeven.

## Twee gescheiden soorten vervolgmetingen

**RF, vastgestelde informatie:** elke arm ontvangt exact dezelfde, vooraf bevroren latere waarnemingen. Verschillen in vraagformulering zijn dan mogelijk meetbaar, maar een andere uitgevoerde interventie niet.

**RI, eigen interventie:** elke arm kiest binnen dezelfde regels een eigen onderzoekshandeling. Daardoor mogen werkelijke vervolgwaarnemingen verschillen. De nieuwe validatie weigert daarom een vooraf ingevulde uniforme uitkomst voor RI.

RF en RI mogen niet achteraf worden samengevoegd. Een technisch groen rapport uit deze fixture heeft uitsluitend status `MECHANICS_ONLY_NOT_APPROVED`, met `prospective_model_runs=0` en `g0_status=NOT_PASSED`.

## Reproduceren

```bash
python3 -m pytest -q research/tests/test_mit_matched_preflight.py

python3 research/scripts/mit_matched_preflight.py check-plan \
  --input research/fixtures/mit_matched_calibration_v1.json \
  --report /tmp/mit_matched_preflight_report.json

python3 research/scripts/mit_matched_preflight.py audit-history \
  --input /secure/checkpoint_results.json \
  --source-notes /secure/source_hypotheses.json \
  --report /tmp/mit_historical_diagnostic.json
```

Lokaal zijn na aanvulling **15 tests geslaagd**. De brongebonden herparse van de historische Actions-JSON geeft 5 oorspronkelijk ongeldige parseruitkomsten, **4 structureel herstelde verwijzingen** en 1 ongestructureerd `NONE`. De controle bevestigt alleen format en historische brontoewijzing; geen enkele van de vier `SAME_CLAIM`-beoordelingen is hiermee wetenschappelijk gevalideerd. Deze gegevens bewijzen geen methodisch verschil.

## Wat nodig blijft voor een volgende live proef

De G0-v3-opzet moet nog door een afzonderlijke technische en conceptuele beoordelaar worden getoetst. De anonieme reviewer van de MIT-notitieparen bevestigt een beoordeling van die paren, niet een goedkeuring van het latere G0-v3-experiment. Daarna zijn nieuwe beschermde casussen, echte bevroren kandidaat-herkomst, passende controleteksten, kostengelijke prompts en onafhankelijk beoordeelde latere vragen nodig.

De primaire weerlegging is eenvoudig: vindt arm C of E dezelfde toetsbare latere vraag als D, dan is de bijzondere bijdrage van de bewaarde kandidaat voor dat geval niet aangetoond. Een positieve uitkomst in D is alleen de eerste stap. De werkelijke inhoudelijke vervolgvraag moet daarna nog uitvoerbaar en controleerbaar blijken.

**Geen nieuwe effectmeting, geen automatische betaalde modelrun, geen verandering aan bestaande productcode of autorisatie.**

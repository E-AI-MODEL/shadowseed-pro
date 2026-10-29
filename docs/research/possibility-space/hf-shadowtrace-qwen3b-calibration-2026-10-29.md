# Qwen2.5-3B: Shadow Trace-instrumentkalibratie

**Datum:** 29 oktober 2026  
**Status:** eenmalig, verkennend, geen G0-acceptatie en geen Q1/Q2-proef  
**Run:** [GitHub Actions #40935970385](https://github.com/E-AI-MODEL/shadowseed-pro/actions/runs/40935970385)  
**Onderzoeksbranch:** `research/hf-shadowtrace-3b-calibration-20261029`

## Waarom dit experiment bestaat

De eerdere [Qwen2.5-0.5B-run #40831589642](https://github.com/E-AI-MODEL/shadowseed-pro/actions/runs/40831589642) was technisch volledig (drie gesprekken, achttien hostbeurten), maar de modelgesimuleerde gesprekspartner stelde herhaaldelijk nagenoeg dezelfde vragen en de detector produceerde geregeld `NONE` met verklarende tekst. De intake kan daardoor tekst accepteren zonder dat die een afzonderlijke, niet-uitgewerkte mogelijkheid vormt.

We kalibreren daarom uitsluitend of Qwen2.5-3B in **dezelfde gesprekssimulator-instructie** betekenisvolle vervolgvraagbeurten en interpreteerbare detectoruitvoer kan produceren. Het is **geen effectmeting van seedopslag, geen bewijs voor Q1/Q2 en geen sterke capaciteitsvergelijking**.

## Experiment (vastgelegd vóór uitkomstbeoordeling)

- **Model:** `Qwen/Qwen2.5-3B-Instruct`, werkelijke Hugging Face revision SHA verplicht in log.
- **Invoer:** twee fictieve gesprekopeningen uit de eerdere pilot (`city`, `sensors`), maximaal vier hostbeurten elk.
- **Modelrollen:** hetzelfde model genereert de hostreacties, detectoruitvoer en afzonderlijk een gesimuleerde gebruikersvraag. De gebruikerssimulator krijgt uitsluitend de laatste twee eigen vraag/antwoordparen, niet de seed- of engine-status.
- **Decoder:** greedy; geen rerolls, geen verbeterde tweede prompt bij falen. Eén modelinstantie is gedeeld door de twee canonieke HF-adapterrollen, voor CPU-geheugenbeheersing.
- **Productpijplijn:** ongewijzigde `ShadowseedEngine.prepare_turn → host model → observe_turn`, bestaande `current_pair`-detector, parsing, intake, `evidence_backed` Gate, TTL/TrTL en autorisatiegrens.
- **Stop:** eerste letterlijke herhaling van een eerdere gebruikersvraag (na uniforme minimale normalisatie) of kort/ongeldig eerste-vraagregel; alle ruwe outputs blijven bewaard. Dit voorkomt een schijnbaar lang gesprek dat alleen dezelfde vraag herhaalt.
- **Geen seedinjectie en geen promotie-door-onderzoeker.** Geen veranderingen aan productdefaults of Gate. Geen uit de bron afgeleide gewenste vervolgvraag.
- **Output:** alle zichtbare antwoorden, volgende vragen, exacte gerenderde promptstrings, detector-raw-output, parserdiagnostiek, intake/seedstaat, runtimefouten, status, modelhash en beurttijd. Verslag is alleen voor synthetische gegevens.

## Wat we na de run zullen beoordelen

1. **Gesprekscontinuïteit**: aantal werkelijk voltooide beurten per geval; exact herhaalde en ongeldige vragen; blind semantisch onderscheid tussen inhoudelijke vervolgvraag, parafrase, nieuw topic zonder aansluiting en herhaalde vraag. Een nieuwe vraag is geen bewijs van een nieuw relationeel perspectief.
2. **Detectorformat**: zuiver `NONE`; `NONE` mét overige tekst; genummerde kandidaten; parse- en intakeverlies; inhoudelijke parafrase van vraag of hostantwoord. De ruwe output is doorslaggevend, niet alleen de geaccepteerde seed.
3. **Herkomst en behoud**: raw detectorfragment → parseritem → intakebesluit → echte weight-zero birth → latere checkpoints; los van autorisatie, promotie of hostantwoord-blootstelling. Nul blootstelling in de gewone route is een bedoelde veiligheidseigenschap.
4. **Alternatieve verklaringen**: modelovertuiging/hallucinatie, lexicale overname, gedeelde sampling, simulatorstuwing, begroting, kleine casusselectie en verschillen in effectieve historie.
5. **Beslispunt**: uitsluitend als de instrumenten uitlegbare meerbeurtdata leveren, een *nieuwe prospectieve* Q1- en Q2-studie voorstellen onder onafhankelijke G0-review. Anders eerst instrumentproblemen oplossen; geen post-hoc selectie van alleen geslaagde gesprekken.

## Wat niet afgeleid mag worden

De 0,5B- en 3B-run verschillen in aantal casussen, antwoordlengte en de door het model veroorzaakte latere promptgeschiedenis. Zelfs meer gegenereerde vervolgvragen in 3B bewijzen geen algemene superioriteit. Een detectorvoorstel is niet automatisch niet-gekozen, nieuw, waar of nuttig. De twee fictieve trajecten vormen geen onafhankelijke dataset van wetenschappelijke ontdekkingen. **Een goed geformatteerde kandidaat is niet hetzelfde als een nieuwe onderzoekbaarheid.**

Bij een technisch geslaagde run blijft de conclusie hoogstens: een mogelijke route voor een volgende, gecontroleerde proef is kalibreerbaar. De hoofdthese blijft onbewezen. Onafhankelijke G0-veto's #234 en #235 zijn niet ingevuld.
